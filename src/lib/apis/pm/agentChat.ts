import { WEBUI_API_BASE_URL } from '$lib/constants';
import type {
	AgentChatRequest,
	AgentChatResponse,
	AgentStatus,
	AgentSkill,
	AgentIntent,
	AgentSkillId
} from './types';
import { EventSourceParserStream } from 'eventsource-parser/stream';

const PM_API_BASE = `${WEBUI_API_BASE_URL}/pm`;

function getHeaders(token: string = '') {
	return {
		Accept: 'application/json',
		'Content-Type': 'application/json',
		...(token && { authorization: `Bearer ${token}` })
	};
}

// ============================================================================
// Stream event types
// ============================================================================

/**
 * Event payload for a 2-phase delete confirmation request from backend.
 * Backend sends this via `__event_call__` when `pm_entry_delete(confirmed=False)`
 * is invoked; the frontend MUST respond via {@link sendEventResponse} so the
 * backend can re-invoke `pm_entry_delete(confirmed=True)`.
 */
export interface EventCallData {
	event_id: string;
	event_type: 'confirmation';
	entry_id?: string;
	entry_title?: string;
	module_type?: string;
	content_preview?: string;
	message: string;
}

/**
 * Discriminated union of all stream events yielded by {@link agentChatStream}.
 *
 * - `content`: incremental text chunk (string) to append to assistant message
 * - `tool_call`: LLM is invoking a tool; show "正在调用工具 X..."
 * - `tool_result`: tool returned; show summary
 * - `event_call`: 2-phase delete confirmation; trigger modal UI
 * - `done`: stream ended; finalize message (skillId/intent if any)
 * - `error`: stream-level error
 */
export type AgentChatStreamEvent =
	| { type: 'content'; data: string }
	| { type: 'tool_call'; data: { name: string; arguments: Record<string, unknown> } }
	| { type: 'tool_result'; data: { name: string; result: unknown } }
	| { type: 'event_call'; data: EventCallData }
	| { type: 'done'; data: { intent?: AgentIntent; skillId?: AgentSkillId } }
	| { type: 'error'; data: { message: string } };

// ============================================================================
// Agent Chat
// ============================================================================

/**
 * Streaming variant of PM agent chat.
 *
 * Opens a POST to `/api/v1/pm/agent/chat` and consumes the SSE event stream
 * (format: `data: {"type": "...", "data": ...}\n\n`). Yields events one at a
 * time so the caller can incrementally update the assistant message content,
 * surface tool-call status, and trigger `__event_call__` confirmation UI.
 *
 * Backend event protocol (per `.trae/specs/adapt-pm-agent-to-streaming-chat/spec.md`):
 * - `{"type":"content","data":"<chunk>"}` - incremental text
 * - `{"type":"tool_call","data":{"name":"...","arguments":{...}}}` - LLM invokes tool
 * - `{"type":"tool_result","data":{"name":"...","result":...}}` - tool returned
 * - `{"type":"event_call","data":EventCallData}` - 2-phase delete confirmation request
 * - `{"type":"done","data":{"intent?":...,"skillId?":...}}` - stream end
 * - `{"type":"error","data":{"message":"..."}}` - error
 *
 * Falls back to legacy non-streaming {@link agentChat} if the response is not
 * a stream (Content-Type != text/event-stream).
 */
