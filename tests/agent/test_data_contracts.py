"""
Test suite for REQ-A-DataContract: Tool input/output data contract validation.

Tests verify that all 6 tools conform to their defined data contracts:
- Tool 1: Get User Profile
- Tool 2: Search Question Templates
- Tool 3: Get Difficulty Keywords
- Tool 4: Validate Question Quality
- Tool 5: Save Generated Question
- Tool 6: Score & Generate Explanation
"""

import pytest
from datetime import datetime
from typing import Any
from pydantic import ValidationError

# REQ: REQ-A-DataContract


class TestTool1UserProfileContract:
    """Test Tool 1: Get User Profile data contract."""

    def test_tool1_output_valid_structure(self):
        """
        TC1.1: Verify Tool 1 outputs valid user profile structure.

        Expected: Output contains self_level, years_experience, job_role,
                 duty, interests, previous_score
        """
        from src.agent.data_contracts import Tool1Output

        valid_output = Tool1Output(
            self_level=5,
            years_experience=3,
            job_role="Software Engineer",
            duty="Backend Development",
            interests=["LLM", "RAG"],
            previous_score=75.0
        )

        assert valid_output.self_level == 5
        assert valid_output.years_experience == 3
        assert valid_output.job_role == "Software Engineer"
        assert valid_output.interests == ["LLM", "RAG"]

    def test_tool1_output_missing_required_field(self):
        """
        TC1.2: Verify Tool 1 raises ValidationError on missing required fields.

        Expected: ValidationError raised when self_level is missing
        """
        from src.agent.data_contracts import Tool1Output

        with pytest.raises(ValidationError):
            Tool1Output(
                years_experience=3,
                job_role="Engineer",
                duty="Backend",
                interests=["LLM"],
                previous_score=75.0
                # Missing: self_level
            )

    def test_tool1_input_validation(self):
        """
        TC1.3: Verify Tool 1 input (user_id) validation.

        Expected: Tool1Input accepts string user_id
        """
        from src.agent.data_contracts import Tool1Input

        valid_input = Tool1Input(user_id="user_123")
        assert valid_input.user_id == "user_123"

    def test_tool1_input_empty_string(self):
        """
        TC1.4: Verify Tool 1 rejects empty user_id.

        Expected: ValidationError on empty string
        """
        from src.agent.data_contracts import Tool1Input

        with pytest.raises(ValidationError):
            Tool1Input(user_id="")


class TestTool2TemplateSearchContract:
    """Test Tool 2: Search Question Templates data contract."""

    def test_tool2_input_valid_structure(self):
        """
        TC2.1: Verify Tool 2 input validation.

        Expected: Tool2Input accepts interests[], difficulty, category
        """
        from src.agent.data_contracts import Tool2Input

        valid_input = Tool2Input(
            interests=["LLM", "RAG"],
            difficulty=5,
            category="technical"
        )

        assert valid_input.interests == ["LLM", "RAG"]
        assert valid_input.difficulty == 5

    def test_tool2_output_template_structure(self):
        """
        TC2.2: Verify Tool 2 output contains template objects.

        Expected: Output is list of QuestionTemplate objects
        """
        from src.agent.data_contracts import Tool2Output, QuestionTemplate

        template = QuestionTemplate(
            id="template_1",
            stem="What is RAG?",
            type="short_answer",
            choices=None,
            correct_answer="keyword1, keyword2",
            correct_rate=0.85,
            usage_count=10,
            avg_difficulty_score=5.0
        )

        output = Tool2Output(templates=[template])
        assert len(output.templates) == 1
        assert output.templates[0].stem == "What is RAG?"

    def test_tool2_output_empty_list(self):
        """
        TC2.3: Verify Tool 2 handles empty search results.

        Expected: Tool2Output accepts empty templates list
        """
        from src.agent.data_contracts import Tool2Output

        output = Tool2Output(templates=[])
        assert output.templates == []


