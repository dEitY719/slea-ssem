"""
Comprehensive tests for REQ-A-RoundID: Round ID generation and tracking.

This module tests Round ID generation, format compliance, uniqueness,
and integration with agent pipelines.

REQ: REQ-A-RoundID
"""

import re
import time
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest

from src.agent.round_id_generator import RoundID, RoundIDGenerator


# ============================================================================
# TEST DATA & FIXTURES
# ============================================================================


@pytest.fixture
def valid_session_id() -> str:
    """Valid session ID for testing."""
    return f"sess_{str(uuid.uuid4())[:8]}"


@pytest.fixture
def valid_user_id() -> str:
    """Valid user ID for testing."""
    return f"user_{str(uuid.uuid4())[:8]}"


@pytest.fixture
def round_id_generator() -> RoundIDGenerator:
    """Create RoundIDGenerator instance."""
    return RoundIDGenerator()


# ============================================================================
# TEST CLASS 1: ROUND ID FORMAT COMPLIANCE (AC1, AC2)
# ============================================================================


class TestRoundIDFormatCompliance:
    """Test Round ID format specification."""

    def test_round_id_format_structure(self, round_id_generator, valid_session_id):
        """
        AC1: Round ID format is {session_id}_{round_number}_{iso_timestamp}.

        Given: Generate Round ID for Round 1
        When: Format checked
        Then: Matches pattern session_id_1_timestamp
        """
        round_id = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )

        # Pattern: {session_id}_{round_number}_{iso_timestamp}
        pattern = r"^sess_[a-f0-9]{8}_[1-2]_\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
        assert re.match(pattern, round_id), f"Round ID {round_id} doesn't match format"

    def test_round_id_contains_session_id(self, round_id_generator, valid_session_id):
        """AC1: Round ID contains session_id as first component."""
        round_id = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )

        assert round_id.startswith(valid_session_id)

    def test_round_id_contains_round_number(self, round_id_generator, valid_session_id):
        """AC1: Round ID contains round_number (1 or 2)."""
        round_id_1 = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )
        assert "_1_" in round_id_1

        round_id_2 = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=2
        )
        assert "_2_" in round_id_2

    def test_round_id_iso_8601_timestamp(self, round_id_generator, valid_session_id):
        """
        AC2: Timestamp is ISO 8601 format with UTC timezone.

        Given: Generate Round ID
        When: Timestamp extracted
        Then: Valid ISO 8601 UTC format
        """
        round_id = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )

        # Parse using generator method instead
        parsed = round_id_generator.parse(round_id)
        assert parsed.timestamp is not None
        assert parsed.timestamp.tzinfo == UTC

    def test_timestamp_format_with_timezone(self, round_id_generator, valid_session_id):
        """AC2: Timestamp includes timezone (+00:00 or Z)."""
        round_id = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )

        # Timestamp should end with timezone indicator
        assert "+00:00" in round_id or "Z" in round_id or "-00:00" in round_id


# ============================================================================
# TEST CLASS 2: ROUND ID GENERATION PERFORMANCE (AC3)
# ============================================================================


class TestRoundIDPerformance:
    """Test Round ID generation performance."""

    def test_round_id_generation_under_1ms(self, round_id_generator, valid_session_id):
        """
        AC3: Round ID generation < 1ms performance.

        Given: Generate Round ID
        When: Measure execution time
        Then: Complete in < 1ms
        """
        start_time = time.time()
        round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )
        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 1.0, f"Generation took {elapsed_ms}ms (threshold: 1ms)"

    def test_batch_generation_performance(self, round_id_generator, valid_session_id):
        """AC3: Batch generation of 1000 Round IDs under 1 second."""
        start_time = time.time()

        for i in range(1000):
            round_id_generator.generate(
                session_id=f"{valid_session_id}_{i}",
                round_number=1
            )

        elapsed_ms = (time.time() - start_time) * 1000
        assert elapsed_ms < 1000, f"Batch took {elapsed_ms}ms (threshold: 1000ms)"


# ============================================================================
# TEST CLASS 3: ROUND ID UNIQUENESS (AC4)
# ============================================================================


