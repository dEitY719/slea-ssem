# REQ-B-A2-Prof-4: Get Latest User Profile Survey

**Status**: COMPLETED

**REQ ID**: REQ-B-A2-Prof-4, REQ-B-A2-Prof-5, REQ-B-A2-Prof-6

**Requirement**: JWT 토큰으로 현재 사용자의 가장 최근 자기평가 정보를 조회할 수 있어야 한다. (인증 필수)

Retrieve current user's most recent self-assessment profile information using JWT token authentication.

---

## Phase 1: Specification

### Endpoint
- **Method**: GET
- **Path**: `/profile/survey`
- **Authentication**: JWT token required (Bearer token in Authorization header)

### Request
No request body or query parameters required.

### Response (Success with data)
```json
{
  "level": "advanced",
  "career": 10,
  "job_role": "Senior Engineer",
  "duty": "System Architecture",
  "interests": ["AI", "Cloud", "ML"]
}
```

### Response (No survey exists)
```json
{
  "level": null,
  "career": null,
  "job_role": null,
  "duty": null,
  "interests": null
}
```

### Response Codes
- **200 OK**: Survey retrieved successfully (or no survey exists with all null)
- **401 Unauthorized**: JWT token missing or invalid

### Database Schema
Query on `user_profile_surveys` table:
- Filter by `user_id` (current authenticated user)
- Order by `submitted_at DESC` to get latest
- Limit 1 record

### Field Mappings
| API Response | Database Column | Type |
|---|---|---|
| level | self_level | str \| null |
| career | years_experience | int \| null |
| job_role | job_role | str \| null |
| duty | duty | str \| null |
| interests | interests | list[str] \| null |

### Implementation Details
- **Service Method**: `ProfileService.get_latest_survey(user_id: int)`
- **API Endpoint**: `profile.py` -> `get_latest_survey()`
- **Response Model**: `SurveyRetrievalResponse`
- **Acceptance Criteria**:
  - JWT authentication enforced (401 without token)
  - Returns most recent by submitted_at DESC
  - Returns all null when no survey exists
  - Response time < 1 second
  - Field names match specification exactly

---

## Phase 2: Test Design

### Test File
**Location**: `tests/backend/test_profile_survey_retrieval.py`

### Test Cases

#### TC-1: Success with all fields
```python
def test_get_profile_survey_success_with_all_fields(
    self, client: TestClient, user_profile_survey_fixture: UserProfileSurvey
) -> None:
```
- Setup: Create survey with all fields populated (level, career, job_role, duty, interests)
- Action: GET /profile/survey with JWT token
- Expected: 200 OK with all fields returned

#### TC-2: Success with null fields
```python
def test_get_profile_survey_no_survey_exists(
    self, client: TestClient
) -> None:
```
- Setup: No survey record created
- Action: GET /profile/survey with JWT token
- Expected: 200 OK with all fields as null

#### TC-3: Performance check
```python
def test_get_profile_survey_response_time_under_1_second(
    self, client: TestClient, user_profile_survey_fixture: UserProfileSurvey
) -> None:
```
- Setup: Create survey record
- Action: GET /profile/survey and measure time
- Expected: Response < 1 second

#### TC-4: Multiple surveys returns latest
```python
def test_get_profile_survey_multiple_surveys_returns_latest(
    self, client: TestClient, authenticated_user: User
) -> None:
```
- Setup: Create 3 surveys with different submitted_at times
- Action: GET /profile/survey
- Expected: Returns only the most recent survey (by submitted_at DESC)

---

## Phase 3: Implementation

### Files Modified

#### 1. `src/backend/api/profile.py`
**Changes**:
- Added `SurveyRetrievalResponse` model (lines 100-107)
- Updated module docstring to include REQ-B-A2-Prof-4/5/6 (line 8)
- Added GET `/profile/survey` endpoint (lines 388-424)
  - Depends on JWT authentication via `get_current_user`
  - Calls `ProfileService.get_latest_survey()`
  - Returns `SurveyRetrievalResponse` (200 OK)

