"""
Test suite for Mode 2 Pipeline parallel batch scoring.

REQ: REQ-A-Mode2-Parallel (Phase 3)

Tests for asyncio.gather-based parallel answer scoring with graceful degradation.
Focus on:
- Concurrent execution performance
- Error handling and graceful degradation
- Metric calculation accuracy
- Edge cases and boundary conditions
"""

import asyncio
import time
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent.pipeline.mode2_pipeline import Mode2Pipeline


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mode2_pipeline():
    """Create Mode2Pipeline instance for testing."""
    return Mode2Pipeline(session_id="sess_test_001")


def create_answer_dict(
    question_id: str,
    question_type: str = "multiple_choice",
    user_answer: str = "A",
    correct_answer: str | None = "A",
    correct_keywords: list[str] | None = None,
    user_id: str = "user_001",
    difficulty: int = 5,
    category: str = "AI",
) -> dict:
    """Helper to create answer dictionary."""
    answer = {
        "user_id": user_id,
        "question_id": question_id,
        "question_type": question_type,
        "user_answer": user_answer,
        "difficulty": difficulty,
        "category": category,
    }
    if correct_answer is not None:
        answer["correct_answer"] = correct_answer
    if correct_keywords is not None:
        answer["correct_keywords"] = correct_keywords
    return answer


def create_score_result(
    question_id: str,
    is_correct: bool = True,
    score: int = 100,
    explanation: str = "Good answer",
) -> dict:
    """Helper to create scoring result."""
    return {
        "attempt_id": str(uuid.uuid4()),
        "session_id": "sess_test_001",
        "question_id": question_id,
        "user_id": "user_001",
        "is_correct": is_correct,
        "score": score,
        "explanation": explanation,
        "keyword_matches": [],
        "feedback": None,
        "graded_at": datetime.now(UTC).isoformat(),
    }


# ============================================================================
# HAPPY PATH TESTS (All answers succeed)
# ============================================================================


@pytest.mark.asyncio
async def test_score_answers_parallel_all_success_small_batch(mode2_pipeline):
    """
    Test: Parallel scoring of 5 answers, all succeed.

    AC1: All 5 answers scored successfully
    AC3: Metrics calculated correctly
    """
    answers = [
        create_answer_dict(f"q_{i:02d}") for i in range(1, 6)
    ]

    with patch.object(
        mode2_pipeline, "score_answer", return_value=create_score_result("q_01")
    ) as mock_score:
        response = await mode2_pipeline.score_answers_batch_parallel(answers)

    # All answers succeeded
    assert len(response["results"]) == 5, "Should have 5 successful results"
    assert response["batch_stats"]["successful_count"] == 5
    assert response["batch_stats"]["failed_count"] == 0
    assert response["batch_stats"]["total_count"] == 5
    assert len(response["failed_question_ids"]) == 0

    # Metrics correct
    assert response["batch_stats"]["average_score"] == 100.0
    assert response["batch_stats"]["correct_count"] == 5
    assert response["batch_stats"]["correct_rate"] == 1.0

    # All mocked
    assert mock_score.call_count == 5


@pytest.mark.asyncio
async def test_score_answers_parallel_medium_batch(mode2_pipeline):
    """
    Test: Parallel scoring of 20 answers, all succeed.

    AC1: All 20 answers scored successfully
    AC4: Concurrency speedup vs sequential
    """
    answers = [
        create_answer_dict(f"q_{i:03d}") for i in range(1, 21)
    ]

    # Mock with small delays to simulate LLM calls
    async def async_score_side_effect(**kwargs):
        await asyncio.sleep(0.05)  # 50ms per answer
        return create_score_result(kwargs.get("question_id", "q_00"))

    with patch.object(
        mode2_pipeline, "a_score_answer", side_effect=async_score_side_effect
    ):
        start = time.time()
        response = await mode2_pipeline.score_answers_batch_parallel(answers)
        elapsed = time.time() - start

    # All succeeded
    assert len(response["results"]) == 20
    assert response["batch_stats"]["successful_count"] == 20

    # Parallel execution should be much faster than 20 * 0.05 = 1.0s
    # With asyncio.gather, should be ~0.05s + overhead (~0.2s typical)
    assert elapsed < 0.5, f"Parallel should be faster, took {elapsed:.2f}s"


