import { writable, derived } from 'svelte/store';
import type { ArchitectureState, Module, Function, Parameter } from '$lib/models/pm/architecture';
import * as api from '$lib/apis/pm/architecture';

function createArchitectureStore() {
  const { subscribe, set, update } = writable<ArchitectureState>({
    modules: [],
    functions: [],
    parameters: [],
    loading: false,
    error: null
  });

  return {
    subscribe,
    
    // Load all data
    async loadAll() {
      update(state => ({ ...state, loading: true, error: null }));
      try {
        const [modules, functions, parameters] = await Promise.all([
          api.getModules(),
          api.getFunctions(),
          api.getParameters()
        ]);
        update(state => ({
          ...state,
          modules,
          functions,
          parameters,
          loading: false
        }));
      } catch (error) {
        update(state => ({
          ...state,
          loading: false,
          error: error instanceof Error ? error.message : 'Unknown error'
        }));
      }
    },

    // Module operations
    async createModule(data: Partial<Module>) {
      try {
        const module = await api.createModule(data);
        update(state => ({
          ...state,
          modules: [...state.modules, module]
        }));
        return module;
      } catch (error) {
        update(state => ({
          ...state,
          error: error instanceof Error ? error.message : 'Failed to create module'
        }));
        throw error;
      }
    },

    async updateModule(id: string, data: Partial<Module>) {
      try {
        const module = await api.updateModule(id, data);
        update(state => ({
          ...state,
          modules: state.modules.map(m => m.id === id ? module : m)
        }));
        return module;
      } catch (error) {
        update(state => ({
          ...state,
          error: error instanceof Error ? error.message : 'Failed to update module'
        }));
        throw error;
      }
    },

    async deleteModule(id: string) {
      try {
        await api.deleteModule(id);
        update(state => ({
          ...state,
          modules: state.modules.filter(m => m.id !== id)
        }));
      } catch (error) {
        update(state => ({
          ...state,
          error: error instanceof Error ? error.message : 'Failed to delete module'
        }));
        throw error;
      }
    },

    // Function operations
    async createFunction(data: Partial<Function>) {
      try {
        const func = await api.createFunction(data);
        update(state => ({
          ...state,
          functions: [...state.functions, func]
        }));
        return func;
      } catch (error) {
        update(state => ({
          ...state,
          error: error instanceof Error ? error.message : 'Failed to create function'
        }));
        throw error;
      }
    },

    async updateFunction(id: string, data: Partial<Function>) {
      try {
        const func = await api.updateFunction(id, data);
        update(state => ({
          ...state,
          functions: state.functions.map(f => f.id === id ? func : f)
        }));
        return func;
      } catch (error) {
        update(state => ({
          ...state,
          error: error instanceof Error ? error.message : 'Failed to update function'
        }));
        throw error;
      }
    },

    async deleteFunction(id: string) {
      try {
        await api.deleteFunction(id);
        update(state => ({
          ...state,
          functions: state.functions.filter(f => f.id !== id)
        }));
      } catch (error) {
        update(state => ({
          ...state,
          error: error instanceof Error ? error.message : 'Failed to delete function'
        }));
        throw error;
      }
    },

    // Parameter operations
    async createParameter(data: Partial<Parameter>) {
      try {
        const parameter = await api.createParameter(data);
        update(state => ({
          ...state,
          parameters: [...state.parameters, parameter]
        }));
        return parameter;
      } catch (error) {
        update(state => ({
          ...state,
          error: error instanceof Error ? error.message : 'Failed to create parameter'
        }));
        throw error;
      }
    },

    async updateParameter(id: string, data: Partial<Parameter>) {
      try {
        const parameter = await api.updateParameter(id, data);
        update(state => ({
          ...state,
          parameters: state.parameters.map(p => p.id === id ? parameter : p)
        }));
        return parameter;
      } catch (error) {
        update(state => ({
          ...state,
          error: error instanceof Error ? error.message : 'Failed to update parameter'
        }));
        throw error;
      }
    },

    async deleteParameter(id: string) {
      try {
        await api.deleteParameter(id);
        update(state => ({
          ...state,
          parameters: state.parameters.filter(p => p.id !== id)
        }));
      } catch (error) {
        update(state => ({
          ...state,
          error: error instanceof Error ? error.message : 'Failed to delete parameter'
        }));
        throw error;
      }
    },

    // Reset error
    clearError() {
      update(state => ({ ...state, error: null }));
    }
  };
}

export const architectureStore = createArchitectureStore();

// Derived stores for filtered data
export const activeModules = derived(
  architectureStore,
  $store => $store.modules.filter((m: Module) => !m.is_deleted)
);

export const activeFunctions = derived(
  architectureStore,
  $store => $store.functions.filter(f => !f.is_deleted)
);

export const activeParameters = derived(
  architectureStore,
  $store => $store.parameters.filter(p => !p.is_deleted)
);

export const isLoading = derived(
  architectureStore,
  $store => $store.loading
);

export const hasError = derived(
  architectureStore,
  $store => $store.error
);
