# Feature Requirement - MVP 1.0.0

**Project**: SLEA-SSEM (S.LSI Education AI Teacher)
**Version**: 1.0
**Last Updated**: 2025-11-06
**Status**: In Development

---

## 📌 Executive Summary

SLEA-SSEM MVP 1.0.0은 S.LSI 임직원의 **AI 역량 수준을 객관적으로 측정하고 등급화**하는 시스템입니다. Azure AD SSO를 통한 가입, 적응형 2단계 레벨 테스트, LLM 기반 자동 채점·해설, 그리고 상대 순위 제시로 구성됩니다. 모든 핵심 기능은 **Multi-AI-Agent 아키텍처**로 자동화되며, 관리자 개입을 최소화합니다.

**Target Users**: S.LSI 전사 임직원(총 ~500명 기준)

---

## 🎯 Scope (MVP 1.0.0)

### 포함 (In Scope)
- ✅ Azure AD/SSO 기반 사용자 인증
- ✅ 닉네임 등록 및 중복 검증
- ✅ 자기평가 정보 수집 (수준, 경력, 직군, 업무, 관심분야)
- ✅ RAG 기반 동적 문항 생성 (1~n차 적응형)
- ✅ 객관식/OX/주관식 혼합 문항 지원
- ✅ LLM 기반 자동 채점 및 부분점수
- ✅ 즉시 피드백 및 해설 생성
- ✅ 5등급 체계 산출 (Beginner ~ Elite)
- ✅ 상대 순위 및 백분위 표시
- ✅ 결과 저장 및 재응시 기능
- ✅ 결과 공유용 배지/이미지 (사내)
- ✅ 마케팅, 반도체, 센서, RTL 등 "재미" 카테고리 문항

### 미포함 (Out of Scope)
- ❌ 정식 학습 일정 자동 생성 (MVP 2.0)
- ❌ 외부 결제/과금 시스템
- ❌ 관리자 콘솔 고도화
- ❌ 학습 아이템 등록/검색 (MVP 2.0)
- ❌ 커뮤니티 기능 (MVP 2.0)

---

## 👥 Key Roles & Agents

### 사용자
- **임직원 (Employee)**: 가입, 레벨 테스트 응시, 결과 확인

### 시스템 에이전트
| 에이전트 | 역할 | 담당 기능 |
|---------|------|---------|
| **Auth-Agent** | Azure AD 인증 & JWT 토큰 관리 | SSO 로그인, 세션 발급 |
| **Profile-Agent** | 사용자 프로필 관리 | 닉네임 검증, 중복 확인, 프로필 저장 |
| **Survey-Agent** | 자기평가 수집 & 검증 | 입력값 유효성 검사, 데이터 저장 |
| **Item-Gen-Agent** | 동적 문항 생성 (RAG) | 1~n차 문항 생성, 난이도 조정 |
| **Scoring-Agent** | 자동 채점 | 객관식/주관식 채점, 점수 계산 |
| **Explain-Agent** | 해설 생성 | 정답/오답 해설, 참고링크 |
| **Rank-Agent** | 순위 & 등급 산출 | 5등급 컷오프, 순위 계산, 백분위 |
| **History-Agent** | 응시 이력 관리 | 이력 저장/조회, 비교 분석 |

### 운영자 (선택)
- RAG 소스 등록, 부적절 콘텐츠 필터링 큐레이션 (최소화)

---

## 🔧 Detailed Feature Requirements

## A. 시나리오 0: 사용자 가입

### A-1. Azure AD/SSO 로그인

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-101** | Azure AD/SSO로 인증을 지원하고, 성공 시 세션·JWT 토큰을 발급해야 한다. | **M** (Must) |
| **REQ-102** | AD 인증 성공 시, 사용자가 기가입 여부를 확인하고 리다이렉션해야 한다. | **M** |
| **REQ-103** | AD 인증 실패 시, 표준 에러 메시지와 재시도 옵션, 헬프 링크를 제공해야 한다. | **M** |
| **REQ-104** | 최초/재방문 판별을 위해 쿠키·세션을 정확히 처리해야 한다. | **S** (Should) |

**수용 기준**:
- "AD 인증 성공 후 3초 내 토큰이 발급되고 세션이 유지된다."
- "AD 인증 실패 시 '다시 시도' 버튼과 '문의' 링크가 표시된다."

---

