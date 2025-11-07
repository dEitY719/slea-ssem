"""
Authentication API endpoints.

REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3, REQ-B-A1-4
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """
    Request model for Samsung AD login.

    Attributes:
        knox_id: User's Samsung Knox ID
        name: User's full name
        dept: Department
        business_unit: Business unit
        email: Email address

    """

    knox_id: str = Field(..., description="User's Samsung Knox ID")
    name: str = Field(..., description="User's full name")
    dept: str = Field(..., description="Department")
    business_unit: str = Field(..., description="Business unit")
    email: str = Field(..., description="Email address")


class LoginResponse(BaseModel):
    """
    Response model for authentication.

    Attributes:
        jwt_token: Signed JWT token
        is_new_user: True if new user account was created

    """

    jwt_token: str = Field(..., description="JWT token")
    is_new_user: bool = Field(..., description="True if new user created")


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Samsung AD Login",
    description="Authenticate user via Samsung AD and return JWT token",
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> JSONResponse:
    """
    Handle Samsung AD authentication.

    REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3, REQ-B-A1-4

    Args:
        request: Login request with user data from Samsung AD
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
        jwt_token, is_new_user = auth_service.authenticate_or_create_user(user_data)

        # Return appropriate status code based on is_new_user
        status_code = 201 if is_new_user else 200

        return JSONResponse(
            status_code=status_code,
            content={
                "jwt_token": jwt_token,
                "is_new_user": is_new_user,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Authentication error")
        raise HTTPException(status_code=500, detail="Authentication failed") from e
