# Postmortem: Prompt Escaping Issue & SOLID-Based Refactoring

**Date**: 2025-11-19
**Status**: ✅ Resolved with Comprehensive Refactoring
**Impact**: Eliminated escaping nightmares, improved maintainability, applied SOLID principles
**Commits**: `956bc23`, `1a3044b`, `fcd76fa`, `c106c56`

---

## Executive Summary

While fixing the "No tool results extracted!" issue, adding JSON examples to the system prompt caused a **critical side effect**: LangChain's `ChatPromptTemplate.from_template()` interpreted curly braces `{}` as template variables.

**Problem**:

```python
# ❌ JSON in prompt causes template variable errors
system_prompt = """
Example:
Action Input: {"user_id": "123-456"}
"""

template = ChatPromptTemplate.from_template(system_prompt)
# Error: 'Input to ChatPromptTemplate is missing variables {"user_id"}'
```

**Root Cause**: Mixing prompt content and template logic in the same file, using `from_template()` which interprets ALL curly braces as variables.

**Solution**: Complete architectural refactoring using **Builder + Factory patterns** to separate content from logic, applying all **5 SOLID principles**.

---

## Problem Deep Dive

### The Escaping Nightmare

Initial attempts to fix this used double-brace escaping:

```python
# ❌ WRONG: Still brittle, requires careful escaping
Action Input: {{"user_id": "123-456"}}  # Extra braces!
Observation: {{"level": "초급"}}         # More escaping!
```

**Problems with escaping approach**:

1. Error-prone - easy to forget escaping on new additions
2. Fragile - breaks if you forget even one place
3. Violates SOLID principles (mixing concerns)
4. Requires updating both content AND logic for simple prompt changes
5. Hard to test (content and logic coupled)

### Why This Happened

The original `react_prompt.py` file had **240 lines mixing**:

- **Content** (system instructions, format rules, examples) - 180 lines
- **Template logic** (ChatPromptTemplate construction) - 30 lines
- **Public API** (simple function) - 30 lines

This coupling caused the escaping issue and violated multiple SOLID principles.

---

## Solution: SOLID-Based Refactoring

### Before: Monolithic Architecture

```
react_prompt.py (240 lines)
├── System prompt content (180 lines)  ← Mixed!
├── Format rules (30 lines)            ← Mixed!
├── Template logic (30 lines)          ← Mixed!
└── Hard to test and maintain
```

### After: Modular, SOLID Architecture

```
src/agent/prompts/
├── prompt_content.py (230 lines)   ← Pure text, NO escaping needed!
├── prompt_builder.py (180 lines)   ← Template logic only
└── react_prompt.py (10 lines)      ← Simple public API
```

---

## Implementation: Step-by-Step

### Step 1: Separate Content from Logic

**File**: `src/agent/prompts/prompt_content.py` (NEW)

**Key Principle**: Pure text constants - natural JSON, no escaping!

```python
# ============================================================================
# ReAct Format Rules
# ============================================================================

REACT_FORMAT_RULES = """========== CRITICAL: MANDATORY ReAct Format Rules ==========

EVERY tool usage MUST follow this COMPLETE and EXACT sequence:

1. Thought: Analyze what you need to do next
2. Action: Name of the EXACT tool to call
3. Action Input: Complete tool parameters as valid JSON dict (ALWAYS required)
4. Observation: Result returned by the tool execution
5. Thought: Analyze the result and decide next step

MANDATORY COMPLIANCE RULES (DO NOT SKIP):
✓ EVERY "Action:" MUST have a corresponding "Action Input:" on the next line
...
"""

# ============================================================================
# ReAct Example (NO escaping needed - content is separate from template)
# ============================================================================

REACT_EXAMPLE = """Example of CORRECT ReAct Format:
---
Thought: I need to get the user's profile...
Action: get_user_profile
Action Input: {"user_id": "e79a0ee1-2a36-4383-91c5-9a8a01f27b62"}
Observation: {"self_level": "초급", "interests": ["AI", "Python"], ...}
Thought: User is at beginner level...
...
---
"""

# ============================================================================
# Complete System Prompt Assembly
# ============================================================================

def get_react_system_prompt() -> str:
    """Assemble complete ReAct system prompt from content blocks.

    Uses string concatenation (not f-strings) to prevent JSON
    from being interpreted as template variables.
    """
    prompt_parts = [
        "You are a Question Generation Expert...",
        REACT_FORMAT_RULES,
        REACT_EXAMPLE,
        "Use the following format to respond:",
        # ... more parts
    ]

    # ✅ KEY: Simple concatenation, NOT f-strings
    return "\n".join(prompt_parts)
```

