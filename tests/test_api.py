"""Automated test suite for Task API (SQLite-backed).

Tests all CRUD operations, database persistence, seed logic, validation rules,
status codes, and JSON error formats using isolated temporary SQLite databases.
"""

import os
import sqlite3
import tempfile
import pytest
from fastapi.testclient import TestClient

import database
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
    """Provide an isolated temporary SQLite database for every test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        temp_db_path = tmp.name

    # Initialize schema and seed data in temporary test database
    database.init_db(temp_db_path)

    # Monkeypatch get_db_connection to direct all app traffic to temp_db_path
    original_get_db = database.get_db_connection
    monkeypatch.setattr(
        database,
        "get_db_connection",
        lambda db_path=temp_db_path: original_get_db(temp_db_path),
    )
    monkeypatch.setattr(database, "DB_PATH", temp_db_path)

    yield temp_db_path

    # Cleanup temporary test database file
    if os.path.exists(temp_db_path):
        os.remove(temp_db_path)


# --------------------------------------------------
# Root and Health Endpoint Tests
# --------------------------------------------------
def test_get_root():
    """Test GET / returns API metadata and 200 OK."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Task API"
    assert data["version"] == "2.0"
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
    """Test GET /tasks returns initial 3 seeded tasks from SQLite and 200 OK."""
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
    """Test POST /tasks creates a new task in SQLite with auto-assigned ID and done=false."""
    response = client.post("/tasks", json={"title": "Buy milk"})
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 4
    assert data["title"] == "Buy milk"
    assert data["done"] is False

    # Verify task is now present in SQLite database
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
    """Test PUT /tasks/{id} updates both title and done status in SQLite."""
    response = client.put("/tasks/1", json={"title": "Buy groceries", "done": True})
    assert response.status_code == 200
    data = response.json()
    assert data == {"id": 1, "title": "Buy groceries", "done": True}

    # Verify persisted updated state in SQLite
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
    """Test DELETE /tasks/{id} removes task from SQLite, returns 204 No Content with empty body."""
    response = client.delete("/tasks/1")
    assert response.status_code == 204
    assert response.content == b""

    # Verify task 1 is gone from SQLite
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
# Database Seed & Persistence Tests
# --------------------------------------------------
def test_seed_not_duplicated_on_reinit(isolated_db):
    """Verify that multiple init_db() calls do not duplicate seed data."""
    # init_db has already run once via fixture
    conn = database.get_db_connection(isolated_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tasks;")
    assert cursor.fetchone()[0] == 3
    conn.close()

    # Call init_db again simulating server restart
    database.init_db(isolated_db)
    database.init_db(isolated_db)

    conn = database.get_db_connection(isolated_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM tasks;")
    assert cursor.fetchone()[0] == 3
    conn.close()


def test_database_persistence(isolated_db):
    """Verify that records written to SQLite persist across connection closures."""
    # Insert via API
    res = client.post("/tasks", json={"title": "Persistence Test Task"})
    assert res.status_code == 201
    created_id = res.json()["id"]

    # Directly open a fresh independent connection to the database file
    direct_conn = sqlite3.connect(isolated_db)
    cursor = direct_conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?;", (created_id,))
    row = cursor.fetchone()
    direct_conn.close()

    assert row is not None
    assert row[0] == created_id
    assert row[1] == "Persistence Test Task"
    assert row[2] == 0
