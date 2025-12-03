"""
Authentication API endpoints.

REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3, REQ-B-A1-4, REQ-B-A1-5, REQ-B-A1-6, REQ-B-A1-7, REQ-B-A1-8, REQ-B-A1-9
"""

import logging
import os

import jwt as pyjwt
from fastapi import APIRouter, Cookie, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


@router.post(
    "/",
    summary="Open ID backend endpoint",
    description="The Open ID backend endpoint is responsible for receiving an Open ID token, issuing a system token in exchange, and then redirecting the user (or the browser) to a pre-set redirection URL along with the newly issued system token.",
)
def auth_redirect() -> RedirectResponse:
    """
    The Open ID backend endpoint is responsible for receiving an Open ID token, issuing a system token in exchange, and then redirecting the user (or the browser) to a pre-set redirection URL along with the newly issued system token.

    Web app -> (Redirect) Identity Provider -> (POST) Backend -> (Redirect) -> Web app

    Returns:
        RedirectResponse with 302 status code

    Raises:
        HTTPException: If AUTH_REDIRECTION_URL is not set

    """
    redirect_url = os.getenv("AUTH_REDIRECTION_URL")
    if not redirect_url:
        raise HTTPException(
            status_code=500,
            detail="AUTH_REDIRECTION_URL environment variable is not set",
        )
    return RedirectResponse(url=redirect_url, status_code=302)


class StatusResponse(BaseModel):
    """
    Response model for authentication status endpoint.



    REQ: REQ-B-A1-9

    Attributes:
        authenticated: True if user is authenticated
        user_id: User's database ID (only when authenticated)
        knox_id: User's Knox ID (only when authenticated)

    """

    authenticated: bool = Field(..., description="Authentication status")
    user_id: int | None = Field(default=None, description="User's database ID")
    knox_id: str | None = Field(default=None, description="User's Knox ID")


@router.get(
    "/status",
    response_model=StatusResponse,
    summary="Authentication Status Check",
    description="Check if user is authenticated and retrieve user information from JWT cookie",
)
def check_auth_status(
    auth_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),  # noqa: B008
) -> JSONResponse:
    """
    Check authentication status by validating JWT from cookie.

    REQ: REQ-B-A1-9

    Args:
        auth_token: JWT token from HttpOnly cookie
        db: Database session

    Returns:
        JSONResponse with authentication status
        - 200 with {authenticated: true, user_id, knox_id} if authenticated
        - 401 with {authenticated: false} if not authenticated or invalid token

    """
    if not auth_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    try:
        auth_service = AuthService(db)
        payload = auth_service.decode_jwt(auth_token)
        knox_id = payload.get("knox_id")

        # Get user from database to retrieve user_id
        if not knox_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing knox_id",
            )

        from src.backend.models.user import User

        user = db.query(User).filter_by(knox_id=knox_id).first()
        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found",
            )

        return JSONResponse(
            status_code=200,
            content={
                "authenticated": True,
                "user_id": user.id,
                "knox_id": knox_id,
            },
        )

    except pyjwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Authentication status check error")
        raise HTTPException(
            status_code=500,
            detail="Authentication status check failed",
        ) from e