@pytest.mark.asyncio
async def test_score_answers_parallel_max_batch_50(mode2_pipeline):
    """
    Test: Parallel scoring of 50 answers (max limit), all succeed.

    AC1: Handles maximum batch size
    AC2: Resource efficient
    """
    answers = [
        create_answer_dict(f"q_{i:03d}") for i in range(1, 51)
    ]

    with patch.object(
        mode2_pipeline, "a_score_answer", return_value=create_score_result("q_00")
    ):
        response = await mode2_pipeline.score_answers_batch_parallel(answers)

    # All succeeded
    assert response["batch_stats"]["successful_count"] == 50
    assert response["batch_stats"]["total_count"] == 50
    assert len(response["results"]) == 50


# ============================================================================
# GRACEFUL DEGRADATION TESTS (Partial failures)
# ============================================================================


@pytest.mark.asyncio
async def test_score_answers_partial_failures_3_of_5(mode2_pipeline):
    """
    Test: 5 answers, 3 succeed, 2 fail.

    AC2: Graceful degradation - failed answers don't stop batch
    AC3: Metrics calculated only from successful answers
    """
    answers = [
        create_answer_dict("q_01"),  # Success
        create_answer_dict("q_02"),  # Success
        create_answer_dict("q_03"),  # Failure
        create_answer_dict("q_04"),  # Success
        create_answer_dict("q_05"),  # Failure
    ]

    async def async_score_side_effect(**kwargs):
        qid = kwargs.get("question_id", "q_00")
        if qid in ["q_03", "q_05"]:
            raise ValueError(f"Mock error for {qid}")
        return create_score_result(qid, score=80)

    with patch.object(
        mode2_pipeline, "a_score_answer", side_effect=async_score_side_effect
    ):
        response = await mode2_pipeline.score_answers_batch_parallel(answers)

    # 3 succeeded, 2 failed
    assert response["batch_stats"]["successful_count"] == 3
    assert response["batch_stats"]["failed_count"] == 2
    assert response["batch_stats"]["total_count"] == 5
    assert len(response["failed_question_ids"]) == 2
    assert "q_03" in response["failed_question_ids"]
    assert "q_05" in response["failed_question_ids"]

    # Metrics only from successful
    assert response["batch_stats"]["average_score"] == 80.0  # (80+80+80)/3
    assert response["batch_stats"]["correct_count"] == 3


@pytest.mark.asyncio
async def test_score_answers_llm_timeout_fallback(mode2_pipeline):
    """
    Test: LLM timeout for short_answer → fallback score.

    AC6: LLM timeout triggers fallback scoring mechanism
    """
    answers = [
        create_answer_dict(
            "q_01",
            question_type="short_answer",
            user_answer="RAG system",
            correct_keywords=["RAG", "retrieval"],
        ),
    ]

    async def async_score_side_effect(**kwargs):
        await asyncio.sleep(0.01)
        raise TimeoutError("LLM timeout")

    with patch.object(
        mode2_pipeline, "a_score_answer", side_effect=async_score_side_effect
    ):
        response = await mode2_pipeline.score_answers_batch_parallel(answers)

    # Should have fallback result
    assert response["batch_stats"]["successful_count"] == 1
    # Fallback result should be included
    assert len(response["results"]) == 1 or len(response["failed_question_ids"]) == 1


