"""
User Profile Tool - Get User's Self-Assessment Information.

REQ: REQ-A-Mode1-Tool1
Tool 1 for Mode 1 pipeline: Retrieve user self-assessment profile.
"""

import logging
import uuid
from typing import Any

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.models.user_profile import UserProfileSurvey

logger = logging.getLogger(__name__)

# Default profile values for fallback
DEFAULT_PROFILE = {
    "self_level": "beginner",
    "years_experience": 0,
    "job_role": "Unknown",
    "duty": "Not specified",
    "interests": [],
    "previous_score": 0,
}


def _validate_user_id(user_id: str) -> None:
    """
    Validate user_id format.

    Args:
        user_id: User ID to validate

    Raises:
        ValueError: If user_id is invalid (empty or wrong format)
        TypeError: If user_id is not a string

    """
    if not isinstance(user_id, str):
        raise TypeError(f"user_id must be string, got {type(user_id)}")
    if not user_id or not user_id.strip():
        raise ValueError("user_id cannot be empty")
    # Basic UUID format check
    try:
        uuid.UUID(user_id)
    except (ValueError, AttributeError) as e:
        raise ValueError(f"user_id must be valid UUID format: {e}") from e


def _get_user_profile_from_db(db: Session, user_id: str) -> UserProfileSurvey | None:
    """
    Query database for user's latest profile.

    Args:
        db: SQLAlchemy session
        user_id: User ID

    Returns:
        UserProfileSurvey instance or None if not found

    Raises:
        Exception: If database query fails

    """
    try:
        profile = (
            db.query(UserProfileSurvey)
            .filter(
                UserProfileSurvey.user_id == int(user_id) if user_id.isdigit() else UserProfileSurvey.user_id == user_id
            )
            .order_by(UserProfileSurvey.submitted_at.desc())
            .first()
        )
        return profile
    except Exception as e:
        logger.warning(f"Database query error for user {user_id}: {e}")
        return None


def _build_profile_response(user_id: str, profile: UserProfileSurvey | None) -> dict[str, Any]:
    """
    Build response dict from database profile.

    Args:
        user_id: User ID (for response)
        profile: UserProfileSurvey instance or None

    Returns:
        dict with profile information

    """
    if profile is None:
        # Return default profile with user_id
        return {
            "user_id": user_id,
            **DEFAULT_PROFILE,
        }

    # Build response from profile
    return {
        "user_id": user_id,
        "self_level": profile.self_level or DEFAULT_PROFILE["self_level"],
        "years_experience": profile.years_experience
        if profile.years_experience is not None
        else DEFAULT_PROFILE["years_experience"],
        "job_role": profile.job_role or DEFAULT_PROFILE["job_role"],
        "duty": profile.duty or DEFAULT_PROFILE["duty"],
        "interests": profile.interests or DEFAULT_PROFILE["interests"],
        "previous_score": profile.previous_score
        if hasattr(profile, "previous_score") and profile.previous_score is not None
        else DEFAULT_PROFILE["previous_score"],
    }


def _get_user_profile_impl(user_id: str) -> dict[str, Any]:
    """
    Implement get_user_profile (without @tool decorator).

    This is the actual function that can be tested.
    The @tool decorator wraps this function.

    Args:
        user_id: User ID (UUID string)

    Returns:
        dict: User profile with fields

    Raises:
        ValueError: If user_id is invalid format
        TypeError: If user_id is not a string

    """
    logger.info(f"Tool 1: Retrieving profile for user {user_id}")

    # Validate input
    try:
        _validate_user_id(user_id)
    except (ValueError, TypeError) as e:
        logger.error(f"Input validation failed: {e}")
        raise

    # Get database session
    db = next(get_db())
    try:
        # Query database
        profile = _get_user_profile_from_db(db, user_id)

        # Build and return response
        result = _build_profile_response(user_id, profile)
        logger.info(f"Successfully retrieved profile for user {user_id}")
        return result

    except Exception as e:
        logger.error(f"Error retrieving profile for user {user_id}: {e}")
        # Fallback: return default profile
        return _build_profile_response(user_id, None)
    finally:
        db.close()


@tool
def get_user_profile(user_id: str) -> dict[str, Any]:
    """
    Get user's self-assessment profile information.

    REQ: REQ-A-Mode1-Tool1

    Args:
        user_id: User ID (UUID string)

    Returns:
        dict: User profile with fields:
            - user_id: User ID
            - self_level: "beginner" | "intermediate" | "advanced"
            - years_experience: 0-60
            - job_role: Job title/role
            - duty: Main responsibilities
            - interests: List of interest categories
            - previous_score: Previous test score (0-100)

    Raises:
        ValueError: If user_id is invalid format
        TypeError: If user_id is not a string

    """
    return _get_user_profile_impl(user_id)
