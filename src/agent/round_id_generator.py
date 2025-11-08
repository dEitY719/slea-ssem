"""
Round ID generation and tracking for agent pipeline.

REQ: REQ-A-RoundID

Provides:
- Round ID generation with unique identification
- Format: {session_id}_{round_number}_{iso_timestamp}
- Parsing and component extraction
- Integration with Mode 1 and Mode 2 pipelines
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RoundID:
    """
    Immutable Round ID with components.

    Attributes:
        session_id: Test session identifier
        round_number: Round number (1 or 2)
        timestamp: Round start time (UTC)

    """

    session_id: str
    round_number: int
    timestamp: datetime

    def __str__(self) -> str:
        """Return Round ID as string."""
        return f"{self.session_id}_{self.round_number}_{self.timestamp.isoformat()}"


class RoundIDGenerator:
    """
    Generator for Round IDs with format: {session_id}_{round_number}_{timestamp}.

    REQ: REQ-A-RoundID

    Features:
    - Unique Round ID generation
    - ISO 8601 timestamp with UTC timezone
    - Component parsing and extraction
    - < 1ms generation performance
    - Support for Round 1 and Round 2
    """

    # ========================================================================
    # GENERATION
    # ========================================================================

    def generate(
        self,
        session_id: str,
        round_number: int,
    ) -> str:
        """
        Generate Round ID.

        AC1: Format is {session_id}_{round_number}_{iso_timestamp}
        AC2: Timestamp is ISO 8601 UTC

        Args:
            session_id: Test session identifier
            round_number: Round number (1 or 2)

        Returns:
            Round ID string

        Raises:
            ValueError: If round_number not 1 or 2
            TypeError: If inputs are wrong type

        """
        # Validate round number
        if not isinstance(round_number, int):
            raise TypeError(f"round_number must be int, got {type(round_number)}")
        if round_number not in (1, 2):
            raise ValueError(f"round_number must be 1 or 2, got {round_number}")

        # Validate session_id
        if not isinstance(session_id, str):
            raise TypeError(f"session_id must be str, got {type(session_id)}")
        if not session_id:
            raise ValueError("session_id cannot be empty")

        # Get current timestamp in UTC with microsecond precision
        timestamp = datetime.now(UTC)

        # Format: {session_id}_{round_number}_{iso_timestamp}
        round_id = f"{session_id}_{round_number}_{timestamp.isoformat()}"

        logger.info(f"Generated Round ID: {round_id} (session={session_id}, round={round_number})")

        return round_id

    # ========================================================================
    # PARSING
    # ========================================================================

    def parse(self, round_id: str) -> RoundID:
        """
        Parse Round ID string into components.

        AC6: Round ID can be parsed back to components.

        Args:
            round_id: Round ID string to parse

        Returns:
            RoundID object with extracted components

        Raises:
            ValueError: If Round ID format invalid
            TypeError: If input is not string

        """
        if not isinstance(round_id, str):
            raise TypeError(f"round_id must be str, got {type(round_id)}")

        # Parse format: {session_id}_{round_number}_{iso_timestamp}
        # ISO timestamp format: 2025-11-09T14:30:45.123456+00:00
        # Round number is always single digit (1 or 2)
        # Find last occurrence of _<digit>_ pattern

        # Find the ISO timestamp by looking for the date pattern (YYYY-MM-DD)
        import re as regex_module

        # Pattern: session_id ending in underscore, digit, underscore, then ISO datetime
        match = regex_module.match(
            r"^(.+)_([1-2])_(\d{4}-\d{2}-\d{2}T.+)$",
            round_id,
        )

        if not match:
            raise ValueError(
                f"Invalid Round ID format: {round_id}. "
                "Expected {{session_id}}_{{round_number}}_{{timestamp}}"
            )

        session_id = match.group(1)
        try:
            round_number = int(match.group(2))
        except ValueError as e:
            raise ValueError(f"Invalid round_number in Round ID: {match.group(2)}") from e

        if round_number not in (1, 2):
            raise ValueError(f"round_number must be 1 or 2, got {round_number}")

        timestamp_str = match.group(3)
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except ValueError as e:
            raise ValueError(f"Invalid timestamp in Round ID: {timestamp_str}") from e

        # Verify timezone is UTC
        if timestamp.tzinfo != UTC:
            raise ValueError(f"Timestamp timezone must be UTC, got {timestamp.tzinfo}")

        return RoundID(
            session_id=session_id,
            round_number=round_number,
            timestamp=timestamp,
        )

    # ========================================================================
    # EXTRACTION
    # ========================================================================

    def extract_session_id(self, round_id: str) -> str:
        """
        Extract session ID from Round ID.

        Args:
            round_id: Round ID string

        Returns:
            Session ID

        """
        parsed = self.parse(round_id)
        return parsed.session_id

    def extract_round_number(self, round_id: str) -> int:
        """
        Extract round number from Round ID.

        Args:
            round_id: Round ID string

        Returns:
            Round number (1 or 2)

        """
        parsed = self.parse(round_id)
        return parsed.round_number

    def extract_timestamp(self, round_id: str) -> datetime:
        """
        Extract timestamp from Round ID.

        Args:
            round_id: Round ID string

        Returns:
            UTC datetime

        """
        parsed = self.parse(round_id)
        return parsed.timestamp

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def is_valid_format(self, round_id: str) -> bool:
        """
        Check if Round ID has valid format.

        Args:
            round_id: Round ID string to validate

        Returns:
            True if valid format, False otherwise

        """
        try:
            self.parse(round_id)
            return True
        except (ValueError, TypeError):
            return False

    def is_round_1(self, round_id: str) -> bool:
        """
        Check if Round ID is for Round 1.

        Args:
            round_id: Round ID string

        Returns:
            True if Round 1, False otherwise

        """
        parsed = self.parse(round_id)
        return parsed.round_number == 1

    def is_round_2(self, round_id: str) -> bool:
        """
        Check if Round ID is for Round 2.

        Args:
            round_id: Round ID string

        Returns:
            True if Round 2, False otherwise

        """
        parsed = self.parse(round_id)
        return parsed.round_number == 2
