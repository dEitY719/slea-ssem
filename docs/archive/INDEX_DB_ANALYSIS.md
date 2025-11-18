# SLEA-SSEM Database & API Analysis - Document Index

## 문서 구성

이 분석은 Frontend-Backend 통신 흐름을 명확히 하기 위해 3개의 문서로 구성되었습니다.

### 1. DB_STRUCTURE_AND_FLOW.md (상세 분석)

**크기**: 16KB (554줄) | **대상**: 전체 개발팀

상세한 내용:

- 1. DB 테이블 구조 (9개 핵심 테이블 상세)
- 2. API 엔드포인트 & Request/Response 흐름 (6개 핵심 API)
- 3. Key Concepts Clarification (prev_answers, 채점 방식, Session/Round)
- 4. Frontend-Backend 통신 Flow (정리)
- 5. 데이터 저장 경로 요약
- 6. 특이사항 & 주의점
- 7. API 엔드포인트 전체 목록 (9개)

**읽는 시간**: 20-30분 | **언제 읽을까**: 전체 아키텍처를 이해해야 할 때

---

### 2. DB_QUICK_REFERENCE.md (빠른 참고서)

**크기**: 4.7KB (149줄) | **대상**: 개발 중에 참고할 사항

요약된 내용:

- 핵심 DB 구조 (테이블 간 데이터 흐름)
- 핵심 테이블 (8개, 역할별)
- 핵심 개념 (prev_answers, 채점 방식, Session/Round)
- API Flow 요약 (5개 주요 API)
- 주의점 (6가지)
- 데이터 조회 패턴 (SQL 예시)

**읽는 시간**: 5분 | **언제 읽을까**: 개발 중에 빠르게 참고할 때

**추천**: 이 문서를 인쇄하거나 즐겨찾기에 추가하세요!

---

### 3. DB_ARCHITECTURE_DIAGRAM.md (시각적 가이드)

**크기**: ~10KB | **대상**: 시각적 학습을 선호하는 사람들

다이어그램:

1. High-Level Data Flow Diagram
2. Test Session Lifecycle (Round 1 → 2)
3. Answer Schema Structure by Question Type
4. API Call Sequence Diagram
5. Entity Relationship Diagram (ERD)
6. prev_answers Data Example

**읽는 시간**: 10분 | **언제 읽을까**: 전체 흐름을 시각적으로 이해하고 싶을 때

---

## 핵심 내용 at a Glance

### 1. 테이블 관계 (3줄 요약)

```
User 설문 → test_sessions(라운드별 독립) → questions + attempt_answers
                                             ↓
                                        test_results(약점분석)
                                             ↓
                                        attempts(최종기록)
```

### 2. prev_answers란?

- **What**: Round 2에서 Round 1의 정보를 참고하는 컨텍스트
- **When**: Round 2+ 생성 시에만 포함
- **How**: Agent 프롬프트에 포함되어 난이도/우선카테고리 조정

### 3. 채점 방식

```
답변저장 → 즉시채점(선택) → 라운드완료후일괄분석
autosave   /answer/score    /score API
```

### 4. Session과 Round

- **라운드별 독립**: Round 1 (session_id=s1), Round 2 (session_id=s2)
- **최종통합**: Attempt 테이블에서 final_grade + rank 기록

### 5. API Flow (한 줄씩)

1. POST /generate → 문제 생성 (Agent)
2. POST /autosave → 답변 저장
3. POST /answer/score → 즉시 채점 (선택)
4. POST /score → 라운드 점수 계산
5. POST /generate-adaptive → Round 2 적응형

---

## 개발 상황별 추천 읽기

### Frontend 개발자

1. 먼저 읽기: `DB_QUICK_REFERENCE.md` (5분)
2. 상세히 읽기: `DB_STRUCTURE_AND_FLOW.md` 섹션 2 (API 흐름) (10분)
3. 확인하기: `DB_ARCHITECTURE_DIAGRAM.md` 섹션 4 (API Sequence) (5분)

**왜?** API 요청/응답 형식과 데이터 흐름만 알면 되기 때문

### Backend 개발자

1. 먼저 읽기: `DB_STRUCTURE_AND_FLOW.md` 전체 (30분)
2. 참고하기: `DB_QUICK_REFERENCE.md` (항상 열어놓기)
3. 시각화하기: `DB_ARCHITECTURE_DIAGRAM.md` (15분)

**왜?** DB 설계, 서비스 로직, API 구현을 이해해야 하기 때문

### PM/기획자

1. 읽기: `DB_ARCHITECTURE_DIAGRAM.md` (10분)
2. 이해하기: `DB_QUICK_REFERENCE.md` (5분)

**왜?** 시스템 흐름과 핵심 개념만 알면 되기 때문

### QA/테스트

1. 읽기: `DB_QUICK_REFERENCE.md` (5분)
2. 참고: `DB_STRUCTURE_AND_FLOW.md` 섹션 4 (API Flow) (10분)
3. 테스트 케이스: `DB_STRUCTURE_AND_FLOW.md` 섹션 2 (각 API별 request/response)

**왜?** API 동작과 데이터 검증을 이해해야 하기 때문

---

## 자주 묻는 질문 (FAQ)

### Q1: prev_answers는 뭔가요?

A: `DB_QUICK_REFERENCE.md` → "핵심 개념" → "prev_answers란?" 참고
또는 `DB_ARCHITECTURE_DIAGRAM.md` → "섹션 6" 참고

### Q2: 1문제씩 채점하나요, 라운드 완료 후 일괄 채점하나요?

A: `DB_QUICK_REFERENCE.md` → "핵심 개념" → "채점 방식: Hybrid" 참고

### Q3: Session과 Round가 어떻게 다른가요?

A: `DB_QUICK_REFERENCE.md` → "핵심 개념" → "Session vs Round" 참고

### Q4: API는 몇 개인가요?

A: `DB_STRUCTURE_AND_FLOW.md` → "섹션 7" 참고 (9개)

### Q5: DB 테이블은 몇 개인가요?

A: `DB_QUICK_REFERENCE.md` → "핵심 테이블" 참고 (8개 핵심 + 추가)

---

## 추가 리소스

### 원본 소스 코드 위치

```
DB 모델: /src/backend/models/
API 라우트: /src/backend/api/questions.py
서비스 로직:
  - /src/backend/services/question_gen_service.py
  - /src/backend/services/autosave_service.py
  - /src/backend/services/scoring_service.py
  - /src/backend/services/adaptive_difficulty_service.py
Agent: /src/agent/
```

### 참고할 다른 문서

- CLAUDE.md: 프로젝트 개발 워크플로우
- docs/AGENT-TEST-SCENARIO.md: Agent 테스트 시나리오
- docs/TOOL_DOCUMENTATION_INDEX.md: Agent Tool 정의

---

## 분석 정보

**분석 날짜**: 2025-01-12
**분석자**: Claude Code (Haiku 4.5)
**분석 범위**:

- 9개 DB 테이블 분석
- 6개 주요 API 엔드포인트 분석
- Agent 통합 흐름 분석
- Frontend-Backend 통신 패턴 분석

**현재 구현 상태**: DB Persistence + Answer Schema Population ✅

---

## 문서 버전 관리

| 버전 | 날짜 | 변경사항 |
|------|------|----------|
| 1.0 | 2025-01-12 | 초기 분석 (3개 문서) |

---

## 피드백 & 개선

이 분석 문서에 대한 피드백이 있으시면:

- 명확하지 않은 부분
- 추가했으면 하는 내용
- 발견된 오류

를 알려주세요. 지속적으로 개선하겠습니다!
