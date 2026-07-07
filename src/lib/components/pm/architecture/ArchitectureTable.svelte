<script lang="ts">
	import type { ArchModule, ArchFeature, ArchParameter } from '$lib/stores/pm/architectureStore';
	import EditItemModal from './EditItemModal.svelte';

	interface Props {
		modules: ArchModule[];
		onUpdate?: (modules: ArchModule[]) => void;
		onEdit?: (type: 'module' | 'feature' | 'parameter', data: any) => void;
		onDelete?: (type: 'module' | 'feature' | 'parameter', id: string) => void;
		onAdd?: (type: 'module' | 'feature' | 'parameter', parentId?: string) => void;
	}

	let { modules = [], onUpdate, onEdit, onDelete, onAdd }: Props = $props();

	let searchQuery = $state('');
	let showEditModal = $state(false);
	let editType = $state<'module' | 'feature' | 'parameter'>('module');
	let editData = $state<Record<string, any>>({});
	let editingItemId = $state<string>('');
	let highlightedItemId = $state<string>('');

	function toggleModule(module: ArchModule) {
		module.expanded = !module.expanded;
		modules = [...modules];
	}

	function toggleFeature(feature: ArchFeature) {
		feature.expanded = !feature.expanded;
		modules = [...modules];
	}

	function filteredModules(): ArchModule[] {
		if (!searchQuery.trim()) return modules;
		const query = searchQuery.toLowerCase();
		return modules.filter((mod: ArchModule) => 
			mod.name.toLowerCase().includes(query) ||
			mod.features.some((feat: ArchFeature) => 
				feat.name.toLowerCase().includes(query) ||
				feat.parameters.some((param: ArchParameter) => param.name.toLowerCase().includes(query))
			)
		);
	}

	function handleAddModule() {
		editType = 'module';
		editData = {};
		editingItemId = '';
		showEditModal = true;
	}

	function handleAddFeature(moduleId: string) {
		editType = 'feature';
		editData = {};
		editingItemId = moduleId;
		showEditModal = true;
	}

	function handleAddParameter(featureId: string) {
		editType = 'parameter';
		editData = {};
		editingItemId = featureId;
		showEditModal = true;
	}

	function handleEdit(type: 'module' | 'feature' | 'parameter', data: any) {
		editType = type;
		editData = { ...data };
		editingItemId = data.id || '';
		showEditModal = true;
	}

	function handleEditSubmit(formData: any) {
		showEditModal = false;
		
		if (editingItemId) {
			// Update existing item
			onEdit?.(editType, { ...formData, id: editingItemId });
		} else {
			// Add new item
			onAdd?.(editType, editingItemId || undefined);
		}
	}

	function handleDelete(type: 'module' | 'feature' | 'parameter', id: string) {
		onDelete?.(type, id);
	}

	function getParamTypeLabel(type: string): string {
		const labels: Record<string, string> = {
			input: '输入',
			output: '输出',
			config: '配置'
		};
		return labels[type] || type;
	}

	function getParamTypeColor(type: string): string {
		const colors: Record<string, string> = {
			input: 'bg-blue-100 text-blue-700',
			output: 'bg-green-100 text-green-700',
			config: 'bg-yellow-100 text-yellow-700'
		};
		return colors[type] || 'bg-gray-100 text-gray-700';
	}

	// Handle highlight from mindmap click
	export function highlightItem(itemId: string) {
		highlightedItemId = itemId;
		// Scroll to the item
		setTimeout(() => {
			const element = document.getElementById(`arch-item-${itemId}`);
			if (element) {
				element.scrollIntoView({ behavior: 'smooth', block: 'center' });
			}
			// Remove highlight after 3 seconds
			setTimeout(() => {
				highlightedItemId = '';
			}, 3000);
		}, 100);
	}
</script>