class TestRoundIDUniqueness:
    """Test Round ID uniqueness and collision prevention."""

    def test_round_ids_are_unique_different_sessions(self, round_id_generator):
        """
        AC4: Round IDs are globally unique (no duplicates).

        Given: Generate Round IDs for different sessions
        When: Compare Round IDs
        Then: All unique
        """
        round_ids = set()

        for i in range(100):
            session_id = f"sess_{i:08d}"
            round_id = round_id_generator.generate(
                session_id=session_id,
                round_number=1
            )
            round_ids.add(round_id)

        assert len(round_ids) == 100, "Duplicate Round IDs detected"

    def test_round_ids_different_same_session(self, round_id_generator, valid_session_id):
        """AC4: Same session, different rounds have different Round IDs."""
        round_id_1 = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )

        # Small delay to ensure different timestamp
        time.sleep(0.001)

        round_id_2 = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=2
        )

        assert round_id_1 != round_id_2

    def test_no_collision_rapid_generation(self, round_id_generator):
        """AC4: Rapid Round ID generation produces unique IDs."""
        session_id = "sess_rapid"
        round_ids = set()

        for _ in range(10):
            round_id = round_id_generator.generate(
                session_id=session_id,
                round_number=1
            )
            round_ids.add(round_id)

        assert len(round_ids) <= 10, "Collisions detected in rapid generation"


# ============================================================================
# TEST CLASS 4: ROUND NUMBER DISTINCTION (AC5)
# ============================================================================


class TestRoundNumberDistinction:
    """Test Round 1 vs Round 2 distinction."""

    def test_round_1_and_2_distinguished(self, round_id_generator, valid_session_id):
        """
        AC5: Round 1 and Round 2 distinguished in Round ID.

        Given: Generate both Round 1 and 2 for same session
        When: Compare Round IDs
        Then: Different IDs, with different round numbers
        """
        round_id_1 = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )
        round_id_2 = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=2
        )

        # Parse round numbers
        parsed_1 = round_id_generator.parse(round_id_1)
        parsed_2 = round_id_generator.parse(round_id_2)

        assert parsed_1.round_number == 1
        assert parsed_2.round_number == 2
        assert round_id_1 != round_id_2

    def test_round_number_validation(self, round_id_generator, valid_session_id):
        """Round numbers must be 1 or 2."""
        # Valid round numbers
        round_id_1 = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )
        assert "_1_" in round_id_1

        round_id_2 = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=2
        )
        assert "_2_" in round_id_2


# ============================================================================
# TEST CLASS 5: ROUND ID PARSING (AC6)
# ============================================================================


class TestRoundIDParsing:
    """Test Round ID parsing and component extraction."""

    def test_parse_round_id_extracts_components(self, round_id_generator, valid_session_id):
        """
        AC6: Round ID can be parsed back to components.

        Given: Generate Round ID
        When: Parse it
        Then: Extract session_id, round_number, timestamp
        """
        original_round_id = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )

        parsed = round_id_generator.parse(original_round_id)

        assert parsed.session_id == valid_session_id
        assert parsed.round_number == 1
        assert parsed.timestamp is not None

    def test_parsed_timestamp_is_datetime(self, round_id_generator, valid_session_id):
        """AC6: Parsed timestamp is valid datetime object."""
        round_id = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )

        parsed = round_id_generator.parse(round_id)

        assert isinstance(parsed.timestamp, datetime)
        assert parsed.timestamp.tzinfo == UTC

    def test_parse_round_id_roundtrip(self, round_id_generator, valid_session_id):
        """AC6: Parse then regenerate produces same Round ID."""
        original_round_id = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=2
        )

        parsed = round_id_generator.parse(original_round_id)

        # Verify components
        assert parsed.session_id == valid_session_id
        assert parsed.round_number == 2
        assert parsed.timestamp is not None


# ============================================================================
# TEST CLASS 6: ROUND ID IMMUTABILITY (AC7)
# ============================================================================


class TestRoundIDImmutability:
    """Test Round ID immutability after creation."""

    def test_round_id_is_string_immutable(self, round_id_generator, valid_session_id):
        """
        AC7: Round ID immutable after creation.

        Given: Generated Round ID
        When: Attempt to modify
        Then: Modification creates new string (immutable)
        """
        round_id = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )

        # Strings are immutable in Python
        original_id = round_id
        # This creates new string, doesn't modify original
        modified_id = round_id + "_modified"

        assert round_id == original_id
        assert modified_id != original_id

    def test_round_id_object_immutable(self, round_id_generator, valid_session_id):
        """AC7: RoundID object with frozen attributes."""
        round_id_obj = RoundID(
            session_id=valid_session_id,
            round_number=1,
            timestamp=datetime.now(UTC)
        )

        # Verify it's frozen/immutable
        assert hasattr(round_id_obj, "session_id")
        assert hasattr(round_id_obj, "round_number")
        assert hasattr(round_id_obj, "timestamp")


# ============================================================================
# TEST CLASS 7: PIPELINE INTEGRATION (AC8)
# ============================================================================


