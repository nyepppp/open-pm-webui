<script lang="ts">
	import { toast } from 'svelte-sonner';

	type ExportFormat = 'xlsx' | 'csv' | 'json' | 'markdown' | 'docx';

	interface ColumnDef {
		key: string;
		label: string;
	}

	interface EntryItem {
		id: string;
		title: string;
		type?: string;
	}

	interface Props {
		open: boolean;
		moduleType: string;
		moduleDisplayName?: string;
		defaultColumns?: ColumnDef[];
		versionId?: string;
		entries?: EntryItem[];
		onClose: () => void;
		onExport: (params: { format: ExportFormat; columns: ColumnDef[] | undefined; entryIds?: string[] }) => Promise<void>;
	}

	let {
		open,
		moduleType,
		moduleDisplayName,
		defaultColumns = [],
		versionId,
		entries = [],
		onClose,
		onExport
	}: Props = $props();

	// 默认格式 xlsx
	let selectedFormat = $state<ExportFormat>('xlsx');
	// 是否启用列选择（默认关闭，导出全部默认列）
	let useCustomColumns = $state(false);
	// 当前选中的列（按顺序），来自 defaultColumns 初始化
	let selectedColumns = $state<ColumnDef[]>([]);
	// 备选列（未选中的）
	let availableColumns = $state<ColumnDef[]>([]);
	// 是否启用条目选择（默认关闭，导出全部条目）
	let useEntryFilter = $state(false);
	// 当前选中的条目 ID 集合
	let selectedEntryIds = $state<Set<string>>(new Set());
	let isExporting = $state(false);

	// 仅在对话框打开瞬间（open: false → true）初始化一次状态
	// 避免父组件 entries 引用变化时重置用户已选条目/列
	let previousOpen = $state(false);
	$effect(() => {
		if (open && !previousOpen) {
			if (defaultColumns.length > 0) {
				// 默认全选，按 defaultColumns 顺序
				selectedColumns = defaultColumns.map(c => ({ ...c }));
				availableColumns = [];
				useCustomColumns = false;
			}
			// 条目默认全选
			selectedEntryIds = new Set(entries.map(e => e.id));
			useEntryFilter = false;
			selectedFormat = 'xlsx';
		}
		previousOpen = open;
	});

	const formatOptions: { value: ExportFormat; label: string; hint: string }[] = [
		{ value: 'xlsx', label: 'Excel', hint: '多 sheet 表格，支持子类型拆分' },
		{ value: 'csv', label: 'CSV', hint: '纯文本表格，多 sheet 时打包 zip' },
		{ value: 'json', label: 'JSON', hint: '结构化数据，含元信息' },
		{ value: 'markdown', label: 'Markdown', hint: '富文本导出，content 保留格式' },
		{ value: 'docx', label: 'Word', hint: '富文本导出，适合文档分发' }
	];

	// 列选择相关操作
	function toggleUseCustomColumns() {
		useCustomColumns = !useCustomColumns;
		if (useCustomColumns) {
			// 启用列选择：默认全选
			if (selectedColumns.length === 0 && defaultColumns.length > 0) {
				selectedColumns = defaultColumns.map(c => ({ ...c }));
				availableColumns = [];
			}
		}
	}

	function moveColumnUp(index: number) {
		if (index <= 0) return;
		const cols = [...selectedColumns];
		[cols[index - 1], cols[index]] = [cols[index], cols[index - 1]];
		selectedColumns = cols;
	}

	function moveColumnDown(index: number) {
		if (index >= selectedColumns.length - 1) return;
		const cols = [...selectedColumns];
		[cols[index], cols[index + 1]] = [cols[index + 1], cols[index]];
		selectedColumns = cols;
	}

	function removeColumn(index: number) {
		const col = selectedColumns[index];
		availableColumns = [...availableColumns, col];
		selectedColumns = selectedColumns.filter((_, i) => i !== index);
	}

	function addColumn(index: number) {
		const col = availableColumns[index];
		selectedColumns = [...selectedColumns, col];
		availableColumns = availableColumns.filter((_, i) => i !== index);
	}

	// 条目选择相关操作
	function toggleUseEntryFilter() {
		useEntryFilter = !useEntryFilter;
		if (useEntryFilter && selectedEntryIds.size === 0 && entries.length > 0) {
			// 启用时若为空则默认全选
			selectedEntryIds = new Set(entries.map(e => e.id));
		}
	}

	function selectAllEntries() {
		selectedEntryIds = new Set(entries.map(e => e.id));
	}

	function clearAllEntries() {
		selectedEntryIds = new Set();
	}

	function toggleEntry(id: string) {
		const next = new Set(selectedEntryIds);
		if (next.has(id)) {
			next.delete(id);
		} else {
			next.add(id);
		}
		selectedEntryIds = next;
	}

	async function handleConfirm() {
		if (isExporting) return;
		isExporting = true;
		try {
			// 未启用自定义列时，默认传展示列（让后端按展示列导出，而非原始 7 列）
			const cols = useCustomColumns
				? selectedColumns
				: (defaultColumns && defaultColumns.length > 0
					? defaultColumns.map(c => ({ ...c }))
					: undefined);
			const ids = useEntryFilter && selectedEntryIds.size > 0 ? Array.from(selectedEntryIds) : undefined;
			await onExport({ format: selectedFormat, columns: cols, entryIds: ids });
			onClose();
		} catch (e: any) {
			toast.error(e.message || '导出失败');
		} finally {
			isExporting = false;
		}
	}
