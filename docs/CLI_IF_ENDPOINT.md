# CLI Interface & API Endpoint Map

**작성일**: 2025-11-09
**목적**: Backend FastAPI 엔드포인트 CRUD 작업 정리 및 함수명 맵핑

---

## 📡 API 엔드포인트 전체 목록

### 🔍 엔드포인트 요약

| HTTP Method | 개수 | 상태 |
|------------|------|------|
| **GET** | 3개 | ✅ |
| **POST** | 8개 | ✅ |
| **PUT** | 3개 | ✅ |
| **PATCH** | 0개 | ⏳ |
| **DELETE** | 0개 | ⏳ |
| **총 개수** | **16개** | ✅ |

---

## 📌 HTTP Method별 상세 목록

### 🟦 GET Endpoints (조회)

| 순서 | Path | 함수명 | 설명 |
|------|------|--------|------|
| 1 | `GET /survey/schema` | `get_survey_schema()` | Survey 폼 스키마 조회 (필드 정의, 검증 규칙) |
| 2 | `GET /questions/resume` | `resume_session()` | 테스트 세션 재개 (세션 상태 복구) |
| 3 | `GET /questions/session/{session_id}/time-status` | `check_time_status()` | 세션 시간 제한 확인 |

### 🟩 POST Endpoints (생성)

| 순서 | Path | 함수명 | 설명 |
|------|------|--------|------|
| 1 | `POST /auth/login` | `login()` | Samsung AD 로그인 (JWT 토큰 발급) |
| 2 | `POST /survey/submit` | `submit_survey()` | Survey 데이터 제출 및 저장 |
| 3 | `POST /profile/nickname/check` | `check_nickname_availability()` | 닉네임 중복 확인 (제안 포함) |
| 4 | `POST /profile/register` | `register_nickname()` | 닉네임 등록 |
| 5 | `POST /questions/generate` | `generate_questions()` | 테스트 문항 생성 (Round 1) |
| 6 | `POST /questions/score` | `calculate_round_score()` | 라운드 점수 계산 및 저장 |
| 7 | `POST /questions/generate-adaptive` | `generate_adaptive_questions()` | 적응형 문항 생성 (Round 2+) |
| 8 | `POST /questions/autosave` | `autosave_answer()` | 답변 자동 저장 (실시간) |

### 🟧 PUT Endpoints (수정)

| 순서 | Path | 함수명 | 설명 |
|------|------|--------|------|
| 1 | `PUT /profile/nickname` | `edit_nickname()` | 닉네임 수정 |
| 2 | `PUT /profile/survey` | `update_survey()` | Survey 업데이트 (새 프로필 레코드 생성) |
| 3 | `PUT /questions/session/{session_id}/status` | `update_session_status()` | 세션 상태 변경 (일시중지/재개) |

### 🟪 PATCH Endpoints (부분 수정)

| 순서 | 상태 | 비고 |
|------|------|------|
| - | ⏳ 구현 예정 | MVP 1.0에서는 미포함 |

### 🔴 DELETE Endpoints (삭제)

| 순서 | 상태 | 비고 |
|------|------|------|
| - | ⏳ 구현 예정 | MVP 1.0에서는 미포함 |

---

## 🗂️ 라우터별 조직

### 1️⃣ Auth Router (`/auth`)

**용도**: 인증 및 세션 관리

| HTTP | Path | 함수명 | 설명 |
|------|------|--------|------|
| POST | `/auth/login` | `login()` | Samsung AD 로그인 → JWT 토큰 발급 |

**관련 파일**: `src/backend/api/auth.py`

---

### 2️⃣ Survey Router (`/survey`)

**용도**: 자기평가 Survey 관리

| HTTP | Path | 함수명 | 설명 |
|------|------|--------|------|
| GET | `/survey/schema` | `get_survey_schema()` | 폼 스키마 조회 |
| POST | `/survey/submit` | `submit_survey()` | Survey 제출 |

