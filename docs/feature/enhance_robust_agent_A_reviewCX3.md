# Review 3: enhance_robust_agent_A (CX)

## Positive Alignment
- REQ-ID 체계가 별도 문서(`docs/AGENT-REQUIREMENTS.md`)로 정리되었지만, 본 문서에서도 Phase별 목표·우선순위를 그대로 유지하고 있어 추적 가능성이 높습니다 (`docs/enhance_robust_agent_A.md:959-1004`).
- DeepSeek 대응을 위해 TextReActAgent, ActionSanitizer, StructuredTool 등의 방안을 명시적으로 제안하고 있어 기술적 대응 옵션은 충분히 다양합니다 (`docs/enhance_robust_agent_A.md:360-514`).

## Remaining Gaps / Suggestions
1. **REQ 매핑이 본문에 명시되지 않음**  
   - 새로 정의한 REQ-ID가 본 문서에는 등장하지 않아, Task ↔ REQ 추적이 여전히 Reader 해석에 맡겨져 있습니다.  
   - *제안*: 각 Phase 섹션의 Task 제목 바로 옆에 `REQ-AGENT-x-y`를 병기하거나, Phase 도입부에 REQ 테이블을 간단히 삽입해 문서 간 왕복 없이도 추적 가능하도록 해 주세요.

2. **Risk/rollback 전략 구체화 필요 (REQ-AGENT-0-0 대응)**  
   - "Option A vs B" 비교는 있지만 실제 롤백/feature flag 전략, rollout metric, 실패 시 즉시 전환 절차가 적혀 있지 않습니다 (`docs/enhance_robust_agent_A.md:984-1002`).  
   - *제안*: Phase 0 섹션 하단에 "Risk Mitigation" 단락을 추가하여, Structured Output 실패 시 TextReActAgent로 자동 전환하는 조건, 로그/알람 기준, Disable 플래그 등을 구체적으로 명시해 주세요.

3. **Gather→Generate 경로의 구체적 시퀀스/오류 처리 누락**  
   - Gather 단계가 FastMCP 도구 호출을 그대로 사용할지, 아니면 Python 내장 호출로 대체할지 설명이 불명확하며, 기존 ErrorHandler/Retry 전략과의 연계가 없다 (`docs/enhance_robust_agent_A.md:185-225`).  
   - *제안*: Gather 단계 흐름도를 추가하고, 각 Tool 호출 지점에서 ErrorHandler/RetryStrategy를 그대로 호출한다는 것을 문서에 명시하여 향후 구현자가 재시도/큐잉 로직을 놓치지 않도록 해 주세요.

4. **TextReActAgent 운영 요구사항 미정**  
   - TextReActAgent 소개 부분은 아이디어 수준이며, `AGENT_CONFIG`(max_iterations, early_stopping), telemetry(`agent_steps`, structured logging) 유지 방안을 설명하지 않습니다 (`docs/enhance_robust_agent_A.md:360-392`).  
   - *제안*: "Operational Guarantees" 섹션을 추가해 TextReActAgent가 동일한 config/관측성을 어떻게 보장할지, Sanitizer/StructuredAgentLogger와 어떻게 연결되는지 명확히 적어 주세요.

5. **테스트 챕터에 E2E/통합 케이스 부재**  
   - Phase 4 테스트 계획은 대부분 mock 기반 단위 테스트이며, 실제 FastMCP + DB + DeepSeek XML 흐름을 검증하는 시나리오가 없습니다 (`docs/enhance_robust_agent_A.md:717-864`).  
   - *제안*: REQ-AGENT-4-2가 지칭하는 E2E 테스트가 어떤 입력·도구·기대 출력으로 구성되는지, 최소 1개 이상의 통합 시나리오(예: DeepSeek XML → Sanitizer → save_question 성공)를 문서에 추가해 주세요.

6. **Provider 선택 우선순위 명문화 필요**  
   - DeepSeekProvider 제안(`docs/enhance_robust_agent_A.md:636-676`)은 기존 `USE_LITE_LLM` 경로와 충돌할 때의 precedence나, LiteLLM 프록시에서 DeepSeek을 사용할 경우 어떤 환경 변수를 써야 하는지 설명이 부족합니다.  
   - *제안*: Provider 선택 로직을 표나 순서도로 정리하여, `LLM_MODEL`, `USE_LITE_LLM`, `FORCE_DEEPSEEK_PROVIDER` 등 환경 변수의 우선순위를 명확히 문서화하세요.

이 항목들을 보강하면, REQ 기반 개발을 착수할 때 명확한 가이드와 롤백 전략을 갖춘 설계 문서가 될 것입니다.

  다음 단계 제안:

  1. docs/enhance_robust_agent_A.md 각 Phase에 REQ-ID를 병기하고 Risk-Mitigation 단락을 추가해 주세요.
  2. Gather→Generate 흐름도와 TextReActAgent의 운영 보증(AGENT_CONFIG, logging 연동)을 문서화해 구현 시 혼선을 줄이세요.
  3. E2E 테스트(REQ-AGENT-4-2)와 Provider 선택 우선순위 규칙을 명시해 REQ-기반 개발 착수 전에 기준을 확정하세요.