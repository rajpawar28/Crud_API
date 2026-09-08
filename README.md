# Task API - Authenticated FastAPI + PostgreSQL + Docker Stack

A production-ready, containerized REST CRUD API built with Python, FastAPI, PostgreSQL, and **Supabase Authentication** for the FlyRank Internship Backend Track.

**Assignment Progression:**
- **A1**: In-memory CRUD API
- **A2**: SQLite-backed API
- **A3**: PostgreSQL + Docker + Docker Compose
- **A4**: **Supabase Auth · Login & Protect** ← current

The complete stack spins up with a single command:
```bash
docker compose up
```

---

## 🏗️ System Architecture

```text
       Client / Browser / curl
                 │
     ┌───────────┴───────────┐
     │                       │
     ▼                       ▼
  Auth Routes           Task Routes
  /auth/signup           /tasks
  /auth/login            /tasks/{id}
  /auth/logout
     │                       │
     ▼                       ▼
┌──────────┐     ┌───────────────────────┐
│ Supabase │     │  PostgreSQL Container │
│  Auth    │     │    (task_db:5432)     │
│ (Cloud)  │     └───────────┬───────────┘
└──────────┘                 │
                    Docker Named Volume
                      ('taskdata')
```

**Key Design:**
- **Supabase** is the Identity Provider — handles user accounts, password hashing, JWTs
- **PostgreSQL** stores task data (CRUD operations)
- **FastAPI** does NOT store passwords, hash passwords, or implement custom crypto

---

