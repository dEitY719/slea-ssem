# Robust Agent CX Enhancement Plan

## Context
- External runs on `gemini-2.0-flash` are stable, but the in-house `deepseek-v3-0324` path (via LiteLLM) yields malformed tool calls (XML action inputs, inconsistent final answers) and forces manual log comparisons.
- The ItemGen agent today assumes Gemini-like behavior everywhere: `create_llm()` just flips between providers (src/agent/config.py:69-119), prompts rely on textual compliance, and JSON handling is brittle in several hotspots.
- Goal: make the `src/agent` stack model-agnostic so any compliant model (Gemini, DeepSeek, GPT, etc.) emits the same ReAct + tool JSON traces without human babysitting.

## Key Findings
1. **No model capability profiles** – Every provider shares the same prompt + execution path even though some models lack OpenAI-style tool calling or structured JSON guarantees, so DeepSeek defaults to plain text/XML despite our JSON instructions (src/agent/config.py:69-119, src/agent/llm_agent.py:592-737).
2. **Prompt-only enforcement of ReAct JSON** – The long ReAct system prompt (src/agent/prompts/prompt_content.py:19-215) is the *only* guard ensuring `Action Input` JSON. There is no runtime validation or automatic repair when a model emits XML/YAML, so the executor just forwards the malformed payload to LangGraph and fails.
3. **Tool I/O lacks structured schemas** – Every tool is decorated with `@tool` but without explicit `args_schema` / `response_model`, meaning LangGraph infers loose signatures and cannot auto-coerce or validate inputs. `score_and_explain` also calls naked LLM prompts that request JSON but parse with a single `json.loads` (src/agent/tools/score_and_explain_tool.py:207-244, 329-399), so non-JSON responses bubble up and break parsing in `_parse_agent_output_score` (src/agent/llm_agent.py:1194-1285).
4. **Parsing utilities exist but are unused where failures happen** – We have `parse_json_robust()` and the `AgentOutputConverter` cleanup strategies, yet `_parse_agent_output_score()` still uses raw `json.loads` and `score_and_explain_tool` never leverages the converter, so XML/Markdown responses immediately raise (src/agent/llm_agent.py:1253-1264).
5. **Zero regression coverage of the agent layer** – `src/agent/tests` is empty, so none of the above behaviors are exercised under pytest. There are no fixtures that simulate alternative providers, malformed tool traces, or prompt regressions.

## Plan (phased)

### Phase 1 – Capability-aware execution
1. Introduce a `ModelCapabilityProfile` (e.g., `supports_tool_calls`, `supports_json_mode`, `needs_react_text`) that is selected alongside the provider in `create_llm()`. Use it inside `ItemGenAgent.__init__` to decide whether to run `create_react_agent` in tool-calling mode or fall back to a stricter text-based ReAct executor.
2. When the profile says JSON mode is available (OpenAI/Gemini), bind `response_format={"type": "json_object"}` or `model.with_structured_output()` so DeepSeek via LiteLLM cannot emit XML even if it tries. When not available, wrap the agent input with a lightweight checker that rewrites obvious `<tool_call>` XML into JSON before LangGraph sees it.

### Phase 2 – Structured tool & output schemas
1. Convert each tool into a `StructuredTool`/`BaseTool` with a Pydantic `args_schema` so LangChain publishes a strict JSON schema (e.g., `class SaveQuestionArgs(BaseModel): item_type: Literal[...] ...`). This makes the executor auto-coerce strings and lets us validate tool inputs before execution.
2. For tool responses, switch to Pydantic models or `TypedDict` (e.g., `class ScoreResult(BaseModel)`) and plug them into LangGraph’s `ToolNode` so malformed tool outputs are surfaced instantly.
3. Inside `_call_llm_score_short_answer` and `_generate_explanation`, use `llm.with_structured_output(OutputSchema)` from LangChain 0.3 instead of free-form prompts. That API emits validated JSON regardless of the vendor and removes our ad-hoc parsing logic.

### Phase 3 – Normalization, fallbacks, and tests
1. Centralize JSON cleanup: expose `AgentOutputConverter.parse_json_robust()` (or `parse_json_robust()` from src/agent/llm_agent.py) as a shared helper and call it from `_parse_agent_output_score`, `score_and_explain_tool`, and any log processing to survive XML/Markdown payloads.
2. Add an `ActionSanitizer` step in the LangGraph state machine (custom `RunnableLambda`) that inspects each `AIMessage`, detects `<tool_call>` / YAML, and rewrites it into the expected JSON dict before the tool node executes.
3. Seed `src/agent/tests` with pytest coverage: fixtures that feed mocked `AIMessage` traces (JSON, XML, Markdown), verify sanitization, and simulate LiteLLM DeepSeek responses. Include snapshot tests for the new structured prompts + capability routing.
4. Instrument both Gemini and LiteLLM paths with structured logging (model name, profile, iteration, sanitized payload) so we can diff runs without moving logs manually.

## Task Breakdown
1. **T1 – Capability profile & routing**
   - Add `src/agent/model_profiles.py` describing each vendor’s abilities.
   - Extend `create_llm()` to return `(llm, profile)` and wire it into `ItemGenAgent` so prompt selection + executor wiring honor the profile.
2. **T2 – Structured tools overhaul**
   - Replace plain `@tool` decorators with `StructuredTool.from_function` or custom `BaseTool` classes embedding `args_schema` and `response_model`.
   - Update `fastmcp_server.TOOLS` to point at the structured instances and adjust tests/mocks.
3. **T3 – Structured LLM outputs**
   - Introduce Pydantic models for `_call_llm_score_short_answer` / `_generate_explanation` responses and invoke `llm.with_structured_output(model)`.
   - Reuse the same parser for final agent answers to stop duplicating JSON cleanup.
4. **T4 – Sanitizer & fallback parser**
   - Build a reusable `ToolCallSanitizer` runnable that normalizes XML/YAML `Action Input` strings before LangGraph executes tools.
   - Update `_parse_agent_output_score` to call the shared robust parser and include telemetry about which cleanup strategy was used.
5. **T5 – Test & telemetry harness**
   - Populate `src/agent/tests` with fixtures covering DeepSeek-style XML traces, structured tool schemas, and capability routing.
   - Emit structured logs (JSON) summarizing model, tool call arguments, and sanitization steps so on-prem debugging no longer requires manual copy/paste.

## References for implementation
- `create_llm` / provider toggle: src/agent/config.py:69-185
- Agent prompt + execution path: src/agent/llm_agent.py:549-747
- Prompt rules relying solely on text: src/agent/prompts/prompt_content.py:19-215
- Brittle JSON parsing: src/agent/llm_agent.py:1194-1265, src/agent/tools/score_and_explain_tool.py:207-244 & 329-399
- Missing tests: src/agent/tests (empty directory)
