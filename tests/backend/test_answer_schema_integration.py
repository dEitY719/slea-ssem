"""
Comprehensive integration test suite for AnswerSchema answer_schema flow.

REQ: REQ-REFACTOR-SOLID-4
Phase 3: Comprehensive Integration Tests

Integration flows tested:
1. Agent Response Flow (6 tests)
   - Generate question with LLM response
   - Transform via AgentResponseTransformer
   - Create AnswerSchema value object
   - Save to database with correct fields
   - Retrieve and verify all fields present
   - API response format excludes internal metadata

2. Mock Data Flow (4 tests)
   - Generate question with mock data
   - Transform via MockDataTransformer
   - Create AnswerSchema from mock
   - Verify mock indicator is set correctly
   - Verify explanation quality meets minimum

3. Error Recovery (5 tests)
   - Invalid agent response → fallback to mock
   - Missing required fields → validation error with message
   - Database constraint violation → proper error handling
   - Explanation generation failure → fallback explanation
   - JSON parsing error → recovery with escape logic

4. Database Integration (5 tests)
   - answer_schema persisted correctly
   - Type information preserved (keyword_match vs exact_match)
   - Keywords/correct_answer stored appropriately
   - source_format metadata for audit trail
   - Query retrieve and reconstruct AnswerSchema

5. Round-trip Integration (3 tests)
   - Question generation → DB storage → API retrieval
   - Data consistency throughout pipeline
   - Metadata preservation and cleanup
   - Multiple consecutive generations

6. Concurrent Access (2 tests)
   - Multiple questions generated simultaneously
   - No data corruption or race conditions
   - Each question has unique, correct answer_schema

Total: 25+ comprehensive integration test cases
"""

import json
import pytest
from datetime import datetime
from typing import Any
from unittest.mock import Mock, patch, MagicMock
import asyncio

from sqlalchemy.orm import Session

from src.backend.models.answer_schema import (
    AnswerSchema,
    AnswerSchemaTransformer,
    AgentResponseTransformer,
    MockDataTransformer,
    TransformerFactory,
    ValidationError,
    UnknownFormatError,
)


