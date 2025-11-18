"""
Tests for AgentOutputConverter.

REQ: REQ-A-OutputConverter

테스트 대상:
- parse_final_answer_json(): Final Answer JSON 추출 및 파싱
- extract_items_from_questions(): 데이터 변환
- normalize_schema_type(): answer_schema 정규화
- validate_answer_schema(): 스키마 검증
- validate_generated_item(): 문항 검증
"""

import json
import pytest

from src.agent.output_converter import AgentOutputConverter


class TestParseFinalAnswerJson:
    """parse_final_answer_json() 테스트."""

    def test_parse_simple_json_array(self):
        """단순 JSON 배열 파싱."""
        content = """
        Some reasoning here.

        Final Answer: [
            {"id": "q1", "stem": "What is AI?"},
            {"id": "q2", "stem": "What is ML?"}
        ]
        """
        result = AgentOutputConverter.parse_final_answer_json(content)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["id"] == "q1"

    def test_parse_json_with_markdown_code_block(self):
        """마크다운 코드블록이 포함된 JSON 파싱."""
        content = """
        Final Answer: ```json
        {
            "id": "q1",
            "stem": "Test question"
        }
        ```
        """
        result = AgentOutputConverter.parse_final_answer_json(content)
        assert isinstance(result, dict)
        assert result["id"] == "q1"

    def test_parse_json_with_escaped_quotes(self):
        """Escaped quotes가 포함된 JSON 파싱 (이미 유효한 JSON)."""
        # LLM은 보통 제대로 escaped quotes를 사용함
        content = """
        Final Answer: {"stem": "What is machine learning?"}
        """
        result = AgentOutputConverter.parse_final_answer_json(content)
        assert isinstance(result, dict)
        assert "machine learning" in result["stem"]

    def test_parse_json_with_python_literals(self):
        """Python 리터럴 (True, False, None)이 포함된 JSON."""
        content = """
        Final Answer: {
            "is_valid": True,
            "keywords": null,
            "score": False
        }
        """
        result = AgentOutputConverter.parse_final_answer_json(content)
        assert isinstance(result, dict)
        assert result["is_valid"] is True
        assert result["keywords"] is None

    def test_parse_json_with_trailing_commas(self):
        """Trailing commas가 있는 JSON."""
        content = """
        Final Answer: {
            "id": "q1",
            "stem": "Test",
        }
        """
        result = AgentOutputConverter.parse_final_answer_json(content)
        assert isinstance(result, dict)
        assert result["id"] == "q1"

    def test_parse_json_multiline_array(self):
        """여러 줄에 걸친 JSON 배열."""
        content = """
        Final Answer: [
            {
                "id": "q1",
                "stem": "Question 1"
            },
            {
                "id": "q2",
                "stem": "Question 2"
            }
        ]
        """
        result = AgentOutputConverter.parse_final_answer_json(content)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_parse_missing_final_answer_pattern(self):
        """Final Answer: 패턴이 없는 경우."""
        content = "Some content without Final Answer"
        with pytest.raises(ValueError, match="Final Answer"):
            AgentOutputConverter.parse_final_answer_json(content)

    def test_parse_empty_content(self):
        """빈 content."""
        with pytest.raises(ValueError):
            AgentOutputConverter.parse_final_answer_json("")

    def test_parse_none_content(self):
        """None content."""
        with pytest.raises(ValueError):
            AgentOutputConverter.parse_final_answer_json(None)

    def test_parse_invalid_json(self):
        """유효하지 않은 JSON."""
        content = 'Final Answer: {"invalid": json without closing brace'
        with pytest.raises(json.JSONDecodeError):
            AgentOutputConverter.parse_final_answer_json(content)


