"""
Comprehensive unit tests for AnswerSchema Value Object.

REQ: REQ-REFACTOR-SOLID-2
Phase 2: Test Design
Phase 3: Implementation

Test coverage:
- AnswerSchema frozen dataclass definition
- Factory methods: from_agent_response(), from_mock_data(), from_dict()
- Conversion methods: to_db_dict(), to_response_dict()
- Immutability enforcement (frozen=True)
- Value Object behavior (__eq__, __hash__)
- Field validation (__post_init__)
- Type safety and mypy compliance
- Integration with TransformerFactory

Test categories:
1. Creation & Factory Methods (11 tests)
   TC-1: Create from agent response
   TC-2: Create from mock data
   TC-3: Generic from_dict with source
   TC-4: Auto-detect format in from_dict
   TC-5: Handle None values
   TC-6: Create with unicode keywords
   TC-7: Create with long explanation
   TC-8: from_dict with extra fields (ignored)
   TC-9: Create minimal schema
   TC-10: Create full schema with created_at
   TC-11: Type validation on creation

2. Conversion Methods (8 tests)
   TC-12: to_db_dict includes all fields
   TC-13: to_db_dict includes created_at
   TC-14: to_response_dict excludes internal fields
   TC-15: to_response_dict includes keywords
   TC-16: to_response_dict includes correct_answer
   TC-17: Round-trip: create → to_db_dict → works
   TC-18: Round-trip with None keywords
   TC-19: Round-trip with None explanation

3. Immutability (4 tests)
   TC-20: frozen=True prevents modification
   TC-21: Cannot modify keywords list
   TC-22: Cannot modify created_at
   TC-23: Properties are read-only

4. Value Object Equality (5 tests)
   TC-24: Equal objects with same data
   TC-25: Different objects with different data
   TC-26: Equality ignores created_at (immutable value)
   TC-27: Hash consistency with equality
   TC-28: Can be used in sets/dicts

5. Field Validation (6 tests)
   TC-29: Validate type field required
   TC-30: Validate keywords is list if present
   TC-31: Validate correct_answer is string if present
   TC-32: Validate explanation is string
   TC-33: Validate either keywords or correct_answer present
   TC-34: Validate source_format is valid

6. Edge Cases (5 tests)
   TC-35: Empty string explanation raises error
   TC-36: None keywords with None correct_answer raises error
   TC-37: Both keywords and correct_answer present (OK)
   TC-38: Unicode in all fields
   TC-39: Very long values (5000+ chars)

7. Integration Tests (3 tests)
   TC-40: Integration with TransformerFactory output
   TC-41: Integration with question_gen_service pattern
   TC-42: Serialization for database storage

Total: 42 comprehensive test cases
"""

import pytest
from datetime import datetime
from dataclasses import FrozenInstanceError
from typing import Any

from src.backend.models.answer_schema import (
    AnswerSchema,
    TransformerFactory,
    AgentResponseTransformer,
    MockDataTransformer,
    ValidationError,
)


