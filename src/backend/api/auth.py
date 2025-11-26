"""
Authentication API endpoints.

REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3, REQ-B-A1-4, REQ-B-A1-5, REQ-B-A1-6, REQ-B-A1-7, REQ-B-A1-8
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.services.auth_service import AuthService, OIDCAuthService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


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

    Attributes:
        code: Authorization code from Azure AD
        code_verifier: PKCE code verifier from frontend

    """

    code: str = Field(..., description="Authorization code from Azure AD")
    code_verifier: str = Field(..., description="PKCE code verifier")


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
    response_model=LoginResponse,
    summary="OIDC Callback",
    description="Handle OIDC callback from Azure AD with authorization code and code_verifier",
)
def oidc_callback(
    request: OIDCCallbackRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> JSONResponse:
    """
    Handle OIDC callback from Azure AD.

    REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3, REQ-B-A1-4, REQ-B-A1-5, REQ-B-A1-6, REQ-B-A1-7

    Flow:
    1. Receive authorization code and code_verifier from frontend
    2. Exchange authorization code for Azure AD tokens (ID Token + Access Token)
    3. Validate ID Token (signature, issuer, audience, expiration)
    4. Extract user claims from ID Token
    5. Create or update user in database
    6. Generate JWT token
    7. Set JWT in HttpOnly cookie
    8. Return user_id and is_new_user flag

    Args:
        request: OIDC callback request with code and code_verifier
        db: Database session

    Returns:
        JSONResponse with JWT token and is_new_user flag
        Status code 201 for new users, 200 for existing users
        Set-Cookie header with HttpOnly JWT cookie

    Raises:
        HTTPException: If OIDC callback fails

    """
    try:
        # REQ-B-A1-1: Receive authorization code and code_verifier
        code = request.code
        code_verifier = request.code_verifier

        # REQ-B-A1-2: Exchange code for Azure AD tokens
        oidc_service = OIDCAuthService()
        tokens = oidc_service.exchange_code_for_tokens(code, code_verifier)

        # REQ-B-A1-3: Validate ID Token
        id_token = tokens.get("id_token")
        if not id_token:
            raise ValueError("ID token not received from Azure AD")

        id_token_claims = oidc_service.validate_id_token(id_token)

        # Extract user claims from ID Token
        user_data = {
            "knox_id": id_token_claims.get("sub", ""),  # Use 'sub' (subject/OID) as knox_id
            "email": id_token_claims.get("email", ""),
            "name": id_token_claims.get("name", ""),
            "dept": id_token_claims.get("dept", ""),
            "business_unit": id_token_claims.get("business_unit", ""),
        }

        # REQ-B-A1-4: Create or update user
        auth_service = AuthService(db)
        jwt_token, is_new_user, user_id = auth_service.authenticate_or_create_user(user_data)

        # REQ-B-A1-5, REQ-B-A1-6: Generate JWT and set in HttpOnly cookie
        status_code = 201 if is_new_user else 200

        response = JSONResponse(
            status_code=status_code,
            content={
                "access_token": jwt_token,
                "token_type": "bearer",
                "user_id": user_id,
                "is_new_user": is_new_user,
            },
        )

        # Set JWT in HttpOnly cookie (REQ-B-A1-6)
        response.set_cookie(
            key="auth_token",
            value=jwt_token,
            httponly=True,
            secure=True,  # Should be True in production (HTTPS only)
            samesite="Lax",
            max_age=86400,  # 24 hours
            path="/",
        )

        return response

    except ValueError as e:
        logger.warning(f"OIDC callback error: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e)) from e
    except Exception as e:
        logger.exception("OIDC callback error")
        raise HTTPException(status_code=500, detail="OIDC callback failed") from e
