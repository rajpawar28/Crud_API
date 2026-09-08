"""Automated test suite for Task API (PostgreSQL/Docker-ready).

Tests all CRUD operations, validation rules, status codes, and error formats.
Supports isolated testing via monkeypatched repository fixtures.
"""

from typing import Any, Dict, List, Optional
import pytest
from fastapi.testclient import TestClient

import database
from main import app

client = TestClient(app)


class MockDatabase:
    """In-memory mock store that mimics PostgreSQL table behavior for fast local test isolation."""

    def __init__(self):
        self.tasks: List[Dict[str, Any]] = [
            {"id": 1, "title": "Learn FastAPI", "done": False},
            {"id": 2, "title": "Build CRUD API", "done": False},
            {"id": 3, "title": "Test API with Swagger", "done": True},
        ]
        self._next_id = 4

    def fetch_all_tasks(self, db_url=None):
        return [t.copy() for t in self.tasks]

    def fetch_task_by_id(self, task_id: int, db_url=None):
        for t in self.tasks:
            if t["id"] == task_id:
                return t.copy()
        return None

    def insert_task(self, title: str, db_url=None):
        new_task = {"id": self._next_id, "title": title, "done": False}
        self._next_id += 1
        self.tasks.append(new_task)
        return new_task.copy()

    def update_task_record(
        self,
        task_id: int,
        title: Optional[str],
        done: Optional[bool],
        db_url=None,
    ):
        for t in self.tasks:
            if t["id"] == task_id:
                if title is not None:
                    t["title"] = title
                if done is not None:
                    t["done"] = done
                return t.copy()
        return None

    def delete_task_record(self, task_id: int, db_url=None):
        for idx, t in enumerate(self.tasks):
            if t["id"] == task_id:
                self.tasks.pop(idx)
                return True
        return False


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
    """Provide an isolated database state for every test."""
    mock_db = MockDatabase()
    monkeypatch.setattr(database, "fetch_all_tasks", mock_db.fetch_all_tasks)
    monkeypatch.setattr(database, "fetch_task_by_id", mock_db.fetch_task_by_id)
    monkeypatch.setattr(database, "insert_task", mock_db.insert_task)
    monkeypatch.setattr(database, "update_task_record", mock_db.update_task_record)
    monkeypatch.setattr(database, "delete_task_record", mock_db.delete_task_record)
    monkeypatch.setattr(database, "init_db", lambda *args, **kwargs: None)
    yield mock_db


# --------------------------------------------------
# Root and Health Endpoint Tests
# --------------------------------------------------
def test_get_root():
    """Test GET / returns API metadata and 200 OK."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Task API"
    assert data["version"] == "3.0"
    assert "/tasks" in data["endpoints"]


def test_get_health():
    """Test GET /health returns status ok and 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --------------------------------------------------
# Read Endpoints (GET /tasks, GET /tasks/{id})
# --------------------------------------------------
def test_get_tasks():
    """Test GET /tasks returns initial 3 seeded tasks from PostgreSQL and 200 OK."""
    response = client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert isinstance(tasks, list)
    assert len(tasks) == 3
    assert tasks[0] == {"id": 1, "title": "Learn FastAPI", "done": False}
    assert tasks[1] == {"id": 2, "title": "Build CRUD API", "done": False}
    assert tasks[2] == {"id": 3, "title": "Test API with Swagger", "done": True}


def test_get_task_existing():
    """Test GET /tasks/{id} for an existing task returns 200 OK."""
    response = client.get("/tasks/1")
    assert response.status_code == 200
    assert response.json() == {"id": 1, "title": "Learn FastAPI", "done": False}


def test_get_task_unknown():
    """Test GET /tasks/{id} for a non-existent task returns 404 with error JSON."""
    response = client.get("/tasks/99")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "99" in data["error"]
    assert data["error"] == "Task 99 not found"


# --------------------------------------------------
# Create Endpoint (POST /tasks)
# --------------------------------------------------
def test_post_task_valid():
    """Test POST /tasks creates a new task in PostgreSQL with auto-assigned ID and done=false."""
    response = client.post("/tasks", json={"title": "Buy milk"})
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 4
    assert data["title"] == "Buy milk"
    assert data["done"] is False

    # Verify task is now present in database
    tasks_res = client.get("/tasks")
    assert len(tasks_res.json()) == 4


def test_post_task_missing_title():
    """Test POST /tasks with missing title returns 400 Bad Request."""
    response = client.post("/tasks", json={})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "Title" in data["error"] or "title" in data["error"] or "body" in data["error"]


