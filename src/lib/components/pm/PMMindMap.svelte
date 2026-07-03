<script lang="ts">
	import { writable, derived } from 'svelte/store';
	import { SvelteFlow, Controls, Background, MiniMap, type Node, type Edge, type NodeTypes } from '@xyflow/svelte';
	import '@xyflow/svelte/dist/style.css';
	import type { MindMapNode } from '$lib/apis/pm/types';

	// Props
	interface Props {
		nodes?: MindMapNode[];
		onChange?: (nodes: MindMapNode[]) => void;
		readonly?: boolean;
	}

	let { nodes: initialNodes = [], onChange, readonly = false }: Props = $props();

	// Performance: large graph threshold
	const LARGE_GRAPH_THRESHOLD = 200;
	let isLargeGraph = $derived(initialNodes.length > LARGE_GRAPH_THRESHOLD);

	// Performance: viewport-based node filtering for large graphs
	let viewportBounds = $state({ x: -500, y: -500, width: 2000, height: 2000 });
	const VIEWPORT_PADDING = 300; // render nodes slightly outside viewport for smooth panning

	// Performance: node count display
	let visibleNodeCount = $state(0);
	let totalNodeCount = $derived(initialNodes.length);

	// Convert MindMapNode to xyflow Node
	function toFlowNodes(nodes: MindMapNode[]): Node[] {
		return nodes.map((node, index) => ({
			id: node.id,
			position: node.position,
			data: { label: node.label, type: node.type, metadata: node.metadata },
			style: {
				background: getNodeColor(node.type),
				borderColor: getNodeBorderColor(node.type),
				borderWidth: 2,
				borderRadius: 8,
				padding: '8px 16px',
				fontSize: 14,
				fontWeight: node.type === 'root' ? 600 : 400,
				color: '#1f2937',
				minWidth: 120,
				textAlign: 'center'
			},
			parentId: node.parentId || undefined
		}));
	}

	function toFlowEdges(nodes: MindMapNode[]): Edge[] {
		const edges: Edge[] = [];
		nodes.forEach(node => {
			if (node.parentId) {
				edges.push({
					id: `e-${node.parentId}-${node.id}`,
					source: node.parentId,
					target: node.id,
					style: { stroke: '#9ca3af', strokeWidth: 2 },
					animated: false
				});
			}
		});
		return edges;
	}

	function getNodeColor(type: string): string {
		switch (type) {
			case 'root': return '#dbeafe'; // blue-100
			case 'branch': return '#dcfce7'; // green-100
			case 'leaf': return '#fef3c7'; // yellow-100
			case 'dependency': return '#f3e8ff'; // purple-100
			default: return '#f3f4f6'; // gray-100
		}
	}

	function getNodeBorderColor(type: string): string {
		switch (type) {
			case 'root': return '#3b82f6'; // blue-500
			case 'branch': return '#22c55e'; // green-500
			case 'leaf': return '#eab308'; // yellow-500
			case 'dependency': return '#a855f7'; // purple-500
			default: return '#9ca3af'; // gray-400
		}
	}

	// Performance: filter nodes by viewport for large graphs
	function filterNodesByViewport(allNodes: Node[], bounds: typeof viewportBounds): Node[] {
		if (!isLargeGraph) return allNodes;

		return allNodes.filter(node => {
			const nodeWidth = 120;
			const nodeHeight = 48;
			return (
				node.position.x + nodeWidth + VIEWPORT_PADDING > bounds.x &&
				node.position.x - VIEWPORT_PADDING < bounds.x + bounds.width &&
				node.position.y + nodeHeight + VIEWPORT_PADDING > bounds.y &&
				node.position.y - VIEWPORT_PADDING < bounds.y + bounds.height
			);
		});
	}

	// Performance: for large graphs, only include edges connecting visible nodes
	function filterEdgesByVisibleNodes(allEdges: Edge[], visibleNodeIds: Set<string>): Edge[] {
		if (!isLargeGraph) return allEdges;
		return allEdges.filter(edge => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target));
	}

	// Reactive state
	let allNodes = writable<Node[]>(toFlowNodes(initialNodes));
	let allEdges = writable<Edge[]>(toFlowEdges(initialNodes));

	// Performance: derived filtered nodes/edges for large graphs
	let visibleNodeIds = $state<Set<string>>(new Set());

	let filteredNodes = derived(allNodes, ($allNodes) => {
		const filtered = filterNodesByViewport($allNodes, viewportBounds);
		visibleNodeIds = new Set(filtered.map(n => n.id));
		visibleNodeCount = filtered.length;
		return filtered;
	});

	let filteredEdges = derived([allEdges], ([$allEdges]) => {
		return filterEdgesByVisibleNodes($allEdges, visibleNodeIds);
	});

	// Use filtered for large graphs, full for small
	let displayNodes = writable<Node[]>([]);
	let displayEdges = writable<Edge[]>([]);
	$effect(() => {
		displayNodes.set(isLargeGraph ? $filteredNodes : $allNodes);
		displayEdges.set(isLargeGraph ? $filteredEdges : $allEdges);
	});

	// Update when props change
	$effect(() => {
		const flowNodes = toFlowNodes(initialNodes);
		const flowEdges = toFlowEdges(initialNodes);
		isLargeGraph = initialNodes.length > LARGE_GRAPH_THRESHOLD;
		allNodes.set(flowNodes);
		allEdges.set(flowEdges);
	});

	// Performance: handle viewport change for large graph filtering
	function handleViewportChange(event: CustomEvent<{ viewport: { x: number; y: number; zoom: number } }>) {
		if (!isLargeGraph) return;
		const { x, y, zoom } = event.detail.viewport;
		// Convert viewport to pixel bounds
		// SvelteFlow viewport x/y are in flow coordinates, we need pixel coordinates
		const containerWidth = viewportBounds.width;
		const containerHeight = viewportBounds.height;
		viewportBounds = {
			x: -x / zoom,
			y: -y / zoom,
			width: containerWidth / zoom,
			height: containerHeight / zoom
		};
	}

	// Handle node changes
	function handleNodesChange(event: CustomEvent<{ nodes: Node[] }>) {
		const updatedNodes = event.detail.nodes.map(node => ({
			id: node.id,
			projectId: '', // Will be set by parent
			parentId: node.parentId || null,
			label: node.data?.label || '',
			type: (node.data?.type as 'root' | 'branch' | 'leaf' | 'dependency') || 'leaf',
			position: node.position,
			metadata: node.data?.metadata || {},
			moduleRef: null,
			createdAt: Date.now(),
			updatedAt: Date.now()
		}));
		onChange?.(updatedNodes);
	}

	// Add new node
	function addNode(parentId: string | null = null) {
		const newNodeId = `node-${Date.now()}`;
		const parentNode = parentId ? $allNodes.find(n => n.id === parentId) : null;
		const newNode: Node = {
			id: newNodeId,
			position: parentNode
				? { x: parentNode.position.x + 200, y: parentNode.position.y + 100 }
				: { x: 100, y: 100 },
			data: { label: '新节点', type: 'leaf', metadata: {} },
			style: {
				background: getNodeColor('leaf'),
				borderColor: getNodeBorderColor('leaf'),
				borderWidth: 2,
				borderRadius: 8,
				padding: '8px 16px',
				fontSize: 14,
				color: '#1f2937',
				minWidth: 120,
				textAlign: 'center'
			}
		};

		allNodes.update(n => [...n, newNode]);

		if (parentId) {
			allEdges.update(e => [
				...e,
				{
					id: `e-${parentId}-${newNodeId}`,
					source: parentId,
					target: newNodeId,
					style: { stroke: '#9ca3af', strokeWidth: 2 }
				}
			]);
		}
	}

	// Delete node
	function deleteNode(nodeId: string) {
		allNodes.update(n => n.filter(node => node.id !== nodeId));
		allEdges.update(e => e.filter(edge => edge.source !== nodeId && edge.target !== nodeId));
	}

	// Toolbar actions
	let selectedNodeId: string | null = $state(null);

	function handleNodeClick(event: CustomEvent<{ node: Node }>) {
		selectedNodeId = event.detail.node.id;
	}

	function handlePaneClick() {
		selectedNodeId = null;
	}

	// Performance: fit view on initial load for large graphs
	let fitViewOnLoad = $derived(isLargeGraph);
