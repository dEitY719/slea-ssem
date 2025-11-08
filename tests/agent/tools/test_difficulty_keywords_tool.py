"""Tests for Difficulty Keywords Tool (REQ-A-Mode1-Tool3).

REQ: REQ-A-Mode1-Tool3
Tests for get_difficulty_keywords() function that retrieves keywords by difficulty.
"""

import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from src.agent.tools.difficulty_keywords_tool import _get_difficulty_keywords_impl


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def valid_keyword_record() -> MagicMock:
    """Create a mock DifficultyKeyword record."""
    keyword = MagicMock()
    keyword.id = "kw_550e8400_e29b_41d4_a716_446655440001"
    keyword.difficulty = 7
    keyword.category = "technical"
    keyword.keywords = [
        "Large Language Model",
        "Transformer",
        "Attention Mechanism",
        "Fine-tuning",
        "Prompt Engineering",
    ]
    keyword.concepts = [
        {
            "name": "Retrieval Augmented Generation",
            "acronym": "RAG",
            "definition": "Technique combining retrieval and generation",
            "key_points": ["Retrieval", "Augmented", "Generation"],
        },
        {
            "name": "Chain-of-Thought Prompting",
            "acronym": "CoT",
            "definition": "Requesting step-by-step reasoning",
            "key_points": ["Step-by-step", "Reasoning", "Explainability"],
        },
    ]
    keyword.example_questions = [
        {
            "stem": "What is RAG?",
            "type": "short_answer",
            "difficulty_score": 7.5,
            "answer_summary": "Combining retrieval with generation",
        }
    ]
    return keyword


@pytest.fixture
def default_keywords() -> dict[str, Any]:
    """DEFAULT_KEYWORDS fallback."""
    return {
        "difficulty": 5,
        "category": "general",
        "keywords": ["Communication", "Problem Solving", "Teamwork"],
        "concepts": [
            {
                "name": "Effective Communication",
                "acronym": "EC",
                "definition": "Clear and efficient information transfer",
                "key_points": ["Clarity", "Listening", "Feedback"],
            }
        ],
        "example_questions": [
            {
                "stem": "What is good communication?",
                "type": "short_answer",
                "difficulty_score": 5.0,
                "answer_summary": "Clear exchange of information",
            }
        ],
    }


@pytest.fixture
def mock_db() -> MagicMock:
    """Create a mock database session."""
    return MagicMock(spec=Session)


# ============================================================================
# Happy Path Tests
# ============================================================================


