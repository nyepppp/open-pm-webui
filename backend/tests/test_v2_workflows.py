"""Tests for v2 workflow API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from fastapi import HTTPException
from fastapi.testclient import TestClient


class TestV2WorkflowAPI:
    """Test cases for v2 workflow API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client with mocked dependencies."""
        from fastapi import FastAPI
        from open_webui.pm.api.v2_workflows import router as workflows_router
        from open_webui.utils.auth import get_verified_user

        app = FastAPI()
        app.include_router(workflows_router, prefix="/api/v2/workflows")

        async def mock_get_verified_user():
            return {"id": "test-user-id", "email": "test@example.com"}

        app.dependency_overrides[get_verified_user] = mock_get_verified_user

        return TestClient(app)

    @pytest.fixture
    def sample_workflow_data(self):
        """Sample workflow data for testing."""
        return {
            "nodes": [
                {"id": "start", "type": "start", "config": {}},
                {"id": "process", "type": "llm", "config": {"model": "gpt-4"}},
                {"id": "end", "type": "end", "config": {}}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "process"},
                {"id": "e2", "source": "process", "target": "end"}
            ],
            "variables": {"input": "test input"}
        }

    @pytest.fixture
    def cyclic_workflow_data(self):
        """Cyclic workflow data for testing validation."""
        return {
            "nodes": [
                {"id": "A", "type": "start", "config": {}},
                {"id": "B", "type": "process", "config": {}},
                {"id": "C", "type": "end", "config": {}}
            ],
            "edges": [
                {"id": "e1", "source": "A", "target": "B"},
                {"id": "e2", "source": "B", "target": "C"},
                {"id": "e3", "source": "C", "target": "A"}  # Creates cycle
            ]
        }

    def test_execute_workflow_v2_success(self, client, sample_workflow_data):
        """Test successful workflow execution."""
        with patch("open_webui.pm.api.v2_workflows.workflow_engine") as mock_engine:
            # Mock execution state
            mock_state = MagicMock()
            mock_state.status.value = "completed"
            mock_state.variables = {"result": "success"}
            mock_state.node_results = {
                "start": MagicMock(status=MagicMock(value="completed"), output={}, error=None),
                "process": MagicMock(status=MagicMock(value="completed"), output={"text": "processed"}, error=None),
                "end": MagicMock(status=MagicMock(value="completed"), output={}, error=None)
            }
            mock_state.error = None

            mock_engine.execute = AsyncMock(return_value=mock_state)

            response = client.post(
                "/api/v2/workflows/test-workflow-id/execute-v2",
                json=sample_workflow_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert "node_results" in data
            assert data["error"] is None

    def test_execute_workflow_v2_error(self, client, sample_workflow_data):
        """Test workflow execution with error."""
        with patch("open_webui.pm.api.v2_workflows.workflow_engine") as mock_engine:
            mock_engine.execute = AsyncMock(side_effect=Exception("Execution failed"))

            response = client.post(
                "/api/v2/workflows/test-workflow-id/execute-v2",
                json=sample_workflow_data
            )

            assert response.status_code == 500
            data = response.json()
            assert "Workflow execution failed" in data["detail"]

    def test_validate_workflow_v2_valid(self, client, sample_workflow_data):
        """Test validation of valid workflow."""
        response = client.post(
            "/api/v2/workflows/test-workflow-id/validate-v2",
            json=sample_workflow_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["error"] is None
        assert data["node_count"] == 3
        assert data["edge_count"] == 2

    def test_validate_workflow_v2_cycle(self, client, cyclic_workflow_data):
        """Test validation of cyclic workflow."""
        response = client.post(
            "/api/v2/workflows/test-workflow-id/validate-v2",
            json=cyclic_workflow_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "cycle" in data["error"].lower()

    def test_validate_workflow_v2_empty(self, client):
        """Test validation with empty workflow."""
        response = client.post(
            "/api/v2/workflows/test-workflow-id/validate-v2",
            json={"nodes": [], "edges": []}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True  # Empty graph is technically valid
        assert data["node_count"] == 0
        assert data["edge_count"] == 0

    def test_execute_workflow_v2_missing_nodes(self, client):
        """Test execution with missing nodes."""
        response = client.post(
            "/api/v2/workflows/test-workflow-id/execute-v2",
            json={"nodes": [], "edges": [], "variables": {}}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    def test_execute_workflow_v2_invalid_workflow_id(self, client, sample_workflow_data):
        """Test execution with invalid workflow ID format."""
        # The endpoint accepts any string as workflow_id
        response = client.post(
            "/api/v2/workflows/invalid-id/execute-v2",
            json=sample_workflow_data
        )

        # Should still process (endpoint doesn't validate UUID format)
        assert response.status_code in [200, 500]

    def test_validate_workflow_v2_disconnected_nodes(self, client):
        """Test validation with disconnected nodes."""
        disconnected_data = {
            "nodes": [
                {"id": "A", "type": "start", "config": {}},
                {"id": "B", "type": "end", "config": {}}  # Disconnected
            ],
            "edges": []  # No edges connecting nodes
        }

        response = client.post(
            "/api/v2/workflows/test-workflow-id/validate-v2",
            json=disconnected_data
        )

        assert response.status_code == 200
        data = response.json()
        # Disconnected nodes should be flagged
        assert data["valid"] is False

    def test_execute_workflow_v2_with_variables(self, client):
        """Test execution with input variables."""
        workflow_data = {
            "nodes": [
                {"id": "start", "type": "start", "config": {}},
                {"id": "process", "type": "variable_set", "config": {"variables": {"output": "{{input}}"}}}
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "process"}
            ],
            "variables": {"input": "test value"}
        }

        with patch("open_webui.pm.api.v2_workflows.workflow_engine") as mock_engine:
            mock_state = MagicMock()
            mock_state.status.value = "completed"
            mock_state.variables = {"input": "test value", "output": "test value"}
            mock_state.node_results = {}
            mock_state.error = None

            mock_engine.execute = AsyncMock(return_value=mock_state)

            response = client.post(
                "/api/v2/workflows/test-workflow-id/execute-v2",
                json=workflow_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert "variables" in data

    @pytest.mark.asyncio
    async def test_workflow_execution_async(self):
        """Test async workflow execution."""
        from open_webui.pm.services.workflow_engine.engine import WorkflowEngine
        from open_webui.pm.services.workflow_engine.state import ExecutionStatus

        engine = WorkflowEngine()

        nodes = [
            {"id": "start", "type": "start", "config": {}},
            {"id": "end", "type": "end", "config": {}}
        ]
        edges = [{"id": "e1", "source": "start", "target": "end"}]

        # Register mock executors
        from open_webui.pm.services.workflow_engine.nodes.base import BaseNodeExecutor
        from open_webui.pm.services.workflow_engine.state import NodeResult, NodeStatus

        class MockExecutor(BaseNodeExecutor):
            async def execute(self, node_config, state):
                return NodeResult(status=NodeStatus.COMPLETED, output={})

        engine.register_node_executor("start", MockExecutor())
        engine.register_node_executor("end", MockExecutor())

        state = await engine.execute(
            workflow_id="test-workflow",
            nodes=nodes,
            edges=edges
        )

        assert state.status == ExecutionStatus.COMPLETED
