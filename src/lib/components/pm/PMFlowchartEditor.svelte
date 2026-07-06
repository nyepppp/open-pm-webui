<script lang="ts">
	import { writable } from 'svelte/store';
	import {
		SvelteFlow,
		Background,
		Controls,
		MiniMap,
		Panel,
		type Node,
		type Edge,
		type Connection,
		type NodeTypes,
		type EdgeTypes
	} from '@xyflow/svelte';
	import '@xyflow/svelte/dist/style.css';
	import type { FlowchartData } from '$lib/apis/pm/types';
	import type { ModuleEntry } from '$lib/apis/pm/types';
	import DynamicNode from './flowchart/DynamicNode.svelte';
	import CustomEdge from './flowchart/CustomEdge.svelte';
	import NodeConfigPanel from './flowchart/NodeConfigPanel.svelte';
	import TraceabilitySidebar from './flowchart/TraceabilitySidebar.svelte';

	interface Props {
		flowchartData: FlowchartData;
		onChange: (data: FlowchartData) => void;
		readonly?: boolean;
		parameterEntries?: ModuleEntry[];
		projectId?: string;
	}

	let { flowchartData, onChange, readonly = false, parameterEntries = [], projectId = '' }: Props = $props();

	// Custom node types — must be stable (declared outside render cycle)
	const nodeTypes: NodeTypes = {
		start: DynamicNode as any,
		process: DynamicNode as any,
		decision: DynamicNode as any,
		end: DynamicNode as any,
		'parameter-input': DynamicNode as any,
		'parameter-output': DynamicNode as any,
		default: DynamicNode as any
	};

	const edgeTypes: EdgeTypes = {
		custom: CustomEdge as any
	};

	// Convert FlowchartData nodes/edges to @xyflow/svelte Node/Edge format
	function toXyNodes(nodes: FlowchartData['nodes']): Node[] {
		return (nodes || []).map((n: any) => ({
			id: n.id,
			type: n.type || 'process',
			position: n.position || { x: 0, y: 0 },
			data: {
				label: n.data?.label || '',
				description: n.data?.description,
				type: n.type,
				style: n.data?.style,
				inputParams: n.data?.inputParams || [],
				outputParams: n.data?.outputParams || []
			}
		}));
	}

	function toXyEdges(edges: FlowchartData['edges']): Edge[] {
		return (edges || []).map((e: any) => ({
			id: e.id,
			source: e.source,
			target: e.target,
			label: e.label,
			type: 'custom',
			data: { style: e.style }
		}));
	}

	// SvelteFlow 0.1.x uses Writable stores
	// Initialize empty; the $effect below populates from flowchartData on mount and on prop changes
	let nodesStore = writable<Node[]>([]);
	let edgesStore = writable<Edge[]>([]);

	// When flowchartData prop changes externally, resync stores
	// Guard: skip if data is identical to current store content (prevents infinite loop
	// when onChange → prop change → $effect → set stores → subscribe → emitChange → onChange)
	let lastSyncedNodesJson = $state('');
	$effect(() => {
		const xyNodes = toXyNodes(flowchartData.nodes);
		const xyEdges = toXyEdges(flowchartData.edges);
		const json = JSON.stringify(xyNodes.map(n => n.id));
		if (json !== lastSyncedNodesJson) {
			lastSyncedNodesJson = json;
			nodesStore.set(xyNodes);
			edgesStore.set(xyEdges);
		}
	});

	// Track selected node for config panel via on:nodeclick / on:paneclick events
	let selectedNodeId = $state<string | null>(null);
	let selectedNodeData = $state<Record<string, unknown> | null>(null);

	function onNodeClick(event: CustomEvent<{ node: Node; event: MouseEvent | TouchEvent }>) {
		const node = event.detail.node;
		selectedNodeId = node.id;
		selectedNodeData = node.data as Record<string, unknown>;
	}

	// eslint-disable-next-line @typescript-eslint/no-unused-vars
	function onPaneClick(_event: CustomEvent<{ event: MouseEvent | TouchEvent }>) {
		selectedNodeId = null;
		selectedNodeData = null;
	}

	// Debounce for auto-save
	let saveTimer: ReturnType<typeof setTimeout> | undefined;

	function emitChange(ns: Node[], es: Edge[]) {
		clearTimeout(saveTimer);
		saveTimer = setTimeout(() => {
			const data: FlowchartData = {
				nodes: ns.map(n => ({
					id: n.id,
					type: n.type || 'process',
					position: n.position,
					data: {
						label: (n.data as Record<string, unknown>)?.label as string || '',
						description: (n.data as Record<string, unknown>)?.description as string | undefined,
						style: (n.data as Record<string, unknown>)?.style as Record<string, unknown> | undefined,
						inputParams: ((n.data as Record<string, unknown>)?.inputParams as string[]) || [],
						outputParams: ((n.data as Record<string, unknown>)?.outputParams as string[]) || [],
						traceability: ((n.data as Record<string, unknown>)?.traceability as Record<string, unknown>) || undefined
					}
				})),
				edges: es.map(e => ({
					id: e.id,
					source: e.source,
					target: e.target,
					label: e.label,
					style: ((e.data as Record<string, unknown>)?.style as Record<string, unknown>) || undefined
				}))
			};
			onChange(data);
		}, 300);
	}

	// Subscribe to store changes for auto-save
	let currentNodes: Node[] = [];
	let currentEdges: Edge[] = [];
	nodesStore.subscribe((ns) => { currentNodes = ns; emitChange(ns, currentEdges); });
	edgesStore.subscribe((es) => { currentEdges = es; emitChange(currentNodes, es); });

	function onConnect(connection: Connection) {
		if (readonly) return;
		const newEdge: Edge = {
			id: `e-${connection.source}-${connection.target}-${Date.now()}`,
			source: connection.source,
			target: connection.target,
			sourceHandle: connection.sourceHandle || undefined,
			targetHandle: connection.targetHandle || undefined,
			type: 'custom',
			data: { style: {} }
		};
		edgesStore.update(es => [...es, newEdge]);
	}

	function addNode(type: string) {
		if (readonly) return;
		const id = `node-${Date.now()}`;
		const labelMap: Record<string, string> = {
			start: '开始', end: '结束', decision: '判断', process: '处理',
			'parameter-input': '参数输入', 'parameter-output': '参数输出'
		};
		const newNode: Node = {
			id,
			type,
			position: { x: 200 + Math.random() * 200, y: 100 + Math.random() * 200 },
			data: { label: labelMap[type] || '节点', type, inputParams: [], outputParams: [] }
		};
		nodesStore.update(ns => [...ns, newNode]);
	}

	function deleteSelected() {
		if (readonly || !selectedNodeId) return;
		const id = selectedNodeId;
		nodesStore.update(ns => ns.filter(n => n.id !== id));
		edgesStore.update(es => es.filter(e => e.source !== id && e.target !== id));
		selectedNodeId = null;
		selectedNodeData = null;
	}

	function updateNodeData(nodeId: string, data: Record<string, unknown>) {
		nodesStore.update(ns => ns.map(n =>
			n.id === nodeId
				? { ...n, data: { ...n.data, ...data } }
				: n
		));
		// Update selected node data
		if (selectedNodeId === nodeId) {
			const updated = currentNodes.find(n => n.id === nodeId);
			if (updated) selectedNodeData = updated.data as Record<string, unknown>;
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if ((event.key === 'Delete' || event.key === 'Backspace') && selectedNodeId) {
			const target = event.target as HTMLElement;
			if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') return;
			event.preventDefault();
			deleteSelected();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="w-full h-full relative" style="min-height: 400px;">
	<SvelteFlow
		nodes={nodesStore}
		edges={edgesStore}
		{nodeTypes}
		{edgeTypes}
		onconnect={onConnect}
		fitView
		nodesDraggable={!readonly}
		nodesConnectable={!readonly}
		elementsSelectable={!readonly}
		deleteKey={readonly ? null : 'Backspace'}
		on:nodeclick={onNodeClick}
		on:paneclick={onPaneClick}
	>
		<Background patternColor="#CBD5E1" gap={20} />
		<Controls />
		<MiniMap />
	</SvelteFlow>

	{#if !readonly}
		<Panel position="top-left">
			<div class="bg-white dark:bg-gray-800 p-2 rounded-lg shadow-lg flex flex-col gap-1.5">
				<div class="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-0.5">节点类型</div>
				<div class="grid grid-cols-2 gap-1.5">
					<button class="px-2.5 py-1 text-xs text-white rounded transition bg-green-500 hover:bg-green-600" onclick={() => addNode('start')}>开始</button>
					<button class="px-2.5 py-1 text-xs text-white rounded transition bg-red-500 hover:bg-red-600" onclick={() => addNode('end')}>结束</button>
					<button class="px-2.5 py-1 text-xs text-white rounded transition bg-blue-500 hover:bg-blue-600" onclick={() => addNode('process')}>处理</button>
					<button class="px-2.5 py-1 text-xs text-white rounded transition bg-yellow-500 hover:bg-yellow-600" onclick={() => addNode('decision')}>判断</button>
					<button class="px-2.5 py-1 text-xs text-white rounded transition bg-purple-500 hover:bg-purple-600" onclick={() => addNode('parameter-input')}>参数输入</button>
					<button class="px-2.5 py-1 text-xs text-white rounded transition bg-pink-500 hover:bg-pink-600" onclick={() => addNode('parameter-output')}>参数输出</button>
				</div>
				{#if selectedNodeId}
					<button class="px-2.5 py-1 text-xs text-white rounded transition bg-gray-500 hover:bg-gray-600 mt-1" onclick={deleteSelected}>删除选中节点</button>
				{/if}
			</div>
		</Panel>
	{/if}

	{#if selectedNodeId && selectedNodeData && !readonly}
		{@const fcNode = {
			id: selectedNodeId,
			type: (selectedNodeData.type as string) || 'process',
			position: { x: 0, y: 0 },
			data: {
				label: (selectedNodeData.label as string) || '',
				description: selectedNodeData.description as string | undefined,
				style: selectedNodeData.style as Record<string, unknown> | undefined,
				inputParams: (selectedNodeData.inputParams as string[]) || [],
				outputParams: (selectedNodeData.outputParams as string[]) || [],
				traceability: selectedNodeData.traceability as Record<string, unknown> | undefined
			}
		}}
		<NodeConfigPanel
			node={fcNode}
			{parameterEntries}
			{projectId}
			onUpdate={updateNodeData}
			onClose={() => { selectedNodeId = null; selectedNodeData = null; }}
		/>
	{/if}

	{#if selectedNodeId && selectedNodeData}
		<TraceabilitySidebar
			nodeId={selectedNodeId}
			nodeData={{
				label: (selectedNodeData.label as string) || '',
				description: selectedNodeData.description as string | undefined,
				inputParams: (selectedNodeData.inputParams as string[]) || [],
				outputParams: (selectedNodeData.outputParams as string[]) || [],
				traceability: selectedNodeData.traceability as {
					entityType: string;
					entityId: string;
					entityName: string;
					versionNumber?: string;
					boundAt: number;
					boundBy?: string;
				} | undefined
			}}
			{projectId}
			onClose={() => { selectedNodeId = null; selectedNodeData = null; }}
		/>
	{/if}
</div>
