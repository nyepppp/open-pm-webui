<script lang="ts">
	// AI 工作流生成器抽屉组件（D1: 多轮对话式澄清）
	// 通过对话式交互调用后端 /api/workflows/ai-generate 接口
	// AI 在信息不足时返回 clarify 事件，向用户追问（每条附建议答案可一键采纳）
	// 用户回答后带 history 重新请求，直到 AI 判断信息充分并生成 workflow
	import { fade, fly } from 'svelte/transition';
	import { onDestroy } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { models } from '$lib/stores';
	import { generateWorkflowWithAI } from '$lib/apis/workflow/index';
	import type {
		AIWorkflowEvent,
		AIGeneratedWorkflow,
		ClarifyQuestion,
		ClarifyHistoryEntry
	} from '$lib/apis/workflow/index';
	import type { Workflow, WorkflowNode, WorkflowEdge, NodeType, Port } from './types';

	// ===== Props =====
	interface Props {
		show?: boolean;
		onGenerated?: (workflow: Workflow) => void;
		onClose?: () => void;
	}

	let { show = $bindable(false), onGenerated, onClose }: Props = $props();

	// ===== State =====
	// 模型选择
	let selectedModelId = $state<string>('');
	// 模板提示（可选，作为 hint 传给后端）
	let templateHint = $state<string>('');
	// 用户输入的描述（初始描述，多轮澄清期间用作用户回答）
	let description = $state<string>('');
	// 上次提交的描述（用于失败后一键重试）
	let lastDescription = $state<string>('');
	// 聊天消息列表：role='user' 是用户描述；role='assistant' 是 AI 状态/结果/追问
	type ChatMessage =
		| { role: 'user'; content: string; ts: number }
		| {
				role: 'assistant';
				content: string;
				ts: number;
				kind: 'status' | 'result' | 'error' | 'clarify';
				warnings?: string[];
				clarifyQuestions?: ClarifyQuestion[];
		  };
	let messages = $state<ChatMessage[]>([]);
	// D1: 多轮澄清历史 — 累积所有 user/assistant 对话内容，下次请求时一起发回后端
	let clarifyHistory = $state<ClarifyHistoryEntry[]>([]);
	// D1: 当前是否处于"等待用户回答追问"模式
	let pendingClarify = $state<ClarifyQuestion[] | null>(null);
	// D1: 用户回答输入（pendingClarify 不为空时显示）
	let userAnswer = $state<string>('');
	// D1: 原始描述（多轮澄清期间保留，每次请求都带）
	let originalDescription = $state<string>('');
	// 是否正在生成（用于禁用输入和按钮）
	let isGenerating = $state(false);
	// D11: 思考时间计时器
	let thinkingStartTime: number | null = null;
	let thinkingElapsed = $state(0);
	let thinkingTimer: ReturnType<typeof setInterval> | null = null;
	// D11: AbortController — 用于打断按钮中止 fetch
	let abortController: AbortController | null = null;
	// 自动滚动锚点
	let messagesContainer = $state<HTMLDivElement | null>(null);

	// ===== Derived =====
	// 从全局 models store 派生可用模型列表
	const modelOptions = $derived(
		($models || [])
			.filter((m: any) => m && m.id)
			.map((m: any) => ({ id: m.id, name: m.name || m.id }))
	);
	// canSubmit: 初始提交模式（无 pendingClarify）
	const canSubmit = $derived(
		!isGenerating &&
			description.trim().length > 0 &&
			selectedModelId.length > 0 &&
			!pendingClarify
	);
	// canAnswer: 回答追问模式
	const canAnswer = $derived(
		!isGenerating && pendingClarify !== null && selectedModelId.length > 0
	);

	// ===== 默认选中第一个模型 =====
	$effect(() => {
		if (!selectedModelId && modelOptions.length > 0) {
			selectedModelId = modelOptions[0].id;
		}
	});

	// ===== 自动滚动到底部 =====
	$effect(() => {
		const _len = messages.length;
		const _last = messages[_len - 1];
		void _len;
		void _last;
		queueMicrotask(() => {
			if (messagesContainer) {
				messagesContainer.scrollTop = messagesContainer.scrollHeight;
			}
		});
	});

	// ===== 关闭抽屉（重置所有状态） =====
	function handleClose() {
		if (isGenerating) {
			toast.warning('生成进行中，关闭抽屉将终止当前请求');
		}
		show = false;
		onClose?.();
	}

	// ===== 重置会话（关闭后再次打开时清空） =====
	function resetSession() {
		messages = [];
		clarifyHistory = [];
		pendingClarify = null;
		userAnswer = '';
		originalDescription = '';
		lastDescription = '';
		description = '';
		isGenerating = false;
	}

	// D11: 启动思考时间计时器
	function startThinkingTimer() {
		thinkingStartTime = Date.now();
		thinkingElapsed = 0;
		if (thinkingTimer) clearInterval(thinkingTimer);
		thinkingTimer = setInterval(() => {
			if (thinkingStartTime) {
				thinkingElapsed = Math.floor((Date.now() - thinkingStartTime) / 1000);
			}
		}, 1000);
	}

	// D11: 停止思考时间计时器
	function stopThinkingTimer() {
		if (thinkingTimer) {
			clearInterval(thinkingTimer);
			thinkingTimer = null;
		}
		thinkingStartTime = null;
		thinkingElapsed = 0;
	}

	// D11: 打断按钮 — 取消当前 AI 生成
	function handleInterrupt() {
		if (abortController) {
			try {
				abortController.abort();
			} catch (_) { /* 已 abort 则忽略 */ }
			abortController = null;
		}
		stopThinkingTimer();
		isGenerating = false;
		// 移除最后一条 status 占位消息（避免残留"正在调用 AI 模型…"）
		messages = messages.filter((m, i) => {
			if (m.role !== 'assistant') return true;
			if (m.kind !== 'status') return true;
			// 只移除最后一条 status
			return i !== messages.length - 1 || m.content.startsWith('生成失败');
		});
		toast.info('已取消 AI 生成');
	}

	// ===== 提交初始描述（首轮请求） =====
	async function handleGenerate() {
		if (!canSubmit) return;

		const userDesc = description.trim();
		if (!userDesc) return;

		// 初始化原始描述（多轮澄清期间保留）
		originalDescription = userDesc;
		lastDescription = userDesc;
		clarifyHistory = [];

		// 追加用户消息
		messages = [
			...messages,
			{ role: 'user', content: userDesc, ts: Date.now() }
		];
		// 清空输入
		description = '';

		// 启动生成（首调用，history 为空）
		await runGenerationFlow(userDesc, []);
	}

	// ===== 提交追问回答（后续轮次） =====
	async function handleAnswerClarify() {
		if (!pendingClarify || !canAnswer) return;

		// 收集用户答案：若用户未填则用所有 suggested_answer 拼接
		const answerText =
			userAnswer.trim() ||
			pendingClarify.map((q) => `${q.key}: ${q.suggested_answer}`).join('\n');

		// 追加用户消息
		messages = [...messages, { role: 'user', content: answerText, ts: Date.now() }];
		// 把追问内容 + 用户答案都加入 history
		// （追问作为 assistant 消息已经在收到 clarify 时加入，这里只加用户答案）
		clarifyHistory = [...clarifyHistory, { role: 'user', content: answerText }];

		// 清空追问状态
		pendingClarify = null;
		userAnswer = '';

		// 继续生成（带 history）
		await runGenerationFlow(originalDescription, clarifyHistory);
	}

	// ===== 一键采纳建议答案 =====
	function adoptSuggestedAnswer(q: ClarifyQuestion) {
		const line = `${q.key}: ${q.suggested_answer}`;
		userAnswer = userAnswer ? `${userAnswer}\n${line}` : line;
	}

	// ===== 一键采纳所有建议答案 =====
	function adoptAllSuggested() {
		if (!pendingClarify) return;
		userAnswer = pendingClarify.map((q) => `${q.key}: ${q.suggested_answer}`).join('\n');
	}

	// ===== 核心生成流程（首调用和后续轮次共用） =====
	async function runGenerationFlow(desc: string, history: ClarifyHistoryEntry[]) {
		isGenerating = true;
		// D11: 启动思考时间计时器 + AbortController
		startThinkingTimer();
		abortController = new AbortController();

		// 追加占位的 AI 状态消息
		const startedAt = Date.now();
		messages = [
			...messages,
			{ role: 'assistant', content: '正在启动 AI 生成…', ts: startedAt, kind: 'status' }
		];

		try {
			const token = localStorage.token || '';
			const modelId = selectedModelId;
			const hint = templateHint.trim() || undefined;

			let lastStatusIndex = messages.length - 1;
			let gotResult = false;

			for await (const event of generateWorkflowWithAI(token, desc, modelId, hint, history, abortController.signal)) {
				const evt = event as AIWorkflowEvent;
				if (evt.type === 'status') {
					// 更新最后一条状态消息内容
					messages = messages.map((m, i) =>
						i === lastStatusIndex && m.role === 'assistant'
							? { ...m, content: evt.content, ts: Date.now(), kind: 'status' }
							: m
					);
				} else if (evt.type === 'clarify') {
					// D1: AI 追问 — 展示给用户，等待回答
					pendingClarify = evt.questions;
					const clarifyText =
						`我需要确认几个关键信息（共 ${evt.questions.length} 项）：\n\n` +
						evt.questions
							.map((q, i) => `${i + 1}. ${q.question}\n   建议答案：${q.suggested_answer}`)
							.join('\n\n');

					// 把追问也加入 history（作为 assistant 消息）
					clarifyHistory = [
						...clarifyHistory,
						{ role: 'assistant', content: clarifyText }
					];

					// 替换占位消息为追问消息
					messages = messages.map((m, i) =>
						i === lastStatusIndex && m.role === 'assistant'
							? {
									...m,
									content: clarifyText,
									ts: Date.now(),
									kind: 'clarify' as const,
									clarifyQuestions: evt.questions
								}
							: m
					);
					// 收到追问，停止当前 SSE 流，等待用户回答
					return;
				} else if (evt.type === 'error') {
					// 替换占位消息为错误
					messages = messages.map((m, i) =>
						i === lastStatusIndex && m.role === 'assistant'
							? { ...m, content: `生成失败：${evt.content}`, ts: Date.now(), kind: 'error' }
							: m
					);
					toast.error(evt.content);
				} else if (evt.type === 'result') {
					gotResult = true;
					const wf = evt.workflow;
					const warnings = evt.warnings || [];

					// 检查后端返回的业务级错误
					if (wf.error === 'LLM_OUTPUT_UNPARSEABLE' || wf.error === 'LLM_CLARIFY_FAILED' || wf.error === 'EMPTY_WORKFLOW' || wf.error === 'LLM_CLARIFY_MAX_ROUNDS_FAILED') {
						const errorContent =
							`✗ 生成失败：${getErrorLabel(wf.error)}\n` +
							(warnings.length > 0
								? `修复记录（${warnings.length} 条）：\n${warnings.map((w) => `• ${w}`).join('\n')}`
								: '');
						messages = messages.map((m, i) =>
							i === lastStatusIndex && m.role === 'assistant'
								? { ...m, content: errorContent, ts: Date.now(), kind: 'error', warnings }
								: m
						);
						toast.error(getErrorLabel(wf.error));
					} else {
						// 替换占位消息为结果摘要
						const summary =
							`✓ 生成完成：${wf.name}\n` +
							`节点 ${wf.nodes?.length || 0} 个 / 连线 ${wf.edges?.length || 0} 条` +
							(wf.template_used ? `\n（使用模板：${wf.template_used}）` : '');
						messages = messages.map((m, i) =>
							i === lastStatusIndex && m.role === 'assistant'
								? { ...m, content: summary, ts: Date.now(), kind: 'result' }
								: m
						);

						// 注入画布
						const injected = injectWorkflow(wf);
						if (injected) {
							if (warnings.length > 0) {
								toast.success(`AI 已自动修复 ${warnings.length} 处问题`);
							} else {
								toast.success('工作流已注入画布');
							}
							onGenerated?.(injected);
						}
					}
				}
			}

			if (!gotResult && !pendingClarify) {
				// 没有收到 result 事件（异常断流）
				messages = messages.map((m, i) =>
					i === lastStatusIndex && m.role === 'assistant'
						? { ...m, content: '生成结束但未收到结果', ts: Date.now(), kind: 'error' }
						: m
				);
			}
		} catch (err: any) {
			// D11: AbortError 不再报错（用户主动取消）
			if (err?.name === 'AbortError') {
				return;
			}
			const errMsg = err?.message || String(err);
			messages = messages.map((m, i) =>
				m.role === 'assistant' && i === messages.length - 1
					? { ...m, content: `生成失败：${errMsg}`, ts: Date.now(), kind: 'error' }
					: m
			);
			toast.error(errMsg);
		} finally {
			isGenerating = false;
			stopThinkingTimer();
			abortController = null;
		}
	}

	// 错误码 → 友好文案
	function getErrorLabel(error?: string): string {
		switch (error) {
			case 'LLM_OUTPUT_UNPARSEABLE':
				return 'LLM 3 次解析失败，无法生成有效工作流';
			case 'LLM_CLARIFY_FAILED':
				return 'LLM 澄清输出解析失败';
			case 'LLM_CLARIFY_MAX_ROUNDS_FAILED':
				return '已达 10 轮上限，兜底生成也失败';
			case 'EMPTY_WORKFLOW':
				return 'LLM 返回的工作流为空';
			default:
				return '生成失败';
		}
	}

	// ===== 将 AI 生成的工作流转换为前端 Workflow 结构 =====
	function injectWorkflow(wf: AIGeneratedWorkflow): Workflow | null {
		try {
			const nodes: WorkflowNode[] = (wf.nodes || []).map((n) => ({
				id: n.id,
				type: (n.type as NodeType) || 'code',
				name: n.name || n.type || 'Node',
				x: n.x ?? 0,
				y: n.y ?? 0,
				width: 160,
				height: 60,
				config: n.config || {},
				ports: defaultPorts()
			}));

			const edges: WorkflowEdge[] = (wf.edges || []).map((e) => ({
				id: e.id,
				sourceNodeId: e.sourceNodeId,
				targetNodeId: e.targetNodeId,
				sourcePortId: e.sourcePortId || 'out',
				targetPortId: e.targetPortId || 'in',
				label: e.label
			}));

			return {
				id: crypto.randomUUID(),
				name: wf.name || 'AI Generated Workflow',
				description: wf.description || '',
				status: 'draft',
				nodes,
				edges
			};
		} catch (err) {
			console.error('injectWorkflow failed:', err);
			return null;
		}
	}

	// 默认端口（一个输入 + 一个输出）
	function defaultPorts(): Port[] {
		return [
			{ id: 'in', name: 'input', direction: 'input' },
			{ id: 'out', name: 'output', direction: 'output' }
		];
	}

	// ===== 输入框回车提交（Shift+Enter 换行） =====
	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			if (pendingClarify) {
				handleAnswerClarify();
			} else {
				handleGenerate();
			}
		}
	}

	// ===== 一键重试上次描述（用于 LLM 解析失败后） =====
	function retryLast() {
		if (!lastDescription || isGenerating) return;
		// 重置澄清历史，重新开始
		clarifyHistory = [];
		pendingClarify = null;
		userAnswer = '';
		// 移除所有 messages，保留原始描述作为新一轮起点
		messages = [];
		description = lastDescription;
		handleGenerate();
	}

	// ===== 重置会话（用户主动清空） =====
	function handleReset() {
		if (isGenerating) {
			toast.warning('生成进行中，无法重置');
			return;
		}
		resetSession();
	}

	// D11: 组件销毁时清理计时器 + abort
	onDestroy(() => {
		stopThinkingTimer();
		if (abortController) {
			try { abortController.abort(); } catch (_) {}
			abortController = null;
		}
	});
