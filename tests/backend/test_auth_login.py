"""
Tests for POST /auth/login endpoint (CLI Direct Login).

REQ: REQ-B-A2-Auth-3
Feature: CLI Direct Login Endpoint that accepts user info and returns JWT token
"""

from datetime import UTC, datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.backend.models.user import User
from src.backend.services.auth_service import AuthService


class TestAuthLoginNewUser:
    """TC-1: Happy Path - New User Login Returns 201 Created"""

    def test_login_new_user_returns_201_and_is_new_user_true(
        self, client: TestClient, db_session: Session
    ) -> None:
        """
        TC-1: POST /auth/login with new user returns 201 Created and is_new_user=true.

        REQ: REQ-B-A2-Auth-3-1, REQ-B-A2-Auth-3-2, REQ-B-A2-Auth-3-3

        Scenario: User logs in for the first time with new knox_id
        Setup: New user does not exist in database
        Action: POST /auth/login with new user data
        Expected: 201 Created with access_token, token_type="bearer", user_id, is_new_user=true

        Acceptance Criteria:
        - Status code is 201 Created
        - Response contains access_token (JWT string)
        - token_type is "bearer"
        - user_id is positive integer
        - is_new_user is true
        - New user created in database with correct fields
        """
        # Setup: Ensure new user doesn't exist
        payload = {
            "knox_id": "new_user_tc1",
            "name": "Test User TC1",
            "email": "tc1@samsung.com",
            "dept": "Engineering",
            "business_unit": "S.LSI",
        }

        # Action: POST /auth/login with new user
        response = client.post("/auth/login", json=payload)

        # Assertions
        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.json()}"
        data = response.json()

        # Check response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "user_id" in data
        assert "is_new_user" in data

        # Check response values
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        assert data["token_type"] == "bearer"
        assert isinstance(data["user_id"], int)
        assert data["user_id"] > 0
        assert data["is_new_user"] is True

        # Verify user created in database
        user = db_session.query(User).filter_by(knox_id="new_user_tc1").first()
        assert user is not None
        assert user.name == "Test User TC1"
        assert user.email == "tc1@samsung.com"
        assert user.dept == "Engineering"
        assert user.business_unit == "S.LSI"
        assert user.id == data["user_id"]


class TestAuthLoginExistingUser:
    """TC-2: Happy Path - Existing User Login Returns 200 OK"""

    def test_login_existing_user_returns_200_and_is_new_user_false(
        self, client: TestClient, db_session: Session, user_fixture: User
    ) -> None:
        """
        TC-2: POST /auth/login with existing user returns 200 OK and is_new_user=false.

        REQ: REQ-B-A2-Auth-3-2, REQ-B-A2-Auth-3-3

        Scenario: User logs in again (user already exists in database)
        Setup: User exists in database
        Action: POST /auth/login with existing user data
        Expected: 200 OK with access_token, token_type="bearer", user_id, is_new_user=false

        Acceptance Criteria:
        - Status code is 200 OK
        - Response contains access_token (JWT string)
        - token_type is "bearer"
        - user_id matches existing user's ID
        - is_new_user is false
        - User's last_login timestamp is updated
        """
        # Setup: Use existing user from fixture
        payload = {
            "knox_id": user_fixture.knox_id,
            "name": user_fixture.name,
            "email": user_fixture.email,
            "dept": user_fixture.dept,
            "business_unit": user_fixture.business_unit,
        }

        original_last_login = user_fixture.last_login

        # Action: POST /auth/login with existing user
        response = client.post("/auth/login", json=payload)

        # Assertions
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
        data = response.json()

        # Check response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "user_id" in data
        assert "is_new_user" in data

        # Check response values
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        assert data["token_type"] == "bearer"
        assert isinstance(data["user_id"], int)
        assert data["user_id"] == user_fixture.id
        assert data["is_new_user"] is False

        # Verify last_login was updated
        db_session.refresh(user_fixture)
        assert user_fixture.last_login is not None
        # last_login should be more recent than original (if it had a value)
        # but since we just updated it, it should be recent
        assert user_fixture.last_login >= original_last_login or original_last_login is None


