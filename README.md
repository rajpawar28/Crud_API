# Task API - REST CRUD API with SQLite Database

A clean, beginner-friendly REST CRUD API built with Python, FastAPI, and SQLite for the FlyRank Internship Backend Track (Week 3 - Assignment A2: *"Connecting your CRUD to the database"*).

---

## 📌 Description

This project builds upon Week 2's Assignment A1 by migrating the storage layer from an ephemeral in-memory list to a persistent **SQLite database (`tasks.db`)**.

The API contract (endpoints, request/response formats, validation rules, error handling, status codes, and Swagger UI) remains 100% identical to A1, but all task data is now safely stored on disk in SQLite and survives server restarts.

---

## 🆕 What's New in Week 3 (Assignment A2)

- **SQLite Database Persistence**: All task operations now read and write directly to a local SQLite database (`tasks.db`).
- **Automatic Initialization & Seeding**: `tasks.db` and the `tasks` table are automatically created on startup. Seed data (3 initial example tasks) is only inserted if the table is empty (`COUNT(*) == 0`), preventing data duplication upon server restarts.
- **100% Parameterized SQL**: All user inputs in `SELECT`, `INSERT`, `UPDATE`, and `DELETE` queries strictly use parameter placeholders (`?`) to prevent SQL injection vulnerabilities.
- **Database Explorer Compatibility**: The generated `tasks.db` is standard SQLite and can be opened directly with tools like [DB Browser for SQLite](https://sqlitebrowser.org/).
- **Isolated Automated Test Suite**: Automated tests execute against isolated temporary SQLite instances, ensuring zero test data corruption on the main development database.

---

## 💡 Why SQLite?

1. **Zero Setup Overhead**: SQLite requires no separate server processes, user management, or network configuration.
2. **Built Into Python**: Uses Python's standard library `sqlite3` without third-party database drivers.
3. **Single File Portability**: The entire database lives in a single local file (`tasks.db`).
4. **Data Persistence**: Data created in one session remains safely stored on disk and persists across restarts.
5. **Beginner Friendly & Production Lightweight**: Provides ACID-compliant transactions and standard SQL syntax while remaining lightweight.

---

## 🛠️ Technology Stack

- **Language**: Python 3.10+
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **ASGI Server**: [Uvicorn](https://www.uvicorn.org/)
- **Database**: [SQLite](https://www.sqlite.org/) (Python built-in `sqlite3`)
- **Data Validation**: [Pydantic v2](https://docs.pydantic.dev/)
- **Testing**: [pytest](https://docs.pytest.org/) & [HTTPX](https://www.python-httpx.org/)

---

## 🗄️ Database Schema & Storage

The application creates and connects to `tasks.db` located in the project root directory.

### Table: `tasks`

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL DEFAULT 0
);
```

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Unique auto-generated task ID |
| `title` | `TEXT` | `NOT NULL` | Task title string (cannot be empty) |
| `done` | `BOOLEAN` | `NOT NULL DEFAULT 0` | Completion status (stored as `0` or `1`, returned as boolean) |

### Automatic Seeding & Restart Behavior

When the database is initialized, the application checks `SELECT COUNT(*) FROM tasks;`:
- If `count == 0`, it inserts the 3 initial example tasks:
  1. `{"id": 1, "title": "Learn FastAPI", "done": false}`
  2. `{"id": 2, "title": "Build CRUD API", "done": false}`
  3. `{"id": 3, "title": "Test API with Swagger", "done": true}`
- If `count > 0`, it skips seeding, guaranteeing that existing tasks and newly created tasks are never overwritten or duplicated across server restarts.

> ℹ️ **Note on Version Control**: `tasks.db` is added to `.gitignore` so every developer or clone starts with a clean, freshly generated database.

---

## 📁 Project Structure

```text
task-api/
├── main.py              # FastAPI application, route handlers, models, and exception handlers
├── database.py          # SQLite connection manager, schema initialization, and seeding
├── requirements.txt     # Minimal dependencies (fastapi, uvicorn, pytest, httpx)
├── README.md            # Comprehensive project documentation and guides
├── .gitignore           # Ignores tasks.db, .venv, __pycache__, and test caches
└── tests/
    ├── __init__.py      # Test package initialization
    └── test_api.py      # Automated pytest suite covering SQLite CRUD, isolation, and persistence
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository and navigate into the project directory
```bash
git clone https://github.com/rajpawar28/Crud_API.git
cd Crud_API
```

### 2. Create and activate a Python virtual environment (Python 3.10+)
```bash
# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Server

Start the FastAPI application with Uvicorn:

```bash
uvicorn main:app --reload
```

Once running, access:
- **Base API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📖 API Endpoints & Status Codes

| Method | Endpoint | Description | Success Status | Error Statuses |
|---|---|---|---|---|
| `GET` | `/` | API metadata & root information | `200 OK` | - |
| `GET` | `/health` | API health check | `200 OK` | - |
| `GET` | `/tasks` | List all tasks from SQLite | `200 OK` | - |
| `GET` | `/tasks/{id}` | Get single task by integer ID | `200 OK` | `404 Not Found` |
| `POST` | `/tasks` | Create a new task in SQLite | `201 Created` | `400 Bad Request` |
| `PUT` | `/tasks/{id}` | Update task title and/or status | `200 OK` | `400 Bad Request`, `404 Not Found` |
| `DELETE` | `/tasks/{id}` | Delete task by integer ID | `204 No Content` (empty body) | `404 Not Found` |

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
  "version": "2.0",
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

### 3. GET /tasks (List All Tasks from SQLite)
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

### 6. POST /tasks (Create Task in SQLite)
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

## 🔄 Testing Database Persistence Across Restarts

To verify that SQLite preserves tasks across server restarts:

1. Start server: `uvicorn main:app --reload`
2. Create a task:
   ```bash
   curl -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"title": "Persistent Task"}'
   ```
3. Stop the server (`Ctrl+C`).
4. Start the server again: `uvicorn main:app --reload`
5. Fetch tasks:
   ```bash
   curl http://localhost:8000/tasks
   ```
6. Observe that `"Persistent Task"` is still present in the list and seed data was **not** duplicated.

---

## 🖥️ Viewing the Database with DB Browser for SQLite

1. Download and install [DB Browser for SQLite](https://sqlitebrowser.org/).
2. Launch the application and click **Open Database**.
3. Select the `tasks.db` file in the project root directory.
4. Click the **Browse Data** tab and choose the `tasks` table to inspect the live rows (`id`, `title`, `done`).

---

## 🔍 SQL Queries Explored (Stage 4)

During database testing and verification, the following standard SQL queries were tested:

1. **Select all tasks**:
   ```sql
   SELECT * FROM tasks;
   ```
   *Result*: Fetches all 3 seeded records with their columns `(id, title, done)`.

2. **Select only completed tasks**:
   ```sql
   SELECT * FROM tasks WHERE done = 1;
   ```
   *Result*: Returns `(3, 'Test API with Swagger', 1)`.

3. **Count total tasks in database**:
   ```sql
   SELECT COUNT(*) FROM tasks;
   ```
   *Result*: Returns `3` (used by `init_db()` to prevent duplicate seeds).

4. **Update all tasks to done**:
   ```sql
   UPDATE tasks SET done = 1;
   ```
   *Result*: Updates all records' completion status to `1`.

5. **Delete completed tasks**:
   ```sql
   DELETE FROM tasks WHERE done = 1;
   ```
   *Result*: Removes tasks where `done == 1`.

---

## 🧪 Automated Testing

Run the full pytest suite:

```bash
pytest -v
```

All 22 test cases run against isolated temporary SQLite databases to guarantee test purity.

---

## 🤖 AI vs Me

In Stage 6 of the assignment, we conducted an AI rematch by comparing a standard naive prompt against our carefully hand-crafted, production-ready implementation located in the root repository. The raw AI generated code is preserved in [`ai-version/main.py`](file:///Users/rajpawar/.gemini/antigravity-ide/scratch/task-api/ai-version/main.py).

### 1. The Full AI Prompt
```text
Build a Python FastAPI task CRUD API connecting to SQLite. Store tasks with id, title, done. Seed 3 tasks on startup and implement GET, POST, PUT, DELETE.
```

### 2. Concrete Differences Identified
1. **Modular Architecture & Database Separation**: The hand-built version neatly separates database lifecycle and connection management into `database.py` and uses FastAPI `lifespan` context managers, whereas the naive AI version crammed global connections and deprecated `@app.on_event("startup")` handlers into a single file.
2. **Strict 400 Bad Request vs 422 Error Handling**: The hand-built version implements custom exception handlers for `RequestValidationError` to adhere strictly to the assignment's `400 Bad Request` JSON format (`{"error": "..."}`), whereas the AI version would emit FastAPI's default `422 Unprocessable Entity` for unhandled Pydantic validation failures.
3. **Database Test Isolation**: The hand-built version uses isolated temporary SQLite databases per test run so test execution never pollutes or wipes the local `tasks.db`, whereas the AI version tests directly modified the production database.

### 3. What AI Did Better
- The AI rapidly drafted the core raw SQL queries (`INSERT`, `SELECT`, `UPDATE`, `DELETE`) with parameterized placeholders in minimal lines of code.

### 4. What AI Got Wrong or Ignored
- Used deprecated `@app.on_event("startup")` instead of modern FastAPI `lifespan`.
- Failed to prevent duplicate seeding when restarted unless the exact conditional check was explicitly reminded.
- Omitted Swagger UI tag groupings, example payloads, and OpenAPI error response schemas.

### 5. What the Original Prompt Failed to Specify
- Did not specify strict `400` status code constraints on schema validation.
- Did not specify test isolation requirements or multi-file architecture guidelines.

### 6. Summary Statement
*After supplying the comprehensive specification with explicit status codes, validation models, and test isolation requirements, the implementation achieved complete test compliance and enterprise-grade structure.*

