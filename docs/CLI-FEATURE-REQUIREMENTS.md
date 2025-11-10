# CLI Feature Requirements

**작성일**: 2025-11-10
**목적**: SLEA-SSEM CLI 기능 요구사항 정의 및 추적
**Format**: REQ-CLI-[DOMAIN]-[NUMBER]

---

## 📊 Feature Summary

| Domain | 전체 | Done | Backlog |
|--------|------|------|---------|
| **Auth** | 2 | 1 | 1 |
| **Survey** | 2 | 2 | 0 |
| **Profile** | 5 | 4 | 1 |
| **Questions** | 8 | 6 | 2 |
| **Session** | 2 | 0 | 2 |
| **Export** | 2 | 0 | 2 |
| **Total** | **21** | **13** | **8** |

---

## 🔐 Auth Domain

### REQ-CLI-AUTH-1: Login with JWT storage

**Description**:
사용자가 `auth login [username]` 명령어로 FastAPI 서버에 로그인하면 JWT 토큰을 받아 세션에 저장하고, 이후 모든 인증 필요 엔드포인트에 자동으로 토큰을 헤더에 포함시킨다.

**사용 예**:
```bash
> auth login bwyoon
Logging in as 'bwyoon'...
✓ Successfully logged in as 'bwyoon'
  Status: New user
  User ID: user-123
  Token (first 20 chars): eyJhbGciOiJIUzI1NiI...
```

**기대 출력**:
- 로그인 성공: `✓ Successfully logged in as [username]`
- 사용자 ID, 토큰 미리보기 표시
- 신규/기존 사용자 구분

**에러 케이스**:
- 서버 미응답: "Failed to connect to http://localhost:8000: ..."
- 로그인 실패: "✗ Login failed"
- 인자 없음: Usage 가이드 표시

**Acceptance Criteria**:
- [x] `auth login [username]` 명령어 작동
- [x] JWT 토큰이 context.session.token에 저장
- [x] JWT 토큰이 이후 모든 요청 헤더에 포함
- [x] context.session.user_id, username 저장
- [x] 로그인 실패 시 명확한 에러 메시지

**Priority**: M (필수)
**Dependencies**: APIClient, CLIContext.session, FastAPI `/auth/login`
**Status**: ✅ Done (Phase 4)

---

### REQ-CLI-AUTH-2: Auto token refresh

**Description**:
JWT 토큰이 만료되면 자동으로 새 토큰을 발급받는다. (선택사항: refresh token 사용)

**사용 예**:
```bash
> questions generate
Token expired. Attempting to refresh...
✓ Token refreshed
✓ Round 1 questions generated
```

**기대 출력**:
- 토큰 갱신 자동 수행
- 사용자에게 투명한 경험 제공

**에러 케이스**:
- Refresh token 만료: "Session expired. Please login again."

**Acceptance Criteria**:
- [ ] 토큰 만료 감지 (401 Unauthorized)
- [ ] 자동 갱신 시도
- [ ] 갱신 실패 시 재로그인 유도

**Priority**: L (향후)
**Dependencies**: Token expiration handling, Refresh endpoint
**Status**: ⏳ Backlog

---

## 📋 Survey Domain

### REQ-CLI-SURVEY-1: Get survey schema

**Description**:
`survey schema` 명령어로 FastAPI 서버에서 survey 폼의 스키마(필드 정의, 타입, 검증 규칙)를 조회한다.

**사용 예**:
```bash
> survey schema
Fetching survey schema...
✓ Survey schema retrieved
  - level: select (required)
  - career: text (optional)
  - interests: multiselect (optional)
```

**기대 출력**:
- 각 필드명, 타입, 필수 여부 표시
- 인증 불필요 (public endpoint)

**에러 케이스**:
- 서버 미응답: "Failed to connect..."
- API 에러: 에러 메시지 표시

**Acceptance Criteria**:
- [x] `survey schema` 명령어 작동
- [x] GET /survey/schema 엔드포인트 호출
- [x] 스키마 정보 파싱 및 표시
- [x] 에러 처리 완벽

**Priority**: M (필수)
**Dependencies**: FastAPI `/survey/schema`
**Status**: ✅ Done (Phase 4)

---

### REQ-CLI-SURVEY-2: Submit survey data

**Description**:
`survey submit [level] [career] [interests]` 명령어로 자기평가 데이터를 제출한다. 로그인 후에만 작동.