export async function* agentChatStream(
	token: string,
	request: AgentChatRequest
): AsyncGenerator<AgentChatStreamEvent> {
	const response = await fetch(`${PM_API_BASE}/agent/chat`, {
		method: 'POST',
		// Request streaming response from backend
		headers: { ...getHeaders(token), Accept: 'text/event-stream' },
		body: JSON.stringify({ ...request, stream: true })
	});

	if (!response.ok) {
		let detail = '';
		try {
			const body = await response.json();
			detail = body.detail || body.message || '';
		} catch {
			// ignore parse error
		}
		yield {
			type: 'error',
			data: { message: `AI 对话失败 (${response.status})${detail ? ': ' + detail : ''}` }
		};
		return;
	}

	// Backend may still respond with JSON (e.g. legacy fallback path or error
	// before stream starts). Detect by Content-Type and degrade gracefully.
	const contentType = response.headers.get('content-type') || '';
	if (!contentType.includes('text/event-stream') || !response.body) {
		// Degrade to non-streaming: yield the full payload as one content event.
		try {
			const json: AgentChatResponse = await response.json();
			if (json.message) {
				yield { type: 'content', data: json.message };
			}
			yield {
				type: 'done',
				data: { intent: json.intent, skillId: json.skillId }
			};
		} catch (err) {
			yield {
				type: 'error',
				data: { message: err instanceof Error ? err.message : String(err) }
			};
		}
		return;
	}

	// Stream SSE: pipe through TextDecoder + EventSourceParser, yield each event.
	const reader = response.body
		.pipeThrough(new TextDecoderStream())
		.pipeThrough(new EventSourceParserStream())
		.getReader();

	try {
		while (true) {
			const { value, done } = await reader.read();
			if (done) {
				break;
			}
			if (!value) {
				continue;
			}
			const data = value.data;
			if (!data) {
				continue;
			}
			if (data === '[DONE]') {
				yield { type: 'done', data: {} };
				return;
			}
			try {
				const parsed = JSON.parse(data) as AgentChatStreamEvent;
				yield parsed;
			} catch (err) {
				console.error('[PM agentChatStream] Failed to parse SSE event:', err, data);
			}
		}
		// Stream ended without explicit [DONE] - emit done to finalize UI.
		yield { type: 'done', data: {} };
	} finally {
		try {
			reader.releaseLock();
		} catch {
			// ignore
		}
	}
}

/**
 * Send user's response to a 2-phase delete `__event_call__` back to backend.
 *
 * Backend endpoint: `POST /api/v1/pm/agent/event-response` with body
 * `{ event_id, confirmed }`. If the user confirmed, backend re-invokes
 * `pm_entry_delete(confirmed=True)` and executes the real delete.
 *
 * Note: backend endpoint is added per spec; if missing, this will throw a
 * network error that the caller can surface.
 */
export async function sendEventResponse(
	token: string,
	eventId: string,
	confirmed: boolean
): Promise<void> {
	const response = await fetch(`${PM_API_BASE}/agent/event-response`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify({ event_id: eventId, confirmed })
	});
	if (!response.ok) {
		let detail = '';
		try {
			const body = await response.json();
			detail = body.detail || body.message || '';
		} catch {
			// ignore
		}
		throw new Error(
			`事件响应失败 (${response.status})${detail ? ': ' + detail : ''}`
		);
	}
}

/**
 * Callback-style adapter over {@link agentChatStream}. Opens the streaming
 * POST to `/api/v1/pm/agent/chat` and forwards each SSE event to `onEvent`.
 *
 * Per spec `.trae/specs/adapt-pm-agent-to-streaming-chat/spec.md` Task N5:
 * the function no longer returns `AgentChatResponse` — all data reaches the
 * caller via `onEvent` (content deltas, tool-call status, event_call
 * confirmation requests, done, error).
 *
 * Prefer {@link agentChatStream} (async generator) for new code — it composes
 * better with `for await` and matches OpenWebUI's `createOpenAITextStream`
 * pattern in `src/lib/apis/streaming/index.ts` (consumed by
 * `src/lib/components/chat/Chat.svelte` L2839-2843). This callback variant is
 * kept for callers that prefer event-driven APIs.
 */
export async function agentChat(
	token: string,
	request: AgentChatRequest,
	onEvent?: (event: AgentChatStreamEvent) => void
): Promise<void> {
	for await (const event of agentChatStream(token, request)) {
		onEvent?.(event);
		if (event.type === 'error') {
			// Error event already carries the message; stop consuming.
			return;
		}
	}
}

export async function getAgentStatus(token: string): Promise<AgentStatus> {
	const response = await fetch(`${PM_API_BASE}/agent/status`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) {
		return { available: false, provider: '', model: '' };
	}
	return response.json();
}

export async function getAgentSkills(token: string): Promise<AgentSkill[]> {
	const response = await fetch(`${PM_API_BASE}/agent/skills`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) return [];
	return response.json();
}

export async function executeAgentSkill(
	token: string,
	skillId: string,
	params: { projectId: string; moduleType?: string; entryId?: string; data?: Record<string, unknown> }
): Promise<AgentChatResponse> {
	const response = await fetch(`${PM_API_BASE}/agent/skill/${skillId}`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(params)
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`Skill 执行失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.json();
}