@pytest.mark.asyncio
async def test_score_answers_all_failures_5_of_5(mode2_pipeline):
    """
    Test: All 5 answers fail - batch still completes.

    AC2: Graceful degradation - batch completes despite all failures
    """
    answers = [
        create_answer_dict(f"q_{i:02d}") for i in range(1, 6)
    ]

    async def async_score_side_effect(**kwargs):
        raise ValueError("Forced error")

    with patch.object(
        mode2_pipeline, "a_score_answer", side_effect=async_score_side_effect
    ):
        response = await mode2_pipeline.score_answers_batch_parallel(answers)

    # All failed
    assert response["batch_stats"]["successful_count"] == 0
    assert response["batch_stats"]["failed_count"] == 5
    assert response["batch_stats"]["total_count"] == 5
    assert len(response["failed_question_ids"]) == 5
    assert len(response["results"]) == 0

    # Stats should handle empty successful list
    assert response["batch_stats"]["average_score"] == 0.0


@pytest.mark.asyncio
async def test_score_answers_mixed_error_types(mode2_pipeline):
    """
    Test: Mix of different errors (ValueError, TimeoutError, general Exception).

    AC2: All error types handled gracefully
    """
    answers = [
        create_answer_dict("q_01"),  # Success
        create_answer_dict("q_02"),  # ValueError
        create_answer_dict("q_03"),  # TimeoutError
        create_answer_dict("q_04"),  # General Exception
        create_answer_dict("q_05"),  # Success
    ]

    async def async_score_side_effect(**kwargs):
        qid = kwargs.get("question_id", "q_00")
        if qid == "q_02":
            raise ValueError("Validation error")
        elif qid == "q_03":
            raise TimeoutError("LLM timeout")
        elif qid == "q_04":
            raise RuntimeError("Unexpected error")
        return create_score_result(qid, score=85)

    with patch.object(
        mode2_pipeline, "a_score_answer", side_effect=async_score_side_effect
    ):
        response = await mode2_pipeline.score_answers_batch_parallel(answers)

    # 2 succeeded, 3 failed
    assert response["batch_stats"]["successful_count"] == 2
    assert response["batch_stats"]["failed_count"] == 3
    assert len(response["failed_question_ids"]) == 3


# ============================================================================
# CONCURRENCY TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_concurrent_execution_timing_parallel_faster(mode2_pipeline):
    """
    Test: Parallel execution is faster than sequential.

    AC4: 10 answers with 0.1s delay each
    - Sequential: ~1.0s
    - Parallel: ~0.1s + overhead (~0.15s typical)
    """
    answers = [
        create_answer_dict(f"q_{i:02d}") for i in range(1, 11)
    ]

    # Simulate concurrent execution
    call_count = 0

    async def slow_async_score(**kwargs):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.1)  # 100ms per answer
        return create_score_result(kwargs.get("question_id", "q_00"))

    with patch.object(mode2_pipeline, "a_score_answer", side_effect=slow_async_score):
        start = time.time()
        response = await mode2_pipeline.score_answers_batch_parallel(answers)
        elapsed = time.time() - start

    # All succeeded
    assert response["batch_stats"]["successful_count"] == 10

    # Timing: parallel should be ~0.1-0.2s, sequential would be ~1.0s
    assert elapsed < 0.5, f"Parallel should be < 0.5s, was {elapsed:.2f}s"
    assert call_count == 10, "All 10 tasks should have been called"


@pytest.mark.asyncio
async def test_no_race_conditions_concurrent_writes(mode2_pipeline):
    """
    Test: No race conditions in concurrent metric updates.

    AC7: Metrics calculated correctly despite concurrent updates
    """
    answers = [
        create_answer_dict(f"q_{i:02d}", score=50 + i * 5) for i in range(1, 6)
    ]

    async def async_score_with_varying_scores(**kwargs):
        idx = int(kwargs.get("question_id", "q_01").split("_")[1]) - 1
        await asyncio.sleep(0.01 * (5 - idx))  # Stagger completion times
        return create_score_result(
            kwargs.get("question_id", "q_00"), score=50 + idx * 5
        )

    with patch.object(
        mode2_pipeline, "a_score_answer", side_effect=async_score_with_varying_scores
    ):
        response = await mode2_pipeline.score_answers_batch_parallel(answers)

    # All succeeded
    assert response["batch_stats"]["successful_count"] == 5

    # Metrics should be consistent (sum of scores / count)
    expected_avg = (55 + 60 + 65 + 70 + 75) / 5  # = 65.0
    assert abs(response["batch_stats"]["average_score"] - expected_avg) < 0.1


