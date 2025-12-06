# REQ-AGENT-0-0 리뷰 (CX)

## 주요 이슈
1. **Feature flag 미적용** (`src/agent/config.py:210-304`)  
   - `should_use_structured_output`는 정의되었지만 실제 에이전트/LLM 경로 어디에서도 호출되지 않습니다(`rg` 기준 테스트 파일만 참조).  
   - 결과적으로 Gemini/DeepSeek 분기나 실패 카운트 기반 차단이 운영 경로에 반영되지 않아 위험 관리(REQ-AGENT-0-0) 효과가 없습니다.  
   - *제안*: `llm_agent.py` 등 structured output을 호출하는 지점에서 `should_use_structured_output(llm.model, failure_count)`로 감싸고, 실패 횟수는 실행기/메트릭에서 전달하도록 통합 테스트를 추가해 주세요.

2. **DB 패치 autouse 해제 회귀** (`tests/conftest.py:52`, `tests/backend/test_auth_endpoint.py:137-151`)  
   - `patch_database_for_tools`가 `autouse=False`로 바뀌었지만 어떤 테스트도 이 픽스처를 명시적으로 요청하지 않습니다.  
   - `test_auth_endpoint`는 여전히 `SessionLocal()`을 직접 열기 때문에 이제 `TEST_DATABASE_URL`이 아닌 기본 `DATABASE_URL`을 사용하며, 로컬 DB 미가동 시 실패하거나 실 DB를 오염시킬 수 있습니다.  
   - *제안*: 최소한 SessionLocal을 직접 여는 테스트에서 픽스처를 요청하거나, 안전한 기본값을 위해 `autouse=True`를 유지/재도입하고 DB 의존 없는 테스트는 별도 마킹하는 방안을 검토해 주세요.

3. **테스트 커버리지 부풀림** (`tests/agent/test_config_risk_management.py:44-66, 202-229, 235-258`)  
   - 6개의 테스트가 `pass`로 남아 있고 로깅/환경 통합 테스트는 단일 assertion도 없습니다. 문서에서 언급한 18개 시나리오 중 env flag 적용, 커스텀 실패 임계값, 로그 검증, env 재적재 흐름이 실제로 검증되지 않습니다.  
   - *제안*: `patch.dict` 후 모듈 재로딩으로 env 플래그/임계값을 검증하고, `caplog`로 INFO/WARNING 메시지를 assert하며, 통합 테스트에서 실제 `STRUCTURED_OUTPUT_CONFIG` 초기화까지 검증하도록 채워 주세요.

4. **Risk mitigation 로직 미구현** (`src/agent/config.py:210-304`, `docs/progress/REQ-AGENT-0-0.md:210-314`)  
   - `rollout_percentage`, `success_rate_threshold`, `latency_threshold_seconds`, `parser_error_rate_threshold` 등 설정이 선언만 되고 어디에서도 사용되지 않습니다. 실패 누적 시 자동 비활성화/알람(문서의 rollback 전략)도 없고, `failure_count`는 호출자가 전달해야 하는 정수 파라미터일 뿐입니다.  
   - *제안*: 최소한 실패 카운터 상태 관리 + 알람 훅을 추가하고, rollout 퍼센트(DeepSeek 0%, Gemini 개발 환경 제한)를 실제 분기 로직에 반영하거나 문서에서 “미구현”으로 명시해 주세요.
