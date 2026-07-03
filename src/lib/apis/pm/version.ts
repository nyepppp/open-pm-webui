import { getOne, create, update, remove } from './index';
import type { Version, ApiResponse } from './types';

export function getVersionList(projectId: string) {
	return getOne<Version[]>(`/projects/${projectId}/versions`);
}

export function getVersion(projectId: string, id: string) {
	return getOne<Version>(`/projects/${projectId}/versions/${id}`);
}

export function createVersion(projectId: string, data: Partial<Version>) {
	return create<Version>(`/projects/${projectId}/versions`, data);
}

export function switchVersion(projectId: string, id: string) {
	return create<{ currentVersionId: string; switchedAt: number }>(
		`/projects/${projectId}/versions/${id}/switch`,
		{}
	);
}

export function compareVersions(projectId: string, versionA: string, versionB: string, moduleType?: string) {
	const params = new URLSearchParams({ versionA, versionB });
	if (moduleType) params.append('moduleType', moduleType);
	return getOne<{
		diff: {
			added: unknown[];
			modified: { entityId: string; entityType: string; changes: { field: string; old: unknown; new: unknown }[] }[];
			deleted: unknown[];
		}
	}>(`/projects/${projectId}/versions/compare?${params.toString()}`);
}

export function rollbackVersion(projectId: string, id: string, scope: 'project' | 'module', moduleType?: string) {
	return create<{ currentVersionId: string }>(
		`/projects/${projectId}/versions/${id}/rollback`,
		{ scope, ...(moduleType && { moduleType }) }
	);
}
