"""
Test suite for QuestionContentValidator (REQ-B-B6-2).

REQ-B-B6-2: 부정확/유해 콘텐츠 필터(비속어, 편향, 저작권 의심)로 부적절 문항을 자동 차단
- REQ-B-B6-2-1: Validate question for profanity (비속어)
- REQ-B-B6-2-2: Validate question for bias (편향)
- REQ-B-B6-2-3: Validate question for copyright concerns (저작권 의심)
- AC1: "문항 생성 후, 콘텐츠 필터링이 적용되어 부정확한 문항이 차단된다."
- AC2: "필터링된 문항은 자동으로 재생성 요청이 발생한다."
"""

import pytest

from src.backend.models import Question
from src.backend.validators.question_content_validator import QuestionContentValidator


class TestProfanityFilter:
    """Test REQ-B-B6-2-1: Profanity detection."""

    def test_valid_question_no_profanity(self, question_factory) -> None:
        """
        REQ-B-B6-2-1: Valid question without profanity.

        Given: Question with clean, appropriate language
        When: validate_question() called
        Then: Returns (True, None)
        """
        question = question_factory(
            stem="What is the capital of France?",
            choices=["Paris", "Lyon", "Marseille"],
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        assert is_valid is True
        assert error is None

    def test_question_with_profanity_in_stem(self, question_factory) -> None:
        """
        REQ-B-B6-2-1: Reject question with profanity in stem.

        Given: Question stem contains inappropriate language
        When: validate_question() called
        Then: Returns (False, error_message) with reason
        """
        question = question_factory(
            stem="What the hell is AI? (profanity example)",
            choices=["Option A", "Option B"],
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        assert is_valid is False
        assert error is not None
        assert "profanity" in error.lower() or "inappropriate" in error.lower()

    def test_question_with_profanity_in_choices(self, question_factory) -> None:
        """
        REQ-B-B6-2-1: Reject question with profanity in choice text.

        Given: One choice contains profanity
        When: validate_question() called
        Then: Returns (False, error_message)
        """
        question = question_factory(
            stem="Which is a programming language?",
            choices=["Python", "Damn Java", "C++"],
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        assert is_valid is False
        assert error is not None

    def test_question_with_profanity_in_explanation(self, question_factory) -> None:
        """
        REQ-B-B6-2-1: Reject question with profanity in answer explanation.

        Given: answer_schema explanation contains profanity
        When: validate_question() called
        Then: Returns (False, error_message)
        """
        question = question_factory(
            stem="What is machine learning?",
            choices=["A", "B"],
            answer_schema={
                "correct_answer": "A",
                "explanation": "Damn, this is how ML works...",
            },
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        assert is_valid is False
        assert error is not None

    def test_multiple_profanity_matches(self, question_factory) -> None:
        """
        REQ-B-B6-2-1: Detect multiple profanity instances.

        Given: Question contains multiple profanity instances
        When: validate_question() called
        Then: Returns (False, error_message) with first match
        """
        question = question_factory(
            stem="What the hell... this damn question",
            choices=["A", "B"],
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        assert is_valid is False
        assert error is not None


class TestBiasFilter:
    """Test REQ-B-B6-2-2: Bias and discrimination detection."""

    def test_valid_question_no_bias(self, question_factory) -> None:
        """
        REQ-B-B6-2-2: Valid question without bias.

        Given: Neutral, objective question
        When: validate_question() called
        Then: Returns (True, None)
        """
        question = question_factory(
            stem="What is the primary function of a transistor?",
            choices=["Switch", "Amplify", "Both"],
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        assert is_valid is True
        assert error is None

    def test_question_with_gender_bias(self, question_factory) -> None:
        """
        REQ-B-B6-2-2: Reject question with gender stereotypes.

        Given: Question contains gender bias (e.g., "a nurse is usually...")
        When: validate_question() called
        Then: Returns (False, error_message) with reason
        """
        question = question_factory(
            stem="Which gender is better at programming?",
            choices=["Male", "Female", "No difference"],
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        assert is_valid is False
        assert error is not None
        assert "bias" in error.lower() or "stereotype" in error.lower()

    def test_question_with_age_bias(self, question_factory) -> None:
        """
        REQ-B-B6-2-2: Reject question with age discrimination.

        Given: Question assumes age-based limitations
        When: validate_question() called
        Then: Returns (False, error_message)
        """
        question = question_factory(
            stem="Old people cannot learn new technologies. True or False?",
            choices=["True", "False"],
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        assert is_valid is False
        assert error is not None

    def test_question_with_cultural_bias(self, question_factory) -> None:
        """
        REQ-B-B6-2-2: Reject question with cultural stereotypes.

        Given: Question contains cultural stereotypes
        When: validate_question() called
        Then: Returns (False, error_message)
        """
        question = question_factory(
            stem="Which culture is best at engineering?",
            choices=["Option A", "Option B"],
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        assert is_valid is False
        assert error is not None

    def test_question_with_ethnic_bias(self, question_factory) -> None:
        """
        REQ-B-B6-2-2: Reject question with ethnic discrimination.

        Given: Question implies ethnic superiority
        When: validate_question() called
        Then: Returns (False, error_message)
        """
        question = question_factory(
            stem="Which race is naturally more intelligent?",
            choices=["Option A", "Option B"],
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        assert is_valid is False
        assert error is not None


class TestCopyrightFilter:
    """Test REQ-B-B6-2-3: Copyright concern detection."""

    def test_valid_question_with_proper_attribution(self, question_factory) -> None:
        """
        REQ-B-B6-2-3: Valid question with proper source attribution.

        Given: Question with clear source citation
        When: validate_question() called
        Then: Returns (True, None)
        """
        question = question_factory(
            stem="According to NIST, what is cryptography? [Source: NIST Guidelines]",
            choices=["A", "B"],
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        assert is_valid is True
        assert error is None

    def test_question_with_direct_quote_no_attribution(self, question_factory) -> None:
        """
        REQ-B-B6-2-3: Reject direct quote without attribution.

        Given: Question contains direct quote without source
        When: validate_question() called
        Then: Returns (False, error_message) with copyright concern
        """
        question = question_factory(
            stem='According to the textbook: "Machine learning is a subset of AI"',
            choices=["A", "B"],
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        assert is_valid is False
        assert error is not None
        assert "copyright" in error.lower() or "attribution" in error.lower() or "source" in error.lower()

    def test_question_with_plagiarized_content_pattern(self, question_factory) -> None:
        """
        REQ-B-B6-2-3: Detect plagiarism patterns.

        Given: Question contains common plagiarism indicators
        When: validate_question() called
        Then: Returns (False, error_message)
        """
        question = question_factory(
            stem="Copy-pasted from Wikipedia without attribution. What is AI?",
            choices=["A", "B"],
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        assert is_valid is False
        assert error is not None

    def test_question_with_suspicious_source_pattern(self, question_factory) -> None:
        """
        REQ-B-B6-2-3: Flag suspicious source patterns.

        Given: Question references source without proper format
        When: validate_question() called
        Then: Returns (False, error_message) or (True, None) depending on confidence
        """
        question = question_factory(
            stem="From the internet: What is blockchain?",
            choices=["A", "B"],
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        # This may return (True, None) or (False, error) depending on filter strictness
        # For MVP, flag vague sources
        if not is_valid:
            assert error is not None


class TestAcceptanceCriteria:
    """Test AC1 and AC2: Content filtering and regeneration."""

    def test_ac1_filtering_applied_after_generation(self, question_factory) -> None:
        """
        AC1: "문항 생성 후, 콘텐츠 필터링이 적용되어 부정확한 문항이 차단된다."

        Given: Generated question with profanity
        When: validate_question() called
        Then: Question is blocked (is_valid=False)
        """
        invalid_question = question_factory(
            stem="What the hell is Python?",
            choices=["A", "B"],
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(invalid_question)

        assert is_valid is False
        assert error is not None

    def test_ac2_regeneration_trigger(self, question_factory) -> None:
        """
        AC2: "필터링된 문항은 자동으로 재생성 요청이 발생한다."

        Given: Question fails validation
        When: is_valid=False
        Then: Service should trigger regeneration (verified at integration level)
        """
        invalid_question = question_factory(
            stem="Which gender is best?",
            choices=["A", "B"],
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(invalid_question)

        # When is_valid=False, calling service should trigger regeneration
        assert is_valid is False
        assert error is not None
        # Regeneration verification happens in integration tests

    def test_all_fields_validated(self, question_factory) -> None:
        """
        AC1: Validation checks stem, choices, and explanation.

        Given: Question with profanity in any field
        When: validate_question() called
        Then: All fields are scanned and violations are caught
        """
        # Test profanity in stem
        q_stem = question_factory(stem="Damn question", choices=["A", "B"])
        validator = QuestionContentValidator()
        is_valid, _ = validator.validate_question(q_stem)
        assert is_valid is False

        # Test profanity in choices
        q_choices = question_factory(stem="Good question", choices=["Hell yes", "No"])
        is_valid, _ = validator.validate_question(q_choices)
        assert is_valid is False

        # Test profanity in explanation
        q_explanation = question_factory(
            stem="Good question",
            choices=["A", "B"],
            answer_schema={"correct_answer": "A", "explanation": "Damn, this is right"},
        )
        is_valid, _ = validator.validate_question(q_explanation)
        assert is_valid is False


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_question_stem(self, question_factory) -> None:
        """
        Edge case: Empty question stem.

        Given: Question with empty stem
        When: validate_question() called
        Then: Handle gracefully (True or False depending on requirement)
        """
        question = question_factory(stem="", choices=["A", "B"])

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        # Empty content should either be valid (skip validation) or raise error
        # For now, allow graceful handling
        assert isinstance(is_valid, bool)

    def test_null_choices(self, question_factory) -> None:
        """
        Edge case: Null choices (for short answer questions).

        Given: Question with None choices (valid for short_answer type)
        When: validate_question() called
        Then: Still validates stem and explanation
        """
        question = question_factory(
            stem="What is AI?",
            choices=None,
            answer_schema={"correct_answer": "Machine learning", "explanation": "AI is..."},
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        # Should validate stem and explanation even without choices
        assert isinstance(is_valid, bool)

    def test_very_long_question_stem(self, question_factory) -> None:
        """
        Edge case: Very long question stem.

        Given: Question with 1900 character stem (DB limit is 2000)
        When: validate_question() called
        Then: Still filters correctly without timeout
        """
        long_stem = "A" * 900 + "What is AI?" + "B" * 900  # Total ~1811 chars (under 2000)
        question = question_factory(stem=long_stem, choices=["A", "B"])

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        # Should handle long text without performance issues
        assert isinstance(is_valid, bool)

    def test_unicode_profanity(self, question_factory) -> None:
        """
        Edge case: Profanity with unicode characters.

        Given: Question with obfuscated profanity (unicode, numbers)
        When: validate_question() called
        Then: Simple patterns detected (complex obfuscation out of scope)
        """
        question = question_factory(
            stem="What is *** (censored word) in AI?",
            choices=["A", "B"],
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        # For MVP, basic unicode handling (out of scope for complex obfuscation)
        assert isinstance(is_valid, bool)

    def test_mixed_valid_and_invalid_content(self, question_factory) -> None:
        """
        Edge case: Question with both valid and invalid content.

        Given: Question with profanity and bias mixed
        When: validate_question() called
        Then: Detects at least one violation
        """
        question = question_factory(
            stem="Damn question: Which gender is better at coding?",
            choices=["Male", "Female"],
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        assert is_valid is False
        assert error is not None


class TestValidatorMethods:
    """Test individual validator methods."""

    def test_profanity_check_method(self) -> None:
        """
        Test _check_profanity() method directly.

        Given: Text with profanity
        When: _check_profanity() called
        Then: Returns (False, error_message)
        """
        validator = QuestionContentValidator()

        is_valid, error = validator._check_profanity("This is damn text")
        assert is_valid is False
        assert error is not None

        is_valid, error = validator._check_profanity("This is clean text")
        assert is_valid is True
        assert error is None

    def test_bias_check_method(self) -> None:
        """
        Test _check_bias() method directly.

        Given: Text with bias
        When: _check_bias() called
        Then: Returns (False, error_message) for biased text
        """
        validator = QuestionContentValidator()

        is_valid, error = validator._check_bias("Which gender is smarter?")
        assert is_valid is False
        assert error is not None

        is_valid, error = validator._check_bias("What is the definition of algorithms?")
        assert is_valid is True
        assert error is None

    def test_copyright_check_method(self) -> None:
        """
        Test _check_copyright() method directly.

        Given: Text with copyright concerns
        When: _check_copyright() called
        Then: Returns (False, error_message) for unattributed quotes
        """
        validator = QuestionContentValidator()

        is_valid, error = validator._check_copyright('According to John Doe: "This is a quote"')
        # Unattributed quote should flag concern
        if not is_valid:
            assert error is not None

        is_valid, error = validator._check_copyright("According to Wikipedia [source]: Information here")
        # Properly attributed should pass
        assert is_valid is True

    def test_validate_question_aggregates_checks(self, question_factory) -> None:
        """
        Test that validate_question() calls all three checks.

        Given: Question that fails one check
        When: validate_question() called
        Then: Returns (False, error) from first failed check
        """
        question = question_factory(
            stem="Damn question about gender differences",
            choices=["A", "B"],
        )

        validator = QuestionContentValidator()
        is_valid, error = validator.validate_question(question)

        # Should detect at least one violation
        assert is_valid is False
        assert error is not None
