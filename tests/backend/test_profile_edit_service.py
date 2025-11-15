"""
Tests for profile edit service.

REQ: REQ-B-A2-Edit-1, REQ-B-A2-Edit-2, REQ-B-A2-Edit-3
"""

import pytest
from sqlalchemy.orm import Session

from src.backend.models.user import User
from src.backend.models.user_profile import UserProfileSurvey
from src.backend.services.profile_service import ProfileService


class TestNicknameEditService:
    """REQ-B-A2-Edit-1, 2: Nickname edit tests."""

    def test_check_nickname_available_for_edit_self(self, db_session: Session, user_fixture: User) -> None:
        """Happy path: User can keep their own nickname."""
        service = ProfileService(db_session)
        result = service.check_nickname_available_for_edit(user_fixture.id, user_fixture.nickname)

        assert result["available"] is True
        assert result["suggestions"] == []

    def test_check_nickname_available_for_edit_taken_by_others(self, db_session: Session, user_fixture: User) -> None:
        """Edge case: Nickname taken by another user."""
        # Create another user
        user2 = User(
            knox_id="user_2",
            name="Another User",
            dept="Test",
            business_unit="Test",
            email="user2@example.com",
            nickname="bob_nickname",
        )
        db_session.add(user2)
        db_session.commit()

        service = ProfileService(db_session)
        # user1 tries to use user2's nickname
        result = service.check_nickname_available_for_edit(user_fixture.id, user2.nickname)

        assert result["available"] is False
        assert len(result["suggestions"]) == 3

    def test_check_nickname_available_for_edit_new_available(self, db_session: Session, user_fixture: User) -> None:
        """Happy path: New nickname available."""
        service = ProfileService(db_session)
        result = service.check_nickname_available_for_edit(user_fixture.id, "new_available_nickname")

        assert result["available"] is True
        assert result["suggestions"] == []

    def test_edit_nickname_success(self, db_session: Session, user_fixture: User) -> None:
        """Happy path: Edit nickname successfully."""
        service = ProfileService(db_session)
        result = service.edit_nickname(user_fixture.id, "new_nickname")

        assert result["user_id"] == user_fixture.id
        assert result["nickname"] == "new_nickname"
        assert "updated_at" in result

        # Verify in DB
        db_session.refresh(user_fixture)
        assert user_fixture.nickname == "new_nickname"

    def test_edit_nickname_with_self(self, db_session: Session, user_fixture: User) -> None:
        """Edge case: User can change to their own nickname."""
        service = ProfileService(db_session)
        result = service.edit_nickname(user_fixture.id, user_fixture.nickname)

        assert result["nickname"] == user_fixture.nickname
        db_session.refresh(user_fixture)
        assert user_fixture.nickname == user_fixture.nickname

    def test_edit_nickname_duplicate_by_others(self, db_session: Session, user_fixture: User) -> None:
        """Edge case: Cannot edit to nickname taken by others."""
        # Create another user
        user2 = User(
            knox_id="user_2",
            name="Another User",
            dept="Test",
            business_unit="Test",
            email="user2@example.com",
            nickname="taken_nickname",
        )
        db_session.add(user2)
        db_session.commit()

        service = ProfileService(db_session)
        # user1 tries to change to user2's nickname
        with pytest.raises(ValueError, match="already taken"):
            service.edit_nickname(user_fixture.id, user2.nickname)

    def test_edit_nickname_invalid_format(self, db_session: Session, user_fixture: User) -> None:
        """Input validation: Invalid nickname format."""
        service = ProfileService(db_session)

        with pytest.raises(ValueError, match="at least 3 characters"):
            service.edit_nickname(user_fixture.id, "ab")

        with pytest.raises(ValueError, match="prohibited word"):
            service.edit_nickname(user_fixture.id, "admin")

    def test_edit_nickname_user_not_found(self, db_session: Session) -> None:
        """Edge case: User not found."""
        service = ProfileService(db_session)

        with pytest.raises(Exception, match="not found"):
            service.edit_nickname(99999, "new_nickname")