**사용 예**:
```bash
> survey submit intermediate "5years" "AI,ML"
Submitting survey...
✓ Survey submitted
  Level: intermediate
  Career: 5years
  Interests: AI,ML
```

**기대 출력**:
- 제출된 데이터 확인 표시
- 성공 메시지

**에러 케이스**:
- 미인증: "✗ Not authenticated. Please login first: auth login [username]"
- 인자 부족: Usage 가이드 표시
- API 에러: 에러 메시지 표시

**Acceptance Criteria**:
- [x] 인증 확인 (token 필수)
- [x] `survey submit [args]` 명령어 작동
- [x] POST /survey/submit 엔드포인트 호출
- [x] 에러 처리

**Priority**: M (필수)
**Dependencies**: APIClient, CLIContext.session.token, FastAPI `/survey/submit`
**Status**: ✅ Done (Phase 4)

---

## 👤 Profile Domain

### REQ-CLI-PROFILE-1: Check nickname availability

**Description**:
`profile nickname check [nickname]` 명령어로 닉네임 중복 여부를 확인한다. 인증 불필요.

**사용 예**:
```bash
> profile nickname check coolname
Checking nickname availability...
✓ Nickname 'coolname' is available

# 또는
✗ Nickname 'coolname' is not available
  Suggestions:
    - coolname1
    - coolname2
```

**기대 출력**:
- 가능: "✓ Nickname 'xxx' is available"
- 불가: "✗ Nickname 'xxx' is not available" + suggestions

**에러 케이스**:
- 서버 에러: "✗ Check failed"
- 인자 없음: Usage 가이드

**Acceptance Criteria**:
- [x] 인증 불필요
- [x] `profile nickname check [nickname]` 작동
- [x] POST /profile/nickname/check 호출
- [x] 가용 여부 및 제안 표시

**Priority**: M (필수)
**Dependencies**: FastAPI `/profile/nickname/check`
**Status**: ✅ Done (Phase 4)

---

### REQ-CLI-PROFILE-2: Register nickname

**Description**:
`profile nickname register [nickname]` 명령어로 새 닉네임을 등록한다. 로그인 필수.

**사용 예**:
```bash
> profile nickname register coolname
Registering nickname 'coolname'...
✓ Nickname 'coolname' registered
```

**기대 출력**:
- 등록 성공 메시지

**에러 케이스**:
- 미인증: "✗ Not authenticated"
- 닉네임 중복: API 에러 메시지
- 인자 없음: Usage 가이드

**Acceptance Criteria**:
- [x] 인증 확인 (token 필수)
- [x] `profile nickname register [nickname]` 작동
- [x] POST /profile/register 호출
- [x] 성공/실패 메시지

**Priority**: M (필수)
**Dependencies**: APIClient, CLIContext.session.token, FastAPI `/profile/register`
**Status**: ✅ Done (Phase 4)

---

### REQ-CLI-PROFILE-3: Edit nickname

**Description**:
`profile nickname edit [new_nickname]` 명령어로 기존 닉네임을 변경한다. 로그인 필수.

**사용 예**:
```bash
> profile nickname edit newname
Updating nickname to 'newname'...
✓ Nickname updated to 'newname'
```

**기대 출력**:
- 업데이트 성공 메시지

**에러 케이스**:
- 미인증: "✗ Not authenticated"
- 중복: API 에러 메시지
- 인자 없음: Usage 가이드

**Acceptance Criteria**:
- [x] 인증 확인 필수
- [x] `profile nickname edit [new_nickname]` 작동
- [x] PUT /profile/nickname 호출
- [x] 성공/실패 메시지

**Priority**: M (필수)
**Dependencies**: APIClient, CLIContext.session.token, FastAPI `/profile/nickname`
**Status**: ✅ Done (Phase 4)

---

### REQ-CLI-PROFILE-4: Update survey

**Description**:
`profile update_survey [level] [career] [interests]` 명령어로 자기평가 정보를 수정한다. 로그인 필수.

**사용 예**:
```bash
> profile update_survey advanced "10years" "AI,ML,NLP"
Updating survey...
✓ Profile survey updated
  New profile record created
```

**기대 출력**:
- 업데이트 성공 메시지
- 새 프로필 레코드 생성 안내

