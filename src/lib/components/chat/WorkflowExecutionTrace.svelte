<script lang="ts">
	interface ExecutionLog {
		node_id: string;
		node_name: string;
		node_type: string;
		status: 'pending' | 'running' | 'completed' | 'failed';
		input_data?: any;
		output_data?: any;
		execution_time?: number;
		timestamp: string;
	}

	interface Props {
		executionId: string;
		logs: ExecutionLog[];
		isLoading?: boolean;
		isStreaming?: boolean;
		expandedNodes?: string[];
	}

	let { 
		executionId, 
		logs = [], 
		isLoading = false, 
		isStreaming = false,
		expandedNodes = []
	}: Props = $props();

	let localExpandedNodes = $state(new Set<string>(expandedNodes));

	function getStatusColor(status: string): string {
		switch (status) {
			case 'completed':
				return 'text-green-600 bg-green-50 dark:bg-green-900/20';
			case 'running':
				return 'text-blue-600 bg-blue-50 dark:bg-blue-900/20';
			case 'failed':
				return 'text-red-600 bg-red-50 dark:bg-red-900/20';
			case 'pending':
				return 'text-gray-600 bg-gray-50 dark:bg-gray-900/20';
			default:
				return 'text-gray-600 bg-gray-50 dark:bg-gray-900/20';
		}
	}

	function getStatusIcon(status: string): string {
		switch (status) {
			case 'completed':
				return '✓';
			case 'running':
				return '⟳';
			case 'failed':
				return '✗';
			case 'pending':
				return '○';
			default:
				return '○';
		}
	}

	function formatExecutionTime(ms: number): string {
		if (ms < 1000) {
			return `${ms}ms`;
		}
		return `${(ms / 1000).toFixed(1)}s`;
	}

	function formatTimestamp(timestamp: string): string {
		return new Date(timestamp).toLocaleTimeString();
	}

	function toggleNode(nodeId: string) {
		if (localExpandedNodes.has(nodeId)) {
			localExpandedNodes.delete(nodeId);
		} else {
			localExpandedNodes.add(nodeId);
		}
		localExpandedNodes = new Set(localExpandedNodes);
	}

	function isExpanded(nodeId: string): boolean {
		return localExpandedNodes.has(nodeId);
	}
</script>

<div class="w-full bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
	<div class="flex items-center justify-between p-3 border-b border-gray-200 dark:border-gray-700">
		<div class="flex items-center gap-2">
			<svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
			</svg>
			<span class="text-sm font-medium text-gray-900 dark:text-white">执行跟踪</span>
			{#if isStreaming}
				<span class="inline-flex items-center gap-1 text-xs text-blue-600">
					<span class="animate-pulse">●</span>
					实时
				</span>
			{/if}
		</div>
		<span class="text-xs text-gray-500 dark:text-gray-400 font-mono">{executionId}</span>
	</div>

	<div class="max-h-96 overflow-y-auto">
		{#if isLoading}
			<div class="flex items-center justify-center py-8">
				<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-400"></div>
			</div>
		{:else if logs.length === 0}
			<div class="text-center py-8 text-gray-500 dark:text-gray-400">
				<p class="text-sm">暂无执行记录</p>
			</div>
		{:else}
			<div class="divide-y divide-gray-100 dark:divide-gray-800">
				{#each logs as log (log.node_id + log.timestamp)}
					<div class="p-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
						<div class="flex items-start gap-3">
							<div class="flex-shrink-0 mt-0.5">
								<span class="inline-flex items-center justify-center w-6 h-6 rounded-full text-sm {getStatusColor(log.status)}">
									{getStatusIcon(log.status)}
								</span>
							</div>

							<div class="flex-1 min-w-0">
								<div class="flex items-center justify-between">
									<div class="flex items-center gap-2">
										<span class="text-sm font-medium text-gray-900 dark:text-white">
											{log.node_name || log.node_id}
										</span>
										<span class="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
											{log.node_type}
										</span>
									</div>
									<div class="flex items-center gap-2">
										{#if log.execution_time}
											<span class="text-xs text-gray-500 dark:text-gray-400">
												{formatExecutionTime(log.execution_time)}
											</span>
										{/if}
										<span class="text-xs text-gray-400 dark:text-gray-500">
											{formatTimestamp(log.timestamp)}
										</span>
									</div>
								</div>

								{#if log.input_data || log.output_data}
									<button
										class="mt-1 text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
										onclick={() => toggleNode(log.node_id)}
									>
										{isExpanded(log.node_id) ? '收起详情' : '展开详情'}
									</button>
								{/if}

								{#if isExpanded(log.node_id)}
									{#if log.input_data}
										<div class="mt-2">
											<details class="text-xs" open>
												<summary class="cursor-pointer text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300">
													输入数据
												</summary>
												<pre class="mt-1 p-2 bg-gray-50 dark:bg-gray-800 rounded-lg text-xs text-gray-600 dark:text-gray-400 overflow-x-auto">{JSON.stringify(log.input_data, null, 2)}</pre>
											</details>
										</div>
									{/if}

									{#if log.output_data}
										<div class="mt-2">
											<details class="text-xs" open>
												<summary class="cursor-pointer text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300">
													输出数据
												</summary>
												<pre class="mt-1 p-2 bg-gray-50 dark:bg-gray-800 rounded-lg text-xs text-gray-600 dark:text-gray-400 overflow-x-auto">{JSON.stringify(log.output_data, null, 2)}</pre>
											</details>
										</div>
									{/if}
								{/if}

								{#if log.status === 'failed'}
									<div class="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded-lg">
										<p class="text-xs text-red-600 dark:text-red-400">执行失败</p>
									</div>
								{/if}
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