@pytest.mark.asyncio
async def test_task_cancellation_graceful_shutdown(mode2_pipeline):
    """
    Test: Graceful handling of task cancellation.

    AC2: Cancelled tasks don't crash batch
    """
    answers = [
        create_answer_dict(f"q_{i:02d}") for i in range(1, 4)
    ]

    async def cancellable_async_score(**kwargs):
        try:
            await asyncio.sleep(10)  # Long sleep to allow cancellation
            return create_score_result(kwargs.get("question_id", "q_00"))
        except asyncio.CancelledError:
            raise ValueError("Task was cancelled")

    with patch.object(
        mode2_pipeline, "a_score_answer", side_effect=cancellable_async_score
    ):
        # Create task and cancel it shortly after
        task = asyncio.create_task(
            mode2_pipeline.score_answers_batch_parallel(answers)
        )
        await asyncio.sleep(0.05)  # Let it start
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass  # Expected


# ============================================================================
# METRICS VALIDATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_batch_stats_accuracy_comprehensive(mode2_pipeline):
    """
    Test: Batch statistics calculated accurately for complex scenario.

    Scenario: 10 answers with varying scores
    - 3 correct (100 pts), 4 partial (70 pts), 3 failed
    """
    answers = [
        create_answer_dict(f"q_{i:02d}") for i in range(1, 11)
    ]

    async def varied_score_async(**kwargs):
        qid = kwargs.get("question_id", "q_00")
        idx = int(qid.split("_")[1])
        if idx <= 3:
            # First 3: correct
            return create_score_result(qid, is_correct=True, score=100)
        elif idx <= 7:
            # Next 4: partial
            return create_score_result(qid, is_correct=False, score=70)
        else:
            # Last 3: failed (exception)
            raise ValueError(f"Error for {qid}")

    with patch.object(
        mode2_pipeline, "a_score_answer", side_effect=varied_score_async
    ):
        response = await mode2_pipeline.score_answers_batch_parallel(answers)

    # Verify counts
    assert response["batch_stats"]["total_count"] == 10
    assert response["batch_stats"]["successful_count"] == 7
    assert response["batch_stats"]["failed_count"] == 3
    assert response["batch_stats"]["correct_count"] == 3

    # Verify average (only 7 successful)
    expected_avg = (3 * 100 + 4 * 70) / 7  # = (300 + 280) / 7 ≈ 82.86
    assert abs(response["batch_stats"]["average_score"] - expected_avg) < 0.1

    # Verify rates
    assert abs(response["batch_stats"]["correct_rate"] - 3 / 7) < 0.01


@pytest.mark.asyncio
async def test_average_score_calculation_edge_cases(mode2_pipeline):
    """
    Test: Average score calculation handles edge cases.

    Cases:
    - All scores 0
    - All scores 100
    - Mixed 0-100
    """
    # Case 1: All zeros
    answers_zeros = [create_answer_dict(f"q_{i:02d}") for i in range(1, 4)]

    with patch.object(
        mode2_pipeline,
        "a_score_answer",
        side_effect=lambda **kw: create_score_result(kw.get("question_id"), score=0),
    ):
        response = await mode2_pipeline.score_answers_batch_parallel(answers_zeros)
        assert response["batch_stats"]["average_score"] == 0.0

    # Case 2: All 100
    answers_100 = [create_answer_dict(f"q_{i:02d}") for i in range(1, 4)]

    with patch.object(
        mode2_pipeline,
        "a_score_answer",
        side_effect=lambda **kw: create_score_result(kw.get("question_id"), score=100),
    ):
        response = await mode2_pipeline.score_answers_batch_parallel(answers_100)
        assert response["batch_stats"]["average_score"] == 100.0


