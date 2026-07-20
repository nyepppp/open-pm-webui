/**
 * BPMN Export/Import Utilities
 *
 * Client-side utilities for exporting and importing workflows in BPMN/XML and JSON formats.
 */

export interface WorkflowExport {
	name: string;
	description: string;
	nodes: WorkflowNode[];
	edges: WorkflowEdge[];
}

export interface WorkflowNode {
	id: string;
	type: string;
	name: string;
	position: { x: number; y: number };
	config: Record<string, any>;
}

export interface WorkflowEdge {
	id: string;
	source_node_id: string;
	target_node_id: string;
	data_mapping?: Record<string, any>;
}

/**
 * Export workflow to JSON format
 */
export function exportToJSON(workflow: WorkflowExport): string {
	const exportData = {
		version: '2.0',
		exported_at: new Date().toISOString(),
		name: workflow.name,
		description: workflow.description,
		nodes: workflow.nodes,
		edges: workflow.edges
	};
	return JSON.stringify(exportData, null, 2);
}

/**
 * Import workflow from JSON format
 */
export function importFromJSON(jsonString: string): WorkflowExport {
	try {
		const data = JSON.parse(jsonString);
		return {
			name: data.name || 'Imported Workflow',
			description: data.description || '',
			nodes: data.nodes || [],
			edges: data.edges || []
		};
	} catch (e) {
		throw new Error(`Invalid JSON: ${e instanceof Error ? e.message : 'Unknown error'}`);
	}
}

/**
 * Export workflow to BPMN 2.0 XML format
 */
