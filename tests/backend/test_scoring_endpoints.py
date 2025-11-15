"""
Tests for scoring API endpoints.

REQ: REQ-B-B3-Score
"""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.backend.models.attempt_answer import AttemptAnswer
from src.backend.models.question import Question
from src.backend.models.test_session import TestSession


class TestScoringEndpoint:
    """REQ-B-B3-Score-1: POST /questions/score endpoint."""

    def test_score_mc_answer_endpoint_success(
        self, client: TestClient, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """POST /questions/score with MC answer returns 200 OK."""
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

        response = client.post(
            "/questions/answer/score",
            json={"session_id": test_session_in_progress.id, "question_id": question.id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["scored"] is True
        assert data["is_correct"] is True
        assert data["score"] == 100.0

    def test_score_tf_answer_endpoint_success(
        self, client: TestClient, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """POST /questions/score with TF answer returns 200 OK."""
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
            user_answer={"answer": "true"},
            response_time_ms=1000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        response = client.post(
            "/questions/answer/score",
            json={"session_id": test_session_in_progress.id, "question_id": question.id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is True
        assert data["score"] == 100.0

    def test_score_short_answer_endpoint_success(
        self, client: TestClient, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """POST /questions/score with short answer returns partial credit."""
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

        response = client.post(
            "/questions/answer/score",
            json={"session_id": test_session_in_progress.id, "question_id": question.id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is False
        assert data["score"] == 50.0

    def test_score_endpoint_invalid_session(self, client: TestClient, db_session: Session) -> None:
        """POST /questions/score with invalid session returns 404."""
        response = client.post(
            "/questions/answer/score",
            json={"session_id": "invalid_session", "question_id": "q1"},
        )

        assert response.status_code == 404

    def test_score_endpoint_invalid_question(
        self, client: TestClient, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """POST /questions/score with invalid question returns 404."""
        response = client.post(
            "/questions/answer/score",
            json={"session_id": test_session_in_progress.id, "question_id": "invalid_question"},
        )

        assert response.status_code == 404

    def test_score_endpoint_with_time_penalty(
        self, client: TestClient, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """POST /questions/score includes time_penalty_applied flag."""
        # Set time exceeded
        test_session_in_progress.started_at = datetime.now(UTC) - timedelta(minutes=25)
        test_session_in_progress.paused_at = datetime.now(UTC)
        test_session_in_progress.status = "paused"
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

        response = client.post(
            "/questions/answer/score",
            json={"session_id": test_session_in_progress.id, "question_id": question.id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["time_penalty_applied"] is True
        assert data["final_score"] < data["score"]

    def test_score_endpoint_response_includes_feedback(
        self, client: TestClient, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """POST /questions/score response includes feedback message."""
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

        response = client.post(
            "/questions/answer/score",
            json={"session_id": test_session_in_progress.id, "question_id": question.id},
        )

        assert response.status_code == 200
        data = response.json()
        assert "feedback" in data
        assert data["feedback"] in ("정답입니다!", "오답입니다.")

    def test_score_endpoint_response_includes_scored_at(
        self, client: TestClient, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """POST /questions/score response includes scored_at timestamp."""
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

        response = client.post(
            "/questions/answer/score",
            json={"session_id": test_session_in_progress.id, "question_id": question.id},
        )

        assert response.status_code == 200
        data = response.json()
        assert "scored_at" in data
        # Should be valid ISO format timestamp
        assert "T" in data["scored_at"]

    def test_score_endpoint_answer_not_yet_saved(
        self, client: TestClient, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """POST /questions/score for answer not yet saved returns 404."""
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

        # No answer saved for this question

        response = client.post(
            "/questions/answer/score",
            json={"session_id": test_session_in_progress.id, "question_id": question.id},
        )

        assert response.status_code == 404

    def test_score_endpoint_correct_answer_feedback(
        self, client: TestClient, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """Correct answer returns '정답입니다!' feedback."""
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

        response = client.post(
            "/questions/answer/score",
            json={"session_id": test_session_in_progress.id, "question_id": question.id},
        )

        data = response.json()
        assert data["feedback"] == "정답입니다!"

    def test_score_endpoint_incorrect_answer_feedback(
        self, client: TestClient, db_session: Session, test_session_in_progress: TestSession
    ) -> None:
        """Incorrect answer returns '오답입니다.' feedback."""
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
            user_answer={"selected_key": "B"},
            response_time_ms=1000,
            saved_at=datetime.now(UTC),
        )
        db_session.add(answer)
        db_session.commit()

        response = client.post(
            "/questions/answer/score",
            json={"session_id": test_session_in_progress.id, "question_id": question.id},
        )

        data = response.json()
        assert data["feedback"] == "오답입니다."
