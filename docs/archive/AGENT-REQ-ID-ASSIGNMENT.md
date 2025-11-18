# AGENT REQUIREMENT - REQ ID 부여 안내

**작성일**: 2025-11-08
**목적**: Item-Gen-Agent LangChain 구현을 위한 REQ ID 체계 정의

---

## 📌 REQ ID 체계

AGENT 개발을 위한 REQ ID는 다음 형식으로 부여합니다:

```
REQ-A-[Feature]-[SubFeature]
```

| 부분 | 설명 | 예시 |
|------|------|------|
| `A` | **Agent** (에이전트 모듈) | A = Agent, B = Backend, F = Frontend |
| `Feature` | 주요 기능 이름 | ItemGen, Tool1, Mode1, etc. |
| `SubFeature` | 세부 기능 (선택사항) | Validate, Score, Pipeline, etc. |

---

## 🤖 AGENT REQUIREMENT REQ ID 할당

### **핵심 컴포넌트**

#### **REQ-A-ItemGen: Item-Gen-Agent (통합)**

- **목적**: LangChain 기반 Item-Gen-Agent 통합
- **범위**: LangChain 에이전트 아키텍처, FastMCP 통합, ReAct 패턴
- **우선순위**: **M** (Must)
- **MVP**: 1.0

---

### **Mode 1: 문항 생성 파이프라인**

#### **REQ-A-Mode1-Pipeline: 문항 생성 모드 전체 파이프라인**

- **목적**: generate_questions() 호출 시 Tool 1-5를 순차적/조건부로 실행
- **범위**: Mode 1 도구 선택 조건, 예외 처리, 재시도 로직
- **우선순위**: **M**
- **Sub-REQ ID들**:
  - REQ-A-Mode1-Tool1: Tool 1 - Get User Profile
  - REQ-A-Mode1-Tool2: Tool 2 - Search Question Templates
  - REQ-A-Mode1-Tool3: Tool 3 - Get Difficulty Keywords
  - REQ-A-Mode1-Tool4: Tool 4 - Validate Question Quality
  - REQ-A-Mode1-Tool5: Tool 5 - Save Generated Question

#### **REQ-A-Mode1-Tool1: Get User Profile**

- **목적**: 사용자의 자기평가 정보 조회
- **입력**: user_id
- **출력**: self_level, years_experience, job_role, duty, interests, previous_score
- **에러 처리**: 실패 → 재시도 3회 → 기본값 사용
- **우선순위**: **M**
- **FastAPI 연결**: GET /api/v1/profile/{user_id}

#### **REQ-A-Mode1-Tool2: Search Question Templates**

- **목적**: 관심분야별 문항 템플릿 검색 (Few-shot 예시로 활용)
- **입력**: interests[], difficulty, category
- **출력**: [{id, stem, type, choices, correct_answer, correct_rate, usage_count, avg_difficulty_score}, ...]
- **에러 처리**: 검색 결과 없음 → 스킵 (Tool 3으로 진행)
- **우선순위**: **M**
- **FastAPI 연결**: POST /api/v1/tools/search-templates

#### **REQ-A-Mode1-Tool3: Get Difficulty Keywords**

- **목적**: 난이도별 키워드 및 개념 조회
- **입력**: difficulty, category
- **출력**: {keywords[], concepts[], example_questions[]}
- **에러 처리**: 실패 → 캐시된 키워드 반환
- **우선순위**: **M**
- **FastAPI 연결**: POST /api/v1/tools/difficulty-keywords

#### **REQ-A-Mode1-Tool4: Validate Question Quality**

- **목적**: 생성된 문항의 품질 검증 (LLM + 규칙 기반)
- **입력**: stem, question_type, choices, correct_answer, [batch]
- **출력**: {is_valid, score, rule_score, final_score, feedback, issues[], recommendation}
- **검증 기준**:
  - LLM 의미 검증 (0~1)
  - 규칙 기반 검증: 길이, 선택지 수, 중복도, 형식 (0~1)
  - final_score = min(LLM_score, rule_score)
  - **추천사항**: >= 0.85 → pass / 0.70~0.84 → revise (최대 2회) / < 0.70 → reject
- **우선순위**: **M**
- **FastAPI 연결**: POST /api/v1/tools/validate-question, POST /api/v1/tools/validate-question/batch

#### **REQ-A-Mode1-Tool5: Save Generated Question**