### A-2. 닉네임 등록

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-105** | 닉네임 입력 시, 실시간으로 DB와 연동하여 중복 여부를 검증해야 한다. | **M** |
| **REQ-106** | 닉네임 중복 시, 3개 이상의 유사 추천 닉네임을 자동 제안해야 한다. | **S** |
| **REQ-107** | 부적절한 단어(금칙어)를 필터링하고 사용 거부 메시지를 표시해야 한다. | **S** |
| **REQ-108** | 가입 확정 시, 사용자 정보(UID, 이메일, 부서, 닉네임, 생성일)를 DB에 저장해야 한다. | **M** |

**수용 기준**:
- "닉네임 중복 시 1초 내 대안 3개가 제안된다."
- "금칙어를 포함한 닉네임은 등록이 거부되고 사유가 표시된다."
- "가입 완료 후 DB 조회 시 사용자 레코드가 정확히 생성되어 있다."

---

### A-3. 온보딩

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-109** | 가입 완료 후 웰컴 모달을 표시하여 요약 가이드와 "레벨 테스트 시작" CTA를 제공해야 한다. | **S** |
| **REQ-110** | (선택) 개인정보·로그 수집에 대한 동의 배너를 표시할 수 있다. | **C** (Could) |

---

## B. 시나리오 1: AI 역량 레벨 테스트

### B-1. 자기평가 정보 입력

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-201** | 레벨 테스트 시작 전, 사용자의 자기평가 폼(Form)을 제공해야 한다. | **M** |
| **REQ-202** | 입력 항목은 다음을 포함해야 한다: <br> - 본인이 생각하는 수준 (초급/중급/상급) <br> - 경력(연차): 숫자 또는 범위 선택 <br> - 직군: 백엔드, 프론트엔드, DevOps, 데이터, 마케팅 등 <br> - 담당 업무: 텍스트 입력 <br> - 관심분야: 체크박스 다중 선택 (LLM, RAG, Agent Architecture, Prompt Engineering, Deep Learning 등) | **M** |
| **REQ-203** | 모든 필수 필드에 대한 유효성 검사를 수행하고, 오류 시 명확한 메시지를 표시해야 한다. | **M** |
| **REQ-204** | Survey-Agent가 입력된 데이터를 검증하고 DB에 저장해야 한다. | **M** |

**수용 기준**:
- "모든 필수 필드를 입력한 후 '다음' 버튼이 활성화된다."
- "유효하지 않은 값 입력 시 필드 옆에 에러 메시지가 표시된다."
- "제출 후 3초 내 Survey-Agent가 데이터를 저장하고 다음 화면으로 진행한다."

---

### B-2. 1차 문항 생성 및 풀이

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-301** | Item-Gen-Agent가 REQ-202의 자기평가 정보를 기반으로 1차 문항 세트(5문항)를 동적으로 생성해야 한다. | **M** |
| **REQ-302** | 생성된 문항은 다음을 포함해야 한다: <br> - 유형: 객관식, OX, 주관식 혼합 <br> - 카테고리: 사용자의 관심분야 반영 <br> - 난이도: 자기평가 수준 반영 <br> - 소스: RAG를 통해 사내/사외 지식 베이스에서 검색 | **M** |
| **REQ-303** | RAG 소스 메타(문헌명, URL 해시, 버전, 타임스탬프)를 저장하여 추적성을 확보해야 한다. | **S** |
| **REQ-304** | 문제 은행(Knowledge Base)에는 AI 기본 지식 외에 마케팅, 반도체, 센서, RTL 등 특정 카테고리의 "재미" 요소를 포함해야 한다. | **S** |
| **REQ-305** | 사용자는 생성된 문항을 순차적으로 풀이하고 답안을 제출해야 한다. | **M** |
| **REQ-306** | 테스트 진행 중 응답은 실시간으로 임시 저장되어 새로고침 시에도 복구 가능해야 한다. | **S** |

**수용 기준**:
- "자기평가 제출 후 3초 내 1차 문항이 화면에 노출된다."
- "RAG 소스 메타가 결과 화면에서 확인 가능하다."
- "마케팅, 반도체 등 특화 카테고리 문항이 확인된다."
- "테스트 중 새로고침 후 이전 응답이 복구된다."

---

