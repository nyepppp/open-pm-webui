<script lang="ts">
  /**
   * ArchitectureDiagram - Fixed Product Architecture Diagram
   *
   * Fixes existing rendering and interaction issues in the architecture diagram.
   * Shows module relationships and agent capabilities with proper interactivity.
   *
   * Features:
   * - Renders module nodes and skill nodes
   * - Shows data flow connections between modules
   * - Interactive: click nodes for details, hover connections for descriptions
   * - Skill nodes display definition on click
   * - Proper error handling and loading states
   */

  import { onMount } from 'svelte';

  interface ArchitectureNode {
    id: string;
    type: 'module' | 'skill' | 'data_flow';
    label: string;
    description: string;
    x: number;
    y: number;
    connections: string[];
    metadata?: Record<string, unknown>;
  }

  interface ArchitectureConnection {
    id: string;
    source: string;
    target: string;
    label: string;
    description: string;
  }

  interface Props {
    nodes?: ArchitectureNode[];
    connections?: ArchitectureConnection[];
    onNodeClick?: (node: ArchitectureNode) => void;
    onConnectionHover?: (connection: ArchitectureConnection | null) => void;
    loading?: boolean;
    error?: string | null;
  }

  let {
    nodes = [],
    connections = [],
    onNodeClick,
    onConnectionHover,
    loading = false,
    error = null,
  }: Props = $props();

  let hoveredConnection: ArchitectureConnection | null = $state(null);
  let selectedNodeId: string | null = $state(null);
  let tooltipPosition = $state({ x: 0, y: 0 });

  const NODE_WIDTH = 140;
  const NODE_HEIGHT = 50;
  const CANVAS_WIDTH = 900;
  const CANVAS_HEIGHT = 500;

  // Color scheme for node types
  const nodeColors = {
    module: { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af' },
    skill: { bg: '#fef3c7', border: '#f59e0b', text: '#92400e' },
    data_flow: { bg: '#d1fae5', border: '#10b981', text: '#065f46' },
  };

  function handleNodeClick(node: ArchitectureNode) {
    selectedNodeId = node.id;
    onNodeClick?.(node);
  }

  function handleConnectionMouseEnter(
    connection: ArchitectureConnection,
    event: MouseEvent
  ) {
    hoveredConnection = connection;
    tooltipPosition = { x: event.clientX, y: event.clientY };
    onConnectionHover?.(connection);
  }

  function handleConnectionMouseLeave() {
    hoveredConnection = null;
    onConnectionHover?.(null);
  }

  function getEdgePath(source: ArchitectureNode, target: ArchitectureNode): string {
    const sx = source.x + NODE_WIDTH / 2;
    const sy = source.y + NODE_HEIGHT / 2;
    const tx = target.x + NODE_WIDTH / 2;
    const ty = target.y + NODE_HEIGHT / 2;

    // Curved path
    const midX = (sx + tx) / 2;
    return `M ${sx} ${sy} C ${midX} ${sy}, ${midX} ${ty}, ${tx} ${ty}`;
  }

  // Default demo data if none provided
  const defaultNodes: ArchitectureNode[] = [
    {
      id: 'module-requirements',
      type: 'module',
      label: '需求管理',
      description: '管理产品需求文档和用户需求',
      x: 100,
      y: 50,
      connections: ['skill-pm-brainstorm'],
    },
    {
      id: 'module-prd',
      type: 'module',
      label: 'PRD文档',
      description: '产品需求文档编写和管理',
      x: 100,
      y: 200,
      connections: ['skill-pm-extract-params', 'module-requirements'],
    },
    {
      id: 'module-testcase',
      type: 'module',
      label: '测试用例',
      description: '测试用例设计和管理',
      x: 100,
      y: 350,
      connections: ['skill-pm-generate-tests', 'module-requirements'],
    },
    {
      id: 'skill-pm-brainstorm',
      type: 'skill',
      label: '头脑风暴',
      description: 'AI辅助头脑风暴生成创意',
      x: 450,
      y: 50,
      connections: ['module-prd'],
    },
    {
      id: 'skill-pm-extract-params',
      type: 'skill',
      label: '提取参数',
      description: '从PRD中提取关键参数',
      x: 450,
      y: 200,
      connections: [],
    },
    {
      id: 'skill-pm-generate-tests',
      type: 'skill',
      label: '生成测试',
      description: '从需求自动生成测试用例',
      x: 450,
      y: 350,
      connections: [],
    },
    {
      id: 'module-workflow',
      type: 'module',
      label: '工作流引擎',
      description: '可视化工作流设计和执行',
      x: 700,
      y: 200,
      connections: [],
    },
  ];

  const defaultConnections: ArchitectureConnection[] = [
    { id: 'c1', source: 'module-requirements', target: 'skill-pm-brainstorm', label: 'feeds into', description: '需求驱动头脑风暴' },
    { id: 'c2', source: 'skill-pm-brainstorm', target: 'module-prd', label: 'generates', description: '头脑风暴生成PRD' },
    { id: 'c3', source: 'module-prd', target: 'skill-pm-extract-params', label: 'analyzed by', description: 'PRD被分析提取参数' },
    { id: 'c4', source: 'module-requirements', target: 'skill-pm-generate-tests', label: 'drives', description: '需求驱动测试生成' },
    { id: 'c5', source: 'skill-pm-generate-tests', target: 'module-testcase', label: 'creates', description: '生成测试用例' },
    { id: 'c6', source: 'module-prd', target: 'module-workflow', label: 'orchestrated by', description: 'PRD被工作流编排' },
  ];

  // Use provided data or defaults
  const displayNodes = $derived(nodes.length > 0 ? nodes : defaultNodes);
  const displayConnections = $derived(connections.length > 0 ? connections : defaultConnections);

  onMount(() => {
    // Ensure nodes are rendered after mount
    selectedNodeId = null;
  });
</script>

<div class="architecture-diagram bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
  <!-- Header -->
  <div class="px-4 py-3 border-b border-gray-200 bg-gray-50">
    <div class="flex items-center justify-between">
      <h3 class="text-sm font-semibold text-gray-900">产品架构图</h3>
      <div class="flex items-center gap-3 text-xs text-gray-500">
        <div class="flex items-center gap-1">
          <span class="w-3 h-3 rounded-full bg-blue-100 border border-blue-400"></span>
          <span>模块</span>
        </div>
        <div class="flex items-center gap-1">
          <span class="w-3 h-3 rounded-full bg-amber-100 border border-amber-400"></span>
          <span>技能</span>
        </div>
        <div class="flex items-center gap-1">
          <span class="w-3 h-3 rounded-full bg-emerald-100 border border-emerald-400"></span>
          <span>数据流</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Canvas -->
  <div class="relative bg-white" style="width: {CANVAS_WIDTH}px; height: {CANVAS_HEIGHT}px;">
    {#if loading}
      <div class="absolute inset-0 flex items-center justify-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span class="ml-3 text-sm text-gray-500">加载架构图中...</span>
      </div>
    {:else if error}
      <div class="absolute inset-0 flex items-center justify-center">
        <div class="text-center p-8">
          <svg class="w-12 h-12 text-red-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
          </svg>
          <h3 class="text-lg font-medium text-gray-900 mb-2">架构图加载失败</h3>
          <p class="text-sm text-gray-600">{error}</p>
        </div>
      </div>
    {:else}
      <svg
        width={CANVAS_WIDTH}
        height={CANVAS_HEIGHT}
        viewBox="0 0 {CANVAS_WIDTH} {CANVAS_HEIGHT}"
        class="bg-white"
      >
        <!-- Grid background -->
        <defs>
          <pattern id="arch-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#f3f4f6" stroke-width="1"/>
          </pattern>
          <marker id="arch-arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#9ca3af"/>
          </marker>
        </defs>
        <rect width="100%" height="100%" fill="url(#arch-grid)"/>

        <!-- Connections -->
        {#each displayConnections as connection}
          {@const sourceNode = displayNodes.find(n => n.id === connection.source)}
          {@const targetNode = displayNodes.find(n => n.id === connection.target)}
          {#if sourceNode && targetNode}
            <g
              class="connection-group cursor-pointer"
              onmouseenter={(e) => handleConnectionMouseEnter(connection, e as unknown as MouseEvent)}
              onmouseleave={handleConnectionMouseLeave}
            >
              <path
                d={getEdgePath(sourceNode, targetNode)}
                fill="none"
                stroke={hoveredConnection?.id === connection.id ? '#3b82f6' : '#9ca3af'}
                stroke-width={hoveredConnection?.id === connection.id ? 3 : 2}
                stroke-dasharray="5,5"
                marker-end="url(#arch-arrow)"
                class="transition-all duration-200"
              />
              <!-- Connection label -->
              <text
                x={(sourceNode.x + targetNode.x) / 2 + NODE_WIDTH / 2}
                y={(sourceNode.y + targetNode.y) / 2 + NODE_HEIGHT / 2 - 8}
                text-anchor="middle"
                class="text-xs fill-gray-500 pointer-events-none"
                font-size="10"
              >
                {connection.label}
              </text>
            </g>
          {/if}
        {/each}

        <!-- Nodes -->
        {#each displayNodes as node}
          {@const colors = nodeColors[node.type]}
          <g
            class="node-group cursor-pointer transition-opacity duration-200 hover:opacity-90"
            onclick={() => handleNodeClick(node)}
            transform="translate({node.x}, {node.y})"
          >
            <!-- Node rectangle -->
            <rect
              width={NODE_WIDTH}
              height={NODE_HEIGHT}
              rx="8"
              ry="8"
              fill={colors.bg}
              stroke={selectedNodeId === node.id ? '#1f2937' : colors.border}
              stroke-width={selectedNodeId === node.id ? 3 : 2}
              class="transition-all duration-200"
            />
            <!-- Node label -->
            <text
              x={NODE_WIDTH / 2}
              y={NODE_HEIGHT / 2 + 4}
              text-anchor="middle"
              class="text-sm font-medium pointer-events-none"
              fill={colors.text}
              font-size="13"
            >
              {node.label}
            </text>
          </g>
        {/each}
      </svg>

      <!-- Connection tooltip -->
      {#if hoveredConnection}
        <div
          class="fixed z-50 bg-gray-900 text-white text-xs rounded-lg px-3 py-2 shadow-lg pointer-events-none"
          style="left: {tooltipPosition.x + 12}px; top: {tooltipPosition.y - 30}px;"
        >
          <div class="font-medium">{hoveredConnection.label}</div>
          <div class="text-gray-300">{hoveredConnection.description}</div>
        </div>
      {/if}

      <!-- Empty state -->
      {#if displayNodes.length === 0}
        <div class="absolute inset-0 flex items-center justify-center">
          <div class="text-center">
            <svg class="mx-auto h-12 w-12 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/>
            </svg>
            <p class="mt-2 text-sm text-gray-500">暂无架构数据</p>
          </div>
        </div>
      {/if}
    {/if}
  </div>
</div>

<style>
  .architecture-diagram {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }
</style>
