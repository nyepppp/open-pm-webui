import { getOne, create, update, remove } from '../index';
import type { ModuleEntry, ApiResponse } from '../types';

const MODULE = 'faq';

export function getFAQList(projectId: string, page = 1, pageSize = 20, search = '') {
	const params = new URLSearchParams({ page: String(page), pageSize: String(pageSize) });
	if (search) params.append('search', search);
	return getOne<ModuleEntry[]>(`/projects/${projectId}/modules/${MODULE}?${params.toString()}`);
}

export function getFAQ(projectId: string, id: string) {
	return getOne<ModuleEntry>(`/projects/${projectId}/modules/${MODULE}/${id}`);
}

export function createFAQ(projectId: string, data: Partial<ModuleEntry>) {
	return create<ModuleEntry>(`/projects/${projectId}/modules/${MODULE}`, data);
}

export function updateFAQ(projectId: string, id: string, data: Partial<ModuleEntry>) {
	return update<ModuleEntry>(`/projects/${projectId}/modules/${MODULE}/${id}`, data);
}

export function deleteFAQ(projectId: string, id: string) {
	return remove(`/projects/${projectId}/modules/${MODULE}/${id}`);
}