### B-3. 즉시 채점 및 해설

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-307** | Scoring-Agent가 각 문항 제출 시 1초 내에 정오답 및 점수를 피드백해야 한다. | **M** |
| **REQ-308** | 채점 로직: <br> - 객관식/OX: 정답 일치 판정 <br> - 주관식: LLM 기반 키워드 매칭, 부분점수 지원 | **M** |
| **REQ-309** | (선택) 응답 시간에 따른 페널티를 적용할 수 있다. (예: 20분 초과 감점) | **C** |
| **REQ-310** | Explain-Agent가 각 문항에 대해 정답/오답 해설 및 참고링크를 생성해야 한다. | **M** |

**수용 기준**:
- "각 문항 제출 후 1초 내 '정답입니다' 또는 '오답입니다' 피드백이 표시된다."
- "주관식 채점 후 부분점수(예: 70점)가 표시된다."
- "해설에 참고 링크가 포함되어 있다."

---

### B-4. 적응형 2차~n차 문항 생성

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-311** | 1차 풀이 결과에 따라 Item-Gen-Agent가 난이도를 조정한 2차 문항 세트를 생성해야 한다. | **M** |
| **REQ-312** | 적응형 난이도 조정 로직: <br> - 점수 0~40: 난이도 유지 또는 감소 <br> - 점수 40~70: 난이도 유지 또는 약간 증가 <br> - 점수 70+: 난이도 상향 또는 초상급 활성화 | **M** |
| **REQ-313** | 2차 문항은 1차 오답 분야를 우선적으로 강화하여 생성해야 한다. | **M** |
| **REQ-314** | (선택) 3차 이상 진행 가능하나, 최소 2회 및 최대 3회로 제한할 수 있다. | **S** |

**수용 기준**:
- "1차 점수 60점 시, 2차는 중급 난이도로 생성된다."
- "1차 오답 카테고리가 2차에서 50% 이상 포함된다."

---

### B-5. 최종 결과 산출

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-401** | Rank-Agent가 모든 응시 회차의 점수를 종합하여 최종 등급을 산출해야 한다. | **M** |
| **REQ-402** | 5등급 체계: Beginner, Intermediate, Intermediate-Advanced, Advanced, Elite | **M** |
| **REQ-403** | 등급 산출 로직: <br> - 기본: 종합 점수 + 난이도 보정 (문항별 정답률 기반 가중) <br> - 초기: 베이지안 평활(백분위 기반)으로 컷오프 업데이트 | **M** |
| **REQ-404** | 결과 페이지에 다음 정보를 표시해야 한다: <br> - 최종 등급 (1~5) + 등급 해설 <br> - 종합 점수 및 분야별 점수 분석 <br> - 각 문항의 정답, 사용자 답변, 해설 <br> - 전사 상대 순위 (예: 3/506) 및 백분위 (상위 28%) | **M** |
| **REQ-405** | 동일 기간(최근 90일) 응시자 풀을 기준으로 상대 분포를 계산해야 한다. | **M** |
| **REQ-406** | 모집단 < 100일 경우, "분포 신뢰도 낮음" 라벨을 표시해야 한다. | **S** |
| **REQ-407** | 결과 페이지에 테스트 로직(간략화)과 향후 학습 계획(MVP 2.0 예고) 안내 문구를 포함해야 한다. | **S** |
| **REQ-408** | 사용자가 다운로드할 수 있는 공유용 배지/이미지(사내 피드 공유용)를 제공해야 한다. | **S** |

**수용 기준**:
- "결과 화면에 등급(1~5), 점수, 순위/모집단, 백분위가 동시에 표시된다."
- "점수 80/100 시 등급이 'Advanced'로 정확히 산출된다."
- "배지 이미지를 다운로드할 수 있다."

---

### B-6. 응시 이력 저장 및 재응시

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-409** | 모든 응시 데이터(자기평가, 문항/응답, 채점결과, 소요시간)를 DB에 저장하여 이력 관리를 해야 한다. | **M** |
| **REQ-410** | History-Agent가 직전 응시 이력을 조회하여 결과 페이지에 비교 티저(간단 차트/텍스트)를 표시해야 한다. | **S** |
| **REQ-411** | 사용자는 언제든 레벨 테스트를 반복 응시할 수 있어야 한다. | **M** |
| **REQ-412** | 재응시 시, 이전 응시 정보가 자동으로 로드되어 사용자 편의를 높여야 한다. | **S** |

**수용 기준**:
- "결과 저장 후 DB 조회 시 응시 이력이 정확히 저장되어 있다."
- "대시보드에서 '재응시' 버튼이 노출되고, 클릭 시 직전 정보가 로드된다."