class TestGetDifficultyKeywordsHappyPath:
    """Tests for successful keyword retrieval."""

    def test_get_difficulty_keywords_db_hit(
        self,
        valid_keyword_record: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Test retrieving keywords from database.

        REQ: REQ-A-Mode1-Tool3, AC1

        Given: Valid difficulty and category
        When: get_difficulty_keywords() is called
        Then: Returns dict with keywords, concepts, example_questions
        """
        # Setup
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = valid_keyword_record

        # Execute
        with patch(
            "src.agent.tools.difficulty_keywords_tool.get_db",
            return_value=iter([mock_db]),
        ):
            result = _get_difficulty_keywords_impl(7, "technical")

        # Assert
        assert result is not None
        assert isinstance(result, dict)
        assert result["difficulty"] == 7
        assert result["category"] == "technical"
        assert "keywords" in result
        assert "concepts" in result
        assert "example_questions" in result
        assert len(result["keywords"]) >= 1
        assert len(result["concepts"]) >= 1

    def test_get_difficulty_keywords_cache_hit(
        self,
        valid_keyword_record: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Test cache hit returns immediately without DB query.

        REQ: REQ-A-Mode1-Tool3, AC4

        Given: Same (difficulty, category) called twice
        When: Second call occurs
        Then: Returns cached result without DB query
        """
        # Setup
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = valid_keyword_record

        # Execute first call
        with patch(
            "src.agent.tools.difficulty_keywords_tool.get_db",
            return_value=iter([mock_db]),
        ):
            result1 = _get_difficulty_keywords_impl(5, "business")
            call_count_after_first = mock_db.query.call_count

        # Execute second call (should use cache)
        with patch(
            "src.agent.tools.difficulty_keywords_tool.get_db",
            return_value=iter([mock_db]),
        ):
            result2 = _get_difficulty_keywords_impl(5, "business")
            call_count_after_second = mock_db.query.call_count

        # Assert
        assert result1 == result2
        assert call_count_after_second == call_count_after_first  # No new query

    def test_get_difficulty_keywords_with_null_fields(
        self,
        mock_db: MagicMock,
    ) -> None:
        """Test that NULL fields are filled with defaults.

        REQ: REQ-A-Mode1-Tool3, AC5

        Given: Record with NULL fields
        When: get_difficulty_keywords() is called
        Then: Returns complete response with defaults
        """
        # Setup
        null_record = MagicMock()
        null_record.difficulty = 10
        null_record.category = "general"
        null_record.keywords = None
        null_record.concepts = None
        null_record.example_questions = None

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = null_record

        # Execute
        with patch(
            "src.agent.tools.difficulty_keywords_tool.get_db",
            return_value=iter([mock_db]),
        ):
            result = _get_difficulty_keywords_impl(10, "general")

        # Assert
        assert result is not None
        assert result["keywords"] is not None
        assert result["concepts"] is not None
        assert result["example_questions"] is not None


# ============================================================================
# Input Validation Tests
# ============================================================================


class TestGetDifficultyKeywordsInputValidation:
    """Tests for input validation."""

    def test_get_difficulty_keywords_invalid_difficulty(self) -> None:
        """Test rejection of difficulty out of range.

        REQ: REQ-A-Mode1-Tool3, AC3

        Given: difficulty=11 (out of range)
        When: get_difficulty_keywords() is called
        Then: ValueError is raised
        """
        with pytest.raises(ValueError):
            _get_difficulty_keywords_impl(11, "technical")

    def test_get_difficulty_keywords_invalid_category(self) -> None:
        """Test rejection of unsupported category.

        REQ: REQ-A-Mode1-Tool3, AC3

        Given: category="unknown"
        When: get_difficulty_keywords() is called
        Then: ValueError is raised
        """
        with pytest.raises(ValueError):
            _get_difficulty_keywords_impl(7, "unknown")


# ============================================================================
# Database Error Tests
# ============================================================================


class TestGetDifficultyKeywordsDatabaseErrors:
    """Tests for database error handling."""

    def test_get_difficulty_keywords_db_connection_error(
        self,
        default_keywords: dict[str, Any],
        mock_db: MagicMock,
    ) -> None:
        """Test handling of database connection errors.

        REQ: REQ-A-Mode1-Tool3, AC2

        Given: Database connection fails
        When: get_difficulty_keywords() is called
        Then: Returns default values, no exception raised
        """
        # Setup
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = OperationalError("Connection failed", None, None)

        # Execute
        with patch(
            "src.agent.tools.difficulty_keywords_tool.get_db",
            return_value=iter([mock_db]),
        ):
            result = _get_difficulty_keywords_impl(7, "technical")

        # Assert
        assert isinstance(result, dict)
        assert "keywords" in result
        assert "concepts" in result

    def test_get_difficulty_keywords_query_timeout(
        self,
        mock_db: MagicMock,
    ) -> None:
        """Test handling of query timeouts.

        REQ: REQ-A-Mode1-Tool3, AC2

        Given: Database query times out
        When: get_difficulty_keywords() is called
        Then: Returns default values, no exception raised
        """
        # Setup
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = Exception("Query timeout")

        # Execute
        with patch(
            "src.agent.tools.difficulty_keywords_tool.get_db",
            return_value=iter([mock_db]),
        ):
            result = _get_difficulty_keywords_impl(5, "business")

        # Assert
        assert isinstance(result, dict)
        assert result is not None


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestGetDifficultyKeywordsEdgeCases:
    """Tests for edge cases."""

    def test_get_difficulty_keywords_all_difficulty_levels(
        self,
        valid_keyword_record: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Test all difficulty levels 1-10.

        REQ: REQ-A-Mode1-Tool3

        Given: All difficulty levels
        When: get_difficulty_keywords() is called for each
        Then: All return valid responses
        """
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = valid_keyword_record

        for diff in range(1, 11):
            with patch(
                "src.agent.tools.difficulty_keywords_tool.get_db",
                return_value=iter([mock_db]),
            ):
                result = _get_difficulty_keywords_impl(diff, "technical")
                assert result is not None
                assert isinstance(result, dict)

    def test_get_difficulty_keywords_all_categories(
        self,
        valid_keyword_record: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Test all supported categories.

        REQ: REQ-A-Mode1-Tool3

        Given: All categories (technical, business, general)
        When: get_difficulty_keywords() is called for each
        Then: All return valid responses
        """
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = valid_keyword_record

        for cat in ["technical", "business", "general"]:
            with patch(
                "src.agent.tools.difficulty_keywords_tool.get_db",
                return_value=iter([mock_db]),
            ):
                result = _get_difficulty_keywords_impl(7, cat)
                assert result is not None
                # Category comes from keyword_record (all same)
                assert isinstance(result, dict)

    def test_get_difficulty_keywords_with_unicode(
        self,
        mock_db: MagicMock,
    ) -> None:
        """Test handling of unicode characters.

        REQ: REQ-A-Mode1-Tool3

        Given: Concepts with Korean text
        When: get_difficulty_keywords() is called
        Then: Unicode is preserved
        """
        # Setup
        unicode_record = MagicMock()
        unicode_record.difficulty = 8  # Different difficulty to avoid cache
        unicode_record.category = "business"  # Different category to avoid cache
        unicode_record.keywords = ["트랜스포머", "주목메커니즘"]
        unicode_record.concepts = [
            {
                "name": "트랜스포머 아키텍처",
                "acronym": "TA",
                "definition": "심층 신경망 모델",
                "key_points": ["주목", "위치", "인코딩"],
            }
        ]
        unicode_record.example_questions = []

        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = unicode_record

        # Execute
        with patch(
            "src.agent.tools.difficulty_keywords_tool.get_db",
            return_value=iter([mock_db]),
        ):
            result = _get_difficulty_keywords_impl(8, "business")

        # Assert
        assert "트랜스포머" in result["keywords"]
        assert len(result["concepts"]) > 0
        assert result["concepts"][0]["name"] == "트랜스포머 아키텍처"

    def test_get_difficulty_keywords_response_completeness(
        self,
        valid_keyword_record: MagicMock,
        mock_db: MagicMock,
    ) -> None:
        """Test response completeness.

        REQ: REQ-A-Mode1-Tool3, AC1

        Given: Valid DB record
        When: get_difficulty_keywords() is called
        Then: All required fields present with valid values
        """
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = valid_keyword_record

        with patch(
            "src.agent.tools.difficulty_keywords_tool.get_db",
            return_value=iter([mock_db]),
        ):
            result = _get_difficulty_keywords_impl(7, "technical")

        # Assert completeness
        assert 5 <= len(result["keywords"]) <= 20
        assert len(result["concepts"]) <= 10
        assert len(result["example_questions"]) <= 5
        for concept in result["concepts"]:
            assert "name" in concept
            assert "acronym" in concept
            assert "definition" in concept
            assert "key_points" in concept
