<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	export let node: any;
	export let selected: boolean = false;

	const dispatch = createEventDispatcher();

	function handleClick() {
		dispatch('select', node);
	}

	function handleDragStart(event: MouseEvent) {
		dispatch('dragstart', { node, event });
	}

	function getNodeColor(type: string): string {
		switch (type) {
			case 'pm_operation':
				return 'bg-blue-100 border-blue-300';
			case 'openwebui_skill':
				return 'bg-green-100 border-green-300';
			case 'openwebui_prompt':
				return 'bg-purple-100 border-purple-300';
			case 'openwebui_tool':
				return 'bg-orange-100 border-orange-300';
			default:
				return 'bg-gray-100 border-gray-300';
		}
	}

	function getNodeIcon(type: string): string {
		switch (type) {
			case 'pm_operation':
				return '📊';
			case 'openwebui_skill':
				return '🔧';
			case 'openwebui_prompt':
				return '💬';
			case 'openwebui_tool':
				return '🛠️';
			default:
				return '📦';
		}
	}
</script>

<div
	class="workflow-node {getNodeColor(node.type)} {selected ? 'ring-2 ring-blue-500' : ''}"
	on:click={handleClick}
	on:mousedown={handleDragStart}
	style="transform: translate({node.position.x}px, {node.position.y}px);"
>
	<div class="node-content">
		<span class="node-icon">{getNodeIcon(node.type)}</span>
		<span class="node-label">{node.type}</span>
	</div>
	
	{#if node.config}
		<div class="node-config">
			{#each Object.entries(node.config) as [key, value]}
				<div class="config-item">
					<span class="config-key">{key}:</span>
					<span class="config-value">{JSON.stringify(value)}</span>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.workflow-node {
		position: absolute;
		border-radius: 0.5rem;
		border: 1px solid #e5e7eb;
		box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
		cursor: move;
		user-select: none;
		min-width: 150px;
		transition: box-shadow 0.2s;
	}

	.workflow-node:hover {
		box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
	}

	.node-content {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem;
	}

	.node-icon {
		font-size: 1.125rem;
	}

	.node-label {
		font-size: 0.875rem;
		font-weight: 500;
		color: #374151;
	}

	.node-config {
		padding: 0 0.5rem 0.5rem;
		font-size: 0.75rem;
		color: #4b5563;
	}

	.config-item {
		display: flex;
		gap: 0.25rem;
	}

	.config-key {
		font-weight: 500;
	}

	.config-value {
		color: #6b7280;
	}
</style>
