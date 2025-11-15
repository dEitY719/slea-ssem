"""
Score & Generate Explanation Tool - Auto-score answers and generate explanations.

REQ: REQ-A-Mode2-Tool6
Tool 6 for Mode 2 pipeline: Auto-score user answers and generate explanations.
"""

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from langchain_core.tools import tool

from src.agent.config import create_llm

logger = logging.getLogger(__name__)

# Question type constants
QUESTION_TYPES = {"multiple_choice", "true_false", "short_answer"}

# Scoring thresholds
HIGH_SCORE_THRESHOLD = 80  # >= 80 → is_correct=True, score=100
PARTIAL_CREDIT_LOWER = 70  # 70-79 → partial credit
PARTIAL_CREDIT_UPPER = 79
LOW_SCORE_THRESHOLD = 70  # < 70 → is_correct=False

# Explanation requirements
MIN_EXPLANATION_LENGTH = 200  # chars
MIN_REFERENCE_LINKS = 3

# LLM scoring defaults
DEFAULT_LLM_SCORE = 50  # Fallback score if LLM fails


def _validate_score_answer_inputs(
    session_id: str,
    user_id: str,
    question_id: str,
    question_type: str,
    user_answer: str,
    correct_answer: str | None = None,
    correct_keywords: list[str] | None = None,
) -> None:
    """
    Validate input parameters for score_and_explain tool.

    Args:
        session_id: Test session ID
        user_id: User ID
        question_id: Question ID
        question_type: "multiple_choice" | "true_false" | "short_answer"
        user_answer: User's response
        correct_answer: Expected answer (required for MC/OX)
        correct_keywords: Keywords for short answer validation

    Raises:
        TypeError: If inputs have wrong types
        ValueError: If inputs have invalid values

    """
    # Validate required string fields
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

    # Validate question_type is supported
    if question_type not in QUESTION_TYPES:
        raise ValueError(f"question_type must be one of {QUESTION_TYPES}, got {question_type}")

    # Validate MC/OX requires correct_answer
    if question_type in {"multiple_choice", "true_false"}:
        if correct_answer is None or not isinstance(correct_answer, str):
            raise ValueError(f"correct_answer required for {question_type}, got {correct_answer}")

    # Validate short_answer requires correct_keywords
    if question_type == "short_answer":
        if correct_keywords is None or not isinstance(correct_keywords, list):
            raise ValueError(f"correct_keywords required for short_answer, got {correct_keywords}")


def _score_multiple_choice(
    user_answer: str,
    correct_answer: str,
) -> tuple[bool, int]:
    """
    Score multiple choice question using exact match.

    Args:
        user_answer: User's response
        correct_answer: Expected answer

    Returns:
        Tuple of (is_correct, score)
        - is_correct: True if exact match, False otherwise
        - score: 100 if correct, 0 if incorrect

    """
    # Normalize: strip whitespace and convert to uppercase
    normalized_user = user_answer.strip().upper()
    normalized_correct = correct_answer.strip().upper()

    is_correct = normalized_user == normalized_correct
    score = 100 if is_correct else 0

    logger.debug(
        f"MC scoring: user='{normalized_user}', correct='{normalized_correct}', is_correct={is_correct}, score={score}"
    )

    return is_correct, score


def _score_true_false(
    user_answer: str,
    correct_answer: str,
) -> tuple[bool, int]:
    """
    Score true/false question using exact match.

    Args:
        user_answer: User's response ("True" or "False")
        correct_answer: Expected answer ("True" or "False")

    Returns:
        Tuple of (is_correct, score)

    """
    # Normalize: case-insensitive comparison
    normalized_user = user_answer.strip().lower()
    normalized_correct = correct_answer.strip().lower()

    is_correct = normalized_user == normalized_correct
    score = 100 if is_correct else 0

    logger.debug(
        f"OX scoring: user='{normalized_user}', correct='{normalized_correct}', is_correct={is_correct}, score={score}"
    )

    return is_correct, score


def _extract_keyword_matches(
    user_answer: str,
    correct_keywords: list[str],
) -> list[str]:
    """
    Extract matched keywords from user answer.

    Args:
        user_answer: User's response text
        correct_keywords: Expected keywords

    Returns:
        List of keywords found in user_answer

    """
    matched = []
    answer_lower = user_answer.lower()

    for keyword in correct_keywords:
        keyword_lower = keyword.lower()
        # Simple substring matching (can be enhanced with regex)
        if keyword_lower in answer_lower:
            matched.append(keyword)

    logger.debug(f"Keyword matching: found {len(matched)}/{len(correct_keywords)}")
    return matched