---

## 📡 API Specification (Agent-wise)

### Auth-Agent

```
POST /api/v1/auth/sso-url
  → {redirect_url: string, session_id: string}

POST /api/v1/auth/callback
  요청: {code: string, state: string}
  → {user_id: string, token: string, email: string, dept: string, is_new_user: boolean}

POST /api/v1/auth/logout
  → {success: boolean}
```

### Profile-Agent

```
GET /api/v1/profile/nickname/check
  요청: {nickname: string}
  → {available: boolean, suggestions: [string], message: string}

POST /api/v1/profile/register
  요청: {user_id: string, nickname: string}
  → {user_id: string, profile_id: string, success: boolean}

GET /api/v1/profile/{user_id}
  → {user_id, email, nickname, dept, created_at, status}
```

### Survey-Agent

```
GET /api/v1/survey/schema
  → {fields: [{name, type, options?, required, validation}]}

POST /api/v1/survey/submit
  요청: {user_id, level, years, job_role, duty, interests: [string]}
  → {survey_id: string, validation_errors?: [], submitted_at: string}
```

### Item-Gen-Agent

```
POST /api/v1/items/generate
  요청: {survey_id: string, round_idx: number, prev_answers?: []}
  → {
    round_id: string,
    items: [{
      id: string,
      type: enum(multiple_choice, true_false, short_answer),
      stem: string,
      choices?: [string],
      answer_schema: {type, keywords?, correct_answer?},
      difficulty: number,
      category: string,
      rag_source_hash: string
    }],
    time_limit_seconds: number
  }

GET /api/v1/items/{item_id}
  → {id, stem, choices, type, difficulty, category}
```

### Scoring-Agent

```
POST /api/v1/scoring/submit-answers
  요청: {
    round_id: string,
    answers: [{item_id, user_answer, response_time_ms}]
  }
  → {
    round_id: string,
    per_item: [{
      item_id,
      correct: boolean,
      score: number,
      extracted_keywords?: [string],
      feedback: string
    }],
    round_score: number,
    round_stats: {avg_response_time, correct_count, total_count}
  }
```

### Explain-Agent

```
POST /api/v1/explanation/generate
  요청: {
    item_id: string,
    user_answer: string,
    correct_answer: string,
    rag_refs?: [string]
  }
  → {
    explanation: string,
    reference_links: [{title, url, source}],
    key_concepts: [string]
  }
```

### Rank-Agent

```
POST /api/v1/ranking/finalize
  요청: {
    user_id: string,
    attempt_id: string,
    rounds: [{idx, score, difficulty_stats}]
  }
  → {
    grade: enum(beginner, intermediate, intermediate_advanced, advanced, elite),
    overall_score: number,
    percentile: number,
    position: number,
    total_candidates: number,
    grade_explanation: string,
    cutoff_info: {grade, min_score, max_score}
  }
```

### History-Agent

```
GET /api/v1/history/latest
  요청: {user_id: string}
  → {
    last_attempt: {
      attempt_id, grade, score, percentile, completed_at
    },
    previous_attempts: [{id, grade, score, completed_at}],
    improvement: {grade_change, score_change, date_diff_days}
  }

POST /api/v1/history/save
  요청: {
    user_id: string,
    survey_id: string,
    rounds: [{round_id, items, answers, score}],
    final_result: {grade, score, rank}
  }
  → {attempt_id: string, success: boolean}
```

---

## 💾 Data Model

