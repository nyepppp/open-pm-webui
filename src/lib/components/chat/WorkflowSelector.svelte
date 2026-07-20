<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { toast } from 'svelte-sonner';

	import Tooltip from '../common/Tooltip.svelte';

	interface Workflow {
		id: string;
		name: string;
		description?: string;
		status: string;
	}

	interface Props {
		workflows: Workflow[];
		selectedWorkflowId?: string;
		pinnedWorkflowIds?: string[];
		requiredProjectId?: string | null;
		onSelect?: (workflowId: string) => void;
		onPin?: (workflowId: string) => void;
		onUnpin?: (workflowId: string) => void;
	}

	let {
		workflows = [],
		selectedWorkflowId = '',
		pinnedWorkflowIds = [],
		requiredProjectId = null,
		onSelect,
		onPin,
		onUnpin
	}: Props = $props();

	const dispatch = createEventDispatcher();

	let searchQuery = $state('');
	let isOpen = $state(false);
	let isLoading = $state(false);
	let executionStatus = $state<'idle' | 'running' | 'completed' | 'failed'>('idle');

	function getFilteredWorkflows(): Workflow[] {
		if (!searchQuery.trim()) return workflows;
		const query = searchQuery.toLowerCase();
		return workflows.filter(
			(w) =>
				w.name.toLowerCase().includes(query) ||
				(w.description && w.description.toLowerCase().includes(query))
		);
	}

	function getPinnedWorkflows(): Workflow[] {
		return workflows.filter((w) => pinnedWorkflowIds.includes(w.id));
	}

	function getUnpinnedWorkflows(): Workflow[] {
		return getFilteredWorkflows().filter((w) => !pinnedWorkflowIds.includes(w.id));
	}

	function handleSelect(workflowId: string) {
		if (!requiredProjectId) {
			toast.error('请先选择项目');
			return;
		}
		// L4: 支持反选 —— 再次点击同一工作流时取消选中（Bug 4 取消入口）
		if (selectedWorkflowId === workflowId) {
			selectedWorkflowId = '';
			onSelect?.('');
			dispatch('select', { workflowId: '' });
		} else {
			selectedWorkflowId = workflowId;
			onSelect?.(workflowId);
			dispatch('select', { workflowId });
		}
		isOpen = false;
	}

	// L4: × 按钮直接取消选择（不触发 dropdown 关闭逻辑）
	function handleClearSelection(event: Event) {
		event.stopPropagation();
		selectedWorkflowId = '';
		onSelect?.('');
		dispatch('select', { workflowId: '' });
	}

	function handlePin(workflowId: string, event: Event) {
		event.stopPropagation();
		if (pinnedWorkflowIds.includes(workflowId)) {
			onUnpin?.(workflowId);
			dispatch('unpin', { workflowId });
		} else {
			onPin?.(workflowId);
			dispatch('pin', { workflowId });
		}
	}

	function toggleOpen() {
		if (!requiredProjectId) {
			toast.error('请先选择项目');
			return;
		}
		isOpen = !isOpen;
	}

	function handleClickOutside(event: MouseEvent) {
		const target = event.target as HTMLElement;
		if (!target.closest('.workflow-selector')) {
			isOpen = false;
		}
	}

	function getStatusColor(status: string): string {
		switch (status) {
			case 'active':
				return 'text-green-500';
			case 'draft':
				return 'text-yellow-500';
			case 'archived':
				return 'text-gray-400';
			default:
				return 'text-gray-400';
		}
	}
</script>

<svelte:window onclick={handleClickOutside} />

