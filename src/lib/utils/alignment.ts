import type { CanvasNode, Point } from '$lib/types/canvas';

/**
 * Alignment and distribution utilities for multi-node operations
 */

/**
 * Align nodes to the left edge of the leftmost node
 */
export function alignLeft(nodes: CanvasNode[]): CanvasNode[] {
  if (nodes.length < 2) return nodes;
  
  const minX = Math.min(...nodes.map(n => n.x));
  return nodes.map(node => ({ ...node, x: minX }));
}

/**
 * Align nodes to the right edge of the rightmost node
 */
export function alignRight(nodes: CanvasNode[]): CanvasNode[] {
  if (nodes.length < 2) return nodes;
  
  const maxRight = Math.max(...nodes.map(n => n.x + n.width));
  return nodes.map(node => ({
    ...node,
    x: maxRight - node.width
  }));
}

/**
 * Align nodes to the top edge of the topmost node
 */
export function alignTop(nodes: CanvasNode[]): CanvasNode[] {
  if (nodes.length < 2) return nodes;
  
  const minY = Math.min(...nodes.map(n => n.y));
  return nodes.map(node => ({ ...node, y: minY }));
}

/**
 * Align nodes to the bottom edge of the bottommost node
 */
export function alignBottom(nodes: CanvasNode[]): CanvasNode[] {
  if (nodes.length < 2) return nodes;
  
  const maxBottom = Math.max(...nodes.map(n => n.y + n.height));
  return nodes.map(node => ({
    ...node,
    y: maxBottom - node.height
  }));
}

/**
 * Center nodes horizontally
 */
export function centerHorizontal(nodes: CanvasNode[]): CanvasNode[] {
  if (nodes.length < 2) return nodes;
  
  const minX = Math.min(...nodes.map(n => n.x));
  const maxRight = Math.max(...nodes.map(n => n.x + n.width));
  const centerX = (minX + maxRight) / 2;
  
  return nodes.map(node => ({
    ...node,
    x: centerX - node.width / 2
  }));
}

/**
 * Center nodes vertically
 */
export function centerVertical(nodes: CanvasNode[]): CanvasNode[] {
  if (nodes.length < 2) return nodes;
  
  const minY = Math.min(...nodes.map(n => n.y));
  const maxBottom = Math.max(...nodes.map(n => n.y + n.height));
  const centerY = (minY + maxBottom) / 2;
  
  return nodes.map(node => ({
    ...node,
    y: centerY - node.height / 2
  }));
}

/**
 * Distribute nodes evenly horizontally
 */
export function distributeHorizontal(nodes: CanvasNode[]): CanvasNode[] {
  if (nodes.length < 3) return nodes;
  
  const sortedNodes = [...nodes].sort((a, b) => a.x - b.x);
  const minX = sortedNodes[0].x;
  const maxRight = sortedNodes[sortedNodes.length - 1].x + sortedNodes[sortedNodes.length - 1].width;
  const totalWidth = maxRight - minX;
  const spacing = totalWidth / (sortedNodes.length - 1);
  
  return sortedNodes.map((node, index) => ({
    ...node,
    x: minX + spacing * index
  }));
}

/**
 * Distribute nodes evenly vertically
 */
export function distributeVertical(nodes: CanvasNode[]): CanvasNode[] {
  if (nodes.length < 3) return nodes;
  
  const sortedNodes = [...nodes].sort((a, b) => a.y - b.y);
  const minY = sortedNodes[0].y;
  const maxBottom = sortedNodes[sortedNodes.length - 1].y + sortedNodes[sortedNodes.length - 1].height;
  const totalHeight = maxBottom - minY;
  const spacing = totalHeight / (sortedNodes.length - 1);
  
  return sortedNodes.map((node, index) => ({
    ...node,
    y: minY + spacing * index
  }));
}
