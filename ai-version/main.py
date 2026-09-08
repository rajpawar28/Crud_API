"""AI-Generated Reference Implementation - Containerized PostgreSQL Stack.

Created for Stage 6 AI vs Me comparison against the hand-crafted implementation.
"""

import os
import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="AI Task API (Postgres)")

DATABASE_URL = os.getenv("DATABASE_URL", "postgres://postgres:dev@db:5432/tasks")


def get_db():
    return psycopg.connect(DATABASE_URL)


@app.on_event("startup")
def startup_db():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS tasks (id SERIAL PRIMARY KEY, title TEXT, done BOOLEAN DEFAULT FALSE);"
            )
            cur.execute("SELECT COUNT(*) FROM tasks;")
            if cur.fetchone()[0] == 0:
                cur.execute("INSERT INTO tasks (title, done) VALUES ('Task 1', false);")
                cur.execute("INSERT INTO tasks (title, done) VALUES ('Task 2', false);")
                cur.execute("INSERT INTO tasks (title, done) VALUES ('Task 3', true);")
            conn.commit()


class TaskIn(BaseModel):
    title: str


@app.get("/tasks")
def get_all():
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks;")
            rows = cur.fetchall()
            return [{"id": r[0], "title": r[1], "done": r[2]} for r in rows]


@app.post("/tasks", status_code=201)
def add_task(t: TaskIn):
    if not t.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done;",
                (t.title, False),
            )
            row = cur.fetchone()
            conn.commit()
            return {"id": row[0], "title": row[1], "done": row[2]}
