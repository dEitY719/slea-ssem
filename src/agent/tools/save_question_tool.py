"""
Save Generated Question Tool - Save validated questions to database.

REQ: REQ-A-Mode1-Tool5
Tool 5 for Mode 1 pipeline: Save validated questions to question_bank with metadata.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from langchain_core.tools import tool

from src.backend.database import get_db
from src.backend.models.question import Question

logger = logging.getLogger(__name__)

# Question type constants
QUESTION_TYPES = {"multiple_choice", "true_false", "short_answer"}

# Difficulty range
MIN_DIFFICULTY = 1
MAX_DIFFICULTY = 10

# Memory queue for failed saves (for batch retry)
SAVE_RETRY_QUEUE: list[dict[str, Any]] = []


def _validate_save_question_inputs(
    item_type: str,
    stem: str,
    choices: list[str] | None,
    correct_key: str | None,
    correct_keywords: list[str] | None,
    difficulty: int,
    categories: list[str],
    round_id: str,
) -> None:
    """
    Validate input parameters.

    Args:
        item_type: Question type
        stem: Question stem
        choices: Answer choices
        correct_key: Correct answer (for MC/TF)
        correct_keywords: Correct keywords (for short_answer)
        difficulty: Difficulty level (1-10)
        categories: Domain categories
        round_id: Round ID

    Raises:
        TypeError: If inputs have wrong types
        ValueError: If inputs have invalid values

    """
    # Validate item_type
    if not isinstance(item_type, str):
        raise TypeError(f"item_type must be string, got {type(item_type)}")
    if item_type not in QUESTION_TYPES:
        raise ValueError(f"item_type must be one of {QUESTION_TYPES}, got {item_type}")

    # Validate stem
    if not isinstance(stem, str):
        raise TypeError(f"stem must be string, got {type(stem)}")
    if not stem or not stem.strip():
        raise ValueError("stem cannot be empty")

    # Validate difficulty
    if not isinstance(difficulty, int):
        raise TypeError(f"difficulty must be int, got {type(difficulty)}")
    if difficulty < MIN_DIFFICULTY or difficulty > MAX_DIFFICULTY:
        raise ValueError(f"difficulty must be {MIN_DIFFICULTY}-{MAX_DIFFICULTY}, got {difficulty}")

    # Validate categories
    if not isinstance(categories, list):
        raise TypeError(f"categories must be list, got {type(categories)}")
    if not categories:
        raise ValueError("categories cannot be empty")
    if not all(isinstance(c, str) for c in categories):
        raise TypeError("All categories must be strings")

    # Validate round_id
    if not isinstance(round_id, str):
        raise TypeError(f"round_id must be string, got {type(round_id)}")
    if not round_id or not round_id.strip():
        raise ValueError("round_id cannot be empty")

    # Type-specific validation
    if item_type == "multiple_choice":
        if correct_key is None:
            raise ValueError("correct_key required for multiple_choice")
        if not choices or correct_key not in choices:
            raise ValueError("correct_key must be in choices for multiple_choice")
    elif item_type == "true_false":
        if correct_key is None:
            raise ValueError("correct_key required for true_false")
        if correct_key not in ["True", "False", "true", "false"]:
            raise ValueError("correct_key must be 'True' or 'False' for true_false")
    elif item_type == "short_answer":
        if correct_keywords is None:
            raise ValueError("correct_keywords required for short_answer")
        if not correct_keywords or not all(isinstance(k, str) for k in correct_keywords):
            raise ValueError("correct_keywords must be non-empty list of strings")


def _build_answer_schema(
    item_type: str,
    correct_key: str | None,
    correct_keywords: list[str] | None,
    validation_score: float | None,
    explanation: str | None,
) -> dict[str, Any]:
    """
    Build answer_schema JSON object.

    Args:
        item_type: Question type
        correct_key: Correct answer (for MC/TF)
        correct_keywords: Correct keywords (for short_answer)
        validation_score: Tool 4's final_score (metadata)
        explanation: Optional explanation

    Returns:
        answer_schema dict for Question model

    """
    schema: dict[str, Any] = {}

    # Add answer info based on type
    if item_type in ("multiple_choice", "true_false"):
        schema["correct_key"] = correct_key
    elif item_type == "short_answer":
        schema["correct_keywords"] = correct_keywords or []

    # Add metadata
    if validation_score is not None:
        schema["validation_score"] = validation_score

    if explanation:
        schema["explanation"] = explanation

    return schema


def _extract_category_string(categories: list[str]) -> str:
    """
    Extract single category string from categories list.

    Uses first category as primary category for the Question model.
    Additional categories could be stored in answer_schema if needed.

    Args:
        categories: List of domain categories

    Returns:
        Primary category (first item)

    """
    return categories[0] if categories else "general"


def _extract_round_number(round_id: str) -> int:
    """
    Extract round number from round_id.

    Format: "{session_id}_{round_number}_{timestamp}"
    Example: "sess_abc123_1_2025-11-06T10:30:00Z"

    Args:
        round_id: Round ID string

    Returns:
        Round number (1 or 2, default 1)

    """
    try:
        parts = round_id.split("_")
        if len(parts) >= 2:
            round_num = int(parts[1])
            return round_num if round_num in (1, 2) else 1
    except (ValueError, IndexError):
        pass
    return 1


def _extract_session_id(round_id: str) -> str:
    """
    Extract session_id from round_id.

    Format: "{session_id}_{round_number}_{timestamp}"

    Args:
        round_id: Round ID string

    Returns:
        Session ID (for linking to test_sessions)

    """
    parts = round_id.split("_")
    return parts[0] if parts else "unknown"


def _save_generated_question_impl(
    item_type: str,
    stem: str,
    choices: list[str] | None = None,
    correct_key: str | None = None,
    correct_keywords: list[str] | None = None,
    difficulty: int = 5,
    categories: list[str] | None = None,
    round_id: str = "",
    validation_score: float | None = None,
    explanation: str | None = None,
) -> dict[str, Any]:
    """
    Implement save_generated_question (without @tool decorator).

    This is the actual function that can be tested.
    The @tool decorator wraps this function.

    Args:
        item_type: Question type
        stem: Question stem
        choices: Answer choices (for multiple_choice)
        correct_key: Correct answer (for MC/TF)
        correct_keywords: Correct keywords (for short_answer)
        difficulty: Difficulty level (1-10)
        categories: Domain categories
        round_id: Round ID for tracking
        validation_score: Tool 4's final_score (metadata)
        explanation: Optional explanation

    Returns:
        dict: Result with question_id, round_id, saved_at, success

    Raises:
        ValueError: If inputs are invalid
        TypeError: If inputs have wrong types

    """
    logger.info(f"Tool 5: Saving generated question (type={item_type})")

    # Set defaults
    if categories is None:
        categories = ["general"]

    # Validate inputs
    try:
        _validate_save_question_inputs(
            item_type, stem, choices, correct_key, correct_keywords, difficulty, categories, round_id
        )
    except (ValueError, TypeError) as e:
        logger.error(f"Input validation failed: {e}")
        raise

    # Build answer_schema
    answer_schema = _build_answer_schema(item_type, correct_key, correct_keywords, validation_score, explanation)

    # Extract metadata
    category_str = _extract_category_string(categories)
    round_num = _extract_round_number(round_id)

    # Get database session and save
    db = next(get_db())
    try:
        # Create Question instance
        question = Question(
            session_id="unknown",  # Will be filled by agent orchestration
            item_type=item_type,
            stem=stem,
            choices=choices,
            answer_schema=answer_schema,
            difficulty=difficulty,
            category=category_str,
            round=round_num,
        )

        # Save to database
        db.add(question)
        db.commit()
        db.refresh(question)

        logger.info(f"Question saved successfully: {question.id}")

        return {
            "question_id": question.id,
            "round_id": round_id,
            "saved_at": question.created_at.isoformat(),
            "success": True,
        }

    except Exception as e:
        logger.error(f"Failed to save question: {e}")
        db.rollback()

        # Fallback: Add to retry queue for batch processing
        retry_item = {
            "item_type": item_type,
            "stem": stem,
            "choices": choices,
            "correct_key": correct_key,
            "correct_keywords": correct_keywords,
            "difficulty": difficulty,
            "categories": categories,
            "round_id": round_id,
            "validation_score": validation_score,
            "explanation": explanation,
        }
        SAVE_RETRY_QUEUE.append(retry_item)
        logger.warning(f"Question added to retry queue (queue size: {len(SAVE_RETRY_QUEUE)})")

        # Return partial success with retry indication
        return {
            "question_id": None,
            "round_id": round_id,
            "saved_at": datetime.now(UTC).isoformat(),
            "success": False,
            "error": str(e),
            "queued_for_retry": True,
        }

    finally:
        db.close()


@tool
def save_generated_question(
    item_type: str,
    stem: str,
    choices: list[str] | None = None,
    correct_key: str | None = None,
    correct_keywords: list[str] | None = None,
    difficulty: int = 5,
    categories: list[str] | None = None,
    round_id: str = "",
    validation_score: float | None = None,
    explanation: str | None = None,
) -> dict[str, Any]:
    """
    Save a validated question to the question_bank.

    REQ: REQ-A-Mode1-Tool5

    This tool saves questions that have passed Tool 4 validation to the database.
    Stores validation metadata (score, explanation) in answer_schema for traceability.

    Args:
        item_type: "multiple_choice" | "true_false" | "short_answer"
        stem: Question text/stem (max 2000 chars)
        choices: Answer choices for multiple_choice (4-5 items) or true_false (2 items)
        correct_key: Correct answer for MC/TF (must be in choices)
        correct_keywords: Correct keywords for short_answer (list of key terms)
        difficulty: Difficulty level 1-10
        categories: Domain categories (e.g., ["LLM", "RAG"])
        round_id: Round ID for tracking (format: "session_id_round_timestamp")
        validation_score: Tool 4's final_score (0.0-1.0) - stored as metadata
        explanation: Optional explanation - stored as metadata

    Returns:
        dict with:
            - question_id: UUID of saved question
            - round_id: Echo of input round_id
            - saved_at: ISO 8601 timestamp
            - success: True if saved, False if queued for retry
            - error: Error message if failed
            - queued_for_retry: True if added to memory queue

    Raises:
        ValueError: If inputs are invalid
        TypeError: If inputs have wrong types

    Example:
        >>> result = save_generated_question(
        ...     item_type="multiple_choice",
        ...     stem="What is RAG?",
        ...     choices=["A", "B", "C", "D"],
        ...     correct_key="B",
        ...     difficulty=7,
        ...     categories=["LLM", "RAG"],
        ...     round_id="sess_123_1_2025-11-09T10:30:00Z",
        ...     validation_score=0.92,
        ...     explanation="RAG combines retrieval with generation..."
        ... )
        >>> result["success"]
        True

    """
    return _save_generated_question_impl(
        item_type,
        stem,
        choices,
        correct_key,
        correct_keywords,
        difficulty,
        categories,
        round_id,
        validation_score,
        explanation,
    )


def get_retry_queue() -> list[dict[str, Any]]:
    """
    Get the memory queue of failed saves for batch retry.

    Returns:
        List of unsaved question dictionaries

    """
    return SAVE_RETRY_QUEUE.copy()


def clear_retry_queue() -> int:
    """
    Clear the memory queue after successful batch retry.

    Returns:
        Number of items cleared

    """
    count = len(SAVE_RETRY_QUEUE)
    SAVE_RETRY_QUEUE.clear()
    return count
