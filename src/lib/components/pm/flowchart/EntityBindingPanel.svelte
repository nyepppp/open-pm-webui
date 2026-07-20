<script lang="ts">
	import { onMount } from 'svelte';
	import { getEntries } from '$lib/apis/pm/index';
	import { createRelation, deleteRelation, getRelationList } from '$lib/apis/pm/relation';
	import { toast } from 'svelte-sonner';

	interface Binding {
		entityType: string;
		entityId: string;
		entityName: string;
		versionId?: string;
		versionNumber?: string;
		boundAt?: number;
		boundBy?: string;
	}

	interface Props {
		projectId: string;
		entryId?: string;
		currentBinding?: Binding;
		onBind: (binding: Binding) => void;
		onUnbind: () => void;
	}

	let { projectId, entryId = '', currentBinding, onBind, onUnbind }: Props = $props();

	let selectedType = $state(currentBinding?.entityType || '');
	let selectedEntity = $state<Binding | null>(currentBinding || null);
	let searchQuery = $state('');
	let entities = $state<any[]>([]);
	let loading = $state(false);
	let bindingRelationId = $state<string | null>(null);
	let binding = $state<Binding | undefined>(currentBinding);

	const entityTypes = [
		{ value: 'prd', label: 'PRD', module: 'prd' },
		{ value: 'module', label: '模块', module: 'product-architecture' },
		{ value: 'feature', label: '功能', module: 'requirement' },
		{ value: 'parameter', label: '参数', module: 'parameter' }
	];

	const typeLabel = (t: string) => entityTypes.find(x => x.value === t)?.label || t;

	async function loadEntities() {
		if (!selectedType) return;
		loading = true;
		entities = [];
		const typeConfig = entityTypes.find(t => t.value === selectedType);
		try {
			if (!typeConfig) {
				toast.error(`未知的实体类型: ${selectedType}`);
				return;
			}
			const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
			if (!token) {
				toast.error('请先登录');
				return;
			}
			if (!projectId) {
				toast.error('未选择项目');
				return;
			}
			const result = await getEntries(token, projectId, typeConfig.module);
			if (!Array.isArray(result)) {
				console.error('API返回非数组数据:', result);
				toast.error('加载实体失败: 服务器返回数据格式错误');
				return;
			}
			entities = result;
		} catch (e: any) {
			console.error('加载实体失败:', e);
			const message = e?.message || '未知错误';
			if (message.includes('404')) {
				toast.error(`模块 "${typeConfig?.label || selectedType}" 暂无数据`);
			} else if (message.includes('403')) {
				toast.error('权限不足，无法访问该模块');
			} else if (message.includes('Failed to fetch') || message.includes('NetworkError')) {
				toast.error('网络错误，请检查网络连接');
			} else {
				toast.error(`加载实体失败: ${message}`);
			}
		} finally {
			loading = false;
		}
	}

	function handleTypeChange(type: string) {
		selectedType = type;
		selectedEntity = null;
		loadEntities();
	}

	function handleEntitySelect(entity: any) {
		selectedEntity = {
			entityType: selectedType,
			entityId: entity.id,
			entityName: entity.title || entity.name || '未命名',
			versionId: entity.versionId || entity.currentVersionId
		};
	}

	async function handleBind() {
		if (!selectedEntity) return;
		onBind(selectedEntity);
		binding = { ...selectedEntity, boundAt: Date.now() };
		toast.success(`已绑定到 ${selectedEntity.entityName}`);
		// Backend: create relation so binding appears on the traceability page (best-effort, local-first)
		if (entryId && projectId) {
			try {
				const created = await createRelation(projectId, {
					entityAId: entryId,
					entityBId: selectedEntity.entityId,
					relationType: 'references',
					confidence: 100,
					confirmed: 1,
					createdBy: 'user'
				} as any);
				bindingRelationId = created?.id || null;
			} catch (e: any) {
				console.warn('[EntityBindingPanel] createRelation failed:', e?.message);
			}
		}
	}

	async function handleUnbindClick() {
		// Backend: delete the relation (best-effort)
		if (projectId && entryId) {
			try {
				if (bindingRelationId) {
					await deleteRelation(projectId, bindingRelationId);
				} else {
					const relations = await getRelationList(projectId, entryId);
					const rel = relations.find(r => r.relationType === 'references');
					if (rel) await deleteRelation(projectId, rel.id);
				}
			} catch (e: any) {
				console.warn('[EntityBindingPanel] deleteRelation failed:', e?.message);
			}
		}
		bindingRelationId = null;
		binding = undefined;
		onUnbind();
		toast.success('已解绑');
	}

	onMount(() => {
		// Auto-load entities if a binding already exists, so the panel shows context immediately
		if (currentBinding?.entityType) {
			selectedType = currentBinding.entityType;
			loadEntities();
		}
	});

	let filteredEntities = $derived(
		entities.filter(e => {
			const query = searchQuery.toLowerCase();
			return (e.title || e.name || '').toLowerCase().includes(query);
		})
	);
