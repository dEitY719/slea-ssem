# Simplified Robust Agent Plan (Reflecting Internal Environment)

**Date**: 2025-12-06
**Author**: Gemini
**Goal**: Fix internal deployment errors with minimal changes, avoiding over-engineering.

---

## 1. Analysis of Current Situation & "Over-Engineering"

### Diagnosis
You correctly identified that `AGENT-REQUIREMENTS.md` was assuming the worst-case scenario (Model doesn't support Tool Calling).
- **Previous Assumption**: Internal model cannot use Tools → Need `TextReActAgent` (Regex parsing).
- **Actual Fact**: Internal models (`deepseek-v3`, `gpt-oss-120b`) **DO support Tool Calling**.

### Conclusion
**We do NOT need `TextReActAgent`.**
Building a separate regex-based agent path is unnecessary complexity (Over-Engineering). We should stick to the standard **LangChain Tool Calling** architecture which you already verified with Gemini.

## 2. Solving the "ReAct vs. Structured Output" Conflict

### The Problem
> "ReAct needs to loop (call tools), but `with_structured_output` forces a final JSON and stops the loop."

### The Solution: "Final Answer as a Tool"
We don't need `with_structured_output` on the *Agent* itself. Instead, we force the Agent to deliver its final result **via a Tool**.

**Design Change**:
Instead of:
```text
Agent: (Thoughts...)
Agent: Final Answer: { "questions": [...] }  <-- Text parsing required (Fragile)
```

Use:
```text
Agent: (Thoughts...)
Agent: Call Tool `submit_final_questions({ "questions": [...] })` <-- Pydantic Validation (Robust)
```

**Why this is better:**
1.  **Maintains ReAct Loop**: The model can call `get_user_profile` -> `get_keywords` -> and finally `submit_final_questions`.
2.  **Type Safety**: The `submit_final_questions` tool uses the exact same Pydantic schema we wanted for Structured Output.
3.  **Model Agnostic**: Works on Gemini, DeepSeek, and GPT-OSS as long as they support Tool Calling.

## 3. Model Recommendation: `gpt-oss-120b` vs `deepseek-v3`

Since you have the option, I strongly recommend prioritizing **`gpt-oss-120b`** for the following reasons:

1.  **Standardization**: "gpt-oss" usually implies adherence to standard OpenAI API patterns. DeepSeek sometimes has unique formatting quirks (even with tool support).
2.  **Capacity**: 120B parameters generally offer superior reasoning and instruction-following capabilities compared to smaller optimized models.
3.  **Stability**: Less likely to hallucinate XML or non-standard tool formats.

**Strategy**: Design for `gpt-oss-120b` (Standard Tool Calling) -> This will likely work for DeepSeek too.

## 4. Minimal Action Plan (Revised)

We will scrap the complex Phase 0/1/2 plan from the previous document. Here is the simplified workflow:

### Step 1: Define the "Final Tool"
Rename or wrap the existing logic into a specific submission tool.
- Currently, you might be relying on `save_generated_question` (called multiple times) or a Final Answer text.
- We will create a `submit_generated_round(questions: List[Question])` tool.

### Step 2: Update Agent Prompt
Tell the Agent:
> "Do NOT output a text Final Answer. You MUST finish the task by calling the `submit_generated_round` tool with all generated questions."

### Step 3: Remove Text Parsing
Delete `_parse_agent_output_generate` and the regex logic.
- **New Flow**:
    1. Agent Loop (LangGraph/Executor)
    2. Agent calls `Tool 1`, `Tool 3`...
    3. Agent calls `submit_generated_round`
    4. We extract the arguments from that specific tool call as the final result.

## 5. Immediate To-Do List

1.  **[Config]** Change `config.py` to allow selecting `gpt-oss-120b` (via LiteLLM or compatible interface).
2.  **[Schema]** Ensure `GenerateQuestionsResponse` (Pydantic) is registered as a **Tool**.
3.  **[Agent]** Update `llm_agent.py` to look for the *submission tool call* instead of parsing `result["output"]`.

---

**Decision Required**:
Do you agree with this "Final Tool" approach? It avoids the "Gather-Then-Generate" complexity while solving the robustness issue.