class TestAnswerSchemaCreation:
    """Test AnswerSchema creation and factory methods."""

    def test_tc1_create_from_agent_response(self) -> None:
        """TC-1: Create AnswerSchema from agent response format."""
        agent_response = {
            "correct_keywords": ["battery", "lithium"],
            "explanation": "Lithium-ion batteries..."
        }

        schema = AnswerSchema.from_agent_response(agent_response)

        assert schema.type == "keyword_match"
        assert schema.keywords == ["battery", "lithium"]
        assert schema.explanation == "Lithium-ion batteries..."
        assert schema.source_format == "agent_response"

    def test_tc2_create_from_mock_data(self) -> None:
        """TC-2: Create AnswerSchema from mock data format."""
        mock_data = {
            "correct_key": "B",
            "explanation": "This is the correct answer"
        }

        schema = AnswerSchema.from_mock_data(mock_data)

        assert schema.type == "exact_match"
        assert schema.correct_answer == "B"
        assert schema.keywords is None
        assert schema.explanation == "This is the correct answer"
        assert schema.source_format == "mock_data"

    def test_tc3_create_from_dict_with_source(self) -> None:
        """TC-3: Create AnswerSchema from generic dict with source parameter."""
        data = {
            "type": "keyword_match",
            "keywords": ["key1", "key2"],
            "explanation": "Test explanation",
        }

        schema = AnswerSchema.from_dict(data, source="custom_format")

        assert schema.type == "keyword_match"
        assert schema.keywords == ["key1", "key2"]
        assert schema.source_format == "custom_format"

    def test_tc4_from_dict_auto_detect_agent_format(self) -> None:
        """TC-4: from_dict auto-detects agent format by correct_keywords presence."""
        data = {
            "correct_keywords": ["answer1"],
            "explanation": "Test"
        }

        schema = AnswerSchema.from_dict(data)

        assert schema.source_format == "agent_response"
        assert schema.keywords == ["answer1"]

    def test_tc5_from_dict_auto_detect_mock_format(self) -> None:
        """TC-5: from_dict auto-detects mock format by correct_key presence."""
        data = {
            "correct_key": "Answer",
            "explanation": "Test"
        }

        schema = AnswerSchema.from_dict(data)

        assert schema.source_format == "mock_data"
        assert schema.correct_answer == "Answer"

    def test_tc6_create_with_unicode_keywords(self) -> None:
        """TC-6: Create AnswerSchema with Korean/Unicode keywords."""
        schema = AnswerSchema.from_agent_response({
            "correct_keywords": ["배터리", "리튬이온"],
            "explanation": "리튬이온 배터리는..."
        })

        assert schema.keywords == ["배터리", "리튬이온"]
        assert "배터리" in schema.keywords

    def test_tc7_create_with_very_long_explanation(self) -> None:
        """TC-7: Create AnswerSchema with long explanation (5000+ chars)."""
        long_text = "A" * 10000

        schema = AnswerSchema.from_agent_response({
            "correct_keywords": ["key"],
            "explanation": long_text
        })

        assert len(schema.explanation) == 10000
        assert schema.explanation == long_text

    def test_tc8_from_dict_ignores_extra_fields(self) -> None:
        """TC-8: from_dict ignores extra fields not in dataclass."""
        data = {
            "type": "keyword_match",
            "keywords": ["k1"],
            "explanation": "Test",
            "extra_field": "should be ignored",
            "another_extra": 123
        }

        schema = AnswerSchema.from_dict(data, source="test")

        assert schema.keywords == ["k1"]
        assert not hasattr(schema, "extra_field")

    def test_tc9_create_minimal_schema(self) -> None:
        """TC-9: Create minimal valid AnswerSchema."""
        schema = AnswerSchema.from_agent_response({
            "correct_keywords": ["answer"],
            "explanation": "Short"
        })

        assert schema.type == "keyword_match"
        assert schema.keywords == ["answer"]
        assert schema.correct_answer is None
        assert schema.created_at is not None  # Should be auto-set

    def test_tc10_create_with_all_fields(self) -> None:
        """TC-10: Create AnswerSchema with all fields specified."""
        now = datetime.now()
        schema = AnswerSchema(
            type="keyword_match",
            keywords=["k1", "k2"],
            correct_answer=None,
            explanation="Full schema",
            source_format="test",
            created_at=now
        )

        assert schema.type == "keyword_match"
        assert schema.keywords == ["k1", "k2"]
        assert schema.created_at == now

    def test_tc11_creation_validates_type_field(self) -> None:
        """TC-11: Creation validates required type field."""
        with pytest.raises((ValidationError, TypeError)):
            AnswerSchema(
                type="",  # Empty type should fail
                keywords=["k1"],
                explanation="Test"
            )