def test_post_task_empty_title():
    """Test POST /tasks with empty string title returns 400 Bad Request."""
    response = client.post("/tasks", json={"title": ""})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "Title" in data["error"] or "empty" in data["error"]


def test_post_task_whitespace_title():
    """Test POST /tasks with whitespace-only title returns 400 Bad Request."""
    response = client.post("/tasks", json={"title": "   "})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "Title" in data["error"] or "empty" in data["error"]


def test_post_task_null_title():
    """Test POST /tasks with null title returns 400 Bad Request."""
    response = client.post("/tasks", json={"title": None})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_post_task_ignores_client_id_and_done():
    """Test POST /tasks rejects client attempting to pass id or done in request body."""
    response = client.post(
        "/tasks", json={"title": "Clean room", "id": 100, "done": True}
    )
    assert response.status_code == 400
    assert "error" in response.json()


# --------------------------------------------------
# Update Endpoint (PUT /tasks/{id})
# --------------------------------------------------
def test_put_task_title_and_done():
    """Test PUT /tasks/{id} updates both title and done status in PostgreSQL."""
    response = client.put("/tasks/1", json={"title": "Buy groceries", "done": True})
    assert response.status_code == 200
    data = response.json()
    assert data == {"id": 1, "title": "Buy groceries", "done": True}

    # Verify persisted updated state in database
    get_res = client.get("/tasks/1")
    assert get_res.json() == {"id": 1, "title": "Buy groceries", "done": True}


def test_put_task_title_only():
    """Test PUT /tasks/{id} updates only title, keeping done unchanged."""
    response = client.put("/tasks/2", json={"title": "Build awesome CRUD API"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 2
    assert data["title"] == "Build awesome CRUD API"
    assert data["done"] is False


def test_put_task_done_only():
    """Test PUT /tasks/{id} updates only done, keeping title unchanged."""
    response = client.put("/tasks/2", json={"done": True})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 2
    assert data["title"] == "Build CRUD API"
    assert data["done"] is True


def test_put_task_unknown_id():
    """Test PUT /tasks/{id} for unknown ID returns 404."""
    response = client.put("/tasks/99", json={"title": "Non-existent", "done": True})
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "99" in data["error"]
    assert data["error"] == "Task 99 not found"


def test_put_task_empty_body():
    """Test PUT /tasks/{id} with empty object returns 400 Bad Request."""
    response = client.put("/tasks/1", json={})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_put_task_empty_title():
    """Test PUT /tasks/{id} with empty title string returns 400 Bad Request."""
    response = client.put("/tasks/1", json={"title": ""})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_put_task_whitespace_title():
    """Test PUT /tasks/{id} with whitespace-only title returns 400 Bad Request."""
    response = client.put("/tasks/1", json={"title": "   "})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


# --------------------------------------------------
# Delete Endpoint (DELETE /tasks/{id})
# --------------------------------------------------
def test_delete_task_existing():
    """Test DELETE /tasks/{id} removes task from PostgreSQL, returns 204 No Content with empty body."""
    response = client.delete("/tasks/1")
    assert response.status_code == 204
    assert response.content == b""

    # Verify task 1 is gone from database
    get_res = client.get("/tasks/1")
    assert get_res.status_code == 404

    # Verify remaining tasks count is 2
    tasks_res = client.get("/tasks")
    assert len(tasks_res.json()) == 2


def test_delete_task_unknown_id():
    """Test DELETE /tasks/{id} with non-existent ID returns 404."""
    response = client.delete("/tasks/99")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "99" in data["error"]
    assert data["error"] == "Task 99 not found"


# --------------------------------------------------
# Full CRUD Lifecycle Test
# --------------------------------------------------
def test_full_crud_lifecycle():
    """Test complete CRUD cycle on task resource."""
    # 1. GET initial tasks
    initial_tasks = client.get("/tasks").json()
    assert len(initial_tasks) == 3

    # 2. POST new task
    create_res = client.post("/tasks", json={"title": "Complete A3 Assignment"})
    assert create_res.status_code == 201
    created_id = create_res.json()["id"]

    # 3. GET newly created task by ID
    get_res = client.get(f"/tasks/{created_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Complete A3 Assignment"
    assert get_res.json()["done"] is False

    # 4. PUT update task
    put_res = client.put(
        f"/tasks/{created_id}",
        json={"title": "Complete A3 Assignment in Docker", "done": True},
    )
    assert put_res.status_code == 200
    assert put_res.json()["done"] is True

    # 5. DELETE task
    del_res = client.delete(f"/tasks/{created_id}")
    assert del_res.status_code == 204

    # 6. GET deleted task returns 404
    assert client.get(f"/tasks/{created_id}").status_code == 404