</script>

{#if open}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
		onclick={onClose}
	>
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div
			class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col"
			onclick={(e) => e.stopPropagation()}
		>
			<!-- Header -->
			<div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700 shrink-0">
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-3">
						<div class="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center flex-shrink-0">
							<svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
							</svg>
						</div>
						<div>
							<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
								导出 {moduleDisplayName || moduleType}
							</h2>
							<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
								选择导出格式、列与条目
							</p>
						</div>
					</div>
					<button
						class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
						onclick={onClose}
						aria-label="关闭"
					>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
			</div>

			<!-- Content -->
			<div class="p-6 space-y-5 overflow-y-auto flex-1">
				<!-- 格式选择 -->
				<div>
					<div class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">导出格式</div>
					<div class="grid grid-cols-5 gap-2">
						{#each formatOptions as opt}
							<button
								class="flex flex-col items-center justify-center p-3 rounded-lg border-2 transition-all text-center
									{selectedFormat === opt.value
										? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
										: 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 text-gray-700 dark:text-gray-300'}"
								onclick={() => (selectedFormat = opt.value)}
								title={opt.hint}
							>
								<span class="text-sm font-medium">{opt.label}</span>
							</button>
						{/each}
					</div>
					<p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
						{#each formatOptions as opt}
							{#if selectedFormat === opt.value}
								{opt.hint}
							{/if}
						{/each}
					</p>
				</div>

				<!-- 列选择 -->
				{#if defaultColumns.length > 0}
					<div class="pt-4 border-t border-gray-200 dark:border-gray-700">
						<label class="flex items-center gap-2 cursor-pointer">
							<input
								type="checkbox"
								class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
								checked={useCustomColumns}
								onchange={toggleUseCustomColumns}
							/>
							<span class="text-sm font-medium text-gray-700 dark:text-gray-300">自定义导出列</span>
							<span class="text-xs text-gray-500 dark:text-gray-400">
								（{useCustomColumns ? '已选 ' + selectedColumns.length + ' 列' : '默认导出全部 ' + defaultColumns.length + ' 列'}）
							</span>
						</label>

						{#if useCustomColumns}
							<div class="mt-3 grid grid-cols-2 gap-3">
								<!-- 已选列（按顺序） -->
								<div class="border border-gray-200 dark:border-gray-700 rounded-lg p-2">
									<div class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2 px-1">已选列（拖拽顺序）</div>
									{#if selectedColumns.length === 0}
										<div class="text-xs text-gray-400 italic py-4 text-center">无已选列</div>
									{:else}
										<ul class="space-y-1">
											{#each selectedColumns as col, i}
												<li class="flex items-center gap-1.5 px-2 py-1.5 rounded bg-blue-50 dark:bg-blue-900/20 text-xs">
													<span class="text-gray-400 font-mono text-[10px] w-4 shrink-0">{i + 1}</span>
													<span class="flex-1 truncate text-gray-800 dark:text-gray-200">{col.label}</span>
													<span class="text-[9px] text-gray-400 font-mono shrink-0">{col.key}</span>
													<button
														class="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 px-0.5"
														onclick={() => moveColumnUp(i)}
														disabled={i === 0}
														title="上移"
													>▲</button>
													<button
														class="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 px-0.5"
														onclick={() => moveColumnDown(i)}
														disabled={i === selectedColumns.length - 1}
														title="下移"
													>▼</button>
													<button
														class="text-red-400 hover:text-red-600 px-0.5"
														onclick={() => removeColumn(i)}
														title="移除"
													>✕</button>
												</li>
											{/each}
										</ul>
									{/if}
								</div>

								<!-- 备选列 -->
								<div class="border border-gray-200 dark:border-gray-700 rounded-lg p-2">
									<div class="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2 px-1">备选列</div>
									{#if availableColumns.length === 0}
										<div class="text-xs text-gray-400 italic py-4 text-center">无备选列</div>
									{:else}
										<ul class="space-y-1">
											{#each availableColumns as col, i}
												<li class="flex items-center gap-1.5 px-2 py-1.5 rounded bg-gray-50 dark:bg-gray-700/50 text-xs">
													<span class="flex-1 truncate text-gray-700 dark:text-gray-300">{col.label}</span>
													<span class="text-[9px] text-gray-400 font-mono shrink-0">{col.key}</span>
													<button
														class="text-green-500 hover:text-green-700 px-1 font-bold"
														onclick={() => addColumn(i)}
														title="添加"
													>+</button>
												</li>
											{/each}
										</ul>
									{/if}
								</div>
							</div>

							<!-- 自定义列提示 -->
							<p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
								JSON 格式忽略列选择；markdown/docx 会按选中列顺序输出表头与元数据。
							</p>
						{/if}
					</div>
				{/if}

				<!-- 条目选择 -->
				{#if entries.length > 0}
					<div class="pt-4 border-t border-gray-200 dark:border-gray-700">
						<label class="flex items-center gap-2 cursor-pointer">
							<input
								type="checkbox"
								class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
								checked={useEntryFilter}
								onchange={toggleUseEntryFilter}
							/>
							<span class="text-sm font-medium text-gray-700 dark:text-gray-300">按条目选择</span>
							<span class="text-xs text-gray-500 dark:text-gray-400">
								（{useEntryFilter ? '已选 ' + selectedEntryIds.size + ' / ' + entries.length + ' 条' : '默认导出全部 ' + entries.length + ' 条'}）
							</span>
						</label>

						{#if useEntryFilter}
							<div class="mt-3 border border-gray-200 dark:border-gray-700 rounded-lg">
								<div class="flex items-center justify-between px-3 py-2 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/30">
									<div class="flex gap-3">
										<button
											class="text-xs text-blue-600 hover:underline dark:text-blue-400"
											onclick={selectAllEntries}
										>全选</button>
										<button
											class="text-xs text-gray-500 hover:underline dark:text-gray-400"
											onclick={clearAllEntries}
										>清空</button>
									</div>
									<span class="text-xs text-gray-400">已选 {selectedEntryIds.size} / {entries.length}</span>
								</div>
								<div class="max-h-48 overflow-y-auto p-2 space-y-0.5">
									{#each entries as entry (entry.id)}
										<label class="flex items-center gap-2 text-sm py-1 px-2 rounded hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer">
											<input
												type="checkbox"
												class="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
												checked={selectedEntryIds.has(entry.id)}
												onchange={() => toggleEntry(entry.id)}
											/>
											<span class="flex-1 truncate text-gray-700 dark:text-gray-300">
												{entry.title || entry.id.slice(0, 8)}
											</span>
											{#if entry.type}
												<span class="text-[10px] text-gray-400 bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded shrink-0">
													{entry.type}
												</span>
											{/if}
										</label>
									{/each}
								</div>
							</div>
							<p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
							勾选要导出的条目；不勾选任何条目时确认按钮将禁用。
						</p>
					{/if}
				</div>
			{:else}
				<!-- 空状态：entries 为空时显示原因提示，避免用户困惑"不能选中" -->
				<div class="pt-4 border-t border-gray-200 dark:border-gray-700">
					<div class="rounded-md border border-amber-200 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-900/10 p-3">
						<div class="flex items-center gap-1.5 mb-1">
							<span class="text-amber-600 dark:text-amber-400">⚠</span>
							<span class="text-xs font-semibold text-amber-700 dark:text-amber-300">暂无可导出的条目</span>
						</div>
						<p class="text-[11px] text-amber-700 dark:text-amber-300 leading-relaxed">
							当前模块没有加载到任何条目数据。可能原因：后端服务未启动、数据加载失败、或该模块确实为空。请检查后端连接或刷新页面后重试。
						</p>
					</div>
				</div>
			{/if}

				<!-- 版本信息 -->
				{#if versionId}
					<div class="pt-4 border-t border-gray-200 dark:border-gray-700">
						<div class="text-xs text-gray-500 dark:text-gray-400">
							导出版本: <span class="font-mono text-gray-700 dark:text-gray-300">{versionId.slice(0, 8)}...</span>
						</div>
					</div>
				{/if}
			</div>

			<!-- Actions -->
			<div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-end gap-3 shrink-0">
				<button
					class="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
					onclick={onClose}
					disabled={isExporting}
				>
					取消
				</button>
				<button
					class="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-500 text-white rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
					onclick={handleConfirm}
					disabled={isExporting || (useCustomColumns && selectedColumns.length === 0) || (useEntryFilter && selectedEntryIds.size === 0)}
				>
					{#if isExporting}
						<svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
						</svg>
						导出中...
					{:else}
						确认导出
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if}