## 🛠️ Technology Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+)
- **ASGI Server**: [Uvicorn](https://www.uvicorn.org/)
- **Database**: [PostgreSQL 16](https://www.postgresql.org/) (Docker)
- **DB Driver**: [psycopg 3](https://www.psycopg.org/psycopg3/) (`psycopg[binary]`)
- **Auth Provider**: [Supabase Auth](https://supabase.com/docs/guides/auth) (`supabase` Python SDK)
- **Containerization**: Docker & Docker Compose
- **Validation**: Pydantic v2
- **Testing**: pytest & HTTPX

---

## 📋 Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or equivalent)
- Docker Compose v2+
- A [Supabase](https://supabase.com/) project (free tier works)

### Supabase Setup

1. Create a project at [supabase.com](https://supabase.com/)
2. Go to **Project Settings → API** and copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon/public key** → `SUPABASE_KEY`
3. Go to **Authentication → Sign In / Providers → Email** and:
   - **Turn "Confirm email" OFF** (for development/testing convenience)

> ⚠️ **NEVER use the `service_role` key.** Only use the anon/public key.

---

## 🔐 Environment Variables

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgres://postgres:dev@db:5432/tasks` |
| `SUPABASE_URL` | Supabase project URL | `https://xxxxx.supabase.co` |
| `SUPABASE_KEY` | Supabase anon/public key | `eyJhbGciOi...` |
| `PORT` | Server port | `3000` |

Setup:
```bash
cp .env.example .env
# Edit .env with your real Supabase credentials
```

> `.env` is listed in both `.gitignore` and `.dockerignore` — secrets never enter Git or Docker images.

---

## ▶️ Running the Project

### Option 1: Docker Compose (Recommended)

```bash
git clone https://github.com/rajpawar28/Crud_API.git
cd Crud_API
cp .env.example .env
# Edit .env with your Supabase credentials
docker compose up --build
```

- **API**: [http://localhost:3000](http://localhost:3000)
- **Swagger UI**: [http://localhost:3000/docs](http://localhost:3000/docs)

### Option 2: Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set DATABASE_URL to localhost and add Supabase credentials
uvicorn main:app --port 8000
```

---

## 📖 API Endpoints

### General & Tasks (from A1–A3)

| Method | Endpoint | Auth? | Success | Error |
|---|---|---|---|---|
| `GET` | `/` | No | `200` | — |
| `GET` | `/health` | No | `200` | — |
| `GET` | `/tasks` | No | `200` | — |
| `GET` | `/tasks/{id}` | No | `200` | `404` |
| `POST` | `/tasks` | No | `201` | `400` |
| `PUT` | `/tasks/{id}` | No | `200` | `400`, `404` |
| `DELETE` | `/tasks/{id}` | No | `204` | `404` |

### Auth (A4)

| Method | Endpoint | Auth? | Success | Error |
|---|---|---|---|---|
| `POST` | `/auth/signup` | No | `201` | `400` |
| `POST` | `/auth/login` | No | `200` | `400`, `401` |
| `POST` | `/auth/logout` | **Yes** | `204` | `401` |

### Public (A4)

| Method | Endpoint | Auth? | Success | Error |
|---|---|---|---|---|
| `GET` | `/public/info` | No | `200` | — |

### Protected (A4)

| Method | Endpoint | Auth? | Success | Error |
|---|---|---|---|---|
| `GET` | `/protected/profile` | **Yes** | `200` | `401` |
| `GET` | `/protected/dashboard` | **Yes** | `200` | `401` |

---

## 🔑 Authentication Flow

### 1. Sign Up
```bash
curl -i -X POST http://localhost:3000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```
**Response (`201 Created`):**
```json
{
  "id": "user-uuid-here",
  "email": "test@example.com",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 2. Log In
```bash
curl -i -X POST http://localhost:3000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```
**Response (`200 OK`):**
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "abc123..."
}
```

### 3. Access Protected Route
```bash
curl -i http://localhost:3000/protected/profile \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```
**Response (`200 OK`):**
```json
{
  "id": "user-uuid-here",
  "email": "test@example.com",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 4. Access Without Token → 401
```bash
curl -i http://localhost:3000/protected/profile
```
**Response (`401 Unauthorized`):**
```json
{
  "error": "Access token required"
}
```

### 5. Access With Tampered Token → 401
```bash
curl -i http://localhost:3000/protected/profile \
  -H "Authorization: Bearer tampered.fake.token"
```
**Response (`401 Unauthorized`):**
```json
{
  "error": "Invalid or expired token"
}
```

### 6. Public Info (No Auth)
```bash
curl -i http://localhost:3000/public/info
```
**Response (`200 OK`):**
```json
{
  "message": "Welcome stranger! This info is public."
}
```

### 7. Dashboard (Protected)
```bash
curl -i http://localhost:3000/protected/dashboard \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```
**Response (`200 OK`):**
```json
{
  "message": "Welcome to your dashboard",
  "user": {
    "id": "user-uuid-here",
    "email": "test@example.com"
  }
}
```

### 8. Log Out (Protected)
```bash
curl -i -X POST http://localhost:3000/auth/logout \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```
**Response (`204 No Content`):**
*(Empty body)*

---

## 🛡️ Security Architecture

| Requirement | Implementation |
|---|---|
| Password storage | **Supabase handles it** — backend never sees or stores passwords |
| Token verification | `supabase.auth.get_user(token)` — network call, not local JWT decode |
| Auth dependency | Single reusable `get_current_user()` FastAPI dependency |
| Swagger UI | HTTPBearer scheme — "Authorize" padlock button in `/docs` |
| Secret management | `.env` excluded from Git and Docker via `.gitignore` + `.dockerignore` |
| API key usage | Anon/public key only — `service_role` never used |
| Error responses | Exact JSON: `"Access token required"`, `"Invalid or expired token"`, `"Invalid login credentials"` |

---

## 🧪 Automated Testing

```bash
source .venv/bin/activate
pytest -v
```

**37 tests** total:
- 21 existing A3 CRUD tests (preserved)
- 16 new A4 auth tests (mocked Supabase)

Test coverage includes:
- Public info access (no auth)
- Signup (valid, missing email, missing password)
- Login (valid, invalid credentials, token returned)
- Protected profile (no token, malformed, fake, tampered, valid)
- Protected dashboard (no token, valid)
- Logout (no token, valid → 204)

---

## 📁 Project Structure

```text
Crud_API/
├── compose.yaml         # Docker Compose (api + db + taskdata volume)
├── Dockerfile           # FastAPI Docker build
├── .dockerignore        # Prevents .env/secrets from entering Docker image
├── .env.example         # Environment variables template
├── .gitignore           # Ignores .env, .venv, bytecode, caches
├── main.py              # FastAPI app: routes, models, exception handlers
├── database.py          # PostgreSQL psycopg 3 repository & seed logic
├── supabase_client.py   # Supabase client initialization (A4)
├── auth.py              # Reusable auth dependency with HTTPBearer (A4)
├── requirements.txt     # Python dependencies
├── README.md            # This file
├── ai-version/
│   └── main.py          # AI comparison reference (Stage 6)
└── tests/
    ├── __init__.py      # Package marker
    └── test_api.py      # 37 automated tests (CRUD + Auth)
```

---

## 🔄 Assignment Progression

| Assignment | Storage | Auth | Deployment |
|---|---|---|---|
| **A1** | In-memory list | None | Local `uvicorn` |
| **A2** | SQLite (`tasks.db`) | None | Local `uvicorn` |
| **A3** | PostgreSQL (Docker) | None | `docker compose up` |
| **A4** | PostgreSQL (Docker) | **Supabase Auth** | `docker compose up` |

---

## 🔍 Inspecting the Database

```bash
docker compose exec db psql -U postgres -d tasks
```

```sql
SELECT * FROM tasks;
SELECT COUNT(*) FROM tasks;
\q
```

---

## 🤖 AI vs Me

In Stage 6 of A3, we evaluated an AI-generated containerization solution. The raw AI version is in `ai-version/main.py`.

**Key differences:** The hand-built version includes retry logic, Docker healthchecks, repository layer isolation, and strict 400 error formatting — all missed by naive AI implementations.
