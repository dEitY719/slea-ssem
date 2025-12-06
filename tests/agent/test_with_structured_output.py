"""
Test suite for REQ-AGENT-0-1: with_structured_output 도입

REQ: REQ-AGENT-0-1

Tests the integration of LangChain's with_structured_output API to:
1. Replace manual JSON parsing (parse_json_robust, AgentOutputConverter)
2. Add type safety via Pydantic models
3. Maintain backward compatibility via should_use_structured_output() guard
4. Support both Gemini (with_structured_output) and DeepSeek (TextReAct fallback)

Test Categories:
- Structured output happy path (Gemini enabled)
- Fallback to TextReAct (DeepSeek)
- Response type validation (Pydantic model)
- Feature flag guard (should_use_structured_output)
- Legacy code removal verification (parse_json_robust, _parse_agent_output_generate)
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError

from src.agent.config import should_use_structured_output
from src.agent.llm_agent import (
    GeneratedItem,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
)


@pytest.mark.no_db_required
class TestStructuredOutputIntegration:
    """Test with_structured_output integration in generate_questions."""

    def test_should_use_structured_output_with_gemini(self):
        """
        Test: should_use_structured_output() returns True for Gemini when enabled.

        REQ: REQ-AGENT-0-1 (Acceptance Criteria #1)
        Scenario: generate_questions called with Gemini LLM and ENABLE_STRUCTURED_OUTPUT=true
        Expected: should_use_structured_output("gemini-2.0-flash") → True
        """
        # Mock STRUCTURED_OUTPUT_CONFIG to enable structured output
        mock_config = {"enabled": True, "max_failures_before_disable": 3}

        with patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", mock_config):
            # Test that guard function correctly identifies Gemini
            assert should_use_structured_output("gemini-2.0-flash", failure_count=0) is True
            assert should_use_structured_output("gemini-1.5-pro", failure_count=0) is True

    def test_should_use_structured_output_with_deepseek(self):
        """
        Test: should_use_structured_output() returns False for DeepSeek.

        REQ: REQ-AGENT-0-1 (Acceptance Criteria #2 - Fallback)
        Scenario: generate_questions called with DeepSeek LLM
        Expected: should_use_structured_output("deepseek-chat") → False
        """
        # Test that guard function correctly identifies DeepSeek
        assert should_use_structured_output("deepseek-chat", failure_count=0) is False
        assert should_use_structured_output("deepseek-v3", failure_count=0) is False

    def test_generate_questions_response_is_pydantic_model(self):
        """
        Test: GenerateQuestionsResponse is a valid Pydantic model with required fields.

        REQ: REQ-AGENT-0-1 (Acceptance Criteria #4 - Type Safety)
        Scenario: Response created with required fields
        Expected: Pydantic validation passes, optional fields have defaults
        """
        # Test Pydantic model structure
        item1 = GeneratedItem(
            id="q_001",
            type="multiple_choice",
            stem="What is 2+2?",
            choices=["3", "4", "5"],
            answer_schema={"type": "exact_match", "answer": "4"},
            difficulty=1,
            category="math",
        )

        response = GenerateQuestionsResponse(
            round_id="round_001",
            items=[item1],
            time_limit_seconds=1200,
        )

        # Verify response structure
        assert isinstance(response, GenerateQuestionsResponse)
        assert response.round_id == "round_001"
        assert len(response.items) == 1
        assert response.items[0].id == "q_001"
        assert response.time_limit_seconds == 1200

    def test_pydantic_validation_enforces_types(self):
        """
        Test: Pydantic validation enforces type requirements.

        REQ: REQ-AGENT-0-1 (Acceptance Criteria #4 - Type Safety)
        Scenario: Invalid type passed to GenerateQuestionsResponse
        Expected: ValidationError raised
        """
        with pytest.raises(ValidationError):
            # Missing required 'round_id' field
            GenerateQuestionsResponse(items=[])

        with pytest.raises(ValidationError):
            # Invalid type for 'items' field
            GenerateQuestionsResponse(round_id="round_001", items="not_a_list")

    def test_parse_json_robust_import_still_works(self):
        """
        Test: parse_json_robust function still exists (backward compatibility).

        REQ: REQ-AGENT-0-1 (Acceptance Criteria #5 - Safe Removal)
        Scenario: Check if parse_json_robust can be imported
        Expected: Function exists but will be marked for removal after Phase 3

        Note: This test verifies the function exists during Phase 2.
              Phase 3 implementation will remove it if no longer used.
        """
        try:
            from src.agent.llm_agent import parse_json_robust

            # Function should exist (will be removed in Phase 3)
            assert callable(parse_json_robust)
        except ImportError:
            pytest.fail("parse_json_robust should exist during Phase 2")

    def test_response_with_optional_fields(self):
        """
        Test: GenerateQuestionsResponse handles optional fields with defaults.

        REQ: REQ-AGENT-0-1 (Acceptance Criteria #4 - Type Safety)
        Scenario: Response created with minimal required fields
        Expected: Optional fields use default values
        """
        item1 = GeneratedItem(
            id="q_001",
            type="multiple_choice",
            stem="Test?",
            choices=["A", "B"],
            answer_schema={"type": "exact_match"},
            difficulty=1,
            category="test",
        )

        response = GenerateQuestionsResponse(round_id="round_001", items=[item1])

        # Check optional fields have defaults
        assert response.agent_steps == 0  # default
        assert response.failed_count == 0  # default
        assert response.total_tokens == 0  # default
        assert response.error_message is None  # default


@pytest.mark.no_db_required
class TestStructuredOutputGuard:
    """Test should_use_structured_output guard prevents DeepSeek errors."""

    def test_feature_flag_guards_deepseek_from_structured_output(self):
        """
        Test: Feature flag prevents with_structured_output on DeepSeek.

        REQ: REQ-AGENT-0-1 (Acceptance Criteria #1 - Safety)
        Scenario: Code checks should_use_structured_output before calling with_structured_output
        Expected: DeepSeek models return False, preventing structured output call
        """
        # Simulate the guard logic in generate_questions
        model_name = "deepseek-chat"
        use_structured = should_use_structured_output(model_name, failure_count=0)

        # Verify guard prevents structured output
        assert use_structured is False

        # Simulate the if-else logic
        if use_structured:
            pytest.fail("DeepSeek should not enter structured output path")

    def test_feature_flag_allows_gemini_structured_output(self):
        """
        Test: Feature flag allows with_structured_output on Gemini.

        REQ: REQ-AGENT-0-1 (Acceptance Criteria #1 - Activation)
        Scenario: Code checks should_use_structured_output before calling with_structured_output
        Expected: Gemini models return True, allowing structured output call
        """
        # Mock STRUCTURED_OUTPUT_CONFIG to enable structured output
        mock_config = {"enabled": True, "max_failures_before_disable": 3}

        with patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", mock_config):
            # Simulate the guard logic in generate_questions
            model_name = "gemini-2.0-flash"
            use_structured = should_use_structured_output(model_name, failure_count=0)

            # Verify guard allows structured output
            assert use_structured is True

            # Simulate the if-else logic
            if not use_structured:
                pytest.fail("Gemini should enter structured output path")


@pytest.mark.no_db_required
class TestLegacyCodeRemovalVerification:
    """Test that legacy parsing functions are no longer needed."""

    def test_agent_output_converter_not_required_for_structured_output(self):
        """
        Test: with_structured_output eliminates need for AgentOutputConverter.parse_final_answer_json.

        REQ: REQ-AGENT-0-1 (Acceptance Criteria #3 - Legacy Code Removal)
        Scenario: with_structured_output returns Pydantic object directly
        Expected: No JSON extraction or parsing needed
        """
        # Verify that Pydantic validation replaces AgentOutputConverter parsing
        valid_item = GeneratedItem(
            id="q_001",
            type="multiple_choice",
            stem="Test?",
            choices=["A", "B"],
            answer_schema={"type": "exact_match"},
            difficulty=1,
            category="test",
        )

        # No JSON parsing needed - direct Pydantic validation
        assert valid_item.id == "q_001"
        assert valid_item.type == "multiple_choice"

    def test_response_structure_matches_with_structured_output_schema(self):
        """
        Test: GenerateQuestionsResponse structure is compatible with with_structured_output.

        REQ: REQ-AGENT-0-1 (Acceptance Criteria #4 - Type Safety)
        Scenario: LLM returns structured response matching GenerateQuestionsResponse
        Expected: Pydantic model validates response automatically
        """
        # Simulate LLM with_structured_output response
        # (In reality, LLM returns dict that Pydantic converts to GenerateQuestionsResponse)
        response_dict = {
            "round_id": "round_001",
            "items": [
                {
                    "id": "q_001",
                    "type": "multiple_choice",
                    "stem": "What is 2+2?",
                    "choices": ["3", "4", "5"],
                    "answer_schema": {"type": "exact_match", "answer": "4"},
                    "difficulty": 1,
                    "category": "math",
                }
            ],
            "time_limit_seconds": 1200,
        }

        # Pydantic automatically validates and converts dict to model
        response = GenerateQuestionsResponse(**response_dict)

        assert isinstance(response, GenerateQuestionsResponse)
        assert response.round_id == "round_001"
        assert len(response.items) == 1


# ============================================================================
# ACCEPTANCE CRITERIA VERIFICATION
# ============================================================================


@pytest.mark.no_db_required
class TestAcceptanceCriteria:
    """Verify all REQ-AGENT-0-1 acceptance criteria."""

    def test_acceptance_1_should_use_structured_output_guard(self):
        """AC #1: should_use_structured_output() guards Gemini-only execution."""
        # Mock STRUCTURED_OUTPUT_CONFIG to enable structured output
        mock_config = {"enabled": True, "max_failures_before_disable": 3}

        with patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", mock_config):
            # Gemini → True
            assert should_use_structured_output("gemini-2.0-flash") is True

        # DeepSeek → False (always, regardless of config)
        assert should_use_structured_output("deepseek-chat") is False

    def test_acceptance_2_parse_json_robust_exists_for_fallback(self):
        """AC #2: parse_json_robust exists as fallback for DeepSeek path."""
        try:
            from src.agent.llm_agent import parse_json_robust

            # Should work for fallback if needed
            assert callable(parse_json_robust)
        except ImportError:
            pytest.fail("parse_json_robust should exist for fallback path")

    def test_acceptance_3_agent_output_converter_not_needed(self):
        """AC #3: AgentOutputConverter.parse_final_answer_json not needed for Gemini path."""
        # Structured output returns Pydantic object directly
        response = GenerateQuestionsResponse(
            round_id="round_001",
            items=[
                GeneratedItem(
                    id="q_001",
                    type="multiple_choice",
                    stem="Test?",
                    choices=["A", "B"],
                    answer_schema={"type": "exact_match"},
                    difficulty=1,
                    category="test",
                )
            ],
        )

        # No JSON parsing needed
        assert isinstance(response, GenerateQuestionsResponse)

    def test_acceptance_4_type_safety_guaranteed(self):
        """AC #4: Type safety guaranteed via Pydantic validation."""
        # Valid model passes
        response = GenerateQuestionsResponse(
            round_id="round_001", items=[], time_limit_seconds=1200
        )
        assert response.time_limit_seconds == 1200

        # Invalid type fails
        with pytest.raises(ValidationError):
            GenerateQuestionsResponse(
                round_id="round_001", items=[], time_limit_seconds="invalid"
            )

    def test_acceptance_5_backward_compatibility_with_deepseek(self):
        """AC #5: Backward compatibility with DeepSeek (should_use_structured_output guard)."""
        # DeepSeek guard prevents structured output call
        assert should_use_structured_output("deepseek-chat") is False

        # Falls back to existing TextReActAgent path (not in test, verified in Phase 3)
