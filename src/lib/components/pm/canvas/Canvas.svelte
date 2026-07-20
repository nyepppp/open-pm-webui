<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { CanvasNode, Connection, ViewTransform, Point } from '$lib/types/canvas';
  import { canvasStore } from '$lib/stores/canvasStore';
  import { renderCanvas } from '$lib/utils/canvasRender';
  import { worldToScreen, screenToWorld, snapToGrid } from '$lib/utils/canvasCoords';

  // Props
  export let width: number = 800;
  export let height: number = 600;

  // Local state
  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D;
  let isPanning = false;
  let isDragging = false;
  let isSelecting = false;
  let isConnecting = false;
  let lastMousePos: Point = { x: 0, y: 0 };
  let selectionStart: Point = { x: 0, y: 0 };
  let draggedNodeId: string | null = null;
  let connectionSourceId: string | null = null;

  // Subscribe to store
  $: state = $canvasStore;
  $: transform = state.view;
  $: nodes = state.nodes;
  $: connections = state.connections;
  $: selection = state.selection;
  $: grid = state.grid;

  onMount(() => {
    ctx = canvas.getContext('2d')!;
    render();
  });

  // Re-render when state changes
  $: if (ctx) {
    render();
  }

  function render() {
    if (!ctx) return;
    renderCanvas(
      ctx,
      width,
      height,
      nodes,
      connections,
      selection.nodeIds,
      transform,
      grid.enabled,
      grid.size
    );
  }

  // Mouse event handlers
  function handleMouseDown(event: MouseEvent) {
    const rect = canvas.getBoundingClientRect();
    const mouseX = event.clientX - rect.left;
    const mouseY = event.clientY - rect.top;
    const worldPos = screenToWorld({ x: mouseX, y: mouseY }, transform);

    lastMousePos = { x: mouseX, y: mouseY };

    // Check if clicking on a node
    const clickedNode = findNodeAtPosition(worldPos);
    
    if (clickedNode) {
      if (event.ctrlKey) {
        // Toggle selection
        if (selection.nodeIds.has(clickedNode.id)) {
          canvasStore.deselectNode(clickedNode.id);
        } else {
          canvasStore.selectNode(clickedNode.id, true);
        }
      } else {
        // Select node
        canvasStore.selectNode(clickedNode.id);
        draggedNodeId = clickedNode.id;
        isDragging = true;
      }
    } else {
      // Start panning or selection
      if (event.button === 0) {
        // Left click on empty space - start selection
        isSelecting = true;
        selectionStart = worldPos;
      } else if (event.button === 1) {
        // Middle click - start panning
        isPanning = true;
      }
    }
  }

  function handleMouseMove(event: MouseEvent) {
    const rect = canvas.getBoundingClientRect();
    const mouseX = event.clientX - rect.left;
    const mouseY = event.clientY - rect.top;
    const worldPos = screenToWorld({ x: mouseX, y: mouseY }, transform);

    if (isPanning) {
      const dx = mouseX - lastMousePos.x;
      const dy = mouseY - lastMousePos.y;
      
      canvasStore.setView({
        panX: transform.panX + dx / transform.zoom,
        panY: transform.panY + dy / transform.zoom
      });
    } else if (isDragging && draggedNodeId) {
      // Move dragged node
      const snappedPos = grid.enabled ? snapToGrid(worldPos, grid.size) : worldPos;
      canvasStore.updateNode(draggedNodeId, { x: snappedPos.x, y: snappedPos.y });
    } else if (isSelecting) {
      // Update selection rectangle
      // This would be handled by a SelectionBox component
    }

    lastMousePos = { x: mouseX, y: mouseY };
  }

  function handleMouseUp(event: MouseEvent) {
    if (isSelecting) {
      // Complete selection
      isSelecting = false;
    }
    
    isPanning = false;
    isDragging = false;
    draggedNodeId = null;
  }

  function handleWheel(event: WheelEvent) {
    event.preventDefault();
    
    const rect = canvas.getBoundingClientRect();
    const mouseX = event.clientX - rect.left;
    const mouseY = event.clientY - rect.top;
    
    // Zoom centered on mouse position
    const zoomFactor = event.deltaY > 0 ? 0.9 : 1.1;
    const newZoom = Math.max(0.1, Math.min(5.0, transform.zoom * zoomFactor));
    
    // Adjust pan to keep mouse position stable
    const worldMouseBefore = screenToWorld({ x: mouseX, y: mouseY }, transform);
    const newTransform = { ...transform, zoom: newZoom };
    const worldMouseAfter = screenToWorld({ x: mouseX, y: mouseY }, newTransform);
    
    canvasStore.setView({
      zoom: newZoom,
      panX: transform.panX + (worldMouseAfter.x - worldMouseBefore.x),
      panY: transform.panY + (worldMouseAfter.y - worldMouseBefore.y)
    });
  }

  function handleKeyDown(event: KeyboardEvent) {
    // Ctrl+0 - Reset view
    if (event.ctrlKey && event.key === '0') {
      event.preventDefault();
      canvasStore.resetView();
    }
    
    // Ctrl++ - Zoom in
    if (event.ctrlKey && event.key === '+') {
      event.preventDefault();
      const newZoom = Math.min(5.0, transform.zoom * 1.2);
      canvasStore.setView({ zoom: newZoom });
    }
    
    // Ctrl+- - Zoom out
    if (event.ctrlKey && event.key === '-') {
      event.preventDefault();
      const newZoom = Math.max(0.1, transform.zoom / 1.2);
      canvasStore.setView({ zoom: newZoom });
    }
    
    // Delete - Delete selected nodes
    if (event.key === 'Delete' || event.key === 'Backspace') {
      event.preventDefault();
      selection.nodeIds.forEach(nodeId => {
        canvasStore.deleteNode(nodeId);
      });
    }
    
    // Ctrl+A - Select all
    if (event.ctrlKey && event.key === 'a') {
      event.preventDefault();
      const allNodeIds = Array.from(nodes.keys());
      canvasStore.selectNodes(allNodeIds);
    }
  }

  function findNodeAtPosition(pos: Point): CanvasNode | null {
    for (const [id, node] of nodes) {
      if (
        pos.x >= node.x &&
        pos.x <= node.x + node.width &&
        pos.y >= node.y &&
        pos.y <= node.y + node.height
      ) {
        return node;
      }
    }
    return null;
  }

  function handleContextMenu(event: MouseEvent) {
    event.preventDefault();
    // Context menu logic would be implemented here
  }
</script>

<div class="canvas-container">
  <canvas
    bind:this={canvas}
    {width}
    {height}
    on:mousedown={handleMouseDown}
    on:mousemove={handleMouseMove}
    on:mouseup={handleMouseUp}
    on:wheel={handleWheel}
    on:keydown={handleKeyDown}
    on:contextmenu={handleContextMenu}
    tabindex="0"
    class="canvas-element"
  />
</div>

<style>
  .canvas-container {
    position: relative;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background-color: #f8f9fa;
  }

  .canvas-element {
    display: block;
    cursor: grab;
    outline: none;
  }

  .canvas-element:active {
    cursor: grabbing;
  }

  .canvas-element:global(.selecting) {
    cursor: crosshair;
  }
</style>
