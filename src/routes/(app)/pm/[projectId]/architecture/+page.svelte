<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import {
		isLoading, loadError,
		architectureHierarchy,
		loadData, retryLoadData
	} from '$lib/stores/pm/architectureStore';
	import type { ArchModule } from '$lib/stores/pm/architectureStore';
	import MindMapView from '$lib/components/pm/architecture/MindMapView.svelte';
	import ArchitectureTable from '$lib/components/pm/architecture/ArchitectureTable.svelte';
	import PMVersionSelector from '$lib/components/pm/PMVersionSelector.svelte';
	import { createEntry, updateEntry, deleteEntry } from '$lib/apis/pm/index';

	let projectId = $derived($page.params.projectId!);
	let showVersionSelector = $state(false);
	let selectedVersion = $state<{ id: string; versionNumber: string; label?: string } | null>(null);
	let activeTab = $state<'mindmap' | 'table'>('mindmap');
	let modules = $state<ArchModule[]>([]);
	let tableRef = $state<any>(null);

	// Subscribe to architecture hierarchy
	$effect(() => {
		const unsubscribe = architectureHierarchy.subscribe(data => {
			modules = data;
		});
		return unsubscribe;
	});

	onMount(() => { loadData(projectId); });

	function handleVersionSelect(version: { id: string; versionNumber: string; label?: string }) {
		selectedVersion = version;
		showVersionSelector = false;
		// Reload data with version
		loadData(projectId);
		toast.success(`已切换到版本 ${version.versionNumber}`);
	}

	function handleNodeClick(moduleId: string, featureId?: string) {
		activeTab = 'table';
		// Scroll to and highlight the clicked node in table
		const targetId = featureId || moduleId;
		if (tableRef) {
			tableRef.highlightItem(targetId);
		}
		toast.info(`定位到: ${moduleId}${featureId ? ' > ' + featureId : ''}`);
	}

	async function handleTableEdit(type: 'module' | 'feature' | 'parameter', data: any) {
		try {
			const token = localStorage.token || '';
			if (!token) {
				toast.error('未登录');
				return;
			}

			// Update entry via API
			await updateEntry(token, data.id, {
				...data,
				module_type: 'product-architecture'
			});
			
			// Refresh data
			await loadData(projectId);
			toast.success('更新成功');
		} catch (e: any) {
			toast.error(e.message || '更新失败');
		}
	}

	async function handleTableDelete(type: 'module' | 'feature' | 'parameter', id: string) {
		try {
			const token = localStorage.token || '';
			if (!token) {
				toast.error('未登录');
				return;
			}

			await deleteEntry(token, id);
			
			// Refresh data
			await loadData(projectId);
			toast.success('删除成功');
		} catch (e: any) {
			toast.error(e.message || '删除失败');
		}
	}

	async function handleTableAdd(type: 'module' | 'feature' | 'parameter', parentId?: string) {
		try {
			const token = localStorage.token || '';
			if (!token) {
				toast.error('未登录');
				return;
			}

			// Create new entry via API
			const newData = {
				module_type: 'product-architecture',
				title: type === 'module' ? '新模块' : type === 'feature' ? '新功能' : '新参数',
				data: {
					type: type,
					parentId: parentId || null
				}
			};

			await createEntry(token, projectId, newData);
			
			// Refresh data
			await loadData(projectId);
			toast.success('添加成功');
		} catch (e: any) {
			toast.error(e.message || '添加失败');
		}
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
		<div class="flex gap-1 mt-2">
			<button
				class="px-4 py-2 rounded-xl text-sm font-medium transition {activeTab === 'mindmap' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'}"
				onclick={() => activeTab = 'mindmap'}
			>
				思维导图
			</button>
			<button
				class="px-4 py-2 rounded-xl text-sm font-medium transition {activeTab === 'table' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'}"
				onclick={() => activeTab = 'table'}
			>
				表格
			</button>
		</div>
	</div>

	<!-- Content -->
	{#if $isLoading}
		<div class="flex items-center justify-center h-[calc(100vh-200px)]">
			<div class="w-8 h-8 border-2 border-gray-300 dark:border-gray-600 border-t-blue-500 rounded-full animate-spin"></div>
		</div>
	{:else if $loadError}
		<div class="flex flex-col items-center justify-center h-[calc(100vh-200px)]">
			<div class="text-red-500 mb-2">{$loadError}</div>
			<button class="px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition" onclick={() => retryLoadData(projectId)}>
				重试
			</button>
		</div>
	{:else}
		{#if activeTab === 'mindmap'}
			<div class="h-[calc(100vh-200px)]">
				<MindMapView modules={modules} onNodeClick={handleNodeClick} />
			</div>
		{:else}
			<div class="h-[calc(100vh-200px)]">
				<ArchitectureTable 
					modules={modules} 
					onEdit={handleTableEdit}
					onDelete={handleTableDelete}
					onAdd={handleTableAdd}
					bind:this={tableRef}
				/>
			</div>
		{/if}
	{/if}
</div>

<!-- Version Selector Modal -->
<PMVersionSelector
	isOpen={showVersionSelector}
	onClose={() => { showVersionSelector = false; }}
	onSelect={handleVersionSelect}
	{projectId}
/>