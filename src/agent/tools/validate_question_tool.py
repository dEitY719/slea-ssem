"""
Validate Question Quality Tool - Validate AI-generated question quality.

REQ: REQ-A-Mode1-Tool4
Tool 4 for Mode 1 pipeline: Validate generated question quality using LLM + rule-based checks.
"""

import logging
from typing import Any

from langchain_core.tools import tool

from src.agent.config import create_llm

logger = logging.getLogger(__name__)

# Question type constants
QUESTION_TYPES = {"multiple_choice", "true_false", "short_answer"}

# Validation rules
STEM_MAX_LENGTH = 250
MIN_CHOICES = 4
MAX_CHOICES = 5

# Score thresholds
MIN_VALID_SCORE = 0.70
PASS_THRESHOLD = 0.85
REVISE_LOWER_THRESHOLD = 0.70
REVISE_UPPER_THRESHOLD = 0.85

# Default score for LLM failure
DEFAULT_LLM_SCORE = 0.5


def _validate_question_inputs(
    stem: str | list[str],
    question_type: str | list[str],
    choices: list[str] | list[list[str]] | None,
    correct_answer: str | list[str],
) -> None:
    """
    Validate input parameters.

    Args:
        stem: Question stem(s)
        question_type: Question type(s)
        choices: Answer choices
        correct_answer: Correct answer(s)

    Raises:
        TypeError: If inputs have wrong types
        ValueError: If inputs have invalid values

    """
    # Handle single vs batch
    if isinstance(stem, str):
        stems = [stem]
        types = [question_type] if isinstance(question_type, str) else question_type
        answers = [correct_answer] if isinstance(correct_answer, str) else correct_answer
    else:
        stems = stem
        types = question_type
        answers = correct_answer

    # Validate each stem
    for s in stems:
        if not isinstance(s, str):
            raise TypeError(f"stem must be string, got {type(s)}")
        if not s or not s.strip():
            raise ValueError("stem cannot be empty")

    # Validate each question type
    for qt in types:
        if not isinstance(qt, str):
            raise TypeError(f"question_type must be string, got {type(qt)}")
        if qt not in QUESTION_TYPES:
            raise ValueError(f"question_type must be one of {QUESTION_TYPES}, got {qt}")

    # Validate choices and answers
    for i, (qt, ans) in enumerate(zip(types, answers, strict=True)):
        if not isinstance(ans, str):
            raise TypeError(f"correct_answer must be string, got {type(ans)}")
        if not ans or not ans.strip():
            raise ValueError("correct_answer cannot be empty")

        if qt == "multiple_choice":
            if choices is None or (isinstance(choices, list) and not choices[i]):
                raise ValueError(f"choices required for multiple_choice type at index {i}")


def _check_rule_based_quality(
    stem: str,
    question_type: str,
    choices: list[str] | None,
    correct_answer: str,
) -> tuple[float, list[str]]:
    """
    Perform rule-based quality validation.

    Args:
        stem: Question stem
        question_type: Question type
        choices: Answer choices (for multiple_choice)
        correct_answer: Correct answer

    Returns:
        Tuple of (score, issues_list)
        - score: 0.0-1.0 rule-based score
        - issues_list: List of detected issues

    """
    issues = []
    score = 1.0

    # Rule 1: Stem length check
    if len(stem) > STEM_MAX_LENGTH:
        issues.append(f"Stem length exceeds maximum ({len(stem)} > {STEM_MAX_LENGTH} chars)")
        score -= 0.2

    # Rule 2: Multiple choice validation
    if question_type == "multiple_choice":
        if not choices or len(choices) < MIN_CHOICES or len(choices) > MAX_CHOICES:
            issues.append(
                f"Invalid number of choices: {len(choices) if choices else 0} (must be {MIN_CHOICES}-{MAX_CHOICES})"
            )
            score -= 0.2

        # Rule 3: Answer in choices
        if choices and correct_answer not in choices:
            issues.append(f"Correct answer '{correct_answer}' not found in choices")
            score -= 0.3

        # Rule 4: No duplicate choices (only check if all items are strings)
        if choices and all(isinstance(c, str) for c in choices):
            if len(choices) != len(set(choices)):
                issues.append("Duplicate choices detected")
                score -= 0.15

    # Ensure score stays in valid range
    score = max(0.0, min(1.0, score))

    return score, issues