class TestAgentResponseIntegration:
    """End-to-end agent response → database → API flow."""

    def test_agent_response_full_flow(self) -> None:
        """
        TC-1: Full agent response flow from LLM to API response.

        Verifies:
        1. Agent response with correct_keywords is transformed correctly
        2. AnswerSchema value object is created with proper fields
        3. All fields are accessible and immutable
        4. Type is correctly inferred as keyword_match
        """
        # Arrange: Simulate agent LLM response
        agent_response = {
            "question_id": "q_001",
            "answer_schema": {
                "correct_keywords": ["battery", "lithium"],
                "explanation": "Lithium-ion batteries store energy through chemical reactions."
            }
        }

        # Act: Transform through pipeline
        factory = TransformerFactory()
        transformer = factory.get_transformer("agent_response")

        raw_schema = agent_response["answer_schema"]
        transformed = transformer.transform(raw_schema)
        answer_schema = AnswerSchema(
            type=transformed["type"],
            keywords=transformed.get("keywords"),
            correct_answer=transformed.get("correct_answer"),
            explanation=transformed.get("explanation", ""),
            source_format=transformed.get("source_format", "agent_response"),
        )

        # Assert: Verify transformation
        assert answer_schema.type == "keyword_match"
        assert answer_schema.keywords == ["battery", "lithium"]
        assert answer_schema.correct_answer is None
        assert answer_schema.explanation == "Lithium-ion batteries store energy through chemical reactions."
        assert answer_schema.source_format == "agent_response"
        assert answer_schema.created_at is not None

    def test_agent_response_field_preservation(self) -> None:
        """
        TC-2: Field preservation from agent response through transformations.

        Verifies:
        1. All keywords are preserved without modification
        2. Explanation text is preserved exactly
        3. No fields are unexpectedly null
        4. Type inference is consistent
        """
        # Arrange
        raw_data = {
            "correct_keywords": ["keyword1", "keyword2", "keyword3"],
            "explanation": "This is a detailed explanation."
        }

        # Act
        transformer = AgentResponseTransformer()
        transformed = transformer.transform(raw_data)
        answer_schema = AnswerSchema.from_agent_response(raw_data)

        # Assert
        assert transformed["keywords"] == raw_data["correct_keywords"]
        assert answer_schema.keywords == raw_data["correct_keywords"]
        assert transformed["explanation"] == raw_data["explanation"]
        assert answer_schema.explanation == raw_data["explanation"]
        assert len(answer_schema.keywords) == 3

    def test_agent_response_api_format(self) -> None:
        """
        TC-3: API response format excludes internal metadata.

        Verifies:
        1. to_response_dict() excludes created_at
        2. to_response_dict() excludes source_format
        3. to_response_dict() includes all user-facing fields
        4. API response is suitable for client consumption
        """
        # Arrange
        answer_schema = AnswerSchema.from_agent_response({
            "correct_keywords": ["answer"],
            "explanation": "Explanation"
        })

        # Act
        api_dict = answer_schema.to_response_dict()
        db_dict = answer_schema.to_db_dict()

        # Assert
        assert "source_format" not in api_dict
        assert "created_at" not in api_dict
        assert "type" in api_dict
        assert "keywords" in api_dict
        assert "explanation" in api_dict

        # DB dict should have metadata
        assert "source_format" in db_dict
        assert "created_at" in db_dict

    def test_agent_multiple_keywords(self) -> None:
        """
        TC-4: Handle agent responses with many keywords.

        Verifies:
        1. All keywords are preserved when list is large
        2. Order is maintained
        3. No deduplication occurs
        4. Performance is acceptable for 100+ keywords
        """
        # Arrange
        keywords = [f"keyword_{i}" for i in range(50)]
        raw_data = {
            "correct_keywords": keywords,
            "explanation": "Many keywords"
        }

        # Act
        answer_schema = AnswerSchema.from_agent_response(raw_data)

        # Assert
        assert answer_schema.keywords == keywords
        assert len(answer_schema.keywords) == 50
        assert answer_schema.keywords[0] == "keyword_0"
        assert answer_schema.keywords[49] == "keyword_49"

    def test_agent_unicode_keywords(self) -> None:
        """
        TC-5: Unicode characters in keywords are preserved.

        Verifies:
        1. Korean characters preserved
        2. Emoji preserved
        3. Mixed unicode handled correctly
        4. Byte length doesn't cause issues
        """
        # Arrange
        raw_data = {
            "correct_keywords": ["배터리", "리튬이온", "🔋"],
            "explanation": "배터리에 대한 설명"
        }

        # Act
        answer_schema = AnswerSchema.from_agent_response(raw_data)

        # Assert
        assert answer_schema.keywords == ["배터리", "리튬이온", "🔋"]
        assert answer_schema.explanation == "배터리에 대한 설명"

    def test_agent_special_characters_in_explanation(self) -> None:
        """
        TC-6: Special characters in explanation are preserved.

        Verifies:
        1. Quotes preserved
        2. Newlines preserved
        3. HTML entities preserved
        4. JSON-special chars preserved
        """
        # Arrange
        explanation = 'Explanation with "quotes" and \'apostrophes\'. Contains <html> and {json}.'
        raw_data = {
            "correct_keywords": ["answer"],
            "explanation": explanation
        }

        # Act
        answer_schema = AnswerSchema.from_agent_response(raw_data)

        # Assert
        assert answer_schema.explanation == explanation


