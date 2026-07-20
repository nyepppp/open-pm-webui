"""
JSON Converter Service

Handles conversion between workflow definitions and JSON format.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional


class JSONConverter:
    """Converts between workflow definitions and JSON format."""

    def workflow_to_json(self, workflow: dict) -> str:
        """Convert a workflow definition to JSON string.

        Args:
            workflow: Workflow definition with nodes and edges

        Returns:
            JSON string
        """
        export_data = {
            "version": "2.0",
            "exported_at": datetime.utcnow().isoformat(),
            "name": workflow.get("name", "Workflow"),
            "description": workflow.get("description", ""),
            "nodes": workflow.get("nodes", []),
            "edges": workflow.get("edges", []),
        }
        return json.dumps(export_data, indent=2, ensure_ascii=False)

    def json_to_workflow(self, json_string: str) -> dict:
        """Convert a JSON string to a workflow definition.

        Args:
            json_string: JSON string

        Returns:
            Workflow definition with nodes and edges

        Raises:
            ValueError: If the JSON is invalid
        """
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        return {
            "name": data.get("name", "Imported Workflow"),
            "description": data.get("description", ""),
            "nodes": data.get("nodes", []),
            "edges": data.get("edges", []),
        }

    def workflow_to_detailed_json(self, workflow: dict) -> str:
        """Convert a workflow definition to detailed JSON with all metadata.

        Args:
            workflow: Workflow definition with nodes and edges

        Returns:
            JSON string with complete workflow data
        """
        export_data = {
            "version": "2.0",
            "exported_at": datetime.utcnow().isoformat(),
            "format": "openwebui-workflow",
            "name": workflow.get("name", "Workflow"),
            "description": workflow.get("description", ""),
            "id": workflow.get("id", str(uuid.uuid4())),
            "status": workflow.get("status", "draft"),
            "nodes": self._process_nodes_for_export(workflow.get("nodes", [])),
            "edges": self._process_edges_for_export(workflow.get("edges", [])),
            "metadata": {
                "node_count": len(workflow.get("nodes", [])),
                "edge_count": len(workflow.get("edges", [])),
                "export_type": "detailed",
            }
        }
        return json.dumps(export_data, indent=2, ensure_ascii=False)

    def detailed_json_to_workflow(self, json_string: str) -> dict:
        """Convert detailed JSON to workflow definition.

        Args:
            json_string: JSON string

        Returns:
            Workflow definition with nodes and edges
        """
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        nodes = self._process_nodes_for_import(data.get("nodes", []))
        edges = self._process_edges_for_import(data.get("edges", []))

        return {
            "name": data.get("name", "Imported Workflow"),
            "description": data.get("description", ""),
            "id": data.get("id", str(uuid.uuid4())),
            "status": data.get("status", "draft"),
            "nodes": nodes,
            "edges": edges,
        }

    def _process_nodes_for_export(self, nodes: List[dict]) -> List[dict]:
        """Process nodes for export, ensuring all data is preserved."""
        processed = []
        for node in nodes:
            processed_node = {
                "id": node.get("id"),
                "type": node.get("type", "custom"),
                "name": node.get("name", "Node"),
                "position": node.get("position", {"x": 0, "y": 0}),
                "config": node.get("config", {}),
            }
            
            # Include optional fields if present
            if "input_schema" in node:
                processed_node["input_schema"] = node["input_schema"]
            if "output_schema" in node:
                processed_node["output_schema"] = node["output_schema"]
            if "script" in node:
                processed_node["script"] = node["script"]
            if "skill_id" in node:
                processed_node["skill_id"] = node["skill_id"]
            
            processed.append(processed_node)
        return processed

    def _process_edges_for_export(self, edges: List[dict]) -> List[dict]:
        """Process edges for export, ensuring all data is preserved."""
        processed = []
        for edge in edges:
            processed_edge = {
                "id": edge.get("id"),
                "source_node_id": edge.get("source_node_id") or edge.get("source"),
                "target_node_id": edge.get("target_node_id") or edge.get("target"),
            }
            
            # Include optional fields
            if "data_mapping" in edge:
                processed_edge["data_mapping"] = edge["data_mapping"]
            if "data_mapping_rules" in edge:
                processed_edge["data_mapping_rules"] = edge["data_mapping_rules"]
            if "label" in edge:
                processed_edge["label"] = edge["label"]
            
            processed.append(processed_edge)
        return processed

    def _process_nodes_for_import(self, nodes: List[dict]) -> List[dict]:
        """Process nodes for import, normalizing field names."""
        processed = []
        for node in nodes:
            processed_node = {
                "id": node.get("id", str(uuid.uuid4())),
                "type": node.get("type", "custom"),
                "name": node.get("name", "Node"),
                "position": node.get("position", {"x": 0, "y": 0}),
                "config": node.get("config", {}),
            }
            
            # Handle position_x/position_y if position is not present
            if "position" not in node:
                position = {
                    "x": node.get("position_x", 0),
                    "y": node.get("position_y", 0),
                }
                processed_node["position"] = position
            
            # Include optional fields
            if "input_schema" in node:
                processed_node["input_schema"] = node["input_schema"]
            if "output_schema" in node:
                processed_node["output_schema"] = node["output_schema"]
            if "script" in node:
                processed_node["script"] = node["script"]
            if "skill_id" in node:
                processed_node["skill_id"] = node["skill_id"]
            
            processed.append(processed_node)
        return processed

    def _process_edges_for_import(self, edges: List[dict]) -> List[dict]:
        """Process edges for import, normalizing field names."""
        processed = []
        for edge in edges:
            processed_edge = {
                "id": edge.get("id", str(uuid.uuid4())),
                "source_node_id": edge.get("source_node_id") or edge.get("source"),
                "target_node_id": edge.get("target_node_id") or edge.get("target"),
                "data_mapping": edge.get("data_mapping", {}),
            }
            
            # Include optional fields
            if "data_mapping_rules" in edge:
                processed_edge["data_mapping_rules"] = edge["data_mapping_rules"]
            if "label" in edge:
                processed_edge["label"] = edge["label"]
            
            processed.append(processed_edge)
        return processed


# Singleton instance
json_converter = JSONConverter()