</script>

<div class="pm-mindmap flex flex-col h-full bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
	<!-- Toolbar -->
	{#if !readonly}
		<div class="flex items-center gap-2 px-4 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
			<button
				class="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
				onclick={() => addNode(selectedNodeId)}
				aria-label="添加节点"
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
				</svg>
				添加节点
			</button>
			{#if selectedNodeId}
				<button
					class="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
					onclick={() => {
						deleteNode(selectedNodeId!);
						selectedNodeId = null;
					}}
					aria-label="删除节点"
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
					</svg>
					删除节点
				</button>
			{/if}
			<div class="flex-1"></div>
			<!-- Performance indicator for large graphs -->
			{#if isLargeGraph}
				<span class="text-xs text-gray-500 dark:text-gray-400" aria-label="节点统计">
					{visibleNodeCount}/{totalNodeCount} 节点可见
				</span>
			{:else}
				<span class="text-xs text-gray-500 dark:text-gray-400">
					{#if selectedNodeId}
						已选择: {selectedNodeId}
					{:else}
						点击节点进行选择
					{/if}
				</span>
			{/if}
		</div>
	{/if}

	<!-- Mind Map Canvas -->
	<div class="flex-1 relative">
		<SvelteFlow
			nodes={$displayNodes}
			edges={$displayEdges}
			onnodeclick={handleNodeClick}
			onpaneclick={handlePaneClick}
			onviewportchange={handleViewportChange}
			fitView={fitViewOnLoad}
			nodesDraggable={!readonly}
			nodesConnectable={!readonly}
			elementsSelectable={!readonly}
			minZoom={0.1}
			maxZoom={2}
		>
			<Background patternColor="#e5e7eb" gap={20} />
			<Controls />
			<MiniMap
				maskColor="rgba(0, 0, 0, 0.1)"
				nodeColor={(node) => getNodeBorderColor(node.data?.type as string)}
			/>
		</SvelteFlow>
	</div>
</div>

<style>
	.pm-mindmap :global(.svelte-flow__node) {
		font-size: 14px;
		font-weight: 500;
	}

	.pm-mindmap :global(.svelte-flow__node.selected) {
		box-shadow: 0 0 0 2px #3b82f6;
	}

	.pm-mindmap :global(.svelte-flow__edge-path) {
		stroke: #9ca3af;
		stroke-width: 2;
	}

	.pm-mindmap :global(.svelte-flow__handle) {
		opacity: 0;
	}

	.pm-mindmap :global(.svelte-flow__controls) {
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}

	.pm-mindmap :global(.svelte-flow__minimap) {
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
	}
</style>