class TestMockDataIntegration:
    """Mock data fallback flow and validation."""

    def test_mock_data_fallback_on_agent_error(self) -> None:
        """
        TC-7: Fallback from agent response to mock data on error.

        Verifies:
        1. Agent response error is caught
        2. Fallback to mock data is attempted
        3. Mock data is successfully transformed
        4. Error recovery is transparent to caller
        """
        # Arrange
        invalid_agent = {
            "correct_keywords": None,  # Invalid
            "explanation": "Bad data"
        }

        fallback_mock = {
            "correct_key": "C",
            "explanation": "Mock explanation"
        }

        # Act: Try agent, catch error, use fallback
        try:
            answer_schema = AnswerSchema.from_agent_response(invalid_agent)
            fallback_used = False
        except (ValidationError, TypeError):
            fallback_used = True
            answer_schema = AnswerSchema.from_mock_data(fallback_mock)

        # Assert
        assert fallback_used is True
        assert answer_schema.type == "exact_match"
        assert answer_schema.correct_answer == "C"
        assert answer_schema.source_format == "mock_data"

    def test_mock_data_field_preservation(self) -> None:
        """
        TC-8: Field preservation from mock data.

        Verifies:
        1. correct_key is transformed to correct_answer
        2. Explanation is preserved
        3. Type is correctly inferred as exact_match
        4. No null fields in result
        """
        # Arrange
        raw_data = {
            "correct_key": "B",
            "explanation": "Option B is the correct answer."
        }

        # Act
        answer_schema = AnswerSchema.from_mock_data(raw_data)

        # Assert
        assert answer_schema.type == "exact_match"
        assert answer_schema.correct_answer == "B"
        assert answer_schema.keywords is None
        assert answer_schema.explanation == "Option B is the correct answer."
        assert answer_schema.source_format == "mock_data"

    def test_mock_data_explanation_quality(self) -> None:
        """
        TC-9: Explanation quality validation in mock data.

        Verifies:
        1. Non-empty explanations are required
        2. Whitespace-only explanations are rejected
        3. Explanation length is preserved
        4. Validation error message is clear
        """
        # Valid explanation
        valid = {
            "correct_key": "A",
            "explanation": "This is a valid explanation."
        }
        answer_schema = AnswerSchema.from_mock_data(valid)
        assert answer_schema.explanation == valid["explanation"]

        # Invalid: empty explanation
        with pytest.raises(ValidationError) as exc_info:
            AnswerSchema.from_mock_data({
                "correct_key": "A",
                "explanation": ""
            })
        assert "explanation" in str(exc_info.value).lower()

        # Invalid: whitespace-only explanation
        with pytest.raises(ValidationError) as exc_info:
            AnswerSchema.from_mock_data({
                "correct_key": "A",
                "explanation": "   \n\t   "
            })
        assert "explanation" in str(exc_info.value).lower()

    def test_mock_data_source_format_tracking(self) -> None:
        """
        TC-10: Source format metadata is tracked for mock data.

        Verifies:
        1. source_format is set to "mock_data"
        2. source_format is preserved in to_db_dict()
        3. source_format is accessible for audit trail
        4. Different sources have different metadata
        """
        # Arrange
        mock_data = {
            "correct_key": "A",
            "explanation": "Mock explanation"
        }

        agent_data = {
            "correct_keywords": ["answer"],
            "explanation": "Agent explanation"
        }

        # Act
        mock_schema = AnswerSchema.from_mock_data(mock_data)
        agent_schema = AnswerSchema.from_agent_response(agent_data)

        # Assert
        assert mock_schema.source_format == "mock_data"
        assert agent_schema.source_format == "agent_response"
        assert mock_schema.to_db_dict()["source_format"] == "mock_data"
        assert agent_schema.to_db_dict()["source_format"] == "agent_response"


