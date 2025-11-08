"""
Question content validation logic.

REQ: REQ-B-B6-2
"""

import re

from src.backend.models import Question


class QuestionContentValidator:
    """
    Validate question content for profanity, bias, and copyright concerns.

    REQ-B-B6-2: Content filtering for profanity (비속어), bias (편향),
    and copyright concerns (저작권 의심)

    Design principle:
    - Single responsibility: Validate question content quality
    - Return tuple: (is_valid, error_message)
    - Check all fields: stem, choices, explanation
    - Three filters: profanity, bias, copyright
    """

    # Profanity keywords (비속어)
    # For MVP 1.0: Basic English profanity list
    # Future: Extend to Korean profanity with linguistic normalization
    PROFANITY_WORDS = {
        "damn",
        "hell",
        "crap",
        "piss",
        "bollocks",
        "arse",
        "bastard",
        "bitch",
        "bugger",
        "cock",
        "dick",
        "fart",
        "fuck",
        "shit",
        "wank",
    }

    # Bias indicator keywords (편향 지시자)
    BIAS_PATTERNS = [
        r"\b(men|women|boys|girls)\s+(are|is)\s+(better|smarter|stronger|naturally)",
        r"\b(which\s+(gender|race|age|culture))\b",
        r"\b(old\s+people|young\s+people)\s+(cannot|can't)",
        r"\b(superior|inferior)\s+(gender|race|culture|ethnicity)",
        r"\b(naturally\s+(intelligent|athletic|good)\s+(at|with))",
        r"\b(stereotype|discriminat)",  # Patterns mentioning stereotypes/discrimination
    ]

    # Copyright concern patterns (저작권 의심)
    COPYRIGHT_PATTERNS = [
        r'"[^"]{10,}"',  # Long quoted text without attribution
        r"\[source.*\]",  # Proper attribution pattern (should be OK)
        r"(wikipedia|textbook|book|article)\s*[:;]?\s*['\"]?",  # Source mention
    ]

    @classmethod
    def validate_question(cls, question: Question) -> tuple[bool, str | None]:
        """
        Validate a question for content quality.

        Args:
            question: Question object with stem, choices, answer_schema

        Returns:
            Tuple of (is_valid, error_message)
                - (True, None) if valid
                - (False, error_message) if invalid

        REQ: REQ-B-B6-2

        """
        # Collect all text to validate
        text_parts = [question.stem]

        # Add choices if present
        if question.choices:
            text_parts.extend(question.choices)

        # Add explanation from answer_schema if present
        if question.answer_schema:
            if "explanation" in question.answer_schema:
                text_parts.append(question.answer_schema["explanation"])

        # Concatenate all text
        full_text = " ".join(str(part) for part in text_parts if part)

        # Check profanity
        is_valid, error = cls._check_profanity(full_text)
        if not is_valid:
            return False, error

        # Check bias
        is_valid, error = cls._check_bias(full_text)
        if not is_valid:
            return False, error

        # Check copyright concerns
        is_valid, error = cls._check_copyright(full_text)
        if not is_valid:
            return False, error

        return True, None

    @classmethod
    def _check_profanity(cls, text: str) -> tuple[bool, str | None]:
        """
        Check for profanity and inappropriate language.

        Args:
            text: Text to check

        Returns:
            (is_valid, error_message)

        """
        text_lower = text.lower()

        # Check for profanity keywords
        for word in cls.PROFANITY_WORDS:
            # Use word boundaries to avoid partial matches
            if re.search(rf"\b{re.escape(word)}\b", text_lower):
                return (
                    False,
                    "Question contains inappropriate language. Please revise.",
                )

        return True, None

    @classmethod
    def _check_bias(cls, text: str) -> tuple[bool, str | None]:
        """
        Check for bias, discrimination, or unfair assumptions.

        Args:
            text: Text to check

        Returns:
            (is_valid, error_message)

        """
        text_lower = text.lower()

        # Check bias patterns
        for pattern in cls.BIAS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return (
                    False,
                    "Question contains biased, stereotyped, or discriminatory language. "
                    "Please ensure the question is objective and fair.",
                )

        # Additional checks for common bias indicators
        bias_indicators = [
            "which gender",
            "which race",
            "which culture",
            "which religion",
            "superior",
            "inferior",
            "naturally intelligent",
            "naturally athletic",
        ]

        for indicator in bias_indicators:
            if indicator in text_lower:
                return (
                    False,
                    "Question may contain biased assumptions. Please revise for objectivity.",
                )

        return True, None

    @classmethod
    def _check_copyright(cls, text: str) -> tuple[bool, str | None]:
        """
        Check for copyright concerns or direct plagiarism.

        Args:
            text: Text to check

        Returns:
            (is_valid, error_message)

        """
        text_lower = text.lower()

        # Check for direct quoted text without proper attribution
        # Pattern: quoted text longer than 10 characters
        quotes = re.findall(r'"([^"]{10,})"', text)
        if quotes:
            # Check if quote has formal source attribution nearby
            for quote in quotes:
                # Look for source attribution markers nearby
                quote_pos = text.lower().find(f'"{quote.lower()}"')
                if quote_pos != -1:
                    # Check 100 characters before quote for formal attribution only
                    context = text[max(0, quote_pos - 100) : quote_pos + len(quote) + 100]
                    # Formal attribution patterns (from sources with proper format)
                    has_formal_source = any(
                        marker in context.lower()
                        for marker in [
                            "[source",
                            "source:",
                            "source =",
                            "citation:",
                            "cite:",
                            "doi:",
                            "url:",
                            "https://",
                            "http://",
                        ]
                    )
                    if not has_formal_source:
                        return (
                            False,
                            "Question contains direct quotes without proper source attribution. "
                            "Please add source information or paraphrase.",
                        )

        # Check for explicit plagiarism/unattributed content indicators
        copyright_indicators = [
            "copy-pasted",
            "from wikipedia",
            "from the internet",
            "directly from",
            "copied from",
        ]

        for indicator in copyright_indicators:
            if indicator in text_lower:
                return (
                    False,
                    "Question may contain plagiarized or unattributed content. "
                    "Please ensure original content or proper attribution.",
                )

        return True, None
