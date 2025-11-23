"""
Survey API endpoints for form schema and submission.

REQ: REQ-B-B1-1, REQ-B-B1-2
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.services.survey_service import SurveyService
from src.backend.utils.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["survey"])


class SurveySchemaResponse(BaseModel):
    """
    Response model for survey schema.

    Attributes:
        fields: List of field definitions with metadata

    """

    fields: list[dict[str, Any]] = Field(..., description="Survey form field definitions")


class SurveySubmitRequest(BaseModel):
    """
    Request model for survey submission.

    Attributes:
        self_level: Self-assessed proficiency level
        years_experience: Years of experience
        job_role: Job role/title
        duty: Main responsibilities
        interests: List of interest categories

    """

    self_level: str | None = Field(None, description="Self-assessed level")
    years_experience: int | None = Field(None, description="Years of experience (0-60)")
    job_role: str | None = Field(None, description="Job role/title (1-100 chars)")
    duty: str | None = Field(None, description="Main responsibilities (1-500 chars)")
    interests: list[str] | None = Field(None, description="Interest categories (1-20 items)")


class SurveySubmitResponse(BaseModel):
    """
    Response model for survey submission.

    Attributes:
        survey_id: Survey record ID
        user_id: User ID
        self_level: Self-assessed level
        submitted_at: Submission timestamp

    """

    survey_id: str = Field(..., description="Survey ID")
    user_id: int = Field(..., description="User ID")
    self_level: str | None = Field(..., description="Self-assessed level")
    submitted_at: str = Field(..., description="Submission timestamp")


@router.get(
    "/schema",
    response_model=SurveySchemaResponse,
    status_code=200,
    summary="Get Survey Schema",
    description="Get survey form schema with field definitions and validation rules",
)
def get_survey_schema(
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """
    Get survey form schema.

    REQ: REQ-B-B1-1

    Returns schema with field definitions, validation rules, and choices.

    Args:
        db: Database session (for consistency with other endpoints)

    Returns:
        Survey schema with field metadata

    """
    try:
        survey_service = SurveyService(db)
        schema = survey_service.get_survey_schema()
        return schema
    except Exception as e:
        logger.exception("Error getting survey schema")
        raise HTTPException(status_code=500, detail="Failed to get survey schema") from e


@router.post(
    "/submit",
    response_model=SurveySubmitResponse,
    status_code=201,
    summary="Submit Survey",
    description="Submit and save survey data",
)
def submit_survey(
    request: SurveySubmitRequest,
    user_id: int = Depends(get_current_user_id),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """
    Submit survey data.

    REQ: REQ-B-B1-2

    Validates survey data and saves to user_profile_surveys table.

    Args:
        request: Survey submission request
        user_id: Current user ID from JWT token
        db: Database session

    Returns:
        Response with survey_id and submission details

    Raises:
        HTTPException: If validation or submission fails

    """
    try:
        survey_service = SurveyService(db)
        survey_data = request.model_dump(exclude_none=True)
        result = survey_service.submit_survey(user_id, survey_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error submitting survey")
        raise HTTPException(status_code=500, detail="Failed to submit survey") from e