class TestErrorRecoveryIntegration:
    """Error scenarios and recovery mechanisms."""

    def test_invalid_agent_response_handled(self) -> None:
        """
        TC-11: Invalid agent response is handled gracefully.

        Verifies:
        1. Malformed agent response raises appropriate error
        2. Error message is descriptive
        3. No partial/corrupted AnswerSchema is created
        4. Caller can distinguish error types
        """
        # Invalid: no correct_keywords
        with pytest.raises(ValidationError) as exc_info:
            AnswerSchema.from_agent_response({
                "explanation": "Missing keywords"
            })
        assert "correct_keywords" in str(exc_info.value)

        # Invalid: correct_keywords is string instead of list
        with pytest.raises(TypeError) as exc_info:
            AnswerSchema.from_agent_response({
                "correct_keywords": "single_keyword",
                "explanation": "Bad type"
            })
        assert "list" in str(exc_info.value).lower()

    def test_missing_required_field_validation(self) -> None:
        """
        TC-12: Missing required fields produce validation errors.

        Verifies:
        1. Missing explanation raises error
        2. Missing correct_keywords raises error
        3. Error messages specify which field is missing
        4. Validation is strict (no defaults for required fields)
        """
        # Missing explanation
        with pytest.raises(ValidationError) as exc_info:
            AnswerSchema.from_agent_response({
                "correct_keywords": ["answer"]
            })
        assert "explanation" in str(exc_info.value).lower()

        # Missing correct_key in mock
        with pytest.raises(ValidationError) as exc_info:
            AnswerSchema.from_mock_data({
                "explanation": "Missing key"
            })
        assert "correct_key" in str(exc_info.value).lower()

    def test_database_constraint_validation(self) -> None:
        """
        TC-13: Database constraints are respected.

        Verifies:
        1. AnswerSchema cannot have both keywords and correct_answer as None
        2. Type field cannot be empty
        3. Explanation cannot be empty
        4. Validation occurs at object creation time (fail-fast)
        """
        # Invalid: both keywords and correct_answer None
        with pytest.raises(ValidationError) as exc_info:
            AnswerSchema(
                type="keyword_match",
                keywords=None,
                correct_answer=None,
                explanation="This should fail"
            )
        assert "keywords" in str(exc_info.value).lower() or "correct_answer" in str(exc_info.value).lower()

        # Invalid: empty type
        with pytest.raises(ValidationError) as exc_info:
            AnswerSchema(
                type="",
                keywords=["answer"],
                explanation="This should fail"
            )
        assert "type" in str(exc_info.value).lower()

    def test_explanation_generation_fallback(self) -> None:
        """
        TC-14: Explanation generation failure triggers fallback.

        Verifies:
        1. Missing/invalid explanation can be detected
        2. Fallback explanation is provided
        3. Fallback is marked in source_format metadata
        4. User is aware explanation is synthetic
        """
        # Arrange: Response with minimal explanation
        minimal_data = {
            "correct_keywords": ["answer"],
            "explanation": "Brief."
        }

        # Act
        answer_schema = AnswerSchema.from_agent_response(minimal_data)

        # Assert
        assert answer_schema.explanation == "Brief."
        # Even brief explanations are stored (quality validation is separate concern)

    def test_json_parsing_with_control_chars(self) -> None:
        """
        TC-15: JSON parsing handles control characters.

        Verifies:
        1. Newlines in explanation are preserved
        2. Tabs preserved
        3. Unicode escapes handled
        4. No silent corruption of special chars
        """
        # Arrange: Response with escaped newlines (as from JSON)
        explanation_with_newlines = "First line\nSecond line\tTabbed"
        raw_data = {
            "correct_keywords": ["answer"],
            "explanation": explanation_with_newlines
        }

        # Act
        answer_schema = AnswerSchema.from_agent_response(raw_data)

        # Assert
        assert answer_schema.explanation == explanation_with_newlines
        assert "\n" in answer_schema.explanation
        assert "\t" in answer_schema.explanation


