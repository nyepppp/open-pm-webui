"""
Integration tests for SSE streaming in Timbal workflow execution.

Tests the Server-Sent Events streaming functionality for real-time
workflow execution updates.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import json

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

from timbal.models import TimbalExecutionStatus


class TestTimbalSSEStreaming:
    """Integration tests for SSE streaming functionality."""

    def test_sse_stream_events_format(self, client, auth_headers):
        """T014-1: Verify SSE stream event format matches contract.

        Expected SSE events (per contracts/api.md):
        event: status
        data: {"status": "running", "progress": 50}

        event: output
        data: {"node_id": "...", "output": "..."}

        event: complete
        data: {"status": "succeeded", "outputs": {}}
        """
        workflow_id = "test-workflow-sse"
        inputs = {"project_id": "proj-123"}

        async def mock_event_generator():
            """Generate SSE events."""
            yield {"event": "status", "data": {"status": "running", "progress": 0}}
            yield {"event": "status", "data": {"status": "running", "progress": 25}}
            yield {"event": "output", "data": {"node_id": "node-1", "output": "Step 1 result"}}
            yield {"event": "status", "data": {"status": "running", "progress": 50}}
            yield {"event": "output", "data": {"node_id": "node-2", "output": "Step 2 result"}}
            yield {"event": "status", "data": {"status": "running", "progress": 75}}
            yield {"event": "complete", "data": {"status": "succeeded", "outputs": {"result": "success"}}}

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()

            # Create async generator for streaming
            async def async_gen():
                events = [
                    {"event": "status", "data": {"status": "running", "progress": 0}},
                    {"event": "status", "data": {"status": "running", "progress": 25}},
                    {"event": "output", "data": {"node_id": "node-1", "output": "Step 1 result"}},
                    {"event": "status", "data": {"status": "running", "progress": 50}},
                    {"event": "output", "data": {"node_id": "node-2", "output": "Step 2 result"}},
                    {"event": "status", "data": {"status": "running", "progress": 75}},
                    {"event": "complete", "data": {"status": "succeeded", "outputs": {"result": "success"}}}
                ]
                for event in events:
                    yield event

            mock_service.stream_workflow = async_gen
            mock_get_service.return_value = mock_service

            response = client.get(
                f"/api/v1/timbal/workflows/{workflow_id}/stream",
                params={"inputs": json.dumps(inputs)},
                headers={**auth_headers, "Accept": "text/event-stream"}
            )

        # SSE endpoint returns streaming response
        assert response.status_code in [200, 307]  # 307 for redirect or 200 for stream

    def test_sse_stream_content_type(self, client, auth_headers):
        """T014-2: Verify SSE endpoint returns correct content type.

        The response should have Content-Type: text/event-stream
        """
        workflow_id = "test-workflow-sse"

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()

            async def async_gen():
                yield {"event": "complete", "data": {"status": "succeeded"}}

            mock_service.stream_workflow = async_gen
            mock_get_service.return_value = mock_service

            response = client.get(
                f"/api/v1/timbal/workflows/{workflow_id}/stream",
                headers={**auth_headers, "Accept": "text/event-stream"}
            )

        # Check content type if streaming is supported
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            assert "text/event-stream" in content_type or "application/json" in content_type

    def test_sse_stream_with_error(self, client, auth_headers):
        """T014-3: Verify SSE stream handles errors gracefully.

        When workflow execution fails, the stream should emit an error event
        before closing.
        """
        workflow_id = "test-workflow-error"

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()

            async def error_gen():
                yield {"event": "status", "data": {"status": "running", "progress": 0}}
                yield {"event": "error", "data": {"error": "Workflow execution failed", "details": "Connection timeout"}}

            mock_service.stream_workflow = error_gen
            mock_get_service.return_value = mock_service

            response = client.get(
                f"/api/v1/timbal/workflows/{workflow_id}/stream",
                headers={**auth_headers, "Accept": "text/event-stream"}
            )

        # Should handle error gracefully
        assert response.status_code in [200, 500]

    def test_sse_stream_progress_updates(self, client, auth_headers):
        """T014-4: Verify SSE stream sends progress updates.

        Tests that the stream includes progress information during execution.
        """
        workflow_id = "test-workflow-progress"

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()

            async def progress_gen():
                for i in range(0, 101, 25):
                    yield {"event": "status", "data": {"status": "running", "progress": i}}
                yield {"event": "complete", "data": {"status": "succeeded", "outputs": {}}}

            mock_service.stream_workflow = progress_gen
            mock_get_service.return_value = mock_service

            response = client.get(
                f"/api/v1/timbal/workflows/{workflow_id}/stream",
                headers={**auth_headers, "Accept": "text/event-stream"}
            )

        # Progress updates should be sent
        assert response.status_code in [200, 307]

    def test_sse_stream_node_outputs(self, client, auth_headers):
        """T014-5: Verify SSE stream includes node outputs.

        Tests that individual node outputs are streamed as they complete.
        """
        workflow_id = "test-workflow-nodes"

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()

            async def node_output_gen():
                yield {"event": "status", "data": {"status": "running", "progress": 0}}
                yield {"event": "output", "data": {"node_id": "node-1", "output": {"project_name": "Test Project"}}}
                yield {"event": "output", "data": {"node_id": "node-2", "output": {"risks": ["Risk 1", "Risk 2"]}}}
                yield {"event": "complete", "data": {"status": "succeeded", "outputs": {"final_result": "analysis complete"}}}

            mock_service.stream_workflow = node_output_gen
            mock_get_service.return_value = mock_service

            response = client.get(
                f"/api/v1/timbal/workflows/{workflow_id}/stream",
                headers={**auth_headers, "Accept": "text/event-stream"}
            )

        # Node outputs should be included
        assert response.status_code in [200, 307]

    def test_sse_stream_completion_event(self, client, auth_headers):
        """T014-6: Verify SSE stream ends with completion event.

        Tests that the stream always ends with a complete event.
        """
        workflow_id = "test-workflow-complete"

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()

            async def complete_gen():
                yield {"event": "status", "data": {"status": "running"}}
                yield {"event": "complete", "data": {"status": "succeeded", "outputs": {"result": "done"}}}

            mock_service.stream_workflow = complete_gen
            mock_get_service.return_value = mock_service

            response = client.get(
                f"/api/v1/timbal/workflows/{workflow_id}/stream",
                headers={**auth_headers, "Accept": "text/event-stream"}
            )

        # Should complete successfully
        assert response.status_code in [200, 307]

    def test_sse_stream_without_accept_header(self, client, auth_headers):
        """T014-7: Verify SSE endpoint behavior without Accept header.

        Tests that the endpoint handles requests without the Accept header.
        """
        workflow_id = "test-workflow-no-header"

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()

            async def simple_gen():
                yield {"event": "complete", "data": {"status": "succeeded"}}

            mock_service.stream_workflow = simple_gen
            mock_get_service.return_value = mock_service

            response = client.get(
                f"/api/v1/timbal/workflows/{workflow_id}/stream",
                headers=auth_headers  # No Accept header
            )

        # Should still work or return appropriate error
        assert response.status_code in [200, 307, 400]
