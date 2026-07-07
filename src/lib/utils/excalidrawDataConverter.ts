import type { FlowchartData, FlowchartNode } from '$lib/apis/pm/types';
import type { TreeModule } from '$lib/stores/pm/architectureStore';

// Node type to Excalidraw shape mapping
const NODE_TYPE_SHAPES: Record<string, string> = {
	start: 'ellipse',
	end: 'ellipse',
	decision: 'diamond',
	process: 'rectangle',
	'parameter-input': 'rectangle',
	'parameter-output': 'rectangle',
	default: 'rectangle'
};

// Shape type validation for Excalidraw
const VALID_EXCALIDRAW_SHAPES = ['rectangle', 'ellipse', 'diamond'];

// Node type to color mapping
const NODE_TYPE_COLORS: Record<string, { bg: string; stroke: string }> = {
	start: { bg: '#dcfce7', stroke: '#86efac' },
	end: { bg: '#fee2e2', stroke: '#fca5a5' },
	decision: { bg: '#fef9c3', stroke: '#fde047' },
	process: { bg: '#dbeafe', stroke: '#93c5fd' },
	'parameter-input': { bg: '#f3e8ff', stroke: '#c4b5fd' },
	'parameter-output': { bg: '#fce7f3', stroke: '#f9a8d4' },
	default: { bg: '#dbeafe', stroke: '#93c5fd' }
};

/**
 * Convert FlowchartData to Excalidraw elements
 */
export function flowchartToExcalidraw(data: FlowchartData): any[] {
	const elements: any[] = [];

	// Convert nodes to Excalidraw shapes
	for (const node of data.nodes || []) {
		const shape = NODE_TYPE_SHAPES[node.type] || 'rectangle';
		const colors = NODE_TYPE_COLORS[node.type] || NODE_TYPE_COLORS.default;
		const pos = node.position || { x: 0, y: 0 };

		// Create shape element
		const shapeElement = {
			id: node.id,
			type: shape,
			x: pos.x,
			y: pos.y,
			width: 120,
			height: shape === 'diamond' ? 80 : 60,
			backgroundColor: colors.bg,
			strokeColor: colors.stroke,
			strokeWidth: 2,
			strokeStyle: 'solid',
			fillStyle: 'solid',
			roughness: 0,
			opacity: 100,
			angle: 0,
			seed: Math.floor(Math.random() * 1000000),
			version: 1,
			versionNonce: Math.floor(Math.random() * 1000000),
			updated: Date.now(),
			isDeleted: false,
			boundElements: null,
			groupIds: [],
			frameId: null,
			link: null,
			locked: false,
			customData: {
				type: node.type,
				label: node.data?.label || '',
				description: node.data?.description || '',
				inputParams: node.data?.inputParams || [],
				outputParams: node.data?.outputParams || [],
				traceability: node.data?.traceability
			}
		};

		elements.push(shapeElement);

		// Create text element for label
		if (node.data?.label) {
			const textElement = {
				id: `text-${node.id}`,
				type: 'text',
				x: pos.x + 10,
				y: pos.y + 20,
				width: 100,
				height: 20,
				text: node.data.label,
				fontSize: 14,
				fontFamily: 'Virgil',
				textAlign: 'center',
				verticalAlign: 'middle',
				strokeColor: '#1f2937',
				backgroundColor: 'transparent',
				strokeWidth: 1,
				strokeStyle: 'solid',
				fillStyle: 'solid',
				roughness: 0,
				opacity: 100,
				angle: 0,
				seed: Math.floor(Math.random() * 1000000),
				version: 1,
				versionNonce: Math.floor(Math.random() * 1000000),
				updated: Date.now(),
				isDeleted: false,
				boundElements: [{ id: node.id, type: shape }],
				groupIds: [],
				frameId: null,
				link: null,
				locked: false
			};
			elements.push(textElement);
		}
	}

	// Convert edges to Excalidraw arrows
	for (const edge of data.edges || []) {
		const arrowElement = {
			id: edge.id,
			type: 'arrow',
			x: 0,
			y: 0,
			width: 0,
			height: 0,
			points: [
				[0, 0],
				[100, 0]
			],
			strokeColor: '#b1b1b7',
			strokeWidth: 1.5,
			strokeStyle: 'solid',
			fillStyle: 'solid',
			roughness: 0,
			opacity: 100,
			angle: 0,
			seed: Math.floor(Math.random() * 1000000),
			version: 1,
			versionNonce: Math.floor(Math.random() * 1000000),
			updated: Date.now(),
			isDeleted: false,
			boundElements: null,
			groupIds: [],
			frameId: null,
			link: null,
			locked: false,
			startBinding: { elementId: edge.source, focus: 0.5, gap: 4 },
			endBinding: { elementId: edge.target, focus: 0.5, gap: 4 },
			startArrowhead: null,
			endArrowhead: 'arrow',
			customData: {
				label: edge.label || '',
				style: edge.style || {}
			}
		};

		elements.push(arrowElement);
	}

	return elements;
}