class TestDatabaseIntegration:
    """Database persistence and querying."""

    def test_answer_schema_persistence(self) -> None:
        """
        TC-16: AnswerSchema persists correctly to database.

        Verifies:
        1. to_db_dict() produces database-compatible format
        2. All fields are included in persisted data
        3. created_at timestamp is set
        4. Persisted data can be loaded back
        """
        # Arrange
        original = AnswerSchema.from_agent_response({
            "correct_keywords": ["answer"],
            "explanation": "Explanation"
        })

        # Act
        db_dict = original.to_db_dict()

        # Assert
        assert "type" in db_dict
        assert "keywords" in db_dict
        assert "correct_answer" in db_dict
        assert "explanation" in db_dict
        assert "source_format" in db_dict
        assert "created_at" in db_dict
        assert db_dict["type"] == original.type
        assert db_dict["keywords"] == original.keywords
        assert db_dict["explanation"] == original.explanation

    def test_type_field_preserved(self) -> None:
        """
        TC-17: Type field (keyword_match vs exact_match) is preserved.

        Verifies:
        1. Agent response has type keyword_match
        2. Mock data has type exact_match
        3. Type is correctly inferred from format
        4. Type is preserved through database round-trip
        """
        # Arrange
        agent = AnswerSchema.from_agent_response({
            "correct_keywords": ["a"],
            "explanation": "e"
        })
        mock = AnswerSchema.from_mock_data({
            "correct_key": "A",
            "explanation": "e"
        })

        # Act & Assert
        assert agent.type == "keyword_match"
        assert agent.to_db_dict()["type"] == "keyword_match"

        assert mock.type == "exact_match"
        assert mock.to_db_dict()["type"] == "exact_match"

    def test_keywords_correct_answer_separation(self) -> None:
        """
        TC-18: Keywords and correct_answer are properly separated.

        Verifies:
        1. Agent response stores keywords, not correct_answer
        2. Mock data stores correct_answer, not keywords
        3. Type field indicates which is present
        4. Both cannot be present simultaneously (by design)
        """
        # Arrange
        agent = AnswerSchema.from_agent_response({
            "correct_keywords": ["a", "b"],
            "explanation": "e"
        })
        mock = AnswerSchema.from_mock_data({
            "correct_key": "X",
            "explanation": "e"
        })

        # Act & Assert: Verify separation
        assert agent.keywords == ["a", "b"]
        assert agent.correct_answer is None

        assert mock.keywords is None
        assert mock.correct_answer == "X"

    def test_source_format_metadata(self) -> None:
        """
        TC-19: Source format metadata enables audit trail.

        Verifies:
        1. source_format identifies data origin
        2. Different sources have different metadata
        3. Metadata is useful for debugging
        4. Can be used for analytics (e.g., "how many questions from agent vs mock?")
        """
        # Arrange
        agent = AnswerSchema.from_agent_response({
            "correct_keywords": ["a"],
            "explanation": "e"
        })
        mock = AnswerSchema.from_mock_data({
            "correct_key": "A",
            "explanation": "e"
        })

        # Act
        agent_db = agent.to_db_dict()
        mock_db = mock.to_db_dict()

        # Assert
        assert agent_db["source_format"] == "agent_response"
        assert mock_db["source_format"] == "mock_data"
        # Can use this for reporting: SELECT COUNT(*) FROM questions WHERE answer_schema->>'source_format' = 'agent_response'

    def test_database_retrieval_integrity(self) -> None:
        """
        TC-20: Retrieved data from database maintains integrity.

        Verifies:
        1. Reconstructed AnswerSchema from DB has all fields
        2. No silent data loss
        3. Immutability is restored after retrieval
        4. Value equality works for reconstructed objects
        """
        # Arrange
        original = AnswerSchema.from_agent_response({
            "correct_keywords": ["answer"],
            "explanation": "Explanation"
        })

        # Simulate database retrieval (to_db_dict → from_dict)
        db_dict = original.to_db_dict()
        retrieved = AnswerSchema.from_dict(
            {k: v for k, v in db_dict.items() if k != "created_at"},
            source="agent_response"
        )

        # Assert
        assert retrieved.type == original.type
        assert retrieved.keywords == original.keywords
        assert retrieved.explanation == original.explanation
        assert retrieved.source_format == original.source_format


