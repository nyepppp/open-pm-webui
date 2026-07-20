import { WEBUI_API_BASE_URL } from '$lib/constants';

type PromptItem = {
	id?: string; // Prompt ID
	command: string;
	name: string; // Changed from title
	content: string;
	data?: object | null;
	meta?: object | null;
	access_grants?: object[];
	version_id?: string | null; // Active version
	commit_message?: string | null; // For history tracking
	is_production?: boolean; // Whether to set new version as production
};

type PromptHistoryItem = {
	id: string;
	prompt_id: string;
	parent_id: string | null;
	snapshot: {
		name: string;
		content: string;
		command: string;
		data: object;
		meta: object;
		access_grants: object[];
	};
	user_id: string;
	commit_message: string | null;
	created_at: number;
	user?: {
		id: string;
		name: string;
		email: string;
	};
};

type PromptDiff = {
	from_id: string;
	to_id: string;
	from_snapshot: object;
	to_snapshot: object;
	content_diff: string[];
	name_changed: boolean;
	access_grants_changed: boolean;
};

export const createNewPrompt = async (token: string, prompt: PromptItem) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/prompts/create`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			...prompt,
			command: prompt.command.startsWith('/') ? prompt.command.slice(1) : prompt.command
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getPrompts = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/prompts/`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getPromptTags = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/prompts/tags`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getPromptItems = async (
	token: string = '',
	query: string | null,
	viewOption: string | null,
	selectedTag: string | null,
	orderBy: string | null,
	direction: string | null,
	page: number
) => {
	let error = null;

	const searchParams = new URLSearchParams();
	if (query) {
		searchParams.append('query', query);
	}
	if (viewOption) {
		searchParams.append('view_option', viewOption);
	}
	if (selectedTag) {
		searchParams.append('tag', selectedTag);
	}
	if (orderBy) {
		searchParams.append('order_by', orderBy);
	}
	if (direction) {
		searchParams.append('direction', direction);
	}
	if (page) {
		searchParams.append('page', page.toString());
	}

	const res = await fetch(`${WEBUI_API_BASE_URL}/prompts/list?${searchParams.toString()}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getPromptList = async (token: string = '') => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/prompts/list`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getPromptById = async (token: string, promptId: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/prompts/id/${promptId}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;

			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const updatePromptById = async (token: string, prompt: PromptItem) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/prompts/id/${prompt.id}/update`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(prompt)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;

			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const updatePromptMetadata = async (
	token: string,
	promptId: string,
	name: string,
	command: string,
	tags: string[] = []
) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/prompts/id/${promptId}/update/meta`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ name, command, tags })
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const setProductionPromptVersion = async (
	token: string,
	promptId: string,
	version_id: string
) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/prompts/id/${promptId}/update/version`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify({
			version_id: version_id
		})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.log(err);
			error = err.detail;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const togglePromptById = async (token: string, promptId: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/prompts/id/${promptId}/toggle`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const deletePromptById = async (token: string, promptId: string) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/prompts/id/${promptId}/delete`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.then((json) => {
			return json;
		})
		.catch((err) => {
			error = err.detail;

			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const updatePromptAccessGrants = async (
	token: string,
	promptId: string,
	accessGrants: any[]
) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/prompts/id/${promptId}/access/update`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ access_grants: accessGrants })
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

////////////////////////////
// Prompt History APIs
////////////////////////////

export const getPromptHistory = async (
	token: string,
	promptId: string,
	page: number = 0
): Promise<PromptHistoryItem[]> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/prompts/id/${promptId}/history?page=${page}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const deletePromptHistoryVersion = async (
	token: string,
	promptId: string,
	historyId: string
): Promise<boolean> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/prompts/id/${promptId}/history/${historyId}`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return false;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getPromptHistoryEntry = async (
	token: string,
	promptId: string,
	historyId: string
): Promise<PromptHistoryItem> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/prompts/id/${promptId}/history/${historyId}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getPromptDiff = async (
	token: string,
	promptId: string,
	fromId: string,
	toId: string
): Promise<PromptDiff> => {
	let error = null;

	const res = await fetch(
		`${WEBUI_API_BASE_URL}/prompts/id/${promptId}/history/diff?from_id=${fromId}&to_id=${toId}`,
		{
			method: 'GET',
			headers: {
				Accept: 'application/json',
				'Content-Type': 'application/json',
				authorization: `Bearer ${token}`
			}
		}
	)
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

////////////////////////////
// Part B: 角色提示词（Role Prompts）API
// 复用 prompts 路由，通过 is_role 字段区分
////////////////////////////

/** 角色提示词结构（与后端 RoleForm + Prompt.data 合并对齐） */
export interface RolePrompt {
	id: string;
	command: string;
	name: string;
	content?: string;
	user_id?: string;
	is_role?: boolean;
	created_at?: number;
	updated_at?: number;
	// 角色配置（存于 prompt.data）
	system_prompt?: string;
	tools?: string[];
	suggested_models?: string[];
	description?: string;
	user?: { id: string; name: string; email: string } | null;
}

/** 角色表单（升级/更新时提交给后端） */
export interface RoleForm {
	system_prompt: string;
	tools: string[];
	suggested_models: string[];
	description: string;
}

/** 将后端返回的 prompt（含 data 字段）展开为 RolePrompt */
function normalizeRolePrompt(raw: any): RolePrompt {
	const data = raw?.data || {};
	return {
		id: raw.id,
		command: raw.command,
		name: raw.name,
		content: raw.content,
		user_id: raw.user_id,
		is_role: raw.is_role ?? true,
		created_at: raw.created_at,
		updated_at: raw.updated_at,
		system_prompt: data.system_prompt ?? '',
		tools: Array.isArray(data.tools) ? data.tools : [],
		suggested_models: Array.isArray(data.suggested_models) ? data.suggested_models : [],
		description: data.description ?? raw?.meta?.description ?? '',
		user: raw.user ?? null
	};
}

/** 获取当前用户可见的所有角色提示词 */
export const getRoles = async (token: string = ''): Promise<RolePrompt[]> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/prompts/roles`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return Array.isArray(res) ? res.map(normalizeRolePrompt) : [];
};

/** 将普通 prompt 升级为角色（或更新已存在角色的配置） */
export const upgradeToRole = async (
	token: string,
	promptId: string,
	form: RoleForm
): Promise<RolePrompt> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/prompts/id/${promptId}/role`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify(form)
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return normalizeRolePrompt(res);
};

/** 取消角色标记（is_role=false，保留 data 内容） */
export const removeRole = async (token: string, promptId: string): Promise<RolePrompt> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/prompts/id/${promptId}/role`, {
		method: 'DELETE',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return normalizeRolePrompt(res);
};
