# Agent 강건성 개선 요구사항 (Agent Robustness Requirements)

> **기반 문서**: `docs/enhance_robust_agent_A.md` (v1.2.2)
> **목표**: DeepSeek 프로덕션 환경 호환성 확보
> **전략**: 개발 환경(Gemini)에서 완벽 검증 → 프로덕션(DeepSeek) 배포

---

## Phase 0: 근본적 해결책 - Structured Output

### REQ-AGENT-0-0: 위험 관리 전략

**Description**:
Phase 0 with_structured_output 도입 시 DeepSeek 미지원 위험 관리. Gemini 개발환경에서만 feature flag로 제어.

**Priority**: P0 (CRITICAL)

**출처**: `docs/enhance_robust_agent_A.md` (Task 0.0, 172-206줄)

**Acceptance Criteria**:
- [ ] `ENABLE_STRUCTURED_OUTPUT` 환경 변수로 제어
- [ ] `should_use_structured_output()` 함수로 모델별 분기
- [ ] Gemini만 with_structured_output 활성화
- [ ] DeepSeek은 TextReActAgent 경로 유지

**Implementation**:
- File: `src/agent/config.py` (수정)
- 안전한 배포 계획: Phase 0a (Gemini) → 0b (DeepSeek 준비) → 0c (프로덕션)

**Status**: ⏳ Backlog

---

### REQ-AGENT-0-1: with_structured_output 도입

**Description**:
수동 Final Answer 파싱 제거. LangChain `with_structured_output`으로 모델 간 차이 추상화.

**Priority**: P0

**출처**: `docs/enhance_robust_agent_A.md` (Task 0.1, 207-237줄)

**Acceptance Criteria**:
- [ ] `_parse_agent_output_generate` 함수 제거
- [ ] `GenerateQuestionsResponse` Pydantic 모델로 응답
- [ ] `parse_json_robust` 등 복잡한 파싱 로직 제거
- [ ] 타입 안전성 보장

**Implementation**:
- File: `src/agent/llm_agent.py` (수정)
- 주의: `should_use_structured_output()`로 감싸서 Gemini만 적용

**Dependencies**: REQ-AGENT-0-0

**Status**: ⏳ Backlog

---

### REQ-AGENT-0-2: Two-Step Gather-Then-Generate

**Description**:
복잡한 ReAct 루프 단순화. Gather (정보 수집) → Generate (구조화된 출력) 2단계로 분리.

**Priority**: P0

**출처**: `docs/enhance_robust_agent_A.md` (Task 0.2, 239-317줄)

**Acceptance Criteria**:
- [ ] Gather 단계에서 ErrorHandler/retry 정책 적용
- [ ] `get_user_profile`, `get_difficulty_keywords` 등 도구 호출 시 재시도
- [ ] Generate 단계에서 `with_structured_output` 사용
- [ ] LLM 호출 횟수 감소 (10+ → 2-3)

**Implementation**:
- File: `src/agent/llm_agent.py` (수정)
- Class: `SimplifiedItemGenAgent`

**Dependencies**: REQ-AGENT-0-0, REQ-AGENT-0-1

**Status**: ⏳ Backlog

---

### REQ-AGENT-0-3: Pydantic 응답 모델 강화

**Description**:
도구 응답도 구조화. `dict` 반환 대신 Pydantic 모델 사용.

**Priority**: P1

**출처**: `docs/enhance_robust_agent_A.md` (Task 0.3, 319-341줄)

**Acceptance Criteria**:
- [ ] `ScoreResult` Pydantic 모델 정의
- [ ] `score_and_explain` 도구가 Pydantic 반환
- [ ] `_call_llm_score_short_answer`에서 `with_structured_output` 사용
- [ ] Field validation (ge=0, le=100 등)

**Implementation**:
- File: `src/agent/tools/*.py` (수정)

**Dependencies**: REQ-AGENT-0-1

**Status**: ⏳ Backlog

---

## Phase 1: Resilient Agent Executor + 기본 인프라

### REQ-AGENT-1-0: ResilientAgentExecutor (개발 환경 검증용)

**Description**:
개발 환경(Gemini)에서 두 경로 모두 검증. StructuredOutputAgent (개발) + TextReActAgent (프로덕션 경로).

**Priority**: P0

**출처**: `docs/enhance_robust_agent_A.md` (Task 1.0, 345-420줄)

**Acceptance Criteria**:
- [ ] 개발 환경: StructuredOutputAgent 먼저 시도
- [ ] 실패 시: TextReActAgent로 프로덕션 경로 검증
- [ ] 프로덕션: TextReActAgent가 유일한 경로
- [ ] ⚠️ "DeepSeek fallback" 개념 아님 - 프로덕션 기본 경로!

**Implementation**:
- File: `src/agent/resilient_executor.py` (신규)
- Class: `ResilientAgentExecutor`