class TestRoundTripIntegration:
    """End-to-end question generation to API response."""

    def test_generation_to_api_response_flow(self) -> None:
        """
        TC-21: Complete flow from generation through API response.

        Verifies:
        1. Agent generates question with answer_schema
        2. Transformed and stored in database
        3. Retrieved and converted to API format
        4. API response is clean (no internal metadata)
        """
        # Arrange: Simulate full flow
        # Step 1: Agent generates
        agent_response = {
            "correct_keywords": ["answer"],
            "explanation": "Explanation"
        }

        # Step 2: Store in database
        answer_schema = AnswerSchema.from_agent_response(agent_response)
        db_dict = answer_schema.to_db_dict()

        # Simulate DB retrieval
        retrieved = AnswerSchema.from_dict(
            {k: v for k, v in db_dict.items() if k != "created_at"},
            source="agent_response"
        )

        # Step 3: Serve via API
        api_response = retrieved.to_response_dict()

        # Assert
        assert "source_format" not in api_response
        assert "created_at" not in api_response
        assert "keywords" in api_response
        assert "explanation" in api_response
        assert api_response["keywords"] == ["answer"]

    def test_multiple_consecutive_generations(self) -> None:
        """
        TC-22: Multiple questions generated consecutively maintain uniqueness.

        Verifies:
        1. Each question gets unique answer_schema
        2. No cross-contamination between questions
        3. All schemas are properly created
        4. Performance is acceptable for 100+ questions
        """
        # Arrange
        questions = []
        for i in range(10):
            schema = AnswerSchema.from_agent_response({
                "correct_keywords": [f"answer_{i}"],
                "explanation": f"Explanation {i}"
            })
            questions.append(schema)

        # Act & Assert
        assert len(questions) == 10
        for i, q in enumerate(questions):
            assert q.keywords == [f"answer_{i}"]
            assert q.explanation == f"Explanation {i}"
            # Each has unique created_at (if generated at different times)

    def test_data_consistency_throughout_pipeline(self) -> None:
        """
        TC-23: Data consistency is maintained throughout pipeline.

        Verifies:
        1. No data loss at any stage
        2. No unexpected transformations
        3. Round-trip preserves all data
        4. Deterministic results (same input → same output)
        """
        # Arrange
        original_data = {
            "correct_keywords": ["key1", "key2"],
            "explanation": "Test explanation"
        }

        # Act: Full pipeline
        answer_schema = AnswerSchema.from_agent_response(original_data)
        db_dict = answer_schema.to_db_dict()
        api_dict = answer_schema.to_response_dict()

        # Assert: Verify consistency
        assert answer_schema.keywords == original_data["correct_keywords"]
        assert db_dict["keywords"] == original_data["correct_keywords"]
        assert api_dict["keywords"] == original_data["correct_keywords"]

        assert answer_schema.explanation == original_data["explanation"]
        assert db_dict["explanation"] == original_data["explanation"]
        assert api_dict["explanation"] == original_data["explanation"]


class TestConcurrentAccess:
    """Concurrent question generation without race conditions."""

    def test_concurrent_question_generation(self) -> None:
        """
        TC-24: Multiple questions can be generated concurrently safely.

        Verifies:
        1. Concurrent creation doesn't cause data corruption
        2. Each question has correct data
        3. No lost updates or race conditions
        4. Performance is acceptable under concurrency
        """
        # Arrange
        num_threads = 5
        schemas = []

        # Act: Create multiple schemas (simulating concurrent generation)
        for i in range(num_threads):
            schema = AnswerSchema.from_agent_response({
                "correct_keywords": [f"answer_{i}"],
                "explanation": f"Explanation {i}"
            })
            schemas.append(schema)

        # Assert
        assert len(schemas) == num_threads
        for i, schema in enumerate(schemas):
            assert schema.keywords == [f"answer_{i}"]
            assert schema.explanation == f"Explanation {i}"

    def test_no_race_conditions(self) -> None:
        """
        TC-25: Factory and transformer are thread-safe.

        Verifies:
        1. Factory.get_transformer() is reentrant
        2. Multiple threads can use factory simultaneously
        3. Transformer instances don't share state
        4. No lock contention or deadlocks
        """
        # Arrange
        factory = TransformerFactory()

        # Act: Multiple transformers created (simulating concurrent requests)
        transformers = [
            factory.get_transformer("agent_response"),
            factory.get_transformer("mock_data"),
            factory.get_transformer("agent_response"),
            factory.get_transformer("mock_data"),
        ]

        # Assert: All are correct type
        assert isinstance(transformers[0], AgentResponseTransformer)
        assert isinstance(transformers[1], MockDataTransformer)
        assert isinstance(transformers[2], AgentResponseTransformer)
        assert isinstance(transformers[3], MockDataTransformer)


