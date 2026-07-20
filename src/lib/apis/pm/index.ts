import { WEBUI_API_BASE_URL } from '$lib/constants';

const PM_API_BASE = `${WEBUI_API_BASE_URL}/pm`;

function getHeaders(token: string = '') {
	return {
		Accept: 'application/json',
		'Content-Type': 'application/json',
		...(token && { authorization: `Bearer ${token}` })
	};
}

/**
 * 包装 fetch，统一处理网络层错误。
 * 浏览器 fetch 抛 TypeError("Failed to fetch") 是网络层错误：
 * 后端未启动 / 端口不对 / CORS 预检失败 / 网络中断 / URL 过长。
 * 翻译为友好中文错误，避免用户看到原始英文 "Failed to fetch"。
 *
 * D7: 增加诊断日志，便于区分根因（CORS / 虚拟 ID / 网络 / URL 过长）。
 */
async function pmFetch(input: string, init?: RequestInit): Promise<Response> {
	try {
		const response = await fetch(input, init);
		// 成功路径日志（debug 级别，便于排查 404/500 但不刷屏）
		console.log('[pmFetch]', init?.method || 'GET', input, '→', response.status);
		return response;
	} catch (e: any) {
		// 网络层错误日志：打印 URL、方法、错误类型、body 大小
		console.error('[pmFetch] network error:', {
			url: input,
			method: init?.method || 'GET',
			errorType: e?.constructor?.name,
			message: e?.message,
			bodyLength: init?.body ? String(init.body).length : 0,
		});
		if (e instanceof TypeError) {
			const msg = e.message || '';
			// D41: 细化网络错误识别，区分 CORS / 网络 / 其他 TypeError
			if (/fetch/i.test(msg) || /network/i.test(msg)) {
				throw new Error('无法连接到后端服务，请检查后端是否启动（默认端口 8080）');
			}
			if (/cors/i.test(msg)) {
				throw new Error('CORS 跨域被拦截，请联系管理员检查后端 CORS 配置');
			}
			// 其他 TypeError 原样抛出（保留原始堆栈）
			throw e;
		}
		throw e;
	}
}

/**
 * D71/K1a: PM API 结构化错误类。
 * 让上层 catch 能按 HTTP 状态码分支（4xx vs 5xx vs 网络），并直接拿到后端 `detail` 字段，
 * 不再依赖字符串正则匹配。
 *
 * 使用：`if (err instanceof PMApiError) { ... err.status / err.detail / err.url }`
 */
export class PMApiError extends Error {
	status: number;
	detail: string;
	url: string;
	constructor(status: number, detail: string, url: string) {
		super(`PM API ${status} on ${url}${detail ? ': ' + detail : ''}`);
		this.name = 'PMApiError';
		this.status = status;
		this.detail = detail;
		this.url = url;
	}
}

/**
 * D71/K1a: 统一从 Response 提取 detail 字段并抛 PMApiError。
 * 内部 helper，供 create/createVersion 等复用。
 */
async function throwPMApiError(response: Response, url: string, method: string): Promise<never> {
	let detail = '';
	try {
		const body = await response.json();
		if (typeof body?.detail === 'string') {
			detail = body.detail;
		} else if (body?.detail) {
			detail = JSON.stringify(body.detail);
		} else if (typeof body?.message === 'string') {
			detail = body.message;
		} else {
			detail = JSON.stringify(body ?? {});
		}
	} catch {
		detail = response.statusText || '';
	}
	throw new PMApiError(response.status, detail, url);
}

