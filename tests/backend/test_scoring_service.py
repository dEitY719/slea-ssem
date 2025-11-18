"""
Tests for scoring service.

REQ: REQ-B-B3-Score, REQ-B-B2-Adapt
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from src.backend.models.attempt_answer import AttemptAnswer
from src.backend.models.question import Question
from src.backend.models.test_session import TestSession
from src.backend.services.scoring_service import ScoringService


class TestScoreCalculation:
    """REQ-B-B3-Score: Calculate round score from attempt answers."""

    def test_calculate_round_score_all_correct(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
        attempt_answers_for_session: list[AttemptAnswer],
    ) -> None:
        """Calculate score when user gets all answers correct."""
        # Update attempt answers to all correct
        from src.backend.models.attempt_answer import AttemptAnswer

        answers = db_session.query(AttemptAnswer).filter_by(session_id=test_session_round1_fixture.id).all()

        for answer in answers:
            answer.is_correct = True
            answer.score = 100.0

        db_session.commit()

        service = ScoringService(db_session)
        score_data = service.calculate_round_score(test_session_round1_fixture.id, 1)

        assert score_data["score"] == 100.0
        assert score_data["correct_count"] == 5
        assert score_data["total_count"] == 5

    def test_calculate_round_score_partial_correct(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
        attempt_answers_for_session: list[AttemptAnswer],
    ) -> None:
        """Calculate score with some correct and some wrong answers."""
        service = ScoringService(db_session)
        score_data = service.calculate_round_score(test_session_round1_fixture.id, 1)

        # 1 correct out of 5 = 20%
        assert score_data["score"] == 20.0
        assert score_data["correct_count"] == 1
        assert score_data["total_count"] == 5

    def test_calculate_round_score_all_wrong(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
        attempt_answers_for_session: list[AttemptAnswer],
    ) -> None:
        """Calculate score when user gets all answers wrong."""
        from src.backend.models.attempt_answer import AttemptAnswer

        answers = db_session.query(AttemptAnswer).filter_by(session_id=test_session_round1_fixture.id).all()

        # Reset answers to unscored state with all wrong answers
        for answer in answers:
            answer.user_answer = {"selected_key": "B"}  # All answers are wrong (correct is "A")
            answer.is_correct = False
            answer.score = 0.0

        db_session.commit()

        service = ScoringService(db_session)
        score_data = service.calculate_round_score(test_session_round1_fixture.id, 1)

        assert score_data["score"] == 0.0
        assert score_data["correct_count"] == 0
        assert score_data["total_count"] == 5

    def test_no_attempt_answers_raises_error(
        self, db_session: Session, test_session_round1_fixture: TestSession
    ) -> None:
        """Missing attempt answers raises ValueError."""
        service = ScoringService(db_session)

        with pytest.raises(ValueError, match="No attempt answers found"):
            service.calculate_round_score(test_session_round1_fixture.id, 1)


class TestWeakCategoryIdentification:
    """REQ-B-B2-Adapt-3: Identify weak categories from wrong answers."""

    def test_identify_single_weak_category(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
        attempt_answers_for_session: list[AttemptAnswer],
    ) -> None:
        """Identify single weak category from wrong answers."""
        service = ScoringService(db_session)
        score_data = service.calculate_round_score(test_session_round1_fixture.id, 1)

        # Expected: RAG (2 wrong), Robotics (1 wrong), LLM (1 wrong)
        wrong_cats = score_data["wrong_categories"]

        assert "RAG" in wrong_cats
        assert wrong_cats["RAG"] == 2

    def test_identify_multiple_weak_categories(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
        attempt_answers_for_session: list[AttemptAnswer],
    ) -> None:
        """Identify multiple weak categories."""
        service = ScoringService(db_session)
        score_data = service.calculate_round_score(test_session_round1_fixture.id, 1)

        wrong_cats = score_data["wrong_categories"]

        # Should have multiple weak categories
        assert len(wrong_cats) > 1
        assert "RAG" in wrong_cats
        assert "Robotics" in wrong_cats or "LLM" in wrong_cats

    def test_no_wrong_answers_no_weak_categories(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
        attempt_answers_for_session: list[AttemptAnswer],
    ) -> None:
        """No weak categories when all answers correct."""
        from src.backend.models.attempt_answer import AttemptAnswer

        answers = db_session.query(AttemptAnswer).filter_by(session_id=test_session_round1_fixture.id).all()

        for answer in answers:
            answer.is_correct = True

        db_session.commit()

        service = ScoringService(db_session)
        score_data = service.calculate_round_score(test_session_round1_fixture.id, 1)

        assert score_data["wrong_categories"] == {}


class TestSaveRoundResult:
    """Save calculated result to database as TestResult record."""

    def test_save_round_result_creates_record(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
        attempt_answers_for_session: list[AttemptAnswer],
    ) -> None:
        """Saving round result creates TestResult record in DB."""
        service = ScoringService(db_session)
        result = service.save_round_result(test_session_round1_fixture.id, 1)

        assert result is not None
        assert result.session_id == test_session_round1_fixture.id
        assert result.round == 1
        assert result.score == 20.0

    def test_saved_result_queryable(
        self,
        db_session: Session,
        test_session_round1_fixture: TestSession,
        attempt_answers_for_session: list[AttemptAnswer],
    ) -> None:
        """Saved result can be queried from database."""
        from src.backend.models.test_result import TestResult

        service = ScoringService(db_session)
        service.save_round_result(test_session_round1_fixture.id, 1)

        # Query from DB
        retrieved = db_session.query(TestResult).filter_by(session_id=test_session_round1_fixture.id, round=1).first()

        assert retrieved is not None
        assert retrieved.score == 20.0
        assert retrieved.correct_count == 1
        assert "RAG" in retrieved.wrong_categories


class TestScoringMultipleChoice:
    """REQ-B-B3-Score-2: Score MC questions with exact match."""

    def test_score_mc_correct_answer(self, db_session: Session, test_session_in_progress: TestSession) -> None:
        """Correct MC answer scores 1.0."""
        service = ScoringService(db_session)

        # Create question
        question = Question(
            session_id=test_session_in_progress.id,
            item_type="multiple_choice",
            stem="What is 2+2?",
            choices=["A", "B", "C", "D"],
            answer_schema={"correct_key": "A", "explanation": "2+2=4, A is correct"},
            difficulty=1,
            category="Math",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        # Save answer
        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"selected_key": "A"},
            response_time_ms=5000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        # Score answer
        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["is_correct"] is True
        assert result["score"] == 100.0

    def test_score_mc_incorrect_answer(self, db_session: Session, test_session_in_progress: TestSession) -> None:
        """Incorrect MC answer scores 0.0."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="multiple_choice",
            stem="What is 2+2?",
            choices=["A", "B", "C", "D"],
            answer_schema={"correct_key": "A"},
            difficulty=1,
            category="Math",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"selected_key": "B"},
            response_time_ms=5000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["is_correct"] is False
        assert result["score"] == 0.0

    def test_score_mc_missing_selected_key(self, db_session: Session, test_session_in_progress: TestSession) -> None:
        """MC answer missing selected_key raises ValueError."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="multiple_choice",
            stem="Test",
            choices=["A", "B"],
            answer_schema={"correct_key": "A"},
            difficulty=1,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"wrong_field": "A"},
            response_time_ms=1000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        with pytest.raises(ValueError, match="selected_key"):
            service.score_answer(test_session_in_progress.id, question.id)

    def test_score_mc_invalid_selected_key(self, db_session: Session, test_session_in_progress: TestSession) -> None:
        """MC answer with invalid key scores 0.0."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="multiple_choice",
            stem="Test",
            choices=["A", "B"],
            answer_schema={"correct_key": "A"},
            difficulty=1,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"selected_key": "Z"},  # Invalid
            response_time_ms=1000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["is_correct"] is False
        assert result["score"] == 0.0

    def test_score_mc_case_insensitive(self, db_session: Session, test_session_in_progress: TestSession) -> None:
        """MC matching is case-insensitive (normalized)."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="multiple_choice",
            stem="Test",
            choices=["Logistic Regression", "Linear Regression"],
            answer_schema={"correct_key": "Logistic Regression"},
            difficulty=1,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"selected_key": "logistic regression"},  # Lowercase
            response_time_ms=1000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        # Case-insensitive comparison should match
        assert result["is_correct"] is True
        assert result["score"] == 100.0

    def test_score_mc_with_whitespace(self, db_session: Session, test_session_in_progress: TestSession) -> None:
        """MC answer with whitespace normalizes and matches."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="multiple_choice",
            stem="Test",
            choices=["A", "B"],
            answer_schema={"correct_key": "A"},
            difficulty=1,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"selected_key": "  A  "},  # With spaces
            response_time_ms=1000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["is_correct"] is True


