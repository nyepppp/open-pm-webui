import { writable, derived, get, type Writable, type Readable } from 'svelte/store';
import type { AgentChatMessage, AgentAction, AgentSkillId, AgentStatus } from '$lib/apis/pm/types';
import {
	agentChatStream,
	getAgentStatus,
	sendEventResponse,
	type EventCallData
} from '$lib/apis/pm/agentChat';
import { getEntry, deleteEntry } from '$lib/apis/pm';
import { generateOpenAIChatCompletion } from '$lib/apis/openai/index';
import { models as modelsStore } from '$lib/stores';

// ============================================================================
// State
// ============================================================================

export const chatMessages: Writable<AgentChatMessage[]> = writable([]);
export const chatSending: Writable<boolean> = writable(false);
export const chatError: Writable<string | null> = writable(null);
export const agentStatus: Writable<AgentStatus> = writable({ available: false, provider: '', model: '' });

// Pending `__event_call__` event from backend (e.g. 2-phase delete
// confirmation). Set by sendMessage when stream yields event_call; consumed
// by PMAgentChatPanel.svelte to render confirmation modal.
export const pendingEventCall: Writable<EventCallData | null> = writable(null);

export const selectedModelId: Writable<string> = writable('');

// Current context (set by the module page)
export const chatContext: Writable<{
	projectId: string;
	moduleType?: string;
	entryId?: string;
	projectName?: string;
	entryTitle?: string;
	entryContentSummary?: string;
}> = writable({ projectId: '' });

// ============================================================================
// Derived
// ============================================================================

export const availableModels = derived(modelsStore, ($models) => {
	return ($models || []).filter((m: any) => m?.id).map((m: any) => ({ id: m.id, name: m.name || m.id }));
});

export const hasModels = derived(availableModels, ($available) => $available.length > 0);

export const lastAssistantMessage: Readable<AgentChatMessage | null> = derived(
	chatMessages,
	$msgs => {
		for (let i = $msgs.length - 1; i >= 0; i--) {
			if ($msgs[i].role === 'assistant') return $msgs[i];
		}
		return null;
	}
);

export const pendingActions: Readable<AgentAction[]> = derived(
	chatMessages,
	$msgs => $msgs.flatMap(m => (m.actions || []).filter(a => a.status === 'pending'))
);

// ============================================================================
// Actions
// ============================================================================

export function addMessage(message: AgentChatMessage) {
	chatMessages.update(list => {
		const updated = [...list, message];
		_saveHistory(updated);
		return updated;
	});
}

export function clearChat() {
	chatMessages.set([]);
	chatError.set(null);
	_clearHistory();
}

export function loadHistory(projectId: string) {
	try {
		const key = `pm-agent-chat-${projectId}`;
		const raw = localStorage.getItem(key);
		if (raw) {
			const parsed = JSON.parse(raw);
			if (Array.isArray(parsed)) {
				chatMessages.set(parsed);
			}
		}
	} catch {
		chatMessages.set([]);
	}
}

function _saveHistory(messages: AgentChatMessage[]) {
	try {
		const ctx = get(chatContext);
		const key = `pm-agent-chat-${ctx.projectId}`;
		// Keep max 100 messages per project
		const toSave = messages.slice(-100);
		localStorage.setItem(key, JSON.stringify(toSave));
	} catch {
		// localStorage might be unavailable
	}
}

function _clearHistory() {
	try {
		const ctx = get(chatContext);
		const key = `pm-agent-chat-${ctx.projectId}`;
		localStorage.removeItem(key);
	} catch {
		// ignore
	}
}

export function updateActionStatus(actionId: string, status: 'applied' | 'dismissed') {
	chatMessages.update(list =>
		list.map(m => ({
			...m,
			actions: (m.actions || []).map(a =>
				a.id === actionId ? { ...a, status } : a
			)
		}))
	);
}

