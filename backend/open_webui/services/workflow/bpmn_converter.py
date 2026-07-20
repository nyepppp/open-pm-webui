"""
BPMN Converter Service

Handles conversion between workflow definitions and BPMN 2.0 XML format.
"""

import json
import uuid
import warnings
from datetime import datetime
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET


class BPMNConverter:
    """Converts between workflow definitions and BPMN 2.0 XML."""

    # BPMN namespace
    BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
    BPMN_DI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
    DC_NS = "http://www.omg.org/spec/DD/20100524/DC"
    XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
    OPENWEBUI_NS = "http://openwebui.com/workflow"

    # Node type to BPMN element mapping
    NODE_TYPE_MAP = {
        "start": "startEvent",
        "end": "endEvent",
        "agent_call": "serviceTask",
        "data_transform": "serviceTask",
        "condition": "exclusiveGateway",
        "parallel": "parallelGateway",
        "merge": "parallelGateway",
        "loop": "subProcess",
        "custom": "serviceTask",
    }

    # Reverse mapping for import
    BPMN_TYPE_MAP = {
        "startEvent": "start",
        "endEvent": "end",
        "task": "agent_call",
        "serviceTask": "agent_call",
        "userTask": "agent_call",
        "scriptTask": "data_transform",
        "exclusiveGateway": "condition",
        "parallelGateway": "parallel",
        "inclusiveGateway": "condition",
        "subProcess": "loop",
        "callActivity": "agent_call",
    }

    def __init__(self):
        self.nsmap = {
            "bpmn": self.BPMN_NS,
            "bpmndi": self.BPMN_DI_NS,
            "dc": self.DC_NS,
            "xsi": self.XSI_NS,
            "openwebui": self.OPENWEBUI_NS,
        }

    def workflow_to_bpmn(self, workflow: dict) -> str:
        """Convert a workflow definition to BPMN 2.0 XML.

        Args:
            workflow: Workflow definition with nodes and edges

        Returns:
            BPMN 2.0 XML string
        """
        # Create root element
        root = ET.Element("bpmn:definitions", {
            "xmlns:bpmn": self.BPMN_NS,
            "xmlns:bpmndi": self.BPMN_DI_NS,
            "xmlns:dc": self.DC_NS,
            "xmlns:xsi": self.XSI_NS,
            "xmlns:openwebui": self.OPENWEBUI_NS,
            "id": f"Definitions_{uuid.uuid4().hex[:8]}",
            "targetNamespace": "http://example.com/workflow",
            "exporter": "OpenWebUI Workflow Designer",
            "exporterVersion": "2.0",
        })

        # Create process
        process_id = f"Process_{uuid.uuid4().hex[:8]}"
        process = ET.SubElement(root, "bpmn:process", {
            "id": process_id,
            "name": workflow.get("name", "Workflow"),
            "isExecutable": "true",
        })

        # Add nodes
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])

        # Create node mapping
        node_elements = {}
        for node in nodes:
            bpmn_element = self._create_bpmn_element(process, node)
            node_elements[node.get("id")] = bpmn_element

        # Add sequence flows (edges)
        for edge in edges:
            self._create_sequence_flow(process, edge, node_elements)

        # Add diagram information
        self._add_diagram_info(root, process_id, nodes, edges)

        # Convert to string
        xml_string = ET.tostring(root, encoding="unicode")
        return self._format_xml(xml_string)

    def bpmn_to_workflow(self, bpmn_xml: str) -> dict:
        """Convert BPMN 2.0 XML to a workflow definition.

        Args:
            bpmn_xml: BPMN 2.0 XML string

        Returns:
            Workflow definition with nodes and edges
        """
        try:
            root = ET.fromstring(bpmn_xml)
        except ET.ParseError as e:
            raise ValueError(f"Invalid BPMN XML: {e}")

        # Find process element
        process = root.find(".//bpmn:process", self.nsmap)
        if process is None:
            process = root.find(".//{http://www.omg.org/spec/BPMN/20100524/MODEL}process")

        if process is None:
            raise ValueError("No process element found in BPMN XML")

        workflow = {
            "name": process.get("name", "Imported Workflow"),
            "description": "",
            "nodes": [],
            "edges": [],
        }

        # Parse nodes
        node_mapping = {}
        for child in process:
            tag = child.tag
            if "startEvent" in tag:
                node = self._parse_start_event(child)
                workflow["nodes"].append(node)
                node_mapping[node["id"]] = node
            elif "endEvent" in tag:
                node = self._parse_end_event(child)
                workflow["nodes"].append(node)
                node_mapping[node["id"]] = node
            elif "task" in tag or "serviceTask" in tag or "userTask" in tag or "scriptTask" in tag or "callActivity" in tag:
                node = self._parse_task(child)
                workflow["nodes"].append(node)
                node_mapping[node["id"]] = node
            elif "exclusiveGateway" in tag or "inclusiveGateway" in tag:
                node = self._parse_gateway(child, "condition")
                workflow["nodes"].append(node)
                node_mapping[node["id"]] = node
            elif "parallelGateway" in tag:
                node = self._parse_gateway(child, "parallel")
                workflow["nodes"].append(node)
                node_mapping[node["id"]] = node
            elif "subProcess" in tag:
                node = self._parse_subprocess(child)
                workflow["nodes"].append(node)
                node_mapping[node["id"]] = node
            elif "sequenceFlow" in tag:
                edge = self._parse_sequence_flow(child)
                workflow["edges"].append(edge)
            else:
                # Handle unsupported elements gracefully
                tag_name = tag.split("}")[-1] if "}" in tag else tag
                warnings.warn(f"Unsupported BPMN element '{tag_name}' - skipping", UserWarning)

        return workflow

    def _create_bpmn_element(self, process: ET.Element, node: dict) -> ET.Element:
        """Create a BPMN element for a workflow node."""
        node_type = node.get("type", "custom")
        node_id = node.get("id", f"node_{uuid.uuid4().hex[:8]}")
        node_name = node.get("name", node_type)
        position = node.get("position", {"x": 0, "y": 0})
        config = node.get("config", {})

        # Map internal type to BPMN type
        bpmn_type = self.NODE_TYPE_MAP.get(node_type, "serviceTask")

        # Create element with common attributes
        element = ET.SubElement(process, f"bpmn:{bpmn_type}", {
            "id": str(node_id),
            "name": str(node_name),
        })

        # Add extension elements for custom data
        extension = ET.SubElement(element, "bpmn:extensionElements")

        # Store original node type
        custom_type = ET.SubElement(extension, "openwebui:nodeType")
        custom_type.text = node_type

        # Store position
        pos_elem = ET.SubElement(extension, "openwebui:position")
        pos_elem.set("x", str(position.get("x", 0)))
        pos_elem.set("y", str(position.get("y", 0)))

        # Store config as JSON
        if config:
            config_elem = ET.SubElement(extension, "openwebui:config")
            config_elem.text = json.dumps(config, ensure_ascii=False)

        # Store label if different from name
        if node_name and node_name != node_type:
            label_elem = ET.SubElement(extension, "openwebui:label")
            label_elem.text = node_name

        return element

    def _create_sequence_flow(self, process: ET.Element, edge: dict, node_elements: dict):
        """Create a sequence flow element."""
        source_id = edge.get("source_node_id") or edge.get("source")
        target_id = edge.get("target_node_id") or edge.get("target")
        edge_id = edge.get("id", f"flow_{uuid.uuid4().hex[:8]}")
        label = edge.get("label", "")
        data_mapping = edge.get("data_mapping", {})

        if source_id and target_id:
            flow = ET.SubElement(process, "bpmn:sequenceFlow", {
                "id": edge_id,
                "sourceRef": source_id,
                "targetRef": target_id,
            })

            # Add extension elements for edge data
            if label or data_mapping:
                extension = ET.SubElement(flow, "bpmn:extensionElements")
                if label:
                    label_elem = ET.SubElement(extension, "openwebui:label")
                    label_elem.text = label
                if data_mapping:
                    mapping_elem = ET.SubElement(extension, "openwebui:dataMapping")
                    mapping_elem.text = json.dumps(data_mapping, ensure_ascii=False)

    def _add_diagram_info(self, root: ET.Element, process_id: str, nodes: List[dict], edges: List[dict]):
        """Add diagram information to the BPMN XML."""
        bpmndi = ET.SubElement(root, "bpmndi:BPMNDiagram", {
            "id": f"BPMNDiagram_{uuid.uuid4().hex[:8]}",
        })

        plane = ET.SubElement(bpmndi, "bpmndi:BPMNPlane", {
            "id": f"BPMNPlane_{uuid.uuid4().hex[:8]}",
            "bpmnElement": process_id,
        })

        # Add node shapes
        for node in nodes:
            position = node.get("position", {"x": 0, "y": 0})
            shape = ET.SubElement(plane, "bpmndi:BPMNShape", {
                "id": f"{node.get('id')}_di",
                "bpmnElement": str(node.get("id", "")),
            })

            # Node dimensions based on type
            node_type = node.get("type", "custom")
            if node_type in ["start", "end"]:
                width, height = 36, 36
            elif node_type in ["condition", "parallel", "merge"]:
                width, height = 50, 50
            else:
                width, height = 100, 80

            bounds = ET.SubElement(shape, "dc:Bounds", {
                "x": str(position.get("x", 0)),
                "y": str(position.get("y", 0)),
                "width": str(width),
                "height": str(height),
            })

        # Add edge shapes
        for edge in edges:
            source_id = edge.get("source_node_id") or edge.get("source")
            target_id = edge.get("target_node_id") or edge.get("target")

            if source_id and target_id:
                ET.SubElement(plane, "bpmndi:BPMNEdge", {
                    "id": f"{edge.get('id', 'flow')}_di",
                    "bpmnElement": edge.get("id", "flow"),
                    "sourceElement": source_id,
                    "targetElement": target_id,
                })

    def _parse_start_event(self, element: ET.Element) -> dict:
        """Parse a start event element."""
        position = self._extract_position(element)
        return {
            "id": element.get("id"),
            "type": "start",
            "name": element.get("name", "Start"),
            "position": position,
            "config": {},
        }

    def _parse_end_event(self, element: ET.Element) -> dict:
        """Parse an end event element."""
        position = self._extract_position(element)
        return {
            "id": element.get("id"),
            "type": "end",
            "name": element.get("name", "End"),
            "position": position,
            "config": {},
        }

    def _parse_task(self, element: ET.Element) -> dict:
        """Parse a task element."""
        node_id = element.get("id")
        node_name = element.get("name", "Task")

        # Try to determine node type from extension elements
        node_type = "agent_call"
        extension = element.find("bpmn:extensionElements", self.nsmap)
        if extension is not None:
            custom_type = extension.find("openwebui:nodeType")
            if custom_type is not None and custom_type.text:
                node_type = custom_type.text

        position = self._extract_position(element)
        config = self._extract_config(element)

        return {
            "id": node_id,
            "type": node_type,
            "name": node_name,
            "position": position,
            "config": config,
        }

    def _parse_gateway(self, element: ET.Element, default_type: str = "condition") -> dict:
        """Parse a gateway element."""
        position = self._extract_position(element)
        return {
            "id": element.get("id"),
            "type": default_type,
            "name": element.get("name", "Gateway"),
            "position": position,
            "config": {},
        }

    def _parse_subprocess(self, element: ET.Element) -> dict:
        """Parse a subprocess element."""
        position = self._extract_position(element)
        return {
            "id": element.get("id"),
            "type": "loop",
            "name": element.get("name", "Loop"),
            "position": position,
            "config": {},
        }

    def _parse_sequence_flow(self, element: ET.Element) -> dict:
        """Parse a sequence flow element."""
        edge_data = {
            "id": element.get("id"),
            "source_node_id": element.get("sourceRef"),
            "target_node_id": element.get("targetRef"),
            "data_mapping": {},
        }

        # Extract label and data mapping from extension elements
        extension = element.find("bpmn:extensionElements", self.nsmap)
        if extension is not None:
            label_elem = extension.find("openwebui:label")
            if label_elem is not None and label_elem.text:
                edge_data["label"] = label_elem.text

            mapping_elem = extension.find("openwebui:dataMapping")
            if mapping_elem is not None and mapping_elem.text:
                try:
                    edge_data["data_mapping"] = json.loads(mapping_elem.text)
                except json.JSONDecodeError:
                    pass

        return edge_data

    def _extract_position(self, element: ET.Element) -> dict:
        """Extract position from extension elements."""
        extension = element.find("bpmn:extensionElements", self.nsmap)
        if extension is not None:
            pos_elem = extension.find("openwebui:position")
            if pos_elem is not None:
                return {
                    "x": float(pos_elem.get("x", 0)),
                    "y": float(pos_elem.get("y", 0)),
                }
        return {"x": 0, "y": 0}

    def _extract_config(self, element: ET.Element) -> dict:
        """Extract config from extension elements."""
        extension = element.find("bpmn:extensionElements", self.nsmap)
        if extension is not None:
            config_elem = extension.find("openwebui:config")
            if config_elem is not None and config_elem.text:
                try:
                    return json.loads(config_elem.text)
                except json.JSONDecodeError:
                    pass
        return {}

    def _format_xml(self, xml_string: str) -> str:
        """Format XML string with proper indentation."""
        try:
            import xml.dom.minidom
            dom = xml.dom.minidom.parseString(xml_string)
            formatted = dom.toprettyxml(indent="  ")
            # Remove empty lines
            lines = [line for line in formatted.split("\n") if line.strip()]
            return "\n".join(lines)
        except Exception:
            return xml_string


# Singleton instance
bpmn_converter = BPMNConverter()