class TestScoringTrueFalse:
    """REQ-B-B3-Score-2: Score TF questions with exact match."""

    def test_score_tf_correct_true(self, db_session: Session, test_session_in_progress: TestSession) -> None:
        """Correct TF=True answer scores 1.0."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="true_false",
            stem="2+2=4",
            answer_schema={"correct_answer": True},
            difficulty=1,
            category="Math",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"answer": "true"},
            response_time_ms=3000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["is_correct"] is True
        assert result["score"] == 100.0

    def test_score_tf_correct_false(self, db_session: Session, test_session_in_progress: TestSession) -> None:
        """Correct TF=False answer scores 100.0."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="true_false",
            stem="2+2=5",
            answer_schema={"correct_answer": False},
            difficulty=1,
            category="Math",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"answer": "false"},
            response_time_ms=3000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["is_correct"] is True
        assert result["score"] == 100.0

    def test_score_tf_incorrect_answer(self, db_session: Session, test_session_in_progress: TestSession) -> None:
        """Incorrect TF answer scores 0.0."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="true_false",
            stem="2+2=4",
            answer_schema={"correct_answer": True},
            difficulty=1,
            category="Math",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"answer": "false"},
            response_time_ms=3000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["is_correct"] is False
        assert result["score"] == 0.0

    def test_score_tf_invalid_format(self, db_session: Session, test_session_in_progress: TestSession) -> None:
        """TF answer with invalid format raises ValueError."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="true_false",
            stem="Test",
            answer_schema={"correct_answer": True},
            difficulty=1,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"answer": "maybe"},  # Invalid
            response_time_ms=1000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        with pytest.raises(ValueError, match="Invalid true/false"):
            service.score_answer(test_session_in_progress.id, question.id)

    def test_score_tf_case_insensitive(self, db_session: Session, test_session_in_progress: TestSession) -> None:
        """TF matching is case-insensitive."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="true_false",
            stem="Test",
            answer_schema={"correct_answer": True},
            difficulty=1,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"answer": "TRUE"},  # Uppercase
            response_time_ms=1000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["is_correct"] is True


class TestScoringShortAnswer:
    """REQ-B-B3-Score-2: Score short answer with keyword matching."""

    def test_score_short_answer_all_keywords_present(
        self, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """All keywords present scores 100.0."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="short_answer",
            stem="What is semiconductor?",
            answer_schema={"keywords": ["silicon", "semiconductor"]},
            difficulty=5,
            category="Semiconductor",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"text": "Semiconductor is made of silicon"},
            response_time_ms=10000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["is_correct"] is True
        assert result["score"] == 100.0

    def test_score_short_answer_partial_keywords(
        self, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """Only 1 of 2 keywords present scores 50.0."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="short_answer",
            stem="Test",
            answer_schema={"keywords": ["silicon", "semiconductor"]},
            difficulty=5,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"text": "Made of silicon"},
            response_time_ms=5000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["is_correct"] is False
        assert result["score"] == 50.0

    def test_score_short_answer_no_keywords(self, db_session: Session, test_session_in_progress: TestSession) -> None:
        """No keywords present scores 0.0."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="short_answer",
            stem="Test",
            answer_schema={"keywords": ["silicon", "semiconductor"]},
            difficulty=5,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"text": "Made of metal"},
            response_time_ms=5000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["is_correct"] is False
        assert result["score"] == 0.0

    def test_score_short_answer_case_insensitive(
        self, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """Keyword matching is case-insensitive."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="short_answer",
            stem="Test",
            answer_schema={"keywords": ["silicon", "semiconductor"]},
            difficulty=5,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"text": "SILICON and SEMICONDUCTOR"},
            response_time_ms=5000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["is_correct"] is True
        assert result["score"] == 100.0

    def test_score_short_answer_empty_response(
        self, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """Empty response scores 0.0."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="short_answer",
            stem="Test",
            answer_schema={"keywords": ["silicon"]},
            difficulty=5,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"text": ""},
            response_time_ms=100,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["score"] == 0.0

    def test_score_short_answer_single_keyword(
        self, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """Single keyword required and found scores 100.0."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="short_answer",
            stem="Test",
            answer_schema={"keywords": ["silicon"]},
            difficulty=5,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"text": "Silicon is important"},
            response_time_ms=5000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["is_correct"] is True
        assert result["score"] == 100.0

    def test_score_short_answer_keyword_substring(
        self, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """Keyword matching supports substring."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="short_answer",
            stem="Test",
            answer_schema={"keywords": ["semi"]},
            difficulty=5,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"text": "semiconductor industry"},
            response_time_ms=5000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["is_correct"] is True
        assert result["score"] == 100.0


