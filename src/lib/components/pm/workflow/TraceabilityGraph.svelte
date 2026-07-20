<script lang="ts">
  /**
   * TraceabilityGraph - Workflow Traceability Visualization
   *
   * Visualizes traceability links between workflow steps, skills, and outputs.
   * Shows how data flows and transforms through the workflow pipeline.
   *
   * Features:
   * - Renders nodes for workflow steps, skills, and module entries
   * - Shows directed edges representing data flow and transformations
   * - Supports filtering by entity type and confidence score
   * - Interactive: click nodes for details, hover edges for mapping rules
   * - Color-coded by entity type
   */

  interface TraceabilityNode {
    id: string;
    type: 'workflow' | 'workflow_node' | 'skill' | 'module_entry';
    label: string;
    description?: string;
    x: number;
    y: number;
    color: string;
    metadata?: Record<string, unknown>;
  }

  interface TraceabilityEdge {
    id: string;
    source: string;
    target: string;
    label?: string;
    confidence: number;
    mappingRules?: Record<string, string>;
  }

  interface Props {
    nodes?: TraceabilityNode[];
    edges?: TraceabilityEdge[];
    selectedNodeId?: string | null;
    onNodeClick?: (node: TraceabilityNode) => void;
    onEdgeClick?: (edge: TraceabilityEdge) => void;
    filterTypes?: string[];
    minConfidence?: number;
  }

  let {
    nodes = [],
    edges = [],
    selectedNodeId = null,
    onNodeClick,
    onEdgeClick,
    filterTypes = [],
    minConfidence = 0.0,
  }: Props = $props();

  // Canvas dimensions
  const CANVAS_WIDTH = 800;
  const CANVAS_HEIGHT = 600;
  const NODE_WIDTH = 160;
  const NODE_HEIGHT = 60;

  // Filter nodes and edges
  const filteredNodes = $derived(
    filterTypes.length > 0
      ? nodes.filter(n => filterTypes.includes(n.type))
      : nodes
  );

  const filteredEdges = $derived(
    edges.filter(e =>
      e.confidence >= minConfidence &&
      filteredNodes.some(n => n.id === e.source) &&
      filteredNodes.some(n => n.id === e.target)
    )
  );

  // Node type colors
  const typeColors: Record<string, string> = {
    workflow: '#3b82f6',      // blue
    workflow_node: '#10b981', // green
    skill: '#f59e0b',         // amber
    module_entry: '#8b5cf6',  // purple
  };

  const typeLabels: Record<string, string> = {
    workflow: '工作流',
    workflow_node: '节点',
    skill: '技能',
    module_entry: '模块条目',
  };

  // Generate SVG path for edge
  function getEdgePath(source: TraceabilityNode, target: TraceabilityNode): string {
    const sx = source.x + NODE_WIDTH / 2;
    const sy = source.y + NODE_HEIGHT / 2;
    const tx = target.x + NODE_WIDTH / 2;
    const ty = target.y + NODE_HEIGHT / 2;

    // Curved path with control points
    const midX = (sx + tx) / 2;
    return `M ${sx} ${sy} C ${midX} ${sy}, ${midX} ${ty}, ${tx} ${ty}`;
  }

  // Calculate edge arrow marker position
  function getArrowPosition(source: TraceabilityNode, target: TraceabilityNode) {
    const angle = Math.atan2(
      target.y - source.y,
      target.x - source.x
    );
    const arrowX = target.x + NODE_WIDTH / 2 - 15 * Math.cos(angle);
    const arrowY = target.y + NODE_HEIGHT / 2 - 15 * Math.sin(angle);
    return { x: arrowX, y: arrowY, angle: angle * (180 / Math.PI) };
  }

  function handleNodeClick(node: TraceabilityNode) {
    onNodeClick?.(node);
  }

  function handleEdgeClick(edge: TraceabilityEdge) {
    onEdgeClick?.(edge);
  }

  // Auto-layout: simple grid-based positioning if positions not provided
  const layoutNodes = $derived(() => {
    if (nodes.length === 0) return [];

    // If nodes already have positions, use them
    const hasPositions = nodes.some(n => n.x !== 0 || n.y !== 0);
    if (hasPositions) return nodes;

    // Simple grid layout
    const cols = Math.ceil(Math.sqrt(nodes.length));
    return nodes.map((node, index) => ({
      ...node,
      x: (index % cols) * 220 + 50,
      y: Math.floor(index / cols) * 100 + 50,
      color: typeColors[node.type] || '#6b7280',
    }));
  });
</script>

