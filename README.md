# Task API - Containerized FastAPI & PostgreSQL Stack

A production-ready, containerized REST CRUD API built with Python, FastAPI, and PostgreSQL for the FlyRank Internship Backend Track (Week 3 - Assignment A3: *"Containerize Your Stack"*).

The complete stack (FastAPI application + PostgreSQL database + persistent volume) spins up with a single command:
```bash
docker compose up
```

---

## 🆕 What's New in Week 3 (Assignment A3)

- **A1**: In-memory list storage (ephemeral).
- **A2**: SQLite local file storage (`tasks.db`).
- **A3**: **PostgreSQL running inside Docker** + **Containerized FastAPI application** managed via **Docker Compose**.
- **Container Networking**: FastAPI connects to PostgreSQL using the Docker network service name (`db:5432`).
- **Persistent Docker Volume**: Database rows survive container restarts and `docker compose down` using named volume `taskdata`.
- **psycopg 3 Driver**: Uses modern, high-performance `psycopg` 3 with 100% parameterized queries (`%s`).
- **Zero Local DB Installation**: No local PostgreSQL installation is required on your host machine.

---

## 🏗️ System Architecture

```text
       Client / Browser / curl
                 │
                 ▼
┌───────────────────────────────────┐
│     Docker Compose Network        │
│                                   │
│  ┌─────────────────────────────┐  │
│  │   FastAPI API Container     │  │
│  │   (task_api, Port 3000)     │  │
│  └──────────────┬──────────────┘  │
│                 │                 │
│                 │ (db:5432)       │
│                 ▼                 │
│  ┌─────────────────────────────┐  │
│  │  PostgreSQL Container       │  │
│  │   (task_db, Port 5432)      │  │
│  └──────────────┬──────────────┘  │
└─────────────────┼─────────────────┘
                  │
                  ▼
       ┌─────────────────────┐
       │ Docker Named Volume │
       │    ('taskdata')     │
       └─────────────────────┘
```

---

## 🛠️ Technology Stack

