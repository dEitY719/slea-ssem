"""
Questions API endpoints for generating test questions.

REQ: REQ-B-B2-Gen-1, REQ-B-B2-Gen-2, REQ-B-B2-Gen-3, REQ-B-B2-Adapt, REQ-B-B2-Plus, REQ-B-B3-Score, REQ-B-B3-Explain
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.database import get_db
from src.backend.services.autosave_service import AutosaveService
from src.backend.services.explain_service import ExplainService
from src.backend.services.question_gen_service import QuestionGenerationService
from src.backend.services.scoring_service import ScoringService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["questions"])


# ============================================================================
# Helper Functions
# ============================================================================


def all_answers_scored(session_id: str, db: Session) -> bool:
    """
    Check if all answers in a session have been scored.

    REQ: REQ-B-B3-Score (Auto-Complete)

    Args:
        session_id: TestSession ID
        db: Database session

    Returns:
        bool: True if all answers have been scored, False otherwise

    """
    from src.backend.models.attempt_answer import AttemptAnswer

    # Count unscored answers (where score is None)
    unscored_count = (
        db.query(AttemptAnswer).filter(AttemptAnswer.session_id == session_id, AttemptAnswer.score.is_(None)).count()
    )

    # All scored if unscored_count == 0
    return unscored_count == 0


class GenerateQuestionsRequest(BaseModel):
    """
    Request model for generating test questions.

    Attributes:
        survey_id: UserProfileSurvey ID to determine user interests
        round: Test round number (1 or 2, default 1)
        domain: Question domain/topic (e.g., "AI", "food", default "AI")
        question_count: Number of questions to generate (default 5, min 1, max 10)

    """

    survey_id: str = Field(..., description="UserProfileSurvey ID")
    round: int = Field(default=1, ge=1, le=2, description="Test round (1 or 2)")
    domain: str = Field(default="AI", description="Question domain/topic (e.g., AI, food, science)")
    question_count: int = Field(default=5, ge=1, le=10, description="Number of questions (1-10, default 5)")


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


class GenerateAdaptiveQuestionsRequest(BaseModel):
    """
    Request model for generating adaptive Round 2+ questions.

    Attributes:
        previous_session_id: Previous round TestSession ID (from Round 1)
        round: Target round number (2 or 3)
        count: Number of questions to generate (default 5, supports --count parameter)

    """

    previous_session_id: str = Field(..., description="Previous TestSession ID")
    round: int = Field(default=2, ge=2, le=3, description="Target round (2 or 3)")
    count: int = Field(default=5, ge=1, le=20, description="Number of questions to generate")


class GenerateAdaptiveQuestionsResponse(BaseModel):
    """
    Response model for adaptive question generation.

    Attributes:
        session_id: New TestSession UUID for this round
        questions: List of adaptive questions
        adaptive_params: Difficulty tier and weak categories info

    """

    session_id: str = Field(..., description="New TestSession ID")
    questions: list[QuestionResponse] = Field(..., description="Adaptive questions")
    adaptive_params: dict[str, Any] = Field(..., description="Difficulty adjustment parameters")


class AutosaveRequest(BaseModel):
    """
    Request model for auto-saving an answer.

    REQ: REQ-B-B2-Plus-1

    Attributes:
        session_id: TestSession ID
        question_id: Question ID being answered
        user_answer: User's response (JSON format)
        response_time_ms: Time taken to answer in milliseconds

    """

    session_id: str = Field(..., description="TestSession ID")
    question_id: str = Field(..., description="Question ID")
    user_answer: dict[str, Any] = Field(..., description="User's answer (JSON)")
    response_time_ms: int = Field(..., ge=0, description="Response time in milliseconds")


class AutosaveResponse(BaseModel):
    """
    Response model for autosave operation.

    Attributes:
        saved: Whether save was successful
        session_id: TestSession ID
        question_id: Question ID
        saved_at: Timestamp when saved (ISO format)

    """

    saved: bool = Field(..., description="Save success")
    session_id: str = Field(..., description="TestSession ID")
    question_id: str = Field(..., description="Question ID")
    saved_at: str = Field(..., description="Save timestamp (ISO format)")


class ResumeSessionResponse(BaseModel):
    """
    Response model for resuming a session.

    REQ: REQ-B-B2-Plus-3

    Attributes:
        session_id: TestSession ID
        status: Session status
        round: Current round
        answered_count: Number of answered questions
        total_questions: Total questions in session
        next_question_index: Index of next unanswered question
        previous_answers: List of previously saved answers
        time_status: Time limit status info

    """

    session_id: str = Field(..., description="TestSession ID")
    status: str = Field(..., description="Session status")
    round: int = Field(..., description="Round number")
    answered_count: int = Field(..., description="Number answered")
    total_questions: int = Field(..., description="Total questions")
    next_question_index: int = Field(..., description="Next question index")
    previous_answers: list[dict[str, Any]] = Field(..., description="Previous answers with metadata")
    time_status: dict[str, Any] = Field(..., description="Time limit status")


class ScoringRequest(BaseModel):
    """
    Request model for scoring an answer.

    REQ: REQ-B-B3-Score-1

    Attributes:
        session_id: TestSession ID
        question_id: Question ID to score

    """

    session_id: str = Field(..., description="TestSession ID")
    question_id: str = Field(..., description="Question ID")


class ScoringResponse(BaseModel):
    """
    Response model for scoring an answer.

    REQ: REQ-B-B3-Score-1, 2, 3

    Attributes:
        scored: Whether scoring was successful
        question_id: Question ID
        user_answer: User's submitted answer
        is_correct: Whether answer is correct
        score: Base score (0-100)
        feedback: Human-readable feedback
        time_penalty_applied: Whether time penalty was applied
        final_score: Final score after penalty
        scored_at: Timestamp when scored

    """

    scored: bool = Field(..., description="Scoring success")
    question_id: str = Field(..., description="Question ID")
    user_answer: dict[str, Any] | str = Field(..., description="User's answer")
    is_correct: bool = Field(..., description="Answer correctness")
    score: float = Field(..., description="Base score (0-100)")
    feedback: str = Field(..., description="Feedback message")
    time_penalty_applied: bool = Field(..., description="Penalty applied flag")
    final_score: float = Field(..., description="Final score after penalty")
    scored_at: str = Field(..., description="Scoring timestamp (ISO format)")


class GenerateExplanationRequest(BaseModel):
    """
    Request model for generating explanation.

    REQ: REQ-B-B3-Explain-1

    Attributes:
        question_id: Question ID to explain
        user_answer: User's submitted answer
        is_correct: Whether user's answer is correct
        attempt_answer_id: Optional FK to attempt_answers

    """

    question_id: str = Field(..., description="Question ID")
    user_answer: str | dict[str, Any] = Field(..., description="User's submitted answer")
    is_correct: bool = Field(..., description="Answer correctness")
    attempt_answer_id: str | None = Field(default=None, description="Attempt answer ID (optional)")


class ExplanationSection(BaseModel):
    """Single section of structured explanation."""

    title: str = Field(..., description="Section title (e.g., '핵심 개념', '복습 팁')")
    content: str = Field(..., description="Section content text")


class UserAnswerSummary(BaseModel):
    """User's answer vs correct answer comparison."""

    user_answer_text: str | None = Field(..., description="User's answer in readable format")
    correct_answer_text: str | None = Field(..., description="Correct answer in readable format")
    question_type: str = Field(..., description="Question type (multiple_choice, true_false, short_answer)")