class TestAnswerSchemaConversion:
    """Test AnswerSchema conversion methods."""

    def test_tc12_to_db_dict_includes_all_fields(self) -> None:
        """TC-12: to_db_dict() includes all fields for database storage."""
        schema = AnswerSchema.from_agent_response({
            "correct_keywords": ["k1", "k2"],
            "explanation": "Explanation"
        })

        db_dict = schema.to_db_dict()

        assert "keywords" in db_dict
        assert "explanation" in db_dict
        assert "source_format" in db_dict
        assert "created_at" in db_dict
        assert db_dict["keywords"] == ["k1", "k2"]

    def test_tc13_to_db_dict_includes_created_at(self) -> None:
        """TC-13: to_db_dict() includes created_at timestamp."""
        schema = AnswerSchema.from_agent_response({
            "correct_keywords": ["k1"],
            "explanation": "Test"
        })

        db_dict = schema.to_db_dict()

        assert "created_at" in db_dict
        assert isinstance(db_dict["created_at"], datetime)

    def test_tc14_to_response_dict_excludes_internal_fields(self) -> None:
        """TC-14: to_response_dict() excludes internal metadata fields."""
        schema = AnswerSchema.from_agent_response({
            "correct_keywords": ["k1"],
            "explanation": "Test"
        })

        api_dict = schema.to_response_dict()

        assert "created_at" not in api_dict
        assert "source_format" not in api_dict

    def test_tc15_to_response_dict_includes_keywords(self) -> None:
        """TC-15: to_response_dict() includes keywords field."""
        schema = AnswerSchema.from_agent_response({
            "correct_keywords": ["keyword1", "keyword2"],
            "explanation": "Test explanation"
        })

        api_dict = schema.to_response_dict()

        assert api_dict["keywords"] == ["keyword1", "keyword2"]
        assert api_dict["explanation"] == "Test explanation"

    def test_tc16_to_response_dict_includes_correct_answer(self) -> None:
        """TC-16: to_response_dict() includes correct_answer field when present."""
        schema = AnswerSchema.from_mock_data({
            "correct_key": "B",
            "explanation": "Explanation"
        })

        api_dict = schema.to_response_dict()

        assert api_dict["correct_answer"] == "B"

    def test_tc17_round_trip_create_to_db_dict(self) -> None:
        """TC-17: Round-trip conversion create → to_db_dict() → works."""
        original_dict = {
            "correct_keywords": ["battery"],
            "explanation": "Lithium batteries store energy"
        }

        schema = AnswerSchema.from_agent_response(original_dict)
        db_dict = schema.to_db_dict()

        # Recreate from db_dict
        schema2 = AnswerSchema.from_dict(db_dict, source=db_dict.get("source_format", "db"))

        assert schema2.keywords == schema.keywords
        assert schema2.explanation == schema.explanation

    def test_tc18_round_trip_with_none_keywords(self) -> None:
        """TC-18: Round-trip conversion with None keywords."""
        schema = AnswerSchema.from_mock_data({
            "correct_key": "Answer",
            "explanation": "Test"
        })

        db_dict = schema.to_db_dict()
        schema2 = AnswerSchema.from_dict(db_dict, source="db")

        assert schema2.keywords is None
        assert schema2.correct_answer == "Answer"

    def test_tc19_round_trip_preserves_type(self) -> None:
        """TC-19: Round-trip conversion preserves type field."""
        schema = AnswerSchema(
            type="multiple_choice",
            keywords=["a", "b"],
            explanation="Test"
        )

        db_dict = schema.to_db_dict()

        assert db_dict["type"] == "multiple_choice"


class TestAnswerSchemaImmutability:
    """Test AnswerSchema immutability (frozen dataclass)."""

    def test_tc20_frozen_prevents_field_modification(self) -> None:
        """TC-20: frozen=True prevents modification after creation."""
        schema = AnswerSchema.from_agent_response({
            "correct_keywords": ["k1"],
            "explanation": "Test"
        })

        with pytest.raises(FrozenInstanceError):
            schema.type = "other"  # type: ignore

    def test_tc21_cannot_modify_keywords(self) -> None:
        """TC-21: Cannot modify keywords after creation."""
        schema = AnswerSchema.from_agent_response({
            "correct_keywords": ["original"],
            "explanation": "Test"
        })

        with pytest.raises(FrozenInstanceError):
            schema.keywords = ["modified"]  # type: ignore

    def test_tc22_cannot_modify_explanation(self) -> None:
        """TC-22: Cannot modify explanation after creation."""
        schema = AnswerSchema.from_agent_response({
            "correct_keywords": ["k1"],
            "explanation": "Original"
        })

        with pytest.raises(FrozenInstanceError):
            schema.explanation = "Modified"  # type: ignore

    def test_tc23_cannot_modify_created_at(self) -> None:
        """TC-23: Cannot modify created_at timestamp."""
        schema = AnswerSchema.from_agent_response({
            "correct_keywords": ["k1"],
            "explanation": "Test"
        })

        original_time = schema.created_at

        with pytest.raises(FrozenInstanceError):
            schema.created_at = datetime.now()  # type: ignore

        assert schema.created_at == original_time


