/**
 * Workflow API client
 */

import { WEBUI_API_BASE_URL } from '$lib/constants';

// Helper: parse JSON response with Content-Type guard to avoid `Unexpected token '<'`
// when SvelteKit SPA fallback returns index.html for unknown routes.
async function parseJsonResponse<T>(response: Response): Promise<T> {
	const contentType = response.headers.get('content-type') || '';
	if (!contentType.includes('application/json')) {
		throw new Error(`Expected JSON response but got ${contentType || 'unknown'}`);
	}
	return response.json() as Promise<T>;
}

export interface Workflow {
	id: string;
	name: string;
	description?: string;
	status: 'draft' | 'active' | 'archived';
	nodes: WorkflowNode[];
	edges: WorkflowEdge[];
	created_at: number;
	updated_at: number;
	owner_id?: string;
	project_ids?: string[];
	project_id?: string;
	tags?: string[];
}

export interface WorkflowNode {
	id: string;
	type: string;
	name: string;
	position_x: number;
	position_y: number;
	config?: Record<string, unknown>;
	input_schema?: Record<string, unknown>;
	output_schema?: Record<string, unknown>;
	script?: string;
	skill_id?: string;
}

export interface WorkflowEdge {
	id: string;
	source_node_id: string;
	target_node_id: string;
	data_mapping_rules?: Record<string, unknown>;
	label?: string;
}

export interface CreateWorkflowRequest {
	name: string;
	description?: string;
	project_ids?: string[];
	tags?: string[];
	nodes?: WorkflowNode[];
	edges?: WorkflowEdge[];
}

export interface UpdateWorkflowRequest {
	name?: string;
	description?: string;
	status?: 'draft' | 'active' | 'archived';
	nodes?: WorkflowNode[];
	edges?: WorkflowEdge[];
	project_ids?: string[];
	tags?: string[];
}

// Helper function to parse workflow data
function parseWorkflow(data: any): Workflow {
	// Parse nodes and edges if they are strings
	let nodes = data.nodes || [];
	let edges = data.edges || [];

	if (typeof nodes === 'string') {
		try { nodes = JSON.parse(nodes); } catch { nodes = []; }
	}
	if (typeof edges === 'string') {
		try { edges = JSON.parse(edges); } catch { edges = []; }
	}

	return {
		...data,
		nodes: Array.isArray(nodes) ? nodes : [],
		edges: Array.isArray(edges) ? edges : []
	};
}

// Get all workflows
export async function getWorkflows(token: string): Promise<Workflow[]> {
	const response = await fetch(`${WEBUI_API_BASE_URL}/workflows/`, {
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`Failed to fetch workflows (${response.status})${detail ? ': ' + detail : ''}`);
	}
	const data = await parseJsonResponse<any[]>(response);
	return data.map(parseWorkflow);
}

// Get workflow by ID
export async function getWorkflow(token: string, id: string): Promise<Workflow> {
	const response = await fetch(`${WEBUI_API_BASE_URL}/workflows/${id}`, {
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`Failed to fetch workflow (${response.status})${detail ? ': ' + detail : ''}`);
	}
	const data = await parseJsonResponse<any>(response);
	return parseWorkflow(data);
}

// Create workflow
export async function createWorkflow(token: string, data: CreateWorkflowRequest): Promise<Workflow> {
	const response = await fetch(`${WEBUI_API_BASE_URL}/workflows/`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			...data,
			nodes: JSON.stringify(data.nodes || []),
			edges: JSON.stringify(data.edges || [])
		})
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`Failed to create workflow (${response.status})${detail ? ': ' + detail : ''}`);
	}
	const result = await parseJsonResponse<any>(response);
	return parseWorkflow(result);
}

// Update workflow
export async function updateWorkflow(token: string, id: string, data: UpdateWorkflowRequest): Promise<Workflow> {
	const response = await fetch(`${WEBUI_API_BASE_URL}/workflows/${id}`, {
		method: 'PUT',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			...data,
			nodes: data.nodes ? JSON.stringify(data.nodes) : undefined,
			edges: data.edges ? JSON.stringify(data.edges) : undefined
		})
	});
	if (!response.ok) {
		let detail: any = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		const err = new Error(`Failed to update workflow (${response.status})${typeof detail === 'string' && detail ? ': ' + detail : ''}`);
		// 附加原始 detail 供调用方判断 400 校验错误结构
		(err as any).detail = detail;
		(err as any).status = response.status;
		throw err;
	}
	const result = await parseJsonResponse<any>(response);
	return parseWorkflow(result);
}

// Delete workflow
export async function deleteWorkflow(token: string, id: string): Promise<void> {
	const response = await fetch(`${WEBUI_API_BASE_URL}/workflows/${id}`, {
		method: 'DELETE',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		}
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`Failed to delete workflow (${response.status})${detail ? ': ' + detail : ''}`);
	}
}

