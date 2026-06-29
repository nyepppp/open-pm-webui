import { getOne, create, update, remove } from '../index';
import type { ModuleEntry, ApiResponse } from '../types';

const MODULE = 'product-architecture';

export function getProductArchitectureList(projectId: string, page = 1, pageSize = 20, search = '') {
	const params = new URLSearchParams({ page: String(page), pageSize: String(pageSize) });
	if (search) params.append('search', search);
	return getOne<ModuleEntry[]>(`/projects/${projectId}/modules/${MODULE}?${params.toString()}`);
}

export function getProductArchitecture(projectId: string, id: string) {
	return getOne<ModuleEntry>(`/projects/${projectId}/modules/${MODULE}/${id}`);
}

export function createProductArchitecture(projectId: string, data: Partial<ModuleEntry>) {
	return create<ModuleEntry>(`/projects/${projectId}/modules/${MODULE}`, data);
}

export function updateProductArchitecture(projectId: string, id: string, data: Partial<ModuleEntry>) {
	return update<ModuleEntry>(`/projects/${projectId}/modules/${MODULE}/${id}`, data);
}

export function deleteProductArchitecture(projectId: string, id: string) {
	return remove(`/projects/${projectId}/modules/${MODULE}/${id}`);
}