class TestSurveyEditService:
    """REQ-B-A2-Edit-3: Survey edit tests."""

    def test_update_survey_new_record(self, db_session: Session, user_fixture: User) -> None:
        """Happy path: Create new survey record."""
        service = ProfileService(db_session)
        survey_data = {
            "self_level": "intermediate",
            "years_experience": 3,
            "job_role": "Engineer",
            "duty": "Development",
            "interests": ["AI", "ML"],
        }
        result = service.update_survey(user_fixture.id, survey_data)

        assert result["user_id"] == user_fixture.id
        assert result["self_level"] == "Intermediate"
        assert "survey_id" in result
        assert "submitted_at" in result

    def test_update_survey_all_fields(self, db_session: Session, user_fixture: User) -> None:
        """Happy path: Survey with all fields."""
        service = ProfileService(db_session)
        survey_data = {
            "self_level": "advanced",
            "years_experience": 5,
            "job_role": "Senior Engineer",
            "duty": "ML Model Development",
            "interests": ["LLM", "RAG", "Robotics"],
        }
        result = service.update_survey(user_fixture.id, survey_data)

        assert result["self_level"] == "Advanced"

        # Verify in DB
        survey = db_session.query(UserProfileSurvey).filter_by(id=result["survey_id"]).first()
        assert survey is not None
        assert survey.years_experience == 5
        assert survey.interests == ["LLM", "RAG", "Robotics"]

    def test_update_survey_partial_fields(self, db_session: Session, user_fixture: User) -> None:
        """Happy path: Survey with only some fields."""
        service = ProfileService(db_session)
        survey_data = {"self_level": "beginner"}
        result = service.update_survey(user_fixture.id, survey_data)

        survey = db_session.query(UserProfileSurvey).filter_by(id=result["survey_id"]).first()
        assert survey.self_level == "Beginner"
        assert survey.years_experience is None
        assert survey.job_role is None

    def test_update_survey_preserves_history(self, db_session: Session, user_fixture: User) -> None:
        """Acceptance criteria: Previous surveys preserved."""
        service = ProfileService(db_session)

        # First survey
        result1 = service.update_survey(user_fixture.id, {"self_level": "beginner"})
        survey_id_1 = result1["survey_id"]

        # Second survey
        result2 = service.update_survey(user_fixture.id, {"self_level": "intermediate"})
        survey_id_2 = result2["survey_id"]

        # Both should exist in DB
        survey1 = db_session.query(UserProfileSurvey).filter_by(id=survey_id_1).first()
        survey2 = db_session.query(UserProfileSurvey).filter_by(id=survey_id_2).first()

        assert survey1 is not None
        assert survey2 is not None
        assert survey1.self_level == "Beginner"
        assert survey2.self_level == "Intermediate"

    def test_update_survey_invalid_level(self, db_session: Session, user_fixture: User) -> None:
        """Input validation: Invalid self_level."""
        service = ProfileService(db_session)

        with pytest.raises(ValueError, match="Invalid self_level"):
            service.update_survey(user_fixture.id, {"self_level": "expert"})

    def test_update_survey_invalid_years_experience(self, db_session: Session, user_fixture: User) -> None:
        """Input validation: Invalid years_experience."""
        service = ProfileService(db_session)

        with pytest.raises(ValueError, match="must be an integer between 0 and 60"):
            service.update_survey(user_fixture.id, {"years_experience": -1})

        with pytest.raises(ValueError, match="must be an integer between 0 and 60"):
            service.update_survey(user_fixture.id, {"years_experience": 100})

    def test_update_survey_invalid_job_role(self, db_session: Session, user_fixture: User) -> None:
        """Input validation: Invalid job_role."""
        service = ProfileService(db_session)

        with pytest.raises(ValueError, match="between 1 and 100 characters"):
            service.update_survey(user_fixture.id, {"job_role": ""})

        with pytest.raises(ValueError, match="between 1 and 100 characters"):
            service.update_survey(user_fixture.id, {"job_role": "a" * 101})

    def test_update_survey_invalid_duty(self, db_session: Session, user_fixture: User) -> None:
        """Input validation: Invalid duty."""
        service = ProfileService(db_session)

        with pytest.raises(ValueError, match="between 1 and 500 characters"):
            service.update_survey(user_fixture.id, {"duty": "a" * 501})

    def test_update_survey_invalid_interests(self, db_session: Session, user_fixture: User) -> None:
        """Input validation: Invalid interests."""
        service = ProfileService(db_session)

        with pytest.raises(ValueError, match="must be a list"):
            service.update_survey(user_fixture.id, {"interests": "not_a_list"})

        with pytest.raises(ValueError, match="must have between 1 and 20 items"):
            service.update_survey(user_fixture.id, {"interests": []})

        with pytest.raises(ValueError, match="must be strings"):
            service.update_survey(user_fixture.id, {"interests": [1, 2, 3]})

    def test_update_survey_user_not_found(self, db_session: Session) -> None:
        """Edge case: User not found."""
        service = ProfileService(db_session)

        with pytest.raises(Exception, match="not found"):
            service.update_survey(99999, {"self_level": "beginner"})