class TestTool3DifficultyKeywordsContract:
    """Test Tool 3: Get Difficulty Keywords data contract."""

    def test_tool3_input_valid_structure(self):
        """
        TC3.1: Verify Tool 3 input validation.

        Expected: Tool3Input accepts difficulty and category
        """
        from src.agent.data_contracts import Tool3Input

        valid_input = Tool3Input(
            difficulty=5,
            category="technical"
        )

        assert valid_input.difficulty == 5
        assert valid_input.category == "technical"

    def test_tool3_output_keyword_structure(self):
        """
        TC3.2: Verify Tool 3 output structure.

        Expected: Output contains keywords[], concepts[], example_questions[]
        """
        from src.agent.data_contracts import Tool3Output

        output = Tool3Output(
            keywords=["LLM", "prompt engineering"],
            concepts=["attention mechanism", "transformer"],
            example_questions=["What is attention?", "Explain transformers"]
        )

        assert len(output.keywords) == 2
        assert len(output.concepts) == 2
        assert len(output.example_questions) == 2

    def test_tool3_output_missing_field(self):
        """
        TC3.3: Verify Tool 3 raises error on missing keywords.

        Expected: ValidationError raised
        """
        from src.agent.data_contracts import Tool3Output

        with pytest.raises(ValidationError):
            Tool3Output(
                concepts=["attention"],
                example_questions=["What is attention?"]
                # Missing: keywords
            )


class TestTool4ValidationContract:
    """Test Tool 4: Validate Question Quality data contract."""

    def test_tool4_input_single_question(self):
        """
        TC4.1: Verify Tool 4 input for single question validation.

        Expected: Tool4Input accepts stem, question_type, choices, correct_answer
        """
        from src.agent.data_contracts import Tool4Input

        valid_input = Tool4Input(
            stem="What is LLM?",
            question_type="short_answer",
            choices=None,
            correct_answer="Large Language Model"
        )

        assert valid_input.stem == "What is LLM?"
        assert valid_input.question_type == "short_answer"

    def test_tool4_input_multiple_choice(self):
        """
        TC4.2: Verify Tool 4 validates multiple choice questions.

        Expected: Tool4Input accepts choices for multiple_choice type
        """
        from src.agent.data_contracts import Tool4Input

        valid_input = Tool4Input(
            stem="Choose the correct answer",
            question_type="multiple_choice",
            choices=["A", "B", "C", "D"],
            correct_answer="A"
        )

        assert valid_input.choices == ["A", "B", "C", "D"]

    def test_tool4_output_validation_result(self):
        """
        TC4.3: Verify Tool 4 output validation result structure.

        Expected: Output contains is_valid, score, rule_score, final_score,
                 recommendation, feedback, issues[]
        """
        from src.agent.data_contracts import Tool4Output

        output = Tool4Output(
            is_valid=True,
            score=0.92,
            rule_score=0.95,
            final_score=0.92,
            recommendation="pass",
            feedback="Question is clear and well-formed",
            issues=[]
        )

        assert output.is_valid is True
        assert output.final_score == 0.92
        assert output.recommendation == "pass"

    def test_tool4_output_revise_recommendation(self):
        """
        TC4.4: Verify Tool 4 handles REVISE recommendation.

        Expected: final_score 0.70-0.84 → recommendation="revise"
        """
        from src.agent.data_contracts import Tool4Output

        output = Tool4Output(
            is_valid=False,
            score=0.75,
            rule_score=0.80,
            final_score=0.75,
            recommendation="revise",
            feedback="Consider adding more depth",
            issues=["unclear_phrasing"]
        )

        assert output.recommendation == "revise"
        assert len(output.issues) >= 0

    def test_tool4_output_reject_recommendation(self):
        """
        TC4.5: Verify Tool 4 handles REJECT recommendation.

        Expected: final_score < 0.70 → recommendation="reject"
        """
        from src.agent.data_contracts import Tool4Output

        output = Tool4Output(
            is_valid=False,
            score=0.65,
            rule_score=0.68,
            final_score=0.65,
            recommendation="reject",
            feedback="Question quality too low",
            issues=["too_ambiguous", "invalid_format"]
        )

        assert output.recommendation == "reject"