export async function getOne<T = unknown>(path: string): Promise<T> {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const response = await pmFetch(`${PM_API_BASE}${path}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`GET ${path} failed (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.json();
}

export async function create<T = unknown>(path: string, data: unknown): Promise<T> {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const url = `${PM_API_BASE}${path}`;
	const response = await pmFetch(url, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) {
		// D71/K1a: 抛结构化 PMApiError，让上层能按 HTTP 状态码分支
		await throwPMApiError(response, url, 'POST');
	}
	return response.json();
}

export async function update<T = unknown>(path: string, data: unknown): Promise<T> {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const response = await pmFetch(`${PM_API_BASE}${path}`, {
		method: 'PUT',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`PUT ${path} failed (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.json();
}

export async function remove<T = unknown>(path: string): Promise<T> {
	const token = (typeof localStorage !== 'undefined' && localStorage.token) || '';
	const response = await pmFetch(`${PM_API_BASE}${path}`, {
		method: 'DELETE',
		headers: getHeaders(token)
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`DELETE ${path} failed (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.json();
}

// ============================================================================
// Projects
// ============================================================================

export async function getProjects(token: string = '') {
	const response = await pmFetch(`${PM_API_BASE}/projects`, {
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
	const response = await pmFetch(`${PM_API_BASE}/projects`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		// Include status code + backend detail so callers can branch on 409 etc.
		const err = new Error(`创建项目失败 (${response.status})${detail ? ': ' + detail : ''}`);
		(err as any).status = response.status;
		(err as any).detail = detail;
		throw err;
	}
	return response.json();
}

export async function getProject(token: string, projectId: string) {
	const response = await pmFetch(`${PM_API_BASE}/projects/${projectId}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to fetch project');
	return response.json();
}

export async function updateProject(token: string, projectId: string, data: Record<string, unknown>) {
	const response = await pmFetch(`${PM_API_BASE}/projects/${projectId}`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		const err = new Error(`更新项目失败 (${response.status})${detail ? ': ' + detail : ''}`);
		(err as any).status = response.status;
		(err as any).detail = detail;
		throw err;
	}
	return response.json();
}

export async function deleteProject(token: string, projectId: string) {
	const response = await pmFetch(`${PM_API_BASE}/projects/${projectId}`, {
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
	const response = await pmFetch(`${PM_API_BASE}/projects/${projectId}/versions`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to fetch versions');
	return response.json();
}

export async function createVersion(token: string, projectId: string, data: { version_number: string; label?: string; description?: string }) {
	const url = `${PM_API_BASE}/projects/${projectId}/versions`;
	const response = await pmFetch(url, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) {
		// D71/K1b: 抛结构化 PMApiError —— Bug 2 D40 兜底创建 v1 失败时能拿到 HTTP 状态码
		await throwPMApiError(response, url, 'POST');
	}
	return response.json();
}

// ============================================================================
// Entries
// ============================================================================

export async function getEntries(token: string, projectId: string, moduleType?: string, versionId?: string) {
	const params = new URLSearchParams();
	if (moduleType) params.append('module_type', moduleType);
	if (versionId) params.append('version_id', versionId);
	const query = params.toString() ? `?${params.toString()}` : '';
	const response = await pmFetch(`${PM_API_BASE}/projects/${projectId}/entries${query}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`获取条目失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	const data = await response.json();
	// Handle both formats: { entries: [...] } and direct array [...]
	return Array.isArray(data) ? data : (data.entries || []);
}

export async function getEntry(token: string, entryId: string) {
	const response = await pmFetch(`${PM_API_BASE}/entries/${entryId}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to fetch entry');
	return response.json();
}

export async function createEntry(token: string, projectId: string, data: { module_type: string; title: string; content?: string; data?: Record<string, unknown>; status?: string; priority?: string; module_version_id?: string }) {
	const response = await pmFetch(`${PM_API_BASE}/projects/${projectId}/entries`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`创建条目失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	const result = await response.json();
	// 加固契约：响应体必须含 id 字段，否则前端无法回填虚拟 ID，不能向 store 插入虚拟行
	if (!result || typeof result.id !== 'string' || !result.id) {
		throw new Error('服务端返回异常，未返回条目 ID');
	}
	return result;
}

export async function updateEntry(token: string, entryId: string, data: Record<string, unknown>) {
	const response = await pmFetch(`${PM_API_BASE}/entries/${entryId}`, {
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
	const response = await pmFetch(`${PM_API_BASE}/entries/${entryId}`, {
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
// Entry Version（条目级修订历史，自动创建）
// 注意：与 PMVersion（项目版本）/ PMModuleVersion（模块版本）是三个独立的概念。
// ============================================================================

export interface EntryVersion {
	id: string;
	entry_id: string;
	version_number: string;
	content?: string;
	entry_metadata?: unknown;
	created_by?: string;
	created_at?: number;
}

/** 获取条目的修订版本列表（按 created_at 降序） */
export async function getEntryVersions(
	token: string,
	projectId: string,
	entryId: string
): Promise<EntryVersion[]> {
	const response = await pmFetch(
		`${PM_API_BASE}/projects/${projectId}/entries/${entryId}/versions`,
		{
			method: 'GET',
			headers: getHeaders(token)
		}
	);
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`获取条目版本列表失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.json();
}

/** 切换条目版本：把 entry 的 content/data 回滚到指定版本快照 */
export async function switchEntryVersion(
	token: string,
	projectId: string,
	entryId: string,
	versionId: string
): Promise<{ entry_id: string; current_version_id: string }> {
	const response = await pmFetch(
		`${PM_API_BASE}/projects/${projectId}/entries/${entryId}/versions/${versionId}/switch`,
		{
			method: 'POST',
			headers: getHeaders(token)
		}
	);
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`切换条目版本失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.json();
}

// ============================================================================
// Batch Import / Export
// ============================================================================

export async function importEntries(
	token: string,
	projectId: string,
	data: {
		module_type: string;
		format: 'json' | 'csv';
		data: unknown[] | string;
		create_versions?: boolean;
	}
) {
	const response = await pmFetch(`${PM_API_BASE}/projects/${projectId}/entries/import`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`导入失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.json();
}

export async function exportEntry(token: string, entryId: string, format: 'json' | 'markdown' | 'csv' = 'json'): Promise<Blob> {
	// 后端端点 /entries/{entry_id}/export 期望 query 参数名为 export_format（非 format）
	const response = await pmFetch(`${PM_API_BASE}/entries/${entryId}/export?export_format=${format}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`导出失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.blob();
}

/**
 * 按模块批量导出（调用后端 POST /pm/projects/{id}/modules/{type}/export 端点）
 * 直接返回文件流 Blob，前端用 URL.createObjectURL + a.click() 触发下载。
 * 与 PMImportExport.svelte 的客户端 flattenEntry 互为兜底。
 *
 * 改用 POST + body 传输参数：避免条目 ID 列表过长触发浏览器 URL 长度限制（8K-32K）导致
 * "Failed to fetch"。GET 端点保留为向后兼容（无 entry_ids 时仍可用）。
 *
 * format 扩展：支持 'markdown' / 'docx'（富文本模块）/ 'xlsx' / 'csv' / 'json'（表格模块）。
 * columns 仅对表格模块生效，JSON 字符串形如 [{"key":"title","label":"标题"}]。
 * entryIds 可选，仅导出指定 ID 的条目；为 undefined 时导出全部。
 */
export async function exportModule(
	token: string,
	projectId: string,
	moduleType: string,
	format: 'xlsx' | 'csv' | 'json' | 'markdown' | 'docx' = 'xlsx',
	versionId?: string,
	columns?: Array<{ key: string; label: string }>,
	entryIds?: string[]
): Promise<Blob> {
	const url = `${PM_API_BASE}/projects/${projectId}/modules/${moduleType}/export`;
	const body: Record<string, unknown> = { format };
	if (versionId) body.version_id = versionId;
	if (columns && columns.length > 0) body.columns = columns;
	if (entryIds && entryIds.length > 0) body.entry_ids = entryIds;

	const response = await pmFetch(url, {
		method: 'POST',
		headers: {
			Accept: 'application/octet-stream',
			'Content-Type': 'application/json',
			...(token && { authorization: `Bearer ${token}` })
		},
		body: JSON.stringify(body)
	});
	if (!response.ok) {
		let detail = '';
		try { const errBody = await response.json(); detail = errBody.detail || errBody.message || ''; } catch {}
		throw new Error(`导出失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.blob();
}

// ============================================================================
// Module Version（模块版本管理）
// 注意：与 PMVersion（项目版本）/ PMEntryVersion（条目修订）是三个独立的概念。
// - PMVersion：项目级版本，由 versionStore + PMVersionSelector 管理
// - PMEntryVersion：单个 entry 的修订历史，自动创建
// - PMModuleVersion：模块级版本，管理一个模块下所有 feature/parameter 的版本集合
// ============================================================================

export interface ModuleVersion {
	id: string;
	module_entry_id: string;
	version_number: string;
	change_summary: string;
	created_by: string;
	created_at: number;
	project_id?: string;
	project_version_id?: string;
}

/** 创建模块版本 */
export async function createModuleVersion(
	token: string,
	projectId: string,
	moduleEntryId: string,
	form: { version_number: string; change_summary: string; project_version_id?: string }
): Promise<ModuleVersion> {
	const response = await pmFetch(
		`${PM_API_BASE}/projects/${projectId}/modules/${moduleEntryId}/versions`,
		{
			method: 'POST',
			headers: getHeaders(token),
			body: JSON.stringify({
				...form,
				module_entry_id: moduleEntryId,
				project_id: projectId
			})
		}
	);
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`创建模块版本失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.json();
}

/** 列出模块的所有版本（按 created_at 降序） */
export async function listModuleVersions(
	token: string,
	projectId: string,
	moduleEntryId: string
): Promise<ModuleVersion[]> {
	const response = await pmFetch(
		`${PM_API_BASE}/projects/${projectId}/modules/${moduleEntryId}/versions`,
		{
			method: 'GET',
			headers: getHeaders(token)
		}
	);
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`获取模块版本列表失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.json();
}

/** 切换模块版本：把该模块下所有 entry 的 module_version_id 更新为 version_id */
export async function switchModuleVersion(
	token: string,
	projectId: string,
	moduleEntryId: string,
	versionId: string
): Promise<{ version_id: string; updated_entry_ids: string[]; count: number }> {
	const response = await pmFetch(
		`${PM_API_BASE}/projects/${projectId}/modules/${moduleEntryId}/versions/${versionId}/switch`,
		{
			method: 'POST',
			headers: getHeaders(token)
		}
	);
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`切换模块版本失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.json();
}

/** 删除模块版本 */
export async function deleteModuleVersion(
	token: string,
	projectId: string,
	moduleEntryId: string,
	versionId: string
): Promise<boolean> {
	const response = await pmFetch(
		`${PM_API_BASE}/projects/${projectId}/modules/${moduleEntryId}/versions/${versionId}`,
		{
			method: 'DELETE',
			headers: getHeaders(token)
		}
	);
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`删除模块版本失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.json();
}

/** 获取模块版本跨度：该模块下 feature/parameter 出现过的不同 module_version_id 数量 */
export async function getModuleVersionSpan(
	token: string,
	projectId: string,
	moduleEntryId: string
): Promise<{ featureSpan: number; parameterSpan: number }> {
	const response = await pmFetch(
		`${PM_API_BASE}/projects/${projectId}/modules/${moduleEntryId}/versions/span`,
		{
			method: 'GET',
			headers: getHeaders(token)
		}
	);
	if (!response.ok) {
		let detail = '';
		try { const body = await response.json(); detail = body.detail || body.message || ''; } catch {}
		throw new Error(`获取版本跨度失败 (${response.status})${detail ? ': ' + detail : ''}`);
	}
	return response.json();
}

// ============================================================================
// Traceability (Entities & Relations)
// ============================================================================

export async function getEntities(token: string, projectId: string) {
	const response = await pmFetch(`${PM_API_BASE}/projects/${projectId}/entities`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to fetch entities');
	return response.json();
}

export async function createEntity(token: string, projectId: string, data: Record<string, unknown>) {
	const response = await pmFetch(`${PM_API_BASE}/projects/${projectId}/entities`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to create entity');
	return response.json();
}

export async function deleteEntity(token: string, entityId: string) {
	const response = await pmFetch(`${PM_API_BASE}/entities/${entityId}`, {
		method: 'DELETE',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to delete entity');
	return response.json();
}

export async function getRelations(token: string, projectId: string) {
	const response = await pmFetch(`${PM_API_BASE}/projects/${projectId}/relations`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to fetch relations');
	return response.json();
}

export async function createRelation(token: string, projectId: string, data: Record<string, unknown>) {
	const response = await pmFetch(`${PM_API_BASE}/projects/${projectId}/relations`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to create relation');
	return response.json();
}

export async function deleteRelation(token: string, relationId: string) {
	const response = await pmFetch(`${PM_API_BASE}/relations/${relationId}`, {
		method: 'DELETE',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to delete relation');
	return response.json();
}

export async function getImpactAnalysis(token: string, projectId: string, entityId: string) {
	const response = await pmFetch(`${PM_API_BASE}/projects/${projectId}/traceability/impact?entity_id=${entityId}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to fetch impact analysis');
	return response.json();
}

export async function getTraceChain(token: string, projectId: string, entityId: string, direction: string = 'both', maxDepth: number = 5) {
	const response = await pmFetch(`${PM_API_BASE}/projects/${projectId}/traceability/chain?entity_id=${entityId}&direction=${direction}&max_depth=${maxDepth}`, {
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
	const response = await pmFetch(`${PM_API_BASE}/agent/tools/create_entry`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to create entry via agent');
	return response.json();
}

export async function agentToolUpdateEntry(token: string, data: Record<string, unknown>) {
	const response = await pmFetch(`${PM_API_BASE}/agent/tools/update_entry`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to update entry via agent');
	return response.json();
}

export async function agentToolCreateRelation(token: string, data: Record<string, unknown>) {
	const response = await pmFetch(`${PM_API_BASE}/agent/tools/create_relation`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to create relation via agent');
	return response.json();
}

export async function agentToolListEntries(token: string, projectId: string, moduleType?: string) {
	const query = moduleType ? `&module_type=${moduleType}` : '';
	const response = await pmFetch(`${PM_API_BASE}/agent/tools/list_entries?project_id=${projectId}${query}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to list entries via agent');
	return response.json();
}

export async function agentToolGetEntry(token: string, entryId: string) {
	const response = await pmFetch(`${PM_API_BASE}/agent/tools/get_entry?entry_id=${entryId}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to get entry via agent');
	return response.json();
}

// ============================================================================
// Flow Engine
// ============================================================================

export interface FlowTemplate {
	id: string;
	name: string;
	description: string;
	input_module: string;
	output_module: string;
	step_count: number;
	source: 'builtin' | 'custom';
	entry_id?: string;
}

export interface FlowPreview {
	template_id: string;
	template_name: string;
	source_entries: { id: string; title: string; module_type: string }[];
	steps: { action: string; description: string; status: string }[];
	estimated_outputs: { type: string; estimated_count: string | number; description: string }[];
}

export interface FlowExecuteResult {
	template_id: string;
	template_name: string;
	source_entry_ids: string[];
	status: string;
	created_entries: unknown[];
	created_relations: unknown[];
	step_results: { action: string; status: string; entry_id?: string }[];
	error?: string;
}

export async function getFlowTemplates(token: string, projectId?: string) {
	const query = projectId ? `?project_id=${projectId}` : '';
	const response = await pmFetch(`${PM_API_BASE}/flow/templates${query}`, {
		method: 'GET',
		headers: getHeaders(token)
	});
	if (!response.ok) throw new Error('Failed to fetch flow templates');
	return response.json() as Promise<{ total: number; templates: FlowTemplate[] }>;
}

export async function previewFlow(token: string, data: { template_id: string; project_id: string; source_entry_ids: string[] }) {
	const response = await pmFetch(`${PM_API_BASE}/flow/preview`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to preview flow');
	return response.json() as Promise<FlowPreview>;
}

export async function executeFlow(token: string, data: { template_id: string; project_id: string; source_entry_ids: string[]; confirmed: boolean }) {
	const response = await pmFetch(`${PM_API_BASE}/flow/execute`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to execute flow');
	return response.json() as Promise<FlowExecuteResult>;
}

// ============================================================================
// Architecture Auto-Extract & Sync
// ============================================================================

export interface ArchitectureNode {
	id: string;
	projectId: string;
	parentId: string | null;
	label: string;
	type: 'root' | 'branch' | 'leaf';
	position: { x: number; y: number };
	metadata: Record<string, unknown>;
	moduleRef?: string;
	createdAt: number;
	updatedAt: number;
}

export interface ArchitectureExtractResult {
	entry_id: string;
	nodes: ArchitectureNode[];
	auto_extracted: boolean;
}

export interface ArchitectureSyncDiff {
	added: ArchitectureNode[];
	removed: ArchitectureNode[];
	modified: ArchitectureNode[];
}

export interface ArchitectureSyncResult {
	entry_id: string;
	nodes: ArchitectureNode[];
	diff: ArchitectureSyncDiff;
	applied: boolean;
}

export async function autoExtractArchitecture(token: string, projectId: string, versionId?: string) {
	const data: Record<string, unknown> = {};
	if (versionId) data.version_id = versionId;
	const response = await pmFetch(`${PM_API_BASE}/projects/${projectId}/architecture/auto-extract`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to auto-extract architecture');
	return response.json() as Promise<ArchitectureExtractResult>;
}

export async function syncArchitecture(token: string, projectId: string, data: { apply?: boolean; version_id?: string }) {
	const response = await pmFetch(`${PM_API_BASE}/projects/${projectId}/architecture/sync`, {
		method: 'POST',
		headers: getHeaders(token),
		body: JSON.stringify(data)
	});
	if (!response.ok) throw new Error('Failed to sync architecture');
	return response.json() as Promise<ArchitectureSyncResult>;
}
