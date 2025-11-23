"""
Tests for explanation generation service.

REQ: REQ-B-B3-Explain
"""

import time
from typing import Any, NoReturn
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.backend.models.question import Question
from src.backend.models.test_session import TestSession

# =========================================================================
# Helper Functions
# =========================================================================


def create_test_question(db_session: Session, test_session: TestSession) -> Question:
    """Create a test question for explanation testing."""
    question = Question(
        id=str(uuid4()),
        session_id=test_session.id,
        item_type="multiple_choice",
        stem="Which of the following is correct?",
        choices=["A", "B", "C", "D"],
        answer_schema={
            "correct_key": "A",
            "explanation": "Placeholder",
        },
        difficulty=5,
        category="LLM",
        round=1,
    )
    db_session.add(question)
    db_session.commit()
    db_session.refresh(question)
    return question


class TestExplanationGeneration:
    """REQ-B-B3-Explain: Generate explanations with reference links."""

    def test_generate_explanation_for_correct_answer(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
    ) -> None:
        """
        Generate explanation for correct answer.

        REQ: REQ-B-B3-Explain-1

        Acceptance Criteria:
        - Explanation text >= 200 characters
        - Reference links >= 3
        - Generation completes < 2000ms
        """
        # Setup
        from src.backend.services.explain_service import ExplainService

        question = create_test_question(db_session, test_session_round1_fixture)

        # Mock LLM response
        mock_llm_response = {
            "explanation": "이것은 200자 이상의 정답 해설입니다. " * 30,  # ~900 chars
            "reference_links": [
                {"title": "Machine Learning Basics", "url": "https://example.com/ml"},
                {"title": "Deep Learning Guide", "url": "https://example.com/dl"},
                {"title": "Neural Networks", "url": "https://example.com/nn"},
            ],
        }

        with patch.object(
            ExplainService, "_generate_with_llm", return_value=(mock_llm_response, False, None)
        ):
            service = ExplainService(db_session)
            start_time = time.time()
            result = service.generate_explanation(
                question_id=question.id,
                user_answer="A",
                is_correct=True,
            )
            elapsed_time = (time.time() - start_time) * 1000  # ms

        # Assertions
        assert result["explanation_text"]
        assert len(result["explanation_text"]) >= 200
        assert len(result["reference_links"]) >= 3
        assert elapsed_time < 2000

    def test_generate_explanation_for_incorrect_answer(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
    ) -> None:
        """
        Generate explanation for incorrect answer.

        REQ: REQ-B-B3-Explain-1

        Explanation should clarify misconception and explain correct answer.
        """
        from src.backend.services.explain_service import ExplainService

        question = create_test_question(db_session, test_session_round1_fixture)

        mock_llm_response = {
            "explanation": "잘못된 답입니다. 정답은 B입니다. " * 30,  # ~900 chars
            "reference_links": [
                {"title": "Common Mistakes", "url": "https://example.com/mistakes"},
                {"title": "Correct Method", "url": "https://example.com/correct"},
                {"title": "Practice Problems", "url": "https://example.com/practice"},
                {"title": "Additional Resources", "url": "https://example.com/resources"},
            ],
        }

        with patch.object(
            ExplainService, "_generate_with_llm", return_value=(mock_llm_response, False, None)
        ):
            service = ExplainService(db_session)
            result = service.generate_explanation(
                question_id=question.id,
                user_answer="C",
                is_correct=False,
            )

        assert result["explanation_text"]
        assert len(result["explanation_text"]) >= 200
        assert len(result["reference_links"]) >= 3

    def test_explanation_length_validation(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
    ) -> None:
        """
        Validate explanation meets minimum length requirement (200 chars).

        REQ: REQ-B-B3-Explain-1 AC1

        Should reject explanations < 200 characters.
        """
        from src.backend.services.explain_service import ExplainService

        question = create_test_question(db_session, test_session_round1_fixture)

        # Mock LLM response with insufficient length
        mock_llm_response = {
            "explanation": "너무 짧은 해설",  # Only ~30 chars
            "reference_links": [
                {"title": "Link 1", "url": "https://example.com/1"},
                {"title": "Link 2", "url": "https://example.com/2"},
                {"title": "Link 3", "url": "https://example.com/3"},
            ],
        }

        with patch.object(
            ExplainService, "_generate_with_llm", return_value=(mock_llm_response, False, None)
        ):
            service = ExplainService(db_session)
            with pytest.raises(ValueError, match="Explanation must be at least 200 characters"):
                service.generate_explanation(
                    question_id=question.id,
                    user_answer="A",
                    is_correct=True,
                )

    def test_reference_links_count_validation(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
    ) -> None:
        """
        Validate reference links meet minimum count requirement (3+ links).

        REQ: REQ-B-B3-Explain-1 AC2

        Should reject explanations with < 3 reference links.
        """
        from src.backend.services.explain_service import ExplainService

        question = create_test_question(db_session, test_session_round1_fixture)

        # Mock LLM response with insufficient links
        mock_llm_response = {
            "explanation": "정답입니다. " * 80,  # ~900 chars
            "reference_links": [
                {"title": "Link 1", "url": "https://example.com/1"},
                {"title": "Link 2", "url": "https://example.com/2"},
            ],  # Only 2 links
        }

        with patch.object(
            ExplainService, "_generate_with_llm", return_value=(mock_llm_response, False, None)
        ):
            service = ExplainService(db_session)
            with pytest.raises(ValueError, match="at least 3 reference links"):
                service.generate_explanation(
                    question_id=question.id,
                    user_answer="A",
                    is_correct=True,
                )

    def test_explanation_generation_performance(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
    ) -> None:
        """
        Performance test: Explanation generation completes < 2000ms.

        REQ: REQ-B-B3-Explain-1 AC3

        SLA: < 2 seconds total time (LLM call + validation + DB save).
        """
        from src.backend.services.explain_service import ExplainService

        question = create_test_question(db_session, test_session_round1_fixture)

        mock_llm_response = {
            "explanation": "성능 테스트 해설입니다. " * 50,  # ~600 chars
            "reference_links": [
                {"title": "Perf Link 1", "url": "https://example.com/perf1"},
                {"title": "Perf Link 2", "url": "https://example.com/perf2"},
                {"title": "Perf Link 3", "url": "https://example.com/perf3"},
            ],
        }

        with patch.object(
            ExplainService, "_generate_with_llm", return_value=(mock_llm_response, False, None)
        ):
            service = ExplainService(db_session)
            start_time = time.time()
            service.generate_explanation(
                question_id=question.id,
                user_answer="A",
                is_correct=True,
            )
            elapsed_time = (time.time() - start_time) * 1000

            assert elapsed_time < 2000, f"Generation took {elapsed_time}ms (exceeds 2000ms SLA)"


