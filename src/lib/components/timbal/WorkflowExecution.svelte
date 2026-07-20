<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { timbalStore } from '$lib/stores/timbalStore';
	import type { TimbalExecutionResponse } from '$lib/apis/timbal/types';

	export let executionId: string;

	let execution: TimbalExecutionResponse | null = null;
	let eventSource: EventSource | null = null;
	let logs: string[] = [];

	onMount(() => {
		// Subscribe to execution updates
		const unsubscribe = timbalStore.subscribe((state) => {
			const exec = state.executions.find((e) => e.execution_id === executionId);
			if (exec) {
				execution = exec;
				if ('logs' in exec && Array.isArray((exec as any).logs)) {
					logs = (exec as any).logs;
				}
			}
		});

		// Setup SSE for real-time updates
		setupSSE();

		return () => {
			unsubscribe();
			if (eventSource) {
				eventSource.close();
			}
		};
	});

	function setupSSE() {
		const baseUrl = import.meta.env.VITE_TIMBAL_BASE_URL || 'http://localhost:3000';
		const url = new URL(`${baseUrl}/workflows/${executionId}/stream`);
		
		eventSource = new EventSource(url.toString());

		eventSource.onmessage = (event) => {
			try {
				const data = JSON.parse(event.data);
				if (data.log) {
					logs = [...logs, data.log];
				}
				if (data.status) {
					// Update execution status
					timbalStore.updateExecution(executionId, { status: data.status });
				}
			} catch (error) {
				console.error('Failed to parse SSE event:', error);
			}
		};

		eventSource.onerror = (error) => {
			console.error('SSE error:', error);
			eventSource?.close();
		};
	}

	function formatStatus(status: string): string {
		return status.charAt(0).toUpperCase() + status.slice(1);
	}

	function getStatusColor(status: string): string {
		switch (status) {
			case 'pending':
				return 'text-yellow-600';
			case 'running':
				return 'text-blue-600';
			case 'completed':
				return 'text-green-600';
			case 'failed':
				return 'text-red-600';
			case 'cancelled':
				return 'text-gray-600';
			default:
				return 'text-gray-600';
		}
	}
</script>

<div class="workflow-execution">
	{#if execution}
		<div class="execution-header">
			<h3 class="text-lg font-semibold">Execution: {execution.execution_id}</h3>
			<span class="status-badge {getStatusColor(execution.status)}">
				{formatStatus(execution.status)}
			</span>
		</div>

		<div class="execution-details">
			<p class="text-sm text-gray-600">
				Started: {new Date(execution.started_at).toLocaleString()}
			</p>
			{#if execution.completed_at}
				<p class="text-sm text-gray-600">
					Completed: {new Date(execution.completed_at).toLocaleString()}
				</p>
			{/if}
		</div>

		{#if execution.error}
			<div class="error-message bg-red-50 border border-red-200 rounded p-3 mt-4">
				<h4 class="text-red-800 font-medium">Error</h4>
				<p class="text-red-700 text-sm">{execution.error.message}</p>
			</div>
		{/if}

		{#if execution.output}
			<div class="output-section mt-4">
				<h4 class="text-sm font-medium text-gray-700 mb-2">Output</h4>
				<pre class="bg-gray-50 rounded p-3 text-sm overflow-auto">
					{JSON.stringify(execution.output, null, 2)}
				</pre>
			</div>
		{/if}

		<div class="logs-section mt-4">
			<h4 class="text-sm font-medium text-gray-700 mb-2">Logs</h4>
			<div class="logs-container bg-gray-900 text-green-400 rounded p-3 h-64 overflow-auto">
				{#if logs.length > 0}
					{#each logs as log}
						<div class="log-entry text-xs font-mono">{log}</div>
					{/each}
				{:else}
					<p class="text-gray-500 text-sm">No logs available</p>
				{/if}
			</div>
		</div>
	{:else}
		<div class="loading-state text-center py-8">
			<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
			<p class="text-gray-600 mt-2">Loading execution...</p>
		</div>
	{/if}
</div>

<style>
	.workflow-execution {
		padding: 1rem;
	}

	.execution-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 1rem;
	}

	.status-badge {
		padding: 0.25rem 0.5rem;
		border-radius: 0.25rem;
		font-size: 0.875rem;
		font-weight: 500;
	}

	.logs-container {
		font-family: monospace;
		font-size: 0.875rem;
	}

	.log-entry {
		padding: 0.25rem 0;
		border-bottom: 1px solid #1f2937;
	}

	.log-entry:last-child {
		border-bottom: none;
	}
</style>
