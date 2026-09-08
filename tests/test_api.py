"""Automated test suite for Task API (PostgreSQL/Docker-ready + Auth A4).

Tests all CRUD operations, validation rules, status codes, error formats,
and Supabase authentication flows.
Supports isolated testing via monkeypatched repository and auth fixtures.
"""

from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

import database
import supabase_client
import auth
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


class MockUser:
    """Mock Supabase user object."""

    def __init__(self, user_id="test-user-id-123", email="test@example.com", created_at="2024-01-01T00:00:00Z"):
        self.id = user_id
        self.email = email
        self.created_at = created_at


class MockSession:
    """Mock Supabase session object."""

    def __init__(self):
        self.access_token = "mock-access-token-abc123"
        self.refresh_token = "mock-refresh-token-xyz789"


class MockSignupResponse:
    """Mock Supabase signup response."""

    def __init__(self, user=None):
        self.user = user or MockUser()


class MockLoginResponse:
    """Mock Supabase login response."""

    def __init__(self, session=None, user=None):
        self.session = session or MockSession()
        self.user = user or MockUser()


class MockGetUserResponse:
    """Mock Supabase get_user response."""

    def __init__(self, user=None):
        self.user = user or MockUser()


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


@pytest.fixture(autouse=True)
def mock_supabase(monkeypatch):
    """Provide a mock Supabase client for all tests."""
    mock_client = MagicMock()
    monkeypatch.setattr(supabase_client, "supabase", mock_client)
    monkeypatch.setattr(auth, "supabase", mock_client)
    # Also patch the supabase imported in main.py
    monkeypatch.setattr("main.supabase", mock_client)

    # Default: get_user succeeds (for protected route tests)
    mock_client.auth.get_user.return_value = MockGetUserResponse()

    yield mock_client


# --------------------------------------------------
# Root and Health Endpoint Tests
# --------------------------------------------------
def test_get_root():
    """Test GET / returns API metadata and 200 OK."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Task API"
    assert data["version"] == "4.0"
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


# ==================================================
# A4 Auth Tests
# ==================================================

# --------------------------------------------------
# GET /public/info (Test 1)
# --------------------------------------------------
def test_get_public_info():
    """Test GET /public/info returns public message with 200 OK — no auth required."""
    response = client.get("/public/info")
    assert response.status_code == 200
    data = response.json()
    assert data == {"message": "Welcome stranger! This info is public."}


# --------------------------------------------------
# POST /auth/signup (Tests 2-4)
# --------------------------------------------------
def test_signup_valid(mock_supabase):
    """Test POST /auth/signup with valid email/password returns 201 Created."""
    mock_supabase.auth.sign_up.return_value = MockSignupResponse()

    response = client.post(
        "/auth/signup",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == "test@example.com"
    assert "created_at" in data


def test_signup_missing_email():
    """Test POST /auth/signup with missing email returns 400 Bad Request."""
    response = client.post("/auth/signup", json={"password": "password123"})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_signup_missing_password():
    """Test POST /auth/signup with missing password returns 400 Bad Request."""
    response = client.post("/auth/signup", json={"email": "test@example.com"})
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


# --------------------------------------------------
# POST /auth/login (Tests 5-7)
# --------------------------------------------------
def test_login_invalid_credentials(mock_supabase):
    """Test POST /auth/login with invalid credentials returns 401 Unauthorized."""
    mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")

    response = client.post(
        "/auth/login",
        json={"email": "wrong@example.com", "password": "wrongpass"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data == {"error": "Invalid login credentials"}


def test_login_valid(mock_supabase):
    """Test POST /auth/login with valid credentials returns 200 OK with tokens."""
    mock_supabase.auth.sign_in_with_password.return_value = MockLoginResponse()

    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["access_token"] == "mock-access-token-abc123"


def test_login_returns_access_token(mock_supabase):
    """Test successful login response contains access_token field."""
    mock_supabase.auth.sign_in_with_password.return_value = MockLoginResponse()

    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert len(data["access_token"]) > 0


# --------------------------------------------------
# GET /protected/profile — Auth required (Tests 8-12)
# --------------------------------------------------
def test_profile_without_auth():
    """Test GET /protected/profile without Authorization header returns 401."""
    response = client.get("/protected/profile")
    assert response.status_code == 401
    data = response.json()
    assert data == {"error": "Access token required"}


def test_profile_with_malformed_auth():
    """Test GET /protected/profile with malformed Authorization returns 401."""
    response = client.get(
        "/protected/profile",
        headers={"Authorization": "NotBearer some-token"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "error" in data


def test_profile_with_fake_token(mock_supabase):
    """Test GET /protected/profile with fake token returns 401."""
    mock_supabase.auth.get_user.side_effect = Exception("Invalid token")

    response = client.get(
        "/protected/profile",
        headers={"Authorization": "Bearer fake-token-12345"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data == {"error": "Invalid or expired token"}


def test_profile_with_tampered_token(mock_supabase):
    """Test GET /protected/profile with tampered token returns 401."""
    mock_supabase.auth.get_user.side_effect = Exception("Invalid token")

    response = client.get(
        "/protected/profile",
        headers={"Authorization": "Bearer tampered.jwt.token"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data == {"error": "Invalid or expired token"}


def test_profile_with_valid_token(mock_supabase):
    """Test GET /protected/profile with valid token returns 200 OK with user info."""
    mock_supabase.auth.get_user.return_value = MockGetUserResponse()

    response = client.get(
        "/protected/profile",
        headers={"Authorization": "Bearer valid-test-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-user-id-123"
    assert data["email"] == "test@example.com"
    assert "created_at" in data


# --------------------------------------------------
# GET /protected/dashboard — Auth required (Tests 13-14)
# --------------------------------------------------
def test_dashboard_without_auth():
    """Test GET /protected/dashboard without token returns 401."""
    response = client.get("/protected/dashboard")
    assert response.status_code == 401
    data = response.json()
    assert data == {"error": "Access token required"}


def test_dashboard_with_valid_token(mock_supabase):
    """Test GET /protected/dashboard with valid token returns 200 OK."""
    mock_supabase.auth.get_user.return_value = MockGetUserResponse()

    response = client.get(
        "/protected/dashboard",
        headers={"Authorization": "Bearer valid-test-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to your dashboard"
    assert data["user"]["id"] == "test-user-id-123"
    assert data["user"]["email"] == "test@example.com"


# --------------------------------------------------
# POST /auth/logout — Auth required (Tests 15-16)
# --------------------------------------------------
def test_logout_without_auth():
    """Test POST /auth/logout without token returns 401."""
    response = client.post("/auth/logout")
    assert response.status_code == 401
    data = response.json()
    assert data == {"error": "Access token required"}


def test_logout_with_valid_token(mock_supabase):
    """Test POST /auth/logout with valid token returns 204 No Content."""
    mock_supabase.auth.get_user.return_value = MockGetUserResponse()

    response = client.post(
        "/auth/logout",
        headers={"Authorization": "Bearer valid-test-token"},
    )
    assert response.status_code == 204
    assert response.content == b""
