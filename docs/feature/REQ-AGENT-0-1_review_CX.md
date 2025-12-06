# REQ-AGENT-0-1 리뷰 (CX)

## 주요 이슈
1. **with_structured_output 미도입** (`src/agent/llm_agent.py:888-1197`, `docs/AGENT-REQUIREMENTS.md:68-89`)  
   - Acceptance 기준은 `_parse_agent_output_generate` 제거 및 `with_structured_output` 경로 도입인데, 여전히 ReAct 결과를 수동 파싱하는 기존 로직만 존재합니다. 신규 코드도 `use_structured` 값을 계산만 하고 실제 LLM 호출/파싱 경로는 전혀 분기되지 않아 기능 도입이 이뤄지지 않았습니다.  
   - *제안*: `generate_questions`에서 `should_use_structured_output`이 True일 때 `self.llm.with_structured_output(GenerateQuestionsResponse)`로 직접 호출하고, 실패 시 TextReAct 파서로 폴백하는 이중 경로를 구현해 주세요. 이후 `_parse_agent_output_generate`의 ReAct 파싱 블록과 `parse_json_robust` 호출 의존성을 제거하거나 폴백 전용으로 한정하세요.

2. **guard 무력화** (`src/agent/llm_agent.py:920-928`)  
   - `use_structured = should_use_structured_output(model_name)`로 결정만 로그하고 이후 로직에서 사용하지 않습니다. 따라서 DeepSeek에서도 구조화 출력 호출을 막지 못하고, Gemini에서도 구조화 경로를 활성화하지 못합니다. 실패 카운트/rollout 퍼센트 역시 호출 경로와 연결되지 않습니다.  
   - *제안*: `generate_questions` 진입부에서 guard 결과를 사용해 경로를 분기하고, `failure_count`를 실행기/메트릭에서 전달받도록 시그니처를 확장해 회로차단기가 실제 동작하도록 묶어 주세요.

3. **테스트가 요구사항을 검증하지 않음** (`tests/agent/test_with_structured_output.py:35-340`)  
   - 모든 테스트가 모델 생성자나 Pydantic 검증만 확인하며, `ItemGenAgent.generate_questions`를 실행하거나 `with_structured_output` 호출 여부를 단 한 번도 assert하지 않습니다. 오히려 `parse_json_robust`가 “존재해야 한다”고 고정(`115-133`, `290-298`)하여 “복잡한 파싱 로직 제거”라는 Acceptance를 역행합니다.  
   - *제안*: Gemini 모형 LLM/Executor를 목킹해 `with_structured_output` 호출 여부와 `GenerateQuestionsResponse` 직렬화 없이 반환되는지 검증하고, DeepSeek 모델에서는 ReAct 폴백이 실행되는 통합 테스트를 추가하세요. 동시에 파싱 함수 존재 여부를 고정시키는 테스트는 제거하거나 폴백 경로 전용으로 스코프를 좁혀 주세요.

4. **진척 보고 오표기** (`docs/progress/REQ-AGENT-0-1.md:1-63`, `docs/DEV-PROGRESS.md:156-161`)  
   - 코드가 여전히 수동 파싱을 사용함에도 “✅ COMPLETED”와 “with_structured_output 도입”으로 상태를 마크해 위험을 가립니다. 실제 구현 완료 전에는 REQ 상태를 Backlog/진행 중으로 돌려야 후속 작업 계획이 어긋나지 않습니다.  
   - *제안*: 구조화 출력 경로가 실행 경로에 연결되고 테스트로 검증될 때까지 두 문서의 상태와 체크박스를 In Progress 수준으로 되돌리고, 남은 작업(경로 분기, 파서 제거, 실패 카운터 연계)을 TODO로 명시하세요.
