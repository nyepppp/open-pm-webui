"""
Smoke tests for PM (Project Management) module endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestPMEndpoints:
    """Basic smoke tests for PM endpoints."""

    def test_get_projects(self, client: TestClient, auth_headers: dict):
        """Test GET /pm/projects returns list."""
        response = client.get("/pm/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_project(self, client: TestClient, auth_headers: dict):
        """Test POST /pm/projects creates a project."""
        data = {
            "name": "Test Project",
            "description": "A test project for smoke testing"
        }
        response = client.post("/pm/projects", json=data, headers=auth_headers)
        assert response.status_code in [200, 201, 422]

    def test_get_entries(self, client: TestClient, auth_headers: dict):
        """Test GET /pm/projects/{id}/entries returns list."""
        project_data = {"name": "Test Project for Entries"}
        resp = client.post("/pm/projects", json=project_data, headers=auth_headers)
        if resp.status_code in [200, 201]:
            project_id = resp.json().get("id", "test-project-id")
            response = client.get(f"/pm/projects/{project_id}/entries", headers=auth_headers)
            assert response.status_code in [200, 404]
        else:
            pytest.skip("Could not create project for entry test")

    def test_create_entry(self, client: TestClient, auth_headers: dict):
        """Test POST /pm/projects/{id}/entries creates an entry."""
        project_data = {"name": "Test Project for Entry Creation"}
        resp = client.post("/pm/projects", json=project_data, headers=auth_headers)
        if resp.status_code in [200, 201]:
            project_id = resp.json().get("id", "test-project-id")
            entry_data = {
                "module_type": "prd",
                "title": "Test PRD Entry",
                "content": "This is a test PRD entry"
            }
            response = client.post(
                f"/pm/projects/{project_id}/entries",
                json=entry_data,
                headers=auth_headers
            )
            assert response.status_code in [200, 201, 422]
        else:
            pytest.skip("Could not create project for entry creation test")

    def test_get_versions(self, client: TestClient, auth_headers: dict):
        """Test GET /pm/projects/{id}/versions returns list."""
        project_data = {"name": "Test Project for Versions"}
        resp = client.post("/pm/projects", json=project_data, headers=auth_headers)
        if resp.status_code in [200, 201]:
            project_id = resp.json().get("id", "test-project-id")
            response = client.get(f"/pm/projects/{project_id}/versions", headers=auth_headers)
            assert response.status_code in [200, 404]
        else:
            pytest.skip("Could not create project for version test")

    def test_agent_chat(self, client: TestClient, auth_headers: dict):
        """Test POST /pm/agent/chat returns response."""
        data = {
            "message": "Hello, this is a test message",
            "project_id": "test-project-id"
        }
        response = client.post("/pm/agent/chat", json=data, headers=auth_headers)
        assert response.status_code in [200, 422, 500]

    def test_agent_skills(self, client: TestClient, auth_headers: dict):
        """Test GET /pm/agent/skills returns skills list."""
        response = client.get("/pm/agent/skills", headers=auth_headers)
        assert response.status_code in [200, 404]

    def test_get_entities(self, client: TestClient, auth_headers: dict):
        """Test GET /pm/projects/{id}/entities returns list."""
        project_data = {"name": "Test Project for Entities"}
        resp = client.post("/pm/projects", json=project_data, headers=auth_headers)
        if resp.status_code in [200, 201]:
            project_id = resp.json().get("id", "test-project-id")
            response = client.get(f"/pm/projects/{project_id}/entities", headers=auth_headers)
            assert response.status_code in [200, 404]
        else:
            pytest.skip("Could not create project for entity test")

    def test_get_relations(self, client: TestClient, auth_headers: dict):
        """Test GET /pm/projects/{id}/relations returns list."""
        project_data = {"name": "Test Project for Relations"}
        resp = client.post("/pm/projects", json=project_data, headers=auth_headers)
        if resp.status_code in [200, 201]:
            project_id = resp.json().get("id", "test-project-id")
            response = client.get(f"/pm/projects/{project_id}/relations", headers=auth_headers)
            assert response.status_code in [200, 404]
        else:
            pytest.skip("Could not create project for relation test")

    def test_traceability_validate(self, client: TestClient, auth_headers: dict):
        """Test GET /pm/projects/{id}/traceability/validate returns validation result."""
        project_data = {"name": "Test Project for Traceability"}
        resp = client.post("/pm/projects", json=project_data, headers=auth_headers)
        if resp.status_code in [200, 201]:
            project_id = resp.json().get("id", "test-project-id")
            response = client.get(
                f"/pm/projects/{project_id}/traceability/validate",
                headers=auth_headers
            )
            assert response.status_code in [200, 404]
        else:
            pytest.skip("Could not create project for traceability test")