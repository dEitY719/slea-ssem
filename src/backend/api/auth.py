"""
Authentication API endpoints.

REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3, REQ-B-A1-4, REQ-B-A1-5, REQ-B-A1-6, REQ-B-A1-7, REQ-B-A1-8, REQ-B-A1-9
"""

import logging

import jwt as pyjwt
from fastapi import APIRouter, Cookie, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    """
    Request model for SSO login.

    Attributes:
        knox_id: User's Knox ID
        name: User's full name
        dept: Department
        business_unit: Business unit
        email: Email address

    """

    knox_id: str = Field(..., description="User's Knox ID")
    name: str = Field(..., description="User's full name")
    dept: str = Field(..., description="Department")
    business_unit: str = Field(..., description="Business unit")
    email: str = Field(..., description="Email address")


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


class OIDCCallbackRequest(BaseModel):
    """
    Request model for OIDC callback endpoint.

    REQ: REQ-B-A1-1
    TODO: Define form-urlencoded parameters (code, state)
    """

    pass


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
    summary="SSO Login",
    description="Authenticate user via SSO and return JWT token",
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> JSONResponse:
    """
    Handle SSO authentication.

    REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3, REQ-B-A1-4

    Args:
        request: Login request with user data from SSO
        db: Database session

    Returns:
        JSONResponse with JWT token and is_new_user flag
        Status code 201 for new users, 200 for existing users

    Raises:
        HTTPException: If authentication fails

    """
    try:
        auth_service = AuthService(db)
        user_data = request.model_dump()
        jwt_token, is_new_user, user_id = auth_service.authenticate_or_create_user(user_data)

        # Return appropriate status code based on is_new_user
        status_code = 201 if is_new_user else 200

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
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Authentication error")
        raise HTTPException(status_code=500, detail="Authentication failed") from e


@router.post(
    "/oidc/callback",
    summary="OIDC Callback",
    description="Handle OIDC callback from IDP (form POST)",
)
def oidc_callback(
    db: Session = Depends(get_db),  # noqa: B008
):
    """
    Handle OIDC callback from IDP.

    REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3, REQ-B-A1-4, REQ-B-A1-5, REQ-B-A1-6, REQ-B-A1-7

    TODO: Implement IDP callback handling
    1. Receive form-urlencoded (code, state) from IDP
    2. Validate state
    3. Exchange code for IDP tokens (with client_secret)
    4. Validate ID Token
    5. Extract user claims and save to DB
    6. Generate JWT and set HttpOnly cookie
    7. Return 302 redirect to /home

    Args:
        db: Database session

    Returns:
        RedirectResponse with HttpOnly cookie

    Raises:
        HTTPException: If OIDC callback fails

    """
    # TODO: Implement OIDC callback logic
    raise HTTPException(status_code=501, detail="OIDC callback not implemented")


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
