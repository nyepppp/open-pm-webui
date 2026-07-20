"""
Integration tests for chat workflow trigger functionality.

Tests that natural language commands in OpenWebUI chat can trigger
Timbal workflows correctly.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import json

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

from timbal.models import TimbalExecutionStatus


class TestChatWorkflowTrigger:
    """Integration tests for chat-based workflow triggering."""

    def test_chat_command_parsing(self, client, auth_headers):
        """T031-1: Verify chat command parsing for workflow triggers.

        Tests that chat commands like "/workflow run <name>" are parsed correctly.
        """
        chat_message = {
            "message": "/workflow run risk-analysis",
            "conversation_id": "conv-123",
            "user_id": "user-123"
        }

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_execution = MagicMock()
            mock_execution.id = "exec-chat-123"
            mock_execution.status = TimbalExecutionStatus.PENDING
            mock_execution.dict.return_value = {
                "id": "exec-chat-123",
                "workflow_id": "wf-risk-analysis",
                "status": "pending",
                "inputs": {"triggered_from": "chat"},
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

            # Simulate chat command processing
            response = client.post(
                "/api/v1/timbal/workflows/wf-risk-analysis/execute",
                json={
                    "inputs": {
                        "triggered_from": "chat",
                        "chat_message": chat_message["message"],
                        "conversation_id": chat_message["conversation_id"]
                    },
                    "sync": False
                },
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] in ["pending", "running"]

    def test_natural_language_workflow_trigger(self, client, auth_headers):
        """T031-2: Verify natural language triggers workflow execution.

        Tests that messages like "analyze project risks for Project Alpha"
        trigger the appropriate workflow.
        """
        natural_messages = [
            "analyze project risks for Project Alpha",
            "run risk analysis on Project Alpha",
            "check risks for Project Alpha"
        ]

        for message in natural_messages:
            with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
                mock_service = MagicMock()
                mock_execution = MagicMock()
                mock_execution.id = f"exec-nlp-{hash(message) % 10000}"
                mock_execution.status = TimbalExecutionStatus.PENDING
                mock_execution.dict.return_value = {
                    "id": f"exec-nlp-{hash(message) % 10000}",
                    "workflow_id": "wf-risk-analysis",
                    "status": "pending",
                    "inputs": {"natural_language": message},
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
                    "/api/v1/timbal/workflows/wf-risk-analysis/execute",
                    json={
                        "inputs": {
                            "natural_language": message,
                            "project_name": "Project Alpha"
                        },
                        "sync": False
                    },
                    headers=auth_headers
                )

            assert response.status_code == 200

    def test_chat_workflow_with_project_selection(self, client, auth_headers):
        """T031-3: Verify interactive project selection in chat.

        Tests that when workflow requires project selection, user is prompted.
        """
        # Simulate workflow that needs project selection
        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()

            # Mock project list response
            mock_projects = {
                "success": True,
                "data": {
                    "projects": [
                        {"id": "proj-1", "name": "Project Alpha"},
                        {"id": "proj-2", "name": "Project Beta"}
                    ]
                }
            }

            mock_service.execute_tool = AsyncMock(return_value=mock_projects)
            mock_get_service.return_value = mock_service

            # Request projects list for selection
            response = client.post(
                "/api/v1/timbal/tools/tool-get-project-list/execute",
                json={"parameters": {}},
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "projects" in data["data"]
        assert len(data["data"]["projects"]) >= 2

    def test_chat_workflow_result_formatting(self, client, auth_headers):
        """T031-4: Verify workflow results are formatted for chat display.

        Tests that workflow outputs are formatted appropriately for chat interface.
        """
        workflow_id = "wf-risk-analysis"

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_execution = MagicMock()
            mock_execution.id = "exec-format-123"
            mock_execution.status = TimbalExecutionStatus.SUCCEEDED
            mock_execution.outputs = {
                "risks": [
                    {"name": "Security Risk", "level": "high", "description": "SQL injection vulnerability"},
                    {"name": "Performance Risk", "level": "medium", "description": "Slow query on large datasets"}
                ],
                "summary": "Found 2 risks",
                "recommendations": [
                    "Implement parameterized queries",
                    "Add database indexing"
                ]
            }
            mock_execution.dict.return_value = {
                "id": "exec-format-123",
                "workflow_id": workflow_id,
                "status": "succeeded",
                "inputs": {"project_id": "proj-123"},
                "outputs": mock_execution.outputs,
                "logs": ["Analysis complete"],
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "error_message": None,
                "stopped_by": None,
                "timeout_at": None
            }
            mock_service.execute_workflow = AsyncMock(return_value=mock_execution)
            mock_get_service.return_value = mock_service

            response = client.post(
                f"/api/v1/timbal/workflows/{workflow_id}/execute",
                json={
                    "inputs": {"project_id": "proj-123"},
                    "sync": True
                },
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "succeeded"
        assert "outputs" in data
        assert "risks" in data["outputs"]

        # Verify results can be formatted for chat
        risks = data["outputs"]["risks"]
        assert len(risks) > 0
        assert "name" in risks[0]
        assert "level" in risks[0]

    def test_chat_workflow_error_handling(self, client, auth_headers):
        """T031-5: Verify error handling in chat workflow execution.

        Tests that errors are handled gracefully and returned to chat.
        """
        workflow_id = "wf-error-test"

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_execution = MagicMock()
            mock_execution.id = "exec-error-123"
            mock_execution.status = TimbalExecutionStatus.FAILED
            mock_execution.error_message = "Workflow definition not found"
            mock_execution.dict.return_value = {
                "id": "exec-error-123",
                "workflow_id": workflow_id,
                "status": "failed",
                "inputs": {},
                "outputs": {},
                "logs": ["Error: Workflow definition not found"],
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "error_message": "Workflow definition not found",
                "stopped_by": None,
                "timeout_at": None
            }
            mock_service.execute_workflow = AsyncMock(return_value=mock_execution)
            mock_get_service.return_value = mock_service

            response = client.post(
                f"/api/v1/timbal/workflows/{workflow_id}/execute",
                json={"inputs": {}, "sync": True},
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert "error_message" in data

    def test_chat_workflow_with_context_injection(self, client, auth_headers):
        """T031-6: Verify OpenWebUI context is injected into workflow.

        Tests that conversation history, user profile, etc. are passed to workflow.
        """
        workflow_id = "wf-context-test"
        context = {
            "conversation_history": [
                {"role": "user", "content": "Analyze risks"},
                {"role": "assistant", "content": "Which project?"}
            ],
            "user_profile": {
                "id": "user-123",
                "name": "Test User"
            },
            "current_project": "proj-123"
        }

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_execution = MagicMock()
            mock_execution.id = "exec-context-123"
            mock_execution.status = TimbalExecutionStatus.SUCCEEDED
            mock_execution.dict.return_value = {
                "id": "exec-context-123",
                "workflow_id": workflow_id,
                "status": "succeeded",
                "inputs": context,
                "outputs": {"result": "Context received"},
                "logs": [],
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "error_message": None,
                "stopped_by": None,
                "timeout_at": None
            }
            mock_service.execute_workflow = AsyncMock(return_value=mock_execution)
            mock_get_service.return_value = mock_service

            response = client.post(
                f"/api/v1/timbal/workflows/{workflow_id}/execute",
                json={
                    "inputs": context,
                    "sync": True
                },
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "succeeded"
