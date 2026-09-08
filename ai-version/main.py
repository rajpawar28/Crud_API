"""AI Generated Version - Task API with SQLite.

Created for comparison against the hand-crafted implementation in Assignment A2.
"""

import os
import sqlite3
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI(title="AI Task API", version="1.0")

DB_FILE = "tasks_ai.db"


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


@app.on_event("startup")
def startup():
    conn = get_db()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT, done INTEGER DEFAULT 0);"
    )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM tasks;").fetchone()[0]
    if count == 0:
        conn.execute("INSERT INTO tasks (title, done) VALUES ('Task 1', 0);")
        conn.execute("INSERT INTO tasks (title, done) VALUES ('Task 2', 0);")
        conn.execute("INSERT INTO tasks (title, done) VALUES ('Task 3', 1);")
        conn.commit()
    conn.close()


class TaskSchema(BaseModel):
    title: str
    done: Optional[bool] = False


@app.get("/tasks")
def list_tasks():
    conn = get_db()
    rows = conn.execute("SELECT id, title, done FROM tasks;").fetchall()
    conn.close()
    return [{"id": r["id"], "title": r["title"], "done": bool(r["done"])} for r in rows]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_db()
    row = conn.execute("SELECT id, title, done FROM tasks WHERE id = ?;", (task_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


@app.post("/tasks", status_code=201)
def create_task(task: TaskSchema):
    if not task.title or not task.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title, done) VALUES (?, ?);", (task.title.strip(), 0))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id, "title": task.title.strip(), "done": False}
