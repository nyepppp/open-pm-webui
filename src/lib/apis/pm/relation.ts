import { getOne, create, remove } from './index';
import type { Relation } from './types';

export function getRelationList(projectId: string, entityId?: string, relationType?: string) {
	const params = new URLSearchParams();
	if (entityId) params.append('entityId', entityId);
	if (relationType) params.append('relationType', relationType);
	return getOne<Relation[]>(`/projects/${projectId}/relations?${params.toString()}`);
}

export function createRelation(projectId: string, data: Partial<Relation>) {
	return create<Relation>(`/projects/${projectId}/relations`, data);
}

export function deleteRelation(projectId: string, id: string) {
	return remove(`/projects/${projectId}/relations/${id}`);
}

export function confirmRelation(projectId: string, id: string) {
	return create<Relation>(`/projects/${projectId}/relations/${id}/confirm`, {});
}

export function getImpactAnalysis(projectId: string, entityId: string) {
	return getOne<{
		upstream: { entityId: string; entityType: string; relationType: string }[];
		downstream: { entityId: string; entityType: string; relationType: string }[];
	}>(`/projects/${projectId}/relations/impact?entityId=${entityId}`);
}

export function getTraceability(projectId: string, entityId: string, direction: 'upstream' | 'downstream' | 'both') {
	return getOne<{
		chain: { entityId: string; entityType: string; relationType: string; depth: number }[];
	}>(`/projects/${projectId}/relations/trace?entityId=${entityId}&direction=${direction}`);
}

export function suggestRelations(projectId: string, entityId: string, targetModuleType: string) {
	return create<{
		suggestions: { entityBId: string; relationType: string; confidence: number; reason: string }[];
	}>(`/projects/${projectId}/relations/suggest`, { entityId, targetModuleType });
}
