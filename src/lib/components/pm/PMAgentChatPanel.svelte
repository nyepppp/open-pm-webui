<script lang="ts">
	import { onMount } from 'svelte';
	import {
		chatMessages,
		chatSending,
		chatError,
		agentStatus,
		chatContext,
		sendMessage,
		clearChat,
		refreshAgentStatus,
		updateActionStatus,
		availableModels,
		hasModels,
		selectedModelId
	} from '$lib/stores/pm/agentChatStore';
	import type { AgentAction, ModuleType } from '$lib/apis/pm/types';

	interface Props {
		isOpen?: boolean;
		onClose?: () => void;
		projectId: string;
		moduleType?: ModuleType;
		entryId?: string;
		projectName?: string;
		entryTitle?: string;
		entryContentSummary?: string;
		onApplyAction?: (action: AgentAction) => void;
	}

	let {
		isOpen = false,
		onClose,
		projectId,
		moduleType,
		entryId,
		projectName,
		entryTitle,
		entryContentSummary,
		onApplyAction
	}: Props = $props();

	let inputMessage = $state('');
	let messagesContainer: HTMLDivElement | undefined = $state();
	let pendingConfirmAction = $state<AgentAction | null>(null);

	// Sync context to store
	$effect(() => {
		chatContext.set({
			projectId,
			moduleType,
			entryId,
			projectName,
			entryTitle,
			entryContentSummary
		});
	});

	onMount(() => {
		refreshAgentStatus();
	});

	// Auto-scroll to bottom on new messages
	$effect(() => {
		const msgs = $chatMessages;
		if (messagesContainer) {
			requestAnimationFrame(() => {
				messagesContainer!.scrollTop = messagesContainer!.scrollHeight;
			});
		}
	});

	function handleSend() {
		if (!inputMessage.trim() || $chatSending) return;
		const msg = inputMessage;
		inputMessage = '';
		sendMessage(msg);
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSend();
		}
	}

	function handleApplyAction(action: AgentAction) {
		pendingConfirmAction = action;
	}

	function confirmApplyAction() {
		if (!pendingConfirmAction) return;
		updateActionStatus(pendingConfirmAction.id, 'applied');
		onApplyAction?.(pendingConfirmAction);
		pendingConfirmAction = null;
	}

	function cancelApplyAction() {
		pendingConfirmAction = null;
	}

	function handleDismissAction(action: AgentAction) {
		updateActionStatus(action.id, 'dismissed');
	}

	function getActionTypeLabel(type: string): string {
		const labels: Record<string, string> = {
			'pm.entry.create': '创建条目',
			'pm.entry.update': '更新条目',
			'pm.relation.create': '创建关联',
			'pm.version.create': '创建版本',
			'pm.parameter.extract': '提取参数'
		};
		return labels[type] || type;
	}

	const quickPrompts = [
		{ label: '生成 PRD 大纲', message: '帮我生成一份 PRD 大纲' },
		{ label: '分析需求', message: '分析当前项目的需求，给出分类和优先级建议' },
		{ label: '竞品调研', message: '帮我做竞品分析，列出关键对比维度' },
		{ label: '提取参数', message: '从当前文档中提取关键参数' },
		{ label: '生成测试用例', message: '为当前功能生成测试用例' },
		{ label: '风险检查', message: '检查当前项目有哪些潜在风险' }
	];
</script>

