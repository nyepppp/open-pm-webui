<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { updateEntry } from '$lib/apis/pm/index';
	import type { TreeModule } from '$lib/stores/pm/architectureStore';

	// Props for architecture entries (to get descriptions)
	interface Props {
		modules: TreeModule[];
		projectId: string;
		selectedModule: string | null;
		selectedFeature: string | null;
		archEntries: any[];
		onSelect: (module: string, feature?: string) => void;
		onAddModule: (name: string) => void;
		onAddFeature: (moduleName: string, featureName: string) => void;
		onDeleteModule: (name: string) => void;
		onDeleteFeature: (moduleName: string, featureName: string) => void;
		onDataChange: () => void;
	}

	let {
		modules = [],
		projectId = '',
		selectedModule = null,
		selectedFeature = null,
		archEntries = [],
		onSelect,
		onAddModule,
		onAddFeature,
		onDeleteModule,
		onDeleteFeature,
		onDataChange
	}: Props = $props();

	let expandedModules = $state<Set<string>>(new Set());
	let showAddModuleForm = $state(false);
	let showAddFeatureForm = $state(false);
	let newModuleName = $state('');
	let newFeatureName = $state('');
	let selectedModuleForFeature = $state('');
	let editingModule = $state<string | null>(null);
	let editingFeature = $state<string | null>(null);
	let editDescription = $state('');

	// Module descriptions loaded from archEntries
	let moduleDescriptions = $state<Map<string, string>>(new Map());
	let featureDescriptions = $state<Map<string, string>>(new Map());

	// Load descriptions from archEntries
	$effect(() => {
		const newModuleDesc = new Map<string, string>();
		const newFeatureDesc = new Map<string, string>();
		
		for (const entry of archEntries) {
			const data = entry.data || {};
			const nodes = data.nodes as any[] || [];
			
			for (const node of nodes) {
				if (node.type === 'branch') {
					// Module description
					const desc = node.metadata?.description || '';
					if (desc) {
						newModuleDesc.set(node.label, desc);
					}
				} else if (node.type === 'leaf' && node.parentId) {
					// Feature description
					const parent = nodes.find((n: any) => n.id === node.parentId);
					if (parent) {
						const desc = node.metadata?.description || '';
						if (desc) {
							newFeatureDesc.set(`${parent.label}::${node.label}`, desc);
						}
					}
				}
			}
		}
		
		moduleDescriptions = newModuleDesc;
		featureDescriptions = newFeatureDesc;
	});

	function toggleModule(moduleName: string) {
		const newExpanded = new Set(expandedModules);
		if (newExpanded.has(moduleName)) {
			newExpanded.delete(moduleName);
		} else {
			newExpanded.add(moduleName);
		}
		expandedModules = newExpanded;
	}

	function handleAddModule() {
		if (!newModuleName.trim()) return;
		onAddModule(newModuleName.trim());
		newModuleName = '';
		showAddModuleForm = false;
	}

	function handleAddFeature() {
		if (!newFeatureName.trim() || !selectedModuleForFeature) return;
		onAddFeature(selectedModuleForFeature, newFeatureName.trim());
		newFeatureName = '';
		showAddFeatureForm = false;
	}

	function startEditModule(moduleName: string) {
		editingModule = moduleName;
		editDescription = moduleDescriptions.get(moduleName) || '';
	}

	function startEditFeature(moduleName: string, featureName: string) {
		editingFeature = `${moduleName}::${featureName}`;
		editDescription = featureDescriptions.get(`${moduleName}::${featureName}`) || '';
	}

	async function saveModuleDescription(moduleName: string) {
		try {
			const token = localStorage.token || '';
			// Find the architecture entry and update the node description
			const entry = archEntries[0];
			if (entry) {
				const data = entry.data || {};
				const nodes = (data.nodes as any[]) || [];
				
				// Find the module node and update its description
				const updatedNodes = nodes.map((node: any) => {
					if (node.label === moduleName && node.type === 'branch') {
						return {
							...node,
							metadata: { ...node.metadata, description: editDescription }
						};
					}
					return node;
				});
				
				await updateEntry(token, entry.id, {
					data: { ...data, nodes: updatedNodes }
				});
				
				moduleDescriptions.set(moduleName, editDescription);
				moduleDescriptions = new Map(moduleDescriptions);
				editingModule = null;
				toast.success('描述已保存');
				onDataChange?.();
			}
		} catch (e: any) {
			toast.error(e.message || '保存描述失败');
		}
	}

	async function saveFeatureDescription(moduleName: string, featureName: string) {
		try {
			const token = localStorage.token || '';
			const entry = archEntries[0];
			if (entry) {
				const data = entry.data || {};
				const nodes = (data.nodes as any[]) || [];
				
				// Find the feature node and update its description
				const updatedNodes = nodes.map((node: any) => {
					if (node.label === featureName && node.type === 'leaf') {
						return {
							...node,
							metadata: { ...node.metadata, description: editDescription }
						};
					}
					return node;
				});
				
				await updateEntry(token, entry.id, {
					data: { ...data, nodes: updatedNodes }
				});
				
				featureDescriptions.set(`${moduleName}::${featureName}`, editDescription);
				featureDescriptions = new Map(featureDescriptions);
				editingFeature = null;
				toast.success('描述已保存');
				onDataChange?.();
			}
		} catch (e: any) {
			toast.error(e.message || '保存描述失败');
		}
	}

	function getModuleDescription(moduleName: string): string {
		return moduleDescriptions.get(moduleName) || '暂无描述';
	}

	function getFeatureDescription(moduleName: string, featureName: string): string {
		return featureDescriptions.get(`${moduleName}::${featureName}`) || '暂无描述';
	}
