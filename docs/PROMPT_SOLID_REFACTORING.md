# Prompt Architecture Refactoring: SOLID Principles Applied

**Date**: 2025-11-19
**Status**: ✅ Complete
**Commit**: `1a3044b`

---

## Problem Statement

지난번 프롬프트 업데이트 후 JSON 예제의 중괄호 `{}`가 LangChain의 ChatPromptTemplate 변수로 해석되어 오류가 발생했습니다.

```python
# ❌ Problem: JSON interpreted as template variables
system_prompt = """...
Action Input: {"user_id": "..."}  # {"user_id"} → detected as template variable!
...
"""

return ChatPromptTemplate.from_template(system_prompt)
```

**Error**: `'Input to ChatPromptTemplate is missing variables {"user_id"}'`

## Root Cause Analysis

### 원인 1: 내용과 로직이 혼합됨

```
react_prompt.py (240 lines)
├─ System prompt content (180 lines)
├─ Template formatting logic (30 lines)
└─ Mixed responsibilities → hard to maintain
```

### 원인 2: from_template() 의존성

```python
# from_template()은 모든 {} 를 template variable로 해석
SystemMessagePromptTemplate.from_template(system_prompt)
                           ^^^^^^^^^^^^^^^^
                           Interprets {} as variables!
```

### 원인 3: 확장성 부족

- 새로운 프롬프트 유형 추가 어려움
- 테스트 불가능 (내용과 로직이 섞여있음)
- 프롬프트 업데이트 시마다 이스케이핑 필요

---

## Solution: SOLID-Based Refactoring

### Architecture Changes

```
BEFORE (Monolithic):
react_prompt.py (240 lines)
├── Everything mixed together
└── Hard to test, modify, extend

AFTER (Modular, SOLID):
src/agent/prompts/
├── prompt_content.py (230 lines) ← Pure content blocks
├── prompt_builder.py (180 lines) ← Template logic only
└── react_prompt.py (10 lines)    ← Simple public API
```

### Key Technical Changes

#### 1. Separate Content from Logic

**prompt_content.py**:

```python
# Pure text content blocks - NO escaping needed!
REACT_FORMAT_RULES = """..."""
REACT_EXAMPLE = """
Example of CORRECT ReAct Format:
Action Input: {"user_id": "e79a0ee1-..."}  # ✅ Natural JSON!
Observation: {"self_level": "초급", ...}   # ✅ No escaping!
"""
TOOL_SELECTION_STRATEGY = """..."""
# ... etc

def get_react_system_prompt() -> str:
    # Simple concatenation - no f-strings, no escaping
    return "\n".join([
        "You are a Question Generation Expert...",
        REACT_FORMAT_RULES,
        REACT_EXAMPLE,
        # ...
    ])
```

#### 2. Builder Pattern for Template Logic

**prompt_builder.py**:

```python
class PromptBuilder(ABC):
    @abstractmethod
    def build(self) -> ChatPromptTemplate:
        pass

class ReactPromptBuilder(PromptBuilder):
    def build(self) -> ChatPromptTemplate:
        system_prompt = get_react_system_prompt()

        # ✅ KEY CHANGE: Use SystemMessage directly
        # Avoids from_template() which interprets {}
        system_message = SystemMessage(content=system_prompt)

        return ChatPromptTemplate.from_messages([
            system_message,  # {} is plain text, not variables!
            MessagesPlaceholder(variable_name="messages"),
        ])
```

#### 3. Factory Pattern for Flexibility

```python
class PromptFactory:
    _builders = {
        "react": ReactPromptBuilder,
        "simple": SimpleReactPromptBuilder,
    }

    @staticmethod
    def get_builder(builder_type: str = "react") -> PromptBuilder:
        return PromptFactory._builders[builder_type]()

# Easy to extend:
# PromptFactory.register_builder("custom", CustomPromptBuilder)
```

#### 4. Simplified Public API

**react_prompt.py**:

```python
def get_react_prompt() -> ChatPromptTemplate:
    # Just delegate to factory - clean and simple
    builder = PromptFactory.get_builder("react")
    return builder.build()
```

---

## SOLID Principles Applied

### 1️⃣ Single Responsibility Principle

- **prompt_content.py**: Only manages prompt content
- **prompt_builder.py**: Only manages template construction
- **react_prompt.py**: Only provides public API
- Each module has ONE reason to change

### 2️⃣ Open/Closed Principle

✅ **Open for extension**:

```python
class CustomPromptBuilder(PromptBuilder):
    def build(self) -> ChatPromptTemplate:
        # Custom implementation
        pass

PromptFactory.register_builder("custom", CustomPromptBuilder)
```

❌ **Closed for modification**: No need to modify existing code

### 3️⃣ Liskov Substitution Principle

All builders implement the same interface:

```python
def build(self) -> ChatPromptTemplate:  # Same signature
    # Different implementations, same contract
```

### 4️⃣ Interface Segregation Principle

Clients only depend on `build()` method:

