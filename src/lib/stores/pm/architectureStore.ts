import { writable, derived, type Writable, type Readable } from 'svelte/store';
import { getEntries } from '$lib/apis/pm/index';
import type { ModuleEntry, MindMapNode, Parameter } from '$lib/apis/pm/types';

// ============================================================================
// Types
// ============================================================================

export interface ArchModule {
	id: string;
	name: string;
	description?: string;
	features: ArchFeature[];
	versionId?: string;
	order: number;
	expanded?: boolean;
}

export interface ArchFeature {
	id: string;
	moduleId: string;
	name: string;
	description?: string;
	parameters: ArchParameter[];
	versionId?: string;
	order: number;
	expanded?: boolean;
}

export interface ArchParameter {
	id: string;
	featureId: string;
	name: string;
	key: string;
	type: 'input' | 'output' | 'config';
	dataType: 'string' | 'number' | 'boolean' | 'object' | 'array';
	defaultValue?: string;
	required: boolean;
	description?: string;
	versionId?: string;
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

// ============================================================================
// State (writable stores)
// ============================================================================

export const parameterEntries: Writable<ModuleEntry[]> = writable([]);
export const archEntries: Writable<ModuleEntry[]> = writable([]);
export const isLoading: Writable<boolean> = writable(false);
export const loadError: Writable<string> = writable('');
export const architectureModules: Writable<ArchModule[]> = writable([]);

// ============================================================================
// In-memory cache
// ============================================================================

interface CacheEntry {
	parameterEntries: ModuleEntry[];
	archEntries: ModuleEntry[];
}

const cache = new Map<string, CacheEntry>();

// ============================================================================
// Memoization cache for aggregation
// ============================================================================

let lastParamEntriesJson = '';
let lastArchEntriesJson = '';
let cachedTree: TreeModule[] = [];

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
		const d = entry.data || {};
		const mod = (d.moduleName as string) || '';
		const feat = (d.featureName as string) || '';
		if (mod) {
			if (!autoModules.has(mod)) autoModules.set(mod, new Set());
			if (feat) autoModules.get(mod)!.add(feat);
		}
	}

	const manualModules = new Map<string, Set<string>>();
	for (const entry of architectureEntries) {
		const d = entry.data || {};
		const nodes = d.nodes as MindMapNode[] | undefined;
		if (!nodes) continue;
		for (const node of nodes) {
			if (node.metadata?.source === 'manual') {
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
					e => e.data?.moduleName === name && e.data?.featureName === f
				).length
			}))
		}));
	
	lastParamEntriesJson = paramJson;
	lastArchEntriesJson = archJson;
	return cachedTree;
}

function convertToArchModules(treeModules: TreeModule[], paramEntries: ModuleEntry[]): ArchModule[] {
	return treeModules.map((mod, modIndex) => {
		const moduleId = `mod-${modIndex}`;
		return {
			id: moduleId,
			name: mod.name,
			description: '',
			features: mod.features.map((feat, featIndex) => {
				const featureId = `feat-${modIndex}-${featIndex}`;
				const featureParams = paramEntries.filter(
					e => e.data?.moduleName === mod.name && e.data?.featureName === feat.name
				);
				return {
					id: featureId,
					moduleId,
					name: feat.name,
					description: '',
					parameters: featureParams.map((paramEntry, paramIndex) => {
						const pData = paramEntry.data || {};
						return {
							id: paramEntry.id || `param-${modIndex}-${featIndex}-${paramIndex}`,
							featureId,
							name: String(paramEntry.title || pData.key || ''),
							key: String(pData.key || ''),
							type: (pData.paramType as 'input' | 'output' | 'config') || 'config',
							dataType: (pData.dataType as 'string' | 'number' | 'boolean' | 'object' | 'array') || 'string',
							defaultValue: String(pData.defaultValue || ''),
							required: pData.required === 1,
							description: String(pData.description || ''),
							versionId: paramEntry.versionId,
							sourceDocument: String(pData.sourceDocument || ''),
							relatedRequirements: Array.isArray(pData.relatedRequirements) ? pData.relatedRequirements : [],
							order: paramIndex
						};
					}),
					versionId: paramEntries[0]?.versionId,
					order: featIndex,
					expanded: false
				};
			}),
			versionId: mod.versionId,
			order: modIndex,
			expanded: false
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

export const architectureHierarchy: Readable<ArchModule[]> = derived(
	[aggregatedTree, parameterEntries],
	([$aggregatedTree, $parameterEntries]) => convertToArchModules($aggregatedTree, $parameterEntries)
);

// ============================================================================
// Actions
// ============================================================================

export async function loadData(projectId: string): Promise<void> {
	isLoading.set(true);
	loadError.set('');

	try {
		const cached = cache.get(projectId);
		if (cached) {
			parameterEntries.set(cached.parameterEntries);
			archEntries.set(cached.archEntries);
			isLoading.set(false);
			return;
		}

		const token = localStorage.token || '';
		if (!token) {
			loadError.set('未登录，请先登录');
			isLoading.set(false);
			return;
		}

		const [paramsResult, archsResult] = await Promise.allSettled([
			getEntries(token, projectId, 'parameter'),
			getEntries(token, projectId, 'product-architecture')
		]);

		let loadedParamEntries: ModuleEntry[] = [];
		let loadedArchEntries: ModuleEntry[] = [];

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

		if (paramsResult.status === 'rejected' && archsResult.status === 'rejected') {
			loadError.set('加载数据失败，请稍后重试');
		}

		cache.set(projectId, {
			parameterEntries: loadedParamEntries,
			archEntries: loadedArchEntries
		});
	} catch (e: any) {
		const errorMsg = e?.message || '加载数据失败';
		loadError.set(errorMsg);
		console.error('[Architecture] loadData failed:', errorMsg);
	} finally {
		isLoading.set(false);
	}
}

export async function retryLoadData(projectId: string): Promise<void> {
	cache.delete(projectId);
	await loadData(projectId);
}

export function resetArchitectureStore(): void {
	parameterEntries.set([]);
	archEntries.set([]);
	architectureModules.set([]);
	isLoading.set(false);
	loadError.set('');
	cache.clear();
}
