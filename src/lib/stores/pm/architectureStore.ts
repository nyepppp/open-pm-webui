import { writable, derived, get, type Writable, type Readable } from 'svelte/store';
import {
	getEntries,
	getRelations,
	listModuleVersions,
	createModuleVersion as apiCreateModuleVersion,
	switchModuleVersion as apiSwitchModuleVersion,
	deleteModuleVersion as apiDeleteModuleVersion,
	type ModuleVersion
} from '$lib/apis/pm/index';
import type { ModuleEntry, MindMapNode, Parameter } from '$lib/apis/pm/types';

// ============================================================================
// Types
// ============================================================================

export interface ArchModule {
	id: string;
	entryId?: string;
	name: string;
	description?: string;
	features: ArchFeature[];
	versionId?: string;
	currentVersionNumber?: string;
	createdVersionNumber?: string;
	branchName?: string;
	createdAt?: number;
	updatedAt?: number;
	status?: string;
	priority?: string;
	order: number;
	expanded?: boolean;
	// 模块版本管理（与项目版本 PMVersion 分离，独立字段）
	moduleVersionId?: string;
	moduleVersions?: ModuleVersion[];
}

export interface ArchFeature {
	id: string;
	entryId?: string;
	moduleId: string;
	name: string;
	description?: string;
	parameters: ArchParameter[];
	versionId?: string;
	currentVersionNumber?: string;
	createdVersionNumber?: string;
	branchName?: string;
	createdAt?: number;
	updatedAt?: number;
	status?: string;
	priority?: string;
	order: number;
	expanded?: boolean;
}

export interface ArchParameter {
	id: string;
	entryId?: string;
	moduleVersionId?: string;
	featureId: string;
	name: string;
	key: string;
	type: 'input' | 'output' | 'config';
	dataType: 'string' | 'number' | 'boolean' | 'object' | 'array';
	defaultValue?: string;
	required: boolean;
	description?: string;
	versionId?: string;
	currentVersionNumber?: string;
	createdAt?: number;
	updatedAt?: number;
	status?: string;
	priority?: string;
	sourceDocument?: string;
	relatedRequirements?: string[];
	order: number;
}

export interface TreeModule {
	name: string;
	source: 'auto' | 'manual';
	features: TreeFeature[];
	versionId?: string;
	updatedAt?: number;
	createdAt?: number;
}

export interface TreeFeature {
	name: string;
	source: 'auto' | 'manual';
	paramCount: number;
	parameters?: Parameter[];
}

export interface PMRelation {
	id: string;
	project_id: string;
	entity_a_id: string;
	entity_b_id: string;
	relation_type: string; // "contains" | "references" | "derives" | "modifies" | "conflicts"
	confidence?: number;
	confirmed?: number;
	created_by?: string;
	version_id?: string;
	created_at?: number;
}

// ============================================================================
// State (writable stores)
// ============================================================================

export const parameterEntries: Writable<ModuleEntry[]> = writable([]);
export const archEntries: Writable<ModuleEntry[]> = writable([]);
export const relationEntries: Writable<PMRelation[]> = writable([]);
export const isLoading: Writable<boolean> = writable(false);
export const loadError: Writable<string> = writable('');
export const architectureModules: Writable<ArchModule[]> = writable([]);

// 最近一次 loadData 使用的 projectId / versionId，供 module version actions 刷新时复用
let lastLoadedProjectId: string | undefined;
let lastLoadedVersionId: string | undefined;

// ============================================================================
// In-memory cache
// ============================================================================

interface CacheEntry {
	parameterEntries: ModuleEntry[];
	archEntries: ModuleEntry[];
	relationEntries: PMRelation[];
}

const cache = new Map<string, CacheEntry>();

// ============================================================================
// Memoization cache for aggregation
// ============================================================================

let lastParamEntriesJson = '';
let lastArchEntriesJson = '';
let cachedTree: TreeModule[] = [];

