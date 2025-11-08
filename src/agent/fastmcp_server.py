"""
FastMCP Tool Server for Item-Gen-Agent

REQ: REQ-A-FastMCP
각 Tool은 별도 REQ로 구현 (REQ-A-Mode1-Tool1~5, REQ-A-Mode2-Tool6)

Reference: LangChain @tool decorator
https://python.langchain.com/docs/concepts/tools
"""

import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


# ============================================================================
# Mode 1: 문항 생성 파이프라인 (Tool 1-5)
# ============================================================================


@tool
def get_user_profile(user_id: str) -> dict:
    """
    Tool 1: Get User Profile

    REQ: REQ-A-Mode1-Tool1

    사용자의 자기평가 정보 조회

    Args:
        user_id: 사용자 ID (UUID)

    Returns:
        dict: 사용자 프로필 정보
        {
            "user_id": "uuid",
            "self_level": "beginner|intermediate|advanced",
            "years_experience": 3,
            "job_role": "Backend Engineer",
            "duty": "FastAPI 개발",
            "interests": ["LLM", "RAG", "Agent Architecture"],
            "previous_score": 72
        }

    에러 처리:
        - 사용자 없음: ValueError 발생
        - 기본값 반환: 재시도 3회 이후

    참고:
        FastAPI 백엔드 엔드포인트: GET /api/v1/profile/{user_id}

    """
    # REQ-A-Mode1-Tool1 구현 (별도)
    # 임시 구현 (Stub)
    logger.info(f"Tool 1: 사용자 {user_id}의 프로필 조회")
    raise NotImplementedError("REQ-A-Mode1-Tool1에서 구현")


@tool
def search_question_templates(interests: list[str], difficulty: int, category: str) -> list[dict]:
    """
    Tool 2: Search Question Templates

    REQ: REQ-A-Mode1-Tool2

    관심분야와 난이도에 맞는 검증된 문항 템플릿 검색
    (Few-shot 예시로 사용)

    Args:
        interests: 관심분야 목록 (예: ["LLM", "RAG"])
        difficulty: 난이도 1~10
        category: 카테고리 ("technical" | "business" | "general")

    Returns:
        list[dict]: 템플릿 리스트 (최대 5개)
        [
            {
                "id": "question_id",
                "stem": "문항 내용",
                "type": "multiple_choice|true_false|short_answer",
                "choices": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "correct_rate": 0.75,
                "usage_count": 5,
                "avg_difficulty_score": 5
            },
            ...
        ]

    에러 처리:
        - 검색 결과 없음: 빈 리스트 반환
        - Tool 3으로 진행

    참고:
        FastAPI 백엔드 엔드포인트: POST /api/v1/tools/search-templates

    """
    # REQ-A-Mode1-Tool2 구현 (별도)
    logger.info(f"Tool 2: 템플릿 검색 (관심분야: {interests}, 난이도: {difficulty})")
    raise NotImplementedError("REQ-A-Mode1-Tool2에서 구현")


@tool
def get_difficulty_keywords(difficulty: int, category: str) -> dict:
    """
    Tool 3: Get Difficulty Keywords

    REQ: REQ-A-Mode1-Tool3

    특정 난이도와 카테고리에 맞는 핵심 키워드와 개념 조회

    Args:
        difficulty: 난이도 1~10
        category: 카테고리 (예: "LLM", "RAG", "Agent Architecture")

    Returns:
        dict: 키워드 및 개념 정보
        {
            "keywords": ["prompt engineering", "token window", "hallucination"],
            "concepts": ["Context Window", "Attention Mechanism"],
            "example_questions": [
                "What is prompt engineering and why is it important?"
            ]
        }

    에러 처리:
        - 데이터 없음: 캐시된 기본 키워드 반환
        - 실패: 재시도 3회 → 기본값

    참고:
        FastAPI 백엔드 엔드포인트: POST /api/v1/tools/difficulty-keywords

    """
    # REQ-A-Mode1-Tool3 구현 (별도)
    logger.info(f"Tool 3: 키워드 조회 (난이도: {difficulty}, 카테고리: {category})")
    raise NotImplementedError("REQ-A-Mode1-Tool3에서 구현")


@tool
def validate_question_quality(
    stem: str,
    question_type: str,
    choices: list[str] | None = None,
    correct_answer: str | None = None,
    batch: bool = False,
) -> dict | list[dict]:
    """
    Tool 4: Validate Question Quality (LLM-based)

    REQ: REQ-A-Mode1-Tool4

    생성된 문항의 품질 검증 (LLM 의미 검증 + 규칙 기반 검증)

    Args:
        stem: 문항 내용
        question_type: 문항 유형 ("multiple_choice" | "true_false" | "short_answer")
        choices: 객관식 선택지 (선택사항)
        correct_answer: 정답 (선택사항)
        batch: 배치 처리 여부

    Returns (단일):
        dict: 검증 결과
        {
            "is_valid": True,
            "score": 0.92,
            "rule_score": 0.95,
            "final_score": 0.92,
            "feedback": "명확하고 적절한 난이도의 문항입니다.",
            "issues": [],
            "recommendation": "pass" | "revise" | "reject"
        }

    Returns (배치):
        list[dict]: 각 문항의 검증 결과

    검증 기준:
        - LLM 의미 검증: 0~1 (명확성, 난이도, 정답 객관성)
        - 규칙 기반: 길이(<=250), 선택지(4~5), 형식, 중복도(<70%)
        - final_score = min(LLM_score, rule_score)
        - 기준: >= 0.85 → pass / 0.70~0.84 → revise (최대 2회) / < 0.70 → reject

    에러 처리:
        - LLM 호출 실패: 재시도 3회
        - 파싱 에러: 기본 점수 0.5 반환

    참고:
        FastAPI 백엔드 엔드포인트:
        - POST /api/v1/tools/validate-question (단일)
        - POST /api/v1/tools/validate-question/batch (배치)

    """
    # REQ-A-Mode1-Tool4 구현 (별도)
    logger.info(f"Tool 4: 문항 검증 (유형: {question_type})")
    raise NotImplementedError("REQ-A-Mode1-Tool4에서 구현")


