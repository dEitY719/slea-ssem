"""
Tests for survey service.

REQ: REQ-B-B1-1, REQ-B-B1-2
"""

from sqlalchemy.orm import Session

from src.backend.models.user import User
from src.backend.services.survey_service import SurveyService


class TestSurveySchema:
    """REQ-B-B1-1: Survey schema tests."""

    def test_get_survey_schema_structure(self, db_session: Session) -> None:
        """Happy path: Get survey schema structure."""
        service = SurveyService(db_session)
        schema = service.get_survey_schema()

        assert "fields" in schema
        assert isinstance(schema["fields"], list)
        assert len(schema["fields"]) > 0

    def test_schema_contains_all_fields(self, db_session: Session) -> None:
        """Happy path: Schema contains all required fields."""
        service = SurveyService(db_session)
        schema = service.get_survey_schema()

        field_names = [f["name"] for f in schema["fields"]]
        assert "self_level" in field_names
        assert "years_experience" in field_names
        assert "job_role" in field_names
        assert "duty" in field_names
        assert "interests" in field_names

    def test_schema_field_metadata(self, db_session: Session) -> None:
        """Happy path: Each field has required metadata."""
        service = SurveyService(db_session)
        schema = service.get_survey_schema()

        for field in schema["fields"]:
            assert "name" in field
            assert "type" in field
            assert "label" in field
            assert "help_text" in field

    def test_self_level_field_validation(self, db_session: Session) -> None:
        """Edge case: self_level field validation rules."""
        service = SurveyService(db_session)
        schema = service.get_survey_schema()

        self_level_field = next(f for f in schema["fields"] if f["name"] == "self_level")
        assert self_level_field["type"] == "enum"
        assert "choices" in self_level_field
        assert set(self_level_field["choices"]) == {"beginner", "intermediate", "advanced"}

    def test_years_experience_field_validation(self, db_session: Session) -> None:
        """Edge case: years_experience field validation rules."""
        service = SurveyService(db_session)
        schema = service.get_survey_schema()

        years_field = next(f for f in schema["fields"] if f["name"] == "years_experience")
        assert years_field["type"] == "integer"
        assert years_field["min"] == 0
        assert years_field["max"] == 60

    def test_interests_field_choices(self, db_session: Session) -> None:
        """Edge case: interests field has predefined choices."""
        service = SurveyService(db_session)
        schema = service.get_survey_schema()

        interests_field = next(f for f in schema["fields"] if f["name"] == "interests")
        assert interests_field["type"] == "array"
        assert "choices" in interests_field
        assert len(interests_field["choices"]) > 0
        # Check for specific categories
        choices = interests_field["choices"]
        assert "AI" in choices
        assert "LLM" in choices
        assert "RAG" in choices


class TestSurveySubmit:
    """REQ-B-B1-2: Survey submission tests."""

    def test_submit_survey_valid_data(self, db_session: Session, user_fixture: User) -> None:
        """Happy path: Submit survey with valid data."""
        service = SurveyService(db_session)
        survey_data = {
            "self_level": "intermediate",
            "years_experience": 3,
            "job_role": "Engineer",
            "duty": "ML Development",
            "interests": ["LLM", "RAG"],
        }

        result = service.submit_survey(user_fixture.id, survey_data)

        assert result["user_id"] == user_fixture.id
        assert result["self_level"] == "Intermediate"
        assert "survey_id" in result
        assert "submitted_at" in result
