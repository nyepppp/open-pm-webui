<script lang="ts">
	import { onMount } from 'svelte';
	import { writable } from 'svelte/store';
	import type { TimbalWorkflow } from '$lib/apis/timbal/types';

	// Props
	export let workflow: TimbalWorkflow | null = null;
	export let onSave: (workflow: TimbalWorkflow) => void = () => {};
	export let onExecute: (workflowId: string) => void = () => {};

	// Local state
	let nodes: any[] = [];
	let edges: any[] = [];
	let selectedNode: any = null;
	let isDragging = false;
	let dragOffset = { x: 0, y: 0 };

	// Canvas state
	let canvasRef: HTMLDivElement;
	let canvasOffset = { x: 0, y: 0 };
	let scale = 1;

	function handleNodeDragStart(event: MouseEvent, node: any) {
		isDragging = true;
		selectedNode = node;
		dragOffset = {
			x: event.clientX - node.position.x,
			y: event.clientY - node.position.y
		};
	}

	function handleNodeDrag(event: MouseEvent) {
		if (!isDragging || !selectedNode) return;

		selectedNode.position = {
			x: event.clientX - dragOffset.x,
			y: event.clientY - dragOffset.y
		};

		// Force re-render
		nodes = [...nodes];
	}

	function handleNodeDragEnd() {
		isDragging = false;
		selectedNode = null;
	}

	function addNode(type: string) {
		const newNode = {
			id: `node_${Date.now()}`,
			type,
			position: { x: 100, y: 100 },
			config: {}
		};
		nodes = [...nodes, newNode];
	}

	function removeNode(nodeId: string) {
		nodes = nodes.filter(n => n.id !== nodeId);
		edges = edges.filter(e => e.source !== nodeId && e.target !== nodeId);
	}

	function connectNodes(sourceId: string, targetId: string) {
		const newEdge = {
			id: `edge_${Date.now()}`,
			source: sourceId,
			target: targetId
		};
		edges = [...edges, newEdge];
	}

	function handleSave() {
		// Always save nodes and edges, even if workflow is null (new workflow scenario)
		const updatedWorkflow: TimbalWorkflow = {
			id: workflow?.id || `wf_${Date.now()}`,
			name: workflow?.name || 'New Workflow',
			description: workflow?.description || '',
			steps: workflow?.steps || [],
			version: workflow?.version || '1.0.0',
			created_at: workflow?.created_at || new Date().toISOString(),
			updated_at: new Date().toISOString()
		};
		onSave(updatedWorkflow);
	}

	function handleExecute() {
		if (!workflow) return;
		onExecute(workflow.id);
	}
</script>

<div class="workflow-designer">
	<!-- Toolbar -->
	<div class="toolbar">
		<button class="btn btn-primary" on:click={() => addNode('pm_operation')}>Add PM Node</button>
		<button class="btn btn-primary" on:click={() => addNode('openwebui_skill')}>Add Skill Node</button>
		<button class="btn btn-primary" on:click={() => addNode('openwebui_prompt')}>Add Prompt Node</button>
		<button class="btn btn-primary" on:click={() => addNode('openwebui_tool')}>Add Tool Node</button>
		<div class="flex-grow"></div>
		<button class="btn btn-secondary" on:click={handleSave}>Save</button>
		<button class="btn btn-success" on:click={handleExecute}>Execute</button>
	</div>

	<!-- Canvas -->
	<div
		class="canvas"
		bind:this={canvasRef}
		on:mousemove={handleNodeDrag}
		on:mouseup={handleNodeDragEnd}
	>
		{#each nodes as node (node.id)}
			<div
				class="node"
				class:selected={selectedNode?.id === node.id}
				style="transform: translate({node.position.x}px, {node.position.y}px); will-change: transform;"
				on:mousedown={(e) => handleNodeDragStart(e, node)}
			>
				<div class="node-header">{node.type}</div>
				<div class="node-body">
					<p class="text-xs text-gray-600">ID: {node.id}</p>
				</div>
				<button class="node-remove" on:click={() => removeNode(node.id)}>×</button>
			</div>
		{/each}

		{#each edges as edge (edge.id)}
			<svg class="edge-line" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; overflow: visible;">
				<line
					x1={nodes.find(n => n.id === edge.source)?.position.x || 0}
					y1={nodes.find(n => n.id === edge.source)?.position.y || 0}
					x2={nodes.find(n => n.id === edge.target)?.position.x || 0}
					y2={nodes.find(n => n.id === edge.target)?.position.y || 0}
					stroke="#94a3b8"
					stroke-width="2"
				/>
			</svg>
		{/each}
	</div>
</div>

<style>
	.workflow-designer {
		display: flex;
		flex-direction: column;
		height: 100%;
		margin-left: auto;
		margin-right: auto;
		max-width: 80rem;
	}

	.toolbar {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1rem;
		background-color: #f3f4f6;
		border-bottom: 1px solid #e5e7eb;
	}

	.canvas {
		flex-grow: 1;
		position: relative;
		background-color: #f9fafb;
		overflow: hidden;
		min-height: 400px;
	}

	.node {
		position: absolute;
		background-color: white;
		border-radius: 0.5rem;
		box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
		border: 1px solid #e5e7eb;
		cursor: move;
		min-width: 150px;
		transition: box-shadow 0.2s;
		transform-origin: center center;
	}

	.node:hover {
		box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
	}

	.node.selected {
		box-shadow: 0 0 0 2px #3b82f6;
	}

	.node-header {
		padding: 0.5rem 0.75rem;
		background-color: #f3f4f6;
		border-radius: 0.5rem 0.5rem 0 0;
		font-weight: 500;
		font-size: 0.875rem;
		color: #374151;
	}

	.node-body {
		padding: 0.75rem;
	}

	.node-remove {
		position: absolute;
		top: -0.5rem;
		right: -0.5rem;
		width: 1.25rem;
		height: 1.25rem;
		background-color: #ef4444;
		color: white;
		border-radius: 9999px;
		font-size: 0.75rem;
		display: flex;
		align-items: center;
		justify-content: center;
		opacity: 0;
		transition: opacity 0.2s;
	}

	.node:hover .node-remove {
		opacity: 1;
	}

	.btn {
		padding: 0.375rem 0.75rem;
		border-radius: 0.25rem;
		font-size: 0.875rem;
		font-weight: 500;
		transition: background-color 0.2s;
	}

	.btn-primary {
		background-color: #2563eb;
		color: white;
	}

	.btn-primary:hover {
		background-color: #1d4ed8;
	}

	.btn-secondary {
		background-color: #e5e7eb;
		color: #374151;
	}

	.btn-secondary:hover {
		background-color: #d1d5db;
	}

	.btn-success {
		background-color: #16a34a;
		color: white;
	}

	.btn-success:hover {
		background-color: #15803d;
	}
</style>