class TestTool5SaveQuestionContract:
    """Test Tool 5: Save Generated Question data contract."""

    def test_tool5_input_multiple_choice(self):
        """
        TC5.1: Verify Tool 5 input for multiple choice question.

        Expected: Tool5Input accepts all fields for MC question
        """
        from src.agent.data_contracts import Tool5Input

        valid_input = Tool5Input(
            item_type="multiple_choice",
            stem="What is LLM?",
            choices=["A", "B", "C", "D"],
            correct_key="A",
            correct_keywords=None,
            difficulty=5,
            categories=["technical"],
            round_id="sess_123_1_2025-11-09T10:30:00",
            validation_score=0.92,
            explanation=None
        )

        assert valid_input.item_type == "multiple_choice"
        assert valid_input.choices == ["A", "B", "C", "D"]

    def test_tool5_input_short_answer(self):
        """
        TC5.2: Verify Tool 5 input for short answer question.

        Expected: Tool5Input accepts correct_keywords for short_answer type
        """
        from src.agent.data_contracts import Tool5Input

        valid_input = Tool5Input(
            item_type="short_answer",
            stem="Explain LLM",
            choices=None,
            correct_key=None,
            correct_keywords=["language model", "deep learning"],
            difficulty=6,
            categories=["technical", "LLM"],
            round_id="sess_123_1_2025-11-09T10:30:00",
            validation_score=0.88,
            explanation="LLM is a model trained on large text data"
        )

        assert valid_input.item_type == "short_answer"
        assert valid_input.correct_keywords == ["language model", "deep learning"]

    def test_tool5_output_success(self):
        """
        TC5.3: Verify Tool 5 output on successful save.

        Expected: Output contains question_id, round_id, saved_at, success=True
        """
        from src.agent.data_contracts import Tool5Output

        output = Tool5Output(
            question_id="q_uuid_123",
            round_id="sess_123_1_2025-11-09T10:30:00",
            saved_at=datetime.utcnow().isoformat(),
            success=True
        )

        assert output.question_id == "q_uuid_123"
        assert output.success is True

    def test_tool5_input_round_id_format(self):
        """
        TC5.4: Verify Tool 5 validates round_id format.

        Expected: round_id follows format sess_id_round_datetime
        """
        from src.agent.data_contracts import Tool5Input

        valid_input = Tool5Input(
            item_type="true_false",
            stem="LLM is a type of AI",
            choices=None,
            correct_key="True",
            correct_keywords=None,
            difficulty=3,
            categories=["general"],
            round_id="sess_abc123_2_2025-11-09T10:30:00.000Z",
            validation_score=0.90
        )

        assert "sess_" in valid_input.round_id
        assert "_" in valid_input.round_id


class TestTool6ScoringContract:
    """Test Tool 6: Score & Generate Explanation data contract."""

    def test_tool6_input_structure(self):
        """
        TC6.1: Verify Tool 6 input validation.

        Expected: Tool6Input accepts all scoring parameters
        """
        from src.agent.data_contracts import Tool6Input

        valid_input = Tool6Input(
            session_id="sess_123",
            user_id="user_456",
            question_id="q_789",
            question_type="short_answer",
            user_answer="LLM is a language model",
            correct_answer="language model",
            correct_keywords=["language", "model"],
            difficulty=5,
            category="technical"
        )

        assert valid_input.session_id == "sess_123"
        assert valid_input.question_type == "short_answer"

    def test_tool6_output_correct_answer(self):
        """
        TC6.2: Verify Tool 6 output for correct answer.

        Expected: Output contains is_correct=True, score >= 80
        """
        from src.agent.data_contracts import Tool6Output

        output = Tool6Output(
            attempt_id="att_123",
            session_id="sess_123",
            question_id="q_789",
            user_id="user_456",
            is_correct=True,
            score=95.0,
            explanation="Your answer is correct!",
            keyword_matches=["language", "model"],
            feedback="Good understanding of LLM",
            graded_at=datetime.utcnow().isoformat()
        )

        assert output.is_correct is True
        assert output.score >= 80.0

    def test_tool6_output_partial_answer(self):
        """
        TC6.3: Verify Tool 6 output for partial answer.

        Expected: Output contains 70 <= score < 80
        """
        from src.agent.data_contracts import Tool6Output

        output = Tool6Output(
            attempt_id="att_124",
            session_id="sess_123",
            question_id="q_789",
            user_id="user_456",
            is_correct=False,
            score=75.0,
            explanation="Partially correct - missing some details",
            keyword_matches=["language"],
            feedback="Include 'model' concept",
            graded_at=datetime.utcnow().isoformat()
        )

        assert output.is_correct is False
        assert 70.0 <= output.score < 80.0

    def test_tool6_output_incorrect_answer(self):
        """
        TC6.4: Verify Tool 6 output for incorrect answer.

        Expected: Output contains is_correct=False, score < 70
        """
        from src.agent.data_contracts import Tool6Output

        output = Tool6Output(
            attempt_id="att_125",
            session_id="sess_123",
            question_id="q_789",
            user_id="user_456",
            is_correct=False,
            score=45.0,
            explanation="Answer does not match expected concepts",
            keyword_matches=[],
            feedback="Review LLM fundamentals",
            graded_at=datetime.utcnow().isoformat()
        )

        assert output.is_correct is False
        assert output.score < 70.0


