"""
Authentication service for Samsung AD user authentication and JWT management.

REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3, REQ-B-A1-4
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from sqlalchemy.orm import Session

from src.backend.config import settings
from src.backend.models.user import User


class AuthService:
    """
    Service for handling user authentication and JWT token management.

    Methods:
        authenticate_or_create_user: Authenticate existing user or create new user
        decode_jwt: Decode and validate JWT token
        _generate_jwt: Generate JWT token from knox_id

    """

    def __init__(self, session: Session) -> None:
        """
        Initialize AuthService with database session.

        Args:
            session: SQLAlchemy database session

        """
        self.session = session

    def authenticate_or_create_user(self, user_data: dict[str, str]) -> tuple[str, bool, int]:
        """
        Authenticate user or create new user account.

        REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3, REQ-B-A1-4

        Args:
            user_data: User information from Samsung AD
                - knox_id: Samsung Knox ID
                - name: User's full name
                - dept: Department
                - business_unit: Business unit
                - email: Email address

        Returns:
            Tuple of (jwt_token, is_new_user, user_id):
                - jwt_token: Signed JWT token containing only {knox_id, iat, exp}
                - is_new_user: True if new user, False if existing user
                - user_id: User's database primary key (integer)

        Raises:
            ValueError: If required fields are missing from user_data

        """
        # REQ-B-A1-1: Validate required fields
        required_fields = ["knox_id", "name", "dept", "business_unit", "email"]
        for field in required_fields:
            if field not in user_data:
                raise ValueError(f"Missing required field: {field}")

        knox_id = user_data["knox_id"]

        # Check if user already exists
        existing_user = self.session.query(User).filter_by(knox_id=knox_id).first()

        if existing_user:
            # REQ-B-A1-4: Existing user - update last_login and generate new JWT
            existing_user.last_login = datetime.now(UTC)
            self.session.commit()
            jwt_token = self._generate_jwt(knox_id)
            return jwt_token, False, existing_user.id

        # REQ-B-A1-3: New user - create user record and generate JWT
        new_user = User(
            knox_id=knox_id,
            name=user_data["name"],
            dept=user_data["dept"],
            business_unit=user_data["business_unit"],
            email=user_data["email"],
            last_login=datetime.now(UTC),
        )
        self.session.add(new_user)
        self.session.commit()

        jwt_token = self._generate_jwt(knox_id)
        return jwt_token, True, new_user.id

    def _generate_jwt(self, knox_id: str) -> str:
        """
        Generate JWT token with only knox_id in payload.

        REQ: REQ-B-A1-2

        Args:
            knox_id: User's Knox ID

        Returns:
            Encoded JWT token as string

        """
        now = datetime.now(UTC)
        expiration = now + timedelta(hours=settings.JWT_EXPIRATION_HOURS)

        payload: dict[str, Any] = {
            "knox_id": knox_id,
            "iat": now,
            "exp": expiration,
        }

        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        return token

    def decode_jwt(self, token: str) -> dict[str, Any]:
        """
        Decode and validate JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded payload as dictionary

        Raises:
            jwt.InvalidTokenError: If token is invalid or expired

        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            return payload
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(f"Invalid token: {str(e)}") from e