/**
 * Convert Excalidraw elements to FlowchartData
 */
export function excalidrawToFlowchart(elements: any[]): FlowchartData {
	const nodes: FlowchartNode[] = [];
	const edges: any[] = [];

	for (const element of elements) {
		if (element.isDeleted) continue;

		// Handle shape elements (nodes)
		if (['rectangle', 'ellipse', 'diamond'].includes(element.type)) {
			const node: FlowchartNode = {
				id: element.id,
				type: element.customData?.type || 'process',
				position: { x: element.x, y: element.y },
				data: {
					label: element.customData?.label || '',
					description: element.customData?.description || '',
					style: {
						shape: element.type,
						backgroundColor: element.backgroundColor,
						borderColor: element.strokeColor
					},
					inputParams: element.customData?.inputParams || [],
					outputParams: element.customData?.outputParams || [],
					traceability: element.customData?.traceability
				}
			};
			nodes.push(node);
		}

		// Handle arrow elements (edges)
		if (element.type === 'arrow') {
			const edge = {
				id: element.id,
				source: element.startBinding?.elementId || '',
				target: element.endBinding?.elementId || '',
				label: element.customData?.label || '',
				style: element.customData?.style || {}
			};
			edges.push(edge);
		}
	}

	return { nodes, edges };
}

/**
 * Get node type from Excalidraw element
 */
export function getNodeTypeFromElement(element: any): string {
	return element.customData?.type || 'process';
}

/**
 * Check if element is a flowchart node
 */
export function isFlowchartNode(element: any): boolean {
	return ['rectangle', 'ellipse', 'diamond'].includes(element.type) && !element.isDeleted;
}

/**
 * Check if element is a flowchart edge
 */
export function isFlowchartEdge(element: any): boolean {
	return element.type === 'arrow' && !element.isDeleted;
}

/**
 * Convert TreeModule[] to Excalidraw elements for architecture mindmap
 */
