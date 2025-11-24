"""
Question generation service for generating test questions.

REQ: REQ-B-B2-Gen-1, REQ-B-B2-Gen-2, REQ-B-B2-Gen-3
REQ: REQ-A-Agent-Backend-1 (Real Agent Integration)
REQ: REQ-REFACTOR-SOLID-1 (AnswerSchemaTransformer Pattern)

Implementation: Async service with Real Agent integration for LLM-based question generation.
"""

import asyncio
import logging
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from src.agent.llm_agent import GenerateQuestionsRequest, create_agent
from src.backend.models.answer_schema import TransformerFactory, ValidationError
from src.backend.models.question import Question
from src.backend.models.test_result import TestResult
from src.backend.models.test_session import TestSession
from src.backend.models.user_profile import UserProfileSurvey
from src.backend.services.adaptive_difficulty_service import AdaptiveDifficultyService

logger = logging.getLogger(__name__)


class QuestionGenerationService:
    """
    Service for generating test questions with Real Agent integration.

    REQ: REQ-B-B2-Gen-1, REQ-B-B2-Gen-2, REQ-B-B2-Gen-3
    REQ: REQ-A-Agent-Backend-1 (Real Agent Integration)

    Implementation:
        - generate_questions: Async method using ItemGenAgent (Google Gemini LLM)
        - generate_questions_adaptive: Round 2+ with adaptive difficulty

    Note: MOCK_QUESTIONS kept for fallback/testing purposes only.
    """

    # Mock question templates for different categories and difficulty levels
    MOCK_QUESTIONS = {
        "LLM": [
            {
                "item_type": "multiple_choice",
                "stem": "LLM(Large Language Model)의 핵심 특성으로 가장 적절한 것은?",
                "choices": [
                    "A: 작은 크기의 신경망으로 단순한 패턴만 인식 가능",
                    "B: 수십억 개 이상의 파라미터를 가진 신경망 모델",
                    "C: 음성 인식만 전문으로 하는 모델",
                    "D: 규칙 기반의 고전적 자연어처리 엔진",
                ],
                "answer_schema": {
                    "correct_key": "B",
                    "explanation": "LLM은 수십억에서 조조 개의 파라미터를 가진 대규모 신경망으로, 방대한 양의 텍스트 데이터로부터 언어 패턴을 학습합니다.",  # noqa: E501
                },
                "difficulty": 4,
            },
            {
                "item_type": "true_false",
                "stem": "트랜스포머(Transformer)는 LLM의 기초 아키텍처이다.",
                "answer_schema": {
                    "correct_key": "true",
                    "explanation": "트랜스포머 아키텍처는 어텐션 메커니즘을 기반으로 하며 현대 LLM의 표준 기초입니다.",
                },
                "difficulty": 5,
            },
            {
                "item_type": "short_answer",
                "stem": "LLM의 학습 과정에서 사용되는 주요 기법 중 하나를 설명하시오. (토큰 예측, 강화학습 등)",
                "answer_schema": {
                    "keywords": ["토큰 예측", "강화학습", "자기감독학습", "사전학습"],
                    "explanation": "LLM은 주로 다음 토큰 예측(Next Token Prediction)을 통한 자기감독학습으로 훈련됩니다.",  # noqa: E501
                },
                "difficulty": 6,
            },
            {
                "item_type": "multiple_choice",
                "stem": "ChatGPT와 같은 대화형 LLM을 만들기 위해 필수적인 과정은?",
                "choices": [
                    "A: 사전학습(Pre-training)만으로 충분",
                    "B: 지시어 튜닝(Instruction Tuning)과 강화학습(RLHF)",
                    "C: 단순 데이터 증강(Data Augmentation)만으로 충분",
                    "D: 사용자 피드백이 없어도 가능",
                ],
                "answer_schema": {
                    "correct_key": "B",
                    "explanation": "대화형 LLM은 사전학습 후 지시어 튜닝과 인간 피드백 강화학습(RLHF)을 통해 만들어집니다.",  # noqa: E501
                },
                "difficulty": 7,
            },
            {
                "item_type": "multiple_choice",
                "stem": "LLM의 가장 큰 제한사항은?",
                "choices": [
                    "A: 속도가 매우 빠름",
                    "B: 할루시네이션(거짓 정보 생성) 발생 가능",
                    "C: 학습 데이터가 너무 많음",
                    "D: 파라미터 수가 너무 적음",
                ],
                "answer_schema": {
                    "correct_key": "B",
                    "explanation": "LLM은 통계적 패턴 학습에만 의존하여 사실과 다른 정보를 마치 사실인 것처럼 생성할 수 있습니다.",  # noqa: E501
                },
                "difficulty": 6,
            },
        ],
        "RAG": [
            {
                "item_type": "multiple_choice",
                "stem": "RAG(Retrieval-Augmented Generation)의 핵심 목표는?",
                "choices": [
                    "A: 모든 답변을 사용자 정의 데이터베이스에서 검색",
                    "B: LLM에 외부 지식을 동적으로 추가하여 답변 정확도 향상",
                    "C: 네트워크 속도 개선",
                    "D: 모델 파라미터 감소",
                ],
                "answer_schema": {
                    "correct_key": "B",
                    "explanation": "RAG는 사용자 정의 데이터베이스에서 관련 문서를 검색하여 LLM에 제공함으로써 정확한 답변을 생성합니다.",  # noqa: E501
                },
                "difficulty": 5,
            },
            {
                "item_type": "true_false",
                "stem": "RAG 시스템에서 벡터 데이터베이스는 필수 요소이다.",
                "answer_schema": {
                    "correct_key": "true",
                    "explanation": "벡터 데이터베이스는 의미 기반 유사도 검색을 수행하여 관련 문서를 빠르게 찾습니다.",
                },
                "difficulty": 5,
            },
            {
                "item_type": "short_answer",
                "stem": "RAG의 두 가지 주요 단계를 작성하시오.",
                "answer_schema": {
                    "keywords": ["검색", "생성", "Retrieval", "Generation"],
                    "explanation": "RAG는 (1) 관련 문서 검색 단계와 (2) 검색된 정보를 활용한 생성 단계로 구성됩니다.",
                },
                "difficulty": 4,
            },
            {
                "item_type": "multiple_choice",
                "stem": "RAG에서 사용하는 임베딩 모델의 역할은?",
                "choices": [
                    "A: 텍스트를 벡터 공간으로 변환",
                    "B: 모델 파라미터 압축",
                    "C: 데이터베이스 암호화",
                    "D: API 응답 속도 향상",
                ],
                "answer_schema": {
                    "correct_key": "A",
                    "explanation": "임베딩 모델은 텍스트를 고차원 벡터로 변환하여 의미 기반 검색을 가능하게 합니다.",
                },
                "difficulty": 6,
            },
            {
                "item_type": "multiple_choice",
                "stem": "RAG 시스템에서 검색 정확도를 높이는 방법은?",
                "choices": [
                    "A: 벡터 데이터베이스 크기 증가",
                    "B: 문서 청킹(Chunking)과 메타데이터 활용",
                    "C: 네트워크 속도 증가",
                    "D: 더 큰 LLM 모델 사용",
                ],
                "answer_schema": {
                    "correct_key": "B",
                    "explanation": "효과적인 문서 청킹과 메타데이터 활용으로 검색 정확도를 크게 향상시킬 수 있습니다.",
                },
                "difficulty": 7,
            },
        ],
        "Robotics": [
            {
                "item_type": "multiple_choice",
                "stem": "로봇 자동화의 첫 번째 단계는?",
                "choices": [
                    "A: 즉시 완전 자동화 도입",
                    "B: 현재 프로세스 분석 및 개선점 파악",
                    "C: 최신 로봇 기술 구매",
                    "D: 작업자 재교육",
                ],
                "answer_schema": {
                    "correct_key": "B",
                    "explanation": "로봇 자동화는 현재 프로세스를 깊이 있게 분석하고 개선점을 파악한 후 진행되어야 합니다.",  # noqa: E501
                },
                "difficulty": 4,
            },
            {
                "item_type": "true_false",
                "stem": "로봇은 모든 종류의 작업을 인간보다 더 잘 수행할 수 있다.",
                "answer_schema": {
                    "correct_key": "false",
                    "explanation": "로봇은 반복적이고 정해진 작업에서 우수하지만, 창의성과 적응력이 필요한 작업에서는 인간이 더 효과적입니다.",  # noqa: E501
                },
                "difficulty": 3,
            },
            {
                "item_type": "short_answer",
                "stem": "로봇공학에서 사용되는 주요 센서 3가지를 나열하시오.",
                "answer_schema": {
                    "keywords": ["카메라", "라이더", "가속도계", "자이로스코프", "근접 센서"],
                    "explanation": "로봇은 시각(카메라), 거리 측정(라이더), 움직임 감지(가속도계/자이로스코프) 등 다양한 센서를 사용합니다.",  # noqa: E501
                },
                "difficulty": 5,
            },
            {
                "item_type": "multiple_choice",
                "stem": "협동 로봇(Cobot)의 주요 특징은?",
                "choices": [
                    "A: 매우 빠른 작동 속도",
                    "B: 인간과 함께 작업할 수 있는 안전 기능",
                    "C: 매우 복잡한 제어 시스템",
                    "D: 일회용 로봇",
                ],
                "answer_schema": {
                    "correct_key": "B",
                    "explanation": "협동 로봇은 인간 근처에서 안전하게 작업할 수 있도록 설계된 로봇입니다.",
                },
                "difficulty": 5,
            },
            {
                "item_type": "multiple_choice",
                "stem": "로봇 비전(Robot Vision) 시스템이 개선되면서 가능해진 응용 분야는?",
                "choices": [
                    "A: 음악 작곡만 가능",
                    "B: 정밀한 품질 검사, 부품 분류, 복잡한 조립 작업",
                    "C: 텍스트 읽기만 가능",
                    "D: 계산만 가능",
                ],
                "answer_schema": {
                    "correct_key": "B",
                    "explanation": "향상된 머신 비전 기술로 로봇이 복잡한 시각적 작업을 정확하게 수행할 수 있게 되었습니다.",  # noqa: E501
                },
                "difficulty": 6,
            },
        ],
    }

    def __init__(self, session: Session) -> None:
        """
        Initialize QuestionGenerationService with database session.

        Args:
            session: SQLAlchemy database session

        """
        self.session = session
        self.transformer_factory = TransformerFactory()

    def _normalize_answer_schema(self, raw_schema: dict[str, Any] | str | None, item_type: str) -> dict[str, Any]:
        """
        Normalize answer_schema from various formats to standard format.

        REQ: REQ-REFACTOR-SOLID-1

        Uses the Transformer pattern to convert various formats:
        - Agent: {"correct_keywords": [...], "explanation": "..."} → normalized via AgentResponseTransformer
        - Mock: {"correct_key": "...", "explanation": "..."} → normalized via MockDataTransformer

        The actual transformation is delegated to appropriate Transformer classes
        registered in TransformerFactory, enabling clean separation of concerns
        and extensibility without modifying this method.

        Args:
            raw_schema: Raw answer_schema from mock data or LLM agent
            item_type: Question type (multiple_choice, true_false, short_answer)

        Returns:
            Normalized answer_schema dict with type, keywords, correct_answer, explanation, source_format

        """
        # Handle null/None schema
        if raw_schema is None:
            return {
                "type": "keyword_match" if item_type == "short_answer" else "exact_match",
                "keywords": None,
                "correct_answer": None,
            }

        # Handle string schema (legacy format)
        if isinstance(raw_schema, str):
            return {"type": raw_schema, "keywords": None, "correct_answer": None}

        # Handle dict schema - delegate to appropriate Transformer via Factory
        if isinstance(raw_schema, dict):
            # If already transformed with source_format, return as-is
            if "source_format" in raw_schema:
                return raw_schema

            # If already normalized by agent output converter (has type, keywords, correct_answer)
            # and doesn't have the raw format keys, treat as already normalized
            if (
                "type" in raw_schema
                and ("keywords" in raw_schema or "correct_answer" in raw_schema)
                and "correct_keywords" not in raw_schema
                and "correct_key" not in raw_schema
            ):
                # Already normalized by agent output converter
                return raw_schema

            # Detect format and get appropriate transformer
            if "correct_keywords" in raw_schema:
                # Agent response format
                try:
                    transformer = self.transformer_factory.get_transformer("agent_response")
                    return transformer.transform(raw_schema)
                except ValidationError as e:
                    logger.error(f"Failed to transform agent response: {e}")
                    # Fallback to safe default
                    return {
                        "type": "keyword_match",
                        "keywords": raw_schema.get("correct_keywords", []),
                        "explanation": raw_schema.get("explanation", ""),
                        "source_format": "agent_response",
                    }

            elif "correct_key" in raw_schema:
                # Mock data format
                try:
                    transformer = self.transformer_factory.get_transformer("mock_data")
                    return transformer.transform(raw_schema)
                except ValidationError as e:
                    logger.error(f"Failed to transform mock data: {e}")
                    # Fallback to safe default
                    return {
                        "type": "exact_match",
                        "correct_answer": raw_schema.get("correct_key", ""),
                        "explanation": raw_schema.get("explanation", ""),
                        "source_format": "mock_data",
                    }

            elif "keywords" in raw_schema:
                # Already in keyword format
                return {
                    "type": "keyword_match",
                    "keywords": raw_schema.get("keywords"),
                    "explanation": raw_schema.get("explanation", ""),
                    "source_format": "standard",
                }

            else:
                # Unknown/legacy format - best effort
                return {
                    "type": raw_schema.get("type", raw_schema.get("answer_type", "exact_match")),
                    "keywords": raw_schema.get("keywords", raw_schema.get("correct_keywords")),
                    "correct_answer": raw_schema.get("correct_answer", raw_schema.get("correct_key")),
                    "explanation": raw_schema.get("explanation", ""),
                    "source_format": "legacy",
                }

        # Fallback
        return {"type": "exact_match", "keywords": None, "correct_answer": None}

    def _validate_answer_schema_before_save(self, normalized_schema: dict[str, Any], item_type: str) -> None:
        r"""
        Validate answer_schema before saving to database (fail-fast pattern).

        Ensures:
        - Required fields are present (type, keywords, correct_answer)
        - No null keywords for keyword_match type (indicates failed transformation)
        - Proper structure for the question type

        Args:
            normalized_schema: Normalized answer_schema dict
            item_type: Question type (multiple_choice, true_false, short_answer)

        Raises:
            ValueError: If validation fails

        """
        if not isinstance(normalized_schema, dict):
            raise ValueError(f"answer_schema must be dict, got {type(normalized_schema)}")

        if "type" not in normalized_schema:
            raise ValueError("answer_schema missing required field: type")

        schema_type = normalized_schema.get("type")

        # Validate keyword_match type has keywords
        if schema_type == "keyword_match":
            keywords = normalized_schema.get("keywords")
            if keywords is None or (isinstance(keywords, list) and len(keywords) == 0):
                raise ValueError(
                    f"answer_schema type={schema_type} requires non-empty keywords list. "
                    f"Got: {keywords}. This indicates Agent response transformation failed. "
                    f"Check if Agent sends 'correct_keywords' field."
                )

        # Validate exact_match type has correct_answer
        if schema_type == "exact_match":
            correct_answer = normalized_schema.get("correct_answer")
            if correct_answer is None or (isinstance(correct_answer, str) and len(correct_answer.strip()) == 0):
                raise ValueError(
                    f"answer_schema type={schema_type} requires non-empty correct_answer. Got: {correct_answer}"
                )

        logger.debug(
            f"✓ answer_schema validated: type={schema_type}, "
            f"item_type={item_type}, keywords_count={len(normalized_schema.get('keywords') or [])}"
        )

    async def generate_questions(
        self,
        user_id: int,
        survey_id: str,
        round_num: int = 1,
        question_count: int = 5,
        question_types: list[str] | None = None,
        domain: str = "AI",
    ) -> dict[str, Any]:
        """
        Generate questions using Real Agent (async) with automatic retry on failure.

        REQ: REQ-B-B2-Gen-1, REQ-B-B2-Gen-2, REQ-B-B2-Gen-3
        REQ: REQ-A-Agent-Backend-1 (Real Agent Integration)

        Workflow:
        1. Validate survey exists and retrieve context
        2. Create TestSession with in_progress status
        3. Retrieve previous round answers (for adaptive difficulty)
        4. Call Real Agent (ItemGenAgent) via GenerateQuestionsRequest with automatic retry
           - Max 3 attempts with exponential backoff (1s, 2s, 4s)
           - Retries on: no tool results extracted, agent execution failure
        5. Save generated items to DB as Question records
        6. Return backwards-compatible dict response

        Args:
            user_id: User ID
            survey_id: UserProfileSurvey ID to get interests
            round_num: Round number (1 or 2, default 1)
            question_count: Number of questions to generate (default 5, test 2)
            question_types: List of question types to generate (e.g., ["multiple_choice"])
            domain: Question domain/topic (e.g., "AI", "food", default "AI")

        Returns:
            Dictionary with:
                - session_id (str): TestSession UUID
                - questions (list): List of question dictionaries with all fields
                - attempt (int): Number of attempts made (metadata)

        Raises:
            Exception: If survey not found or max retries exceeded

        """
        # Auto-retry configuration
        max_retries = 3
        retry_delays = [1, 2, 4]  # Exponential backoff in seconds

        try:
            # Step 1: Validate survey and get context
            survey = self.session.query(UserProfileSurvey).filter_by(user_id=user_id, id=survey_id).first()
            if not survey:
                raise Exception(f"Survey with id {survey_id} not found for user {user_id}.")

            logger.debug(f"✓ Survey found: interests={survey.interests}")

            # Step 2: Create TestSession
            session_id = str(uuid4())
            test_session = TestSession(
                id=session_id,
                user_id=user_id,
                survey_id=survey_id,
                round=round_num,
                status="in_progress",
            )
            self.session.add(test_session)
            self.session.flush()  # Flush to ensure ID is set
            self.session.commit()
            logger.debug(f"✓ TestSession created: session_id={session_id}")

            # Verify session was created
            verify_session = self.session.query(TestSession).filter_by(id=session_id).first()
            if not verify_session:
                logger.error(f"❌ Failed to verify TestSession creation: {session_id}")
                raise Exception(f"TestSession creation failed: {session_id}")
            logger.debug("✓ Verified TestSession exists in database")

            # Step 3: Retrieve previous answers (for adaptive difficulty)
            prev_answers = None
            if round_num > 1:
                prev_answers = self._get_previous_answers(user_id, round_num - 1)
                logger.debug(f"✓ Previous answers retrieved: count={len(prev_answers) if prev_answers else 0}")

            # Step 4: Call Real Agent with automatic retry
            agent_response = None
            last_error = None

            for attempt in range(max_retries):
                try:
                    logger.debug(f"Question generation attempt {attempt + 1}/{max_retries}")

                    agent = await create_agent()
                    logger.debug("✓ Agent created successfully")

                    agent_request = GenerateQuestionsRequest(
                        session_id=session_id,
                        survey_id=survey_id,
                        round_idx=round_num,
                        prev_answers=prev_answers,
                        question_count=question_count,
                        question_types=question_types,
                        domain=domain,
                    )
                    logger.debug(f"✓ GenerateQuestionsRequest created: session_id={session_id}, count={question_count}")

                    agent_response = await agent.generate_questions(agent_request)
                    logger.debug(
                        f"Agent response received: {len(agent_response.items)} items, tokens={agent_response.total_tokens}"
                    )

                    # Check if agent generated any questions
                    if agent_response.items:
                        logger.debug(
                            f"✓ Agent generated {len(agent_response.items)} questions on attempt {attempt + 1}"
                        )
                        break  # Success, exit retry loop
                    else:
                        # No tool results extracted, retry
                        last_error = f"No tool results extracted (attempt {attempt + 1}/{max_retries})"
                        if attempt < max_retries - 1:
                            logger.warning(
                                f"⚠️  Attempt {attempt + 1}: No results. Retrying in {retry_delays[attempt]}s..."
                            )
                            await asyncio.sleep(retry_delays[attempt])
                            continue
                        else:
                            logger.error(f"❌ Final attempt {attempt + 1}: No results after {max_retries} attempts")
                            raise Exception(last_error)

                except Exception as e:
                    last_error = str(e)
                    if attempt == max_retries - 1:
                        logger.error(f"❌ Final attempt {attempt + 1} failed: {e}")
                        raise
                    logger.warning(f"⚠️  Attempt {attempt + 1} failed: {e}. Retrying in {retry_delays[attempt]}s...")
                    await asyncio.sleep(retry_delays[attempt])

            # Step 5: Save generated items to DB
            questions_list = []
            if agent_response and agent_response.items:
                # Limit items to requested question_count (safety filter)
                items_to_save = agent_response.items[:question_count]
                logger.debug(
                    f"Agent returned {len(agent_response.items)} items, limiting to {question_count} as requested"
                )
                for item in items_to_save:
                    # Handle both Pydantic model and dict for answer_schema
                    answer_schema_value = (
                        item.answer_schema.model_dump()
                        if hasattr(item.answer_schema, "model_dump")
                        else item.answer_schema
                    )
                    # Normalize answer_schema to standard format (fixes agent response format)
                    # Type: answer_schema_value is dict[str, Any] after model_dump() call
                    normalized_schema = self._normalize_answer_schema(
                        answer_schema_value,  # type: ignore[arg-type]
                        item.type,
                    )

                    # Validate answer_schema before saving (fail-fast pattern)
                    self._validate_answer_schema_before_save(normalized_schema, item.type)

                    question = Question(
                        id=item.id,
                        session_id=session_id,
                        item_type=item.type,
                        stem=item.stem,
                        choices=item.choices,
                        answer_schema=normalized_schema,
                        difficulty=item.difficulty,
                        category=item.category,
                        round=round_num,
                    )
                    self.session.add(question)
                    questions_list.append(question)
                    logger.debug(f"Saved question: id={item.id}, type={item.type}")

                self.session.commit()

            # Step 6: Format and return response (backwards compatible dict format)
            response = {
                "session_id": session_id,
                "questions": [
                    {
                        "id": q.id,
                        "item_type": q.item_type,
                        "stem": q.stem,
                        "choices": q.choices,
                        "answer_schema": q.answer_schema,
                        "difficulty": q.difficulty,
                        "category": q.category,
                    }
                    for q in questions_list
                ],
                "attempt": attempt + 1,  # Include attempt count in response
            }
            logger.info(
                f"✅ Generated {len(questions_list)} questions "
                f"(tokens: {agent_response.total_tokens if agent_response else 0}, attempt: {attempt + 1}/{max_retries})"
            )
            return response

        except Exception as e:
            logger.error(f"❌ Question generation failed after {max_retries} attempts: {e}")
            # Return error response with empty questions (graceful degradation)
            return {
                "session_id": f"error_{uuid4().hex[:8]}",
                "questions": [],
                "error": str(e),
                "attempt": max_retries,
            }

    def _get_previous_answers(self, user_id: int, round_num: int) -> list[dict[str, Any]] | None:
        """
        Retrieve previous round answers for adaptive difficulty.

        REQ: REQ-A-Agent-Backend-1 (Context for Agent)

        Args:
            user_id: User ID
            round_num: Round number to retrieve answers from

        Returns:
            List of previous answers dict or None if not found

        """
        try:
            # Get the latest TestResult for the round
            test_result = (
                self.session.query(TestResult)
                .join(TestSession, TestSession.id == TestResult.session_id)
                .filter(TestSession.user_id == user_id, TestResult.round == round_num)
                .order_by(TestResult.created_at.desc())
                .first()
            )

            if not test_result:
                logger.debug(f"No previous answers found for round {round_num}")
                return None

            # Get questions and answers from the previous session
            prev_session = self.session.query(TestSession).filter_by(id=test_result.session_id).first()
            if not prev_session:
                return None

            prev_questions = self.session.query(Question).filter_by(session_id=prev_session.id).all()
            if not prev_questions:
                return None

            # Build prev_answers list from session data
            # This will be used by Agent for context
            prev_answers = [
                {
                    "question_id": q.id,
                    "category": q.category,
                    "difficulty": q.difficulty,
                    "item_type": q.item_type,
                }
                for q in prev_questions
            ]

            logger.debug(f"✓ Retrieved {len(prev_answers)} previous answers for adaptive context")
            return prev_answers

        except Exception as e:
            logger.warning(f"Failed to retrieve previous answers: {e}")
            return None

    async def generate_questions_adaptive(
        self,
        user_id: int,
        session_id: str,
        round_num: int = 2,
        question_count: int = 5,
    ) -> dict[str, Any]:
        """
        Generate Round 2+ questions with adaptive difficulty using Real Agent.

        REQ: REQ-B-B2-Adapt-1, REQ-B-B2-Adapt-2, REQ-B-B2-Adapt-3

        Analyzes previous round results and generates questions with:
        - Real Agent LLM-based generation
        - Adjusted difficulty based on score
        - Prioritized weak categories (≥50%)

        Args:
            user_id: User ID
            session_id: Previous TestSession ID (Round N-1)
            round_num: Target round number (2, 3, etc.)
            question_count: Number of questions to generate (default 5, supports --count parameter)

        Returns:
            Dictionary with:
                - session_id (str): New TestSession UUID for this round
                - questions (list): List of adaptive questions (count as requested)
                - adaptive_params (dict): Difficulty tier, weak categories

        Raises:
            ValueError: If previous round results not found

        """
        # Get previous round result
        prev_round = round_num - 1
        prev_result = (
            self.session.query(TestResult)
            .join(TestSession, TestSession.id == TestResult.session_id)
            .filter(TestSession.user_id == user_id, TestResult.round == prev_round)
            .order_by(TestResult.created_at.desc())
            .first()
        )

        if not prev_result:
            raise ValueError(
                f"Round {prev_round} results not found for user {user_id}. "
                "Cannot generate adaptive Round {round_num}."
            )

        # Get adaptive difficulty parameters
        adaptive_service = AdaptiveDifficultyService(self.session)
        params = adaptive_service.get_adaptive_generation_params(prev_result.session_id)

        # Get the survey_id from the previous session
        prev_session = self.session.query(TestSession).filter_by(id=prev_result.session_id).first()
        if not prev_session:
            raise ValueError(f"Previous TestSession {prev_result.session_id} not found")

        # Create new test session for this round
        new_session_id = str(uuid4())
        test_session = TestSession(
            id=new_session_id,
            user_id=user_id,
            survey_id=prev_session.survey_id,
            round=round_num,
            status="in_progress",
        )
        self.session.add(test_session)
        self.session.commit()

        # Get weak categories from adaptive parameters
        priority_ratio = params["priority_ratio"]
        adjusted_difficulty = params["adjusted_difficulty"]

        # Extract domain/category from priority_ratio (weak categories)
        weak_categories = list(priority_ratio.keys()) if priority_ratio else []
        domain = weak_categories[0] if weak_categories else "AI"

        logger.debug(
            f"Adaptive Round {round_num}: "
            f"difficulty={adjusted_difficulty}, "
            f"weak_categories={weak_categories}, "
            f"count={question_count}"
        )

        # Retrieve previous answers for adaptive context
        prev_answers = self._get_previous_answers(user_id, prev_round)
        logger.debug(f"Previous answers for adaptive context: {len(prev_answers) if prev_answers else 0}")

        # Call Real Agent with adaptive parameters
        # Note: adjusted_difficulty is a float (e.g., 3.5), we pass it as-is
        agent = await create_agent()
        agent_request = GenerateQuestionsRequest(
            session_id=new_session_id,
            survey_id=prev_session.survey_id,
            round_idx=round_num,
            prev_answers=prev_answers,
            question_count=question_count,
            question_types=None,  # Let agent choose
            domain=domain,
        )
        logger.debug(f"✓ Created adaptive GenerateQuestionsRequest for {domain}, count={question_count}")

        agent_response = await agent.generate_questions(agent_request)
        logger.debug(f"Agent response: {len(agent_response.items) if agent_response.items else 0} items")

        # Save generated items to DB
        questions_list = []
        if agent_response and agent_response.items:
            items_to_save = agent_response.items[:question_count]
            for item in items_to_save:
                # Handle both Pydantic model and dict for answer_schema
                answer_schema_value = (
                    item.answer_schema.model_dump() if hasattr(item.answer_schema, "model_dump") else item.answer_schema
                )

                question = Question(
                    id=str(uuid4()),
                    session_id=new_session_id,
                    item_type=item.type,
                    stem=item.stem,
                    choices=item.choices,
                    answer_schema=answer_schema_value,
                    difficulty=item.difficulty,
                    category=item.category,
                    round=round_num,
                )
                self.session.add(question)
                questions_list.append(question)

        self.session.commit()
        logger.debug(f"✓ Saved {len(questions_list)} adaptive questions to DB")

        # Format response (backward compatible with existing clients)
        return {
            "session_id": new_session_id,
            "questions": [
                {
                    "id": q.id,
                    "item_type": q.item_type,
                    "stem": q.stem,
                    "choices": q.choices,
                    "answer_schema": q.answer_schema,
                    "difficulty": q.difficulty,
                    "category": q.category,
                }
                for q in questions_list
            ],
            "adaptive_params": params,
        }