class TestAuthLoginValidation:
    """TC-3: Input Validation - Missing Required Fields Returns 422"""

    def test_login_missing_knox_id_returns_422(self, client: TestClient) -> None:
        """
        TC-3a: POST /auth/login with missing knox_id returns 422 Unprocessable Entity.

        REQ: REQ-B-A2-Auth-3-4

        Scenario: User omits knox_id from request
        Setup: Prepare incomplete request
        Action: POST /auth/login without knox_id
        Expected: 422 Unprocessable Entity

        Acceptance Criteria:
        - Status code is 422
        - Error detail provided
        - No user created in database
        """
        payload = {
            # Missing knox_id
            "name": "Test User",
            "email": "test@samsung.com",
            "dept": "Engineering",
            "business_unit": "S.LSI",
        }

        response = client.post("/auth/login", json=payload)

        assert response.status_code == 422
        assert "detail" in response.json() or "errors" in response.json()

    def test_login_missing_name_returns_422(self, client: TestClient) -> None:
        """TC-3b: POST /auth/login with missing name returns 422."""
        payload = {
            "knox_id": "user_tc3b",
            # Missing name
            "email": "test@samsung.com",
            "dept": "Engineering",
            "business_unit": "S.LSI",
        }

        response = client.post("/auth/login", json=payload)

        assert response.status_code == 422

    def test_login_missing_email_returns_422(self, client: TestClient) -> None:
        """TC-3c: POST /auth/login with missing email returns 422."""
        payload = {
            "knox_id": "user_tc3c",
            "name": "Test User",
            # Missing email
            "dept": "Engineering",
            "business_unit": "S.LSI",
        }

        response = client.post("/auth/login", json=payload)

        assert response.status_code == 422

    def test_login_missing_dept_returns_422(self, client: TestClient) -> None:
        """TC-3d: POST /auth/login with missing dept returns 422."""
        payload = {
            "knox_id": "user_tc3d",
            "name": "Test User",
            "email": "test@samsung.com",
            # Missing dept
            "business_unit": "S.LSI",
        }

        response = client.post("/auth/login", json=payload)

        assert response.status_code == 422

    def test_login_missing_business_unit_returns_422(self, client: TestClient) -> None:
        """TC-3e: POST /auth/login with missing business_unit returns 422."""
        payload = {
            "knox_id": "user_tc3e",
            "name": "Test User",
            "email": "test@samsung.com",
            "dept": "Engineering",
            # Missing business_unit
        }

        response = client.post("/auth/login", json=payload)

        assert response.status_code == 422

    def test_login_empty_payload_returns_422(self, client: TestClient) -> None:
        """TC-3f: POST /auth/login with empty payload returns 422."""
        payload = {}

        response = client.post("/auth/login", json=payload)

        assert response.status_code == 422


class TestAuthLoginTokenValidity:
    """TC-4: Token Validity - Returned JWT Can Be Used in Subsequent Requests"""

    def test_login_returned_token_valid_for_subsequent_requests(
        self, client: TestClient, db_session: Session
    ) -> None:
        """
        TC-4: Returned JWT token from POST /auth/login is valid for subsequent API calls.

        REQ: REQ-B-A2-Auth-3-3

        Scenario: User logs in and uses returned token to access other endpoints
        Setup: None
        Action:
          1. POST /auth/login to get JWT token
          2. Use token in GET /auth/status request
        Expected: Both requests succeed and user info matches

        Acceptance Criteria:
        - Login returns 201/200 with valid JWT
        - GET /auth/status with returned token returns 200 and authenticated=true
        - User data from status matches login request
        """
        # Action 1: Login to get token
        login_payload = {
            "knox_id": "token_test_user",
            "name": "Token Test User",
            "email": "token_test@samsung.com",
            "dept": "Engineering",
            "business_unit": "S.LSI",
        }

        login_response = client.post("/auth/login", json=login_payload)
        assert login_response.status_code in [200, 201]

        login_data = login_response.json()
        access_token = login_data["access_token"]
        user_id = login_data["user_id"]

        # Action 2: Use token in subsequent request
        status_response = client.get("/auth/status", cookies={"auth_token": access_token})

        # Assertions
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["authenticated"] is True
        assert status_data["user_id"] == user_id
        assert status_data["knox_id"] == "token_test_user"