<div class="workflow-selector relative">
	<Tooltip content={!requiredProjectId ? '请先选择项目' : (selectedWorkflowId ? '点击 × 取消选择；双路径：工作流用于多步骤编排，简单写入由 AI 直接调用工具' : '选择工作流执行多步骤编排；简单写入由 AI 直接调用工具')} placement="top">
	<button
		class="flex items-center gap-2 px-3 py-2 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors text-sm {!requiredProjectId ? 'opacity-50 cursor-not-allowed' : ''}"
		onclick={toggleOpen}
		disabled={isLoading}
	>
	{#if isLoading}
		<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 dark:border-gray-400" />
	{:else}
		<svg class="w-4 h-4 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
		</svg>
	{/if}
	<span class="text-gray-700 dark:text-gray-300">
		{#if selectedWorkflowId}
			{@const selected = workflows.find((w) => w.id === selectedWorkflowId)}
			{selected?.name || '选择工作流'}
		{:else}
			选择工作流
		{/if}
	</span>
	<!-- L4: 已选时显示 × 取消按钮（Bug 4 取消入口） -->
	{#if selectedWorkflowId}
		<button
			class="ml-0.5 p-0.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition"
			onclick={handleClearSelection}
			title="取消选择"
			aria-label="取消工作流选择"
		>
			<svg class="w-3.5 h-3.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
			</svg>
		</button>
	{/if}
	<svg
		class="w-4 h-4 text-gray-400 transition-transform {isOpen ? 'rotate-180' : ''}"
		fill="none"
		stroke="currentColor"
		viewBox="0 0 24 24"
	>
		<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
	</svg>
</button>
</Tooltip>

	{#if isOpen}
		<div
			class="absolute bottom-full left-0 mb-2 w-80 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-xl z-50"
		>
			<div class="p-3 border-b border-gray-200 dark:border-gray-700">
				<div class="relative">
					<svg
						class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
						/>
					</svg>
					<input
						type="text"
						class="w-full pl-9 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						placeholder="搜索工作流..."
						bind:value={searchQuery}
					/>
				</div>
			</div>

			{#if getPinnedWorkflows().length > 0}
				<div class="p-2">
					<h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-2 py-1">
						固定的工作流
					</h4>
					{#each getPinnedWorkflows() as workflow (workflow.id)}
						<div
							class="flex items-center gap-2 p-2 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors {selectedWorkflowId === workflow.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''}"
							onclick={() => handleSelect(workflow.id)}
							role="button"
							tabindex="0"
							onkeydown={(e) => {
								if (e.key === 'Enter' || e.key === ' ') {
									e.preventDefault();
									handleSelect(workflow.id);
								}
							}}
						>
							<svg class="w-4 h-4 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
								<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
							</svg>
							<div class="flex-1 min-w-0">
								<p class="text-sm font-medium text-gray-900 dark:text-white truncate">
									{workflow.name}
								</p>
								{#if workflow.description}
									<p class="text-xs text-gray-500 dark:text-gray-400 truncate">
										{workflow.description}
									</p>
								{/if}
							</div>
							<span class="text-xs {getStatusColor(workflow.status)}">
								{workflow.status === 'active' ? '运行中' : workflow.status === 'draft' ? '草稿' : '已归档'}
							</span>
							<button
								class="text-yellow-500 hover:text-yellow-600 transition-colors"
								onclick={(e) => handlePin(workflow.id, e)}
							>
								<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
									<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
								</svg>
							</button>
						</div>
					{/each}
				</div>
			{/if}

			<div class="p-2 max-h-60 overflow-y-auto">
				<h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider px-2 py-1">
					所有工作流
				</h4>
				{#if getUnpinnedWorkflows().length === 0}
					<div class="text-center py-4">
						<p class="text-sm text-gray-500 dark:text-gray-400">没有可用工作流</p>
					</div>
				{:else}
					{#each getUnpinnedWorkflows() as workflow (workflow.id)}
						<div
							class="flex items-center gap-2 p-2 rounded-lg cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors {selectedWorkflowId === workflow.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''}"
							onclick={() => handleSelect(workflow.id)}
							role="button"
							tabindex="0"
							onkeydown={(e) => {
								if (e.key === 'Enter' || e.key === ' ') {
									e.preventDefault();
									handleSelect(workflow.id);
								}
							}}
						>
							<svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M13 10V3L4 14h7v7l9-11h-7z"
								/>
							</svg>
							<div class="flex-1 min-w-0">
								<p class="text-sm font-medium text-gray-900 dark:text-white truncate">
									{workflow.name}
								</p>
								{#if workflow.description}
									<p class="text-xs text-gray-500 dark:text-gray-400 truncate">
										{workflow.description}
									</p>
								{/if}
							</div>
							<span class="text-xs {getStatusColor(workflow.status)}">
								{workflow.status === 'active' ? '运行中' : workflow.status === 'draft' ? '草稿' : '已归档'}
							</span>
							<button
								class="text-gray-400 hover:text-yellow-500 transition-colors"
								onclick={(e) => handlePin(workflow.id, e)}
							>
								<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
									/>
								</svg>
							</button>
						</div>
					{/each}
				{/if}
			</div>
		</div>
	{/if}
</div>
