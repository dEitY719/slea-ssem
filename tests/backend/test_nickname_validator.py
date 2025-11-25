"""
Tests for nickname validator.

REQ: REQ-B-A2-2, REQ-B-A2-4
"""

from src.backend.validators.nickname import NicknameValidator


class TestNicknameValidation:
    """REQ-B-A2-2: Nickname validation logic."""

    # === Happy Path Tests ===

    def test_valid_nickname_single_character(self) -> None:
        """Happy path: Single character nickname (length=1, new minimum)."""
        # TC-1: REQ-B-A2-Avail-2 - minimum length changed from 3 to 1
        is_valid, error = NicknameValidator.validate("a")
        assert is_valid is True
        assert error is None

    def test_valid_nickname_format(self) -> None:
        """Happy path: Valid nickname (1-30 chars, alphanumeric + underscore)."""
        # TC-2: Basic mixed characters (backward compatible)
        is_valid, error = NicknameValidator.validate("john_doe")
        assert is_valid is True
        assert error is None

        is_valid, error = NicknameValidator.validate("alice123")
        assert is_valid is True
        assert error is None

    def test_valid_nickname_korean(self) -> None:
        """Happy path: Korean characters allowed (REQ-B-A2-Avail-2)."""
        # TC-3: Unicode support - Korean characters
        is_valid, error = NicknameValidator.validate("김철수")
        assert is_valid is True
        assert error is None

        is_valid, error = NicknameValidator.validate("이영희")
        assert is_valid is True
        assert error is None

    def test_valid_nickname_unicode_emoji(self) -> None:
        """Happy path: Unicode emoji characters allowed (REQ-B-A2-Avail-2)."""
        # TC-4: Unicode support - emoji characters
        is_valid, error = NicknameValidator.validate("😊alice")
        assert is_valid is True
        assert error is None

        is_valid, error = NicknameValidator.validate("john🎉")
        assert is_valid is True
        assert error is None

    def test_valid_nickname_special_characters(self) -> None:
        """Happy path: Special characters allowed (REQ-B-A2-Avail-2)."""
        # TC-5: Special characters now allowed
        is_valid, error = NicknameValidator.validate("alice@home")
        assert is_valid is True
        assert error is None

        is_valid, error = NicknameValidator.validate("john#2024")
        assert is_valid is True
        assert error is None

        is_valid, error = NicknameValidator.validate("bob-doe")
        assert is_valid is True
        assert error is None

    # === Input Validation Tests ===

    def test_nickname_empty_string(self) -> None:
        """Input validation: Empty string rejected."""
        # TC-6: New minimum length validation (1 char)
        is_valid, error = NicknameValidator.validate("")
        assert is_valid is False
        assert "at least 1 character" in error

    def test_nickname_too_short(self) -> None:
        """Input validation: Nickname < 1 char is now invalid."""
        # TC-6 variant: Verify minimum length enforcement
        is_valid, error = NicknameValidator.validate("ab")
        assert is_valid is True  # 2 chars is valid (>= 1)
        assert error is None

    def test_nickname_too_long(self) -> None:
        """Input validation: Nickname > 30 chars."""
        # TC-7: Maximum length validation
        is_valid, error = NicknameValidator.validate("a" * 31)
        assert is_valid is False
        assert "at most 30 characters" in error

    # === Edge Cases ===

    def test_valid_nickname_max_length(self) -> None:
        """Edge case: Valid at maximum length (30 chars)."""
        # TC-11: Verify max length boundary
        is_valid, error = NicknameValidator.validate("a" * 30)
        assert is_valid is True
        assert error is None

    def test_valid_nickname_all_special_characters(self) -> None:
        """Edge case: Special-character-only nickname."""
        # TC-12: All special chars allowed
        is_valid, error = NicknameValidator.validate("@#$%")
        assert is_valid is True
        assert error is None

    def test_valid_nickname_mixed_unicode(self) -> None:
        """Edge case: Mixed Unicode characters (Korean, emoji, English)."""
        # TC-13: Mixed Unicode support
        is_valid, error = NicknameValidator.validate("alice_😊_名前")
        assert is_valid is True
        assert error is None

    # === Forbidden Words Tests ===

    def test_nickname_with_forbidden_words_exact_match(self) -> None:
        """REQ-B-A2-Avail-4: Forbidden words rejected (exact match)."""
        # TC-8: Exact match forbidden words
        is_valid, error = NicknameValidator.validate("admin")
        assert is_valid is False
        assert "prohibited word" in error

        is_valid, error = NicknameValidator.validate("system")
        assert is_valid is False
        assert "prohibited word" in error

        is_valid, error = NicknameValidator.validate("root")
        assert is_valid is False
        assert "prohibited word" in error

    def test_nickname_with_forbidden_words_prefix(self) -> None:
        """REQ-B-A2-Avail-4: Forbidden words rejected (prefix match)."""
        # TC-9: Prefix match forbidden words
        # Test with numbers/underscores added
        is_valid, error = NicknameValidator.validate("admin123")
        assert is_valid is False
        assert "prohibited word" in error

        is_valid, error = NicknameValidator.validate("system_user")
        assert is_valid is False
        assert "prohibited word" in error

    def test_nickname_with_forbidden_words_and_unicode(self) -> None:
        """REQ-B-A2-Avail-4: Forbidden words rejected even with Unicode suffix."""
        # TC-10: Forbidden word with Unicode characters
        is_valid, error = NicknameValidator.validate("admin_😊")
        assert is_valid is False
        assert "prohibited word" in error

        is_valid, error = NicknameValidator.validate("system🎉")
        assert is_valid is False
        assert "prohibited word" in error

    # === Helper Method Tests ===

    def test_valid_nickname_with_numbers_and_underscore(self) -> None:
        """Happy path: Valid format with mixed characters."""
        # Backward compatibility: existing valid nicknames still work
        is_valid, error = NicknameValidator.validate("john_doe_123")
        assert is_valid is True
        assert error is None

    def test_get_validation_error_message(self) -> None:
        """REQ-B-A2-Avail-4: Get error message helper."""
        # TC-14: Error helper method works correctly

        # Invalid: empty string
        error_msg = NicknameValidator.get_validation_error("")
        assert error_msg is not None
        assert "at least 1 character" in error_msg

        # Invalid: forbidden word
        error_msg = NicknameValidator.get_validation_error("admin")
        assert error_msg is not None
        assert "prohibited word" in error_msg

        # Valid nickname
        error_msg = NicknameValidator.get_validation_error("john_doe")
        assert error_msg is None
