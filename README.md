# Task API - REST CRUD API

A clean, beginner-friendly REST CRUD API built with Python and FastAPI for the FlyRank Internship Backend Track (Week 2 - Assignment A1).

---

## 📌 Description

This project implements a complete in-memory Task Management REST API. It supports standard CRUD operations (`GET`, `POST`, `PUT`, `DELETE`), robust input validation, meaningful error handling, and interactive API documentation powered by OpenAPI and Swagger UI.

> ⚠️ **Important Note on Data Storage**:
> All task data is stored strictly **in-memory**. There is no database or file persistence. When the server restarts, all data resets back to the initial 3 example tasks.

---

## 🚀 Features

- **Full CRUD Operations**:
  - `GET /`: Retrieve API metadata and resource endpoints.
  - `GET /health`: Health check endpoint.
  - `GET /tasks`: Retrieve the list of all tasks.
  - `GET /tasks/{id}`: Retrieve a single task by ID.
  - `POST /tasks`: Create a new task with automatic collision-free ID assignment.
  - `PUT /tasks/{id}`: Update an existing task's title and/or completion status.
  - `DELETE /tasks/{id}`: Delete a task by ID returning `204 No Content` with an empty body.
- **Strict Input Validation**:
  - Automatically rejects missing, empty, or whitespace-only task titles.
  - Disallows client-supplied `id` or `done` values on task creation.
  - Formats all validation and client errors as `400 Bad Request` with descriptive JSON messages (`{"error": "..."}`).
- **Proper HTTP Status Codes**: Returns `200`, `201`, `204`, `400`, and `404` accurately.
- **Interactive Swagger Documentation**: Built-in interactive UI at `/docs`.
- **Zero Database / Zero File Persist Overhead**: Lightweight and instant setup.
- **Comprehensive Automated Test Suite**: 100% test coverage for all endpoints and error cases.

---

## 🛠️ Technology Stack

- **Language**: Python 3.10+
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **ASGI Server**: [Uvicorn](https://www.uvicorn.org/)
- **Data Validation**: [Pydantic v2](https://docs.pydantic.dev/)
- **Testing**: [pytest](https://docs.pytest.org/) & [HTTPX](https://www.python-httpx.org/)

---

## 📁 Project Structure

```text
task-api/
├── main.py              # FastAPI application, route handlers, models, and error handlers
├── requirements.txt     # Minimal, strictly necessary dependencies
├── README.md            # Complete project documentation and guide
├── .gitignore           # Git ignore patterns for Python, venv, and test caches
└── tests/
    ├── __init__.py      # Test package initialization
    └── test_api.py      # Automated pytest suite covering all CRUD endpoints and errors
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository and navigate into the project directory
```bash
git clone <repository-url>
cd task-api
```

### 2. Create and activate a Python virtual environment (Python 3.10+)
```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (Command Prompt / PowerShell)
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Server

Start the local development server with live reload:

```bash
uvicorn main:app --reload
```

Once running, the server is available at:
- **Base API URL**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📖 API Endpoints & Status Codes

| Method | Endpoint | Description | Success Status | Error Statuses |
|---|---|---|---|---|
| `GET` | `/` | API metadata & root information | `200 OK` | - |
| `GET` | `/health` | API health check | `200 OK` | - |
| `GET` | `/tasks` | List all tasks | `200 OK` | - |
| `GET` | `/tasks/{id}` | Get single task by integer ID | `200 OK` | `404 Not Found` |
| `POST` | `/tasks` | Create a new task | `201 Created` | `400 Bad Request` |
| `PUT` | `/tasks/{id}` | Update task title and/or status | `200 OK` | `400 Bad Request`, `404 Not Found` |
| `DELETE` | `/tasks/{id}` | Delete task by integer ID | `204 No Content` (empty body) | `404 Not Found` |

---

## 📋 Initial Example Data

The in-memory database initializes with exactly 3 example tasks:

```json
[
  {
    "id": 1,
    "title": "Learn FastAPI",
    "done": false
  },
  {
    "id": 2,
    "title": "Build CRUD API",
    "done": false
  },
  {
    "id": 3,
    "title": "Test API with Swagger",
    "done": true
  }
]
```

---

## 🔍 Interactive Swagger UI

Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

- You can view all schemas (`TaskCreate`, `TaskUpdate`, `TaskResponse`, `ErrorResponse`).
- Use the **Try it out** button to execute any CRUD operation directly against your running local server.

---

## 💻 Working `curl` Examples

### 1. GET / (API Metadata)
```bash
curl -i http://localhost:8000/
```
**Response (`200 OK`):**
```json
{
  "name": "Task API",
  "version": "1.0",
  "endpoints": [
    "/tasks"
  ]
}
```

---

### 2. GET /health (Health Check)
```bash
curl -i http://localhost:8000/health
```
**Response (`200 OK`):**
```json
{
  "status": "ok"
}
```

---

### 3. GET /tasks (List All Tasks)
```bash
curl -i http://localhost:8000/tasks
```
**Response (`200 OK`):**
```json
[
  {
    "id": 1,
    "title": "Learn FastAPI",
    "done": false
  },
  {
    "id": 2,
    "title": "Build CRUD API",
    "done": false
  },
  {
    "id": 3,
    "title": "Test API with Swagger",
    "done": true
  }
]
```

---

### 4. GET /tasks/1 (Get Existing Task)
```bash
curl -i http://localhost:8000/tasks/1
```
**Response (`200 OK`):**
```json
{
  "id": 1,
  "title": "Learn FastAPI",
  "done": false
}
```

---

### 5. GET /tasks/99 (Get Unknown Task - 404)
```bash
curl -i http://localhost:8000/tasks/99
```
**Response (`404 Not Found`):**
```json
{
  "error": "Task 99 not found"
}
```

---

### 6. POST /tasks (Create Task)
```bash
curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy milk"}'
```
**Response (`201 Created`):**
```json
{
  "id": 4,
  "title": "Buy milk",
  "done": false
}
```

---

### 7. POST /tasks with Invalid Body (400 Bad Request)
```bash
curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "   "}'
```
**Response (`400 Bad Request`):**
```json
{
  "error": "Title is required and cannot be empty"
}
```

---

### 8. PUT /tasks/1 (Update Task)
```bash
curl -i -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Buy groceries", "done": true}'
```
**Response (`200 OK`):**
```json
{
  "id": 1,
  "title": "Buy groceries",
  "done": true
}
```

---

### 9. PUT /tasks/1 with Invalid Body (400 Bad Request)
```bash
curl -i -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"title": ""}'
```
**Response (`400 Bad Request`):**
```json
{
  "error": "Title cannot be empty"
}
```

---

### 10. DELETE /tasks/1 (Delete Task - 204 No Content)
```bash
curl -i -X DELETE http://localhost:8000/tasks/1
```
**Response (`204 No Content`):**
```http
HTTP/1.1 204 No Content
date: ...
server: uvicorn
```
*(No response body is returned)*

---

## 🧪 Automated Testing

Run the automated test suite with pytest:

```bash
pytest
```

For verbose output with test details:
```bash
pytest -v
```

---

## 🔄 Resetting Data

Since tasks exist only in memory, you can reset the data at any time by stopping the server (`Ctrl+C`) and restarting it:

```bash
uvicorn main:app --reload
```