</script>

{#if show}
	<!-- 背景遮罩 -->
	<div
		class="fixed inset-0 z-40 bg-black/40"
		transition:fade={{ duration: 150 }}
		onclick={handleClose}
		onkeydown={(e) => { if (e.key === 'Escape') handleClose(); }}
		role="presentation"
	></div>

	<!-- 抽屉主体 -->
	<aside
		class="fixed right-0 top-0 bottom-0 z-50 w-full max-w-[480px] flex flex-col bg-white dark:bg-gray-900 dark:text-gray-100 shadow-2xl border-l border-gray-200 dark:border-gray-800"
		transition:fly={{ x: 480, duration: 200 }}
		role="dialog"
		aria-label="AI 工作流生成器"
	>
		<!-- 头部 -->
		<header class="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-800">
			<div class="flex items-center gap-2">
				<svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
				</svg>
				<h2 class="text-base font-semibold">AI 创建工作流</h2>
			</div>
			<button
				class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
				onclick={handleClose}
				aria-label="关闭"
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</header>

		<!-- 模型 + 模板选择区 -->
		<div class="px-4 py-3 border-b border-gray-200 dark:border-gray-800 space-y-2">
			<div class="flex items-center gap-2">
				<label for="ai-model-select" class="text-xs text-gray-500 dark:text-gray-400 w-14 shrink-0">模型</label>
				<select
					id="ai-model-select"
					class="flex-1 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-transparent px-2 py-1.5 outline-none focus:border-blue-500"
					bind:value={selectedModelId}
					disabled={isGenerating}
				>
					{#if modelOptions.length === 0}
						<option value="">无可用模型</option>
					{:else}
						{#each modelOptions as opt (opt.id)}
							<option value={opt.id}>{opt.name}</option>
						{/each}
					{/if}
				</select>
			</div>
			<div class="flex items-center gap-2">
				<label for="ai-template-hint" class="text-xs text-gray-500 dark:text-gray-400 w-14 shrink-0">模板</label>
				<input
					id="ai-template-hint"
					type="text"
					class="flex-1 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-transparent px-2 py-1.5 outline-none focus:border-blue-500"
					placeholder="可选：content_moderation / data_pipeline / 留空自动选择"
					bind:value={templateHint}
					disabled={isGenerating}
				/>
			</div>
		</div>

		<!-- 消息列表 -->
		<div
			bind:this={messagesContainer}
			class="flex-1 overflow-y-auto px-4 py-3 space-y-3"
		>
			{#if messages.length === 0}
				<div class="h-full flex flex-col items-center justify-center text-center text-gray-400 dark:text-gray-500">
					<svg class="w-12 h-12 mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
					</svg>
					<p class="text-sm">描述你想要的工作流，AI 会先追问关键信息再生成</p>
					<p class="text-xs mt-2 opacity-75">例如：内容审核流水线，先 LLM 分析，再根据分数分流</p>
				</div>
			{:else}
				{#each messages as msg (msg.ts + msg.role + msg.content.slice(0, 8))}
					{#if msg.role === 'user'}
						<div class="flex justify-end" in:fly={{ x: 20, duration: 150 }}>
							<div class="max-w-[80%] rounded-2xl rounded-br-sm bg-blue-600 text-white px-3 py-2 text-sm whitespace-pre-wrap break-words">
								{msg.content}
							</div>
						</div>
					{:else}
						<div
							class="flex justify-start"
							in:fly={{ x: -20, duration: 150 }}
						>
							<div
								class="max-w-[95%] rounded-2xl rounded-bl-sm px-3 py-2 text-sm whitespace-pre-wrap break-words
								{msg.kind === 'error'
									? 'bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300'
									: msg.kind === 'result'
										? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300'
										: msg.kind === 'clarify'
											? 'bg-amber-50 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200 border border-amber-200 dark:border-amber-800'
											: 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200'}"
							>
								{#if msg.kind === 'status' && isGenerating}
								<span class="inline-block w-3 h-3 mr-1 align-middle border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></span>
								{#if thinkingElapsed > 0}
									<span class="text-[10px] text-gray-400 ml-1">{thinkingElapsed}s</span>
								{/if}
							{/if}

								{#if msg.kind === 'clarify' && msg.clarifyQuestions}
									<!-- D1: 追问消息特殊样式 -->
									<div class="font-medium mb-2 flex items-center gap-1.5">
										<svg class="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
											<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093M12 17h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
										</svg>
										需要确认 {msg.clarifyQuestions.length} 项关键信息
									</div>
									<div class="space-y-2">
										{#each msg.clarifyQuestions as q, i (q.key + i)}
											<div class="rounded-lg bg-white/60 dark:bg-gray-900/40 px-2.5 py-2 border border-amber-100 dark:border-amber-900/50">
												<div class="text-xs text-amber-700 dark:text-amber-300 font-medium mb-0.5">
													{i + 1}. {q.question}
												</div>
												<div class="flex items-start justify-between gap-2">
													<div class="text-xs text-gray-600 dark:text-gray-300 flex-1">
														<span class="opacity-60">建议答案：</span>
														<span class="font-medium">{q.suggested_answer}</span>
														{#if q.reason}
															<div class="text-[10px] opacity-60 mt-0.5">{q.reason}</div>
														{/if}
													</div>
													<!-- 单条采纳按钮（仅在当前 pendingClarify 是这一组时可用） -->
													{#if pendingClarify && pendingClarify.find(p => p.key === q.key)}
														<button
															class="shrink-0 px-2 py-0.5 rounded-md text-[10px] font-medium bg-amber-600 hover:bg-amber-700 text-white transition-colors"
															onclick={() => adoptSuggestedAnswer(q)}
														>
															采纳
														</button>
													{/if}
												</div>
											</div>
										{/each}
									</div>
								{:else}
									{msg.content}
								{/if}

								{#if msg.kind === 'error' && lastDescription && !isGenerating}
									<div class="mt-2 pt-2 border-t border-red-200 dark:border-red-800">
										<button
											class="px-3 py-1 rounded-lg text-xs font-medium bg-red-600 hover:bg-red-700 text-white transition-colors"
											onclick={retryLast}
										>
											↻ 重试（使用上次描述）
										</button>
									</div>
								{/if}
							</div>
						</div>
					{/if}
				{/each}
			{/if}
		</div>

		<!-- 输入区（根据 pendingClarify 切换模式） -->
		<div class="px-4 py-3 border-t border-gray-200 dark:border-gray-800">
			{#if pendingClarify}
				<!-- D1: 回答追问模式 -->
				<div class="flex items-center justify-between mb-1.5">
					<span class="text-xs text-amber-600 dark:text-amber-400 font-medium">
						回答追问（{pendingClarify.length} 项） · 留空将自动采纳所有建议
					</span>
					<button
						class="text-[11px] px-2 py-0.5 rounded-md bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 hover:bg-amber-200 dark:hover:bg-amber-900/60 transition-colors"
						onclick={adoptAllSuggested}
						disabled={isGenerating}
					>
						采纳所有建议
					</button>
				</div>
				<textarea
					class="w-full text-sm rounded-xl border border-amber-300 dark:border-amber-700 bg-amber-50/40 dark:bg-amber-900/10 px-3 py-2 outline-none focus:border-amber-500 resize-none disabled:opacity-50"
					rows="4"
					placeholder={"逐条回答，格式：key: 答案（每行一条）。例如：\n" + pendingClarify.map(q => `${q.key}: ${q.suggested_answer}`).join('\n')}
					bind:value={userAnswer}
					onkeydown={handleKeydown}
					disabled={isGenerating}
				></textarea>
				<div class="flex items-center justify-between mt-2">
					<span class="text-xs text-gray-400">
						{isGenerating ? `AI 思考中… ${thinkingElapsed}s` : (userAnswer ? `${userAnswer.length} 字` : '将采纳建议答案')}
					</span>
					<div class="flex items-center gap-2">
						{#if isGenerating}
							<!-- D11: 打断按钮 — 取消当前 AI 生成 -->
							<button
								class="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-50 hover:bg-red-100 text-red-600 dark:bg-red-900/20 dark:hover:bg-red-900/40 dark:text-red-400 transition-colors"
								onclick={handleInterrupt}
								title="取消当前 AI 生成"
							>
								打断
							</button>
						{:else}
							<button
								class="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
								onclick={handleReset}
								disabled={isGenerating}
							>
								重置会话
							</button>
						{/if}
						<button
							class="px-4 py-1.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed
							{canAnswer
								? 'bg-amber-600 hover:bg-amber-700 text-white'
								: 'bg-gray-200 dark:bg-gray-800 text-gray-400'}"
							onclick={handleAnswerClarify}
							disabled={!canAnswer}
						>
							{isGenerating ? '提交中' : '提交回答'}
						</button>
					</div>
				</div>
			{:else}
				<!-- 初始描述 / 重新生成模式 -->
				<textarea
					class="w-full text-sm rounded-xl border border-gray-200 dark:border-gray-700 bg-transparent px-3 py-2 outline-none focus:border-blue-500 resize-none disabled:opacity-50"
					rows="3"
					placeholder="描述你想生成的工作流（Enter 发送，Shift+Enter 换行）"
					bind:value={description}
					onkeydown={handleKeydown}
					disabled={isGenerating}
				></textarea>
				<div class="flex items-center justify-between mt-2">
					<span class="text-xs text-gray-400">
						{isGenerating ? `AI 思考中… ${thinkingElapsed}s` : `${description.length} 字`}
					</span>
					<div class="flex items-center gap-2">
						{#if isGenerating}
							<!-- D11: 打断按钮 — 取消当前 AI 生成 -->
							<button
								class="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-50 hover:bg-red-100 text-red-600 dark:bg-red-900/20 dark:hover:bg-red-900/40 dark:text-red-400 transition-colors"
								onclick={handleInterrupt}
								title="取消当前 AI 生成"
							>
								打断
							</button>
						{:else if messages.length > 0}
							<button
								class="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
								onclick={handleReset}
							>
								重置会话
							</button>
						{/if}
						<button
							class="px-4 py-1.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed
							{canSubmit
								? 'bg-blue-600 hover:bg-blue-700 text-white'
								: 'bg-gray-200 dark:bg-gray-800 text-gray-400'}"
							onclick={handleGenerate}
							disabled={!canSubmit}
						>
							{isGenerating ? '生成中' : '生成'}
						</button>
					</div>
				</div>
			{/if}
		</div>
	</aside>
{/if}

<style>
	/* 抽屉自身滚动条美化 */
	.overflow-y-auto::-webkit-scrollbar {
		width: 6px;
	}
	.overflow-y-auto::-webkit-scrollbar-thumb {
		background-color: rgba(155, 155, 155, 0.3);
		border-radius: 3px;
	}
</style>
