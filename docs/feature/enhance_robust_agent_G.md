# Plan to Enhance Agent Robustness for Multi-LLM Support

## 1. Problem Analysis

The current agent implementation, while functional with Gemini models, is fragile and not easily portable to other LLMs like DeepSeek. The core issues stem from:

1.  **Over-reliance on String Parsing:** The agent's logic heavily depends on the LLM producing a specific text format: a `ReAct` thought process culminating in a `Final Answer:` block containing a JSON string. This requires complex and brittle parsing logic (`output_converter.py`, `_parse_agent_output_generate` in `llm_agent.py`) to extract the final data.

2.  **Model-Specific Output Format:** The entire system assumes the LLM will follow the prescribed `ReAct/JSON` format. However, different models have their own native preferences for structured output. As observed, DeepSeek may prefer XML or have a different JSON tool-calling mechanism, causing the string-based parsing to fail completely.

3.  **Complex and Fragile Agent Loop:** The current ReAct loop is overly granular. The agent makes numerous LLM calls to decide on small steps (get profile, get keywords, validate, save). This "micro-management" by the LLM increases latency, cost, and the probability of failure at any given step. If the LLM deviates from the prescribed tool sequence, the entire process can derail.

## 2. Proposed Solution: A Modern, Model-Agnostic Architecture

To address these issues, we will refactor the agent to leverage modern features in LangChain that abstract away model differences and reduce reliance on manual parsing.

1.  **Embrace Structured Output (`with_structured_output`):**
    - We will eliminate all manual `Final Answer:` string parsing.
    - The agent's final generation step will invoke the LLM using `with_structured_output`, binding the output to a Pydantic model (e.g., `GenerateQuestionsResponse`).
    - LangChain will be responsible for adding the necessary model-specific instructions (e.g., using JSON mode for Gemini, or other techniques for different models) to ensure the output conforms to the Pydantic schema.
    - This makes the output parsing robust, reliable, and model-agnostic.

2.  **Simplify the Agent's Task (Two-Step "Gather-Then-Generate" Process):**
    - The agent's role will be simplified. Instead of a complex, multi-step reasoning process for a single request, it will follow a clear two-step pattern:
        1.  **Gather:** Use the available tools (`get_user_profile`, `get_difficulty_keywords`, etc.) to collect all necessary context and information in one or more initial steps.
        2.  **Generate:** With all the information gathered, make a **single call** to the LLM using `with_structured_output` to generate the complete, structured final response (e.g., the full list of questions).
    - This approach is more efficient, reduces the number of LLM calls, and moves complex validation/saving logic from the LLM's reasoning process into deterministic Python code.

3.  **Conditional Output Strategy (for XML Models):**
    - To explicitly support models like DeepSeek that may prefer XML, we can implement a conditional output strategy.
    - The agent will detect the model being used. If it's an XML-first model, it will use LangChain's `XMLOutputParser` and a prompt that instructs the model to generate XML. This works *with* the model's strengths, rather than against them. For JSON-native models, it will continue to use the Pydantic-based structured output.

4.  **Simplify the System Prompt:**
    - The `prompt_content.py` will be heavily refactored. The verbose and rigid instructions for the `Thought/Action/Observation` loop and `Final Answer` JSON format will be removed.
    - The new prompt will be simpler, focusing on the high-level **goal** of the task and the **tools available** for information gathering, trusting LangChain's structured output mechanisms to handle the format.

## 3. Refactoring Plan & Tasks

### Task 1: Refactor `llm_agent.py` to use `with_structured_output`
- **Objective:** Replace manual JSON parsing with LangChain's structured output mechanism.
- **Actions:**
    - In `generate_questions`, after gathering context, call the LLM with `.with_structured_output(GenerateQuestionsResponse)`.
    - Remove the `_parse_agent_output_generate` and `_parse_agent_output_score` methods. The output from the LLM will already be a Pydantic object.
    - Remove the `parse_json_robust` helper function, as it will no longer be needed.

### Task 2: Simplify the Agent Logic to a Two-Step Process
- **Objective:** Change the agent from a micro-manager to a "gather-then-generate" executor.
- **Actions:**
    - Modify the main agent invocation logic in `generate_questions`.
    - The first phase of the agent's execution will be dedicated to calling information-gathering tools (`get_user_profile`, etc.).
    - The second phase will be a single call to the LLM (as described in Task 1) to generate the final output, passing the gathered information as context.
    - Move the question validation and saving logic outside of the LLM loop. After the `GenerateQuestionsResponse` is received, iterate through the generated items in Python to validate and save them.

### Task 3: Refactor System Prompt in `prompt_content.py`
- **Objective:** Remove rigid formatting rules and simplify the prompt to focus on the goal.
- **Actions:**
    - Delete `REACT_FORMAT_RULES`, `REACT_EXAMPLE`, and `RESPONSE_FORMAT_RULES` sections.
    - Rewrite the system prompt to be a high-level directive. Example: "You are a question generation expert. Use the available tools to gather context about the user and topic. Then, generate a set of questions that meet the user's requirements."
    - The detailed tool-calling sequence (`TOOL_SELECTION_STRATEGY`) can be simplified to just describe what each tool does.

### Task 4: Deprecate and Remove `output_converter.py`
- **Objective:** Eliminate the now-redundant manual parsing module.
- **Actions:**
    - Once the `llm_agent.py` is refactored to use `with_structured_output`, the `AgentOutputConverter` class will no longer be used.
    - Delete the file `src/agent/output_converter.py`.
    - Remove any corresponding import statements in `llm_agent.py`.

### Task 5: (Optional but Recommended) Implement a Conditional XML Strategy
- **Objective:** Add explicit, robust support for XML-preferring models like DeepSeek.
- **Actions:**
    - In `llm_agent.py`, add a configuration check for the model being used.
    - If the model is `deepseek`, create a prompt that asks for XML output.
    - Use LangChain's `XMLOutputParser` to parse the result. A Pydantic-to-XML conversion might be needed to define the expected structure.
    - This ensures the agent is not just less fragile, but truly multi-modal in its output handling.
