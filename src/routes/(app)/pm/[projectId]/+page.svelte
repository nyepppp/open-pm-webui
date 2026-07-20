<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import dayjs from '$lib/dayjs';
	import { getEntries } from '$lib/apis/pm/index';
	import { currentVersion, versions as versionList } from '$lib/stores/pm/versionStore';
	import { agentStatus, refreshAgentStatus, hasModels } from '$lib/stores/pm/agentChatStore';

	let projectId = $derived($page.params.projectId || '');

	// SVG icon paths (Heroicons outline, 24x24)
	const svgIcons: Record<string, string> = {
		prd: 'M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z',
		requirement: 'M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15a2.25 2.25 0 012.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z',
		roadmap: 'M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z',
		parameter: 'M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75',
		architecture: 'M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9',
		competitor: 'M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z',
		testcase: 'M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5',
		risk: 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z',
		meeting: 'M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10',
		acceptance: 'M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
		faq: 'M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z',
		prototype: 'M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0022.5 18.75V5.25A2.25 2.25 0 0020.25 3H3.75A2.25 2.25 0 001.5 5.25v13.5A2.25 2.25 0 003.75 21z',
		schedule: 'M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5',
		'requirement-boundary': 'M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.75m0 0l-.5 1.5m.75-9l3-3 2.148 2.148A12.061 12.061 0 0116.5 7.605',
		spec: 'M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z',
		flowchart: 'M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5'
	};

	let moduleGroups = $derived([
		{
			id: 'plan', label: '规划', modules: [
				{ id: 'prd', label: 'PRD 文档', desc: '产品需求文档', href: `/pm/${projectId}/prd` },
				{ id: 'requirement', label: '需求管理', desc: '需求收集与分析', href: `/pm/${projectId}/requirement` },
				{ id: 'roadmap', label: '产品路线图', desc: '版本规划', href: `/pm/${projectId}/roadmap` }
			]
		},
		{
			id: 'design', label: '设计', modules: [
			{ id: 'parameter', label: '参数配置', desc: '参数清单管理', href: `/pm/${projectId}/parameter` },
			{ id: 'architecture', label: '产品架构', desc: '架构设计', href: `/pm/${projectId}/architecture` },
				{ id: 'prototype', label: '原型/UI设计', desc: '设计稿与评审', href: `/pm/${projectId}/prototype` },
				{ id: 'competitor', label: '竞品分析', desc: '竞品对比矩阵', href: `/pm/${projectId}/competitor` },
				{ id: 'spec', label: 'SPEC 规范', desc: '规范文档管理', href: `/pm/${projectId}/spec` },
				{ id: 'flowchart', label: '流程图', desc: '流程图编辑', href: `/pm/${projectId}/flowchart` }
			]
		},
		{
			id: 'execute', label: '执行', modules: [
				{ id: 'schedule', label: '项目排期', desc: '甘特图与任务', href: `/pm/${projectId}/schedule` },
				{ id: 'testcase', label: '测试用例', desc: '用例管理', href: `/pm/${projectId}/testcase` },
				{ id: 'risk', label: '风险分析', desc: '风险管控', href: `/pm/${projectId}/risk` },
				{ id: 'meeting', label: '会议纪要', desc: '评审记录', href: `/pm/${projectId}/meeting` }
			]
		},
		{
			id: 'review', label: '复盘', modules: [
				{ id: 'acceptance', label: '验收报告', desc: '验收检查', href: `/pm/${projectId}/acceptance` },
				{ id: 'faq', label: 'FAQ', desc: '常见问题', href: `/pm/${projectId}/faq` }
			]
		},
		{
			id: 'boundary', label: '边界', modules: [
				{ id: 'requirement-boundary', label: '需求边界', desc: '需求边界分析', href: `/pm/${projectId}/requirement-boundary` }
			]
		}
	]);

	const allModules = $derived(moduleGroups.flatMap(g => g.modules));

	// Stats
	let moduleCounts = $state<Record<string, number>>({});
	let statusCounts = $state<Record<string, number>>({});
	let isLoadingStats = $state(true);

	// Recent activity
	let recentItems = $state<any[]>([]);
	let isLoadingRecent = $state(true);

	// Filter / Search / Pagination for recent activity
	let searchQuery = $state('');
	let filterModuleType = $state<string>('all');
	let filterStatus = $state<string>('all');
	let currentPage = $state(1);
	const PAGE_SIZE = 20;

	let filteredRecentItems = $derived(() => {
		let result = recentItems;
		if (searchQuery.trim()) {
			const q = searchQuery.toLowerCase();
			result = result.filter(e => (e.title || '').toLowerCase().includes(q));
		}
		if (filterModuleType !== 'all') {
			result = result.filter(e => (e.module_type || e.moduleType) === filterModuleType);
		}
		if (filterStatus !== 'all') {
			result = result.filter(e => (e.status || 'draft') === filterStatus);
		}
		return result;
	});
	let filteredRecent = $derived(filteredRecentItems());
	let totalPages = $derived(Math.max(1, Math.ceil(filteredRecent.length / PAGE_SIZE)));
	let pagedRecentItems = $derived(filteredRecent.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE));
	$effect(() => { filteredRecent; if (currentPage > totalPages) currentPage = totalPages; });

	// Traceability count
	let traceabilityCount = $state(0);

	// Version-bound entry counts
	let versionEntryCounts = $state<Record<string, number>>({});

	async function loadDashboardData() {
		const token = localStorage.token || '';
		isLoadingStats = true;
		isLoadingRecent = true;
		try {
			const allEntries = await getEntries(token, projectId);
			// Count per module
			const counts: Record<string, number> = {};
			for (const mod of allModules) { counts[mod.id] = 0; }
			for (const entry of allEntries) {
				const mt = entry.module_type || entry.moduleType || '';
				if (counts[mt] !== undefined) counts[mt]++;
				else counts[mt] = 1;
			}
			moduleCounts = counts;
			// Count per status
			const sCounts: Record<string, number> = { draft: 0, review: 0, approved: 0, archived: 0 };
			for (const entry of allEntries) {
				const s = entry.status || 'draft';
				if (sCounts[s] !== undefined) sCounts[s]++;
			}
			statusCounts = sCounts;
			// Count traceability relations
			let relCount = 0;
			for (const entry of allEntries) {
				const data = entry.data || entry.metadata || {};
				if (data.requirementId) relCount++;
				if (data.parameterId) relCount++;
				if (data.featureName) relCount++;
				if (data.sourceDocument) relCount++;
			}
			traceabilityCount = relCount;
			// Version-bound entry counts
			const vCounts: Record<string, number> = {};
			for (const entry of allEntries) {
				const vid = entry.versionId || (entry.data || entry.metadata || {}).versionId || '';
				if (vid) {
					vCounts[vid] = (vCounts[vid] || 0) + 1;
				}
			}
			versionEntryCounts = vCounts;
			// Recent items
			const sorted = [...allEntries].sort((a: any, b: any) => {
				const ta = a.updated_at || a.updatedAt || 0;
				const tb = b.updated_at || b.updatedAt || 0;
				return tb - ta;
			});
			recentItems = sorted;
		} catch {
			moduleCounts = {};
			statusCounts = {};
			recentItems = [];
		} finally {
			isLoadingStats = false;
			isLoadingRecent = false;
		}
	}

	onMount(() => { loadDashboardData(); refreshAgentStatus(); });

	import { normalizeTs, formatDate, formatDateTime } from '$lib/utils/pmTimeUtils';

	function formatTime(ts: unknown): string {
		const ms = normalizeTs(ts);
		if (ms == null) return '';
		try { return dayjs(ms).fromNow(); } catch { return ''; }
	}

	function getModuleLabel(moduleType: string): string {
		return allModules.find(m => m.id === moduleType)?.label || moduleType;
	}

	function getModuleHref(moduleType: string): string {
		return allModules.find(m => m.id === moduleType)?.href || `/pm/${projectId}/${moduleType}`;
	}

	function getVersionLabel(vid: string): string {
		const v = $versionList.find((v: any) => v.id === vid);
		return v?.versionNumber || v?.version_number || '';
	}
