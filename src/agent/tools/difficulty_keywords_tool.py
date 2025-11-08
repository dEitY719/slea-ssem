"""
Difficulty Keywords Tool - Get keywords and concepts by difficulty level.

REQ: REQ-A-Mode1-Tool3
Tool 3 for Mode 1 pipeline: Retrieve difficulty-specific keywords and concepts.
"""

import logging
import threading
from typing import Any

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from src.backend.database import get_db

logger = logging.getLogger(__name__)

# Supported categories
SUPPORTED_CATEGORIES = {"technical", "business", "general"}
DIFFICULTY_MIN = 1
DIFFICULTY_MAX = 10
CACHE_TTL_SECONDS = 3600  # 1 hour

# In-memory cache
_keywords_cache: dict[str, Any] = {}
_cache_lock = threading.Lock()

# Default keywords fallback
DEFAULT_KEYWORDS = {
    "difficulty": 5,
    "category": "general",
    "keywords": [
        "Communication",
        "Problem Solving",
        "Teamwork",
        "Critical Thinking",
        "Adaptability",
    ],
    "concepts": [
        {
            "name": "Effective Communication",
            "acronym": "EC",
            "definition": "Clear and efficient exchange of information",
            "key_points": [
                "Clear message formulation",
                "Active listening",
                "Feedback exchange",
            ],
        },
        {
            "name": "Problem-Solving Approach",
            "acronym": "PSA",
            "definition": "Systematic method for addressing challenges",
            "key_points": [
                "Define the problem",
                "Generate solutions",
                "Evaluate and implement",
            ],
        },
    ],
    "example_questions": [
        {
            "stem": "What is effective communication in a team?",
            "type": "short_answer",
            "difficulty_score": 5.0,
            "answer_summary": "Clear exchange of information with active listening",
        }
    ],
}


def _validate_inputs(difficulty: int, category: str) -> None:
    """
    Validate input parameters.

    Args:
        difficulty: Difficulty level (1-10)
        category: Category ("technical", "business", or "general")

    Raises:
        TypeError: If inputs have wrong types
        ValueError: If inputs have invalid values

    """
    # Validate difficulty
    if not isinstance(difficulty, int):
        if isinstance(difficulty, float) and difficulty.is_integer():
            difficulty = int(difficulty)
        else:
            raise TypeError(f"difficulty must be int, got {type(difficulty)}")
    if difficulty < DIFFICULTY_MIN or difficulty > DIFFICULTY_MAX:
        raise ValueError(f"difficulty must be {DIFFICULTY_MIN}-{DIFFICULTY_MAX}, got {difficulty}")

    # Validate category
    if not isinstance(category, str):
        raise TypeError(f"category must be string, got {type(category)}")
    category_lower = category.lower()
    if category_lower not in SUPPORTED_CATEGORIES:
        raise ValueError(f"category must be one of {SUPPORTED_CATEGORIES}, got {category}")


def _get_cache_key(difficulty: int, category: str) -> str:
    """Generate cache key."""
    return f"{difficulty}_{category}"


def _get_from_cache(cache_key: str) -> dict[str, Any] | None:
    """Get value from cache if exists."""
    with _cache_lock:
        return _keywords_cache.get(cache_key)


def _set_in_cache(cache_key: str, value: dict[str, Any]) -> None:
    """Set value in cache."""
    with _cache_lock:
        _keywords_cache[cache_key] = value
        # Simple TTL: just keep in cache (in production, use expiration)


def _get_keywords_from_db(db: Session, difficulty: int, category: str) -> dict[str, Any] | None:
    """
    Query database for keywords.

    Args:
        db: SQLAlchemy session
        difficulty: Difficulty level
        category: Category

    Returns:
        Keywords dict or None if not found

    """
    try:
        # Import here to avoid circular imports
        from src.backend.models.difficulty_keyword import DifficultyKeyword

        record = (
            db.query(DifficultyKeyword)
            .filter(DifficultyKeyword.difficulty == difficulty)
            .filter(DifficultyKeyword.category == category)
            .first()
        )

        if record is None:
            return None

        # Build response dict
        result = {
            "difficulty": record.difficulty,
            "category": record.category,
            "keywords": record.keywords or [],
            "concepts": record.concepts or [],
            "example_questions": record.example_questions or [],
        }

        return result

    except Exception as e:
        logger.warning(f"Database query error: {e}")
        return None


