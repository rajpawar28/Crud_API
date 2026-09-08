"""Database module for Task API (PostgreSQL with psycopg 3).

Handles PostgreSQL connection management, schema initialization, retry logic,
and initial seed data using environment-based configuration.
Follows the FlyRank Week 3 Assignment A3 specification.
"""

import os
import time
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
import psycopg
from psycopg.rows import dict_row

# Load environment variables from .env file if present
load_dotenv()

# Default PostgreSQL connection URL (overridable via DATABASE_URL env var)
DEFAULT_DATABASE_URL = "postgres://postgres:dev@localhost:5432/tasks"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

# Initial seed data for empty database (exactly 3 tasks)
INITIAL_TASKS: List[Tuple[str, bool]] = [
    ("Learn FastAPI", False),
    ("Build CRUD API", False),
    ("Test API with Swagger", True),
]


def get_db_url(db_url: Optional[str] = None) -> str:
    """Return the active database connection URL."""
    return db_url or os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_db_connection(db_url: Optional[str] = None) -> psycopg.Connection:
    """Create and return a configured PostgreSQL connection using psycopg 3.

    Configured with dict_row row_factory for dictionary-like column access.
    """
    url = get_db_url(db_url)
    conn = psycopg.connect(url, row_factory=dict_row)
    return conn


def init_db(
    db_url: Optional[str] = None, max_retries: int = 5, retry_delay: float = 2.0
) -> None:
    """Initialize the PostgreSQL database schema and seed initial tasks if table is empty.

    Includes retry logic to ensure connection reliability when Docker containers are starting up.
    - Creates the tasks table if it does not exist.
    - Only seeds the 3 initial tasks when the table is completely empty (COUNT == 0).
    - Prevents seed data duplication upon subsequent server restarts.
    """
    url = get_db_url(db_url)
    conn = None

    for attempt in range(1, max_retries + 1):
        try:
            conn = psycopg.connect(url, row_factory=dict_row)
            break
        except Exception as e:
            if attempt < max_retries:
                time.sleep(retry_delay)
            else:
                raise ConnectionError(
                    f"Failed to connect to PostgreSQL at {url} after {max_retries} attempts: {e}"
                ) from e

    try:
        with conn.cursor() as cursor:
            # Create tasks table with primary key id, title, and boolean done
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE
                );
                """
            )
            conn.commit()

            # Check whether the table currently has any records
            cursor.execute("SELECT COUNT(*) FROM tasks;")
            row = cursor.fetchone()
            count = row["count"] if isinstance(row, dict) else row[0]

            # Only insert seed records when the table is completely empty
            if count == 0:
                for title, done in INITIAL_TASKS:
                    cursor.execute(
                        "INSERT INTO tasks (title, done) VALUES (%s, %s);",
                        (title, done),
                    )
                conn.commit()
    finally:
        conn.close()


# --------------------------------------------------
# Database Query Repository Functions
# --------------------------------------------------
def fetch_all_tasks(db_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all tasks from PostgreSQL."""
    with get_db_connection(db_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, title, done FROM tasks ORDER BY id ASC;")
            rows = cursor.fetchall()
            return [
                {"id": r["id"], "title": r["title"], "done": bool(r["done"])}
                for r in rows
            ]


def fetch_task_by_id(
    task_id: int, db_url: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Retrieve a single task by ID from PostgreSQL."""
    with get_db_connection(db_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, done FROM tasks WHERE id = %s;",
                (task_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return {
                "id": row["id"],
                "title": row["title"],
                "done": bool(row["done"]),
            }


def insert_task(title: str, db_url: Optional[str] = None) -> Dict[str, Any]:
    """Insert a new task into PostgreSQL and return created record."""
    with get_db_connection(db_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done;",
                (title, False),
            )
            conn.commit()
            row = cursor.fetchone()
            return {
                "id": row["id"],
                "title": row["title"],
                "done": bool(row["done"]),
            }


def update_task_record(
    task_id: int,
    title: Optional[str],
    done: Optional[bool],
    db_url: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update an existing task in PostgreSQL."""
    with get_db_connection(db_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, title, done FROM tasks WHERE id = %s;",
                (task_id,),
            )
            existing = cursor.fetchone()
            if existing is None:
                return None

            new_title = title if title is not None else existing["title"]
            new_done = done if done is not None else existing["done"]

            cursor.execute(
                "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING id, title, done;",
                (new_title, new_done, task_id),
            )
            conn.commit()
            row = cursor.fetchone()
            return {
                "id": row["id"],
                "title": row["title"],
                "done": bool(row["done"]),
            }


def delete_task_record(task_id: int, db_url: Optional[str] = None) -> bool:
    """Delete a task by ID from PostgreSQL. Returns True if deleted, False if not found."""
    with get_db_connection(db_url) as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
            conn.commit()
            return cursor.rowcount > 0
