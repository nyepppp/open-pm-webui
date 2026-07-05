<script lang="ts">
	import { writable, derived } from 'svelte/store';
	import { SvelteFlow, Controls, Background, MiniMap, type Node, type Edge } from '@xyflow/svelte';
	import '@xyflow/svelte/dist/style.css';
	import type { MindMapNode } from '$lib/apis/pm/types';
	import { autoExtractArchitecture, syncArchitecture, type ArchitectureSyncDiff } from '$lib/apis/pm/index';
	import { toast } from 'svelte-sonner';

	interface Version {
		id: string;
		versionNumber: string;
		label?: string;
	}

	interface Props {
		nodes?: MindMapNode[];
		onChange?: (nodes: MindMapNode[]) => void;
		readonly?: boolean;
		projectId?: string;
		versions?: Version[];
		onSync?: (diff: ArchitectureSyncDiff) => void;
	}

	let {
		nodes: initialNodes = [],
		onChange,
		readonly = false,
		projectId = '',
		versions = [],
		onSync
	}: Props = $props();

	const LARGE_GRAPH_THRESHOLD = 200;
	let isLargeGraph = $derived(initialNodes.length > LARGE_GRAPH_THRESHOLD);

	let viewportBounds = $state({ x: -500, y: -500, width: 2000, height: 2000 });
	const VIEWPORT_PADDING = 300;

	let visibleNodeCount = $state(0);
	let totalNodeCount = $derived(initialNodes.length);

	let selectedVersionId = $state<string | null>(null);
	let syncing = $state(false);
	let syncDiff = $state<ArchitectureSyncDiff | null>(null);
	let showSyncDiff = $state(false);
	let hoveredNodeId = $state<string | null>(null);

	let versionFilteredNodes = $derived.by(() => {
		if (!selectedVersionId) return initialNodes;
		return initialNodes.filter((node) => {
			const meta = node.metadata || {};
			const nodeVersionId = meta.versionId as string | undefined;
			return !nodeVersionId || nodeVersionId === selectedVersionId;
		});
	});

	function toFlowNodes(nodes: MindMapNode[]): Node[] {
		return nodes.map((node) => ({
			id: node.id,
			position: node.position,
			data: {
				label: node.label,
				type: node.type,
				metadata: node.metadata,
				moduleRef: node.moduleRef
			},
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
		nodes.forEach((node) => {
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
			case 'root':
				return '#dbeafe';
			case 'branch':
				return '#dcfce7';
			case 'leaf':
				return '#fef3c7';
			case 'dependency':
				return '#f3e8ff';
			default:
				return '#f3f4f6';
		}
	}

	function getNodeBorderColor(type: string): string {
		switch (type) {
			case 'root':
				return '#3b82f6';
			case 'branch':
				return '#22c55e';
			case 'leaf':
				return '#eab308';
			case 'dependency':
				return '#a855f7';
			default:
				return '#9ca3af';
		}
	}

	function filterNodesByViewport(allNodes: Node[], bounds: typeof viewportBounds): Node[] {
		if (!isLargeGraph) return allNodes;
		return allNodes.filter((node) => {
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

	function filterEdgesByVisibleNodes(allEdges: Edge[], visibleNodeIds: Set<string>): Edge[] {
		if (!isLargeGraph) return allEdges;
		return allEdges.filter((edge) => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target));
	}

	let allNodes = writable<Node[]>(toFlowNodes(versionFilteredNodes));
	let allEdges = writable<Edge[]>(toFlowEdges(versionFilteredNodes));

	let visibleNodeIds = $state<Set<string>>(new Set());

	let filteredNodes = derived(allNodes, ($allNodes) => {
		const filtered = filterNodesByViewport($allNodes, viewportBounds);
		visibleNodeIds = new Set(filtered.map((n) => n.id));
		visibleNodeCount = filtered.length;
		return filtered;
	});

	let filteredEdges = derived([allEdges], ([$allEdges]) => {
		return filterEdgesByVisibleNodes($allEdges, visibleNodeIds);
	});

	let displayNodes = writable<Node[]>([]);
	let displayEdges = writable<Edge[]>([]);
	$effect(() => {
		displayNodes.set(isLargeGraph ? $filteredNodes : $allNodes);
		displayEdges.set(isLargeGraph ? $filteredEdges : $allEdges);
	});

	$effect(() => {
		const flowNodes = toFlowNodes(versionFilteredNodes);
		const flowEdges = toFlowEdges(versionFilteredNodes);
		isLargeGraph = versionFilteredNodes.length > LARGE_GRAPH_THRESHOLD;
		allNodes.set(flowNodes);
		allEdges.set(flowEdges);
	});

	function handleViewportChange(event: CustomEvent<{ viewport: { x: number; y: number; zoom: number } }>) {
		if (!isLargeGraph) return;
		const { x, y, zoom } = event.detail.viewport;
		const containerWidth = viewportBounds.width;
		const containerHeight = viewportBounds.height;
		viewportBounds = {
			x: -x / zoom,
			y: -y / zoom,
			width: containerWidth / zoom,
			height: containerHeight / zoom
		};
	}

	function handleNodesChange(event: CustomEvent<{ nodes: Node[] }>) {
		const updatedNodes = event.detail.nodes.map((node) => ({
			id: node.id,
			projectId: projectId,
			parentId: node.parentId || null,
			label: node.data?.label || '',
			type: (node.data?.type as 'root' | 'branch' | 'leaf' | 'dependency') || 'leaf',
			position: node.position,
			metadata: node.data?.metadata || {},
			moduleRef: node.data?.moduleRef || null,
			createdAt: Date.now(),
			updatedAt: Date.now()
		}));
		onChange?.(updatedNodes);
	}

	function addNode(parentId: string | null = null) {
		const newNodeId = `node-${Date.now()}`;
		const parentNode = parentId ? $allNodes.find((n) => n.id === parentId) : null;
		const newNode: Node = {
			id: newNodeId,
			position: parentNode ? { x: parentNode.position.x + 200, y: parentNode.position.y + 100 } : { x: 100, y: 100 },
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
		allNodes.update((n) => [...n, newNode]);
		if (parentId) {
			allEdges.update((e) => [...e, { id: `e-${parentId}-${newNodeId}`, source: parentId, target: newNodeId, style: { stroke: '#9ca3af', strokeWidth: 2 } }]);
		}
	}

	function deleteNode(nodeId: string) {
		allNodes.update((n) => n.filter((node) => node.id !== nodeId));
		allEdges.update((e) => e.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
	}

	let selectedNodeId: string | null = $state(null);

	function handleNodeClick(event: CustomEvent<{ node: Node }>) {
		const node = event.detail.node;
		selectedNodeId = node.id;
		const moduleRef = node.data?.moduleRef as string | undefined;
		const moduleType = node.data?.metadata?.moduleType as string | undefined;
		if (moduleRef && moduleType && projectId) {
			window.location.href = `/pm/${projectId}/${moduleType}`;
		}
	}

	function handleNodeMouseOver(event: CustomEvent<{ node: Node }>) {
		hoveredNodeId = event.detail.node.id;
	}

	function handleNodeMouseOut() {
		hoveredNodeId = null;
	}

	function handlePaneClick() {
		selectedNodeId = null;
	}

	let fitViewOnLoad = $derived(isLargeGraph);

	let hoveredNodeData = $derived.by(() => {
		if (!hoveredNodeId) return null;
		const node = $allNodes.find((n) => n.id === hoveredNodeId);
		if (!node) return null;
		return {
			label: node.data?.label as string,
			type: node.data?.type as string,
			metadata: node.data?.metadata as Record<string, unknown>,
			moduleRef: node.data?.moduleRef as string | undefined
		};
	});

	async function handleSync() {
		if (!projectId) return;
		syncing = true;
		try {
			const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
			const result = await syncArchitecture(token, projectId, {
				apply: false,
				version_id: selectedVersionId || undefined
			});
			syncDiff = result.diff;
			showSyncDiff = true;
		} catch {
			toast.error('架构同步失败');
		} finally {
			syncing = false;
		}
	}

	async function handleApplySync() {
		if (!projectId) return;
		syncing = true;
		try {
			const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
			const result = await syncArchitecture(token, projectId, {
				apply: true,
				version_id: selectedVersionId || undefined
			});
			syncDiff = result.diff;
			showSyncDiff = false;
			onSync?.(result.diff);
			toast.success('架构已同步');
		} catch {
			toast.error('架构同步失败');
		} finally {
			syncing = false;
		}
	}
</script>

<div class="pm-mindmap flex flex-col h-full bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
	<!-- Toolbar -->
	<div class="flex items-center gap-2 px-4 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 flex-wrap">
		{#if !readonly}
			<button
				class="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
				onclick={() => addNode(selectedNodeId)}
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
				>
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
					</svg>
					删除节点
				</button>
			{/if}
		{/if}

		{#if projectId}
			<button
				class="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors disabled:opacity-50"
				disabled={syncing}
				onclick={handleSync}
			>
				<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
				</svg>
				{syncing ? '同步中...' : '同步架构'}
			</button>
		{/if}

		{#if versions.length > 0}
			<select
				class="px-2 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
				bind:value={selectedVersionId}
			>
				<option value="">所有版本</option>
				{#each versions as ver (ver.id)}
					<option value={ver.id}>{ver.versionNumber}{ver.label ? ` - ${ver.label}` : ''}</option>
				{/each}
			</select>
		{/if}

		<div class="flex-1"></div>

		{#if isLargeGraph}
			<span class="text-xs text-gray-500 dark:text-gray-400">
				{visibleNodeCount}/{totalNodeCount} 节点可见
			</span>
		{:else}
			<span class="text-xs text-gray-500 dark:text-gray-400">
				{#if selectedNodeId}
					已选择: {selectedNodeId}
				{:else}
					点击节点导航至对应模块
				{/if}
			</span>
		{/if}
	</div>

	<!-- Mind Map Canvas -->
	<div class="flex-1 relative">
		<SvelteFlow
			nodes={$displayNodes}
			edges={$displayEdges}
			onnodeclick={handleNodeClick}
			onnodemouseover={handleNodeMouseOver}
			onnodemouseout={handleNodeMouseOut}
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

		<!-- Tooltip -->
		{#if hoveredNodeData}
			{@const hd = hoveredNodeData}
			<div
				class="absolute top-3 right-3 z-10 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-3 max-w-xs pointer-events-none"
			>
				<div class="font-medium text-sm text-gray-900 dark:text-white mb-1">{hd.label}</div>
				<div class="text-xs text-gray-500 dark:text-gray-400 space-y-0.5">
					<div>类型: {hd.metadata?.moduleType || hd.type}</div>
					{#if hd.metadata?.status}
						<div>状态: {hd.metadata.status}</div>
					{/if}
					{#if hd.metadata?.priority}
						<div>优先级: {hd.metadata.priority}</div>
					{/if}
					{#if hd.metadata?.versionId}
						<div>版本: {hd.metadata.versionId}</div>
					{/if}
					{#if hd.moduleRef}
						<div class="text-blue-500">可导航至条目</div>
					{/if}
				</div>
			</div>
		{/if}
	</div>
</div>

<!-- Sync Diff Modal -->
{#if showSyncDiff && syncDiff}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
		role="dialog"
		aria-modal="true"
		onclick={() => (showSyncDiff = false)}
	>
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div
			class="bg-white dark:bg-gray-900 rounded-3xl border border-gray-100/30 dark:border-gray-850/30 shadow-xl w-full max-w-lg mx-4 p-6 max-h-[80vh] overflow-y-auto"
			onclick={(e) => e.stopPropagation()}
		>
			<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">架构变更</h2>
			<p class="text-sm text-gray-500 dark:text-gray-400 mb-4">检测到以下变更，确认后将更新架构图。</p>

			<div class="space-y-3 mb-4">
				{#if syncDiff.added.length > 0}
					<div>
						<h3 class="text-sm font-medium text-green-600 dark:text-green-400 mb-1">新增 ({syncDiff.added.length})</h3>
						{#each syncDiff.added as node}
							<div class="text-sm text-gray-700 dark:text-gray-300 px-3 py-1.5 rounded-xl bg-green-50 dark:bg-green-900/20 mb-1">
								{node.label} <span class="text-xs text-gray-400">({node.metadata?.moduleType || 'unknown'})</span>
							</div>
						{/each}
					</div>
				{/if}

				{#if syncDiff.removed.length > 0}
					<div>
						<h3 class="text-sm font-medium text-red-600 dark:text-red-400 mb-1">移除 ({syncDiff.removed.length})</h3>
						{#each syncDiff.removed as node}
							<div class="text-sm text-gray-700 dark:text-gray-300 px-3 py-1.5 rounded-xl bg-red-50 dark:bg-red-900/20 mb-1">
								{node.label} <span class="text-xs text-gray-400">({node.metadata?.moduleType || 'unknown'})</span>
							</div>
						{/each}
					</div>
				{/if}

				{#if syncDiff.modified.length > 0}
					<div>
						<h3 class="text-sm font-medium text-yellow-600 dark:text-yellow-400 mb-1">变更 ({syncDiff.modified.length})</h3>
						{#each syncDiff.modified as node}
							<div class="text-sm text-gray-700 dark:text-gray-300 px-3 py-1.5 rounded-xl bg-yellow-50 dark:bg-yellow-900/20 mb-1">
								{node.label} <span class="text-xs text-gray-400">({node.metadata?.moduleType || 'unknown'})</span>
							</div>
						{/each}
					</div>
				{/if}

				{#if syncDiff.added.length === 0 && syncDiff.removed.length === 0 && syncDiff.modified.length === 0}
					<p class="text-sm text-gray-500 dark:text-gray-400 text-center py-4">无变更</p>
				{/if}
			</div>

			<div class="flex justify-end gap-2">
				<button
					class="px-3 py-1.5 rounded-xl bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
					onclick={() => (showSyncDiff = false)}
				>
					取消
				</button>
				<button
					class="px-3 py-1.5 rounded-xl bg-green-600 text-white text-sm font-medium hover:bg-green-700 transition-colors"
					onclick={handleApplySync}
				>
					应用变更
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.pm-mindmap :global(.svelte-flow__node) {
		font-size: 14px;
		font-weight: 500;
		cursor: pointer;
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
