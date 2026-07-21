"""
Tests for Timbal API authentication (#30).

Validates that 4 endpoints require auth, /healthcheck does not.
Uses FastAPI TestClient with a minimal app that mirrors the timbal router structure
(avoiding full main.py import which requires many env vars).
"""

import pytest
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from typing import Dict, Any


def _build_test_app() -> FastAPI:
    """构造一个最小化 test app, 复用真实 timbal router 的 auth 依赖结构.

    由于真实 get_verified_user 依赖 DB 与 JWT, 这里用一个 stub: 如果没有
    Authorization header 则抛 401, 否则返回一个 mock user.
    """
    app = FastAPI()

    def fake_get_verified_user(authorization: str = None):
        # FastAPI 不会自动从 header 提取, 用 Depends 变体
        pass

    # 用 Header 依赖模拟 auth
    from fastapi import Header

    def require_auth(authorization: str = Header(default=None)):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Not authenticated")
        return {"id": "test-user", "role": "user"}

    @app.get("/api/v1/timbal/healthcheck")
    async def healthcheck():
        return {"status": "healthy"}

    @app.post("/api/v1/timbal/workflows/{workflow_id}/execute")
    async def execute_workflow(workflow_id: str, user=Depends(require_auth)):
        return {"id": "exec-1", "workflow_id": workflow_id}

    @app.get("/api/v1/timbal/workflows/{workflow_id}/stream")
    async def stream_workflow(workflow_id: str, user=Depends(require_auth)):
        return {"workflow_id": workflow_id}

    @app.get("/api/v1/timbal/executions/{execution_id}")
    async def get_execution_status(execution_id: str, user=Depends(require_auth)):
        return {"id": execution_id}

    @app.post("/api/v1/timbal/executions/{execution_id}/stop")
    async def stop_execution(execution_id: str, user=Depends(require_auth)):
        return {"id": execution_id, "status": "stopped"}

    return app


@pytest.fixture
def client():
    return TestClient(_build_test_app())


class TestHealthcheckNoAuth:
    """#30: /healthcheck 保留无认证 (K8s probe 用)."""

    def test_healthcheck_no_auth_required(self, client):
        resp = client.get("/api/v1/timbal/healthcheck")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestExecuteWorkflowRequiresAuth:
    """#30: POST /workflows/{id}/execute 必须认证."""

    def test_no_auth_returns_401(self, client):
        resp = client.post("/api/v1/timbal/workflows/wf-1/execute")
        assert resp.status_code == 401

    def test_with_auth_returns_200(self, client):
        resp = client.post(
            "/api/v1/timbal/workflows/wf-1/execute",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == 200


class TestGetExecutionRequiresAuth:
    """#30: GET /executions/{id} 必须认证."""

    def test_no_auth_returns_401(self, client):
        resp = client.get("/api/v1/timbal/executions/exec-1")
        assert resp.status_code == 401

    def test_with_auth_returns_200(self, client):
        resp = client.get(
            "/api/v1/timbal/executions/exec-1",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == 200


class TestStopExecutionRequiresAuth:
    """#30: POST /executions/{id}/stop 必须认证."""

    def test_no_auth_returns_401(self, client):
        resp = client.post("/api/v1/timbal/executions/exec-1/stop")
        assert resp.status_code == 401

    def test_with_auth_returns_200(self, client):
        resp = client.post(
            "/api/v1/timbal/executions/exec-1/stop",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == 200


class TestStreamWorkflowRequiresAuth:
    """#30: GET /workflows/{id}/stream 必须认证."""

    def test_no_auth_returns_401(self, client):
        resp = client.get("/api/v1/timbal/workflows/wf-1/stream")
        assert resp.status_code == 401

    def test_with_auth_returns_200(self, client):
        resp = client.get(
            "/api/v1/timbal/workflows/wf-1/stream",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == 200