- **Application Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **ASGI Web Server**: [Uvicorn](https://www.uvicorn.org/)
- **Database Engine**: [PostgreSQL 16](https://www.postgresql.org/) (Official Docker Image)
- **Database Driver**: [psycopg 3](https://www.psycopg.org/psycopg3/) (`psycopg[binary]`)
- **Containerization**: [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)
- **Data Validation**: [Pydantic v2](https://docs.pydantic.dev/)
- **Testing**: [pytest](https://docs.pytest.org/) & [HTTPX](https://www.python-httpx.org/)

---

## 📋 Prerequisites

To run this application, you only need:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Podman / OrbStack)
- Docker Compose v2+

> 💡 **Zero Local PostgreSQL Requirement**: You do NOT need to install PostgreSQL locally on your host machine.

---

## 🔐 Environment Variables & Secrets

Database credentials and connection URLs are managed securely via environment variables.

| Variable | Description | Example (Local Host) | Example (Docker Compose) |
|---|---|---|---|
| `DATABASE_URL` | Full PostgreSQL connection string | `postgres://postgres:dev@localhost:5432/tasks` | `postgres://postgres:dev@db:5432/tasks` |

- **`.env.example`** (Committed): Provides safe template configurations.
- **`.env`** (Ignored in `.gitignore` & `.dockerignore`): Keeps local secrets out of version control and Docker images.

---

## ▶️ Running the Project (One-Command Startup)

### 1. Clone the repository
```bash
git clone https://github.com/rajpawar28/Crud_API.git
cd Crud_API
```

### 2. (Optional) Setup `.env`
```bash
cp .env.example .env
```

### 3. Start the entire container stack
```bash
docker compose up --build
```

To run in the background (detached mode):
```bash
docker compose up -d
```

Once started:
- **FastAPI API**: [http://localhost:3000](http://localhost:3000)
- **Interactive Swagger UI**: [http://localhost:3000/docs](http://localhost:3000/docs)
- **ReDoc Documentation**: [http://localhost:3000/redoc](http://localhost:3000/redoc)
- **PostgreSQL Database**: `localhost:5432`

---

## 🗄️ Database Schema & Seeding Behavior

### Table: `tasks`
```sql
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL DEFAULT FALSE
);
```

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` | Unique auto-incrementing task ID |
| `title` | `TEXT` | `NOT NULL` | Task title string (validated non-empty) |
| `done` | `BOOLEAN` | `NOT NULL DEFAULT FALSE` | Boolean completion flag (`true`/`false`) |

### Automatic Seeding Logic
On startup, the application checks `SELECT COUNT(*) FROM tasks;`:
- If `count == 0`, it inserts the 3 initial example tasks:
  1. `{"id": 1, "title": "Learn FastAPI", "done": false}`
  2. `{"id": 2, "title": "Build CRUD API", "done": false}`
  3. `{"id": 3, "title": "Test API with Swagger", "done": true}`
- If `count > 0`, seeding is skipped, preventing duplicate rows across restarts.

---

## 📖 API Endpoints & Status Codes

| Method | Endpoint | Description | Success Status | Error Statuses |
|---|---|---|---|---|
| `GET` | `/` | API metadata & root information | `200 OK` | - |
| `GET` | `/health` | API health check | `200 OK` | - |
| `GET` | `/tasks` | List all tasks from PostgreSQL | `200 OK` | - |
| `GET` | `/tasks/{id}` | Get single task by integer ID | `200 OK` | `404 Not Found` |
| `POST` | `/tasks` | Create a new task in PostgreSQL | `201 Created` | `400 Bad Request` |
| `PUT` | `/tasks/{id}` | Update task title and/or status | `200 OK` | `400 Bad Request`, `404 Not Found` |
| `DELETE` | `/tasks/{id}` | Delete task by integer ID | `204 No Content` (empty body) | `404 Not Found` |

---

## 💻 Working `curl` Examples

### 1. GET / (API Metadata)
```bash
curl -i http://localhost:3000/
```
**Response (`200 OK`):**
```json
{
  "name": "Task API",
  "version": "3.0",
  "endpoints": [
    "/tasks"
  ]
}
```

---

### 2. GET /health (Health Check)
```bash
curl -i http://localhost:3000/health
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
curl -i http://localhost:3000/tasks
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
curl -i http://localhost:3000/tasks/1
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
curl -i http://localhost:3000/tasks/99
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
curl -i -X POST http://localhost:3000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Docker container task"}'
```
**Response (`201 Created`):**
```json
{
  "id": 4,
  "title": "Docker container task",
  "done": false
}
```

---

### 7. POST /tasks with Invalid Body (400 Bad Request)
```bash
curl -i -X POST http://localhost:3000/tasks \
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
curl -i -X PUT http://localhost:3000/tasks/1 \
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

### 9. DELETE /tasks/1 (Delete Task - 204 No Content)
```bash
curl -i -X DELETE http://localhost:3000/tasks/1
```
**Response (`204 No Content`):**
```http
HTTP/1.1 204 No Content
date: ...
server: uvicorn
```
*(No response body returned)*

---

## 🔍 Inspecting the Database with `psql`

You can connect directly to the running PostgreSQL container using `docker compose exec`:

```bash
docker compose exec db psql -U postgres -d tasks
```

Inside the interactive `psql` shell:
```sql
-- List tables
\dt

-- View all task rows
SELECT * FROM tasks;

-- Count total tasks
SELECT COUNT(*) FROM tasks;

-- Exit psql
\q
```

---

## 🔄 Persistence Test Across `docker compose down`

To verify database persistence with Docker named volumes:

1. Start the stack: `docker compose up -d`
2. Create a new task:
   ```bash
   curl -X POST http://localhost:3000/tasks -H "Content-Type: application/json" -d '{"title": "Persistent Docker Task"}'
   ```
3. Take down the containers:
   ```bash
   docker compose down
   ```
4. Start the stack again:
   ```bash
   docker compose up -d
   ```
5. Fetch tasks:
   ```bash
   curl http://localhost:3000/tasks
   ```
6. Observe that `"Persistent Docker Task"` still exists and initial seed data was not duplicated!

---

## 🧪 Automated Testing

Run the automated test suite locally:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run pytest
pytest -v
```

All 21 test cases execute against isolated database fixtures ensuring complete test purity.

---

## 📁 Project Structure

```text
Crud_API/
├── compose.yaml         # Docker Compose configuration (api + db + taskdata volume)
├── Dockerfile           # Multi-stage/lightweight FastAPI Docker build
├── .dockerignore        # Prevents secrets/caches from entering Docker image
├── .env.example         # Example environment variables template
├── .gitignore           # Ignores .env, .venv, bytecode, and test caches
├── main.py              # FastAPI application, route handlers, models, and lifespan
├── database.py          # PostgreSQL psycopg 3 repository, connection, and seed logic
├── requirements.txt     # Python dependencies (fastapi, uvicorn, psycopg, python-dotenv, pytest)
├── README.md            # Comprehensive project documentation
├── ai-version/
│   └── main.py          # AI comparison reference implementation (Stage 6)
└── tests/
    ├── __init__.py      # Package marker
    └── test_api.py      # Automated test suite
```

---

## 🤖 AI vs Me

In Stage 6 of the assignment, we evaluated an AI-generated containerization solution against our hand-crafted implementation. The raw AI version is stored in [`ai-version/main.py`](file:///Users/rajpawar/.gemini/antigravity-ide/scratch/task-api/ai-version/main.py).

### 1. The Full AI Prompt
```text
Containerize a FastAPI Task CRUD API with PostgreSQL in Docker. Include Dockerfile, compose.yaml with persistent volume, psycopg 3 parameterized queries, and automatic 3-task seeding on empty database.
```

### 2. Concrete Differences Identified
1. **Connection Reliability & Retries**: The hand-built version includes retry logic in `init_db()` alongside Docker Compose `healthcheck` dependencies (`condition: service_healthy`), whereas naive AI implementations crash if the API container starts before PostgreSQL completes initialization.
2. **Repository Layer Isolation**: The hand-built version cleanly encapsulates all PostgreSQL queries into `database.py` with parameterized `%s` queries and `RETURNING` clauses, keeping `main.py` routes completely clean.
3. **Strict 400 Bad Request Formatting**: Custom exception handlers ensure invalid request bodies emit `400 Bad Request` with `{"error": "..."}` rather than FastAPI's default `422`.

### 3. What AI Did Better
- Rapidly templated basic `Dockerfile` and `compose.yaml` boilerplate syntax.

### 4. What AI Got Wrong or Ignored
- Missed healthchecks on the database service leading to container race conditions.
- Omitted `.dockerignore` causing local virtual environments and `.env` files to be copied into the container.

### 5. What the Original Prompt Failed to Specify
- Container healthchecks, service restart policies, and clean test isolation.

### 6. Summary Statement
*Implementing structured healthchecks, container isolation, and repository modularity delivered a resilient, zero-configuration Docker Compose deployment.*
