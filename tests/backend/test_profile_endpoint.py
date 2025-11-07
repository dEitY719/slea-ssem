"""
Tests for profile API endpoints.

REQ: REQ-B-A2-1, REQ-B-A2-2, REQ-B-A2-3, REQ-B-A2-5
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.backend.models.user import User


class TestProfileEndpoint:
    """REQ-B-A2-1, 2, 3, 5: FastAPI endpoints."""

    def test_post_profile_check_nickname_available(self, client: TestClient) -> None:
        """Integration test: POST /profile/nickname/check - available."""
        payload = {"nickname": "new_user_123"}

        response = client.post("/profile/nickname/check", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        assert data["suggestions"] == []

    def test_post_profile_check_nickname_taken(self, client: TestClient, user_fixture: User) -> None:
        """Integration test: POST /profile/nickname/check - taken with suggestions."""
        payload = {"nickname": user_fixture.nickname}

        response = client.post("/profile/nickname/check", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
        assert len(data["suggestions"]) == 3

    def test_post_profile_check_nickname_invalid(self, client: TestClient) -> None:
        """Integration test: POST /profile/nickname/check - invalid format."""
        # Test too short
        response = client.post("/profile/nickname/check", json={"nickname": "ab"})
        assert response.status_code == 400
        assert "at least 3 characters" in response.json()["detail"]

        # Test forbidden word
        response = client.post("/profile/nickname/check", json={"nickname": "admin"})
        assert response.status_code == 400
        assert "prohibited word" in response.json()["detail"]

        # Test invalid characters
        response = client.post("/profile/nickname/check", json={"nickname": "user@domain"})
        assert response.status_code == 400
        assert "letters, numbers, and underscores" in response.json()["detail"]

    def test_post_profile_register_nickname(self, client: TestClient, db_session: Session) -> None:
        """Integration test: POST /profile/register - successful registration."""
        from src.backend.models.user import User

        # Create a user with id=1 (required because endpoint uses hardcoded user_id=1)
        user = User(
            knox_id="register_test_user",
            name="Register Test User",
            dept="Test",
            business_unit="Test",
            email="register@example.com",
        )
        db_session.add(user)
        db_session.commit()

        payload = {"nickname": "john_doe"}

        response = client.post("/profile/register", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["nickname"] == "john_doe"
        assert "user_id" in data
        assert "updated_at" in data

    def test_post_profile_register_invalid_nickname(self, client: TestClient) -> None:
        """Integration test: POST /profile/register - validation error."""
        # Test too short
        response = client.post("/profile/register", json={"nickname": "ab"})
        assert response.status_code == 400
        assert "at least 3 characters" in response.json()["detail"]

        # Test forbidden word
        response = client.post("/profile/register", json={"nickname": "admin"})
        assert response.status_code == 400
        assert "prohibited word" in response.json()["detail"]

    def test_post_profile_register_duplicate_nickname(self, client: TestClient, user_fixture: User) -> None:
        """Integration test: POST /profile/register - duplicate nickname."""
        payload = {"nickname": user_fixture.nickname}

        response = client.post("/profile/register", json=payload)

        assert response.status_code == 400
        assert "already taken" in response.json()["detail"]
