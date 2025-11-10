# REQ-CLI-AUTH-1: Login with JWT storage

**작성일**: 2025-11-10
**개발자**: Claude Code (bwyoon)
**상태**: ✅ Phase 4 (Done)

---

## 📋 Requirement Summary

**REQ ID**: REQ-CLI-AUTH-1
**Feature**: Login with JWT token storage and automatic inclusion in subsequent requests
**Priority**: M (필수)

### Description

사용자가 `auth login [username]` 명령어로 FastAPI 서버에 로그인하면:
1. 서버에서 JWT 토큰을 받음
2. 토큰을 CLI 세션에 저장 (context.session.token)
3. 이후 모든 인증 필요 엔드포인트에 자동으로 토큰을 Authorization 헤더에 포함

### Acceptance Criteria

- [x] `auth login [username]` 명령어 작동
- [x] JWT 토큰이 context.session.token에 저장
- [x] JWT 토큰이 이후 모든 요청 헤더에 자동 포함
- [x] context.session.user_id, username 저장
- [x] 로그인 실패 시 명확한 에러 메시지 표시
- [x] 신규/기존 사용자 구분 표시

---

## 🔧 Implementation Details

### Modified Files

1. **src/cli/client.py** (새로 생성)
   - APIClient 클래스: HTTP 요청/응답 처리
   - JWT 토큰 관리 (set_token, get_token, clear_token)
   - 자동 Authorization 헤더 추가
   - 에러 처리 (연결 실패, JSON 파싱 등)

2. **src/cli/context.py** (수정)
   - SessionState 데이터클래스 추가
   - CLIContext에 client, session 필드 추가

3. **src/cli/actions/auth.py** (수정)
   - login() 함수: 실제 API 호출 구현
   - POST /auth/login 엔드포인트 호출
   - 토큰 및 사용자 정보 저장

### Implementation Logic

```python
# src/cli/client.py - APIClient
def set_token(token: str) -> None:
    """JWT 토큰 저장"""
    self.token = token

def _get_headers() -> dict[str, str]:
    """Authorization 헤더 자동 추가"""
    headers = {"Content-Type": "application/json"}
    if self.token:
        headers["Authorization"] = f"Bearer {self.token}"
    return headers

def make_request(method, path, json_data=None) -> tuple[int, dict, str]:
    """API 요청 + 에러 처리"""
    # httpx 요청, 에러 처리, 응답 파싱 등
```

```python
# src/cli/context.py - CLIContext
@dataclass
class CLIContext:
    console: Console
    logger: Logger
    client: APIClient           # HTTP 클라이언트
    session: SessionState       # 세션 상태 (토큰, 사용자 정보)
```

```python
# src/cli/actions/auth.py - login()
def login(context: CLIContext, *args: str) -> None:
    # 1. API 호출: POST /auth/login
    status_code, response, error = context.client.make_request(
        "POST", "/auth/login",
        json_data={"knox_id": username, ...}
    )

    # 2. 토큰 저장
    token = response.get("access_token")
    context.client.set_token(token)
    context.session.token = token
    context.session.user_id = response.get("user_id")
    context.session.username = username

    # 3. 결과 표시
    print(f"✓ Successfully logged in as '{username}'")
```

### API Integration

**Endpoint**: `POST /auth/login`

**Request**:
```json
{
  "knox_id": "bwyoon",
  "name": "bwyoon",
  "email": "bwyoon@samsung.com",
  "dept": "Engineering",
  "business_unit": "S.LSI"
}
```

**Response (Success)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "user-123",
  "is_new_user": false
}
```

**Response (Error)**:
```json
{
  "detail": "Invalid credentials"
}
```

---

## 📋 Test Coverage

### Test Strategy

- ✅ Happy path: 성공적 로그인
- ✅ Input validation: 인자 없음
- ✅ Error handling: 서버 미응답, API 에러
- ✅ State management: 토큰/사용자 정보 저장

### Tests Implemented

**Location**: `tests/cli/test_auth.py`

```python
def test_login_success():
    """정상 로그인 테스트"""
    # APIClient mock으로 응답 반환
    # 토큰 저장 확인
    # 사용자 정보 저장 확인

def test_login_connection_error():
    """서버 미응답 테스트"""
    # 연결 실패 처리 확인

def test_login_missing_args():
    """인자 없음 테스트"""
    # Usage 가이드 출력 확인

def test_login_new_vs_returning_user():
    """신규/기존 사용자 구분 테스트"""
    # is_new_user 플래그 처리 확인
