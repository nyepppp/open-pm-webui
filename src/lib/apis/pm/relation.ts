import { getOne, create, remove } from './index';
import type { Relation } from './types';

/**
 * PM 关系 / 溯源 API
 *
 * 后端路由（routers/pm.py）：
 * - GET    /projects/{project_id}/relations              列出项目所有关系
 * - POST   /projects/{project_id}/relations              创建关系
 * - DELETE /relations/{relation_id}                      删除关系（注意：无 project 前缀）
 * - POST   /relations/{relation_id}/confirm              确认关系（confirmed=1）
 * - POST   /projects/{project_id}/relations/suggest      建议候选关系
 * - GET    /projects/{project_id}/traceability/impact?entity_id=...     影响分析
 * - GET    /projects/{project_id}/traceability/chain?entity_id=...&direction=...   溯源链
 *
 * 注意：traceability 系列用 snake_case 查询参数（entity_id），与后端 FastAPI 一致。
 */

export function getRelationList(projectId: string, entityId?: string, relationType?: string) {
	// 后端 /projects/{id}/relations 不接受 query 参数（返回全量），前端按 entityId/relationType 过滤
	// 注意：后端 PMRelationModel 返回 snake_case（entity_a_id / entity_b_id / relation_type），
	// getOne 不做 case 转换，因此 filter 必须用 snake_case 字段名。
	return getOne<Relation[]>(`/projects/${projectId}/relations`).then(list => {
		if (!Array.isArray(list)) return [] as Relation[];
		return list.filter((r: any) => {
			if (entityId && r.entity_a_id !== entityId && r.entity_b_id !== entityId) return false;
			if (relationType && r.relation_type !== relationType) return false;
			return true;
		});
	});
}

export function createRelation(projectId: string, data: Partial<Relation>) {
	// 后端 create_relation 路由读 snake_case 字段（entity_a_id / entity_b_id / relation_type / version_id），
	// 前端调用方可能传 camelCase（PMTraceabilityGraph）或 snake_case（architectureStore），
	// 这里统一转成 snake_case 再发请求。忽略 versionSnapshot（后端不识别，Phase 6.5 处理快照）。
	const payload: Record<string, unknown> = {
		entity_a_id: (data as any).entityAId ?? (data as any).entity_a_id ?? '',
		entity_b_id: (data as any).entityBId ?? (data as any).entity_b_id ?? '',
		relation_type: (data as any).relationType ?? (data as any).relation_type ?? 'references',
		confidence: (data as any).confidence ?? 100,
		confirmed: (data as any).confirmed ?? 1,
		created_by: (data as any).createdBy ?? (data as any).created_by,
		version_id: (data as any).versionId ?? (data as any).version_id,
	};
	return create<Relation>(`/projects/${projectId}/relations`, payload);
}

export function deleteRelation(projectId: string, id: string) {
	// projectId 保留参数以兼容现有调用方签名，但后端路由是 /relations/{id}（无 project 前缀）
	return remove(`/relations/${id}`);
}

export function confirmRelation(projectId: string, id: string) {
	return create<Relation>(`/relations/${id}/confirm`, {});
}

export function getImpactAnalysis(projectId: string, entityId: string) {
	return getOne<{
		entity_id: string;
		upstream: { entity: any; relation_type: string; confidence: number }[];
		downstream: { entity: any; relation_type: string; confidence: number }[];
		total_affected: number;
	}>(`/projects/${projectId}/traceability/impact?entity_id=${entityId}`);
}

export function getTraceability(projectId: string, entityId: string, direction: 'upstream' | 'downstream' | 'both') {
	return getOne<{
		start_entity_id: string;
		direction: string;
		max_depth: number;
		chain: { entity: any; depth: number; path: any[] }[];
	}>(`/projects/${projectId}/traceability/chain?entity_id=${entityId}&direction=${direction}`);
}

export function suggestRelations(projectId: string, entityId: string, targetModuleType: string) {
	return create<{
		suggestions: { entityBId: string; entityType: string; name: string }[];
	}>(`/projects/${projectId}/relations/suggest`, { entityId, targetModuleType });
}