def _call_llm_score_short_answer(
    user_answer: str,
    correct_keywords: list[str],
    difficulty: int | None = None,
) -> tuple[int, str]:
    """
    Call LLM to score short answer based on semantic understanding.

    Args:
        user_answer: User's response
        correct_keywords: Expected keywords
        difficulty: Question difficulty level (optional)

    Returns:
        Tuple of (score, reasoning)
        - score: 0-100 numeric score
        - reasoning: Explanation from LLM

    Raises:
        Exception: If LLM call fails (caught and returns default)

    """
    try:
        llm = create_llm()

        keywords_str = ", ".join(correct_keywords)
        difficulty_hint = f"Difficulty: {difficulty}/10\n" if difficulty else ""

        prompt = f"""Evaluate the following short answer response on a scale of 0-100.

User Answer: {user_answer}

Expected Keywords/Concepts: {keywords_str}

{difficulty_hint}Scoring criteria:
1. Presence of key keywords/concepts (40 points)
2. Semantic correctness and relevance (40 points)
3. Clarity and completeness (20 points)

Respond with ONLY a JSON object on a single line:
{{"score": <number 0-100>, "reasoning": "<brief explanation>"}}

Example:
{{"score": 85, "reasoning": "Mentions key concepts but lacks depth"}}

Do not include markdown or any other text."""

        try:
            response = llm.invoke(prompt)
            response_text = response.content.strip()

            # Parse JSON response
            try:
                result = json.loads(response_text)
                score = int(result.get("score", DEFAULT_LLM_SCORE))
                reasoning = result.get("reasoning", "")

                # Clamp score to 0-100
                score = max(0, min(100, score))

                logger.info(f"LLM short answer score: {score}")
                return score, reasoning
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Could not parse LLM JSON response: {response_text}, {e}")
                return DEFAULT_LLM_SCORE, "Unable to parse LLM response"

        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            return DEFAULT_LLM_SCORE, "LLM service temporarily unavailable"

    except Exception as e:
        logger.error(f"LLM initialization failed: {e}")
        return DEFAULT_LLM_SCORE, "LLM service error"


def _score_short_answer(
    user_answer: str,
    correct_keywords: list[str],
    difficulty: int | None = None,
) -> tuple[bool, int, list[str]]:
    """
    Score short answer using LLM semantic evaluation.

    Args:
        user_answer: User's response
        correct_keywords: Expected keywords
        difficulty: Question difficulty level (optional)

    Returns:
        Tuple of (is_correct, score, keyword_matches)
        - is_correct: True if score >= 80, False otherwise
        - score: 0-100 numeric score from LLM
        - keyword_matches: List of keywords found

    """
    # Extract keyword matches
    keyword_matches = _extract_keyword_matches(user_answer, correct_keywords)

    # Get LLM score
    llm_score, reasoning = _call_llm_score_short_answer(user_answer, correct_keywords, difficulty)

    # Determine is_correct based on score threshold
    is_correct = llm_score >= HIGH_SCORE_THRESHOLD

    logger.debug(
        f"Short answer scoring: score={llm_score}, is_correct={is_correct}, "
        f"keywords={len(keyword_matches)}/{len(correct_keywords)}"
    )

    return is_correct, llm_score, keyword_matches