**Benefits**:

- JSON examples are **natural text**, no escaping needed
- Easy to modify content without touching logic
- Content can be tested independently
- No LangChain template interpretation

### Step 2: Builder Pattern for Template Logic

**File**: `src/agent/prompts/prompt_builder.py` (NEW)

```python
from abc import ABC, abstractmethod
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage

class PromptBuilder(ABC):
    """Base class for prompt builders (SOLID: Liskov Substitution)"""

    @abstractmethod
    def build(self) -> ChatPromptTemplate:
        """Build the prompt template."""
        raise NotImplementedError()


class ReactPromptBuilder(PromptBuilder):
    """Builder for ReAct prompt template"""

    def build(self) -> ChatPromptTemplate:
        """Build ReAct prompt.

        KEY CHANGE: Use SystemMessage directly instead of from_template()
        This avoids ChatPromptTemplate.from_template() which interprets {} as variables.
        """
        from langchain_core.messages import SystemMessage

        # Step 1: Get content (pure text, no escaping needed!)
        system_prompt = get_react_system_prompt()

        # Step 2: Create SystemMessage directly (NOT from_template)
        # This prevents {} in JSON from being interpreted as template variables
        system_message = SystemMessage(content=system_prompt)

        # Step 3: Create template with direct messages
        return ChatPromptTemplate.from_messages([
            system_message,  # {} stays as plain text!
            MessagesPlaceholder(variable_name="messages"),
        ])


class SimpleReactPromptBuilder(PromptBuilder):
    """Builder for simple ReAct prompt (MVP version)"""

    def build(self) -> ChatPromptTemplate:
        system_prompt = get_simple_system_prompt()
        system_message = SystemMessage(content=system_prompt)
        return ChatPromptTemplate.from_messages([
            system_message,
            MessagesPlaceholder(variable_name="messages"),
        ])
```

**Benefits**:

- Template logic is **isolated** from content
- Easy to create new prompt variations
- Testable independently
- Uses correct LangChain pattern (SystemMessage instead of from_template)

### Step 3: Factory Pattern for Flexibility

```python
class PromptFactory:
    """Factory for creating prompt builders

    SOLID: Dependency Inversion + Open/Closed
    - Clients depend on factory, not concrete builders
    - Easy to add new prompt types without modifying existing code
    """

    _builders = {
        "react": ReactPromptBuilder,
        "simple": SimpleReactPromptBuilder,
    }

    @staticmethod
    def get_builder(builder_type: str = "react") -> PromptBuilder:
        if builder_type not in PromptFactory._builders:
            raise ValueError(f"Unknown builder type: {builder_type}")
        return PromptFactory._builders[builder_type]()

    @staticmethod
    def register_builder(builder_type: str, builder_class: type) -> None:
        """Register new builder (Open/Closed Principle)"""
        if not issubclass(builder_class, PromptBuilder):
            raise TypeError(f"{builder_class} must extend PromptBuilder")
        PromptFactory._builders[builder_type] = builder_class
```

**Benefits**:

- Extensibility without modifying existing code
- Easy to register custom builders
- Centralizes builder creation logic

### Step 4: Simplify Public API