**Status**: ⏳ Backlog

---

### REQ-AGENT-1-1: ModelCapabilityDetector (YAML 외부화)

**Description**:
모델별 지원 기능 자동 감지. YAML 파일로 외부화하여 배포 없이 설정 변경.

**Priority**: P0

**출처**: `docs/enhance_robust_agent_A.md` (Task 1.1, 421-452줄)

**Acceptance Criteria**:
- [ ] `ModelCapability` dataclass 정의
- [ ] `config/model_capabilities.yaml` 생성
- [ ] `detect_capability()` 함수로 모델 이름 기반 감지
- [ ] Gemini, DeepSeek, GPT-4 등 프로파일 정의

**Implementation**:
- File: `src/agent/model_capability.py` (신규)
- File: `config/model_capabilities.yaml` (신규)

**Status**: ⏳ Backlog

---

### REQ-AGENT-1-2: TextReActAgent (DeepSeek 프로덕션용)

**Description**:
Tool Calling 없이 순수 텍스트 기반 ReAct 실행. DeepSeek XML 처리.

**Priority**: P0 (CRITICAL)

**출처**: `docs/enhance_robust_agent_A.md` (Task 1.2, 454-636줄)

**Acceptance Criteria**:
- [ ] 텍스트 기반 ReAct 루프 구현
- [ ] Action/Action Input 파싱 (JSON + XML 지원)
- [ ] AGENT_CONFIG 통합 (max_iterations, agent_steps 보장)
- [ ] ActionSanitizer와 연동
- [ ] StructuredAgentLogger와 연동

**Implementation**:
- File: `src/agent/text_react_agent.py` (신규)
- Class: `TextReActAgent`

**Dependencies**: REQ-AGENT-1-1

**Status**: ⏳ Backlog

---

### REQ-AGENT-1-3: LiteLLM 설정 충돌 해결

**Description**:
DeepSeekProvider와 LiteLLM 간 명확한 우선순위 설정. 사내 환경 충돌 방지.

**Priority**: P0 (CRITICAL)

**출처**: `docs/enhance_robust_agent_A.md` (Task 1.3, 637-678줄)

**Acceptance Criteria**:
- [ ] `FORCE_LLM_PROVIDER` 환경 변수 지원
- [ ] 명시적 우선순위: force > 모델명 > 기본값
- [ ] LiteLLM 경로와 DeepSeekProvider 충돌 시 precedence 명확화

**Implementation**:
- File: `src/agent/config.py` (수정)

**Status**: ⏳ Backlog

---

## Phase 2: Output Parser 강화 + StructuredTool

### REQ-AGENT-2-0: StructuredTool with args_schema

**Description**:
도구 입력 자동 검증 및 coercion. Pydantic args_schema로 타입 안전성 보장.

**Priority**: P0

**출처**: `docs/enhance_robust_agent_A.md` (Task 2.0, 680-731줄)

**Acceptance Criteria**:
- [ ] `SaveQuestionArgs` Pydantic 모델 정의
- [ ] `StructuredTool.from_function`으로 도구 생성
- [ ] LangGraph 자동 입력 검증
- [ ] `@model_validator`로 복잡한 검증 로직

**Implementation**:
- File: `src/agent/tools/*.py` (수정)
- Tool: `save_generated_question`, etc.

**Status**: ⏳ Backlog

---

### REQ-AGENT-2-1: ActionSanitizer (XML → JSON 전처리)

**Description**:
LangGraph 실행 전 DeepSeek XML tool call을 JSON으로 변환.

**Priority**: P0

**출처**: `docs/enhance_robust_agent_A.md` (Task 2.1, 733-798줄)

**Acceptance Criteria**:
- [ ] `<tool_call>` XML 형식 감지
- [ ] JSON Action Input으로 변환
- [ ] LangGraph state machine에 삽입 (RunnableLambda)
- [ ] 여러 XML 패턴 지원

**Implementation**:
- File: `src/agent/action_sanitizer.py` (신규)
- Class: `ActionSanitizer`

**Dependencies**: REQ-AGENT-1-2

**Status**: ⏳ Backlog

---

### REQ-AGENT-2-2: parse_json_robust 전역 활용

**Description**:
기존 robust 파서가 사용되지 않는 곳에 적용. XML/YAML 응답 처리.

**Priority**: P1

**출처**: `docs/enhance_robust_agent_A.md` (Task 2.2, 800-827줄)

**Acceptance Criteria**:
- [ ] `score_and_explain_tool.py`에서 `parse_json_robust` 사용
- [ ] `_call_llm_score_short_answer` 함수 수정
- [ ] `_generate_explanation` 함수 수정
- [ ] `_parse_agent_output_score` 함수 수정