**에러 케이스**:
- 미인증: "✗ Not authenticated"
- 인자 부족: Usage 가이드

**Acceptance Criteria**:
- [x] 인증 확인 필수
- [x] `profile update_survey [args]` 작동
- [x] PUT /profile/survey 호출
- [x] 성공 메시지

**Priority**: M (필수)
**Dependencies**: APIClient, CLIContext.session.token, FastAPI `/profile/survey`
**Status**: ✅ Done (Phase 4)

---

### REQ-CLI-PROFILE-5: View user profile

**Description**:
`profile view` 명령어로 현재 로그인한 사용자의 프로필 정보를 조회한다. 로그인 필수.

**사용 예**:
```bash
> profile view
Fetching profile...
✓ Profile loaded
  Username: bwyoon
  Nickname: coolname
  Level: intermediate
  Career: 5years
  Interests: AI,ML
```

**기대 출력**:
- 사용자 정보 일목요연하게 표시

**에러 케이스**:
- 미인증: "✗ Not authenticated"
- API 에러: 에러 메시지

**Acceptance Criteria**:
- [ ] 인증 확인 필수
- [ ] `profile view` 명령어 작동
- [ ] GET /profile (또는 /user/profile) 호출
- [ ] 프로필 정보 표시

**Priority**: L (향후)
**Dependencies**: FastAPI profile endpoint
**Status**: ⏳ Backlog

---

## ❓ Questions Domain

### REQ-CLI-QUESTIONS-1: Generate Round 1 questions

**Description**:
`questions generate` 명령어로 Round 1 테스트 문항 10개를 생성한다. 로그인 필수.

**사용 예**:
```bash
> questions generate
Generating Round 1 questions...
✓ Round 1 questions generated
  Session: session-123
  Questions: 10
```

**기대 출력**:
- 생성된 세션 ID
- 문항 개수

**에러 케이스**:
- 미인증: "✗ Not authenticated"
- API 에러: "✗ Generation failed"

**Acceptance Criteria**:
- [x] 인증 확인 필수
- [x] `questions generate` 명령어 작동
- [x] POST /questions/generate 호출
- [x] 세션 ID를 context.session.current_session_id에 저장
- [x] context.session.current_round = 1 설정

**Priority**: M (필수)
**Dependencies**: APIClient, CLIContext.session, FastAPI `/questions/generate`
**Status**: ✅ Done (Phase 4)

---

### REQ-CLI-QUESTIONS-2: Generate adaptive questions

**Description**:
`questions generate adaptive` 명령어로 Round 2 적응형 문항을 생성한다. Round 1 완료 후 작동.

**사용 예**:
```bash
> questions generate adaptive
Generating adaptive questions...
✓ Adaptive questions generated
  Questions: 10
  Difficulty: Advanced
```

**기대 출력**:
- 문항 개수
- 난이도

**에러 케이스**:
- 미인증: "✗ Not authenticated"
- 활성 세션 없음: "✗ No active session"
- API 에러: "✗ Generation failed"

**Acceptance Criteria**:
- [x] 인증 확인 필수
- [x] 활성 세션 확인 필수
- [x] `questions generate adaptive` 작동
- [x] POST /questions/generate-adaptive 호출
- [x] context.session.current_round = 2 설정

**Priority**: M (필수)
**Dependencies**: APIClient, CLIContext.session, FastAPI `/questions/generate-adaptive`
**Status**: ✅ Done (Phase 4)

---

### REQ-CLI-QUESTIONS-3: Autosave answer

**Description**:
`questions answer autosave [question_id] [answer]` 명령어로 답변을 실시간으로 저장한다. 로그인 필수.

**사용 예**:
```bash
> questions answer autosave q1 "machine learning is a subset of AI"
Autosaving answer...
✓ Answer autosaved
```

**기대 출력**:
- 저장 완료 메시지

**에러 케이스**:
- 미인증: "✗ Not authenticated"
- 인자 부족: Usage 가이드
- API 에러: "✗ Autosave failed"

**Acceptance Criteria**:
- [x] 인증 확인 필수
- [x] `questions answer autosave [q_id] [answer]` 작동
- [x] POST /questions/autosave 호출
- [x] 성공 메시지

**Priority**: M (필수)
**Dependencies**: APIClient, CLIContext.session.token, FastAPI `/questions/autosave`
**Status**: ✅ Done (Phase 4)