**File**: `src/agent/prompts/react_prompt.py` (MODIFIED)

```python
from src.agent.prompts.prompt_builder import PromptFactory

def get_react_prompt() -> ChatPromptTemplate:
    """ReAct prompt using Builder Pattern via Factory"""
    builder = PromptFactory.get_builder("react")
    return builder.build()


def get_simple_react_prompt() -> ChatPromptTemplate:
    """Simple ReAct prompt"""
    builder = PromptFactory.get_builder("simple")
    return builder.build()
```

**Before**: 240 lines with mixed concerns
**After**: 10 lines of clean delegation

---

## SOLID Principles Applied

### 1️⃣ Single Responsibility Principle

Each module has ONE reason to change:

| Module | Responsibility | Changes Only When |
|--------|-----------------|-------------------|
| `prompt_content.py` | Content management | Prompt rules/examples need updating |
| `prompt_builder.py` | Template construction | Template framework changes |
| `react_prompt.py` | Public API | API signature needs change |

### 2️⃣ Open/Closed Principle

**Open for extension**:

```python
# Add custom prompt type without modifying factory
class MyCustomPromptBuilder(PromptBuilder):
    def build(self) -> ChatPromptTemplate:
        # Custom implementation
        pass

PromptFactory.register_builder("custom", MyCustomPromptBuilder)
```

**Closed for modification**: No need to touch existing code.

### 3️⃣ Liskov Substitution Principle

All builders implement same interface:

```python
def build(self) -> ChatPromptTemplate:  # Same signature
    # Different implementations, same contract
```

Clients can use any builder interchangeably.

### 4️⃣ Interface Segregation Principle

Clients only depend on `build()` method:

```python
builder = PromptFactory.get_builder("react")
prompt = builder.build()  # Simple, focused interface
```

No exposure to unnecessary methods.

### 5️⃣ Dependency Inversion Principle

- Code depends on **abstractions** (PromptBuilder)
- Not on concrete implementations
- Easy to swap implementations for testing

---

## Key Technical Insight

### The Critical Difference

```python
# ❌ WRONG: from_template() interprets {} as variables
SystemMessagePromptTemplate.from_template("""
    Action Input: {"user_id": "..."}
    # {} is interpreted as template variable!
""")

# ✅ CORRECT: SystemMessage treats {} as plain text
SystemMessage(content="""
    Action Input: {"user_id": "..."}
    # {} is just plain text!
""")
```

**Why this matters**:

- `from_template()` scans ALL curly braces and treats them as variable placeholders
- `SystemMessage` just stores the string as-is, no interpretation
- When wrapped in `ChatPromptTemplate.from_messages()`, the SystemMessage content is preserved

---

## Benefits Comparison

| Aspect | Before | After |
|--------|--------|-------|
| **Escaping needed** | YES (`{{` and `}}`) | NO (natural JSON) |
| **Test ability** | Hard (mixed concerns) | Easy (separated) |
| **Modify prompts** | Risky (might break escaping) | Safe (edit content.py only) |
| **Add new prompts** | Difficult (copy-paste code) | Easy (add builder class) |
| **Code organization** | Monolithic (240 lines) | Modular (10+180+230 lines) |
| **Maintenance** | High (many responsibilities) | Low (focused modules) |
| **Future-proofing** | Fragile (escaping issues) | Robust (no parsing) |

---

## Future Extensions Made Easy

### Example 1: Add Conditional Content

```python
def get_react_system_prompt(include_examples: bool = True) -> str:
    parts = [...]
    if include_examples:
        parts.append(REACT_EXAMPLE)
    return "\n".join(parts)
```

### Example 2: Add Custom Prompt Type

```python
class DynamicPromptBuilder(PromptBuilder):
    def __init__(self, custom_rules: str):
        self.custom_rules = custom_rules

    def build(self) -> ChatPromptTemplate:
        prompt = f"Custom rules:\n{self.custom_rules}\n{get_react_system_prompt()}"
        return ChatPromptTemplate.from_messages([
            SystemMessage(content=prompt),
            MessagesPlaceholder(variable_name="messages"),
        ])

PromptFactory.register_builder("dynamic", DynamicPromptBuilder)
```

