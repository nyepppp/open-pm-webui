<script lang="ts">
	import { writable } from 'svelte/store';
	import type { FlowchartData, FlowchartNode } from '$lib/apis/pm/types';
	import type { ModuleEntry } from '$lib/apis/pm/types';
	import ExcalidrawCanvas from './excalidraw/ExcalidrawCanvas.svelte';
	import NodeConfigPanel from './flowchart/NodeConfigPanel.svelte';
	import TraceabilitySidebar from './flowchart/TraceabilitySidebar.svelte';
	import { flowchartToExcalidraw, excalidrawToFlowchart } from '$lib/utils/excalidrawDataConverter';

	interface Props {
		flowchartData: FlowchartData;
		onChange: (data: FlowchartData) => void;
		readonly?: boolean;
		parameterEntries?: ModuleEntry[];
		projectId?: string;
	}

	let { flowchartData, onChange, readonly = false, parameterEntries = [], projectId = '' }: Props = $props();

	// Excalidraw canvas ref
	let excalidrawCanvasRef: any = $state(null);

	// Track selected element for config panel
	let selectedElement = $state<any>(null);
	let selectedNodeData = $state<Record<string, unknown> | null>(null);
	let activePanel = $state<'config' | 'traceability'>('config');

	// Convert FlowchartData to Excalidraw initial data
	let initialData = $state<any>({
		elements: [],
		appState: {
			viewBackgroundColor: '#ffffff',
			gridSize: 20
		}
	});

	$effect(() => {
		const elements = flowchartToExcalidraw(flowchartData);
		initialData = {
			elements,
			appState: {
				viewBackgroundColor: '#ffffff',
				gridSize: 20
			}
		};
	});

	// Debounce for auto-save
	let saveTimer: ReturnType<typeof setTimeout> | undefined;

	function handleChange(elements: any[], appState: any) {
		clearTimeout(saveTimer);
		saveTimer = setTimeout(() => {
			const data = excalidrawToFlowchart(elements);
			onChange(data);
		}, 300);
	}

	function handleElementClick(element: any) {
		if (readonly) return;
		selectedElement = element;
		selectedNodeData = element.customData || {};
		activePanel = 'config';
	}

	function handlePaneClick() {
		selectedElement = null;
		selectedNodeData = null;
	}

	function updateNodeData(nodeId: string, data: Partial<FlowchartNode['data']>) {
		// Update the element in Excalidraw
		if (excalidrawCanvasRef) {
			const api = excalidrawCanvasRef.getAPI();
			if (api) {
				const elements = api.getSceneElements();
				const updatedElements = elements.map((el: any) => {
					if (el.id === nodeId) {
						// Handle shape change
						let updatedEl = {
							...el,
							customData: { ...el.customData, ...data }
						};
						
						// If shape is being updated, change the element type
						if (data.style?.shape) {
							const shapeMap: Record<string, string> = {
								'rectangle': 'rectangle',
								'rounded': 'rectangle',
								'circle': 'ellipse',
								'ellipse': 'ellipse',
								'diamond': 'diamond'
							};
							const newType = shapeMap[data.style.shape] || el.type;
							updatedEl = {
								...updatedEl,
								type: newType
							};
						}
						
						// If colors are being updated, apply them
						if (data.style?.backgroundColor) {
							updatedEl = {
								...updatedEl,
								backgroundColor: data.style.backgroundColor
							};
						}
						if (data.style?.borderColor) {
							updatedEl = {
								...updatedEl,
								strokeColor: data.style.borderColor
							};
						}
						
						return updatedEl;
					}
					return el;
				});
				api.updateScene({ elements: updatedElements });
			}
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if ((event.key === 'Delete' || event.key === 'Backspace') && selectedElement) {
			const target = event.target as HTMLElement;
			if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') return;
			event.preventDefault();
			// Delete selected element via Excalidraw API
			if (excalidrawCanvasRef) {
				const api = excalidrawCanvasRef.getAPI();
				if (api) {
					api.updateScene({
						elements: api.getSceneElements().map((el: any) =>
							el.id === selectedElement.id ? { ...el, isDeleted: true } : el
						)
					});
				}
			}
			selectedElement = null;
			selectedNodeData = null;
		}
	}

	// Export functions
	export function exportToPNG() {
		if (excalidrawCanvasRef) {
			const api = excalidrawCanvasRef.getAPI();
			if (api) {
				// Use Excalidraw's export API
				api.exportToBlob({
					mimeType: 'image/png'
				}).then((blob: Blob) => {
					const url = URL.createObjectURL(blob);
					const link = document.createElement('a');
					link.href = url;
					link.download = 'flowchart.png';
					link.click();
					URL.revokeObjectURL(url);
				});
			}
		}
	}

	export function exportToSVG() {
		if (excalidrawCanvasRef) {
			const api = excalidrawCanvasRef.getAPI();
			if (api) {
				// SVG export is handled differently, using canvas
				const canvas = document.querySelector('canvas');
				if (canvas) {
					const url = canvas.toDataURL('image/png');
					const link = document.createElement('a');
					link.href = url;
					link.download = 'flowchart.png';
					link.click();
				}
			}
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="w-full h-full relative" style="min-height: 400px;">
	<ExcalidrawCanvas
		bind:this={excalidrawCanvasRef}
		initialData={initialData}
		onChange={handleChange}
		onElementClick={handleElementClick}
		theme="light"
		viewModeEnabled={readonly}
		gridModeEnabled={true}
	/>

	{#if selectedElement && selectedNodeData && !readonly}
		{@const fcNode: FlowchartNode = {
			id: selectedElement.id,
			type: (selectedNodeData.type as string) || 'process',
			position: { x: selectedElement.x || 0, y: selectedElement.y || 0 },
			data: {
				label: (selectedNodeData.label as string) || '',
				description: selectedNodeData.description as string | undefined,
				style: {
					shape: selectedElement.type,
					backgroundColor: selectedElement.backgroundColor,
					borderColor: selectedElement.strokeColor
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
				onClose={() => { selectedElement = null; selectedNodeData = null; }}
				onViewTraceability={() => activePanel = 'traceability'}
			/>
		{:else}
			<TraceabilitySidebar
				nodeId={selectedElement.id}
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
				onClose={() => { selectedElement = null; selectedNodeData = null; }}
				onViewConfig={() => activePanel = 'config'}
			/>
		{/if}
	{/if}
</div>