function getModuleNames(entryData: Record<string, unknown>): string[] {
	const d = entryData || {};
	const candidates = [
		d.moduleName, d.module_name, d.module, d.moduleTitle, d.module_title,
		d.moduleId, d.module_id, d.title, d.name
	];
	return candidates.filter(Boolean).map(String);
}

function getFeatureNames(entryData: Record<string, unknown>): string[] {
	const d = entryData || {};
	// 注意：不包含 d.title / d.name —— 那些是通用字段，会导致同名功能跨模块冲突。
	// 仅匹配明确的 feature 字段名。ID 字段仅用于 ID 优先匹配，不作为名称候选。
	const candidates = [
		d.featureName, d.feature_name, d.feature, d.featureTitle, d.feature_title
	];
	return candidates.filter(Boolean).map(String);
}

/** 取条目 data 中的 feature ID 候选（用于 ID 优先匹配，避免同名冲突） */
function getFeatureIds(entryData: Record<string, unknown>): string[] {
	const d = entryData || {};
	const candidates = [d.featureId, d.feature_id];
	return candidates.filter(Boolean).map(String);
}

function aggregateModuleFeatureTree(
	paramEntries: ModuleEntry[],
	architectureEntries: ModuleEntry[]
): TreeModule[] {
	const paramJson = JSON.stringify(paramEntries.map(e => e.id));
	const archJson = JSON.stringify(architectureEntries.map(e => e.id));

	if (paramJson === lastParamEntriesJson && archJson === lastArchEntriesJson && cachedTree.length > 0) {
		return cachedTree;
	}

	const autoModules = new Map<string, Set<string>>();
	for (const entry of paramEntries) {
		const d = entry.data || entry.metadata || {};
		const modCandidates = getModuleNames(d);
		const featCandidates = getFeatureNames(d);
		const mod = modCandidates[0] || '';
		const effectiveMod = mod || '未分类模块';

		if (!autoModules.has(effectiveMod)) autoModules.set(effectiveMod, new Set());

		for (const feat of featCandidates) {
			if (feat && feat !== effectiveMod) {
				autoModules.get(effectiveMod)!.add(feat);
			}
		}

		if (featCandidates.length === 0 && entry.title && entry.title !== effectiveMod) {
			autoModules.get(effectiveMod)!.add(entry.title);
		}
	}

	const manualModules = new Map<string, Set<string>>();
	for (const entry of architectureEntries) {
		const d = entry.data || entry.metadata || {};
		const nodes = d.nodes as MindMapNode[] | undefined;
		if (!nodes || !Array.isArray(nodes)) {
			// 区分条目类型：feature/parameter 应归到父 module 下，而非当成顶级模块。
			// 仅 module 或无 type 标记的旧条目才走原顶级模块逻辑。
			// D44-fix: skill 写入的是 data.node_type（'module'/'function'/'parameter'），
			// 前端原本只读 data.type（'feature'/'parameter'）导致字段不匹配。这里把
			// node_type 映射到 type 体系，向后兼容旧数据（旧数据无 node_type 仍走原逻辑）。
			const dRawType = (d as any).type as string | undefined;
			const dRawNodeType = (d as any).node_type as string | undefined;
			const dNodeTypeMapped =
				dRawNodeType === 'function' ? 'feature'
				: dRawNodeType === 'parameter' ? 'parameter'
				: dRawNodeType; // 'module' 或 undefined 保留原值
			const dType = dRawType || dNodeTypeMapped;
			const dModuleName = (d as any).moduleName as string | undefined;
			const dFeatureName = (d as any).featureName as string | undefined;

			if (dType === 'feature' && dModuleName) {
				if (!manualModules.has(dModuleName)) manualModules.set(dModuleName, new Set());
				const featName = String(dFeatureName || (d as any).name || d.title || entry.title || '');
				if (featName && featName !== dModuleName) {
					manualModules.get(dModuleName)!.add(featName);
				}
			} else if (dType === 'parameter' && dModuleName && dFeatureName) {
				if (!manualModules.has(dModuleName)) manualModules.set(dModuleName, new Set());
				if (!manualModules.get(dModuleName)!.has(dFeatureName)) {
					manualModules.get(dModuleName)!.add(dFeatureName);
				}
			} else if (d.title || entry.title) {
				const title = String(d.title || entry.title);
				if (!manualModules.has(title)) manualModules.set(title, new Set());
			}
			continue;
		}
		for (const node of nodes) {
			// Treat undefined source as manual; only skip explicitly auto-extracted nodes
			if (node.metadata?.source === 'auto') continue;

			if (node.type === 'branch') {
				if (!manualModules.has(node.label)) manualModules.set(node.label, new Set());
			} else if (node.type === 'leaf' && node.parentId) {
				const parent = nodes.find(n => n.id === node.parentId);
				if (parent) {
					if (!manualModules.has(parent.label)) manualModules.set(parent.label, new Set());
					manualModules.get(parent.label)!.add(node.label);
				}
			}
		}
	}

	const allModules = new Map(autoModules);
	for (const [mod, feats] of manualModules) {
		if (!allModules.has(mod)) allModules.set(mod, new Set());
		for (const f of feats) allModules.get(mod)!.add(f);
	}

	cachedTree = [...allModules.entries()]
		.sort(([a], [b]) => a.localeCompare(b))
		.map(([name, features]) => ({
			name,
			source: autoModules.has(name) ? ('auto' as const) : ('manual' as const),
			features: [...features].sort().map(f => ({
				name: f,
				source: (autoModules.get(name)?.has(f) ? 'auto' : 'manual') as 'auto' | 'manual',
				paramCount: paramEntries.filter(
					e => {
						const d = e.data || e.metadata || {};
						const modCandidates = getModuleNames(d);
						const featCandidates = getFeatureNames(d);
						return modCandidates.includes(name) && featCandidates.includes(f);
					}
				).length
			}))
		}));

	lastParamEntriesJson = paramJson;
	lastArchEntriesJson = archJson;
	return cachedTree;
}

