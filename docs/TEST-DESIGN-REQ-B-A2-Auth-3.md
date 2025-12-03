# REQ-B-A2-Auth-3: TEST DESIGN DOCUMENT

## Phase 2: TEST DESIGN (TDD Approach)

**Requirement**: REQ-B-A2-Auth-3 - CLI Direct Login Endpoint (Backend)
**Feature**: POST /auth/login endpoint that accepts user data and returns JWT token
**Test File**: `tests/backend/test_auth_login.py`
**Framework**: pytest + FastAPI TestClient
**Status**: Test skeleton generated (Phase 2 complete)

---

## Test Case Overview

**Total Test Cases**: 5 primary + 5 extended + 5 acceptance criteria

**Coverage Target**: 100% of acceptance criteria + edge cases

**Test Organization**:
- TC-1: Happy Path (New User)
- TC-2: Happy Path (Existing User)
- TC-3: Input Validation
- TC-4: Token Validity
- TC-5: Database Consistency + Edge Cases

---

## Test Case Details

### TC-1: Happy Path - New User Login Returns 201 Created

**Class**: `TestAuthLoginNewUser`
**Test Method**: `test_login_new_user_returns_201_and_is_new_user_true`

**Purpose**: Verify basic sanity - endpoint creates new user and returns proper response

**Setup**:
- Ensure new user with knox_id="new_user_tc1" doesn't exist in database
- Prepare request payload with all 5 required fields

**Action**:
- POST /auth/login with new user data

**Expected Results**:
- HTTP Status: 201 Created
- Response body contains all required fields:
  - access_token: string (JWT)
  - token_type: "bearer"
  - user_id: positive integer
  - is_new_user: true
- User created in database with correct fields

**Acceptance Criteria**:
- Response status is exactly 201
- access_token is non-empty string
- token_type equals "bearer"
- user_id is valid positive integer
- is_new_user equals true
- Database record exists with matching knox_id, name, email, dept, business_unit

**Importance**: Critical - Core requirement verification

---

### TC-2: Happy Path - Existing User Login Returns 200 OK

**Class**: `TestAuthLoginExistingUser`
**Test Method**: `test_login_existing_user_returns_200_and_is_new_user_false`

**Purpose**: Verify endpoint handles returning users correctly

**Setup**:
- Use pre-existing user from user_fixture
- Note original last_login timestamp

**Action**:
- POST /auth/login with existing user data

**Expected Results**:
- HTTP Status: 200 OK
- Response body contains all required fields
- is_new_user: false
- user_id matches existing user's ID
- User's last_login updated to current time

**Acceptance Criteria**:
- Response status is exactly 200
- access_token is valid JWT string
- token_type equals "bearer"
- user_id matches fixture user's ID (no duplicate created)
- is_new_user equals false
- last_login timestamp updated to current time or more recent

**Importance**: High - Differentiation between new and existing users

---

### TC-3: Input Validation - Missing Required Fields

**Class**: `TestAuthLoginValidation`
**Test Methods**: 6 validation tests

**Purpose**: Verify all 5 required fields are enforced

**Test Cases**:
1. `test_login_missing_knox_id_returns_422` - missing knox_id
2. `test_login_missing_name_returns_422` - missing name
3. `test_login_missing_email_returns_422` - missing email
4. `test_login_missing_dept_returns_422` - missing dept
5. `test_login_missing_business_unit_returns_422` - missing business_unit
6. `test_login_empty_payload_returns_422` - empty payload

**Setup**:
- Prepare requests with one field missing

**Action**:
- POST /auth/login without required field

**Expected Results**:
- HTTP Status: 422 Unprocessable Entity
- Error detail provided in response
- No user created in database

**Acceptance Criteria**:
- All 5 fields are required
- Missing any field returns 422
- Error message is informative
- No side effects (no user created)

**Importance**: High - Security and data integrity

---

### TC-4: Token Validity - JWT Can Be Used in Subsequent Requests

**Class**: `TestAuthLoginTokenValidity`
**Test Method**: `test_login_returned_token_valid_for_subsequent_requests`

**Purpose**: Verify returned JWT is valid and works with other endpoints

**Setup**:
- None

**Action**:
1. POST /auth/login to receive JWT token
2. Use returned token in subsequent GET /auth/status request

**Expected Results**:
- Login returns 201 or 200
- GET /auth/status with token returns 200
- Status endpoint shows authenticated: true
- User data matches login request
- Returned user_id matches token payload