class TestTimePenalty:
    """REQ-B-B3-Score-3: Apply time penalty for exceeding 20 minutes."""

    def test_apply_no_penalty_within_time_limit(
        self, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """No penalty when within 20-minute limit."""
        service = ScoringService(db_session)

        # Set started_at to 10 minutes ago
        test_session_in_progress.started_at = datetime.now(UTC) - timedelta(minutes=10)
        test_session_in_progress.time_limit_ms = 1200000
        db_session.commit()

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="multiple_choice",
            stem="Test",
            choices=["A"],
            answer_schema={"correct_key": "A"},
            difficulty=1,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"selected_key": "A"},
            response_time_ms=1000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["time_penalty_applied"] is False
        assert result["final_score"] == 100.0

    def test_apply_penalty_exceeded_time_limit(
        self, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """Penalty applied when 25 minutes elapsed on 20-min limit."""
        service = ScoringService(db_session)

        # Set started_at to 25 minutes ago, mark paused
        test_session_in_progress.started_at = datetime.now(UTC) - timedelta(minutes=25)
        test_session_in_progress.paused_at = datetime.now(UTC)
        test_session_in_progress.status = "paused"
        test_session_in_progress.time_limit_ms = 1200000  # 20 minutes
        db_session.commit()

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="multiple_choice",
            stem="Test",
            choices=["A"],
            answer_schema={"correct_key": "A"},
            difficulty=1,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"selected_key": "A"},
            response_time_ms=1000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["time_penalty_applied"] is True
        # MC score = 100.0, penalty = (25-20)/20 * 100.0 = 25.0, final = 100.0 - 25.0 = 75.0
        assert result["final_score"] == pytest.approx(75.0, abs=0.01)

    def test_apply_penalty_score_not_below_zero(
        self, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """Final score never goes below 0."""
        service = ScoringService(db_session)

        # Set started_at to 30 minutes ago
        test_session_in_progress.started_at = datetime.now(UTC) - timedelta(minutes=30)
        test_session_in_progress.paused_at = datetime.now(UTC)
        test_session_in_progress.status = "paused"
        test_session_in_progress.time_limit_ms = 1200000
        db_session.commit()

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="true_false",
            stem="Test",
            answer_schema={"correct_answer": True},
            difficulty=1,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        # Wrong answer (score 0)
        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"answer": "false"},
            response_time_ms=1000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["final_score"] >= 0.0

    def test_apply_penalty_session_not_started(
        self, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """No penalty if session not started yet."""
        service = ScoringService(db_session)

        # started_at is None
        test_session_in_progress.started_at = None
        test_session_in_progress.time_limit_ms = 1200000
        db_session.commit()

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="multiple_choice",
            stem="Test",
            choices=["A"],
            answer_schema={"correct_key": "A"},
            difficulty=1,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"selected_key": "A"},
            response_time_ms=1000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["time_penalty_applied"] is False
        assert result["final_score"] == 100.0

    def test_apply_penalty_session_not_paused(self, db_session: Session, test_session_in_progress: TestSession) -> None:
        """No penalty if session not paused (still in_progress)."""
        service = ScoringService(db_session)

        # Set started_at to 25 minutes ago but status is still in_progress
        test_session_in_progress.started_at = datetime.now(UTC) - timedelta(minutes=25)
        test_session_in_progress.status = "in_progress"  # Not paused
        test_session_in_progress.time_limit_ms = 1200000
        db_session.commit()

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="multiple_choice",
            stem="Test",
            choices=["A"],
            answer_schema={"correct_key": "A"},
            difficulty=1,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"selected_key": "A"},
            response_time_ms=1000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        assert result["time_penalty_applied"] is False
        assert result["final_score"] == 100.0


