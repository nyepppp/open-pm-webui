import { createEntry, updateEntry } from '$lib/apis/pm/index';
import type { MindMapNode } from '$lib/apis/pm/types';

// ============================================================================
// Constants
// ============================================================================

export const statusMap: Record<string, { l: string; c: string }> = {
	draft: { l: '草稿', c: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400' },
	review: { l: '评审中', c: 'bg-yellow-50 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-400' },
	approved: { l: '已批准', c: 'bg-green-50 text-green-600 dark:bg-green-900/30 dark:text-green-400' },
	archived: { l: '已归档', c: 'bg-gray-100 text-gray-400 dark:bg-gray-800 dark:text-gray-500' }
};

// ============================================================================
// Helpers
// ============================================================================

export function getEntryData(entry: any, key: string): string {
	return (entry.data || entry.metadata || {})[key] ?? '';
}

// ============================================================================
// Business Logic
// ============================================================================

/**
 * Save architecture entry (create or update) with the given nodes.
 * Errors propagate to the caller.
 */
export async function saveArchitectureEntry(
	token: string,
	projectId: string,
	editingEntryId: string | null,
	nodes: MindMapNode[],
	existingData?: Record<string, unknown>
): Promise<void> {
	if (!editingEntryId) {
		await createEntry(token, projectId, {
			module_type: 'product-architecture',
			title: '产品架构图',
			status: 'draft',
			priority: 'p2',
			data: { ...existingData, nodes }
		});
	} else {
		await updateEntry(token, editingEntryId, {
			data: { ...existingData, nodes }
		});
	}
}

/**
 * Add a manual module (branch node) to the architecture.
 * Returns the updated nodes array. Caller handles saving.
 */
export async function addManualModule(
	token: string,
	projectId: string,
	name: string,
	currentNodes: MindMapNode[],
	editingEntryId: string | null,
	existingData?: Record<string, unknown>
): Promise<MindMapNode[]> {
	const newId = `manual-${Date.now()}`;
	const newNode: MindMapNode = {
		id: newId,
		projectId: projectId,
		type: 'branch',
		label: name,
		parentId: null,
		position: { x: 0, y: 0 },
		createdAt: Date.now(),
		updatedAt: Date.now(),
		metadata: { source: 'manual' }
	};
	return [...currentNodes, newNode];
}

/**
 * Add a manual feature (leaf node) under a module.
 * If the parent module doesn't exist, it is auto-created.
 * Returns the updated nodes array. Caller handles saving.
 */
export async function addManualFeature(
	token: string,
	projectId: string,
	moduleName: string,
	featureName: string,
	currentNodes: MindMapNode[],
	editingEntryId: string | null,
	existingData?: Record<string, unknown>
): Promise<MindMapNode[]> {
	const existingParent = currentNodes.find((n) => n.label === moduleName && n.type === 'branch');

	let nodesToAdd: MindMapNode[] = [];
	let parentId: string;

	if (existingParent) {
		parentId = existingParent.id;
	} else {
		// Create parent module first
		parentId = `manual-${Date.now()}-parent`;
		nodesToAdd.push({
			id: parentId,
			projectId: projectId,
			type: 'branch',
			label: moduleName,
			parentId: null,
			position: { x: 0, y: 0 },
			createdAt: Date.now(),
			updatedAt: Date.now(),
			metadata: { source: 'manual' }
		});
	}

	const newId = `manual-${Date.now()}`;
	nodesToAdd.push({
		id: newId,
		projectId: projectId,
		type: 'leaf',
		label: featureName,
		parentId: parentId,
		position: { x: 0, y: 0 },
		createdAt: Date.now(),
		updatedAt: Date.now(),
		metadata: { source: 'manual' }
	});

	return [...currentNodes, ...nodesToAdd];
}

/**
 * Delete a manual module and all its children.
 * Returns the filtered nodes array. Caller handles saving.
 */
export async function deleteManualModule(
	token: string,
	projectId: string,
	name: string,
	currentNodes: MindMapNode[],
	editingEntryId: string | null,
	existingData?: Record<string, unknown>
): Promise<MindMapNode[]> {
	const moduleNode = currentNodes.find((n) => n.label === name && n.type === 'branch');
	if (!moduleNode) return currentNodes;
	return currentNodes.filter((n) => n.id !== moduleNode.id && n.parentId !== moduleNode.id);
}

/**
 * Delete a manual feature from a module.
 * Returns the filtered nodes array. Caller handles saving.
 */
export async function deleteManualFeature(
	token: string,
	projectId: string,
	moduleName: string,
	featureName: string,
	currentNodes: MindMapNode[],
	editingEntryId: string | null,
	existingData?: Record<string, unknown>
): Promise<MindMapNode[]> {
	const featureNode = currentNodes.find(
		(n) =>
			n.label === featureName &&
			n.type === 'leaf' &&
			currentNodes.find((p) => p.id === n.parentId)?.label === moduleName
	);
	if (!featureNode) return currentNodes;
	return currentNodes.filter((n) => n.id !== featureNode.id);
}
