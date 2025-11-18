"""
Tests for question generation service with retake functionality (REQ-B-B2-Retake).

REQ: REQ-B-B2-Retake-1, REQ-B-B2-Retake-2, REQ-B-B2-Retake-3, REQ-B-B2-Retake-4

Tests validate:
1. Retake creates new TestSession with new UUID (not reusing completed session)
2. Each retake is independent (no state pollution from previous session)
3. Retake with Round 1 - same survey_id or new survey_id
4. Retake → Round 2 adaptive (previous_session_id correctly handled)
5. Error handling for retake scenarios
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.agent.llm_agent import AnswerSchema, GeneratedItem, GenerateQuestionsRequest, GenerateQuestionsResponse
from src.backend.models.question import Question
from src.backend.models.test_result import TestResult
from src.backend.models.test_session import TestSession
from src.backend.models.user import User
from src.backend.models.user_profile import UserProfileSurvey
from src.backend.services.question_gen_service import QuestionGenerationService


def create_mock_item(item_id: str = "test_q_001", item_type: str = "multiple_choice") -> GeneratedItem:
    """Create a mock GeneratedItem for testing."""
    if item_type == "short_answer":
        answer_schema = AnswerSchema(
            type="keyword_match",
            keywords=["test", "keyword"],
            correct_answer=None,
        )
    else:
        answer_schema = AnswerSchema(
            type="exact_match",
            keywords=None,
            correct_answer="A",
        )

    return GeneratedItem(
        id=item_id,
        type=item_type,
        stem="Test question stem?",
        choices=["A", "B", "C", "D"] if item_type == "multiple_choice" else None,
        answer_schema=answer_schema,
        difficulty=5,
        category="test",
    )


class TestQuestionGenerationRetake:
    """
    REQ-B-B2-Retake: 재응시 문항 생성 테스트.

    Test Cases:
    - TC-1: Retake (Round 1 same survey_id) creates NEW session (not reusing completed)
    - TC-2: Retake creates independent TestSession with new UUID
    - TC-3: Retake with new survey_id (user modified self-assessment)
    - TC-4: Retake Round 1 → Round 2 adaptive (previous_session_id correctly used)
    - TC-5: Multiple retakes create separate sessions (no state pollution)
    - TC-6: Retake with completed session - previous session status unchanged
    - TC-7: Error when survey not found during retake
    - TC-8: Error when Agent fails during retake
    """

    # ====================================================================
    # TC-1: Retake (Round 1 same survey) creates NEW session
    # ====================================================================

    @pytest.mark.asyncio
    async def test_retake_round1_same_survey_creates_new_session(
        self, db_session: Session, authenticated_user: User, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """
        TC-1: Verify retake with same survey_id creates new TestSession with new UUID.

        REQ-B-B2-Retake-1, REQ-B-B2-Retake-2:
        - POST /questions/generate 호출 (이전과 동일)
        - 새로운 UUID로 TestSession 생성
        - 이전 세션과 독립적 (completed 상태 무관)
        """
        service = QuestionGenerationService(db_session)

        # Setup: Create first Round 1 session (completed)
        first_session_id = str(uuid4())
        first_session = TestSession(
            id=first_session_id,
            user_id=authenticated_user.id,
            survey_id=user_profile_survey_fixture.id,
            round=1,
            status="completed",
        )
        db_session.add(first_session)
        db_session.commit()

        # Add some questions to first session
        for i in range(5):
            question = Question(
                id=str(uuid4()),
                session_id=first_session_id,
                item_type="multiple_choice",
                stem=f"First session Q{i+1}",
                choices=["A", "B", "C", "D"],
                answer_schema={"correct_key": "A", "explanation": "Test"},
                difficulty=5,
                category="test",
                round=1,
            )
            db_session.add(question)
        db_session.commit()

        # Mock Agent for retake
        mock_agent = AsyncMock()
        mock_agent.generate_questions = AsyncMock(
            return_value=GenerateQuestionsResponse(
                round_id="round_retake_001",
                items=[create_mock_item(f"retake_q_{i}") for i in range(5)],
                time_limit_seconds=1200,
            )
        )

        with patch("src.backend.services.question_gen_service.create_agent", return_value=mock_agent):
            # Perform retake with same survey_id
            result = await service.generate_questions(
                user_id=authenticated_user.id,
                survey_id=user_profile_survey_fixture.id,
                round_num=1,
            )

        # Verify: New session created with new UUID
        new_session_id = result["session_id"]
        assert new_session_id != first_session_id, "Retake should create NEW session, not reuse old one"

        # Verify: New session is in_progress
        new_session = db_session.query(TestSession).filter_by(id=new_session_id).first()
        assert new_session is not None
        assert new_session.status == "in_progress"

        # Verify: Old session still completed (unchanged)
        old_session = db_session.query(TestSession).filter_by(id=first_session_id).first()
        assert old_session.status == "completed"

        # Verify: Questions in new session
        new_questions = db_session.query(Question).filter_by(session_id=new_session_id).all()
        assert len(new_questions) == 5

        # Verify: Old questions still in old session
        old_questions = db_session.query(Question).filter_by(session_id=first_session_id).all()
        assert len(old_questions) == 5

    # ====================================================================
    # TC-2: Retake creates independent TestSession with new UUID
    # ====================================================================

    @pytest.mark.asyncio
    async def test_retake_creates_independent_session(
        self, db_session: Session, authenticated_user: User, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """
        TC-2: Verify each retake creates completely independent TestSession.

        REQ-B-B2-Retake-2: 항상 새로운 세션을 생성해야 한다.
        """
        service = QuestionGenerationService(db_session)

        # Create first completed session
        first_session_id = str(uuid4())
        first_session = TestSession(
            id=first_session_id,
            user_id=authenticated_user.id,
            survey_id=user_profile_survey_fixture.id,
            round=1,
            status="completed",
        )
        db_session.add(first_session)
        db_session.flush()

        # Mock Agent
        mock_agent = AsyncMock()

        retake_session_ids = []

        with patch("src.backend.services.question_gen_service.create_agent", return_value=mock_agent):
            # Perform 2 retakes
            for attempt in range(2):
                mock_agent.generate_questions = AsyncMock(
                    return_value=GenerateQuestionsResponse(
                        round_id=f"round_retake_{attempt}",
                        items=[create_mock_item(f"attempt{attempt}_q_{i}") for i in range(5)],
                        time_limit_seconds=1200,
                    )
                )
                result = await service.generate_questions(
                    user_id=authenticated_user.id,
                    survey_id=user_profile_survey_fixture.id,
                    round_num=1,
                )
                retake_session_ids.append(result["session_id"])

        # Verify: Each retake has unique session_id
        assert retake_session_ids[0] != retake_session_ids[1]
        assert retake_session_ids[0] != first_session_id
        assert retake_session_ids[1] != first_session_id

        # Verify: All sessions exist in DB with correct status
        db_session.refresh(first_session)
        for session_id in retake_session_ids:
            session = db_session.query(TestSession).filter_by(id=session_id).first()
            assert session is not None
            assert session.status == "in_progress"

    # ====================================================================
    # TC-3: Retake with new survey_id (user modified self-assessment)
    # ====================================================================

    @pytest.mark.asyncio
    async def test_retake_with_new_survey_id(
        self, db_session: Session, authenticated_user: User, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """
        TC-3: Verify retake with new survey_id creates session linked to new survey.

        REQ-B-B2-Retake-2: 새로운 survey_id로 새 세션 생성
        """
        service = QuestionGenerationService(db_session)

        # Create first completed session with old survey
        first_session_id = str(uuid4())
        first_session = TestSession(
            id=first_session_id,
            user_id=authenticated_user.id,
            survey_id=user_profile_survey_fixture.id,
            round=1,
            status="completed",
        )
        db_session.add(first_session)
        db_session.commit()

        # Create new survey (simulating user editing self-assessment)
        new_survey = UserProfileSurvey(
            user_id=authenticated_user.id,
            self_level="Advanced",
            years_experience=10,
            job_role="Senior Engineer",
            interests=["AI", "RAG", "Robotics"],  # Modified
        )
        db_session.add(new_survey)
        db_session.commit()

        # Mock Agent
        mock_agent = AsyncMock()
        mock_agent.generate_questions = AsyncMock(
            return_value=GenerateQuestionsResponse(
                round_id="round_retake_003",
                items=[create_mock_item(f"q_{i}") for i in range(5)],
                time_limit_seconds=1200,
            )
        )

        with patch("src.backend.services.question_gen_service.create_agent", return_value=mock_agent):
            # Perform retake with new survey
            result = await service.generate_questions(
                user_id=authenticated_user.id,
                survey_id=new_survey.id,  # New survey_id
                round_num=1,
            )

        # Verify: New session linked to new survey
        new_session_id = result["session_id"]
        new_session = db_session.query(TestSession).filter_by(id=new_session_id).first()
        assert new_session.survey_id == new_survey.id
        assert new_session.survey_id != user_profile_survey_fixture.id

        # Verify: Old session still linked to old survey
        old_session = db_session.query(TestSession).filter_by(id=first_session_id).first()
        assert old_session.survey_id == user_profile_survey_fixture.id

    # ====================================================================
    # TC-4: Retake Round 1 → Round 2 adaptive
    # ====================================================================

    @pytest.mark.asyncio
    async def test_retake_round2_adaptive_after_round1_completed(
        self, db_session: Session, authenticated_user: User, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """
        TC-4: Verify Round 1 completed → Round 2 adaptive works correctly.

        REQ-B-B2-Retake-3: 적응형 라운드(Round 2) 진행 시
        previous_session_id를 사용하여 generate-adaptive 호출
        """
        service = QuestionGenerationService(db_session)

        # Setup: Create Round 1 completed session with questions
        r1_session_id = str(uuid4())
        r1_session = TestSession(
            id=r1_session_id,
            user_id=authenticated_user.id,
            survey_id=user_profile_survey_fixture.id,
            round=1,
            status="completed",
        )
        db_session.add(r1_session)
        db_session.flush()

        # Add Round 1 questions
        for i in range(5):
            question = Question(
                id=str(uuid4()),
                session_id=r1_session_id,
                item_type="multiple_choice",
                stem=f"Round 1 Q{i+1}",
                choices=["A", "B", "C", "D"],
                answer_schema={"correct_key": "A", "explanation": "Test"},
                difficulty=5,
                category="AI" if i < 3 else "RAG",
                round=1,
            )
            db_session.add(question)
        db_session.commit()

        # Add Round 1 TestResult (score 60)
        r1_result = TestResult(
            session_id=r1_session_id,
            round=1,
            score=60,
            total_points=60,  # 60% of 100
            correct_count=3,
            total_count=5,
            wrong_categories={"RAG": 2},
        )
        db_session.add(r1_result)
        db_session.commit()

        # Now perform Round 2 adaptive generation
        # This uses generate_questions_adaptive which queries the completed Round 1 session
        result = await service.generate_questions_adaptive(
            user_id=authenticated_user.id,
            session_id=r1_session_id,  # previous_session_id
            round_num=2,
        )

        # Verify: New Round 2 session created
        r2_session_id = result["session_id"]
        assert r2_session_id != r1_session_id

        r2_session = db_session.query(TestSession).filter_by(id=r2_session_id).first()
        assert r2_session is not None
        assert r2_session.round == 2
        assert r2_session.status == "in_progress"

        # Verify: Round 1 session unchanged
        r1_session_check = db_session.query(TestSession).filter_by(id=r1_session_id).first()
        assert r1_session_check.status == "completed"

        # Verify: Round 2 questions created
        r2_questions = db_session.query(Question).filter_by(session_id=r2_session_id).all()
        assert len(r2_questions) == 5

    # ====================================================================
    # TC-5: Multiple retakes create separate sessions (no state pollution)
    # ====================================================================

    @pytest.mark.asyncio
    async def test_multiple_retakes_no_state_pollution(
        self, db_session: Session, authenticated_user: User, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """
        TC-5: Verify multiple consecutive retakes don't pollute each other's state.

        REQ-B-B2-Retake-1: 매번 새로운 테스트세션 생성
        """
        service = QuestionGenerationService(db_session)

        # Mock Agent
        mock_agent = AsyncMock()

        session_ids = []

        with patch("src.backend.services.question_gen_service.create_agent", return_value=mock_agent):
            # Perform 3 consecutive retakes
            for attempt in range(3):
                # Update mock to return different questions each time
                mock_agent.generate_questions = AsyncMock(
                    return_value=GenerateQuestionsResponse(
                        round_id=f"round_retake_{attempt}",
                        items=[create_mock_item(f"attempt{attempt}_q_{i}") for i in range(5)],
                        time_limit_seconds=1200,
                    )
                )

                result = await service.generate_questions(
                    user_id=authenticated_user.id,
                    survey_id=user_profile_survey_fixture.id,
                    round_num=1,
                )
                session_ids.append(result["session_id"])

                # Mark previous session as completed (simulating retake after completion)
                if attempt > 0:
                    prev_session = db_session.query(TestSession).filter_by(id=session_ids[attempt - 1]).first()
                    prev_session.status = "completed"
                    db_session.commit()

        # Verify: All sessions have unique IDs
        assert len(set(session_ids)) == 3

        # Verify: Each session has its own questions
        for i, session_id in enumerate(session_ids):
            questions = db_session.query(Question).filter_by(session_id=session_id).all()
            assert len(questions) == 5
            # Check that questions are unique to this session
            for q in questions:
                assert f"attempt{i}_q_" in q.id

    # ====================================================================
    # TC-6: Retake with completed session - previous session status unchanged
    # ====================================================================

    @pytest.mark.asyncio
    async def test_retake_preserves_previous_completed_session(
        self, db_session: Session, authenticated_user: User, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """
        TC-6: Verify retake doesn't modify previous completed session's status.

        REQ-B-B2-Retake-2: 이전 세션은 변경되지 않음
        """
        service = QuestionGenerationService(db_session)

        # Create first completed session
        first_session_id = str(uuid4())
        first_session = TestSession(
            id=first_session_id,
            user_id=authenticated_user.id,
            survey_id=user_profile_survey_fixture.id,
            round=1,
            status="completed",
        )
        db_session.add(first_session)
        db_session.commit()

        # Add questions to first session
        for i in range(5):
            question = Question(
                id=str(uuid4()),
                session_id=first_session_id,
                item_type="multiple_choice",
                stem=f"First Q{i+1}",
                choices=["A", "B", "C", "D"],
                answer_schema={"correct_key": "A"},
                difficulty=5,
                category="test",
                round=1,
            )
            db_session.add(question)
        db_session.commit()

        # Mock Agent
        mock_agent = AsyncMock()
        mock_agent.generate_questions = AsyncMock(
            return_value=GenerateQuestionsResponse(
                round_id="round_retake_006",
                items=[create_mock_item(f"retake_q_{i}") for i in range(5)],
                time_limit_seconds=1200,
            )
        )

        with patch("src.backend.services.question_gen_service.create_agent", return_value=mock_agent):
            result = await service.generate_questions(
                user_id=authenticated_user.id,
                survey_id=user_profile_survey_fixture.id,
                round_num=1,
            )

        # Verify: Previous session completely unchanged
        first_session_after = db_session.query(TestSession).filter_by(id=first_session_id).first()
        assert first_session_after.status == "completed"
        assert first_session_after.user_id == authenticated_user.id
        assert first_session_after.survey_id == user_profile_survey_fixture.id
        assert first_session_after.round == 1

        first_questions_after = db_session.query(Question).filter_by(session_id=first_session_id).all()
        assert len(first_questions_after) == 5

    # ====================================================================
    # TC-7: Error when survey not found during retake
    # ====================================================================

    @pytest.mark.asyncio
    async def test_retake_error_survey_not_found(self, db_session: Session, authenticated_user: User) -> None:
        """
        TC-7: Verify error handling when survey_id doesn't exist during retake.

        REQ-B-B2-Retake-1: 설문이 없을 경우 에러 처리 (graceful degradation)
        """
        service = QuestionGenerationService(db_session)

        # Use non-existent survey_id
        non_existent_survey_id = str(uuid4())

        result = await service.generate_questions(
            user_id=authenticated_user.id,
            survey_id=non_existent_survey_id,
            round_num=1,
        )

        # Verify: Error response returned (graceful degradation, not exception)
        assert "error" in result or len(result.get("questions", [])) == 0

    # ====================================================================
    # TC-8: Error handling when Agent fails during retake
    # ====================================================================

    @pytest.mark.asyncio
    async def test_retake_error_agent_failure(
        self, db_session: Session, authenticated_user: User, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """
        TC-8: Verify error handling when Agent fails during retake.

        REQ-B-B2-Retake-1: Agent 실패 시 적절한 에러 처리
        """
        service = QuestionGenerationService(db_session)

        # Mock Agent to fail
        mock_agent = AsyncMock()
        mock_agent.generate_questions = AsyncMock(side_effect=Exception("Agent error: LLM unavailable"))

        with patch("src.backend.services.question_gen_service.create_agent", return_value=mock_agent):
            result = await service.generate_questions(
                user_id=authenticated_user.id,
                survey_id=user_profile_survey_fixture.id,
                round_num=1,
            )

        # Verify: Error response returned (graceful degradation)
        assert "error" in result or len(result.get("questions", [])) == 0
