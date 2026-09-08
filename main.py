"""Task API - Main Application Module.

A clean, beginner-friendly REST CRUD API built with FastAPI and SQLite storage.
Follows the FlyRank Week 3 Assignment A2 specification.
"""

from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, model_validator
from starlette.exceptions import HTTPException as StarletteHTTPException

import database


# --------------------------------------------------
# Lifespan Management (Auto Database Initialization)
# --------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure SQLite database and seed data are initialized on startup."""
    database.init_db()
    yield


# --------------------------------------------------
# OpenAPI Documentation & App Setup
# --------------------------------------------------
TAGS_METADATA = [
    {
        "name": "General",
        "description": "General API metadata and health check endpoints.",
    },
    {
        "name": "Tasks",
        "description": "CRUD operations for managing tasks stored in SQLite.",
    },
]

app = FastAPI(
    title="Task API",
    description=(
        "A clean, beginner-friendly REST CRUD API for managing tasks. "
        "All data is persisted in a local SQLite database (tasks.db)."
    ),
    version="2.0",
    openapi_tags=TAGS_METADATA,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# --------------------------------------------------
# Request & Response Schemas
# --------------------------------------------------
class RootResponse(BaseModel):
    """Schema for root endpoint response."""

    name: str = Field(
        ...,
        examples=["Task API"],
        description="Name of the API",
    )
    version: str = Field(
        ...,
        examples=["2.0"],
        description="API version",
    )
    endpoints: List[str] = Field(
        ...,
        examples=[["/tasks"]],
        description="List of primary resource endpoints",
    )


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str = Field(
        ...,
        examples=["ok"],
        description="Current health status of the API",
    )


class TaskCreate(BaseModel):
    """Schema for creating a new task."""

    title: str = Field(
        ...,
        description="The title of the task (cannot be empty, whitespace-only, or null)",
    )

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: Any) -> str:
        if v is None or not isinstance(v, str) or not v.strip():
            raise ValueError("Title is required and cannot be empty")
        return v.strip()

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "title": "Buy milk"
            }
        },
    }


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""

    title: Optional[str] = Field(
        default=None,
        description="Updated title of the task (cannot be empty or whitespace-only)",
    )
    done: Optional[bool] = Field(
        default=None,
        description="Updated completion status of the task",
    )

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v: Any) -> Optional[str]:
        if v is not None:
            if not isinstance(v, str) or not v.strip():
                raise ValueError("Title cannot be empty")
            return v.strip()
        return v

    @model_validator(mode="after")
    def validate_non_empty(self) -> "TaskUpdate":
        if self.title is None and self.done is None:
            raise ValueError(
                "Invalid request body: at least one field ('title' or 'done') must be provided"
            )
        return self

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "title": "Buy groceries",
                "done": True,
            }
        },
    }


class TaskResponse(BaseModel):
    """Schema for task response."""

    id: int = Field(
        ...,
        examples=[1],
        description="Unique integer identifier for the task",
    )
    title: str = Field(
        ...,
        examples=["Learn FastAPI"],
        description="Title of the task",
    )
    done: bool = Field(
        ...,
        examples=[False],
        description="Completion status of the task",
    )


class ErrorResponse(BaseModel):
    """Schema for JSON error responses."""

    error: str = Field(
        ...,
        examples=["Task 99 not found"],
        description="Descriptive explanation of the error",
    )


# --------------------------------------------------
# Custom Exception Handlers
# --------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Convert validation errors to HTTP 400 Bad Request with assignment-compliant JSON error message."""
    errors = exc.errors()
    for err in errors:
        loc = err.get("loc", ())
        msg = err.get("msg", "")

        # Value error raised directly by Pydantic validator
        ctx = err.get("ctx", {})
        if "error" in ctx and isinstance(ctx["error"], Exception):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": str(ctx["error"])},
            )

        if "title" in loc or "title" in msg.lower():
            if request.method == "PUT":
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Title cannot be empty"},
                )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Title is required and cannot be empty"},
            )
        if "id" in loc:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid task ID"},
            )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Invalid request body"},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Ensure all HTTP exceptions return structured JSON errors."""
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})


