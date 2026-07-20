/**
 * Canvas API client service
 * Handles all HTTP requests to the backend canvas API
 */

import type { CanvasState, CanvasNode, Connection } from '$lib/types/canvas';

const API_BASE_URL = '/api/v1';

class CanvasApiError extends Error {
  constructor(public status: number, public message: string) {
    super(message);
    this.name = 'CanvasApiError';
  }
}

async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };
  
  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new CanvasApiError(
      response.status,
      errorData.message || `HTTP ${response.status}`
    );
  }
  
  return response;
}

// Canvas CRUD operations
export async function createCanvas(projectId: string, name: string): Promise<CanvasState> {
  const response = await fetchWithAuth(`/projects/${projectId}/canvases`, {
    method: 'POST',
    body: JSON.stringify({ name })
  });
  return response.json();
}

export async function getCanvas(canvasId: string): Promise<CanvasState> {
  const response = await fetchWithAuth(`/canvases/${canvasId}`);
  return response.json();
}

export async function updateCanvas(canvasId: string, updates: Partial<CanvasState>): Promise<CanvasState> {
  const response = await fetchWithAuth(`/canvases/${canvasId}`, {
    method: 'PATCH',
    body: JSON.stringify(updates)
  });
  return response.json();
}

export async function deleteCanvas(canvasId: string): Promise<void> {
  await fetchWithAuth(`/canvases/${canvasId}`, {
    method: 'DELETE'
  });
}

// Node operations
export async function createNode(canvasId: string, node: Omit<CanvasNode, 'id'>): Promise<CanvasNode> {
  const response = await fetchWithAuth(`/canvases/${canvasId}/nodes`, {
    method: 'POST',
    body: JSON.stringify(node)
  });
  return response.json();
}

export async function updateNode(nodeId: string, updates: Partial<CanvasNode>): Promise<CanvasNode> {
  const response = await fetchWithAuth(`/nodes/${nodeId}`, {
    method: 'PATCH',
    body: JSON.stringify(updates)
  });
  return response.json();
}

export async function deleteNode(nodeId: string): Promise<void> {
  await fetchWithAuth(`/nodes/${nodeId}`, {
    method: 'DELETE'
  });
}

// Connection operations
export async function createConnection(canvasId: string, connection: Omit<Connection, 'id'>): Promise<Connection> {
  const response = await fetchWithAuth(`/canvases/${canvasId}/connections`, {
    method: 'POST',
    body: JSON.stringify(connection)
  });
  return response.json();
}

export async function deleteConnection(connectionId: string): Promise<void> {
  await fetchWithAuth(`/connections/${connectionId}`, {
    method: 'DELETE'
  });
}

// Export operations
export async function exportCanvas(canvasId: string, format: 'json' | 'png' | 'svg' | 'drawio' | 'markdown'): Promise<Blob> {
  const response = await fetchWithAuth(`/canvases/${canvasId}/export?format=${format}`);
  return response.blob();
}

// Import operations
export async function importCanvas(projectId: string, format: string, data: unknown, name: string): Promise<CanvasState> {
  const response = await fetchWithAuth(`/projects/${projectId}/canvases/import`, {
    method: 'POST',
    body: JSON.stringify({ format, data, name })
  });
  return response.json();
}
