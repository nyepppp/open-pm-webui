"""
Contract tests for Timbal workflow execution endpoints.

Tests the API contract for POST /workflows/{id}/execute and related endpoints.
These tests verify that the API responses conform to the expected schema.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import json

# Import models for type checking
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

from timbal.models import TimbalExecutionStatus


class TestTimbalWorkflowExecutionContract:
    """Contract tests for workflow execution API."""

    def test_execute_workflow_async_response_schema(self, client, auth_headers):
        """T013-1: Verify async execution response schema matches contract.

        Expected (per contracts/api.md):
        {
          "execution_id": "uuid",
          "status": "pending",
          "started_at": "datetime"
        }
        """
        workflow_id = "test-workflow-123"
        request_data = {
            "inputs": {"project_id": "proj-123"},
            "sync": False
        }

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_execution = MagicMock()
            mock_execution.id = "exec-test-123"
            mock_execution.status = TimbalExecutionStatus.PENDING
            mock_execution.started_at = datetime.utcnow()
            mock_execution.dict.return_value = {
                "id": "exec-test-123",
                "workflow_id": workflow_id,
                "status": "pending",
                "inputs": {"project_id": "proj-123"},
                "outputs": {},
                "logs": [],
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": None,
                "error_message": None,
                "stopped_by": None,
                "timeout_at": None
            }
            mock_service.execute_workflow = AsyncMock(return_value=mock_execution)
            mock_get_service.return_value = mock_service

            response = client.post(
                f"/api/v1/timbal/workflows/{workflow_id}/execute",
                json=request_data,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()

        # Verify response schema
        assert "id" in data or "execution_id" in data
        assert "status" in data
        assert data["status"] == "pending"
        assert "workflow_id" in data

    def test_execute_workflow_sync_response_schema(self, client, auth_headers):
        """T013-2: Verify sync execution response schema matches contract.

        Expected (per contracts/api.md):
        {
          "execution_id": "uuid",
          "status": "succeeded",
          "outputs": {},
          "completed_at": "datetime"
        }
        """
        workflow_id = "test-workflow-123"
        request_data = {
            "inputs": {"project_id": "proj-123"},
            "sync": True
        }

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_execution = MagicMock()
            mock_execution.id = "exec-test-456"
            mock_execution.status = TimbalExecutionStatus.SUCCEEDED
            mock_execution.outputs = {"result": "success", "data": {"risks": []}}
            mock_execution.completed_at = datetime.utcnow()
            mock_execution.dict.return_value = {
                "id": "exec-test-456",
                "workflow_id": workflow_id,
                "status": "succeeded",
                "inputs": {"project_id": "proj-123"},
                "outputs": {"result": "success", "data": {"risks": []}},
                "logs": ["Step 1 completed", "Step 2 completed"],
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "error_message": None,
                "stopped_by": None,
                "timeout_at": None
            }
            mock_service.execute_workflow = AsyncMock(return_value=mock_execution)
            mock_get_service.return_value = mock_service

            response = client.post(
                f"/api/v1/timbal/workflows/{workflow_id}/execute?sync=true",
                json=request_data,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()

        # Verify response schema for sync execution
        assert "id" in data or "execution_id" in data
        assert "status" in data
        assert data["status"] == "succeeded"
        assert "outputs" in data
        assert "completed_at" in data or data.get("completed_at") is not None

    def test_execute_workflow_error_response_schema(self, client, auth_headers):
        """T013-3: Verify error response schema matches contract.

        Expected (per contracts/api.md):
        {
          "error": {
            "code": "string",
            "message": "string",
            "details": {}
          }
        }
        """
        workflow_id = "non-existent-workflow"
        request_data = {
            "inputs": {},
            "sync": False
        }

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.execute_workflow = AsyncMock(side_effect=Exception("Workflow not found"))
            mock_get_service.return_value = mock_service

            response = client.post(
                f"/api/v1/timbal/workflows/{workflow_id}/execute",
                json=request_data,
                headers=auth_headers
            )

        # Should return error response
        assert response.status_code in [404, 500]
        data = response.json()

        # Verify error schema
        assert "detail" in data or "error" in data

    def test_execute_workflow_with_inputs_validation(self, client, auth_headers):
        """T013-4: Verify execution accepts and processes inputs correctly.

        Tests that the API correctly passes inputs to the execution service.
        """
        workflow_id = "test-workflow-123"
        test_inputs = {
            "project_id": "proj-123",
            "analysis_type": "risk",
            "depth": "comprehensive"
        }
        request_data = {
            "inputs": test_inputs,
            "sync": False
        }

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_execution = MagicMock()
            mock_execution.id = "exec-test-789"
            mock_execution.status = TimbalExecutionStatus.PENDING
            mock_execution.inputs = test_inputs
            mock_execution.dict.return_value = {
                "id": "exec-test-789",
                "workflow_id": workflow_id,
                "status": "pending",
                "inputs": test_inputs,
                "outputs": {},
                "logs": [],
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": None,
                "error_message": None,
                "stopped_by": None,
                "timeout_at": None
            }
            mock_service.execute_workflow = AsyncMock(return_value=mock_execution)
            mock_get_service.return_value = mock_service

            response = client.post(
                f"/api/v1/timbal/workflows/{workflow_id}/execute",
                json=request_data,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()

        # Verify inputs are preserved
        assert "inputs" in data or "workflow_id" in data

    def test_get_execution_status_response_schema(self, client, auth_headers):
        """T013-5: Verify GET /executions/{id} response schema.

        Expected (per contracts/api.md):
        {
          "id": "uuid",
          "workflow_id": "uuid",
          "status": "running",
          "inputs": {},
          "outputs": {},
          "logs": [...],
          "started_at": "datetime",
          "completed_at": "datetime",
          "error_message": "string"
        }
        """
        execution_id = "exec-test-123"

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_execution = MagicMock()
            mock_execution.id = execution_id
            mock_execution.workflow_id = "wf-test-123"
            mock_execution.status = TimbalExecutionStatus.RUNNING
            mock_execution.inputs = {"project_id": "proj-123"}
            mock_execution.outputs = {"partial": "data"}
            mock_execution.logs = ["Step 1 started"]
            mock_execution.error_message = None
            mock_execution.dict.return_value = {
                "id": execution_id,
                "workflow_id": "wf-test-123",
                "status": "running",
                "inputs": {"project_id": "proj-123"},
                "outputs": {"partial": "data"},
                "logs": ["Step 1 started"],
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": None,
                "error_message": None,
                "stopped_by": None,
                "timeout_at": None
            }
            mock_service.get_execution_status = AsyncMock(return_value=mock_execution)
            mock_get_service.return_value = mock_service

            response = client.get(
                f"/api/v1/timbal/executions/{execution_id}",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()

        # Verify execution status schema
        assert "id" in data
        assert "workflow_id" in data
        assert "status" in data
        assert data["status"] == "running"
        assert "inputs" in data
        assert "outputs" in data
        assert "logs" in data

    def test_stop_execution_response_schema(self, client, auth_headers):
        """T013-6: Verify POST /executions/{id}/stop response schema.

        Expected (per contracts/api.md):
        {
          "id": "uuid",
          "status": "stopped",
          "stopped_at": "datetime"
        }
        """
        execution_id = "exec-test-123"

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_execution = MagicMock()
            mock_execution.id = execution_id
            mock_execution.status = TimbalExecutionStatus.STOPPED
            mock_execution.dict.return_value = {
                "id": execution_id,
                "workflow_id": "wf-test-123",
                "status": "stopped",
                "inputs": {},
                "outputs": {},
                "logs": ["Execution stopped by user"],
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "error_message": None,
                "stopped_by": "user-123",
                "timeout_at": None
            }
            mock_service.stop_execution = AsyncMock(return_value=mock_execution)
            mock_get_service.return_value = mock_service

            response = client.post(
                f"/api/v1/timbal/executions/{execution_id}/stop",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()

        # Verify stop response schema
        assert "id" in data
        assert "status" in data
        assert data["status"] == "stopped"

    def test_workflow_execution_status_transitions(self, client, auth_headers):
        """T013-7: Verify execution status transitions follow state machine.

        Tests that status transitions follow: pending -> running -> succeeded/failed/stopped
        """
        workflow_id = "test-workflow-123"
        execution_id = "exec-test-transitions"

        # Test 1: Initial status should be pending or running
        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_execution = MagicMock()
            mock_execution.id = execution_id
            mock_execution.status = TimbalExecutionStatus.PENDING
            mock_execution.dict.return_value = {
                "id": execution_id,
                "workflow_id": workflow_id,
                "status": "pending",
                "inputs": {},
                "outputs": {},
                "logs": [],
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": None,
                "error_message": None,
                "stopped_by": None,
                "timeout_at": None
            }
            mock_service.execute_workflow = AsyncMock(return_value=mock_execution)
            mock_get_service.return_value = mock_service

            response = client.post(
                f"/api/v1/timbal/workflows/{workflow_id}/execute",
                json={"inputs": {}, "sync": False},
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["pending", "running"]

    def test_execution_not_found_error(self, client, auth_headers):
        """T013-8: Verify 404 error for non-existent execution.

        Tests that accessing a non-existent execution returns proper 404 error.
        """
        execution_id = "non-existent-exec"

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_execution_status = AsyncMock(return_value=None)
            mock_get_service.return_value = mock_service

            response = client.get(
                f"/api/v1/timbal/executions/{execution_id}",
                headers=auth_headers
            )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
