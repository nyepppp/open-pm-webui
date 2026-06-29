<script lang="ts">
	import { page } from '$app/stores';

	let projectId = $derived($page.params.projectId);

	// Step categories
	const categories: Record<string, { label: string; color: string }> = {
		planning: { label: '规划', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300' },
		design: { label: '设计', color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300' },
		management: { label: '管理', color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300' },
		acceptance: { label: '验收', color: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' },
		review: { label: '复盘', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300' },
		enablement: { label: '赋能', color: 'bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300' }
	};

	// Step statuses
	const statusConfig: Record<string, { label: string; color: string; dot: string }> = {
		pending: { label: '待开始', color: 'bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-400', dot: 'bg-gray-400 dark:bg-gray-500' },
		in_progress: { label: '进行中', color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300', dot: 'bg-blue-500' },
		completed: { label: '已完成', color: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300', dot: 'bg-green-500' },
		blocked: { label: '已阻塞', color: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300', dot: 'bg-red-500' },
		skipped: { label: '已跳过', color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300', dot: 'bg-yellow-500' }
	};

	interface Deliverable {
		name: string;
		module: string;
	}

	interface WorkflowStep {
		id: string;
		name: string;
		category: string;
		status: string;
		description: string;
		deliverables: Deliverable[];
		nextSteps: string[];
	}

	// Default workflow template (mock data)
	let workflowSteps = $state<WorkflowStep[]>([
		{
			id: 'requirement',
			name: '需求收集',
			category: 'planning',
			status: 'completed',
			description: '收集和整理项目需求，明确业务目标和用户痛点',
			deliverables: [
				{ name: '需求文档', module: 'requirement' },
				{ name: '用户故事地图', module: 'requirement' }
			],
			nextSteps: ['组织需求评审会议', '确认优先级排序']
		},
		{
			id: 'competitor',
			name: '竞品分析',
			category: 'planning',
			status: 'completed',
			description: '分析竞品功能、体验和商业模式，找出差异化机会',
			deliverables: [{ name: '竞品分析报告', module: 'competitor' }],
			nextSteps: ['提炼差异化功能点', '确定产品定位']
		},
		{
			id: 'prd',
			name: 'PRD编写',
			category: 'design',
			status: 'in_progress',
			description: '编写产品需求文档，详细描述功能规格和交互逻辑',
			deliverables: [
				{ name: 'PRD文档', module: 'prd' },
				{ name: '功能清单', module: 'prd' }
			],
			nextSteps: ['完成核心功能描述', '补充非功能性需求']
		},
		{
			id: 'parameter',
			name: '参数提取',
			category: 'design',
			status: 'pending',
			description: '从PRD中提取配置参数和技术参数，形成参数矩阵',
			deliverables: [{ name: '参数矩阵表', module: 'parameter' }],
			nextSteps: ['梳理可配置参数', '确认参数默认值']
		},
		{
			id: 'prototype',
			name: '原型走查',
			category: 'design',
			status: 'pending',
			description: '对原型设计进行走查，确保交互逻辑和视觉规范一致',
			deliverables: [
				{ name: '走查记录', module: 'prototype' },
				{ name: '问题清单', module: 'prototype' }
			],
			nextSteps: ['确认设计规范', '标记高优先级问题']
		},
		{
			id: 'testcase',
			name: '测试用例',
			category: 'enablement',
			status: 'pending',
			description: '根据PRD编写测试用例，覆盖核心业务场景',
			deliverables: [{ name: '测试用例集', module: 'testcase' }],
			nextSteps: ['覆盖核心场景', '补充边界用例']
		},
		{
			id: 'schedule',
			name: '排期',
			category: 'management',
			status: 'pending',
			description: '制定项目排期计划，明确里程碑和资源分配',
			deliverables: [
				{ name: '排期计划', module: 'schedule' },
				{ name: '资源分配表', module: 'schedule' }
			],
			nextSteps: ['确认关键里程碑', '评估资源风险']
		},
		{
			id: 'meeting',
			name: '评审',
			category: 'management',
			status: 'pending',
			description: '组织PRD评审会议，收集反馈并达成共识',
			deliverables: [
				{ name: '评审纪要', module: 'meeting' },
				{ name: '待办事项', module: 'meeting' }
			],
			nextSteps: ['发送评审邀请', '准备评审材料']
		},
		{
			id: 'risk',
			name: '风险管控',
			category: 'management',
			status: 'pending',
			description: '识别项目风险并制定应对策略',
			deliverables: [{ name: '风险登记表', module: 'risk' }],
			nextSteps: ['识别高风险项', '制定缓解措施']
		},
		{
			id: 'acceptance',
			name: '验收',
			category: 'acceptance',
			status: 'pending',
			description: '按验收标准对交付物进行验收确认',
			deliverables: [
				{ name: '验收报告', module: 'acceptance' },
				{ name: '问题清单', module: 'acceptance' }
			],
			nextSteps: ['确认验收标准', '执行验收测试']
		},
		{
			id: 'review',
			name: '复盘',
			category: 'review',
			status: 'pending',
			description: '对项目过程进行复盘总结，沉淀经验教训',
			deliverables: [
				{ name: '复盘报告', module: 'review' },
				{ name: '改进计划', module: 'review' }
			],
			nextSteps: ['组织复盘会议', '梳理改进项']
		}
	]);

	let selectedStepId = $state<string | null>(null);
	let showCreateModal = $state(false);

	let selectedStep = $derived(workflowSteps.find((s) => s.id === selectedStepId) ?? null);
	let completedCount = $derived(workflowSteps.filter((s) => s.status === 'completed').length);
	let totalCount = $derived(workflowSteps.length);
	let progressPercent = $derived(totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0);

	function toggleStep(id: string) {
		selectedStepId = selectedStepId === id ? null : id;
	}

	function markStepStatus(stepId: string, newStatus: string) {
		const idx = workflowSteps.findIndex((s) => s.id === stepId);
		if (idx !== -1) {
			workflowSteps[idx] = { ...workflowSteps[idx], status: newStatus };
		}
	}

	function getCategoryBadge(category: string) {
		return categories[category] ?? categories.planning;
	}

	function getStatusConfig(status: string) {
		return statusConfig[status] ?? statusConfig.pending;
	}
</script>

<svelte:head>
	<title>工作流 - PM</title>
</svelte:head>

<div class="p-4 md:p-6 max-w-5xl mx-auto">
	<!-- Header -->
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
				创建工作流
			</button>
		</div>

		<!-- Progress bar -->
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

	<!-- Workflow Steps Board -->
	{#if workflowSteps.length === 0}
		<!-- Empty state -->
		<div class="flex flex-col items-center justify-center py-16 text-center">
			<div class="w-16 h-16 mb-4 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
				<svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
				</svg>
			</div>
			<h3 class="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">暂无工作流</h3>
			<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">创建工作流以开始流程协作</p>
			<button
				class="px-3 py-1.5 rounded-xl bg-black text-white dark:bg-white dark:text-black text-sm font-medium hover:opacity-90 transition-opacity"
				onclick={() => (showCreateModal = true)}
			>
				创建工作流
			</button>
		</div>
	{:else}
		<div class="flex flex-col gap-1">
			{#each workflowSteps as step, index (step.id)}
				{@const cat = getCategoryBadge(step.category)}
				{@const stat = getStatusConfig(step.status)}
				{@const isSelected = selectedStepId === step.id}
				{@const isLast = index === workflowSteps.length - 1}

				<!-- Step Card -->
				<div class="group">
					<div
						class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100/30 dark:border-gray-850/30 transition-all duration-200 {isSelected
							? 'ring-2 ring-blue-500/30 shadow-md'
							: 'hover:shadow-sm hover:border-gray-200 dark:hover:border-gray-750'}"
					>
						<!-- Step Header (clickable) -->
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
							<!-- Step number circle -->
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
									{#if step.status === 'completed'}
										<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2.5">
											<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
										</svg>
									{:else}
										{index + 1}
									{/if}
								</div>
							</div>

							<!-- Step name & description -->
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

							<!-- Status badge & deliverables count -->
							<div class="flex items-center gap-2 flex-shrink-0">
								<span
									class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium {stat.color}"
								>
									<span class="w-1.5 h-1.5 rounded-full {stat.dot}"></span>
									{stat.label}
								</span>
								<span class="text-xs text-gray-400 dark:text-gray-500 hidden sm:inline">
									{step.deliverables.length} 交付物
								</span>
								<!-- Expand chevron -->
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

						<!-- Expanded Details -->
						{#if isSelected && selectedStep}
							<div class="px-4 pb-4 border-t border-gray-50 dark:border-gray-800/50">
								<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3">
									<!-- Deliverables -->
									<div class="md:col-span-2">
										<h4
											class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2"
										>
											交付物
										</h4>
										<div class="flex flex-col gap-1.5">
											{#each step.deliverables as deliv}
												<a
													href="/pm/{projectId}/{deliv.module}"
													class="flex items-center gap-2 px-3 py-2 rounded-xl bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-sm text-gray-700 dark:text-gray-300 group/link"
												>
													<svg
														class="w-4 h-4 text-gray-400 group-hover/link:text-blue-500 flex-shrink-0"
														fill="none"
														stroke="currentColor"
														viewBox="0 0 24 24"
													>
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															stroke-width="2"
															d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
														/>
													</svg>
													{deliv.name}
													<svg
														class="w-3 h-3 ml-auto text-gray-300 dark:text-gray-600 group-hover/link:text-blue-500 flex-shrink-0"
														fill="none"
														stroke="currentColor"
														viewBox="0 0 24 24"
													>
														<path
															stroke-linecap="round"
															stroke-linejoin="round"
															stroke-width="2"
															d="M9 5l7 7-7 7"
														/>
													</svg>
												</a>
											{/each}
										</div>
									</div>

									<!-- Next Steps & Actions -->
									<div>
										<h4
											class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2"
										>
											建议下一步
										</h4>
										<ul class="space-y-1.5 mb-4">
											{#each step.nextSteps as ns}
												<li class="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
													<span
														class="w-1.5 h-1.5 rounded-full bg-gray-300 dark:bg-gray-600 mt-1.5 flex-shrink-0"
													></span>
													{ns}
												</li>
											{/each}
										</ul>

										<!-- Action buttons -->
										<div class="flex flex-col gap-2">
											{#if step.status !== 'completed'}
												<button
													class="w-full px-3 py-1.5 rounded-xl bg-green-600 text-white text-sm font-medium hover:bg-green-700 transition-colors"
													onclick={() => markStepStatus(step.id, 'completed')}
												>
													标记完成
												</button>
											{/if}
											{#if step.status !== 'in_progress' && step.status !== 'completed'}
												<button
													class="w-full px-3 py-1.5 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
													onclick={() => markStepStatus(step.id, 'in_progress')}
												>
													标记进行中
												</button>
											{/if}
											{#if step.status === 'completed'}
												<button
													class="w-full px-3 py-1.5 rounded-xl bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
													onclick={() => markStepStatus(step.id, 'in_progress')}
												>
													重新开启
												</button>
											{/if}
										</div>
									</div>
								</div>
							</div>
						{/if}
					</div>

					<!-- Connector line between steps -->
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

<!-- Create Workflow Modal -->
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
			class="bg-white dark:bg-gray-900 rounded-3xl border border-gray-100/30 dark:border-gray-850/30 shadow-xl w-full max-w-md mx-4 p-6"
			onclick={(e) => e.stopPropagation()}
		>
			<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">创建工作流</h2>
			<p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
				选择工作流模板以快速开始，或创建空白工作流自定义步骤。
			</p>

			<div class="space-y-2 mb-6">
				<button
					class="w-full text-left px-4 py-3 rounded-2xl border border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 transition-colors"
					onclick={() => {
						showCreateModal = false;
					}}
				>
					<div class="font-medium text-gray-900 dark:text-white text-sm">产品研发流程</div>
					<div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
						11 个步骤 · 需求收集到复盘全流程
					</div>
				</button>
				<button
					class="w-full text-left px-4 py-3 rounded-2xl border border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-500 transition-colors"
					onclick={() => {
						workflowSteps = [];
						showCreateModal = false;
					}}
				>
					<div class="font-medium text-gray-900 dark:text-white text-sm">空白工作流</div>
					<div class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">从零开始自定义步骤</div>
				</button>
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