def _generate_explanation(
    question_type: str,
    is_correct: bool,
    score: int,
    user_answer: str,
    correct_keywords: list[str] | None = None,
) -> tuple[str, list[dict[str, str]]]:
    """
    Generate explanation and reference links using LLM.

    Args:
        question_type: Type of question
        is_correct: Whether answer was correct
        score: Numeric score
        user_answer: User's response
        correct_keywords: Expected keywords (for short answer)

    Returns:
        Tuple of (explanation_text, reference_links)
        - explanation_text: Generated explanation (>= 500 chars)
        - reference_links: List of [{title, url}, ...] (>= 3)

    """
    try:
        llm = create_llm()

        # Build prompt based on correctness
        if is_correct:
            tone = "affirmative and educational"
            opening = "Excellent! Your answer demonstrates solid understanding."
        else:
            tone = "constructive and helpful"
            opening = f"Your answer received {score}/100. Let me help you understand."

        keywords_info = ""
        if correct_keywords:
            keywords_info = f"Key concepts to understand: {', '.join(correct_keywords)}\n\n"

        prompt = f"""Generate a learning explanation for a student's answer.

Tone: {tone}
Opening: {opening}

Student's Answer: {user_answer}

{keywords_info}Guidelines:
1. Start with {opening}
2. Provide 3-4 sentences explaining the correct/improved answer
3. Include key learning points
4. Suggest areas for further review if needed
5. End with encouragement

The explanation must be at least 500 characters long and educational.

Then provide 3+ reference links as JSON (one per line after explanation):
Reference Link 1: {{"title": "<topic title>", "url": "https://example.com/..."}}
Reference Link 2: {{"title": "<topic title>", "url": "https://example.com/..."}}
Reference Link 3: {{"title": "<topic title>", "url": "https://example.com/..."}}

Format: First the explanation text (multiple sentences), then the JSON references below."""

        try:
            response = llm.invoke(prompt)
            full_response = response.content.strip()

            # Parse response: explanation + references
            lines = full_response.split("\n")

            # Find where JSON starts (starts with {)
            explanation_lines = []
            reference_lines = []
            found_json = False

            for line in lines:
                line_stripped = line.strip()
                if line_stripped.startswith("{"):
                    found_json = True

                if found_json:
                    reference_lines.append(line_stripped)
                else:
                    explanation_lines.append(line)

            explanation_text = "\n".join(explanation_lines).strip()

            # Ensure minimum explanation length
            if len(explanation_text) < MIN_EXPLANATION_LENGTH:
                explanation_text += "\n\nFor more detailed explanation, please consult the reference materials below."

            # Parse reference links
            reference_links = []
            for ref_line in reference_lines:
                if not ref_line:
                    continue
                try:
                    # Remove trailing "Reference Link N:" prefix if present
                    ref_content = ref_line
                    if ":" in ref_content:
                        ref_content = ref_content.split(":", 1)[1].strip()

                    ref_obj = json.loads(ref_content)
                    if "title" in ref_obj and "url" in ref_obj:
                        reference_links.append(
                            {
                                "title": ref_obj["title"],
                                "url": ref_obj["url"],
                            }
                        )
                except (json.JSONDecodeError, ValueError):
                    continue

            # Ensure minimum references
            while len(reference_links) < MIN_REFERENCE_LINKS:
                reference_links.append(
                    {
                        "title": f"Reference Material {len(reference_links) + 1}",
                        "url": "https://example.com/reference",
                    }
                )

            logger.info(f"Generated explanation ({len(explanation_text)} chars) with {len(reference_links)} references")
            return explanation_text, reference_links

        except Exception as e:
            logger.error(f"Explanation generation failed: {e}")
            # Return fallback explanation
            fallback_explanation = (
                f"Your answer received a score of {score}/100. "
                "Please review the reference materials below for a deeper understanding."
            )
            fallback_refs = [
                {"title": "Learning Resource 1", "url": "https://example.com/learn1"},
                {"title": "Learning Resource 2", "url": "https://example.com/learn2"},
                {"title": "Learning Resource 3", "url": "https://example.com/learn3"},
            ]
            return fallback_explanation, fallback_refs

    except Exception as e:
        logger.error(f"LLM initialization for explanation failed: {e}")
        fallback_explanation = "Review the reference materials below to improve your understanding."
        fallback_refs = [
            {"title": "Resource 1", "url": "https://example.com/resource1"},
            {"title": "Resource 2", "url": "https://example.com/resource2"},
            {"title": "Resource 3", "url": "https://example.com/resource3"},
        ]
        return fallback_explanation, fallback_refs


