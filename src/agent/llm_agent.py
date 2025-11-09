"""
Item-Gen-Agent: LangChain ReAct 기반 자율 AI 에이전트.

REQ: REQ-A-ItemGen

개요:
    LangChain의 최신 Agent 패턴 (ReAct)을 사용하여 자동으로 도구를 선택·활용하는
    AI 에이전트입니다. Mode 1 (문항 생성)과 Mode 2 (자동 채점) 두 가지 모드를 지원합니다.

참고:
    - LangChain 공식 문서: https://python.langchain.com/docs/concepts/agents
    - create_react_agent: https://python.langchain.com/api_reference/langchain/agents/
    - 최신 API 버전: LangChain 0.3.x+

품질 기준:
    - 팀 동료 참고 코드 (높은 수준의 문서화)
    - 공식 문서 예시 기반 구현
    - 타입 힌트 & 에러 처리 명시
"""

import json
import logging
from datetime import UTC, datetime

from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from src.agent.config import AGENT_CONFIG, create_llm
from src.agent.fastmcp_server import TOOLS
from src.agent.prompts.react_prompt import get_react_prompt

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Schemas (입출력 데이터 계약)
# ============================================================================


class GenerateQuestionsRequest(BaseModel):
    """문항 생성 요청."""

    user_id: str = Field(..., description="사용자 ID (UUID)")
    difficulty: int = Field(..., ge=1, le=10, description="난이도 1~10")
    interests: list[str] = Field(default_factory=list, description="관심분야 (예: ['LLM', 'RAG'])")
    num_questions: int = Field(default=5, ge=1, le=10, description="생성할 문항 개수")
    test_session_id: str | None = Field(default=None, description="테스트 세션 ID (Round ID 생성용)")


class GeneratedQuestion(BaseModel):
    """생성된 문항."""

    question_id: str = Field(..., description="문항 ID (UUID)")
    stem: str = Field(..., description="문항 내용")
    item_type: str = Field(..., description="문항 유형")
    choices: list[str] | None = Field(default=None, description="객관식 선택지")
    correct_answer: str = Field(..., description="정답")
    difficulty: int = Field(..., description="난이도")
    category: str = Field(..., description="카테고리")
    validation_score: float = Field(..., ge=0, le=1, description="검증 점수 (Tool 4)")
    saved_at: str = Field(..., description="저장 시간")


class GenerateQuestionsResponse(BaseModel):
    """문항 생성 응답."""

    success: bool = Field(..., description="성공 여부")
    questions: list[GeneratedQuestion] = Field(default_factory=list, description="생성된 문항 리스트")
    total_generated: int = Field(..., description="생성된 문항 총 개수")
    failed_count: int = Field(..., description="실패한 문항 개수")
    agent_steps: int = Field(..., description="에이전트 반복 횟수 (ReAct 단계)")
    error_message: str | None = Field(default=None, description="에러 메시지")


class ScoreAnswerRequest(BaseModel):
    """자동 채점 요청."""

    session_id: str = Field(..., description="시험 세션 ID")
    user_id: str = Field(..., description="응시자 ID")
    question_id: str = Field(..., description="문항 ID")
    question_type: str = Field(..., description="문항 유형")
    user_answer: str = Field(..., description="응시자의 답변")
    correct_answer: str | None = Field(default=None, description="정답 (객관식/OX용)")
    correct_keywords: list[str] | None = Field(default=None, description="정답 키워드 (주관식용)")
    difficulty: int | None = Field(default=None, description="난이도")
    category: str | None = Field(default=None, description="카테고리")


class ScoreAnswerResponse(BaseModel):
    """자동 채점 응답."""

    attempt_id: str = Field(..., description="채점 ID (UUID)")
    question_id: str = Field(..., description="문항 ID")
    is_correct: bool = Field(..., description="정답 여부")
    score: int = Field(..., ge=0, le=100, description="점수 0~100")
    explanation: str = Field(..., description="정답 해설")
    feedback: str | None = Field(default=None, description="부분 정답 피드백")
    keyword_matches: list[str] = Field(default_factory=list, description="매칭된 키워드 (주관식)")
    graded_at: str = Field(..., description="채점 시간")


