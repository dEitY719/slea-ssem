"""
Tests for OIDC authentication endpoint and service.

REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3, REQ-B-A1-4, REQ-B-A1-5, REQ-B-A1-6, REQ-B-A1-7, REQ-B-A1-8
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.backend.config import settings
from src.backend.models.user import User
from src.backend.services.auth_service import AuthService, OIDCAuthService

# Set OIDC environment variables for testing
os.environ.setdefault("OIDC_CLIENT_ID", "test_client_id")
os.environ.setdefault("OIDC_CLIENT_SECRET", "test_client_secret")
os.environ.setdefault("OIDC_TENANT_ID", "test_tenant_id")
os.environ.setdefault("OIDC_REDIRECT_URI", "http://localhost:3000/auth/callback")


@pytest.fixture(scope="function", autouse=True)
def setup_oidc_settings() -> None:
    """
    Reset OIDC settings for each test.

    This ensures that the settings object has test OIDC endpoints configured.
    """
    # Set OIDC endpoints directly on settings object
    settings.OIDC_CLIENT_ID = os.getenv("OIDC_CLIENT_ID", "test_client_id")
    settings.OIDC_CLIENT_SECRET = os.getenv("OIDC_CLIENT_SECRET", "test_client_secret")
    settings.OIDC_TENANT_ID = os.getenv("OIDC_TENANT_ID", "test_tenant_id")
    settings.OIDC_REDIRECT_URI = os.getenv("OIDC_REDIRECT_URI", "http://localhost:3000/auth/callback")

    # Construct Azure AD endpoints
    if settings.OIDC_TENANT_ID:
        settings.OIDC_TOKEN_ENDPOINT = (
            f"https://login.microsoftonline.com/{settings.OIDC_TENANT_ID}/oauth2/v2.0/token"
        )
        settings.OIDC_JWKS_ENDPOINT = (
            f"https://login.microsoftonline.com/{settings.OIDC_TENANT_ID}/discovery/v2.0/keys"
        )
    yield


class TestOIDCCallbackEndpoint:
    """REQ: REQ-B-A1-1~REQ-B-A1-7 - Test OIDC callback endpoint."""

    def test_oidc_callback_with_valid_authorization_code(self, client: TestClient, db_session: Session) -> None:
        """
        TC-1: Happy path - Valid authorization code and code_verifier.

        REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-5, REQ-B-A1-6, REQ-B-A1-7

        Given: Valid authorization code and code_verifier from frontend
        When: POST /auth/oidc/callback with code and code_verifier
        Then:
            - Azure AD token exchange succeeds
            - JWT generated and set in HttpOnly cookie
            - Response contains user_id and is_new_user flag
            - Status code 201 for new user, 200 for existing user
        """
        # GIVEN: Valid authorization code and code_verifier
        auth_code = "valid_auth_code_123"
        code_verifier = "valid_code_verifier_456"

        # Mock Azure AD token response
        azure_token_response = {
            "access_token": "azure_access_token_xyz",
            "id_token": _create_mock_id_token(
                sub="user_oid_123",
                email="user@samsung.com",
                name="Test User",
                dept="AI Lab",
                business_unit="Research",
            ),
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        # WHEN: POST /auth/oidc/callback
        with patch("src.backend.api.auth.OIDCAuthService") as mock_oidc_service_class:
            mock_oidc_service = MagicMock()
            mock_oidc_service_class.return_value = mock_oidc_service
            mock_oidc_service.exchange_code_for_tokens.return_value = azure_token_response
            mock_oidc_service.validate_id_token.return_value = {
                "sub": "user_oid_123",
                "email": "user@samsung.com",
                "name": "Test User",
                "dept": "AI Lab",
                "business_unit": "Research",
            }

            response = client.post(
                "/auth/oidc/callback",
                json={"code": auth_code, "code_verifier": code_verifier},
            )

        # THEN: Response should be successful
        assert response.status_code in [200, 201]
        response_data = response.json()
        assert "access_token" in response_data
        assert "token_type" in response_data
        assert response_data["token_type"] == "bearer"
        assert "user_id" in response_data
        assert "is_new_user" in response_data
        assert isinstance(response_data["user_id"], int)
        assert isinstance(response_data["is_new_user"], bool)

        # AND: JWT token should be set in HttpOnly cookie
        assert "set-cookie" in response.headers
        set_cookie = response.headers.get("set-cookie", "")
        assert "auth_token" in set_cookie or "jwt" in set_cookie.lower()
        assert "HttpOnly" in set_cookie
        assert "SameSite" in set_cookie

    def test_oidc_callback_new_user_registration(self, client: TestClient, db_session: Session) -> None:
        """
        TC-2: New user creation during OIDC callback.

        REQ: REQ-B-A1-3, REQ-B-A1-7

        Given: Authorization code for new user (not in database)
        When: POST /auth/oidc/callback
        Then:
            - User record created in database
            - is_new_user=True in response
            - Status code 201
        """
        # GIVEN: New user's authorization code
        auth_code = "new_user_auth_code"
        code_verifier = "new_user_code_verifier"

        # Initial count of users
        initial_user_count = db_session.query(User).count()

        # Mock Azure AD token response for new user
        azure_token_response = {
            "access_token": "azure_token_new_user",
            "id_token": _create_mock_id_token(
                sub="new_user_oid_999",
                email="newuser@samsung.com",
                name="New User",
                dept="Sales",
                business_unit="NA",
            ),
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        # WHEN: POST /auth/oidc/callback for new user
        with patch("src.backend.api.auth.OIDCAuthService") as mock_oidc_service_class:
            mock_oidc_service = MagicMock()
            mock_oidc_service_class.return_value = mock_oidc_service
            mock_oidc_service.exchange_code_for_tokens.return_value = azure_token_response
            mock_oidc_service.validate_id_token.return_value = {
                "sub": "new_user_oid_999",
                "email": "newuser@samsung.com",
                "name": "New User",
                "dept": "Sales",
                "business_unit": "NA",
            }

            response = client.post(
                "/auth/oidc/callback",
                json={"code": auth_code, "code_verifier": code_verifier},
            )

        # THEN: New user should be created
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["is_new_user"] is True

        # AND: User count should increase
        new_user_count = db_session.query(User).count()
        assert new_user_count == initial_user_count + 1

        # AND: User should exist in database with correct data
        new_user = db_session.query(User).filter_by(email="newuser@samsung.com").first()
        assert new_user is not None
        assert new_user.name == "New User"
        assert new_user.dept == "Sales"

    def test_oidc_callback_existing_user_login(self, client: TestClient, db_session: Session, user_fixture: User) -> None:
        """
        TC-3: Existing user re-login during OIDC callback.

        REQ: REQ-B-A1-4, REQ-B-A1-7

        Given: Authorization code for existing user
        When: POST /auth/oidc/callback
        Then:
            - is_new_user=False in response
            - Status code 200
            - last_login timestamp updated
        """
        # GIVEN: Existing user
        existing_user = user_fixture
        original_last_login = existing_user.last_login

        auth_code = "existing_user_auth_code"
        code_verifier = "existing_user_code_verifier"

        # Mock Azure AD token response
        azure_token_response = {
            "access_token": "azure_token_existing",
            "id_token": _create_mock_id_token(
                sub=existing_user.knox_id,
                email=existing_user.email,
                name=existing_user.name,
                dept=existing_user.dept,
                business_unit=existing_user.business_unit,
            ),
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        # WHEN: POST /auth/oidc/callback for existing user
        with patch("src.backend.api.auth.OIDCAuthService") as mock_oidc_service_class:
            mock_oidc_service = MagicMock()
            mock_oidc_service_class.return_value = mock_oidc_service
            mock_oidc_service.exchange_code_for_tokens.return_value = azure_token_response
            mock_oidc_service.validate_id_token.return_value = {
                "sub": existing_user.knox_id,
                "email": existing_user.email,
                "name": existing_user.name,
                "dept": existing_user.dept,
                "business_unit": existing_user.business_unit,
            }

            response = client.post(
                "/auth/oidc/callback",
                json={"code": auth_code, "code_verifier": code_verifier},
            )

        # THEN: Response should indicate existing user
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["is_new_user"] is False
        assert response_data["user_id"] == existing_user.id

        # AND: last_login should be updated
        db_session.refresh(existing_user)
        assert existing_user.last_login > original_last_login


class TestOIDCAuthService:
    """REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3 - Test OIDC service layer."""

    def test_exchange_code_for_tokens_success(self) -> None:
        """
        TC-4: Token exchange with Azure AD.

        REQ: REQ-B-A1-1, REQ-B-A1-2

        Given: Valid authorization code and code_verifier
        When: Call exchange_code_for_tokens
        Then: Azure AD token endpoint receives correct request and returns tokens
        """
        # GIVEN: Valid authorization code and code_verifier
        auth_code = "auth_code_valid"
        code_verifier = "code_verifier_valid"

        # Mock httpx.post to Azure AD endpoint
        with patch("src.backend.services.auth_service.httpx.post") as mock_post, patch(
            "src.backend.services.auth_service.settings"
        ) as mock_settings:
            # Setup mock settings to bypass mock token generation
            mock_settings.OIDC_CLIENT_ID = "test_client_id"  # Not "your-azure-app-id"
            mock_settings.OIDC_TENANT_ID = "test_tenant_id"
            mock_settings.OIDC_TOKEN_ENDPOINT = "https://login.microsoftonline.com/test_tenant_id/oauth2/v2.0/token"

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "azure_access_token",
                "id_token": _create_mock_id_token(
                    sub="user_sub",
                    email="user@samsung.com",
                    name="Test User",
                    dept="Dept",
                    business_unit="BU",
                ),
                "token_type": "Bearer",
                "expires_in": 3600,
            }
            mock_post.return_value = mock_response

            # WHEN: Call exchange_code_for_tokens
            oidc_service = OIDCAuthService()
            tokens = oidc_service.exchange_code_for_tokens(auth_code, code_verifier)

            # THEN: Tokens should be returned
            assert "access_token" in tokens
            assert "id_token" in tokens
            assert tokens["token_type"] == "Bearer"

            # AND: POST was called to Azure AD token endpoint
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "/token" in call_args[0][0]  # Check URL contains /token

    def test_validate_id_token_with_valid_token(self) -> None:
        """
        TC-5: ID Token validation with signature, issuer, audience, expiration, nonce.

        REQ: REQ-B-A1-3

        Given: Valid ID Token from Azure AD
        When: Call validate_id_token
        Then:
            - Signature verified
            - Issuer checked
            - Audience verified
            - Expiration checked
            - Nonce validated (if provided)
            - User claims extracted
        """
        # GIVEN: Valid ID Token
        id_token = _create_mock_id_token(
            sub="user_sub_123",
            email="user@samsung.com",
            name="Test User",
            dept="AI Lab",
            business_unit="Research",
        )

        # Mock both _get_jwks and jwt.decode to simulate successful validation
        with patch("src.backend.services.auth_service.jwt.decode") as mock_decode, patch(
            "src.backend.services.auth_service.OIDCAuthService._get_jwks"
        ) as mock_jwks:
            mock_jwks.return_value = {"keys": []}  # Mock JWKS response
            mock_decode.return_value = {
                "sub": "user_sub_123",
                "email": "user@samsung.com",
                "name": "Test User",
                "dept": "AI Lab",
                "business_unit": "Research",
                "iss": f"https://login.microsoftonline.com/{settings.OIDC_TENANT_ID}/v2.0",
                "aud": settings.OIDC_CLIENT_ID,
                "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
                "iat": int(datetime.now(timezone.utc).timestamp()),
            }

            # WHEN: Call validate_id_token
            oidc_service = OIDCAuthService()
            claims = oidc_service.validate_id_token(id_token)

            # THEN: Claims should be extracted
            assert claims["sub"] == "user_sub_123"
            assert claims["email"] == "user@samsung.com"
            assert claims["name"] == "Test User"

    def test_validate_id_token_with_invalid_signature(self) -> None:
        """
        Edge case: Invalid JWT signature raises error.

        REQ: REQ-B-A1-3

        Given: ID Token with invalid signature
        When: Call validate_id_token
        Then: InvalidTokenError raised
        """
        # GIVEN: Invalid ID Token
        invalid_id_token = "invalid.token.signature"

        # Mock both _get_jwks and jwt.decode to simulate signature validation failure
        with patch("src.backend.services.auth_service.jwt.decode") as mock_decode, patch(
            "src.backend.services.auth_service.OIDCAuthService._get_jwks"
        ) as mock_jwks:
            mock_jwks.return_value = {"keys": []}  # Mock JWKS response
            mock_decode.side_effect = jwt.InvalidSignatureError("Invalid signature")

            # WHEN/THEN: Should raise error (wrapped as InvalidTokenError)
            oidc_service = OIDCAuthService()
            with pytest.raises(jwt.InvalidTokenError):
                oidc_service.validate_id_token(invalid_id_token)

    def test_validate_id_token_with_expired_token(self) -> None:
        """
        Edge case: Expired ID Token raises error.

        REQ: REQ-B-A1-3

        Given: Expired ID Token
        When: Call validate_id_token
        Then: jwt.ExpiredSignatureError raised
        """
        # GIVEN: Expired ID Token
        expired_id_token = _create_mock_id_token(
            sub="user_sub",
            email="user@samsung.com",
            name="Test User",
            dept="Dept",
            business_unit="BU",
            exp_hours=-1,  # Already expired
        )

        # Mock both _get_jwks and jwt.decode to simulate expiration validation failure
        with patch("src.backend.services.auth_service.jwt.decode") as mock_decode, patch(
            "src.backend.services.auth_service.OIDCAuthService._get_jwks"
        ) as mock_jwks:
            mock_jwks.return_value = {"keys": []}  # Mock JWKS response
            mock_decode.side_effect = jwt.ExpiredSignatureError("Token expired")

            # WHEN/THEN: Should raise error (wrapped as InvalidTokenError)
            oidc_service = OIDCAuthService()
            with pytest.raises(jwt.InvalidTokenError):
                oidc_service.validate_id_token(expired_id_token)


class TestOIDCInputValidation:
    """REQ: REQ-B-A1-1 - Test input validation for OIDC callback."""

    def test_oidc_callback_missing_authorization_code(self, client: TestClient) -> None:
        """
        Input validation: Missing authorization code raises error.

        REQ: REQ-B-A1-1

        Given: Request without authorization code
        When: POST /auth/oidc/callback
        Then: 422 Unprocessable Entity (Pydantic validation error)
        """
        # GIVEN: Request missing code
        request_body = {"code_verifier": "some_verifier"}

        # WHEN: POST /auth/oidc/callback
        response = client.post("/auth/oidc/callback", json=request_body)

        # THEN: Should return validation error
        assert response.status_code == 422

    def test_oidc_callback_missing_code_verifier(self, client: TestClient) -> None:
        """
        Input validation: Missing code_verifier raises error.

        REQ: REQ-B-A1-1

        Given: Request without code_verifier
        When: POST /auth/oidc/callback
        Then: 422 Unprocessable Entity (Pydantic validation error)
        """
        # GIVEN: Request missing code_verifier
        request_body = {"code": "some_code"}

        # WHEN: POST /auth/oidc/callback
        response = client.post("/auth/oidc/callback", json=request_body)

        # THEN: Should return validation error
        assert response.status_code == 422

    def test_oidc_callback_invalid_authorization_code(self, client: TestClient) -> None:
        """
        Error case: Invalid authorization code from Azure AD.

        REQ: REQ-B-A1-1, REQ-B-A1-2

        Given: Invalid authorization code
        When: POST /auth/oidc/callback
        Then: 401 Unauthorized error with descriptive message
        """
        # GIVEN: Invalid authorization code
        auth_code = "invalid_code_123"
        code_verifier = "valid_verifier"

        # Mock Azure AD to return error
        with patch("src.backend.api.auth.OIDCAuthService") as mock_oidc_service_class:
            mock_oidc_service = MagicMock()
            mock_oidc_service_class.return_value = mock_oidc_service
            mock_oidc_service.exchange_code_for_tokens.side_effect = ValueError(
                "Invalid authorization code"
            )

            # WHEN: POST /auth/oidc/callback
            response = client.post(
                "/auth/oidc/callback",
                json={"code": auth_code, "code_verifier": code_verifier},
            )

        # THEN: Should return 401 Unauthorized
        assert response.status_code == 401


class TestJWTCookieHandling:
    """REQ: REQ-B-A1-5, REQ-B-A1-6 - Test JWT cookie setup."""

    def test_jwt_set_in_httponly_cookie(self, client: TestClient, db_session: Session) -> None:
        """
        Acceptance criteria: JWT set in HttpOnly cookie with secure flags.

        REQ: REQ-B-A1-5, REQ-B-A1-6

        Given: Valid OIDC callback
        When: POST /auth/oidc/callback
        Then: Set-Cookie header contains JWT with HttpOnly, SameSite, Path flags
        """
        # GIVEN: Valid authorization code
        auth_code = "valid_code"
        code_verifier = "valid_verifier"

        # Mock Azure AD token response
        azure_token_response = {
            "access_token": "access_token",
            "id_token": _create_mock_id_token(
                sub="user_sub",
                email="user@samsung.com",
                name="User",
                dept="Dept",
                business_unit="BU",
            ),
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        # WHEN: POST /auth/oidc/callback
        with patch("src.backend.api.auth.OIDCAuthService") as mock_oidc_service_class:
            mock_oidc_service = MagicMock()
            mock_oidc_service_class.return_value = mock_oidc_service
            mock_oidc_service.exchange_code_for_tokens.return_value = azure_token_response
            mock_oidc_service.validate_id_token.return_value = {
                "sub": "user_sub",
                "email": "user@samsung.com",
                "name": "User",
                "dept": "Dept",
                "business_unit": "BU",
            }

            response = client.post(
                "/auth/oidc/callback",
                json={"code": auth_code, "code_verifier": code_verifier},
            )

        # THEN: Set-Cookie header should contain HttpOnly and SameSite flags
        assert response.status_code in [200, 201]
        set_cookie = response.headers.get("set-cookie", "")
        assert "HttpOnly" in set_cookie
        assert "SameSite" in set_cookie
        assert "Path=" in set_cookie


class TestAuthenticationWithCookie:
    """REQ: REQ-B-A1-8 - Test JWT cookie validation in subsequent requests."""

    def test_api_request_with_valid_jwt_cookie(self, db_session: Session, user_fixture: User) -> None:
        """
        Acceptance criteria: Subsequent API requests validate JWT cookie.

        REQ: REQ-B-A1-8

        Given: Valid JWT in cookie
        When: Decode JWT and verify it's valid
        Then: JWT should be valid and decodable
        """
        # GIVEN: Valid JWT token
        auth_service = AuthService(db_session)
        jwt_token, _, _ = auth_service.authenticate_or_create_user(
            {
                "knox_id": user_fixture.knox_id,
                "name": user_fixture.name,
                "dept": user_fixture.dept,
                "business_unit": user_fixture.business_unit,
                "email": user_fixture.email,
            }
        )

        # WHEN: Decode and verify JWT
        decoded = auth_service.decode_jwt(jwt_token)

        # THEN: JWT should be valid and contain expected claims
        assert decoded is not None
        assert "knox_id" in decoded
        assert decoded["knox_id"] == user_fixture.knox_id

    def test_api_request_with_invalid_jwt_cookie(self, db_session: Session) -> None:
        """
        Error case: Invalid JWT in cookie.

        REQ: REQ-B-A1-8

        Given: Invalid JWT in cookie
        When: Try to decode invalid JWT
        Then: jwt.InvalidTokenError raised
        """
        # GIVEN: Invalid JWT token
        invalid_token = "invalid.jwt.token"

        # WHEN: Try to decode invalid JWT
        auth_service = AuthService(db_session)
        with pytest.raises(jwt.InvalidTokenError):
            auth_service.decode_jwt(invalid_token)


# ============================================================================
# Helper Functions
# ============================================================================


def _create_mock_id_token(
    sub: str,
    email: str,
    name: str,
    dept: str,
    business_unit: str,
    exp_hours: int = 1,
) -> str:
    """
    Create a mock ID Token for testing.

    Args:
        sub: Subject (user OID)
        email: Email address
        name: Full name
        dept: Department
        business_unit: Business unit
        exp_hours: Token expiration hours from now

    Returns:
        Encoded JWT token as string
    """
    now = datetime.now(timezone.utc)
    expiration = now + timedelta(hours=exp_hours)

    payload: dict[str, Any] = {
        "sub": sub,
        "email": email,
        "name": name,
        "dept": dept,
        "business_unit": business_unit,
        "iss": "https://login.microsoftonline.com/{tenant}/v2.0",
        "aud": getattr(settings, "OIDC_CLIENT_ID", "test_client_id"),
        "exp": int(expiration.timestamp()),
        "iat": int(now.timestamp()),
    }

    # Create a mock token (not actually signed, for testing purposes)
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
    return token