function buildSystemPrompt(): string {
	const ctx = get(chatContext);
	const parts = ['你是 PM 工作台的 AI 助手，帮助产品经理完成日常工作。'];
	if (ctx.projectName) parts.push(`当前项目：${ctx.projectName}`);
	if (ctx.moduleType) parts.push(`当前模块：${ctx.moduleType}`);
	if (ctx.entryTitle) parts.push(`当前条目：${ctx.entryTitle}`);
	if (ctx.entryContentSummary) parts.push(`条目摘要：${ctx.entryContentSummary}`);
	parts.push('请用中文回答，给出专业、可操作的建议。');
	return parts.join('\n');
}

async function sendViaOpenWebUI(userMessage: string): Promise<AgentChatMessage> {
	const modelId = get(selectedModelId) || get(availableModels)[0]?.id;
	if (!modelId) throw new Error('没有可用的 AI 模型');

	const ctx = get(chatContext);
	const history = get(chatMessages);
	const systemPrompt = buildSystemPrompt();

	const messages = [
		{ role: 'system', content: systemPrompt },
		...history.slice(-20).map(m => ({ role: m.role as string, content: m.content })),
		{ role: 'user', content: userMessage.trim() }
	];

	const token = localStorage.token || '';
	const response = await generateOpenAIChatCompletion(token, {
		model: modelId,
		messages,
		stream: false
	});

	const content = typeof response === 'string' ? response :
		response?.choices?.[0]?.message?.content || '未获取到回复';

	return {
		id: (Date.now() + 1).toString(),
		role: 'assistant',
		content,
		timestamp: Date.now()
	};
}

export async function sendMessage(userMessage: string): Promise<void> {
	if (!userMessage.trim()) return;

	const ctx = get(chatContext);
	const userMsg: AgentChatMessage = {
		id: Date.now().toString(),
		role: 'user',
		content: userMessage.trim(),
		timestamp: Date.now()
	};
	addMessage(userMsg);
	chatSending.set(true);
	chatError.set(null);

	try {
		// Try PM backend first
		const token = localStorage.token || '';
		const status = get(agentStatus);

		if (status.available) {
			// Streaming path: create empty assistant message, then incrementally
			// update its content as stream events arrive (Task N5 / 6.2).
			const assistantId = (Date.now() + 1).toString();
			const assistantMsg: AgentChatMessage = {
				id: assistantId,
				role: 'assistant',
				content: '',
				timestamp: Date.now()
			};
			addMessage(assistantMsg);

			const stream = agentChatStream(token, {
				message: userMessage.trim(),
				projectId: ctx.projectId,
				moduleType: ctx.moduleType,
				entryId: ctx.entryId,
				context: {
					projectName: ctx.projectName,
					entryTitle: ctx.entryTitle,
					entryContentSummary: ctx.entryContentSummary
				}
			});

			for await (const event of stream) {
				switch (event.type) {
					case 'content':
						// Append incremental chunk to assistant message.
						chatMessages.update((list) => {
							const updated = [...list];
							const last = updated[updated.length - 1];
							if (last && last.id === assistantId) {
								last.content += event.data;
							}
							return updated;
						});
						break;
					case 'tool_call':
						// Surface "calling tool" status inside the same message.
						chatMessages.update((list) => {
							const updated = [...list];
							const last = updated[updated.length - 1];
							if (last && last.id === assistantId) {
								last.content += `\n\n> ⚙️ 正在调用工具 \`${event.data.name}\`...\n`;
							}
							return updated;
						});
						break;
					case 'tool_result':
						// Surface short tool result summary.
						chatMessages.update((list) => {
							const updated = [...list];
							const last = updated[updated.length - 1];
							if (last && last.id === assistantId) {
								const summary = _summarizeToolResult(event.data.result);
								last.content += `\n> ✅ 工具 \`${event.data.name}\` 返回: ${summary}\n`;
							}
							return updated;
						});
						break;
					case 'event_call':
						// 2-phase delete (or similar): trigger confirmation modal.
						// The stream may continue after the user responds; we set
						// pendingEventCall and let PMAgentChatPanel render the modal.
						pendingEventCall.set(event.data);
						break;
					case 'done':
						// Finalize: attach intent/skillId if backend sent them.
						chatMessages.update((list) => {
							const updated = [...list];
							const last = updated[updated.length - 1];
							if (last && last.id === assistantId) {
								if (event.data.skillId) {
									last.skillId = event.data.skillId;
								}
							}
							return updated;
						});
						break;
					case 'error':
						throw new Error(event.data.message);
				}
			}
		} else if (get(hasModels)) {
			// Fallback to OpenWebUI direct chat (non-streaming)
			const assistantMsg = await sendViaOpenWebUI(userMessage);
			addMessage(assistantMsg);
		} else {
			throw new Error('AI 服务未配置，请先配置 AI 模型');
		}
	} catch (err) {
		chatError.set(err instanceof Error ? err.message : String(err));
		addMessage({
			id: (Date.now() + 1).toString(),
			role: 'assistant',
			content: '抱歉，AI 服务暂时不可用。请稍后重试或检查 AI 配置。所有模块仍可手动编辑。',
			timestamp: Date.now()
		});
	} finally {
		chatSending.set(false);
	}
}

