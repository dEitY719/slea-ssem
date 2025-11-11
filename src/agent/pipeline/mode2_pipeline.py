"""
Mode 2 Auto-Scoring Pipeline - Orchestrate question answer scoring workflow.

REQ: REQ-A-Mode2-Pipeline
Pipeline for Mode 2: Auto-score user answers and generate explanations.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from src.agent.tools.score_and_explain_tool import _score_and_explain_impl

logger = logging.getLogger(__name__)

# Question type constants
QUESTION_TYPES = {"multiple_choice", "true_false", "short_answer"}


def _validate_score_request(
    session_id: str,
    user_id: str,
    question_id: str,
    question_type: str,
    user_answer: str,
    correct_answer: str | None = None,
    correct_keywords: list[str] | None = None,
) -> None:
    """
    Validate score request before processing.

    Args:
        session_id: Test session ID
        user_id: User ID
        question_id: Question ID
        question_type: "multiple_choice" | "true_false" | "short_answer"
        user_answer: User's response
        correct_answer: Expected answer (required for MC/OX)
        correct_keywords: Keywords for SA validation

    Raises:
        ValueError: If validation fails
        TypeError: If type is wrong

    """
    # Required string fields
    required_fields = {
        "session_id": session_id,
        "user_id": user_id,
        "question_id": question_id,
        "question_type": question_type,
        "user_answer": user_answer,
    }

    for field_name, field_value in required_fields.items():
        if not isinstance(field_value, str):
            raise TypeError(f"{field_name} must be string, got {type(field_value)}")

    # Validate question_type
    if question_type not in QUESTION_TYPES:
        raise ValueError(f"question_type must be one of {QUESTION_TYPES}, got {question_type}")

    # Validate MC/OX requires correct_answer
    if question_type in {"multiple_choice", "true_false"}:
        if correct_answer is None or not isinstance(correct_answer, str):
            raise ValueError(f"correct_answer required for {question_type}, got {correct_answer}")

    # Validate SA requires correct_keywords
    if question_type == "short_answer":
        if correct_keywords is None or not isinstance(correct_keywords, list):
            raise ValueError(f"correct_keywords required for short_answer, got {correct_keywords}")


def _score_answer_impl(
    session_id: str,
    user_id: str,
    question_id: str,
    question_type: str,
    user_answer: str,
    correct_answer: str | None = None,
    correct_keywords: list[str] | None = None,
    difficulty: int | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """
    Implement score_answer for Mode 2 pipeline (without class wrapper).

    This is the orchestration logic that can be tested independently.

    Args:
        session_id: Test session ID
        user_id: User ID
        question_id: Question ID
        question_type: "multiple_choice" | "true_false" | "short_answer"
        user_answer: User's response
        correct_answer: Expected answer (required for MC/OX)
        correct_keywords: Keywords for SA validation
        difficulty: Question difficulty level (optional)
        category: Question category (optional)

    Returns:
        dict with scoring result:
            - attempt_id: Unique attempt identifier
            - session_id: Test session ID
            - question_id: Question ID
            - user_id: User ID
            - is_correct: Boolean correctness
            - score: 0-100 score
            - explanation: Explanation text
            - keyword_matches: Keywords found (for SA)
            - feedback: Additional feedback or None
            - graded_at: ISO format timestamp

    Raises:
        ValueError: If validation fails
        TypeError: If types are wrong

    """
    logger.info(f"Mode 2 Pipeline: Scoring question {question_id}, type={question_type}")

    # Phase 1: Validate request
    try:
        _validate_score_request(
            session_id,
            user_id,
            question_id,
            question_type,
            user_answer,
            correct_answer,
            correct_keywords,
        )
    except (ValueError, TypeError) as e:
        logger.error(f"Request validation failed: {e}")
        raise

    # Phase 2: Call Tool 6 (score_and_explain)
    try:
        logger.info(f"Mode 2 Pipeline: Calling Tool 6 for question {question_id}")

        result = _score_and_explain_impl(
            session_id=session_id,
            user_id=user_id,
            question_id=question_id,
            question_type=question_type,
            user_answer=user_answer,
            correct_answer=correct_answer,
            correct_keywords=correct_keywords,
            difficulty=difficulty,
            category=category,
        )

        logger.info(f"Mode 2 Pipeline: Tool 6 success - score={result['score']}, is_correct={result['is_correct']}")

        return result

    except TimeoutError as e:
        logger.error(f"Mode 2 Pipeline: Tool 6 timeout: {e}")
        # For MC/OX, can use exact match fallback
        # For SA, return default score
        if question_type in {"multiple_choice", "true_false"}:
            is_correct = user_answer.strip().upper() == correct_answer.strip().upper()
            score = 100 if is_correct else 0
        else:
            # SA fallback: default score with LLM timeout message
            is_correct = False
            score = 50

        fallback_explanation = (
            "The system experienced a temporary delay in generating a detailed explanation. "
            "Please review the key concepts to improve your understanding."
        )

        result = {
            "attempt_id": str(uuid.uuid4()),
            "session_id": session_id,
            "question_id": question_id,
            "user_id": user_id,
            "is_correct": is_correct,
            "score": score,
            "explanation": fallback_explanation,
            "keyword_matches": ([] if question_type == "short_answer" else []),
            "feedback": "LLM service temporarily unavailable. Score based on basic validation.",
            "graded_at": datetime.now(UTC).isoformat(),
        }

        logger.warning(f"Mode 2 Pipeline: Returned fallback score {score} for {question_type}")
        return result

    except Exception as e:
        logger.error(f"Mode 2 Pipeline: Tool 6 failed: {e}")
        raise


class Mode2Pipeline:
    """
    Mode 2 Auto-Scoring Pipeline.

    Orchestrates the complete workflow for auto-scoring user answers and
    generating explanations using Tool 6.

    REQ: REQ-A-Mode2-Pipeline

    Design principle:
    - Single tool (Tool 6) execution per request
    - Request validation before tool call
    - Graceful error handling with fallback
    - Full context preservation (request → response)

    """

    def __init__(self, session_id: str | None = None) -> None:
        """
        Initialize Mode 2 Pipeline.

        Args:
            session_id: Optional test session ID for logging context

        """
        self.session_id = session_id
        logger.info(f"Mode 2 Pipeline initialized (session={session_id})")

    def score_answer(
        self,
        user_id: str,
        question_id: str,
        question_type: str,
        user_answer: str,
        correct_answer: str | None = None,
        correct_keywords: list[str] | None = None,
        difficulty: int | None = None,
        category: str | None = None,
    ) -> dict[str, Any]:
        """
        Score a single answer using Tool 6.

        REQ: REQ-A-Mode2-Pipeline

        Args:
            user_id: User identifier
            question_id: Question identifier
            question_type: "multiple_choice" | "true_false" | "short_answer"
            user_answer: User's response text
            correct_answer: Expected answer (required for MC/OX)
            correct_keywords: Keywords for SA validation (required for SA)
            difficulty: Question difficulty (optional)
            category: Question category (optional)

        Returns:
            dict with scoring result:
                - attempt_id: Unique attempt identifier
                - session_id: Test session ID
                - question_id: Question ID
                - user_id: User ID
                - is_correct: Boolean correctness
                - score: 0-100 score
                - explanation: Explanation text
                - keyword_matches: Keywords found (for SA)
                - feedback: Additional feedback
                - graded_at: ISO format timestamp

        Raises:
            ValueError: If inputs are invalid
            TypeError: If types are wrong

        Example:
            >>> pipeline = Mode2Pipeline(session_id="sess_001")
            >>> result = pipeline.score_answer(
            ...     user_id="user_001",
            ...     question_id="q_001",
            ...     question_type="multiple_choice",
            ...     user_answer="B",
            ...     correct_answer="B",
            ... )
            >>> result["is_correct"]
            True

        """
        return _score_answer_impl(
            session_id=self.session_id,
            user_id=user_id,
            question_id=question_id,
            question_type=question_type,
            user_answer=user_answer,
            correct_answer=correct_answer,
            correct_keywords=correct_keywords,
            difficulty=difficulty,
            category=category,
        )

    def score_answers_batch(
        self,
        answers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Score multiple answers in batch with graceful degradation.

        Implements graceful degradation pattern: Individual answer failures do not stop
        the entire batch. Successful answers are returned with statistics, and failed
        question IDs are tracked separately.

        Args:
            answers: List of answer dicts with fields:
                - user_id, question_id, question_type, user_answer
                - correct_answer (for MC/OX), correct_keywords (for SA)
                - difficulty, category (optional)

        Returns:
            dict with:
                - results: List of successful scoring results
                - failed_question_ids: List of question IDs that failed
                - batch_stats: Statistics for successful results
                  - total_count: Total answers processed
                  - successful_count: Successfully scored answers
                  - failed_count: Failed answers
                  - average_score: Average score of successful answers
                  - correct_count: Number of correct answers

        Example:
            >>> answers = [
            ...     {
            ...         "user_id": "user_001",
            ...         "question_id": "q_001",
            ...         "question_type": "multiple_choice",
            ...         "user_answer": "B",
            ...         "correct_answer": "B",
            ...     },
            ...     {
            ...         "user_id": "user_001",
            ...         "question_id": "q_002",
            ...         "question_type": "short_answer",
            ...         "user_answer": "RAG combines retrieval",
            ...         "correct_keywords": ["RAG", "retrieval"],
            ...     },
            ... ]
            >>> response = pipeline.score_answers_batch(answers)
            >>> len(response["results"])  # Successful answers
            2
            >>> response["batch_stats"]["successful_count"]
            2

        """
        logger.info(f"Mode 2 Pipeline: Batch scoring {len(answers)} answers (graceful degradation enabled)")

        # Track results and failures
        successful_results: list[dict[str, Any]] = []
        failed_question_ids: list[str] = []

        # Metrics for statistics
        total_score = 0.0
        correct_count = 0

        for i, answer in enumerate(answers):
            question_id = answer.get("question_id", f"unknown_{i}")
            try:
                result = self.score_answer(
                    user_id=answer["user_id"],
                    question_id=answer["question_id"],
                    question_type=answer["question_type"],
                    user_answer=answer["user_answer"],
                    correct_answer=answer.get("correct_answer"),
                    correct_keywords=answer.get("correct_keywords"),
                    difficulty=answer.get("difficulty"),
                    category=answer.get("category"),
                )
                successful_results.append(result)

                # Accumulate stats
                total_score += result.get("score", 0)
                if result.get("is_correct", False):
                    correct_count += 1

                logger.info(f"Mode 2 Pipeline: Batch {i + 1}/{len(answers)} - q={question_id} ✓")

            except (ValueError, TypeError) as e:
                # Graceful degradation: Log error and continue
                logger.warning(f"Mode 2 Pipeline: Batch {i + 1}/{len(answers)} - q={question_id} ✗ ({str(e)[:100]})")
                failed_question_ids.append(question_id)

            except Exception as e:
                # Unexpected error
                logger.error(f"Mode 2 Pipeline: Batch {i + 1}/{len(answers)} - q={question_id} unexpected error: {e}")
                failed_question_ids.append(question_id)

        # Calculate statistics
        successful_count = len(successful_results)
        failed_count = len(failed_question_ids)
        average_score = (total_score / successful_count) if successful_count > 0 else 0.0

        batch_stats = {
            "total_count": len(answers),
            "successful_count": successful_count,
            "failed_count": failed_count,
            "average_score": average_score,
            "correct_count": correct_count,
            "correct_rate": (correct_count / successful_count) if successful_count > 0 else 0.0,
        }

        response = {
            "results": successful_results,
            "failed_question_ids": failed_question_ids,
            "batch_stats": batch_stats,
        }

        logger.info(
            f"Mode 2 Pipeline: Batch complete - "
            f"success={successful_count}/{len(answers)}, "
            f"failed={failed_count}, "
            f"avg_score={average_score:.1f}"
        )
        return response
