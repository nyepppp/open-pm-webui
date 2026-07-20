import type { CanvasNode, Connection, Point, ViewTransform } from '$lib/types/canvas';
import { worldToScreen, doRectsIntersect } from './canvasCoords';

/**
 * Canvas rendering pipeline
 * Handles viewport culling, dirty region tracking, and efficient redraws
 */

export interface RenderContext {
  ctx: CanvasRenderingContext2D;
  width: number;
  height: number;
  transform: ViewTransform;
}

export interface DirtyRegion {
  x: number;
  y: number;
  width: number;
  height: number;
}

/**
 * Check if a node is within the visible viewport
 */
export function isNodeVisible(
  node: CanvasNode,
  viewport: { x: number; y: number; width: number; height: number }
): boolean {
  return doRectsIntersect(
    { x: node.x, y: node.y, width: node.width, height: node.height },
    viewport
  );
}

/**
 * Calculate the visible viewport in world coordinates
 */
export function getVisibleViewport(
  canvasWidth: number,
  canvasHeight: number,
  transform: ViewTransform
): { x: number; y: number; width: number; height: number } {
  const worldTopLeft = {
    x: -transform.panX,
    y: -transform.panY
  };
  
  return {
    x: worldTopLeft.x,
    y: worldTopLeft.y,
    width: canvasWidth / transform.zoom,
    height: canvasHeight / transform.zoom
  };
}

/**
 * Render the background grid
 */
export function renderGrid(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  transform: ViewTransform,
  gridSize: number,
  gridColor: string = '#e0e0e0'
): void {
  ctx.save();
  ctx.strokeStyle = gridColor;
  ctx.lineWidth = 1 / transform.zoom;
  
  const viewport = getVisibleViewport(width, height, transform);
  const startX = Math.floor(viewport.x / gridSize) * gridSize;
  const startY = Math.floor(viewport.y / gridSize) * gridSize;
  
  ctx.beginPath();
  
  // Vertical lines
  for (let x = startX; x < viewport.x + viewport.width; x += gridSize) {
    const screenX = (x + transform.panX) * transform.zoom;
    ctx.moveTo(screenX, 0);
    ctx.lineTo(screenX, height);
  }
  
  // Horizontal lines
  for (let y = startY; y < viewport.y + viewport.height; y += gridSize) {
    const screenY = (y + transform.panY) * transform.zoom;
    ctx.moveTo(0, screenY);
    ctx.lineTo(width, screenY);
  }
  
  ctx.stroke();
  ctx.restore();
}

/**
 * Render a single node
 */
export function renderNode(
  ctx: CanvasRenderingContext2D,
  node: CanvasNode,
  transform: ViewTransform,
  isSelected: boolean
): void {
  ctx.save();
  
  const screenX = (node.x + transform.panX) * transform.zoom;
  const screenY = (node.y + transform.panY) * transform.zoom;
  const screenWidth = node.width * transform.zoom;
  const screenHeight = node.height * transform.zoom;
  
  // Draw node shape
  ctx.fillStyle = node.style.fillColor;
  ctx.strokeStyle = isSelected ? '#0066cc' : node.style.borderColor;
  ctx.lineWidth = isSelected ? 2 / transform.zoom : node.style.borderWidth / transform.zoom;
  
  switch (node.type) {
    case 'circle':
      ctx.beginPath();
      ctx.ellipse(
        screenX + screenWidth / 2,
        screenY + screenHeight / 2,
        screenWidth / 2,
        screenHeight / 2,
        0,
        0,
        Math.PI * 2
      );
      ctx.fill();
      ctx.stroke();
      break;
      
    case 'diamond':
      ctx.beginPath();
      ctx.moveTo(screenX + screenWidth / 2, screenY);
      ctx.lineTo(screenX + screenWidth, screenY + screenHeight / 2);
      ctx.lineTo(screenX + screenWidth / 2, screenY + screenHeight);
      ctx.lineTo(screenX, screenY + screenHeight / 2);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      break;
      
    case 'rounded-rectangle':
      ctx.beginPath();
      ctx.roundRect(screenX, screenY, screenWidth, screenHeight, 8 * transform.zoom);
      ctx.fill();
      ctx.stroke();
      break;
      
    default: // rectangle
      ctx.beginPath();
      ctx.rect(screenX, screenY, screenWidth, screenHeight);
      ctx.fill();
      ctx.stroke();
  }
  
  // Draw text
  if (node.text) {
    ctx.fillStyle = node.style.fontColor;
    ctx.font = `${node.style.fontSize * transform.zoom}px ${node.style.fontFamily}`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(
      node.text,
      screenX + screenWidth / 2,
      screenY + screenHeight / 2
    );
  }
  
  // Draw selection handles if selected
  if (isSelected) {
    ctx.strokeStyle = '#0066cc';
    ctx.lineWidth = 1 / transform.zoom;
    const handleSize = 6 / transform.zoom;
    
    // Corner handles
    const corners = [
      { x: screenX - handleSize, y: screenY - handleSize },
      { x: screenX + screenWidth, y: screenY - handleSize },
      { x: screenX + screenWidth, y: screenY + screenHeight },
      { x: screenX - handleSize, y: screenY + screenHeight }
    ];
    
    corners.forEach(corner => {
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(corner.x, corner.y, handleSize * 2, handleSize * 2);
      ctx.strokeRect(corner.x, corner.y, handleSize * 2, handleSize * 2);
    });
  }
  
  ctx.restore();
}

