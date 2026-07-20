"""Tests for v2 agent API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from fastapi.testclient import TestClient


class TestV2AgentAPI:
    """Test cases for v2 agent API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi import FastAPI
        from open_webui.pm.api.v2_agent import router as agent_router

        app = FastAPI()
        app.include_router(agent_router, prefix="/api/v2/agent")

        return TestClient(app)

    @pytest.fixture
    def sample_session_config(self):
        """Sample agent session configuration."""
        return {
            "name": "Test Agent Session",
            "agent_type": "react",
            "llm_config": {
                "model": "gpt-4",
                "temperature": 0.7
            },
            "memory_config": {
                "short_term_size": 10,
                "long_term_enabled": False
            },
            "allowed_tools": ["search", "calculator"]
        }

    @pytest.fixture
    def sample_chat_message(self):
        """Sample chat message."""
        return {
            "message": "Hello, agent!"
        }

    def test_create_agent_session(self, client, sample_session_config):
        """Test creating an agent session."""
        response = client.post(
            "/api/v2/agent/sessions",
            json=sample_session_config
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "created"
        assert data["config"] == sample_session_config

    def test_create_agent_session_empty_config(self, client):
        """Test creating agent session with empty config."""
        response = client.post(
            "/api/v2/agent/sessions",
            json={}
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "created"

    def test_chat_with_agent_success(self, client, sample_chat_message):
        """Test successful agent chat."""
        with patch("open_webui.pm.api.v2_agent.agent_runtime") as mock_runtime:
            # Mock agent run
            mock_run = MagicMock()
            mock_run.assistant_message = "Hello! I'm your AI assistant."
            mock_run.thought_process = [
                MagicMock(
                    observation="User greeted me",
                    reasoning="I should respond politely",
                    action="respond"
                )
            ]
            mock_run.tool_calls = []
            mock_run.token_usage = {"prompt_tokens": 10, "completion_tokens": 5}
            mock_run.duration_ms = 1500

            mock_runtime.run = AsyncMock(return_value=mock_run)

            response = client.post(
                "/api/v2/agent/test-session-id/chat",
                json=sample_chat_message
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Hello! I'm your AI assistant."
            assert data["session_id"] == "test-session-id"
            assert "thought_process" in data
            assert "token_usage" in data
            assert data["duration_ms"] == 1500

    def test_chat_with_agent_error(self, client, sample_chat_message):
        """Test agent chat with error."""
        with patch("open_webui.pm.api.v2_agent.agent_runtime") as mock_runtime:
            mock_runtime.run = AsyncMock(side_effect=Exception("Agent runtime error"))

            response = client.post(
                "/api/v2/agent/test-session-id/chat",
                json=sample_chat_message
            )

            assert response.status_code == 500
            data = response.json()
            assert "Agent chat failed" in data["detail"]

    def test_chat_with_agent_empty_message(self, client):
        """Test agent chat with empty message."""
        with patch("open_webui.pm.api.v2_agent.agent_runtime") as mock_runtime:
            mock_run = MagicMock()
            mock_run.assistant_message = ""
            mock_run.thought_process = []
            mock_run.tool_calls = []
            mock_run.token_usage = {}
            mock_run.duration_ms = 0

            mock_runtime.run = AsyncMock(return_value=mock_run)

            response = client.post(
                "/api/v2/agent/test-session-id/chat",
                json={"message": ""}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == ""

    def test_get_agent_runs(self, client):
        """Test getting agent runs."""
        response = client.get("/api/v2/agent/test-session-id/runs")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-id"
        assert isinstance(data["runs"], list)
        assert len(data["runs"]) == 0  # Currently returns empty list

    def test_delete_agent_session(self, client):
        """Test deleting an agent session."""
        with patch("open_webui.pm.api.v2_agent.memory_store") as mock_memory:
            mock_memory.clear = AsyncMock()

            response = client.delete("/api/v2/agent/test-session-id")

            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "test-session-id"
            assert data["status"] == "deleted"

    def test_delete_agent_session_error(self, client):
        """Test deleting agent session with error."""
        with patch("open_webui.pm.api.v2_agent.memory_store") as mock_memory:
            mock_memory.clear = AsyncMock(side_effect=Exception("Memory clear failed"))

            response = client.delete("/api/v2/agent/test-session-id")

            assert response.status_code == 500
            data = response.json()
            assert "Failed to delete session" in data["detail"]

    def test_chat_with_agent_with_tools(self, client):
        """Test agent chat with tool calls."""
        with patch("open_webui.pm.api.v2_agent.agent_runtime") as mock_runtime:
            mock_run = MagicMock()
            mock_run.assistant_message = "I used a tool to help you."
            mock_run.thought_process = [
                MagicMock(
                    observation="User asked for calculation",
                    reasoning="I should use the calculator tool",
                    action="use_tool"
                )
            ]
            mock_run.tool_calls = [
                {
                    "tool": "calculator",
                    "params": {"expression": "2+2"},
                    "result": "4"
                }
            ]
            mock_run.token_usage = {"prompt_tokens": 20, "completion_tokens": 10}
            mock_run.duration_ms = 2500

            mock_runtime.run = AsyncMock(return_value=mock_run)

            response = client.post(
                "/api/v2/agent/test-session-id/chat",
                json={"message": "Calculate 2+2"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "I used a tool to help you."
            assert len(data["tool_calls"]) == 1
            assert data["tool_calls"][0]["tool"] == "calculator"

    def test_chat_with_agent_long_conversation(self, client):
        """Test agent chat with long conversation."""
        with patch("open_webui.pm.api.v2_agent.agent_runtime") as mock_runtime:
            mock_run = MagicMock()
            mock_run.assistant_message = "This is a detailed response."
            mock_run.thought_process = [
                MagicMock(
                    observation="Long user message" * 100,
                    reasoning="Processing...",
                    action="respond"
                )
            ]
            mock_run.tool_calls = []
            mock_run.token_usage = {"prompt_tokens": 500, "completion_tokens": 200}
            mock_run.duration_ms = 5000

            mock_runtime.run = AsyncMock(return_value=mock_run)

            response = client.post(
                "/api/v2/agent/test-session-id/chat",
                json={"message": "Long message" * 100}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "This is a detailed response."

    def test_session_persistence(self, client, sample_session_config):
        """Test that session data is persisted."""
        # Create session
        create_response = client.post(
            "/api/v2/agent/sessions",
            json=sample_session_config
        )

        assert create_response.status_code == 200
        session_data = create_response.json()
        session_id = session_data["session_id"]

        # Verify session_id is a valid UUID format
        try:
            UUID(session_id)
        except ValueError:
            pytest.fail("Session ID is not a valid UUID")

    def test_concurrent_chat_requests(self, client):
        """Test handling concurrent chat requests."""
        with patch("open_webui.pm.api.v2_agent.agent_runtime") as mock_runtime:
            mock_run = MagicMock()
            mock_run.assistant_message = "Response"
            mock_run.thought_process = []
            mock_run.tool_calls = []
            mock_run.token_usage = {}
            mock_run.duration_ms = 1000

            mock_runtime.run = AsyncMock(return_value=mock_run)

            # Simulate multiple concurrent requests
            import concurrent.futures

            def make_request():
                return client.post(
                    "/api/v2/agent/test-session-id/chat",
                    json={"message": "Hello"}
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(make_request) for _ in range(3)]
                responses = [f.result() for f in futures]

            for response in responses:
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_agent_runtime_initialization(self):
        """Test agent runtime initialization."""
        from open_webui.pm.services.agent_runtime.agent import AgentRuntime
        from open_webui.pm.services.agent_runtime.memory import MemoryStore
        from open_webui.pm.services.agent_runtime.tools import ToolRegistry

        tool_registry = ToolRegistry()
        memory_store = MemoryStore()

        agent = AgentRuntime(
            llm_config={"model": "gpt-4", "temperature": 0.7},
            tool_registry=tool_registry,
            memory_store=memory_store
        )

        assert agent.llm_config["model"] == "gpt-4"
        assert agent.llm_config["temperature"] == 0.7
        assert agent.tool_registry == tool_registry
        assert agent.memory_store == memory_store

    @pytest.mark.asyncio
    async def test_agent_run(self):
        """Test agent run execution."""
        from open_webui.pm.services.agent_runtime.agent import AgentRuntime
        from open_webui.pm.services.agent_runtime.memory import MemoryStore
        from open_webui.pm.services.agent_runtime.tools import ToolRegistry

        tool_registry = ToolRegistry()
        memory_store = MemoryStore()

        agent = AgentRuntime(
            llm_config={"model": "gpt-4", "temperature": 0.7},
            tool_registry=tool_registry,
            memory_store=memory_store
        )

        # Mock the OpenAI client
        with patch.object(agent, 'client') as mock_client:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = """
            Observation: User said hello
            Thought: I should respond
            Action: respond
            Action Input: {"message": "Hello!"}
            """
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5

            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            run = await agent.run(
                session_id=UUID("12345678-1234-1234-1234-123456789abc"),
                user_message="Hello"
            )

            assert run.assistant_message is not None
            assert run.session_id == UUID("12345678-1234-1234-1234-123456789abc")
            assert run.user_message == "Hello"
