import { WEBUI_API_BASE_URL } from '$lib/constants';

const PM_API_BASE = `${WEBUI_API_BASE_URL}/pm`;

function getHeaders(token: string = '') {
	return {
		Accept: 'application/json',
		'Content-Type': 'application/json',
		...(token && { authorization: `Bearer ${token}` })
	};
}

export async function getOne<T = unknown>(path: string): Promise<T> {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const response = await fetch(`${PM_API_BASE}${path}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error(`GET ${path} failed (${response.status})`);
	return response.json();
}

export async function create<T = unknown>(path: string, data: unknown): Promise<T> {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const response = await fetch(`${PM_API_BASE}${path}`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error(`POST ${path} failed (${response.status})`);
	return response.json();
}

export async function update<T = unknown>(path: string, data: unknown): Promise<T> {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const response = await fetch(`${PM_API_BASE}${path}`, {
		method: 'PUT',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error(`PUT ${path} failed (${response.status})`);
	return response.json();
}

export async function remove<T = unknown>(path: string): Promise<T> {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const response = await fetch(`${PM_API_BASE}${path}`, {
		method: 'DELETE',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error(`DELETE ${path} failed (${response.status})`);
	return response.json();
}

// ============================================================================
// Projects
// ============================================================================

export async function getProjects(token: string = '') {
	const response = await fetch(`${PM_API_BASE}/projects`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`获取项目失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.json();
}

export async function createProject(token: string, data: { name: string; description?: string }) {
	const response = await fetch(`${PM_API_BASE}/projects`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to create project');
	return response.json();
}

export async function getProject(token: string, projectId: string) {
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to fetch project');
	return response.json();
}

export async function updateProject(token: string, projectId: string, data: Record<string, unknown>) {
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to update project');
	return response.json();
}

export async function deleteProject(token: string, projectId: string) {
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}`, {
		method: 'DELETE',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to delete project');
	return response.json();
}

// ============================================================================
// Versions
// ============================================================================

export async function getVersions(token: string, projectId: string) {
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}/versions`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to fetch versions');
	return response.json();
}

export async function createVersion(token: string, projectId: string, data: { version_number: string; label?: string; description?: string }) {
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}/versions`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to create version');
	return response.json();
}

// ============================================================================
// Entries
// ============================================================================

export async function getEntries(token: string, projectId: string, moduleType?: string) {
	const query = moduleType ? `?module_type=${moduleType}` : '';
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}/entries${query}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`获取条目失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.json();
}

export async function getEntry(token: string, entryId: string) {
	const response = await fetch(`${PM_API_BASE}/entries/${entryId}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to fetch entry');
	return response.json();
}

export async function createEntry(token: string, projectId: string, data: { module_type: string; title: string; content?: string; data?: Record<string, unknown>; status?: string; priority?: string }) {
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}/entries`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`创建条目失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.json();
}

export async function updateEntry(token: string, entryId: string, data: Record<string, unknown>) {
	const response = await fetch(`${PM_API_BASE}/entries/${entryId}`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`更新条目失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.json();
}

export async function deleteEntry(token: string, entryId: string) {
	const response = await fetch(`${PM_API_BASE}/entries/${entryId}`, {
		method: 'DELETE',
		headers: getHeaders(token)
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`删除条目失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.json();
}

// ============================================================================
// Traceability (Entities & Relations)
// ============================================================================

export async function getEntities(token: string, projectId: string) {
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}/entities`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to fetch entities');
	return response.json();
}

export async function createEntity(token: string, projectId: string, data: Record<string, unknown>) {
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}/entities`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to create entity');
	return response.json();
}

export async function deleteEntity(token: string, entityId: string) {
	const response = await fetch(`${PM_API_BASE}/entities/${entityId}`, {
		method: 'DELETE',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to delete entity');
	return response.json();
}

export async function getRelations(token: string, projectId: string) {
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}/relations`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to fetch relations');
	return response.json();
}

export async function createRelation(token: string, projectId: string, data: Record<string, unknown>) {
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}/relations`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to create relation');
	return response.json();
}

export async function deleteRelation(token: string, relationId: string) {
	const response = await fetch(`${PM_API_BASE}/relations/${relationId}`, {
		method: 'DELETE',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to delete relation');
	return response.json();
}

export async function getImpactAnalysis(token: string, projectId: string, entityId: string) {
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}/traceability/impact?entity_id=${entityId}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to fetch impact analysis');
	return response.json();
}

export async function getTraceChain(token: string, projectId: string, entityId: string, direction: string = 'both', maxDepth: number = 5) {
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}/traceability/chain?entity_id=${entityId}&direction=${direction}&max_depth=${maxDepth}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to fetch trace chain');
	return response.json();
}

// ============================================================================
// Agent Tools
// ============================================================================

export async function agentToolCreateEntry(token: string, data: Record<string, unknown>) {
	const response = await fetch(`${PM_API_BASE}/agent/tools/create_entry`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to create entry via agent');
	return response.json();
}

export async function agentToolUpdateEntry(token: string, data: Record<string, unknown>) {
	const response = await fetch(`${PM_API_BASE}/agent/tools/update_entry`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to update entry via agent');
	return response.json();
}

export async function agentToolCreateRelation(token: string, data: Record<string, unknown>) {
	const response = await fetch(`${PM_API_BASE}/agent/tools/create_relation`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to create relation via agent');
	return response.json();
}

export async function agentToolListEntries(token: string, projectId: string, moduleType?: string) {
	const query = moduleType ? `&module_type=${moduleType}` : '';
	const response = await fetch(`${PM_API_BASE}/agent/tools/list_entries?project_id=${projectId}${query}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to list entries via agent');
	return response.json();
}

export async function agentToolGetEntry(token: string, entryId: string) {
	const response = await fetch(`${PM_API_BASE}/agent/tools/get_entry?entry_id=${entryId}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to get entry via agent');
	return response.json();
}
