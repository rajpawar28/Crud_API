"""Task API - Main Application Module.

A clean, beginner-friendly REST CRUD API built with FastAPI and in-memory storage.
Follows the FlyRank Week 2 Assignment A1 specification.
"""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, model_validator
from starlette.exceptions import HTTPException as StarletteHTTPException

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
        "description": "CRUD operations for managing tasks stored in memory.",
    },
]

app = FastAPI(
    title="Task API",
    description=(
        "A clean, beginner-friendly REST CRUD API for managing tasks. "
        "All data is stored in memory and resets upon server restart."
    ),
    version="1.0",
    openapi_tags=TAGS_METADATA,
    docs_url="/docs",
    redoc_url="/redoc",
)

# --------------------------------------------------
# Initial Data & In-Memory Storage
# --------------------------------------------------
INITIAL_TASKS: List[Dict[str, Any]] = [
    {"id": 1, "title": "Learn FastAPI", "done": False},
    {"id": 2, "title": "Build CRUD API", "done": False},
    {"id": 3, "title": "Test API with Swagger", "done": True},
]

# Mutable in-memory store
tasks_db: List[Dict[str, Any]] = [task.copy() for task in INITIAL_TASKS]


def reset_tasks() -> None:
    """Reset in-memory tasks to the initial 3 example tasks."""
    global tasks_db
    tasks_db = [task.copy() for task in INITIAL_TASKS]


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
        examples=["1.0"],
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
        "version": "1.0",
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
    description="Returns the complete list of tasks currently stored in memory.",
    tags=["Tasks"],
)
def get_tasks():
    """Return all in-memory tasks."""
    return tasks_db


@app.get(
    "/tasks/{id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"model": TaskResponse, "description": "Task found and returned"},
        404: {"model": ErrorResponse, "description": "Task not found with the requested ID"},
    },
    summary="Get Task by ID",
    description="Returns a single task by its integer ID. Returns 404 if not found.",
    tags=["Tasks"],
)
def get_task(id: int):
    """Return a single task by ID."""
    for task in tasks_db:
        if task["id"] == id:
            return task
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {id} not found",
    )


@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"model": TaskResponse, "description": "Task created successfully"},
        400: {"model": ErrorResponse, "description": "Validation error or invalid request body"},
    },
    summary="Create New Task",
    description=(
        "Creates a new task with the given title. Automatically assigns the next available ID "
        "and sets done to false. Rejects empty, whitespace-only, or missing titles."
    ),
    tags=["Tasks"],
)
def create_task(task_in: TaskCreate):
    """Create a new task in memory."""
    next_id = max([t["id"] for t in tasks_db], default=0) + 1
    new_task = {
        "id": next_id,
        "title": task_in.title,
        "done": False,
    }
    tasks_db.append(new_task)
    return new_task


@app.put(
    "/tasks/{id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"model": TaskResponse, "description": "Task updated successfully"},
        400: {"model": ErrorResponse, "description": "Validation error or invalid request body"},
        404: {"model": ErrorResponse, "description": "Task not found with the requested ID"},
    },
    summary="Update Task by ID",
    description=(
        "Updates an existing task's title and/or done status. "
        "Returns 404 if the task is not found or 400 if the payload is invalid."
    ),
    tags=["Tasks"],
)
def update_task(id: int, task_in: TaskUpdate):
    """Update an existing task in memory."""
    for task in tasks_db:
        if task["id"] == id:
            if task_in.title is not None:
                task["title"] = task_in.title
            if task_in.done is not None:
                task["done"] = task_in.done
            return task
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {id} not found",
    )


@app.delete(
    "/tasks/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Task deleted successfully with empty response body"},
        404: {"model": ErrorResponse, "description": "Task not found with the requested ID"},
    },
    summary="Delete Task by ID",
    description="Deletes a task by its integer ID. Returns 204 No Content on success or 404 if not found.",
    tags=["Tasks"],
)
def delete_task(id: int):
    """Delete a task by ID."""
    for idx, task in enumerate(tasks_db):
        if task["id"] == id:
            tasks_db.pop(idx)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task {id} not found",
    )
