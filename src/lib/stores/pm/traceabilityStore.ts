/**
 * traceabilityStore —— 溯源链路/影响分析缓存层。
 *
 * 职责：
 * - 缓存 getTraceability / getImpactAnalysis 结果（按 projectId + entityId 维度）
 * - TTL 5 分钟，超时自动失效
 * - createRelation / deleteRelation 后主动 invalidate
 *
 * 用法：
 *   import { loadTraceChain, invalidateProject } from '$lib/stores/pm/traceabilityStore';
 *   await loadTraceChain(projectId, entityId, 'both');
 *   // 关系变更后：
 *   invalidateProject(projectId);
 */

import { writable } from 'svelte/store';
import { getTraceability, getImpactAnalysis } from '$lib/apis/pm/relation';

interface TraceCacheEntry {
	chain: any[];
	timestamp: number;
}
interface ImpactCacheEntry {
	upstream: any[];
	downstream: any[];
	totalAffected: number;
	timestamp: number;
}

const TTL_MS = 5 * 60 * 1000;

// projectId → cacheKey → 缓存
const traceCache = new Map<string, Map<string, TraceCacheEntry>>();
const impactCache = new Map<string, Map<string, ImpactCacheEntry>>();

export const traceChain = writable<any[]>([]);
export const impact = writable<{ upstream: any[]; downstream: any[]; totalAffected: number }>({
	upstream: [], downstream: [], totalAffected: 0
});
export const isTraceLoading = writable(false);
export const isImpactLoading = writable(false);

export async function loadTraceChain(
	projectId: string,
	entityId: string,
	direction: 'upstream' | 'downstream' | 'both' = 'both',
	force = false
): Promise<void> {
	isTraceLoading.set(true);
	try {
		// 缓存 key 需包含 direction，避免不同方向串
		const cacheKey = `${entityId}:${direction}`;
		let projCache = traceCache.get(projectId);
		if (!projCache) {
			projCache = new Map();
			traceCache.set(projectId, projCache);
		}
		const cached = projCache.get(cacheKey);
		if (!force && cached && Date.now() - cached.timestamp < TTL_MS) {
			traceChain.set(cached.chain);
			return;
		}
		const res = await getTraceability(projectId, entityId, direction);
		const chain = res?.chain || [];
		projCache.set(cacheKey, { chain, timestamp: Date.now() });
		traceChain.set(chain);
	} finally {
		isTraceLoading.set(false);
	}
}

export async function loadImpact(projectId: string, entityId: string, force = false): Promise<void> {
	isImpactLoading.set(true);
	try {
		let projCache = impactCache.get(projectId);
		if (!projCache) {
			projCache = new Map();
			impactCache.set(projectId, projCache);
		}
		const cached = projCache.get(entityId);
		if (!force && cached && Date.now() - cached.timestamp < TTL_MS) {
			impact.set({ upstream: cached.upstream, downstream: cached.downstream, totalAffected: cached.totalAffected });
			return;
		}
		const res: any = await getImpactAnalysis(projectId, entityId);
		const upstream = res?.upstream || [];
		const downstream = res?.downstream || [];
		const totalAffected = res?.total_affected ?? (upstream.length + downstream.length);
		projCache.set(entityId, { upstream, downstream, totalAffected, timestamp: Date.now() });
		impact.set({ upstream, downstream, totalAffected });
	} finally {
		isImpactLoading.set(false);
	}
}

export function invalidateProject(projectId: string): void {
	traceCache.delete(projectId);
	impactCache.delete(projectId);
}

export function pruneExpired(): void {
	const t = Date.now();
	for (const [, projCache] of traceCache) {
		for (const [key, entry] of projCache) {
			if (t - entry.timestamp >= TTL_MS) projCache.delete(key);
		}
	}
	for (const [, projCache] of impactCache) {
		for (const [key, entry] of projCache) {
			if (t - entry.timestamp >= TTL_MS) projCache.delete(key);
		}
	}
}
