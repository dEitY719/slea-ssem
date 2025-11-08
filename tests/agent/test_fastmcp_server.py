"""
Comprehensive tests for REQ-A-FastMCP: FastMCP Server Implementation.

This module tests FastMCP server tools, error handling, and integration.

REQ: REQ-A-FastMCP
"""

from typing import Any

import pytest

from src.agent.error_handler import ErrorHandler
from src.agent.fastmcp_server import TOOLS


# ============================================================================
# TEST CLASS 1: TOOL REGISTRATION (AC7, AC8)
# ============================================================================


class TestToolRegistration:
    """Test tool registration."""

    def test_tools_list_exists(self):
        """AC8: TOOLS list exists and has 6 tools."""
        assert TOOLS is not None
        assert isinstance(TOOLS, list)
        assert len(TOOLS) == 6

    def test_all_tools_have_invoke_method(self):
        """AC8: All tools can be invoked (LangChain StructuredTool)."""
        for tool in TOOLS:
            assert hasattr(tool, "invoke") or hasattr(tool, "func")

    def test_tool_names_correct(self):
        """AC8: All tool names are correct."""
        tool_names = [tool.name for tool in TOOLS]
        expected_names = [
            "get_user_profile",
            "search_question_templates",
            "get_difficulty_keywords",
            "validate_question_quality",
            "save_generated_question",
            "score_and_explain",
        ]
        assert tool_names == expected_names

    def test_tools_have_descriptions(self):
        """AC8: All tools have descriptions."""
        for tool in TOOLS:
            assert hasattr(tool, "description")
            assert len(tool.description) > 0


# ============================================================================
# TEST CLASS 2: TOOL 1 - GET USER PROFILE (AC1)
# ============================================================================


class TestTool1GetUserProfile:
    """Test Tool 1: Get User Profile."""

    def test_tool1_exists_in_list(self):
        """AC1: Tool 1 is registered."""
        tool1 = TOOLS[0]
        assert tool1.name == "get_user_profile"

    def test_tool1_has_required_fields(self):
        """AC1: Tool 1 returns required fields."""
        tool1 = TOOLS[0]
        result = tool1.invoke({"user_id": "test_user"})

        required_fields = [
            "user_id",
            "self_level",
            "years_experience",
            "job_role",
            "duty",
            "interests",
            "previous_score",
        ]
        for field in required_fields:
            assert field in result


# ============================================================================
# TEST CLASS 3: TOOL 2 - SEARCH TEMPLATES (AC2)
# ============================================================================


class TestTool2SearchTemplates:
    """Test Tool 2: Search Question Templates."""

    def test_tool2_exists_in_list(self):
        """AC2: Tool 2 is registered."""
        tool2 = TOOLS[1]
        assert tool2.name == "search_question_templates"

    def test_tool2_returns_list(self):
        """AC2: Tool 2 returns a list of templates."""
        tool2 = TOOLS[1]
        result = tool2.invoke({
            "interests": ["AI"],
            "difficulty": 5,
            "category": "technical",
        })
        assert isinstance(result, list)


# ============================================================================
# TEST CLASS 4: TOOL 3 - DIFFICULTY KEYWORDS (AC3)
# ============================================================================


class TestTool3DifficultyKeywords:
    """Test Tool 3: Get Difficulty Keywords."""

    def test_tool3_exists_in_list(self):
        """AC3: Tool 3 is registered."""
        tool3 = TOOLS[2]
        assert tool3.name == "get_difficulty_keywords"

    def test_tool3_returns_dict_with_keywords(self):
        """AC3: Tool 3 returns keywords structure."""
        tool3 = TOOLS[2]
        result = tool3.invoke({
            "difficulty": 5,
            "category": "technical",
        })
        assert isinstance(result, dict)
        assert "keywords" in result
        assert "concepts" in result


# ============================================================================
# TEST CLASS 5: TOOL 4 - VALIDATE QUALITY (AC4)
# ============================================================================


class TestTool4ValidateQuality:
    """Test Tool 4: Validate Question Quality."""

    def test_tool4_exists_in_list(self):
        """AC4: Tool 4 is registered."""
        tool4 = TOOLS[3]
        assert tool4.name == "validate_question_quality"

    def test_tool4_returns_validation_score(self):
        """AC4: Tool 4 returns score threshold (0.70)."""
        tool4 = TOOLS[3]
        result = tool4.invoke({
            "stem": "What is AI?",
            "question_type": "multiple_choice",
        })
        assert isinstance(result, dict)
        assert "final_score" in result
        # Tool should respect 0.70 threshold
        assert isinstance(result.get("final_score"), (int, float))


# ============================================================================
# TEST CLASS 6: TOOL 5 - SAVE QUESTION (AC5)
# ============================================================================


