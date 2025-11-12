"""
Tests for authentication API endpoint.

REQ: REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3, REQ-B-A1-4
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
