"""
ItemGenAgent Tests

REQ: REQ-A-ItemGen

Comprehensive test suite for LangChain AgentExecutor-based Item-Gen-Agent.
Tests both Mode 1 (question generation) and Mode 2 (auto-grading).

Reference: LangChain Agent Testing Guide
https://python.langchain.com/docs/how_to/agent_structured_outputs
"""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from src.agent.llm_agent import (
    AnswerSchema,
    GeneratedItem,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    ItemGenAgent,
    ItemScore,
    RoundStats,
    ScoreAnswerRequest,
    ScoreAnswerResponse,
    SubmitAnswersRequest,
    SubmitAnswersResponse,
    UserAnswer,
    create_agent,
)

# ============================================================================
# Fixtures: LLM & Agent Mocking
# ============================================================================


@pytest.fixture
def mock_llm():
    """Mock Google Gemini LLM"""
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_tools():
    """Mock FastMCP tools"""
    tools = [
        MagicMock(name="get_user_profile"),
        MagicMock(name="search_question_templates"),
        MagicMock(name="get_difficulty_keywords"),
        MagicMock(name="validate_question_quality"),
        MagicMock(name="save_generated_question"),
        MagicMock(name="score_and_explain"),
    ]
    for tool in tools:
        tool.func = MagicMock()
    return tools


@pytest.fixture
def agent_instance(mock_llm, mock_tools):
    """Create ItemGenAgent with mocked dependencies"""
    with patch("src.agent.llm_agent.create_llm", return_value=mock_llm):
        with patch("src.agent.llm_agent.TOOLS", mock_tools):
            with patch("src.agent.llm_agent.get_react_prompt") as mock_prompt:
                with patch("src.agent.llm_agent.create_react_agent") as mock_create_agent:
                    # Mock the LangGraph agent (executor)
                    mock_executor = AsyncMock()
                    mock_executor.ainvoke = AsyncMock()
                    mock_create_agent.return_value = mock_executor

                    agent = ItemGenAgent()
                    agent.executor = mock_executor  # Set executor mock
                    return agent


# ============================================================================
# Phase 1: Test Mode 1 - Question Generation (Tool 1-5)
# ============================================================================


