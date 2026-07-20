// Canvas Types - Core interfaces for the canvas interaction system

export interface Point {
  x: number;
  y: number;
}

export interface Size {
  width: number;
  height: number;
}

export interface Bounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

// Node Types
export type NodeShape = 'rectangle' | 'circle' | 'diamond' | 'rounded-rectangle';

export interface NodeStyle {
  fillColor: string;
  borderColor: string;
  borderWidth: number;
  fontFamily: string;
  fontSize: number;
  fontColor: string;
}

export interface CanvasNode {
  id: string;
  type: NodeShape;
  x: number;
  y: number;
  width: number;
  height: number;
  text: string;
  style: NodeStyle;
  zIndex: number;
  customProperties: Record<string, unknown>;
}

// Connection Types
export type AnchorPosition = 'top' | 'right' | 'bottom' | 'left';
export type LineStyle = 'solid' | 'dashed' | 'dotted';
export type ArrowStyle = 'none' | 'arrow' | 'diamond';

export interface Connection {
  id: string;
  sourceNodeId: string;
  targetNodeId: string;
  sourceAnchor: AnchorPosition;
  targetAnchor: AnchorPosition;
  lineStyle: LineStyle;
  arrowStyle: ArrowStyle;
  color: string;
  thickness: number;
  bendPoints: Point[];
}

// Selection Types
export interface Selection {
  nodeIds: Set<string>;
  connectionIds: Set<string>;
  primaryNodeId: string | null;
}

// Group Types
export interface NodeGroup {
  id: string;
  name: string;
  nodeIds: Set<string>;
}

// Canvas State Types
export interface ViewTransform {
  zoom: number;
  panX: number;
  panY: number;
}

export interface ViewState extends ViewTransform {}

export interface GridState {
  enabled: boolean;
  size: number;
}

export interface CanvasState {
  id: string;
  projectId: string;
  name: string;
  view: ViewState;
  grid: GridState;
  nodes: Map<string, CanvasNode>;
  connections: Map<string, Connection>;
  selection: Selection;
  groups: Map<string, NodeGroup>;
}

// History Types
export type OperationType = 'addNode' | 'moveNode' | 'deleteNode' | 'editNode' | 'addConnection' | 'deleteConnection' | 'editConnection' | 'groupNodes' | 'ungroupNodes';

export interface HistoryEntry {
  type: OperationType;
  previousState: unknown;
  newState: unknown;
  timestamp: number;
}

// Event Types
export interface CanvasMouseEvent {
  clientX: number;
  clientY: number;
  button: number;
  shiftKey: boolean;
  ctrlKey: boolean;
  altKey: boolean;
}

export interface CanvasKeyboardEvent {
  key: string;
  ctrlKey: boolean;
  shiftKey: boolean;
  altKey: boolean;
}