**Implementation**:
- File: `src/agent/tools/score_and_explain_tool.py` (수정)
- File: `src/agent/llm_agent.py` (수정)

**Status**: ⏳ Backlog

---

### REQ-AGENT-2-3: MultiFormatOutputParser

**Description**:
JSON, XML, Key-Value 등 다양한 출력 형식 처리.

**Priority**: P1

**출처**: `docs/enhance_robust_agent_A.md` (Task 2.3, 829-918줄)

**Acceptance Criteria**:
- [ ] `JSONToolCallParser` 구현
- [ ] `XMLToolCallParser` 구현
- [ ] `TextReActParser` 구현
- [ ] Fallback chain으로 순차 시도

**Implementation**:
- File: `src/agent/output_parser.py` (신규)
- Class: `MultiFormatOutputParser`

**Dependencies**: REQ-AGENT-2-1

**Status**: ⏳ Backlog

---

## Phase 3: Provider 전략 개선

### REQ-AGENT-3-1: DeepSeekProvider 전용 구현

**Description**:
DeepSeek 모델 특성에 맞는 설정. Tool Calling 비활성화, 낮은 temperature.

**Priority**: P1

**출처**: `docs/enhance_robust_agent_A.md` (Task 3.1, 920-960줄)

**Acceptance Criteria**:
- [ ] `DeepSeekProvider` 클래스 구현
- [ ] temperature 0.1로 형식 일관성 향상
- [ ] Tool Calling은 TextReActAgent에서 수동 처리
- [ ] LiteLLM 경로와 통합

**Implementation**:
- File: `src/agent/config.py` (수정)
- Class: `DeepSeekProvider`

**Dependencies**: REQ-AGENT-1-3

**Status**: ⏳ Backlog

---

### REQ-AGENT-3-2: 프롬프트 강화 (DeepSeek 최적화)

**Description**:
DeepSeek이 더 잘 따르는 프롬프트 형식. XML 사용 금지 명시.

**Priority**: P1

**출처**: `docs/enhance_robust_agent_A.md` (Task 3.2, 962-999줄)

**Acceptance Criteria**:
- [ ] `DEEPSEEK_FORMAT_ENFORCEMENT` 지시문 추가
- [ ] XML/markdown 사용 금지 명시
- [ ] 올바른 예시 + 잘못된 예시 제공
- [ ] 텍스트 기반 ReAct 형식 강조

**Implementation**:
- File: `src/agent/prompts/prompt_content.py` (수정)

**Status**: ⏳ Backlog

---

## Phase 4: 통합 테스트 및 검증

### REQ-AGENT-4-0: 테스트 인프라 구축

**Description**:
`tests/agent/` 디렉토리에 테스트 기반 구축. Mock fixtures + conftest.

**Priority**: P0

**출처**: `docs/enhance_robust_agent_A.md` (Task 4.0, 1001-1059줄)

**Acceptance Criteria**:
- [ ] `tests/agent/conftest.py` 생성
- [ ] `mock_gemini_response` fixture
- [ ] `mock_deepseek_xml_response` fixture
- [ ] `mock_deepseek_malformed_response` fixture
- [ ] 테스트 디렉토리 구조 생성

**Implementation**:
- Directory: `tests/agent/` (신규)
- Files: `conftest.py`, `fixtures/*.py`

**Status**: ⏳ Backlog

---

### REQ-AGENT-4-1: Multi-Model 호환성 테스트

**Description**:
다양한 모델에서 동작 검증. Gemini, DeepSeek, GPT-4 호환성.

**Priority**: P1

**출처**: `docs/enhance_robust_agent_A.md` (Task 4.1, 1061-1094줄)

**Acceptance Criteria**:
- [ ] `test_capability_detection` 파라미터화
- [ ] `test_text_react_agent_basic` 구현
- [ ] Mock LLM으로 텍스트 기반 ReAct 검증
- [ ] Final Answer 출력 확인

**Implementation**:
- File: `tests/agent/test_multi_model_compatibility.py` (신규)

**Dependencies**: REQ-AGENT-4-0

**Status**: ⏳ Backlog

---

### REQ-AGENT-4-2: E2E 테스트 시나리오

**Description**:
FastMCP + DB 상호작용 검증. DeepSeek XML → Sanitizer → SaveQuestion 전체 흐름.

**Priority**: P0 (CRITICAL)

**출처**: `docs/enhance_robust_agent_A.md` (Task 4.2, 1118-1204줄)

**Acceptance Criteria**:
- [ ] `test_e2e_deepseek_xml_to_save_question` 구현
- [ ] DeepSeek XML 응답 → ActionSanitizer → TextReActAgent
- [ ] `save_generated_question` tool 호출 검증
- [ ] `test_e2e_gemini_structured_output` 구현

**Implementation**:
- File: `tests/agent/test_e2e_scenarios.py` (신규)

