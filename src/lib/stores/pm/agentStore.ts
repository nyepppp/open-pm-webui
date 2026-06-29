import { writable, derived, type Writable, type Readable } from 'svelte/store';
import type { AgentSuggestion } from '$lib/apis/pm/types';

// ============================================================================
// State
// ============================================================================

export const agentSuggestions: Writable<AgentSuggestion[]> = writable([]);
export const agentLoading: Writable<boolean> = writable(false);
export const agentError: Writable<string | null> = writable(null);

// Agent configuration
export const agentConfig: Writable<{
	autoAnalyze: boolean;
	autoAnalyzeOnSave: boolean;
	autoAnalyzeInterval: number;
	provider: string;
	model: string;
}> = writable({
	autoAnalyze: false,
	autoAnalyzeOnSave: true,
	autoAnalyzeInterval: 3600,
	provider: 'openai',
	model: 'gpt-4'
});

// ============================================================================
// Derived
// ============================================================================

export const pendingSuggestions: Readable<AgentSuggestion[]> = derived(
	agentSuggestions,
	$suggestions => $suggestions.filter(s => s.status === 'pending')
);

export const confirmedSuggestions: Readable<AgentSuggestion[]> = derived(
	agentSuggestions,
	$suggestions => $suggestions.filter(s => s.status === 'confirmed')
);

export const rejectedSuggestions: Readable<AgentSuggestion[]> = derived(
	agentSuggestions,
	$suggestions => $suggestions.filter(s => s.status === 'rejected')
);

export const suggestionCount: Readable<number> = derived(
	agentSuggestions,
	$suggestions => $suggestions.length
);

export const pendingSuggestionCount: Readable<number> = derived(
	pendingSuggestions,
	$pending => $pending.length
);

// ============================================================================
// Actions
// ============================================================================

export function setSuggestions(suggestions: AgentSuggestion[]) {
	agentSuggestions.set(suggestions);
}

export function addSuggestion(suggestion: AgentSuggestion) {
	agentSuggestions.update(list => [...list, suggestion]);
}

export function updateSuggestion(updated: AgentSuggestion) {
	agentSuggestions.update(list =>
		list.map(s => (s.id === updated.id ? updated : s))
	);
}

export function confirmSuggestion(suggestionId: string) {
	agentSuggestions.update(list =>
		list.map(s =>
			s.id === suggestionId ? { ...s, status: 'confirmed' as const } : s
		)
	);
}

export function rejectSuggestion(suggestionId: string) {
	agentSuggestions.update(list =>
		list.map(s =>
			s.id === suggestionId ? { ...s, status: 'rejected' as const } : s
		)
	);
}

export function removeSuggestion(suggestionId: string) {
	agentSuggestions.update(list => list.filter(s => s.id !== suggestionId));
}

export function clearSuggestions() {
	agentSuggestions.set([]);
}

export function setAgentLoading(loading: boolean) {
	agentLoading.set(loading);
}

export function setAgentError(error: string | null) {
	agentError.set(error);
}

export function setAgentConfig(config: Partial<{
	autoAnalyze: boolean;
	autoAnalyzeOnSave: boolean;
	autoAnalyzeInterval: number;
	provider: string;
	model: string;
}>) {
	agentConfig.update(current => ({ ...current, ...config }));
}
