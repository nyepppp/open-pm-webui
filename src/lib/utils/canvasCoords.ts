import type { Point } from '$lib/types/canvas';

/**
 * Coordinate transformation utilities
 * Converts between world coordinates (canvas space) and screen coordinates (viewport space)
 */

export interface ViewTransform {
  zoom: number;
  panX: number;
  panY: number;
}

/**
 * Convert world coordinates to screen coordinates
 */
export function worldToScreen(point: Point, transform: ViewTransform): Point {
  return {
    x: (point.x + transform.panX) * transform.zoom,
    y: (point.y + transform.panY) * transform.zoom
  };
}

/**
 * Convert screen coordinates to world coordinates
 */
export function screenToWorld(point: Point, transform: ViewTransform): Point {
  return {
    x: point.x / transform.zoom - transform.panX,
    y: point.y / transform.zoom - transform.panY
  };
}

/**
 * Snap a point to the nearest grid intersection
 */
export function snapToGrid(point: Point, gridSize: number): Point {
  return {
    x: Math.round(point.x / gridSize) * gridSize,
    y: Math.round(point.y / gridSize) * gridSize
  };
}

/**
 * Check if a point is within a rectangle
 */
export function isPointInRect(
  point: Point,
  rect: { x: number; y: number; width: number; height: number }
): boolean {
  return (
    point.x >= rect.x &&
    point.x <= rect.x + rect.width &&
    point.y >= rect.y &&
    point.y <= rect.y + rect.height
  );
}

/**
 * Check if two rectangles intersect
 */
export function doRectsIntersect(
  rect1: { x: number; y: number; width: number; height: number },
  rect2: { x: number; y: number; width: number; height: number }
): boolean {
  return (
    rect1.x < rect2.x + rect2.width &&
    rect1.x + rect1.width > rect2.x &&
    rect1.y < rect2.y + rect2.height &&
    rect1.y + rect1.height > rect2.y
  );
}

/**
 * Calculate distance between two points
 */
export function distance(p1: Point, p2: Point): number {
  const dx = p2.x - p1.x;
  const dy = p2.y - p1.y;
  return Math.sqrt(dx * dx + dy * dy);
}

/**
 * Calculate the bounding box of a set of points
 */
export function calculateBoundingBox(points: Point[]): { x: number; y: number; width: number; height: number } | null {
  if (points.length === 0) return null;
  
  let minX = Infinity, minY = Infinity;
  let maxX = -Infinity, maxY = -Infinity;
  
  for (const point of points) {
    minX = Math.min(minX, point.x);
    minY = Math.min(minY, point.y);
    maxX = Math.max(maxX, point.x);
    maxY = Math.max(maxY, point.y);
  }
  
  return {
    x: minX,
    y: minY,
    width: maxX - minX,
    height: maxY - minY
  };
}
