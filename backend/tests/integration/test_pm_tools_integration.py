"""
Integration tests for PM data read/write operations via Timbal tools.

Tests the bidirectional data flow between Timbal workflows and PM workspace.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

from timbal.models import TimbalTool


class TestPMDataReadWrite:
    """Integration tests for PM data read/write via Timbal tools."""

    def test_read_project_list(self, client, auth_headers):
        """T024-1: Verify reading project list from PM workspace.

        Tests that the get_project_list tool returns actual PM workspace projects.
        """
        tool_id = "tool-get-project-list"
        request_data = {
            "parameters": {}
        }

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_result = {
                "success": True,
                "data": {
                    "projects": [
                        {
                            "id": "proj-1",
                            "name": "Project Alpha",
                            "description": "First project",
                            "status": "active",
                            "created_at": datetime.utcnow().isoformat()
                        },
                        {
                            "id": "proj-2",
                            "name": "Project Beta",
                            "description": "Second project",
                            "status": "active",
                            "created_at": datetime.utcnow().isoformat()
                        }
                    ]
                }
            }
            mock_service.execute_tool = AsyncMock(return_value=mock_result)
            mock_get_service.return_value = mock_service

            response = client.post(
                f"/api/v1/timbal/tools/{tool_id}/execute",
                json=request_data,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "projects" in data["data"]
        assert len(data["data"]["projects"]) > 0

        # Verify project structure
        project = data["data"]["projects"][0]
        assert "id" in project
        assert "name" in project

    def test_read_requirements_for_project(self, client, auth_headers):
        """T024-2: Verify reading requirements for a specific project.

        Tests that requirements can be fetched for a given project ID.
        """
        tool_id = "tool-get-requirements"
        request_data = {
            "parameters": {
                "project_id": "proj-123"
            }
        }

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_result = {
                "success": True,
                "data": {
                    "project_id": "proj-123",
                    "requirements": [
                        {
                            "id": "req-1",
                            "title": "User Authentication",
                            "description": "Implement user login",
                            "status": "in_progress",
                            "priority": "high",
                            "created_at": datetime.utcnow().isoformat()
                        }
                    ]
                }
            }
            mock_service.execute_tool = AsyncMock(return_value=mock_result)
            mock_get_service.return_value = mock_service

            response = client.post(
                f"/api/v1/timbal/tools/{tool_id}/execute",
                json=request_data,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "requirements" in data["data"]

    def test_create_requirement_in_project(self, client, auth_headers):
        """T024-3: Verify creating a requirement in PM workspace.

        Tests that new requirements can be created via Timbal tools.
        """
        tool_id = "tool-create-requirement"
        request_data = {
            "parameters": {
                "project_id": "proj-123",
                "title": "New Feature Request",
                "description": "Add dark mode support",
                "priority": "medium"
            }
        }

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_result = {
                "success": True,
                "data": {
                    "requirement": {
                        "id": "req-new-123",
                        "project_id": "proj-123",
                        "title": "New Feature Request",
                        "description": "Add dark mode support",
                        "priority": "medium",
                        "status": "open",
                        "created_at": datetime.utcnow().isoformat()
                    }
                }
            }
            mock_service.execute_tool = AsyncMock(return_value=mock_result)
            mock_get_service.return_value = mock_service

            response = client.post(
                f"/api/v1/timbal/tools/{tool_id}/execute",
                json=request_data,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "requirement" in data["data"]
        assert data["data"]["requirement"]["title"] == "New Feature Request"

    def test_update_project_status(self, client, auth_headers):
        """T024-4: Verify updating project status in PM workspace.

        Tests that project data can be updated via Timbal tools.
        """
        tool_id = "tool-update-project"
        request_data = {
            "parameters": {
                "project_id": "proj-123",
                "updates": {
                    "status": "completed",
                    "completion_date": datetime.utcnow().isoformat()
                }
            }
        }

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_result = {
                "success": True,
                "data": {
                    "project": {
                        "id": "proj-123",
                        "status": "completed",
                        "updated_at": datetime.utcnow().isoformat()
                    }
                }
            }
            mock_service.execute_tool = AsyncMock(return_value=mock_result)
            mock_get_service.return_value = mock_service

            response = client.post(
                f"/api/v1/timbal/tools/{tool_id}/execute",
                json=request_data,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["project"]["status"] == "completed"

    def test_delete_requirement(self, client, auth_headers):
        """T024-5: Verify deleting a requirement from PM workspace.

        Tests that requirements can be deleted via Timbal tools.
        """
        tool_id = "tool-delete-requirement"
        request_data = {
            "parameters": {
                "requirement_id": "req-123"
            }
        }

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_result = {
                "success": True,
                "data": {
                    "deleted": True,
                    "requirement_id": "req-123"
                }
            }
            mock_service.execute_tool = AsyncMock(return_value=mock_result)
            mock_get_service.return_value = mock_service

            response = client.post(
                f"/api/v1/timbal/tools/{tool_id}/execute",
                json=request_data,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["deleted"] is True

    def test_read_documents_for_project(self, client, auth_headers):
        """T024-6: Verify reading documents for a specific project.

        Tests that documents can be fetched for a given project ID.
        """
        tool_id = "tool-get-documents"
        request_data = {
            "parameters": {
                "project_id": "proj-123"
            }
        }

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()
            mock_result = {
                "success": True,
                "data": {
                    "project_id": "proj-123",
                    "documents": [
                        {
                            "id": "doc-1",
                            "title": "PRD Document",
                            "type": "prd",
                            "content_summary": "Product requirements",
                            "created_at": datetime.utcnow().isoformat()
                        }
                    ]
                }
            }
            mock_service.execute_tool = AsyncMock(return_value=mock_result)
            mock_get_service.return_value = mock_service

            response = client.post(
                f"/api/v1/timbal/tools/{tool_id}/execute",
                json=request_data,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "documents" in data["data"]

    def test_bidirectional_data_flow(self, client, auth_headers):
        """T024-7: Verify bidirectional data flow between Timbal and PM.

        Tests that data can be read from PM, processed, and written back.
        """
        # Step 1: Read project data
        read_tool_id = "tool-get-project"
        read_request = {
            "parameters": {"project_id": "proj-123"}
        }

        with patch('open_webui.routers.timbal.get_execution_service') as mock_get_service:
            mock_service = MagicMock()

            # Mock read operation
            mock_read_result = {
                "success": True,
                "data": {
                    "project": {
                        "id": "proj-123",
                        "name": "Test Project",
                        "status": "active"
                    }
                }
            }

            # Mock write operation
            mock_write_result = {
                "success": True,
                "data": {
                    "project": {
                        "id": "proj-123",
                        "name": "Test Project (Updated)",
                        "status": "active"
                    }
                }
            }

            mock_service.execute_tool = AsyncMock(side_effect=[mock_read_result, mock_write_result])
            mock_get_service.return_value = mock_service

            # Execute read
            response1 = client.post(
                f"/api/v1/timbal/tools/{read_tool_id}/execute",
                json=read_request,
                headers=auth_headers
            )

            assert response1.status_code == 200
            data1 = response1.json()
            assert data1["success"] is True

            # Execute write (update)
            update_request = {
                "parameters": {
                    "project_id": "proj-123",
                    "updates": {"name": "Test Project (Updated)"}
                }
            }

            response2 = client.post(
                f"/api/v1/timbal/tools/tool-update-project/execute",
                json=update_request,
                headers=auth_headers
            )

            assert response2.status_code == 200
            data2 = response2.json()
            assert data2["success"] is True
