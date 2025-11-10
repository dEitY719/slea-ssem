# CLI Quick Start Guide

**작성일**: 2025-11-10
**최종 수정**: 2025-11-10
**상태**: ✅ Ready to use

---

## 🚀 5분 안에 시작하기

### 1️⃣ 서버 시작

터미널 1:
```bash
./tools/dev.sh up
# Starting dev server on localhost:8000...
# ✓ Server running
```

### 2️⃣ CLI 시작

터미널 2:
```bash
./tools/dev.sh cli
# Welcome to the SLEA-SSEM CLI!
# Type 'help' for a list of commands, or 'exit' to quit.
>
```

### 3️⃣ 로그인

```bash
> auth login testuser
Logging in as 'testuser'...
✓ Successfully logged in as 'testuser'
  Status: New user
  User ID: user-123
  Token (first 20 chars): eyJhbGciOiJIUzI1NiI...
```

### 4️⃣ 테스트 시작

```bash
# Survey 조회
> survey schema

# 자기평가 제출
> survey submit intermediate "5years" "AI,ML"

# 문항 생성
> questions generate
✓ Round 1 questions generated
  Session: session-123
  Questions: 10

# 답변 저장
> questions answer autosave q1 "my answer"

# 점수 계산
> questions score
✓ Round score calculated
  Total: 85/100
  Correct: 8/10
```

---

## 📚 전체 명령어 참조

### 인증 (Auth)

```bash
auth login [username]              # 로그인 (JWT 토큰 발급)
```

**예시**:
```bash
> auth login bwyoon
✓ Successfully logged in as 'bwyoon'
```

### 설문조사 (Survey)

```bash
survey schema                      # Survey 폼 스키마 조회
survey submit [level] [career] [interests]  # Survey 데이터 제출
```

**예시**:
```bash
> survey schema
✓ Survey schema retrieved
  - level: select (required)
  - career: text (optional)
  - interests: multiselect (optional)

> survey submit intermediate "5years" "AI,ML"
✓ Survey submitted
```

### 프로필 (Profile)

```bash
profile nickname check [nickname]  # 닉네임 중복 확인
profile nickname register [nickname]  # 닉네임 등록
profile nickname edit [new_nickname]   # 닉네임 수정
profile update_survey [level] [career] [interests]  # Survey 업데이트
```

**예시**:
```bash
> profile nickname check coolname
✓ Nickname 'coolname' is available

> profile nickname register coolname
✓ Nickname 'coolname' registered

> profile nickname edit coolname2
✓ Nickname updated to 'coolname2'

> profile update_survey advanced "10years" "AI,ML,NLP"
✓ Profile survey updated
  New profile record created
```

### 문항 & 테스트 (Questions)

#### 세션 관리

```bash
questions session resume          # 테스트 세션 재개
questions session status [pause|resume]  # 세션 상태 변경
questions session time_status     # 세션 시간 제한 확인
```

#### 문항 생성

```bash
questions generate                # Round 1 문항 생성 (10개)
questions generate adaptive       # Round 2 적응형 문항 생성
```

#### 답변 처리

```bash
questions answer autosave [question_id] [answer]  # 답변 자동 저장
questions answer score [question_id] [answer]     # 답변 채점
questions score                   # 라운드 전체 점수 계산
questions explanation generate [question_id]  # 문제 해설 생성
```

**예시 - 전체 테스트 플로우**:
```bash
# 1. 문항 생성
> questions generate
✓ Round 1 questions generated
  Session: session-123
  Questions: 10

# 2. 각 문항별 답변 저장 (실시간)
> questions answer autosave q1 "Machine learning is..."
✓ Answer autosaved

> questions answer autosave q2 "AI is..."
✓ Answer autosaved

# 3. 점수 계산
> questions score
✓ Round score calculated
  Total: 85/100
  Correct: 8/10

# 4. Round 2로 진행
> questions generate adaptive
✓ Adaptive questions generated
  Questions: 10
  Difficulty: Advanced

# 5. Round 2 답변 저장 및 채점...
```

### 시스템 (System)

```bash
help                              # 사용 가능한 명령어 목록
clear                             # 터미널 화면 정리
exit                              # CLI 종료
```

---

## 🔑 주요 개념

### 세션 상태 자동 추적

로그인하면 **자동으로 다음 정보를 추적**:

```
context.session:
  ├─ token: "eyJhbGciOiJIUzI1NiI..."  (JWT)
  ├─ user_id: "user-123"
  ├─ username: "bwyoon"
  ├─ current_session_id: "session-123"
  └─ current_round: 1
```

**의미**: 로그인 후 모든 명령어가 자동으로 JWT 토큰을 포함하고, 세션 ID를 기억한다.

### 인증 필수 명령어

로그인 전에는 **다음 명령어 사용 불가**:

```
✅ profile nickname check (인증 불필요)
✅ survey schema (인증 불필요)

❌ survey submit (로그인 필수)
❌ profile nickname register (로그인 필수)
❌ questions generate (로그인 필수)
❌ ... (모든 문항/테스트 관련 명령어)
```

### 에러 처리

