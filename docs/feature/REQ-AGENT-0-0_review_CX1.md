# REQ-AGENT-0-0 리뷰 (CX1)

## 주요 이슈
1. **no_db_required 마킹이 DB 연결을 막지 못함** (`tests/conftest.py:52-80`)  
   - `patch_database_for_tools`가 `autouse=True`이면서 `db_engine`을 파라미터로 받아, `request.keywords`를 확인하기 전에도 `db_engine`이 항상 생성됩니다.  
   - `@pytest.mark.no_db_required`가 붙은 `tests/agent/test_config_risk_management.py` 역시 `TEST_DATABASE_URL`이 필요해 unit 테스트가 다시 DB 의존적으로 회귀했습니다.  
   - *제안*: `patch_database_for_tools(request)`에서 마커 확인 후 `request.getfixturevalue("db_engine")`를 호출하도록 바꾸거나, autouse=False로 되돌리고 DB가 필요한 테스트만 명시적으로 opt-in 하세요.

2. **Feature flag 분기 미적용 상태 지속** (`src/agent/config.py:210-304`, `rg should_use_structured_output`)  
   - `should_use_structured_output`는 여전히 프로덕션 경로에서 호출되지 않습니다(테스트만 참조). Gemini/DeepSeek 분기와 실패 카운트 차단이 실행 경로에 반영되지 않아 REQ-AGENT-0-0 핵심 위험 관리가 미적용입니다.  
   - *제안*: structured output을 사용하는 LLM 경로(예: `llm_agent.py` generate/score 흐름)에서 호출하도록 연결하고, 실패 카운터/로그 전달 지점을 명확히 하세요.

3. **환경 변수 적용 검증 부족** (`tests/agent/test_config_risk_management.py:45-90, 273-309`)  
   - env 플래그/임계값 테스트가 `STRUCTURED_OUTPUT_CONFIG`를 MagicMock/딕셔너리로 대체하는 방식이라, 실제 환경 변수 로딩·모듈 재로딩 경로가 검증되지 않습니다.  
   - Acceptance의 “ENV로 제어” 요구를 보수적으로 커버하려면 `patch.dict(os.environ, ...)` 후 모듈 리로드로 기본 설정이 달라지는지 확인하는 테스트를 보강하는 것이 안전합니다.

4. **롤백/알람 설정은 여전히 선언만 존재** (`src/agent/config.py:210-218`)  
   - `rollout_percentage`, `success_rate_threshold`, `latency_threshold_seconds`, `parser_error_rate_threshold` 등은 어디에서도 사용되지 않아 문서상의 위험 완화(성공률/지연/파서 에러 기반 비활성화, 알람)가 여전히 미구현 상태입니다.  
   - *제안*: 최소한 실패 카운터 상태 관리 + 알람 훅, rollout 퍼센트 반영 여부를 명시하고, 미구현이면 Progress/README에 “TODO”로 표시해 추적 가능성을 확보하세요.
