"""
Tests for survey API endpoints.

REQ: REQ-B-B1-1, REQ-B-B1-2
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.backend.models.user import User


class TestGetSurveySchema:
    """REQ-B-B1-1: GET /survey/schema endpoint tests."""

    def test_get_survey_schema_success(self, client: TestClient) -> None:
        """Integration test: GET /survey/schema - success."""
        response = client.get("/survey/schema")

        assert response.status_code == 200
        data = response.json()
        assert "fields" in data
        assert isinstance(data["fields"], list)
        assert len(data["fields"]) > 0

    def test_get_survey_schema_field_structure(self, client: TestClient) -> None:
        """Integration test: GET /survey/schema - field metadata."""
        response = client.get("/survey/schema")

        assert response.status_code == 200
        data = response.json()

        # Check that each field has required metadata
        for field in data["fields"]:
            assert "name" in field
            assert "type" in field
            assert "label" in field
            assert "help_text" in field

    def test_get_survey_schema_contains_interests_choices(self, client: TestClient) -> None:
        """Integration test: GET /survey/schema - interests field choices."""
        response = client.get("/survey/schema")

        assert response.status_code == 200
        data = response.json()

        interests_field = next(f for f in data["fields"] if f["name"] == "interests")
        assert "choices" in interests_field
        assert "AI" in interests_field["choices"]
        assert "LLM" in interests_field["choices"]


class TestPostSurveySubmit:
    """REQ-B-B1-2: POST /survey/submit endpoint tests."""

    def test_post_survey_submit_success(self, client: TestClient, db_session: Session) -> None:
        """Integration test: POST /survey/submit - successful submission."""
        # Create user with id=1 (endpoint uses hardcoded user_id=1)
        user = User(
            knox_id="survey_submit_user",
            name="Survey Submit User",
            dept="Test",
            business_unit="Test",
            email="survey_submit@example.com",
        )
        db_session.add(user)
        db_session.commit()

        payload = {
            "self_level": "intermediate",
            "years_experience": 3,
            "job_role": "Engineer",
            "duty": "Development",
            "interests": ["AI", "LLM"],
        }
        response = client.post("/survey/submit", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["self_level"] == "Intermediate"
        assert "survey_id" in data
        assert "user_id" in data
        assert "submitted_at" in data

    def test_post_survey_submit_invalid_level(self, client: TestClient, db_session: Session) -> None:
        """Integration test: POST /survey/submit - invalid level."""
        # Create user with id=1
        user = User(
            knox_id="invalid_level_survey_user",
            name="Invalid Level Survey User",
            dept="Test",
            business_unit="Test",
            email="invalid_survey@example.com",
        )
        db_session.add(user)
        db_session.commit()

        payload = {"self_level": "expert"}
        response = client.post("/survey/submit", json=payload)

        assert response.status_code == 400
        assert "Invalid self_level" in response.json()["detail"]

    def test_post_survey_submit_invalid_interests(self, client: TestClient, db_session: Session) -> None:
        """Integration test: POST /survey/submit - invalid interests."""
        # Create user with id=1
        user = User(
            knox_id="invalid_interests_survey_user",
            name="Invalid Interests Survey User",
            dept="Test",
            business_unit="Test",
            email="invalid_interests_survey@example.com",
        )
        db_session.add(user)
        db_session.commit()

        payload = {"interests": []}
        response = client.post("/survey/submit", json=payload)

        assert response.status_code == 400
        assert "between 1 and 20 items" in response.json()["detail"]

    def test_post_survey_submit_empty_body(self, client: TestClient, db_session: Session) -> None:
        """Integration test: POST /survey/submit - empty body (all optional)."""
        # Create user with id=1
        user = User(
            knox_id="empty_survey_user",
            name="Empty Survey User",
            dept="Test",
            business_unit="Test",
            email="empty_survey@example.com",
        )
        db_session.add(user)
        db_session.commit()

        payload = {}
        response = client.post("/survey/submit", json=payload)

        assert response.status_code == 201
        assert "survey_id" in response.json()
