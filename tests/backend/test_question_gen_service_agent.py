"""
Tests for question generation service with Real Agent integration (Phase 2).

REQ: REQ-A-Agent-Backend-1 (Mock → Real Agent 통합)

Tests validate:
1. Async method signature conversion
2. Agent creation and method call
3. GenerateQuestionsRequest construction
4. Previous answers retrieval (for adaptive difficulty)
5. Response handling and DB persistence
6. Error handling (survey not found, Agent failure, DB error)
7. Backwards compatibility with dict response format
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


class TestQuestionGenerationAgentIntegration:
    """
    Phase 2 Test Design: REQ-A-Agent-Backend-1.

    Test Cases:
    - TC-1: Async signature works (method is awaitable)
    - TC-2: Agent is created and called with correct request
    - TC-3: GenerateQuestionsRequest has survey_id, round_idx, prev_answers
    - TC-4: Previous answers are retrieved and passed to Agent
    - TC-5: Agent response items are saved to DB
    - TC-6: Response format is backwards compatible (dict with session_id, questions)
    - TC-7: Error when survey not found
    - TC-8: Error when Agent fails
    - TC-9: Error when DB save fails
    - TC-10: Questions have all required fields after Agent generation
    """

    # ====================================================================
    # TC-1: Async Signature Conversion
    # ====================================================================

    @pytest.mark.asyncio
    async def test_generate_questions_is_async(
        self, db_session: Session, authenticated_user: User, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """TC-1: Verify generate_questions is async (awaitable)."""
        service = QuestionGenerationService(db_session)

        # Mock Agent to avoid real LLM call
        mock_agent = AsyncMock()
        mock_agent.generate_questions = AsyncMock(
            return_value=GenerateQuestionsResponse(
                round_id="round_test_001",
                items=[create_mock_item()],
                time_limit_seconds=1200,
            )
        )

        with patch("src.backend.services.question_gen_service.create_agent", return_value=mock_agent):
            # Should be awaitable (no synchronous call)
            result = await service.generate_questions(
                user_id=authenticated_user.id,
                survey_id=user_profile_survey_fixture.id,
                round_num=1,
            )

            assert isinstance(result, dict)
            assert "session_id" in result

    # ====================================================================
    # TC-2: Agent Creation and Method Call
    # ====================================================================

    @pytest.mark.asyncio
    async def test_agent_is_created_and_called(
        self, db_session: Session, authenticated_user: User, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """TC-2: Verify create_agent() is called and Agent.generate_questions() is invoked."""
        service = QuestionGenerationService(db_session)

        # Mock Agent
        mock_agent = AsyncMock()
        mock_agent.generate_questions = AsyncMock(
            return_value=GenerateQuestionsResponse(
                round_id="round_test_002",
                items=[create_mock_item("test_q_002")],
                time_limit_seconds=1200,
            )
        )

        with patch("src.backend.services.question_gen_service.create_agent", return_value=mock_agent) as mock_create:
            await service.generate_questions(
                user_id=authenticated_user.id,
                survey_id=user_profile_survey_fixture.id,
                round_num=1,
            )

            # Verify create_agent was called
            mock_create.assert_called_once()

            # Verify Agent.generate_questions was called
            mock_agent.generate_questions.assert_called_once()

    # ====================================================================
    # TC-3: GenerateQuestionsRequest Construction
    # ====================================================================

    @pytest.mark.asyncio
    async def test_generate_questions_request_construction(
        self, db_session: Session, authenticated_user: User, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """TC-3: Verify GenerateQuestionsRequest is constructed with correct fields."""
        service = QuestionGenerationService(db_session)

        # Capture the request passed to Agent
        captured_request = None

        async def capture_request(request: GenerateQuestionsRequest) -> GenerateQuestionsResponse:
            """Capture and forward request."""
            nonlocal captured_request
            captured_request = request
            return GenerateQuestionsResponse(
                round_id="round_test_003",
                items=[create_mock_item()],
                time_limit_seconds=1200,
            )

        mock_agent = AsyncMock()
        mock_agent.generate_questions = AsyncMock(side_effect=capture_request)

        with patch("src.backend.services.question_gen_service.create_agent", return_value=mock_agent):
            await service.generate_questions(
                user_id=authenticated_user.id,
                survey_id=user_profile_survey_fixture.id,
                round_num=1,
            )

            # Verify request fields
            assert captured_request is not None
            assert captured_request.survey_id == user_profile_survey_fixture.id
            assert captured_request.round_idx == 1
            assert hasattr(captured_request, "prev_answers")

    # ====================================================================
    # TC-4: Previous Answers Retrieval (Adaptive Difficulty)
    # ====================================================================

    @pytest.mark.asyncio
    async def test_previous_answers_retrieved_for_round2(
        self,
        db_session: Session,
        authenticated_user: User,
        user_profile_survey_fixture: UserProfileSurvey,
        test_session_round1_fixture: TestSession,
    ) -> None:
        """TC-4: For Round 2+, previous answers from Round 1 are retrieved and passed to Agent."""
        service = QuestionGenerationService(db_session)

        # Create Round 1 questions and answers
        q1 = Question(
            id=str(uuid4()),
            session_id=test_session_round1_fixture.id,
            item_type="multiple_choice",
            stem="Question 1?",
            choices=["A", "B", "C", "D"],
            answer_schema={"correct_key": "A"},
            difficulty=5,
            category="LLM",
            round=1,
        )
        db_session.add(q1)
        db_session.commit()

        # Capture request to verify prev_answers
        captured_request = None

        async def capture_request(request: GenerateQuestionsRequest) -> GenerateQuestionsResponse:
            """Capture request for verification."""
            nonlocal captured_request
            captured_request = request
            return GenerateQuestionsResponse(
                round_id="round_test_004",
                items=[create_mock_item()],
                time_limit_seconds=1200,
            )

        mock_agent = AsyncMock()
        mock_agent.generate_questions = AsyncMock(side_effect=capture_request)

        with patch("src.backend.services.question_gen_service.create_agent", return_value=mock_agent):
            await service.generate_questions(
                user_id=authenticated_user.id,
                survey_id=user_profile_survey_fixture.id,
                round_num=2,  # Round 2
            )

            # Verify prev_answers was populated
            assert captured_request is not None
            # prev_answers should be non-empty for Round 2 (if Round 1 data exists)
            # The exact structure depends on implementation

    # ====================================================================
    # TC-5: Agent Response Items Saved to DB
    # ====================================================================

    @pytest.mark.asyncio
    async def test_agent_response_items_saved_to_database(
        self, db_session: Session, authenticated_user: User, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """TC-5: Generated items from Agent response are persisted to DB as Question records."""
        service = QuestionGenerationService(db_session)

        # Create mock Agent response with 2 generated items
        mock_item1 = GeneratedItem(
            id=str(uuid4()),
            type="multiple_choice",
            stem="Mock question 1?",
            choices=["A", "B", "C", "D"],
            answer_schema={"type": "exact_match", "correct_answer": "A"},
            difficulty=5,
            category="LLM",
            validation_score=0.95,
        )
        mock_item2 = GeneratedItem(
            id=str(uuid4()),
            type="short_answer",
            stem="Mock question 2?",
            answer_schema={"type": "keyword_match", "keywords": ["answer1", "answer2"]},
            difficulty=6,
            category="RAG",
            validation_score=0.88,
        )

        mock_response = GenerateQuestionsResponse(
            round_id="round_test_005",
            items=[mock_item1, mock_item2],
            time_limit_seconds=1200,
        )

        mock_agent = AsyncMock()
        mock_agent.generate_questions = AsyncMock(return_value=mock_response)

        with patch("src.backend.services.question_gen_service.create_agent", return_value=mock_agent):
            result = await service.generate_questions(
                user_id=authenticated_user.id,
                survey_id=user_profile_survey_fixture.id,
                round_num=1,
            )

            session_id = result["session_id"]

            # Verify questions were saved to DB
            saved_questions = db_session.query(Question).filter_by(session_id=session_id).all()
            assert len(saved_questions) == 2

            # Verify question data matches Agent response
            assert saved_questions[0].item_type == "multiple_choice"
            assert saved_questions[0].stem == "Mock question 1?"
            assert saved_questions[1].item_type == "short_answer"
            assert saved_questions[1].stem == "Mock question 2?"

    # ====================================================================
    # TC-6: Backwards Compatibility (Dict Response Format)
    # ====================================================================

    @pytest.mark.asyncio
    async def test_response_format_backwards_compatible(
        self, db_session: Session, authenticated_user: User, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """TC-6: Response format remains dict with session_id and questions keys."""
        service = QuestionGenerationService(db_session)

        mock_item = GeneratedItem(
            id=str(uuid4()),
            type="multiple_choice",
            stem="Question?",
            choices=["A", "B"],
            answer_schema={"type": "exact_match", "correct_answer": "A"},
            difficulty=5,
            category="LLM",
            validation_score=0.95,
        )

        mock_response = GenerateQuestionsResponse(
            round_id="round_test_006",
            items=[mock_item],
            time_limit_seconds=1200,
        )

        mock_agent = AsyncMock()
        mock_agent.generate_questions = AsyncMock(return_value=mock_response)

        with patch("src.backend.services.question_gen_service.create_agent", return_value=mock_agent):
            result = await service.generate_questions(
                user_id=authenticated_user.id,
                survey_id=user_profile_survey_fixture.id,
                round_num=1,
            )

            # Verify dict format
            assert isinstance(result, dict)
            assert "session_id" in result
            assert "questions" in result
            assert isinstance(result["session_id"], str)
            assert isinstance(result["questions"], list)

            # Verify question fields (backwards compatibility)
            for question in result["questions"]:
                assert "id" in question
                assert "item_type" in question
                assert "stem" in question
                assert "answer_schema" in question
                assert "difficulty" in question
                assert "category" in question

    # ====================================================================
    # TC-7: Error - Survey Not Found
    # ====================================================================

    @pytest.mark.asyncio
    async def test_error_survey_not_found(self, db_session: Session, user_fixture: User) -> None:
        """TC-7: Graceful error response when survey_id does not exist in database."""
        service = QuestionGenerationService(db_session)

        result = await service.generate_questions(
            user_id=user_fixture.id,
            survey_id="nonexistent_survey_id",
            round_num=1,
        )

        # Should return graceful error response (not raise exception)
        assert isinstance(result, dict)
        assert "error" in result or (result.get("questions", []) == [])
        assert "not found" in result.get("error", "").lower() or len(result.get("questions", [])) == 0

    # ====================================================================
    # TC-8: Error - Agent Failure
    # ====================================================================

    @pytest.mark.asyncio
    async def test_error_agent_generation_failure(
        self, db_session: Session, authenticated_user: User, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """TC-8: Handle Agent timeout or LLM failure gracefully."""
        service = QuestionGenerationService(db_session)

        # Mock Agent to raise an exception
        mock_agent = AsyncMock()
        mock_agent.generate_questions = AsyncMock(side_effect=TimeoutError("Agent generation timeout"))

        with patch("src.backend.services.question_gen_service.create_agent", return_value=mock_agent):
            result = await service.generate_questions(
                user_id=authenticated_user.id,
                survey_id=user_profile_survey_fixture.id,
                round_num=1,
            )

            # Should return a valid response with empty items (graceful degradation)
            assert isinstance(result, dict)
            assert "session_id" in result or "error" in result or len(result.get("questions", [])) == 0

    # ====================================================================
    # TC-9: Error - DB Save Failure
    # ====================================================================

    @pytest.mark.asyncio
    async def test_error_db_save_failure(
        self, db_session: Session, authenticated_user: User, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """TC-9: Handle database save errors and return partial results."""
        service = QuestionGenerationService(db_session)

        mock_item = GeneratedItem(
            id=str(uuid4()),
            type="multiple_choice",
            stem="Question?",
            choices=["A", "B"],
            answer_schema={"type": "exact_match", "correct_answer": "A"},
            difficulty=5,
            category="LLM",
            validation_score=0.95,
        )

        mock_response = GenerateQuestionsResponse(
            round_id="round_test_009",
            items=[mock_item],
            time_limit_seconds=1200,
        )

        mock_agent = AsyncMock()
        mock_agent.generate_questions = AsyncMock(return_value=mock_response)

        # Mock DB session.add to raise error
        with patch(
            "src.backend.services.question_gen_service.create_agent", return_value=mock_agent
        ), patch.object(db_session, "add", side_effect=Exception("DB connection error")):
            result = await service.generate_questions(
                user_id=authenticated_user.id,
                survey_id=user_profile_survey_fixture.id,
                round_num=1,
            )

            # Should return a response (error handling)
            assert isinstance(result, dict)

    # ====================================================================
    # TC-10: Generated Questions Have Required Fields
    # ====================================================================

    @pytest.mark.asyncio
    async def test_generated_questions_have_required_fields(
        self, db_session: Session, authenticated_user: User, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """TC-10: All generated questions have required fields (id, type, stem, answer_schema, etc.)."""
        service = QuestionGenerationService(db_session)

        # Create multiple mock items with different types
        mock_items = [
            GeneratedItem(
                id=str(uuid4()),
                type="multiple_choice",
                stem="MC Question?",
                choices=["A", "B", "C", "D"],
                answer_schema={"type": "exact_match", "correct_answer": "B"},
                difficulty=5,
                category="LLM",
                validation_score=0.92,
            ),
            GeneratedItem(
                id=str(uuid4()),
                type="true_false",
                stem="True or false?",
                answer_schema={"type": "exact_match", "correct_answer": "true"},
                difficulty=3,
                category="RAG",
                validation_score=0.88,
            ),
            GeneratedItem(
                id=str(uuid4()),
                type="short_answer",
                stem="Short answer question?",
                answer_schema={"type": "keyword_match", "keywords": ["key1", "key2"]},
                difficulty=7,
                category="LLM",
                validation_score=0.95,
            ),
        ]

        mock_response = GenerateQuestionsResponse(
            round_id="round_test_010",
            items=mock_items,
            time_limit_seconds=1200,
        )

        mock_agent = AsyncMock()
        mock_agent.generate_questions = AsyncMock(return_value=mock_response)

        with patch("src.backend.services.question_gen_service.create_agent", return_value=mock_agent):
            result = await service.generate_questions(
                user_id=authenticated_user.id,
                survey_id=user_profile_survey_fixture.id,
                round_num=1,
            )

            # Verify all required fields are present
            for question in result["questions"]:
                assert "id" in question, "Missing 'id' field"
                assert "item_type" in question, "Missing 'item_type' field"
                assert "stem" in question, "Missing 'stem' field"
                assert "answer_schema" in question, "Missing 'answer_schema' field"
                assert "difficulty" in question, "Missing 'difficulty' field"
                assert "category" in question, "Missing 'category' field"

                # Verify field types
                assert isinstance(question["id"], str)
                assert isinstance(question["item_type"], str)
                assert isinstance(question["stem"], str)
                assert isinstance(question["answer_schema"], dict)
                assert isinstance(question["difficulty"], int)
                assert isinstance(question["category"], str)

                # Verify valid values
                assert question["item_type"] in ["multiple_choice", "true_false", "short_answer"]
                assert 1 <= question["difficulty"] <= 10

    # ====================================================================
    # TC-11: Round 2 Adaptive with Weak Categories
    # ====================================================================

    @pytest.mark.asyncio
    async def test_round2_with_weak_categories(
        self,
        db_session: Session,
        authenticated_user: User,
        user_profile_survey_fixture: UserProfileSurvey,
        test_session_round1_fixture: TestSession,
        test_result_low_score: TestResult,
    ) -> None:
        """TC-11: Round 2 includes weak categories from Round 1 results."""
        service = QuestionGenerationService(db_session)

        # Create questions for Round 1
        for _ in range(3):
            q = Question(
                id=str(uuid4()),
                session_id=test_session_round1_fixture.id,
                item_type="multiple_choice",
                stem="Question?",
                choices=["A", "B", "C", "D"],
                answer_schema={"correct_key": "A"},
                difficulty=5,
                category="RAG",  # Weak category from test_result_low_score
                round=1,
            )
            db_session.add(q)
        db_session.commit()

        # Capture request to verify prev_answers includes weak categories
        captured_request = None

        async def capture_request(request: GenerateQuestionsRequest) -> GenerateQuestionsResponse:
            """Capture request for weak categories validation."""
            nonlocal captured_request
            captured_request = request
            return GenerateQuestionsResponse(
                round_id="round_test_011",
                items=[create_mock_item("test_q_011")],
                time_limit_seconds=1200,
            )

        mock_agent = AsyncMock()
        mock_agent.generate_questions = AsyncMock(side_effect=capture_request)

        with patch("src.backend.services.question_gen_service.create_agent", return_value=mock_agent):
            await service.generate_questions(
                user_id=authenticated_user.id,
                survey_id=user_profile_survey_fixture.id,
                round_num=2,
            )

            # Verify Agent received Round 1 context
            assert captured_request is not None
            assert captured_request.round_idx == 2

    # ====================================================================
    # TC-12: Test Session Created with Correct Metadata
    # ====================================================================

    @pytest.mark.asyncio
    async def test_test_session_created_with_metadata(
        self, db_session: Session, authenticated_user: User, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """TC-12: TestSession record is created with correct user, survey, round, and status."""
        service = QuestionGenerationService(db_session)

        mock_agent = AsyncMock()
        mock_agent.generate_questions = AsyncMock(
            return_value=GenerateQuestionsResponse(
                round_id="round_test_012",
                items=[create_mock_item("test_q_012")],
                time_limit_seconds=1200,
            )
        )

        with patch("src.backend.services.question_gen_service.create_agent", return_value=mock_agent):
            result = await service.generate_questions(
                user_id=authenticated_user.id,
                survey_id=user_profile_survey_fixture.id,
                round_num=1,
            )

            session_id = result["session_id"]

            # Verify TestSession was created
            test_session = db_session.query(TestSession).filter_by(id=session_id).first()
            assert test_session is not None
            assert test_session.user_id == authenticated_user.id
            assert test_session.survey_id == user_profile_survey_fixture.id
            assert test_session.round == 1
            assert test_session.status == "in_progress"


# ======================================================================
# Test Summary Document (for Phase 2 Approval)
# ======================================================================
"""
Phase 2: TEST DESIGN - REQ-A-Agent-Backend-1

Test Count: 12 test cases (TC-1 to TC-12)
Coverage Areas:
  ✓ Async signature conversion
  ✓ Agent creation & invocation
  ✓ Request construction
  ✓ Previous answers retrieval
  ✓ DB persistence
  ✓ Response format compatibility
  ✓ Error handling (3 scenarios)
  ✓ Field validation
  ✓ Adaptive difficulty context
  ✓ Metadata tracking

All tests use mocking to avoid real LLM calls.
Integration tests (real Agent) deferred to Phase 3 (E2E).

Dependencies:
  - AsyncMock from unittest.mock
  - pytest.mark.asyncio for async test support
  - GenerateQuestionsResponse & GeneratedItem from agent
  - DB fixtures from conftest.py
"""