class TestExtractItemsFromQuestions:
    """extract_items_from_questions() 테스트."""

    def test_extract_single_multiple_choice_question(self):
        """단일 객관식 문항 추출."""
        q_data = {
            "question_id": "q1",
            "type": "multiple_choice",
            "stem": "What is AI?",
            "choices": ["A. ...", "B. ...", "C. ...", "D. ..."],
            "answer_schema": {"type": "exact_match"},
            "correct_answer": "B",
            "difficulty": 3,
            "category": "AI",
            "validation_score": 0.95,
        }

        items = AgentOutputConverter.extract_items_from_questions([q_data])
        assert len(items) == 1
        item = items[0]
        assert item["id"] == "q1"
        assert item["type"] == "multiple_choice"
        assert item["stem"] == "What is AI?"
        assert item["answer_schema"]["correct_answer"] == "B"
        assert item["validation_score"] == 0.95

    def test_extract_short_answer_with_keywords(self):
        """키워드가 있는 단답식 문항 추출."""
        q_data = {
            "question_id": "q2",
            "type": "short_answer",
            "stem": "Explain machine learning",
            "answer_schema": {"type": "keyword_match"},
            "correct_keywords": ["learning", "data", "improve"],
            "difficulty": 5,
            "category": "ML",
        }

        items = AgentOutputConverter.extract_items_from_questions([q_data])
        assert len(items) == 1
        item = items[0]
        assert item["type"] == "short_answer"
        assert item["answer_schema"]["keywords"] == ["learning", "data", "improve"]
        assert item["answer_schema"]["correct_answer"] is None

    def test_extract_multiple_questions(self):
        """여러 문항 추출."""
        q_data_list = [
            {
                "question_id": "q1",
                "type": "multiple_choice",
                "stem": "Q1",
                "choices": ["A", "B"],
                "answer_schema": "exact_match",
                "correct_answer": "A",
                "difficulty": 1,
                "category": "AI",
            },
            {
                "question_id": "q2",
                "type": "true_false",
                "stem": "Q2",
                "answer_schema": "exact_match",
                "correct_answer": "True",
                "difficulty": 2,
                "category": "ML",
            },
        ]

        items = AgentOutputConverter.extract_items_from_questions(q_data_list)
        assert len(items) == 2
        assert items[0]["type"] == "multiple_choice"
        assert items[1]["type"] == "true_false"

    def test_extract_question_missing_required_fields(self):
        """필수 필드 누락 (건너뜀)."""
        q_data_list = [
            {
                "question_id": "q1",
                "type": "multiple_choice",
                "stem": "Valid question",
                "difficulty": 1,
                "category": "AI",
            },
            {
                # stem 누락 - 건너뜀
                "question_id": "q2",
                "type": "multiple_choice",
                "difficulty": 1,
                "category": "AI",
            },
            {
                # type 누락 - 건너뜀
                "stem": "Q3",
                "difficulty": 1,
                "category": "AI",
            },
        ]

        items = AgentOutputConverter.extract_items_from_questions(q_data_list)
        # 유효한 1개만 추출됨
        assert len(items) == 1
        assert items[0]["id"] == "q1"

    def test_extract_with_auto_generated_id(self):
        """문항 ID 자동 생성."""
        q_data = {
            # question_id 없음
            "type": "multiple_choice",
            "stem": "Test",
            "difficulty": 1,
            "category": "AI",
        }

        items = AgentOutputConverter.extract_items_from_questions([q_data])
        assert len(items) == 1
        # UUID 형식으로 자동 생성됨
        assert items[0]["id"].startswith("q_")
        assert len(items[0]["id"]) > 4

    def test_extract_single_dict_converted_to_list(self):
        """단일 dict가 list로 변환됨."""
        q_data = {
            "question_id": "q1",
            "type": "multiple_choice",
            "stem": "Test",
            "difficulty": 1,
            "category": "AI",
        }

        items = AgentOutputConverter.extract_items_from_questions(q_data)
        assert len(items) == 1


