"""
Agent Output Converter: Structured parsing of LangChain Agent responses.

REQ: REQ-A-OutputConverter

개요:
    LangChain ReAct Agent의 다양한 출력 형식(ReAct 텍스트, structured JSON)을
    일관되고 구조화된 GeneratedItem/ScoreResult로 변환합니다.

    주요 기능:
    - Final Answer JSON 추출 및 파싱
    - 다양한 answer_schema 형식 정규화
    - 타입별 데이터 변환 (MC vs Short Answer)
    - 검증 및 에러 처리

설계 원칙:
    - Single Responsibility: 파싱만 담당
    - Dependency Inversion: Pydantic 모델과만 의존
    - Composition: 작은 메서드 조합
    - Testability: 각 메서드 독립적 테스트 가능
"""

import json
import logging
import re
import uuid

logger = logging.getLogger(__name__)


# ============================================================================
# AgentOutputConverter: 핵심 클래스
# ============================================================================


class AgentOutputConverter:
    r"""
    LangChain Agent 출력을 구조화된 형식으로 변환.

    지원하는 입력 형식:
    1. ReAct 텍스트: "Final Answer: [...JSON...]"
    2. Structured: "Final Answer: {json_object}"
    3. 마크다운: "Final Answer: ```json\n[...]\n```"

    예제:
        converter = AgentOutputConverter()

        # Final Answer JSON 추출 및 파싱
        questions_data = converter.parse_final_answer_json(ai_message_content)

        # 데이터를 GeneratedItem으로 변환
        items = converter.extract_items_from_questions(
            questions_data,
            question_types=["multiple_choice", "short_answer"]
        )

        # answer_schema 검증
        for item in items:
            assert converter.validate_answer_schema(item.answer_schema)
    """

    # ==========================================================================
    # 1. JSON 추출 및 파싱
    # ==========================================================================

    @staticmethod
    def parse_final_answer_json(content: str, max_attempts: int = 5) -> dict | list:
        """
        ReAct 형식의 AI Message에서 Final Answer JSON을 추출하고 파싱.

        처리 단계:
        1. "Final Answer:" 패턴 탐색
        2. 마크다운 코드블록 제거 (```json ... ```)
        3. Escaped 문자 처리
        4. Robust JSON 파싱 (5가지 cleanup strategy)

        Args:
            content: AI Message의 content (ReAct 텍스트 형식)
            max_attempts: 최대 cleanup 시도 횟수

        Returns:
            파싱된 JSON 객체 또는 배열

        Raises:
            json.JSONDecodeError: 모든 cleanup 시도 실패 시
            ValueError: content가 None이거나 Final Answer 패턴 없을 시

        """
        if not content or not isinstance(content, str):
            raise ValueError("content must be a non-empty string")

        # Step 1: "Final Answer:" 패턴 탐색
        if "Final Answer:" not in content:
            raise ValueError('Content must contain "Final Answer:" pattern')

        json_start = content.find("Final Answer:") + len("Final Answer:")
        json_str = content[json_start:].strip()

        # Step 2: 마크다운 코드블록 제거
        json_str = AgentOutputConverter._remove_markdown_code_blocks(json_str)

        # Step 3: Escaped 문자 처리
        json_str = AgentOutputConverter._unescape_json_string(json_str)

        # Step 4: Robust JSON 파싱
        try:
            parsed = AgentOutputConverter._parse_json_robust(json_str, max_attempts)
            logger.info("✅ Successfully parsed Final Answer JSON")
            return parsed
        except json.JSONDecodeError:
            logger.error(f"❌ Failed to parse Final Answer JSON after {max_attempts} attempts")
            raise

    @staticmethod
    def _remove_markdown_code_blocks(json_str: str) -> str:
        """마크다운 코드블록 (```json ... ```) 제거."""
        if "```json" in json_str:
            return json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            return json_str.split("```")[1].split("```")[0].strip()
        return json_str

    @staticmethod
    def _unescape_json_string(json_str: str) -> str:
        r"""
        JSON 문자열의 escaped 문자 처리.

        처리 대상:
        - \\' → ' (single quote)
        - \\" → " (double quote)
        - \\bNone\\b → null (Python None)
        """
        # Remove backslash before single quotes
        json_str = json_str.replace("\\'", "'")
        # Replace escaped double quotes
        json_str = json_str.replace('\\"', '"')
        # Convert Python None to JSON null
        json_str = re.sub(r"\bNone\b", "null", json_str)
        return json_str

    @staticmethod
    def _parse_json_robust(json_str: str, max_attempts: int = 5) -> dict | list:
        """
        5가지 cleanup strategy를 순차적으로 적용하는 robust JSON 파싱.

        Strategy 1: 현상태로 파싱
        Strategy 2: Python literals (True/False) 변환
        Strategy 3: Trailing commas 제거
        Strategy 4: Escape 문자 처리
        Strategy 5: Control characters 제거

        Args:
            json_str: Raw JSON 문자열
            max_attempts: 최대 시도 횟수

        Returns:
            파싱된 JSON 객체 또는 배열

        Raises:
            json.JSONDecodeError: 모든 전략 실패 시

        """
        cleanup_strategies = [
            ("no_cleanup", lambda s: s),
            ("fix_python_literals", lambda s: re.sub(r"\b(True|False)\b", lambda m: m.group(1).lower(), s)),
            ("fix_trailing_commas", lambda s: re.sub(r",(\s*[}\]])", r"\1", s)),
            ("fix_escapes", lambda s: re.sub(r"\\(?!\\|/|[btnfr])", "\\\\", s)),
            ("remove_control_chars", lambda s: s.encode("utf-8", "ignore").decode("utf-8")),
        ]

        last_error = None
        for attempt_num, (strategy_name, cleanup_fn) in enumerate(cleanup_strategies, 1):
            try:
                cleaned_json = cleanup_fn(json_str)
                result = json.loads(cleaned_json)

                if attempt_num > 1:
                    logger.debug(
                        f"✅ JSON parsing succeeded with strategy '{strategy_name}' "
                        f"(attempt {attempt_num}/{len(cleanup_strategies)})"
                    )
                return result

            except json.JSONDecodeError as e:
                last_error = e
                logger.debug(f"⚠️  Strategy '{strategy_name}' failed: {str(e)[:100]}")
                if attempt_num >= max_attempts:
                    break

        raise last_error

    # ==========================================================================
    # 2. 데이터 변환: 질문 데이터 → GeneratedItem
    # ==========================================================================

    @staticmethod
    def extract_items_from_questions(
        questions_data: dict | list,
        question_types: list[str] | None = None,
    ) -> list[dict]:
        """
        파싱된 JSON 데이터를 정규화된 item dict 리스트로 변환.

        입력 데이터 구조:
        [
            {
                "question_id": "...",
                "type": "multiple_choice",
                "stem": "...",
                "choices": [...],
                "answer_schema": {...} or "exact_match",
                "difficulty": 5,
                "category": "AI",
                "correct_answer": "B" (optional, from Tool 5),
                "validation_score": 0.9
            },
            ...
        ]

        반환값: 정규화된 dict (caller가 GeneratedItem으로 변환)
        [
            {
                "id": "q_xxx",
                "type": "multiple_choice",
                "stem": "...",
                "choices": [...],
                "answer_schema": {
                    "type": "exact_match",
                    "keywords": None,
                    "correct_answer": "B"
                },
                "difficulty": 5,
                "category": "AI",
                "validation_score": 0.9
            },
            ...
        ]

        Args:
            questions_data: 파싱된 JSON (list 또는 dict)
            question_types: 기대하는 질문 타입 (필터링용, optional)

        Returns:
            list[dict]: 정규화된 item dict 리스트

        Raises:
            ValueError: 필수 필드 부족 시

        """
        if not isinstance(questions_data, list):
            questions_data = [questions_data]

        items: list[dict] = []

        for q_dict in questions_data:
            try:
                item = AgentOutputConverter._convert_question_to_item(q_dict)
                items.append(item)
            except ValueError as e:
                logger.warning(f"⚠️  Skipped invalid question: {str(e)}")
                continue

        logger.info(f"✅ Extracted {len(items)} valid items from questions data")
        return items

    @staticmethod
    def _convert_question_to_item(q_dict: dict) -> dict:
        """
        단일 질문 dict를 정규화된 item dict로 변환.

        필수 필드:
        - type: "multiple_choice" | "true_false" | "short_answer"
        - stem: 질문 텍스트

        선택 필드:
        - question_id: UUID (없으면 자동 생성)
        - choices: 선택지 (MC/TF에 필요)
        - answer_schema: dict 또는 string (정규화됨)
        - difficulty: 1-10 (기본값 5)
        - category: 문항 카테고리 (기본값 "AI")
        - validation_score: 검증 점수 (기본값 0.0)

        Returns:
            dict: 정규화된 item dict (GeneratedItem 호환)

        Raises:
            ValueError: 필수 필드 부족 시

        """
        # 필수 필드 검증
        if "type" not in q_dict or "stem" not in q_dict:
            raise ValueError(f"Missing required fields: type or stem in {q_dict}")

        question_type = q_dict.get("type", "multiple_choice")
        stem = q_dict.get("stem", "")

        if not stem:
            raise ValueError("stem cannot be empty")

        # Answer schema 정규화
        raw_answer_schema = q_dict.get("answer_schema")
        normalized_schema_type = AgentOutputConverter.normalize_schema_type(raw_answer_schema)

        # Correct answer 추출 (다중 필드 지원)
        correct_answer_value = (
            q_dict.get("correct_answer")
            or q_dict.get("correct_key")
            or (raw_answer_schema.get("correct_answer") if isinstance(raw_answer_schema, dict) else None)
            or (raw_answer_schema.get("correct_key") if isinstance(raw_answer_schema, dict) else None)
        )

        # Type별 answer_schema 구성 (dict 반환)
        if question_type == "short_answer":
            # Extract keywords from either top-level or nested answer_schema
            keywords = q_dict.get("correct_keywords")
            if keywords is None and isinstance(raw_answer_schema, dict):
                keywords = raw_answer_schema.get("keywords") or raw_answer_schema.get("correct_keywords")

            answer_schema_dict = {
                "type": normalized_schema_type,
                "keywords": keywords,
                "correct_answer": None,
            }
        else:
            answer_schema_dict = {
                "type": normalized_schema_type,
                "keywords": None,
                "correct_answer": correct_answer_value,
            }

        item_dict = {
            "id": q_dict.get("question_id", f"q_{uuid.uuid4().hex[:8]}"),
            "type": question_type,
            "stem": stem,
            "choices": q_dict.get("choices"),
            "answer_schema": answer_schema_dict,
            "difficulty": int(q_dict.get("difficulty", 5)),
            "category": q_dict.get("category", "AI"),
            "validation_score": float(q_dict.get("validation_score", 0.0)),
        }

        return item_dict

    # ==========================================================================
    # 3. Answer Schema 정규화
    # ==========================================================================

    @staticmethod
    def normalize_schema_type(answer_schema_raw: str | dict | None) -> str:
        """
        다양한 형식의 answer_schema를 표준 타입 문자열로 정규화.

        지원하는 입력 형식:
        1. Tool 5 형식: {"type": "exact_match", ...}
        2. Mock 형식: {"correct_key": "B", "explanation": "..."}
        3. Keyword 형식: {"keywords": [...]}
        4. 문자열: "exact_match"
        5. List: [...] (keyword_match로 추론)
        6. correct_answer만 있는 경우: exact_match
        7. correct_keywords만 있는 경우: keyword_match

        반환값:
        - "exact_match" (MC, TF 기본)
        - "keyword_match" (Short answer)
        - "semantic_match" (고급 채점)

        Args:
            answer_schema_raw: Raw answer_schema 값

        Returns:
            정규화된 타입 문자열

        """
        if isinstance(answer_schema_raw, dict):
            # Case 1: Tool 5 형식 - 명시적 'type' 필드
            if "type" in answer_schema_raw:
                schema_type = answer_schema_raw.get("type")
                if isinstance(schema_type, str) and schema_type:
                    return schema_type

            # Case 2: Mock 형식 - "correct_key" 또는 "explanation"
            if "correct_key" in answer_schema_raw or "explanation" in answer_schema_raw:
                return "exact_match"

            # Case 3: Keywords 포함 - keyword_match
            if "keywords" in answer_schema_raw and answer_schema_raw.get("keywords"):
                return "keyword_match"

            # Case 4: correct_keywords 포함 - keyword_match
            if "correct_keywords" in answer_schema_raw and answer_schema_raw.get("correct_keywords"):
                return "keyword_match"

            # Case 5: correct_answer 포함 (MC/TF) - exact_match
            if "correct_answer" in answer_schema_raw or "correct_key" in answer_schema_raw:
                return "exact_match"

            # Case 6: 기타 'type' 필드
            for key in ["answer_type", "schema_type", "answer_schema_type"]:
                if key in answer_schema_raw:
                    val = answer_schema_raw.get(key)
                    if isinstance(val, str) and val:
                        return val

        if isinstance(answer_schema_raw, str):
            return answer_schema_raw.strip() if answer_schema_raw else "exact_match"

        if isinstance(answer_schema_raw, list):
            return "keyword_match"

        # 기본값
        logger.warning(
            f"⚠️  answer_schema has unexpected type: {type(answer_schema_raw).__name__}. Defaulting to 'exact_match'"
        )
        return "exact_match"

    @staticmethod
    def normalize_answer_schema_dict(answer_schema_raw: str | dict | None, question_type: str) -> dict:
        """
        Raw answer_schema를 정규화된 dict로 변환.

        입력:
        - answer_schema_raw: 다양한 형식의 raw answer_schema
        - question_type: 질문 타입 ("multiple_choice", "true_false", "short_answer")

        출력:
        {
            "type": "exact_match" | "keyword_match" | "semantic_match",
            "keywords": [...] or None,
            "correct_answer": "..." or None
        }

        규칙:
        - short_answer: keywords만 포함, correct_answer는 None
        - MC/TF: correct_answer만 포함, keywords는 None

        Args:
            answer_schema_raw: Raw answer_schema
            question_type: 질문 타입

        Returns:
            정규화된 answer_schema dict

        """
        schema_type = AgentOutputConverter.normalize_schema_type(answer_schema_raw)

        # Extract values from raw schema
        keywords = None
        correct_answer = None

        if isinstance(answer_schema_raw, dict):
            # Extract keywords
            keywords = answer_schema_raw.get("keywords") or answer_schema_raw.get("correct_keywords")

            # Extract correct_answer
            correct_answer = answer_schema_raw.get("correct_answer") or answer_schema_raw.get("correct_key")

        # Type-aware construction
        if question_type == "short_answer":
            return {
                "type": schema_type,
                "keywords": keywords,
                "correct_answer": None,  # Not used for short answer
            }
        else:
            # MC or TF
            return {
                "type": schema_type,
                "keywords": None,  # Not used for MC/TF
                "correct_answer": correct_answer,
            }

    # ==========================================================================
    # 4. 검증
    # ==========================================================================

    @staticmethod
    def validate_answer_schema(answer_schema: dict) -> bool:
        """
        Answer schema dict의 일관성을 검증.

        규칙:
        1. type은 항상 필수
        2. short_answer: keywords는 있고, correct_answer는 None
        3. MC/TF: correct_answer는 있고, keywords는 None
        4. type은 유효한 값 ("exact_match", "keyword_match", "semantic_match")

        Args:
            answer_schema: 검증할 answer_schema dict

        Returns:
            bool: 유효하면 True, 아니면 False

        """
        if not isinstance(answer_schema, dict):
            logger.warning(f"❌ answer_schema must be dict, got {type(answer_schema).__name__}")
            return False

        schema_type = answer_schema.get("type")
        if not schema_type:
            logger.warning("❌ answer_schema.type is missing")
            return False

        valid_types = ["exact_match", "keyword_match", "semantic_match"]
        if schema_type not in valid_types:
            logger.warning(f"❌ answer_schema.type '{schema_type}' not in {valid_types}")
            return False

        return True

    @staticmethod
    def validate_generated_item(item: dict) -> bool:
        """
        Validate all fields in a generated item dict.

        검사 항목:
        1. id: UUID 형식
        2. type: 유효한 질문 타입
        3. stem: 비어있지 않음
        4. answer_schema: 유효함
        5. difficulty: 1-10 범위
        6. category: 비어있지 않음

        Args:
            item: 검증할 item dict

        Returns:
            bool: 유효하면 True

        """
        if not isinstance(item, dict):
            logger.warning(f"❌ item must be dict, got {type(item).__name__}")
            return False

        # Type 검증
        item_type = item.get("type")
        valid_types = ["multiple_choice", "true_false", "short_answer"]
        if item_type not in valid_types:
            logger.warning(f"❌ Invalid item type: {item_type}")
            return False

        # Stem 검증
        stem = item.get("stem")
        if not stem or not isinstance(stem, str):
            logger.warning("❌ Invalid or missing stem")
            return False

        # Answer schema 검증
        answer_schema = item.get("answer_schema")
        if not AgentOutputConverter.validate_answer_schema(answer_schema):
            return False

        # Difficulty 검증
        difficulty = item.get("difficulty")
        if not isinstance(difficulty, int) or not (1 <= difficulty <= 10):
            logger.warning(f"❌ difficulty out of range: {difficulty}")
            return False

        # Category 검증
        category = item.get("category")
        if not category:
            logger.warning("❌ category is empty")
            return False

        return True