</script>

<div class="flex flex-col h-full">
	<!-- Header -->
	<div class="flex items-center justify-between mb-4">
		<h3 class="text-lg font-medium text-gray-900 dark:text-white">模块/功能管理</h3>
		<div class="flex gap-2">
			<button
				class="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
				onclick={() => { showAddModuleForm = true; showAddFeatureForm = false; }}
			>
				+ 添加模块
			</button>
			<button
				class="px-3 py-1.5 text-sm bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
				onclick={() => { showAddFeatureForm = true; showAddModuleForm = false; }}
			>
				+ 添加功能
			</button>
		</div>
	</div>

	<!-- Add Module Form -->
	{#if showAddModuleForm}
		<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-4 border border-gray-200 dark:border-gray-700">
			<div class="flex gap-2">
				<input
					type="text"
					class="flex-1 px-3 py-2 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800"
					placeholder="模块名称"
					bind:value={newModuleName}
					onkeydown={(e) => e.key === 'Enter' && handleAddModule()}
				>
				<button
					class="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
					onclick={handleAddModule}
				>
					添加
				</button>
				<button
					class="px-3 py-1.5 text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg"
					onclick={() => { showAddModuleForm = false; newModuleName = ''; }}
				>
					取消
				</button>
			</div>
		</div>
	{/if}

	<!-- Add Feature Form -->
	{#if showAddFeatureForm}
		<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-4 border border-gray-200 dark:border-gray-700">
			<div class="flex gap-2 mb-2">
				<select
					class="px-3 py-2 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800"
					bind:value={selectedModuleForFeature}
				>
					<option value="">选择模块</option>
					{#each modules as mod}
						<option value={mod.name}>{mod.name}</option>
					{/each}
				</select>
				<input
					type="text"
					class="flex-1 px-3 py-2 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800"
					placeholder="功能名称"
					bind:value={newFeatureName}
					onkeydown={(e) => e.key === 'Enter' && handleAddFeature()}
				>
				<button
					class="px-3 py-1.5 text-sm bg-green-600 hover:bg-green-700 text-white rounded-lg"
					onclick={handleAddFeature}
				>
					添加
				</button>
				<button
					class="px-3 py-1.5 text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg"
					onclick={() => { showAddFeatureForm = false; newFeatureName = ''; }}
				>
					取消
				</button>
			</div>
		</div>
	{/if}

	<!-- Module/Feature List -->
	<div class="flex-1 overflow-y-auto">
		{#if modules.length === 0}
			<div class="flex items-center justify-center h-32 text-gray-400 dark:text-gray-500 text-sm">
				暂无模块，点击"添加模块"开始
			</div>
		{:else}
			<table class="w-full text-sm text-left">
				<thead class="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-800 dark:text-gray-400 sticky top-0">
					<tr>
						<th class="px-4 py-3">模块名称</th>
						<th class="px-4 py-3">来源</th>
						<th class="px-4 py-3">功能数量</th>
						<th class="px-4 py-3">描述</th>
						<th class="px-4 py-3 text-right">操作</th>
					</tr>
				</thead>
				<tbody>
					{#each modules as mod}
						<tr class="bg-white border-b dark:bg-gray-900 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800">
							<td class="px-4 py-3">
								<button
									class="flex items-center gap-2 font-medium text-gray-900 dark:text-white hover:text-blue-600"
									onclick={() => toggleModule(mod.name)}
								>
									<svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
										{#if expandedModules.has(mod.name)}
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
										{:else}
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
										{/if}
									</svg>
									{mod.name}
								</button>
							</td>
							<td class="px-4 py-3">
								{#if mod.source === 'manual'}
									<span class="px-2 py-1 text-xs rounded bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400">手动</span>
								{:else}
									<span class="px-2 py-1 text-xs rounded bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400">自动</span>
								{/if}
							</td>
							<td class="px-4 py-3">{mod.features.length}</td>
							<td class="px-4 py-3 text-gray-500 dark:text-gray-400 max-w-xs truncate">
								{getModuleDescription(mod.name)}
							</td>
							<td class="px-4 py-3 text-right">
								<div class="flex items-center justify-end gap-2">
									<button
										class="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400"
										onclick={() => startEditModule(mod.name)}
									>
										编辑描述
									</button>
									<button
										class="text-xs text-red-600 hover:text-red-800 dark:text-red-400"
										onclick={() => onDeleteModule(mod.name)}
									>
										删除
									</button>
								</div>
							</td>
						</tr>
						{#if editingModule === mod.name}
							<tr class="bg-blue-50 dark:bg-blue-900/20">
								<td colspan="5" class="px-4 py-3">
									<textarea
										class="w-full px-3 py-2 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 mb-2"
										rows="3"
										placeholder="模块描述..."
										bind:value={editDescription}
									></textarea>
									<div class="flex gap-2">
										<button
											class="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
											onclick={() => saveModuleDescription(mod.name)}
										>
											保存
										</button>
										<button
											class="px-3 py-1.5 text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg"
											onclick={() => { editingModule = null; }}
										>
											取消
										</button>
									</div>
								</td>
							</tr>
						{/if}
						{#if expandedModules.has(mod.name)}
							<tr>
								<td colspan="5" class="px-4 py-0">
									<table class="w-full text-sm">
										<thead class="text-xs text-gray-600 bg-gray-100 dark:bg-gray-800 dark:text-gray-400">
											<tr>
												<th class="px-4 py-2 pl-8">功能名称</th>
												<th class="px-4 py-2">来源</th>
												<th class="px-4 py-2">参数数量</th>
												<th class="px-4 py-2">描述</th>
												<th class="px-4 py-2 text-right">操作</th>
											</tr>
										</thead>
										<tbody>
											{#each mod.features as feature}
												<tr class="border-b dark:border-gray-700">
													<td class="px-4 py-2 pl-8">{feature.name}</td>
													<td class="px-4 py-2">
														{#if feature.source === 'manual'}
															<span class="px-2 py-0.5 text-xs rounded bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400">手动</span>
														{:else}
															<span class="px-2 py-0.5 text-xs rounded bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400">自动</span>
														{/if}
													</td>
													<td class="px-4 py-2">{feature.paramCount}</td>
													<td class="px-4 py-2 text-gray-500 dark:text-gray-400 max-w-xs truncate">
														{getFeatureDescription(mod.name, feature.name)}
													</td>
													<td class="px-4 py-2 text-right">
														<div class="flex items-center justify-end gap-2">
															<button
																class="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400"
																onclick={() => startEditFeature(mod.name, feature.name)}
																>
																编辑描述
																</button>
																<button
																class="text-xs text-red-600 hover:text-red-800 dark:text-red-400"
																	onclick={() => onDeleteFeature(mod.name, feature.name)}
																>
																删除
																</button>
														</div>
													</td>
												</tr>
												{#if editingFeature === `${mod.name}::${feature.name}`}
													<tr class="bg-blue-50 dark:bg-blue-900/20">
														<td colspan="5" class="px-4 py-2">
															<textarea
																class="w-full px-3 py-2 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 mb-2"
																rows="2"
																placeholder="功能描述..."
																bind:value={editDescription}
															></textarea>
															<div class="flex gap-2">
																<button
																	class="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
																	onclick={() => saveFeatureDescription(mod.name, feature.name)}
																	>
																	保存
																	</button>
																<button
																	class="px-3 py-1.5 text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg"
																	onclick={() => { editingFeature = null; }}
																	>
																	取消
																	</button>
															</div>
														</td>
													</tr>
												{/if}
											{/each}
										</tbody>
									</table>
								</td>
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>
		{/if}
	</div>
</div>