class TestExplanationRetrieval:
    """REQ-B-B3-Explain: Retrieve cached explanations."""

    def test_get_explanation_by_question_id(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
    ) -> None:
        """
        Retrieve cached explanation by question ID.

        REQ: REQ-B-B3-Explain-1

        Should return explanation if previously generated.
        """
        from src.backend.services.explain_service import ExplainService

        question = create_test_question(db_session, test_session_round1_fixture)

        # Generate explanation first
        mock_llm_response = {
            "explanation": "캐시된 해설입니다. " * 50,
            "reference_links": [
                {"title": "Link 1", "url": "https://example.com/1"},
                {"title": "Link 2", "url": "https://example.com/2"},
                {"title": "Link 3", "url": "https://example.com/3"},
            ],
        }

        with patch.object(
            ExplainService, "_generate_with_llm", return_value=(mock_llm_response, False, None)
        ):
            service = ExplainService(db_session)
            service.generate_explanation(
                question_id=question.id,
                user_answer="A",
                is_correct=True,
            )

        # Retrieve cached explanation
        result = service.get_explanation(question_id=question.id)
        assert result is not None
        assert result["question_id"] == question.id
        assert len(result["reference_links"]) >= 3

    def test_get_explanation_not_found(
        self,
        db_session: Session,
    ) -> None:
        """
        Retrieve explanation for non-existent question returns None.

        REQ: REQ-B-B3-Explain-1

        Should gracefully handle missing explanations.
        """
        from src.backend.services.explain_service import ExplainService

        service = ExplainService(db_session)
        result = service.get_explanation(question_id="non_existent_id")

        assert result is None