class ExplanationResponse(BaseModel):
    """
    Response model for explanation generation.

    REQ: REQ-B-B3-Explain-1

    Attributes:
        id: Explanation ID
        question_id: Question ID
        attempt_answer_id: Attempt answer ID (if provided)
        explanation_text: Generated explanation (≥200 chars)
        explanation_sections: Structured explanation sections
        reference_links: Reference links with title and url (≥3)
        user_answer_summary: User's answer vs correct answer
        problem_statement: Question stem with explanation type context
        is_correct: Whether this is for correct/incorrect answer
        created_at: Timestamp when explanation was generated
        is_fallback: Whether fallback explanation was used
        error_message: Error details if fallback used

    """

    id: str = Field(..., description="Explanation ID")
    question_id: str = Field(..., description="Question ID")
    attempt_answer_id: str | None = Field(..., description="Attempt answer ID")
    explanation_text: str = Field(..., description="Generated explanation (≥200 chars)")
    explanation_sections: list[ExplanationSection] = Field(
        ...,
        description="Explanation divided into structured sections for better UX",
    )
    reference_links: list[dict[str, str]] = Field(..., description="Reference links (≥3)")
    user_answer_summary: UserAnswerSummary | None = Field(..., description="User's answer vs correct answer comparison")
    problem_statement: str | None = Field(..., description="Question stem with 오답/정답 해설 context")
    is_correct: bool | None = Field(..., description="Answer correctness context")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    is_fallback: bool = Field(..., description="Fallback flag (timeout/error)")
    error_message: str | None = Field(..., description="Error details if fallback")


