import { writable, derived } from 'svelte/store';
import type { TimbalWorkflow, TimbalExecutionResponse } from '$lib/apis/timbal/types';

// ============================================================================
// Types
// ============================================================================

export interface TimbalStore {
	workflows: TimbalWorkflow[];
	executions: TimbalExecutionResponse[];
	selectedWorkflow: TimbalWorkflow | null;
	selectedExecution: TimbalExecutionResponse | null;
	isLoading: boolean;
	error: string | null;
}

// ============================================================================
// Initial State
// ============================================================================

const initialState: TimbalStore = {
	workflows: [],
	executions: [],
	selectedWorkflow: null,
	selectedExecution: null,
	isLoading: false,
	error: null
};

// ============================================================================
// Store
// ============================================================================

function createTimbalStore() {
	const { subscribe, set, update } = writable<TimbalStore>(initialState);

	return {
		subscribe,
		set,
		update,
		
		// Workflow actions
		setWorkflows: (workflows: TimbalWorkflow[]) => {
			update(state => ({ ...state, workflows }));
		},
		
		addWorkflow: (workflow: TimbalWorkflow) => {
			update(state => ({
				...state,
				workflows: [...state.workflows, workflow]
			}));
		},
		
		updateWorkflow: (workflowId: string, updates: Partial<TimbalWorkflow>) => {
			update(state => ({
				...state,
				workflows: state.workflows.map(w =>
					w.id === workflowId ? { ...w, ...updates } : w
				)
			}));
		},
		
		removeWorkflow: (workflowId: string) => {
			update(state => ({
				...state,
				workflows: state.workflows.filter(w => w.id !== workflowId)
			}));
		},
		
		selectWorkflow: (workflow: TimbalWorkflow | null) => {
			update(state => ({ ...state, selectedWorkflow: workflow }));
		},
		
		// Execution actions
		setExecutions: (executions: TimbalExecutionResponse[]) => {
			update(state => ({ ...state, executions }));
		},
		
		addExecution: (execution: TimbalExecutionResponse) => {
			update(state => ({
				...state,
				executions: [execution, ...state.executions]
			}));
		},
		
		updateExecution: (executionId: string, updates: Partial<TimbalExecutionResponse>) => {
			update(state => ({
				...state,
				executions: state.executions.map(e =>
					e.execution_id === executionId ? { ...e, ...updates } : e
				)
			}));
		},
		
		selectExecution: (execution: TimbalExecutionResponse | null) => {
			update(state => ({ ...state, selectedExecution: execution }));
		},
		
		// Loading and error
		setLoading: (isLoading: boolean) => {
			update(state => ({ ...state, isLoading }));
		},
		
		setError: (error: string | null) => {
			update(state => ({ ...state, error }));
		},
		
		// Reset
		reset: () => {
			set(initialState);
		}
	};
}

export const timbalStore = createTimbalStore();

// ============================================================================
// Derived Stores
// ============================================================================

export const workflowCount = derived(
	timbalStore,
	$store => $store.workflows.length
);

export const executionCount = derived(
	timbalStore,
	$store => $store.executions.length
);

export const activeExecutions = derived(
	timbalStore,
	$store => $store.executions.filter(e => e.status === 'running')
);

export const hasError = derived(
	timbalStore,
	$store => !!$store.error
);
