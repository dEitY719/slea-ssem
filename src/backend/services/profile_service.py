"""
Profile service for nickname management.

REQ: REQ-B-A2-1, REQ-B-A2-2, REQ-B-A2-3, REQ-B-A2-5
"""

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from src.backend.models.user import User
from src.backend.validators.nickname import NicknameValidator


class ProfileService:
    """
    Service for managing user profiles and nicknames.

    Methods:
        check_nickname_availability: Check if nickname is available
        generate_nickname_alternatives: Generate 3 alternative suggestions
        register_nickname: Register nickname for user

    """

    def __init__(self, session: Session) -> None:
        """
        Initialize ProfileService with database session.

        Args:
            session: SQLAlchemy database session

        """
        self.session = session

    def check_nickname_availability(self, nickname: str) -> dict[str, Any]:
        """
        Check if nickname is available and suggest alternatives if not.

        REQ: REQ-B-A2-1, REQ-B-A2-3

        Args:
            nickname: Nickname to check

        Returns:
            Dictionary with:
                - available (bool): True if nickname is available
                - suggestions (list[str]): List of 3 alternatives if taken, empty if available

        Raises:
            ValueError: If nickname fails validation

        """
        # Validate format first
        is_valid, error_msg = NicknameValidator.validate(nickname)
        if not is_valid:
            raise ValueError(error_msg)

        # Check if nickname exists in database
        existing_user = self.session.query(User).filter_by(nickname=nickname).first()

        if existing_user:
            # Nickname is taken, generate alternatives
            suggestions = self.generate_nickname_alternatives(nickname)
            return {"available": False, "suggestions": suggestions}

        # Nickname is available
        return {"available": True, "suggestions": []}

    def generate_nickname_alternatives(self, base_nickname: str) -> list[str]:
        """
        Generate 3 alternative nickname suggestions.

        REQ: REQ-B-A2-3

        Generates alternatives in format: base_nickname_1, base_nickname_2, base_nickname_3
        Returns only available alternatives.

        Args:
            base_nickname: Base nickname to generate alternatives from

        Returns:
            List of 3 available nickname alternatives

        """
        suggestions: list[str] = []
        counter = 1

        while len(suggestions) < 3 and counter <= 100:  # Safeguard against infinite loop
            candidate = f"{base_nickname}_{counter}"

            # Check if candidate is available
            if len(candidate) <= 30:  # Max length constraint
                existing = self.session.query(User).filter_by(nickname=candidate).first()
                if not existing:
                    suggestions.append(candidate)

            counter += 1

        return suggestions[:3]  # Return first 3 suggestions

    def register_nickname(self, user_id: int, nickname: str) -> dict[str, Any]:
        """
        Register nickname for user.

        REQ: REQ-B-A2-5

        Args:
            user_id: User ID (from REQ-B-A1 authentication)
            nickname: Nickname to register

        Returns:
            Dictionary with:
                - user_id (int): User ID
                - nickname (str): Registered nickname
                - updated_at (str): ISO format timestamp

        Raises:
            ValueError: If nickname is invalid or already taken
            Exception: If user not found

        """
        # Validate nickname
        is_valid, error_msg = NicknameValidator.validate(nickname)
        if not is_valid:
            raise ValueError(error_msg)

        # Check if nickname is available
        existing = self.session.query(User).filter_by(nickname=nickname).first()
        if existing:
            raise ValueError(f"Nickname '{nickname}' is already taken.")

        # Get user and update nickname
        user = self.session.query(User).filter_by(id=user_id).first()
        if not user:
            raise Exception(f"User with id {user_id} not found.")

        user.nickname = nickname
        user.updated_at = datetime.utcnow()
        self.session.commit()

        return {
            "user_id": user.id,
            "nickname": user.nickname,
            "updated_at": user.updated_at.isoformat(),
        }
