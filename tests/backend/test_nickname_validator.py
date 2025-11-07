"""
Tests for nickname validator.

REQ: REQ-B-A2-2, REQ-B-A2-4
"""

from src.backend.validators.nickname import NicknameValidator


class TestNicknameValidation:
    """REQ-B-A2-2: Nickname validation logic."""

    def test_valid_nickname_format(self) -> None:
        """Happy path: Valid nickname (3-30 chars, alphanumeric + underscore)."""
        is_valid, error = NicknameValidator.validate("john_doe")
        assert is_valid is True
        assert error is None

        is_valid, error = NicknameValidator.validate("alice123")
        assert is_valid is True
        assert error is None

    def test_nickname_too_short(self) -> None:
        """Input validation: Nickname < 3 chars."""
        is_valid, error = NicknameValidator.validate("ab")
        assert is_valid is False
        assert "at least 3 characters" in error

    def test_nickname_too_long(self) -> None:
        """Input validation: Nickname > 30 chars."""
        is_valid, error = NicknameValidator.validate("a" * 31)
        assert is_valid is False
        assert "at most 30 characters" in error

    def test_nickname_invalid_characters(self) -> None:
        """Input validation: Special characters not allowed."""
        # Test with @ symbol
        is_valid, error = NicknameValidator.validate("alice@domain")
        assert is_valid is False
        assert "letters, numbers, and underscores" in error

        # Test with hyphen
        is_valid, error = NicknameValidator.validate("alice-name")
        assert is_valid is False
        assert "letters, numbers, and underscores" in error

        # Test with space
        is_valid, error = NicknameValidator.validate("alice name")
        assert is_valid is False
        assert "letters, numbers, and underscores" in error

    def test_nickname_with_forbidden_words(self) -> None:
        """REQ-B-A2-4: Forbidden words filter."""
        # Test exact match
        is_valid, error = NicknameValidator.validate("admin")
        assert is_valid is False
        assert "prohibited word" in error

        is_valid, error = NicknameValidator.validate("system")
        assert is_valid is False
        assert "prohibited word" in error

        # Test with numbers/underscores added
        is_valid, error = NicknameValidator.validate("admin123")
        assert is_valid is False
        assert "prohibited word" in error

        is_valid, error = NicknameValidator.validate("system_user")
        assert is_valid is False
        assert "prohibited word" in error

    def test_valid_nickname_with_numbers_and_underscore(self) -> None:
        """Happy path: Valid format with mixed characters."""
        is_valid, error = NicknameValidator.validate("john_doe_123")
        assert is_valid is True
        assert error is None

    def test_get_validation_error_message(self) -> None:
        """REQ-B-A2-4: Get error message helper."""
        # Invalid nickname
        error_msg = NicknameValidator.get_validation_error("ab")
        assert error_msg is not None
        assert "at least 3 characters" in error_msg

        # Valid nickname
        error_msg = NicknameValidator.get_validation_error("john_doe")
        assert error_msg is None