```

**Test Results**: ✅ All tests passing (100%)

---

## 💡 Design Decisions

### 1. APIClient as DI Container

**선택**: APIClient를 CLIContext에 주입

**이유**:
- 모든 API 호출이 일관된 토큰 관리
- 테스트 시 mock 교체 용이
- 향후 middleware 추가 가능 (retry, rate limit 등)

### 2. SessionState as Data Container

**선택**: 별도 SessionState 데이터클래스

**이유**:
- 세션 상태를 명확히 정의
- 타입 안정성 (mypy strict mode 준수)
- 향후 파일 저장/복구 용이 (직렬화)

### 3. Token in Both Client and Session

**선택**: 토큰을 client, session 모두에 저장

**이유**:
- client.token: API 요청 시 자동 포함
- session.token: 세션 저장/복구, 상태 추적

### 4. Error Message Details

**선택**: 에러 시 상세 메시지 표시

**이유**:
- 사용자가 문제 파악 용이
- 디버깅 시 도움
- 전문성 향상

---

## 🔄 Integration with Other Features

### Dependent Features (이후 구현된 기능들)

모든 인증 필요 엔드포인트가 이 토큰 관리 메커니즘에 의존:

- REQ-CLI-SURVEY-2: Survey 제출
- REQ-CLI-PROFILE-2: 닉네임 등록
- REQ-CLI-PROFILE-3: 닉네임 수정
- REQ-CLI-PROFILE-4: Survey 업데이트
- REQ-CLI-QUESTIONS-*: 모든 문항 관련 기능

### Token Propagation Flow

```
auth login
    ↓
context.client.set_token(token)
context.session.token = token
    ↓
다음 명령어 실행
    ↓
context.client.make_request()
    ↓
_get_headers()에서 자동으로 "Authorization: Bearer [token]"
    ↓
API 요청 → 서버에서 토큰 검증
```

---

## 🚀 Deployment Notes

### 환경 설정

**로컬 개발**:
```bash
./tools/dev.sh up  # FastAPI 서버 시작 (localhost:8000)
./tools/dev.sh cli # CLI 시작
```

**API 서버 URL**: http://localhost:8000 (하드코딩, 향후 설정화 가능)

### Security Considerations

- ✅ JWT 토큰은 메모리에만 저장 (파일 저장 안 함, REQ-CLI-SESSION-1에서 선택적)
- ✅ 토큰 유효기간: 24시간 (서버 설정)
- ✅ 토큰 갱신: 수동 재로그인 필요 (REQ-CLI-AUTH-2 향후 구현)

---

## 📊 Code Quality

### Linting & Type Checking

```
✅ ruff format: Pass
✅ ruff check: Pass (모든 violations 수정)
✅ mypy strict: Pass (타입 힌트 완벽)
✅ Line length: ≤120 chars
```

### Code Metrics

- **Files modified**: 3개
- **Lines added**: ~150 (client.py, context.py, auth.py)
- **Complexity**: O(1) (네트워크 I/O 제외)

---

## 🔍 Future Enhancements

### REQ-CLI-AUTH-2: Auto Token Refresh (Backlog)

```python
# 401 Unauthorized 감지 → 자동 토큰 갱신
if status_code == 401:
    refresh_token()  # Refresh endpoint 호출
    retry_request()  # 원래 요청 재시도
```

### Token Expiration Handling

```python
# 토큰 만료 시간 추적
token_exp = decode_jwt(token).get('exp')
if time.time() > token_exp:
    print("⚠️ Token expiring soon. Please login again.")
```

---

## 📝 Commit Information

**Commit SHA**: [pending]
**Branch**: main
**Author**: Claude Code (bwyoon)
**Date**: 2025-11-10

**Commit Message**:
```
feat(cli): Implement REQ-CLI-AUTH-1 - Login with JWT token storage

- Create APIClient (httpx-based) for HTTP communication
- Extend CLIContext with SessionState for token management
- Implement auth login command with token persistence
- Add automatic Authorization header injection in all requests
- Support new/returning user distinction
- Full error handling and user feedback

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## ✅ Phase 4 Checklist

- [x] Specification defined (Phase 1)
- [x] Tests designed (Phase 2)
- [x] Implementation complete (Phase 3)
- [x] All tests passing (100%)
- [x] Code quality checks passing
- [x] Progress file created (Phase 4)
- [x] DEV-PROGRESS.md updated
- [x] Ready for commit

---

**Status**: ✅ Complete
**Last Updated**: 2025-11-10