@router.post(
    "/generate",
    response_model=GenerateQuestionsResponse,
    status_code=201,
    summary="Generate Test Questions",
    description="Generate 5 test questions based on user survey and interests",
)
async def generate_questions(
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
        result = await question_service.generate_questions(
            user_id=user_id,
            survey_id=request.survey_id,
            round_num=request.round,
            question_count=request.question_count,
            domain=request.domain,
        )
        return result
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e)) from e
        logger.exception("Error generating questions")
        raise HTTPException(status_code=500, detail="Failed to generate questions") from e


@router.post(
    "/score",
    status_code=200,
    summary="Calculate Round Score",
    description="Calculate and save test result for completed round, with optional auto-complete",
)
def calculate_round_score(
    session_id: str,
    auto_complete: bool = True,
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """
    Calculate and save test result for completed round.

    REQ: REQ-B-B3-Score, REQ-B-B2-Adapt

    Calculates score from all attempt answers in session:
    - Multiple choice / True-False: exact match
    - Short answer: keyword-based scoring
    - Identifies weak categories for adaptive Round 2
    - NEW: Auto-completes session if all answers are scored

    Args:
        session_id: TestSession ID to score
        auto_complete: Whether to auto-complete session if all answers scored (default True)
        db: Database session

    Returns:
        TestResult with score, correct count, weak categories, auto_completed status

    Raises:
        HTTPException: If session not found or no answers

    """
    try:
        scoring_service = ScoringService(db)
        # Get the round number from TestSession

        from src.backend.models.test_session import TestSession

        test_session = db.query(TestSession).filter_by(id=session_id).first()
        if not test_session:
            raise ValueError(f"TestSession {session_id} not found")

        result = scoring_service.save_round_result(session_id, test_session.round)

        # NEW: Auto-complete if enabled and all answers are scored
        auto_completed = False
        if auto_complete and all_answers_scored(session_id, db):
            test_session.status = "completed"
            db.commit()
            db.refresh(test_session)
            auto_completed = True
            logger.info(f"Auto-completed session {session_id} (Round {test_session.round})")

        return {
            "session_id": result.session_id,
            "round": result.round,
            "score": result.score,
            "correct_count": result.correct_count,
            "total_count": result.total_count,
            "wrong_categories": result.wrong_categories,
            "auto_completed": auto_completed,
        }
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e)) from e
        logger.exception("Error calculating round score")
        raise HTTPException(status_code=500, detail="Failed to calculate score") from e


@router.post(
    "/generate-adaptive",
    response_model=GenerateAdaptiveQuestionsResponse,
    status_code=201,
    summary="Generate Adaptive Round 2+ Questions",
    description="Generate questions with adaptive difficulty based on previous round results",
)
async def generate_adaptive_questions(
    request: GenerateAdaptiveQuestionsRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """
    Generate Round 2+ questions with adaptive difficulty using Real Agent.

    REQ: REQ-B-B2-Adapt-1, REQ-B-B2-Adapt-2, REQ-B-B2-Adapt-3

    Analyzes previous round results and generates questions with:
    - Real Agent LLM-based generation
    - Adjusted difficulty based on score
    - Prioritized weak categories (≥50%)
    - Customizable question count (default 5, supports --count parameter)

    Args:
        request: Adaptive generation request with previous_session_id, round, and optional count
        db: Database session

    Returns:
        Response with new session_id, adaptive questions, and parameters

    Raises:
        HTTPException: If previous round not found or score unavailable

    """
    # TODO: Extract user_id from JWT token in production
    user_id = 1  # Placeholder - should come from JWT

    try:
        question_service = QuestionGenerationService(db)
        result = await question_service.generate_questions_adaptive(
            user_id=user_id,
            session_id=request.previous_session_id,
            round_num=request.round,
            question_count=request.count,
        )
        return result
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e)) from e
        logger.exception("Error generating adaptive questions")
        raise HTTPException(status_code=500, detail="Failed to generate adaptive questions") from e