class TestNormalizeAnswerSchemaDict:
    """normalize_answer_schema_dict() 테스트."""

    def test_normalize_mc_with_correct_answer(self):
        """MC 타입 answer_schema 정규화."""
        raw = {"type": "exact_match", "correct_answer": "B"}
        result = AgentOutputConverter.normalize_answer_schema_dict(raw, "multiple_choice")
        assert result["type"] == "exact_match"
        assert result["correct_answer"] == "B"
        assert result["keywords"] is None

    def test_normalize_short_answer_with_keywords(self):
        """Short answer 타입 answer_schema 정규화."""
        raw = {"type": "keyword_match", "keywords": ["AI", "machine learning"]}
        result = AgentOutputConverter.normalize_answer_schema_dict(raw, "short_answer")
        assert result["type"] == "keyword_match"
        assert result["keywords"] == ["AI", "machine learning"]
        assert result["correct_answer"] is None

    def test_normalize_true_false_with_correct_key(self):
        """TF 타입 (correct_key 사용) 정규화."""
        raw = {"correct_key": "True"}
        result = AgentOutputConverter.normalize_answer_schema_dict(raw, "true_false")
        assert result["type"] == "exact_match"
        assert result["correct_answer"] == "True"
        assert result["keywords"] is None

    def test_normalize_short_answer_with_correct_keywords(self):
        """Short answer (correct_keywords 필드) 정규화."""
        raw = {"correct_keywords": ["python", "programming"]}
        result = AgentOutputConverter.normalize_answer_schema_dict(raw, "short_answer")
        assert result["type"] == "keyword_match"
        assert result["keywords"] == ["python", "programming"]

    def test_normalize_string_type_mc(self):
        """String 형식 answer_schema (MC)."""
        raw = "exact_match"
        result = AgentOutputConverter.normalize_answer_schema_dict(raw, "multiple_choice")
        assert result["type"] == "exact_match"
        assert result["correct_answer"] is None
        assert result["keywords"] is None


class TestNormalizeSchemaType:
    """normalize_schema_type() 테스트."""

    def test_normalize_tool5_format(self):
        """Tool 5 형식 (explicit type)."""
        schema = {"type": "exact_match", "keywords": None, "correct_answer": "B"}
        result = AgentOutputConverter.normalize_schema_type(schema)
        assert result == "exact_match"

    def test_normalize_tool5_keyword_format(self):
        """Tool 5 keyword 형식."""
        schema = {"type": "keyword_match", "keywords": ["learn", "data"]}
        result = AgentOutputConverter.normalize_schema_type(schema)
        assert result == "keyword_match"

    def test_normalize_mock_format(self):
        """Mock 형식 (correct_key + explanation)."""
        schema = {"correct_key": "B", "explanation": "This is correct"}
        result = AgentOutputConverter.normalize_schema_type(schema)
        assert result == "exact_match"

    def test_normalize_keyword_dict_format(self):
        """Keywords dict 형식."""
        schema = {"keywords": ["artificial", "intelligence", "machine"]}
        result = AgentOutputConverter.normalize_schema_type(schema)
        assert result == "keyword_match"

    def test_normalize_string_format(self):
        """문자열 형식."""
        result = AgentOutputConverter.normalize_schema_type("semantic_match")
        assert result == "semantic_match"

    def test_normalize_list_format(self):
        """List 형식 (keyword_match로 추론)."""
        result = AgentOutputConverter.normalize_schema_type(["keyword1", "keyword2"])
        assert result == "keyword_match"

    def test_normalize_none_format(self):
        """None (기본값)."""
        result = AgentOutputConverter.normalize_schema_type(None)
        assert result == "exact_match"

    def test_normalize_empty_dict(self):
        """빈 dict (기본값)."""
        result = AgentOutputConverter.normalize_schema_type({})
        assert result == "exact_match"

    def test_normalize_answer_type_field(self):
        """answer_type 필드 (alternative field name)."""
        schema = {"answer_type": "semantic_match"}
        result = AgentOutputConverter.normalize_schema_type(schema)
        assert result == "semantic_match"


