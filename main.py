"""Task API - Main Application Module.

A clean, beginner-friendly REST CRUD API built with FastAPI and in-memory storage.
"""

from fastapi import FastAPI

app = FastAPI(
    title="Task API",
    description="A clean REST CRUD API for managing tasks.",
    version="1.0",
)