# ============================================================================
# EDGE CASES AND BOUNDARY CONDITIONS
# ============================================================================


@pytest.mark.asyncio
async def test_empty_batch(mode2_pipeline):
    """
    Test: Empty batch (0 answers) handled gracefully.

    AC1: Returns empty response with zero stats
    """
    answers: list[dict] = []

    response = await mode2_pipeline.score_answers_batch_parallel(answers)

    # Should handle empty gracefully
    assert response["batch_stats"]["total_count"] == 0
    assert response["batch_stats"]["successful_count"] == 0
    assert response["batch_stats"]["failed_count"] == 0
    assert len(response["results"]) == 0
    assert len(response["failed_question_ids"]) == 0


@pytest.mark.asyncio
async def test_single_answer_batch(mode2_pipeline):
    """
    Test: Single answer (1 question) - minimal parallelization benefit.

    AC1: Works correctly with single item
    """
    answers = [create_answer_dict("q_01")]

    with patch.object(
        mode2_pipeline, "a_score_answer", return_value=create_score_result("q_01")
    ):
        response = await mode2_pipeline.score_answers_batch_parallel(answers)

    assert response["batch_stats"]["successful_count"] == 1
    assert response["batch_stats"]["total_count"] == 1
    assert len(response["results"]) == 1


@pytest.mark.asyncio
async def test_unicode_answers_multilingual(mode2_pipeline):
    """
    Test: Unicode characters in answers (Korean, Chinese, etc).

    AC3: Handles multi-byte UTF-8 correctly
    """
    answers = [
        create_answer_dict(
            "q_01",
            user_answer="라그는 정보검색 기반 생성형 AI입니다",  # Korean
            correct_keywords=["라그", "정보검색"],
        ),
        create_answer_dict(
            "q_02",
            user_answer="机器学习是人工智能的子集",  # Chinese
            correct_keywords=["机器学习", "人工智能"],
        ),
    ]

    with patch.object(
        mode2_pipeline, "a_score_answer", return_value=create_score_result("q_00")
    ):
        response = await mode2_pipeline.score_answers_batch_parallel(answers)

    assert response["batch_stats"]["successful_count"] == 2
    assert len(response["results"]) == 2


@pytest.mark.asyncio
async def test_long_batch_processing_stability(mode2_pipeline):
    """
    Test: Stability with longer batch (25 answers).

    AC4: Handles sustained parallel load
    """
    answers = [
        create_answer_dict(f"q_{i:03d}") for i in range(1, 26)
    ]

    with patch.object(
        mode2_pipeline, "a_score_answer", return_value=create_score_result("q_00")
    ):
        response = await mode2_pipeline.score_answers_batch_parallel(answers)

    assert response["batch_stats"]["successful_count"] == 25
    assert response["batch_stats"]["total_count"] == 25
    assert response["batch_stats"]["average_score"] == 100.0


# ============================================================================
# BACKWARD COMPATIBILITY
# ============================================================================


def test_sequential_batch_still_works(mode2_pipeline):
    """
    Test: Original sequential score_answers_batch() still works.

    Ensure backward compatibility - old API should still function.
    """
    answers = [
        create_answer_dict("q_01"),
        create_answer_dict("q_02"),
    ]

    with patch.object(
        mode2_pipeline, "score_answer", return_value=create_score_result("q_00")
    ):
        response = mode2_pipeline.score_answers_batch(answers)

    # Original method should still work
    assert response["batch_stats"]["successful_count"] == 2
    assert len(response["results"]) == 2