function convertToArchModules(
	treeModules: TreeModule[],
	paramEntries: ModuleEntry[],
	archEntries: ModuleEntry[]
): ArchModule[] {
	return treeModules.map((mod, modIndex) => {
		const moduleId = `mod-${modIndex}`;
		// Find param entries matching this module name (for module-level versionId)
		const moduleParams = paramEntries.filter(e => {
			const d = e.data || {};
			const modCandidates = getModuleNames(d);
			return modCandidates.includes(mod.name);
		});
		// Prefer direct module/feature archEntries (module_type='product-architecture')
		// over paramEntries for metadata — these entries carry the user-authored
		// description, branchName, createdVersionNumber, etc.
		const moduleArchEntry = archEntries.find(e => e.title === mod.name);
		const moduleMeta = moduleArchEntry || moduleParams[0];

		const moduleDescription: string =
			(typeof moduleArchEntry?.data?.description === 'string' && moduleArchEntry.data.description) ||
			(typeof moduleArchEntry?.content === 'string' && moduleArchEntry.content) ||
			'';

		return {
			id: moduleId,
			entryId: moduleArchEntry?.id,
			name: mod.name,
			description: moduleDescription,
			branchName: moduleMeta?.branchName,
			createdVersionNumber: moduleMeta?.createdVersionNumber,
			features: mod.features.map((feat, featIndex) => {
			const featureId = `feat-${modIndex}-${featIndex}`;
			// Find direct feature archEntry by title (best-effort match)
			const featureArchEntry = archEntries.find(e =>
				e.title === feat.name &&
				(e.data?.type === 'feature' || !e.data?.type)
			);
			// 真实 entryId（用于 ID 优先匹配参数，避免同名功能跨模块共享参数）
			const featEntryId = featureArchEntry?.id;
			// Support flexible key naming when filtering parameters.
			// ID 优先（新数据，D3 持久化 featureId 后），名称回退（旧数据）
			const featureParams = paramEntries.filter(
				e => {
					const d = e.data || {};
					// ID 优先匹配
					if (featEntryId) {
						const featIds = getFeatureIds(d);
						if (featIds.includes(featEntryId)) return true;
					}
					// 名称回退
					const modCandidates = getModuleNames(d);
					const featCandidates = getFeatureNames(d);
					return modCandidates.includes(mod.name) && featCandidates.includes(feat.name);
				}
			);
			const featureMeta = featureArchEntry || featureParams[0];

				const featureDescription: string =
					(typeof featureArchEntry?.data?.description === 'string' && featureArchEntry.data.description) ||
					(typeof featureArchEntry?.content === 'string' && featureArchEntry.content) ||
					'';

				return {
					id: featureId,
					entryId: featureArchEntry?.id,
					moduleId,
					name: feat.name,
					description: featureDescription,
					branchName: featureMeta?.branchName,
					createdVersionNumber: featureMeta?.createdVersionNumber,
					parameters: featureParams.map((paramEntry, paramIndex) => {
					const pData = paramEntry.data || {};
					return {
						id: paramEntry.id || `param-${modIndex}-${featIndex}-${paramIndex}`,
						entryId: paramEntry.id,
						moduleVersionId: (paramEntry as any).module_version_id,
						featureId,
						name: String(paramEntry.title || pData.key || ''),
						key: String(pData.key || ''),
						type: ((pData.paramType === 'input' || pData.paramType === 'output' || pData.paramType === 'config')
						? pData.paramType
						: 'config') as 'input' | 'output' | 'config',
						dataType: (pData.dataType as 'string' | 'number' | 'boolean' | 'object' | 'array') || 'string',
						defaultValue: String(pData.defaultValue || ''),
						required: pData.required === true || pData.required === 1,
						description: String(pData.description || ''),
						versionId: paramEntry.versionId,
						currentVersionNumber: paramEntry.currentVersionNumber,
						createdAt: paramEntry.createdAt,
						updatedAt: paramEntry.updatedAt,
						status: paramEntry.status,
						priority: paramEntry.priority,
						sourceDocument: String(pData.sourceDocument || ''),
						relatedRequirements: Array.isArray(pData.relatedRequirements) ? pData.relatedRequirements : [],
						order: paramIndex
					};
				}),
					// Use direct archEntry metadata if available; otherwise fallback to first matching param
					versionId: featureMeta?.versionId,
					currentVersionNumber: featureMeta?.currentVersionNumber,
					createdAt: featureMeta?.createdAt,
					updatedAt: featureMeta?.updatedAt,
					status: featureMeta?.status,
					priority: featureMeta?.priority,
					order: featIndex,
					expanded: false
				};
			}),
			// Use direct archEntry metadata if available; otherwise fallback to first matching param
		versionId: moduleMeta?.versionId,
		currentVersionNumber: moduleMeta?.currentVersionNumber,
		createdAt: moduleMeta?.createdAt,
		updatedAt: moduleMeta?.updatedAt,
		status: moduleMeta?.status,
		priority: moduleMeta?.priority,
		order: modIndex,
		expanded: false,
		// 模块版本 ID（从 entry.module_version_id 读取，后端 create_entry 自动创建 v1）
		moduleVersionId: (moduleArchEntry as any)?.module_version_id
	};
});
}

