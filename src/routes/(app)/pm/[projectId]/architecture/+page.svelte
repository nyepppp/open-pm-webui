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
	import PMMindMap from '$lib/components/pm/PMMindMap.svelte';
	import ModuleFeatureTree from '$lib/components/pm/ModuleFeatureTree.svelte';
	import ParameterTable from '$lib/components/pm/ParameterTable.svelte';
	import { versions as versionList } from '$lib/stores/pm/versionStore';
	import type { MindMapNode } from '$lib/apis/pm/types';

	let projectId = $derived($page.params.projectId!);
	let activeTab = $state<'mindmap' | 'params'>('mindmap');
	let navigateToModule = $state<string | null>(null);
	let navigateToFeature = $state<string | null>(null);
	let selectedModule = $state<string | null>(null);
	let selectedFeature = $state<string | null>(null);
	let treeCollapsed = $state(false);

	$effect(() => {
		function onResize() { if (window.innerWidth < 768 && !treeCollapsed) treeCollapsed = true; }
		onResize();
		window.addEventListener('resize', onResize);
		return () => window.removeEventListener('resize', onResize);
	});

	$effect(() => {
		if (navigateToModule) {
			selectedModule = navigateToModule;
			selectedFeature = navigateToFeature;
			navigateToModule = null;
			navigateToFeature = null;
		}
	});

	onMount(() => { loadData(projectId); });

	let versionOptions = $derived($versionList.map((v: any) => ({ id: v.id, versionNumber: v.versionNumber, label: v.label })));

	async function handleMindmapChange(nodes: MindMapNode[]) {
		try {
			const token = localStorage.token || '';
			await saveArchitectureEntry(token, projectId, $editingEntryId, nodes, $archEntries[0]?.data);
			await loadData(projectId);
		} catch (e: any) { toast.error(e.message || '保存架构图失败'); }
	}

	async function handleSync() { await loadData(projectId); }

	function handleNavigate(target: { moduleName: string; featureName?: string }) {
		navigateToModule = target.moduleName;
		navigateToFeature = target.featureName || null;
		activeTab = 'params';
	}

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

	function handleTreeSelect(module: string, feature?: string) { selectedModule = module; selectedFeature = feature || null; }
	async function handleParamDataChange() { await loadData(projectId); }
</script>

<div class="w-full min-h-full h-full px-3 md:px-[18px]">
	<div class="flex flex-col gap-1 px-1 mt-1.5 mb-3">
		<div class="flex justify-between items-center">
			<div class="flex items-center md:self-center text-xl font-medium px-0.5 gap-2 shrink-0">
				<div>产品架构</div>
			</div>
			<div class="flex w-full justify-end gap-1.5">
				<button class="px-2 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white transition font-medium text-sm flex items-center" title="AI 助手">
					<svg class="size-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
					<div class="ml-1 text-xs">AI</div>
				</button>
			</div>
		</div>
		<ArchitectureTabBar {activeTab} onTabChange={(tab) => { activeTab = tab; }} />
	</div>

	{#if $isLoading}
		<ArchitectureLoading />
	{:else if $loadError}
		<ArchitectureError error={$loadError} onRetry={() => retryLoadData(projectId)} />
	{:else if activeTab === 'mindmap'}
		<div class="h-[calc(100vh-200px)]">
			<PMMindMap
				nodes={$mindmapNodes}
				onChange={handleMindmapChange}
				{projectId}
				versions={versionOptions}
				onSync={handleSync}
				aggregatedModules={$aggregatedTree}
				onNavigate={handleNavigate}
			/>
		</div>
	{:else if activeTab === 'params'}
		<div class="flex gap-3 h-[calc(100vh-200px)]">
			<div class="{treeCollapsed ? 'w-full' : 'w-64 shrink-0'} flex flex-col">
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
				/>
			</div>
			<div class="flex-1 min-w-0 overflow-hidden">
				<ParameterTable
					entries={$parameterEntries}
					{projectId}
					filterModule={selectedModule}
					filterFeature={selectedFeature}
					onDataChange={handleParamDataChange}
				/>
			</div>
		</div>
	{/if}
</div>