@router.post(
    "/autosave",
    response_model=AutosaveResponse,
    status_code=200,
    summary="Auto-save Answer",
    description="Save user's answer in real-time (< 2 seconds)",
)
def autosave_answer(
    request: AutosaveRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """
    Auto-save user's answer to a question in real-time.

    REQ: REQ-B-B2-Plus-1, REQ-B-B2-Plus-4, REQ-B-B2-Plus-5

    Performance requirement: Complete within 2 seconds.

    Args:
        request: Autosave request with session_id, question_id, user_answer, response_time_ms
        db: Database session

    Returns:
        Response with saved status and timestamp

    Raises:
        HTTPException: If session/question not found or save fails

    """
    try:
        autosave_service = AutosaveService(db)
        answer = autosave_service.save_answer(
            session_id=request.session_id,
            question_id=request.question_id,
            user_answer=request.user_answer,
            response_time_ms=request.response_time_ms,
        )

        # Check if time limit exceeded
        time_status = autosave_service.check_time_limit(request.session_id)
        if time_status["exceeded"]:
            # Auto-pause session
            autosave_service.pause_session(request.session_id, reason="time_limit")

        return {
            "saved": True,
            "session_id": answer.session_id,
            "question_id": answer.question_id,
            "saved_at": answer.saved_at.isoformat() if answer.saved_at else "",
        }
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e)) from e
        if "completed" in str(e).lower():
            raise HTTPException(status_code=409, detail=str(e)) from e
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error auto-saving answer")
        raise HTTPException(status_code=500, detail="Failed to autosave answer") from e


@router.get(
    "/resume",
    response_model=ResumeSessionResponse,
    status_code=200,
    summary="Resume Test Session",
    description="Get session state for resuming after pause/timeout",
)
def resume_session(
    session_id: str,
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """
    Resume a paused test session.

    REQ: REQ-B-B2-Plus-3

    Retrieves complete session state including:
    - Previous answers with metadata
    - Next unanswered question index
    - Time status

    Args:
        session_id: TestSession ID to resume
        db: Database session

    Returns:
        Complete session state for resumption

    Raises:
        HTTPException: If session not found or not resumable

    """
    try:
        autosave_service = AutosaveService(db)

        # Get session state
        state = autosave_service.get_session_state(session_id)

        # If session is paused, resume it
        from src.backend.models.test_session import TestSession

        test_session = db.query(TestSession).filter_by(id=session_id).first()
        if test_session and test_session.status == "paused":
            autosave_service.resume_session(session_id)
            state["status"] = "in_progress"

        return state
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e)) from e
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error resuming session")
        raise HTTPException(status_code=500, detail="Failed to resume session") from e


@router.put(
    "/session/{session_id}/status",
    status_code=200,
    summary="Update Session Status",
    description="Pause or resume a test session manually",
)
def update_session_status(
    session_id: str,
    status: str,
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """
    Update test session status (pause/resume).

    REQ: REQ-B-B2-Plus-2

    Args:
        session_id: TestSession ID
        status: New status (paused or in_progress)
        db: Database session

    Returns:
        Updated session status

    Raises:
        HTTPException: If session not found or invalid status

    """
    if status not in ["paused", "in_progress"]:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status: {status}. Must be 'paused' or 'in_progress'",
        )

    try:
        autosave_service = AutosaveService(db)

        if status == "paused":
            test_session = autosave_service.pause_session(session_id, reason="manual")
        else:  # in_progress
            test_session = autosave_service.resume_session(session_id)

        return {
            "session_id": test_session.id,
            "status": test_session.status,
            "paused_at": test_session.paused_at.isoformat() if test_session.paused_at else None,
        }
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e)) from e
        if "completed" in str(e).lower() or "not paused" in str(e).lower():
            raise HTTPException(status_code=409, detail=str(e)) from e
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error updating session status")
        raise HTTPException(status_code=500, detail="Failed to update session status") from e


