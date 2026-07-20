<script lang="ts">
	import { createEventDispatcher } from 'svelte';

	// Props
	export let workspaces: Array<{ id: string; name: string }> = [];
	export let selectedWorkspaceId: string | null = null;

	// Events
	const dispatch = createEventDispatcher<{
		bind: { workspaceId: string };
		unbind: void;
		switch: { workspaceId: string };
	}>();

	function handleSelect(event: Event) {
		const target = event.target as HTMLSelectElement;
		const workspaceId = target.value;
		if (workspaceId) {
			dispatch('bind', { workspaceId });
		}
	}

	function handleUnbind() {
		dispatch('unbind');
	}

	function handleSwitch(workspaceId: string) {
		dispatch('switch', { workspaceId });
	}
</script>

<div class="workspace-selector">
	{#if selectedWorkspaceId}
		<div class="current-workspace">
			<span>Workspace: {workspaces.find(w => w.id === selectedWorkspaceId)?.name || 'Unknown'}</span>
			<button on:click={handleUnbind}>Unbind</button>
		</div>
	{:else}
		<select on:change={handleSelect}>
			<option value="">Select a workspace...</option>
			{#each workspaces as workspace}
				<option value={workspace.id}>{workspace.name}</option>
			{/each}
		</select>
	{/if}
</div>

<style>
	.workspace-selector {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 5px 10px;
		background-color: #f5f5f5;
		border-radius: 4px;
	}

	.current-workspace {
		display: flex;
		align-items: center;
		gap: 10px;
	}

	.current-workspace span {
		font-weight: bold;
	}

	.workspace-selector select {
		padding: 5px 10px;
		border-radius: 4px;
		border: 1px solid #ddd;
	}

	.workspace-selector button {
		padding: 5px 10px;
		border-radius: 4px;
		border: 1px solid #ddd;
		background-color: #fff;
		cursor: pointer;
	}

	.workspace-selector button:hover {
		background-color: #f0f0f0;
	}
</style>
