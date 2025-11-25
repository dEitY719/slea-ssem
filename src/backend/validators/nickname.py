"""
Nickname validation logic.

REQ: REQ-B-A2-2, REQ-B-A2-4
"""


class NicknameValidator:
    """
    Validate nicknames with format and forbidden word checks.

    REQ-B-A2-2: Nickname validation (length, special chars, forbidden words)
    REQ-B-A2-4: Forbidden word filter with clear rejection reason
    """

    MIN_LENGTH = 1
    MAX_LENGTH = 30

    # Forbidden words list (금칙어)
    FORBIDDEN_WORDS = {
        "admin",
        "administrator",
        "system",
        "root",
        "moderator",
        "mod",
        "staff",
        "support",
        "bot",
        "service",
        "account",
        "user",
        "test",
        "temp",
        "guest",
        "anonymous",
    }

    @classmethod
    def validate(cls, nickname: str) -> tuple[bool, str | None]:
        """
        Validate nickname format and content.

        Args:
            nickname: Nickname to validate

        Returns:
            Tuple of (is_valid, error_message)
                - (True, None) if valid
                - (False, error_message) if invalid

        REQ: REQ-B-A2-2

        """
        # Check length
        if len(nickname) < cls.MIN_LENGTH:
            return False, f"Nickname must be at least {cls.MIN_LENGTH} characters long."

        if len(nickname) > cls.MAX_LENGTH:
            return False, f"Nickname must be at most {cls.MAX_LENGTH} characters long."

        # REQ-B-A2-Avail-2: Allow all Unicode characters, Korean, special chars, etc.
        # No character type restrictions beyond length + forbidden words

        # Check forbidden words (case-insensitive)
        nickname_lower = nickname.lower()
        if nickname_lower in cls.FORBIDDEN_WORDS:
            return (
                False,
                f"The nickname '{nickname}' is a prohibited word. Please choose another.",
            )

        # Check if nickname contains forbidden words as substring
        for forbidden in cls.FORBIDDEN_WORDS:
            if forbidden in nickname_lower:
                # Allow if it's a substring but not the exact match
                # e.g., "admin123" should be rejected, but "admin_user" might be OK
                # For strictness, reject if it starts with or is exactly a forbidden word
                if nickname_lower.startswith(forbidden):
                    return (
                        False,
                        "The nickname contains a prohibited word. Please choose another.",
                    )

        return True, None

    @classmethod
    def get_validation_error(cls, nickname: str) -> str | None:
        """
        Get validation error message for nickname.

        Args:
            nickname: Nickname to validate

        Returns:
            Error message if invalid, None if valid

        REQ: REQ-B-A2-2, REQ-B-A2-4

        """
        is_valid, error_msg = cls.validate(nickname)
        return error_msg if not is_valid else None
