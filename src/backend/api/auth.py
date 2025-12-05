"""
Authentication API endpoints.

REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3, REQ-B-A1-4, REQ-B-A1-5, REQ-B-A1-6, REQ-B-A1-7, REQ-B-A1-8, REQ-B-A1-9
"""

import logging
import os

import jwt as pyjwt
from fastapi import APIRouter, Cookie, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import DataError
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
    Open ID backend endpoint for OAuth token exchange and redirection.

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


class LoginRequest(BaseModel):
    """
    Request model for SSO login.

    Attributes:
        knox_id: User's Knox ID
        name: User's full name
        dept: Department
        business_unit: Business unit
        email: Email address (must be valid email format)

    """

    knox_id: str = Field(..., description="User's Knox ID")
    name: str = Field(..., description="User's full name")
    dept: str = Field(..., description="Department")
    business_unit: str = Field(..., description="Business unit")
    email: EmailStr = Field(..., description="Email address (validated format)")


class LoginResponse(BaseModel):
    """
    Response model for authentication.

    Attributes:
        access_token: Signed JWT token
        token_type: Token type (bearer)
        user_id: User's database primary key (integer)
        is_new_user: True if new user account was created

    """

    access_token: str = Field(..., description="JWT token")
    token_type: str = Field(default="bearer", description="Token type")
    user_id: int = Field(..., description="User's database ID (integer primary key)")
    is_new_user: bool = Field(..., description="True if new user created")


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


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Direct Login Endpoint",
    description="CLI and development login endpoint that accepts user info and returns JWT token",
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> JSONResponse:
    """
    Direct login endpoint for CLI and development use.

    REQ: REQ-B-A2-Auth-3

    Accepts user data (knox_id, name, email, dept, business_unit),
    creates new user if doesn't exist, updates if exists,
    and returns JWT token with user info.

    Args:
        request: LoginRequest containing user information
        db: Database session

    Returns:
        JSONResponse with:
        - 201 Created (new user): {access_token, token_type, user_id, is_new_user: true}
        - 200 OK (existing user): {access_token, token_type, user_id, is_new_user: false}

    Raises:
        HTTPException: 422 if validation fails, 500 if internal error

    """
    try:
        # Prepare user data dict from request
        user_data = {
            "knox_id": request.knox_id,
            "name": request.name,
            "email": request.email,
            "dept": request.dept,
            "business_unit": request.business_unit,
        }

        # Call service to create/update user and generate token
        auth_service = AuthService(db)
        jwt_token, is_new_user, user_id = auth_service.authenticate_or_create_user(user_data)

        # Determine status code: 201 for new user, 200 for existing
        status_code = 201 if is_new_user else 200

        # Return response with appropriate status code
        return JSONResponse(
            status_code=status_code,
            content={
                "access_token": jwt_token,
                "token_type": "bearer",
                "user_id": user_id,
                "is_new_user": is_new_user,
            },
        )

    except ValueError as e:
        # Validation errors (missing required fields)
        logger.warning(f"Login validation error: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=str(e),
        ) from e
    except DataError as e:
        # Database validation errors (e.g., field too long)
        logger.warning(f"Login data validation error: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail="Input data validation failed: field value exceeds maximum length",
        ) from e
    except Exception as e:
        # Unexpected errors
        logger.exception("Login error")
        raise HTTPException(
            status_code=500,
            detail="Login failed",
        ) from e


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
        return JSONResponse(
            status_code=401,
            content={"authenticated": False},
        )

    try:
        auth_service = AuthService(db)
        payload = auth_service.decode_jwt(auth_token)
        knox_id = payload.get("knox_id")

        # Get user from database to retrieve user_id
        if not knox_id:
            return JSONResponse(
                status_code=401,
                content={"authenticated": False},
            )

        from src.backend.models.user import User

        user = db.query(User).filter_by(knox_id=knox_id).first()
        if not user:
            return JSONResponse(
                status_code=401,
                content={"authenticated": False},
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
        return JSONResponse(
            status_code=401,
            content={"authenticated": False},
        )
    except Exception as e:
        logger.exception("Authentication status check error")
        raise HTTPException(
            status_code=500,
            detail="Authentication status check failed",
        ) from e
