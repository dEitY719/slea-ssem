"""
Explanation generation service for generating question explanations with reference links.

REQ: REQ-B-B3-Explain
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from src.backend.models.answer_explanation import AnswerExplanation
from src.backend.models.question import Question


class ExplainService:
    """
    Service for generating explanations for test questions.

    REQ: REQ-B-B3-Explain-1

    Methods:
        generate_explanation: Generate new explanation or retrieve cached
        get_explanation: Retrieve cached explanation

    Design:
        - Generates 500+ character explanations with 3+ reference links
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
                - explanation_text (str): Generated explanation (≥500 chars)
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
            return self._format_explanation_response(cached, attempt_answer_id)

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

        return self._format_explanation_response(explanation)

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
        query = self.session.query(AnswerExplanation).filter_by(question_id=question_id)

        if attempt_answer_id:
            query = query.filter_by(attempt_answer_id=attempt_answer_id)

        explanation = query.first()

        if not explanation:
            return None

        return self._format_explanation_response(explanation)

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
        Generate explanation using LLM.

        Args:
            question: Question object
            user_answer: User's submitted answer
            is_correct: Whether answer is correct

        Returns:
            Dictionary with 'explanation' and 'reference_links'

        Raises:
            TimeoutError: If LLM request times out

        """
        # Mock implementation - placeholder for actual LLM integration
        # In production, replace with OpenAI/Claude API calls
        return self._generate_mock_explanation(question, user_answer, is_correct)

    def _generate_mock_explanation(
        self,
        question: Question,
        user_answer: str | dict,
        is_correct: bool,
    ) -> dict[str, Any]:
        """
        Generate mock explanation (placeholder for LLM integration).

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

        if is_correct:
            explanation_template = (
                f"'{stem}' 문제에 대한 정답 해설입니다.\n\n"
                f"귀하의 답변이 정확합니다. 이는 {category} 분야의 중요한 개념입니다.\n"
                f"정답을 선택하신 이유는 문제의 핵심을 정확하게 파악하셨기 때문입니다.\n\n"
                f"더 깊이 있는 이해를 위해 다음 사항들을 주목하세요:\n"
                f"1. 이 개념의 핵심 원리와 적용 범위\n"
                f"2. 실무에서의 활용 예시\n"
                f"3. 관련 기술이나 이론과의 연결고리\n"
                f"4. 흔한 오해와 정확한 구분\n\n"
                f"이 내용을 잘 숙지하면 관련 문제들을 더 효과적으로 해결할 수 있습니다."
            )
        else:
            answer_schema = question.answer_schema
            correct_key = answer_schema.get("correct_key", "N/A")

            explanation_template = (
                f"'{stem}' 문제에 대한 오답 해설입니다.\n\n"
                f"귀하의 답변: {user_answer}\n"
                f"정답: {correct_key}\n\n"
                f"이 문제에서 자주 하는 실수:\n"
                f"많은 수험자들이 문제의 세부 조건을 놓치거나 "
                f"비슷한 개념을 혼동하여 오답을 선택합니다.\n\n"
                f"정답이 {correct_key}인 이유:\n"
                f"1. {category} 분야의 기본 원리에 부합\n"
                f"2. 다른 선택지들과의 차별화된 특성\n"
                f"3. 실제 사례와의 연결고리\n\n"
                f"향후 학습 방향:\n"
                f"이 유형의 문제를 다시 한번 복습하고, "
                f"관련 개념들의 차이점을 명확하게 구분하는 것이 중요합니다."
            )

        # Create reference links (category-specific)
        reference_links = self._generate_mock_references(category, is_correct)

        return {
            "explanation": explanation_template,
            "reference_links": reference_links,
        }

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

        # AC1: Explanation >= 500 characters
        if len(explanation) < 500:
            raise ValueError(f"Explanation must be at least 500 characters. Got {len(explanation)} chars.")

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
        attempt_answer_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Format explanation as API response.

        Args:
            explanation: AnswerExplanation ORM object
            attempt_answer_id: Optional override for attempt_answer_id

        Returns:
            Formatted explanation dictionary

        """
        return {
            "id": explanation.id,
            "question_id": explanation.question_id,
            "attempt_answer_id": attempt_answer_id or explanation.attempt_answer_id,
            "explanation_text": explanation.explanation_text,
            "reference_links": explanation.reference_links,
            "is_correct": explanation.is_correct,
            "created_at": explanation.created_at.isoformat(),
            "is_fallback": False,
            "error_message": None,
        }

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