</script>

<div class="space-y-4">
	<!-- Bound summary card (when a binding exists) -->
	{#if binding}
		<div class="rounded-lg border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20 p-3">
			<div class="flex items-center justify-between mb-1">
				<span class="text-xs font-medium text-green-700 dark:text-green-300">已绑定</span>
				<button
					class="text-xs text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
					onclick={handleUnbindClick}
				>
					解绑
				</button>
			</div>
			<div class="text-sm font-medium text-gray-900 dark:text-gray-100">{binding.entityName}</div>
			<div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
				类型: {typeLabel(binding.entityType)}
				{#if binding.versionId}· 版本: {binding.versionId}{/if}
				{#if binding.boundAt}· 绑定于 {new Date(binding.boundAt).toLocaleString('zh-CN')}{/if}
			</div>
		</div>
	{/if}

	<!-- Instruction (only when no binding) -->
	{#if !binding}
		<p class="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
			选择要绑定的实体类型，然后从列表中选择实体并点击「绑定实体」。绑定后可在溯源页面查看关联关系。
		</p>
	{/if}

	<!-- Entity Type Selection -->
	<div>
		<label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">实体类型</label>
		<div class="grid grid-cols-2 gap-2">
			{#each entityTypes as type}
				<button
					class="px-3 py-2 text-xs rounded-lg border transition text-left {selectedType === type.value ? 'bg-blue-50 border-blue-300 text-blue-700 dark:bg-blue-900/20 dark:border-blue-700 dark:text-blue-300' : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300'}"
					onclick={() => handleTypeChange(type.value)}
				>
					{type.label}
				</button>
			{/each}
		</div>
	</div>

	<!-- Search -->
	{#if selectedType}
		<div>
			<label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">搜索实体</label>
			<input
				type="text"
				class="w-full px-3 py-2 text-sm border border-gray-200 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 outline-none focus:ring-1 focus:ring-blue-400"
				placeholder="输入关键词搜索..."
				bind:value={searchQuery}
			/>
		</div>

		<!-- Entity List -->
		<div class="max-h-48 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg">
			{#if loading}
				<div class="flex items-center justify-center py-4">
					<div class="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-400"></div>
				</div>
			{:else if filteredEntities.length === 0}
				<div class="text-center py-4 text-sm text-gray-500 dark:text-gray-400">
					暂无实体数据
				</div>
			{:else}
				<div class="divide-y divide-gray-100 dark:divide-gray-700">
					{#each filteredEntities as entity}
						<button
							class="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-700/50 transition {selectedEntity?.entityId === entity.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''}"
							onclick={() => handleEntitySelect(entity)}
						>
							<div class="font-medium text-gray-900 dark:text-gray-100">
								{entity.title || entity.name || '未命名'}
								{#if entity.currentVersionNumber || entity.version}
									<span class="text-xs text-gray-500 dark:text-gray-400 ml-1">(v{entity.currentVersionNumber || entity.version})</span>
								{/if}
							</div>
							{#if entity.description}
								<div class="text-xs text-gray-500 dark:text-gray-400 truncate">{entity.description}</div>
							{/if}
						</button>
					{/each}
				</div>
			{/if}
		</div>
	{/if}

	<!-- Actions -->
	<div class="flex gap-2 pt-2">
		<button
			class="flex-1 px-3 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
			disabled={!selectedEntity}
			onclick={handleBind}
		>
			绑定实体
		</button>
	</div>
</div>
