"""
Profile API endpoints.

REQ: REQ-B-A2-Avail-1, REQ-B-A2-Avail-2, REQ-B-A2-Avail-3, REQ-B-A2-Avail-4,
     REQ-B-A2-Reg-1, REQ-B-A2-Reg-2, REQ-B-A2-Reg-3,
     REQ-B-A2-View-1, REQ-B-A2-View-2,
     REQ-B-A2-Edit-1, REQ-B-A2-Edit-2, REQ-B-A2-Edit-3, REQ-B-A2-Edit-4,
     REQ-B-A2-Prof-1, REQ-B-A2-Prof-2, REQ-B-A2-Prof-3
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.models.user import User
from src.backend.services.profile_service import ProfileService
from src.backend.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["profile"])


# ============================================================================
# Request/Response Models
# ============================================================================


class NicknameCheckRequest(BaseModel):
    """Request model for nickname availability check."""

    nickname: str = Field(..., description="Nickname to check", min_length=1)


class NicknameCheckResponse(BaseModel):
    """Response model for nickname availability check."""

    available: bool = Field(..., description="Whether nickname is available")
    suggestions: list[str] = Field(..., description="Alternative suggestions if taken")


class NicknameRegisterRequest(BaseModel):
    """Request model for nickname registration."""

    nickname: str = Field(..., description="Nickname to register", min_length=3, max_length=20)


class NicknameRegisterResponse(BaseModel):
    """Response model for nickname registration."""

    success: bool = Field(..., description="Registration success")
    message: str = Field(..., description="Result message")
    user_id: str = Field(..., description="User's knox_id")
    nickname: str = Field(..., description="Registered nickname")
    registered_at: str = Field(..., description="Registration timestamp")


class NicknameViewResponse(BaseModel):
    """Response model for nickname view."""

    user_id: str = Field(..., description="User's knox_id")
    nickname: str | None = Field(..., description="Current nickname (null if not set)")
    registered_at: str | None = Field(..., description="Registration timestamp")
    updated_at: str | None = Field(..., description="Last update timestamp")


class NicknameEditRequest(BaseModel):
    """Request model for nickname edit."""

    nickname: str = Field(..., description="New nickname", min_length=3, max_length=20)


class NicknameEditResponse(BaseModel):
    """Response model for nickname edit."""

    success: bool = Field(..., description="Update success")
    message: str = Field(..., description="Result message")
    user_id: str = Field(..., description="User's knox_id")
    old_nickname: str | None = Field(..., description="Previous nickname")
    new_nickname: str = Field(..., description="New nickname")
    updated_at: str = Field(..., description="Update timestamp")


class SurveyUpdateRequest(BaseModel):
    """Request model for survey update."""

    level: str | None = Field(None, description="Self-assessed level")
    career: str | None = Field(None, description="Years of experience")
    job_role: str | None = Field(None, description="Job role/title")
    duty: str | None = Field(None, description="Main responsibilities")
    interests: list[str] | None = Field(None, description="Interest categories")


class SurveyUpdateResponse(BaseModel):
    """Response model for survey update."""

    success: bool = Field(..., description="Update success")
    message: str = Field(..., description="Result message")
    user_id: str = Field(..., description="User's knox_id")
    survey_id: str = Field(..., description="Survey record ID")
    updated_at: str = Field(..., description="Update timestamp")


# ============================================================================
# API Endpoints
# ============================================================================


@router.post(
    "/nickname/check",
    response_model=NicknameCheckResponse,
    status_code=200,
    summary="Check Nickname Availability",
    description="Check if nickname is available (public, no authentication required)",
)
def check_nickname_availability(
    request: NicknameCheckRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """
    Check if nickname is available.

    REQ: REQ-B-A2-Avail-1, REQ-B-A2-Avail-2, REQ-B-A2-Avail-3, REQ-B-A2-Avail-4

    Args:
        request: Nickname check request
        db: Database session

    Returns:
        Response with availability and suggestions

    Raises:
        HTTPException: 400 if validation fails

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
    description="Register nickname for authenticated user (requires JWT)",
)
def register_nickname(
    request: NicknameRegisterRequest,
    user: User = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """
    Register nickname for authenticated user.

    REQ: REQ-B-A2-Reg-1, REQ-B-A2-Reg-2, REQ-B-A2-Reg-3

    Args:
        request: Nickname registration request
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Response with registered nickname and timestamp

    Raises:
        HTTPException: 400 if validation fails, 401 if not authenticated

    """
    try:
        profile_service = ProfileService(db)
        result = profile_service.register_nickname(user.id, request.nickname)
        return {
            "success": True,
            "message": "닉네임 등록 완료",
            "user_id": user.knox_id,
            "nickname": result["nickname"],
            "registered_at": result["updated_at"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error registering nickname")
        raise HTTPException(status_code=500, detail="Failed to register nickname") from e


@router.get(
    "/nickname",
    response_model=NicknameViewResponse,
    status_code=200,
    summary="Get Nickname",
    description="Get current user's nickname information (requires JWT)",
)
def get_nickname(
    user: User = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    """
    Get current user's nickname information.

    REQ: REQ-B-A2-View-1, REQ-B-A2-View-2

    Args:
        user: Current authenticated user (from JWT)

    Returns:
        Response with user's nickname information

    Raises:
        HTTPException: 401 if not authenticated

    """
    return {
        "user_id": user.knox_id,
        "nickname": user.nickname,
        "registered_at": user.created_at.isoformat() if user.nickname else None,
        "updated_at": user.updated_at.isoformat() if user.nickname else None,
    }


@router.put(
    "/nickname",
    response_model=NicknameEditResponse,
    status_code=200,
    summary="Edit Nickname",
    description="Edit current user's nickname (requires JWT)",
)
def edit_nickname(
    request: NicknameEditRequest,
    user: User = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """
    Edit current user's nickname.

    REQ: REQ-B-A2-Edit-1, REQ-B-A2-Edit-2, REQ-B-A2-Edit-3, REQ-B-A2-Edit-4

    Args:
        request: Nickname edit request
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Response with updated nickname and timestamp

    Raises:
        HTTPException: 400 if validation fails, 401 if not authenticated

    """
    try:
        old_nickname = user.nickname
        profile_service = ProfileService(db)
        result = profile_service.edit_nickname(user.id, request.nickname)
        return {
            "success": True,
            "message": "닉네임 수정 완료",
            "user_id": user.knox_id,
            "old_nickname": old_nickname,
            "new_nickname": result["nickname"],
            "updated_at": result["updated_at"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error editing nickname")
        raise HTTPException(status_code=500, detail="Failed to edit nickname") from e


@router.put(
    "/survey",
    response_model=SurveyUpdateResponse,
    status_code=201,
    summary="Update Survey",
    description="Update user profile survey information (requires JWT)",
)
def update_survey(
    request: SurveyUpdateRequest,
    user: User = Depends(get_current_user),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """
    Update user profile survey.

    REQ: REQ-B-A2-Prof-1, REQ-B-A2-Prof-2, REQ-B-A2-Prof-3

    Creates new survey record (never updates existing) to maintain audit trail.

    Args:
        request: Survey update request
        user: Current authenticated user (from JWT)
        db: Database session

    Returns:
        Response with created survey ID and details

    Raises:
        HTTPException: 400 if validation fails, 401 if not authenticated

    """
    try:
        profile_service = ProfileService(db)
        survey_data = request.model_dump(exclude_none=True)
        result = profile_service.update_survey(user.id, survey_data)
        return {
            "success": True,
            "message": "자기평가 정보 업데이트 완료",
            "user_id": user.knox_id,
            "survey_id": result["survey_id"],
            "updated_at": result["submitted_at"],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error updating survey")
        raise HTTPException(status_code=500, detail="Failed to update survey") from e
