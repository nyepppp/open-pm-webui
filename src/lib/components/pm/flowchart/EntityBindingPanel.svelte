<script lang="ts">
	import { getEntries } from '$lib/apis/pm/index';
	import { toast } from 'svelte-sonner';

	interface Props {
		projectId: string;
		currentBinding?: {
			entityType: string;
			entityId: string;
			entityName: string;
			versionId?: string;
		};
		onBind: (binding: {
			entityType: string;
			entityId: string;
			entityName: string;
			versionId?: string;
		}) => void;
		onUnbind: () => void;
	}

	let { projectId, currentBinding, onBind, onUnbind }: Props = $props();

	let selectedType = $state(currentBinding?.entityType || '');
	let selectedEntity = $state(currentBinding || null);
	let searchQuery = $state('');
	let entities = $state<any[]>([]);
	let loading = $state(false);

	const entityTypes = [
		{ value: 'prd', label: 'PRD', module: 'prd' },
		{ value: 'module', label: '模块', module: 'architecture' },
		{ value: 'feature', label: '功能', module: 'requirement' },
		{ value: 'parameter', label: '参数', module: 'parameter' }
	];

	async function loadEntities() {
		if (!selectedType) return;
		loading = true;
		try {
			const typeConfig = entityTypes.find(t => t.value === selectedType);
			if (!typeConfig) return;
			const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
			const result = await getEntries(token, projectId, typeConfig.module);
			entities = Array.isArray(result) ? result : [];
		} catch (e) {
			toast.error('加载实体失败');
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
			entityName: entity.title || entity.name || '未命名'
		};
	}

	function handleBind() {
		if (!selectedEntity) return;
		onBind(selectedEntity);
	}

	let filteredEntities = $derived(
		entities.filter(e => {
			const query = searchQuery.toLowerCase();
			return (e.title || e.name || '').toLowerCase().includes(query);
		})
	);
</script>

<div class="space-y-4">
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
		{#if currentBinding}
			<button
				class="px-3 py-2 text-sm bg-red-50 hover:bg-red-100 text-red-600 dark:bg-red-900/20 dark:hover:bg-red-900/30 dark:text-red-400 rounded-lg transition"
				onclick={onUnbind}
			>
				解绑
			</button>
		{/if}
	</div>
</div>
