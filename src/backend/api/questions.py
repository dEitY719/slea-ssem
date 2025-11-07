"""
Questions API endpoints for generating test questions.

REQ: REQ-B-B2-Gen-1, REQ-B-B2-Gen-2, REQ-B-B2-Gen-3
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.services.question_gen_service import QuestionGenerationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questions", tags=["questions"])


class GenerateQuestionsRequest(BaseModel):
    """
    Request model for generating test questions.

    Attributes:
        survey_id: UserProfileSurvey ID to determine user interests
        round: Test round number (1 or 2, default 1)

    """

    survey_id: str = Field(..., description="UserProfileSurvey ID")
    round: int = Field(default=1, ge=1, le=2, description="Test round (1 or 2)")


class QuestionResponse(BaseModel):
    """
    Response model for a single question.

    Attributes:
        id: Question UUID
        item_type: Question type (multiple_choice, true_false, short_answer)
        stem: Question text/content
        choices: Answer choices (for multiple_choice/true_false)
        answer_schema: Correct answer and explanation
        difficulty: Difficulty level (1-10)
        category: Question category/topic

    """

    id: str = Field(..., description="Question ID")
    item_type: str = Field(..., description="Question type")
    stem: str = Field(..., description="Question text")
    choices: list[str] | None = Field(None, description="Answer choices")
    answer_schema: dict[str, Any] = Field(..., description="Answer info and explanation")
    difficulty: int = Field(..., description="Difficulty level")
    category: str = Field(..., description="Question category")


class GenerateQuestionsResponse(BaseModel):
    """
    Response model for question generation.

    Attributes:
        session_id: TestSession UUID
        questions: List of generated questions

    """

    session_id: str = Field(..., description="TestSession ID")
    questions: list[QuestionResponse] = Field(..., description="Generated questions")


@router.post(
    "/generate",
    response_model=GenerateQuestionsResponse,
    status_code=201,
    summary="Generate Test Questions",
    description="Generate 5 test questions based on user survey and interests",
)
def generate_questions(
    request: GenerateQuestionsRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """
    Generate test questions for a user.

    REQ: REQ-B-B2-Gen-1, REQ-B-B2-Gen-2, REQ-B-B2-Gen-3

    Generates 5 questions based on user profile survey (interests, level).
    Creates a test session and returns questions for the session.

    Args:
        request: Question generation request with survey_id and round
        db: Database session

    Returns:
        Response with session_id and list of 5 questions

    Raises:
        HTTPException: If survey not found or generation fails

    """
    # TODO: Extract user_id from JWT token in production
    user_id = 1  # Placeholder - should come from JWT

    try:
        question_service = QuestionGenerationService(db)
        result = question_service.generate_questions(
            user_id=user_id,
            survey_id=request.survey_id,
            round_num=request.round,
        )
        return result
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e)) from e
        logger.exception("Error generating questions")
        raise HTTPException(status_code=500, detail="Failed to generate questions") from e
