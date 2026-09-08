"""Supabase client module for Task API (A4 Auth).

Initializes a reusable Supabase client from environment variables.
Uses the anon/public key only — NEVER service_role.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file if present
load_dotenv()

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")


def get_supabase_client() -> Client:
    """Create and return a configured Supabase client.

    Raises RuntimeError if required environment variables are missing.
    """
    if not SUPABASE_URL or SUPABASE_URL == "your_project_url":
        raise RuntimeError(
            "SUPABASE_URL environment variable is not set. "
            "Please configure it in your .env file."
        )
    if not SUPABASE_KEY or SUPABASE_KEY == "your_anon_key":
        raise RuntimeError(
            "SUPABASE_KEY environment variable is not set. "
            "Please configure it in your .env file."
        )
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# Create a single reusable client instance
# This will be None if env vars are not configured (allows tests to run)
supabase: Client | None = None
try:
    supabase = get_supabase_client()
except RuntimeError:
    supabase = None