```python
builder = PromptFactory.get_builder("react")
prompt = builder.build()  # Simple, focused interface
```

### 5️⃣ Dependency Inversion Principle

- Depends on abstraction (`PromptBuilder`)
- Not on concrete implementations
- Easy to swap implementations

---

## Technical Details

### Why SystemMessage instead of from_template()?

```python
# ❌ WRONG: from_template interprets {} as variables
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

### String Concatenation instead of f-strings

```python
# ❌ WRONG: f-strings still cause issues if {} appears
prompt = f"""Content with {json_variable}"""

# ✅ CORRECT: Simple concatenation with no interpretation
parts = ["Content", json_content, "More content"]
prompt = "\n".join(parts)
```

---

## Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Escaping needed** | YES ({{"user_id": ...}}) | NO ({"user_id": ...}) |
| **Test ability** | Hard (mixed concerns) | Easy (separated) |
| **Modify prompts** | Risky (might break escaping) | Safe (just edit content) |
| **Add new prompts** | Difficult (copy-paste code) | Easy (add builder class) |
| **Code organization** | Monolithic (240 lines) | Modular (10+180+230 lines) |
| **Maintenance** | High (many responsibilities) | Low (focused modules) |
| **Future-proofing** | Fragile (escaping issues) | Robust (no parsing) |

---

## File Structure

```
src/agent/prompts/
├── __init__.py
├── prompt_content.py (NEW - 230 lines)
│   ├── REACT_FORMAT_RULES (constant)
│   ├── REACT_EXAMPLE (constant - with natural JSON!)
│   ├── TOOL_SELECTION_STRATEGY (constant)
│   ├── RESPONSE_FORMAT_RULES (constant)
│   ├── USER_PROFICIENCY_LEVELS (constant)
│   ├── QUALITY_REQUIREMENTS (constant)
│   ├── get_react_system_prompt() → str
│   └── get_simple_system_prompt() → str
│
├── prompt_builder.py (NEW - 180 lines)
│   ├── PromptBuilder (ABC)
│   ├── ReactPromptBuilder
│   ├── SimpleReactPromptBuilder
│   ├── PromptFactory
│   └── Uses SystemMessage (no from_template)
│
└── react_prompt.py (MODIFIED - 10 lines)
    ├── get_react_prompt() → delegates to factory
    └── get_simple_react_prompt() → delegates to factory
```

---

## Testing

### Verification Results

✅ **Format & Lint**: All checks pass

```
ruff format . → OK
ruff check . → All checks passed!
```

✅ **Functionality**: Prompts render correctly

```
Input variables: ['messages']
JSON: {"user_id": "..."} rendered without escaping
Format rules present
ReAct example present
```

✅ **Design**: SOLID principles verified

```
Single Responsibility: Each module has one reason to change
Open/Closed: Easy to extend with new builders
Liskov Substitution: All builders implement same interface
Interface Segregation: Clients use simple build() method
Dependency Inversion: Depends on abstractions
```

---

## Future Improvements (Easy Now!)

### Add Custom Prompt Type

```python
# Step 1: Create builder
class MyCustomPromptBuilder(PromptBuilder):
    def build(self) -> ChatPromptTemplate:
        # Custom implementation
        pass

# Step 2: Register
PromptFactory.register_builder("custom", MyCustomPromptBuilder)

# Step 3: Use
prompt = PromptFactory.get_builder("custom").build()
```

### Modify Prompt Content

```python
# Before: Update prompt_content.py and react_prompt.py
# After: Just update prompt_content.py - template logic untouched!

# Simply edit the constant:
REACT_FORMAT_RULES = """Updated rules..."""
# Done! No escaping needed, no template logic changes
```

### Add Conditional Content

```python
def get_react_system_prompt(include_examples: bool = True) -> str:
    parts = [...]
    if include_examples:
        parts.append(REACT_EXAMPLE)
    return "\n".join(parts)
```

---

## Summary

### What Was Fixed

❌ JSON escaping issues → ✅ No escaping needed
❌ Mixed concerns → ✅ Separate modules
❌ Hard to test → ✅ Testable components
❌ Fragile code → ✅ Robust design

### How It Works

1. **Content** stays as pure text (no escaping)
2. **Logic** handles template construction cleanly
3. **Factory** manages different prompt types
4. **API** is simple and focused

### Why This Matters

This refactoring ensures that **future prompt updates will never have escaping issues again**. The architecture is now:

- ✅ Maintainable (clear separation of concerns)
- ✅ Extensible (easy to add new prompts)
- ✅ Testable (independent components)
- ✅ Robust (proper design patterns)

---

## References

- **SOLID Principles**: <https://en.wikipedia.org/wiki/SOLID>
- **Builder Pattern**: <https://refactoring.guru/design-patterns/builder>
- **Factory Pattern**: <https://refactoring.guru/design-patterns/factory-method>
- **LangChain Prompts**: <https://python.langchain.com/docs/concepts/prompt_templates>

---

**Commit**: `1a3044b`
**Status**: ✅ Complete and Verified