### users
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  emp_no VARCHAR(50) UNIQUE,
  dept VARCHAR(100),
  nickname VARCHAR(50) UNIQUE NOT NULL,
  created_at TIMESTAMP NOT NULL,
  last_login TIMESTAMP,
  status ENUM('active', 'inactive'),
  INDEX(email, nickname)
);
```

### user_profile_surveys
```sql
CREATE TABLE user_profile_surveys (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  self_level ENUM('beginner', 'intermediate', 'advanced'),
  years_experience INT,
  job_role VARCHAR(100),
  duty TEXT,
  interests JSON, -- ["LLM", "RAG", ...]
  submitted_at TIMESTAMP NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id)
);
```

### question_bank
```sql
CREATE TABLE question_bank (
  id UUID PRIMARY KEY,
  round_id UUID,
  item_type ENUM('multiple_choice', 'true_false', 'short_answer'),
  stem TEXT NOT NULL,
  choices JSON, -- for multiple_choice
  correct_key VARCHAR(500), -- for multiple_choice/true_false
  correct_keywords JSON, -- for short_answer
  difficulty INT, -- 1~10
  categories JSON, -- ["LLM", "RAG", ...]
  rag_source_hash VARCHAR(255),
  created_at TIMESTAMP,
  INDEX(difficulty, categories)
);
```

### attempts
```sql
CREATE TABLE attempts (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  survey_id UUID REFERENCES user_profile_surveys(id),
  started_at TIMESTAMP NOT NULL,
  finished_at TIMESTAMP,
  final_grade ENUM('beginner', 'intermediate', 'intermediate_advanced', 'advanced', 'elite'),
  final_score DECIMAL(5,2),
  percentile INT,
  rank INT,
  total_candidates INT,
  status ENUM('in_progress', 'completed'),
  FOREIGN KEY(user_id) REFERENCES users(id),
  INDEX(user_id, finished_at)
);
```

### attempt_rounds
```sql
CREATE TABLE attempt_rounds (
  id UUID PRIMARY KEY,
  attempt_id UUID NOT NULL REFERENCES attempts(id),
  round_idx INT,
  score DECIMAL(5,2),
  time_spent_seconds INT,
  created_at TIMESTAMP,
  FOREIGN KEY(attempt_id) REFERENCES attempts(id)
);
```

### attempt_answers
```sql
CREATE TABLE attempt_answers (
  id UUID PRIMARY KEY,
  round_id UUID NOT NULL REFERENCES attempt_rounds(id),
  item_id UUID REFERENCES question_bank(id),
  user_answer_raw TEXT,
  score DECIMAL(5,2),
  is_correct BOOLEAN,
  response_time_ms INT,
  created_at TIMESTAMP,
  FOREIGN KEY(round_id) REFERENCES attempt_rounds(id)
);
```

### analytics
```sql
CREATE TABLE analytics (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  event_type VARCHAR(100), -- 'signup', 'survey_submit', 'attempt_start', 'answer_submit', 'result_view'
  payload JSON,
  created_at TIMESTAMP,
  INDEX(user_id, event_type, created_at)
);
```

### ranking_snapshots
```sql
CREATE TABLE ranking_snapshots (
  id UUID PRIMARY KEY,
  snapshot_date DATE NOT NULL,
  grade_cutoffs JSON, -- {beginner: 0, intermediate: 40, ...}
  grade_distribution JSON, -- {beginner: 45, intermediate: 150, ...}
  total_population INT,
  created_at TIMESTAMP,
  UNIQUE(snapshot_date)
);
```

---

## 🎓 등급 및 랭킹 로직

### 5등급 컷오프 방식

```
점수 범위 (초기 정의, 운영 중 동적 조정):
  Beginner:               0 ~ 40점
  Intermediate:         40 ~ 60점
  Intermediate-Advanced: 60 ~ 75점
  Advanced:             75 ~ 90점
  Elite:                90 ~ 100점

최종 점수 계산:
  final_score = (round1_score × 0.4) + (round2_score × 0.6) + difficulty_bonus

  난이도 보정(difficulty_bonus):
    - 평균 정답률 > 80%: +5점
    - 평균 정답률 40~80%: ±0점
    - 평균 정답률 < 40%: -5점
```

### 상대 순위 및 백분위

```
계산 기준: 최근 90일 응시자 풀
순위 = RANK() OVER (ORDER BY final_score DESC)
백분위 = (순위 - 1) / (총 응시자 수) × 100

예시:
  순위: 3/506명
  백분위: (3-1)/506 × 100 = 0.4% (상위 0.4%)
```

### 신뢰도 관리

```
IF total_candidates < 100:
  label = "분포 신뢰도 낮음 (샘플 부족)"
  percentile_confidence = "medium"
ELSE IF total_candidates >= 100:
  percentile_confidence = "high"