---

### REQ-CLI-QUESTIONS-4: Score answer

**Description**:
`questions answer score [question_id] [answer]` 명령어로 단일 답변을 채점한다. 로그인 필수.

**사용 예**:
```bash
> questions answer score q1 "machine learning is a subset of AI"
Scoring answer...
✓ Answer scored: 85%
  ✓ Correct
```

**기대 출력**:
- 점수 (%)
- 정오답 여부

**에러 케이스**:
- 미인증: "✗ Not authenticated"
- 인자 부족: Usage 가이드
- API 에러: "✗ Scoring failed"

**Acceptance Criteria**:
- [x] 인증 확인 필수
- [x] `questions answer score [q_id] [answer]` 작동
- [x] POST /questions/answer/score 호출
- [x] 점수와 정오답 표시

**Priority**: M (필수)
**Dependencies**: APIClient, CLIContext.session.token, FastAPI `/questions/answer/score`
**Status**: ✅ Done (Phase 4)

---

### REQ-CLI-QUESTIONS-5: Calculate round score

**Description**:
`questions score` 명령어로 전체 라운드 점수를 계산하고 저장한다. 로그인 필수.

**사용 예**:
```bash
> questions score
Calculating round score...
✓ Round score calculated
  Total: 85/100
  Correct: 8/10
```

**기대 출력**:
- 총점
- 정답 개수

**에러 케이스**:
- 미인증: "✗ Not authenticated"
- API 에러: "✗ Calculation failed"

**Acceptance Criteria**:
- [x] 인증 확인 필수
- [x] `questions score` 명령어 작동
- [x] POST /questions/score 호출
- [x] 총점 및 정답 개수 표시

**Priority**: M (필수)
**Dependencies**: APIClient, CLIContext.session.token, FastAPI `/questions/score`
**Status**: ✅ Done (Phase 4)

---

### REQ-CLI-QUESTIONS-6: Generate explanation

**Description**:
`questions explanation generate [question_id]` 명령어로 특정 문제의 해설을 생성한다. 로그인 필수.

**사용 예**:
```bash
> questions explanation generate q1
Generating explanation...
✓ Explanation generated
  Machine learning (ML) is a subset of Artificial Intelligence (AI)...
```

**기대 출력**:
- 해설 텍스트 (처음 100자)

**에러 케이스**:
- 미인증: "✗ Not authenticated"
- 인자 없음: Usage 가이드
- API 에러: "✗ Generation failed"

**Acceptance Criteria**:
- [x] 인증 확인 필수
- [x] `questions explanation generate [q_id]` 작동
- [x] POST /questions/explanations 호출
- [x] 해설 표시

**Priority**: M (필수)
**Dependencies**: APIClient, CLIContext.session.token, FastAPI `/questions/explanations`
**Status**: ✅ Done (Phase 4)

---

### REQ-CLI-QUESTIONS-7: Resume session

**Description**:
`questions session resume` 명령어로 이전에 중단된 테스트 세션을 재개한다. 로그인 필수.

**사용 예**:
```bash
> questions session resume
Resuming test session...
✓ Test session resumed
  Session ID: session-123
  Questions: 10
```

**기대 출력**:
- 세션 ID
- 문항 개수

**에러 케이스**:
- 미인증: "✗ Not authenticated"
- 재개 가능한 세션 없음: API 에러
- API 에러: "✗ Resume failed"

**Acceptance Criteria**:
- [x] 인증 확인 필수
- [x] `questions session resume` 작동
- [x] GET /questions/resume 호출
- [x] context.session.current_session_id 저장

**Priority**: M (필수)
**Dependencies**: APIClient, CLIContext.session, FastAPI `/questions/resume`
**Status**: ✅ Done (Phase 4)

---

### REQ-CLI-QUESTIONS-8: Check time status

**Description**:
`questions session time_status` 명령어로 테스트 시간 제한을 확인한다. 로그인 + 활성 세션 필수.

**사용 예**:
```bash
> questions session time_status
Checking time status...
✓ Time status checked
  Elapsed: 300s | Remaining: 900s
```

**기대 출력**:
- 경과 시간
- 남은 시간
- (선택) 시간 초과 경고

**에러 케이스**:
- 미인증: "✗ Not authenticated"
- 활성 세션 없음: "✗ No active session"
- API 에러: "✗ Check failed"