**Acceptance Criteria**:
- Token is immediately usable in other endpoints
- Token payload contains correct user information
- Status endpoint recognizes token as valid
- No authentication errors with returned token

**Importance**: High - Core integration point

---

### TC-5: Database Consistency - Multiple Logins with Same User

**Class**: `TestAuthLoginConsistency`
**Test Method**: `test_login_multiple_times_same_user_returns_consistent_user_id`

**Purpose**: Verify database consistency and prevent duplicate users

**Setup**:
- Clear database of test user

**Action**:
1. First POST /auth/login with user A (new user)
2. Second POST /auth/login with user A (same data)

**Expected Results**:
- First request:
  - Status: 201 Created
  - is_new_user: true
  - Returns user_id=X
- Second request:
  - Status: 200 OK
  - is_new_user: false
  - Returns user_id=X (same ID)
- Database contains exactly 1 user record (no duplicates)

**Acceptance Criteria**:
- User IDs match between login attempts
- No duplicate users created
- Second login identifies existing user correctly
- Database state is consistent

**Importance**: Critical - Data integrity

---

### TC-5 Extended: Edge Cases and Error Scenarios

**Class**: `TestAuthLoginEdgeCases`

#### TC-5a: Special Characters in Fields
**Test Method**: `test_login_with_special_characters_in_fields`
- Handles Korean, special characters, parentheses
- User data preserved correctly in database

#### TC-5b: Whitespace Handling
**Test Method**: `test_login_with_whitespace_in_fields`
- Tests leading/trailing whitespace
- Either accepts or trims gracefully

#### TC-5c: Very Long Fields
**Test Method**: `test_login_with_very_long_fields`
- Tests 500+ character strings
- Either accepts or returns validation error

---

### Acceptance Criteria Verification Tests

**Class**: `TestAuthLoginAcceptanceCriteria`

#### AC-1: Required Fields in Request
**Test Method**: `test_acceptance_criteria_ac1_required_fields_in_request`
- Verifies knox_id, name, email, dept, business_unit required
- Each missing field returns 422

#### AC-2: New User is_new_user=true
**Test Method**: `test_acceptance_criteria_ac2_new_user_is_new_user_true`
- Confirms new users get is_new_user: true

#### AC-3: Existing User is_new_user=false
**Test Method**: `test_acceptance_criteria_ac3_existing_user_is_new_user_false`
- Confirms existing users get is_new_user: false

#### AC-4: Token Usable in Subsequent Calls
**Test Method**: `test_acceptance_criteria_ac4_token_usable_in_subsequent_api_calls`
- Token works in GET /auth/status
- Other endpoints recognize token as authenticated

#### AC-5: Response Time < 1 Second
**Test Method**: `test_acceptance_criteria_ac5_response_completes_within_time_limit`
- Measures endpoint latency
- Ensures < 1000ms response time

---

## Test Execution Matrix

| Test Case | Method | Status | Endpoint | HTTP Method | Expected Status |
|-----------|--------|--------|----------|-------------|-----------------|
| TC-1 | test_login_new_user_returns_201_and_is_new_user_true | Skeleton | /auth/login | POST | 201 |
| TC-2 | test_login_existing_user_returns_200_and_is_new_user_false | Skeleton | /auth/login | POST | 200 |
| TC-3a | test_login_missing_knox_id_returns_422 | Skeleton | /auth/login | POST | 422 |
| TC-3b | test_login_missing_name_returns_422 | Skeleton | /auth/login | POST | 422 |
| TC-3c | test_login_missing_email_returns_422 | Skeleton | /auth/login | POST | 422 |
| TC-3d | test_login_missing_dept_returns_422 | Skeleton | /auth/login | POST | 422 |
| TC-3e | test_login_missing_business_unit_returns_422 | Skeleton | /auth/login | POST | 422 |
| TC-3f | test_login_empty_payload_returns_422 | Skeleton | /auth/login | POST | 422 |
| TC-4 | test_login_returned_token_valid_for_subsequent_requests | Skeleton | /auth/login + /auth/status | POST + GET | 201/200 + 200 |
| TC-5 | test_login_multiple_times_same_user_returns_consistent_user_id | Skeleton | /auth/login | POST | 201 + 200 |
| TC-5a | test_login_with_special_characters_in_fields | Skeleton | /auth/login | POST | 201 |
| TC-5b | test_login_with_whitespace_in_fields | Skeleton | /auth/login | POST | 201/422 |
| TC-5c | test_login_with_very_long_fields | Skeleton | /auth/login | POST | 201/422 |
| AC-1 | test_acceptance_criteria_ac1_required_fields_in_request | Skeleton | /auth/login | POST | 422 |
| AC-2 | test_acceptance_criteria_ac2_new_user_is_new_user_true | Skeleton | /auth/login | POST | 201 |
| AC-3 | test_acceptance_criteria_ac3_existing_user_is_new_user_false | Skeleton | /auth/login | POST | 200 |
| AC-4 | test_acceptance_criteria_ac4_token_usable_in_subsequent_api_calls | Skeleton | /auth/login + /auth/status | POST + GET | 201 + 200 |
| AC-5 | test_acceptance_criteria_ac5_response_completes_within_time_limit | Skeleton | /auth/login | POST | 201 |

