"""
Profile service for nickname management and profile editing.

REQ: REQ-B-A2-1, REQ-B-A2-2, REQ-B-A2-3, REQ-B-A2-5, REQ-B-A2-Edit-1, REQ-B-A2-Edit-2, REQ-B-A2-Edit-3
"""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from src.backend.models.user import User
from src.backend.models.user_profile import UserProfileSurvey
from src.backend.validators.nickname import NicknameValidator


class ProfileService:
    """
    Service for managing user profiles and nicknames.

    Methods:
        check_nickname_availability: Check if nickname is available
        generate_nickname_alternatives: Generate 3 alternative suggestions
        register_nickname: Register nickname for user
        check_nickname_available_for_edit: Check if nickname is available (excluding self)
        edit_nickname: Edit user's nickname
        update_survey: Create/update user profile survey

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
        user.updated_at = datetime.now(UTC)
        self.session.commit()

        return {
            "user_id": user.id,
            "nickname": user.nickname,
            "updated_at": user.updated_at.isoformat(),
        }

    def check_nickname_available_for_edit(self, user_id: int, nickname: str) -> dict[str, Any]:
        """
        Check if nickname is available for edit (excluding current user).

        REQ: REQ-B-A2-Edit-1

        For profile edit, user can keep their existing nickname without conflict.
        Only checks if OTHER users have taken the nickname.

        Args:
            user_id: Current user ID (to exclude from duplicate check)
            nickname: New nickname to check

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

        # Check if nickname exists in database (excluding current user)
        existing_user = self.session.query(User).filter(User.nickname == nickname, User.id != user_id).first()

        if existing_user:
            # Nickname is taken by someone else, generate alternatives
            suggestions = self.generate_nickname_alternatives(nickname)
            return {"available": False, "suggestions": suggestions}

        # Nickname is available
        return {"available": True, "suggestions": []}

    def edit_nickname(self, user_id: int, nickname: str) -> dict[str, Any]:
        """
        Edit user's nickname.

        REQ: REQ-B-A2-Edit-1, REQ-B-A2-Edit-2

        Args:
            user_id: User ID to edit
            nickname: New nickname

        Returns:
            Dictionary with:
                - user_id (int): User ID
                - nickname (str): Updated nickname
                - updated_at (str): ISO format timestamp

        Raises:
            ValueError: If nickname is invalid or already taken by others
            Exception: If user not found

        """
        # Validate nickname format
        is_valid, error_msg = NicknameValidator.validate(nickname)
        if not is_valid:
            raise ValueError(error_msg)

        # Check if nickname is taken by others (exclude self)
        existing = self.session.query(User).filter(User.nickname == nickname, User.id != user_id).first()
        if existing:
            raise ValueError(f"Nickname '{nickname}' is already taken.")

        # Get user and update nickname
        user = self.session.query(User).filter_by(id=user_id).first()
        if not user:
            raise Exception(f"User with id {user_id} not found.")

        user.nickname = nickname
        user.updated_at = datetime.now(UTC)
        self.session.commit()

        return {
            "user_id": user.id,
            "nickname": user.nickname,
            "updated_at": user.updated_at.isoformat(),
        }

    def update_survey(self, user_id: int, survey_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create new user profile survey record.

        REQ: REQ-B-A2-Edit-3

        Design: Always creates NEW record (never updates existing).
        This maintains complete audit trail of user's profile changes.

        Args:
            user_id: User ID
            survey_data: Survey data dict with keys:
                - self_level: 'beginner', 'intermediate', or 'advanced'
                - years_experience: int (0-60)
                - job_role: str (1-100 chars)
                - duty: str (1-500 chars)
                - interests: list[str] (1-20 items)

        Returns:
            Dictionary with:
                - survey_id (str): UUID of created survey
                - user_id (int): User ID
                - self_level (str): Self-assessed level
                - submitted_at (str): ISO format timestamp

        Raises:
            ValueError: If survey data is invalid
            Exception: If user not found

        """
        # Check user exists
        user = self.session.query(User).filter_by(id=user_id).first()
        if not user:
            raise Exception(f"User with id {user_id} not found.")

        # Validate survey data
        self._validate_survey_data(survey_data)

        # Create new survey record (never update existing)
        survey = UserProfileSurvey(
            id=str(uuid4()),
            user_id=user_id,
            self_level=survey_data.get("self_level"),
            years_experience=survey_data.get("years_experience"),
            job_role=survey_data.get("job_role"),
            duty=survey_data.get("duty"),
            interests=survey_data.get("interests"),
            submitted_at=datetime.now(UTC),
        )

        self.session.add(survey)
        self.session.commit()

        return {
            "survey_id": survey.id,
            "user_id": survey.user_id,
            "self_level": survey.self_level,
            "submitted_at": survey.submitted_at.isoformat(),
        }

    def _validate_survey_data(self, survey_data: dict[str, Any]) -> None:
        """
        Validate survey data fields.

        Args:
            survey_data: Survey data to validate

        Raises:
            ValueError: If any field is invalid

        """
        # Validate self_level if provided
        if "self_level" in survey_data and survey_data["self_level"] is not None:
            valid_levels = ("beginner", "intermediate", "advanced")
            if survey_data["self_level"] not in valid_levels:
                raise ValueError(f"Invalid self_level. Must be one of: {', '.join(valid_levels)}")

        # Validate years_experience if provided
        if "years_experience" in survey_data and survey_data["years_experience"] is not None:
            years = survey_data["years_experience"]
            if not isinstance(years, int) or years < 0 or years > 60:
                raise ValueError("years_experience must be an integer between 0 and 60")

        # Validate job_role if provided
        if "job_role" in survey_data and survey_data["job_role"] is not None:
            role = survey_data["job_role"]
            if not isinstance(role, str) or len(role) < 1 or len(role) > 100:
                raise ValueError("job_role must be a string between 1 and 100 characters")

        # Validate duty if provided
        if "duty" in survey_data and survey_data["duty"] is not None:
            duty = survey_data["duty"]
            if not isinstance(duty, str) or len(duty) < 1 or len(duty) > 500:
                raise ValueError("duty must be a string between 1 and 500 characters")

        # Validate interests if provided
        if "interests" in survey_data and survey_data["interests"] is not None:
            interests = survey_data["interests"]
            if not isinstance(interests, list):
                raise ValueError("interests must be a list of strings")
            if len(interests) < 1 or len(interests) > 20:
                raise ValueError("interests must have between 1 and 20 items")
            if not all(isinstance(item, str) for item in interests):
                raise ValueError("All items in interests must be strings")
