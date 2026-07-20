<script lang="ts">
  import type { WorkflowNode, WorkflowEdge, NodeType, NodeTemplate, Point, Port } from './types';
  import { NODE_TYPE_COLORS } from './types';
  import { onDestroy } from 'svelte';

  // ===== Props =====
  interface Props {
    nodes: WorkflowNode[];
    edges: WorkflowEdge[];
    selectedNodeId?: string | null;
    selectedEdgeId?: string | null;
    nodeResults?: Record<string, any>;
    validationErrors?: Array<{ node_id: string; node_name: string; error: string }> | null;
    onNodeSelect?: (nodeId: string | null) => void;
    onNodeMove?: (nodeId: string, position: Point) => void;
    onNodeDrop?: (template: NodeTemplate, position: Point) => void;
    onEdgeCreate?: (sourceNodeId: string, targetNodeId: string, sourcePortId?: string, targetPortId?: string) => void;
    onEdgeSelect?: (edgeId: string | null) => void;
    onEdgeDelete?: (edgeId: string) => void;
  }

  let {
    nodes,
    edges,
    selectedNodeId = null,
    selectedEdgeId = null,
    nodeResults = {},
    validationErrors = null,
    onNodeSelect,
    onNodeMove,
    onNodeDrop,
    onEdgeCreate,
    onEdgeSelect,
    onEdgeDelete
  }: Props = $props();

  // ===== State =====
  let isDragging = $state(false);
  let draggedNodeId = $state<string | null>(null);
  let dragOffset = $state<Point>({ x: 0, y: 0 });
  let canvasRef = $state<HTMLDivElement | null>(null);
  let svgRef = $state<SVGSVGElement | null>(null);

  // Connection state
  let isConnecting = $state(false);
  let connectingFrom = $state<{ nodeId: string; portId: string; portPos: Point } | null>(null);
  let mousePos = $state<Point>({ x: 0, y: 0 });

  // 画布平移和缩放（用于居中节点、用户拖拽和滚轮缩放）
  // 节点本身坐标不变，<g transform="translate(pan.x, pan.y) scale(zoom)"> 包裹整体内容实现视觉变换。
  let pan = $state<{ x: number; y: number }>({ x: 0, y: 0 });
  let zoom = $state<number>(1);
  let isPanning = $state<boolean>(false);
  let panStart = $state<{ x: number; y: number }>({ x: 0, y: 0 });   // mousedown 屏幕坐标
  let panStartPan = $state<{ x: number; y: number }>({ x: 0, y: 0 }); // mousedown 时的 pan 值
  const MIN_ZOOM = 0.2;
  const MAX_ZOOM = 3;

  // ===== Constants =====
  const NODE_WIDTH = 160;
  const NODE_HEIGHT = 60;
  const PORT_RADIUS = 7;
  const PORT_HIT_RADIUS = 14;
  const GRID_SIZE = 20;

  // ===== Derived =====
  const selectedNode = $derived(nodes.find(n => n.id === selectedNodeId));

  // ===== Helpers =====
  function getNodeColor(type: NodeType): string {
    return NODE_TYPE_COLORS[type] || '#6b7280';
  }

  function getNodePorts(node: WorkflowNode) {
    return node.ports || [];
  }

  // Returns port position in node-local coordinates (relative to node's top-left).
  // Used inside <g transform="translate(node.x, node.y)"> where the node is rendered.
  function getPortPosition(node: WorkflowNode, port: Port): Point {
    const nodeW = node.width || NODE_WIDTH;
    const nodeH = node.height || NODE_HEIGHT;

    if (port.direction === 'input') {
      // Input ports on left side
      const inputPorts = getNodePorts(node).filter(p => p.direction === 'input');
      const inputIndex = inputPorts.indexOf(port);
      const spacing = nodeH / (inputPorts.length + 1);
      return { x: 0, y: spacing * (inputIndex + 1) };
    } else {
      // Output ports on right side
      const outputPorts = getNodePorts(node).filter(p => p.direction === 'output');
      const outputIndex = outputPorts.indexOf(port);
      const spacing = nodeH / (outputPorts.length + 1);
      return { x: nodeW, y: spacing * (outputIndex + 1) };
    }
  }

  // Returns port position in SVG global coordinates (absolute, for edges drawn at <svg> root).
  function getPortGlobalPosition(node: WorkflowNode, port: Port): Point {
    const local = getPortPosition(node, port);
    return { x: node.x + local.x, y: node.y + local.y };
  }

  function getEdgePath(edge: WorkflowEdge): string {
    const sourceNode = nodes.find(n => n.id === edge.sourceNodeId);
    const targetNode = nodes.find(n => n.id === edge.targetNodeId);
    if (!sourceNode || !targetNode) return '';

    const sourceW = sourceNode.width || NODE_WIDTH;
    const sourceH = sourceNode.height || NODE_HEIGHT;
    const targetH = targetNode.height || NODE_HEIGHT;

    // Default to node edge midpoints (global coords)
    let startX = sourceNode.x + sourceW;
    let startY = sourceNode.y + sourceH / 2;
    let endX = targetNode.x;
    let endY = targetNode.y + targetH / 2;

    if (edge.sourcePortId) {
      const sourcePort = getNodePorts(sourceNode).find(p => p.id === edge.sourcePortId);
      if (sourcePort) {
        const pos = getPortGlobalPosition(sourceNode, sourcePort);
        startX = pos.x;
        startY = pos.y;
      }
    }
    if (edge.targetPortId) {
      const targetPort = getNodePorts(targetNode).find(p => p.id === edge.targetPortId);
      if (targetPort) {
        const pos = getPortGlobalPosition(targetNode, targetPort);
        endX = pos.x;
        endY = pos.y;
      }
    }

    // Bezier curve
    const controlOffset = Math.abs(endX - startX) * 0.5;
    const c1x = startX + controlOffset;
    const c2x = endX - controlOffset;

    return `M ${startX} ${startY} C ${c1x} ${startY}, ${c2x} ${endY}, ${endX} ${endY}`;
  }

  function getTempEdgePath(from: Point, to: Point): string {
    const controlOffset = Math.abs(to.x - from.x) * 0.5;
    const c1x = from.x + controlOffset;
    const c2x = to.x - controlOffset;
    return `M ${from.x} ${from.y} C ${c1x} ${from.y}, ${c2x} ${to.y}, ${to.x} ${to.y}`;
  }

  // ===== Event Handlers =====
  function handleCanvasMouseDown(event: MouseEvent) {
    // 防御性判定是否点击在"空白区域"：
    // 之前的判定只覆盖 rect/path 两种 tagName，遇到 polygon/circle/text/g/line 等会失效
    // 改为用 closest() 反向检查：只要不在 node-group / port-group / edge-path / 任何 button 内，
    // 就视为空白区域（可拖曳画布）
    const target = event.target as Element;
    let isEmptyArea = true;
    if (target && typeof target.closest === 'function') {
      // 点击在节点 / 端口 / 连线 / 任何带 role=button 的 SVG 元素上 → 非空白
      if (target.closest('.node-group, .port-group, .edge-path, [role="button"], button, [data-no-pan]')) {
        isEmptyArea = false;
      }
    }
    // 兜底：canvasRef / svgRef 自身一定是空白
    if (event.target === canvasRef || event.target === svgRef) {
      isEmptyArea = true;
    }

    // Deselect when clicking on empty canvas
    if (isEmptyArea) {
      onNodeSelect?.(null);
      onEdgeSelect?.(null);
    }

    // 仅左键在空白区域启动画布拖拽（避免影响节点/端口/连线的点击）
    if (event.button !== 0) return;
    if (isEmptyArea) {
      isPanning = true;
      panStart = { x: event.clientX, y: event.clientY };
      panStartPan = { x: pan.x, y: pan.y };
      attachDocListeners();
    }
  }

  function handleNodeMouseDown(event: MouseEvent, node: WorkflowNode) {
    // Don't start dragging if a connection is in progress
    if (isConnecting) return;
    event.stopPropagation();
    isDragging = true;
    draggedNodeId = node.id;
    attachDocListeners();
    // dragOffset 保存屏幕坐标到节点本地坐标的偏移，考虑 pan 和 zoom：
    // screen = rect.left + pan + node * zoom  =>  node = (screen - rect.left - pan - dragOffset) / zoom
    // 这里 dragOffset = screen - rect.left - pan - node * zoom（mousedown 时计算）
    if (canvasRef) {
      const rect = canvasRef.getBoundingClientRect();
      dragOffset = {
        x: event.clientX - rect.left - pan.x - node.x * zoom,
        y: event.clientY - rect.top - pan.y - node.y * zoom
      };
    } else {
      dragOffset = { x: 0, y: 0 };
    }
    onNodeSelect?.(node.id);
    onEdgeSelect?.(null);
  }

  function handleCanvasMouseMove(event: MouseEvent) {
    // 画布拖拽优先（与节点拖拽、连接互斥）
    if (isPanning) {
      pan = {
        x: panStartPan.x + (event.clientX - panStart.x),
        y: panStartPan.y + (event.clientY - panStart.y)
      };
      return;
    }
    if (isDragging && draggedNodeId && canvasRef) {
      // 反推节点本地坐标：node = (screen - rect.left - pan - dragOffset) / zoom
      const rect = canvasRef.getBoundingClientRect();
      const newX = (event.clientX - rect.left - pan.x - dragOffset.x) / zoom;
      const newY = (event.clientY - rect.top - pan.y - dragOffset.y) / zoom;
      onNodeMove?.(draggedNodeId, { x: newX, y: newY });
    }
    if (isConnecting && canvasRef) {
      // 将屏幕坐标转换为画布逻辑坐标（与 portPos 同坐标系）
      const rect = canvasRef.getBoundingClientRect();
      mousePos = {
        x: (event.clientX - rect.left - pan.x) / zoom,
        y: (event.clientY - rect.top - pan.y) / zoom
      };
    }
  }

  function handleCanvasMouseUp(event: MouseEvent) {
    const wasActive = isPanning || isDragging || isConnecting;
    if (isPanning) {
      isPanning = false;
    }
    if (isDragging) {
      isDragging = false;
      draggedNodeId = null;
    }
    // If connecting but didn't release on a port, cancel
    if (isConnecting) {
      isConnecting = false;
      connectingFrom = null;
    }
    if (wasActive) {
      detachDocListeners();
    }
  }

  // 在 mousedown 启动 pan/drag/connect 时挂到 document，确保鼠标移出 canvas 后仍能持续接收 mousemove。
  // 否则鼠标移到 sidebar/property panel/toolbar 上时拖拽会卡死——这是"画布不能拖"的真实根因。
  function attachDocListeners() {
    document.addEventListener('mousemove', handleCanvasMouseMove);
    document.addEventListener('mouseup', handleCanvasMouseUp);
  }
  function detachDocListeners() {
    document.removeEventListener('mousemove', handleCanvasMouseMove);
    document.removeEventListener('mouseup', handleCanvasMouseUp);
  }

  // 组件卸载时兜底清理 document 监听，防止拖拽中卸载组件导致内存泄漏
  onDestroy(detachDocListeners);

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    event.dataTransfer!.dropEffect = 'copy';
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    const data = event.dataTransfer?.getData('application/json');
    if (!data || !canvasRef) return;

    try {
      const template = JSON.parse(data);
      const rect = canvasRef.getBoundingClientRect();
      // 将屏幕坐标转换为画布逻辑坐标（考虑 pan 和 zoom）
      const x = (event.clientX - rect.left - pan.x) / zoom;
      const y = (event.clientY - rect.top - pan.y) / zoom;
      onNodeDrop?.(template, { x, y });
    } catch (e) {
      console.error('Failed to parse dropped node:', e);
    }
  }

  // 滚轮缩放：以鼠标位置为锚点，缩放范围 [MIN_ZOOM, MAX_ZOOM]
  function handleWheel(event: WheelEvent) {
    event.preventDefault();
    if (!canvasRef) return;
    const rect = canvasRef.getBoundingClientRect();
    const mouseX = event.clientX - rect.left;
    const mouseY = event.clientY - rect.top;
    // 缩放因子（ deltaY > 0 表示向下滚动，缩小）
    const delta = -event.deltaY * 0.001;
    const newZoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom * (1 + delta)));
    if (Math.abs(newZoom - zoom) < 1e-6) return;
    // 锚点缩放：鼠标下的画布点保持不动
    // screen = pan + canvas * zoom  =>  pan_new = mouse - canvas * zoom_new
    // 其中 canvas = (mouse - pan_old) / zoom_old
    const canvasX = (mouseX - pan.x) / zoom;
    const canvasY = (mouseY - pan.y) / zoom;
    pan = { x: mouseX - canvasX * newZoom, y: mouseY - canvasY * newZoom };
    zoom = newZoom;
  }

  function handleNodeClick(event: MouseEvent, node: WorkflowNode) {
    event.stopPropagation();
    onNodeSelect?.(node.id);
    onEdgeSelect?.(null);
  }

  // ===== Port Connection Handlers =====
  function handlePortMouseDown(event: MouseEvent, node: WorkflowNode, port: Port) {
    event.stopPropagation();
    event.preventDefault();
    // Force-clear any drag state regardless of stopPropagation behavior,
    // so node drag and connection never run simultaneously.
    isDragging = false;
    draggedNodeId = null;

    // Only output ports start a connection
    if (port.direction !== 'output') return;

    const portPos = getPortGlobalPosition(node, port);
    isConnecting = true;
    connectingFrom = { nodeId: node.id, portId: port.id, portPos };
    mousePos = { x: portPos.x, y: portPos.y };
    attachDocListeners();
  }

  function handlePortMouseUp(event: MouseEvent, node: WorkflowNode, port: Port) {
    event.stopPropagation();
    event.preventDefault();
    // Only input ports receive a connection
    if (port.direction !== 'input') return;

    if (isConnecting && connectingFrom) {
      // Don't connect a node to itself
      if (connectingFrom.nodeId !== node.id) {
        onEdgeCreate?.(connectingFrom.nodeId, node.id, connectingFrom.portId, port.id);
      }
      isConnecting = false;
      connectingFrom = null;
    }
  }

  function handleEdgeClick(event: MouseEvent, edge: WorkflowEdge) {
    event.stopPropagation();
    onEdgeSelect?.(edge.id);
    onNodeSelect?.(null);
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Delete') {
      if (selectedEdgeId && onEdgeDelete) {
        onEdgeDelete(selectedEdgeId);
      }
    }
  }

  // ===== 画布居中（FAIL-1 修复） =====
  // 计算并设置 pan，使目标节点居中显示在画布 viewport 中央。
  // 节点屏幕坐标 = pan + 节点本地坐标 * zoom，要让节点中心落在 viewport 中心，
  // 需满足：pan + nodeCenter * zoom = viewportCenter，故 pan = viewportCenter - nodeCenter * zoom。
  export function centerOnNode(nodeId: string) {
    const target = nodes.find(n => n.id === nodeId);
    if (!target || !canvasRef) return;
    const nodeW = target.width || NODE_WIDTH;
    const nodeH = target.height || NODE_HEIGHT;
    const nodeCenterX = target.x + nodeW / 2;
    const nodeCenterY = target.y + nodeH / 2;
    const rect = canvasRef.getBoundingClientRect();
    pan = {
      x: rect.width / 2 - nodeCenterX * zoom,
      y: rect.height / 2 - nodeCenterY * zoom
    };
  }
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
  class="workflow-canvas"
  class:panning={isPanning}
  bind:this={canvasRef}
  onmousedown={handleCanvasMouseDown}
  onmousemove={handleCanvasMouseMove}
  onmouseup={handleCanvasMouseUp}
  onwheel={handleWheel}
  ondragover={handleDragOver}
  ondrop={handleDrop}
  onkeydown={handleKeyDown}
  tabindex="0"
  role="application"
  aria-label="Workflow canvas"