class TestExplanationValidation:
    """REQ-B-B3-Explain: Input validation and error handling."""

    def test_invalid_question_id_raises_error(
        self,
        db_session: Session,
    ) -> None:
        """
        Generate explanation for non-existent question raises ValueError.

        REQ: REQ-B-B3-Explain-1

        Should validate question exists in database.
        """
        from src.backend.services.explain_service import ExplainService

        service = ExplainService(db_session)

        with pytest.raises(ValueError, match="Question not found"):
            service.generate_explanation(
                question_id="non_existent_id",
                user_answer="A",
                is_correct=True,
            )

    def test_empty_user_answer_validation(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
    ) -> None:
        """
        Empty user answer should raise ValueError.

        REQ: REQ-B-B3-Explain-1

        Validate non-empty user response.
        """
        from src.backend.services.explain_service import ExplainService

        question = create_test_question(db_session, test_session_round1_fixture)
        service = ExplainService(db_session)

        with pytest.raises(ValueError, match="user_answer cannot be empty"):
            service.generate_explanation(
                question_id=question.id,
                user_answer="",
                is_correct=True,
            )

    def test_llm_timeout_graceful_degradation(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
    ) -> None:
        """
        LLM timeout (exceeds 2s) triggers graceful degradation.

        REQ: REQ-B-B3-Explain-1 AC3

        Should return partial/fallback explanation with error flag.
        """
        from src.backend.services.explain_service import ExplainService

        question = create_test_question(db_session, test_session_round1_fixture)

        # Mock LLM timeout
        def timeout_side_effect(*args: Any, **kwargs: Any) -> NoReturn:  # noqa: ANN401
            raise TimeoutError("LLM request timed out")

        with patch.object(ExplainService, "_generate_with_llm", side_effect=timeout_side_effect):
            service = ExplainService(db_session)
            result = service.generate_explanation(
                question_id=question.id,
                user_answer="A",
                is_correct=True,
            )

            # Should return fallback explanation
            assert result is not None
            assert result.get("is_fallback") is True
            assert "error_message" in result


class TestExplanationPersistence:
    """REQ-B-B3-Explain: Database persistence and caching."""

    def test_explanation_persisted_to_database(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
    ) -> None:
        """
        Generated explanation should be saved to database.

        REQ: REQ-B-B3-Explain-1

        Verify AnswerExplanation model is created.
        """
        from src.backend.models.answer_explanation import AnswerExplanation
        from src.backend.services.explain_service import ExplainService

        question = create_test_question(db_session, test_session_round1_fixture)

        mock_llm_response = {
            "explanation": "데이터베이스에 저장된 해설입니다. " * 50,
            "reference_links": [
                {"title": "Link 1", "url": "https://example.com/1"},
                {"title": "Link 2", "url": "https://example.com/2"},
                {"title": "Link 3", "url": "https://example.com/3"},
            ],
        }

        with patch.object(
            ExplainService, "_generate_with_llm", return_value=(mock_llm_response, False, None)
        ):
            service = ExplainService(db_session)
            result = service.generate_explanation(
                question_id=question.id,
                user_answer="A",
                is_correct=True,
            )

        # Verify explanation persisted
        saved_explanation = db_session.query(AnswerExplanation).filter_by(question_id=question.id).first()

        assert saved_explanation is not None
        assert saved_explanation.id == result["id"]
        assert len(saved_explanation.reference_links) >= 3

    def test_explanation_reuse_for_same_question(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
    ) -> None:
        """
        Same question should reuse cached explanation.

        REQ: REQ-B-B3-Explain-1

        Should not call LLM for previously explained questions.
        """
        from src.backend.services.explain_service import ExplainService

        question = create_test_question(db_session, test_session_round1_fixture)

        mock_llm_response = {
            "explanation": "캐시 재사용 테스트. " * 50,
            "reference_links": [
                {"title": "Link 1", "url": "https://example.com/1"},
                {"title": "Link 2", "url": "https://example.com/2"},
                {"title": "Link 3", "url": "https://example.com/3"},
            ],
        }

        # First call
        with patch.object(
            ExplainService, "_generate_with_llm", return_value=(mock_llm_response, False, None)
        ) as mock_llm:
            service = ExplainService(db_session)
            result1 = service.generate_explanation(
                question_id=question.id,
                user_answer="A",
                is_correct=True,
            )
            assert mock_llm.call_count == 1

            # Second call should use cache
            result2 = service.generate_explanation(
                question_id=question.id,
                user_answer="A",
                is_correct=True,
            )
            # LLM should not be called again
            assert mock_llm.call_count == 1
            assert result1["id"] == result2["id"]

    def test_explanation_with_attempt_answer_tracking(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
        attempt_answers_for_session: list,
    ) -> None:
        """
        Explanation can be linked to specific attempt answer.

        REQ: REQ-B-B3-Explain-1

        Optional: Track which user attempt the explanation belongs to.
        """
        from src.backend.services.explain_service import ExplainService

        # Use first attempt answer from fixture
        attempt_answer = attempt_answers_for_session[0]

        mock_llm_response = {
            "explanation": "시도별 추적 해설. " * 50,
            "reference_links": [
                {"title": "Link 1", "url": "https://example.com/1"},
                {"title": "Link 2", "url": "https://example.com/2"},
                {"title": "Link 3", "url": "https://example.com/3"},
            ],
        }

        with patch.object(
            ExplainService, "_generate_with_llm", return_value=(mock_llm_response, False, None)
        ):
            service = ExplainService(db_session)
            result = service.generate_explanation(
                question_id=attempt_answer.question_id,
                user_answer=attempt_answer.user_answer,
                is_correct=attempt_answer.is_correct,
                attempt_answer_id=attempt_answer.id,
            )

            assert result["attempt_answer_id"] == attempt_answer.id