export function treeToExcalidraw(modules: TreeModule[]): any[] {
	const elements: any[] = [];
	const MODULE_WIDTH = 160;
	const MODULE_HEIGHT = 80;
	const FEATURE_WIDTH = 140;
	const FEATURE_HEIGHT = 60;
	const HORIZONTAL_SPACING = 200;
	const VERTICAL_SPACING = 120;

	// Create root node (Product)
	const rootId = 'root-product';
	const rootElement = {
		id: rootId,
		type: 'rectangle',
		x: 400,
		y: 50,
		width: 120,
		height: 60,
		backgroundColor: '#dbeafe',
		strokeColor: '#3b82f6',
		strokeWidth: 2,
		strokeStyle: 'solid',
		fillStyle: 'solid',
		roughness: 0,
		opacity: 100,
		angle: 0,
		seed: Math.floor(Math.random() * 1000000),
		version: 1,
		versionNonce: Math.floor(Math.random() * 1000000),
		updated: Date.now(),
		isDeleted: false,
		boundElements: null,
		groupIds: [],
		frameId: null,
		link: null,
		locked: false,
		customData: {
			type: 'root',
			label: '产品',
			moduleName: '',
			featureName: ''
		}
	};
	elements.push(rootElement);

	// Add root text
	const rootText = {
		id: `text-${rootId}`,
		type: 'text',
		x: 400 + 10,
		y: 50 + 20,
		width: 100,
		height: 20,
		text: '产品',
		fontSize: 16,
		fontFamily: 'Virgil',
		textAlign: 'center',
		verticalAlign: 'middle',
		strokeColor: '#1f2937',
		backgroundColor: 'transparent',
		strokeWidth: 1,
		strokeStyle: 'solid',
		fillStyle: 'solid',
		roughness: 0,
		opacity: 100,
		angle: 0,
		seed: Math.floor(Math.random() * 1000000),
		version: 1,
		versionNonce: Math.floor(Math.random() * 1000000),
		updated: Date.now(),
		isDeleted: false,
		boundElements: [{ id: rootId, type: 'rectangle' }],
		groupIds: [],
		frameId: null,
		link: null,
		locked: false
	};
	elements.push(rootText);

/**
 * Convert TreeModule[] to Excalidraw elements for architecture mindmap
 * Uses a hierarchical tree layout algorithm
 */
export function treeToExcalidraw(modules: TreeModule[]): any[] {
	const elements: any[] = [];
	
	// Layout constants
	const CANVAS_WIDTH = 1200;
	const ROOT_Y = 50;
	const MODULE_Y = 180;
	const FEATURE_START_Y = 320;
	const FEATURE_SPACING = 100;
	const MODULE_WIDTH = 160;
	const MODULE_HEIGHT = 80;
	const FEATURE_WIDTH = 140;
	const FEATURE_HEIGHT = 60;
	
	// Calculate horizontal positions for modules
	const totalModuleWidth = modules.length * MODULE_WIDTH + (modules.length - 1) * 80;
	const startX = (CANVAS_WIDTH - totalModuleWidth) / 2;
	
	// Create root node (Product) at center
	const rootId = 'root-product';
	const rootX = CANVAS_WIDTH / 2 - 60;
	const rootElement = {
		id: rootId,
		type: 'rectangle',
		x: rootX,
		y: ROOT_Y,
		width: 120,
		height: 60,
		backgroundColor: '#dbeafe',
		strokeColor: '#3b82f6',
		strokeWidth: 2,
		strokeStyle: 'solid',
		fillStyle: 'solid',
		roughness: 0,
		opacity: 100,
		angle: 0,
		seed: Math.floor(Math.random() * 1000000),
		version: 1,
		versionNonce: Math.floor(Math.random() * 1000000),
		updated: Date.now(),
		isDeleted: false,
		boundElements: null,
		groupIds: [],
		frameId: null,
		link: null,
		locked: false,
		customData: {
			type: 'root',
			label: '产品',
			moduleName: '',
			featureName: ''
		}
	};
	elements.push(rootElement);

	// Add root text
	const rootText = {
		id: `text-${rootId}`,
		type: 'text',
		x: rootX + 10,
		y: ROOT_Y + 20,
		width: 100,
		height: 20,
		text: '产品',
		fontSize: 16,
		fontFamily: 'Virgil',
		textAlign: 'center',
		verticalAlign: 'middle',
		strokeColor: '#1f2937',
		backgroundColor: 'transparent',
		strokeWidth: 1,
		strokeStyle: 'solid',
		fillStyle: 'solid',
		roughness: 0,
		opacity: 100,
		angle: 0,
		seed: Math.floor(Math.random() * 1000000),
		version: 1,
		versionNonce: Math.floor(Math.random() * 1000000),
		updated: Date.now(),
		isDeleted: false,
		boundElements: [{ id: rootId, type: 'rectangle' }],
		groupIds: [],
		frameId: null,
		link: null,
		locked: false
	};
	elements.push(rootText);

	// Create module nodes with proper horizontal distribution
	modules.forEach((mod, modIndex) => {
		const modX = startX + modIndex * (MODULE_WIDTH + 80);
		const modY = MODULE_Y;
		const modId = `mod-${mod.name}`;

		// Module shape
		const modElement = {
			id: modId,
			type: 'rectangle',
			x: modX,
			y: modY,
			width: MODULE_WIDTH,
			height: MODULE_HEIGHT,
			backgroundColor: mod.source === 'manual' ? '#f9fafb' : '#dcfce7',
			strokeColor: mod.source === 'manual' ? '#9ca3af' : '#22c55e',
			strokeWidth: 2,
			strokeStyle: mod.source === 'manual' ? 'dashed' : 'solid',
			fillStyle: 'solid',
			roughness: 0,
			opacity: 100,
			angle: 0,
			seed: Math.floor(Math.random() * 1000000),
			version: 1,
			versionNonce: Math.floor(Math.random() * 1000000),
			updated: Date.now(),
			isDeleted: false,
			boundElements: null,
			groupIds: [],
			frameId: null,
			link: null,
			locked: false,
			customData: {
				type: 'module',
				label: mod.name,
				moduleName: mod.name,
				featureName: '',
				source: mod.source
			}
		};
		elements.push(modElement);

		// Module text - centered
		const modText = {
			id: `text-${modId}`,
			type: 'text',
			x: modX + 10,
			y: modY + 30,
			width: MODULE_WIDTH - 20,
			height: 20,
			text: mod.name,
			fontSize: 14,
			fontFamily: 'Virgil',
			textAlign: 'center',
			verticalAlign: 'middle',
			strokeColor: '#1f2937',
			backgroundColor: 'transparent',
			strokeWidth: 1,
			strokeStyle: 'solid',
			fillStyle: 'solid',
			roughness: 0,
			opacity: 100,
			angle: 0,
			seed: Math.floor(Math.random() * 1000000),
			version: 1,
			versionNonce: Math.floor(Math.random() * 1000000),
			updated: Date.now(),
			isDeleted: false,
			boundElements: [{ id: modId, type: 'rectangle' }],
			groupIds: [],
			frameId: null,
			link: null,
			locked: false
		};
		elements.push(modText);

		// Create arrow from root to module - vertical line from bottom of root to top of module
		const arrowId = `arrow-${rootId}-${modId}`;
		const rootCenterX = rootX + 60;
		const rootBottomY = ROOT_Y + 60;
		const modCenterX = modX + MODULE_WIDTH / 2;
		const modTopY = modY;
		
		const arrowElement = {
			id: arrowId,
			type: 'arrow',
			x: 0,
			y: 0,
			width: 0,
			height: 0,
			points: [
				[rootCenterX, rootBottomY],
				[modCenterX, modTopY]
			],
			strokeColor: '#b1b1b7',
			strokeWidth: 1.5,
			strokeStyle: 'solid',
			fillStyle: 'solid',
			roughness: 0,
			opacity: 100,
			angle: 0,
			seed: Math.floor(Math.random() * 1000000),
			version: 1,
			versionNonce: Math.floor(Math.random() * 1000000),
			updated: Date.now(),
			isDeleted: false,
			boundElements: null,
			groupIds: [],
			frameId: null,
			link: null,
			locked: false,
			startBinding: { elementId: rootId, focus: 0.5, gap: 4 },
			endBinding: { elementId: modId, focus: 0.5, gap: 4 },
			startArrowhead: null,
			endArrowhead: 'arrow'
		};
		elements.push(arrowElement);

		// Create feature nodes - vertically stacked under each module
		mod.features.forEach((feat, featIndex) => {
			const featX = modX + (MODULE_WIDTH - FEATURE_WIDTH) / 2; // Center feature under module
			const featY = FEATURE_START_Y + featIndex * FEATURE_SPACING;
			const featId = `feat-${mod.name}-${feat.name}`;

			// Feature shape
			const featElement = {
				id: featId,
				type: 'rectangle',
				x: featX,
				y: featY,
				width: FEATURE_WIDTH,
				height: FEATURE_HEIGHT,
				backgroundColor: feat.source === 'manual' ? '#f9fafb' : '#fef3c7',
				strokeColor: feat.source === 'manual' ? '#9ca3af' : '#eab308',
				strokeWidth: 2,
				strokeStyle: feat.source === 'manual' ? 'dashed' : 'solid',
				fillStyle: 'solid',
				roughness: 0,
				opacity: 100,
				angle: 0,
				seed: Math.floor(Math.random() * 1000000),
				version: 1,
				versionNonce: Math.floor(Math.random() * 1000000),
				updated: Date.now(),
				isDeleted: false,
				boundElements: null,
				groupIds: [],
				frameId: null,
				link: null,
				locked: false,
				customData: {
					type: 'feature',
					label: feat.name,
					moduleName: mod.name,
					featureName: feat.name,
					source: feat.source,
					paramCount: feat.paramCount
				}
			};
			elements.push(featElement);

			// Feature text - centered
			const featText = {
				id: `text-${featId}`,
				type: 'text',
				x: featX + 10,
				y: featY + 20,
				width: FEATURE_WIDTH - 20,
				height: 20,
				text: feat.name,
				fontSize: 12,
				fontFamily: 'Virgil',
				textAlign: 'center',
				verticalAlign: 'middle',
				strokeColor: '#1f2937',
				backgroundColor: 'transparent',
				strokeWidth: 1,
				strokeStyle: 'solid',
				fillStyle: 'solid',
				roughness: 0,
				opacity: 100,
				angle: 0,
				seed: Math.floor(Math.random() * 1000000),
				version: 1,
				versionNonce: Math.floor(Math.random() * 1000000),
				updated: Date.now(),
				isDeleted: false,
				boundElements: [{ id: featId, type: 'rectangle' }],
				groupIds: [],
				frameId: null,
				link: null,
				locked: false
			};
			elements.push(featText);

			// Create arrow from module to feature - vertical line
			const featArrowId = `arrow-${modId}-${featId}`;
			const modCenterX = modX + MODULE_WIDTH / 2;
			const modBottomY = modY + MODULE_HEIGHT;
			const featCenterX = featX + FEATURE_WIDTH / 2;
			const featTopY = featY;
			
			const featArrowElement = {
				id: featArrowId,
				type: 'arrow',
				x: 0,
				y: 0,
				width: 0,
				height: 0,
				points: [
					[modCenterX, modBottomY],
					[featCenterX, featTopY]
				],
				strokeColor: '#b1b1b7',
				strokeWidth: 1.5,
				strokeStyle: 'solid',
				fillStyle: 'solid',
				roughness: 0,
				opacity: 100,
				angle: 0,
				seed: Math.floor(Math.random() * 1000000),
				version: 1,
				versionNonce: Math.floor(Math.random() * 1000000),
				updated: Date.now(),
				isDeleted: false,
				boundElements: null,
				groupIds: [],
				frameId: null,
				link: null,
				locked: false,
				startBinding: { elementId: modId, focus: 0.5, gap: 4 },
				endBinding: { elementId: featId, focus: 0.5, gap: 4 },
				startArrowhead: null,
				endArrowhead: 'arrow'
			};
			elements.push(featArrowElement);
		});
	});

	return elements;
}