@tool
def save_generated_question(
    item_type: str,
    stem: str,
    difficulty: int,
    categories: list[str],
    round_id: str,
    choices: list[str] | None = None,
    correct_key: str | None = None,
    correct_keywords: list[str] | None = None,
    validation_score: float | None = None,
    explanation: str | None = None,
) -> dict:
    """
    Tool 5: Save Generated Question

    REQ: REQ-A-Mode1-Tool5

    검증 통과한 문항을 question_bank에 저장

    Args:
        item_type: 문항 유형 ("multiple_choice" | "true_false" | "short_answer")
        stem: 문항 내용
        difficulty: 난이도 1~10
        categories: 도메인 카테고리 (예: ["LLM", "RAG"])
        round_id: 라운드 ID (자동 생성)
        choices: 객관식 선택지 (선택사항)
        correct_key: 객관식/OX 정답 (선택사항)
        correct_keywords: 주관식 키워드 (선택사항)
        validation_score: Tool 4에서 받은 final_score (메타데이터)
        explanation: 해설 (선택사항)

    Returns:
        dict: 저장 결과
        {
            "question_id": "uuid",
            "round_id": "...",
            "saved_at": "2025-11-06T10:30:00Z",
            "success": True
        }

    에러 처리:
        - DB 저장 실패: 메모리 큐에 임시 저장 → 배치 재시도
        - 네트워크 에러: 재시도 3회

    참고:
        FastAPI 백엔드 엔드포인트: POST /api/v1/tools/save-question

    """
    # REQ-A-Mode1-Tool5 구현 (별도)
    logger.info(f"Tool 5: 문항 저장 (라운드: {round_id})")
    raise NotImplementedError("REQ-A-Mode1-Tool5에서 구현")


# ============================================================================
# Mode 2: 자동 채점 파이프라인 (Tool 6)
# ============================================================================


@tool
def score_and_explain(
    session_id: str,
    user_id: str,
    question_id: str,
    question_type: str,
    user_answer: str,
    correct_answer: str | None = None,
    correct_keywords: list[str] | None = None,
    difficulty: int | None = None,
    category: str | None = None,
) -> dict:
    """
    Tool 6: Score & Generate Explanation (LLM-based)

    REQ: REQ-A-Mode2-Tool6

    응시자의 답변을 자동 채점하고 해설 생성

    Args:
        session_id: 시험 세션 ID
        user_id: 응시자 ID
        question_id: 문항 ID
        question_type: 문항 유형 ("multiple_choice" | "true_false" | "short_answer")
        user_answer: 응시자의 답변
        correct_answer: 정답 (객관식/OX용)
        correct_keywords: 정답 키워드 (주관식용)
        difficulty: 난이도 (LLM 프롬프트용)
        category: 카테고리 (LLM 프롬프트용)

    Returns:
        dict: 채점 결과
        {
            "attempt_id": "uuid",
            "session_id": "uuid",
            "question_id": "uuid",
            "user_id": "uuid",
            "is_correct": True,
            "score": 100,
            "explanation": "정답 해설: 이것이 정답인 이유는...",
            "keyword_matches": ["keyword1", "keyword2"],
            "feedback": "더 나은 답변을 위한 피드백...",
            "graded_at": "2025-11-06T10:35:00Z"
        }

    채점 기준:
        - 객관식/OX: user_answer == correct_answer → is_correct = True, score = 100
        - 주관식: LLM 평가 (0~100)
          * >= 80: is_correct = True
          * 70~79: 부분 정답
          * < 70: is_correct = False

    에러 처리:
        - LLM 호출 실패: 재시도 3회
        - 파싱 에러: 기본 점수 0 반환

    참고:
        FastAPI 백엔드 엔드포인트: POST /api/v1/tools/score-and-explain

    """
    # REQ-A-Mode2-Tool6 구현 (별도)
    logger.info(f"Tool 6: 채점 (세션: {session_id}, 문항: {question_id})")
    raise NotImplementedError("REQ-A-Mode2-Tool6에서 구현")


# ============================================================================
# Tool 목록
# ============================================================================

TOOLS = [
    get_user_profile,
    search_question_templates,
    get_difficulty_keywords,
    validate_question_quality,
    save_generated_question,
    score_and_explain,
]