### Example 3: Modify Prompt Content

```python
# Before: Had to update both content AND escaping logic
# After: Just update prompt_content.py
REACT_FORMAT_RULES = """Updated rules..."""
# Done! No escaping needed, no template logic changes
```

---

## Verification & Testing

### Format & Lint Checks

```
ruff format . → ✅ OK
ruff check . → ✅ All checks passed!
```

### Functionality Verification

```
✅ JSON examples render correctly without escaping
✅ Input variables: ['messages']
✅ Format rules present and complete
✅ ReAct example present with natural JSON
```

### Design Verification

```
✅ Single Responsibility: Each module has one reason to change
✅ Open/Closed: Easy to extend with new builders
✅ Liskov Substitution: All builders implement same interface
✅ Interface Segregation: Clients use simple build() method
✅ Dependency Inversion: Depends on abstractions
```

---

## Files Created/Modified

### New Files

- `src/agent/prompts/prompt_content.py` (230 lines)
- `src/agent/prompts/prompt_builder.py` (180 lines)

### Modified Files

- `src/agent/prompts/react_prompt.py` (240 → 10 lines)

### Documentation

- `docs/PROMPT_SOLID_REFACTORING.md` (361 lines - complete reference)
- `CLAUDE.md` (+191 lines - LLM guidelines)

---

## Lessons for Future Projects

### Problem Pattern

Mixing content and logic leads to:

- Escaping nightmares when adding examples
- Hard to test and maintain
- Fragile when requirements change

### Prevention Checklist

When adding LLM prompts to ANY project:

- [ ] **Separate content from logic**
  - Content: `prompts/content.py` (pure text)
  - Logic: `prompts/builder.py` (template construction)

- [ ] **Use correct LangChain patterns**
  - ✅ Use `SystemMessage(content=...)` for static text
  - ❌ Don't use `from_template()` if JSON is in content

- [ ] **Apply SOLID principles**
  - Single Responsibility: Content ≠ Logic
  - Open/Closed: Easy to extend with new builders
  - Use Builder + Factory patterns

- [ ] **No escaping needed**
  - If you're double-bracing `{{`, you're doing it wrong
  - Refactor to separate content from template logic

- [ ] **Test independently**
  - Test content generation separately
  - Test template construction separately
  - Mock content when testing builders

---

## Related Documentation

### This Project's Artifacts

- `docs/PROMPT_SOLID_REFACTORING.md` - Complete implementation reference
- `docs/postmortem-litellm-no-tool-results.md` - Related issue (incomplete ReAct format)
- `CLAUDE.md` → "LLM-Based Development Guidelines" - Best practices

### External References

- **SOLID Principles**: <https://en.wikipedia.org/wiki/SOLID>
- **Builder Pattern**: <https://refactoring.guru/design-patterns/builder>
- **Factory Pattern**: <https://refactoring.guru/design-patterns/factory-method>
- **LangChain Prompts**: <https://python.langchain.com/docs/concepts/prompt_templates>

---

## Status

✅ **Architecture Refactored**: SOLID principles applied across 3 files
✅ **Escaping Issues Eliminated**: No more double-bracing needed
✅ **Tested**: All format and lint checks pass
✅ **Documented**: Complete implementation guide + best practices
✅ **Future-Proof**: Easy to extend and maintain

---

**Key Takeaway**:

When prompt content has special characters (JSON, code, etc.), **NEVER mix it with template logic**. Separate them, use `SystemMessage` instead of `from_template()`, and apply SOLID principles. This makes prompts maintainable and eliminates escaping issues entirely.

---

**Previous**: See `postmortem-litellm-no-tool-results.md` for the ReAct format issue that triggered this refactoring.
