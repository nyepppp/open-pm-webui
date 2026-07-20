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
		entryId?: string;
	}

	let { flowchartData, onChange, readonly = false, parameterEntries = [], projectId = '', entryId = '' }: Props = $props();

	// ReactFlow refs
	let reactFlowCanvasRef: any = $state(null);

	// Track selected node for config panel
	let selectedNodeId = $state<string | null>(null);
	let selectedNodeData = $state<Record<string, unknown> | null>(null);
	let activePanel = $state<'config' | 'traceability'>('config');
	
	// 编辑器模式
	let editorMode = $state<'select' | 'pan' | 'connect' | 'add'>('select');
	let selectedNodeType = $state<string>('rectangle');

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
			arrowEnd: true,
			style: edge.style || {}
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
	let reactFlowData = $state({ nodes: [] as any[], edges: [] as any[] });

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

	// 节点创建功能
	const nodeShapes = [
		{ type: 'rectangle', label: '矩形', icon: 'M2 2h20v20H2z' },
		{ type: 'rounded', label: '圆角矩形', icon: 'M2 2h20v20H2z' },
		{ type: 'circle', label: '圆形', icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z' },
		{ type: 'diamond', label: '菱形', icon: 'M12 2L2 12l10 10 10-10L12 2z' },
		{ type: 'ellipse', label: '椭圆', icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z' }
	];

	function createNode(shape: string) {
		const newNode: any = {
			id: `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
			type: 'default',
			position: { 
				x: 100 + Math.random() * 200, 
				y: 100 + Math.random() * 200 
			},
			data: {
				label: '新节点',
				description: '',
				shape: shape,
				backgroundColor: '#dbeafe',
				borderColor: '#93c5fd',
				inputParams: [],
				outputParams: [],
				traceability: undefined,
				customData: {}
			},
			style: getNodeStyle({
				id: '',
				type: 'process',
				position: { x: 0, y: 0 },
				data: {
					label: '新节点',
					style: { shape: shape as any }
				}
			} as FlowchartNode)
		};
		
		reactFlowData.nodes = [...reactFlowData.nodes, newNode];
		handleNodesChange(reactFlowData.nodes);
	}

	function clearCanvas() {
		if (confirm('确定要清空画布吗？此操作不可撤销。')) {
			reactFlowData.nodes = [];
			reactFlowData.edges = [];
			handleNodesChange(reactFlowData.nodes);
			handleEdgesChange(reactFlowData.edges);
		}
	}
	
	// 切换模式
	function setMode(mode: 'select' | 'pan' | 'connect' | 'add') {
		editorMode = mode;
	}

	// Export functions
	export function exportToPNG() {
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

	// Import functions
	function importFromFile() {
		const input = document.createElement('input');
		input.type = 'file';
		input.accept = '.md,.drawio,.xml,.json,.csv';
		input.onchange = (e: Event) => {
			const file = (e.target as HTMLInputElement).files?.[0];
			if (!file) return;
			
			const reader = new FileReader();
			reader.onload = (event) => {
				const content = event.target?.result as string;
				if (!content) return;
				
				try {
					const importedData = parseFlowchartData(content, file.name);
					if (importedData) {
						reactFlowData = {
							nodes: importedData.nodes.map(node => ({
								...node,
								style: getNodeStyle(node)
							})),
							edges: importedData.edges.map(edge => ({
								...edge,
								arrowEnd: true
							}))
						};
						handleNodesChange(reactFlowData.nodes);
						handleEdgesChange(reactFlowData.edges);
					}
				} catch (error) {
					console.error('导入失败:', error);
					alert('导入失败，请检查文件格式');
				}
			};
			reader.readAsText(file);
		};
		input.click();
	}

	function parseFlowchartData(content: string, filename: string): { nodes: any[]; edges: any[] } | null {
		const ext = filename.split('.').pop()?.toLowerCase();
		
		if (ext === 'md') {
			return parseMarkdown(content);
		} else if (ext === 'drawio' || ext === 'xml') {
			return parseDrawIO(content);
		} else if (ext === 'json') {
			return parseJSON(content);
		} else if (ext === 'csv') {
			return parseCSV(content);
		}
		
		return null;
	}

	function parseMarkdown(content: string): { nodes: any[]; edges: any[] } {
		const nodes: any[] = [];
		const edges: any[] = [];
		const nodeMap = new Map<string, string>();
		
		const lines = content.split('\n');
		let inNodesSection = false;
		let inEdgesSection = false;
		
		for (const line of lines) {
			const trimmed = line.trim();
			
			if (trimmed === '## 节点') {
				inNodesSection = true;
				inEdgesSection = false;
				continue;
			}
			if (trimmed === '## 连接') {
				inNodesSection = false;
				inEdgesSection = true;
				continue;
			}
			
			if (inNodesSection && trimmed.startsWith('- **')) {
				const match = trimmed.match(/- \*\*(.+?)\*\*/);
				if (match) {
					const nodeId = `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
					const label = match[1];
					nodeMap.set(label, nodeId);
					
					nodes.push({
						id: nodeId,
						type: 'process',
						position: { 
							x: 100 + Math.random() * 400, 
							y: 100 + Math.random() * 300 
						},
						data: {
							label: label,
							shape: 'rectangle',
							backgroundColor: '#dbeafe',
							borderColor: '#93c5fd',
							customData: {}
						}
					});
				}
			}
			
			if (inEdgesSection && trimmed.includes('→')) {
				const parts = trimmed.split('→').map(s => s.trim());
				if (parts.length === 2) {
					const sourceLabel = parts[0].replace(/^- /, '');
					const targetLabel = parts[1];
					const sourceId = nodeMap.get(sourceLabel);
					const targetId = nodeMap.get(targetLabel);
					
					if (sourceId && targetId) {
						edges.push({
							id: `edge-${sourceId}-${targetId}-${Date.now()}`,
							source: sourceId,
							target: targetId,
							label: '',
							lineType: 'straight',
							arrowEnd: true
						});
					}
				}
			}
		}
		
		return { nodes, edges };
	}

	function parseDrawIO(content: string): { nodes: any[]; edges: any[] } {
		const nodes: any[] = [];
		const edges: any[] = [];
		
		const parser = new DOMParser();
		const xmlDoc = parser.parseFromString(content, 'text/xml');
		
		const mxCells = xmlDoc.querySelectorAll('mxCell');
		const nodeMap = new Map<string, string>();
		
		for (const cell of mxCells) {
			const id = cell.getAttribute('id');
			const value = cell.getAttribute('value') || '';
			const vertex = cell.getAttribute('vertex');
			const edge = cell.getAttribute('edge');
			
			if (vertex === '1' && id) {
				const geometry = cell.querySelector('mxGeometry');
				const x = parseFloat(geometry?.getAttribute('x') || '0');
				const y = parseFloat(geometry?.getAttribute('y') || '0');
				
				nodeMap.set(id, id);
				nodes.push({
					id: id,
					type: 'process',
					position: { x, y },
					data: {
						label: value,
						shape: 'rectangle',
						backgroundColor: '#dbeafe',
						borderColor: '#93c5fd',
						customData: {}
					}
				});
			} else if (edge === '1' && id) {
				const source = cell.getAttribute('source');
				const target = cell.getAttribute('target');
				
				if (source && target) {
					edges.push({
						id: id,
						source: source,
						target: target,
						label: value,
						lineType: 'straight',
						arrowEnd: true
					});
				}
			}
		}
		
		return { nodes, edges };
	}

	function parseJSON(content: string): { nodes: any[]; edges: any[] } {
		const data = JSON.parse(content);
		return {
			nodes: (data.nodes || []).map((node: any) => ({
				...node,
				data: {
					...node.data,
					customData: node.data?.customData || {}
				}
			})),
			edges: (data.edges || []).map((edge: any) => ({
				...edge,
				arrowEnd: true
			}))
		};
	}

	function parseCSV(content: string): { nodes: any[]; edges: any[] } {
		const lines = content.split('\n');
		const nodes: any[] = [];
		const edges: any[] = [];
		const nodeMap = new Map<string, string>();
		
		for (const line of lines.slice(1)) {
			const parts = line.split(',').map(s => s.trim());
			if (parts.length >= 2) {
				const nodeId = `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
				const label = parts[0];
				nodeMap.set(label, nodeId);
				
				nodes.push({
					id: nodeId,
					type: 'process',
					position: { 
						x: 100 + Math.random() * 400, 
						y: 100 + Math.random() * 300 
					},
					data: {
						label: label,
						shape: 'rectangle',
						backgroundColor: '#dbeafe',
						borderColor: '#93c5fd',
						customData: {}
					}
				});
				
				if (parts[1] && parts[1] !== '') {
					const targetLabel = parts[1];
					const targetId = nodeMap.get(targetLabel);
					if (targetId) {
						edges.push({
							id: `edge-${nodeId}-${targetId}-${Date.now()}`,
							source: nodeId,
							target: targetId,
							label: parts[2] || '',
							lineType: 'straight',
							arrowEnd: true
						});
					}
				}
			}
		}
		
		return { nodes, edges };
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="w-full h-full flex flex-col" style="min-height: 400px;">
	<!-- 工具栏 -->
	{#if !readonly}
		<div class="flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
			<!-- 模式切换 -->
			<div class="flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-0.5">
				<button
					class="px-2 py-1 text-xs rounded-md transition {editorMode === 'select' ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}"
					title="选择模式 (V)"
					onclick={() => setMode('select')}
				>
					<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z" /></svg>
				</button>
				<button
					class="px-2 py-1 text-xs rounded-md transition {editorMode === 'pan' ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}"
					title="拖拽模式 (H)"
					onclick={() => setMode('pan')}
				>
					<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 9l-3 3 3 3M9 5l3-3 3 3M15 19l-3 3-3-3M19 9l3 3-3 3" /></svg>
				</button>
				<button
					class="px-2 py-1 text-xs rounded-md transition {editorMode === 'connect' ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}"
					title="连线模式 (L)"
					onclick={() => setMode('connect')}
				>
					<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
				</button>
			</div>
			
			<div class="w-px h-5 bg-gray-300 dark:bg-gray-600 mx-1"></div>
			
			<!-- 添加节点 -->
			{#if editorMode === 'add'}
				<div class="flex items-center gap-1">
					<span class="text-xs text-gray-500 dark:text-gray-400 mr-1">添加：</span>
					{#each nodeShapes as shape}
						<button
							class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition {selectedNodeType === shape.type ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600' : ''}"
							title={shape.label}
							onclick={() => { selectedNodeType = shape.type; createNode(shape.type); }}
						>
							<svg class="w-5 h-5 text-gray-600 dark:text-gray-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
								<path d={shape.icon} />
							</svg>
						</button>
					{/each}
				</div>
			{:else}
				<button
					class="px-2 py-1 text-xs rounded-md transition {selectedNodeType ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-gray-100 shadow-sm' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}"
					title="添加节点模式 (N)"
					onclick={() => setMode('add')}
				>
					<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 4v16m8-8H4" /></svg>
				</button>
			{/if}
			
			<div class="w-px h-5 bg-gray-300 dark:bg-gray-600 mx-1"></div>
			
			<button
				class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition text-gray-600 dark:text-gray-300"
				title="导入"
				onclick={() => importFromFile()}
			>
				<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0l-4 4m4-4v12" /></svg>
			</button>
			
			<button
				class="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition text-gray-600 dark:text-gray-300"
				title="导出"
				onclick={() => exportToMarkdown()}
			>
				<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
			</button>
			
			<button
				class="p-1.5 rounded hover:bg-red-100 dark:hover:bg-red-900/30 transition text-red-600 dark:text-red-400"
				title="清空画布"
				onclick={clearCanvas}
			>
				<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
			</button>
			
			<div class="ml-auto text-xs text-gray-400">
				{#if editorMode === 'select'}
					选择模式：拖拽移动 | 双击编辑 | Delete 删除
				{:else if editorMode === 'pan'}
					拖拽模式：拖拽平移画布
				{:else if editorMode === 'connect'}
					连线模式：点击节点锚点开始，点击目标锚点完成
				{:else if editorMode === 'add'}
					添加模式：选择形状后点击画布
				{/if}
			</div>
		</div>
	{/if}
	
	<div class="flex-1 relative">
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
			mode={editorMode}
		/>

		{#if selectedNodeId && selectedNodeData && !readonly}
		{@const node = reactFlowData.nodes.find(n => n.id === selectedNodeId)}
		{#if node}
			{@const liveData = node.data || {}}
			{@const fcNode: FlowchartNode = {
				id: selectedNodeId,
				type: (liveData.type as string) || (selectedNodeData.type as string) || 'process',
				position: node.position || { x: 0, y: 0 },
				data: {
					label: (liveData.label as string) || (selectedNodeData.label as string) || '',
					description: (liveData.description as string | undefined) ?? selectedNodeData.description as string | undefined,
					style: {
						shape: (liveData.shape as 'rectangle' | 'rounded' | 'circle' | 'diamond' | 'ellipse') || (selectedNodeData.shape as 'rectangle' | 'rounded' | 'circle' | 'diamond' | 'ellipse') || 'rectangle',
						backgroundColor: (liveData.backgroundColor as string | undefined) ?? selectedNodeData.backgroundColor as string | undefined,
						borderColor: (liveData.borderColor as string | undefined) ?? selectedNodeData.borderColor as string | undefined
					},
					inputParams: (liveData.inputParams as string[]) || (selectedNodeData.inputParams as string[]) || [],
					outputParams: (liveData.outputParams as string[]) || (selectedNodeData.outputParams as string[]) || [],
					traceability: (liveData.traceability as any) ?? selectedNodeData.traceability as any
				}
			}}
			{#if activePanel === 'config'}
				<NodeConfigPanel
				node={fcNode}
				{parameterEntries}
				{projectId}
				{entryId}
				onUpdate={updateNodeData}
				onClose={() => { selectedNodeId = null; selectedNodeData = null; }}
				onViewTraceability={() => activePanel = 'traceability'}
			/>
			{:else}
				<TraceabilitySidebar
					nodeId={selectedNodeId}
					nodeData={{
						label: (liveData.label as string) || (selectedNodeData.label as string) || '',
						description: (liveData.description as string | undefined) ?? selectedNodeData.description as string | undefined,
						inputParams: (liveData.inputParams as string[]) || (selectedNodeData.inputParams as string[]) || [],
						outputParams: (liveData.outputParams as string[]) || (selectedNodeData.outputParams as string[]) || [],
						traceability: (liveData.traceability as {
							entityType: string;
							entityId: string;
							entityName: string;
							versionNumber?: string;
							boundAt: number;
							boundBy?: string;
						} | undefined) ?? selectedNodeData.traceability as any
					}}
					{projectId}
					onClose={() => { selectedNodeId = null; selectedNodeData = null; }}
					onViewConfig={() => activePanel = 'config'}
				/>
			{/if}
		{/if}
	{/if}
	</div>
</div>
