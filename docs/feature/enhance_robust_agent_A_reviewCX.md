# Review: enhance_robust_agent_A (CX)

## Highlights I Agree With
- Phase 0에서 `with_structured_output`을 도입해 수동 파싱을 제거하려는 방향은 장기 유지보수 관점에서 큰 이득이 있으며, 모델 간 차이를 LangChain이 흡수하게 된다는 이점이 명확합니다 (`docs/enhance_robust_agent_A.md:146-225`).
- ModelCapabilityProfile + AgentFactory로 모델별 실행 경로를 분기하려는 아이디어가 제기되어, DeepSeek와 Gemini 간 차이를 구조적으로 관리할 수 있는 토대가 생겼습니다 (`docs/enhance_robust_agent_A.md:126-143`, `docs/enhance_robust_agent_A.md:360-392`).
- 테스트/로깅 강화를 Phase 4 전체로 끌어올린 점은 저 역시 지속적으로 제기했던 공백을 해소할 수 있는 좋은 기회입니다 (`docs/enhance_robust_agent_A.md:717-864`, `docs/enhance_robust_agent_A.md:928-955`).

## Observations & Recommendations
1. **Structured Output 선행 적용 위험 관리 필요**  
   - 문서 초반에서는 DeepSeek가 JSON schema/Tool Calling을 일관되게 지원하지 못한다고 명시했는데 (`docs/enhance_robust_agent_A.md:49-53`), Phase 0 로드맵은 여전히 모든 모델을 `with_structured_output` 기반으로 재구조화하는 것을 P0로 잡고 있습니다 (`docs/enhance_robust_agent_A.md:146-225`).  
   - **제안**: ModelCapabilityProfile을 먼저 적용하거나, 최소한 `with_structured_output` 사용 여부를 capability/feature flag로 감싸 단일 모델(Gemini)에서 안정화를 완료한 후 DeepSeek 경로에 rollout 하는 단계적 전략을 문서에 명시해 주세요.

2. **Gather-then-Generate 설계에 대한 에러 처리/재시도 전략 부재**  
   - Gather 단계에서 직접 `get_user_profile`, `get_difficulty_keywords` 등을 호출하도록 제안하면서도 (`docs/enhance_robust_agent_A.md:185-225`), 기존 `ErrorHandler`/`retry_strategy`가 어떻게 재사용되는지 언급이 없습니다. FastMCP tool 경계를 우회하면 현재의 재시도/큐잉/메트릭이 모두 바이패스됩니다.  
   - **제안**: Gather 단계에서도 동일한 retry/fallback 정책을 적용할 수 있도록 `ErrorHandler`를 호출하거나, 최소한 문서에 "Gather 단계는 FastMCP 도구 호출을 그대로 사용하고, Structured Output은 Generate 단계에만 적용"과 같은 명시적 가드레일을 추가해 주세요.

3. **TextReActAgent 제안이 AGENT_CONFIG 및 Observability 요구사항을 충족하는지 불명확**  
   - Text 기반 ReAct 루프를 직접 구현하겠다는 부분(`docs/enhance_robust_agent_A.md:360-392`)은 필요한 fallback이지만, 최대 반복 횟수, `agent_steps` 카운트, partial-result 반환 등의 현재 계약이 어떻게 보장되는지 설명이 없습니다. 또한 ActionSanitizer와 StructuredAgentLogger와의 연동도 누락되어 있습니다.  
   - **제안**: TextReActAgent 설계에 `AGENT_CONFIG` 파라미터를 그대로 적용하고, Sanitizer/로깅 훅을 동일하게 거칠 수 있도록 상태 전이를 정의해 주세요. 그렇지 않으면 모델별 행동 추적이 어렵습니다.

4. **테스트 계획이 단위 수준에 머물러 있음**  
   - 테스트 챕터에서 제안된 항목들은 대부분 mock 기반 단위 테스트 위주이며 (`docs/enhance_robust_agent_A.md:717-864`), 실제 FastMCP 도구/데이터베이스와 상호작용하는 integration/e2e 커버리지는 비어 있습니다.  
   - **제안**: 최소한 하나의 end-to-end 시나리오(예: mock DB + save/validate tool 호출)를 `./tools/dev.sh test` 파이프라인에 포함시키고, DeepSeek XML → Sanitizer → SaveQuestion까지 흐름을 검증하는 시퀀스를 테스트 계획에 추가해 주세요.

5. **DeepSeekProvider 정의는 있지만 LiteLLM 경로와의 우선순위/설정 충돌 설명이 부족**  
   - `LLMFactory`에서 DeepSeekProvider를 추가하려는 제안이 있으나 (`docs/enhance_robust_agent_A.md:636-676`), 기존 `USE_LITE_LLM` 플래그나 사내 프록시 설정과 충돌 시 어떻게 우선순위를 결정하는지 명시되어 있지 않습니다. 사내 환경에서는 DeepSeek가 LiteLLM 프록시를 통해 제공되는 경우가 대부분이라, 단순히 `LLM_MODEL` 문자열만으로 분기하면 설정 충돌이 생깁니다.  
   - **제안**: DeepSeekProvider 선택 조건을 "명시적 환경 변수"(예: `FORCE_DEEPSEEK_PROVIDER=True`)로 제한하거나, LiteLLM 경로와 겹칠 때의 precedence를 문서에 서술해 주세요.

---
위 항목들을 보강하면, A 문서가 제시한 근본적인 개선안이 보다 현실적인 rollout 플랜과 결합될 수 있을 것 같습니다. 필요하면 제가 Phase 1/2 세부 설계 초안을 추가로 정리하겠습니다.