/**
 * Render a connection between two nodes
 */
export function renderConnection(
  ctx: CanvasRenderingContext2D,
  connection: Connection,
  nodes: Map<string, CanvasNode>,
  transform: ViewTransform
): void {
  const sourceNode = nodes.get(connection.sourceNodeId);
  const targetNode = nodes.get(connection.targetNodeId);
  
  if (!sourceNode || !targetNode) return;
  
  ctx.save();
  
  const sourceX = (sourceNode.x + sourceNode.width / 2 + transform.panX) * transform.zoom;
  const sourceY = (sourceNode.y + sourceNode.height / 2 + transform.panY) * transform.zoom;
  const targetX = (targetNode.x + targetNode.width / 2 + transform.panX) * transform.zoom;
  const targetY = (targetNode.y + targetNode.height / 2 + transform.panY) * transform.zoom;
  
  ctx.strokeStyle = connection.color;
  ctx.lineWidth = connection.thickness / transform.zoom;
  
  // Set line style
  if (connection.lineStyle === 'dashed') {
    ctx.setLineDash([5 / transform.zoom, 5 / transform.zoom]);
  } else if (connection.lineStyle === 'dotted') {
    ctx.setLineDash([2 / transform.zoom, 2 / transform.zoom]);
  }
  
  ctx.beginPath();
  ctx.moveTo(sourceX, sourceY);
  
  // Draw bend points
  if (connection.bendPoints && connection.bendPoints.length > 0) {
    connection.bendPoints.forEach(point => {
      ctx.lineTo((point.x + transform.panX) * transform.zoom, (point.y + transform.panY) * transform.zoom);
    });
  }
  
  ctx.lineTo(targetX, targetY);
  ctx.stroke();
  
  // Draw arrow
  if (connection.arrowStyle !== 'none') {
    const angle = Math.atan2(targetY - sourceY, targetX - sourceX);
    const arrowSize = 10 / transform.zoom;
    
    ctx.beginPath();
    ctx.moveTo(targetX, targetY);
    ctx.lineTo(
      targetX - arrowSize * Math.cos(angle - Math.PI / 6),
      targetY - arrowSize * Math.sin(angle - Math.PI / 6)
    );
    ctx.moveTo(targetX, targetY);
    ctx.lineTo(
      targetX - arrowSize * Math.cos(angle + Math.PI / 6),
      targetY - arrowSize * Math.sin(angle + Math.PI / 6)
    );
    ctx.stroke();
  }
  
  ctx.restore();
}

/**
 * Main render function - renders the entire canvas
 */
export function renderCanvas(
  ctx: CanvasRenderingContext2D,
  width: number,
  height: number,
  nodes: Map<string, CanvasNode>,
  connections: Map<string, Connection>,
  selectedNodeIds: Set<string>,
  transform: ViewTransform,
  gridEnabled: boolean,
  gridSize: number
): void {
  // Clear canvas
  ctx.clearRect(0, 0, width, height);
  
  // Draw grid
  if (gridEnabled) {
    renderGrid(ctx, width, height, transform, gridSize);
  }
  
  // Calculate visible viewport
  const viewport = getVisibleViewport(width, height, transform);
  
  // Render connections first (behind nodes)
  connections.forEach(connection => {
    renderConnection(ctx, connection, nodes, transform);
  });
  
  // Render nodes
  nodes.forEach(node => {
    if (isNodeVisible(node, viewport)) {
      renderNode(ctx, node, transform, selectedNodeIds.has(node.id));
    }
  });
}