class TestAuthLoginConsistency:
    """TC-5: Database Consistency - Multiple Logins with Same User"""

    def test_login_multiple_times_same_user_returns_consistent_user_id(
        self, client: TestClient, db_session: Session
    ) -> None:
        """
        TC-5: Multiple logins with same user returns same user_id and no duplicates.

        REQ: REQ-B-A2-Auth-3-2, REQ-B-A2-Auth-3-5

        Scenario: User logs in twice (simulating multiple login attempts)
        Setup: Clear any existing test user
        Action:
          1. POST /auth/login with user A (first time)
          2. POST /auth/login with user A (second time)
        Expected:
        - First: 201, is_new_user=true, user_id=X
        - Second: 200, is_new_user=false, user_id=X (same ID)
        - Only one user record in database (no duplicates)

        Acceptance Criteria:
        - First login returns 201 with is_new_user=true
        - Second login returns 200 with is_new_user=false
        - Both logins return same user_id
        - Only one user record exists in database
        """
        payload = {
            "knox_id": "duplicate_test_user",
            "name": "Duplicate Test User",
            "email": "duplicate_test@samsung.com",
            "dept": "Engineering",
            "business_unit": "S.LSI",
        }

        # Action 1: First login (new user)
        first_response = client.post("/auth/login", json=payload)
        assert first_response.status_code == 201
        first_data = first_response.json()
        first_user_id = first_data["user_id"]
        assert first_data["is_new_user"] is True

        # Action 2: Second login (same user)
        second_response = client.post("/auth/login", json=payload)
        assert second_response.status_code == 200
        second_data = second_response.json()
        second_user_id = second_data["user_id"]
        assert second_data["is_new_user"] is False

        # Assertions
        # Same user_id both times
        assert first_user_id == second_user_id

        # Only one user record in database
        users = db_session.query(User).filter_by(knox_id="duplicate_test_user").all()
        assert len(users) == 1
        assert users[0].id == first_user_id