**Total Tests**: 18 test methods covering all scenarios

---

## Test File Structure

### File Location
```
tests/backend/test_auth_login.py
```

### Import Structure
```python
from datetime import UTC, datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.backend.models.user import User
from src.backend.services.auth_service import AuthService
```

### Fixture Dependencies
- `client`: TestClient with mocked database (from conftest.py)
- `db_session`: Database session for assertions (from conftest.py)
- `user_fixture`: Pre-created test user (from conftest.py)

### Test Classes
1. TestAuthLoginNewUser - TC-1
2. TestAuthLoginExistingUser - TC-2
3. TestAuthLoginValidation - TC-3
4. TestAuthLoginTokenValidity - TC-4
5. TestAuthLoginConsistency - TC-5
6. TestAuthLoginEdgeCases - TC-5 extended
7. TestAuthLoginAcceptanceCriteria - AC-1 through AC-5

---

## REQ Traceability

All tests are mapped to requirement sub-items:

| REQ Sub-Item | Test Coverage |
|--------------|---------------|
| REQ-B-A2-Auth-3-1 | TC-1, TC-4, AC-5 |
| REQ-B-A2-Auth-3-2 | TC-1, TC-2, TC-5, AC-2, AC-3 |
| REQ-B-A2-Auth-3-3 | TC-1, TC-2, TC-4, AC-4 |
| REQ-B-A2-Auth-3-4 | TC-3, AC-1 |
| REQ-B-A2-Auth-3-5 | TC-5 |

---

## Next Steps (Phase 3: Implementation)

### Endpoint Implementation Required
Location: `src/backend/api/auth.py`

The endpoint needs to:
1. Accept LoginRequest (knox_id, name, email, dept, business_unit)
2. Call AuthService.authenticate_or_create_user()
3. Return LoginResponse with access_token, token_type, user_id, is_new_user
4. Return 201 for new users, 200 for existing users

### Expected Implementation Pattern
```python
@router.post("/login", response_model=LoginResponse, status_code=200)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    auth_service = AuthService(db)
    user_data = request.dict()
    token, is_new, user_id = auth_service.authenticate_or_create_user(user_data)

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user_id=user_id,
        is_new_user=is_new,
    )
```

**Note**: Status code selection (201 vs 200) handled in endpoint logic

---

## Test Quality Checklist

- [x] 5 primary test cases designed
- [x] TC-1 is basic happy path (new user)
- [x] TC-2 is main happy path (existing user)
- [x] TC-3 covers input validation
- [x] TC-4 covers token validity
- [x] TC-5 covers database consistency
- [x] Additional edge cases included
- [x] Acceptance criteria tests included
- [x] Test file location correct: `tests/backend/test_auth_login.py`
- [x] Test framework matches project: pytest + TestClient
- [x] File skeleton created with proper structure
- [x] REQ IDs in all test docstrings
- [x] Each test has clear purpose statement
- [x] Test file syntax validated

---

## Test Execution

### Run All Auth Login Tests
```bash
pytest tests/backend/test_auth_login.py -v
```

### Run Specific Test
```bash
pytest tests/backend/test_auth_login.py::TestAuthLoginNewUser::test_login_new_user_returns_201_and_is_new_user_true -v
```

### Run with Coverage
```bash
pytest tests/backend/test_auth_login.py -v --cov=src/backend/api/auth --cov-report=html
```

---

## Status

**Phase 2 Complete**: Test design and skeleton generated
- Test file created: ✓
- 18 test methods defined: ✓
- All test classes implemented: ✓
- REQ traceability added: ✓
- Syntax validated: ✓

**Ready for Phase 3**: Implementation