# --------------------------------------------------
# Endpoints
# --------------------------------------------------
@app.get(
    "/",
    response_model=RootResponse,
    status_code=status.HTTP_200_OK,
    summary="Get API Metadata",
    description="Returns general metadata about the Task API, version, and available endpoints.",
    tags=["General"],
)
def get_root():
    """Return API metadata."""
    return {
        "name": "Task API",
        "version": "2.0",
        "endpoints": ["/tasks"],
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Returns the operational health status of the API.",
    tags=["General"],
)
def get_health():
    """Return API health status."""
    return {"status": "ok"}


@app.get(
    "/tasks",
    response_model=List[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="List All Tasks",
    description="Returns the complete list of tasks currently stored in SQLite.",
    tags=["Tasks"],
)
def get_tasks():
    """Return all tasks from SQLite."""
    conn = database.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, done FROM tasks;")
        rows = cursor.fetchall()
        return [
            {"id": row["id"], "title": row["title"], "done": bool(row["done"])}
            for row in rows
        ]
    finally:
        conn.close()


@app.get(
    "/tasks/{id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"model": TaskResponse, "description": "Task found and returned"},
        404: {"model": ErrorResponse, "description": "Task not found with the requested ID"},
    },
    summary="Get Task by ID",
    description="Returns a single task by its integer ID from SQLite. Returns 404 if not found.",
    tags=["Tasks"],
)
def get_task(id: int):
    """Return a single task by ID from SQLite."""
    conn = database.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?;", (id,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {id} not found",
            )
        return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}
    finally:
        conn.close()


@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"model": TaskResponse, "description": "Task created successfully in SQLite"},
        400: {"model": ErrorResponse, "description": "Validation error or invalid request body"},
    },
    summary="Create New Task",
    description=(
        "Creates a new task with the given title in SQLite. "
        "The database automatically assigns the ID and sets done to false."
    ),
    tags=["Tasks"],
)
def create_task(task_in: TaskCreate):
    """Insert a new task into SQLite and return it."""
    conn = database.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?);",
            (task_in.title, 0),
        )
        conn.commit()
        new_id = cursor.lastrowid
        return {
            "id": new_id,
            "title": task_in.title,
            "done": False,
        }
    finally:
        conn.close()


@app.put(
    "/tasks/{id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"model": TaskResponse, "description": "Task updated successfully in SQLite"},
        400: {"model": ErrorResponse, "description": "Validation error or invalid request body"},
        404: {"model": ErrorResponse, "description": "Task not found with the requested ID"},
    },
    summary="Update Task by ID",
    description=(
        "Updates an existing task's title and/or done status in SQLite using parameterized SQL. "
        "Returns 404 if the task is not found or 400 if the payload is invalid."
    ),
    tags=["Tasks"],
)
def update_task(id: int, task_in: TaskUpdate):
    """Update an existing task in SQLite."""
    conn = database.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?;", (id,))
        existing = cursor.fetchone()
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {id} not found",
            )

        new_title = task_in.title if task_in.title is not None else existing["title"]
        new_done = int(task_in.done) if task_in.done is not None else existing["done"]

        cursor.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?;",
            (new_title, new_done, id),
        )
        conn.commit()
        return {
            "id": id,
            "title": new_title,
            "done": bool(new_done),
        }
    finally:
        conn.close()


@app.delete(
    "/tasks/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Task deleted successfully with empty response body"},
        404: {"model": ErrorResponse, "description": "Task not found with the requested ID"},
    },
    summary="Delete Task by ID",
    description="Deletes a task from SQLite by its integer ID. Returns 204 No Content on success or 404 if not found.",
    tags=["Tasks"],
)
def delete_task(id: int):
    """Delete a task from SQLite by ID."""
    conn = database.get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?;", (id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {id} not found",
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    finally:
        conn.close()