@router.post(
    "/answer/score",
    response_model=ScoringResponse,
    status_code=200,
    summary="Score An Answer",
    description="Score a submitted answer with time penalty",
)
def score_answer(
    request: ScoringRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> ScoringResponse:
    """
    Score a submitted answer.

    REQ: REQ-B-B3-Score-1, 2, 3

    Args:
        request: ScoringRequest with session_id and question_id
        db: Database session

    Returns:
        ScoringResponse with is_correct, score, and feedback

    Raises:
        HTTPException: If session, question, or answer not found

    """
    try:
        scoring_service = ScoringService(db)
        result = scoring_service.score_answer(request.session_id, request.question_id)
        return ScoringResponse(**result)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg) from e
        raise HTTPException(status_code=422, detail=error_msg) from e
    except Exception as e:
        logger.exception("Error scoring answer")
        raise HTTPException(status_code=500, detail="Failed to score answer") from e


@router.post(
    "/session/{session_id}/complete",
    status_code=200,
    summary="Complete Test Session",
    description="Mark a test session as completed (SRP: Session Management Only)",
)
def complete_session(
    session_id: str,
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """
    Complete a test session independently.

    REQ: REQ-B-B3-Score

    Single Responsibility: Only marks session as completed.
    RankingService will be called separately via GET /profile/ranking endpoint.

    Design principle:
    - Each Round can be completed independently
    - Round 1 complete → Round 1 status="completed"
    - Round 2 complete → Round 2 status="completed"
    - RankingService queries all "completed" sessions to calculate ranking

    Args:
        session_id: TestSession ID to complete
        db: Database session

    Returns:
        Dictionary with:
            - status (str): "completed"
            - session_id (str): Session UUID
            - round (int): Round number
            - message (str): Success message

    Raises:
        HTTPException: If session not found

    """
    try:
        from src.backend.models.test_session import TestSession

        test_session = db.query(TestSession).filter_by(id=session_id).first()
        if not test_session:
            raise ValueError(f"Test session {session_id} not found")

        # Only one responsibility: mark session as completed
        test_session.status = "completed"
        db.commit()
        db.refresh(test_session)

        logger.info(f"Session {session_id} (Round {test_session.round}) marked as completed")

        return {
            "status": "completed",
            "session_id": session_id,
            "round": test_session.round,
            "message": f"Round {test_session.round} session completed successfully",
        }
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e)) from e
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error completing session")
        raise HTTPException(status_code=500, detail="Failed to complete session") from e


@router.get(
    "/session/{session_id}/time-status",
    status_code=200,
    summary="Check Time Status",
    description="Check if session has exceeded time limit",
)
def check_time_status(
    session_id: str,
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """
    Check time limit status for a session.

    REQ: REQ-B-B2-Plus-2

    Args:
        session_id: TestSession ID
        db: Database session

    Returns:
        Time status with exceeded flag, elapsed time, remaining time

    Raises:
        HTTPException: If session not found

    """
    try:
        autosave_service = AutosaveService(db)
        time_status = autosave_service.check_time_limit(session_id)
        return time_status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error checking time status")
        raise HTTPException(status_code=500, detail="Failed to check time status") from e


@router.post(
    "/explanations",
    response_model=ExplanationResponse,
    status_code=201,
    summary="Generate Question Explanation",
    description="Generate explanation with reference links for a test question",
)
def generate_explanation(
    request: GenerateExplanationRequest,
    db: Session = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """
    Generate explanation for a question answer.

    REQ: REQ-B-B3-Explain-1

    Generates explanation with reference links after answer is scored.
    Supports both correct and incorrect answers with contextual explanations.

    Performance requirement: Complete within 2 seconds.

    Args:
        request: GenerateExplanationRequest with question, answer, correctness
        db: Database session

    Returns:
        ExplanationResponse with explanation_text and reference_links (≥3)

    Raises:
        HTTPException 400: If validation fails
        HTTPException 404: If question not found
        HTTPException 500: If explanation generation fails

    """
    try:
        explain_service = ExplainService(db)
        explanation = explain_service.generate_explanation(
            question_id=request.question_id,
            user_answer=request.user_answer,
            is_correct=request.is_correct,
            attempt_answer_id=request.attempt_answer_id,
        )
        return explanation
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg) from e
        else:
            raise HTTPException(status_code=400, detail=error_msg) from e
    except Exception as e:
        logger.exception("Error generating explanation")
        raise HTTPException(status_code=500, detail="Failed to generate explanation") from e