**관련 파일**: `src/backend/api/survey.py`

---

### 3️⃣ Profile Router (`/profile`)

**용도**: 사용자 프로필 및 닉네임 관리

| HTTP | Path | 함수명 | 설명 |
|------|------|--------|------|
| POST | `/profile/nickname/check` | `check_nickname_availability()` | 닉네임 중복 확인 |
| POST | `/profile/register` | `register_nickname()` | 닉네임 등록 |
| PUT | `/profile/nickname` | `edit_nickname()` | 닉네임 수정 |
| PUT | `/profile/survey` | `update_survey()` | Survey 업데이트 |

**관련 파일**: `src/backend/api/profile.py`

---

### 4️⃣ Questions Router (`/questions`)

**용도**: 테스트 문항 생성, 채점, 저장

| HTTP | Path | 함수명 | 설명 |
|------|------|--------|------|
| GET | `/questions/resume` | `resume_session()` | 세션 재개 |
| GET | `/questions/session/{session_id}/time-status` | `check_time_status()` | 시간 제한 확인 |
| POST | `/questions/generate` | `generate_questions()` | Round 1 문항 생성 |
| POST | `/questions/score` | `calculate_round_score()` | 라운드 점수 계산 |
| POST | `/questions/generate-adaptive` | `generate_adaptive_questions()` | Round 2+ 문항 생성 |
| POST | `/questions/autosave` | `autosave_answer()` | 답변 자동 저장 |
| POST | `/questions/answer/score` | `score_answer()` | 단일 답변 채점 |
| POST | `/questions/explanations` | `generate_explanation()` | 해설 생성 |
| PUT | `/questions/session/{session_id}/status` | `update_session_status()` | 세션 상태 변경 |

**관련 파일**: `src/backend/api/questions.py`

---

## 📊 엔드포인트 도메인별 분류

### 인증 (Authentication)

- `POST /auth/login` → `login()`

### 설문조사 (Survey Management)

- `GET /survey/schema` → `get_survey_schema()`
- `POST /survey/submit` → `submit_survey()`
- `PUT /profile/survey` → `update_survey()`

### 프로필 관리 (Profile Management)

- `POST /profile/nickname/check` → `check_nickname_availability()`
- `POST /profile/register` → `register_nickname()`
- `PUT /profile/nickname` → `edit_nickname()`

### 테스트 관리 (Test/Questions Management)

#### 문항 생성

- `POST /questions/generate` → `generate_questions()`
- `POST /questions/generate-adaptive` → `generate_adaptive_questions()`

#### 세션 관리

- `GET /questions/resume` → `resume_session()`
- `GET /questions/session/{session_id}/time-status` → `check_time_status()`
- `PUT /questions/session/{session_id}/status` → `update_session_status()`

#### 답변 처리

- `POST /questions/autosave` → `autosave_answer()`
- `POST /questions/answer/score` → `score_answer()`

#### 채점 및 설명

- `POST /questions/score` → `calculate_round_score()`
- `POST /questions/explanations` → `generate_explanation()`

---

## 🔄 CRUD 작업 맵핑

### Create (생성) - POST

```
POST /auth/login                          → login()
POST /survey/submit                       → submit_survey()
POST /profile/nickname/check              → check_nickname_availability()
POST /profile/register                    → register_nickname()
POST /questions/generate                  → generate_questions()
POST /questions/score                     → calculate_round_score()
POST /questions/generate-adaptive         → generate_adaptive_questions()
POST /questions/autosave                  → autosave_answer()
POST /questions/answer/score              → score_answer()
POST /questions/explanations              → generate_explanation()
```

### Read (조회) - GET

```
GET /survey/schema                        → get_survey_schema()
GET /questions/resume                     → resume_session()
GET /questions/session/{session_id}/time-status → check_time_status()
```

### Update (수정) - PUT

