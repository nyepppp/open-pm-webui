import { writable, derived, type Writable, type Readable } from 'svelte/store';
import { getEntries } from '$lib/apis/pm/index';
import type { ModuleEntry, MindMapNode } from '$lib/apis/pm/types';

// ============================================================================
// Types
// ============================================================================

export interface TreeModule {
	name: string;
	source: 'auto' | 'manual';
	features: TreeFeature[];
}

export interface TreeFeature {
	name: string;
	source: 'auto' | 'manual';
	paramCount: number;
}

// ============================================================================
// State (writable stores)
// ============================================================================

export const parameterEntries: Writable<ModuleEntry[]> = writable([]);
export const archEntries: Writable<ModuleEntry[]> = writable([]);
export const isLoading: Writable<boolean> = writable(false);
export const loadError: Writable<string> = writable('');

// ============================================================================
// In-memory cache
// ============================================================================

interface CacheEntry {
	parameterEntries: ModuleEntry[];
	archEntries: ModuleEntry[];
}

const cache = new Map<string, CacheEntry>();

// ============================================================================
// Aggregation logic (matches +page.svelte lines 116-174)
// ============================================================================

function aggregateModuleFeatureTree(
	paramEntries: ModuleEntry[],
	architectureEntries: ModuleEntry[]
): TreeModule[] {
	// 1. Auto modules from parameter entries
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

	// 2. Manual modules/features from product-architecture entries
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

	// 3. Merge: auto primary, manual supplements
	const allModules = new Map(autoModules);
	for (const [mod, feats] of manualModules) {
		if (!allModules.has(mod)) allModules.set(mod, new Set());
		for (const f of feats) allModules.get(mod)!.add(f);
	}

	// 4. Build TreeModule[]
	return [...allModules.entries()]
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

// ============================================================================
// Actions
// ============================================================================

export async function loadData(projectId: string): Promise<void> {
	isLoading.set(true);
	loadError.set('');

	try {
		// Check cache first
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

		// Update cache on successful load (even if partial)
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
	isLoading.set(false);
	loadError.set('');
	cache.clear();
}