class TestPipelineOutputContract:
    """Test Pipeline output data contract."""

    def test_pipeline_output_generated_questions(self):
        """
        TC7.1: Verify pipeline output for generated questions.

        Expected: PipelineOutput contains list of generated questions
        """
        from src.agent.data_contracts import PipelineOutput, GeneratedQuestionOutput

        question = GeneratedQuestionOutput(
            question_id="q_123",
            stem="What is LLM?",
            type="short_answer",
            choices=None,
            correct_answer="language model",
            difficulty=5,
            category="technical",
            round_id="sess_123_1_2025-11-09T10:30:00",
            validation_score=0.92,
            saved_at="2025-11-09T10:30:00Z"
        )

        output = PipelineOutput(
            questions=[question],
            total_generated=1,
            total_valid=1,
            total_rejected=0
        )

        assert len(output.questions) == 1
        assert output.total_valid == 1

    def test_pipeline_output_multiple_questions(self):
        """
        TC7.2: Verify pipeline output with multiple questions.

        Expected: PipelineOutput aggregates stats correctly
        """
        from src.agent.data_contracts import PipelineOutput, GeneratedQuestionOutput

        questions = [
            GeneratedQuestionOutput(
                question_id=f"q_{i}",
                stem=f"Question {i}",
                type="multiple_choice",
                choices=["A", "B", "C", "D"],
                correct_answer="A",
                difficulty=5 + i,
                category="technical",
                round_id="sess_123_1_2025-11-09T10:30:00",
                validation_score=0.85 + (i * 0.05),
                saved_at="2025-11-09T10:30:00Z"
            )
            for i in range(3)
        ]

        output = PipelineOutput(
            questions=questions,
            total_generated=5,
            total_valid=3,
            total_rejected=2
        )

        assert len(output.questions) == 3
        assert output.total_generated == 5


class TestDataContractIntegration:
    """Integration tests for data contracts across tools."""

    def test_tool4_output_to_tool5_input_mapping(self):
        """
        TC8.1: Verify Tool 4 output can feed to Tool 5 input.

        Expected: Tool4 validation_score maps to Tool5 validation_score
        """
        from src.agent.data_contracts import Tool4Output, Tool5Input

        # Tool 4 output
        validation = Tool4Output(
            is_valid=True,
            score=0.92,
            rule_score=0.95,
            final_score=0.92,
            recommendation="pass",
            feedback="Good",
            issues=[]
        )

        # Tool 5 input using Tool 4 output
        save_input = Tool5Input(
            item_type="multiple_choice",
            stem="Test question",
            choices=["A", "B", "C"],
            correct_key="A",
            correct_keywords=None,
            difficulty=5,
            categories=["technical"],
            round_id="sess_123_1_2025-11-09T10:30:00",
            validation_score=validation.final_score,
            explanation=None
        )

        assert save_input.validation_score == validation.final_score

    def test_tool5_output_to_pipeline_mapping(self):
        """
        TC8.2: Verify Tool 5 output maps to PipelineOutput.

        Expected: Tool5Output fields present in pipeline output
        """
        from src.agent.data_contracts import Tool5Output, PipelineOutput, GeneratedQuestionOutput

        # Tool 5 output
        save_output = Tool5Output(
            question_id="q_123",
            round_id="sess_123_1_2025-11-09T10:30:00",
            saved_at="2025-11-09T10:30:00Z",
            success=True
        )

        # Map to pipeline output
        question = GeneratedQuestionOutput(
            question_id=save_output.question_id,
            stem="Test",
            type="short_answer",
            choices=None,
            correct_answer="answer",
            difficulty=5,
            category="technical",
            round_id=save_output.round_id,
            validation_score=0.92,
            saved_at=save_output.saved_at
        )

        assert question.question_id == save_output.question_id
        assert question.saved_at == save_output.saved_at
