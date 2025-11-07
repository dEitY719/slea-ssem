"""
Tests for profile service.

REQ: REQ-B-A2-1, REQ-B-A2-3, REQ-B-A2-5
"""

import pytest
from sqlalchemy.orm import Session

from src.backend.models.user import User
from src.backend.services.profile_service import ProfileService


class TestNicknameDuplicateCheck:
    """REQ-B-A2-1: Duplicate nickname check."""

    def test_check_available_nickname(self, db_session: Session) -> None:
        """Happy path: Nickname not taken."""
        service = ProfileService(db_session)
        result = service.check_nickname_availability("new_user")

        assert result["available"] is True
        assert result["suggestions"] == []

    def test_check_duplicate_nickname(self, db_session: Session, user_fixture: User) -> None:
        """Edge case: Nickname already taken."""
        service = ProfileService(db_session)
        result = service.check_nickname_availability(user_fixture.nickname)

        assert result["available"] is False
        assert len(result["suggestions"]) == 3

    def test_check_invalid_nickname_raises_error(self, db_session: Session) -> None:
        """Input validation: Invalid nickname raises ValueError."""
        service = ProfileService(db_session)

        with pytest.raises(ValueError, match="at least 3 characters"):
            service.check_nickname_availability("ab")

        with pytest.raises(ValueError, match="prohibited word"):
            service.check_nickname_availability("admin")


class TestNicknameAlternativeGeneration:
    """REQ-B-A2-3: Generate 3 alternative suggestions."""

    def test_generate_three_alternatives(self, db_session: Session) -> None:
        """Happy path: Generate 3 unique alternatives."""
        service = ProfileService(db_session)
        alts = service.generate_nickname_alternatives("john")

        assert len(alts) == 3
        assert "john_1" in alts
        assert "john_2" in alts
        assert "john_3" in alts

    def test_alternatives_are_available(self, db_session: Session, user_fixture: User) -> None:
        """Acceptance criteria: All suggestions must be available."""
        service = ProfileService(db_session)
        result = service.check_nickname_availability(user_fixture.nickname)
        alts = result["suggestions"]

        # All unique
        assert len(set(alts)) == 3

        # All available
        for alt in alts:
            check_result = service.check_nickname_availability(alt)
            assert check_result["available"] is True

    def test_alternatives_skip_taken_nicknames(self, db_session: Session) -> None:
        """Edge case: Skip already taken alternatives."""
        service = ProfileService(db_session)

        # Create users with john_1 and john_2
        user1 = User(
            knox_id="user_test_1",
            name="Test User 1",
            dept="Test",
            business_unit="Test",
            email="test1@example.com",
            nickname="john_1",
        )
        user2 = User(
            knox_id="user_test_2",
            name="Test User 2",
            dept="Test",
            business_unit="Test",
            email="test2@example.com",
            nickname="john_2",
        )
        db_session.add(user1)
        db_session.add(user2)
        db_session.commit()

        # Generate alternatives - should skip john_1 and john_2
        alts = service.generate_nickname_alternatives("john")

        assert len(alts) == 3
        assert "john_1" not in alts
        assert "john_2" not in alts
        assert "john_3" in alts


class TestProfileServiceRegistration:
    """REQ-B-A2-5: Save user record with nickname."""

    def test_register_new_nickname(self, db_session: Session) -> None:
        """Happy path: Register nickname for user."""
        # Create a user first (simulating REQ-B-A1)
        user = User(
            knox_id="test_user",
            name="Test User",
            dept="Test",
            business_unit="Test",
            email="test@example.com",
        )
        db_session.add(user)
        db_session.commit()

        # Register nickname
        service = ProfileService(db_session)
        result = service.register_nickname(user.id, "alice_nickname")

        assert result["user_id"] == user.id
        assert result["nickname"] == "alice_nickname"
        assert "updated_at" in result

        # Verify in DB
        db_session.refresh(user)
        assert user.nickname == "alice_nickname"

    def test_cannot_register_invalid_nickname(self, db_session: Session) -> None:
        """Input validation: Reject invalid nicknames."""
        # Create user
        user = User(
            knox_id="test_user",
            name="Test User",
            dept="Test",
            business_unit="Test",
            email="test@example.com",
        )
        db_session.add(user)
        db_session.commit()

        service = ProfileService(db_session)

        # Test too short
        with pytest.raises(ValueError, match="at least 3 characters"):
            service.register_nickname(user.id, "ab")

        # Test forbidden word
        with pytest.raises(ValueError, match="prohibited word"):
            service.register_nickname(user.id, "admin")

    def test_cannot_register_duplicate_nickname(self, db_session: Session, user_fixture: User) -> None:
        """Edge case: Cannot register duplicate nickname."""
        # Create another user
        user2 = User(
            knox_id="test_user_2",
            name="Test User 2",
            dept="Test",
            business_unit="Test",
            email="test2@example.com",
        )
        db_session.add(user2)
        db_session.commit()

        service = ProfileService(db_session)

        # Try to register same nickname as user_fixture
        with pytest.raises(ValueError, match="already taken"):
            service.register_nickname(user2.id, user_fixture.nickname)

    def test_register_user_not_found(self, db_session: Session) -> None:
        """Edge case: User not found raises exception."""
        service = ProfileService(db_session)

        with pytest.raises(Exception, match="not found"):
            service.register_nickname(99999, "alice_nickname")