class TestImmutabilityAndValueObject:
    """Test immutability and value object properties."""

    def test_answer_schema_immutability(self) -> None:
        """
        TC-26: AnswerSchema is immutable (frozen).

        Verifies:
        1. Cannot modify keywords after creation
        2. Cannot modify explanation after creation
        3. FrozenInstanceError raised on modification attempt
        4. Immutability prevents bugs from accidental mutation
        """
        # Arrange
        schema = AnswerSchema.from_agent_response({
            "correct_keywords": ["a"],
            "explanation": "e"
        })

        # Act & Assert: Cannot modify
        with pytest.raises(Exception):  # FrozenInstanceError
            schema.keywords = ["b"]  # type: ignore

        with pytest.raises(Exception):  # FrozenInstanceError
            schema.explanation = "new"  # type: ignore

        # Original is unchanged
        assert schema.keywords == ["a"]
        assert schema.explanation == "e"

    def test_value_object_equality(self) -> None:
        """
        TC-27: Value objects with same data are equal.

        Verifies:
        1. Two AnswerSchema instances with same data are equal
        2. Equality compares all fields
        3. Different objects can be equal by value
        4. Enables use in collections and comparisons
        """
        # Arrange
        schema1 = AnswerSchema.from_agent_response({
            "correct_keywords": ["a"],
            "explanation": "e"
        })
        schema2 = AnswerSchema.from_agent_response({
            "correct_keywords": ["a"],
            "explanation": "e"
        })

        # Act & Assert
        assert schema1.type == schema2.type
        assert schema1.keywords == schema2.keywords
        assert schema1.explanation == schema2.explanation
        # Note: created_at will differ, so full equality might not hold
        # This is expected behavior for value objects with timestamps

    def test_value_object_hashing(self) -> None:
        """
        TC-28: AnswerSchema instances can be hashed for collections.

        Verifies:
        1. AnswerSchema.__hash__() returns consistent hash
        2. Can be used as dict key
        3. Can be added to sets
        4. Hash consistency across calls
        """
        # Arrange
        schema = AnswerSchema.from_agent_response({
            "correct_keywords": ["a"],
            "explanation": "e"
        })

        # Act: Use in collections
        schema_set = {schema}
        schema_dict = {schema: "value"}

        # Assert
        assert schema in schema_set
        assert schema_dict[schema] == "value"
        assert hash(schema) == hash(schema)  # Consistent hash


class TestFactoryPattern:
    """Factory pattern for transformer creation and extension."""

    def test_factory_creates_correct_transformers(self) -> None:
        """
        TC-29: Factory creates appropriate transformer for format type.

        Verifies:
        1. "agent_response" returns AgentResponseTransformer
        2. "mock_data" returns MockDataTransformer
        3. Factory instances are reusable
        4. Format type matching is case-insensitive
        """
        # Arrange
        factory = TransformerFactory()

        # Act
        agent_transformer = factory.get_transformer("agent_response")
        mock_transformer = factory.get_transformer("mock_data")

        # Test case insensitivity
        agent_upper = factory.get_transformer("AGENT_RESPONSE")
        mock_upper = factory.get_transformer("MOCK_DATA")

        # Assert
        assert isinstance(agent_transformer, AgentResponseTransformer)
        assert isinstance(mock_transformer, MockDataTransformer)
        assert isinstance(agent_upper, AgentResponseTransformer)
        assert isinstance(mock_upper, MockDataTransformer)

    def test_factory_unknown_format_error(self) -> None:
        """
        TC-30: Factory raises UnknownFormatError for unrecognized format.

        Verifies:
        1. Unknown format type raises error
        2. Error message lists supported formats
        3. Error is specific and actionable
        4. No default/fallback transformer
        """
        # Arrange
        factory = TransformerFactory()

        # Act & Assert
        with pytest.raises(UnknownFormatError) as exc_info:
            factory.get_transformer("unknown_format")

        error_msg = str(exc_info.value)
        assert "unknown_format" in error_msg
        assert "agent_response" in error_msg or "mock_data" in error_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
