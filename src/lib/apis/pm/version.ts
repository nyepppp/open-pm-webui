import { getOne, create, update, remove } from './index';
import type { Version, EntryVersion, VersionBranch, VersionMerge, ApiResponse } from './types';

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

// Entry-level version APIs

export function getEntryVersions(projectId: string, entryId: string) {
	return getOne<EntryVersion[]>(`/projects/${projectId}/entries/${entryId}/versions`);
}

export function getEntryVersion(projectId: string, entryId: string, versionId: string) {
	return getOne<EntryVersion>(`/projects/${projectId}/entries/${entryId}/versions/${versionId}`);
}

export function createEntryVersion(projectId: string, entryId: string, data: { changeSummary?: string; branchName?: string; projectVersionId?: string }) {
	return create<EntryVersion>(`/projects/${projectId}/entries/${entryId}/versions`, data);
}

export function switchEntryVersion(projectId: string, entryId: string, versionId: string) {
	return create<{ entryId: string; currentVersionId: string }>(
		`/projects/${projectId}/entries/${entryId}/versions/${versionId}/switch`,
		{}
	);
}

export function compareEntryVersions(projectId: string, entryId: string, versionA: string, versionB: string) {
	return getOne<{
		contentDiff: { path: string; type: 'added' | 'removed' | 'modified'; old: unknown; new: unknown }[];
		metadataDiff: { field: string; old: unknown; new: unknown }[];
	}>(`/projects/${projectId}/entries/${entryId}/versions/compare?versionA=${versionA}&versionB=${versionB}`);
}

// Branch APIs

export function getBranches(projectId: string, entryId: string) {
	return getOne<VersionBranch[]>(`/projects/${projectId}/entries/${entryId}/branches`);
}

export function createBranch(projectId: string, entryId: string, data: { name: string; sourceVersionId?: string }) {
	return create<VersionBranch>(`/projects/${projectId}/entries/${entryId}/branches`, data);
}

export function switchBranch(projectId: string, entryId: string, branchId: string) {
	return create<{ entryId: string; currentBranchId: string }>(
		`/projects/${projectId}/entries/${entryId}/branches/${branchId}/switch`,
		{}
	);
}

// Merge APIs

export function createMerge(projectId: string, entryId: string, data: { branchId: string; targetVersionId?: string }) {
	return create<VersionMerge>(`/projects/${projectId}/entries/${entryId}/merges`, data);
}

export function resolveMergeConflict(projectId: string, entryId: string, mergeId: string, data: { conflictIndex: number; resolution: 'source' | 'target' | 'manual'; resolvedValue?: unknown }) {
	return create<VersionMerge>(
		`/projects/${projectId}/entries/${entryId}/merges/${mergeId}/resolve`,
		data
	);
}

export function completeMerge(projectId: string, entryId: string, mergeId: string) {
	return create<{ mergedVersionId: string }>(
		`/projects/${projectId}/entries/${entryId}/merges/${mergeId}/complete`,
		{}
	);
}
