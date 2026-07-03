import { WEBUI_API_BASE_URL } from '$lib/constants';
import type { AgentChatRequest, AgentChatResponse, AgentStatus, AgentSkill } from './types';

const PM_API_BASE = `${WEBUI_API_BASE_URL}/pm`;

function getHeaders(token: string = '') {
	return {
		Accept: 'application/json',
		'Content-Type': 'application/json',
		...(token && { authorization: `Bearer ${token}` })
	};
}

// ============================================================================
// Agent Chat
// ============================================================================

export async function agentChat(token: string, request: AgentChatRequest): Promise<AgentChatResponse> {
	const response = await fetch(`${PM_API_BASE}/agent/chat`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(request)
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`AI 对话失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.json();
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