class TestValidateAnswerSchema:
    """validate_answer_schema() 테스트."""

    def test_validate_valid_exact_match(self):
        """유효한 exact_match."""
        schema = {
            "type": "exact_match",
            "keywords": None,
            "correct_answer": "B",
        }
        assert AgentOutputConverter.validate_answer_schema(schema) is True

    def test_validate_valid_keyword_match(self):
        """유효한 keyword_match."""
        schema = {
            "type": "keyword_match",
            "keywords": ["learning", "data"],
            "correct_answer": None,
        }
        assert AgentOutputConverter.validate_answer_schema(schema) is True

    def test_validate_invalid_type(self):
        """유효하지 않은 type."""
        schema = {
            "type": "invalid_type",
            "keywords": None,
            "correct_answer": "B",
        }
        assert AgentOutputConverter.validate_answer_schema(schema) is False

    def test_validate_missing_type(self):
        """type 필드 누락."""
        schema = {
            "type": "",
            "keywords": None,
            "correct_answer": "B",
        }
        assert AgentOutputConverter.validate_answer_schema(schema) is False


class TestValidateGeneratedItem:
    """validate_generated_item() 테스트."""

    def test_validate_valid_multiple_choice(self):
        """유효한 객관식 문항."""
        item = {
            "id": "q1",
            "type": "multiple_choice",
            "stem": "What is AI?",
            "choices": ["A", "B", "C", "D"],
            "answer_schema": {
                "type": "exact_match",
                "keywords": None,
                "correct_answer": "B",
            },
            "difficulty": 3,
            "category": "AI",
        }
        assert AgentOutputConverter.validate_generated_item(item) is True

    def test_validate_valid_short_answer(self):
        """유효한 단답식 문항."""
        item = {
            "id": "q2",
            "type": "short_answer",
            "stem": "Explain AI",
            "answer_schema": {
                "type": "keyword_match",
                "keywords": ["intelligence", "machine"],
                "correct_answer": None,
            },
            "difficulty": 5,
            "category": "ML",
        }
        assert AgentOutputConverter.validate_generated_item(item) is True

    def test_validate_invalid_type(self):
        """유효하지 않은 question type."""
        item = {
            "id": "q1",
            "type": "invalid_type",
            "stem": "Test",
            "answer_schema": {"type": "exact_match", "correct_answer": "A"},
            "difficulty": 1,
            "category": "AI",
        }
        assert AgentOutputConverter.validate_generated_item(item) is False

    def test_validate_empty_stem(self):
        """비어있는 stem."""
        item = {
            "id": "q1",
            "type": "multiple_choice",
            "stem": "",
            "answer_schema": {"type": "exact_match", "correct_answer": "A"},
            "difficulty": 1,
            "category": "AI",
        }
        assert AgentOutputConverter.validate_generated_item(item) is False

    def test_validate_invalid_difficulty(self):
        """유효하지 않은 difficulty (범위 초과)."""
        item = {
            "id": "q1",
            "type": "multiple_choice",
            "stem": "Test",
            "answer_schema": {"type": "exact_match", "correct_answer": "A"},
            "difficulty": 15,  # > 10
            "category": "AI",
        }
        assert AgentOutputConverter.validate_generated_item(item) is False

    def test_validate_missing_category(self):
        """category 누락."""
        item = {
            "id": "q1",
            "type": "multiple_choice",
            "stem": "Test",
            "answer_schema": {"type": "exact_match", "correct_answer": "A"},
            "difficulty": 5,
            "category": "",  # Empty
        }
        assert AgentOutputConverter.validate_generated_item(item) is False


