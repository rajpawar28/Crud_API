"""Database module for Task API.

Handles SQLite connection management, schema initialization, and initial seed data.
Follows the FlyRank Week 3 Assignment A2 specification.
"""

import os
import sqlite3
from typing import List, Optional, Tuple

# Default database filename
DB_NAME = "tasks.db"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)

# Initial seed data for empty database (exactly 3 tasks)
INITIAL_TASKS: List[Tuple[str, int]] = [
    ("Learn FastAPI", 0),
    ("Build CRUD API", 0),
    ("Test API with Swagger", 1),
]


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create and return a configured SQLite connection.

    Uses sqlite3.Row as the row_factory to enable dictionary-like column access.
    """
    target_path = db_path or DB_PATH
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize the SQLite database schema and seed initial tasks if table is empty.

    - Creates tasks.db and the tasks table if not exists.
    - Only seeds the 3 initial tasks when the table is completely empty (COUNT == 0).
    - Prevents seed data duplication upon subsequent server restarts.
    """
    target_path = db_path or DB_PATH
    conn = get_db_connection(target_path)
    cursor = conn.cursor()

    # Create tasks table with primary key id, title, and boolean done (stored as 0/1)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        );
        """
    )
    conn.commit()

    # Check whether the table currently has any records
    cursor.execute("SELECT COUNT(*) FROM tasks;")
    count = cursor.fetchone()[0]

    # Only insert seed records when the table is empty
    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?);",
            INITIAL_TASKS,
        )
        conn.commit()

    conn.close()
