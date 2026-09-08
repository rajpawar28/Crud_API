"""Authentication module for Task API (A4 Auth).

Provides a reusable FastAPI dependency for Bearer token authentication
using Supabase as the identity provider.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from supabase_client import supabase

# HTTPBearer scheme — generates the "Authorize" padlock button in Swagger UI
# auto_error=False so we can return our own 401 JSON instead of FastAPI's default
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    """Reusable FastAPI dependency that extracts and verifies a Bearer JWT.

    Flow:
    1. Extract Authorization: Bearer <token> header
    2. Verify token with Supabase (network call, not local decode)
    3. Return authenticated user or raise 401

    Exact error messages per assignment spec:
    - Missing/malformed header → {"error": "Access token required"}
    - Invalid/expired token   → {"error": "Invalid or expired token"}
    """
    # 1. Check that credentials were provided
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Access token required"},
        )

    token = credentials.credentials

    # 2. Verify token with Supabase (makes a network call)
    if supabase is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired token"},
        )

    try:
        user_response = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired token"},
        )

    if user_response is None or user_response.user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid or expired token"},
        )

    return user_response.user
