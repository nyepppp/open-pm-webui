import { getOne, create, update, remove } from '../index';
import type { ModuleEntry, ApiResponse } from '../types';

const MODULE = 'meeting';

export function getMeetingList(projectId: string, page = 1, pageSize = 20, search = '') {
	const params = new URLSearchParams({ page: String(page), pageSize: String(pageSize) });
	if (search) params.append('search', search);
	return getOne<ModuleEntry[]>(`/projects/${projectId}/modules/${MODULE}?${params.toString()}`);
}

export function getMeeting(projectId: string, id: string) {
	return getOne<ModuleEntry>(`/projects/${projectId}/modules/${MODULE}/${id}`);
}

export function createMeeting(projectId: string, data: Partial<ModuleEntry>) {
	return create<ModuleEntry>(`/projects/${projectId}/modules/${MODULE}`, data);
}

export function updateMeeting(projectId: string, id: string, data: Partial<ModuleEntry>) {
	return update<ModuleEntry>(`/projects/${projectId}/modules/${MODULE}/${id}`, data);
}

export function deleteMeeting(projectId: string, id: string) {
	return remove(`/projects/${projectId}/modules/${MODULE}/${id}`);
}
