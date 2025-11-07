"""
Profile API endpoints.

REQ: REQ-B-A2-1, REQ-B-A2-2, REQ-B-A2-3, REQ-B-A2-5
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.services.profile_service import ProfileService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])


class NicknameCheckRequest(BaseModel):
    """
    Request model for nickname availability check.

    Attributes:
        nickname: Nickname to check

    """

    nickname: str = Field(..., description="Nickname to check", min_length=1)


class NicknameCheckResponse(BaseModel):
    """
    Response model for nickname availability check.

    Attributes:
        available: True if nickname is available
        suggestions: List of alternatives if taken

    """

    available: bool = Field(..., description="Whether nickname is available")
    suggestions: list[str] = Field(..., description="Alternative suggestions if taken")


class NicknameRegisterRequest(BaseModel):
    """
    Request model for nickname registration.

    Attributes:
        nickname: Nickname to register

    """

    nickname: str = Field(..., description="Nickname to register")


class NicknameRegisterResponse(BaseModel):
    """
    Response model for nickname registration.

    Attributes:
        user_id: User ID
        nickname: Registered nickname
        updated_at: Update timestamp

    """

    user_id: int = Field(..., description="User ID")
    nickname: str = Field(..., description="Registered nickname")
    updated_at: str = Field(..., description="Update timestamp")


@router.post(
    "/nickname/check",
    response_model=NicknameCheckResponse,
    status_code=200,
    summary="Check Nickname Availability",
    description="Check if nickname is available and get suggestions if taken",
)
def check_nickname_availability(
    request: NicknameCheckRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, object]:
    """
    Check if nickname is available.

    REQ: REQ-B-A2-1, REQ-B-A2-3

    Args:
        request: Nickname check request
        db: Database session

    Returns:
        Response with availability and suggestions

    Raises:
        HTTPException: If validation fails

    """
    try:
        profile_service = ProfileService(db)
        result = profile_service.check_nickname_availability(request.nickname)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error checking nickname availability")
        raise HTTPException(status_code=500, detail="Failed to check nickname") from e


@router.post(
    "/register",
    response_model=NicknameRegisterResponse,
    status_code=201,
    summary="Register Nickname",
    description="Register nickname for authenticated user",
)
def register_nickname(
    request: NicknameRegisterRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, object]:
    """
    Register nickname for user.

    REQ: REQ-B-A2-5

    Args:
        request: Nickname registration request
        db: Database session

    Returns:
        Response with registered nickname and timestamp

    Raises:
        HTTPException: If validation or registration fails

    """
    # TODO: Extract user_id from JWT token in production
    # For now, using a placeholder. In production, extract from auth token.
    # user_id = get_current_user_id(token)
    user_id = 1  # Placeholder - should come from JWT

    try:
        profile_service = ProfileService(db)
        result = profile_service.register_nickname(user_id, request.nickname)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error registering nickname")
        raise HTTPException(status_code=500, detail="Failed to register nickname") from e
