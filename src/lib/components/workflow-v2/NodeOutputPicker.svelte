<script lang="ts">
  import type { WorkflowNode, WorkflowEdge, NodeOutputSchema, NodeType } from './types';
  import { NODE_CATEGORIES } from './types';

  // ===== Props =====
  interface Props {
    currentNode: WorkflowNode | null;
    nodes: WorkflowNode[];
    edges: WorkflowEdge[];
    onInsert?: (variableRef: string) => void;
    onClose?: () => void;
  }

  let { currentNode, nodes, edges, onInsert, onClose }: Props = $props();

  // ===== State =====
  let searchQuery = $state('');

  // ===== Derived =====
  // Reverse BFS to find all upstream nodes of currentNode
  const upstreamNodes = $derived(() => {
    if (!currentNode) return [];
    return findUpstreamNodes(currentNode.id, nodes, edges);
  });

  // Filter by search query
  const filteredUpstream = $derived(() => {
    const upstream = upstreamNodes();
    if (!searchQuery.trim()) return upstream;
    const q = searchQuery.toLowerCase();
    return upstream.filter(n =>
      n.name.toLowerCase().includes(q) ||
      n.id.toLowerCase().includes(q) ||
      n.type.toLowerCase().includes(q)
    );
  });

  // ===== Helpers =====
  function findUpstreamNodes(
    currentNodeId: string,
    nodes: WorkflowNode[],
    edges: WorkflowEdge[]
  ): WorkflowNode[] {
    const visited = new Set<string>();
    const queue = [currentNodeId];
    const upstream: WorkflowNode[] = [];
    let depth = 0;
    const MAX_DEPTH = 10;

    while (queue.length > 0 && depth < MAX_DEPTH) {
      const current = queue.shift()!;
      if (visited.has(current)) continue;
      visited.add(current);

      // Find all edges pointing to current node
      const incomingEdges = edges.filter(e => e.targetNodeId === current);
      for (const edge of incomingEdges) {
        const sourceNode = nodes.find(n => n.id === edge.sourceNodeId);
        if (sourceNode && !visited.has(sourceNode.id)) {
          upstream.push(sourceNode);
          queue.push(sourceNode.id);
        }
      }
      depth++;
    }
    return upstream;
  }

  // Get outputs schema for a node by looking up its template
  function getNodeOutputs(node: WorkflowNode): NodeOutputSchema[] {
    // For dynamic-field nodes, derive from config.output_variable
    if (node.type === 'template' || node.type === 'parameter_extractor' || node.type === 'code') {
      const varName = (node.config?.output_variable as string) || 'result';
      const type = node.type === 'code' ? 'object' : 'string';
      return [{ name: varName, type, description: '动态输出变量' }];
    }

    // For start node, expose $input
    if (node.type === 'start') {
      return [{ name: 'input', type: 'string', description: '工作流输入参数' }];
    }

    // Lookup in NODE_CATEGORIES by type
    for (const category of NODE_CATEGORIES) {
      for (const template of category.nodes) {
        if (template.type === node.type) {
          return template.outputs || [];
        }
      }
    }
    return [];
  }

  function handleInsert(nodeId: string, fieldName: string) {
    const ref = `${nodeId}.${fieldName}`;
    onInsert?.(ref);
  }

  function handleClose() {
    onClose?.();
  }
</script>