export function exportToBPMN(workflow: WorkflowExport): string {
	const processId = `Process_${generateId()}`;

	let bpmnXml = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                  xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  id="Definitions_${generateId()}"
                  targetNamespace="http://example.com/workflow"
                  exporter="OpenWebUI Workflow Designer"
                  exporterVersion="2.0">
  <bpmn:process id="${processId}" name="${escapeXml(workflow.name)}" isExecutable="true">
`;

	// Add nodes
	for (const node of workflow.nodes) {
		bpmnXml += nodeToBpmnElement(node);
	}

	// Add edges (sequence flows)
	for (const edge of workflow.edges) {
		bpmnXml += edgeToBpmnElement(edge);
	}

	bpmnXml += `  </bpmn:process>
`;

	// Add diagram information
	bpmnXml += addBpmnDiagram(processId, workflow.nodes, workflow.edges);

	bpmnXml += `</bpmn:definitions>`;

	return bpmnXml;
}

/**
 * Import workflow from BPMN 2.0 XML format
 */
export function importFromBPMN(bpmnXml: string): WorkflowExport {
	const parser = new DOMParser();
	const doc = parser.parseFromString(bpmnXml, 'application/xml');

	// Check for parsing errors
	const parserError = doc.querySelector('parsererror');
	if (parserError) {
		throw new Error('Invalid BPMN XML');
	}

	const process = doc.querySelector('process');
	if (!process) {
		throw new Error('No process element found in BPMN XML');
	}

	const workflow: WorkflowExport = {
		name: process.getAttribute('name') || 'Imported Workflow',
		description: '',
		nodes: [],
		edges: []
	};

	// Parse nodes
	const nodeElements = process.querySelectorAll('startEvent, endEvent, task, serviceTask, userTask, exclusiveGateway, parallelGateway, subProcess');
	nodeElements.forEach((element) => {
		const node = parseBpmnNode(element);
		if (node) {
			workflow.nodes.push(node);
		}
	});

	// Parse edges
	const edgeElements = process.querySelectorAll('sequenceFlow');
	edgeElements.forEach((element) => {
		const edge = parseBpmnEdge(element);
		if (edge) {
			workflow.edges.push(edge);
		}
	});

	return workflow;
}

/**
 * Download workflow as a file
 */
export function downloadWorkflow(content: string, filename: string, mimeType: string = 'application/json') {
	const blob = new Blob([content], { type: mimeType });
	const url = URL.createObjectURL(blob);
	const link = document.createElement('a');
	link.href = url;
	link.download = filename;
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	URL.revokeObjectURL(url);
}

/**
 * Read file content as text
 */
export function readFileContent(file: File): Promise<string> {
	return new Promise((resolve, reject) => {
		const reader = new FileReader();
		reader.onload = (e) => resolve(e.target?.result as string);
		reader.onerror = (e) => reject(e);
		reader.readAsText(file);
	});
}

// Helper functions

function nodeToBpmnElement(node: WorkflowNode): string {
	const nodeType = node.type;
	const nodeId = escapeXml(node.id);
	const nodeName = escapeXml(node.name || node.type);

	switch (nodeType) {
		case 'start':
			return `    <bpmn:startEvent id="${nodeId}" name="${nodeName}" />\n`;
		case 'end':
			return `    <bpmn:endEvent id="${nodeId}" name="${nodeName}" />\n`;
		case 'condition':
			return `    <bpmn:exclusiveGateway id="${nodeId}" name="${nodeName}" />\n`;
		case 'parallel':
		case 'merge':
			return `    <bpmn:parallelGateway id="${nodeId}" name="${nodeName}" />\n`;
		default:
			return `    <bpmn:serviceTask id="${nodeId}" name="${nodeName}">\n      <bpmn:extensionElements>\n        <openwebui:nodeType>${nodeType}</openwebui:nodeType>\n      </bpmn:extensionElements>\n    </bpmn:serviceTask>\n`;
	}
}

function edgeToBpmnElement(edge: WorkflowEdge): string {
	return `    <bpmn:sequenceFlow id="${escapeXml(edge.id)}" sourceRef="${escapeXml(edge.source_node_id)}" targetRef="${escapeXml(edge.target_node_id)}" />\n`;
}

function addBpmnDiagram(processId: string, nodes: WorkflowNode[], edges: WorkflowEdge[]): string {
	let diagramXml = `  <bpmndi:BPMNDiagram id="BPMNDiagram_${generateId()}">\n    <bpmndi:BPMNPlane id="BPMNPlane_${generateId()}" bpmnElement="${processId}">\n`;

	// Add node shapes
	for (const node of nodes) {
		const pos = node.position || { x: 0, y: 0 };
		diagramXml += `      <bpmndi:BPMNShape id="${node.id}_di" bpmnElement="${node.id}">\n        <dc:Bounds x="${pos.x}" y="${pos.y}" width="100" height="80" />\n      </bpmndi:BPMNShape>\n`;
	}

	// Add edge shapes
	for (const edge of edges) {
		diagramXml += `      <bpmndi:BPMNEdge id="${edge.id}_di" bpmnElement="${edge.id}" sourceElement="${edge.source_node_id}" targetElement="${edge.target_node_id}" />\n`;
	}

	diagramXml += `    </bpmndi:BPMNPlane>\n  </bpmndi:BPMNDiagram>\n`;

	return diagramXml;
}

function parseBpmnNode(element: Element): WorkflowNode | null {
	const tagName = element.tagName.toLowerCase();
	const nodeId = element.getAttribute('id') || generateId();
	const nodeName = element.getAttribute('name') || 'Node';

	let nodeType = 'custom';

	if (tagName.includes('startevent')) {
		nodeType = 'start';
	} else if (tagName.includes('endevent')) {
		nodeType = 'end';
	} else if (tagName.includes('exclusivegateway')) {
		nodeType = 'condition';
	} else if (tagName.includes('parallelgateway')) {
		nodeType = 'parallel';
	} else if (tagName.includes('subprocess')) {
		nodeType = 'loop';
	} else {
		// Try to get custom type from extension elements
		const extension = element.querySelector('extensionElements');
		if (extension) {
			const customType = extension.querySelector('nodeType');
			if (customType && customType.textContent) {
				nodeType = customType.textContent;
			}
		}
	}

	return {
		id: nodeId,
		type: nodeType,
		name: nodeName,
		position: { x: 0, y: 0 },
		config: {}
	};
}

function parseBpmnEdge(element: Element): WorkflowEdge | null {
	const edgeId = element.getAttribute('id') || generateId();
	const sourceRef = element.getAttribute('sourceRef');
	const targetRef = element.getAttribute('targetRef');

	if (!sourceRef || !targetRef) {
		return null;
	}

	return {
		id: edgeId,
		source_node_id: sourceRef,
		target_node_id: targetRef,
		data_mapping: {}
	};
}

function generateId(): string {
	return Math.random().toString(36).substring(2, 15);
}

function escapeXml(str: string): string {
	return str
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&apos;');
}