**Dependencies**: REQ-AGENT-4-0, REQ-AGENT-2-1

**Status**: ⏳ Backlog

---

### REQ-AGENT-4-3: Key Performance Metrics

**Description**:
성과 측정 및 모델 간 비교. Grafana/Datadog 연동.

**Priority**: P1

**출처**: `docs/enhance_robust_agent_A.md` (Task 4.3, 1206-1282줄)

**Acceptance Criteria**:
- [ ] `AgentMetrics` dataclass 정의
- [ ] `MetricsCollector` 클래스 구현
- [ ] agent_execution_status, latency, token_count 추적
- [ ] Prometheus/CloudWatch 전송

**Implementation**:
- File: `src/agent/metrics.py` (신규)

**Status**: ⏳ Backlog

---

### REQ-AGENT-4-4: 구조화된 로깅

**Description**:
사내/사외 환경 간 디버깅 용이성 향상. JSON 로그 자동 내보내기.

**Priority**: P1

**출처**: `docs/enhance_robust_agent_A.md` (Task 4.4, 1284-1401줄)

**Acceptance Criteria**:
- [ ] `AgentExecutionLog` dataclass 정의
- [ ] `StructuredAgentLogger` 클래스 구현
- [ ] JSON 형식 로그 출력
- [ ] `export_session()` 메서드로 전체 세션 저장

**Implementation**:
- File: `src/agent/structured_logging.py` (신규)

**Status**: ⏳ Backlog

---

## 우선순위 매트릭스

| REQ-ID | Task | 영향도 | 위험도 | 우선순위 |
|--------|------|--------|--------|----------|
| **REQ-AGENT-0-0** | **위험 관리 전략** | **Critical** | Medium | **P0** |
| **REQ-AGENT-1-0** | **ResilientAgentExecutor** | **Critical** | Low | **P0** |
| **REQ-AGENT-1-1** | **ModelCapability YAML** | High | Low | **P0** |
| **REQ-AGENT-0-1** | **with_structured_output** | **Critical** | Medium | **P0** |
| **REQ-AGENT-0-2** | **Two-Step Gather-Generate** | **Critical** | Medium | **P0** |
| REQ-AGENT-0-3 | Pydantic 응답 모델 | High | Low | P1 |
| **REQ-AGENT-1-2** | **TextReActAgent** | **High** | Low | **P0** |
| **REQ-AGENT-1-3** | **LiteLLM 설정 충돌** | **High** | Low | **P0** |
| **REQ-AGENT-2-0** | **StructuredTool args_schema** | **High** | Low | **P0** |
| **REQ-AGENT-2-1** | **ActionSanitizer** | **High** | Medium | **P0** |
| REQ-AGENT-2-2 | parse_json_robust 활용 | High | Low | P1 |
| REQ-AGENT-2-3 | MultiFormatOutputParser | High | Medium | P1 |
| **REQ-AGENT-4-0** | **테스트 인프라** | **High** | Low | **P0** |
| **REQ-AGENT-4-2** | **E2E 테스트** | **High** | Low | **P0** |
| REQ-AGENT-4-3 | Key Performance Metrics | High | Low | P1 |
| REQ-AGENT-4-4 | 구조화된 로깅 | High | Low | P1 |
| REQ-AGENT-3-1 | DeepSeekProvider | Medium | Low | P1 |
| REQ-AGENT-3-2 | 프롬프트 강화 | Medium | Low | P1 |
| REQ-AGENT-4-1 | Multi-Model 테스트 | Medium | Low | P1 |

---

## 구현 순서 (4주 계획)

### Week 1: 기반 인프라 + 위험 관리
- REQ-AGENT-4-0 (테스트 인프라)
- REQ-AGENT-0-0 (위험 관리)
- REQ-AGENT-1-0 (ResilientAgentExecutor)
- REQ-AGENT-1-1 (ModelCapability)

### Week 2: 핵심 구현 - Phase 0 + Phase 1
- REQ-AGENT-1-3 (LiteLLM 충돌 해결)
- REQ-AGENT-0-1 (with_structured_output)
- REQ-AGENT-0-2 (Two-Step Gather-Generate)
- REQ-AGENT-4-2 (E2E 테스트)

### Week 3: 호환성 레이어 + 안전성
- REQ-AGENT-1-2 (TextReActAgent)
- REQ-AGENT-2-0 (StructuredTool)
- REQ-AGENT-2-1 (ActionSanitizer)
- REQ-AGENT-4-3 (Metrics)

### Week 4: 검증 + 배포 준비
- REQ-AGENT-4-1 (Multi-Model 테스트)
- REQ-AGENT-4-4 (구조화된 로깅)
- 프로덕션 배포 (DeepSeek)

---

**문서 생성일**: 2025-12-05
**기반 문서**: `docs/enhance_robust_agent_A.md` v1.2.2
