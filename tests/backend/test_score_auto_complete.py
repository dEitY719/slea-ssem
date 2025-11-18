"""
Tests for auto-complete feature in score endpoint.

REQ: REQ-B-B3-Score (Auto-Complete)

Tests verify that the /questions/score endpoint automatically completes
the session when all answers have been scored.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.backend.models.attempt_answer import AttemptAnswer
from src.backend.models.question import Question
from src.backend.models.test_session import TestSession
from src.backend.models.user_profile import UserProfileSurvey


class TestScoreAutoComplete:
    """Tests for auto-complete functionality in score endpoint."""

    def _create_question(
        self, db_session: Session, session_id: str, question_num: int
    ) -> Question:
        """Helper method to create a question."""
        question = Question(
            session_id=session_id,
            item_type="multiple_choice",
            stem=f"Question {question_num}",
            choices=["A", "B", "C", "D"],
            answer_schema={"correct_key": ["A", "B", "C", "D"][question_num % 4]},
            difficulty=question_num,
            category="AI",
        )
        db_session.add(question)
        db_session.flush()
        return question

    def test_auto_complete_when_all_answers_scored(
        self,
        client: TestClient,
        db_session: Session,
        user_profile_survey_fixture: UserProfileSurvey,
    ) -> None:
        """
        Test that session is auto-completed when all answers are scored.

        REQ: REQ-B-B3-Score (Auto-Complete)

        Scenario:
            1. Create a test session
            2. Create questions
            3. Create test responses (answers) with scores
            4. Call /questions/score
            5. Verify session status is "completed"
            6. Verify response includes "auto_completed": True
        """
        # Create test session
        test_session = TestSession(
            user_id=1,
            survey_id=user_profile_survey_fixture.id,
            round=1,
            status="in_progress",
        )
        db_session.add(test_session)
        db_session.flush()

        # Create questions (required for foreign key)
        question1 = self._create_question(db_session, test_session.id, 1)
        question2 = self._create_question(db_session, test_session.id, 2)

        # Create test responses with scores
        response1 = AttemptAnswer(
            session_id=test_session.id,
            question_id=question1.id,
            user_answer={"selected_key": "A"},
            score=100.0,
        )
        response2 = AttemptAnswer(
            session_id=test_session.id,
            question_id=question2.id,
            user_answer={"selected_key": "B"},
            score=85.0,
        )
        db_session.add(response1)
        db_session.add(response2)
        db_session.commit()

        # Call score endpoint with auto_complete=True
        payload = {"session_id": test_session.id, "auto_complete": True}
        response = client.post(
            "/questions/score",
            params=payload,
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["auto_completed"] is True

        # Verify session status changed to "completed"
        db_session.refresh(test_session)
        assert test_session.status == "completed"

    def test_auto_complete_scores_unscored_answers_first(
        self,
        client: TestClient,
        db_session: Session,
        user_profile_survey_fixture: UserProfileSurvey,
    ) -> None:
        """
        Test that scoring unscored answers before checking auto-complete.

        REQ: REQ-B-B3-Score (Auto-Complete)

        Scenario:
            1. Create a test session
            2. Create test responses (some without scores)
            3. Call /questions/score with auto_complete=True
            4. Verify endpoint auto-scores unscored answers first
            5. Then verifies if all are now scored, and auto-completes if enabled
            6. Verify response includes "auto_completed": True (because all get scored)
            7. Verify session status is "completed"
        """
        # Create test session
        test_session = TestSession(
            user_id=1,
            survey_id=user_profile_survey_fixture.id,
            round=1,
            status="in_progress",
        )
        db_session.add(test_session)
        db_session.flush()

        # Create questions
        question1 = self._create_question(db_session, test_session.id, 1)
        question2 = self._create_question(db_session, test_session.id, 2)

        # Create test response with score
        response1 = AttemptAnswer(
            session_id=test_session.id,
            question_id=question1.id,
            user_answer={"selected_key": "A"},  # Correct answer (matches answer_schema)
            score=100.0,
        )
        # Create test response WITHOUT score (None) - will be auto-scored
        response2 = AttemptAnswer(
            session_id=test_session.id,
            question_id=question2.id,
            user_answer={"selected_key": "B"},  # Correct answer for question2
            score=None,  # Not scored yet - will be scored by endpoint
        )
        db_session.add(response1)
        db_session.add(response2)
        db_session.commit()

        # Call score endpoint
        payload = {"session_id": test_session.id, "auto_complete": True}
        response = client.post(
            "/questions/score",
            params=payload,
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        # Both answers are now scored (response2 was auto-scored), so auto_complete should be True
        assert data["auto_completed"] is True

        # Verify session status is "completed"
        db_session.refresh(test_session)
        assert test_session.status == "completed"

    def test_auto_complete_false_disables_auto_complete(
        self,
        client: TestClient,
        db_session: Session,
        user_profile_survey_fixture: UserProfileSurvey,
    ) -> None:
        """
        Test that auto_complete=False disables auto-complete.

        REQ: REQ-B-B3-Score (Auto-Complete)

        Scenario:
            1. Create a test session
            2. Create test responses with all scores
            3. Call /questions/score with auto_complete=False
            4. Verify session status is still "in_progress"
            5. Verify response includes "auto_completed": False
        """
        # Create test session
        test_session = TestSession(
            user_id=1,
            survey_id=user_profile_survey_fixture.id,
            round=1,
            status="in_progress",
        )
        db_session.add(test_session)
        db_session.flush()

        # Create questions
        question1 = self._create_question(db_session, test_session.id, 1)
        question2 = self._create_question(db_session, test_session.id, 2)

        # Create test responses with scores
        response1 = AttemptAnswer(
            session_id=test_session.id,
            question_id=question1.id,
            user_answer={"selected_key": "A"},
            score=100.0,
        )
        response2 = AttemptAnswer(
            session_id=test_session.id,
            question_id=question2.id,
            user_answer={"selected_key": "B"},
            score=85.0,
        )
        db_session.add(response1)
        db_session.add(response2)
        db_session.commit()

        # Call score endpoint with auto_complete=False
        payload = {"session_id": test_session.id, "auto_complete": False}
        response = client.post(
            "/questions/score",
            params=payload,
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["auto_completed"] is False

        # Verify session status is still "in_progress"
        db_session.refresh(test_session)
        assert test_session.status == "in_progress"

    def test_auto_complete_default_true(
        self,
        client: TestClient,
        db_session: Session,
        user_profile_survey_fixture: UserProfileSurvey,
    ) -> None:
        """
        Test that auto_complete defaults to True when not specified.

        REQ: REQ-B-B3-Score (Auto-Complete)

        Scenario:
            1. Create a test session
            2. Create test responses with all scores
            3. Call /questions/score WITHOUT auto_complete parameter
            4. Verify session is auto-completed (default behavior)
        """
        # Create test session
        test_session = TestSession(
            user_id=1,
            survey_id=user_profile_survey_fixture.id,
            round=1,
            status="in_progress",
        )
        db_session.add(test_session)
        db_session.flush()

        # Create questions
        question1 = self._create_question(db_session, test_session.id, 1)
        question2 = self._create_question(db_session, test_session.id, 2)

        # Create test responses with scores
        response1 = AttemptAnswer(
            session_id=test_session.id,
            question_id=question1.id,
            user_answer={"selected_key": "A"},
            score=100.0,
        )
        response2 = AttemptAnswer(
            session_id=test_session.id,
            question_id=question2.id,
            user_answer={"selected_key": "B"},
            score=85.0,
        )
        db_session.add(response1)
        db_session.add(response2)
        db_session.commit()

        # Call score endpoint WITHOUT auto_complete parameter (should default to True)
        response = client.post(
            "/questions/score",
            params={"session_id": test_session.id},
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["auto_completed"] is True

        # Verify session status changed to "completed"
        db_session.refresh(test_session)
        assert test_session.status == "completed"

    def test_auto_complete_round_2_session(
        self,
        client: TestClient,
        db_session: Session,
        user_profile_survey_fixture: UserProfileSurvey,
    ) -> None:
        """
        Test that auto-complete works for Round 2 sessions.

        REQ: REQ-B-B3-Score (Auto-Complete)

        Scenario:
            1. Create a Round 2 test session
            2. Create test responses with all scores
            3. Call /questions/score
            4. Verify Round 2 session is auto-completed
        """
        # Create Round 2 test session
        test_session = TestSession(
            user_id=1,
            survey_id=user_profile_survey_fixture.id,
            round=2,  # Round 2
            status="in_progress",
        )
        db_session.add(test_session)
        db_session.flush()

        # Create questions
        question1 = self._create_question(db_session, test_session.id, 1)
        question2 = self._create_question(db_session, test_session.id, 2)

        # Create test responses with scores
        response1 = AttemptAnswer(
            session_id=test_session.id,
            question_id=question1.id,
            user_answer={"selected_key": "A"},
            score=95.0,
        )
        response2 = AttemptAnswer(
            session_id=test_session.id,
            question_id=question2.id,
            user_answer={"selected_key": "B"},
            score=90.0,
        )
        db_session.add(response1)
        db_session.add(response2)
        db_session.commit()

        # Call score endpoint
        response = client.post(
            "/questions/score",
            params={"session_id": test_session.id},
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["auto_completed"] is True
        assert data["round"] == 2

        # Verify session status changed to "completed"
        db_session.refresh(test_session)
        assert test_session.status == "completed"

    def test_score_response_includes_auto_completed_field(
        self,
        client: TestClient,
        db_session: Session,
        user_profile_survey_fixture: UserProfileSurvey,
    ) -> None:
        """
        Test that score response always includes 'auto_completed' field.

        REQ: REQ-B-B3-Score (Auto-Complete)

        Scenario:
            1. Create a test session with all answers scored
            2. Call /questions/score
            3. Verify response includes all required fields including 'auto_completed'
        """
        # Create test session
        test_session = TestSession(
            user_id=1,
            survey_id=user_profile_survey_fixture.id,
            round=1,
            status="in_progress",
        )
        db_session.add(test_session)
        db_session.flush()

        # Create question
        question1 = self._create_question(db_session, test_session.id, 1)

        # Create test response with score
        response1 = AttemptAnswer(
            session_id=test_session.id,
            question_id=question1.id,
            user_answer={"selected_key": "A"},
            score=100.0,
        )
        db_session.add(response1)
        db_session.commit()

        # Call score endpoint
        response = client.post(
            "/questions/score",
            params={"session_id": test_session.id},
        )

        # Verify response structure
        assert response.status_code == 200
        data = response.json()

        # Check all required fields are present
        assert "score" in data
        assert "correct_count" in data
        assert "total_count" in data
        assert "wrong_categories" in data
        assert "auto_completed" in data  # NEW field