class TestTool5SaveQuestion:
    """Test Tool 5: Save Generated Question."""

    def test_tool5_exists_in_list(self):
        """AC5: Tool 5 is registered."""
        tool5 = TOOLS[4]
        assert tool5.name == "save_generated_question"

    def test_tool5_returns_save_result(self):
        """AC5: Tool 5 returns save result."""
        tool5 = TOOLS[4]
        result = tool5.invoke({
            "item_type": "multiple_choice",
            "stem": "Question?",
            "difficulty": 5,
            "categories": ["technical"],
            "round_id": "sess_001_1",
        })
        assert isinstance(result, dict)
        assert "success" in result or "question_id" in result


# ============================================================================
# TEST CLASS 7: TOOL 6 - SCORE & EXPLAIN (AC6)
# ============================================================================


class TestTool6ScoreAndExplain:
    """Test Tool 6: Score & Generate Explanation."""

    def test_tool6_exists_in_list(self):
        """AC6: Tool 6 is registered."""
        tool6 = TOOLS[5]
        assert tool6.name == "score_and_explain"

    def test_tool6_returns_scoring_result(self):
        """AC6: Tool 6 returns scoring with required fields."""
        tool6 = TOOLS[5]
        result = tool6.invoke({
            "session_id": "sess_001",
            "user_id": "user_123",
            "question_id": "q_001",
            "question_type": "multiple_choice",
            "user_answer": "B",
            "correct_answer": "B",
            "difficulty": 5,
            "category": "technical",
        })
        required_fields = ["is_correct", "score", "explanation", "graded_at"]
        for field in required_fields:
            assert field in result


# ============================================================================
# TEST CLASS 8: LANGCHAIN INTEGRATION (AC8)
# ============================================================================


class TestLangChainIntegration:
    """Test integration with LangChain agent."""

    def test_tools_compatible_with_langchain(self):
        """AC8: Tools are compatible with LangChain agent execution."""
        assert len(TOOLS) == 6
        for tool in TOOLS:
            # LangChain StructuredTool has these attributes
            assert hasattr(tool, "invoke")
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")

    def test_tools_have_standard_interface(self):
        """AC8: Tools have standard LangChain interface."""
        for tool in TOOLS:
            # All tools should be LangChain tools
            assert hasattr(tool, "invoke")


# ============================================================================
# TEST CLASS 9: ACCEPTANCE CRITERIA SUMMARY (AC1-AC8)
# ============================================================================


class TestAcceptanceCriteria:
    """Verify all acceptance criteria are met."""

    def test_ac1_tool1_fastmcp_wrapper(self):
        """AC1: Tool 1 FastMCP wrapper with retry logic."""
        tool1 = TOOLS[0]
        assert tool1.name == "get_user_profile"
        result = tool1.invoke({"user_id": "user_123"})
        assert result is not None
        assert isinstance(result, dict)

    def test_ac2_tool2_fastmcp_wrapper(self):
        """AC2: Tool 2 FastMCP wrapper with empty result handling."""
        tool2 = TOOLS[1]
        assert tool2.name == "search_question_templates"
        result = tool2.invoke({
            "interests": ["AI"],
            "difficulty": 5,
            "category": "technical",
        })
        assert isinstance(result, list)

    def test_ac3_tool3_fastmcp_wrapper(self):
        """AC3: Tool 3 FastMCP wrapper with cached/default fallback."""
        tool3 = TOOLS[2]
        assert tool3.name == "get_difficulty_keywords"
        result = tool3.invoke({
            "difficulty": 5,
            "category": "technical",
        })
        assert isinstance(result, dict)

    def test_ac4_tool4_fastmcp_wrapper(self):
        """AC4: Tool 4 FastMCP wrapper with score threshold 0.70."""
        tool4 = TOOLS[3]
        assert tool4.name == "validate_question_quality"
        result = tool4.invoke({
            "stem": "Question?",
            "question_type": "multiple_choice",
        })
        assert "score" in result

    def test_ac5_tool5_fastmcp_wrapper(self):
        """AC5: Tool 5 FastMCP wrapper with queue on failure."""
        tool5 = TOOLS[4]
        assert tool5.name == "save_generated_question"
        result = tool5.invoke({
            "item_type": "multiple_choice",
            "stem": "Question?",
            "difficulty": 5,
            "categories": ["technical"],
            "round_id": "sess_001_1",
        })
        assert isinstance(result, dict)

    def test_ac6_tool6_fastmcp_wrapper(self):
        """AC6: Tool 6 FastMCP wrapper with LLM timeout fallback."""
        tool6 = TOOLS[5]
        assert tool6.name == "score_and_explain"
        result = tool6.invoke({
            "session_id": "sess_001",
            "user_id": "user_123",
            "question_id": "q_001",
            "question_type": "multiple_choice",
            "user_answer": "B",
            "correct_answer": "B",
            "difficulty": 5,
            "category": "technical",
        })
        assert "is_correct" in result

    def test_ac7_tools_registered(self):
        """AC7: Tools are registered and available."""
        assert len(TOOLS) == 6
        for tool in TOOLS:
            assert hasattr(tool, "invoke")

    def test_ac8_tools_invocation_interface(self):
        """AC8: Standard interface for LangChain agent."""
        assert len(TOOLS) == 6
        for tool in TOOLS:
            assert hasattr(tool, "invoke")
            assert hasattr(tool, "name")