class TestRoundTrip:
    """End-to-end 변환 테스트."""

    def test_roundtrip_multiple_choice(self):
        """MC 문항: JSON → GeneratedItem."""
        content = """
        Final Answer: [
            {
                "question_id": "q1",
                "type": "multiple_choice",
                "stem": "What is artificial intelligence?",
                "choices": [
                    "A. Study of animals",
                    "B. Simulation of human intelligence in machines",
                    "C. Programming language",
                    "D. Computer hardware"
                ],
                "answer_schema": {"type": "exact_match"},
                "correct_answer": "B",
                "difficulty": 2,
                "category": "AI",
                "validation_score": 0.95
            }
        ]
        """

        # Parse
        questions_data = AgentOutputConverter.parse_final_answer_json(content)
        assert isinstance(questions_data, list)

        # Extract
        items = AgentOutputConverter.extract_items_from_questions(questions_data)
        assert len(items) == 1

        item = items[0]
        assert item["id"] == "q1"
        assert item["type"] == "multiple_choice"
        assert item["stem"] == "What is artificial intelligence?"
        assert len(item["choices"]) == 4
        assert item["answer_schema"]["type"] == "exact_match"
        assert item["answer_schema"]["correct_answer"] == "B"
        assert item["difficulty"] == 2
        assert item["category"] == "AI"

        # Validate
        assert AgentOutputConverter.validate_generated_item(item) is True

    def test_roundtrip_short_answer(self):
        """Short answer 문항: JSON → GeneratedItem."""
        content = """
        Final Answer: {
            "question_id": "q2",
            "type": "short_answer",
            "stem": "Explain the difference between AI and ML.",
            "answer_schema": {"type": "keyword_match"},
            "correct_keywords": ["artificial intelligence", "machine learning", "subset"],
            "difficulty": 4,
            "category": "AI",
            "validation_score": 0.88
        }
        """

        # Parse
        questions_data = AgentOutputConverter.parse_final_answer_json(content)

        # Extract
        items = AgentOutputConverter.extract_items_from_questions(questions_data)
        assert len(items) == 1

        item = items[0]
        assert item["type"] == "short_answer"
        assert item["answer_schema"]["type"] == "keyword_match"
        assert item["answer_schema"]["keywords"] == ["artificial intelligence", "machine learning", "subset"]
        assert item["answer_schema"]["correct_answer"] is None

        # Validate
        assert AgentOutputConverter.validate_generated_item(item) is True

    def test_roundtrip_multiple_questions(self):
        """여러 문항 변환."""
        content = """
        Final Answer: [
            {
                "question_id": "q1",
                "type": "multiple_choice",
                "stem": "Q1?",
                "choices": ["A", "B"],
                "answer_schema": "exact_match",
                "correct_answer": "A",
                "difficulty": 1,
                "category": "AI"
            },
            {
                "question_id": "q2",
                "type": "true_false",
                "stem": "Q2?",
                "answer_schema": "exact_match",
                "correct_answer": "True",
                "difficulty": 2,
                "category": "ML"
            },
            {
                "question_id": "q3",
                "type": "short_answer",
                "stem": "Q3?",
                "answer_schema": {"type": "keyword_match"},
                "correct_keywords": ["key1", "key2"],
                "difficulty": 3,
                "category": "DL"
            }
        ]
        """

        questions_data = AgentOutputConverter.parse_final_answer_json(content)
        items = AgentOutputConverter.extract_items_from_questions(questions_data)

        assert len(items) == 3
        assert all(AgentOutputConverter.validate_generated_item(item) for item in items)
        assert items[0]["type"] == "multiple_choice"
        assert items[1]["type"] == "true_false"
        assert items[2]["type"] == "short_answer"

    def test_parse_json_with_python_boolean_false(self):
        """Python False를 JSON false로 변환해서 파싱."""
        content = """
        Final Answer: {
            "question_id": "q1",
            "type": "multiple_choice",
            "stem": "Test?",
            "is_active": False
        }
        """
        result = AgentOutputConverter.parse_final_answer_json(content)
        assert result["is_active"] is False

    def test_parse_json_robustness_with_unicode(self):
        """Unicode 문자 포함 JSON 파싱."""
        content = """
        Final Answer: {
            "question_id": "q1",
            "type": "multiple_choice",
            "stem": "인공지능이란 무엇인가?",
            "choices": ["A. 기계학습", "B. 딥러닝", "C. 신경망"]
        }
        """
        result = AgentOutputConverter.parse_final_answer_json(content)
        assert "인공지능" in result["stem"]
        assert "기계학습" in result["choices"][0]
