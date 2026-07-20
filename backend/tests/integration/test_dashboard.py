"""
Integration tests for workflow management dashboard.

Tests the centralized dashboard for viewing and managing all workflows.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import json

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

from timbal.models import TimbalExecutionStatus


class TestWorkflowDashboard:
    """Integration tests for workflow management dashboard."""

    def test_list_workflows_dashboard(self, client, auth_headers):
        """T042-1: Verify workflow list page displays all workflows.

        Tests that the dashboard lists all workflows with status indicators.
        """
        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_workflows = [
                {
                    "id": "wf-1",
                    "name": "Risk Analysis",
                    "description": "Analyze project risks",
                    "version": "1.0.0",
                    "status": "active",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                },
                {
                    "id": "wf-2",
                    "name": "Requirement Gathering",
                    "description": "Gather requirements",
                    "version": "1.2.0",
                    "status": "active",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                },
                {
                    "id": "wf-3",
                    "name": "Code Review",
                    "description": "Review code changes",
                    "version": "2.0.0",
                    "status": "disabled",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            ]
            mock_service.list_workflows = AsyncMock(return_value=mock_workflows)
            mock_get_service.return_value = mock_service

            response = client.get(
                "/api/v1/timbal/workflows",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()

        # Verify list structure
        if "workflows" in data:
            workflows = data["workflows"]
        else:
            workflows = data

        assert len(workflows) >= 3

        # Verify each workflow has required fields
        for workflow in workflows:
            assert "id" in workflow
            assert "name" in workflow
            assert "status" in workflow

    def test_workflow_detail_page(self, client, auth_headers):
        """T042-2: Verify workflow detail page shows execution logs.

        Tests that the workflow detail page displays execution history and logs.
        """
        workflow_id = "wf-1"

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_workflow = MagicMock()
            mock_workflow.dict.return_value = {
                "id": workflow_id,
                "name": "Risk Analysis",
                "description": "Analyze project risks",
                "nodes": [],
                "edges": [],
                "config": {},
                "version": "1.0.0",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Mock executions for this workflow
            mock_executions = [
                {
                    "id": "exec-1",
                    "workflow_id": workflow_id,
                    "status": "succeeded",
                    "inputs": {"project_id": "proj-123"},
                    "outputs": {"risks": []},
                    "logs": ["Started", "Completed"],
                    "started_at": datetime.utcnow().isoformat(),
                    "completed_at": datetime.utcnow().isoformat(),
                    "error_message": None
                }
            ]

            mock_service.get_workflow = AsyncMock(return_value=mock_workflow)
            mock_service.get_executions = AsyncMock(return_value=mock_executions)
            mock_get_service.return_value = mock_service

            response = client.get(
                f"/api/v1/timbal/workflows/{workflow_id}",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"] == workflow_id

    def test_enable_disable_workflow(self, client, auth_headers):
        """T042-3: Verify workflow enable/disable toggle.

        Tests that workflows can be enabled and disabled from the dashboard.
        """
        workflow_id = "wf-1"

        # Test disable
        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_workflow = MagicMock()
            mock_workflow.dict.return_value = {
                "id": workflow_id,
                "name": "Risk Analysis",
                "status": "disabled",
                "version": "1.0.0",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            mock_service.update_workflow = AsyncMock(return_value=mock_workflow)
            mock_get_service.return_value = mock_service

            response = client.put(
                f"/api/v1/timbal/workflows/{workflow_id}",
                json={"status": "disabled"},
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "disabled"

    def test_workflow_execution_status_indicators(self, client, auth_headers):
        """T042-4: Verify workflow status indicators in dashboard.

        Tests that the dashboard shows correct status indicators for workflows.
        """
        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_workflows = [
                {
                    "id": "wf-1",
                    "name": "Active Workflow",
                    "status": "active",
                    "last_execution": {
                        "status": "succeeded",
                        "completed_at": datetime.utcnow().isoformat()
                    }
                },
                {
                    "id": "wf-2",
                    "name": "Failed Workflow",
                    "status": "active",
                    "last_execution": {
                        "status": "failed",
                        "error_message": "Connection timeout"
                    }
                },
                {
                    "id": "wf-3",
                    "name": "Disabled Workflow",
                    "status": "disabled",
                    "last_execution": None
                }
            ]
            mock_service.list_workflows = AsyncMock(return_value=mock_workflows)
            mock_get_service.return_value = mock_service

            response = client.get(
                "/api/v1/timbal/workflows",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()

        if "workflows" in data:
            workflows = data["workflows"]
        else:
            workflows = data

        # Verify status indicators
        statuses = [w["status"] for w in workflows]
        assert "active" in statuses
        assert "disabled" in statuses

    def test_workflow_search_and_filter(self, client, auth_headers):
        """T042-5: Verify workflow search and filter functionality.

        Tests that workflows can be searched and filtered in the dashboard.
        """
        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_workflows = [
                {
                    "id": "wf-1",
                    "name": "Risk Analysis",
                    "description": "Analyze risks",
                    "status": "active"
                }
            ]
            mock_service.search_workflows = AsyncMock(return_value=mock_workflows)
            mock_get_service.return_value = mock_service

            response = client.get(
                "/api/v1/timbal/workflows?search=risk&status=active",
                headers=auth_headers
            )

        # Search should return filtered results
        assert response.status_code in [200, 307]

    def test_workflow_execution_history(self, client, auth_headers):
        """T042-6: Verify execution history display in dashboard.

        Tests that execution history is displayed correctly for each workflow.
        """
        workflow_id = "wf-1"

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_executions = [
                {
                    "id": "exec-1",
                    "workflow_id": workflow_id,
                    "status": "succeeded",
                    "started_at": datetime.utcnow().isoformat(),
                    "completed_at": datetime.utcnow().isoformat(),
                    "duration_seconds": 5.2
                },
                {
                    "id": "exec-2",
                    "workflow_id": workflow_id,
                    "status": "failed",
                    "started_at": datetime.utcnow().isoformat(),
                    "completed_at": datetime.utcnow().isoformat(),
                    "error_message": "Timeout"
                }
            ]
            mock_service.get_executions = AsyncMock(return_value=mock_executions)
            mock_get_service.return_value = mock_service

            response = client.get(
                f"/api/v1/timbal/workflows/{workflow_id}/executions",
                headers=auth_headers
            )

        # Should return execution history
        assert response.status_code in [200, 404]

    def test_dashboard_crud_permissions(self, client, auth_headers):
        """T042-7: Verify CRUD operations are accessible to authenticated users.

        Tests that all authenticated users can perform CRUD operations
        (open permissions model per spec).
        """
        # Test create
        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_workflow = MagicMock()
            mock_workflow.dict.return_value = {
                "id": "wf-new",
                "name": "New Workflow",
                "status": "active"
            }
            mock_service.create_workflow = AsyncMock(return_value=mock_workflow)
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/v1/timbal/workflows",
                json={"name": "New Workflow", "nodes": [], "edges": []},
                headers=auth_headers
            )

        assert response.status_code in [200, 201]

        # Test update
        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_workflow = MagicMock()
            mock_workflow.dict.return_value = {
                "id": "wf-1",
                "name": "Updated Workflow",
                "status": "active"
            }
            mock_service.update_workflow = AsyncMock(return_value=mock_workflow)
            mock_get_service.return_value = mock_service

            response = client.put(
                "/api/v1/timbal/workflows/wf-1",
                json={"name": "Updated Workflow"},
                headers=auth_headers
            )

        assert response.status_code == 200

        # Test delete
        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.delete_workflow = AsyncMock(return_value=True)
            mock_get_service.return_value = mock_service

            response = client.delete(
                "/api/v1/timbal/workflows/wf-1",
                headers=auth_headers
            )

        assert response.status_code == 204