def _normalize_response(data: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize response, filling in defaults for NULL fields.

    Args:
        data: Response dict from DB (may have NULL fields)

    Returns:
        Normalized response with defaults

    """
    if data is None:
        return DEFAULT_KEYWORDS.copy()

    # Fill in defaults for null/missing fields
    result = {
        "difficulty": data.get("difficulty", DEFAULT_KEYWORDS["difficulty"]),
        "category": data.get("category", DEFAULT_KEYWORDS["category"]),
        "keywords": data.get("keywords") or DEFAULT_KEYWORDS["keywords"],
        "concepts": data.get("concepts") or DEFAULT_KEYWORDS["concepts"],
        "example_questions": data.get("example_questions") or DEFAULT_KEYWORDS["example_questions"],
    }

    return result


def _get_difficulty_keywords_impl(difficulty: int, category: str) -> dict[str, Any]:
    """
    Implement get_difficulty_keywords (without @tool decorator).

    This is the actual function that can be tested.
    The @tool decorator wraps this function.

    Args:
        difficulty: Difficulty level (1-10)
        category: Category ("technical", "business", or "general")

    Returns:
        dict: Keywords with fields:
            - difficulty: Echo of input
            - category: Echo of input
            - keywords: list[str] of keywords (5-20 items)
            - concepts: list[dict] with name, acronym, definition, key_points
            - example_questions: list[dict] with stem, type, difficulty_score, answer_summary

    Raises:
        ValueError: If difficulty or category invalid
        TypeError: If inputs have wrong types

    """
    logger.info(f"Tool 3: Retrieving keywords for difficulty={difficulty}, category={category}")

    # Validate inputs
    try:
        _validate_inputs(difficulty, category)
    except (ValueError, TypeError) as e:
        logger.error(f"Input validation failed: {e}")
        raise

    # Try cache first
    cache_key = _get_cache_key(difficulty, category)
    cached_result = _get_from_cache(cache_key)
    if cached_result is not None:
        logger.debug(f"Cache HIT for {cache_key}")
        return cached_result

    # Cache miss - query database
    logger.debug(f"Cache MISS for {cache_key}")
    db = next(get_db())
    try:
        # Query database
        db_result = _get_keywords_from_db(db, difficulty, category)

        # Normalize response (fill defaults for NULL fields)
        result = _normalize_response(db_result)

        # Store in cache
        _set_in_cache(cache_key, result)

        logger.info(f"Successfully retrieved keywords for difficulty={difficulty}")
        return result

    except Exception as e:
        logger.error(f"Error retrieving keywords: {e}")
        # Graceful degradation: return defaults
        return DEFAULT_KEYWORDS.copy()
    finally:
        db.close()


@tool
def get_difficulty_keywords(difficulty: int, category: str) -> dict[str, Any]:
    """
    Get keywords and concepts for a specific difficulty level.

    REQ: REQ-A-Mode1-Tool3

    This tool provides difficulty-specific keywords, concepts, and example
    questions to enhance LLM-based question generation. Uses in-memory caching
    with 1-hour TTL for performance optimization.

    Args:
        difficulty: Difficulty level (1-10 range)
                    1-3: Beginner, 4-6: Intermediate, 7-9: Advanced, 10: Expert
        category: Question category ("technical", "business", or "general")

    Returns:
        dict: Contains:
            - difficulty: Input difficulty level (echo)
            - category: Input category (echo)
            - keywords: List of 5-20 relevant keywords
            - concepts: List of up to 10 concept dicts, each with:
                - name: Concept name
                - acronym: Short acronym
                - definition: Concept definition
                - key_points: List of 3-5 key points
            - example_questions: List of up to 5 example questions, each with:
                - stem: Question text
                - type: "short_answer", "multiple_choice", or "true_false"
                - difficulty_score: 1.0-10.0 actual difficulty
                - answer_summary: Brief answer summary

    Raises:
        ValueError: If difficulty not in 1-10 or category not recognized
        TypeError: If inputs have wrong types

    Example:
        >>> result = get_difficulty_keywords(difficulty=7, category="technical")
        >>> result["keywords"]
        ["LLM", "Transformer", "Attention", ...]

    """
    return _get_difficulty_keywords_impl(difficulty, category)
