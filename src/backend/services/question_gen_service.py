"""
Question generation service for generating test questions.

REQ: REQ-B-B2-Gen-1, REQ-B-B2-Gen-2, REQ-B-B2-Gen-3

Note: This is a Mock implementation. In production, replace with actual LLM integration.
"""

from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from src.backend.models.question import Question
from src.backend.models.test_session import TestSession
from src.backend.models.user_profile import UserProfileSurvey


class QuestionGenerationService:
    """
    Service for generating test questions.

    REQ: REQ-B-B2-Gen-1, REQ-B-B2-Gen-2, REQ-B-B2-Gen-3

    Current Implementation: Mock data (placeholder for LLM integration)
    Future: Replace mock_questions() with actual OpenAI/LLM API calls

    Methods:
        generate_questions: Generate 5 questions based on survey data

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

    def generate_questions(
        self,
        user_id: int,
        survey_id: str,
        round_num: int = 1,
    ) -> dict[str, Any]:
        """
        Generate 5 questions based on survey data (Mock Implementation).

        REQ: REQ-B-B2-Gen-1, REQ-B-B2-Gen-2, REQ-B-B2-Gen-3

        In production, this would call LLM API (OpenAI, etc.) with:
        - User's proficiency level
        - User's interests
        - Category-specific "fun" prompts

        Current: Returns mock questions based on user interests

        Args:
            user_id: User ID
            survey_id: UserProfileSurvey ID to get interests
            round_num: Round number (1 or 2, default 1)

        Returns:
            Dictionary with:
                - session_id (str): TestSession UUID
                - questions (list): List of 5 question dictionaries with all fields

        Raises:
            Exception: If survey not found

        """
        # Get survey to determine user interests
        survey = self.session.query(UserProfileSurvey).filter_by(id=survey_id).first()
        if not survey:
            raise Exception(f"Survey with id {survey_id} not found.")

        # Create test session
        session_id = str(uuid4())
        test_session = TestSession(
            id=session_id,
            user_id=user_id,
            survey_id=survey_id,
            round=round_num,
            status="in_progress",
        )
        self.session.add(test_session)
        self.session.commit()

        # Generate 5 questions based on user interests
        questions_list = []
        interests = survey.interests or []

        # Select categories: use survey interests if available, otherwise use all categories
        selected_categories = interests if interests else list(self.MOCK_QUESTIONS.keys())

        # Generate 5 questions (cycling through categories)
        for idx in range(5):
            category = selected_categories[idx % len(selected_categories)]
            mock_questions = self.MOCK_QUESTIONS.get(category, [])

            if not mock_questions:
                continue

            # Select mock question (use idx to vary)
            mock_q = mock_questions[idx % len(mock_questions)]

            # Create Question record
            question = Question(
                id=str(uuid4()),
                session_id=session_id,
                item_type=mock_q["item_type"],
                stem=mock_q["stem"],
                choices=mock_q.get("choices"),
                answer_schema=mock_q["answer_schema"],
                difficulty=mock_q["difficulty"],
                category=category,
                round=round_num,
            )
            self.session.add(question)
            questions_list.append(question)

        self.session.commit()

        # Format response
        return {
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
        }