def _call_llm_validation(
    stem: str,
    question_type: str,
    choices: list[str] | None,
    correct_answer: str,
) -> float:
    """
    Call LLM to validate semantic quality of question.

    Args:
        stem: Question stem
        question_type: Question type
        choices: Answer choices
        correct_answer: Correct answer

    Returns:
        LLM quality score (0.0-1.0)

    Raises:
        Exception: If LLM call fails (caught and returns default)

    """
    try:
        llm = create_llm()

        # Build prompt for LLM validation
        if choices:
            choices_str = "\n".join(f"- {c}" for c in choices)
        else:
            choices_str = "N/A"

        prompt = f"""Evaluate the quality of this question on a scale of 0.0 to 1.0.

Question Stem: {stem}
Question Type: {question_type}
Choices: {choices_str}
Correct Answer: {correct_answer}

Consider these criteria:
1. Clarity: Is the question clear and unambiguous?
2. Appropriateness: Is the difficulty level appropriate?
3. Correctness: Is the correct answer objective and verifiable?
4. Bias: Are there any biases or inappropriate language?
5. Format: Is the format valid and properly structured?

Respond with ONLY a number between 0.0 and 1.0, like: 0.85

Do not include any explanation, just the score."""

        try:
            response = llm.invoke(prompt)
            score_text = response.content.strip()

            # Parse score from response
            score = float(score_text)
            score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
            logger.info(f"LLM validation score: {score}")
            return score
        except ValueError:
            logger.warning(f"Could not parse LLM response as float: {score_text}")
            return DEFAULT_LLM_SCORE

    except Exception as e:
        logger.error(f"LLM validation failed: {e}")
        return DEFAULT_LLM_SCORE


def _get_recommendation(final_score: float) -> str:
    """
    Determine recommendation based on final score.

    Args:
        final_score: Final validation score (0.0-1.0)

    Returns:
        "pass" | "revise" | "reject"

    """
    if final_score >= PASS_THRESHOLD:
        return "pass"
    elif final_score >= REVISE_LOWER_THRESHOLD:
        return "revise"
    else:
        return "reject"


def _should_discard_question(final_score: float, recommendation: str) -> bool:
    """
    Determine if question should be discarded.

    REQ: REQ-A-Mode1-Tool4-Discard (should_discard logic)

    Question should be discarded if:
    1. Final score < MIN_VALID_SCORE (0.70), OR
    2. Recommendation is "reject"

    A question is only valid and kept if:
    - final_score >= 0.70 AND recommendation != "reject"

    Args:
        final_score: Final validation score (0.0-1.0)
        recommendation: Recommendation string ("pass"|"revise"|"reject")

    Returns:
        True if question should be discarded, False if should be kept

    """
    # Discard if score is below threshold
    if final_score < MIN_VALID_SCORE:
        return True

    # Discard if recommendation is reject
    if recommendation == "reject":
        return True

    # Otherwise keep the question
    return False


def _build_feedback(
    score: float,
    rule_score: float,
    issues: list[str],
    recommendation: str,
) -> str:
    """
    Build human-readable feedback.

    Args:
        score: LLM semantic score
        rule_score: Rule-based score
        issues: List of issues found
        recommendation: Recommendation (pass/revise/reject)

    Returns:
        Feedback string

    """
    feedback_parts = []

    if recommendation == "pass":
        feedback_parts.append("질문이 우수한 품질입니다. 즉시 저장할 수 있습니다.")
    elif recommendation == "revise":
        feedback_parts.append("질문이 기본 기준을 충족하지만 개선이 가능합니다. 피드백을 바탕으로 재생성을 권장합니다.")
    else:  # reject
        feedback_parts.append("질문이 기준을 충족하지 않습니다. 새로운 질문 생성을 권장합니다.")

    if issues:
        feedback_parts.append("\n발견된 문제점:\n" + "\n".join(f"- {issue}" for issue in issues))

    feedback_parts.append(f"\n점수: LLM {score:.2f} / 규칙 {rule_score:.2f}")

    return "".join(feedback_parts)


def _validate_question_quality_impl(
    stem: str | list[str],
    question_type: str | list[str],
    choices: list[str] | list[list[str]] | None = None,
    correct_answer: str | list[str] = None,
    batch: bool = False,
) -> dict[str, Any] | list[dict[str, Any]]:
    """
    Implement validate_question_quality (without @tool decorator).

    This is the actual function that can be tested.
    The @tool decorator wraps this function.

    Args:
        stem: Question stem(s)
        question_type: Question type(s)
        choices: Answer choices (for multiple_choice)
        correct_answer: Correct answer(s)
        batch: If True, process multiple questions at once

    Returns:
        dict or list[dict]: Validation result(s) with fields:
            - is_valid: bool (final_score >= 0.70)
            - score: float (LLM semantic score 0-1)
            - rule_score: float (rule-based score 0-1)
            - final_score: float (min of score and rule_score)
            - feedback: str (human-readable feedback)
            - issues: list[str] (detected problems)
            - recommendation: "pass" | "revise" | "reject"

    Raises:
        ValueError: If inputs are invalid
        TypeError: If inputs have wrong types

    """
    logger.info(f"Tool 4: Validating question quality (batch={batch})")

    # Validate inputs
    try:
        _validate_question_inputs(stem, question_type, choices, correct_answer)
    except (ValueError, TypeError) as e:
        logger.error(f"Input validation failed: {e}")
        raise

    # Handle batch vs single
    if batch or isinstance(stem, list):
        # Batch validation
        stems = stem if isinstance(stem, list) else [stem]
        types = question_type if isinstance(question_type, list) else [question_type]
        answers = correct_answer if isinstance(correct_answer, list) else [correct_answer]

        # Handle choices - could be list of lists or single list or None
        if choices is None:
            all_choices = [None] * len(stems)
        elif isinstance(choices, list) and choices and isinstance(choices[0], list):
            # Already list of lists for batch
            all_choices = choices
        elif isinstance(choices, list) and choices and isinstance(choices[0], str):
            # Single list - apply to all
            all_choices = [choices] * len(stems)
        else:
            all_choices = [None] * len(stems)

        results = []
        for s, qt, c, ans in zip(stems, types, all_choices, answers, strict=True):
            result = _validate_single_question(s, qt, c, ans)
            results.append(result)

        logger.info(f"Batch validation completed: {len(results)} questions")
        return results
    else:
        # Single validation
        result = _validate_single_question(stem, question_type, choices, correct_answer)
        logger.info("Single question validation completed")
        return result