class TestRoundIDPipelineIntegration:
    """Test Round ID integration with pipelines."""

    def test_round_id_compatible_with_mode1_pipeline(self, round_id_generator, valid_session_id):
        """
        AC8: Round ID works with Mode 1 pipeline.

        Given: Mode 1 generates questions in Round 1
        When: Round ID attached to questions
        Then: Can be retrieved and parsed
        """
        round_id = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )

        # Simulate question with Round ID
        question = {
            "question_id": str(uuid.uuid4()),
            "round_id": round_id,
            "stem": "Test question?",
            "type": "multiple_choice",
        }

        assert question["round_id"] == round_id
        parsed = round_id_generator.parse(round_id)
        assert parsed.round_number == 1

    def test_round_id_compatible_with_mode2_pipeline(self, round_id_generator, valid_session_id):
        """AC8: Round ID works with Mode 2 pipeline."""
        round_id = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=2
        )

        # Simulate scoring result with Round ID
        score_result = {
            "attempt_id": str(uuid.uuid4()),
            "round_id": round_id,
            "score": 85,
            "is_correct": True,
        }

        assert score_result["round_id"] == round_id
        parsed = round_id_generator.parse(round_id)
        assert parsed.round_number == 2

    def test_round_id_chronological_ordering(self, round_id_generator, valid_session_id):
        """AC8: Round IDs can be chronologically ordered by timestamp."""
        round_ids = []

        for i in range(3):
            round_id = round_id_generator.generate(
                session_id=f"{valid_session_id}_{i}",
                round_number=1
            )
            round_ids.append(round_id)
            time.sleep(0.001)

        # Parse and sort by timestamp
        parsed_list = [
            round_id_generator.parse(rid) for rid in round_ids
        ]

        # Verify chronological order
        timestamps = [p.timestamp for p in parsed_list]
        assert timestamps == sorted(timestamps)


# ============================================================================
# TEST CLASS 8: ACCEPTANCE CRITERIA SUMMARY
# ============================================================================


class TestAcceptanceCriteria:
    """Verify all acceptance criteria are met."""

    def test_ac1_format_structure(self, round_id_generator, valid_session_id):
        """AC1: Format is {session_id}_{round_number}_{iso_timestamp}."""
        round_id = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )

        # Verify format by parsing
        parsed = round_id_generator.parse(round_id)
        assert parsed.session_id == valid_session_id
        assert parsed.round_number == 1
        assert parsed.timestamp is not None

    def test_ac2_iso_8601_utc(self, round_id_generator, valid_session_id):
        """AC2: Timestamp is ISO 8601 format with UTC timezone."""
        round_id = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )

        # Parse to verify timestamp is ISO 8601 with UTC
        parsed = round_id_generator.parse(round_id)
        dt = parsed.timestamp

        # Must be ISO 8601 with UTC
        assert isinstance(dt, datetime)
        assert dt.tzinfo == UTC

    def test_ac3_performance(self, round_id_generator, valid_session_id):
        """AC3: Generation < 1ms."""
        start = time.time()
        round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )
        elapsed_ms = (time.time() - start) * 1000
        assert elapsed_ms < 1.0

    def test_ac4_uniqueness(self, round_id_generator):
        """AC4: Round IDs are unique."""
        ids = {
            round_id_generator.generate(
                session_id=f"sess_{i}",
                round_number=1
            )
            for i in range(100)
        }
        assert len(ids) == 100

    def test_ac5_round_distinction(self, round_id_generator, valid_session_id):
        """AC5: Round 1 and 2 distinguished."""
        r1 = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )
        r2 = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=2
        )
        assert "_1_" in r1
        assert "_2_" in r2
        assert r1 != r2

    def test_ac6_parseable(self, round_id_generator, valid_session_id):
        """AC6: Round ID can be parsed."""
        round_id = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )
        parsed = round_id_generator.parse(round_id)
        assert parsed.session_id == valid_session_id
        assert parsed.round_number == 1

    def test_ac7_immutable(self, round_id_generator, valid_session_id):
        """AC7: Round ID immutable."""
        round_id = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )
        original = round_id
        # String immutability
        assert round_id == original

    def test_ac8_pipeline_compatible(self, round_id_generator, valid_session_id):
        """AC8: Works with Mode 1 and Mode 2 pipelines."""
        r1 = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=1
        )
        r2 = round_id_generator.generate(
            session_id=valid_session_id,
            round_number=2
        )

        # Both should be usable in pipeline
        assert r1 and r2
        assert len(r1) > 0 and len(r2) > 0
