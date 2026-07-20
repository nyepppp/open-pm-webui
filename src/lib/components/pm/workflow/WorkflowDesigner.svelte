<script lang="ts">
  import { onMount } from 'svelte';
  import WorkflowNodeSidebar from './WorkflowNodeSidebar.svelte';

  // Types
  interface Node {
    id: string;
    type: string;
    name: string;
    x: number;
    y: number;
    config?: Record<string, any>;
  }

  interface Edge {
    id: string;
    sourceNodeId: string;
    targetNodeId: string;
    dataMappingRules?: Record<string, string>;
    label?: string;
  }

  interface Workflow {
    id: string;
    name: string;
    description?: string;
    status?: string;
    created_at?: number;
    nodes: Node[];
    edges: Edge[];
  }

  // Props
  export let workflow: Workflow | null = null;
  export let onSave: (workflow: Workflow) => void = () => {};
  export let onExecute: (workflowId: string, inputData: any) => void = () => {};

  // State
  let nodes: Node[] = workflow?.nodes || [];
  let edges: Edge[] = workflow?.edges || [];
  let selectedNode: Node | null = null;
  let isDragging = false;
  let dragOffset = { x: 0, y: 0 };
  let draggedNode: Node | null = null;
  let isConnecting = false;
  let connectionStart: Node | null = null;
  let mousePosition = { x: 0, y: 0 };
  let sidebarCollapsed = false;
  let draggedTemplate: any = null;
  let isDraggingFromSidebar = false;

  // Node types available in the palette
  const nodeTypes = [
    { type: 'start', label: 'Start', color: '#4CAF50' },
    { type: 'end', label: 'End', color: '#F44336' },
    { type: 'agent_call', label: 'Agent Call', color: '#2196F3' },
    { type: 'data_transform', label: 'Data Transform', color: '#FF9800' },
    { type: 'condition', label: 'Condition', color: '#9C27B0' },
    { type: 'loop', label: 'Loop', color: '#795548' },
    { type: 'parallel_merge', label: 'Parallel Merge', color: '#607D8B' },
    { type: 'custom', label: 'Custom', color: '#757575' },
  ];

  function addNode(type: string, x: number, y: number, config?: Record<string, any>) {
    const newNode: Node = {
      id: `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type,
      name: type,
      x,
      y,
      config: config || {},
    };
    nodes = [...nodes, newNode];
    updateWorkflow();
    return newNode;
  }

  function removeNode(nodeId: string) {
    nodes = nodes.filter((n) => n.id !== nodeId);
    edges = edges.filter((e) => e.sourceNodeId !== nodeId && e.targetNodeId !== nodeId);
    selectedNode = null;
    updateWorkflow();
  }

  function addEdge(sourceNodeId: string, targetNodeId: string) {
    // Check if edge already exists
    const existing = edges.find(
      e => e.sourceNodeId === sourceNodeId && e.targetNodeId === targetNodeId
    );
    if (existing) return;

    const newEdge: Edge = {
      id: `edge-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      sourceNodeId,
      targetNodeId,
      dataMappingRules: {},
    };
    edges = [...edges, newEdge];
    updateWorkflow();
  }

  function removeEdge(edgeId: string) {
    edges = edges.filter((e) => e.id !== edgeId);
    updateWorkflow();
  }

  function updateWorkflow() {
    if (workflow) {
      workflow = { ...workflow, nodes, edges };
    }
  }

  function handleNodeMouseDown(event: MouseEvent, node: Node) {
    if (event.button === 0) {
      // Left click - start dragging
      isDragging = true;
      draggedNode = node;
      dragOffset = { x: event.clientX - node.x, y: event.clientY - node.y };
      selectedNode = node;
    }
  }

  function handleNodeMouseUp(event: MouseEvent, node: Node) {
    if (isConnecting && connectionStart && connectionStart.id !== node.id) {
      // Complete connection
      addEdge(connectionStart.id, node.id);
      isConnecting = false;
      connectionStart = null;
    }
    isDragging = false;
    draggedNode = null;
  }

  function handleCanvasMouseMove(event: MouseEvent) {
    mousePosition = { x: event.clientX, y: event.clientY };

    if (isDragging && draggedNode) {
      draggedNode.x = event.clientX - dragOffset.x;
      draggedNode.y = event.clientY - dragOffset.y;
      nodes = [...nodes]; // Trigger reactivity
    }
  }

  function handleCanvasMouseUp() {
    isDragging = false;
    draggedNode = null;
    isConnecting = false;
    connectionStart = null;
  }

  function handleCanvasClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      selectedNode = null;
    }
  }

  function startConnection(node: Node) {
    isConnecting = true;
    connectionStart = node;
  }

  function getNodePosition(nodeId: string) {
    const node = nodes.find((n) => n.id === nodeId);
    return node ? { x: node.x, y: node.y } : { x: 0, y: 0 };
  }

  function getEdgePath(edge: Edge) {
    const source = getNodePosition(edge.sourceNodeId);
    const target = getNodePosition(edge.targetNodeId);
    return `M ${source.x} ${source.y} L ${target.x} ${target.y}`;
  }

  function getNodeColor(type: string) {
    const nodeType = nodeTypes.find((t) => t.type === type);
    return nodeType?.color || '#757575';
  }

  function handleSave() {
    // Always save nodes and edges, even if workflow is null (new workflow scenario)
    const now = Date.now();
    const updatedWorkflow = {
      ...workflow,
      id: workflow?.id || `wf_${now}`,
      name: workflow?.name || 'New Workflow',
      status: workflow?.status || 'draft',
      nodes: nodes || [],
      edges: edges || [],
      created_at: workflow?.created_at || now,
      updated_at: now
    };
    onSave(updatedWorkflow);
  }

  function handleExecute() {
    if (workflow) {
      onExecute(workflow.id, {});
    }
  }

  // Export/Import functions
  function handleExportJSON() {
    const exportData = {
      version: '2.0',
      exported_at: new Date().toISOString(),
      name: workflow?.name || 'Workflow',
      description: workflow?.description || '',
      nodes: nodes.map(n => ({
        id: n.id,
        type: n.type,
        name: n.name,
        position: { x: n.x, y: n.y },
        config: n.config || {}
      })),
      edges: edges.map(e => ({
        id: e.id,
        source_node_id: e.sourceNodeId,
        target_node_id: e.targetNodeId
      }))
    };
    const jsonString = JSON.stringify(exportData, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${(workflow?.name || 'workflow').replace(/\s+/g, '_')}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  function handleExportBPMN() {
    // Import the BPMN export utility
    import('$lib/components/workflow/utils/exportImport').then(({ exportToBPMN }) => {
      const exportData = {
        name: workflow?.name || 'Workflow',
        description: workflow?.description || '',
        nodes: nodes.map(n => ({
          id: n.id,
          type: n.type,
          name: n.name,
          position: { x: n.x, y: n.y },
          config: n.config || {}
        })),
        edges: edges.map(e => ({
          id: e.id,
          source_node_id: e.sourceNodeId,
          target_node_id: e.targetNodeId
        }))
      };
      const bpmnXml = exportToBPMN(exportData);
      const blob = new Blob([bpmnXml], { type: 'application/xml' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${(workflow?.name || 'workflow').replace(/\s+/g, '_')}.bpmn`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    });
  }

  function handleImportJSON(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        const data = JSON.parse(content);
        
        // Update nodes and edges from imported data
        if (data.nodes && Array.isArray(data.nodes)) {
          nodes = data.nodes.map((n: any) => ({
            id: n.id || `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            type: n.type || 'custom',
            name: n.name || n.type || 'Node',
            x: n.position?.x || n.x || 0,
            y: n.position?.y || n.y || 0,
            config: n.config || {}
          }));
        }
        
        if (data.edges && Array.isArray(data.edges)) {
          edges = data.edges.map((e: any) => ({
            id: e.id || `edge-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            sourceNodeId: e.source_node_id || e.source,
            targetNodeId: e.target_node_id || e.target,
            dataMappingRules: e.data_mapping || e.dataMappingRules || {}
          }));
        }
        
        updateWorkflow();
      } catch (err) {
        console.error('Failed to import JSON:', err);
        alert('导入失败：无效的JSON文件');
      }
    };
    reader.readAsText(file);
    input.value = ''; // Reset input
  }

  function handleImportBPMN(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const bpmnXml = e.target?.result as string;
        
        // Import the BPMN import utility
        import('$lib/components/workflow/utils/exportImport').then(({ importFromBPMN }) => {
          const data = importFromBPMN(bpmnXml);
          
          // Update nodes and edges from imported data
          if (data.nodes && Array.isArray(data.nodes)) {
            nodes = data.nodes.map((n: any) => ({
              id: n.id || `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              type: n.type || 'custom',
              name: n.name || n.type || 'Node',
              x: n.position?.x || n.x || 0,
              y: n.position?.y || n.y || 0,
              config: n.config || {}
            }));
          }
          
          if (data.edges && Array.isArray(data.edges)) {
            edges = data.edges.map((e: any) => ({
              id: e.id || `edge-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              sourceNodeId: e.source_node_id || e.source,
              targetNodeId: e.target_node_id || e.target,
              dataMappingRules: e.data_mapping || e.dataMappingRules || {}
            }));
          }
          
          updateWorkflow();
        });
      } catch (err) {
        console.error('Failed to import BPMN:', err);
        alert('导入失败：无效的BPMN文件');
      }
    };
    reader.readAsText(file);
    input.value = ''; // Reset input
  }

  // Drag and drop from sidebar
  function handleCanvasDragOver(event: DragEvent) {
    event.preventDefault();
    event.dataTransfer!.dropEffect = 'copy';
  }

  function handleCanvasDrop(event: DragEvent) {
    event.preventDefault();
    const data = event.dataTransfer?.getData('application/json');
    if (!data) return;

    try {
      const template = JSON.parse(data);
      const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;

      // Create node from template
      addNode(template.type, x, y, template.config);
    } catch (e) {
      console.error('Failed to parse dropped node:', e);
    }
  }

  // Keyboard shortcuts
  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Delete' && selectedNode) {
      removeNode(selectedNode.id);
    }
  }

  onMount(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  });
</script>

<div class="workflow-designer flex h-full bg-gray-50 dark:bg-gray-900">
  <!-- Node Sidebar -->
  <WorkflowNodeSidebar
    collapsed={sidebarCollapsed}
    onToggleCollapse={() => sidebarCollapsed = !sidebarCollapsed}
    on:nodeSelect={(e) => {
      // Optional: handle node selection from sidebar
      console.log('Selected node:', e.detail);
    }}
  />

  <!-- Main Canvas Area -->
  <div class="flex-1 flex flex-col min-w-0">
    <!-- Toolbar -->
    <div class="flex items-center gap-2 px-4 py-3 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div class="flex items-center gap-2">
        <h1 class="text-lg font-semibold text-gray-900 dark:text-white">
          {workflow?.name || 'Untitled Workflow'}
        </h1>
      </div>

      <div class="flex-1"></div>

      <div class="flex items-center gap-2">
        <div class="flex items-center gap-1 mr-2">
          <button
            class="px-3 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-lg transition-colors"
            on:click={handleExportJSON}
            title="导出JSON"
          >
            <span class="flex items-center gap-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              JSON
            </span>
          </button>
          <button
            class="px-3 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-lg transition-colors"
            on:click={handleExportBPMN}
            title="导出BPMN"
          >
            <span class="flex items-center gap-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              BPMN
            </span>
          </button>
          <label class="px-3 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-lg transition-colors cursor-pointer">
            <span class="flex items-center gap-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              导入JSON
            </span>
            <input type="file" accept=".json" class="hidden" on:change={handleImportJSON} />
          </label>
          <label class="px-3 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-lg transition-colors cursor-pointer">
            <span class="flex items-center gap-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              导入BPMN
            </span>
            <input type="file" accept=".bpmn,.xml" class="hidden" on:change={handleImportBPMN} />
          </label>
        </div>
        
        <div class="w-px h-6 bg-gray-300 dark:bg-gray-600 mx-1"></div>
        
        <button
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          on:click={handleSave}
        >
          保存
        </button>
        <button
          class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors"
          on:click={handleExecute}
        >
          执行
        </button>
        {#if selectedNode}
          <button
            class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors"
            on:click={() => selectedNode && removeNode(selectedNode.id)}
          >
            删除节点
          </button>
        {/if}
      </div>
    </div>

    <!-- Canvas -->
    <div
      class="flex-1 relative bg-white dark:bg-gray-900 overflow-hidden"
      on:mousemove={handleCanvasMouseMove}
      on:mouseup={handleCanvasMouseUp}
      on:click={handleCanvasClick}
      on:dragover={handleCanvasDragOver}
      on:drop={handleCanvasDrop}
    >
      <!-- Grid background -->
      <div class="absolute inset-0 opacity-30" style="background-image: radial-gradient(circle, #e5e7eb 1px, transparent 1px); background-size: 20px 20px;"></div>

      <!-- Edges -->
      <svg class="absolute inset-0 w-full h-full pointer-events-none">
        {#each edges as edge}
          <path
            d={getEdgePath(edge)}
            stroke="#6b7280"
            stroke-width="2"
            fill="none"
            marker-end="url(#arrowhead)"
            class="pointer-events-auto cursor-pointer hover:stroke-blue-500 transition-colors"
            on:click={() => removeEdge(edge.id)}
          />
        {/each}
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#6b7280" />
          </marker>
        </defs>
      </svg>

      <!-- Nodes -->
      {#each nodes as node}
        <div
          class="absolute w-32 p-3 rounded-lg shadow-md cursor-grab select-none transition-shadow hover:shadow-lg {selectedNode?.id === node.id ? 'ring-2 ring-blue-500 ring-offset-2' : ''}"
          style="left: {node.x}px; top: {node.y}px; background-color: {getNodeColor(node.type)};"
          on:mousedown={(e) => handleNodeMouseDown(e, node)}
          on:mouseup={(e) => handleNodeMouseUp(e, node)}
        >
          <div class="text-white font-semibold text-sm">{node.name}</div>
          <div class="text-white/80 text-xs mt-1">{node.type}</div>
          {#if selectedNode?.id === node.id}
            <div class="mt-2 pt-2 border-t border-white/20">
              <button
                class="text-xs text-white/90 hover:text-white underline"
                on:click={() => startConnection(node)}
              >
                连接
              </button>
            </div>
          {/if}
        </div>
      {/each}

      <!-- Empty state -->
      {#if nodes.length === 0}
        <div class="absolute inset-0 flex items-center justify-center">
          <div class="text-center">
            <svg class="mx-auto h-12 w-12 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <p class="mt-2 text-sm text-gray-500">从左侧拖拽节点到此处</p>
            <p class="text-xs text-gray-400">或点击节点直接添加</p>
          </div>
        </div>
      {/if}
    </div>
  </div>

  <!-- Node Config Panel -->
  {#if selectedNode}
    <div class="w-80 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 p-4 overflow-y-auto">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">节点配置</h3>

      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">名称</label>
          <input
            type="text"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            bind:value={selectedNode.name}
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">类型</label>
          <select
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            bind:value={selectedNode.type}
          >
            {#each nodeTypes as type}
              <option value={type.type}>{type.label}</option>
            {/each}
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">配置 (JSON)</label>
          <textarea
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono"
            rows="5"
            value={JSON.stringify(selectedNode.config || {}, null, 2)}
            on:change={(e) => {
              try {
                selectedNode!.config = JSON.parse(e.currentTarget.value);
              } catch (err) {
                // Invalid JSON, ignore
              }
            }}
          />
        </div>

        <div class="pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            class="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
            on:click={() => {
              // Save config changes
              updateWorkflow();
            }}
          >
            应用配置
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>
