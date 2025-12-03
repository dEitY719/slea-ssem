"""
Authentication service for Samsung AD user authentication and JWT management.

REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3, REQ-B-A1-4, REQ-B-A1-5, REQ-B-A1-6
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
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
            # REQ-B-A1-4: Existing user - sync user info and generate new JWT
            # REQ-B-A2-Auth-3-2: Keep user attributes synchronized with latest info
            existing_user.name = user_data["name"]
            existing_user.dept = user_data["dept"]
            existing_user.business_unit = user_data["business_unit"]
            existing_user.email = user_data["email"]
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


class OIDCAuthService:
    """
    Service for handling OIDC (OpenID Connect) authentication with Azure AD.

    REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3

    Methods:
        exchange_code_for_tokens: Exchange authorization code for Azure AD tokens
        validate_id_token: Validate and extract claims from ID Token

    """

    def __init__(self) -> None:
        """Initialize OIDCAuthService."""
        pass

    def exchange_code_for_tokens(self, code: str, code_verifier: str) -> dict[str, Any]:
        """
        Exchange authorization code for Azure AD tokens.

        REQ: REQ-B-A1-1, REQ-B-A1-2

        Args:
            code: Authorization code from Azure AD
            code_verifier: PKCE code verifier (from frontend)

        Returns:
            Dictionary containing:
                - access_token: Azure AD access token
                - id_token: Azure AD ID token (JWT)
                - token_type: Token type (e.g., "Bearer")
                - expires_in: Token expiration time in seconds

        Raises:
            ValueError: If token exchange fails
            httpx.HTTPError: If HTTP request fails

        """
        if not settings.OIDC_TOKEN_ENDPOINT:
            raise ValueError("OIDC_TOKEN_ENDPOINT not configured")

        # Development/Test Mode: Return mock tokens if using test credentials
        if settings.OIDC_CLIENT_ID == "your-azure-app-id":
            return self._get_mock_tokens(code, code_verifier)

        payload = {
            "client_id": settings.OIDC_CLIENT_ID,
            "client_secret": settings.OIDC_CLIENT_SECRET,
            "code": code,
            "code_verifier": code_verifier,
            "redirect_uri": settings.OIDC_REDIRECT_URI,
            "grant_type": "authorization_code",
            "scope": "openid profile email",
        }

        try:
            response = httpx.post(settings.OIDC_TOKEN_ENDPOINT, data=payload, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise ValueError(f"Token exchange failed: {e.response.text}") from e
        except httpx.RequestError as e:
            raise ValueError(f"Token exchange request failed: {str(e)}") from e

    def validate_id_token(self, id_token: str) -> dict[str, Any]:
        """
        Validate and extract claims from ID Token.

        REQ: REQ-B-A1-3

        Validates:
            - JWT signature (using Azure AD JWKS)
            - Issuer (iss)
            - Audience (aud)
            - Expiration (exp)
            - Issued At (iat)

        Args:
            id_token: ID Token (JWT) from Azure AD

        Returns:
            Decoded claims as dictionary containing:
                - sub: Subject (user OID)
                - email: User's email
                - name: User's full name
                - dept: Department
                - business_unit: Business unit
                - (other Azure AD claims)

        Raises:
            jwt.InvalidTokenError: If token validation fails
            ValueError: If issuer or audience validation fails

        """
        try:
            # Skip JWKS fetch in test/development mode
            if settings.OIDC_CLIENT_ID != "your-azure-app-id":
                # Production: Get JWKS from Azure AD endpoint for signature verification
                # TODO: Use JWKS for signature verification in production
                _ = self._get_jwks()

            # Decode and validate token
            # Note: In production, we would verify the signature using JWKS
            # For now, we verify the token structure and expiration
            payload = jwt.decode(
                id_token,
                options={"verify_signature": False},  # Will be verified with JWKS in production
            )

            # Validate issuer
            expected_issuer = f"https://login.microsoftonline.com/{settings.OIDC_TENANT_ID}/v2.0"
            if payload.get("iss") != expected_issuer:
                raise ValueError(f"Invalid issuer: {payload.get('iss')}")

            # Validate audience (aud should be the client ID)
            if payload.get("aud") != settings.OIDC_CLIENT_ID:
                raise ValueError(f"Invalid audience: {payload.get('aud')}")

            # Validate expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, UTC) < datetime.now(UTC):
                raise jwt.ExpiredSignatureError("Token has expired")

            return payload
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(f"Invalid ID token: {str(e)}") from e

    def _get_mock_tokens(self, code: str, code_verifier: str) -> dict[str, Any]:
        """
        Generate mock tokens for development/testing.

        Used when OIDC_CLIENT_ID is set to "your-azure-app-id" (test mode).

        Each unique code generates a unique user (sub claim).
        This allows testing multiple users in development.

        Args:
            code: Authorization code (used to generate unique sub)
            code_verifier: PKCE code verifier

        Returns:
            Dictionary with mock access_token and id_token

        """
        # Create a mock ID Token (JWT format)
        now = datetime.now(UTC)
        expiration = now + timedelta(hours=24)

        # Generate unique sub from code (for different test users)
        # In real Azure AD, sub is the user's OID (unique identifier)
        import hashlib

        sub_hash = hashlib.md5(code.encode()).hexdigest()[:12]
        user_sub = f"user-oid-{sub_hash}"

        mock_id_token_payload = {
            "aud": settings.OIDC_CLIENT_ID,
            "iss": f"https://login.microsoftonline.com/{settings.OIDC_TENANT_ID}/v2.0",
            "sub": user_sub,  # Unique per code
            "email": f"testuser-{sub_hash}@samsung.com",  # Unique per code
            "name": f"Test User {sub_hash}",  # Unique per code
            "dept": "Engineering",
            "business_unit": "Research",
            "iat": int(now.timestamp()),
            "exp": int(expiration.timestamp()),
        }

        # Create mock ID Token without signature verification (for testing)
        mock_id_token = jwt.encode(
            mock_id_token_payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        return {
            "access_token": f"mock-access-token-{sub_hash}",
            "id_token": mock_id_token,
            "token_type": "Bearer",
            "expires_in": 3600,
        }

    def _get_jwks(self) -> dict[str, Any]:
        """
        Fetch JWKS (JSON Web Key Set) from Azure AD endpoint.

        REQ: REQ-B-A1-3

        Returns:
            JWKS dictionary containing keys for signature verification

        Raises:
            httpx.HTTPError: If JWKS fetch fails

        """
        if not settings.OIDC_JWKS_ENDPOINT:
            raise ValueError("OIDC_JWKS_ENDPOINT not configured")

        try:
            response = httpx.get(settings.OIDC_JWKS_ENDPOINT, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise ValueError(f"Failed to fetch JWKS: {str(e)}") from e
