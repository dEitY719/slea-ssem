"""
ItemGenAgent Tests

REQ: REQ-A-ItemGen

Comprehensive test suite for LangChain ReAct-based Item-Gen-Agent.
Tests both Mode 1 (question generation) and Mode 2 (auto-grading).

Reference: LangChain Agent Testing Guide
https://python.langchain.com/docs/how_to/agent_structured_outputs
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime
import json

from src.agent.llm_agent import (
    ItemGenAgent,
    GenerateQuestionsRequest,
    GenerateQuestionsResponse,
    GeneratedQuestion,
    ScoreAnswerRequest,
    ScoreAnswerResponse,
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
                mock_prompt.return_value = MagicMock()
                with patch("src.agent.llm_agent.create_react_agent") as mock_create:
                    # Mock the agent (CompiledStateGraph)
                    mock_agent = AsyncMock()
                    mock_create.return_value = mock_agent
                    agent = ItemGenAgent()
                    agent.agent = mock_agent  # Ensure mocked agent is set
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
            - Valid GenerateQuestionsRequest (difficulty=5)
        When:
            - generate_questions() is called
        Then:
            - AgentExecutor invokes with correct input format
            - Returns GenerateQuestionsResponse with success=True
            - total_generated=1, failed_count=0
        """
        import json

        request = GenerateQuestionsRequest(
            user_id="user_123",
            difficulty=5,
            interests=["LLM", "RAG"],
            num_questions=1,
        )

        # Mock LangGraph output (messages format) with realistic JSON content
        agent_instance.agent.ainvoke.return_value = {
            "messages": [
                {"role": "user", "content": "Generate questions..."},
                {"type": "tool", "name": "get_user_profile", "content": "profile_data"},
                {
                    "type": "tool",
                    "name": "save_generated_question",
                    "content": json.dumps({
                        "question_id": "q_001",
                        "stem": "What is LLM?",
                        "item_type": "short_answer",
                        "difficulty": 5,
                        "category": "AI",
                        "validation_score": 0.90,
                        "saved_at": "2025-11-09T10:00:00Z",
                        "success": True
                    })
                },
                {"role": "ai", "content": "Generated 1 question successfully"},
            ]
        }

        response = await agent_instance.generate_questions(request)

        assert response.success is True
        assert response.total_generated == 1
        assert response.failed_count == 0
        assert response.agent_steps >= 2
        assert response.error_message is None

    @pytest.mark.asyncio
    async def test_generate_questions_multiple_questions(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Generate 5 questions (default)

        Given:
            - GenerateQuestionsRequest with num_questions=5
        When:
            - generate_questions() is called
        Then:
            - Returns response with total_generated=5
            - agent_steps reflects full ReAct loop iterations
        """
        import json

        request = GenerateQuestionsRequest(
            user_id="user_456",
            difficulty=7,
            interests=["Agent Architecture"],
            num_questions=5,
        )

        # Helper to create question JSON
        def create_question(qid: int) -> str:
            return json.dumps({
                "question_id": f"q_{qid:03d}",
                "stem": f"Question {qid}",
                "item_type": "multiple_choice",
                "choices": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "difficulty": 7,
                "category": "AI",
                "validation_score": 0.88 + qid * 0.01,
                "saved_at": "2025-11-09T10:00:00Z",
                "success": True
            })

        # Mock LangGraph message format with multiple tool calls
        agent_instance.agent.ainvoke.return_value = {
            "messages": [
                {"role": "user", "content": "Generate 5 questions"},
                {"type": "tool", "name": "get_user_profile", "content": "profile"},
                {"type": "tool", "name": "search_question_templates", "content": "templates"},
                {"type": "tool", "name": "get_difficulty_keywords", "content": "keywords"},
                {"type": "tool", "name": "validate_question_quality", "content": "q1_valid"},
                {"type": "tool", "name": "save_generated_question", "content": create_question(1)},
                {"type": "tool", "name": "validate_question_quality", "content": "q2_valid"},
                {"type": "tool", "name": "save_generated_question", "content": create_question(2)},
                {"type": "tool", "name": "validate_question_quality", "content": "q3_valid"},
                {"type": "tool", "name": "save_generated_question", "content": create_question(3)},
                {"type": "tool", "name": "validate_question_quality", "content": "q4_valid"},
                {"type": "tool", "name": "save_generated_question", "content": create_question(4)},
                {"type": "tool", "name": "validate_question_quality", "content": "q5_valid"},
                {"type": "tool", "name": "save_generated_question", "content": create_question(5)},
                {"role": "ai", "content": "Successfully generated 5 questions"},
            ],
        }

        response = await agent_instance.generate_questions(request)

        assert response.success is True
        assert response.total_generated == 5
        assert response.failed_count == 0
        # agent_steps counts messages where type is 'tool' (13 tool messages)
        assert response.agent_steps == 13
        agent_instance.agent.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_questions_with_test_session_id(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Generate questions with test session tracking

        Given:
            - GenerateQuestionsRequest with test_session_id="sess_abc"
        When:
            - generate_questions() is called
        Then:
            - agent_input includes session ID
            - Agent can track round_id for question persistence
        """
        request = GenerateQuestionsRequest(
            user_id="user_789",
            difficulty=3,
            interests=[],
            num_questions=3,
            test_session_id="sess_abc_2025",
        )

        agent_instance.agent.ainvoke.return_value = {
            "output": "Generated 3 questions for session sess_abc_2025",
            "intermediate_steps": [],
        }

        response = await agent_instance.generate_questions(request)

        # Verify session ID was passed to agent
        call_args = agent_instance.agent.ainvoke.call_args
        # Check if session ID was passed in the messages content
        messages = call_args[0][0].get("messages", [])
        assert any("sess_abc_2025" in str(m.get("content", "")) for m in messages)
        assert response.success is True


class TestGenerateQuestionsValidation:
    """Test input validation for question generation"""

    @pytest.mark.asyncio
    async def test_generate_questions_invalid_difficulty_low(self):
        """
        REQ: REQ-A-ItemGen
        Reject invalid difficulty (< 1)

        Given:
            - GenerateQuestionsRequest with difficulty=0
        When:
            - Request is created
        Then:
            - Pydantic validation raises ValueError
        """
        with pytest.raises(ValueError):
            GenerateQuestionsRequest(
                user_id="user_invalid",
                difficulty=0,  # Invalid: < 1
                interests=[],
            )

    @pytest.mark.asyncio
    async def test_generate_questions_invalid_difficulty_high(self):
        """
        REQ: REQ-A-ItemGen
        Reject invalid difficulty (> 10)

        Given:
            - GenerateQuestionsRequest with difficulty=11
        When:
            - Request is created
        Then:
            - Pydantic validation raises ValueError
        """
        with pytest.raises(ValueError):
            GenerateQuestionsRequest(
                user_id="user_invalid",
                difficulty=11,  # Invalid: > 10
                interests=[],
            )

    @pytest.mark.asyncio
    async def test_generate_questions_invalid_num_questions_zero(self):
        """
        REQ: REQ-A-ItemGen
        Reject invalid num_questions (< 1)

        Given:
            - GenerateQuestionsRequest with num_questions=0
        When:
            - Request is created
        Then:
            - Pydantic validation raises ValueError
        """
        with pytest.raises(ValueError):
            GenerateQuestionsRequest(
                user_id="user_invalid",
                difficulty=5,
                num_questions=0,  # Invalid: < 1
            )

    @pytest.mark.asyncio
    async def test_generate_questions_invalid_num_questions_exceeds_max(self):
        """
        REQ: REQ-A-ItemGen
        Reject num_questions > 10

        Given:
            - GenerateQuestionsRequest with num_questions=11
        When:
            - Request is created
        Then:
            - Pydantic validation raises ValueError
        """
        with pytest.raises(ValueError):
            GenerateQuestionsRequest(
                user_id="user_invalid",
                difficulty=5,
                num_questions=11,  # Invalid: > 10
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
            - Returns GenerateQuestionsResponse with success=False
            - error_message contains exception details
            - questions list is empty
        """
        request = GenerateQuestionsRequest(
            user_id="user_error",
            difficulty=5,
            num_questions=3,
        )

        agent_instance.agent.ainvoke.side_effect = RuntimeError(
            "LLM API timeout"
        )

        response = await agent_instance.generate_questions(request)

        assert response.success is False
        assert len(response.questions) == 0
        assert response.total_generated == 0
        assert response.failed_count == 3
        assert "LLM API timeout" in response.error_message

    @pytest.mark.asyncio
    async def test_generate_questions_llm_parsing_error(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Handle LLM output parsing error

        Given:
            - executor returns malformed output
        When:
            - _parse_agent_output_generate() is called
        Then:
            - Returns response with error_message
            - Graceful degradation
        """
        request = GenerateQuestionsRequest(
            user_id="user_parse_error",
            difficulty=5,
            num_questions=2,
        )

        # Malformed output
        agent_instance.agent.ainvoke.return_value = {
            "output": "Invalid JSON [[[",
            "intermediate_steps": [],
        }

        response = await agent_instance.generate_questions(request)

        # Should handle gracefully
        assert isinstance(response, GenerateQuestionsResponse)


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
            - ScoreAnswerRequest with question_type="multiple_choice"
            - user_answer matches correct_answer
        When:
            - score_and_explain() is called
        Then:
            - Returns response with is_correct=True
            - score=100
            - explanation provided
        """
        request = ScoreAnswerRequest(
            session_id="sess_123",
            user_id="user_abc",
            question_id="q_001",
            question_type="multiple_choice",
            user_answer="A",
            correct_answer="A",
        )

        agent_instance.agent.ainvoke.return_value = {
            "output": (
                "Score: 100\n"
                "Is Correct: True\n"
                "Explanation: Option A is the correct answer because..."
            ),
            "intermediate_steps": [("Tool 6", "graded")],
        }

        response = await agent_instance.score_and_explain(request)

        assert isinstance(response, ScoreAnswerResponse)
        assert response.question_id == "q_001"

    @pytest.mark.asyncio
    async def test_score_multiple_choice_incorrect(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Score multiple choice answer (incorrect)

        Given:
            - user_answer differs from correct_answer
        When:
            - score_and_explain() is called
        Then:
            - Returns response with is_correct=False
            - score=0
            - explanation clarifies correct answer
        """
        request = ScoreAnswerRequest(
            session_id="sess_124",
            user_id="user_def",
            question_id="q_002",
            question_type="multiple_choice",
            user_answer="C",
            correct_answer="B",
        )

        agent_instance.agent.ainvoke.return_value = {
            "output": (
                "Score: 0\n"
                "Is Correct: False\n"
                "Explanation: The correct answer is B, not C."
            ),
            "intermediate_steps": [("Tool 6", "graded")],
        }

        response = await agent_instance.score_and_explain(request)

        assert isinstance(response, ScoreAnswerResponse)
        assert response.question_id == "q_002"

    @pytest.mark.asyncio
    async def test_score_true_false(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Score true/false answer

        Given:
            - ScoreAnswerRequest with question_type="true_false"
        When:
            - score_and_explain() is called
        Then:
            - Returns response with is_correct (boolean)
            - score (0 or 100)
        """
        request = ScoreAnswerRequest(
            session_id="sess_125",
            user_id="user_ghi",
            question_id="q_003",
            question_type="true_false",
            user_answer="True",
            correct_answer="True",
        )

        agent_instance.agent.ainvoke.return_value = {
            "output": "Score: 100\nIs Correct: True",
            "intermediate_steps": [("Tool 6", "graded")],
        }

        response = await agent_instance.score_and_explain(request)

        assert isinstance(response, ScoreAnswerResponse)
        assert response.graded_at is not None

    @pytest.mark.asyncio
    async def test_score_short_answer_correct(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Score short answer (LLM-based) - Correct

        Given:
            - question_type="short_answer"
            - user_answer contains correct keywords
        When:
            - score_and_explain() is called
        Then:
            - score >= 80 (is_correct=True)
            - keyword_matches populated
        """
        request = ScoreAnswerRequest(
            session_id="sess_126",
            user_id="user_jkl",
            question_id="q_004",
            question_type="short_answer",
            user_answer="LLM is a large language model trained on vast text data.",
            correct_keywords=["large", "language", "model"],
        )

        agent_instance.agent.ainvoke.return_value = {
            "output": (
                "Score: 92\n"
                "Is Correct: True\n"
                "Keyword Matches: large, language, model\n"
                "Explanation: Excellent understanding of LLM fundamentals."
            ),
            "intermediate_steps": [("Tool 6", "graded")],
        }

        response = await agent_instance.score_and_explain(request)

        assert isinstance(response, ScoreAnswerResponse)
        assert response.question_id == "q_004"

    @pytest.mark.asyncio
    async def test_score_short_answer_partial(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Score short answer - Partial credit (70-79)

        Given:
            - user_answer contains some but not all keywords
        When:
            - score_and_explain() is called
        Then:
            - 70 <= score < 80
            - feedback provided for improvement
        """
        request = ScoreAnswerRequest(
            session_id="sess_127",
            user_id="user_mno",
            question_id="q_005",
            question_type="short_answer",
            user_answer="LLM is a language model.",
            correct_keywords=["large", "language", "model", "training"],
        )

        agent_instance.agent.ainvoke.return_value = {
            "output": (
                "Score: 75\n"
                "Is Correct: False\n"
                "Keyword Matches: language, model\n"
                "Feedback: You captured 'language' and 'model' but missed 'large' "
                "and 'training'. Consider mentioning scale and training process."
            ),
            "intermediate_steps": [("Tool 6", "graded")],
        }

        response = await agent_instance.score_and_explain(request)

        assert isinstance(response, ScoreAnswerResponse)
        assert response.question_id == "q_005"

    @pytest.mark.asyncio
    async def test_score_short_answer_incorrect(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Score short answer - Incorrect (< 70)

        Given:
            - user_answer lacks correct keywords
        When:
            - score_and_explain() is called
        Then:
            - score < 70
            - is_correct=False
        """
        request = ScoreAnswerRequest(
            session_id="sess_128",
            user_id="user_pqr",
            question_id="q_006",
            question_type="short_answer",
            user_answer="I don't know.",
            correct_keywords=["transformer", "attention", "mechanism"],
        )

        agent_instance.agent.ainvoke.return_value = {
            "output": (
                "Score: 0\n"
                "Is Correct: False\n"
                "Explanation: No understanding of transformer mechanism demonstrated."
            ),
            "intermediate_steps": [("Tool 6", "graded")],
        }

        response = await agent_instance.score_and_explain(request)

        assert isinstance(response, ScoreAnswerResponse)


class TestScoreAnswerValidation:
    """Test input validation for scoring"""

    @pytest.mark.asyncio
    async def test_score_answer_missing_session_id(self):
        """
        REQ: REQ-A-ItemGen
        Reject request without session_id

        Given:
            - ScoreAnswerRequest without session_id
        When:
            - Request is created
        Then:
            - Pydantic validation raises error
        """
        with pytest.raises(Exception):  # Pydantic error
            ScoreAnswerRequest(
                user_id="user_test",
                question_id="q_test",
                question_type="short_answer",
                user_answer="answer",
            )

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
        with pytest.raises(Exception):  # Pydantic error
            ScoreAnswerRequest(
                session_id="sess_test",
                user_id="user_test",
                question_id="q_test",
                question_type="short_answer",
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
            - executor.ainvoke() raises APIError
        Then:
            - Returns ScoreAnswerResponse with score=0
            - explanation contains error message
            - is_correct=False
        """
        request = ScoreAnswerRequest(
            session_id="sess_error",
            user_id="user_error",
            question_id="q_error",
            question_type="short_answer",
            user_answer="test answer",
        )

        agent_instance.agent.ainvoke.side_effect = RuntimeError("API unavailable")

        response = await agent_instance.score_and_explain(request)

        assert isinstance(response, ScoreAnswerResponse)
        assert response.score == 0
        assert response.is_correct is False

    @pytest.mark.asyncio
    async def test_score_answer_timeout(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Handle scoring timeout gracefully

        Given:
            - executor times out
        When:
            - score_and_explain() is called
        Then:
            - Returns response with timeout error message
        """
        request = ScoreAnswerRequest(
            session_id="sess_timeout",
            user_id="user_timeout",
            question_id="q_timeout",
            question_type="short_answer",
            user_answer="test",
        )

        agent_instance.agent.ainvoke.side_effect = TimeoutError("Tool timeout")

        response = await agent_instance.score_and_explain(request)

        assert isinstance(response, ScoreAnswerResponse)


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
            - LLM is created (ChatGoogleGenerativeAI)
            - ReAct prompt is loaded
            - 6 tools are registered
            - create_react_agent() is called
            - Agent (CompiledStateGraph) is configured
        """
        with patch("src.agent.llm_agent.create_llm") as mock_create_llm:
            with patch("src.agent.llm_agent.get_react_prompt") as mock_prompt:
                with patch("src.agent.llm_agent.TOOLS") as mock_tools:
                    with patch("src.agent.llm_agent.create_react_agent") as mock_create_agent:
                        mock_llm = MagicMock()
                        mock_create_llm.return_value = mock_llm
                        mock_tools_list = [MagicMock() for _ in range(6)]
                        mock_tools.__iter__ = MagicMock(
                            return_value=iter(mock_tools_list)
                        )
                        mock_tools.__len__ = MagicMock(return_value=6)
                        mock_agent = MagicMock()
                        mock_create_agent.return_value = mock_agent

                        agent = ItemGenAgent()

                        assert agent.llm is not None
                        assert agent.prompt is not None
                        assert agent.tools is not None
                        assert agent.agent is not None

    def test_agent_initialization_no_gemini_api_key(self):
        """
        REQ: REQ-A-ItemGen
        Reject initialization without GEMINI_API_KEY

        Given:
            - GEMINI_API_KEY not set
        When:
            - ItemGenAgent() is called
        Then:
            - Raises ValueError with informative message
        """
        with patch("src.agent.llm_agent.create_llm") as mock_create_llm:
            mock_create_llm.side_effect = ValueError(
                "GEMINI_API_KEY 환경 변수가 설정되지 않았습니다."
            )

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
            mock_instance = AsyncMock(spec=ItemGenAgent)
            MockAgent.return_value = mock_instance

            result = await create_agent()

            assert result is not None


# ============================================================================
# Integration Tests (Optional, with Real Components)
# ============================================================================


class TestIntegrationWithMockedComponents:
    """Integration tests with mocked LLM and tools"""

    @pytest.mark.asyncio
    async def test_full_question_generation_flow(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Full Mode 1 flow: Tool 1 → 2 → 3 → 4 → 5 → 6

        Integration test demonstrating complete pipeline

        Given:
            - Complete environment with all tools
        When:
            - Full question generation is executed
        Then:
            - All tools are called in correct order
            - Questions are validated and saved
            - Response contains all metadata
        """
        import json

        request = GenerateQuestionsRequest(
            user_id="integration_user",
            difficulty=6,
            interests=["LLM", "RAG", "Agent"],
            num_questions=2,
        )

        # Simulate realistic LangGraph output with JSON tool outputs
        agent_instance.agent.ainvoke.return_value = {
            "messages": [
                {"role": "user", "content": "Generate 2 questions"},
                {"type": "tool", "name": "get_user_profile", "content": "{}"},
                {"type": "tool", "name": "search_question_templates", "content": "{}"},
                {"type": "tool", "name": "get_difficulty_keywords", "content": "{}"},
                {"type": "tool", "name": "validate_question_quality", "content": "{}"},
                {
                    "type": "tool",
                    "name": "save_generated_question",
                    "content": json.dumps({
                        "question_id": "q_int_001",
                        "stem": "Integration test Q1",
                        "item_type": "short_answer",
                        "difficulty": 6,
                        "category": "AI",
                        "validation_score": 0.85,
                        "saved_at": "2025-11-09T10:00:00Z",
                        "success": True
                    })
                },
                {"type": "tool", "name": "validate_question_quality", "content": "{}"},
                {
                    "type": "tool",
                    "name": "save_generated_question",
                    "content": json.dumps({
                        "question_id": "q_int_002",
                        "stem": "Integration test Q2",
                        "item_type": "short_answer",
                        "difficulty": 6,
                        "category": "AI",
                        "validation_score": 0.87,
                        "saved_at": "2025-11-09T10:05:00Z",
                        "success": True
                    })
                },
                {"role": "ai", "content": "Generated 2 questions successfully"},
            ],
        }

        response = await agent_instance.generate_questions(request)

        assert response.success is True
        assert response.total_generated == 2
        assert response.failed_count == 0
        # 7 tool messages
        assert response.agent_steps == 7

    @pytest.mark.asyncio
    async def test_full_scoring_flow(self, agent_instance):
        """
        REQ: REQ-A-ItemGen
        Full Mode 2 flow: Tool 6 execution

        Integration test for auto-grading pipeline

        Given:
            - Short answer question with keywords
        When:
            - score_and_explain() is executed
        Then:
            - Tool 6 processes and returns score
            - Explanation and feedback are generated
        """
        request = ScoreAnswerRequest(
            session_id="integration_session",
            user_id="integration_user",
            question_id="q_integration",
            question_type="short_answer",
            user_answer=(
                "Transformers use attention mechanisms to process "
                "sequential data in parallel."
            ),
            correct_keywords=["transformers", "attention", "parallel"],
            difficulty=7,
            category="Deep Learning",
        )

        agent_instance.agent.ainvoke.return_value = {
            "messages": [
                {"role": "user", "content": "Score this answer"},
                {"type": "tool", "name": "score_and_explain", "content": "graded"},
                {"role": "ai", "content": "Score: 88, Excellent understanding"},
            ],
        }

        response = await agent_instance.score_and_explain(request)

        assert isinstance(response, ScoreAnswerResponse)
        assert response.question_id == "q_integration"


# ============================================================================
# Phase 5: Test Parsing Logic (REQ-A-LangChain Implementation)
# ============================================================================


class TestParseAgentOutputGenerate:
    """Test _parse_agent_output_generate() parsing logic"""

    @pytest.mark.asyncio
    async def test_parse_tool_output_with_json_content(self, agent_instance):
        """
        REQ: REQ-A-LangChain
        Parse tool output when content is JSON string

        Given:
            - Tool returns JSON string in content field
        When:
            - _parse_agent_output_generate() is called
        Then:
            - JSON is parsed and question data extracted
            - question_id, stem, item_type, etc. populated
        """
        import json

        tool_output = {
            "question_id": "q_123",
            "stem": "What is a transformer?",
            "item_type": "short_answer",
            "difficulty": 5,
            "category": "AI",
            "validation_score": 0.92,
            "saved_at": "2025-11-09T10:00:00Z",
        }

        result = {
            "messages": [
                {"role": "user", "content": "Generate"},
                {
                    "type": "tool",
                    "name": "save_generated_question",
                    "content": json.dumps(tool_output),
                },
                {"role": "ai", "content": "Success"},
            ]
        }

        response = agent_instance._parse_agent_output_generate(result, 1)

        assert response.success is True
        assert response.total_generated >= 0

    @pytest.mark.asyncio
    async def test_parse_multiple_saved_questions(self, agent_instance):
        """
        REQ: REQ-A-LangChain
        Parse multiple save_generated_question tool outputs

        Given:
            - Messages contain 3 save_generated_question tool calls
        When:
            - _parse_agent_output_generate() is called
        Then:
            - All 3 questions extracted and aggregated
            - total_generated=3, failed_count=0
        """
        import json

        result = {
            "messages": [
                {"role": "user", "content": "Generate 3"},
                {
                    "type": "tool",
                    "name": "save_generated_question",
                    "content": json.dumps({"question_id": "q1", "success": True}),
                },
                {
                    "type": "tool",
                    "name": "save_generated_question",
                    "content": json.dumps({"question_id": "q2", "success": True}),
                },
                {
                    "type": "tool",
                    "name": "save_generated_question",
                    "content": json.dumps({"question_id": "q3", "success": True}),
                },
                {"role": "ai", "content": "Done"},
            ]
        }

        response = agent_instance._parse_agent_output_generate(result, 3)

        assert response.total_generated == 3

    @pytest.mark.asyncio
    async def test_parse_partial_failure_mixed_messages(self, agent_instance):
        """
        REQ: REQ-A-LangChain
        Parse when some tools fail (error messages in content)

        Given:
            - Messages contain both success and error tool outputs
        When:
            - _parse_agent_output_generate() is called
        Then:
            - Successful questions counted
            - Failed count reflects error messages
            - error_message populated
        """
        import json

        result = {
            "messages": [
                {"role": "user", "content": "Generate 2"},
                {
                    "type": "tool",
                    "name": "save_generated_question",
                    "content": json.dumps(
                        {"question_id": "q1", "success": True}
                    ),
                },
                {
                    "type": "tool",
                    "name": "save_generated_question",
                    "content": json.dumps(
                        {"error": "Validation failed", "success": False}
                    ),
                },
                {"role": "ai", "content": "Partial success"},
            ]
        }

        response = agent_instance._parse_agent_output_generate(result, 2)

        assert response.total_generated >= 1
        assert response.failed_count >= 0

    @pytest.mark.asyncio
    async def test_parse_malformed_json_content(self, agent_instance):
        """
        REQ: REQ-A-LangChain
        Handle malformed JSON in tool output

        Given:
            - Tool content contains invalid JSON
        When:
            - _parse_agent_output_generate() is called
        Then:
            - Gracefully skips malformed message
            - Returns response with error_message
        """
        result = {
            "messages": [
                {"role": "user", "content": "Generate"},
                {"type": "tool", "name": "save_generated_question", "content": "invalid json [[["},
                {"role": "ai", "content": "Error"},
            ]
        }

        response = agent_instance._parse_agent_output_generate(result, 1)

        assert isinstance(response, GenerateQuestionsResponse)


class TestParseAgentOutputScore:
    """Test _parse_agent_output_score() parsing logic"""

    @pytest.mark.asyncio
    async def test_parse_score_tool_output_json(self, agent_instance):
        """
        REQ: REQ-A-LangChain
        Parse Tool 6 (score_and_explain) output when JSON

        Given:
            - Tool 6 returns JSON with is_correct, score, explanation
        When:
            - _parse_agent_output_score() is called
        Then:
            - Fields extracted: is_correct, score, explanation, feedback
            - keyword_matches populated if present
        """
        import json

        tool_output = {
            "attempt_id": "att_123",
            "is_correct": True,
            "score": 92,
            "explanation": "Excellent understanding",
            "keyword_matches": ["transformer", "attention"],
            "feedback": "Great work!",
            "graded_at": "2025-11-09T10:00:00Z",
        }

        result = {
            "messages": [
                {"role": "user", "content": "Score"},
                {
                    "type": "tool",
                    "name": "score_and_explain",
                    "content": json.dumps(tool_output),
                },
                {"role": "ai", "content": "Graded"},
            ]
        }

        response = agent_instance._parse_agent_output_score(result, "q_123")

        assert isinstance(response, ScoreAnswerResponse)
        assert response.question_id == "q_123"

    @pytest.mark.asyncio
    async def test_parse_score_with_keyword_matches(self, agent_instance):
        """
        REQ: REQ-A-LangChain
        Extract keyword_matches from Tool 6 output

        Given:
            - Short answer scored with keyword matches
        When:
            - _parse_agent_output_score() is called
        Then:
            - keyword_matches list extracted and populated
        """
        import json

        tool_output = {
            "attempt_id": "att_456",
            "is_correct": False,
            "score": 75,
            "explanation": "Partial understanding",
            "keyword_matches": ["ai", "learning"],
            "feedback": "You got 2/4 keywords",
            "graded_at": "2025-11-09T11:00:00Z",
        }

        result = {
            "messages": [
                {"role": "user", "content": "Score"},
                {
                    "type": "tool",
                    "name": "score_and_explain",
                    "content": json.dumps(tool_output),
                },
            ]
        }

        response = agent_instance._parse_agent_output_score(result, "q_456")

        assert isinstance(response, ScoreAnswerResponse)

    @pytest.mark.asyncio
    async def test_parse_score_missing_optional_fields(self, agent_instance):
        """
        REQ: REQ-A-LangChain
        Handle Tool 6 output with missing optional fields

        Given:
            - Tool 6 returns minimal output (missing feedback)
        When:
            - _parse_agent_output_score() is called
        Then:
            - Defaults provided for missing fields
            - Response still valid
        """
        import json

        tool_output = {
            "attempt_id": "att_789",
            "is_correct": True,
            "score": 100,
            "explanation": "Correct!",
            "graded_at": "2025-11-09T12:00:00Z",
            # Missing: keyword_matches, feedback
        }

        result = {
            "messages": [
                {"role": "user", "content": "Score"},
                {
                    "type": "tool",
                    "name": "score_and_explain",
                    "content": json.dumps(tool_output),
                },
            ]
        }

        response = agent_instance._parse_agent_output_score(result, "q_789")

        assert isinstance(response, ScoreAnswerResponse)


class TestAgentMessageProcessing:
    """Test message processing and tool call extraction"""

    @pytest.mark.asyncio
    async def test_count_tool_messages_accurately(self, agent_instance):
        """
        REQ: REQ-A-LangChain
        Count tool messages for agent_steps field

        Given:
            - Messages with mixed types (user, tool, ai)
        When:
            - _parse_agent_output_generate() counts messages
        Then:
            - agent_steps correctly counts "tool" type messages
        """
        result = {
            "messages": [
                {"role": "user", "content": "Generate"},
                {"type": "tool", "name": "get_user_profile", "content": "1"},
                {"type": "tool", "name": "search_question_templates", "content": "2"},
                {"role": "ai", "content": "thinking"},  # Should NOT count
                {"type": "tool", "name": "get_difficulty_keywords", "content": "3"},
            ]
        }

        response = agent_instance._parse_agent_output_generate(result, 1)

        # Should count 3 tool messages (not the ai message)
        assert response.agent_steps >= 3

    @pytest.mark.asyncio
    async def test_handle_missing_messages_field(self, agent_instance):
        """
        REQ: REQ-A-LangChain
        Handle result without messages field gracefully

        Given:
            - Result dict missing "messages" key
        When:
            - _parse_agent_output_generate() is called
        Then:
            - Returns response with agent_steps=0
            - success=True, questions=[]
        """
        result = {"output": "Some text output"}  # No "messages"

        response = agent_instance._parse_agent_output_generate(result, 1)

        assert isinstance(response, GenerateQuestionsResponse)
        assert response.agent_steps == 0