/**
 * Respond to a pending `__event_call__` (e.g. 2-phase delete confirmation).
 * Called by PMAgentChatPanel when user clicks "确认删除" or "取消".
 * Sends the response to backend via POST /api/v1/pm/agent/event-response;
 * backend then re-invokes the tool with confirmed=true/false.
 */
export async function respondToEventCall(
	confirmed: boolean,
	options?: { silent?: boolean }
): Promise<void> {
	const pending = get(pendingEventCall);
	if (!pending) return;
	const token = localStorage.token || '';
	try {
		await sendEventResponse(token, pending.event_id, confirmed);
		if (!options?.silent) {
			// Surface a system-style assistant note so the user sees confirmation
			// that the response was delivered.
			const note = confirmed
				? `✅ 已确认操作「${pending.entry_title || pending.entry_id || pending.event_id}」，后端正在执行...`
				: `ℹ️ 已取消操作「${pending.entry_title || pending.entry_id || pending.event_id}」`;
			chatMessages.update((list) => [
				...list,
				{
					id: (Date.now() + 1).toString(),
					role: 'assistant',
					content: note,
					timestamp: Date.now()
				}
			]);
		}
	} catch (err) {
		chatError.set(err instanceof Error ? err.message : String(err));
	} finally {
		pendingEventCall.set(null);
	}
}

/**
 * Format a tool result value into a short single-line summary for inline
 * display. Truncates long JSON to 200 chars.
 */
function _summarizeToolResult(value: unknown): string {
	let text: string;
	if (typeof value === 'string') {
		text = value;
	} else {
		try {
			text = JSON.stringify(value);
		} catch {
			text = String(value);
		}
	}
	if (text.length > 200) {
		return text.slice(0, 200) + '…';
	}
	return text;
}

// Bug 9 (v10): Helpers for OperationPreviewModal flow.
// fetchEntryForPreview: fetch full entry state to show as "before" in diff.
// executeConfirmedDelete: called when user confirms delete in OperationPreviewModal.
export async function fetchEntryForPreview(entryId: string): Promise<Record<string, unknown> | null> {
	try {
		const token = localStorage.token || '';
		const entry = await getEntry(token, entryId);
		return entry as Record<string, unknown>;
	} catch (err) {
		console.error('[PMAgent] fetchEntryForPreview failed:', err);
		return null;
	}
}

export async function executeConfirmedDelete(entryId: string): Promise<boolean> {
	try {
		const token = localStorage.token || '';
		await deleteEntry(token, entryId);
		return true;
	} catch (err) {
		console.error('[PMAgent] executeConfirmedDelete failed:', err);
		return false;
	}
}

export async function refreshAgentStatus(): Promise<void> {
	try {
		const token = localStorage.token || '';
		const status = await getAgentStatus(token);
		agentStatus.set(status);
	} catch {
		agentStatus.set({ available: false, provider: '', model: '' });
	}

	// Also check OpenWebUI models availability
	const $models = get(availableModels);
	if ($models.length > 0 && !get(selectedModelId)) {
		selectedModelId.set($models[0].id);
	}
}