**Acceptance Criteria**:
- [x] 인증 확인 필수
- [x] 활성 세션 확인 필수
- [x] `questions session time_status` 작동
- [x] GET /questions/session/{session_id}/time-status 호출
- [x] 시간 정보 표시

**Priority**: M (필수)
**Dependencies**: APIClient, CLIContext.session, FastAPI `/questions/session/{id}/time-status`
**Status**: ✅ Done (Phase 4)

---

## 💾 Session Domain

### REQ-CLI-SESSION-1: Save session to file

**Description**:
`session save [filename]` 명령어로 현재 세션 상태(토큰, 사용자 정보, 현재 테스트 세션 ID)를 JSON 파일로 저장한다.

**사용 예**:
```bash
> session save my_session.json
Saving session...
✓ Session saved to my_session.json
  User: bwyoon
  Session ID: session-123
  Round: 1
```

**파일 포맷**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiI...",
  "user_id": "user-123",
  "username": "bwyoon",
  "current_session_id": "session-123",
  "current_round": 1,
  "saved_at": "2025-11-10T10:30:00Z"
}
```

**기대 출력**:
- 저장 성공 메시지
- 저장된 파일명, 사용자명, 세션 정보

**에러 케이스**:
- 파일 쓰기 실패: "✗ Failed to save session: [error]"
- 인자 없음: Usage 가이드

**Acceptance Criteria**:
- [ ] `session save [filename]` 명령어 작동
- [ ] 세션 상태를 JSON으로 직렬화
- [ ] 파일에 저장
- [ ] 성공 메시지 표시

**Priority**: H (장기 운영 시 필수)
**Dependencies**: CLIContext.session, JSON, file I/O
**Status**: ⏳ Backlog

---

### REQ-CLI-SESSION-2: Load session from file

**Description**:
`session load [filename]` 명령어로 저장된 세션 파일을 복구한다.

**사용 예**:
```bash
> session load my_session.json
Loading session...
✓ Session loaded
  User: bwyoon
  Session ID: session-123
  Round: 1
```

**기대 출력**:
- 로드 성공 메시지
- 복구된 사용자 정보, 세션 정보

**에러 케이스**:
- 파일 없음: "✗ File not found: my_session.json"
- 파일 포맷 오류: "✗ Invalid session file format"
- 토큰 만료: "⚠️  Token may have expired. Consider logging in again."

**Acceptance Criteria**:
- [ ] `session load [filename]` 명령어 작동
- [ ] JSON 파일 파싱
- [ ] context.session 복구
- [ ] 토큰 유효성 검사 (선택)

**Priority**: H (장기 운영)
**Dependencies**: CLIContext.session, JSON, file I/O
**Status**: ⏳ Backlog

---

## 📤 Export Domain

### REQ-CLI-EXPORT-1: Export results as JSON

**Description**:
`export json` 명령어로 현재 테스트 결과를 JSON 파일로 내보낸다.

**사용 예**:
```bash
> export json results.json
Exporting results...
✓ Results exported to results.json
  Session: session-123
  Round: 1
  Score: 85/100
