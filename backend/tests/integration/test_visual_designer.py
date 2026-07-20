"""
Integration tests for visual workflow designer CRUD operations.

Tests the visual workflow designer functionality including creating,
editing, saving, and loading workflows.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import json

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

from timbal.models import TimbalWorkflow, TimbalNode, TimbalExecutionStatus


class TestVisualDesignerCRUD:
    """Integration tests for visual workflow designer CRUD operations."""

    def test_create_workflow_visual(self, client, auth_headers):
        """T036-1: Verify creating a workflow via visual designer.

        Tests that workflows can be created with nodes and edges from the visual designer.
        """
        workflow_data = {
            "name": "Visual Workflow Test",
            "description": "Created via visual designer",
            "nodes": [
                {
                    "id": "node-1",
                    "type": "pm_data_source",
                    "config": {"project_id": "proj-123"},
                    "position_x": 100,
                    "position_y": 100
                },
                {
                    "id": "node-2",
                    "type": "get_requirements",
                    "config": {"filter": "active"},
                    "position_x": 300,
                    "position_y": 100
                }
            ],
            "edges": [
                {
                    "id": "edge-1",
                    "source": "node-1",
                    "target": "node-2"
                }
            ],
            "config": {"timeout": 30}
        }

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_workflow = MagicMock()
            mock_workflow.id = "wf-visual-123"
            mock_workflow.name = workflow_data["name"]
            mock_workflow.dict.return_value = {
                "id": "wf-visual-123",
                "name": workflow_data["name"],
                "description": workflow_data["description"],
                "nodes": workflow_data["nodes"],
                "edges": workflow_data["edges"],
                "config": workflow_data["config"],
                "version": "1.0.0",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            mock_service.create_workflow = AsyncMock(return_value=mock_workflow)
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/v1/timbal/workflows",
                json=workflow_data,
                headers=auth_headers
            )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert data["name"] == workflow_data["name"]

    def test_update_workflow_visual(self, client, auth_headers):
        """T036-2: Verify updating a workflow via visual designer.

        Tests that existing workflows can be modified with new nodes and edges.
        """
        workflow_id = "wf-visual-123"
        update_data = {
            "name": "Updated Visual Workflow",
            "description": "Updated via visual designer",
            "nodes": [
                {
                    "id": "node-1",
                    "type": "pm_data_source",
                    "config": {"project_id": "proj-123"},
                    "position_x": 100,
                    "position_y": 100
                },
                {
                    "id": "node-2",
                    "type": "get_requirements",
                    "config": {"filter": "active"},
                    "position_x": 300,
                    "position_y": 100
                },
                {
                    "id": "node-3",
                    "type": "analyze",
                    "config": {"analysis_type": "risk"},
                    "position_x": 500,
                    "position_y": 100
                }
            ],
            "edges": [
                {"id": "edge-1", "source": "node-1", "target": "node-2"},
                {"id": "edge-2", "source": "node-2", "target": "node-3"}
            ],
            "config": {"timeout": 60}
        }

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_workflow = MagicMock()
            mock_workflow.id = workflow_id
            mock_workflow.dict.return_value = {
                "id": workflow_id,
                "name": update_data["name"],
                "description": update_data["description"],
                "nodes": update_data["nodes"],
                "edges": update_data["edges"],
                "config": update_data["config"],
                "version": "1.0.1",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            mock_service.update_workflow = AsyncMock(return_value=mock_workflow)
            mock_get_service.return_value = mock_service

            response = client.put(
                f"/api/v1/timbal/workflows/{workflow_id}",
                json=update_data,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == workflow_id
        assert len(data["nodes"]) == 3

    def test_delete_workflow_visual(self, client, auth_headers):
        """T036-3: Verify deleting a workflow via visual designer.

        Tests that workflows can be deleted from the visual designer.
        """
        workflow_id = "wf-visual-123"

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.delete_workflow = AsyncMock(return_value=True)
            mock_get_service.return_value = mock_service

            response = client.delete(
                f"/api/v1/timbal/workflows/{workflow_id}",
                headers=auth_headers
            )

        assert response.status_code == 204

    def test_get_workflow_visual(self, client, auth_headers):
        """T036-4: Verify retrieving a workflow for visual designer.

        Tests that workflow data is returned in format suitable for visual editor.
        """
        workflow_id = "wf-visual-123"

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_workflow = MagicMock()
            mock_workflow.dict.return_value = {
                "id": workflow_id,
                "name": "Visual Workflow Test",
                "description": "Test workflow",
                "nodes": [
                    {
                        "id": "node-1",
                        "type": "pm_data_source",
                        "config": {"project_id": "proj-123"},
                        "position_x": 100,
                        "position_y": 100
                    }
                ],
                "edges": [],
                "config": {"timeout": 30},
                "version": "1.0.0",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            mock_service.get_workflow = AsyncMock(return_value=mock_workflow)
            mock_get_service.return_value = mock_service

            response = client.get(
                f"/api/v1/timbal/workflows/{workflow_id}",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == workflow_id
        assert "nodes" in data
        assert "edges" in data
        assert "config" in data

    def test_workflow_node_validation(self, client, auth_headers):
        """T036-5: Verify node validation in visual designer.

        Tests that invalid node configurations are rejected.
        """
        invalid_workflow = {
            "name": "Invalid Workflow",
            "description": "Should fail validation",
            "nodes": [
                {
                    "id": "node-1",
                    "type": "unknown_type",  # Invalid type
                    "config": {},
                    "position_x": -1,  # Invalid position
                    "position_y": 100
                }
            ],
            "edges": [],
            "config": {}
        }

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.create_workflow = AsyncMock(side_effect=ValueError("Invalid node type: unknown_type"))
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/v1/timbal/workflows",
                json=invalid_workflow,
                headers=auth_headers
            )

        assert response.status_code in [400, 422]

    def test_workflow_versioning(self, client, auth_headers):
        """T036-6: Verify workflow versioning in visual designer.

        Tests that saving a workflow creates a new version.
        """
        workflow_id = "wf-visual-versioned"
        workflow_data = {
            "name": "Versioned Workflow",
            "description": "Testing versioning",
            "nodes": [],
            "edges": [],
            "config": {}
        }

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_workflow = MagicMock()
            mock_workflow.dict.return_value = {
                "id": workflow_id,
                "name": workflow_data["name"],
                "description": workflow_data["description"],
                "nodes": [],
                "edges": [],
                "config": {},
                "version": "abc123def",  # Git-style version hash
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            mock_service.create_workflow = AsyncMock(return_value=mock_workflow)
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/v1/timbal/workflows",
                json=workflow_data,
                headers=auth_headers
            )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "version" in data
        assert len(data["version"]) > 0

    def test_workflow_save_and_reload(self, client, auth_headers):
        """T036-7: Verify workflow save and reload preserves layout.

        Tests that saving and reloading a workflow preserves node positions and connections.
        """
        workflow_id = "wf-save-reload"
        workflow_data = {
            "name": "Save and Reload Test",
            "description": "Testing persistence",
            "nodes": [
                {
                    "id": "node-1",
                    "type": "pm_data_source",
                    "config": {"project_id": "proj-123"},
                    "position_x": 150,
                    "position_y": 200
                },
                {
                    "id": "node-2",
                    "type": "analyze",
                    "config": {"type": "risk"},
                    "position_x": 450,
                    "position_y": 200
                }
            ],
            "edges": [
                {"id": "edge-1", "source": "node-1", "target": "node-2"}
            ],
            "config": {"timeout": 30}
        }

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_workflow = MagicMock()
            mock_workflow.dict.return_value = {
                "id": workflow_id,
                **workflow_data,
                "version": "1.0.0",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            mock_service.create_workflow = AsyncMock(return_value=mock_workflow)
            mock_get_service.return_value = mock_service

            # Save workflow
            response = client.post(
                "/api/v1/timbal/workflows",
                json=workflow_data,
                headers=auth_headers
            )

        assert response.status_code in [200, 201]
        data = response.json()

        # Verify layout preserved
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1
        assert data["nodes"][0]["position_x"] == 150
        assert data["nodes"][0]["position_y"] == 200
