"""
Tests for authentication API endpoint.

REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3, REQ-B-A1-4, REQ-B-A1-9
"""

from fastapi.testclient import TestClient

from src.backend.models.user import User


class TestAuthEndpoint:
    """REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3, REQ-B-A1-4 - Test FastAPI authentication endpoint."""

    def test_post_auth_login_new_user(self, client: TestClient) -> None:
        """
        Integration test: POST /auth/login with new user data.

        REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3

        Given: New user data
        When: POST /auth/login
        Then: 201 Created with JWT + is_new_user=true
        """
        # GIVEN: New user data
        payload = {
            "knox_id": "user123",
            "name": "John Doe",
            "dept": "AI Lab",
            "business_unit": "Research",
            "email": "john.doe@samsung.com",
        }

        # WHEN: POST /auth/login
        response = client.post("/auth/login", json=payload)

        # THEN: 201 Created with JWT + flag
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["is_new_user"] is True
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        assert "user_id" in data
        assert isinstance(data["user_id"], int)
        assert data["user_id"] > 0

    def test_post_auth_login_existing_user(self, client: TestClient, user_fixture: User) -> None:
        """
        Integration test: POST /auth/login with existing user.

        REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-4

        Given: Existing user data
        When: POST /auth/login
        Then: 200 OK with new JWT + is_new_user=false
        """
        # GIVEN: Existing user data
        payload = {
            "knox_id": user_fixture.knox_id,
            "name": user_fixture.name,
            "dept": user_fixture.dept,
            "business_unit": user_fixture.business_unit,
            "email": user_fixture.email,
        }

        # WHEN: POST /auth/login
        response = client.post("/auth/login", json=payload)

        # THEN: 200 OK with JWT + flag
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["is_new_user"] is False
        assert isinstance(data["access_token"], str)
        assert "user_id" in data
        assert isinstance(data["user_id"], int)
        assert data["user_id"] == user_fixture.id

    def test_post_auth_login_missing_required_field(self, client: TestClient) -> None:
        """
        Integration test: POST /auth/login missing required field.

        REQ: REQ-B-A1-1

        Given: Incomplete user data
        When: POST /auth/login
        Then: 400 Bad Request
        """
        # GIVEN: Incomplete user data (missing email)
        payload = {
            "knox_id": "user123",
            "name": "John Doe",
            "dept": "AI Lab",
            "business_unit": "Research",
            # Missing: "email"
        }

        # WHEN: POST /auth/login
        response = client.post("/auth/login", json=payload)

        # THEN: 400 Bad Request
        assert response.status_code == 422  # Pydantic validation error

    def test_post_auth_login_invalid_payload(self, client: TestClient) -> None:
        """
        Integration test: POST /auth/login with invalid JSON.

        Given: Invalid JSON payload
        When: POST /auth/login
        Then: 422 Unprocessable Entity
        """
        # GIVEN: Invalid JSON (missing all fields)
        payload = {}

        # WHEN: POST /auth/login
        response = client.post("/auth/login", json=payload)

        # THEN: 422 Unprocessable Entity
        assert response.status_code == 422


class TestAuthStatusEndpoint:
    """REQ: REQ-B-A1-9 - Test authentication status check endpoint."""

    def test_get_auth_status_authenticated(self, client: TestClient, user_fixture: User) -> None:
        """
        Integration test: GET /auth/status with valid JWT cookie.

        REQ: REQ-B-A1-9

        Given: Valid JWT token in auth_token cookie
        When: GET /auth/status
        Then: 200 OK with {authenticated: true, user_id, knox_id}
        """
        # GIVEN: Create JWT token for user
        from src.backend.services.auth_service import AuthService
        from src.backend.database import SessionLocal

        db = SessionLocal()
        try:
            auth_service = AuthService(db)
            jwt_token, _, _ = auth_service.authenticate_or_create_user({
                "knox_id": user_fixture.knox_id,
                "name": user_fixture.name,
                "dept": user_fixture.dept,
                "business_unit": user_fixture.business_unit,
                "email": user_fixture.email,
            })
        finally:
            db.close()

        # WHEN: GET /auth/status with JWT in cookie
        response = client.get("/auth/status", cookies={"auth_token": jwt_token})

        # THEN: 200 OK with authenticated status
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["user_id"] == user_fixture.id
        assert data["knox_id"] == user_fixture.knox_id

    def test_get_auth_status_no_cookie(self, client: TestClient) -> None:
        """
        Integration test: GET /auth/status without JWT cookie.

        REQ: REQ-B-A1-9

        Given: No auth_token cookie provided
        When: GET /auth/status
        Then: 200 OK with {authenticated: false}
        """
        # GIVEN: No cookie provided

        # WHEN: GET /auth/status without cookie
        response = client.get("/auth/status")

        # THEN: 200 OK with authenticated: false
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False

    def test_get_auth_status_invalid_token(self, client: TestClient) -> None:
        """
        Integration test: GET /auth/status with invalid JWT token.

        REQ: REQ-B-A1-9

        Given: Invalid JWT token
        When: GET /auth/status
        Then: 200 OK with {authenticated: false}
        """
        # GIVEN: Invalid JWT token
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid_payload.invalid_signature"

        # WHEN: GET /auth/status with invalid token
        response = client.get("/auth/status", cookies={"auth_token": invalid_token})

        # THEN: 200 OK with authenticated: false
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False

    def test_get_auth_status_expired_token(self, client: TestClient) -> None:
        """
        Integration test: GET /auth/status with expired JWT token.

        REQ: REQ-B-A1-9

        Given: Expired JWT token
        When: GET /auth/status
        Then: 200 OK with {authenticated: false}
        """
        # GIVEN: Create expired token
        from datetime import UTC, datetime, timedelta
        from src.backend.config import settings
        import jwt

        now = datetime.now(UTC)
        expired_payload = {
            "knox_id": "user123",
            "iat": now - timedelta(hours=25),
            "exp": now - timedelta(hours=1),  # Expired 1 hour ago
        }
        expired_token = jwt.encode(
            expired_payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        # WHEN: GET /auth/status with expired token
        response = client.get("/auth/status", cookies={"auth_token": expired_token})

        # THEN: 200 OK with authenticated: false
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False

    def test_get_auth_status_token_without_knox_id(self, client: TestClient) -> None:
        """
        Integration test: GET /auth/status with token missing knox_id.

        REQ: REQ-B-A1-9

        Given: JWT token without knox_id in payload
        When: GET /auth/status
        Then: 200 OK with {authenticated: false}
        """
        # GIVEN: Token without knox_id
        from datetime import UTC, datetime, timedelta
        from src.backend.config import settings
        import jwt

        now = datetime.now(UTC)
        expiration = now + timedelta(hours=24)
        invalid_payload = {
            "iat": now,
            "exp": expiration,
            # Missing: "knox_id"
        }
        token_without_knox_id = jwt.encode(
            invalid_payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

        # WHEN: GET /auth/status with token missing knox_id
        response = client.get("/auth/status", cookies={"auth_token": token_without_knox_id})

        # THEN: 200 OK with authenticated: false
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is False