</script>

<svelte:head>
	<title>工作台 - PM</title>
</svelte:head>

<div class="p-4 md:p-6 max-w-5xl mx-auto">
	<div class="mb-6">
		<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">工作台</h2>
		<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">选择模块开始工作</p>
	</div>

	<!-- Status overview cards -->
	{#if !isLoadingStats}
		<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
			<div class="bg-white dark:bg-gray-850 rounded-2xl border border-gray-100 dark:border-gray-800 p-4">
				<div class="text-xs text-gray-500 dark:text-gray-400 mb-1">草稿</div>
				<div class="text-2xl font-bold text-gray-900 dark:text-gray-100">{statusCounts.draft || 0}</div>
			</div>
			<div class="bg-white dark:bg-gray-850 rounded-2xl border border-gray-100 dark:border-gray-800 p-4">
				<div class="text-xs text-yellow-600 dark:text-yellow-400 mb-1">评审中</div>
				<div class="text-2xl font-bold text-gray-900 dark:text-gray-100">{statusCounts.review || 0}</div>
			</div>
			<div class="bg-white dark:bg-gray-850 rounded-2xl border border-gray-100 dark:border-gray-800 p-4">
				<div class="text-xs text-green-600 dark:text-green-400 mb-1">已批准</div>
				<div class="text-2xl font-bold text-gray-900 dark:text-gray-100">{statusCounts.approved || 0}</div>
			</div>
			<div class="bg-white dark:bg-gray-850 rounded-2xl border border-gray-100 dark:border-gray-800 p-4">
				<div class="text-xs text-gray-400 dark:text-gray-500 mb-1">已归档</div>
				<div class="text-2xl font-bold text-gray-900 dark:text-gray-100">{statusCounts.archived || 0}</div>
			</div>
			<!-- Traceability card -->
			<button class="bg-white dark:bg-gray-850 rounded-2xl border border-gray-100 dark:border-gray-800 p-4 text-left hover:border-purple-200 dark:hover:border-purple-800 transition" onclick={() => goto(`/pm/${projectId}/traceability`)}>
				<div class="text-xs text-purple-600 dark:text-purple-400 mb-1">溯源</div>
				<div class="text-2xl font-bold text-gray-900 dark:text-gray-100">{traceabilityCount}</div>
				<div class="text-xs text-gray-400 mt-0.5">关联关系</div>
			</button>
			<!-- AI Agent status card -->
			<div class="bg-purple-50 dark:bg-purple-900/20 rounded-2xl border border-purple-100 dark:border-purple-800/50 p-4">
				<div class="text-xs text-purple-600 dark:text-purple-400 mb-1">AI 助手</div>
				<div class="flex items-center gap-1.5">
					<div class="w-2 h-2 rounded-full {$agentStatus.available || $hasModels ? 'bg-green-500' : 'bg-gray-400'}"></div>
					<span class="text-sm font-medium text-gray-900 dark:text-gray-100">{$agentStatus.available ? '在线' : $hasModels ? '可用' : '未配置'}</span>
				</div>
				{#if $agentStatus.available}
					<div class="text-xs text-purple-500 mt-0.5">{$agentStatus.model}</div>
				{:else if $hasModels}
					<div class="text-xs text-purple-500 mt-0.5">已连接 OpenWebUI 模型</div>
				{:else}
					<a href="/workspace/models" class="text-xs text-blue-500 hover:text-blue-600 mt-0.5 inline-block">前往配置 →</a>
				{/if}
			</div>
		</div>

		<!-- Version card + Module group totals -->
		<div class="mt-3 grid grid-cols-2 sm:grid-cols-5 gap-3">
			<!-- Current version card -->
			<a href="/pm/{projectId}/versions" class="bg-blue-50 dark:bg-blue-900/20 rounded-2xl border border-blue-100 dark:border-blue-800/50 p-4 block hover:bg-blue-100 dark:hover:bg-blue-900/30 transition">
				<div class="text-xs text-blue-600 dark:text-blue-400 mb-1">当前版本</div>
				<div class="text-2xl font-bold text-blue-700 dark:text-blue-300">{$currentVersion?.versionNumber || '-'}</div>
				{#if $currentVersion?.label}
					<div class="text-xs text-blue-500 mt-0.5">{$currentVersion.label}</div>
				{/if}
				{#if $currentVersion && versionEntryCounts[$currentVersion.id]}
					<div class="text-xs text-blue-400 mt-0.5">{versionEntryCounts[$currentVersion.id]} 条目</div>
				{/if}
				<div class="text-[10px] text-blue-400 mt-1">点击管理版本 →</div>
			</a>
			{#each moduleGroups as group (group.id)}
				<div class="bg-gray-50 dark:bg-gray-800/50 rounded-xl p-3">
					<div class="text-xs text-gray-500 dark:text-gray-400 mb-0.5">{group.label}</div>
					<div class="text-lg font-semibold text-gray-700 dark:text-gray-300">
						{group.modules.reduce((sum, mod) => sum + (moduleCounts[mod.id] || 0), 0)}
						<span class="text-xs font-normal text-gray-400 ml-1">条目</span>
					</div>
				</div>
			{/each}
		</div>
	{/if}

	<!-- Module entry cards -->
	<div class="mt-6 grid gap-6">
		{#each moduleGroups as group (group.id)}
			<div>
				<h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">{group.label}</h3>
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
					{#each group.modules as mod (mod.id)}
						<a
							class="flex items-center gap-3 p-4 bg-white dark:bg-gray-850 rounded-2xl border border-gray-100 dark:border-gray-800 hover:border-gray-200 dark:hover:border-gray-700 hover:shadow-sm transition text-left"
							href={mod.href}
							onclick={(e) => {
								e.preventDefault();
								goto(mod.href);
							}}
						>
							<div class="flex-shrink-0 w-5 h-5 text-gray-500 dark:text-gray-400">
								<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-5">
									<path stroke-linecap="round" stroke-linejoin="round" d={svgIcons[mod.id]} />
								</svg>
							</div>
							<div class="flex-1 min-w-0">
								<span class="text-sm font-medium text-gray-900 dark:text-gray-100 block">{mod.label}</span>
								<span class="text-xs text-gray-500 dark:text-gray-400">{mod.desc}</span>
							</div>
							{#if moduleCounts[mod.id] !== undefined}
								<span class="text-xs font-medium text-gray-400 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded-full flex-shrink-0">{moduleCounts[mod.id]}</span>
							{/if}
						</a>
					{/each}
				</div>
			</div>
		{/each}
	</div>

	<!-- Recent activity -->
	<div class="mt-6">
		<div class="flex items-center justify-between mb-3">
			<h3 class="text-sm font-medium text-gray-700 dark:text-gray-300">最近更新</h3>
			<span class="text-xs text-gray-400">{filteredRecent.length} 条</span>
		</div>

		<!-- Search & Filters -->
		<div class="mb-3 flex flex-col sm:flex-row gap-2">
			<div class="relative flex-1">
				<svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
				</svg>
				<input
					type="text"
					placeholder="搜索标题..."
					class="w-full pl-9 pr-3 py-1.5 text-sm bg-white dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-gray-100"
					bind:value={searchQuery}
				/>
			</div>
			<select
				class="px-3 py-1.5 text-sm bg-white dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-gray-100"
				bind:value={filterModuleType}
			>
				<option value="all">全部模块</option>
				{#each allModules as mod}
					<option value={mod.id}>{mod.label}</option>
				{/each}
			</select>
			<select
				class="px-3 py-1.5 text-sm bg-white dark:bg-gray-850 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-gray-100"
				bind:value={filterStatus}
			>
				<option value="all">全部状态</option>
				<option value="draft">草稿</option>
				<option value="review">评审中</option>
				<option value="approved">已批准</option>
				<option value="archived">已归档</option>
			</select>
		</div>

		{#if isLoadingRecent}
			<div class="flex items-center justify-center py-8"><div class="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-400"></div></div>
		{:else if filteredRecent.length === 0}
			<div class="py-8 text-center text-sm text-gray-400">暂无内容</div>
		{:else}
			<div class="bg-white dark:bg-gray-850 rounded-2xl border border-gray-100 dark:border-gray-800 divide-y divide-gray-50 dark:divide-gray-800">
				{#each pagedRecentItems as item (item.id)}
					<a
						class="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition text-left"
						href={getModuleHref(item.module_type || item.moduleType)}
					>
						<div class="flex-shrink-0 w-4 h-4 text-gray-400 dark:text-gray-500">
							<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-4">
								<path stroke-linecap="round" stroke-linejoin="round" d={svgIcons[item.module_type || item.moduleType] || svgIcons.prd} />
							</svg>
						</div>
						<div class="flex-1 min-w-0">
							<div class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{item.title}</div>
							<span class="text-xs text-gray-400">{getModuleLabel(item.module_type || item.moduleType)}</span>
						</div>
						{#if item.versionId || (item.data || item.metadata || {}).versionId}
							<span class="px-1.5 py-0.5 rounded text-[10px] bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400 flex-shrink-0">{getVersionLabel(item.versionId || (item.data || item.metadata || {}).versionId)}</span>
						{/if}
						<span class="text-xs text-gray-400 flex-shrink-0 whitespace-nowrap">{formatTime(item.updated_at || item.updatedAt)}</span>
					</a>
				{/each}
			</div>

			<!-- Pagination -->
			{#if totalPages >= 1}
				<div class="flex items-center justify-between mt-3 px-1">
					<button
						class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-850 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition"
						disabled={currentPage <= 1}
						onclick={() => currentPage--}
					>
						上一页
					</button>
					<span class="text-sm text-gray-500 dark:text-gray-400">{currentPage} / {totalPages}</span>
					<button
						class="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-850 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition"
						disabled={currentPage >= totalPages}
						onclick={() => currentPage++}
					>
						下一页
					</button>
				</div>
			{/if}
		{/if}
	</div>
</div>
