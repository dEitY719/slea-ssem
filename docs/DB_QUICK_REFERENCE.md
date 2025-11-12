# SLEA-SSEM: DB & API 빠른 참고서

## 핵심 DB 구조

### 테이블 간 데이터 흐름

```
User 설문 제출 (UserProfileSurvey 생성)
  ↓
POST /generate (QuestionGenerationService)
  ├─ TestSession 생성 (round=1, status=in_progress)
  ├─ Agent 호출 (prev_answers=None)
  └─ Questions 테이블에 5개 저장
  ↓
[사용자 문제 풀기]
  ├─ POST /autosave → AttemptAnswer (user_answer만 저장)
  ├─ [선택] POST /answer/score → AttemptAnswer (is_correct, score 업데이트)
  ↓
POST /score (ScoringService.save_round_result)
  ├─ TestResult 생성 (correct_count, wrong_categories)
  └─ TestSession.status = completed
  ↓
POST /generate-adaptive (Round 2용)
  ├─ TestResult(round=1) 조회
  ├─ AdaptiveDifficultyService (난이도 조정)
  ├─ TestSession 생성 (round=2)
  ├─ Agent 호출 (prev_answers 포함)
  └─ Questions 테이블에 5개 저장 (적응형)
  ↓
[위 과정 반복 (라운드 2)]
  ↓
최종 Attempt 기록
  ├─ Attempt 생성 (final_grade, final_score, rank)
  ├─ AttemptRounds 생성 (각 라운드별)
  └─ HistoryService/RankingService 호출
```

## 핵심 테이블

| 테이블 | 역할 | Key Field | Note |
|--------|------|----------|------|
| users | 사용자 기본정보 | id (PK) | |
| user_profile_surveys | 설문 이력 (매번 NEW) | id, user_id, interests, submitted_at | 이력관리, UPDATE 없음 |
| test_sessions | 진행 중인 테스트 | id, user_id, survey_id, round, status | session_id별로 round 독립 |
| questions | 문제 저장소 | id, session_id, item_type, answer_schema, difficulty | Agent가 생성 |
| attempt_answers | 사용자 답변 (실시간) | session_id, question_id, user_answer, is_correct, score | autosave → scoring |
| test_results | 라운드 점수 기록 | session_id, round, score, correct_count, wrong_categories | Round 2 적응형 입력 |
| attempts | 최종 기록 (영구) | user_id, final_grade, final_score, rank, percentile | 랭킹 계산 포함 |
| attempt_rounds | 라운드별 과정 | attempt_id, round_idx, score | 이력 상세 |

## 핵심 개념

### prev_answers란?

- Round N+1에서 Round N의 결과를 참고하는 정보
- 포함: question_id, category, difficulty, item_type
- Agent 프롬프트에 포함되어 다음 라운드 어려움도/우선 카테고리 결정

### 채점 방식: Hybrid

1. **실시간 저장**: POST /autosave → AttemptAnswer (user_answer만)
2. **선택적 즉시 채점**: POST /answer/score → is_correct, score 업데이트
3. **라운드 완료 후**: POST /score → TestResult 생성 (약점 분석)

### Session vs Round

```
User
├─ Test Session 1 (session_id=s1, round=1)
│  └─ 5 Questions
├─ Test Session 2 (session_id=s2, round=2) ← 다른 session_id!
│  └─ 5 Questions (adaptive)
└─ Attempt (최종 기록)
   ├─ AttemptRound(round=1)
   └─ AttemptRound(round=2)
```

## API Flow 요약

### 라운드 1 시작

```
POST /generate
{
  "survey_id": "survey-uuid",
  "round": 1,
  "domain": "AI"
}
→ session_id + 5 questions
```

### 답변 저장 & 채점

```
1. POST /autosave
   {session_id, question_id, user_answer, response_time_ms}
   → saved_at (계속 다음 문제로)

2. POST /answer/score (선택)
   {session_id, question_id}
   → is_correct, score (즉시 피드백)
```

### 라운드 완료

```
POST /score?session_id=s1
→ TestResult(round=1, score=80%, wrong_categories={...})
```

### 적응형 라운드 2

```
POST /generate-adaptive
{
  "previous_session_id": "s1",
  "round": 2
}
→ new_session_id + 5 adaptive questions
```

### 재개 (타임아웃 후)

```
GET /resume?session_id=s1
→ answered_count, next_question_index, previous_answers
```

## 주의점

1. **UserProfileSurvey**: 매번 NEW 레코드 (UPDATE 없음)
2. **TestSession**: 라운드별 독립 (다른 session_id)
3. **wrong_categories**: JSON {"LLM": 1, "RAG": 0} (약점 분석)
4. **AutoSave**: session.started_at은 첫 저장 시만 설정
5. **Time Limit**: 20분(1200000ms), 초과 시 자동 paused
6. **Answer Schema**: 질문 유형별로 다른 구조
   - MC/TF: {correct_key: "B", explanation: "..."}
   - SA: {keywords: [...], explanation: "..."}

## 데이터 조회 패턴

```
현재 세션 문제들:
SELECT * FROM questions WHERE session_id = ?

사용자 답변:
SELECT * FROM attempt_answers WHERE session_id = ? AND question_id = ?

이전 라운드 점수:
SELECT * FROM test_results WHERE session_id = ? (round=1 결과로 round=2 생성)

사용자 모든 시도:
SELECT * FROM attempts WHERE user_id = ? ORDER BY created_at DESC

최종 점수:
SELECT final_score, rank, percentile FROM attempts WHERE id = ?
```