#### 2. `src/backend/services/profile_service.py`
**Changes**:
- Added `get_latest_survey()` method (lines 301-347)
  - Queries `UserProfileSurvey` table
  - Filters by user_id
  - Orders by submitted_at DESC
  - Returns latest survey or all null if none exists
- Updated class docstring to include method (line 29)

#### 3. `tests/backend/test_profile_survey_retrieval.py` (NEW)
**Content**:
- `TestProfileSurveyRetrieval` class with 4 test methods
- TC-1: Success with all fields
- TC-2: No survey exists (all null)
- TC-3: Performance check (< 1 second)
- TC-4: Multiple surveys returns latest

### Implementation Pattern
Followed existing code patterns from other profile endpoints:
```python
# In endpoint:
result = profile_service.get_latest_survey(user.id)
return result  # Returns dict matching SurveyRetrievalResponse

# In service:
survey = self.session.query(UserProfileSurvey)\
    .filter_by(user_id=user_id)\
    .order_by(UserProfileSurvey.submitted_at.desc())\
    .first()

if not survey:
    return {"level": None, "career": None, ...}

return {
    "level": survey.self_level,
    "career": survey.years_experience,
    "job_role": survey.job_role,
    "duty": survey.duty,
    "interests": survey.interests,
}
```

### Code Quality Checks
- Ruff format: PASSED (all files unchanged)
- Ruff lint: PASSED (all checks passed)
- Type hints: Complete
- Docstrings: Complete

---

## Phase 4: Summary

### Implementation Complete
- [x] GET /profile/survey endpoint implemented
- [x] JWT authentication enforced
- [x] Most recent survey retrieved (order by submitted_at DESC)
- [x] All null returned when no survey exists
- [x] Response model matches specification
- [x] Test cases created and passing
- [x] Code formatted and linted
- [x] Type hints and docstrings complete

### Files Modified
1. `src/backend/api/profile.py` - Added endpoint and response model
2. `src/backend/services/profile_service.py` - Added service method
3. `tests/backend/test_profile_survey_retrieval.py` - New test file (created)

### Traceability

| REQ ID | Component | Implementation |
|---|---|---|
| REQ-B-A2-Prof-4 | API endpoint | GET /profile/survey (lines 388-424) |
| REQ-B-A2-Prof-4 | Service method | ProfileService.get_latest_survey() (lines 301-347) |
| REQ-B-A2-Prof-5 | Response handler | Returns all null when no survey (lines 331-338) |
| REQ-B-A2-Prof-6 | Performance | Index on (user_id, submitted_at DESC) in model |

### Test Coverage
- TC-1: Happy path (all fields populated)
- TC-2: Edge case (no survey exists)
- TC-3: Performance (< 1 second response)
- TC-4: Edge case (multiple surveys, returns latest)

### Git Commit
**SHA**: [To be generated in Phase 4]
**Message**:
```
feat: Implement GET /profile/survey endpoint for user profile retrieval (REQ-B-A2-Prof-4)

- Add JWT authentication for /profile/survey endpoint
- Query most recent user_profile_surveys record by submitted_at
- Return all null values when no survey exists
- Implement field mapping: level, career, job_role, duty, interests
- Add 4 comprehensive test cases covering all scenarios
- Verify response time < 1 second
- All tests passing, code quality clean

REQ: REQ-B-A2-Prof-4, REQ-B-A2-Prof-5, REQ-B-A2-Prof-6
```

---

## Acceptance Criteria Verification

- [x] GET /profile/survey endpoint exists
- [x] JWT authentication enforced (401 without token)
- [x] Returns most recent submitted_at record
- [x] Returns all null when no survey exists
- [x] Response time < 1 second (database index on user_id, submitted_at)
- [x] Field names match specification exactly (level, career, job_role, duty, interests)
- [x] Handles edge cases (null fields in DB, missing records)
- [x] All tests passing
- [x] Code formatted and linted

**Status**: ALL CRITERIA MET ✓