```

**파일 포맷**:
```json
{
  "session_id": "session-123",
  "user_id": "user-123",
  "round": 1,
  "total_score": 85,
  "total_count": 10,
  "correct_count": 8,
  "questions": [
    {
      "question_id": "q1",
      "user_answer": "...",
      "score": 100,
      "is_correct": true
    }
  ],
  "exported_at": "2025-11-10T10:30:00Z"
}
```

**기대 출력**:
- 내보내기 성공 메시지
- 세션 정보, 점수

**에러 케이스**:
- 활성 세션 없음: "✗ No active session to export"
- 파일 쓰기 실패: "✗ Failed to export: [error]"

**Acceptance Criteria**:
- [ ] 활성 세션 확인 필수
- [ ] `export json [filename]` 명령어 작동
- [ ] API에서 결과 조회 (또는 캐시된 결과 사용)
- [ ] JSON 파일로 저장

**Priority**: L (향후)
**Dependencies**: Active session, API results endpoint
**Status**: ⏳ Backlog

---

### REQ-CLI-EXPORT-2: Export results as CSV

**Description**:
`export csv` 명령어로 테스트 결과를 CSV 파일로 내보낸다.

**사용 예**:
```bash
> export csv results.csv
Exporting results...
✓ Results exported to results.csv
```

**파일 포맷**:
```
question_id,user_answer,score,is_correct
q1,answer1,100,true
q2,answer2,50,false
...
```

**기대 출력**:
- 내보내기 성공 메시지

**에러 케이스**:
- 활성 세션 없음: "✗ No active session to export"
- 파일 쓰기 실패: "✗ Failed to export: [error]"

**Acceptance Criteria**:
- [ ] 활성 세션 확인 필수
- [ ] `export csv [filename]` 명령어 작동
- [ ] CSV 파일로 저장

**Priority**: L (향후)
**Dependencies**: Active session, API results endpoint, CSV library
**Status**: ⏳ Backlog

---

## 🔧 System Domain

### REQ-CLI-SYSTEM-1: Help command

**Description**:
`help` 명령어로 사용 가능한 모든 명령어와 사용법을 표시한다.

**상태**: ✅ Done (built-in)

---

### REQ-CLI-SYSTEM-2: Clear terminal

**Description**:
`clear` 명령어로 터미널 화면을 정리한다.

**상태**: ✅ Done (built-in)

---

## 📈 Development Progress

| Domain | REQ ID | Feature | Phase | Status | Notes |
|--------|--------|---------|-------|--------|-------|
| Auth | REQ-CLI-AUTH-1 | Login with JWT | 4 | ✅ Done | Commit: [pending] |
| Auth | REQ-CLI-AUTH-2 | Auto refresh | 0 | ⏳ Backlog | 향후 |
| Survey | REQ-CLI-SURVEY-1 | Get schema | 4 | ✅ Done | Commit: [pending] |
| Survey | REQ-CLI-SURVEY-2 | Submit data | 4 | ✅ Done | Commit: [pending] |
| Profile | REQ-CLI-PROFILE-1 | Check nickname | 4 | ✅ Done | Commit: [pending] |
| Profile | REQ-CLI-PROFILE-2 | Register nickname | 4 | ✅ Done | Commit: [pending] |
| Profile | REQ-CLI-PROFILE-3 | Edit nickname | 4 | ✅ Done | Commit: [pending] |
| Profile | REQ-CLI-PROFILE-4 | Update survey | 4 | ✅ Done | Commit: [pending] |
| Profile | REQ-CLI-PROFILE-5 | View profile | 0 | ⏳ Backlog | 향후 |
| Questions | REQ-CLI-QUESTIONS-1 | Generate Round 1 | 4 | ✅ Done | Commit: [pending] |
| Questions | REQ-CLI-QUESTIONS-2 | Generate adaptive | 4 | ✅ Done | Commit: [pending] |
| Questions | REQ-CLI-QUESTIONS-3 | Autosave answer | 4 | ✅ Done | Commit: [pending] |
| Questions | REQ-CLI-QUESTIONS-4 | Score answer | 4 | ✅ Done | Commit: [pending] |
| Questions | REQ-CLI-QUESTIONS-5 | Calculate score | 4 | ✅ Done | Commit: [pending] |
| Questions | REQ-CLI-QUESTIONS-6 | Generate explanation | 4 | ✅ Done | Commit: [pending] |
| Questions | REQ-CLI-QUESTIONS-7 | Resume session | 4 | ✅ Done | Commit: [pending] |
| Questions | REQ-CLI-QUESTIONS-8 | Check time status | 4 | ✅ Done | Commit: [pending] |
| Session | REQ-CLI-SESSION-1 | Save to file | 0 | ⏳ Backlog | JSON persistence |
| Session | REQ-CLI-SESSION-2 | Load from file | 0 | ⏳ Backlog | Session recovery |
| Export | REQ-CLI-EXPORT-1 | Export as JSON | 0 | ⏳ Backlog | Results export |
| Export | REQ-CLI-EXPORT-2 | Export as CSV | 0 | ⏳ Backlog | Results export |

---

## 📝 Next Steps

1. **Phase 1 Review**: Requirement 정의 검토 및 승인
2. **REQ-CLI-SESSION-1 구현**: Session persistence (높은 우선순위)
3. **REQ-CLI-PROFILE-5 구현**: View profile (선택)
4. **REQ-CLI-EXPORT-1/2 구현**: Results export (선택)

---

**Last Updated**: 2025-11-10
**Author**: Claude Code
**Status**: ✅ Initial requirements documented
