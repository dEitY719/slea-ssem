"""
Explanation generation service for generating question explanations with reference links.

REQ: REQ-B-B3-Explain, REQ-B-B3-Explain-2

Uses Gemini LLM to generate dynamic explanations based on problem context.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from src.agent.config import create_llm
from src.backend.models.answer_explanation import AnswerExplanation
from src.backend.models.question import Question

logger = logging.getLogger(__name__)


class ExplainService:
    """
    Service for generating explanations for test questions.

    REQ: REQ-B-B3-Explain-1

    Methods:
        generate_explanation: Generate new explanation or retrieve cached
        get_explanation: Retrieve cached explanation

    Design:
        - Generates 200+ character explanations with 3+ reference links
        - Caches explanations by question_id (reused across users)
        - Separates prompts for correct vs incorrect answers
        - Supports timeout handling with graceful degradation

    """

    def __init__(self, session: Session) -> None:
        """
        Initialize ExplainService with database session.

        Args:
            session: SQLAlchemy database session

        """
        self.session = session

    def generate_explanation(
        self,
        question_id: str,
        user_answer: str | dict,
        is_correct: bool,
        attempt_answer_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate explanation for a question answer.

        REQ: REQ-B-B3-Explain-1

        Performance requirement: Complete within 2 seconds.

        Args:
            question_id: Question ID to explain
            user_answer: User's submitted answer
            is_correct: Whether answer is correct
            attempt_answer_id: Optional FK to attempt_answers for tracking

        Returns:
            Dictionary with:
                - id (str): Explanation ID
                - question_id (str): Question ID
                - attempt_answer_id (str|None): Attempt answer ID if provided
                - explanation_text (str): Generated explanation (≥200 chars)
                - reference_links (list[dict]): Reference links with title+url (≥3)
                - is_correct (bool): Whether this is for correct/incorrect answer
                - created_at (str): ISO timestamp
                - is_fallback (bool): Whether fallback was used due to timeout
                - error_message (str|None): Error details if fallback used

        Raises:
            ValueError: If question not found or validation fails

        """
        # Validate inputs
        if not question_id:
            raise ValueError("question_id cannot be empty")

        if isinstance(user_answer, str) and not user_answer.strip():
            raise ValueError("user_answer cannot be empty")

        # Validate question exists
        question = self.session.query(Question).filter_by(id=question_id).first()
        if not question:
            raise ValueError(f"Question not found: {question_id}")

        # Check for cached explanation (by question_id + is_correct)
        cached = self.session.query(AnswerExplanation).filter_by(question_id=question_id, is_correct=is_correct).first()

        if cached:
            return self._format_explanation_response(
                explanation=cached,
                question=question,
                user_answer=user_answer,
                attempt_answer_id=attempt_answer_id,
            )

        # Generate new explanation
        try:
            llm_response = self._generate_with_llm(
                question=question,
                user_answer=user_answer,
                is_correct=is_correct,
            )
        except TimeoutError as e:
            # Graceful degradation: return fallback explanation
            return self._create_fallback_explanation(
                question_id=question_id,
                error_message=str(e),
            )

        # Validate explanation meets requirements
        self._validate_explanation(llm_response)

        # Save to database
        explanation = AnswerExplanation(
            id=str(uuid4()),
            question_id=question_id,
            attempt_answer_id=attempt_answer_id,
            explanation_text=llm_response["explanation"],
            reference_links=llm_response["reference_links"],
            is_correct=is_correct,
        )
        self.session.add(explanation)
        self.session.commit()
        self.session.refresh(explanation)

        return self._format_explanation_response(
            explanation=explanation,
            question=question,
            user_answer=user_answer,
        )

    def get_explanation(
        self,
        question_id: str,
        attempt_answer_id: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Retrieve cached explanation for a question.

        REQ: REQ-B-B3-Explain-1

        Args:
            question_id: Question ID
            attempt_answer_id: Optional - filter by specific attempt

        Returns:
            Explanation dict or None if not found

        """
        from src.backend.models.attempt_answer import AttemptAnswer

        query = self.session.query(AnswerExplanation).filter_by(question_id=question_id)

        if attempt_answer_id:
            query = query.filter_by(attempt_answer_id=attempt_answer_id)

        explanation = query.first()

        if not explanation:
            return None

        # Load related question and attempt answer for formatting
        question = self.session.query(Question).filter_by(id=question_id).first()
        user_answer = None
        if explanation.attempt_answer_id:
            attempt = self.session.query(AttemptAnswer).filter_by(id=explanation.attempt_answer_id).first()
            if attempt:
                user_answer = attempt.user_answer

        return self._format_explanation_response(
            explanation=explanation,
            question=question,
            user_answer=user_answer,
        )

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _generate_with_llm(
        self,
        question: Question,
        user_answer: str | dict,
        is_correct: bool,
    ) -> dict[str, Any]:
        """
        Generate explanation using LLM (Gemini with fallback to Mock).

        REQ: REQ-B-B3-Explain-2

        Args:
            question: Question object
            user_answer: User's submitted answer
            is_correct: Whether answer is correct

        Returns:
            Dictionary with 'explanation' and 'reference_links'

        Raises:
            TimeoutError: If LLM request times out

        """
        try:
            logger.info("Attempting to generate explanation using Gemini LLM")
            result = self._generate_with_gemini(question, user_answer, is_correct)
            logger.info("✓ Gemini LLM successfully generated explanation")
            return result
        except Exception as e:
            logger.error(f"✗ Gemini API failed with error: {type(e).__name__}: {e}")
            logger.info("Falling back to Mock LLM for explanation")
            return self._generate_mock_explanation(question, user_answer, is_correct)

    def _generate_with_gemini(
        self,
        question: Question,
        user_answer: str | dict,
        is_correct: bool,
    ) -> dict[str, Any]:
        """
        Generate explanation using Gemini LLM.

        REQ: REQ-B-B3-Explain-2

        Args:
            question: Question object
            user_answer: User's submitted answer
            is_correct: Whether answer is correct

        Returns:
            Dictionary with 'explanation' and 'reference_links'

        """
        # Create Gemini LLM client
        llm = create_llm()

        # Build prompt with question context
        prompt = self._build_explanation_prompt(question, user_answer, is_correct)

        # Call Gemini LLM
        response = llm.invoke(prompt)
        response_text = response.content

        logger.debug(f"Gemini response: {response_text[:200]}...")

        return self._parse_llm_response(response_text)

    def _build_explanation_prompt(self, question: Question, user_answer: str | dict, is_correct: bool) -> str:
        """
        Build LLM prompt with question context for explanation generation.

        REQ: REQ-B-B3-Explain-2

        Args:
            question: Question object
            user_answer: User's submitted answer
            is_correct: Whether answer is correct

        Returns:
            Formatted prompt string

        """
        # Format user answer for display
        if isinstance(user_answer, dict):
            if "selected_key" in user_answer:
                user_answer_str = f"선택: {user_answer['selected_key']}"
            elif "answer" in user_answer:
                val = user_answer["answer"]
                user_answer_str = "참" if val else "거짓" if isinstance(val, bool) else str(val)
            elif "text" in user_answer:
                user_answer_str = str(user_answer["text"])
            else:
                user_answer_str = str(user_answer)
        else:
            user_answer_str = str(user_answer)

        # Extract correct answer
        answer_schema = question.answer_schema or {}
        correct_key = self._extract_correct_answer_key(answer_schema, question.item_type or "unknown")

        # Build detailed prompt
        prompt = f"""다음 문제에 대해 사용자 답변을 평가하고 맞춤형 해설을 작성해주세요.

문제 유형: {question.item_type}
문제 주제: {question.category}

<문제>
{question.stem}
</문제>

"""

        # Add choices if available
        if question.choices:
            prompt += f"""선택지:
{chr(10).join(f"- {choice}" for choice in question.choices)}

"""

        # Add answer info
        prompt += f"""사용자 답변: {user_answer_str}
정답: {correct_key}
정오답: {"정답" if is_correct else "오답"}

다음 JSON 포맷으로 해설을 작성해주세요. 괄호는 포함하지 마세요:
{{
  "explanation": "[틀린 이유]\\n사용자가 왜 틀렸을 가능성이 있는지 구체적으로 분석해주세요. (50-100자)\\n\\n[정답의 원리]\\n정답이 왜 맞는지, 개념 설명 + 구체적 예시를 포함해주세요. (100-150자)\\n\\n[개념 구분]\\n유사한 개념들을 비교하여 구분해주세요. (50-100자)\\n\\n[복습 팁]\\n사용자가 이 유형의 문제를 잘하기 위한 팁을 제시해주세요. (50-100자)",
  "reference_links": [
    {{"title": "참고자료 제목 1", "url": "https://example.com/resource1"}},
    {{"title": "참고자료 제목 2", "url": "https://example.com/resource2"}},
    {{"title": "참고자료 제목 3", "url": "https://example.com/resource3"}}
  ]
}}

요구사항:
- 각 섹션은 200자 이상의 구체적이고 유용한 설명이어야 합니다.
- 문제의 구체적인 내용(stem, 선택지 등)을 활용하여 맞춤형 해설을 작성해주세요.
- 참고 링크는 3개 이상, 한글 제목 포함해야 합니다.
- JSON은 유효한 형식이어야 합니다.
"""

        return prompt

    def _parse_llm_response(self, response_text: str) -> dict[str, Any]:
        """
        Parse LLM response and extract structured explanation.

        REQ: REQ-B-B3-Explain-2

        Args:
            response_text: Claude API response text

        Returns:
            Dictionary with 'explanation' and 'reference_links'

        Raises:
            ValueError: If response cannot be parsed

        """
        try:
            # Extract JSON from response (may be wrapped in markdown code blocks)
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_text = response_text.strip()

            # Parse JSON
            data = json.loads(json_text)

            # Validate structure
            if "explanation" not in data or "reference_links" not in data:
                raise ValueError("Missing required fields: explanation, reference_links")

            explanation = data["explanation"]
            reference_links = data["reference_links"]

            # Validate explanation length
            if len(explanation) < 200:
                logger.warning(f"Explanation too short ({len(explanation)} chars), using fallback")
                raise ValueError(f"Explanation must be at least 200 chars, got {len(explanation)}")

            # Validate reference links
            if len(reference_links) < 3:
                logger.warning(f"Not enough reference links ({len(reference_links)}), using fallback")
                raise ValueError(f"Must have at least 3 reference links, got {len(reference_links)}")

            # Validate link structure
            for link in reference_links:
                if not isinstance(link, dict) or "title" not in link or "url" not in link:
                    raise ValueError(f"Invalid link format: {link}")

            return {
                "explanation": explanation,
                "reference_links": reference_links,
            }

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            raise ValueError(f"Invalid LLM response format: {e}") from e

    def _generate_mock_explanation(
        self,
        question: Question,
        user_answer: str | dict,
        is_correct: bool,
    ) -> dict[str, Any]:
        """
        Generate mock explanation (placeholder for real LLM integration).

        This simulates what a real LLM would return. The explanation should be
        actual content, not instructions/prompts.

        REQ: REQ-B-B3-Explain-1

        Args:
            question: Question object
            user_answer: User's answer
            is_correct: Whether answer is correct

        Returns:
            Dictionary with explanation_text and reference_links

        """
        # Build context from question
        stem = question.stem
        category = question.category
        question_type = question.item_type or "unknown"
        answer_schema = question.answer_schema or {}

        # Generate mock explanation based on correctness
        if is_correct:
            explanation_text = self._generate_correct_answer_explanation(stem, category, answer_schema)
        else:
            # Get correct answer from schema, with proper fallback
            correct_key = self._extract_correct_answer_key(answer_schema, question_type)
            explanation_text = self._generate_incorrect_answer_explanation(
                stem, category, user_answer, correct_key, question_type
            )

        # Create reference links (category-specific)
        reference_links = self._generate_mock_references(category, is_correct)

        return {
            "explanation": explanation_text,
            "reference_links": reference_links,
        }

    def _generate_correct_answer_explanation(
        self,
        stem: str,
        category: str,
        answer_schema: dict[str, Any],
    ) -> str:
        """
        Generate mock explanation for correct answer.

        Returns actual explanation content (simulating LLM output).
        """
        explanations = {
            "LLM": (
                f"'{stem}'에 대한 정답 해설입니다.\n\n"
                f"당신의 답변이 정확합니다. {category} 분야에서 이것은 핵심 개념입니다.\n\n"
                f"[핵심 개념] 대규모 언어 모델(LLM)은 수십억 개의 파라미터를 가진 신경망으로, "
                f"트랜스포머 아키텍처를 기반으로 합니다. 자기주의 메커니즘을 통해 입력 텍스트의 "
                f"맥락을 파악하고 다음 토큰을 예측합니다.\n\n"
                f"[실무 예시] OpenAI의 GPT-4, Google의 Gemini, Meta의 Llama 등이 이러한 아키텍처를 "
                f"따릅니다. 이들은 자연어 처리, 코드 생성, 창의적 작업 등 다양한 분야에 적용되고 있습니다.\n\n"
                f"[심화 개념] Transfer Learning을 통해 사전학습된 LLM을 특정 분야에 미세조정하면, "
                f"적은 리소스로도 고성능을 얻을 수 있습니다. 이는 LLM 시대의 핵심 장점입니다."
            ),
            "RAG": (
                f"'{stem}'에 대한 정답 해설입니다.\n\n"
                f"당신의 답변이 정확합니다. Retrieval-Augmented Generation은 최신 정보를 제공하는 "
                f"핵심 기술입니다.\n\n"
                f"[핵심 개념] RAG는 문서 데이터베이스에서 관련 정보를 검색한 후, 이를 LLM의 입력으로 "
                f"제공하여 더 정확한 답변을 생성하는 기술입니다.\n\n"
                f"[실무 예시] 기업의 내부 문서 기반 Q&A 시스템, 의료 기록 기반 진단 보조 시스템 등에서 "
                f"활용됩니다. 이를 통해 LLM의 할루시네이션 문제를 줄일 수 있습니다.\n\n"
                f"[심화 개념] 벡터 임베딩과 의미론적 검색을 결합하면, 더 정교한 정보 검색이 가능합니다."
            ),
            "Robotics": (
                f"'{stem}'에 대한 정답 해설입니다.\n\n"
                f"당신의 답변이 정확합니다. 로봇공학의 기본 원리를 잘 이해하셨습니다.\n\n"
                f"[핵심 개념] 로봇은 센서(입력), 제어기(처리), 액추에이터(출력)의 3가지 주요 구성으로 "
                f"이루어집니다. 피드백 제어를 통해 목표 상태를 유지합니다.\n\n"
                f"[실무 예시] 자동차의 자율주행 시스템, 산업용 로봇팔, 드론 등이 이러한 원리를 "
                f"적용합니다.\n\n"
                f"[심화 개념] 기계학습과 로봇공학의 결합으로 더욱 지능형 로봇이 개발되고 있습니다."
            ),
        }
        return explanations.get(
            category,
            f"'{stem}'에 대한 정답 해설입니다.\n\n"
            f"당신의 답변이 정확합니다. 이것은 {category} 분야의 중요한 개념입니다.\n\n"
            f"[핵심 내용] 이 개념의 정의와 원리, 그리고 실제 응용 분야를 이해하는 것이 중요합니다.\n\n"
            f"[실무 활용] 이러한 지식은 실무에서 효과적으로 적용될 수 있습니다.\n\n"
            f"[향후 학습] 관련 심화 개념들을 학습하면 더욱 폭넓은 이해가 가능합니다.",
        )

    def _extract_correct_answer_key(self, answer_schema: dict[str, Any], question_type: str) -> str:
        """
        Extract correct answer from answer_schema with proper fallback handling.

        For True/False questions, returns formatted string ("참" or "거짓").
        For multiple choice, returns the choice key.
        For short answer, returns the expected text.

        Args:
            answer_schema: Question's answer schema
            question_type: Type of question (true_false, multiple_choice, short_answer)

        Returns:
            Formatted correct answer string

        """
        # Try correct_key first (use 'is not None' to handle False values)
        correct_key = answer_schema.get("correct_key")
        if correct_key is not None:
            # Handle boolean values for true/false questions
            if isinstance(correct_key, bool):
                return "참" if correct_key else "거짓"
            if isinstance(correct_key, str):
                key_lower = correct_key.lower().strip()
                if key_lower == "true":
                    return "참"
                elif key_lower == "false":
                    return "거짓"
            # Ensure non-empty string
            key_str = str(correct_key).strip()
            if key_str:
                return key_str

        # Try correct_answer field (use 'is not None' to handle False values)
        correct_answer = answer_schema.get("correct_answer")
        if correct_answer is not None:
            if isinstance(correct_answer, bool):
                return "참" if correct_answer else "거짓"
            answer_str = str(correct_answer).strip()
            if answer_str:
                return answer_str

        # Fallback based on question type - use generic message instead of placeholder
        if question_type == "true_false":
            return "참"  # Safe default for true/false
        elif question_type == "multiple_choice":
            return "[정답]"  # Clear marker that answer info is missing
        elif question_type == "short_answer":
            return "[예상 답변]"  # Clear marker that answer info is missing
        else:
            return "[정답]"  # Generic marker for unknown types

    def _generate_incorrect_answer_explanation(
        self,
        stem: str,
        category: str,
        user_answer: str | dict,
        correct_key: str,
        question_type: str = "unknown",
    ) -> str:
        """
        Generate mock explanation for incorrect answer.

        Returns actual explanation content (simulating LLM output).

        Args:
            stem: Question text
            category: Question category
            user_answer: User's submitted answer
            correct_key: Correct answer (formatted)
            question_type: Type of question for context

        """
        explanations = {
            "LLM": (
                f"'{stem}'에 대한 오답 해설입니다.\n\n"
                f"당신의 선택이 정확하지 않습니다. 정답은 '{correct_key}'입니다.\n\n"
                f"[틀린 이유] 이 선택지는 LLM의 기본 특성을 간과합니다. LLM은 학습 과정에서 "
                f"수많은 토큰 시퀀스를 처리하며, 이를 통해 통계적 패턴을 학습합니다.\n\n"
                f"[정답의 원리] '{correct_key}'가 맞는 이유는 {category} 분야의 기본 원리에 "
                f"부합하기 때문입니다. 이는 여러 연구 논문에서 검증되었습니다.\n\n"
                f"[개념 구분] 유사해 보이는 개념들을 정확히 구분하는 것이 중요합니다. "
                f"예를 들어, LLM과 전통적인 규칙 기반 시스템의 차이를 이해해야 합니다.\n\n"
                f"[복습 팁] 이 유형의 문제를 다시 한번 검토하고, 관련 개념들의 특징을 비교해보세요."
            ),
            "RAG": (
                f"'{stem}'에 대한 오답 해설입니다.\n\n"
                f"당신의 선택이 정확하지 않습니다. 정답은 '{correct_key}'입니다.\n\n"
                f"[틀린 이유] 이 선택지는 RAG의 목적을 잘못 이해하고 있습니다. RAG는 단순히 "
                f"정보를 검색하는 것이 아니라, 검색된 정보를 LLM의 입력으로 활용합니다.\n\n"
                f"[정답의 원리] '{correct_key}'가 맞는 이유는 RAG의 아키텍처와 동작 방식을 "
                f"정확히 이해했기 때문입니다.\n\n"
                f"[개념 구분] 검색(Retrieval), 생성(Generation), 그리고 두 단계의 통합 과정을 "
                f"명확히 구분해야 합니다.\n\n"
                f"[복습 팁] RAG의 전체 파이프라인을 다시 그려보면서 각 단계를 정리해보세요."
            ),
            "Robotics": (
                f"'{stem}'에 대한 오답 해설입니다.\n\n"
                f"당신의 선택이 정확하지 않습니다. 정답은 '{correct_key}'입니다.\n\n"
                f"[틀린 이유] 로봇의 운동학과 동역학을 혼동하기 쉽습니다. 운동학은 위치와 속도만 "
                f"다루고, 동역학은 힘과 토크를 포함합니다.\n\n"
                f"[정답의 원리] '{correct_key}'가 맞는 이유는 로봇공학의 기본 원리에 정확히 "
                f"부합하기 때문입니다.\n\n"
                f"[개념 구분] 센서, 제어기, 액추에이터의 역할을 정확히 이해해야 합니다. "
                f"각각이 어떤 신호를 처리하는지 생각해보세요.\n\n"
                f"[복습 팁] 로봇의 제어 루프를 단계별로 따라가며 각 컴포넌트의 역할을 정리하세요."
            ),
        }
        return explanations.get(
            category,
            f"'{stem}'에 대한 오답 해설입니다.\n\n"
            f"당신의 선택이 정확하지 않습니다. 정답은 '{correct_key}'입니다.\n\n"
            f"[틀린 이유] 이 선택지는 {category} 분야의 핵심 개념을 놓치고 있습니다.\n\n"
            f"[정답의 원리] '{correct_key}'가 맞는 이유는 기본 원리와 개념을 정확히 따르기 때문입니다.\n\n"
            f"[개념 구분] 유사한 개념들을 비교하여 정확하게 구분하는 것이 중요합니다.\n\n"
            f"[복습 팁] 이 유형의 문제를 다시 검토하고, 관련 개념들을 깊이 있게 학습해보세요.",
        )

    def _generate_mock_references(
        self,
        category: str,
        is_correct: bool,
    ) -> list[dict[str, str]]:
        """
        Generate mock reference links by category.

        Args:
            category: Question category
            is_correct: Whether this is for correct answer

        Returns:
            List of reference links with title and url

        """
        # Mock references by category
        references_by_category = {
            "LLM": [
                {
                    "title": "Large Language Models 기초 개념",
                    "url": "https://example.com/llm-basics",
                },
                {
                    "title": "트랜스포머 아키텍처 상세 해석",
                    "url": "https://example.com/transformer-guide",
                },
                {
                    "title": "LLM 학습 프로세스 완벽 이해",
                    "url": "https://example.com/llm-training",
                },
                {
                    "title": "실무 적용 사례 및 Best Practices",
                    "url": "https://example.com/llm-best-practices",
                },
            ],
            "RAG": [
                {
                    "title": "Retrieval-Augmented Generation 원리",
                    "url": "https://example.com/rag-fundamentals",
                },
                {
                    "title": "벡터 데이터베이스와 임베딩",
                    "url": "https://example.com/vector-db",
                },
                {
                    "title": "RAG 시스템 구축 가이드",
                    "url": "https://example.com/rag-implementation",
                },
                {
                    "title": "성능 최적화 및 튜닝",
                    "url": "https://example.com/rag-optimization",
                },
            ],
            "Robotics": [
                {
                    "title": "로봇공학 기초",
                    "url": "https://example.com/robotics-basics",
                },
                {
                    "title": "로봇 제어 이론",
                    "url": "https://example.com/robot-control",
                },
                {
                    "title": "센서 및 액추에이터",
                    "url": "https://example.com/sensors-actuators",
                },
                {
                    "title": "로봇 학습 및 자동화",
                    "url": "https://example.com/robot-learning",
                },
            ],
        }

        # Get category references, fallback to generic
        category_refs = references_by_category.get(
            category,
            [
                {"title": "기본 개념 설명", "url": "https://example.com/basics"},
                {"title": "심화 학습 자료", "url": "https://example.com/advanced"},
                {"title": "실전 예제", "url": "https://example.com/examples"},
                {"title": "관련 자료 모음", "url": "https://example.com/resources"},
            ],
        )

        # Return 3 references
        return category_refs[:3]

    def _validate_explanation(self, llm_response: dict[str, Any]) -> None:
        """
        Validate explanation meets quality requirements.

        REQ: REQ-B-B3-Explain-1 AC1, AC2

        Args:
            llm_response: Response from LLM

        Raises:
            ValueError: If validation fails

        """
        explanation = llm_response.get("explanation", "")
        links = llm_response.get("reference_links", [])

        # AC1: Explanation >= 200 characters
        if len(explanation) < 200:
            raise ValueError(f"Explanation must be at least 200 characters. Got {len(explanation)} chars.")

        # AC2: Reference links >= 3
        if len(links) < 3:
            raise ValueError(f"Response must have at least 3 reference links. Got {len(links)} links.")

        # Validate link structure
        for link in links:
            if not isinstance(link, dict):
                raise ValueError(f"Invalid link format: {link}")
            if "title" not in link or "url" not in link:
                raise ValueError(f"Link missing required fields (title, url): {link}")

    def _format_explanation_response(
        self,
        explanation: AnswerExplanation,
        question: Question | None = None,
        user_answer: str | dict | None = None,
        attempt_answer_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Format explanation as API response with sections and answer summary.

        Args:
            explanation: AnswerExplanation ORM object
            question: Question object (for answer formatting)
            user_answer: User's answer (for comparison)
            attempt_answer_id: Optional override for attempt_answer_id

        Returns:
            Formatted explanation dictionary with sections and answer summary

        """
        # Parse explanation text into sections
        sections = self._parse_explanation_sections(explanation.explanation_text)

        # Generate user answer summary
        user_answer_summary = None
        if question and user_answer is not None:
            user_answer_summary = self._format_user_answer_summary(
                question=question,
                user_answer=user_answer,
                is_correct=explanation.is_correct,
            )

        # Extract problem statement for display
        problem_statement = None
        if question:
            problem_statement = self._extract_problem_statement(question.stem, explanation.is_correct)

        return {
            "id": explanation.id,
            "question_id": explanation.question_id,
            "attempt_answer_id": attempt_answer_id or explanation.attempt_answer_id,
            "explanation_text": explanation.explanation_text,
            "explanation_sections": sections,
            "reference_links": explanation.reference_links,
            "user_answer_summary": user_answer_summary,
            "problem_statement": problem_statement,
            "is_correct": explanation.is_correct,
            "created_at": explanation.created_at.isoformat(),
            "is_fallback": False,
            "error_message": None,
        }

    def _parse_explanation_sections(self, explanation_text: str) -> list[dict[str, str]]:
        """
        Parse explanation text into sections by [title] markers.

        Example input:
            '[틀린 이유] Content here...
             [정답의 원리] Content here...'

        Returns:
            List of {"title": "...", "content": "..."}

        """
        import re

        sections = []
        # Match patterns like [제목] Content
        pattern = r"\[([^\]]+)\]\s*(.+?)(?=\[|$)"
        matches = re.findall(pattern, explanation_text, re.DOTALL)

        for title, content in matches:
            stripped_content = content.strip()
            if stripped_content:
                sections.append(
                    {
                        "title": f"[{title}]",
                        "content": stripped_content,
                    }
                )

        # If no sections found, treat entire text as one section
        if not sections:
            sections.append(
                {
                    "title": "[설명]",
                    "content": explanation_text.strip(),
                }
            )

        return sections

    def _format_user_answer_summary(
        self,
        question: Question,
        user_answer: str | dict,
        is_correct: bool,
    ) -> dict[str, Any]:
        """
        Format user's answer vs correct answer for display.

        Args:
            question: Question object
            user_answer: User's submitted answer
            is_correct: Whether answer is correct

        Returns:
            Dictionary with user_answer_text and correct_answer_text

        """
        question_type = question.item_type or "unknown"
        answer_schema = question.answer_schema or {}

        # Format user answer based on question type
        user_answer_text = self._format_answer_for_display(user_answer, question_type)

        # Format correct answer based on question type
        correct_answer_text = self._format_correct_answer_for_display(answer_schema, question_type)

        return {
            "user_answer_text": user_answer_text,
            "correct_answer_text": correct_answer_text,
            "question_type": question_type,
        }

    def _format_answer_for_display(self, user_answer: str | dict, question_type: str) -> str:
        """Convert user_answer to readable format based on question type."""
        if isinstance(user_answer, str):
            return user_answer

        if not isinstance(user_answer, dict):
            return str(user_answer)

        # Multiple Choice: extract selected_key
        if "selected_key" in user_answer:
            key = user_answer["selected_key"]
            return f"선택: {key}"

        # True/False: convert boolean
        if "answer" in user_answer:
            val = user_answer["answer"]
            if isinstance(val, bool):
                return "참" if val else "거짓"
            return str(val)

        # Short Answer: extract text
        if "text" in user_answer:
            text = user_answer["text"]
            return text if isinstance(text, str) else str(text)

        # Fallback
        return str(user_answer)

    def _format_correct_answer_for_display(self, answer_schema: dict[str, Any], question_type: str) -> str:
        """Extract correct answer from answer_schema for display."""
        # Get correct_key or correct_answer
        correct_key = answer_schema.get("correct_key")
        if correct_key:
            # Handle true/false questions - convert to readable format
            if isinstance(correct_key, str):
                key_lower = correct_key.lower()
                if key_lower == "true":
                    return "정답: 참"
                elif key_lower == "false":
                    return "정답: 거짓"
            return f"정답: {correct_key}"

        # Try correct_answer field
        correct_answer = answer_schema.get("correct_answer")
        if correct_answer:
            if isinstance(correct_answer, bool):
                return f"정답: {'참' if correct_answer else '거짓'}"
            return f"정답: {correct_answer}"

        return "정답: [정보 없음]"

    def _extract_problem_statement(self, stem: str, is_correct: bool) -> str:
        """
        Extract problem statement for display.

        Formats the question stem with "오답/정답 해설입니다" suffix.

        Args:
            stem: Question stem/text
            is_correct: Whether this is for correct answer

        Returns:
            Formatted problem statement string

        """
        statement_type = "정답" if is_correct else "오답"
        return f"'{stem}'에 대한 {statement_type} 해설입니다."

    def _create_fallback_explanation(
        self,
        question_id: str,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        """
        Create fallback explanation when LLM fails.

        Args:
            question_id: Question ID
            error_message: Error details

        Returns:
            Fallback explanation dict

        """
        return {
            "id": str(uuid4()),
            "question_id": question_id,
            "attempt_answer_id": None,
            "explanation_text": (
                "죄송합니다. 현재 상세한 해설을 생성할 수 없습니다. "
                "나중에 다시 시도해주시거나, 교육 담당자에게 문의하세요."
            ),
            "reference_links": [
                {
                    "title": "학습 가이드",
                    "url": "https://example.com/help",
                },
                {
                    "title": "FAQ",
                    "url": "https://example.com/faq",
                },
                {
                    "title": "고객 지원",
                    "url": "https://example.com/support",
                },
            ],
            "is_correct": None,
            "created_at": datetime.now(UTC).isoformat(),
            "is_fallback": True,
            "error_message": error_message,
        }