// ============================================================================
// Derived stores
// ============================================================================

export const aggregatedTree: Readable<TreeModule[]> = derived(
	[parameterEntries, archEntries],
	([$parameterEntries, $archEntries]) => aggregateModuleFeatureTree($parameterEntries, $archEntries)
);

export const mindmapNodes: Readable<MindMapNode[]> = derived(archEntries, $archEntries => {
	if ($archEntries.length > 0) {
		const data = $archEntries[0].data || {};
		return (data.nodes as MindMapNode[]) || [];
	}
	return [];
});

export const editingEntryId: Readable<string | null> = derived(
	archEntries,
	$archEntries => $archEntries[0]?.id || null
);

// architectureHierarchy 改为 Writable，支持 replaceVirtualId 直接更新虚拟 ID
export const architectureHierarchy: Writable<ArchModule[]> = writable<ArchModule[]>([]);

// 从底层 store 重新计算 architectureHierarchy
function recomputeHierarchy(): void {
	const tree = get(aggregatedTree);
	const params = get(parameterEntries);
	const archs = get(archEntries);
	architectureHierarchy.set(convertToArchModules(tree, params, archs));
}

// 订阅底层 store，数据变化时自动重新计算 hierarchy。
// aggregatedTree 已依赖 parameterEntries/archEntries，但 convertToArchModules
// 还会直接读取这两个 store 来匹配 entryId，所以三者都要订阅。
// 模块级引用防止订阅被回收。
const _hierarchyRecomputeSub = derived(
	[aggregatedTree, parameterEntries, archEntries],
	(values) => values
).subscribe(() => {
	recomputeHierarchy();
});

