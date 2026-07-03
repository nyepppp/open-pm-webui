<script lang="ts">
	import { getEntry } from '$lib/apis/pm/index';
	import { getRelationList, deleteRelation } from '$lib/apis/pm/relation';
	import { toast } from 'svelte-sonner';
	import type { RelationType } from '$lib/apis/pm/types';

	interface Props {
		projectId: string;
		entityId: string;
		entityName: string;
		entityType: string;
		onClose?: () => void;
		onNavigate?: (moduleType: string, entryId: string) => void;
		onRelationDeleted?: (relationId: string) => void;
	}

	let { projectId, entityId, entityName, entityType, onClose, onNavigate, onRelationDeleted }: Props = $props();

	let loading = $state(true);
	let entryData = $state<any>(null);
	let relations = $state<any[]>([]);

	const moduleTypeMap: Record<string, string> = {
		prd: 'PRD 文档', requirement: '需求', parameter: '参数', testcase: '测试用例',
		risk: '风险', competitor: '竞品', roadmap: '路线图', meeting: '会议',
		acceptance: '验收', faq: 'FAQ', 'product-architecture': '产品架构',
		prototype: '原型', schedule: '排期'
	};

	const relationTypeLabels: Record<string, string> = {
		contains: '包含', references: '引用', derives: '派生', modifies: '修改', conflicts: '冲突'
	};

	$effect(() => {
		loadDetails();
	});

	async function loadDetails() {
		loading = true;
		try {
			const token = localStorage.token || '';
			entryData = await getEntry(token, entityId);
			relations = await getRelationList(projectId, entityId) || [];
		} catch (e: any) {
			console.warn('[PMTraceDetailPanel] load failed:', e?.message);
		} finally {
			loading = false;
		}
	}

	async function handleDeleteRelation(relId: string) {
		try {
			await deleteRelation(projectId, relId);
			relations = relations.filter(r => r.id !== relId);
			onRelationDeleted?.(relId);
			toast.success('关联已删除');
		} catch (e: any) {
			toast.error(e?.message || '删除关联失败');
		}
	}

	function handleNavigate() {
		if (entryData?.moduleType) {
			onNavigate?.(entryData.moduleType, entityId);
		}
	}
</script>

<div class="w-80 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col h-full overflow-hidden">
	<div class="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between bg-gray-50 dark:bg-gray-850">
		<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">{entityName}</h3>
		<button class="p-1 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition" onclick={onClose}>
			<svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
		</button>
	</div>

	<div class="flex-1 overflow-y-auto">
		{#if loading}
			<div class="flex items-center justify-center py-12">
				<div class="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
			</div>
		{:else if entryData}
			<!-- Entity info -->
			<div class="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
				<div class="flex items-center gap-2 mb-2">
					<span class="px-2 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">{moduleTypeMap[entryData.moduleType] || entityType}</span>
					<span class="px-2 py-0.5 text-xs rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">{entryData.status || '草稿'}</span>
				</div>
				{#if entryData.content}
					<p class="text-xs text-gray-500 dark:text-gray-400 line-clamp-3">{entryData.content}</p>
				{/if}
				<button
					class="mt-2 px-3 py-1.5 text-xs bg-black text-white dark:bg-white dark:text-black rounded-lg transition hover:opacity-80"
					onclick={handleNavigate}
				>
					打开编辑
				</button>
			</div>

			<!-- Relations -->
			<div class="px-4 py-3">
				<h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-2">关联关系 ({relations.length})</h4>
				{#if relations.length === 0}
					<p class="text-xs text-gray-400">暂无关联关系</p>
				{:else}
					<div class="space-y-1.5">
						{#each relations as rel (rel.id)}
							<div class="flex items-center justify-between px-2 py-1.5 bg-gray-50 dark:bg-gray-850 rounded-lg">
								<div class="flex items-center gap-1.5 min-w-0">
									<span class="px-1.5 py-0.5 text-[10px] rounded {rel.relationType === 'conflicts' ? 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400' : rel.relationType === 'derives' ? 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400' : 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400'}">
										{relationTypeLabels[rel.relationType] || rel.relationType}
									</span>
									<span class="text-[10px] text-gray-500 truncate">{rel.entityAId === entityId ? rel.entityBId?.slice(0, 8) : rel.entityAId?.slice(0, 8)}...</span>
								</div>
								<button
									class="p-0.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20 transition shrink-0"
									onclick={() => handleDeleteRelation(rel.id)}
									title="删除关联"
								>
									<svg class="w-3 h-3 text-gray-400 hover:text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
								</button>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{:else}
			<div class="px-4 py-6 text-center text-xs text-gray-400">加载失败</div>
		{/if}
	</div>
</div>