**예시 - 미인증 상태에서 보호된 명령어 사용**:
```bash
> survey submit intermediate "5years" "AI,ML"
✗ Not authenticated
Please login first: auth login [username]
```

**예시 - 서버 미응답**:
```bash
> auth login bwyoon
Logging in as 'bwyoon'...
✗ Login failed
  Error: Failed to connect to http://localhost:8000: Connection refused
```

---

## 🎯 일반적인 사용 시나리오

### 시나리오 1: 신규 사용자 첫 응시

```bash
# 1. 로그인
> auth login newuser

# 2. 닉네임 확인 및 등록
> profile nickname check mynick
✓ Nickname 'mynick' is available

> profile nickname register mynick
✓ Nickname 'mynick' registered

# 3. 자기평가 정보 입력
> survey submit intermediate "3years" "AI"
✓ Survey submitted

# 4. Round 1 테스트
> questions generate
✓ Round 1 questions generated

> questions answer autosave q1 "my answer"
> questions answer autosave q2 "my answer"
... (10개 모두)

> questions score
✓ Round score calculated
  Total: 75/100

# 5. Round 2 테스트 (적응형)
> questions generate adaptive
✓ Adaptive questions generated
  Difficulty: Advanced

... (Round 2 진행)

# 6. 최종 결과
> questions score
✓ Round score calculated
  Total: 82/100
```

### 시나리오 2: 기존 사용자 재응시

```bash
# 1. 로그인
> auth login existinguser
✓ Successfully logged in as 'existinguser'
  Status: Returning user

# 2. 자기평가 정보 업데이트 (선택)
> profile update_survey advanced "5years" "AI,ML,NLP"
✓ Profile survey updated

# 3. 기존 세션 재개 (선택) 또는 새 테스트 시작
> questions session resume
✓ Test session resumed
  Session ID: session-abc

# 또는
> questions generate  # 새 세션 시작
```

### 시나리오 3: 테스트 중단 및 재개

```bash
# 1. 테스트 진행 중...
> questions answer autosave q5 "my answer"
✓ Answer autosaved

# 2. 중단 (CLI 종료)
> exit

# (나중에 다시 시작)

# 1. 로그인
> auth login bwyoon

# 2. 이전 세션 재개
> questions session resume
✓ Test session resumed
  Session ID: session-123 (이전 것)
  Questions: 10

# 3. 계속 진행
> questions answer autosave q6 "continue answer"
```

---

## 🐛 일반적인 문제 해결

### Q1: "Failed to connect to http://localhost:8000"

**원인**: FastAPI 서버가 실행 중이지 않음

**해결**:
```bash
# 다른 터미널에서 서버 시작
./tools/dev.sh up
```

### Q2: "✗ Not authenticated"

**원인**: 로그인하지 않음 또는 토큰 만료

**해결**:
```bash
> auth login [username]
```

### Q3: "Usage: auth login [username]"

**원인**: 명령어 인자 누락

**해결**:
```bash
> auth login bwyoon  # username 추가
```

### Q4: "✗ Nickname 'xxx' is not available"

**원인**: 닉네임 이미 사용 중

**해결**:
```bash
> profile nickname check xxx
✗ Nickname 'xxx' is not available
  Suggestions:
    - xxx1
    - xxx2

> profile nickname register xxx1  # 제안된 이름 사용
```

---

## 📖 더 알아보기

### 문서

- `docs/CLI-FEATURE-REQUIREMENTS.md`: 모든 CLI 기능 명세
- `docs/DEV-PROGRESS.md`: CLI 개발 진행 상황
- `CLAUDE.md`: CLI Feature Requirement Workflow 정의

### 구현

- `src/cli/client.py`: HTTP API 클라이언트
- `src/cli/context.py`: CLI 컨텍스트 & 세션 상태
- `src/cli/actions/`: 각 도메인별 명령어 구현

---

## 💡 팁 & 트릭

### 1. 자동 완성

```bash
> que[TAB]  # 자동 완성으로 "questions" 완성
```

### 2. 긴 입력값

```bash
# 띄어쓰기 있는 입력값은 따옴표 사용
> profile update_survey "intermediate" "5 years" "AI,ML"
```

### 3. 여러 정보 한 번에

```bash
# Survey 제출 시 한 줄에
> survey submit intermediate "5years" "AI,ML"
```

### 4. 도움말 항상 확인

```bash
> help        # 전체 명령어 목록
> profile     # "profile" 도메인 도움말
> profile nickname  # "profile nickname" 도움말
```

---

## 🚀 다음 단계

### REQ-CLI-SESSION-1: 세션 파일 저장 (향후)

```bash
> session save my_session.json
✓ Session saved to my_session.json
  User: bwyoon
  Session ID: session-123
  Round: 1

> session load my_session.json
✓ Session loaded
  User: bwyoon (이전 세션 복구됨)
```

### REQ-CLI-EXPORT-1: 결과 내보내기 (향후)

```bash
> export json results.json
✓ Results exported to results.json

> export csv results.csv
✓ Results exported to results.csv
```

---

**마지막 업데이트**: 2025-11-10
**상태**: ✅ Ready for production testing