class TestFullScoringFlow:
    """REQ-B-B3-Score-1 & 2: End-to-end scoring flows."""

    def test_score_mc_answer_updates_attempt_answer_db(
        self, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """Scoring updates AttemptAnswer is_correct and score in DB."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="multiple_choice",
            stem="Test",
            choices=["A", "B"],
            answer_schema={"correct_key": "A"},
            difficulty=1,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"selected_key": "A"},
            is_correct=False,  # Initially false
            score=0.0,  # Initially 0
            response_time_ms=1000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        # Score answer
        service.score_answer(test_session_in_progress.id, question.id)

        # Verify DB was updated
        db_session.refresh(answer)
        assert answer.is_correct is True
        assert answer.score == 100.0

    def test_score_short_answer_with_penalty(self, db_session: Session, test_session_in_progress: TestSession) -> None:
        """Short answer score reflects both base score and penalty."""
        service = ScoringService(db_session)

        # Set time exceeded
        test_session_in_progress.started_at = datetime.now(UTC) - timedelta(minutes=25)
        test_session_in_progress.paused_at = datetime.now(UTC)
        test_session_in_progress.status = "paused"
        test_session_in_progress.time_limit_ms = 1200000
        db_session.commit()

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="short_answer",
            stem="Test",
            answer_schema={"keywords": ["silicon"]},
            difficulty=5,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"text": "silicon"},
            response_time_ms=5000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result = service.score_answer(test_session_in_progress.id, question.id)

        # Base score 100, penalty = 25%, final = 75
        assert result["score"] == 100.0
        assert result["time_penalty_applied"] is True
        assert result["final_score"] == pytest.approx(75.0, abs=1.0)

    def test_idempotent_scoring(self, db_session: Session, test_session_in_progress: TestSession) -> None:
        """Scoring same question twice returns same result."""
        service = ScoringService(db_session)

        question = Question(
            session_id=test_session_in_progress.id,
            item_type="multiple_choice",
            stem="Test",
            choices=["A", "B"],
            answer_schema={"correct_key": "A"},
            difficulty=1,
            category="Test",
            round=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = AttemptAnswer(
            session_id=test_session_in_progress.id,
            question_id=question.id,
            user_answer={"selected_key": "A"},
            response_time_ms=1000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        result1 = service.score_answer(test_session_in_progress.id, question.id)
        result2 = service.score_answer(test_session_in_progress.id, question.id)

        assert result1["is_correct"] == result2["is_correct"]
        assert result1["score"] == result2["score"]

        # Verify only 1 record in DB
        count = db_session.query(AttemptAnswer).filter_by(session_id=test_session_in_progress.id).count()
        assert count == 1

    def test_score_answer_invalid_session(self, db_session: Session) -> None:
        """Scoring with invalid session raises ValueError."""
        service = ScoringService(db_session)

        with pytest.raises(ValueError, match="not found"):
            service.score_answer("invalid_session", "q1")
