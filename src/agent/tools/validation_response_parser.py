"""
Validation Response Parser - Parse and handle Tool 4 (validate_question_quality) responses.

REQ: REQ-A-Mode1-Tool4-Parser

Handles:
1. Parsing validation responses (single & batch)
2. Detecting and handling contradictory responses
3. Fallback parsing when responses are malformed
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Score thresholds (must match validate_question_tool.py)
MIN_VALID_SCORE = 0.70
PASS_THRESHOLD = 0.85
REVISE_LOWER_THRESHOLD = 0.70


class ValidationResponseParser:
    """
    Parse and validate Tool 4 (validate_question_quality) responses.

    Handles:
    - Single vs batch responses
    - Contradictory response detection (should_discard=true but score>=0.7)
    - Default values for missing fields
    - Type conversions
    """

    @staticmethod
    def parse_response(
        response: dict[str, Any] | list[dict[str, Any]],
        batch: bool = False,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Parse Tool 4 validation response with contradiction handling.

        Args:
            response: Raw Tool 4 response (single dict or list of dicts)
            batch: True if batch response expected

        Returns:
            Parsed response with resolved contradictions

        Raises:
            ValueError: If response format is invalid

        """
        if batch or isinstance(response, list):
            return ValidationResponseParser._parse_batch_response(response)
        else:
            return ValidationResponseParser._parse_single_response(response)

    @staticmethod
    def _parse_single_response(response: dict[str, Any]) -> dict[str, Any]:
        """
        Parse single question validation response.

        Handles:
        - Missing fields (uses defaults)
        - Contradictory should_discard flag
        - Type conversions

        Args:
            response: Single validation response dict

        Returns:
            Parsed response with normalized fields

        Raises:
            ValueError: If response is missing critical fields

        """
        # Extract and validate critical fields
        final_score = float(response.get("final_score", 0.0))
        recommendation = str(response.get("recommendation", "reject")).lower()
        should_discard_raw = response.get("should_discard", None)

        # Determine should_discard based on score and recommendation
        # (in case of contradiction)
        should_discard = ValidationResponseParser._resolve_should_discard(
            final_score, recommendation, should_discard_raw
        )

        # Build normalized response
        parsed = {
            "is_valid": response.get("is_valid", final_score >= MIN_VALID_SCORE),
            "score": float(response.get("score", 0.0)),
            "rule_score": float(response.get("rule_score", 0.0)),
            "final_score": final_score,
            "feedback": str(response.get("feedback", "")),
            "issues": response.get("issues", []),
            "recommendation": recommendation,
            "should_discard": should_discard,
        }

        logger.debug(f"Parsed validation response: {parsed}")
        return parsed

    @staticmethod
    def _parse_batch_response(
        responses: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Parse batch validation responses.

        Args:
            responses: List of validation response dicts

        Returns:
            List of parsed responses

        """
        parsed_list = []
        for i, response in enumerate(responses):
            try:
                parsed = ValidationResponseParser._parse_single_response(response)
                parsed_list.append(parsed)
            except (ValueError, KeyError) as e:
                logger.error(f"Error parsing response {i}: {e}")
                # Add default failed response
                parsed_list.append(ValidationResponseParser._default_failed_response())

        logger.debug(f"Parsed {len(parsed_list)} batch responses")
        return parsed_list

    @staticmethod
    def _resolve_should_discard(
        final_score: float,
        recommendation: str,
        should_discard_raw: Any,  # noqa: ANN401
    ) -> bool:
        """
        Resolve should_discard flag, handling contradictions.

        Contradiction scenarios:
        1. should_discard=true but final_score >= 0.7 → CONTRADICTION
           Resolution: Check recommendation
           - If recommendation="pass" → should_discard=False (keep)
           - If recommendation="revise" → should_discard=False (keep)
           - If recommendation="reject" → should_discard=True (discard)

        2. should_discard=false but final_score < 0.7 → CONTRADICTION
           Resolution: Check recommendation
           - If recommendation="reject" → should_discard=True (discard)
           - Else → should_discard=False (keep)

        Args:
            final_score: Final validation score (0.0-1.0)
            recommendation: Recommendation string
            should_discard_raw: Raw should_discard value from response

        Returns:
            Resolved should_discard boolean

        """
        # If should_discard_raw is None, derive from score and recommendation
        if should_discard_raw is None:
            return final_score < MIN_VALID_SCORE or recommendation == "reject"

        should_discard_bool = bool(should_discard_raw)

        # Detect contradictions
        is_contradictory = False
        if should_discard_bool and final_score >= MIN_VALID_SCORE:
            # Contradiction: should_discard=true but score >= 0.7
            is_contradictory = True
            logger.warning(
                f"Contradictory validation: should_discard=true but "
                f"final_score={final_score:.2f} >= {MIN_VALID_SCORE}. "
                f"Recommendation: {recommendation}"
            )

        if not should_discard_bool and final_score < MIN_VALID_SCORE:
            # Contradiction: should_discard=false but score < 0.7
            is_contradictory = True
            logger.warning(
                f"Contradictory validation: should_discard=false but "
                f"final_score={final_score:.2f} < {MIN_VALID_SCORE}. "
                f"Using score-based decision."
            )

        # Resolve contradictions
        if is_contradictory:
            # Priority order: recommendation > score
            if recommendation == "reject":
                return True
            elif recommendation in ("pass", "revise"):
                return False
            else:
                # Fallback: use score
                return final_score < MIN_VALID_SCORE

        return should_discard_bool

    @staticmethod
    def _default_failed_response() -> dict[str, Any]:
        """
        Create default failed response (for parsing errors).

        Returns:
            Default response with score=0.0, should_discard=True

        """
        return {
            "is_valid": False,
            "score": 0.0,
            "rule_score": 0.0,
            "final_score": 0.0,
            "feedback": "Validation error - default rejection",
            "issues": ["Parsing error in validation response"],
            "recommendation": "reject",
            "should_discard": True,
        }

    @staticmethod
    def validate_response_structure(response: dict[str, Any]) -> bool:
        """
        Validate response structure against expected schema.

        Args:
            response: Response dict to validate

        Returns:
            True if structure is valid

        """
        required_fields = ["is_valid", "score", "rule_score", "final_score", "recommendation"]
        for field in required_fields:
            if field not in response:
                logger.error(f"Missing required field: {field}")
                return False

        return True
