<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { getFlowTemplates, executeFlow, previewFlow, type FlowTemplate, type FlowPreview } from '$lib/apis/pm/index';
	import { getEntries } from '$lib/apis/pm/index';
	import type { ModuleEntry } from '$lib/apis/pm/types';

	let projectId = $derived($page.params.projectId);

	const categories: Record<string, { label: string; color: string }> = {
		planning: { label: '规划', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300' },
		design: { label: '设计', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300' },
		management: { label: '管理', color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300' },
		acceptance: { label: '验收', color: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' },
		review: { label: '复盘', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300' },
		enablement: { label: '赋能', color: 'bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300' }
	};

	const statusConfig: Record<string, { label: string; color: string; dot: string }> = {
		pending: { label: '待开始', color: 'bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-400', dot: 'bg-gray-400 dark:bg-gray-500' },
		in_progress: { label: '进行中', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300', dot: 'bg-blue-500' },
		completed: { label: '已完成', color: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300', dot: 'bg-green-500' },
		blocked: { label: '已阻塞', color: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300', dot: 'bg-red-500' },
		skipped: { label: '已跳过', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300', dot: 'bg-yellow-500' }
	};

	const moduleCategoryMap: Record<string, string> = {
		requirement: 'planning', competitor: 'planning', prd: 'design',
		parameter: 'design', prototype: 'design', testcase: 'enablement',
		schedule: 'management', meeting: 'management', risk: 'management',
		acceptance: 'acceptance', 'product-architecture': 'design',
		spec: 'review', faq: 'review'
	};

	interface FlowStep {
		id: string;
		name: string;
		category: string;
		status: string;
		description: string;
		templateId: string;
		inputModule: string;
		outputModule: string;
	}

	let flowTemplates = $state<FlowTemplate[]>([]);
	let flowSteps = $state<FlowStep[]>([]);
	let entriesByModule = $state<Record<string, ModuleEntry[]>>({});
	let loading = $state(true);
	let selectedStepId = $state<string | null>(null);
	let showCreateModal = $state(false);
	let executingStepId = $state<string | null>(null);
	let showPreviewModal = $state(false);
	let previewData = $state<FlowPreview | null>(null);
	let previewingStepId = $state<string | null>(null);

	let selectedStep = $derived(flowSteps.find((s) => s.id === selectedStepId) ?? null);
	let completedCount = $derived(flowSteps.filter((s) => s.status === 'completed').length);
	let totalCount = $derived(flowSteps.length);
	let progressPercent = $derived(totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0);

	async function loadData() {
		if (!projectId) return;
		loading = true;
		try {
			const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
			const [tplResult, entriesResult] = await Promise.all([
				getFlowTemplates(token, projectId),
				getEntries(token, projectId)
			]);
			flowTemplates = tplResult.templates;

			const byModule: Record<string, ModuleEntry[]> = {};
			for (const entry of entriesResult) {
				const mt = entry.moduleType || 'unknown';
				if (!byModule[mt]) byModule[mt] = [];
				byModule[mt].push(entry);
			}
			entriesByModule = byModule;

			buildFlowSteps();
		} catch (e) {
			console.error('Failed to load workflow data', e);
		} finally {
			loading = false;
		}
	}

	function buildFlowSteps() {
		const steps: FlowStep[] = flowTemplates.map((tpl) => {
			const hasInput = (entriesByModule[tpl.input_module]?.length ?? 0) > 0;
			const hasOutput = (entriesByModule[tpl.output_module]?.length ?? 0) > 0;
			let status = 'pending';
			if (hasOutput) status = 'completed';
			else if (hasInput) status = 'in_progress';

			return {
				id: tpl.id,
				name: tpl.name,
				category: moduleCategoryMap[tpl.input_module] || 'planning',
				status,
				description: tpl.description,
				templateId: tpl.id,
				inputModule: tpl.input_module,
				outputModule: tpl.output_module
			};
		});
		flowSteps = steps;
	}

	function toggleStep(id: string) {
		selectedStepId = selectedStepId === id ? null : id;
	}

	function getCategoryBadge(category: string) {
		return categories[category] ?? categories.planning;
	}

	function getStatusConfig(status: string) {
		return statusConfig[status] ?? statusConfig.pending;
	}

	async function handlePreview(step: FlowStep) {
		if (!projectId) return;
		const token = localStorage.token || '';
		const sourceEntries = entriesByModule[step.inputModule] || [];
		if (sourceEntries.length === 0) {
			toast.error('没有可用的源条目，请先在对应模块创建条目');
			return;
		}
		previewingStepId = step.id;
		try {
			previewData = await previewFlow(token, {
				template_id: step.templateId,
				project_id: projectId,
				source_entry_ids: sourceEntries.map((e) => e.id)
			});
			showPreviewModal = true;
		} catch (e) {
			toast.error('预览失败');
		} finally {
			previewingStepId = null;
		}
	}

	async function handleExecute(step: FlowStep) {
		if (!projectId) return;
		const token = localStorage.token || '';
		const sourceEntries = entriesByModule[step.inputModule] || [];
		if (sourceEntries.length === 0) {
			toast.error('没有可用的源条目');
			return;
		}
		executingStepId = step.id;
		try {
			await executeFlow(token, {
				template_id: step.templateId,
				project_id: projectId,
				source_entry_ids: sourceEntries.map((e) => e.id),
				confirmed: true
			});
			toast.success(`${step.name} 执行完成`);
			await loadData();
		} catch (e) {
			toast.error('执行失败');
		} finally {
			executingStepId = null;
		}
	}

	async function handleConfirmPreview() {
		if (!previewData) return;
		const step = flowSteps.find((s) => s.id === previewingStepId);
		if (!step) return;
		showPreviewModal = false;
		await handleExecute(step);
	}

	onMount(() => {
		loadData();
	});
</script>

<svelte:head>
	<title>工作流 - PM</title>
</svelte:head>

<div class="p-4 md:p-6 max-w-5xl mx-auto">
	<div class="mb-6">
		<div class="flex items-center justify-between mb-3">
			<div class="flex items-center gap-3">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">工作流</h2>
				<span class="text-sm text-gray-500 dark:text-gray-400">
					{completedCount}/{totalCount} 步骤已完成
				</span>
			</div>
			<button
				class="px-3 py-1.5 rounded-xl bg-black text-white dark:bg-white dark:text-black text-sm font-medium hover:opacity-90 transition-opacity"
				onclick={() => (showCreateModal = true)}
			>
				选择流程
			</button>
		</div>

		<div class="w-full h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
			<div
				class="h-full bg-green-500 rounded-full transition-all duration-500 ease-out"
				style="width: {progressPercent}%"
			></div>
		</div>
		<div class="flex justify-between mt-1">
			<span class="text-xs text-gray-400 dark:text-gray-500">进度</span>
			<span class="text-xs text-gray-400 dark:text-gray-500">{progressPercent}%</span>
		</div>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-16">
			<div class="w-6 h-6 border-2 border-gray-300 dark:border-gray-600 border-t-blue-500 rounded-full animate-spin"></div>
		</div>
	{:else if flowSteps.length === 0}
		<div class="flex flex-col items-center justify-center py-16 text-center">
			<div class="w-16 h-16 mb-4 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
				<svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
				</svg>
			</div>
			<h3 class="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">暂无工作流</h3>
			<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">选择流程模板以开始协作</p>
			<button
				class="px-3 py-1.5 rounded-xl bg-black text-white dark:bg-white dark:text-black text-sm font-medium hover:opacity-90 transition-opacity"
				onclick={() => (showCreateModal = true)}
			>
				选择流程
			</button>
		</div>
	{:else}
		<div class="flex flex-col gap-1">
			{#each flowSteps as step, index (step.id)}
				{@const cat = getCategoryBadge(step.category)}
				{@const stat = getStatusConfig(step.status)}
				{@const isSelected = selectedStepId === step.id}
				{@const isLast = index === flowSteps.length - 1}
				{@const inputEntries = entriesByModule[step.inputModule] || []}
				{@const outputEntries = entriesByModule[step.outputModule] || []}
				{@const isExecuting = executingStepId === step.id}

				<div class="group">
					<div
						class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100/30 dark:border-gray-850/30 transition-all duration-200 {isSelected
							? 'ring-2 ring-blue-500/30 shadow-md'
							: 'hover:shadow-sm hover:border-gray-200 dark:hover:border-gray-750'}"
					>
						<!-- svelte-ignore a11y_click_events_have_key_events -->
						<div
							class="flex items-center gap-3 px-4 py-3 cursor-pointer select-none"
							role="button"
							tabindex="0"
							onclick={() => toggleStep(step.id)}
							onkeydown={(e) => {
								if (e.key === 'Enter' || e.key === ' ') {
									e.preventDefault();
									toggleStep(step.id);
								}
							}}
						>
							<div class="flex-shrink-0">
								<div
									class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold {step.status ===
									'completed'
										? 'bg-green-500 text-white'
										: step.status === 'in_progress'
											? 'bg-blue-500 text-white ring-2 ring-blue-200 dark:ring-blue-800'
											: step.status === 'blocked'
												? 'bg-red-500 text-white'
												: 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'}"
								>
									{#if isExecuting}
										<div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
									{:else if step.status === 'completed'}
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
											<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
										</svg>
									{:else}
										{index + 1}
									{/if}
								</div>
							</div>

							<div class="flex-1 min-w-0">
								<div class="flex items-center gap-2 flex-wrap">
									<span
										class="font-medium text-gray-900 dark:text-white {step.status === 'completed'
											? 'line-through opacity-60'
											: ''}"
									>
										{step.name}
									</span>
									<span
										class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium {cat.color}"
									>
										{cat.label}
									</span>
								</div>
								<p
									class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate {step.status ===
									'completed'
										? 'opacity-50'
										: ''}"
								>
									{step.description}
								</p>
							</div>

							<div class="flex items-center gap-2 flex-shrink-0">
								<span
									class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium {stat.color}"
								>
									<span class="w-1.5 h-1.5 rounded-full {stat.dot}"></span>
									{stat.label}
								</span>
								<span class="text-xs text-gray-400 dark:text-gray-500 hidden sm:inline">
									{inputEntries.length}→{outputEntries.length}
								</span>
								<svg
									class="w-4 h-4 text-gray-400 transition-transform duration-200 {isSelected ? 'rotate-180' : ''}"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
								>
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
								</svg>
							</div>
						</div>

						{#if isSelected && selectedStep}
							<div class="px-4 pb-4 border-t border-gray-50 dark:border-gray-800/50">
								<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3">
									<div>
										<h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
											输入 ({step.inputModule})
										</h4>
										<div class="flex flex-col gap-1.5">
											{#each inputEntries.slice(0, 5) as entry}
												<a
													href="/pm/{projectId}/{step.inputModule}"
													class="flex items-center gap-2 px-3 py-2 rounded-xl bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-sm text-gray-700 dark:text-gray-300 group/link"
												>
													<svg class="w-4 h-4 text-gray-400 group-hover/link:text-blue-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
													</svg>
													<span class="truncate">{entry.title}</span>
												</a>
											{/each}
											{#if inputEntries.length === 0}
												<p class="text-xs text-gray-400 dark:text-gray-500 px-3 py-2">暂无输入条目</p>
											{/if}
											{#if inputEntries.length > 5}
												<p class="text-xs text-gray-400 dark:text-gray-500 px-3">+{inputEntries.length - 5} 更多</p>
											{/if}
										</div>
									</div>

									<div>
										<h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
											输出 ({step.outputModule})
										</h4>
										<div class="flex flex-col gap-1.5">
											{#each outputEntries.slice(0, 5) as entry}
												<a
													href="/pm/{projectId}/{step.outputModule}"
													class="flex items-center gap-2 px-3 py-2 rounded-xl bg-green-50 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-900/30 transition-colors text-sm text-green-700 dark:text-green-300 group/link"
												>
													<svg class="w-4 h-4 text-green-500 group-hover/link:text-green-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
														<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
													</svg>
													<span class="truncate">{entry.title}</span>
												</a>
											{/each}
											{#if outputEntries.length === 0}
												<p class="text-xs text-gray-400 dark:text-gray-500 px-3 py-2">暂无输出条目</p>
											{/if}
											{#if outputEntries.length > 5}
												<p class="text-xs text-gray-400 dark:text-gray-500 px-3">+{outputEntries.length - 5} 更多</p>
											{/if}
										</div>
									</div>

									<div>
										<h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
											操作
										</h4>
										<div class="flex flex-col gap-2">
											{#if step.status !== 'completed' && inputEntries.length > 0}
												<button
													class="w-full px-3 py-1.5 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
													disabled={isExecuting}
													onclick={() => handlePreview(step)}
												>
													预览执行
												</button>
												<button
													class="w-full px-3 py-1.5 rounded-xl bg-green-600 text-white text-sm font-medium hover:bg-green-700 transition-colors disabled:opacity-50"
													disabled={isExecuting}
													onclick={() => handleExecute(step)}
												>
													{isExecuting ? '执行中...' : '立即执行'}
												</button>
											{:else if inputEntries.length === 0}
												<p class="text-xs text-gray-400 dark:text-gray-500">需要先在 {step.inputModule} 模块创建条目</p>
												<a
													href="/pm/{projectId}/{step.inputModule}"
													class="w-full block text-center px-3 py-1.5 rounded-xl bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
												>
													前往创建
												</a>
											{/if}
											{#if step.status === 'completed'}
												<button
													class="w-full px-3 py-1.5 rounded-xl bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
													onclick={() => handlePreview(step)}
												>
													重新执行
												</button>
											{/if}
										</div>
									</div>
								</div>
							</div>
						{/if}
					</div>

					{#if !isLast && !isSelected}
						<div class="flex justify-center py-0.5">
							<div class="w-0.5 h-3 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- Flow Template Selection Modal -->
{#if showCreateModal}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
		role="dialog"
		aria-modal="true"
		onclick={() => (showCreateModal = false)}
	>
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div
			class="bg-white dark:bg-gray-900 rounded-3xl border border-gray-100/30 dark:border-gray-850/30 shadow-xl w-full max-w-lg mx-4 p-6 max-h-[80vh] overflow-y-auto"
			onclick={(e) => e.stopPropagation()}
		>
			<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">选择流程模板</h2>
			<p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
				选择一个流程模板以执行 AI 驱动的工作流。
			</p>

			<div class="space-y-2 mb-4">
				{#each flowTemplates as tpl (tpl.id)}
					<button
						class="w-full text-left px-4 py-3 rounded-2xl border border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 transition-colors"
						onclick={() => {
							showCreateModal = false;
							selectedStepId = tpl.id;
						}}
					>
						<div class="flex items-center gap-2">
							<span class="font-medium text-gray-900 dark:text-white text-sm">{tpl.name}</span>
							{#if tpl.source === 'custom'}
								<span class="px-1.5 py-0.5 text-[10px] font-medium rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">自定义</span>
							{/if}
						</div>
						<div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
							{tpl.input_module} → {tpl.output_module} · {tpl.step_count} 步骤
						</div>
						<p class="text-xs text-gray-400 dark:text-gray-500 mt-1 line-clamp-2">{tpl.description}</p>
					</button>
				{/each}
				{#if flowTemplates.length === 0}
					<p class="text-sm text-gray-400 dark:text-gray-500 text-center py-4">暂无可用模板</p>
				{/if}
			</div>

			<div class="flex justify-end">
				<button
					class="px-3 py-1.5 rounded-xl bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
					onclick={() => (showCreateModal = false)}
				>
					取消
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Flow Preview Modal -->
{#if showPreviewModal && previewData}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
		role="dialog"
		aria-modal="true"
		onclick={() => (showPreviewModal = false)}
	>
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div
			class="bg-white dark:bg-gray-900 rounded-3xl border border-gray-100/30 dark:border-gray-850/30 shadow-xl w-full max-w-lg mx-4 p-6"
			onclick={(e) => e.stopPropagation()}
		>
			<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">
				{previewData.template_name}
			</h2>
			<p class="text-sm text-gray-500 dark:text-gray-400 mb-4">预览执行步骤和预期输出</p>

			<div class="space-y-3 mb-4">
				<div>
					<h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">源条目</h4>
					{#each previewData.source_entries as src}
						<div class="text-sm text-gray-700 dark:text-gray-300 px-3 py-1.5 rounded-xl bg-gray-50 dark:bg-gray-800/50 mb-1">
							{src.title} <span class="text-xs text-gray-400">({src.module_type})</span>
						</div>
					{/each}
				</div>

				<div>
					<h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">执行步骤</h4>
					{#each previewData.steps as step, i}
						<div class="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 mb-1">
							<span class="w-6 h-6 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-xs font-bold text-gray-500">{i + 1}</span>
							<span class="font-medium">{step.action}</span>
							<span class="text-xs text-gray-400">— {step.description}</span>
						</div>
					{/each}
				</div>

				{#if previewData.estimated_outputs.length > 0}
					<div>
						<h4 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">预期输出</h4>
						{#each previewData.estimated_outputs as out}
							<div class="text-sm text-gray-700 dark:text-gray-300 px-3 py-1.5 rounded-xl bg-blue-50 dark:bg-blue-900/20 mb-1">
								{out.type}: {out.description} ({out.estimated_count})
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<div class="flex justify-end gap-2">
				<button
					class="px-3 py-1.5 rounded-xl bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
					onclick={() => (showPreviewModal = false)}
				>
					取消
				</button>
				<button
					class="px-3 py-1.5 rounded-xl bg-green-600 text-white text-sm font-medium hover:bg-green-700 transition-colors"
					onclick={handleConfirmPreview}
				>
					确认执行
				</button>
			</div>
		</div>
	</div>
{/if}