- **목적**: 검증 통과한 문항을 question_bank에 저장
- **입력**: item_type, stem, choices, correct_key, correct_keywords, difficulty, categories[], round_id, validation_score, explanation
- **출력**: {question_id, round_id, saved_at, success}
- **에러 처리**: 저장 실패 → 메모리 큐 임시 저장 → 배치 재시도
- **우선순위**: **M**
- **FastAPI 연결**: POST /api/v1/tools/save-question

---

### **Mode 2: 자동 채점 파이프라인**

#### **REQ-A-Mode2-Pipeline: 자동 채점 모드 전체 파이프라인**

- **목적**: score_and_explain() 호출 시 Tool 6 실행
- **범위**: Mode 2 도구 선택, 예외 처리
- **우선순위**: **M**

#### **REQ-A-Mode2-Tool6: Score & Generate Explanation**

- **목적**: 응시자의 답변을 자동 채점하고 해설 생성
- **입력**: session_id, user_id, question_id, question_type, user_answer, correct_answer, correct_keywords[], difficulty, category
- **출력**: {attempt_id, session_id, question_id, user_id, is_correct, score, explanation, keyword_matches[], feedback, graded_at}
- **채점 방식**:
  - 객관식/OX: 정확 매칭 (user_answer == correct_answer)
  - 주관식: LLM 기반 의미 평가 (키워드 포함도, 문맥 이해도)
  - 기준: >= 80점 → is_correct=True, 70~79점 → 부분 정답, < 70점 → False
- **우선순위**: **M**
- **FastAPI 연결**: POST /api/v1/tools/score-and-explain

---

### **인프라 & 통합**

#### **REQ-A-FastMCP: FastMCP 서버 구현**

- **목적**: 6개 도구를 FastMCP @tool로 등록 및 실행
- **범위**: Tool 1-6 FastMCP 래퍼, 에러 처리, 타임아웃 관리
- **우선순위**: **M**
- **위치**: src/agent/fastmcp_server.py

#### **REQ-A-LangChain: LangChain Agent 구현**

- **목적**: ReAct 패턴 기반 에이전트 루프 구현
- **범위**: 에이전트 초기화, 도구 바인딩, 실행 루프, 상태 관리
- **우선순위**: **M**
- **위치**: src/agent/llm_agent.py

#### **REQ-A-CategoryMapping: 카테고리 & 난이도 체계 통일**

- **목적**: 전체 시스템에서 단일 카테고리 체계 사용
- **범위**: 카테고리 정의, 도메인 → 상위 카테고리 매핑
- **카테고리**: "technical" (LLM, RAG, ...), "business" (전략, 관리, ...), "general" (소통, 문제해결)
- **우선순위**: **S** (Should)

#### **REQ-A-BatchProcessing: 배치 처리 지원**

- **목적**: 여러 문항을 한 번에 검증 (Tool 4)
- **범위**: 배치 API 설계, 병렬 처리, 성능 최적화
- **우선순위**: **S**
- **FastAPI 연결**: POST /api/v1/tools/validate-question/batch

---

### **데이터 & 상태 관리**

#### **REQ-A-RoundID: Round ID 생성 및 추적**

- **목적**: 문항 생성 라운드 식별 및 추적
- **규칙**: round_id = f"{test_session_id}_{round_number}_{datetime.isoformat()}"
- **우선순위**: **M**

#### **REQ-A-DataContract: Tool 입출력 데이터 계약**

- **목적**: 모든 도구의 입출력 스키마 명확화
- **범위**: Tool 1-6 데이터 타입, 선택사항 필드, 에러 응답
- **우선순위**: **M**

---

### **에러 처리 & 복원력**

#### **REQ-A-ErrorHandling: 통합 에러 처리**

- **목적**: 도구 실패 시 자동 재시도 및 폴백
- **범위**:
  - Tool 1: 재시도 3회 → 기본값
  - Tool 2: 검색 결과 없음 → 스킵
  - Tool 3: 실패 → 캐시 반환
  - Tool 4: 점수 < 0.70 → 폐기 & 재생성 (최대 2회)
  - Tool 5: 저장 실패 → 메모리 큐 → 배치 재시도
  - Tool 6: 채점 실패 → 사용자 피드백
- **우선순위**: **M**

#### **REQ-A-Logging: 에이전트 실행 로깅**

- **목적**: 디버깅 및 모니터링을 위한 상세 로깅
- **범위**: 도구 호출, 입출력, 실행 시간, 에러
- **우선순위**: **S**

---

### **테스트 & QA**

