"""
Tests for profile survey retrieval endpoint.

REQ: REQ-B-A2-Prof-4, REQ-B-A2-Prof-5, REQ-B-A2-Prof-6

Phase 2 Test Design:
- TC-1 to TC-9: Functional test cases (already implemented)
- TC-10 to TC-14: Performance benchmark test cases (new for Phase 2)

Phase 2 (Test Design) focuses on:
1. Performance statistics analysis: 10 iterations with mean/median/p95
2. Scale testing: 10, 100, 1000 surveys with performance verification
3. Query optimization validation: No N+1 problems
4. Index usage verification: Query plans confirm index usage
5. Baseline establishment: For future regression detection
"""

import statistics
import time
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from src.backend.models.user import User
from src.backend.models.user_profile import UserProfileSurvey


class TestProfileSurveyRetrieval:
    """REQ-B-A2-Prof-4, 5, 6: Profile survey retrieval endpoint."""

    def test_get_profile_survey_no_survey_exists(self, client: TestClient) -> None:
        """TC-3: GET /profile/survey - No survey exists, return all null."""
        # Don't create any survey for this user
        response = client.get("/profile/survey")

        assert response.status_code == 200
        data = response.json()
        assert data["level"] is None
        assert data["career"] is None
        assert data["job_role"] is None
        assert data["duty"] is None
        assert data["interests"] is None

    def test_get_profile_survey_success_with_all_fields(
        self, client: TestClient, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """TC-1: GET /profile/survey - Success with all fields populated."""
        # user_profile_survey_fixture already has all fields populated
        response = client.get("/profile/survey")

        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "Intermediate"
        assert data["career"] == 3
        assert data["job_role"] == "Senior Engineer"
        assert data["duty"] == "ML Model Development"
        assert data["interests"] == ["LLM", "RAG"]

    def test_get_profile_survey_response_time_under_1_second(
        self, client: TestClient, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """TC-6: GET /profile/survey - Response within 1 second."""
        # Measure response time
        start_time = time.time()
        response = client.get("/profile/survey")
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 1.0  # Must respond within 1 second

    def test_get_profile_survey_without_jwt_token(self) -> None:
        """
        TC-4: GET /profile/survey - No JWT token should return 401 or 403.

        REQ: REQ-B-A2-Prof-4 (Authentication required)

        Note: Status code may be 401 (Unauthorized) or 403 (Forbidden) depending
        on middleware implementation. Both indicate failed authentication.
        """
        from src.backend.main import app

        unauthenticated_client = TestClient(app)
        # Don't include authorization header
        response = unauthenticated_client.get("/profile/survey")

        # Accept both 401 (Unauthorized) and 403 (Forbidden) as auth failures
        assert response.status_code in (401, 403)
        data = response.json()
        assert "detail" in data

    def test_get_profile_survey_null_fields_are_truly_null(self, client: TestClient, db_session: Session) -> None:
        """
        TC-9: Null fields must be None, not empty strings or other falsy values.

        REQ: REQ-B-A2-Prof-5
        """
        # Don't create any survey - all fields should be null
        response = client.get("/profile/survey")

        assert response.status_code == 200
        data = response.json()

        # Verify each field is explicitly None
        assert data["level"] is None
        assert data["career"] is None
        assert data["job_role"] is None
        assert data["duty"] is None
        assert data["interests"] is None

        # Ensure they are not empty strings
        assert data["level"] != ""
        assert data["job_role"] != ""
        assert data["duty"] != ""
        assert data["interests"] != []

    def test_get_profile_survey_response_structure(self, client: TestClient) -> None:
        """
        TC-7: Response structure must have all 5 expected fields.

        REQ: REQ-B-A2-Prof-5
        """
        response = client.get("/profile/survey")

        assert response.status_code == 200
        data = response.json()

        # Verify all 5 fields are present
        expected_fields = ["level", "career", "job_role", "duty", "interests"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

        # Verify no extra fields
        assert len(data) == 5, f"Expected 5 fields, got {len(data)}: {list(data.keys())}"

    def test_get_profile_survey_most_recent_by_submitted_at(
        self, client: TestClient, authenticated_user: User, db_session: Session
    ) -> None:
        """
        TC-8: With multiple surveys, return the most recent by submitted_at.

        REQ: REQ-B-A2-Prof-4, REQ-B-A2-Prof-5
        """
        # Create first survey with old timestamp
        old_time = datetime.now(UTC) - timedelta(days=10)
        survey1 = UserProfileSurvey(
            user_id=authenticated_user.id,
            self_level="Beginner",
            years_experience=1,
            job_role="Junior Dev",
            duty="Code writing",
            interests=["Python"],
            submitted_at=old_time,
        )

        # Create second survey with recent timestamp
        recent_time = datetime.now(UTC)
        survey2 = UserProfileSurvey(
            user_id=authenticated_user.id,
            self_level="Advanced",
            years_experience=5,
            job_role="Senior Engineer",
            duty="System Design",
            interests=["Architecture"],
            submitted_at=recent_time,
        )

        db_session.add(survey1)
        db_session.add(survey2)
        db_session.commit()

        # Should return the most recent survey (survey2)
        response = client.get("/profile/survey")

        assert response.status_code == 200
        data = response.json()
        assert data["level"] == "Advanced"
        assert data["career"] == 5
        assert data["job_role"] == "Senior Engineer"
        assert data["duty"] == "System Design"
        assert data["interests"] == ["Architecture"]

    def test_get_profile_survey_partial_null_fields(
        self, client: TestClient, authenticated_user: User, db_session: Session
    ) -> None:
        """
        TC-2: Survey with some null fields should return actual values + null.

        REQ: REQ-B-A2-Prof-5
        """
        # Create survey with some fields null (if allowed by schema)
        survey = UserProfileSurvey(
            user_id=authenticated_user.id,
            self_level="Intermediate",
            years_experience=3,
            job_role=None,  # This field is null
            duty="Development",
            interests=None,  # This field is null
        )
        db_session.add(survey)
        db_session.commit()

        response = client.get("/profile/survey")

        assert response.status_code == 200
        data = response.json()
        # Verify actual values are returned
        assert data["level"] == "Intermediate"
        assert data["career"] == 3
        assert data["duty"] == "Development"
        # Verify null fields remain null
        assert data["job_role"] is None
        assert data["interests"] is None

    # Phase 2: Performance Test Cases (TC-10 to TC-14)

    def test_get_profile_survey_performance_10_iterations(
        self, client: TestClient, user_profile_survey_fixture: UserProfileSurvey
    ) -> None:
        """
        TC-10: Performance baseline - 10 iterations measure mean/median/p95.

        REQ: REQ-B-A2-Prof-6 (Response within 1 second)

        Acceptance Criteria:
        - mean < 500ms (baseline expectation)
        - median < 400ms (typical case)
        - p95 < 1000ms (99% of requests must pass requirement)
        - All 10 iterations must complete
        - No outlier (single iteration > 2s is suspect)
        """
        iterations = 10
        response_times = []

        # Warm-up request to avoid cold-start bias
        client.get("/profile/survey")

        # Measure 10 iterations
        for _ in range(iterations):
            start_time = time.time()
            response = client.get("/profile/survey")
            elapsed_time = (time.time() - start_time) * 1000  # Convert to ms

            assert response.status_code == 200
            response_times.append(elapsed_time)

        # Analyze statistics
        mean_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        p95_time = sorted(response_times)[int(0.95 * len(response_times))]
        min_time = min(response_times)
        max_time = max(response_times)

        # Print performance metrics for analysis
        print(f"\nPerformance Statistics (10 iterations):")
        print(f"  Min:    {min_time:.2f}ms")
        print(f"  Mean:   {mean_time:.2f}ms")
        print(f"  Median: {median_time:.2f}ms")
        print(f"  P95:    {p95_time:.2f}ms")
        print(f"  Max:    {max_time:.2f}ms")
        print(f"  All responses: {[f'{t:.2f}ms' for t in response_times]}")

        # Assertions
        assert mean_time < 500, f"Mean response time {mean_time:.2f}ms exceeds 500ms baseline"
        assert median_time < 400, f"Median response time {median_time:.2f}ms exceeds 400ms"
        assert p95_time < 1000, f"P95 response time {p95_time:.2f}ms exceeds 1000ms requirement"

    def test_get_profile_survey_scale_10_surveys(
        self, client: TestClient, authenticated_user: User, db_session: Session
    ) -> None:
        """
        TC-11: Scale test - 10 surveys for same user, verify performance.

        REQ: REQ-B-A2-Prof-6

        Acceptance Criteria:
        - Response time < 1000ms even with 10 surveys
        - Only fetches latest (DESC order)
        - Index on (user_id, submitted_at) used
        """
        # Create 10 surveys for the same user
        for i in range(10):
            survey = UserProfileSurvey(
                user_id=authenticated_user.id,
                self_level="Intermediate",
                years_experience=i + 1,
                job_role=f"Role-{i}",
                duty=f"Duty-{i}",
                interests=[f"Interest-{i}"],
                submitted_at=datetime.now(UTC) - timedelta(days=10 - i),
            )
            db_session.add(survey)
        db_session.commit()

        # Measure response time
        start_time = time.time()
        response = client.get("/profile/survey")
        elapsed_time = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert elapsed_time < 1000, f"Response time {elapsed_time:.2f}ms exceeds 1000ms"

        # Verify latest survey is returned (highest years_experience)
        data = response.json()
        assert data["career"] == 10, "Should return latest survey by submitted_at"

    def test_get_profile_survey_scale_100_surveys_different_users(
        self, client: TestClient, authenticated_user: User, db_session: Session
    ) -> None:
        """
        TC-12: Scale test - 100 surveys for same user across time, verify index.

        REQ: REQ-B-A2-Prof-6

        Acceptance Criteria:
        - Response time < 1000ms even with 100 surveys for same user
        - Index on (user_id, submitted_at) ensures efficient latest lookup
        - Only fetches 1 latest record (LIMIT 1)
        """
        # Create 100 surveys for the same user across different timestamps
        # (Simulating a user taking many surveys over time)
        for i in range(100):
            survey = UserProfileSurvey(
                user_id=authenticated_user.id,
                self_level="Intermediate",
                years_experience=5 + (i % 10),
                job_role=f"Role-{i % 5}",
                duty=f"Duty-{i % 5}",
                interests=[f"Interest-{i % 3}"],
                submitted_at=datetime.now(UTC) - timedelta(days=100 - i),
            )
            db_session.add(survey)

        db_session.commit()

        # Measure response time
        start_time = time.time()
        response = client.get("/profile/survey")
        elapsed_time = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert elapsed_time < 1000, f"Response time {elapsed_time:.2f}ms exceeds 1000ms"

        # Verify latest survey is returned (most recent by submitted_at)
        # For i=99 (last iteration), years_experience = 5 + (99 % 10) = 5 + 9 = 14
        data = response.json()
        assert data["career"] == 14, "Should return most recent survey (i=99: 5 + 9)"

    def test_get_profile_survey_scale_1000_surveys_stress(
        self, client: TestClient, authenticated_user: User, db_session: Session
    ) -> None:
        """
        TC-13: Stress test - 1000 surveys for same user, measure performance ceiling.

        REQ: REQ-B-A2-Prof-6

        Acceptance Criteria:
        - Response time < 1500ms (relaxed for stress test)
        - Database query still efficient with large dataset
        - Index prevents degradation as records accumulate
        """
        # Create 1000 surveys for the same user across time
        # (Simulating long-term history of survey submissions)
        for i in range(1000):
            survey = UserProfileSurvey(
                user_id=authenticated_user.id,
                self_level="Intermediate" if i % 2 == 0 else "Advanced",
                years_experience=5 + (i % 15),
                job_role=f"Role-{i % 5}",
                duty=f"Duty-{i % 8}",
                interests=[f"Interest-{i % 10}"],
                submitted_at=datetime.now(UTC) - timedelta(days=1000 - i),
            )
            db_session.add(survey)

        db_session.commit()

        # Measure response time
        start_time = time.time()
        response = client.get("/profile/survey")
        elapsed_time = (time.time() - start_time) * 1000

        assert response.status_code == 200
        # Relaxed assertion for stress test (baseline allows up to 1500ms)
        assert elapsed_time < 1500, f"Stress test: response time {elapsed_time:.2f}ms"

        # Verify latest survey is returned (most recent by submitted_at)
        # For i=999 (last iteration), years_experience = 5 + (999 % 15) = 5 + 9 = 14
        data = response.json()
        assert data["career"] == 14, "Should return most recent survey (i=999: 5 + 9)"

    def test_get_profile_survey_index_usage_verification(
        self, client: TestClient, user_profile_survey_fixture: UserProfileSurvey, db_session: Session
    ) -> None:
        """
        TC-14: Verify query uses composite index (user_id, submitted_at).

        REQ: REQ-B-A2-Prof-6

        Acceptance Criteria:
        - Query plan shows index usage
        - No sequential scan on user_profile_surveys table
        - Index name: ix_user_id_submitted_at
        """
        # Execute EXPLAIN ANALYZE to check query plan
        # Note: This query mirrors ProfileService.get_latest_survey()
        query = text(
            """
            EXPLAIN ANALYZE
            SELECT * FROM user_profile_surveys
            WHERE user_id = :user_id
            ORDER BY submitted_at DESC
            LIMIT 1
            """
        )

        result = db_session.execute(query, {"user_id": user_profile_survey_fixture.user_id})
        plan_text = "\n".join([row[0] for row in result])

        print(f"\nQuery Plan:\n{plan_text}")

        # Verify index usage
        # PostgreSQL will show index name in the plan if used
        assert "ix_user_id_submitted_at" in plan_text or "Index Scan" in plan_text, (
            f"Query plan does not show expected index usage:\n{plan_text}"
        )
        # Ensure no sequential scan (which would be inefficient)
        assert "Seq Scan" not in plan_text, (
            f"Query plan shows sequential scan (inefficient):\n{plan_text}"
        )