def _validate_single_question(
    stem: str,
    question_type: str,
    choices: list[str] | None,
    correct_answer: str,
) -> dict[str, Any]:
    """
    Validate a single question.

    Args:
        stem: Question stem
        question_type: Question type
        choices: Answer choices
        correct_answer: Correct answer

    Returns:
        Validation result dict with:
            - is_valid: bool (True if final_score >= 0.70)
            - score: float (LLM semantic score)
            - rule_score: float (rule-based score)
            - final_score: float (min of score and rule_score)
            - feedback: str (human-readable feedback)
            - issues: list[str] (detected problems)
            - recommendation: "pass"|"revise"|"reject"
            - should_discard: bool (True if should regenerate, False if should keep)

    """
    # Rule-based validation
    rule_score, issues = _check_rule_based_quality(stem, question_type, choices, correct_answer)

    # LLM semantic validation
    llm_score = _call_llm_validation(stem, question_type, choices, correct_answer)

    # Final score is minimum of LLM and rule scores
    final_score = min(llm_score, rule_score)

    # Determine recommendation
    recommendation = _get_recommendation(final_score)

    # Determine is_valid
    is_valid = final_score >= MIN_VALID_SCORE

    # Determine should_discard (opposite of is_valid)
    should_discard = _should_discard_question(final_score, recommendation)

    # Build feedback
    feedback = _build_feedback(llm_score, rule_score, issues, recommendation)

    logger.debug(
        f"Question validation: final_score={final_score:.2f}, "
        f"is_valid={is_valid}, should_discard={should_discard}, "
        f"recommendation={recommendation}"
    )

    return {
        "is_valid": is_valid,
        "score": llm_score,
        "rule_score": rule_score,
        "final_score": final_score,
        "feedback": feedback,
        "issues": issues,
        "recommendation": recommendation,
        "should_discard": should_discard,
    }


@tool
def validate_question_quality(
    stem: str,
    question_type: str,
    choices: list[str] | None = None,
    correct_answer: str | None = None,
) -> dict[str, Any]:
    """
    Validate the quality of an AI-generated question.

    REQ: REQ-A-Mode1-Tool4

    This tool performs 2-stage validation:
    1. LLM-based semantic validation (clarity, appropriateness, correctness, bias)
    2. Rule-based validation (length, choices count, format, duplicates)

    Final score = min(LLM_score, rule_score)
    should_discard = (final_score < 0.70) OR (recommendation == "reject")

    Args:
        stem: Question stem text (max 250 chars)
        question_type: "multiple_choice" | "true_false" | "short_answer"
        choices: Answer choices for multiple_choice (4-5 items) or None for other types
        correct_answer: Correct answer text

    Returns:
        dict with:
            - is_valid: bool (True if final_score >= 0.70)
            - score: float (LLM semantic score, 0.0-1.0)
            - rule_score: float (rule-based score, 0.0-1.0)
            - final_score: float (min of score and rule_score)
            - feedback: str (human-readable feedback in Korean)
            - issues: list[str] (detected problems)
            - recommendation: "pass" (>=0.85) | "revise" (0.70-0.85) | "reject" (<0.70)
            - should_discard: bool (True if should regenerate, False if should keep)

    Raises:
        ValueError: If inputs are invalid
        TypeError: If inputs have wrong types

    Example:
        >>> result = validate_question_quality(
        ...     stem="What is RAG?",
        ...     question_type="multiple_choice",
        ...     choices=["A", "B", "C", "D"],
        ...     correct_answer="B"
        ... )
        >>> result["recommendation"]
        "pass"
        >>> result["should_discard"]
        False

    """
    return _validate_question_quality_impl(stem, question_type, choices, correct_answer, False)