// Execute workflow
export async function executeWorkflow(
	token: string,
	id: string,
	inputData: Record<string, unknown>,
	chatModelId?: string
): Promise<{ execution_id: string }> {
	// 将 chatModelId 注入到 input_data 中（后端会弹出 _chat_model_id 并用作 chat_model_id）
	const payload = chatModelId
		? { ...inputData, _chat_model_id: chatModelId }
		: inputData;
	const response = await fetch(`${WEBUI_API_BASE_URL}/workflows/${id}/execute`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify(payload)
	});
	if (!response.ok) throw new Error('Failed to execute workflow');
	return parseJsonResponse<{ execution_id: string }>(response);
}

// Execution status types
export interface ExecutionNodeResult {
	status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
	output?: Record<string, unknown>;
	error?: string;
	started_at?: number;
	completed_at?: number;
	execution_time_ms?: number;
}

export interface ExecutionStatus {
	execution_id: string;
	workflow_id: string;
	status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'awaiting_input';
	node_results?: Record<string, ExecutionNodeResult>;
	variables?: Record<string, unknown>;
	logs?: Array<{ timestamp: number; event_type: string; data: Record<string, unknown> }>;
	error_message?: string;
	started_at?: number;
	completed_at?: number;
	output_data?: Record<string, unknown>;
	/** 当 status === 'awaiting_input' 时存在，描述 human_input 节点的表单定义 */
	awaiting_input?: {
		node_id: string;
		prompt: string;
		fields: Array<{
			name: string;
			label: string;
			type: 'text' | 'textarea' | 'select' | 'confirm';
			options?: string[];
			required?: boolean;
		}>;
		output_variable: string;
	};
}

