import { writable, derived, get } from 'svelte/store';
import type { CanvasState, CanvasNode, Connection, Selection, NodeGroup, ViewState, GridState, HistoryEntry } from '$lib/types/canvas';

// Initial state
const initialState: CanvasState = {
  id: '',
  projectId: '',
  name: 'Untitled Canvas',
  view: {
    zoom: 1,
    panX: 0,
    panY: 0
  },
  grid: {
    enabled: true,
    size: 20
  },
  nodes: new Map(),
  connections: new Map(),
  selection: {
    nodeIds: new Set(),
    connectionIds: new Set(),
    primaryNodeId: null
  },
  groups: new Map()
};

// Create the store
function createCanvasStore() {
  const { subscribe, set, update } = writable<CanvasState>({ ...initialState });
  
  // History for undo/redo
  let history: HistoryEntry[] = [];
  let historyIndex = -1;
  const MAX_HISTORY = 100;

  return {
    subscribe,
    
    // View operations
    setView: (view: Partial<ViewState>) => {
      update(state => ({
        ...state,
        view: { ...state.view, ...view }
      }));
    },
    
    resetView: () => {
      update(state => ({
        ...state,
        view: { zoom: 1, panX: 0, panY: 0 }
      }));
    },
    
    // Grid operations
    toggleGrid: () => {
      update(state => ({
        ...state,
        grid: { ...state.grid, enabled: !state.grid.enabled }
      }));
    },
    
    setGridSize: (size: number) => {
      update(state => ({
        ...state,
        grid: { ...state.grid, size }
      }));
    },
    
    // Node operations
    addNode: (node: CanvasNode) => {
      update(state => {
        const newNodes = new Map(state.nodes);
        newNodes.set(node.id, node);
        return { ...state, nodes: newNodes };
      });
    },
    
    updateNode: (id: string, updates: Partial<CanvasNode>) => {
      update(state => {
        const node = state.nodes.get(id);
        if (!node) return state;
        const newNodes = new Map(state.nodes);
        newNodes.set(id, { ...node, ...updates });
        return { ...state, nodes: newNodes };
      });
    },
    
    deleteNode: (id: string) => {
      update(state => {
        const newNodes = new Map(state.nodes);
        newNodes.delete(id);
        
        // Remove connections associated with this node
        const newConnections = new Map(state.connections);
        state.connections.forEach((conn, connId) => {
          if (conn.sourceNodeId === id || conn.targetNodeId === id) {
            newConnections.delete(connId);
          }
        });
        
        // Remove from selection
        const newSelection = { ...state.selection };
        newSelection.nodeIds = new Set(state.selection.nodeIds);
        newSelection.nodeIds.delete(id);
        
        return { 
          ...state, 
          nodes: newNodes, 
          connections: newConnections,
          selection: newSelection
        };
      });
    },
    
    // Connection operations
    addConnection: (connection: Connection) => {
      update(state => {
        const newConnections = new Map(state.connections);
        newConnections.set(connection.id, connection);
        return { ...state, connections: newConnections };
      });
    },
    
    deleteConnection: (id: string) => {
      update(state => {
        const newConnections = new Map(state.connections);
        newConnections.delete(id);
        return { ...state, connections: newConnections };
      });
    },
    
    // Selection operations
    selectNode: (id: string, append = false) => {
      update(state => {
        const newSelection = { ...state.selection };
        if (append) {
          newSelection.nodeIds = new Set(state.selection.nodeIds);
          newSelection.nodeIds.add(id);
        } else {
          newSelection.nodeIds = new Set([id]);
          newSelection.connectionIds = new Set();
        }
        newSelection.primaryNodeId = id;
        return { ...state, selection: newSelection };
      });
    },
    selectNodes: (ids: string[]) => {
      update(state => {
        const newSelection = { 
          ...state.selection,
          nodeIds: new Set(ids),
          connectionIds: new Set<string>(),
          primaryNodeId: ids[0] || null
        };
        return { ...state, selection: newSelection };
      });
    },
    
    clearSelection: () => {
      update(state => ({
        ...state,
        selection: {
          nodeIds: new Set(),
          connectionIds: new Set(),
          primaryNodeId: null
        }
      }));
    },
    
    // Group operations
    createGroup: (group: NodeGroup) => {
      update(state => {
        const newGroups = new Map(state.groups);
        newGroups.set(group.id, group);
        return { ...state, groups: newGroups };
      });
    },
    
    deleteGroup: (id: string) => {
      update(state => {
        const newGroups = new Map(state.groups);
        newGroups.delete(id);
        return { ...state, groups: newGroups };
      });
    },
    
    // History operations
    addHistoryEntry: (entry: HistoryEntry) => {
      // Remove future history if we're not at the end
      if (historyIndex < history.length - 1) {
        history = history.slice(0, historyIndex + 1);
      }
      
      history.push(entry);
      
      // Limit history size
      if (history.length > MAX_HISTORY) {
        history = history.slice(-MAX_HISTORY);
      }
      
      historyIndex = history.length - 1;
    },
    
    undo: () => {
      if (historyIndex < 0) return;
      
      const entry = history[historyIndex];
      // Apply the undo logic based on the operation type
      // This would restore the previous state
      historyIndex--;
    },
    
    redo: () => {
      if (historyIndex >= history.length - 1) return;
      
      historyIndex++;
      const entry = history[historyIndex];
      // Apply the redo logic based on the operation type
      // This would apply the new state
    },
    
    canUndo: () => historyIndex >= 0,
    canRedo: () => historyIndex < history.length - 1,
    
    // Import/Export
    exportToJSON: () => {
      const state = get({ subscribe });
      return JSON.stringify({
        ...state,
        nodes: Array.from(state.nodes.entries()),
        connections: Array.from(state.connections.entries()),
        groups: Array.from(state.groups.entries())
      });
    },
    
    importFromJSON: (json: string) => {
      const data = JSON.parse(json);
      const state: CanvasState = {
        ...data,
        nodes: new Map(data.nodes),
        connections: new Map(data.connections),
        groups: new Map(data.groups)
      };
      set(state);
    },
    
    // Reset
    reset: () => {
      set({ ...initialState });
      history = [];
      historyIndex = -1;
    }
  };
}

export const canvasStore = createCanvasStore();