<div class="w-full h-full flex flex-col">
	<!-- Search bar -->
	<div class="flex items-center gap-2 mb-4">
		<div class="flex-1 relative">
			<input
				type="text"
				placeholder="搜索模块、功能或参数..."
				class="w-full px-4 py-2 pl-10 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
				bind:value={searchQuery}
			/>
			<svg class="w-5 h-5 text-gray-400 absolute left-3 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
			</svg>
		</div>
		<button
			class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition flex items-center gap-2"
			onclick={handleAddModule}
		>
			<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
			</svg>
			新增模块
		</button>
	</div>

	<!-- Table -->
	<div class="flex-1 overflow-auto border border-gray-200 dark:border-gray-700 rounded-2xl">
		<table class="w-full">
			<thead class="bg-gray-50 dark:bg-gray-800 sticky top-0">
				<tr>
					<th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider w-1/3">名称</th>
					<th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">类型/Key</th>
					<th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">数据类型</th>
					<th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">必填</th>
					<th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">描述</th>
					<th class="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">操作</th>
				</tr>
			</thead>
			<tbody class="divide-y divide-gray-100 dark:divide-gray-700">
				{#each filteredModules() as module (module.id)}
					<!-- Module Row -->
					<tr 
						id={`arch-item-${module.id}`}
						class="bg-blue-50/50 dark:bg-blue-900/20 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors {highlightedItemId === module.id ? 'ring-2 ring-yellow-400' : ''}"
					>
						<td class="px-4 py-3">
							<div class="flex items-center gap-2">
								<button class="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition" onclick={() => toggleModule(module)} aria-label={module.expanded ? '收起模块' : '展开模块'}>
									<svg class="w-4 h-4 text-gray-500 transition-transform {module.expanded ? 'rotate-90' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
									</svg>
								</button>
								<span class="font-semibold text-gray-900 dark:text-gray-100">{module.name}</span>
								<span class="text-xs text-gray-500">({module.features.length} 功能)</span>
							</div>
						</td>
						<td class="px-4 py-3">
							<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">模块</span>
						</td>
						<td class="px-4 py-3"></td>
						<td class="px-4 py-3"></td>
						<td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{module.description || ''}</td>
						<td class="px-4 py-3 text-right">
							<div class="flex items-center justify-end gap-1">
								<button class="p-1.5 text-blue-600 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-lg transition" title="编辑" onclick={() => handleEdit('module', module)}>
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
									</svg>
								</button>
								<button class="p-1.5 text-blue-600 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-lg transition" title="添加功能" onclick={() => handleAddFeature(module.id)}>
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
									</svg>
								</button>
								<button class="p-1.5 text-red-600 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition" title="删除" onclick={() => handleDelete('module', module.id)}>
									<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.818L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
									</svg>
								</button>
							</div>
						</td>
					</tr>

					<!-- Feature Rows -->
					{#if module.expanded}
						{#each module.features as feature (feature.id)}
							<tr 
								id={`arch-item-${feature.id}`}
								class="bg-green-50/30 dark:bg-green-900/10 hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors {highlightedItemId === feature.id ? 'ring-2 ring-yellow-400' : ''}"
							>
								<td class="px-4 py-3 pl-12">
									<div class="flex items-center gap-2">
										<button class="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition" onclick={() => toggleFeature(feature)} aria-label={feature.expanded ? '收起功能' : '展开功能'}>
											<svg class="w-4 h-4 text-gray-500 transition-transform {feature.expanded ? 'rotate-90' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
											</svg>
										</button>
										<span class="font-medium text-gray-800 dark:text-gray-200">{feature.name}</span>
										<span class="text-xs text-gray-500">({feature.parameters.length} 参数)</span>
									</div>
								</td>
								<td class="px-4 py-3">
									<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700">功能</span>
								</td>
								<td class="px-4 py-3"></td>
								<td class="px-4 py-3"></td>
								<td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{feature.description || ''}</td>
								<td class="px-4 py-3 text-right">
									<div class="flex items-center justify-end gap-1">
										<button class="p-1.5 text-blue-600 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-lg transition" title="编辑" onclick={() => handleEdit('feature', feature)}>
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
											</svg>
										</button>
										<button class="p-1.5 text-green-600 hover:bg-green-100 dark:hover:bg-green-900/30 rounded-lg transition" title="添加参数" onclick={() => handleAddParameter(feature.id)}>
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
											</svg>
										</button>
										<button class="p-1.5 text-red-600 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition" title="删除" onclick={() => handleDelete('feature', feature.id)}>
											<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.818L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
											</svg>
										</button>
									</div>
								</td>
							</tr>

							<!-- Parameter Rows -->
							{#if feature.expanded}
								{#each feature.parameters as param (param.id)}
									<tr 
										id={`arch-item-${param.id}`}
										class="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors {highlightedItemId === param.id ? 'ring-2 ring-yellow-400' : ''}"
									>
										<td class="px-4 py-3 pl-20">
											<span class="text-gray-700 dark:text-gray-300">{param.name}</span>
										</td>
										<td class="px-4 py-3">
											<div class="flex items-center gap-2">
												<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium {getParamTypeColor(param.type)}">
													{getParamTypeLabel(param.type)}
												</span>
												<code class="text-xs text-gray-500">{param.key}</code>
											</div>
										</td>
										<td class="px-4 py-3">
											<span class="text-xs text-gray-500">{param.dataType}</span>
										</td>
										<td class="px-4 py-3">
											{#if param.required}
												<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700">必填</span>
											{:else}
												<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-500">可选</span>
											{/if}
										</td>
										<td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{param.description || ''}</td>
										<td class="px-4 py-3 text-right">
											<div class="flex items-center justify-end gap-1">
												<button class="p-1.5 text-blue-600 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-lg transition" title="编辑" onclick={() => handleEdit('parameter', param)}>
													<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
													</svg>
												</button>
												<button class="p-1.5 text-red-600 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition" title="删除" onclick={() => handleDelete('parameter', param.id)}>
													<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.818L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
													</svg>
												</button>
											</div>
										</td>
									</tr>
								{/each}
							{/if}
						{/each}
					{/if}
				{/each}
			</tbody>
		</table>
	</div>

	<!-- Edit Modal -->
	<EditItemModal
		show={showEditModal}
		type={editType}
		data={editData}
		onClose={() => { showEditModal = false; }}
		onSubmit={handleEditSubmit}
	/>
</div>