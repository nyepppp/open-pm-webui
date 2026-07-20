/**
 * ganttCache —— 甘特图聚合结果记忆化缓存。
 *
 * 职责：
 * - 记忆化 GanttEntry[] → frappe Task[] 的转换结果（按 entries 引用缓存）
 * - 监听 entry create/update/delete 事件主动 invalidate
 * - TTL 5 分钟，超时自动失效
 *
 * 用法：
 *   const tasks = getOrComputeTasks(entries, () => convert(entries));
 *   invalidateProject(projectId);
 */

interface CacheEntry {
	tasks: any[];
	timestamp: number;
	// 关联的 entry id 集合，用于精确 invalidate
	entryIds: Set<string>;
}

const TTL_MS = 5 * 60 * 1000; // 5 分钟

// 按 projectId 维度组织的缓存
// key: projectId → (cacheKey → CacheEntry)
const projectCaches = new Map<string, Map<string, CacheEntry>>();

function now(): number {
	return Date.now();
}

/**
 * 取或计算缓存的 tasks。
 * cacheKey 应包含 moduleType + timeScale + viewOffset，确保不同视图不串。
 */
export function getOrComputeTasks(
	projectId: string,
	cacheKey: string,
	entryIds: string[],
	compute: () => any[]
): any[] {
	let projCache = projectCaches.get(projectId);
	if (!projCache) {
		projCache = new Map();
		projectCaches.set(projectId, projCache);
	}

	const cached = projCache.get(cacheKey);
	const idsSet = new Set(entryIds);

	// 命中条件：未过期 + entry id 集合一致
	if (cached && now() - cached.timestamp < TTL_MS && setEquals(cached.entryIds, idsSet)) {
		return cached.tasks;
	}

	const tasks = compute();
	projCache.set(cacheKey, {
		tasks,
		timestamp: now(),
		entryIds: idsSet
	});
	return tasks;
}

/**
 * invalidate 一个项目下所有甘特缓存（entry 增删改后调用）。
 */
export function invalidateProject(projectId: string): void {
	projectCaches.delete(projectId);
}

/**
 * invalidate 一个项目下特定 moduleType 的缓存。
 * cacheKey 前缀匹配 moduleType。
 */
export function invalidateModule(projectId: string, moduleType: string): void {
	const projCache = projectCaches.get(projectId);
	if (!projCache) return;
	for (const key of projCache.keys()) {
		if (key.includes(`:${moduleType}:`)) {
			projCache.delete(key);
		}
	}
}

/** 清理所有过期缓存（可周期性调用）。 */
export function pruneExpired(): void {
	const t = now();
	for (const [, projCache] of projectCaches) {
		for (const [key, entry] of projCache) {
			if (t - entry.timestamp >= TTL_MS) {
				projCache.delete(key);
			}
		}
	}
}

function setEquals(a: Set<string>, b: Set<string>): boolean {
	if (a.size !== b.size) return false;
	for (const x of a) {
		if (!b.has(x)) return false;
	}
	return true;
}