// ============================================================================
// Actions
// ============================================================================

export async function loadData(projectId: string, versionId?: string): Promise<void> {
	isLoading.set(true);
	loadError.set('');

	// 记录最近一次加载参数，供 module version actions 刷新时复用
	lastLoadedProjectId = projectId;
	lastLoadedVersionId = versionId;

	// Cache key includes versionId so switching versions doesn't return stale data
	const cacheKey = `${projectId}:${versionId ?? 'all'}`;

	try {
		const cached = cache.get(cacheKey);
		if (cached) {
			parameterEntries.set(cached.parameterEntries);
			archEntries.set(cached.archEntries);
			relationEntries.set(cached.relationEntries);
			isLoading.set(false);
			return;
		}

		const token = localStorage.token || '';
		if (!token) {
			loadError.set('未登录，请先登录');
			isLoading.set(false);
			return;
		}

		const [paramsResult, archsResult, relsResult] = await Promise.allSettled([
			getEntries(token, projectId, 'parameter', versionId),
			getEntries(token, projectId, 'product-architecture', versionId),
			getRelations(token, projectId)
		]);

		let loadedParamEntries: ModuleEntry[] = [];
		let loadedArchEntries: ModuleEntry[] = [];
		let loadedRelationEntries: PMRelation[] = [];

		if (paramsResult.status === 'fulfilled') {
			loadedParamEntries = paramsResult.value;
			parameterEntries.set(loadedParamEntries);
		} else {
			console.error('[Architecture] Failed to load parameters:', paramsResult.reason);
		}

		if (archsResult.status === 'fulfilled') {
			loadedArchEntries = archsResult.value;
			archEntries.set(loadedArchEntries);
		} else {
			console.error('[Architecture] Failed to load architecture:', archsResult.reason);
		}

		if (relsResult.status === 'fulfilled') {
			loadedRelationEntries = Array.isArray(relsResult.value) ? relsResult.value : [];
			relationEntries.set(loadedRelationEntries);
		} else {
			console.error('[Architecture] Failed to load relations:', relsResult.reason);
			relationEntries.set([]);
		}

		if (paramsResult.status === 'rejected' && archsResult.status === 'rejected') {
			loadError.set('加载数据失败，请稍后重试');
		}

		cache.set(cacheKey, {
			parameterEntries: loadedParamEntries,
			archEntries: loadedArchEntries,
			relationEntries: loadedRelationEntries
		});

		// 异步加载每个模块的版本列表（不阻塞主数据加载）
		// 与项目版本（PMVersion）分离：这里只加载模块级版本（PMModuleVersion）
		try {
			const token = localStorage.token || '';
			if (token) {
				// 从已计算的 hierarchy 中取所有有 entryId 的模块
				const currentModules = get(architectureHierarchy);
				const moduleEntries = currentModules
					.filter(m => m.entryId)
					.map(m => ({ entryId: m.entryId as string, virtualId: m.id }));
				if (moduleEntries.length > 0) {
					const versionsPerModule = await Promise.allSettled(
						moduleEntries.map(me => listModuleVersions(token, projectId, me.entryId))
					);
					// D1: 只附加 moduleVersions 列表用于"创建版本"按钮和版本数显示，
					// 不再用 moduleVersions 的版本号覆盖 currentVersionNumber。
					// 架构页"版本"列统一显示项目版本号（PMVersion，来自 $currentVersion.versionNumber），
					// 由 ArchitectureTable 通过 projectVersionNumber prop 接收。
					architectureHierarchy.update(modules => modules.map(mod => {
						const idx = moduleEntries.findIndex(me => me.virtualId === mod.id);
						if (idx >= 0 && versionsPerModule[idx].status === 'fulfilled') {
							const versions = versionsPerModule[idx].value || [];
							return {
								...mod,
								moduleVersions: versions,
								// currentVersionNumber 保持原始值（来自 PMEntryVersion，文档版本语义）
							};
						}
						return mod;
					}));
				}
			}
		} catch (e: any) {
			console.warn('[Architecture] Failed to load module versions:', e?.message);
		}
	} catch (e: any) {
		const errorMsg = e?.message || '加载数据失败';
		loadError.set(errorMsg);
		console.error('[Architecture] loadData failed:', errorMsg);
	} finally {
		isLoading.set(false);
	}
}