```
PUT /profile/nickname                     → edit_nickname()
PUT /profile/survey                       → update_survey()
PUT /questions/session/{session_id}/status → update_session_status()
```

### Delete (삭제) - DELETE

```
(구현 예정)
```

---

## 📝 함수명 네이밍 규칙

### 동사 + 명사 패턴

- `get_*` - 조회 (GET)
- `check_*` - 확인/검증 (POST)
- `submit_*` - 제출 (POST)
- `register_*` - 등록 (POST)
- `generate_*` - 생성 (POST)
- `calculate_*` - 계산 (POST)
- `score_*` - 채점 (POST)
- `autosave_*` - 자동 저장 (POST)
- `edit_*` - 수정 (PUT)
- `update_*` - 업데이트 (PUT)
- `resume_*` - 재개 (GET)

---

## 🔐 권한 및 인증

| 엔드포인트 | 인증 필요 | 설명 |
|-----------|---------|------|
| `POST /auth/login` | ❌ | 로그인 (인증 불필요) |
| 나머지 모든 엔드포인트 | ✅ | JWT 토큰 필요 |

---

## 📋 Path Parameter 정리

| Parameter | 타입 | 사용 엔드포인트 | 설명 |
|-----------|------|-----------------|------|
| `{session_id}` | str | `/questions/session/{session_id}/time-status` | 테스트 세션 ID |
| `{session_id}` | str | `/questions/session/{session_id}/status` | 테스트 세션 ID |

---

## 🚀 엔드포인트 사용 시나리오

### 시나리오 1: 신규 사용자 테스트 응시

```
1. POST /auth/login                 → 로그인 (JWT 획득)
2. GET /survey/schema               → 설문 폼 스키마 조회
3. POST /survey/submit              → 설문 제출
4. POST /questions/generate         → Round 1 문항 생성
5. POST /questions/autosave         → 실시간 답변 저장
6. POST /questions/score            → Round 1 완료 (채점)
7. POST /questions/generate-adaptive → Round 2 문항 생성 (적응형)
```

### 시나리오 2: 세션 일시중지 및 재개

```
1. PUT /questions/session/{session_id}/status  → 세션 일시중지
2. GET /questions/resume                       → 세션 상태 복구
3. GET /questions/session/{session_id}/time-status → 시간 확인
4. PUT /questions/session/{session_id}/status  → 세션 재개
```

### 시나리오 3: 닉네임 관리

```
1. POST /profile/nickname/check    → 닉네임 중복 확인
2. POST /profile/register          → 닉네임 등록
3. PUT /profile/nickname           → 닉네임 수정
```

---

## 📚 관련 문서

| 문서 | 경로 | 설명 |
|------|------|------|
| Backend API 명세 | `docs/API_SPECIFICATION.md` | 상세 API 스펙 |
| 프로젝트 구조 | `docs/PROJECT_SETUP_PROMPT.md` | 프로젝트 전체 구조 |
| 사용자 시나리오 | `docs/user_scenarios_mvp1.md` | 사용자 사용 시나리오 |

---

## 🔗 파일 위치

| 라우터 | 파일 경로 |
|--------|----------|
| Auth | `src/backend/api/auth.py` |
| Survey | `src/backend/api/survey.py` |
| Profile | `src/backend/api/profile.py` |
| Questions | `src/backend/api/questions.py` |
| 초기화 | `src/backend/api/__init__.py` |

---

## 📌 다음 추가될 엔드포인트

### PATCH (부분 수정)

- `PATCH /profile/...` - 부분 프로필 수정
- `PATCH /questions/...` - 부분 문항 수정

### DELETE (삭제)

- `DELETE /profile/...` - 프로필 삭제
- `DELETE /questions/...` - 세션/문항 삭제

---

**작성자**: Claude Code
**마지막 업데이트**: 2025-11-09
**상태**: ✅ MVP 1.0 완료 (16개 엔드포인트)
