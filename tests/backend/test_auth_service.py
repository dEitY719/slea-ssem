"""
Tests for authentication service.

REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3, REQ-B-A1-4
"""

from datetime import datetime, timedelta

import jwt
import pytest
from sqlalchemy.orm import Session

from src.backend.config import settings
from src.backend.models.user import User
from src.backend.services.auth_service import AuthService


class TestAuthServiceNewUserRegistration:
    """REQ: REQ-B-A1-1, REQ-B-A1-3 - Test new user registration flow."""

    def test_authenticate_or_create_user_creates_new_user(self, db_session: Session) -> None:
        """
        Happy path: New user with valid Samsung AD data.

        REQ: REQ-B-A1-1, REQ-B-A1-3

        Given: Valid new user data from Samsung AD
        When: Authenticate new user
        Then: User created, JWT generated, is_new_user=True
        """
        # GIVEN: Valid new user data from Samsung AD
        user_data = {
            "knox_id": "user123",
            "name": "John Doe",
            "dept": "AI Lab",
            "business_unit": "Research",
            "email": "john.doe@samsung.com",
        }

        # WHEN: Authenticate new user
        auth_service = AuthService(db_session)
        jwt_token, is_new_user, user_id = auth_service.authenticate_or_create_user(user_data)

        # THEN: New user record created, JWT generated, flag is True
        assert is_new_user is True
        assert jwt_token is not None
        assert isinstance(jwt_token, str)
        assert user_id is not None
        assert isinstance(user_id, int)

        # AND: User exists in database
        user = db_session.query(User).filter_by(knox_id="user123").first()
        assert user is not None
        assert user.name == "John Doe"
        assert user.dept == "AI Lab"
        assert user.email == "john.doe@samsung.com"


class TestAuthServiceExistingUserLogin:
    """REQ: REQ-B-A1-4 - Test existing user re-login flow."""

    def test_authenticate_or_create_user_existing_user_updates_login(
        self, db_session: Session, user_fixture: User
    ) -> None:
        """
        Happy path: Existing user login.

        REQ: REQ-B-A1-4

        Given: Existing user in database
        When: Authenticate existing user (re-login)
        Then: JWT regenerated, is_new_user=False, last_login updated
        """
        # GIVEN: Existing user in database
        existing_user = user_fixture
        original_login = existing_user.last_login

        user_data = {
            "knox_id": existing_user.knox_id,
            "name": existing_user.name,
            "dept": existing_user.dept,
            "business_unit": existing_user.business_unit,
            "email": existing_user.email,
        }

        # WHEN: Authenticate existing user (re-login)
        auth_service = AuthService(db_session)
        jwt_token, is_new_user, user_id = auth_service.authenticate_or_create_user(user_data)

        # THEN: JWT regenerated, flag is False
        assert is_new_user is False
        assert jwt_token is not None
        assert user_id == existing_user.id

        # AND: last_login timestamp updated
        db_session.refresh(existing_user)
        assert existing_user.last_login is not None
        assert original_login is not None
        assert existing_user.last_login >= original_login


class TestJWTTokenPayload:
    """REQ: REQ-B-A1-2 - Verify JWT token structure and payload."""

    def test_jwt_token_payload_contains_knox_id_only(self, db_session: Session) -> None:
        """
        Acceptance criteria: JWT payload contains only knox_id, iat, exp.

        REQ: REQ-B-A1-2

        Given: User data
        When: Generate JWT
        Then: Payload contains only knox_id, iat, exp
        """
        # GIVEN: User data
        user_data = {
            "knox_id": "user123",
            "name": "John Doe",
            "dept": "AI Lab",
            "business_unit": "Research",
            "email": "john.doe@samsung.com",
        }

        # WHEN: Generate JWT
        auth_service = AuthService(db_session)
        jwt_token, _, _ = auth_service.authenticate_or_create_user(user_data)

        # THEN: Decode and verify payload contains only knox_id, iat, exp
        payload = auth_service.decode_jwt(jwt_token)
        assert "knox_id" in payload
        assert payload["knox_id"] == "user123"
        assert "iat" in payload
        assert "exp" in payload
        # Ensure no other user fields are in JWT
        assert "email" not in payload
        assert "name" not in payload
        assert "dept" not in payload
        assert "business_unit" not in payload