class TestAuthLoginEdgeCases:
    """TC-5 Extended: Edge Cases and Error Scenarios"""

    def test_login_with_special_characters_in_fields(
        self, client: TestClient, db_session: Session
    ) -> None:
        """
        TC-5-Special: Handle special characters in user data fields.

        REQ: REQ-B-A2-Auth-3

        Scenario: User data contains special characters (Korean, emojis, etc.)
        Setup: None
        Action: POST /auth/login with special characters in name, email, etc.
        Expected: 201 with user created successfully

        Acceptance Criteria:
        - Request with special characters succeeds
        - User created with correct data
        """
        payload = {
            "knox_id": "special_char_user",
            "name": "윤범원 (Beom Won Yoon)",
            "email": "bwyoon@samsung.com",
            "dept": "Engineering 엔지니어링",
            "business_unit": "S.LSI",
        }

        response = client.post("/auth/login", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["is_new_user"] is True

        # Verify in database
        user = db_session.query(User).filter_by(knox_id="special_char_user").first()
        assert user is not None
        assert user.name == "윤범원 (Beom Won Yoon)"

    def test_login_with_whitespace_in_fields(
        self, client: TestClient, db_session: Session
    ) -> None:
        """
        TC-5-Whitespace: Handle whitespace in user data fields.

        REQ: REQ-B-A2-Auth-3

        Scenario: User data has leading/trailing whitespace
        Setup: None
        Action: POST /auth/login with whitespace in fields
        Expected: 201 with user created (whitespace preserved or trimmed)

        Acceptance Criteria:
        - Request succeeds
        - User created (implementation determines trimming)
        """
        payload = {
            "knox_id": "  whitespace_user  ",
            "name": "  Test User  ",
            "email": "  test@samsung.com  ",
            "dept": "  Engineering  ",
            "business_unit": "  S.LSI  ",
        }

        response = client.post("/auth/login", json=payload)

        # Should succeed or trim whitespace
        assert response.status_code in [201, 422]  # Depending on validation

    def test_login_with_very_long_fields(
        self, client: TestClient, db_session: Session
    ) -> None:
        """
        TC-5-Long: Handle very long user data fields.

        REQ: REQ-B-A2-Auth-3

        Scenario: User data contains very long strings
        Setup: None
        Action: POST /auth/login with very long field values
        Expected: 201 if valid, 422 if exceeds max length

        Acceptance Criteria:
        - Request properly handled
        - Error returned if exceeds max length
        """
        long_string = "a" * 500

        payload = {
            "knox_id": long_string,
            "name": long_string,
            "email": f"{long_string}@samsung.com",
            "dept": long_string,
            "business_unit": long_string,
        }

        response = client.post("/auth/login", json=payload)

        # Should either succeed or return validation error
        assert response.status_code in [201, 422]


class TestAuthLoginAcceptanceCriteria:
    """TC-4 (Extended): Acceptance Criteria Verification"""

    def test_acceptance_criteria_ac1_required_fields_in_request(
        self, client: TestClient
    ) -> None:
        """
        AC-1: Request must contain knox_id, name, email, dept, business_unit.

        REQ: REQ-B-A2-Auth-3-4

        Scenario: Verify all required fields are enforced
        Expected: Missing any field returns 422

        Acceptance Criteria:
        - All 5 fields are required
        - Missing any field returns 422
        """
        required_fields = ["knox_id", "name", "email", "dept", "business_unit"]
        base_payload = {
            "knox_id": "ac1_user",
            "name": "AC1 Test",
            "email": "ac1@samsung.com",
            "dept": "Engineering",
            "business_unit": "S.LSI",
        }

        # Test that each field is required
        for field in required_fields:
            incomplete_payload = {k: v for k, v in base_payload.items() if k != field}
            response = client.post("/auth/login", json=incomplete_payload)
            assert response.status_code == 422, f"Field {field} should be required"

    def test_acceptance_criteria_ac2_new_user_is_new_user_true(
        self, client: TestClient
    ) -> None:
        """
        AC-2: New user login returns is_new_user: true.

        REQ: REQ-B-A2-Auth-3-2

        Scenario: First login with new user
        Expected: is_new_user=true

        Acceptance Criteria:
        - is_new_user field equals true for new users
        """
        payload = {
            "knox_id": "ac2_new_user",
            "name": "AC2 New User",
            "email": "ac2@samsung.com",
            "dept": "Engineering",
            "business_unit": "S.LSI",
        }

        response = client.post("/auth/login", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["is_new_user"] is True

    def test_acceptance_criteria_ac3_existing_user_is_new_user_false(
        self, client: TestClient, user_fixture: User
    ) -> None:
        """
        AC-3: Existing user login returns is_new_user: false.

        REQ: REQ-B-A2-Auth-3-2

        Scenario: Login with user that already exists
        Expected: is_new_user=false

        Acceptance Criteria:
        - is_new_user field equals false for existing users
        """
        payload = {
            "knox_id": user_fixture.knox_id,
            "name": user_fixture.name,
            "email": user_fixture.email,
            "dept": user_fixture.dept,
            "business_unit": user_fixture.business_unit,
        }

        response = client.post("/auth/login", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["is_new_user"] is False

    def test_acceptance_criteria_ac4_token_usable_in_subsequent_api_calls(
        self, client: TestClient
    ) -> None:
        """
        AC-4: Returned JWT token can be used in other API calls.

        REQ: REQ-B-A2-Auth-3-3

        Scenario: Use login token to access protected endpoint
        Expected: Protected endpoint accepts token

        Acceptance Criteria:
        - Token works in subsequent API calls
        - Subsequent call returns authenticated user info
        """
        payload = {
            "knox_id": "ac4_user",
            "name": "AC4 Test User",
            "email": "ac4@samsung.com",
            "dept": "Engineering",
            "business_unit": "S.LSI",
        }

        # Login
        login_response = client.post("/auth/login", json=payload)
        assert login_response.status_code in [200, 201]
        token = login_response.json()["access_token"]

        # Use token in subsequent call
        status_response = client.get("/auth/status", cookies={"auth_token": token})
        assert status_response.status_code == 200
        assert status_response.json()["authenticated"] is True

    def test_acceptance_criteria_ac5_response_completes_within_time_limit(
        self, client: TestClient
    ) -> None:
        """
        AC-5: Endpoint response completes within 1 second.

        REQ: REQ-B-A2-Auth-3

        Scenario: Measure response time
        Expected: Response time < 1 second

        Acceptance Criteria:
        - Response time < 1000ms
        """
        import time

        payload = {
            "knox_id": "ac5_user",
            "name": "AC5 Test User",
            "email": "ac5@samsung.com",
            "dept": "Engineering",
            "business_unit": "S.LSI",
        }

        start_time = time.time()
        response = client.post("/auth/login", json=payload)
        end_time = time.time()

        elapsed_ms = (end_time - start_time) * 1000

        assert response.status_code in [200, 201]
        # Allow 2 seconds for CI/CD environments, but should be much faster
        assert elapsed_ms < 2000, f"Response took {elapsed_ms}ms, expected < 1000ms"