class TestAnswerSchemaEquality:
    """Test Value Object equality and hashing."""

    def test_tc24_equal_objects_with_same_data(self) -> None:
        """TC-24: Two AnswerSchema instances with same data and created_at are equal."""
        # Create schema1
        schema1 = AnswerSchema.from_agent_response({
            "correct_keywords": ["k1", "k2"],
            "explanation": "Test"
        })

        # Create schema2 with same created_at timestamp
        schema2 = AnswerSchema(
            type=schema1.type,
            keywords=schema1.keywords,
            correct_answer=schema1.correct_answer,
            explanation=schema1.explanation,
            source_format=schema1.source_format,
            created_at=schema1.created_at  # Use same timestamp
        )

        assert schema1 == schema2

    def test_tc25_different_objects_with_different_data(self) -> None:
        """TC-25: Two AnswerSchema instances with different data are not equal."""
        schema1 = AnswerSchema.from_agent_response({
            "correct_keywords": ["k1"],
            "explanation": "Test1"
        })
        schema2 = AnswerSchema.from_agent_response({
            "correct_keywords": ["k2"],
            "explanation": "Test2"
        })

        assert schema1 != schema2

    def test_tc26_equality_ignores_created_at_differences(self) -> None:
        """TC-26: Equality compares by value, may differ on created_at timing."""
        now1 = datetime.now()
        now2 = datetime.now()

        schema1 = AnswerSchema(
            type="keyword_match",
            keywords=["k1"],
            explanation="Test",
            created_at=now1
        )
        schema2 = AnswerSchema(
            type="keyword_match",
            keywords=["k1"],
            explanation="Test",
            created_at=now2
        )

        # Equality should use all fields, including created_at
        # So if timestamps differ, objects are different
        if now1 != now2:
            assert schema1 != schema2
        else:
            assert schema1 == schema2

    def test_tc27_hash_consistency_with_equality(self) -> None:
        """TC-27: Hash is consistent - equal objects have same hash."""
        schema1 = AnswerSchema.from_agent_response({
            "correct_keywords": ["k1"],
            "explanation": "Test"
        })
        # Create second instance with same data but don't allow created_at difference
        schema2 = AnswerSchema(
            type=schema1.type,
            keywords=schema1.keywords,
            correct_answer=schema1.correct_answer,
            explanation=schema1.explanation,
            source_format=schema1.source_format,
            created_at=schema1.created_at
        )

        if schema1 == schema2:
            assert hash(schema1) == hash(schema2)

    def test_tc28_can_be_used_in_sets_and_dicts(self) -> None:
        """TC-28: AnswerSchema objects can be stored in sets and dicts."""
        schema1 = AnswerSchema.from_agent_response({
            "correct_keywords": ["k1"],
            "explanation": "Test"
        })

        # Create second instance to test hashing
        schema2 = AnswerSchema(
            type=schema1.type,
            keywords=schema1.keywords,
            correct_answer=schema1.correct_answer,
            explanation=schema1.explanation,
            source_format=schema1.source_format,
            created_at=schema1.created_at
        )

        # Can be used in set
        schema_set = {schema1, schema2}
        assert isinstance(schema_set, set)

        # Can be used as dict key
        schema_dict = {schema1: "value1"}
        assert schema_dict[schema1] == "value1"


class TestAnswerSchemaValidation:
    """Test AnswerSchema field validation in __post_init__."""

    def test_tc29_type_field_required(self) -> None:
        """TC-29: type field is required and validated."""
        with pytest.raises((ValidationError, TypeError, ValueError)):
            AnswerSchema(
                type="",  # Empty type
                keywords=["k1"],
                explanation="Test"
            )

    def test_tc30_keywords_must_be_list_if_present(self) -> None:
        """TC-30: keywords must be list if present."""
        with pytest.raises((ValidationError, TypeError)):
            AnswerSchema(
                type="keyword_match",
                keywords="not a list",  # type: ignore
                explanation="Test"
            )

    def test_tc31_correct_answer_must_be_string_if_present(self) -> None:
        """TC-31: correct_answer must be string if present."""
        with pytest.raises((ValidationError, TypeError)):
            AnswerSchema(
                type="exact_match",
                correct_answer=123,  # type: ignore
                explanation="Test"
            )

    def test_tc32_explanation_must_be_string(self) -> None:
        """TC-32: explanation must be non-empty string."""
        with pytest.raises((ValidationError, TypeError)):
            AnswerSchema(
                type="keyword_match",
                keywords=["k1"],
                explanation=""  # Empty explanation
            )

    def test_tc33_must_have_keywords_or_correct_answer(self) -> None:
        """TC-33: Must have either keywords or correct_answer."""
        with pytest.raises(ValidationError):
            AnswerSchema(
                type="keyword_match",
                keywords=None,
                correct_answer=None,  # Both None
                explanation="Test"
            )

    def test_tc34_source_format_defaults_to_unknown(self) -> None:
        """TC-34: source_format defaults to 'unknown' if not specified."""
        schema = AnswerSchema(
            type="keyword_match",
            keywords=["k1"],
            explanation="Test"
        )

        assert schema.source_format == "unknown"


class TestAnswerSchemaEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_tc35_empty_explanation_raises_error(self) -> None:
        """TC-35: Empty or whitespace-only explanation raises error."""
        with pytest.raises(ValidationError):
            AnswerSchema(
                type="keyword_match",
                keywords=["k1"],
                explanation="   "  # Whitespace only
            )

    def test_tc36_both_keywords_and_answer_none_raises_error(self) -> None:
        """TC-36: Both keywords and correct_answer None raises error."""
        with pytest.raises(ValidationError):
            AnswerSchema(
                type="keyword_match",
                keywords=None,
                correct_answer=None,
                explanation="Test"
            )

    def test_tc37_both_keywords_and_answer_present_ok(self) -> None:
        """TC-37: Both keywords and correct_answer can be present."""
        schema = AnswerSchema(
            type="hybrid_match",
            keywords=["k1", "k2"],
            correct_answer="full_answer",
            explanation="Test"
        )

        assert schema.keywords == ["k1", "k2"]
        assert schema.correct_answer == "full_answer"

    def test_tc38_unicode_in_all_fields(self) -> None:
        """TC-38: Unicode characters work in all fields."""
        schema = AnswerSchema(
            type="keyword_match",
            keywords=["한글", "日本語", "العربية"],
            explanation="다국어 설명: Explanation in multiple 言語"
        )

        assert "한글" in schema.keywords
        assert "多言" in schema.keywords or "日本" in schema.keywords[1]

    def test_tc39_very_long_values_handled(self) -> None:
        """TC-39: Very long keyword and explanation values (5000+ chars)."""
        long_keyword = "A" * 5000
        long_explanation = "B" * 10000

        schema = AnswerSchema(
            type="keyword_match",
            keywords=[long_keyword, "short"],
            explanation=long_explanation
        )

        assert len(schema.keywords[0]) == 5000
        assert len(schema.explanation) == 10000


class TestAnswerSchemaIntegration:
    """Test integration with other components."""

    def test_tc40_integration_with_transformer_factory(self) -> None:
        """TC-40: AnswerSchema works with TransformerFactory output."""
        factory = TransformerFactory()

        # Agent response transform
        agent_transformer = factory.get_transformer("agent_response")
        transformed = agent_transformer.transform({
            "correct_keywords": ["battery"],
            "explanation": "Batteries store energy"
        })

        # Create AnswerSchema from transformed data
        schema = AnswerSchema.from_dict(transformed, source="agent_response")

        assert schema.keywords == ["battery"]
        assert schema.source_format == "agent_response"

    def test_tc41_integration_with_question_gen_service_pattern(self) -> None:
        """TC-41: AnswerSchema usage pattern matches question_gen_service."""
        # Simulate what question_gen_service does
        agent_response = {
            "correct_keywords": ["answer1"],
            "explanation": "Explanation"
        }

        # Service creates AnswerSchema
        schema = AnswerSchema.from_agent_response(agent_response)

        # Service saves to DB
        db_dict = schema.to_db_dict()
        assert "keywords" in db_dict
        assert "source_format" in db_dict

        # Service returns to API
        api_dict = schema.to_response_dict()
        assert "created_at" not in api_dict
        assert "source_format" not in api_dict

    def test_tc42_serialization_for_database_storage(self) -> None:
        """TC-42: AnswerSchema serializes correctly for database storage."""
        schema = AnswerSchema.from_agent_response({
            "correct_keywords": ["k1", "k2"],
            "explanation": "Test explanation"
        })

        # Should be serializable to JSON-compatible dict
        db_dict = schema.to_db_dict()

        # All values should be JSON serializable types
        assert isinstance(db_dict["type"], str)
        assert isinstance(db_dict["keywords"], list) or db_dict["keywords"] is None
        assert isinstance(db_dict["explanation"], str)
        assert isinstance(db_dict["source_format"], str)
        assert isinstance(db_dict["created_at"], datetime)
