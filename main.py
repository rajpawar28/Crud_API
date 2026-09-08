"""Task API - Main Application Module.

A clean, beginner-friendly REST CRUD API built with FastAPI and in-memory storage.
"""

from typing import Any, Dict, List
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
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


class TaskCreate(BaseModel):
    title: str = Field(..., description="The title of the task (cannot be empty or whitespace)")

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
        }
    }


class TaskResponse(BaseModel):
    id: int = Field(..., example=1, description="Unique identifier for the task")
    title: str = Field(..., example="Learn FastAPI", description="Title of the task")
    done: bool = Field(..., example=False, description="Completion status of the task")


class ErrorResponse(BaseModel):
    error: str = Field(..., example="Task 99 not found", description="Descriptive error message")


# --------------------------------------------------
# Exception Handlers
# --------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Convert FastAPI validation errors from 422 to 400 Bad Request with custom JSON message."""
    errors = exc.errors()
    for err in errors:
        loc = err.get("loc", ())
        msg = err.get("msg", "")
        # Custom check for title validation errors
        if "title" in loc or "title" in msg.lower():
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


@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"model": TaskResponse, "description": "Task created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request body"},
    },
    summary="Create New Task",
    description="Creates a new task with the given title. Automatically assigns the next available ID and sets done to false.",
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
