# Agent 안정화 재계획 (CX 관점)

작성 배경: 사내 마이그레이션 시 에러가 발생했고, `docs/AGENT-REQUIREMENTS.md`의 with_structured_output 중심 설계가 과도한지 재검토가 필요합니다. 사내에서는 `deepseek-v3-0324`, `gpt-oss-120b` 두 모델만 사용 가능하며, 두 모델 모두 Tool Calling을 지원한다고 확인되었습니다.

---

## 1) 현 상황 정리
- **사외(개발)**: Gemini + ReAct Tool Calling 경로는 정상 동작 확인.
- **사내(운영 후보)**: `deepseek-v3-0324`, `gpt-oss-120b` 모두 Tool Calling 가능. 단, with_structured_output은 LangChain/LiteLLM 경로에서 지원 여부가 불안정하거나 미확인.
- **요구사항 괴리**: AGENT-REQUIREMENTS는 “with_structured_output으로 수동 파싱 제거”를 필수로 가정하지만, 실제 기능은 Tool(1-5)에 강하게 의존해 Structured Output 단독 호출로는 완결이 어렵습니다.
- **목표**: 최소 변경으로 “모델 의존성을 낮춘 ReAct+Tool” 경로를 사내에서도 안정화. 필요 시 기본 모델을 `gpt-oss-120b`로 전환 검토.

---

## 2) DeepSeek Tool Calling & LangChain 호환성
- `deepseek-v3-0324`는 OpenAI-style tool calling을 지원하므로 **ReAct+Tool 경로는 유지 가능**합니다.
- 다만 **LangChain의 `with_structured_output` 지원은 모델/프록시 조합마다 상이**합니다. LiteLLM을 통한 DeepSeek에서 이 API가 안정적으로 동작하는지는 불확실하며, 현 코드베이스에도 실제 호출 경로가 없습니다. → 구조화 출력 강제는 리스크가 큽니다.
- 결론: **Tool Calling 경로를 1차선으로 두고, 구조화 출력은 선택적·후순위**로 두는 것이 현실적입니다.

---

## 3) Over-engineering 평가
- 문제 정의와 해법 불일치: 현재 문제는 “사내 모델별 Tool 호출/파싱 호환성”인데, 요구서는 “수동 파싱 제거”에 초점을 두어 비용이 과대화되었습니다.
- generate_questions는 Tool 1-5 호출을 전제로 하므로, with_structured_output 단독으로는 완료할 수 없습니다. 오히려 ReAct 루프를 유지하면서 **모델별 Tool 호출 형식 차이를 흡수**하는 편이 비용 대비 효과가 높습니다.
- 따라서 REQ-AGENT-0-1의 목표를 “다중 LLM에서 동일 ReAct+Tool 경로 안정화”로 재정의하고, structured output은 **옵션**으로 격하하는 것을 권장합니다.

---

## 4) 모델 선택 가이드 (deepseek-v3-0324 vs gpt-oss-120b)
- **우선 실험**: 두 모델 모두 동일 프롬프트/툴 스키마로 실행하여 아래 지표를 비교합니다.
  - Tool 호출 준수율(누락/잘못된 툴 선택), JSON 형식 오류율, 응답 지연, 비용, 실패 시 회복 가능성.
- **선택 원칙**:
  - gpt-oss-120b가 Tool 호출 정확도/안정성이 우수하면 기본 모델을 gpt-oss-120b로 전환하고 DeepSeek는 백업 경로로 남깁니다.
  - 두 모델 품질이 유사하면: DeepSeek를 기본으로 하되, **모델 프로파일**(예: message schema, stop reason, tool call key 차이)을 만들어 파서/프롬프트에서 분기합니다.
- 어떤 경우든 **ReAct+Tool 경로는 공유**하고, 모델별 차이는 프롬프트/정규화 레이어에서 흡수하는 방향으로 최소화합니다.

### ✅ 결정: gpt-oss-120b를 기본 모델로 사용
- 기본 LLM: gpt-oss-120b
- 백업/대체: deepseek-v3-0324 (동일 ReAct+Tool 경로, 모델 프로파일로 분기)
- 영향:
  - 프롬프트/정규화 레이어는 gpt-oss-120b에 맞춰 우선 최적화.
  - DeepSeek는 동일 인터페이스를 유지하되, tool_call 페이로드/JSON 형식 차이를 `_extract_tool_results`와 `parse_json_robust(model_name=...)`에서 흡수.
  - with_structured_output는 Gemini 개발용 실험 옵션으로 유지, 운영 경로는 ReAct+Tool을 1순위로 사용.

---

## 5) 최소 변경 해결 전략 (권장)
1. **관측 강화**: 사내 환경에서 `generate_questions` 실행 시 messages/intermediate_steps를 로깅하여 “어디서 깨지는지”를 우선 파악합니다.
2. **모델별 프롬프트 스위치**: `get_react_prompt(model_name)` 형태로 gpt-oss-120b용을 기본값으로, DeepSeek용은 별도 분기로 관리하여 Tool 호출 실패를 줄입니다.
3. **Tool 호출 정규화 레이어**: `_extract_tool_results`에서 gpt-oss-120b/DeepSeek의 tool_call 페이로드 차이를 흡수해 일관된 `(tool_name, output)`으로 변환합니다.
4. **파싱 보강 (선택적)**: `parse_json_robust`에 `model_name` 힌트를 받아 gpt-oss-120b/DeepSeek 전용 정제 전략을 넣어 회복력을 높입니다.
5. **구조화 출력은 선택적**: Gemini(개발)에서만 `with_structured_output`을 실험적으로 유지하되, 운영 경로는 ReAct+Tool을 1순위로 둡니다. 구조화 출력이 실제로 안정화되면 그때 도입을 재평가합니다.

---

## 6) 요구사항 조정 제안
- REQ-AGENT-0-1의 Acceptance를 **“모델 독립적 ReAct+Tool 안정화”**로 재정의:
  - Tool Calling 지원 모델(DeepSeek, GPT-OSS)에서 동일한 generate_questions 플로우가 동작할 것.
  - 모델별 프롬프트/정규화로 tool_call 파싱 실패율을 낮출 것.
  - 구조화 출력(with_structured_output)은 필수가 아니라 선택적 실험으로 명시.
- Structured Output 관련 항목은 **후순위(Phase 2)**로 이동:
  - “파싱 복잡도 감소”는 필요 시에만, 모델 지원이 검증된 경우에만 추진.

---

## 7) 다음 행동 제안 (단기 1~2주)
1. 사내 두 모델에 동일 요청을 보내 **Tool call 로그/형식 차이를 수집**(gpt-oss-120b 기준, DeepSeek는 비교용).
2. `get_react_prompt` 및 `_extract_tool_results`에 **모델 프로파일 분기** 추가(기본: gpt-oss-120b, 보조: DeepSeek).
3. 파싱 에러 로그 기반으로 `parse_json_robust(model_name=...)` 정규화 규칙 보강.
4. gpt-oss-120b를 기본 모델로 고정하고, DeepSeek는 호환성 유지용 백업으로 관리.

이 방향이면 기존 구조를 유지하면서 LLM 의존성을 낮추고, 마이그레이션 이슈를 빠르게 해소할 수 있습니다. 필요한 경우 이후 단계에서 구조화 출력 도입을 다시 검토하면 됩니다.
