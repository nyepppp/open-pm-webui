<script lang="ts">
	// Import CSS at module level to ensure it's loaded
	import '@xyflow/svelte/dist/style.css';
	import { onMount, onDestroy } from 'svelte';
	import { writable } from 'svelte/store';

	interface Props {
		nodes: any[];
		edges: any[];
		onNodesChange?: (nodes: any[]) => void;
		onEdgesChange?: (edges: any[]) => void;
		onConnect?: (connection: any) => void;
		onNodeClick?: (node: any) => void;
		onPaneClick?: () => void;
		readonly?: boolean;
	}

	let { 
		nodes = [], 
		edges = [], 
		onNodesChange, 
		onEdgesChange, 
		onConnect, 
		onNodeClick, 
		onPaneClick,
		readonly = false 
	}: Props = $props();

	let container: HTMLDivElement;
	let SvelteFlow: any = $state(null);
	let Background: any = $state(null);
	let Controls: any = $state(null);
	let MiniMap: any = $state(null);
	let Panel: any = $state(null);
	let loadError = $state<string | null>(null);
	let isLoading = $state(true);

	// Local state for nodes and edges
	let localNodes = $state<any[]>([]);
	let localEdges = $state<any[]>([]);

	$effect(() => {
		localNodes = nodes ? [...nodes] : [];
	});

	$effect(() => {
		localEdges = edges ? [...edges] : [];
	});

	onMount(async () => {
		if (!container) return;

		try {
			// Dynamically import ReactFlow Svelte components
			const reactFlowModule = await import('@xyflow/svelte');
			SvelteFlow = reactFlowModule.SvelteFlow;
			if (!SvelteFlow) {
				console.error('[ReactFlowCanvas] SvelteFlow not found in module');
				loadError = 'SvelteFlow component not found in @xyflow/svelte module';
				return;
			}
			Background = reactFlowModule.Background;
			Controls = reactFlowModule.Controls;
			MiniMap = reactFlowModule.MiniMap;
			Panel = reactFlowModule.Panel;
			
			isLoading = false;
		} catch (error: any) {
			console.error('[ReactFlowCanvas] Failed to load @xyflow/svelte:', error);
			loadError = error?.message || 'Failed to load ReactFlow library';
			// Mark as loading complete even on error to prevent infinite loading
			isLoading = false;
		}
	});

	function handleNodesChange(event: any) {
		localNodes = event.detail || event;
		onNodesChange?.(localNodes);
	}

	function handleEdgesChange(event: any) {
		localEdges = event.detail || event;
		onEdgesChange?.(localEdges);
	}

	function handleConnect(event: any) {
		onConnect?.(event.detail || event);
	}

	function handleNodeClick(event: any) {
		onNodeClick?.(event.detail || event);
	}

	function handlePaneClick() {
		onPaneClick?.();
	}
</script>

<div bind:this={container} class="w-full h-full" style="min-height: 400px;">
	{#if !isLoading && SvelteFlow}
		<SvelteFlow
			nodes={localNodes}
			edges={localEdges}
			on:nodesChange={handleNodesChange}
			on:edgesChange={handleEdgesChange}
			on:connect={handleConnect}
			on:nodeClick={handleNodeClick}
			on:paneClick={handlePaneClick}
			fitView
			zoomOnScroll={!readonly}
			panOnDrag={!readonly}
			selectNodesOnDrag={false}
			deleteKey={readonly ? null : 'Delete'}
		>
			<Background patternColor="#e5e7eb" gap={20} />
			<Controls />
			<MiniMap />
		</SvelteFlow>
	{:else}
		{#if loadError}
			<div class="flex flex-col items-center justify-center h-full text-center p-4">
				<svg class="w-10 h-10 text-red-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" /></svg>
				<p class="text-sm text-red-500 dark:text-red-400 mb-2">加载流程图组件失败</p>
				<p class="text-xs text-gray-500 mb-3">{loadError}</p>
				<button class="px-3 py-1.5 text-xs bg-black text-white dark:bg-white dark:text-black rounded-lg transition" onclick={() => window.location.reload()}>刷新页面</button>
			</div>
		{:else}
			<div class="w-full h-full flex items-center justify-center bg-gray-50">
				<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
			</div>
		{/if}
	{/if}
</div>
