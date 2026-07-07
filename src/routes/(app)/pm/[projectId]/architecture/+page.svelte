<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		parameterEntries, archEntries, isLoading, loadError,
		aggregatedTree, mindmapNodes, editingEntryId,
		loadData, retryLoadData
	} from '$lib/stores/pm/architectureStore';
	import {
		saveArchitectureEntry, addManualModule, addManualFeature,
		deleteManualModule, deleteManualFeature
	} from '$lib/services/architectureService';
	import ArchitectureTabBar from '$lib/components/pm/architecture/ArchitectureTabBar.svelte';
	import ArchitectureLoading from '$lib/components/pm/architecture/ArchitectureLoading.svelte';
	import ArchitectureError from '$lib/components/pm/architecture/ArchitectureError.svelte';
	import ModuleFeatureTree from '$lib/components/pm/ModuleFeatureTree.svelte';
	import ModuleFeatureManager from '$lib/components/pm/architecture/ModuleFeatureManager.svelte';
	import ParameterTable from '$lib/components/pm/ParameterTable.svelte';
	import MindMapCanvas from '$lib/components/pm/mindmap/MindMapCanvas.svelte';
	import PMVersionSelector from '$lib/components/pm/PMVersionSelector.svelte';
	import { treeToMindMap } from '$lib/utils/excalidrawDataConverter';
	import type { MindMapNode } from '$lib/apis/pm/types';

	let projectId = $derived($page.params.projectId!);
	let selectedModule = $state<string | null>(null);
	let selectedFeature = $state<string | null>(null);
	let treeCollapsed = $state(false);
	let showVersionSelector = $state(false);
	let selectedVersion = $state<{ id: string; versionNumber: string; label?: string } | null>(null);
	let activeTab = $state<'mindmap' | 'modules' | 'params'>('mindmap');

	// Responsive: collapse tree on small screens
	$effect(() => {
		let resizeTimer: ReturnType<typeof setTimeout>;
		function onResize() {
			clearTimeout(resizeTimer);
			resizeTimer = setTimeout(() => {
				if (window.innerWidth < 768 && !treeCollapsed) treeCollapsed = true;
			}, 200);
		}
		onResize();
		window.addEventListener('resize', onResize);
		return () => {
			clearTimeout(resizeTimer);
			window.removeEventListener('resize', onResize);
		};
	});

	onMount(() => { loadData(projectId); });

	async function handleAddModule(name: string) {
		try {
			const token = localStorage.token || '';
			const updatedNodes = await addManualModule(token, projectId, name, $mindmapNodes, $editingEntryId);
			await saveArchitectureEntry(token, projectId, $editingEntryId, updatedNodes, $archEntries[0]?.data);
			await loadData(projectId);
			toast.success(`模块 "${name}" 已添加`);
		} catch (e: any) { toast.error(e.message || '添加模块失败'); }
	}

	async function handleAddFeature(moduleName: string, featureName: string) {
		try {
			const token = localStorage.token || '';
			const updatedNodes = await addManualFeature(token, projectId, moduleName, featureName, $mindmapNodes, $editingEntryId);
			await saveArchitectureEntry(token, projectId, $editingEntryId, updatedNodes, $archEntries[0]?.data);
			await loadData(projectId);
			toast.success(`功能 "${featureName}" 已添加到 "${moduleName}"`);
		} catch (e: any) { toast.error(e.message || '添加功能失败'); }
	}

	async function handleDeleteModule(name: string) {
		try {
			const token = localStorage.token || '';
			const updatedNodes = await deleteManualModule(token, projectId, name, $mindmapNodes, $editingEntryId);
			await saveArchitectureEntry(token, projectId, $editingEntryId, updatedNodes, $archEntries[0]?.data);
			await loadData(projectId);
			if (selectedModule === name) { selectedModule = null; selectedFeature = null; }
			toast.success(`模块 "${name}" 已删除`);
		} catch (e: any) { toast.error(e.message || '删除模块失败'); }
	}

	async function handleDeleteFeature(moduleName: string, featureName: string) {
		try {
			const token = localStorage.token || '';
			const updatedNodes = await deleteManualFeature(token, projectId, moduleName, featureName, $mindmapNodes, $editingEntryId);
			await saveArchitectureEntry(token, projectId, $editingEntryId, updatedNodes, $archEntries[0]?.data);
			await loadData(projectId);
			if (selectedFeature === featureName) selectedFeature = null;
			toast.success(`功能 "${featureName}" 已删除`);
		} catch (e: any) { toast.error(e.message || '删除功能失败'); }
	}

	function handleTreeSelect(module: string, feature?: string) {
		selectedModule = module;
		selectedFeature = feature || null;
	}

	async function handleParamDataChange() { await loadData(projectId); }

	function handleVersionSelect(version: { id: string; versionNumber: string; label?: string }) {
		selectedVersion = version;
		showVersionSelector = false;
		// TODO: Reload data with version filter
		toast.success(`已切换到版本 ${version.versionNumber}`);
	}
</script>