export async function retryLoadData(projectId: string, versionId?: string): Promise<void> {
	const cacheKey = `${projectId}:${versionId ?? 'all'}`;
	cache.delete(cacheKey);
	await loadData(projectId, versionId);
}

// ============================================================================
// Module Version Actions（模块版本管理，与项目版本分离）
// ============================================================================

/** 创建模块版本，成功后刷新 store */
export async function createModuleVersionAction(
	projectId: string,
	moduleEntryId: string,
	form: { version_number: string; change_summary: string; project_version_id?: string }
): Promise<void> {
	const token = localStorage.token || '';
	if (!token) throw new Error('未登录');
	await apiCreateModuleVersion(token, projectId, moduleEntryId, form);
	// 刷新 store 以拉取新版本列表（复用最近一次加载的 versionId）
	await retryLoadData(projectId, lastLoadedVersionId);
}

/** 切换模块版本，成功后刷新 store */
export async function switchModuleVersionAction(
	projectId: string,
	moduleEntryId: string,
	versionId: string
): Promise<void> {
	const token = localStorage.token || '';
	if (!token) throw new Error('未登录');
	await apiSwitchModuleVersion(token, projectId, moduleEntryId, versionId);
	await retryLoadData(projectId, lastLoadedVersionId);
}

/** 删除模块版本，成功后刷新 store */
export async function deleteModuleVersionAction(
	projectId: string,
	moduleEntryId: string,
	versionId: string
): Promise<void> {
	const token = localStorage.token || '';
	if (!token) throw new Error('未登录');
	await apiDeleteModuleVersion(token, projectId, moduleEntryId, versionId);
	await retryLoadData(projectId, lastLoadedVersionId);
}

export function resetArchitectureStore(): void {
	parameterEntries.set([]);
	archEntries.set([]);
	relationEntries.set([]);
	architectureModules.set([]);
	isLoading.set(false);
	loadError.set('');
	cache.clear();
}

// ============================================================================
// Virtual ID 回填与反查工具方法
// ============================================================================

/**
 * 将 architectureHierarchy 中的虚拟 ID（前缀 mod- / feat- / param-）替换为服务端返回的真实 ID。
 * 同时同步更新 relationEntries 中引用该虚拟 ID 的源/目标字段。
 *
 * 用途：handleTableAdd 在 createEntry 成功后立即调用，确保新增条目可被编辑/删除，
 * 无需等待 retryLoadData 完成全量刷新。
 */
