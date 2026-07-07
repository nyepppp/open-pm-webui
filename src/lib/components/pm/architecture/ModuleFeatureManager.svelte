<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { updateEntry } from '$lib/apis/pm/index';
	import type { TreeModule } from '$lib/stores/pm/architectureStore';
	import ModuleCard from './ModuleCard.svelte';
	import AddFeatureModal from './AddFeatureModal.svelte';

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

	<!-- Add Feature Modal -->
	<AddFeatureModal
		show={showAddFeatureForm}
		moduleName={selectedModuleForFeature}
		onClose={() => { showAddFeatureForm = false; newFeatureName = ''; }}
		onSubmit={(featureName, parameters) => {
			if (selectedModuleForFeature) {
				onAddFeature(selectedModuleForFeature, featureName);
				showAddFeatureForm = false;
			}
		}}
	/>

	<!-- Module Cards Grid -->
	<div class="flex-1 overflow-y-auto">
		{#if modules.length === 0}
			<div class="flex items-center justify-center h-32 text-gray-400 dark:text-gray-500 text-sm">
				暂无模块，点击"添加模块"开始
			</div>
		{:else}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				{#each modules as mod}
					<ModuleCard
						module={mod}
						selected={selectedModule === mod.name}
						expanded={expandedModules.has(mod.name)}
						selectedFeature={selectedFeature}
						description={getModuleDescription(mod.name)}
						onSelect={() => {
							toggleModule(mod.name);
							onSelect(mod.name);
						}}
						onFeatureSelect={(featureName) => {
							onSelect(mod.name, featureName);
						}}
						onAddFeature={() => {
							selectedModuleForFeature = mod.name;
							showAddFeatureForm = true;
						}}
						onDelete={() => onDeleteModule(mod.name)}
						onEditDescription={() => startEditModule(mod.name)}
					/>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Edit Description Modal -->
	{#if editingModule}
		<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onclick={() => editingModule = null}>
			<div class="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-lg mx-4" onclick={(e) => e.stopPropagation()}>
				<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
					编辑模块描述
				</h3>
				<textarea
					class="w-full px-3 py-2 text-sm border rounded-lg border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 mb-4"
					rows="4"
					placeholder="模块描述..."
					bind:value={editDescription}
				></textarea>
				<div class="flex gap-2 justify-end">
					<button
						class="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
										onclick={() => {
											if (editingModule) {
												saveModuleDescription(editingModule);
											}
										}}
					>
						保存
					</button>
					<button
						class="px-4 py-2 text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg"
						onclick={() => { editingModule = null; }}
					>
						取消
					</button>
				</div>
			</div>
		</div>
	{/if}
</div>
