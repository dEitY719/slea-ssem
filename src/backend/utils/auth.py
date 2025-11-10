"""Authentication utilities for JWT token extraction."""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.models.user import User
from src.backend.services.auth_service import AuthService

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and validate JWT token, return current User object.

    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session

    Returns:
        User object of authenticated user

    Raises:
        HTTPException: 401 if token is invalid or user not found

    """
    try:
        token = credentials.credentials
        auth_service = AuthService(db)
        payload = auth_service.decode_jwt(token)
        knox_id = payload.get("knox_id")
        if not knox_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Find user by knox_id
        user = db.query(User).filter_by(knox_id=knox_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user_id(
    user: User = Depends(get_current_user),
) -> int:
    """
    Get current user's database ID.

    Args:
        user: Current user from JWT token

    Returns:
        User's database ID (integer)

    """
    return user.id
