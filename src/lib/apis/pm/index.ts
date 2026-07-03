import { WEBUI_API_BASE_URL } from '$lib/constants';

const PM_API_BASE = `${WEBUI_API_BASE_URL}/api/v1/pm`;

function getHeaders(token: string = '') {
	return {
		Accept: 'application/json',
		'Content-Type': 'application/json',
		...(token && { authorization: `Bearer ${token}` })
	};
}

function toSnakeCase(data: Record<string, unknown>): Record<string, unknown> {
	const result: Record<string, unknown> = {};
	for (const [key, value] of Object.entries(data)) {
		const snakeKey = key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
		result[snakeKey] = value;
	}
	return result;
}

function toCamelCase<T = Record<string, unknown>>(data: Record<string, unknown>): T {
	const result: Record<string, unknown> = {};
	for (const [key, value] of Object.entries(data)) {
		const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
		result[camelKey] = value;
	}
	return result as T;
}

export async function getOne<T>(path: string, token: string = ''): Promise<T> {
	const response = await fetch(`${PM_API_BASE}${path}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error(`Failed to fetch ${path}`);
	const data = await response.json();
	if (Array.isArray(data)) {
		return data.map((item) => toCamelCase(item)) as T;
	}
	return toCamelCase(data) as T;
}

export async function create<T>(path: string, data: Record<string, unknown>, token: string = ''): Promise<T> {
	const response = await fetch(`${PM_API_BASE}${path}`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(toSnakeCase(data))
	});
	if (!response.ok) throw new Error(`Failed to create ${path}`);
	return toCamelCase(await response.json()) as T;
}

export async function update<T>(path: string, data: Record<string, unknown>, token: string = ''): Promise<T> {
	const response = await fetch(`${PM_API_BASE}${path}`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(toSnakeCase(data))
	});
	if (!response.ok) throw new Error(`Failed to update ${path}`);
	return toCamelCase(await response.json()) as T;
}

export async function remove(path: string, token: string = ''): Promise<boolean> {
	const response = await fetch(`${PM_API_BASE}${path}`, {
		method: 'DELETE',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error(`Failed to delete ${path}`);
	return true;
}

// ============================================================================
// Projects
// ============================================================================

export async function getProjects(token: string = '') {
	const response = await fetch(`${PM_API_BASE}/projects`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to fetch projects');
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
	if (!response.ok) throw new Error('Failed to fetch entries');
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

export async function createEntry(token: string, projectId: string, data: { module_type: string; title: string; content?: string; data?: Record<string, unknown>; status?: string; priority?: string; version_id?: string }) {
	const response = await fetch(`${PM_API_BASE}/projects/${projectId}/entries`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to create entry');
	return response.json();
}

export async function updateEntry(token: string, entryId: string, data: Record<string, unknown>) {
	const response = await fetch(`${PM_API_BASE}/entries/${entryId}`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to update entry');
	return response.json();
}

export async function deleteEntry(token: string, entryId: string) {
	const response = await fetch(`${PM_API_BASE}/entries/${entryId}`, {
		method: 'DELETE',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to delete entry');
	return response.json();
}
