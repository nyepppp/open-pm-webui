import { writable, derived } from 'svelte/store';
import type { Workflow } from '$lib/apis/workflow/index';

interface WorkflowState {
	workflows: Workflow[];
	currentWorkflow: Workflow | null;
	loading: boolean;
	error: string | null;
}

function createWorkflowStore() {
	const { subscribe, set, update } = writable<WorkflowState>({
		workflows: [],
		currentWorkflow: null,
		loading: false,
		error: null
	});

	return {
		subscribe,
		setWorkflows: (workflows: Workflow[]) =>
			update((state) => ({ ...state, workflows })),
		setCurrentWorkflow: (workflow: Workflow | null) =>
			update((state) => ({ ...state, currentWorkflow: workflow })),
		setLoading: (loading: boolean) =>
			update((state) => ({ ...state, loading })),
		setError: (error: string | null) =>
			update((state) => ({ ...state, error })),
		addWorkflow: (workflow: Workflow) =>
			update((state) => ({
				...state,
				workflows: [workflow, ...state.workflows]
			})),
		updateWorkflow: (id: string, data: Partial<Workflow>) =>
			update((state) => ({
				...state,
				workflows: state.workflows.map((w) =>
					w.id === id ? { ...w, ...data } : w
				)
			})),
		removeWorkflow: (id: string) =>
			update((state) => ({
				...state,
				workflows: state.workflows.filter((w) => w.id !== id)
			})),
		reset: () =>
			set({
				workflows: [],
				currentWorkflow: null,
				loading: false,
				error: null
			})
	};
}

export const workflowStore = createWorkflowStore();

// Derived stores
export const workflows = derived(
	workflowStore,
	($store) => $store.workflows
);

export const currentWorkflow = derived(
	workflowStore,
	($store) => $store.currentWorkflow
);

export const isLoading = derived(
	workflowStore,
	($store) => $store.loading
);

export const hasError = derived(
	workflowStore,
	($store) => $store.error
);
