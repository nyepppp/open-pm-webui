import { getOne, create, update, remove } from '../index';
import type { ModuleEntry, ApiResponse } from '../types';

const MODULE = 'requirement';

export function getRequirementList(projectId: string, page = 1, pageSize = 20, search = '') {
	const params = new URLSearchParams({ page: String(page), pageSize: String(pageSize) });
	if (search) params.append('search', search);
	return getOne<ModuleEntry[]>(`/projects/${projectId}/modules/${MODULE}?${params.toString()}`);
}

export function getRequirement(projectId: string, id: string) {
	return getOne<ModuleEntry>(`/projects/${projectId}/modules/${MODULE}/${id}`);
}

export function createRequirement(projectId: string, data: Partial<ModuleEntry>) {
	return create<ModuleEntry>(`/projects/${projectId}/modules/${MODULE}`, data);
}

export function updateRequirement(projectId: string, id: string, data: Partial<ModuleEntry>) {
	return update<ModuleEntry>(`/projects/${projectId}/modules/${MODULE}/${id}`, data);
}

export function deleteRequirement(projectId: string, id: string) {
	return remove(`/projects/${projectId}/modules/${MODULE}/${id}`);
}