```

---

## 📝 문항 품질 & RAG 요구사항

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-501** | RAG 소스 메타(문헌명, URL 해시, 버전, 타임스탐프)를 저장하여 추적 가능해야 한다. | **M** |
| **REQ-502** | 부정확/유해 콘텐츠 필터(비속어, 편향, 저작권 의심)로 부적절 문항을 자동 차단해야 한다. | **M** |
| **REQ-503** | 사용자가 문항에 대해 신고할 수 있는 채널을 제공하고, 신고 큐에 적재 후 자동 재생성을 시도해야 한다. | **S** |
| **REQ-504** | 문항의 난이도 균형(정답률)을 모니터링하여 극단값을 사전 차단해야 한다. | **S** |

---

## 🎨 UX 요구사항

### 핵심 화면 및 기능

| 화면 | 주요 요소 | 필수 기능 |
|------|---------|---------|
| **로그인** | AD 로그인 버튼, 에러 메시지 | SSO 리다이렉트, 토큰 발급 |
| **닉네임 등록** | 입력 필드, 중복 체크 버튼, 제안 목록 | 실시간 중복 검증, 자동 제안 |
| **온보딩 모달** | 요약 텍스트, "시작하기" CTA | 웰컴 메시지 표시 |
| **자기평가 폼** | 수준/경력/직군/업무/관심분야 입력 | 유효성 검사, 제출 |
| **테스트 화면** | 문항 네비게이션, 진행률, 남은 시간(선택), 임시 저장 | 순차 풀이, 실시간 저장 |
| **즉시 피드백** | 정오답 표시, 점수, 짧은 해설 | 토스트/패널 알림 |
| **결과 페이지** | 등급, 점수, 순위, 백분위, 분야별 분석, 해설 리스트 | 공유 배지 다운로드, 재응시 CTA |
| **재응시 비교** | 이전 결과 vs 현재, 차트/텍스트 비교 | History-Agent 데이터 표시 |

---

## ⚡ 비기능 요구사항

| 항목 | 요구사항 | 목표 |
|------|---------|------|
| **성능** | 문항 생성 ≤ 3s/세트 | 99th percentile |
| | 채점/해설 ≤ 1s/문항 | 99th percentile |
| | 결과 페이지 로드 ≤ 2s | 99th percentile |
| **가용성** | 시스템 가동률 | 99.5%+ |
| **보안** | Azure AD/SSO, JWT 토큰 관리, 역할기반 접근 | 표준 준수 |
| | 개인정보 최소 수집, 암호화 저장 | GDPR/개인정보보호법 준수 |
| **감사/로깅** | 모든 생성·채점·결과 이벤트 추적 | Event ID, User ID, Timestamp |
| **접근성** | 키보드 전용 탐색, 명도 대비 | WCAG 2.1 AA 준수 |
| **국제화** | 한국어 기본, 영어 확장 지원 | 문항·해설 다국어 플래그 |

---

## 🚨 에러 & 엣지 케이스

| 시나리오 | 처리 방식 | 사용자 안내 |
|---------|---------|-----------|
| **AD 인증 실패** | 재시도 1회 + 헬프 링크 제공 | "계정 정보를 다시 확인해주세요" |
| **닉네임 중복** | 대안 3개 자동 제안 | "다음 닉네임을 추천합니다" |
| **닉네임 금칙어** | 거부 + 이유 안내 | "부적절한 단어가 포함되었습니다" |
| **테스트 중 이탈/새로고침** | 자동 저장 후 재개 | "이전 진행 상황에서 재개됩니다" |
| **문항 생성 타임아웃** | 재시도 1회 + 캐시 세트 대체 | "문항을 불러오는 중입니다" |
| **채점 오류** | 서버 로그 기록 + 안내 | "일시적 오류입니다. 관리자에 문의해주세요" |
| **표본 부족(< 100)** | 신뢰도 라벨 표시 | "현재 응시자가 적어 분포 신뢰도가 낮습니다" |

---

## 🎯 우선순위 (MoSCoW)

### Must (필수)
- ✅ REQ-101~REQ-108: AD 로그인, 닉네임 등록
- ✅ REQ-201~REQ-203: 자기평가 입력
- ✅ REQ-301~REQ-306: 문항 생성 및 풀이
- ✅ REQ-307~REQ-310: 채점 및 해설
- ✅ REQ-311~REQ-313: 적응형 난이도
- ✅ REQ-401~REQ-405: 등급 및 순위 산출
- ✅ REQ-409, REQ-411: 이력 저장 및 재응시
- ✅ REQ-501, REQ-502: 콘텐츠 품질 & 필터링

### Should (권장)
- ✅ REQ-106, REQ-107: 닉네임 제안, 금칙어 필터
- ✅ REQ-303, REQ-304: RAG 소스 해시, 재미 카테고리
- ✅ REQ-306, REQ-310: 자동 저장, 해설 생성
- ✅ REQ-406, REQ-407: 신뢰도 라벨, 학습 예고
- ✅ REQ-408: 공유 배지
- ✅ REQ-410, REQ-412: 비교 분석, 자동 로드

### Could (선택)
- ✅ REQ-109: 온보딩 모달
- ✅ REQ-110: 개인정보 동의
- ✅ REQ-309: 시간 페널티
- ✅ REQ-314: 3회차 이상
- ✅ REQ-504: 난이도 모니터링

---

## 📊 성공 지표 (KPI)

| 지표 | 목표값 | 측정 주기 |
|------|--------|---------|
| 가입 완료율 | ≥ 90% | 주간 |
| 레벨 테스트 완료율 | ≥ 70% | 주간 |
| 평균 테스트 소요 시간 | 15~20분 | 주간 |
| 문항 생성 실패 대체율 | ≤ 3% | 일간 |
| 평균 응답 시간/문항 | ≤ 3분 | 주간 |
| 결과 공유 클릭률 | ≥ 20% | 주간 |
| 재응시 전환율 | ≥ 25% | 월간 |
| 시스템 가동률 | ≥ 99.5% | 일간 |

---

## ✅ 수용 기준 (Acceptance Criteria) 예시

1. **가입 완료**
   - "사용자가 AD 로그인 후 3초 내 토큰이 발급된다."
   - "닉네임 중복 시 1초 내 대안 3개가 제안된다."
   - "가입 완료 후 DB에 사용자 레코드가 생성된다."

2. **문항 생성**
   - "자기평가 제출 후 3초 내 1차 문항이 화면에 노출된다."
   - "마케팅, 반도체 등 특화 카테고리 문항이 포함된다."

3. **채점 & 해설**
   - "각 문항 제출 후 1초 내 '정답/오답' 피드백이 표시된다."
   - "해설에 참고 링크가 포함되어 있다."

4. **결과 페이지**
   - "등급(1~5), 점수, 순위/모집단, 백분위가 동시에 표시된다."
   - "배지 이미지를 다운로드할 수 있다."

5. **재응시**
   - "대시보드에서 '재응시' 버튼이 노출되고, 클릭 시 직전 정보가 로드된다."

---

## 🚀 릴리스 슬라이스 (Release Plan)

### R1: 기본 가입 및 온보딩
- AD 로그인/SSO
- 닉네임 등록 (중복 체크)
- 온보딩 모달

**완료 기준**: 사용자가 가입을 완료하고 대시보드에 접근 가능

---

### R2: 자기평가 → 1차 테스트
- 자기평가 폼 입력
- Item-Gen-Agent 1차 문항 생성
- 순차적 문항 풀이
- Scoring-Agent 채점
- Explain-Agent 해설 생성
- 간소 결과 페이지

**완료 기준**: 사용자가 1차 테스트를 완료하고 기본 결과를 확인

---

### R3: 적응형 2차 & 최종 결과
- 적응형 2차 문항 생성
- 5등급 산출 & 순위 계산
- 상세 결과 페이지 (등급, 점수, 순위, 백분위)
- 이력 저장 및 재응시 기능
- 공유 배지

**완료 기준**: MVP 1.0.0 핵심 기능 완성

---

### R4: 품질 & 성능 최적화
- RAG 주입 및 소스 해시 저장
- 콘텐츠 품질 필터 (비속어, 편향)
- 문항 신고 채널
- 성능 튜닝 (생성 시간 < 3s, 채점 < 1s)

**완료 기준**: MVP 1.0.0 프로덕션 레벨 완성

---

## 🔮 향후 확장 (MVP 2.0)

다음은 MVP 2.0.0에서 구현될 예정입니다 (현재 범위 밖):

- **시나리오 2**: 학습 아이템 등록 및 관리
- **시나리오 3**: 학습 아이템 평가 (별점, 후기)
- **시나리오 4**: 학습 아이템 검색 및 필터링
- **시나리오 5**: 학습 코디네이터 (맞춤형 학습 일정 자동 생성)

자세한 내용은 `docs/user_scenarios_mvp1.md`의 "MVP 2.0 시나리오" 섹션을 참조.

---

## 📚 참고 문서

- `docs/user_scenarios_mvp1.md`: 상세 사용자 시나리오
- `docs/PROJECT_SETUP_PROMPT.md`: 프로젝트 설정 가이드
- `CLAUDE.md`: 개발 가이드 및 명령어
