<script lang="ts">
	import { writable } from 'svelte/store';
	import type { FlowchartData, FlowchartNode } from '$lib/apis/pm/types';
	import type { ModuleEntry } from '$lib/apis/pm/types';
	import ReactFlowCanvas from './reactflow/ReactFlowCanvas.svelte';
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

	// ReactFlow refs
	let reactFlowCanvasRef: any = $state(null);

	// Track selected node for config panel
	let selectedNodeId = $state<string | null>(null);
	let selectedNodeData = $state<Record<string, unknown> | null>(null);
	let activePanel = $state<'config' | 'traceability'>('config');

	// Convert FlowchartData to ReactFlow format
	function convertToReactFlow(data: FlowchartData) {
		const nodes = (data.nodes || []).map(node => ({
			id: node.id,
			type: 'default',
			position: node.position || { x: 0, y: 0 },
			data: {
				label: node.data?.label || '',
				description: node.data?.description || '',
				shape: node.data?.style?.shape || 'rectangle',
				backgroundColor: node.data?.style?.backgroundColor,
				borderColor: node.data?.style?.borderColor,
				inputParams: node.data?.inputParams || [],
				outputParams: node.data?.outputParams || [],
				traceability: node.data?.traceability,
				customData: node.data
			},
			style: getNodeStyle(node)
		}));

		const edges = (data.edges || []).map(edge => ({
			id: edge.id,
			source: edge.source,
			target: edge.target,
			label: edge.label || '',
			type: 'smoothstep',
			markerEnd: { type: 'arrowclosed' }
		}));

		return { nodes, edges };
	}

	function getNodeStyle(node: FlowchartNode) {
		const shape = node.data?.style?.shape || 'rectangle';
		const baseStyle: Record<string, string> = {
			width: '140px',
			height: shape === 'diamond' ? '100px' : '60px',
			backgroundColor: node.data?.style?.backgroundColor || '#dbeafe',
			borderColor: node.data?.style?.borderColor || '#93c5fd',
			borderWidth: '2px',
			borderStyle: 'solid',
			display: 'flex',
			alignItems: 'center',
			justifyContent: 'center',
			fontSize: '14px',
			fontWeight: '500',
			color: '#1f2937'
		};

		// Apply shape-specific styles
		switch (shape) {
			case 'rounded':
				baseStyle.borderRadius = '12px';
				break;
			case 'circle':
				baseStyle.borderRadius = '50%';
				baseStyle.width = '80px';
				baseStyle.height = '80px';
				break;
			case 'diamond':
				baseStyle.transform = 'rotate(45deg)';
				baseStyle.width = '80px';
				baseStyle.height = '80px';
				break;
			case 'ellipse':
				baseStyle.borderRadius = '50% / 30%';
				baseStyle.width = '120px';
				break;
		}

		return baseStyle;
	}

	// Convert ReactFlow format back to FlowchartData
	function convertFromReactFlow(nodes: any[], edges: any[]): FlowchartData {
		const flowchartNodes: FlowchartNode[] = nodes.map(node => ({
			id: node.id,
			type: node.data?.customData?.type || 'process',
			position: node.position || { x: 0, y: 0 },
			data: {
				label: node.data?.label || '',
				description: node.data?.description || '',
				style: {
					shape: node.data?.shape || 'rectangle',
					backgroundColor: node.data?.backgroundColor,
					borderColor: node.data?.borderColor
				},
				inputParams: node.data?.inputParams || [],
				outputParams: node.data?.outputParams || [],
				traceability: node.data?.traceability
			}
		}));

		const flowchartEdges = edges.map(edge => ({
			id: edge.id,
			source: edge.source,
			target: edge.target,
			label: edge.label || ''
		}));

		return { nodes: flowchartNodes, edges: flowchartEdges };
	}

	// Initial data conversion
	let reactFlowData = $state(convertToReactFlow(flowchartData));

	$effect(() => {
		reactFlowData = convertToReactFlow(flowchartData);
	});

	// Debounce for auto-save
	let saveTimer: ReturnType<typeof setTimeout> | undefined;

	function handleNodesChange(nodes: any[]) {
		clearTimeout(saveTimer);
		saveTimer = setTimeout(() => {
			const data = convertFromReactFlow(nodes, reactFlowData.edges);
			onChange(data);
		}, 300);
	}

	function handleEdgesChange(edges: any[]) {
		clearTimeout(saveTimer);
		saveTimer = setTimeout(() => {
			const data = convertFromReactFlow(reactFlowData.nodes, edges);
			onChange(data);
		}, 300);
	}

	function handleConnect(connection: any) {
		const newEdge = {
			id: `edge-${connection.source}-${connection.target}-${Date.now()}`,
			source: connection.source,
			target: connection.target,
			label: '',
			type: 'smoothstep',
			markerEnd: { type: 'arrowclosed' }
		};
		reactFlowData.edges = [...reactFlowData.edges, newEdge];
		handleEdgesChange(reactFlowData.edges);
	}

	function handleNodeClick(node: any) {
		if (readonly) return;
		selectedNodeId = node.id;
		selectedNodeData = node.data || {};
		activePanel = 'config';
	}

	function handlePaneClick() {
		selectedNodeId = null;
		selectedNodeData = null;
	}

	function updateNodeData(nodeId: string, data: Partial<FlowchartNode['data']>) {
		reactFlowData.nodes = reactFlowData.nodes.map(node => {
			if (node.id === nodeId) {
				const updatedNode = { ...node };
				updatedNode.data = { ...updatedNode.data, ...data };
				
				// Update style if shape or colors changed
				if (data.style) {
					updatedNode.style = getNodeStyle({
						...node,
						data: { ...node.data, ...data }
					} as FlowchartNode);
				}
				
				return updatedNode;
			}
			return node;
		});
		
		// Trigger save
		handleNodesChange(reactFlowData.nodes);
	}

	function handleKeydown(event: KeyboardEvent) {
		if ((event.key === 'Delete' || event.key === 'Backspace') && selectedNodeId) {
			const target = event.target as HTMLElement;
			if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') return;
			event.preventDefault();
			
			// Delete selected node and its edges
			reactFlowData.nodes = reactFlowData.nodes.filter(n => n.id !== selectedNodeId);
			reactFlowData.edges = reactFlowData.edges.filter(e => e.source !== selectedNodeId && e.target !== selectedNodeId);
			
			selectedNodeId = null;
			selectedNodeData = null;
			
			handleNodesChange(reactFlowData.nodes);
		}
	}

	// Export functions
	export function exportToPNG() {
		// ReactFlow doesn't have built-in PNG export, would need html-to-image
		console.warn('PNG export not yet implemented for ReactFlow');
	}

	export function exportToSVG() {
		console.warn('SVG export not yet implemented for ReactFlow');
	}

	export function exportToMarkdown() {
		const data = flowchartData;
		let markdown = '# 流程图\n\n';
		
		if (data.nodes && data.nodes.length > 0) {
			markdown += '## 节点\n\n';
			for (const node of data.nodes) {
				markdown += `- **${node.data?.label || '未命名'}** (${node.type})\n`;
				if (node.data?.description) {
					markdown += `  - 描述: ${node.data.description}\n`;
				}
				if (node.data?.inputParams && node.data.inputParams.length > 0) {
					markdown += `  - 输入参数: ${node.data.inputParams.join(', ')}\n`;
				}
				if (node.data?.outputParams && node.data.outputParams.length > 0) {
					markdown += `  - 输出参数: ${node.data.outputParams.join(', ')}\n`;
				}
				markdown += '\n';
			}
		}
		
		if (data.edges && data.edges.length > 0) {
			markdown += '## 连接\n\n';
			for (const edge of data.edges) {
				const sourceNode = data.nodes.find(n => n.id === edge.source);
				const targetNode = data.nodes.find(n => n.id === edge.target);
				markdown += `- ${sourceNode?.data?.label || edge.source} → ${targetNode?.data?.label || edge.target}\n`;
			}
		}
		
		const blob = new Blob([markdown], { type: 'text/markdown' });
		const url = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = url;
		link.download = 'flowchart.md';
		link.click();
		URL.revokeObjectURL(url);
	}

	export function exportToDrawIO() {
		const data = flowchartData;
		let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
		xml += '<mxfile host="app.diagrams.net" modified="' + new Date().toISOString() + '" agent="OpenWebUI" version="21.0.0" etag="" type="device">\n';
		xml += '  <diagram name="Page-1" id="">\n';
		xml += '    <mxGraphModel dx="800" dy="600" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">\n';
		xml += '      <root>\n';
		xml += '        <mxCell id="0" />\n';
		xml += '        <mxCell id="1" parent="0" />\n';
		
		for (const node of data.nodes || []) {
			const pos = node.position || { x: 0, y: 0 };
			const shape = node.data?.style?.shape || 'rectangle';
			let mxShape = 'rectangle';
			if (shape === 'ellipse' || shape === 'circle') mxShape = 'ellipse';
			if (shape === 'diamond') mxShape = 'rhombus';
			
			xml += `        <mxCell id="${node.id}" value="${node.data?.label || ''}" style="shape=${mxShape};fillColor=${node.data?.style?.backgroundColor || '#dbeafe'};strokeColor=${node.data?.style?.borderColor || '#93c5fd'};" vertex="1" parent="1">\n`;
			xml += `          <mxGeometry x="${pos.x}" y="${pos.y}" width="120" height="60" as="geometry" />\n`;
			xml += '        </mxCell>\n';
		}
		
		for (const edge of data.edges || []) {
			xml += `        <mxCell id="${edge.id}" value="${edge.label || ''}" edge="1" source="${edge.source}" target="${edge.target}" parent="1">\n`;
			xml += '          <mxGeometry relative="1" as="geometry" />\n';
			xml += '        </mxCell>\n';
		}
		
		xml += '      </root>\n';
		xml += '    </mxGraphModel>\n';
		xml += '  </diagram>\n';
		xml += '</mxfile>';
		
		const blob = new Blob([xml], { type: 'application/xml' });
		const url = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = url;
		link.download = 'flowchart.drawio';
		link.click();
		URL.revokeObjectURL(url);
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="w-full h-full relative" style="min-height: 400px;">
	<ReactFlowCanvas
		bind:this={reactFlowCanvasRef}
		nodes={reactFlowData.nodes}
		edges={reactFlowData.edges}
		onNodesChange={handleNodesChange}
		onEdgesChange={handleEdgesChange}
		onConnect={handleConnect}
		onNodeClick={handleNodeClick}
		onPaneClick={handlePaneClick}
		readonly={readonly}
	/>

	{#if selectedNodeId && selectedNodeData && !readonly}
		{@const node = reactFlowData.nodes.find(n => n.id === selectedNodeId)}
		{#if node}
			{@const fcNode: FlowchartNode = {
				id: selectedNodeId,
				type: (selectedNodeData.type as string) || 'process',
				position: node.position || { x: 0, y: 0 },
				data: {
					label: (selectedNodeData.label as string) || '',
					description: selectedNodeData.description as string | undefined,
					style: {
						shape: (selectedNodeData.shape as 'rectangle' | 'rounded' | 'circle' | 'diamond' | 'ellipse') || 'rectangle',
						backgroundColor: selectedNodeData.backgroundColor as string | undefined,
						borderColor: selectedNodeData.borderColor as string | undefined
					},
					inputParams: (selectedNodeData.inputParams as string[]) || [],
					outputParams: (selectedNodeData.outputParams as string[]) || [],
					traceability: selectedNodeData.traceability as any
				}
			}}
			{#if activePanel === 'config'}
				<NodeConfigPanel
					node={fcNode}
					{parameterEntries}
					{projectId}
					onUpdate={updateNodeData}
					onClose={() => { selectedNodeId = null; selectedNodeData = null; }}
					onViewTraceability={() => activePanel = 'traceability'}
				/>
			{:else}
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
					onViewConfig={() => activePanel = 'config'}
				/>
			{/if}
		{/if}
	{/if}
</div>