>
  <svg
    bind:this={svgRef}
    class="canvas-svg"
    width="100%"
    height="100%"
  >
    <!-- Definitions -->
    <defs>
      <!-- Arrow marker -->
      <marker
        id="arrowhead"
        markerWidth="10"
        markerHeight="7"
        refX="9"
        refY="3.5"
        orient="auto"
      >
        <polygon points="0 0, 10 3.5, 0 7" fill="#6b7280" />
      </marker>
      <marker
        id="arrowhead-selected"
        markerWidth="10"
        markerHeight="7"
        refX="9"
        refY="3.5"
        orient="auto"
      >
        <polygon points="0 0, 10 3.5, 0 7" fill="#3b82f6" />
      </marker>
      <!-- Grid pattern -->
      <pattern id="grid" width={GRID_SIZE} height={GRID_SIZE} patternUnits="userSpaceOnUse">
        <path d="M {GRID_SIZE} 0 L 0 0 0 {GRID_SIZE}" fill="none" stroke="#e5e7eb" stroke-width="0.5" />
      </pattern>
    </defs>

    <!-- Grid background -->
    <rect width="100%" height="100%" fill="url(#grid)" />

    <!-- FAIL-1: 用 <g transform="translate(pan.x, pan.y) scale(zoom)"> 包裹所有可平移内容，
         让 centerOnNode 能通过调整 pan 把目标节点居中到 viewport 中央，
         同时支持滚轮缩放。grid 背景保留在 g 之外，永远填满 viewport。 -->
    <g transform="translate({pan.x}, {pan.y}) scale({zoom})">
      <!-- Edges -->
      {#each edges as edge (edge.id)}
        {@const pathData = getEdgePath(edge)}
        {#if pathData}
          <path
            d={pathData}
            class="edge-path"
            class:selected={edge.id === selectedEdgeId}
            stroke={edge.id === selectedEdgeId ? '#3b82f6' : '#6b7280'}
            stroke-width={edge.id === selectedEdgeId ? 3 : 2}
            fill="none"
            marker-end={edge.id === selectedEdgeId ? 'url(#arrowhead-selected)' : 'url(#arrowhead)'}
            onclick={(e) => handleEdgeClick(e, edge)}
            role="button"
            tabindex="0"
            aria-label={`Edge from ${edge.sourceNodeId} to ${edge.targetNodeId}`}
          />
          <!-- Edge label -->
          {#if edge.label}
            {@const sourceNode = nodes.find(n => n.id === edge.sourceNodeId)}
            {@const targetNode = nodes.find(n => n.id === edge.targetNodeId)}
            {#if sourceNode && targetNode}
              <text
                x={(sourceNode.x + (sourceNode.width || NODE_WIDTH) + targetNode.x) / 2}
                y={(sourceNode.y + targetNode.y) / 2 - 8}
                class="edge-label"
                text-anchor="middle"
              >
                {edge.label}
              </text>
            {/if}
          {/if}
        {/if}
      {/each}

      <!-- Temporary connection line while dragging -->
      {#if isConnecting && connectingFrom}
        <path
          d={getTempEdgePath(connectingFrom.portPos, mousePos)}
          class="temp-edge"
          stroke="#3b82f6"
          stroke-width="2"
          stroke-dasharray="5,5"
          fill="none"
          pointer-events="none"
        />
      {/if}

      <!-- Nodes -->
      {#each nodes as node (node.id)}
        {@const nodeValidationError = validationErrors?.find(e => e.node_id === node.id)}
        <g
          class="node-group"
          class:selected={node.id === selectedNodeId}
          class:validation-error={!!nodeValidationError}
          transform="translate({node.x}, {node.y})"
          onmousedown={(e) => handleNodeMouseDown(e, node)}
          onclick={(e) => handleNodeClick(e, node)}
          role="button"
          tabindex="0"
          aria-label={`Node ${node.name} (${node.type})`}
        >
          <!-- Node background -->
          <rect
            class="node-rect"
            width={node.width || NODE_WIDTH}
            height={node.height || NODE_HEIGHT}
            rx="8"
            ry="8"
            fill={getNodeColor(node.type)}
            stroke={nodeValidationError ? '#ef4444' : (node.id === selectedNodeId ? '#3b82f6' : 'transparent')}
            stroke-width={nodeValidationError || node.id === selectedNodeId ? 3 : 0}
          />
          {#if nodeValidationError}
            <title>校验错误：{nodeValidationError.error}</title>
          {/if}

          <!-- Node content -->
          <foreignObject
            x="0"
            y="0"
            width={node.width || NODE_WIDTH}
            height={node.height || NODE_HEIGHT}
          >
            <div class="node-content">
              <div class="node-name">{node.name}</div>
              <div class="node-type">{node.type}</div>
            </div>
          </foreignObject>

          <!-- Execution status indicator -->
          {#if nodeResults[node.id]}
            {@const result = nodeResults[node.id]}
            {#if result.status === 'running' || result.status === 'in_progress'}
              <circle class="node-status running" cx={(node.width || NODE_WIDTH) - 10} cy={10} r="6" fill="#f59e0b">
                <animate attributeName="opacity" values="0.3;1;0.3" dur="1s" repeatCount="indefinite" />
              </circle>
            {:else if result.status === 'completed'}
              <circle class="node-status completed" cx={(node.width || NODE_WIDTH) - 10} cy={10} r="6" fill="#22c55e" />
            {:else if result.status === 'failed'}
              <circle class="node-status failed" cx={(node.width || NODE_WIDTH) - 10} cy={10} r="6" fill="#ef4444" />
            {/if}
          {/if}

          <!-- Ports -->
          {#each getNodePorts(node) as port}
            {@const pos = getPortPosition(node, port)}
            {@const isInput = port.direction === 'input'}
            {@const isConnectingTarget = isConnecting && isInput && connectingFrom?.nodeId !== node.id}
            <g
              class="port-group"
              class:input={isInput}
              class:output={!isInput}
              onmousedown={(e) => handlePortMouseDown(e, node, port)}
              onmouseup={(e) => handlePortMouseUp(e, node, port)}
              role="button"
              tabindex="0"
              aria-label={`${port.direction} port: ${port.name}`}
            >
              <!-- Transparent hit area (larger for easier targeting) -->
              <circle
                class="port-hit"
                cx={pos.x}
                cy={pos.y}
                r={PORT_HIT_RADIUS}
                fill="transparent"
              />
              <!-- Visible port circle -->
              <circle
                class="node-port"
                class:input={isInput}
                class:output={!isInput}
                class:connecting-target={isConnectingTarget}
                cx={pos.x}
                cy={pos.y}
                r={isConnectingTarget ? PORT_RADIUS + 3 : PORT_RADIUS}
                fill="#fff"
                stroke={getNodeColor(node.type)}
                stroke-width={isConnectingTarget ? 3 : 2}
                pointer-events="none"
              />
            </g>
          {/each}
        </g>
      {/each}
    </g>
  </svg>
</div>

<style>
  .workflow-canvas {
    width: 100%;
    height: 100%;
    position: relative;
    overflow: hidden;
    background-color: #f9fafb;
    cursor: grab;
    outline: none;
  }

  .workflow-canvas.panning {
    cursor: grabbing;
  }

  .workflow-canvas:focus {
    outline: none;
  }

  .canvas-svg {
    width: 100%;
    height: 100%;
    display: block;
  }

  /* Grid background */
  .canvas-svg :global(rect[fill="url(#grid)"]) {
    opacity: 0.5;
  }

  /* Edges */
  .edge-path {
    pointer-events: stroke;
    cursor: pointer;
    transition: stroke 0.2s ease, stroke-width 0.2s ease;
  }

  .edge-path:hover {
    stroke: #3b82f6;
    stroke-width: 3;
  }

  .edge-path.selected {
    stroke: #3b82f6;
    stroke-width: 3;
  }

  .edge-label {
    font-size: 11px;
    fill: #6b7280;
    pointer-events: none;
    user-select: none;
  }

  .temp-edge {
    pointer-events: none;
  }

  /* Nodes */
  .node-group {
    cursor: grab;
    user-select: none;
    transition: filter 0.2s ease;
  }

  .node-group:active {
    cursor: grabbing;
  }

  .node-group:hover .node-rect {
    filter: brightness(1.1);
  }

  .node-group.selected .node-rect {
    filter: drop-shadow(0 0 4px rgba(59, 130, 246, 0.5));
  }

  .node-group.validation-error .node-rect {
    filter: drop-shadow(0 0 6px rgba(239, 68, 68, 0.7));
    animation: pulse-error 1.5s ease-in-out infinite;
  }

  @keyframes pulse-error {
    0%, 100% {
      filter: drop-shadow(0 0 4px rgba(239, 68, 68, 0.5));
    }
    50% {
      filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.9));
    }
  }

  .node-rect {
    transition: stroke-width 0.15s ease, filter 0.2s ease;
  }

  .node-content {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4px 8px;
    box-sizing: border-box;
    pointer-events: none;
  }

  .node-name {
    color: white;
    font-weight: 600;
    font-size: 13px;
    text-align: center;
    line-height: 1.2;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 100%;
  }

  .node-type {
    color: rgba(255, 255, 255, 0.8);
    font-size: 11px;
    text-align: center;
    margin-top: 2px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  /* Ports */
  .port-group {
    cursor: crosshair;
  }

  .port-hit {
    /* Invisible larger hit area; visible style comes from .node-port */
    pointer-events: all;
  }

  .node-port {
    transition: fill 0.15s ease, stroke-width 0.15s ease, transform 0.15s ease;
    transform-box: fill-box;
    transform-origin: center;
  }

  /* Hover effect: scale up the visible port when the hit area is hovered.
     Using transform on a <g>'s child via :hover on the group works reliably
     across modern browsers (unlike the SVG geometry property `r` via CSS). */
  .port-group:hover .node-port {
    fill: #dbeafe;
    stroke-width: 3;
    transform: scale(1.4);
  }

  .node-port.connecting-target {
    fill: #bfdbfe;
    stroke: #3b82f6;
    stroke-width: 3;
  }

  /* Node status indicators */
  .node-status.running {
    animation: pulse 1s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 1; }
  }

  /* Dark mode support */
  @media (prefers-color-scheme: dark) {
    .workflow-canvas {
      background-color: #111827;
    }
  }
</style>
