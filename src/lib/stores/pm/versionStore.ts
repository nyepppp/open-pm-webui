import { writable, derived, type Writable, type Readable } from 'svelte/store';
import type { Version } from '$lib/apis/pm/types';

// ============================================================================
// State
// ============================================================================

export const versions: Writable<Version[]> = writable([]);
export const currentVersion: Writable<Version | null> = writable(null);
export const versionLoading: Writable<boolean> = writable(false);
export const versionError: Writable<string | null> = writable(null);
export const versionSearchQuery: Writable<string> = writable('');

// ============================================================================
// Derived
// ============================================================================

export const sortedVersions: Readable<Version[]> = derived(
	versions,
	$versions => [...$versions].sort((a, b) => b.createdAt - a.createdAt)
);

export const filteredVersions: Readable<Version[]> = derived(
	[sortedVersions, versionSearchQuery],
	([$sorted, $query]) => {
		if (!$query.trim()) {
			return $sorted;
		}
		const lowerQuery = $query.toLowerCase();
		return $sorted.filter(
			v =>
				v.versionNumber.toLowerCase().includes(lowerQuery) ||
				v.description.toLowerCase().includes(lowerQuery) ||
				v.label?.toLowerCase().includes(lowerQuery)
		);
	}
);

export const versionCount: Readable<number> = derived(versions, $v => $v.length);

// ============================================================================
// Actions
// ============================================================================

export function setVersions(versionList: Version[]) {
	versions.set(versionList);
}

export function addVersion(version: Version) {
	versions.update(list => [...list, version]);
}

export function updateVersion(updated: Version) {
	versions.update(list =>
		list.map(v => (v.id === updated.id ? updated : v))
	);
	currentVersion.update(current => {
		if (current?.id === updated.id) {
			return updated;
		}
		return current;
	});
}

export function removeVersion(versionId: string) {
	versions.update(list => list.filter(v => v.id !== versionId));
	currentVersion.update(current => {
		if (current?.id === versionId) {
			return null;
		}
		return current;
	});
}

export function setCurrentVersion(version: Version | null) {
	currentVersion.set(version);
}

export function setVersionSearchQuery(query: string) {
	versionSearchQuery.set(query);
}

export function setVersionLoading(loading: boolean) {
	versionLoading.set(loading);
}

export function setVersionError(error: string | null) {
	versionError.set(error);
}

export function resetVersionStore() {
	versions.set([]);
	currentVersion.set(null);
	versionLoading.set(false);
	versionError.set(null);
	versionSearchQuery.set('');
}