// Get execution status
export async function getExecutionStatus(
	token: string,
	workflowId: string,
	executionId: string
): Promise<ExecutionStatus> {
	const response = await fetch(
		`${WEBUI_API_BASE_URL}/workflows/${workflowId}/executions/${executionId}/status`,
		{
			method: 'GET',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				...(token && { Authorization: `Bearer ${token}` })
			}
		}
	);
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`Failed to fetch execution status (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return parseJsonResponse<ExecutionStatus>(response);
}

/** 恢复挂起在 human_input 节点的 workflow execution。
 *  前端在轮询到 status === 'awaiting_input' 后弹出表单，
 *  用户提交后调用本函数唤醒后端 asyncio.Event，工作流继续执行。
 */
export async function resumeWorkflowRun(
	token: string,
	executionId: string,
	nodeId: string,
	response: Record<string, unknown>
): Promise<{ status: string; execution_id: string; node_id: string }> {
	const res = await fetch(`${WEBUI_API_BASE_URL}/workflows/runs/${executionId}/resume`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Accept: 'application/json',
			...(token && { Authorization: `Bearer ${token}` })
		},
		body: JSON.stringify({ node_id: nodeId, response })
	});
	if (!res.ok) {
		let detail = '';
		try { const body = await res.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`Resume failed (${res.status})${detail ? ': ' + detail : ''}`);
	}
	return parseJsonResponse<{ status: string; execution_id: string; node_id: string }>(res);
}

// ===== AI Workflow Generation =====

/** D1: AI 多轮澄清单条追问结构 */
export interface ClarifyQuestion {
	key: string;
	question: string;
	suggested_answer: string;
	reason?: string;
}

/** AI 生成工作流 SSE 事件类型 */
export type AIWorkflowEvent =
	| { type: 'status'; content: string }
	| { type: 'clarify'; questions: ClarifyQuestion[] }
	| { type: 'result'; workflow: AIGeneratedWorkflow; warnings: string[] }
	| { type: 'error'; content: string };

/** AI 生成的工作流结构（与后端 ai_generator.py 输出对齐） */
export interface AIGeneratedWorkflow {
	name: string;
	description?: string;
	nodes: Array<{
		id: string;
		type: string;
		name: string;
		x: number;
		y: number;
		config?: Record<string, unknown>;
	}>;
	edges: Array<{
		id: string;
		sourceNodeId: string;
		targetNodeId: string;
		label?: string;
		sourcePortId?: string;
		targetPortId?: string;
	}>;
	warnings?: string[];
	template_used?: string | null;
	error?: string;
}

/** D1: 多轮澄清历史条目 */
export interface ClarifyHistoryEntry {
	role: 'user' | 'assistant';
	content: string;
}

/**
 * AI 流式生成工作流（D1: 多轮澄清，无轮次上限）。
 *
 * 通过 SSE 推送事件：
 * - {type: 'status', content} — 进度状态
 * - {type: 'clarify', questions} — AI 追问，前端收集答案后带 history 重新请求
 * - {type: 'result', workflow, warnings} — 最终结果
 * - {type: 'error', content} — 错误
 *
 * 用法：
 * ```ts
 * const history: ClarifyHistoryEntry[] = [];
 * for await (const event of generateWorkflowWithAI(token, description, modelId, undefined, history)) {
 *   if (event.type === 'clarify') {
 *     // 展示追问给用户，收集答案后把 {role:'assistant', content: JSON.stringify(event.questions)}
 *     // 和 {role:'user', content: '用户的答案'} push 到 history，再次调用 generateWorkflowWithAI
 *   }
 *   if (event.type === 'result') { ... }
 * }
 * ```
 */
export async function* generateWorkflowWithAI(
	token: string,
	description: string,
	modelId: string,
	templateHint?: string,
	history?: ClarifyHistoryEntry[],
	signal?: AbortSignal
): AsyncGenerator<AIWorkflowEvent, void, unknown> {
	const response = await fetch(`${WEBUI_API_BASE_URL}/workflows/ai-generate`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${token}`,
			'Content-Type': 'application/json',
			Accept: 'text/event-stream'
		},
		body: JSON.stringify({
			description,
			model_id: modelId,
			template_hint: templateHint ?? null,
			history: history ?? null
		}),
		signal
	});

	if (!response.ok) {
		let detail = '';
		try {
			const body = await response.json();
			detail = body.detail || body.message || '';
		} catch {}
		throw new Error(`AI 生成请求失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}

	if (!response.body) {
		throw new Error('AI 生成响应没有 body');
	}

	const reader = response.body.getReader();
	const decoder = new TextDecoder('utf-8');
	let buffer = '';

	try {
		while (true) {
			const { done, value } = await reader.read();
			if (done) break;

			buffer += decoder.decode(value, { stream: true });

			// SSE 事件以 "\n\n" 分隔
			let separatorIndex: number;
			while ((separatorIndex = buffer.indexOf('\n\n')) !== -1) {
				const rawEvent = buffer.slice(0, separatorIndex);
				buffer = buffer.slice(separatorIndex + 2);

				// 解析 "data: ..." 行（忽略 event:/id:/comment 行）
				const dataLines = rawEvent
					.split('\n')
					.filter((l) => l.startsWith('data:'))
					.map((l) => l.slice(5).trimStart());

				if (dataLines.length === 0) continue;

				const dataStr = dataLines.join('\n');
				try {
					const parsed = JSON.parse(dataStr) as AIWorkflowEvent;
					yield parsed;
				} catch (err) {
					console.error('Failed to parse SSE event:', dataStr, err);
				}
			}
		}
	} finally {
		reader.releaseLock();
	}
}

// ===== Part A: Extensions API =====

export type ExtensionType = 'tools' | 'functions' | 'skills' | 'mcp';

export interface ExtensionSpecField {
	name: string;
	type: string;
	description?: string;
	required?: boolean;
}

export interface Extension {
	id: string;
	name: string;
	description?: string;
	spec?: ExtensionSpecField[];
	// MCP 扩展独有字段：用于二级联动
	server_id?: string;
	server_name?: string;
}

// Get extensions list (tools / functions / skills / mcp)
export async function getExtensions(
	token: string,
	type: ExtensionType
): Promise<Extension[]> {
	const response = await fetch(`${WEBUI_API_BASE_URL}/workflows/extensions/${type}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			...(token && { Authorization: `Bearer ${token}` })
		}
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`Failed to fetch extensions (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return parseJsonResponse<Extension[]>(response);
}

// ===== Part B: Execution Node Detail API =====

export interface ExecutionNodeDetail {
	node_id: string;
	node_name: string;
	node_type: string;
	execution_id: string;
	workflow_id: string;
	status: string;
	output?: Record<string, unknown>;
	error?: string;
	execution_time_ms?: number;
	tool_call?: {
		extension_id?: string;
		input?: unknown;
		output?: unknown;
	} | null;
	write_target?: string | null;
	// FAIL-3: answer 节点实际写入 PM 条目后返回的 entry_id 与上下文，前端用于生成跳转链接
	write_target_entry_id?: string | null;
	write_target_project_id?: string | null;
	write_target_module?: string | null;
}

// Get execution node detail (runtime tracing)
export async function getExecutionNodeDetail(
	token: string,
	workflowId: string,
	executionId: string,
	nodeId: string
): Promise<ExecutionNodeDetail> {
	const response = await fetch(
		`${WEBUI_API_BASE_URL}/workflows/${workflowId}/executions/${executionId}/node/${nodeId}`,
		{
			method: 'GET',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				...(token && { Authorization: `Bearer ${token}` })
			}
		}
	);
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`Failed to fetch node detail (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return parseJsonResponse<ExecutionNodeDetail>(response);
}

// ===== Part B: Workflow Validation Error =====

export interface WorkflowValidationDetail {
	node_id: string;
	node_name: string;
	error: string;
	all_errors?: WorkflowValidationDetail[];
}
