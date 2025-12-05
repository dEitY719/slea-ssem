- 문서 1.3절에서 이미 DeepSeek이 OpenAI식 tool calling/JSON schema를 안정적으로 지원하지 못한다고 명시했는데(docs/
    enhance_robust_agent_A.md:49-53), Phase 0 계획은 모든 모델에 with_structured_output을 바로 적용한다고 가정하고 있습니다(docs/
    enhance_robust_agent_A.md:146-225). 모델 능력에 따라 점진적으로 롤아웃한다는 설명이나 fallback 전략이 없어서, 동일한 문제가 반
    복될 우려가 큽니다. 우선 Gemini 계열만 대상으로 적용하고 DeepSeek는 text ReAct + Sanitizer 경로를 유지하는 등 단계적 도입 계획
    을 문서에 적어주세요.
  - Gather→Generate 리팩터링(docs/enhance_robust_agent_A.md:185-225)에서 Python 코드가 직접 get_user_profile,
    get_difficulty_keywords 등을 호출하도록 제안하지만, 기존 FastMCP 래퍼가 제공하던 retry/backoff/circuit breaker(src/agent/
    error_handler.py, retry_strategy.py)가 어떻게 재사용되는지 명시가 없습니다. 현재 ErrorHandler가 관리하던 DB/저장 실패 처리가 우
    회될 수 있으므로, Gather 단계에서도 기존 Tool 인터페이스나 ErrorHandler를 그대로 호출한다는 보충 설명이 필요합니다.
  - TextReActAgent는 DeepSeek fallback으로 소개되지만(docs/enhance_robust_agent_A.md:360-392), AGENT_CONFIG에 정의된
    max_iterations, early_stopping_method, agent_steps 등 운영 계약을 어떻게 준수하는지, Sanitizer·Structured logging과 어떻게 연동
    되는지에 대한 설계가 빠져 있습니다. 이대로면 새 Agent를 도입했을 때 관측성과 부분결과 반환 보장이 깨질 수 있으니, 상태 전이/설
    정 연동 방법을 문서에 추가해야 합니다.
  - 테스트 계획이 대부분 mock 단위 테스트에 집중되어 있고(docs/enhance_robust_agent_A.md:717-864), 실제 FastMCP Tool + DB 경로를 검
    증하는 integration/E2E 시나리오가 언급되지 않았습니다. 최근 문제들이 end-to-end 경로에서만 재현되던 만큼, 최소 한 개의 DeepSeek
    XML→Sanitizer→save_question 흐름을 ./tools/dev.sh test에서 돌릴 수 있도록 테스트 챕터에 포함해 주세요.
  - DeepSeekProvider 선택 로직(docs/enhance_robust_agent_A.md:636-676)은 LLM_MODEL 문자열만 보고 분기하는데, 기존 LiteLLM 프
    록시 기반 설정과 충돌할 때의 우선순위를 설명하지 않습니다. 사내 환경은 LiteLLM을 통해 DeepSeek를 노출하는 경우가 많으므로,
    FORCE_DEEPSEEK_PROVIDER 같은 명시적 플래그를 두거나 LiteLLM 경로와 충돌 시 precedence를 문서에 적어 운영 혼선을 막아야 합니다.

  이 다섯 가지를 문서에 보강하면 리팩터링 이후 추가 디버깅을 크게 줄일 수 있을 것입니다.