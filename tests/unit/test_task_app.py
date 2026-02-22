"""
Tests for Task Tracking App - List and Task Operations
"""
import pytest
import sqlite3
import os
import sys
from fastapi.testclient import TestClient
from unittest.mock import patch

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set test database path before importing app
TEST_DB = "test_tasks.db"
os.environ['TEST_DB_PATH'] = TEST_DB

from app.main import app, init_db, get_db, API_KEY

client = TestClient(app)
API_KEY_HEADER = {"x-api-key": API_KEY}


@pytest.fixture(autouse=True)
def setup_test_db():
    """Set up test database before each test."""
    # Use test database
    import app.main
    app.main.DB_PATH = TEST_DB
    
    # Initialize database
    init_db()
    
    yield
    
    # Cleanup after test
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


class TestListOperations:
    """Tests for list creation, retrieval, and deletion."""

    def test_get_lists_empty(self):
        """Test getting lists when database is empty."""
        response = client.get("/api/lists")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_list_success(self):
        """Test creating a new list."""
        response = client.post(
            "/api/lists",
            json={"name": "Test List"},
            headers=API_KEY_HEADER
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["name"] == "Test List"
        assert "list_id" in data

    def test_create_list_requires_auth(self):
        """Test that creating a list requires API key."""
        response = client.post(
            "/api/lists",
            json={"name": "Test List"}
        )
        assert response.status_code == 422  # Missing header

    def test_create_list_invalid_auth(self):
        """Test that invalid API key is rejected."""
        response = client.post(
            "/api/lists",
            json={"name": "Test List"},
            headers={"x-api-key": "wrong-key"}
        )
        assert response.status_code == 401

    def test_create_list_empty_name(self):
        """Test that empty list name is rejected."""
        response = client.post(
            "/api/lists",
            json={"name": ""},
            headers=API_KEY_HEADER
        )
        assert response.status_code == 422

    def test_create_list_whitespace_name(self):
        """Test that whitespace-only name is rejected."""
        response = client.post(
            "/api/lists",
            json={"name": "   "},
            headers=API_KEY_HEADER
        )
        assert response.status_code == 422

    def test_delete_list_success(self):
        """Test deleting an existing list."""
        # First create a list
        create_response = client.post(
            "/api/lists",
            json={"name": "To Delete"},
            headers=API_KEY_HEADER
        )
        list_id = create_response.json()["list_id"]
        
        # Then delete it
        response = client.delete(
            f"/api/lists/{list_id}",
            headers=API_KEY_HEADER
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_delete_list_not_found(self):
        """Test deleting a non-existent list."""
        response = client.delete(
            "/api/lists/99999",
            headers=API_KEY_HEADER
        )
        assert response.status_code == 404

    def test_delete_list_requires_auth(self):
        """Test that deleting a list requires API key."""
        response = client.delete("/api/lists/1")
        assert response.status_code == 422


class TestTaskOperations:
    """Tests for task creation, retrieval, and toggling."""

    @pytest.fixture
    def test_list(self):
        """Create a test list for task tests."""
        response = client.post(
            "/api/lists",
            json={"name": "Test List"},
            headers=API_KEY_HEADER
        )
        return response.json()["list_id"]

    def test_get_tasks_empty(self, test_list):
        """Test getting tasks when list is empty."""
        response = client.get(f"/api/lists/{test_list}/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_add_task_success(self, test_list):
        """Test adding a task to a list."""
        response = client.post(
            "/api/tasks",
            json={"list_id": test_list, "title": "Test Task"},
            headers=API_KEY_HEADER
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["title"] == "Test Task"
        assert "task_id" in data

    def test_add_task_to_nonexistent_list(self):
        """Test adding a task to a non-existent list."""
        response = client.post(
            "/api/tasks",
            json={"list_id": 99999, "title": "Test Task"},
            headers=API_KEY_HEADER
        )
        assert response.status_code == 404

    def test_add_task_empty_title(self, test_list):
        """Test that empty task title is rejected."""
        response = client.post(
            "/api/tasks",
            json={"list_id": test_list, "title": ""},
            headers=API_KEY_HEADER
        )
        assert response.status_code == 422

    def test_add_task_requires_auth(self, test_list):
        """Test that adding a task requires API key."""
        response = client.post(
            "/api/tasks",
            json={"list_id": test_list, "title": "Test Task"}
        )
        assert response.status_code == 422

    def test_toggle_task_success(self, test_list):
        """Test toggling a task's done status."""
        # Add a task
        add_response = client.post(
            "/api/tasks",
            json={"list_id": test_list, "title": "Toggle Me"},
            headers=API_KEY_HEADER
        )
        task_id = add_response.json()["task_id"]
        
        # Toggle it on
        response = client.patch(
            f"/api/tasks/{task_id}/toggle",
            headers=API_KEY_HEADER
        )
        assert response.status_code == 200
        assert response.json()["done"] is True
        
        # Toggle it off
        response = client.patch(
            f"/api/tasks/{task_id}/toggle",
            headers=API_KEY_HEADER
        )
        assert response.status_code == 200
        assert response.json()["done"] is False

    def test_toggle_task_not_found(self):
        """Test toggling a non-existent task."""
        response = client.patch(
            "/api/tasks/99999/toggle",
            headers=API_KEY_HEADER
        )
        assert response.status_code == 404

    def test_get_tasks_after_creation(self, test_list):
        """Test that created tasks appear in list."""
        # Add a task
        client.post(
            "/api/tasks",
            json={"list_id": test_list, "title": "My Task"},
            headers=API_KEY_HEADER
        )
        
        # Get tasks
        response = client.get(f"/api/lists/{test_list}/tasks")
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["title"] == "My Task"
        assert tasks[0]["done"] is False


class TestErrorHandling:
    """Tests for error handling."""

    def test_database_error(self):
        """Test handling of database errors."""
        # Close the database to cause an error
        with patch('app.main.get_db') as mock_get_db:
            mock_get_db.side_effect = sqlite3.Error("Database locked")
            
            response = client.get("/api/lists")
            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
