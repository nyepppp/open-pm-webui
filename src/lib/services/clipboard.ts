import type { CanvasNode } from '$lib/types/canvas';

/**
 * Clipboard service for copy/paste operations
 */

interface ClipboardData {
  nodes: CanvasNode[];
  timestamp: number;
}

let clipboardData: ClipboardData | null = null;

export function copyToClipboard(nodes: CanvasNode[]): void {
  clipboardData = {
    nodes: nodes.map(node => ({ ...node, id: generateId() })),
    timestamp: Date.now()
  };
}

export function cutToClipboard(nodes: CanvasNode[]): void {
  clipboardData = {
    nodes: nodes.map(node => ({ ...node, id: generateId() })),
    timestamp: Date.now()
  };
}

export function pasteFromClipboard(): CanvasNode[] {
  if (!clipboardData) return [];
  
  // Offset pasted nodes to avoid overlap
  return clipboardData.nodes.map(node => ({
    ...node,
    x: node.x + 20,
    y: node.y + 20
  }));
}

export function hasClipboardData(): boolean {
  return clipboardData !== null;
}

function generateId(): string {
  return Math.random().toString(36).substr(2, 9);
}