#### **REQ-A-Mode1-Test: Mode 1 (문항 생성) 통합 테스트**

- **목적**: 문항 생성 파이프라인 E2E 테스트
- **테스트 케이스**: Happy path, Tool 실패, 검증 불통과, 재시도
- **우선순위**: **M**

#### **REQ-A-Mode2-Test: Mode 2 (자동 채점) 통합 테스트**

- **목적**: 자동 채점 파이프라인 E2E 테스트
- **테스트 케이스**: 객관식/OX/주관식 채점, 부분 정답, LLM 오류
- **우선순위**: **M**

---

## 📊 전체 REQ ID 요약

### **필수 (Must - **M**)**

| REQ ID | 기능 | 영역 |
|--------|------|------|
| REQ-A-ItemGen | Item-Gen-Agent 통합 | 핵심 |
| REQ-A-Mode1-Pipeline | 문항 생성 파이프라인 | 핵심 |
| REQ-A-Mode1-Tool1 | Get User Profile | Mode 1 |
| REQ-A-Mode1-Tool2 | Search Question Templates | Mode 1 |
| REQ-A-Mode1-Tool3 | Get Difficulty Keywords | Mode 1 |
| REQ-A-Mode1-Tool4 | Validate Question Quality | Mode 1 |
| REQ-A-Mode1-Tool5 | Save Generated Question | Mode 1 |
| REQ-A-Mode2-Pipeline | 자동 채점 파이프라인 | 핵심 |
| REQ-A-Mode2-Tool6 | Score & Generate Explanation | Mode 2 |
| REQ-A-FastMCP | FastMCP 서버 구현 | 인프라 |
| REQ-A-LangChain | LangChain Agent | 인프라 |
| REQ-A-RoundID | Round ID 생성 | 데이터 |
| REQ-A-DataContract | 입출력 데이터 계약 | 데이터 |
| REQ-A-ErrorHandling | 에러 처리 | 안정성 |
| REQ-A-Mode1-Test | Mode 1 테스트 | QA |
| REQ-A-Mode2-Test | Mode 2 테스트 | QA |

### **권장 (Should - **S**)**

| REQ ID | 기능 | 영역 |
|--------|------|------|
| REQ-A-CategoryMapping | 카테고리 체계 | 데이터 |
| REQ-A-BatchProcessing | 배치 처리 | 성능 |
| REQ-A-Logging | 실행 로깅 | 운영 |

---

## 🎯 개발 순서 권장안

**Phase 1: 기초 설정** (주 1)

1. REQ-A-FastMCP: FastMCP 서버 구축
2. REQ-A-LangChain: LangChain 에이전트 초기화
3. REQ-A-DataContract: 데이터 계약 정의

**Phase 2: Mode 1 구현** (주 2-3)
4. REQ-A-Mode1-Tool1 ~ Tool5: 각 도구 구현
5. REQ-A-Mode1-Pipeline: 도구 선택 조건 및 파이프라인
6. REQ-A-Mode1-Test: 통합 테스트

**Phase 3: Mode 2 구현** (주 3-4)
7. REQ-A-Mode2-Tool6: 자동 채점 & 해설
8. REQ-A-Mode2-Pipeline: 채점 파이프라인
9. REQ-A-Mode2-Test: 채점 테스트

**Phase 4: 안정성 & 성능** (주 4-5)
10. REQ-A-ErrorHandling: 에러 처리 강화
11. REQ-A-RoundID: Round ID 추적
12. REQ-A-CategoryMapping: 카테고리 통일
13. REQ-A-BatchProcessing: 배치 처리
14. REQ-A-Logging: 로깅 & 모니터링

---

## 📝 사용 예시

**명령어**:

```bash
# REQ-A-Mode1-Tool4 (문항 검증) 개발
"REQ-A-Mode1-Tool4 기능 구현해"

# REQ-A-ErrorHandling (에러 처리) 개발
"REQ-A-ErrorHandling 개발해"

# REQ-A-Mode1-Test (Mode 1 테스트) 개발
"REQ-A-Mode1-Test 작성해"
```

---

## 🔗 관련 문서

- **Feature Requirement**: docs/feature_requirement_mvp1.md (lines 1557-2200+)
- **Backend REQ ID**: REQ-B-A1 ~ REQ-B-B6
- **Frontend REQ ID**: REQ-F-A1 ~ REQ-F-B6

---

**작성자**: Claude Code
**검토 필요**: Team Lead (REQ ID 체계 확인)