<div class="traceability-graph bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
  <!-- Header -->
  <div class="px-4 py-3 border-b border-gray-200 bg-gray-50">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-gray-900">追溯链路图</h3>
      <div class="flex items-center gap-2 text-xs text-gray-500">
        <span>节点: {filteredNodes.length}</span>
        <span>连接: {filteredEdges.length}</span>
      </div>
    </div>

    <!-- Legend -->
    <div class="flex items-center gap-3 mt-2">
      {#each Object.entries(typeColors) as [type, color]}
        <div class="flex items-center gap-1">
          <span class="w-3 h-3 rounded-full" style="background-color: {color}"></span>
          <span class="text-xs text-gray-600">{typeLabels[type] || type}</span>
        </div>
      {/each}
    </div>
  </div>

  <!-- Graph Canvas -->
  <div class="relative" style="width: {CANVAS_WIDTH}px; height: {CANVAS_HEIGHT}px;">
    <svg
      width={CANVAS_WIDTH}
      height={CANVAS_HEIGHT}
      viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}"
      class="bg-white"
    >
      <!-- Grid background -->
      <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#f3f4f6" stroke-width="1"/>
        </pattern>
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="7"
          refX="9"
          refY="3.5"
          orient="auto"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill="#9ca3af"/>
        </marker>
      </defs>
      <rect width="100%" height="100%" fill="url(#grid)"/>

      <!-- Edges -->
      {#each filteredEdges as edge}
        {@const sourceNode = filteredNodes.find(n => n.id === edge.source)}
        {@const targetNode = filteredNodes.find(n => n.id === edge.target)}
        {#if sourceNode && targetNode}
          <g
            class="edge-group cursor-pointer hover:opacity-80"
            onclick={() => handleEdgeClick(edge)}
          >
            <path
              d={getEdgePath(sourceNode, targetNode)}
              fill="none"
              stroke="#9ca3af"
              stroke-width="2"
              marker-end="url(#arrowhead)"
              class="transition-all duration-200"
            />
            <!-- Edge label -->
            {#if edge.label}
              <text
                x={(sourceNode.x + targetNode.x) / 2 + NODE_WIDTH / 2}
                y={(sourceNode.y + targetNode.y) / 2 + NODE_HEIGHT / 2 - 5}
                text-anchor="middle"
                class="text-xs fill-gray-500"
                font-size="11"
              >
                {edge.label}
              </text>
            {/if}
            <!-- Confidence badge -->
            <text
              x={(sourceNode.x + targetNode.x) / 2 + NODE_WIDTH / 2}
              y={(sourceNode.y + targetNode.y) / 2 + NODE_HEIGHT / 2 + 12}
              text-anchor="middle"
              class="text-xs fill-gray-400"
              font-size="10"
            >
              {(edge.confidence * 100).toFixed(0)}%
            </text>
          </g>
        {/if}
      {/each}

      <!-- Nodes -->
      {#each filteredNodes as node}
        <g
          class="node-group cursor-pointer transition-all duration-200 hover:opacity-90"
          onclick={() => handleNodeClick(node)}
          transform="translate({node.x}, {node.y})"
        >
          <!-- Node rectangle -->
          <rect
            width={NODE_WIDTH}
            height={NODE_HEIGHT}
            rx="8"
            ry="8"
            fill={node.color || typeColors[node.type] || '#6b7280'}
            stroke={selectedNodeId === node.id ? '#1f2937' : 'transparent'}
            stroke-width={selectedNodeId === node.id ? 3 : 0}
            class="transition-all duration-200"
          />
          <!-- Node label -->
          <text
            x={NODE_WIDTH / 2}
            y={NODE_HEIGHT / 2 - 5}
            text-anchor="middle"
            class="text-sm font-medium fill-white"
            font-size="12"
          >
            {node.label}
          </text>
          <!-- Node type -->
          <text
            x={NODE_WIDTH / 2}
            y={NODE_HEIGHT / 2 + 10}
            text-anchor="middle"
            class="text-xs fill-white/80"
            font-size="10"
          >
            {typeLabels[node.type] || node.type}
          </text>
        </g>
      {/each}
    </svg>

    <!-- Empty state -->
    {#if filteredNodes.length === 0}
      <div class="absolute inset-0 flex items-center justify-center">
        <div class="text-center">
          <svg class="mx-auto h-12 w-12 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
          </svg>
          <p class="mt-2 text-sm text-gray-500">暂无追溯链路数据</p>
          <p class="text-xs text-gray-400">执行工作流后将自动生成</p>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .traceability-graph {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }
</style>