class TestLLMIntegration:
    """REQ-B-B3-Explain: LLM integration and prompt engineering."""

    def test_llm_prompt_for_correct_answer(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
    ) -> None:
        """
        LLM prompt for correct answer emphasizes reinforcement.

        REQ: REQ-B-B3-Explain-1

        Prompt should differ for correct vs incorrect answers.
        Verifies explanation is generated with correct is_correct flag.
        """
        from src.backend.services.explain_service import ExplainService

        question = create_test_question(db_session, test_session_round1_fixture)

        mock_llm_response = {
            "explanation": "정답입니다. " * 80,  # ~900 chars
            "reference_links": [
                {"title": "Link 1", "url": "https://example.com/1"},
                {"title": "Link 2", "url": "https://example.com/2"},
                {"title": "Link 3", "url": "https://example.com/3"},
            ],
        }

        with patch.object(
            ExplainService, "_generate_with_llm", return_value=(mock_llm_response, False, None)
        ):
            service = ExplainService(db_session)
            result = service.generate_explanation(
                question_id=question.id,
                user_answer="A",
                is_correct=True,
            )

            # Verify explanation was generated with correct context
            assert result is not None
            assert result["explanation_text"]
            assert len(result["reference_links"]) >= 3
            assert result["is_correct"] is True

    def test_llm_prompt_for_incorrect_answer(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
    ) -> None:
        """
        LLM prompt for incorrect answer emphasizes clarification.

        REQ: REQ-B-B3-Explain-1

        Should explain common misconceptions.
        Verifies explanation is generated with incorrect is_correct flag.
        """
        from src.backend.services.explain_service import ExplainService

        question = create_test_question(db_session, test_session_round1_fixture)

        mock_llm_response = {
            "explanation": "오답입니다. " * 80,  # ~900 chars
            "reference_links": [
                {"title": "Link 1", "url": "https://example.com/1"},
                {"title": "Link 2", "url": "https://example.com/2"},
                {"title": "Link 3", "url": "https://example.com/3"},
            ],
        }

        with patch.object(
            ExplainService, "_generate_with_llm", return_value=(mock_llm_response, False, None)
        ):
            service = ExplainService(db_session)
            result = service.generate_explanation(
                question_id=question.id,
                user_answer="B",
                is_correct=False,
            )

            # Verify explanation was generated with incorrect context
            assert result is not None
            assert result["explanation_text"]
            assert len(result["reference_links"]) >= 3
            assert result["is_correct"] is False

    def test_extract_correct_answer_with_missing_schema(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
    ) -> None:
        """
        Test _extract_correct_answer_key with missing or incomplete answer_schema.

        REQ: REQ-B-B3-Explain-1

        Should handle cases where answer_schema lacks correct_key or correct_answer.
        For True/False questions, should return "참" as safe default.
        For Multiple Choice, should return "[정답]" clear marker.
        """
        from src.backend.services.explain_service import ExplainService

        service = ExplainService(db_session)

        # Test True/False with missing schema
        result = service._extract_correct_answer_key({}, "true_false")
        assert result == "참", "True/False should default to '참'"

        # Test Multiple Choice with missing schema
        result = service._extract_correct_answer_key({}, "multiple_choice")
        assert result == "[정답]", "Multiple choice should show clear marker"

        # Test with boolean correct_key
        result = service._extract_correct_answer_key(
            {"correct_key": True}, "true_false"
        )
        assert result == "참"

        result = service._extract_correct_answer_key(
            {"correct_key": False}, "true_false"
        )
        assert result == "거짓"

        # Test with string correct_key
        result = service._extract_correct_answer_key(
            {"correct_key": "true"}, "true_false"
        )
        assert result == "참"

        result = service._extract_correct_answer_key(
            {"correct_key": "false"}, "true_false"
        )
        assert result == "거짓"

        # Test with regular correct_key
        result = service._extract_correct_answer_key(
            {"correct_key": "B"}, "multiple_choice"
        )
        assert result == "B"

        # Test with correct_answer fallback
        result = service._extract_correct_answer_key(
            {"correct_answer": "Expected answer"}, "short_answer"
        )
        assert result == "Expected answer"