# ============================================================================
# ItemGenAgent Main Class
# ============================================================================


class ItemGenAgent:
    """
    LangChain ReAct 기반 Item-Gen-Agent.

    설명:
        - LangChain의 최신 create_react_agent() API 사용
        - FastMCP 도구 (Tool 1-6) 자동 선택 & 실행
        - ReAct 패턴: Thought → Action → Observation → Reflection
        - 구조화된 입출력 (Pydantic)
        - 상세한 로깅 (디버깅)

    사용 예시:
        ```python
        # 에이전트 생성
        agent = ItemGenAgent()

        # Mode 1: 문항 생성
        request = GenerateQuestionsRequest(
            user_id="123",
            difficulty=5,
            interests=["LLM", "RAG"]
        )
        response = await agent.generate_questions(request)

        # Mode 2: 자동 채점
        score_request = ScoreAnswerRequest(
            session_id="sess_123",
            user_id="user_123",
            question_id="q_456",
            question_type="short_answer",
            user_answer="The answer is..."
        )
        score_response = await agent.score_and_explain(score_request)
        ```

    참고:
        - LangChain 공식: https://python.langchain.com/docs/concepts/agents
        - create_react_agent: Thought/Action/Observation 패턴 자동 구현
        - AgentExecutor: 도구 호출 및 에러 처리 관리
    """

    def __init__(self) -> None:
        """
        Initialize ItemGenAgent.

        단계:
            1. LLM 생성 (Google Gemini)
            2. ReAct 프롬프트 로드
            3. FastMCP 도구 등록
            4. create_react_agent()로 에이전트 생성 (LangGraph CompiledStateGraph)

        에러 처리:
            - GEMINI_API_KEY 없음: ValueError
            - LLM 초기화 실패: 로그 + 재시도
        """
        logger.info("ItemGenAgent 초기화 중...")

        try:
            # 1. LLM 생성
            self.llm = create_llm()
            logger.info("✓ LLM (Google Gemini) 생성 완료")

            # 2. ReAct 프롬프트 로드
            self.prompt = get_react_prompt()
            logger.info("✓ ReAct 프롬프트 로드 완료")

            # 3. 도구 목록 (6개)
            self.tools = TOOLS
            logger.info(f"✓ {len(self.tools)}개 도구 등록 완료: {[t.name for t in self.tools]}")

            # 4. create_react_agent() - LangGraph 최신 API (v0.2.x+)
            # 반환: CompiledStateGraph (LangGraph v2 호환)
            # 참고: LangGraph의 create_react_agent는 LangChain의 deprecated initialize_agent를 대체
            self.agent = create_react_agent(
                model=self.llm,
                tools=self.tools,
                prompt=self.prompt,
                debug=AGENT_CONFIG.get("debug", False),
            )
            logger.info("✓ ReAct 에이전트 생성 완료 (LangGraph CompiledStateGraph)")

            logger.info("✅ ItemGenAgent 초기화 성공")

        except Exception as e:
            logger.error(f"❌ ItemGenAgent 초기화 실패: {e}")
            raise

    async def generate_questions(self, request: GenerateQuestionsRequest) -> GenerateQuestionsResponse:
        """
        Mode 1: Generate questions (Tool 1-5 auto-select).

        REQ: REQ-A-Mode1-Pipeline

        단계:
            1. 사용자 프로필 조회 (Tool 1)
            2. 템플릿 검색 (Tool 2) - 선택사항
            3. 난이도별 키워드 조회 (Tool 3)
            4. LLM으로 문항 생성
            5. 각 문항 검증 (Tool 4)
            6. 검증 통과 문항 저장 (Tool 5)

        Args:
            request: GenerateQuestionsRequest

        Returns:
            GenerateQuestionsResponse

        에러 처리:
            - Tool 호출 실패: 자동 재시도 (최대 3회)
            - 에이전트 최대 반복: 부분 결과 반환
            - LLM 오류: 에러 메시지 포함

        참고:
            - AgentExecutor: 도구 호출 및 ReAct 루프 자동 관리
            - Thought/Action/Observation: 에이전트 로그에서 추적 가능

        """
        logger.info(f"📝 문항 생성 시작: user_id={request.user_id}, difficulty={request.difficulty}")

        try:
            # 에이전트 입력 구성
            agent_input = f"""
Generate {request.num_questions} high-quality questions for user {request.user_id}.
Difficulty level: {request.difficulty} (1~10)
User interests: {", ".join(request.interests) if request.interests else "general"}
Test session ID: {request.test_session_id or "new_session"}

Follow these steps:
1. Get user profile (Tool 1)
2. Search templates for interests (Tool 2) if interests are provided
3. Get difficulty keywords (Tool 3)
4. Generate and validate each question (Tool 4)
5. Save validated questions (Tool 5)

Return exactly {request.num_questions} questions with validation scores.
"""

            # 에이전트 실행 (ReAct 루프)
            # CompiledStateGraph (LangGraph)가 다음을 자동으로 수행:
            # - Thought: 에이전트 추론
            # - Action: 도구 선택
            # - Observation: 도구 결과
            # - 반복 또는 종료
            result = await self.agent.ainvoke({"messages": [{"role": "user", "content": agent_input}]})

            logger.info(f"✅ 에이전트 실행 완료: {result}")

            # 결과 파싱
            response = self._parse_agent_output_generate(result, request.num_questions)
            logger.info(f"✅ 문항 생성 성공: {response.total_generated}개 생성, {response.failed_count}개 실패")

            return response

        except Exception as e:
            logger.error(f"❌ 문항 생성 실패: {e}")
            return GenerateQuestionsResponse(
                success=False,
                questions=[],
                total_generated=0,
                failed_count=request.num_questions,
                agent_steps=0,
                error_message=str(e),
            )

    async def score_and_explain(self, request: ScoreAnswerRequest) -> ScoreAnswerResponse:
        """
        Mode 2: Auto-grade answers (Tool 6).

        REQ: REQ-A-Mode2-Pipeline

        단계:
            1. Tool 6 호출 (자동 채점 & 해설 생성)

        Args:
            request: ScoreAnswerRequest

        Returns:
            ScoreAnswerResponse

        에러 처리:
            - Tool 6 호출 실패: 재시도 3회
            - LLM 오류: 기본 점수 0 반환

        참고:
            - Tool 6: 객관식/OX (정확 매칭) vs 주관식 (LLM 평가)
            - 채점 기준: >= 80 → 정답, 70~79 → 부분 정답, < 70 → 오답

        """
        logger.info(f"📋 자동 채점 시작: session_id={request.session_id}, question_id={request.question_id}")

        try:
            # 에이전트 입력 구성
            agent_input = f"""
Score and explain the following answer:

Session ID: {request.session_id}
User ID: {request.user_id}
Question ID: {request.question_id}
Question Type: {request.question_type}
User Answer: {request.user_answer}
Correct Answer: {request.correct_answer or "N/A"}
Correct Keywords: {", ".join(request.correct_keywords) if request.correct_keywords else "N/A"}
Difficulty: {request.difficulty or "unknown"}
Category: {request.category or "general"}

Use Tool 6 (score_and_explain) to:
1. Score the answer (0~100)
2. Generate explanation
3. Provide feedback if needed

Return: is_correct, score, explanation, feedback
"""

            # 에이전트 실행
            result = await self.agent.ainvoke({"messages": [{"role": "user", "content": agent_input}]})

            logger.info(f"✅ 채점 완료: {result}")

            # 결과 파싱
            response = self._parse_agent_output_score(result, request.question_id)
            logger.info(f"✅ 채점 성공: score={response.score}, is_correct={response.is_correct}")

            return response

        except Exception as e:
            logger.error(f"❌ 채점 실패: {e}")
            # 기본값 반환
            return ScoreAnswerResponse(
                attempt_id="error",
                question_id=request.question_id,
                is_correct=False,
                score=0,
                explanation=f"채점 중 오류 발생: {str(e)}",
                graded_at=datetime.now(UTC).isoformat(),
            )

    def _parse_agent_output_generate(self, result: dict, num_questions: int) -> GenerateQuestionsResponse:
        """
        Parse agent output for question generation (REQ-A-LangChain).

        Args:
            result: CompiledStateGraph (LangGraph)의 출력
            num_questions: 요청한 문항 개수

        Returns:
            GenerateQuestionsResponse

        로직:
            1. result["messages"]에서 모든 메시지 추출
            2. type="tool"인 메시지 필터링
            3. tool.name이 "save_generated_question"인 메시지에서 question 데이터 파싱
            4. 각 question을 GeneratedQuestion으로 변환
            5. 성공/실패 개수 집계

        참고:
            - LangGraph CompiledStateGraph 출력은 {"messages": [...]} 형식
            - 각 메시지는 {"type": "tool", "name": "...", "content": "..."} 또는
              {"role": "user/ai", "content": "..."}
            - Tool 출력은 대부분 JSON 문자열 형태

        """
        logger.info("문항 생성 결과 파싱 중...")

        try:
            # 1. 메시지 추출
            messages = result.get("messages", [])
            if not messages:
                logger.warning("메시지 리스트가 비어있음")
                return GenerateQuestionsResponse(
                    success=True,
                    questions=[],
                    total_generated=0,
                    failed_count=num_questions,
                    agent_steps=0,
                )

            # 2. Tool 메시지 개수 (agent_steps)
            tool_messages = [m for m in messages if m.get("type") == "tool"]
            agent_steps = len(tool_messages)
            logger.info(f"Tool 메시지 {agent_steps}개 발견")

            # 3. save_generated_question 도구 결과 파싱
            questions: list[GeneratedQuestion] = []
            failed_count = 0
            error_messages: list[str] = []

            for message in messages:
                if message.get("type") != "tool":
                    continue

                tool_name = message.get("name", "")
                if tool_name != "save_generated_question":
                    continue

                content = message.get("content", "")
                if not content:
                    failed_count += 1
                    continue

                # JSON 파싱
                try:
                    tool_output = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON 파싱 실패: {content[:100]}")
                    failed_count += 1
                    error_messages.append(f"JSON decode error: {str(e)}")
                    continue

                # success 플래그 확인 (없으면 성공으로 간주, error 있으면 실패로 간주)
                has_error = "error" in tool_output
                is_success = tool_output.get("success", not has_error)

                if not is_success or has_error:
                    failed_count += 1
                    if "error" in tool_output:
                        error_messages.append(tool_output["error"])
                    continue

                # GeneratedQuestion 객체 생성
                try:
                    question = GeneratedQuestion(
                        question_id=tool_output.get("question_id", f"q_{datetime.now(UTC).timestamp()}"),
                        stem=tool_output.get("stem", ""),
                        item_type=tool_output.get("item_type", "unknown"),
                        choices=tool_output.get("choices"),
                        correct_answer=tool_output.get("correct_answer", ""),
                        difficulty=tool_output.get("difficulty", 5),
                        category=tool_output.get("category", "general"),
                        validation_score=tool_output.get("validation_score", 0.0),
                        saved_at=tool_output.get("saved_at", datetime.now(UTC).isoformat()),
                    )
                    questions.append(question)
                    logger.info(f"✓ 문항 파싱 성공: {question.question_id}")

                except Exception as e:
                    logger.error(f"GeneratedQuestion 생성 실패: {e}")
                    failed_count += 1
                    error_messages.append(str(e))
                    continue

            # 4. 응답 생성
            total_generated = len(questions) + failed_count
            error_msg = " | ".join(error_messages) if error_messages else None

            response = GenerateQuestionsResponse(
                success=len(questions) > 0,
                questions=questions,
                total_generated=total_generated,
                failed_count=failed_count,
                agent_steps=agent_steps,
                error_message=error_msg,
            )

            logger.info(
                f"✅ 파싱 완료: 성공={len(questions)}, 실패={failed_count}, "
                f"agent_steps={agent_steps}"
            )
            return response

        except Exception as e:
            logger.error(f"❌ 파싱 중 예상치 못한 오류: {e}")
            return GenerateQuestionsResponse(
                success=False,
                questions=[],
                total_generated=0,
                failed_count=num_questions,
                agent_steps=0,
                error_message=f"Parsing error: {str(e)}",
            )

    def _parse_agent_output_score(self, result: dict, question_id: str) -> ScoreAnswerResponse:
        """
        Parse agent output for auto-grading (REQ-A-LangChain).

        Args:
            result: CompiledStateGraph (LangGraph)의 출력
            question_id: 문항 ID

        Returns:
            ScoreAnswerResponse

        로직:
            1. result["messages"]에서 type="tool", name="score_and_explain" 메시지 찾기
            2. 메시지 content를 JSON으로 파싱
            3. is_correct, score, explanation, feedback, keyword_matches 추출
            4. ScoreAnswerResponse로 변환

        참고:
            - Tool 6 (score_and_explain) 출력 구조:
              {
                "attempt_id": "str",
                "is_correct": bool,
                "score": float (0-100),
                "explanation": str,
                "keyword_matches": list[str] (optional),
                "feedback": str (optional),
                "graded_at": str (ISO format)
              }

        """
        logger.info(f"채점 결과 파싱 중... question_id={question_id}")

        try:
            # 1. 메시지 추출
            messages = result.get("messages", [])
            if not messages:
                logger.warning("메시지 리스트가 비어있음")
                return ScoreAnswerResponse(
                    attempt_id="error",
                    question_id=question_id,
                    is_correct=False,
                    score=0,
                    explanation="No messages found",
                    graded_at=datetime.now(UTC).isoformat(),
                )

            # 2. score_and_explain 도구 메시지 찾기
            score_message = None
            for message in messages:
                if message.get("type") == "tool" and message.get("name") == "score_and_explain":
                    score_message = message
                    break

            if not score_message:
                logger.warning("score_and_explain 메시지를 찾을 수 없음")
                return ScoreAnswerResponse(
                    attempt_id="error",
                    question_id=question_id,
                    is_correct=False,
                    score=0,
                    explanation="Tool not executed",
                    graded_at=datetime.now(UTC).isoformat(),
                )

            # 3. JSON 파싱
            content = score_message.get("content", "")
            if not content:
                logger.warning("Tool 메시지 content가 비어있음")
                return ScoreAnswerResponse(
                    attempt_id="error",
                    question_id=question_id,
                    is_correct=False,
                    score=0,
                    explanation="Empty tool output",
                    graded_at=datetime.now(UTC).isoformat(),
                )

            try:
                tool_output = json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON 파싱 실패: {content[:100]}")
                return ScoreAnswerResponse(
                    attempt_id="error",
                    question_id=question_id,
                    is_correct=False,
                    score=0,
                    explanation=f"JSON decode error: {str(e)}",
                    graded_at=datetime.now(UTC).isoformat(),
                )

            # 4. ScoreAnswerResponse 생성
            response = ScoreAnswerResponse(
                attempt_id=tool_output.get("attempt_id", f"att_{datetime.now(UTC).timestamp()}"),
                question_id=question_id,
                is_correct=tool_output.get("is_correct", False),
                score=int(tool_output.get("score", 0)),
                explanation=tool_output.get("explanation", ""),
                feedback=tool_output.get("feedback"),
                keyword_matches=tool_output.get("keyword_matches", []),
                graded_at=tool_output.get("graded_at", datetime.now(UTC).isoformat()),
            )

            logger.info(
                f"✅ 채점 파싱 완료: "
                f"is_correct={response.is_correct}, score={response.score}"
            )
            return response

        except Exception as e:
            logger.error(f"❌ 채점 파싱 중 오류: {e}")
            return ScoreAnswerResponse(
                attempt_id="error",
                question_id=question_id,
                is_correct=False,
                score=0,
                explanation=f"Parsing error: {str(e)}",
                graded_at=datetime.now(UTC).isoformat(),
            )


# ============================================================================
# Factory Function
# ============================================================================


async def create_agent() -> ItemGenAgent:
    """
    Create ItemGenAgent factory function.

    Returns:
        ItemGenAgent: 초기화된 에이전트

    사용:
        ```python
        agent = await create_agent()
        ```

    """
    return ItemGenAgent()
