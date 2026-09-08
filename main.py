"""Task API - Main Application Module.

A clean, beginner-friendly REST CRUD API built with FastAPI and in-memory storage.
"""

from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI(
    title="Task API",
    description="A clean REST CRUD API for managing tasks.",
    version="1.0",
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


def reset_tasks():
    """Helper to reset in-memory tasks to initial 3 tasks."""
    global tasks_db
    tasks_db = [task.copy() for task in INITIAL_TASKS]


# --------------------------------------------------
# Schemas
# --------------------------------------------------
class RootResponse(BaseModel):
    name: str = Field(..., example="Task API")
    version: str = Field(..., example="1.0")
    endpoints: List[str] = Field(..., example=["/tasks"])


class HealthResponse(BaseModel):
    status: str = Field(..., example="ok")


class TaskResponse(BaseModel):
    id: int = Field(..., example=1, description="Unique identifier for the task")
    title: str = Field(..., example="Learn FastAPI", description="Title of the task")
    done: bool = Field(..., example=False, description="Completion status of the task")


class ErrorResponse(BaseModel):
    error: str = Field(..., example="Task 99 not found", description="Descriptive error message")


# --------------------------------------------------
# Exception Handlers
# --------------------------------------------------
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
    summary="API Information",
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
    responses={
        200: {"model": TaskResponse, "description": "Task details"},
        404: {"model": ErrorResponse, "description": "Task not found"},
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