{#if isOpen}
	<div class="fixed inset-0 z-50 flex justify-end">
		<!-- Backdrop -->
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div class="absolute inset-0 bg-black/30" onclick={() => onClose?.()}></div>

		<!-- Panel -->
		<div class="relative w-full max-w-md h-full bg-white dark:bg-gray-900 shadow-2xl flex flex-col border-l border-gray-200 dark:border-gray-700">
			<!-- Header -->
			<div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
				<div class="flex items-center gap-2">
					<div class="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center" aria-hidden="true">
						<svg class="w-4 h-4 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
						</svg>
					</div>
					<div>
						<h2 class="text-sm font-semibold text-gray-900 dark:text-gray-100">AI 助手</h2>
						<div class="flex items-center gap-1">
							<div class="w-1.5 h-1.5 rounded-full {$agentStatus.available || $hasModels ? 'bg-green-500' : 'bg-gray-400'}"></div>
							<span class="text-[10px] text-gray-500">
								{#if $agentStatus.available}
									{$agentStatus.model}
								{:else if $hasModels}
									{#if $selectedModelId}
										{$availableModels.find((m: any) => m.id === $selectedModelId)?.name || $selectedModelId}
									{:else}
										已连接
									{/if}
								{:else}
									未连接
								{/if}
							</span>
						</div>
					</div>
				</div>
				<div class="flex items-center gap-1">
					<button
						class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
						onclick={() => clearChat()}
						title="清空对话"
						aria-label="清空对话"
					>
						<svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
						</svg>
					</button>
					<button
						class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
						onclick={() => onClose?.()}
						aria-label="关闭"
					>
						<svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
			</div>

			<!-- Model selector (when PM agent not available but OpenWebUI models exist) -->
			{#if !$agentStatus.available && $hasModels}
				<div class="px-4 py-2 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800">
					<div class="flex items-center gap-2">
						<span class="text-[10px] text-gray-500 whitespace-nowrap">模型：</span>
						<select
							class="flex-1 text-xs px-2 py-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md outline-hidden"
							bind:value={$selectedModelId}
						>
							{#each $availableModels as model (model.id)}
								<option value={model.id}>{model.name}</option>
							{/each}
						</select>
					</div>
				</div>
			{:else if !$agentStatus.available && !$hasModels}
				<div class="px-4 py-2 bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-100 dark:border-yellow-800/50">
					<div class="flex items-center justify-between">
						<span class="text-xs text-yellow-700 dark:text-yellow-400">未配置 AI 模型</span>
						<a href="/workspace/models" class="text-xs text-blue-600 dark:text-blue-400 hover:underline">前往配置 →</a>
					</div>
				</div>
			{/if}

			<!-- Context indicator -->
			{#if moduleType || entryTitle}
				<div class="px-4 py-2 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800 text-xs text-gray-500">
					{#if projectName}<span class="text-gray-700 dark:text-gray-300 font-medium">{projectName}</span> · {/if}
					{#if moduleType}<span>{moduleType}</span>{/if}
					{#if entryTitle}<span class="ml-1 text-gray-400">→ {entryTitle}</span>{/if}
				</div>
			{/if}

			<!-- Messages -->
			<div bind:this={messagesContainer} class="flex-1 overflow-y-auto px-4 py-3 space-y-4">
				{#if $chatMessages.length === 0}
					<div class="text-center py-8">
						<svg class="w-10 h-10 mx-auto mb-3 text-purple-200 dark:text-purple-800" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
						</svg>
						<p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">PM AI 助手</p>
						<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
							我可以帮你生成 PRD、分析需求、竞品调研、提取参数等
						</p>
						<!-- Quick prompts -->
						<div class="flex flex-wrap gap-1.5 justify-center px-2">
							{#each quickPrompts as qp (qp.label)}
								<button
									class="px-2.5 py-1 text-xs rounded-full bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 hover:bg-purple-100 dark:hover:bg-purple-900/50 transition"
									onclick={() => { inputMessage = qp.message; handleSend(); }}
								>
									{qp.label}
								</button>
							{/each}
						</div>
					</div>
				{:else}
					{#each $chatMessages as msg (msg.id)}
						<div class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'}">
							<div class="max-w-[85%] {msg.role === 'user'
								? 'bg-purple-600 text-white rounded-2xl rounded-br-md px-3.5 py-2'
								: 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-2xl rounded-bl-md px-3.5 py-2'}">
								<!-- Skill badge -->
								{#if msg.skillId && msg.role === 'assistant'}
									<div class="flex items-center gap-1 mb-1.5">
										<svg class="w-3 h-3 text-purple-500 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
											<path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12" />
										</svg>
										<span class="text-[10px] font-medium text-purple-600 dark:text-purple-400">{msg.skillId}</span>
									</div>
								{/if}

								<p class="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>

								<!-- Actions -->
								{#if msg.actions && msg.actions.length > 0}
									<div class="mt-2 space-y-1.5">
										{#each msg.actions as action (action.id)}
											{#if action.status === 'pending'}
												<div class="bg-white dark:bg-gray-700 rounded-lg p-2.5 border border-gray-200 dark:border-gray-600">
													<div class="flex items-center gap-1.5 mb-1">
														<span class="px-1.5 py-0.5 text-[10px] rounded bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 font-medium">{getActionTypeLabel(action.type)}</span>
													</div>
													<p class="text-xs font-medium text-gray-800 dark:text-gray-200 mb-0.5">{action.label}</p>
													<p class="text-[10px] text-gray-500 dark:text-gray-400 mb-2">{action.description}</p>
													<div class="flex gap-1.5">
														<button
															class="flex-1 px-2 py-1 text-xs font-medium bg-green-600 hover:bg-green-700 text-white rounded-md transition"
															onclick={() => handleApplyAction(action)}
														>
															应用
														</button>
														<button
															class="px-2 py-1 text-xs font-medium bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 text-gray-700 dark:text-gray-200 rounded-md transition"
															onclick={() => handleDismissAction(action)}
														>
															忽略
														</button>
													</div>
												</div>
											{:else if action.status === 'applied'}
												<div class="flex items-center gap-1.5 text-xs text-green-600 dark:text-green-400">
													<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
													<span>{action.label} - 已应用</span>
												</div>
											{:else}
												<div class="flex items-center gap-1.5 text-xs text-gray-400">
													<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
													<span>{action.label} - 已忽略</span>
												</div>
											{/if}
										{/each}
									</div>
								{/if}
							</div>
						</div>
					{/each}

					{#if $chatSending}
						<div class="flex justify-start">
							<div class="bg-gray-100 dark:bg-gray-800 rounded-2xl rounded-bl-md px-4 py-3">
								<div class="flex items-center gap-2">
									<div class="animate-spin rounded-full h-3 w-3 border-2 border-purple-600 border-t-transparent"></div>
									<span class="text-xs text-gray-500">思考中...</span>
								</div>
							</div>
						</div>
					{/if}

					{#if $chatError}
						<div class="flex justify-start">
							<div class="bg-red-50 dark:bg-red-900/20 rounded-2xl rounded-bl-md px-3.5 py-2 border border-red-200 dark:border-red-800">
								<p class="text-xs text-red-600 dark:text-red-400">{$chatError}</p>
							</div>
						</div>
					{/if}
				{/if}
			</div>

			<!-- Input -->
			<div class="border-t border-gray-200 dark:border-gray-700 p-3">
				<div class="flex items-end gap-2">
					<textarea
						class="flex-1 text-sm px-3 py-2 bg-gray-50 dark:bg-gray-800 border-0 rounded-xl outline-hidden focus:ring-2 focus:ring-purple-500 resize-none max-h-32"
						placeholder="输入消息，如：帮我生成 PRD 大纲..."
						rows="1"
						bind:value={inputMessage}
						onkeydown={handleKeydown}
						disabled={$chatSending || (!$agentStatus.available && !$hasModels)}
					></textarea>
					<button
						class="flex-shrink-0 p-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white transition disabled:opacity-50 disabled:cursor-not-allowed"
						onclick={handleSend}
						disabled={!inputMessage.trim() || $chatSending || (!$agentStatus.available && !$hasModels)}
						aria-label="发送"
					>
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.768 0 013.27 20.876L5.999 12zm0 0h7.5" />
						</svg>
					</button>
				</div>
			</div>
		</div>
	</div>

	<!-- Action Confirmation Dialog -->
	{#if pendingConfirmAction}
		<div class="fixed inset-0 z-[60] bg-black/40 flex items-center justify-center" onclick={() => cancelApplyAction()}>
			<div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 p-4 max-w-sm w-full mx-4" onclick={(e) => e.stopPropagation()}>
				<div class="flex items-center gap-2 mb-3">
					<div class="w-8 h-8 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
						<svg class="w-4 h-4 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
						</svg>
					</div>
					<h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100">确认执行操作</h3>
				</div>
				<p class="text-sm text-gray-700 dark:text-gray-300 mb-1 font-medium">{pendingConfirmAction.label}</p>
				<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">{pendingConfirmAction.description}</p>
				<div class="flex gap-2 justify-end">
					<button class="px-3 py-1.5 text-sm rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 transition" onclick={cancelApplyAction}>取消</button>
					<button class="px-3 py-1.5 text-sm rounded-lg bg-green-600 hover:bg-green-700 text-white font-medium transition" onclick={confirmApplyAction}>确认执行</button>
				</div>
			</div>
		</div>
	{/if}
{/if}