class TestGenerateQuestionsHappyPath:
    """Test successful question generation flow"""

    @pytest.mark.asyncio
    async def test_generate_questions_single_question(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Happy path: Generate 1 high-quality question

        Given:
            - Valid GenerateQuestionsRequest (round_idx=1)
        When:
            - generate_questions() is called
        Then:
            - AgentExecutor invokes with correct input format
            - Returns GenerateQuestionsResponse with round_id
            - items list contains 1 GeneratedItem
        """
        request = GenerateQuestionsRequest(
            session_id="session_123",
            survey_id="survey_123",
            round_idx=1,
            prev_answers=None,
        )

        # Mock AgentExecutor output format with intermediate_steps
        agent_instance.executor.ainvoke.return_value = {
            "output": "Generated 1 question successfully",
            "intermediate_steps": [
                ("get_user_profile", "profile_data"),
                ("save_generated_question", json.dumps({
                    "question_id": "q_001",
                    "stem": "What is LLM?",
                    "item_type": "short_answer",
                    "difficulty": 5,
                    "category": "AI",
                    "answer_type": "keyword_match",
                    "correct_keywords": ["large", "language", "model"],
                    "validation_score": 0.90,
                    "saved_at": "2025-11-11T10:00:00Z",
                    "success": True,
                }))
            ]
        }

        response = await agent_instance.generate_questions(request)

        assert isinstance(response, GenerateQuestionsResponse)
        assert response.round_id is not None
        assert len(response.items) == 1
        assert response.items[0].id == "q_001"
        assert response.error_message is None

    @pytest.mark.asyncio
    async def test_generate_questions_multiple_questions(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Generate multiple questions in single round

        Given:
            - GenerateQuestionsRequest with round_idx=2
        When:
            - generate_questions() is called
        Then:
            - Returns response with multiple GeneratedItem objects
        """
        request = GenerateQuestionsRequest(
            session_id="session_456",
            survey_id="survey_456",
            round_idx=2,
            prev_answers=[{"item_id": "q_prev_1", "score": 85}],
        )

        # Helper to create question JSON
        def create_question(qid: int) -> str:
            return json.dumps({
                "question_id": f"q_{qid:03d}",
                "stem": f"Question {qid}",
                "item_type": "multiple_choice",
                "choices": ["A", "B", "C", "D"],
                "answer_type": "exact_match",
                "correct_answer": "A",
                "difficulty": 7,
                "category": "AI",
                "validation_score": 0.88 + qid * 0.01,
                "saved_at": "2025-11-11T10:00:00Z",
                "success": True,
            })

        # Mock AgentExecutor with multiple save_generated_question calls
        agent_instance.executor.ainvoke.return_value = {
            "output": "Generated 3 questions successfully",
            "intermediate_steps": [
                ("get_user_profile", "profile"),
                ("get_difficulty_keywords", "keywords"),
                ("save_generated_question", create_question(1)),
                ("validate_question_quality", "valid"),
                ("save_generated_question", create_question(2)),
                ("validate_question_quality", "valid"),
                ("save_generated_question", create_question(3)),
            ]
        }

        response = await agent_instance.generate_questions(request)

        assert response.round_id is not None
        assert len(response.items) == 3
        assert response.failed_count == 0
        agent_instance.executor.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_questions_adaptive_mode(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Generate questions with previous answers (adaptive testing)

        Given:
            - GenerateQuestionsRequest with prev_answers
        When:
            - generate_questions() is called
        Then:
            - prev_answers included in agent input
            - Difficulty adjusted based on previous performance
        """
        request = GenerateQuestionsRequest(
            session_id="session_adaptive",
            survey_id="survey_adaptive",
            round_idx=2,
            prev_answers=[
                {"item_id": "q_1", "score": 100},
                {"item_id": "q_2", "score": 75}
            ],
        )

        agent_instance.executor.ainvoke.return_value = {
            "output": "Generated adaptive questions",
            "intermediate_steps": []
        }

        response = await agent_instance.generate_questions(request)

        assert isinstance(response, GenerateQuestionsResponse)
        # Verify prev_answers were passed to agent
        call_args = agent_instance.executor.ainvoke.call_args
        # ainvoke is called with {"messages": [HumanMessage(content=agent_input)]}
        messages = call_args[0][0].get("messages", [])
        assert len(messages) > 0, "No messages in ainvoke call"
        agent_input_str = messages[0].content if hasattr(messages[0], 'content') else str(messages[0])
        assert "prev_answers" in agent_input_str.lower() or "previous" in agent_input_str.lower(), \
            f"prev_answers not found in agent input: {agent_input_str}"


class TestGenerateQuestionsValidation:
    """Test input validation for question generation"""

    @pytest.mark.asyncio
    async def test_generate_questions_invalid_round_idx(self):
        """
        REQ: REQ-A-ItemGen
        Reject invalid round_idx (< 1)

        Given:
            - GenerateQuestionsRequest with round_idx=0
        When:
            - Request is created
        Then:
            - Pydantic validation raises ValueError
        """
        with pytest.raises(ValueError):
            GenerateQuestionsRequest(
                session_id="session_test",
                survey_id="survey_test",
                round_idx=0,  # Invalid: < 1
            )

    @pytest.mark.asyncio
    async def test_generate_questions_missing_survey_id(self):
        """
        REQ: REQ-A-ItemGen
        Reject request without survey_id

        Given:
            - GenerateQuestionsRequest without survey_id
        When:
            - Request is created
        Then:
            - Pydantic validation raises error
        """
        with pytest.raises(Exception):  # Missing required field
            GenerateQuestionsRequest(
                session_id="session_test",
                round_idx=1,
            )


class TestGenerateQuestionsErrorHandling:
    """Test error handling in question generation"""

    @pytest.mark.asyncio
    async def test_generate_questions_executor_raises_exception(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Handle executor failure gracefully

        Given:
            - Valid GenerateQuestionsRequest
        When:
            - executor.ainvoke() raises RuntimeError
        Then:
            - Returns GenerateQuestionsResponse with error_message
            - items list is empty
        """
        request = GenerateQuestionsRequest(
            session_id="session_error",
            survey_id="survey_error",
            round_idx=1,
        )

        agent_instance.executor.ainvoke.side_effect = RuntimeError("LLM API timeout")

        response = await agent_instance.generate_questions(request)

        assert isinstance(response, GenerateQuestionsResponse)
        assert len(response.items) == 0
        assert "LLM API timeout" in response.error_message

    @pytest.mark.asyncio
    async def test_generate_questions_malformed_output(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Handle malformed agent output

        Given:
            - executor returns invalid intermediate_steps
        When:
            - _parse_agent_output_generate() is called
        Then:
            - Returns response with error_message
            - Graceful degradation
        """
        request = GenerateQuestionsRequest(
            session_id="session_malformed",
            survey_id="survey_malformed",
            round_idx=1,
        )

        # Invalid output
        agent_instance.executor.ainvoke.return_value = {
            "output": "Invalid",
            "intermediate_steps": None,  # Invalid
        }

        response = await agent_instance.generate_questions(request)

        assert isinstance(response, GenerateQuestionsResponse)
        assert response.round_id is not None


# ============================================================================
# Phase 2: Test Mode 2 - Auto-Grading (Tool 6)
# ============================================================================


class TestScoreAndExplainHappyPath:
    """Test successful auto-grading flow"""

    @pytest.mark.asyncio
    async def test_score_multiple_choice_correct(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Score multiple choice answer (correct)

        Given:
            - ScoreAnswerRequest for multiple_choice
            - user_answer is correct
        When:
            - score_and_explain() is called
        Then:
            - Returns response with correct=True
            - score >= 80
            - explanation provided
        """
        request = ScoreAnswerRequest(
            round_id="round_123",
            item_id="item_001",
            user_answer="A",
            response_time_ms=5000,
        )

        agent_instance.executor.ainvoke.return_value = {
            "output": "Score: 100",
            "intermediate_steps": [
                ("score_and_explain", json.dumps({
                    "correct": True,
                    "score": 100,
                    "explanation": "Option A is correct",
                    "feedback": None,
                    "extracted_keywords": [],
                    "graded_at": "2025-11-11T10:00:00Z",
                }))
            ]
        }

        response = await agent_instance.score_and_explain(request)

        assert isinstance(response, ScoreAnswerResponse)
        assert response.item_id == "item_001"
        assert response.correct is True
        assert response.score == 100

    @pytest.mark.asyncio
    async def test_score_multiple_choice_incorrect(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Score multiple choice answer (incorrect)

        Given:
            - user_answer differs from correct answer
        When:
            - score_and_explain() is called
        Then:
            - Returns response with correct=False
            - score=0
        """
        request = ScoreAnswerRequest(
            round_id="round_124",
            item_id="item_002",
            user_answer="C",
            response_time_ms=8000,
        )

        agent_instance.executor.ainvoke.return_value = {
            "output": "Score: 0",
            "intermediate_steps": [
                ("score_and_explain", json.dumps({
                    "correct": False,
                    "score": 0,
                    "explanation": "The correct answer is B, not C",
                    "feedback": None,
                    "extracted_keywords": [],
                    "graded_at": "2025-11-11T10:01:00Z",
                }))
            ]
        }

        response = await agent_instance.score_and_explain(request)

        assert response.correct is False
        assert response.score == 0

    @pytest.mark.asyncio
    async def test_score_short_answer_with_keywords(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Score short answer with keyword extraction

        Given:
            - Short answer with keyword matching
        When:
            - score_and_explain() is called
        Then:
            - extracted_keywords populated
            - score based on keyword matches
        """
        request = ScoreAnswerRequest(
            round_id="round_125",
            item_id="item_003",
            user_answer="LLM is a large language model trained on vast data.",
            response_time_ms=10000,
        )

        agent_instance.executor.ainvoke.return_value = {
            "output": "Score: 90",
            "intermediate_steps": [
                ("score_and_explain", json.dumps({
                    "correct": True,
                    "score": 90,
                    "explanation": "Excellent understanding",
                    "feedback": "Could mention training techniques",
                    "extracted_keywords": ["large", "language", "model"],
                    "graded_at": "2025-11-11T10:02:00Z",
                }))
            ]
        }

        response = await agent_instance.score_and_explain(request)

        assert response.correct is True
        assert response.score == 90
        assert len(response.extracted_keywords) == 3


class TestScoreAnswerValidation:
    """Test input validation for scoring"""

    @pytest.mark.asyncio
    async def test_score_answer_missing_round_id(self):
        """
        REQ: REQ-A-ItemGen
        round_id is now optional for backward compatibility

        Given:
            - ScoreAnswerRequest without round_id
        When:
            - Request is created
        Then:
            - Request is successfully created (round_id is optional)
        """
        request = ScoreAnswerRequest(
            item_id="item_test",
            user_answer="answer",
        )
        assert request.user_answer == "answer"
        assert request.round_id is None  # round_id is optional

    @pytest.mark.asyncio
    async def test_score_answer_missing_user_answer(self):
        """
        REQ: REQ-A-ItemGen
        Reject request without user_answer

        Given:
            - ScoreAnswerRequest without user_answer
        When:
            - Request is created
        Then:
            - Pydantic validation raises error
        """
        with pytest.raises(Exception):
            ScoreAnswerRequest(
                round_id="round_test",
                item_id="item_test",
            )


class TestScoreAnswerErrorHandling:
    """Test error handling in scoring"""

    @pytest.mark.asyncio
    async def test_score_answer_executor_raises_exception(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Handle executor failure in scoring

        Given:
            - Valid ScoreAnswerRequest
        When:
            - executor.ainvoke() raises RuntimeError
        Then:
            - Returns ScoreAnswerResponse with score=0
            - explanation contains error message
            - correct=False
        """
        request = ScoreAnswerRequest(
            round_id="round_error",
            item_id="item_error",
            user_answer="test answer",
        )

        agent_instance.executor.ainvoke.side_effect = RuntimeError("API unavailable")

        response = await agent_instance.score_and_explain(request)

        assert isinstance(response, ScoreAnswerResponse)
        assert response.score == 0.0
        assert response.correct is False


# ============================================================================
# Phase 3: Test ItemGenAgent Initialization
# ============================================================================


class TestItemGenAgentInitialization:
    """Test agent setup and configuration"""

    def test_agent_initialization_success(self):
        """
        REQ: REQ-A-ItemGen
        Initialize agent with valid config

        Given:
            - GEMINI_API_KEY environment variable set
        When:
            - ItemGenAgent() is called
        Then:
            - LLM is created
            - Prompt is loaded
            - 6 tools are registered
            - AgentExecutor is configured
        """
        with patch("src.agent.llm_agent.create_llm") as mock_create_llm:
            with patch("src.agent.llm_agent.get_react_prompt") as mock_prompt:
                with patch("src.agent.llm_agent.TOOLS") as mock_tools:
                    with patch("src.agent.llm_agent.create_react_agent") as mock_create_agent:
                        mock_llm = MagicMock()
                        mock_create_llm.return_value = mock_llm
                        mock_tools_list = [MagicMock() for _ in range(6)]
                        mock_tools.__iter__ = MagicMock(return_value=iter(mock_tools_list))
                        mock_tools.__len__ = MagicMock(return_value=6)
                        mock_agent = MagicMock()
                        mock_create_agent.return_value = mock_agent

                        agent = ItemGenAgent()

                        assert agent.llm is not None
                        assert agent.tools is not None
                        assert agent.executor is not None

    def test_agent_initialization_no_gemini_api_key(self):
        """
        REQ: REQ-A-ItemGen
        Reject initialization without GEMINI_API_KEY

        Given:
            - GEMINI_API_KEY not set
        When:
            - ItemGenAgent() is called
        Then:
            - Raises ValueError
        """
        with patch("src.agent.llm_agent.create_llm") as mock_create_llm:
            mock_create_llm.side_effect = ValueError("GEMINI_API_KEY not set")

            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                ItemGenAgent()


# ============================================================================
# Phase 4: Test Factory Function
# ============================================================================


class TestCreateAgentFactory:
    """Test create_agent() factory function"""

    @pytest.mark.asyncio
    async def test_create_agent_returns_instance(self):
        """
        REQ: REQ-A-ItemGen
        Factory function returns ItemGenAgent instance

        Given:
            - Valid environment configuration
        When:
            - create_agent() is called
        Then:
            - Returns ItemGenAgent instance
        """
        with patch("src.agent.llm_agent.ItemGenAgent") as MockAgent:
            mock_instance = MagicMock(spec=ItemGenAgent)
            MockAgent.return_value = mock_instance

            result = await create_agent()

            assert result is not None


# ============================================================================
# Phase 5: Test Parsing Logic
# ============================================================================


class TestParseAgentOutputGenerate:
    """Test _parse_agent_output_generate() parsing logic"""

    @pytest.mark.asyncio
    async def test_parse_single_saved_question(self, agent_instance):
        """
        REQ: REQ-A-LangChain
        Parse single save_generated_question tool output

        Given:
            - intermediate_steps with one save_generated_question
        When:
            - _parse_agent_output_generate() is called
        Then:
            - GeneratedItem extracted with answer_schema
        """
        tool_output = {
            "question_id": "q_123",
            "stem": "What is a transformer?",
            "item_type": "short_answer",
            "answer_type": "keyword_match",
            "correct_keywords": ["transformer", "attention"],
            "difficulty": 5,
            "category": "AI",
            "validation_score": 0.92,
            "saved_at": "2025-11-11T10:00:00Z",
            "success": True,
        }

        result = {
            "output": "Generated",
            "intermediate_steps": [
                ("save_generated_question", json.dumps(tool_output))
            ]
        }

        response = agent_instance._parse_agent_output_generate(result, "round_test_123")

        assert isinstance(response, GenerateQuestionsResponse)
        assert response.round_id == "round_test_123"
        assert len(response.items) == 1
        assert response.items[0].id == "q_123"
        assert response.items[0].answer_schema.type == "keyword_match"

    @pytest.mark.asyncio
    async def test_parse_multiple_saved_questions(self, agent_instance):
        """
        REQ: REQ-A-LangChain
        Parse multiple save_generated_question tool outputs

        Given:
            - intermediate_steps with 3 save_generated_question calls
        When:
            - _parse_agent_output_generate() is called
        Then:
            - All 3 items extracted
        """
        result = {
            "output": "Generated 3",
            "intermediate_steps": [
                ("save_generated_question", json.dumps({"question_id": "q1", "stem": "Q1", "success": True})),
                ("save_generated_question", json.dumps({"question_id": "q2", "stem": "Q2", "success": True})),
                ("save_generated_question", json.dumps({"question_id": "q3", "stem": "Q3", "success": True})),
            ]
        }

        response = agent_instance._parse_agent_output_generate(result, "round_multi")

        assert len(response.items) == 3

    @pytest.mark.asyncio
    async def test_parse_malformed_json_in_intermediate_steps(self, agent_instance):
        """
        REQ: REQ-A-LangChain
        Handle malformed JSON in intermediate_steps

        Given:
            - Tool output with invalid JSON
        When:
            - _parse_agent_output_generate() is called
        Then:
            - Gracefully skips malformed entry
            - Returns response with error_message
        """
        result = {
            "output": "Error",
            "intermediate_steps": [
                ("save_generated_question", "invalid json [[[")
            ]
        }

        response = agent_instance._parse_agent_output_generate(result, "round_error")

        assert isinstance(response, GenerateQuestionsResponse)
        assert response.error_message is not None


class TestParseAgentOutputScore:
    """Test _parse_agent_output_score() parsing logic"""

    @pytest.mark.asyncio
    async def test_parse_score_tool_output_json(self, agent_instance):
        """
        REQ: REQ-A-LangChain
        Parse Tool 6 (score_and_explain) output

        Given:
            - Tool 6 returns JSON with correct, score, explanation
        When:
            - _parse_agent_output_score() is called
        Then:
            - Fields extracted correctly
        """
        tool_output = {
            "correct": True,
            "score": 92,
            "explanation": "Excellent understanding",
            "extracted_keywords": ["transformer", "attention"],
            "feedback": "Great work!",
            "graded_at": "2025-11-11T10:00:00Z",
        }

        result = {
            "output": "Graded",
            "intermediate_steps": [
                ("score_and_explain", json.dumps(tool_output))
            ]
        }

        response = agent_instance._parse_agent_output_score(result, "item_test")

        assert isinstance(response, ScoreAnswerResponse)
        assert response.item_id == "item_test"
        assert response.correct is True
        assert response.score == 92

    @pytest.mark.asyncio
    async def test_parse_score_with_extracted_keywords(self, agent_instance):
        """
        REQ: REQ-A-LangChain
        Extract keywords from Tool 6 output

        Given:
            - Short answer scored with keyword extraction
        When:
            - _parse_agent_output_score() is called
        Then:
            - extracted_keywords list populated
        """
        tool_output = {
            "correct": True,
            "score": 85,
            "explanation": "Good understanding",
            "extracted_keywords": ["ai", "learning", "model"],
            "feedback": "Well explained",
            "graded_at": "2025-11-11T11:00:00Z",
        }

        result = {
            "output": "Graded",
            "intermediate_steps": [
                ("score_and_explain", json.dumps(tool_output))
            ]
        }

        response = agent_instance._parse_agent_output_score(result, "item_456")

        assert len(response.extracted_keywords) == 3


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegrationWithMockedComponents:
    """Integration tests with mocked LLM and tools"""

    @pytest.mark.asyncio
    async def test_full_question_generation_flow(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Full Mode 1 flow with complete pipeline

        Given:
            - Complete environment with all tools
        When:
            - Full question generation is executed
        Then:
            - Questions are validated and saved
            - Response contains proper structure
        """
        request = GenerateQuestionsRequest(
            session_id="integration_session",
            survey_id="integration_survey",
            round_idx=1,
        )

        agent_instance.executor.ainvoke.return_value = {
            "output": "Generated 2 questions",
            "intermediate_steps": [
                ("get_user_profile", "{}"),
                ("save_generated_question", json.dumps({
                    "question_id": "q_int_001",
                    "stem": "Integration Q1",
                    "item_type": "multiple_choice",
                    "success": True
                })),
                ("save_generated_question", json.dumps({
                    "question_id": "q_int_002",
                    "stem": "Integration Q2",
                    "item_type": "short_answer",
                    "success": True
                })),
            ]
        }

        response = await agent_instance.generate_questions(request)

        assert response.round_id is not None
        assert len(response.items) == 2
        assert response.time_limit_seconds == 1200

    @pytest.mark.asyncio
    async def test_full_scoring_flow(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Full Mode 2 flow with auto-grading

        Given:
            - Short answer question
        When:
            - score_and_explain() is executed
        Then:
            - Tool 6 processes and returns complete response
        """
        request = ScoreAnswerRequest(
            round_id="integration_round",
            item_id="integration_item",
            user_answer="Transformers use attention mechanisms",
        )

        agent_instance.executor.ainvoke.return_value = {
            "output": "Graded successfully",
            "intermediate_steps": [
                ("score_and_explain", json.dumps({
                    "correct": True,
                    "score": 88,
                    "explanation": "Good explanation",
                    "extracted_keywords": ["transformers", "attention"],
                    "feedback": None,
                    "graded_at": "2025-11-11T10:00:00Z"
                }))
            ]
        }

        response = await agent_instance.score_and_explain(request)

        assert response.item_id == "integration_item"
        assert response.correct is True
        assert response.score == 88


# ============================================================================
# Phase 2: Test Mode 2 - Batch Answer Submission
# ============================================================================


class TestSubmitAnswersBatchHappyPath:
    """Test successful batch answer submission"""

    @pytest.mark.asyncio
    async def test_submit_answers_multiple_items(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Submit answers for multiple items in one batch

        Given:
            - SubmitAnswersRequest with 3 items
        When:
            - submit_answers() is called
        Then:
            - Returns SubmitAnswersResponse with per_item results
            - Includes round_score and round_stats
        """
        request = SubmitAnswersRequest(
            round_id="batch_round_001",
            answers=[
                UserAnswer(item_id="item_1", user_answer="Answer 1", response_time_ms=5000),
                UserAnswer(item_id="item_2", user_answer="Answer 2", response_time_ms=4000),
                UserAnswer(item_id="item_3", user_answer="Answer 3", response_time_ms=6000),
            ]
        )

        # Mock score_and_explain to return different scores
        responses = [
            ScoreAnswerResponse(
                item_id="item_1", correct=True, score=90.0,
                extracted_keywords=["keyword1"], explanation="Good", feedback=None,
                graded_at=datetime.now(UTC).isoformat()
            ),
            ScoreAnswerResponse(
                item_id="item_2", correct=True, score=85.0,
                extracted_keywords=["keyword2"], explanation="Good", feedback=None,
                graded_at=datetime.now(UTC).isoformat()
            ),
            ScoreAnswerResponse(
                item_id="item_3", correct=False, score=50.0,
                extracted_keywords=[], explanation="Incomplete", feedback=None,
                graded_at=datetime.now(UTC).isoformat()
            ),
        ]

        agent_instance.score_and_explain = AsyncMock(side_effect=responses)

        response = await agent_instance.submit_answers(request)

        # Verify response structure
        assert isinstance(response, SubmitAnswersResponse)
        assert response.round_id == "batch_round_001"
        assert len(response.per_item) == 3

        # Verify per-item results
        assert response.per_item[0].item_id == "item_1"
        assert response.per_item[0].correct is True
        assert response.per_item[0].score == 90.0

        assert response.per_item[1].correct is True
        assert response.per_item[2].correct is False

    @pytest.mark.asyncio
    async def test_submit_answers_single_item(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Submit answers for single item in batch

        Given:
            - SubmitAnswersRequest with 1 item
        When:
            - submit_answers() is called
        Then:
            - Returns response with 1 per_item result
        """
        request = SubmitAnswersRequest(
            round_id="single_batch",
            answers=[
                UserAnswer(item_id="solo_item", user_answer="Solo answer", response_time_ms=3000),
            ]
        )

        mock_response = ScoreAnswerResponse(
            item_id="solo_item", correct=True, score=100.0,
            extracted_keywords=[], explanation="Perfect", feedback=None,
            graded_at=datetime.now(UTC).isoformat()
        )

        agent_instance.score_and_explain = AsyncMock(return_value=mock_response)

        response = await agent_instance.submit_answers(request)

        assert len(response.per_item) == 1
        assert response.per_item[0].item_id == "solo_item"
        assert response.round_score == 100.0


class TestSubmitAnswersStatistics:
    """Test RoundStats calculation in batch submission"""

    @pytest.mark.asyncio
    async def test_round_stats_calculation(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Verify RoundStats aggregation

        Given:
            - Batch with 3 items (scores: 90, 80, 70; times: 5000, 4000, 6000)
        When:
            - submit_answers() is called
        Then:
            - round_score = 80.0 (average)
            - correct_count = 3
            - total_count = 3
            - avg_response_time = 5000.0 (average)
        """
        request = SubmitAnswersRequest(
            round_id="stats_test",
            answers=[
                UserAnswer(item_id="s1", user_answer="A1", response_time_ms=5000),
                UserAnswer(item_id="s2", user_answer="A2", response_time_ms=4000),
                UserAnswer(item_id="s3", user_answer="A3", response_time_ms=6000),
            ]
        )

        responses = [
            ScoreAnswerResponse(item_id="s1", correct=True, score=90.0, extracted_keywords=[], explanation="", feedback=None, graded_at=datetime.now(UTC).isoformat()),
            ScoreAnswerResponse(item_id="s2", correct=True, score=80.0, extracted_keywords=[], explanation="", feedback=None, graded_at=datetime.now(UTC).isoformat()),
            ScoreAnswerResponse(item_id="s3", correct=True, score=70.0, extracted_keywords=[], explanation="", feedback=None, graded_at=datetime.now(UTC).isoformat()),
        ]

        agent_instance.score_and_explain = AsyncMock(side_effect=responses)

        response = await agent_instance.submit_answers(request)

        # Verify round score (average of 90, 80, 70)
        assert response.round_score == 80.0

        # Verify round stats
        assert response.round_stats.correct_count == 3
        assert response.round_stats.total_count == 3
        # Average of 5000, 4000, 6000 = 5000
        assert response.round_stats.avg_response_time == 5000.0

    @pytest.mark.asyncio
    async def test_round_stats_partial_correct(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Calculate stats when some answers are incorrect

        Given:
            - Batch with 4 items (2 correct, 2 incorrect)
        When:
            - submit_answers() is called
        Then:
            - correct_count = 2
            - total_count = 4
            - round_score includes incorrect answers
        """
        request = SubmitAnswersRequest(
            round_id="partial_correct",
            answers=[
                UserAnswer(item_id="p1", user_answer="A", response_time_ms=3000),
                UserAnswer(item_id="p2", user_answer="B", response_time_ms=3000),
                UserAnswer(item_id="p3", user_answer="C", response_time_ms=3000),
                UserAnswer(item_id="p4", user_answer="D", response_time_ms=3000),
            ]
        )

        responses = [
            ScoreAnswerResponse(item_id="p1", correct=True, score=100.0, extracted_keywords=[], explanation="", feedback=None, graded_at=datetime.now(UTC).isoformat()),
            ScoreAnswerResponse(item_id="p2", correct=True, score=100.0, extracted_keywords=[], explanation="", feedback=None, graded_at=datetime.now(UTC).isoformat()),
            ScoreAnswerResponse(item_id="p3", correct=False, score=0.0, extracted_keywords=[], explanation="", feedback=None, graded_at=datetime.now(UTC).isoformat()),
            ScoreAnswerResponse(item_id="p4", correct=False, score=0.0, extracted_keywords=[], explanation="", feedback=None, graded_at=datetime.now(UTC).isoformat()),
        ]

        agent_instance.score_and_explain = AsyncMock(side_effect=responses)

        response = await agent_instance.submit_answers(request)

        assert response.round_stats.correct_count == 2
        assert response.round_stats.total_count == 4
        # Average of (100, 100, 0, 0) = 50
        assert response.round_score == 50.0


class TestSubmitAnswersValidation:
    """Test input validation for batch submission"""

    @pytest.mark.asyncio
    async def test_submit_answers_empty_batch(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Handle empty batch submission gracefully

        Given:
            - SubmitAnswersRequest with empty answers list
        When:
            - SubmitAnswersRequest is created
        Then:
            - Request is created (validation not enforced at model level)
            - submit_answers() would handle empty list appropriately
        """
        # Note: Empty batch creation is allowed at model level
        # Validation would be enforced at API endpoint level if needed
        request = SubmitAnswersRequest(
            round_id="empty_batch",
            answers=[]
        )
        assert request.round_id == "empty_batch"
        assert len(request.answers) == 0

    @pytest.mark.asyncio
    async def test_submit_answers_missing_round_id(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Handle round_id properly in request

        Given:
            - SubmitAnswersRequest with round_id (required field)
        When:
            - object is created
        Then:
            - Round_id is accepted (Pydantic Field(...) requires it to be non-None)
            - Empty string is technically allowed at model level
        """
        # Required field check: round_id cannot be omitted
        with pytest.raises(ValueError):
            SubmitAnswersRequest(
                # Missing round_id entirely
                answers=[
                    UserAnswer(item_id="test", user_answer="answer", response_time_ms=1000)
                ]
            )

    @pytest.mark.asyncio
    async def test_submit_answers_negative_response_time(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Reject negative response times

        Given:
            - UserAnswer with negative response_time_ms
        When:
            - object is created
        Then:
            - Raises validation error
        """
        with pytest.raises(ValueError):
            UserAnswer(
                item_id="test",
                user_answer="answer",
                response_time_ms=-1000
            )


class TestSubmitAnswersErrorHandling:
    """Test error handling in batch submission"""

    @pytest.mark.asyncio
    async def test_submit_answers_partial_failure_continues(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Batch continues on individual item failure

        Given:
            - 3 items where second item fails during scoring
        When:
            - submit_answers() is called
        Then:
            - First and third items are scored successfully
            - Second item has fallback score (0.0)
            - Batch completes without raising exception
        """
        request = SubmitAnswersRequest(
            round_id="fail_batch",
            answers=[
                UserAnswer(item_id="f1", user_answer="A", response_time_ms=1000),
                UserAnswer(item_id="f2", user_answer="B", response_time_ms=1000),
                UserAnswer(item_id="f3", user_answer="C", response_time_ms=1000),
            ]
        )

        # Second call raises exception, others succeed
        def side_effect(*args, **kwargs):
            request_arg = args[0]
            if request_arg.item_id == "f2":
                raise RuntimeError("Scoring failed")
            if request_arg.item_id == "f1":
                return ScoreAnswerResponse(item_id="f1", correct=True, score=90.0, extracted_keywords=[], explanation="", feedback=None, graded_at=datetime.now(UTC).isoformat())
            return ScoreAnswerResponse(item_id="f3", correct=False, score=50.0, extracted_keywords=[], explanation="", feedback=None, graded_at=datetime.now(UTC).isoformat())

        agent_instance.score_and_explain = AsyncMock(side_effect=side_effect)

        response = await agent_instance.submit_answers(request)

        # Verify batch completed despite partial failure
        assert len(response.per_item) == 3
        assert response.per_item[0].score == 90.0
        # Second item should have fallback score of 0.0
        assert response.per_item[1].score == 0.0
        assert response.per_item[1].correct is False
        assert response.per_item[2].score == 50.0

    @pytest.mark.asyncio
    async def test_submit_answers_executor_timeout(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Handle executor timeout gracefully

        Given:
            - Executor times out during batch scoring
        When:
            - submit_answers() is called
        Then:
            - All items get fallback score (0.0)
            - Response is returned with error indication
        """
        request = SubmitAnswersRequest(
            round_id="timeout_batch",
            answers=[
                UserAnswer(item_id="t1", user_answer="A", response_time_ms=1000),
            ]
        )

        agent_instance.score_and_explain = AsyncMock(
            side_effect=TimeoutError("Scoring timeout")
        )

        response = await agent_instance.submit_answers(request)

        # Verify fallback response
        assert response.per_item[0].score == 0.0
        assert response.per_item[0].correct is False


class TestSubmitAnswersIntegration:
    """Integration tests for batch submission"""

    @pytest.mark.asyncio
    async def test_submit_answers_response_structure(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Verify complete response structure

        Given:
            - Valid batch submission
        When:
            - submit_answers() returns response
        Then:
            - All required fields are present
            - Types are correct
        """
        request = SubmitAnswersRequest(
            round_id="struct_test",
            answers=[
                UserAnswer(item_id="struct_1", user_answer="Answer", response_time_ms=2000),
                UserAnswer(item_id="struct_2", user_answer="Answer", response_time_ms=3000),
            ]
        )

        responses = [
            ScoreAnswerResponse(item_id="struct_1", correct=True, score=95.0, extracted_keywords=["key1"], explanation="Exp1", feedback="FB1", graded_at=datetime.now(UTC).isoformat()),
            ScoreAnswerResponse(item_id="struct_2", correct=False, score=40.0, extracted_keywords=[], explanation="Exp2", feedback=None, graded_at=datetime.now(UTC).isoformat()),
        ]

        agent_instance.score_and_explain = AsyncMock(side_effect=responses)

        response = await agent_instance.submit_answers(request)

        # Verify all fields present
        assert response.round_id == "struct_test"
        assert isinstance(response.per_item, list)
        assert isinstance(response.round_score, float)
        assert isinstance(response.round_stats, RoundStats)

        # Verify ItemScore fields
        item_1 = response.per_item[0]
        assert item_1.item_id == "struct_1"
        assert item_1.correct is True
        assert item_1.score == 95.0
        assert item_1.extracted_keywords == ["key1"]
        assert item_1.feedback == "FB1"

        # Verify RoundStats fields
        assert response.round_stats.avg_response_time == 2500.0
        assert response.round_stats.correct_count == 1
        assert response.round_stats.total_count == 2
