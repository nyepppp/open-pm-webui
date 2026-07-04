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

	interface Props {
		flowchartData: FlowchartData;
		onChange: (data: FlowchartData) => void;
		readonly?: boolean;
		parameterEntries?: ModuleEntry[];
	}

	let { flowchartData, onChange, readonly = false, parameterEntries = [] }: Props = $props();

	// Custom node types — must be stable (declared outside render cycle)
	// Use `as any` for nodeTypes/edgeTypes to bypass Svelte 5 Component vs Svelte 4 class mismatch
	// This is a known @xyflow/svelte@0.1.x incompatibility with Svelte 5 component types
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

	// SvelteFlow 0.1.x uses Writable stores for nodes/edges
	let nodesStore = writable<Node[]>(
		(flowchartData.nodes || []).map((n: any) => ({
			id: n.id,
			type: n.type,
			position: n.position,
			data: {
				label: n.data.label,
				description: n.data.description,
				type: n.type,
				style: n.data.style,
				inputParams: n.data.inputParams,
				outputParams: n.data.outputParams
			}
		}))
	);
	let edgesStore = writable<Edge[]>(
		(flowchartData.edges || []).map((e: any) => ({
			id: e.id,
			source: e.source,
			target: e.target,
			label: e.label,
			type: 'custom',
			data: { style: e.style }
		}))
	);

	// Track selected node for config panel
	let selectedNodeId = $state<string | null>(null);
	let selectedNode = $state<Node | null>(null);

	// Debounce for auto-save
	let saveTimer: ReturnType<typeof setTimeout> | undefined;

	function emitChange(ns: Node[], es: Edge[]) {
	 clearTimeout(saveTimer);
		saveTimer = setTimeout(() => {
			const data: FlowchartData = {
				nodes: ns.map(n => ({
					id: n.id,
					type: n.type,
					position: n.position,
					data: {
						label: (n.data as Record<string, unknown>)?.label as string || '',
						description: (n.data as Record<string, unknown>)?.description as string | undefined,
						style: (n.data as Record<string, unknown>)?.style as Record<string, unknown> | undefined,
						inputParams: ((n.data as Record<string, unknown>)?.inputParams as string[]) || [],
						outputParams: ((n.data as Record<string, unknown>)?.outputParams as string[]) || []
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
		nodesStore.update(ns => ns.filter(n => n.id !== selectedNodeId));
		edgesStore.update(es => es.filter(e => e.source !== selectedNodeId && e.target !== selectedNodeId));
		selectedNodeId = null;
		selectedNode = null;
	}

	function onNodeClick(event: { detail: { node: Node } }) {
		selectedNodeId = event.detail.node.id;
		selectedNode = event.detail.node;
	}

	function onPaneClick() {
		selectedNodeId = null;
		selectedNode = null;
	}

	function updateNodeData(nodeId: string, data: Record<string, unknown>) {
		nodesStore.update(ns => ns.map(n =>
			n.id === nodeId
				? { ...n, data: { ...n.data, ...data } }
				: n
		));
		// Update selected node reference
		if (selectedNodeId === nodeId) {
			const updated = currentNodes.find(n => n.id === nodeId);
			if (updated) selectedNode = updated;
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if ((event.key === 'Delete' || event.key === 'Backspace') && selectedNodeId) {
			// Only delete if not focused in an input
			const target = event.target as HTMLElement;
			if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') return;
			event.preventDefault();
			deleteSelected();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="w-full h-full relative">
	<SvelteFlow
		nodes={nodesStore}
		edges={edgesStore}
		{nodeTypes}
		{edgeTypes}
		onconnect={onConnect}
		on:nodeclick={onNodeClick}
		on:paneclick={onPaneClick}
		fitView
		nodesDraggable={!readonly}
		nodesConnectable={!readonly}
		elementsSelectable={!readonly}
		deleteKey={readonly ? null : 'Backspace'}
		class="bg-gray-50 dark:bg-gray-900"
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

	{#if selectedNode && !readonly}
		{@const fcNode = {
			id: selectedNode.id,
			type: selectedNode.type,
			position: selectedNode.position,
			data: {
				label: (selectedNode.data as Record<string, unknown>)?.label as string || '',
				description: (selectedNode.data as Record<string, unknown>)?.description as string | undefined,
				style: (selectedNode.data as Record<string, unknown>)?.style as Record<string, unknown> | undefined,
				inputParams: ((selectedNode.data as Record<string, unknown>)?.inputParams as string[]) || [],
				outputParams: ((selectedNode.data as Record<string, unknown>)?.outputParams as string[]) || []
			}
		}}
		<NodeConfigPanel
			node={fcNode}
			{parameterEntries}
			onUpdate={updateNodeData}
			onClose={() => { selectedNodeId = null; selectedNode = null; }}
		/>
	{/if}
</div>
