"""Task API - Main Application Module.

A clean, beginner-friendly REST CRUD API built with FastAPI and in-memory storage.
"""

from typing import List
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="Task API",
    description="A clean REST CRUD API for managing tasks.",
    version="1.0",
)


class RootResponse(BaseModel):
    name: str = Field(..., example="Task API")
    version: str = Field(..., example="1.0")
    endpoints: List[str] = Field(..., example=["/tasks"])


class HealthResponse(BaseModel):
    status: str = Field(..., example="ok")


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