<div class="node-output-picker">
  <div class="picker-header">
    <h4 class="picker-title">插入变量</h4>
    <button class="close-btn" onclick={handleClose} title="关闭">×</button>
  </div>

  <div class="picker-search">
    <input
      type="text"
      class="search-input"
      placeholder="搜索节点或字段..."
      bind:value={searchQuery}
    />
  </div>

  <div class="picker-list">
    {#if filteredUpstream().length === 0}
      <div class="empty-state">
        {#if !currentNode}
          <p>请先选择一个节点</p>
        {:else if upstreamNodes().length === 0}
          <p>当前节点没有上游节点</p>
          <p class="hint">请先从上游节点连线到当前节点</p>
        {:else}
          <p>没有匹配的节点</p>
        {/if}
      </div>
    {:else}
      {#each filteredUpstream() as node (node.id)}
        {@const outputs = getNodeOutputs(node)}
        {#if outputs.length > 0}
          <div class="node-group">
            <div class="node-group-header">
              <span class="node-name">{node.name}</span>
              <span class="node-type-badge">{node.type}</span>
            </div>
            <div class="node-fields">
              {#each outputs as field (field.name)}
                <button
                  class="field-btn"
                  onclick={() => handleInsert(node.id, field.name)}
                  title={field.description || ''}
                >
                  <span class="field-name">{field.name}</span>
                  <span class="field-type">{field.type}</span>
                </button>
              {/each}
            </div>
          </div>
        {/if}
      {/each}
    {/if}
  </div>

  <div class="picker-footer">
    <span class="hint">点击字段插入 <code>{'{'}{'{node_id.field}{'}'}'}</code></span>
  </div>
</div>

<style>
  .node-output-picker {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    margin-top: 4px;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    z-index: 100;
    max-height: 400px;
    display: flex;
    flex-direction: column;
  }

  .picker-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    border-bottom: 1px solid #f3f4f6;
  }

  .picker-title {
    font-size: 13px;
    font-weight: 600;
    color: #111827;
    margin: 0;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 18px;
    line-height: 1;
    color: #6b7280;
    cursor: pointer;
    padding: 2px 6px;
    border-radius: 4px;
  }

  .close-btn:hover {
    background: #f3f4f6;
    color: #111827;
  }

  .picker-search {
    padding: 8px 12px;
    border-bottom: 1px solid #f3f4f6;
  }

  .search-input {
    width: 100%;
    padding: 6px 10px;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    font-size: 13px;
    outline: none;
    box-sizing: border-box;
  }

  .search-input:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
  }

  .picker-list {
    flex: 1;
    overflow-y: auto;
    padding: 4px 0;
  }

  .empty-state {
    padding: 24px 12px;
    text-align: center;
    color: #6b7280;
    font-size: 13px;
  }

  .empty-state .hint {
    font-size: 11px;
    color: #9ca3af;
    margin-top: 4px;
  }

  .node-group {
    margin-bottom: 4px;
  }

  .node-group-header {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: #f9fafb;
  }

  .node-name {
    font-size: 12px;
    font-weight: 600;
    color: #374151;
  }

  .node-type-badge {
    font-size: 10px;
    padding: 1px 6px;
    background: #e5e7eb;
    border-radius: 3px;
    color: #6b7280;
  }

  .node-fields {
    padding: 2px 0;
  }

  .field-btn {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 6px 16px;
    background: none;
    border: none;
    cursor: pointer;
    text-align: left;
    transition: background 0.15s;
  }

  .field-btn:hover {
    background: #eff6ff;
  }

  .field-name {
    font-size: 12px;
    color: #1f2937;
    font-family: 'Monaco', 'Menlo', monospace;
  }

  .field-type {
    font-size: 10px;
    color: #9ca3af;
    padding: 1px 5px;
    background: #f3f4f6;
    border-radius: 3px;
  }

  .picker-footer {
    padding: 6px 12px;
    border-top: 1px solid #f3f4f6;
    background: #f9fafb;
  }

  .picker-footer .hint {
    font-size: 10px;
    color: #9ca3af;
  }

  .picker-footer code {
    font-family: 'Monaco', 'Menlo', monospace;
    background: #e5e7eb;
    padding: 1px 4px;
    border-radius: 2px;
    font-size: 10px;
  }

  :global(.dark) .node-output-picker {
    background: #1f2937;
    border-color: #374151;
  }

  :global(.dark) .picker-header {
    border-color: #374151;
  }

  :global(.dark) .picker-title {
    color: #f9fafb;
  }

  :global(.dark) .close-btn {
    color: #9ca3af;
  }

  :global(.dark) .close-btn:hover {
    background: #374151;
    color: #f9fafb;
  }

  :global(.dark) .picker-search {
    border-color: #374151;
  }

  :global(.dark) .search-input {
    background: #111827;
    border-color: #374151;
    color: #f9fafb;
  }

  :global(.dark) .node-group-header {
    background: #111827;
  }

  :global(.dark) .node-name {
    color: #e5e7eb;
  }

  :global(.dark) .node-type-badge {
    background: #374151;
    color: #9ca3af;
  }

  :global(.dark) .field-btn:hover {
    background: #1e3a5f;
  }

  :global(.dark) .field-name {
    color: #f9fafb;
  }

  :global(.dark) .field-type {
    background: #374151;
    color: #9ca3af;
  }

  :global(.dark) .picker-footer {
    border-color: #374151;
    background: #111827;
  }

  :global(.dark) .picker-footer code {
    background: #374151;
  }
</style>