export function replaceVirtualId(virtualId: string, realId: string): void {
	if (!virtualId || !realId || virtualId === realId) return;

	// 替换 architectureHierarchy 中所有匹配的虚拟 ID（module/feature/parameter 三层）
	architectureHierarchy.update(modules => {
		return modules.map(mod => {
			const modIdMatch = mod.id === virtualId;
			const modEntryIdMatch = mod.entryId === virtualId;
			return {
				...mod,
				id: modIdMatch ? realId : mod.id,
				entryId: modIdMatch || modEntryIdMatch ? realId : mod.entryId,
				features: mod.features.map(feat => {
					const featIdMatch = feat.id === virtualId;
					const featEntryIdMatch = feat.entryId === virtualId;
					return {
						...feat,
						id: featIdMatch ? realId : feat.id,
						entryId: featIdMatch || featEntryIdMatch ? realId : feat.entryId,
						// 功能的 moduleId 指向父模块的虚拟 ID，需同步更新
						moduleId: feat.moduleId === virtualId ? realId : feat.moduleId,
						parameters: feat.parameters.map(param => ({
							...param,
							id: param.id === virtualId ? realId : param.id,
							// 参数的 featureId 指向父功能的虚拟 ID，需同步更新
							featureId: param.featureId === virtualId ? realId : param.featureId
						}))
					};
				})
			};
		});
	});

	// 同步更新 relationEntries 中引用该虚拟 ID 的源/目标字段
	relationEntries.update(relations => {
		return relations.map(rel => ({
			...rel,
			entity_a_id: rel.entity_a_id === virtualId ? realId : rel.entity_a_id,
			entity_b_id: rel.entity_b_id === virtualId ? realId : rel.entity_b_id
		}));
	});
}

/**
 * 通过 title + parentId 在 store 中反查真实条目（id 不以 mod-/feat-/param- 开头）。
 *
 * 用途：handleTableEdit / handleTableDelete 检测到虚拟 ID 时的兜底反查。
 * 当 replaceVirtualId 未命中（例如页面刷新后 store 重新派生、虚拟 ID 已变化），
 * 通过名称 + 父节点定位真实条目。
 *
 * @returns 命中则返回 { id, type }，否则返回 null
 */
export function findEntryByTitleAndParent(
	title: string,
	parentId?: string
): { id: string; type: 'module' | 'feature' | 'parameter' } | null {
	if (!title) return null;
	const modules = get(architectureHierarchy);

	for (const mod of modules) {
		// 模块：无父节点（或 parentId 为根哨兵 __root__）
		if (mod.name === title && (!parentId || parentId === '__root__')) {
			// 模块的 id 始终为虚拟 ID（mod-*），真实 ID 在 entryId
			const realId = mod.entryId || (mod.id.startsWith('mod-') ? null : mod.id);
			if (realId) return { id: realId, type: 'module' };
		}
		for (const feat of mod.features) {
			// 功能：父节点为模块（feat.moduleId === parentId）
			if (feat.name === title && (!parentId || parentId === mod.id || parentId === feat.moduleId)) {
				const realId = feat.entryId || (feat.id.startsWith('feat-') ? null : feat.id);
				if (realId) return { id: realId, type: 'feature' };
			}
			for (const param of feat.parameters) {
				// 参数：父节点为功能（param.featureId === parentId）
				if (param.name === title && (!parentId || parentId === feat.id || parentId === param.featureId)) {
					// 参数的 id 直接使用服务端真实 ID（paramEntry.id），虚拟前缀仅作兜底
					const realId = param.id.startsWith('param-') ? null : param.id;
					if (realId) return { id: realId, type: 'parameter' };
				}
			}
		}
	}
	return null;
}
