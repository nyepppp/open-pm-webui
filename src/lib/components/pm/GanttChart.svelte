<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	// D15: frappe-gantt 1.2.2 发布包缺少 dist 目录（package.json exports 指向 dist 但实际只有 src）
	// 直接 import 'frappe-gantt' 会因 exports 字段解析到 ./dist/frappe-gantt.es.js 失败
	// 改用 src/index.js 入口 + src/styles/gantt.css
	import Gantt from 'frappe-gantt/src/index.js';
	import 'frappe-gantt/src/styles/gantt.css';

	/**
	 * GanttChart —— 基于 frappe-gantt 的甘特图组件。
	 *
	 * 替换原 +page.svelte 中手写的、带 {#key filteredEntries} 反模式的甘特渲染。
	 * frappe-gantt 内部用 SVG 自管 DOM，避免每次过滤变化销毁整棵子树。
	 *
	 * 跨模块条目（风险/会议/需求等）通过 custom_class 染色 + 名称前缀标注。
	 *
	 * 暴露给父组件（通过 bind:this）的方法：
	 * - centerOnToday()：将今天列滚动到视口中央
	 * - scrollToDate(dateStr: 'YYYY-MM-DD')：滚动到指定日期
	 */

	export interface GanttEntry {
		id: string;
		title: string;
		content?: string;
		_sd: string; // 归一化后的开始日期（任何可被 new Date() 解析的格式）
		_ed: string; // 归一化后的结束日期
		_source?: string; // 来源模块类型（schedule/roadmap/risk/meeting/requirement/...）
		data?: Record<string, any>;
		[key: string]: any;
	}

	interface Props {
		entries: GanttEntry[];
		timeScale?: 'day' | 'week' | 'month';
		moduleType?: string;
		onEntryClick?: (entry: GanttEntry) => void;
	}

	let {
		entries,
		timeScale = 'week',
		moduleType = '',
		onEntryClick
	}: Props = $props();

	// 跨模块来源颜色 / 标签（与 +page.svelte 的 sourceColorMap/sourceLabelMap 对齐）
	const sourceColorMap: Record<string, string> = {
		schedule: 'gantt-bar-schedule',
		roadmap: 'gantt-bar-roadmap',
		risk: 'gantt-bar-risk',
		meeting: 'gantt-bar-meeting',
		requirement: 'gantt-bar-requirement'
	};
	const sourceLabelMap: Record<string, string> = {
		schedule: '排期',
		roadmap: '路线图',
		risk: '风险',
		meeting: '会议',
		requirement: '需求'
	};

	const nodeStatusClassMap: Record<string, string> = {
		completed: 'gantt-bar-completed',
		in_progress: 'gantt-bar-in-progress',
		delayed: 'gantt-bar-delayed',
		planned: 'gantt-bar-planned'
	};

	let container: HTMLDivElement;
	let ganttInstance: any = null;
	// 小地图视口状态：{left, width, totalWidth}
	let minimapViewport = $state({ left: 0, width: 0, totalWidth: 0 });

	// 把 timeScale 映射到 frappe-gantt 的 view_mode
	function toViewMode(ts: string): string {
		if (ts === 'day') return 'Day';
		if (ts === 'month') return 'Month';
		return 'Week';
	}

	// 把任意日期值格式化为 'YYYY-MM-DD'
	function formatDate(d: any): string | null {
		if (!d) return null;
		const dt = new Date(d);
		if (isNaN(dt.getTime())) return null;
		const y = dt.getFullYear();
		const m = String(dt.getMonth() + 1).padStart(2, '0');
		const day = String(dt.getDate()).padStart(2, '0');
		return `${y}-${m}-${day}`;
	}

	// 取条目的 data 字段值
	function getData(entry: GanttEntry, key: string): any {
		return entry.data?.[key] ?? (entry as any)[key];
	}

	// 把 GanttEntry[] 转为 frappe-gantt task[]
	function toTasks(ents: GanttEntry[]): any[] {
		const tasks: any[] = [];
		const todayStr = formatDate(new Date());
		const todayTime = todayStr ? new Date(todayStr).getTime() : Date.now();
		for (const e of ents) {
			const start = formatDate(e._sd);
			let end = formatDate(e._ed);
			if (!start || !end) continue;
			// frappe-gantt 要求 end > start；单日条目 end 设为 start+1 天
			if (start === end) {
				const dt = new Date(end);
				dt.setDate(dt.getDate() + 1);
				end = formatDate(dt) || end;
			}
			const src = e._source || moduleType;
			const srcLabel = sourceLabelMap[src] || src;
			const isCross = src !== moduleType;
			const ns = getData(e, 'nodeStatus');
			const pg = Number(getData(e, 'progress')) || 0;
			// dependencies 字段可能是 ID 数组或逗号分隔字符串
			let deps = getData(e, 'dependencies');
			if (typeof deps === 'string') deps = deps.split(',').map((s: string) => s.trim()).filter(Boolean);
			if (!Array.isArray(deps)) deps = [];

			// custom_class：跨模块优先用来源色，否则按状态色
			let customClass = '';
			if (isCross && sourceColorMap[src]) {
				customClass = sourceColorMap[src];
			} else if (ns && nodeStatusClassMap[ns]) {
				customClass = nodeStatusClassMap[ns];
			}

			// 时间态类（历史视觉）：past/current/future，与来源/状态色并存
			// past: 已结束（end <= today）；current: 进行中（start <= today < end）；future: 未开始（start > today）
			const startTime = new Date(start).getTime();
			const endTime = new Date(end).getTime();
			let temporalClass = '';
			if (endTime <= todayTime) {
				temporalClass = 'gantt-bar-past';
			} else if (startTime <= todayTime) {
				temporalClass = 'gantt-bar-current';
			} else {
				temporalClass = 'gantt-bar-future';
			}
			// 多类合并（frappe-gantt custom_class 支持空格分隔多类）
			const fullClass = [customClass, temporalClass].filter(Boolean).join(' ').trim();

			const desc = getData(e, 'description') || e.content || '';

			tasks.push({
				id: e.id,
				name: (isCross ? `[${srcLabel}] ` : '') + (e.title || ''),
				start,
				end,
				progress: pg,
				dependencies: deps,
				custom_class: fullClass,
				description: desc ? String(desc).slice(0, 120) : '',
				_raw_entry: e
			});
		}
		return tasks;
	}

	// 动态获取 today 列宽度（frappe-gantt 1.2.2 的 today 列类名为 .today）
	function getTodayColumnWidth(): number {
		if (!container) return 40;
		// frappe-gantt 1.2.2 在 .gantt-container 内生成 .today 标识今天列
		// .today 是 SVG 元素，没有 offsetWidth，需用 getBoundingClientRect()
		const todayCell = container.querySelector('.gantt-container .today') as SVGElement | null;
		if (todayCell) {
			const rect = todayCell.getBoundingClientRect();
			if (rect.width > 0) return rect.width;
		}
		// 退化：取任意一列的宽度（grid-row rect 有 width 属性）
		const anyCell = container.querySelector('.gantt-container .grid-row rect') as SVGElement | null;
		if (anyCell) {
			const w = (anyCell as any).getAttribute('width');
			if (w) return Number(w) || 40;
			// 也尝试 getBoundingClientRect 兜底
			const r = anyCell.getBoundingClientRect();
			if (r.width > 0) return r.width;
		}
		return 40;
	}

	// 更新小地图视口状态
	function updateMinimap() {
		if (!container) return;
		const inner = container.querySelector('.gantt-container') as HTMLElement | null;
		if (!inner) return;
		minimapViewport = {
			left: inner.scrollLeft,
			width: inner.clientWidth,
			totalWidth: inner.scrollWidth
		};
	}

	// 附加 scroll 监听器到 .gantt-container，使小地图随用户滚动实时同步
	// rebuild 会清空 container.innerHTML 重建 .gantt-container，所以每次 rebuild 后需重新附加
	let currentScrollTarget: HTMLElement | null = null;
	function attachScrollListener() {
		if (!container) return;
		const inner = container.querySelector('.gantt-container') as HTMLElement | null;
		if (!inner) return;
		// 避免重复绑定：若上一次的目标还在，先移除
		if (currentScrollTarget && currentScrollTarget !== inner) {
			currentScrollTarget.removeEventListener('scroll', onGanttScroll);
		}
		if (currentScrollTarget !== inner) {
			inner.addEventListener('scroll', onGanttScroll, { passive: true });
			currentScrollTarget = inner;
		}
	}

	// scroll 回调：rAF 节流，避免高频 scroll 事件卡顿
	let scrollRafId: number | null = null;
	function onGanttScroll() {
		if (scrollRafId !== null) return;
		scrollRafId = requestAnimationFrame(() => {
			scrollRafId = null;
			updateMinimap();
		});
	}

	// 销毁当前实例并重建
	// recenterToday=true 时重建后重新居中 today 列；false 时恢复原 scrollLeft
	function rebuild(recenterToday: boolean = false) {
		if (!container) return;
		// 保存滚动位置（rebuild 会重置 scrollLeft，需在末尾恢复或重新居中）
		const inner = container.querySelector('.gantt-container') as HTMLElement | null;
		const savedScrollLeft = inner?.scrollLeft;

		// 清空容器内 frappe-gantt 创建的 SVG + popup
		container.innerHTML = '';
		const tasks = toTasks(entries);
		if (tasks.length === 0) {
			ganttInstance = null;
			return;
		}
		try {
			ganttInstance = new Gantt(container, tasks, {
			view_mode: toViewMode(timeScale),
			language: 'zh',
			readonly: false,
			scroll_to: 'today',
			today_button: false,
			popup_on: 'hover',
				custom_popup_html: null as any,
				on_click: (task: any) => {
					if (onEntryClick && task._raw_entry) {
						onEntryClick(task._raw_entry);
					}
				},
				on_date_change: () => {
					// 拖拽改日期暂不回写（避免误操作），仅本地更新
				},
				on_progress_change: () => {}
			});
		} catch (err) {
			console.error('[GanttChart] frappe-gantt init failed:', err);
			ganttInstance = null;
			return;
		}

		// 末尾：若 recenterToday 则居中，否则恢复 savedScrollLeft
		// 双层 RAF 确保 frappe-gantt 内部布局完成
		if (recenterToday) {
			requestAnimationFrame(() => {
				requestAnimationFrame(() => {
					centerOnToday();
					updateMinimap();
				});
			});
		} else if (savedScrollLeft !== undefined && savedScrollLeft > 0) {
			requestAnimationFrame(() => {
				const innerAfter = container.querySelector('.gantt-container') as HTMLElement | null;
				if (innerAfter) innerAfter.scrollLeft = savedScrollLeft;
				updateMinimap();
			});
		} else {
			requestAnimationFrame(updateMinimap);
		}
		// 附加 scroll 监听器到新创建的 .gantt-container，使小地图随滚动同步
		attachScrollListener();
	}

	// 将今天列滚动到视口中央（供父组件通过 bind:this 调用）
	function centerOnToday() {
		if (!container || !ganttInstance) return;
		const inner = container.querySelector('.gantt-container') as HTMLElement | null;
		if (!inner) return;
		// 先用 frappe-gantt 内置方法定位到 today 列
		ganttInstance.set_scroll_position('today');
		// 双层 RAF 确保 frappe-gantt 内部布局完成
		requestAnimationFrame(() => {
			requestAnimationFrame(() => {
				const currentLeft = inner.scrollLeft;
				const viewportWidth = inner.clientWidth;
				// 动态获取 today 列宽度，让 today 列真正居中
				const colWidth = getTodayColumnWidth();
				inner.scrollTo({
					left: currentLeft - viewportWidth / 2 + colWidth / 2,
					behavior: 'smooth'
				});
				updateMinimap();
			});
		});
	}

	// 滚动到指定日期（供父组件通过 bind:this 调用）
	// dateStr 格式：'YYYY-MM-DD'
	function scrollToDate(dateStr: string) {
		if (!container || !ganttInstance || !dateStr) return;
		const inner = container.querySelector('.gantt-container') as HTMLElement | null;
		if (!inner) return;
		const targetDate = new Date(dateStr);
		if (isNaN(targetDate.getTime())) return;
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		const diffDays = Math.round((targetDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

		// 先定位 today，再按列宽偏移 diffDays 列并居中
		ganttInstance.set_scroll_position('today');
		requestAnimationFrame(() => {
			requestAnimationFrame(() => {
				const colWidth = getTodayColumnWidth();
				const viewportWidth = inner.clientWidth;
				inner.scrollTo({
					left: inner.scrollLeft + diffDays * colWidth - viewportWidth / 2 + colWidth / 2,
					behavior: 'smooth'
				});
				updateMinimap();
			});
		});
	}

	// D3: 跳到最后一个任务居中 — 取 end_date 最晚的任务的中心日期，
	// 复用 scrollToDate 让它出现在视口中央
	function scrollToEnd() {
		if (!container || !ganttInstance) return;
		const tasks = toTasks(entries);
		if (tasks.length === 0) return;
		let maxEnd = -Infinity;
		let matchingStart = Infinity;
		for (const t of tasks) {
			const e = new Date(t.end).getTime();
			if (e > maxEnd) {
				maxEnd = e;
				matchingStart = new Date(t.start).getTime();
			}
		}
		if (maxEnd === -Infinity) return;
		// 取最晚任务的中心日期
		const midTime = (matchingStart + maxEnd) / 2;
		const midDate = new Date(midTime);
		const y = midDate.getFullYear();
		const m = String(midDate.getMonth() + 1).padStart(2, '0');
		const d = String(midDate.getDate()).padStart(2, '0');
		scrollToDate(`${y}-${m}-${d}`);
	}

	// 键盘快捷键处理器
	function handleKeydown(e: KeyboardEvent) {
		if (!container || !ganttInstance) return;
		// 焦点在输入框/textarea/contenteditable 时不拦截
		const target = e.target as HTMLElement;
		if (target) {
			const tag = target.tagName.toLowerCase();
			if (tag === 'input' || tag === 'textarea' || target.isContentEditable) return;
		}
		const inner = container.querySelector('.gantt-container') as HTMLElement | null;
		if (!inner) return;
		const step = inner.clientWidth * 0.3; // 30% viewport
		const key = e.key.toLowerCase();
		switch (key) {
			case 't':
				e.preventDefault();
				centerOnToday();
				break;
			case 'arrowleft':
				e.preventDefault();
				inner.scrollBy({ left: -step, behavior: 'smooth' });
				break;
			case 'arrowright':
				e.preventDefault();
				inner.scrollBy({ left: step, behavior: 'smooth' });
				break;
			case 'home':
				e.preventDefault();
				inner.scrollTo({ left: 0, behavior: 'smooth' });
				break;
			case 'end':
				e.preventDefault();
				inner.scrollTo({ left: inner.scrollWidth, behavior: 'smooth' });
				break;
		}
	}

	// 小地图点击跳转
	function handleMinimapClick(e: MouseEvent) {
		if (!container) return;
		const inner = container.querySelector('.gantt-container') as HTMLElement | null;
		if (!inner) return;
		const target = e.currentTarget as HTMLElement;
		const rect = target.getBoundingClientRect();
		const ratio = (e.clientX - rect.left) / rect.width;
		inner.scrollTo({
			left: ratio * inner.scrollWidth - inner.clientWidth / 2,
			behavior: 'smooth'
		});
	}

	onMount(() => {
		rebuild();
		// 等 frappe-gantt 内部布局完成后再居中 today 列
		requestAnimationFrame(() => {
			requestAnimationFrame(() => {
				centerOnToday();
			});
		});
		// 绑定键盘快捷键
		window.addEventListener('keydown', handleKeydown);
	});

	onDestroy(() => {
		window.removeEventListener('keydown', handleKeydown);
		// 清理 scroll 监听器，避免内存泄漏
		if (currentScrollTarget) {
			currentScrollTarget.removeEventListener('scroll', onGanttScroll);
			currentScrollTarget = null;
		}
		if (scrollRafId !== null) {
			cancelAnimationFrame(scrollRafId);
			scrollRafId = null;
		}
		ganttInstance = null;
		if (container) container.innerHTML = '';
	});

	// entries 变化时重建（preserve scroll，不重置到 today）
	// 拆分自原合并 $effect：原 $effect 同时追踪 entries+timeScale，导致 entries 变化（如过滤）
	// 时也触发 recenterToday=true，丢失用户滚动位置
	$effect(() => {
		const _ents = entries;
		// 跳过首次（onMount 已处理）
		if (ganttInstance !== null || (container && container.children.length > 0)) {
			queueMicrotask(() => rebuild(false));
		}
	});

	// timeScale 变化时优先用 frappe-gantt 内置 change_view_mode（不销毁 DOM，保留滚动）
	// 若 ganttInstance 不存在（首次），则走 rebuild 流程
	$effect(() => {
		const _ts = timeScale;
		if (!ganttInstance) return;
		// 首次跳过（onMount 已用初始 timeScale 创建实例）
		if (container && container.children.length > 0) {
			queueMicrotask(() => {
				try {
					ganttInstance.change_view_mode(toViewMode(_ts));
					// 视图模式切换后列宽变化，重新居中 today 列让用户保持上下文
					requestAnimationFrame(() => {
						requestAnimationFrame(() => {
							centerOnToday();
						});
					});
				} catch (err) {
					// change_view_mode 失败时退化到全量重建
					console.warn('[GanttChart] change_view_mode failed, falling back to rebuild:', err);
					rebuild(true);
				}
			});
		}
	});

	// 暴露给父组件（bind:this）的方法
	// Svelte 5 runes 模式下，函数声明不会自动挂到组件实例，需显式 export
	export { centerOnToday, scrollToDate, scrollToEnd };
</script>

<div class="gantt-wrapper">
	{#if entries.length === 0}
		<div class="py-8 text-center text-sm text-gray-400">
			暂无带日期的条目（含风险/会议/需求/排期/路线图），无法展示甘特图
		</div>
	{:else}
		<!-- 顶部小地图：显示完整时间范围 + 当前视口位置 -->
		<div
			class="gantt-minimap"
			onclick={handleMinimapClick}
			role="button"
			tabindex="-1"
			aria-label="点击小地图跳转到对应位置"
			title="点击跳转"
		>
			<div
				class="gantt-minimap-viewport"
				style="left: {minimapViewport.totalWidth > 0
					? (minimapViewport.left / minimapViewport.totalWidth) * 100
					: 0}%; width: {minimapViewport.totalWidth > 0
					? Math.max((minimapViewport.width / minimapViewport.totalWidth) * 100, 2)
					: 100}%"
			></div>
		</div>
		<div class="gantt-scroll" bind:this={container}></div>
		<!-- 键盘快捷键提示 + 图例 -->
		<div class="gantt-shortcut-hint">
			<kbd>T</kbd> 今天 · <kbd>←</kbd>/<kbd>→</kbd> 滚动 · <kbd>Home</kbd>/<kbd>End</kbd> 跳到首尾
			<span class="gantt-legend">
				· <span class="gantt-legend-dot gantt-legend-past"></span>已结束
				<span class="gantt-legend-dot gantt-legend-current"></span>进行中
				<span class="gantt-legend-dot gantt-legend-future"></span>未开始
			</span>
		</div>
	{/if}
</div>

<style>
	:global(.gantt-wrapper) {
		width: 100%;
		min-width: 0;
		padding: 0.75rem;
	}
	:global(.gantt-scroll) {
		overflow-x: auto;
		width: 100%;
		max-width: 100%;
		min-width: 700px;
	}
	/* 图例 */
	.gantt-legend {
		margin-left: 8px;
		display: inline-flex;
		align-items: center;
		gap: 4px;
	}
	.gantt-legend-dot {
		display: inline-block;
		width: 8px;
		height: 8px;
		border-radius: 2px;
		margin-left: 4px;
		vertical-align: middle;
	}
	.gantt-legend-past {
		background: #9ca3af;
		opacity: 0.6;
	}
	.gantt-legend-current {
		background: #3b82f6;
	}
	.gantt-legend-future {
		background: #9ca3af;
	}
	/* 小地图 */
	.gantt-minimap {
		height: 8px;
		background: #e5e7eb;
		border-radius: 4px;
		position: relative;
		cursor: pointer;
		margin-bottom: 6px;
		overflow: hidden;
	}
	:global(.dark) .gantt-minimap {
		background: #374151;
	}
	.gantt-minimap-viewport {
		position: absolute;
		top: 0;
		height: 100%;
		background: rgba(59, 130, 246, 0.3);
		border-left: 1px solid rgba(59, 130, 246, 0.6);
		border-right: 1px solid rgba(59, 130, 246, 0.6);
		transition: left 0.1s ease-out, width 0.1s ease-out;
		pointer-events: none;
	}
	/* 键盘快捷键提示 */
	.gantt-shortcut-hint {
		margin-top: 4px;
		font-size: 10px;
		color: #9ca3af;
		text-align: right;
	}
	.gantt-shortcut-hint kbd {
		display: inline-block;
		padding: 1px 4px;
		font-size: 9px;
		font-family: monospace;
		background: #f3f4f6;
		border: 1px solid #d1d5db;
		border-radius: 3px;
		color: #6b7280;
	}
	:global(.dark) .gantt-shortcut-hint kbd {
		background: #374151;
		border-color: #4b5563;
		color: #9ca3af;
	}
	/* 跨模块来源色 */
	:global(.gantt-bar-schedule) {
		fill: #3b82f6 !important;
	}
	:global(.gantt-bar-roadmap) {
		fill: #a855f7 !important;
	}
	:global(.gantt-bar-risk) {
		fill: #ef4444 !important;
	}
	:global(.gantt-bar-meeting) {
		fill: #f59e0b !important;
	}
	:global(.gantt-bar-requirement) {
		fill: #10b981 !important;
	}
	/* 本模块状态色 */
	:global(.gantt-bar-completed) {
		fill: #22c55e !important;
	}
	:global(.gantt-bar-in-progress) {
		fill: #3b82f6 !important;
	}
	:global(.gantt-bar-delayed) {
		fill: #ef4444 !important;
	}
	:global(.gantt-bar-planned) {
		fill: #9ca3af !important;
	}
	/* 时间态视觉（历史区分）：past 半透明 / current 加边框高亮 / future 虚线边框 */
	/* 与来源色/状态色并存：temporal class 控制 opacity 和 stroke，不覆盖 fill */
	:global(.gantt-bar-past) {
		opacity: 0.55;
	}
	:global(.gantt-bar-current) {
		stroke: #1e40af;
		stroke-width: 2;
	}
	:global(.gantt-bar-future) {
		opacity: 0.75;
		stroke: #6b7280;
		stroke-width: 1;
		stroke-dasharray: 4 3;
	}
	/* today 列高亮（frappe-gantt 1.2.2 用 .today 类标识） */
	:global(.gantt-container .today) {
		background-color: rgba(59, 130, 246, 0.1) !important;
		border-left: 2px solid rgba(59, 130, 246, 0.5);
	}
	/* 暗色模式适配 */
	:global(.dark .gantt-container) {
		background: #1f2937;
		color: #e5e7eb;
	}
	:global(.dark .gantt-container .grid-row) {
		fill: #374151 !important;
	}
	:global(.dark .gantt-container .grid-header) {
		fill: #111827 !important;
	}
	:global(.dark .gantt-container .lower-text),
	:global(.dark .gantt-container .upper-text) {
		fill: #9ca3af !important;
	}
	:global(.dark .gantt-container .today) {
		background-color: rgba(59, 130, 246, 0.15) !important;
		border-left-color: rgba(96, 165, 250, 0.7);
	}
</style>