class TestAuthServiceInputValidation:
    """REQ: REQ-B-A1-1 - Test input validation for Samsung AD user data."""

    def test_authenticate_or_create_user_missing_required_fields(self, db_session: Session) -> None:
        """
        Input validation: Missing required fields raises ValueError.

        REQ: REQ-B-A1-1

        Given: Incomplete user data (missing email)
        When: Attempt authentication
        Then: ValueError raised with descriptive message
        """
        # GIVEN: Incomplete user data (missing email)
        user_data = {
            "knox_id": "user123",
            "name": "John Doe",
            "dept": "AI Lab",
            "business_unit": "Research",
            # Missing: "email"
        }

        # WHEN/THEN: Should raise ValueError
        auth_service = AuthService(db_session)
        with pytest.raises(ValueError, match="Missing required field: email"):
            auth_service.authenticate_or_create_user(user_data)

    def test_authenticate_or_create_user_duplicate_knox_id(self, db_session: Session, user_fixture: User) -> None:
        """
        Edge case: Duplicate knox_id does not create new record.

        REQ: REQ-B-A1-1, REQ-B-A1-4

        Given: Existing user
        When: Attempt to create user with same knox_id
        Then: Return existing user (not create duplicate)
        """
        # GIVEN: Existing user
        existing_knox_id = user_fixture.knox_id

        user_data = {
            "knox_id": existing_knox_id,
            "name": "Different Name",
            "dept": "Different Dept",
            "business_unit": "Different BU",
            "email": "different@samsung.com",
        }

        # WHEN: Attempt to create user with same knox_id
        auth_service = AuthService(db_session)
        jwt_token, is_new_user, user_id = auth_service.authenticate_or_create_user(user_data)

        # THEN: Should return existing user (not create duplicate)
        assert is_new_user is False
        assert user_id == user_fixture.id
        user_count = db_session.query(User).filter_by(knox_id=existing_knox_id).count()
        assert user_count == 1  # Only one record exists


class TestJWTTokenExpiration:
    """REQ: REQ-B-A1-2 - Test JWT token expiration."""

    def test_jwt_token_has_valid_expiration(self, db_session: Session) -> None:
        """
        Acceptance criteria: JWT token expiration is set correctly.

        REQ: REQ-B-A1-2

        Given: User data
        When: Generate JWT
        Then: Token has valid expiration time
        """
        # GIVEN: User data
        user_data = {
            "knox_id": "user123",
            "name": "John Doe",
            "dept": "AI Lab",
            "business_unit": "Research",
            "email": "john.doe@samsung.com",
        }

        # WHEN: Generate JWT
        auth_service = AuthService(db_session)
        jwt_token, _, _ = auth_service.authenticate_or_create_user(user_data)

        # THEN: Decode and verify expiration
        payload = auth_service.decode_jwt(jwt_token)
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])

        # Verify expiration is approximately 24 hours from issue time
        expected_exp = iat_time + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 5  # Allow 5 seconds difference


class TestJWTTokenDecoding:
    """REQ: REQ-B-A1-2 - Test JWT token decoding."""

    def test_decode_invalid_jwt_raises_error(self, db_session: Session) -> None:
        """
        Edge case: Invalid JWT raises error.

        REQ: REQ-B-A1-2

        Given: Invalid JWT token
        When: Attempt to decode
        Then: InvalidTokenError raised
        """
        # GIVEN: Invalid JWT token
        invalid_token = "invalid.token.here"

        # WHEN/THEN: Should raise error
        auth_service = AuthService(db_session)
        with pytest.raises(jwt.InvalidTokenError):
            auth_service.decode_jwt(invalid_token)