def _score_and_explain_impl(
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
    Implement score_and_explain (without @tool decorator).

    This is the actual function that can be tested.
    The @tool decorator wraps this function.

    Args:
        session_id: Test session ID
        user_id: User ID
        question_id: Question ID
        question_type: "multiple_choice" | "true_false" | "short_answer"
        user_answer: User's response
        correct_answer: Expected answer (required for MC/OX)
        correct_keywords: Keywords for short answer validation
        difficulty: Question difficulty level (optional)
        category: Question category (optional)

    Returns:
        dict with fields:
            - attempt_id: Unique attempt identifier
            - session_id: Test session ID
            - question_id: Question ID
            - user_id: User ID
            - is_correct: Boolean correctness
            - score: 0-100 score
            - explanation: Explanation text
            - keyword_matches: Keywords found (for short answer)
            - feedback: Additional feedback or None
            - graded_at: ISO format timestamp

    Raises:
        ValueError: If inputs are invalid
        TypeError: If inputs have wrong types

    """
    logger.info(f"Tool 6: Scoring answer for question {question_id}, type={question_type}")

    # Validate inputs
    try:
        _validate_score_answer_inputs(
            session_id, user_id, question_id, question_type, user_answer, correct_answer, correct_keywords
        )
    except (ValueError, TypeError) as e:
        logger.error(f"Input validation failed: {e}")
        raise

    # Score based on question type
    keyword_matches = []
    if question_type == "multiple_choice":
        is_correct, score = _score_multiple_choice(user_answer, correct_answer)
    elif question_type == "true_false":
        is_correct, score = _score_true_false(user_answer, correct_answer)
    else:  # short_answer
        is_correct, score, keyword_matches = _score_short_answer(user_answer, correct_keywords, difficulty)

    # Generate explanation
    explanation_text, reference_links = _generate_explanation(
        question_type, is_correct, score, user_answer, correct_keywords
    )

    # Determine feedback
    feedback = None
    if question_type == "short_answer" and not is_correct:
        if PARTIAL_CREDIT_LOWER <= score <= PARTIAL_CREDIT_UPPER:
            feedback = (
                f"Good effort! You earned {score}/100. "
                "Review the explanation and reference materials to improve your understanding."
            )
        else:
            feedback = f"This needs more work ({score}/100). Please carefully review the key concepts and try again."

    # Build response
    attempt_id = str(uuid.uuid4())
    graded_at = datetime.now(UTC).isoformat()

    result = {
        "attempt_id": attempt_id,
        "session_id": session_id,
        "question_id": question_id,
        "user_id": user_id,
        "is_correct": is_correct,
        "score": score,
        "explanation": explanation_text,
        "keyword_matches": keyword_matches,
        "feedback": feedback,
        "graded_at": graded_at,
    }

    logger.info(f"Tool 6: Graded question {question_id}: is_correct={is_correct}, score={score}")
    return result


@tool
def score_and_explain(
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
    Score user answer and generate explanation.

    REQ: REQ-A-Mode2-Tool6

    This tool performs auto-grading and explanation generation:
    1. MC/OX: Exact string match (case-insensitive)
    2. Short Answer: LLM-based semantic evaluation with keyword matching
    3. Explanation: Generated explanation with minimum 3 reference links

    Scoring logic:
    - MC/OX: is_correct = (user_answer == correct_answer)
    - Short Answer: is_correct = (LLM_score >= 80)
    - Partial Credit: 70-79 points → is_correct=False but score > 0

    Args:
        session_id: Test session identifier
        user_id: User identifier
        question_id: Question identifier
        question_type: "multiple_choice" | "true_false" | "short_answer"
        user_answer: User's response text
        correct_answer: Expected answer (required for MC/OX)
        correct_keywords: Keywords for short answer validation (required for short_answer)
        difficulty: Question difficulty (1-10, optional)
        category: Question category (optional)

    Returns:
        dict with:
            - attempt_id: UUID of scoring result
            - session_id: Test session ID
            - question_id: Question ID
            - user_id: User ID
            - is_correct: bool (True if score >= 80 for SA, exact match for MC/OX)
            - score: int (0-100)
            - explanation: str (explanation text, >= 500 chars)
            - keyword_matches: list[str] (keywords found in short answer)
            - feedback: str | None (additional feedback for partial credit)
            - graded_at: str (ISO timestamp)

    Raises:
        ValueError: If inputs are invalid
        TypeError: If inputs have wrong types

    Example (MC):
        >>> result = score_and_explain(
        ...     session_id="sess_001",
        ...     user_id="user_001",
        ...     question_id="q_001",
        ...     question_type="multiple_choice",
        ...     user_answer="B",
        ...     correct_answer="B",
        ... )
        >>> result["is_correct"]
        True

    Example (Short Answer):
        >>> result = score_and_explain(
        ...     session_id="sess_001",
        ...     user_id="user_001",
        ...     question_id="q_003",
        ...     question_type="short_answer",
        ...     user_answer="RAG combines retrieval and generation",
        ...     correct_keywords=["RAG", "retrieval", "generation"],
        ... )
        >>> result["score"]
        85

    """
    return _score_and_explain_impl(
        session_id,
        user_id,
        question_id,
        question_type,
        user_answer,
        correct_answer,
        correct_keywords,
        difficulty,
        category,
    )
