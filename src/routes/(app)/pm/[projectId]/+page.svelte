<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import dayjs from '$lib/dayjs';
	import { getEntries } from '$lib/apis/pm/index';

	let projectId = $derived($page.params.projectId);

	const moduleGroups = [
		{
			id: 'plan', label: '🗺️ 规划', modules: [
				{ id: 'prd', label: 'PRD 文档', desc: '产品需求文档', href: `/pm/${projectId}/prd`, icon: '📄' },
				{ id: 'requirement', label: '需求管理', desc: '需求收集与分析', href: `/pm/${projectId}/requirement`, icon: '📋' },
				{ id: 'roadmap', label: '产品路线图', desc: '版本规划', href: `/pm/${projectId}/roadmap`, icon: '🗺️' }
			]
		},
		{
			id: 'design', label: '🎨 设计', modules: [
				{ id: 'parameter', label: '参数配置', desc: '参数清单管理', href: `/pm/${projectId}/parameter`, icon: '⚙️' },
				{ id: 'product-architecture', label: '产品架构', desc: '架构设计', href: `/pm/${projectId}/product-architecture`, icon: '🏗️' },
				{ id: 'competitor', label: '竞品分析', desc: '竞品对比矩阵', href: `/pm/${projectId}/competitor`, icon: '🔍' }
			]
		},
		{
			id: 'execute', label: '⚡ 执行', modules: [
				{ id: 'testcase', label: '测试用例', desc: '用例管理', href: `/pm/${projectId}/testcase`, icon: '🧪' },
				{ id: 'risk', label: '风险分析', desc: '风险管控', href: `/pm/${projectId}/risk`, icon: '⚠️' },
				{ id: 'meeting', label: '会议纪要', desc: '评审记录', href: `/pm/${projectId}/meeting`, icon: '📝' }
			]
		},
		{
			id: 'review', label: '📊 复盘', modules: [
				{ id: 'acceptance', label: '验收报告', desc: '验收检查', href: `/pm/${projectId}/acceptance`, icon: '✅' },
				{ id: 'faq', label: 'FAQ', desc: '常见问题', href: `/pm/${projectId}/faq`, icon: '❓' }
			]
		}
	];

	const allModules = moduleGroups.flatMap(g => g.modules);

	// Kanban stats
	let moduleCounts = $state<Record<string, number>>({});
	let isLoadingStats = $state(true);

	// Recent activity
	let recentItems = $state<any[]>([]);
	let isLoadingRecent = $state(true);

	async function loadDashboardData() {
		const token = localStorage.token || '';
		isLoadingStats = true;
		isLoadingRecent = true;
		try {
			const allEntries = await getEntries(token, projectId);
			// Count per module
			const counts: Record<string, number> = {};
			for (const mod of allModules) {
				counts[mod.id] = 0;
			}
			for (const entry of allEntries) {
				const mt = entry.module_type || entry.moduleType || '';
				if (counts[mt] !== undefined) counts[mt]++;
				else counts[mt] = 1;
			}
			moduleCounts = counts;
			// Recent items — sort by updatedAt desc, take 20
			const sorted = [...allEntries].sort((a: any, b: any) => {
				const ta = a.updated_at || a.updatedAt || 0;
				const tb = b.updated_at || b.updatedAt || 0;
				return tb - ta;
			});
			recentItems = sorted.slice(0, 20);
		} catch {
			moduleCounts = {};
			recentItems = [];
		} finally {
			isLoadingStats = false;
			isLoadingRecent = false;
		}
	}

	onMount(() => { loadDashboardData(); });

	function formatTime(ts: number): string {
		try { return dayjs(ts / 1_000_000).fromNow(); } catch { return ''; }
	}

	function getModuleLabel(moduleType: string): string {
		return allModules.find(m => m.id === moduleType)?.label || moduleType;
	}

	function getModuleIcon(moduleType: string): string {
		return allModules.find(m => m.id === moduleType)?.icon || '📌';
	}

	function getModuleHref(moduleType: string): string {
		return allModules.find(m => m.id === moduleType)?.href || `/pm/${projectId}/${moduleType}`;
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

	<!-- Module entry cards -->
	<div class="grid gap-6">
		{#each moduleGroups as group (group.id)}
			<div>
				<h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">{group.label}</h3>
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
					{#each group.modules as mod (mod.id)}
						<button
							class="flex items-center gap-3 p-4 bg-white dark:bg-gray-850 rounded-2xl border border-gray-100 dark:border-gray-800 hover:border-gray-200 dark:hover:border-gray-700 hover:shadow-sm transition text-left"
							onclick={() => goto(mod.href)}
						>
							<span class="text-xl flex-shrink-0">{mod.icon}</span>
							<div class="flex-1 min-w-0">
								<span class="text-sm font-medium text-gray-900 dark:text-gray-100 block">{mod.label}</span>
								<span class="text-xs text-gray-500 dark:text-gray-400">{mod.desc}</span>
							</div>
							{#if moduleCounts[mod.id] !== undefined}
								<span class="text-xs font-medium text-gray-400 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded-full flex-shrink-0">{moduleCounts[mod.id]}</span>
							{/if}
						</button>
					{/each}
				</div>
			</div>
		{/each}
	</div>

	<!-- Kanban stats row -->
	{#if !isLoadingStats}
		<div class="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-3">
			{#each moduleGroups as group (group.id)}
				<div class="bg-white dark:bg-gray-850 rounded-2xl border border-gray-100 dark:border-gray-800 p-4">
					<div class="text-xs text-gray-500 dark:text-gray-400 mb-1">{group.label}</div>
					<div class="text-2xl font-bold text-gray-900 dark:text-gray-100">
						{group.modules.reduce((sum, mod) => sum + (moduleCounts[mod.id] || 0), 0)}
					</div>
					<div class="text-xs text-gray-400 mt-1">{group.modules.length} 个模块</div>
				</div>
			{/each}
		</div>
	{/if}

	<!-- Recent activity -->
	<div class="mt-6">
		<h3 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">最近更新</h3>
		{#if isLoadingRecent}
			<div class="flex items-center justify-center py-8"><div class="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-400"></div></div>
		{:else if recentItems.length === 0}
			<div class="py-8 text-center text-sm text-gray-400">暂无内容</div>
		{:else}
			<div class="bg-white dark:bg-gray-850 rounded-2xl border border-gray-100 dark:border-gray-800 divide-y divide-gray-50 dark:divide-gray-800">
				{#each recentItems as item (item.id)}
					<button
						class="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition text-left"
						onclick={() => goto(getModuleHref(item.module_type || item.moduleType))}
					>
						<span class="text-base flex-shrink-0">{getModuleIcon(item.module_type || item.moduleType)}</span>
						<div class="flex-1 min-w-0">
							<div class="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{item.title}</div>
							<div class="text-xs text-gray-400">{getModuleLabel(item.module_type || item.moduleType)}</div>
						</div>
						<span class="text-xs text-gray-400 flex-shrink-0 whitespace-nowrap">{formatTime(item.updated_at || item.updatedAt)}</span>
					</button>
				{/each}
			</div>
		{/if}
	</div>
</div>