<div class="w-full min-h-full h-full px-3 md:px-[18px]">
	<!-- Header -->
	<div class="flex flex-col gap-1 px-1 mt-1.5 mb-3">
		<div class="flex justify-between items-center">
			<div class="flex items-center md:self-center text-xl font-medium px-0.5 gap-2 shrink-0">
				<div>产品架构</div>
				{#if selectedVersion}
					<span class="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
						{selectedVersion.versionNumber}
					</span>
				{/if}
			</div>
			<div class="flex w-full justify-end gap-1.5 relative z-10">
				<!-- Version Selector -->
				<button
					class="px-2 py-1.5 rounded-xl bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition font-medium text-sm flex items-center"
					onclick={() => { showVersionSelector = true; }}
					title="选择版本"
				>
					<svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
					</svg>
					<span>{selectedVersion?.versionNumber || '选择版本'}</span>
				</button>
				<!-- AI Assistant -->
				<button class="px-2 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white transition font-medium text-sm flex items-center" title="AI 助手">
					<svg class="size-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
					<div class="ml-1 text-xs">AI</div>
				</button>
			</div>
		</div>
		<!-- Tab Bar -->
		<ArchitectureTabBar {activeTab} onTabChange={(tab) => { activeTab = tab; }} />
	</div>

	<!-- Content -->
	{#if $isLoading}
		<ArchitectureLoading />
	{:else if $loadError}
		<ArchitectureError error={$loadError} onRetry={() => retryLoadData(projectId)} />
	{:else}
		<!-- Tab 1: Mind Map -->
		<div class="h-[calc(100vh-200px)]" class:hidden={activeTab !== 'mindmap'}>
			{#if activeTab === 'mindmap'}
				<div class="h-full relative">
					<MindMapCanvas
						data={treeToMindMap($aggregatedTree)}
						version={selectedVersion?.versionNumber}
						onNodeClick={(node) => {
							if (node.type === 'module') {
								selectedModule = node.name;
								selectedFeature = null;
							} else if (node.type === 'feature') {
								// Find parent module
								const parentModule = $aggregatedTree.find(m => 
									m.features.some(f => f.name === node.name)
								);
								if (parentModule) {
									selectedModule = parentModule.name;
									selectedFeature = node.name;
								}
							}
						}}
					/>
				</div>
			{/if}
		</div>

		<!-- Tab 2: Module/Feature Management -->
		<div class="h-[calc(100vh-200px)]" class:hidden={activeTab !== 'modules'}>
			{#if activeTab === 'modules'}
				<div class="flex gap-3 h-full">
					<!-- Left: Module-Feature Tree -->
					<div class="{treeCollapsed ? 'w-full' : 'w-72 shrink-0'} flex flex-col">
						<div class="flex items-center justify-between mb-2">
							{#if !treeCollapsed}
								<span class="text-sm font-medium text-gray-700 dark:text-gray-300">模块结构</span>
							{/if}
							<button class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400 transition-colors" onclick={() => { treeCollapsed = !treeCollapsed; }} title={treeCollapsed ? '展开导航' : '收起导航'}>
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									{#if treeCollapsed}
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
									{:else}
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
									{/if}
								</svg>
							</button>
						</div>
						<ModuleFeatureTree
							modules={$aggregatedTree}
							{selectedModule}
							{selectedFeature}
							onSelect={handleTreeSelect}
							onAddModule={handleAddModule}
							onAddFeature={handleAddFeature}
							onDeleteModule={handleDeleteModule}
							onDeleteFeature={handleDeleteFeature}
							collapsed={treeCollapsed}
							versionInfo={selectedVersion}
						/>
					</div>
					<!-- Right: Module/Feature Description -->
					<div class="flex-1 min-w-0 overflow-hidden">
						<ModuleFeatureManager
							modules={$aggregatedTree}
							{projectId}
							{selectedModule}
							{selectedFeature}
							archEntries={$archEntries}
							onSelect={handleTreeSelect}
							onAddModule={handleAddModule}
							onAddFeature={handleAddFeature}
							onDeleteModule={handleDeleteModule}
							onDeleteFeature={handleDeleteFeature}
							onDataChange={handleParamDataChange}
						/>
					</div>
				</div>
			{/if}
		</div>

		<!-- Tab 3: Parameter Table -->
		<div class="h-[calc(100vh-200px)]" class:hidden={activeTab !== 'params'}>
			{#if activeTab === 'params'}
				<div class="flex gap-3 h-full">
					<!-- Left: Module-Feature Tree -->
					<div class="{treeCollapsed ? 'w-full' : 'w-72 shrink-0'} flex flex-col">
						<div class="flex items-center justify-between mb-2">
							{#if !treeCollapsed}
								<span class="text-sm font-medium text-gray-700 dark:text-gray-300">模块结构</span>
							{/if}
							<button class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400 transition-colors" onclick={() => { treeCollapsed = !treeCollapsed; }} title={treeCollapsed ? '展开导航' : '收起导航'}>
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									{#if treeCollapsed}
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
									{:else}
										<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
									{/if}
								</svg>
							</button>
						</div>
						<ModuleFeatureTree
							modules={$aggregatedTree}
							{selectedModule}
							{selectedFeature}
							onSelect={handleTreeSelect}
							onAddModule={handleAddModule}
							onAddFeature={handleAddFeature}
							onDeleteModule={handleDeleteModule}
							onDeleteFeature={handleDeleteFeature}
							collapsed={treeCollapsed}
							versionInfo={selectedVersion}
						/>
					</div>
					<!-- Right: Parameter Table -->
					<div class="flex-1 min-w-0 overflow-hidden">
						<ParameterTable
							entries={$parameterEntries}
							{projectId}
							filterModule={selectedModule}
							filterFeature={selectedFeature}
							onDataChange={handleParamDataChange}
							versionId={selectedVersion?.id || null}
						/>
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>

<!-- Version Selector Modal -->
<PMVersionSelector
	isOpen={showVersionSelector}
	onClose={() => { showVersionSelector = false; }}
	onSelect={handleVersionSelect}
	{projectId}
/>