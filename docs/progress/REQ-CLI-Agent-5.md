# REQ-CLI-Agent-5: agent tools 명령 (Tool 1-6 디버깅 인터페이스)

**Status**: Phase 4️⃣ - COMPLETE ✅
**Git Commit**: `2535036`
**Priority**: 🟡 MEDIUM
**Dependencies**: [REQ-CLI-Agent-1] ✅ DONE, [REQ-A-Mode1-Tool1~5] ✅ DONE, [REQ-A-Mode2-Tool6] ✅ DONE
**Target Completion**: Phase 4 (Design phase)

---

## 📋 Phase 1: SPECIFICATION

### 1.1 Requirement Summary

Implement `agent tools` command suite that:

- Provides direct CLI access to invoke individual Tools 1-6
- Enables debugging and testing of tool functionality
- Supports tool-specific parameters for each tool
- Returns formatted output (Rich tables/panels) for easy interpretation
- Includes comprehensive help for each tool

### 1.2 Feature Intent

Enable developers and testers to:

- Debug individual tool behavior in isolation
- Test tool parameters without running full pipeline
- Validate tool outputs during development
- Quickly verify tool functionality changes
- Support both Mode 1 (Tools 1-5) and Mode 2 (Tool 6) tools

### 1.3 Detailed Specification

#### Location & Implementation

**Files to Create/Modify**:

- ✅ Modify: `src/cli/actions/agent.py` (replace 6 placeholders: t1-t6 functions)
- ✅ New: Comprehensive test suite in `tests/cli/test_agent_tools.py`

#### Command Signatures

```bash
agent tools [SUBCOMMAND] [OPTIONS]

Subcommands:
  t1  Get User Profile
  t2  Search Question Templates
  t3  Get Difficulty Keywords
  t4  Validate Question Quality
  t5  Save Generated Question
  t6  Score & Generate Explanation
```

#### Tool 1: Get User Profile

**Command**:

```bash
agent tools t1 --user-id USER_ID [--help]
```

**Options**:

- `--user-id TEXT` - User ID (required)
- `--help` - Show help

**Input**:

- user_id: string (required)

**Success Output**:

```
🔍 Tool 1: Get User Profile
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User: user_123
Skill Level: 7/10
Experience (Years): 5
Interests:
  - Python
  - Machine Learning
  - Data Science
Job Role: Software Engineer
Category Expertise:
  - Backend Development (8/10)
  - Data Analysis (6/10)
```

**Error Cases**:

- Missing --user-id
- User not found
- API/database error

---

#### Tool 2: Search Question Templates

**Command**:

```bash
agent tools t2 --interests TEXT --difficulty INT [--category TEXT] [--help]
```

**Options**:

- `--interests TEXT` - Comma-separated interests (required)
- `--difficulty INT` - Difficulty level 1-10 (required)
- `--category TEXT` - Question category (optional)
- `--help` - Show help

**Input**:

- interests: list[str] (required, comma-separated)
- difficulty: int (1-10, required)
- category: str (optional)

**Success Output**:

```
📚 Tool 2: Search Question Templates
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Templates Found: 5
Interests: Python, Data Science
Difficulty: 7 (±1.5 range: 5.5-8.5)

┌─────────┬───────────────────────┬────────────┬──────────┐
│ ID      │ Stem                  │ Type       │ Difficulty│
├─────────┼───────────────────────┼────────────┼──────────┤
│ tmpl_01 │ What is list comprehension? │ MC | 6.5 |
│ tmpl_02 │ Explain decorators    │ SA | 7.0 |
│ tmpl_03 │ Python async/await    │ MC | 7.5 |
│ tmpl_04 │ Describe generators   │ SA | 6.8 |
│ tmpl_05 │ GIL in Python?        │ MC | 7.2 |
└─────────┴───────────────────────┴────────────┴──────────┘
```

**Error Cases**:

- Missing required parameters
- Invalid difficulty (not 1-10)
- No templates found
- API error

---

#### Tool 3: Get Difficulty Keywords

**Command**:

```bash
agent tools t3 --difficulty INT [--category TEXT] [--help]
```

**Options**:

- `--difficulty INT` - Difficulty level 1-10 (required)
- `--category TEXT` - Question category (optional)
- `--help` - Show help

**Input**:

- difficulty: int (1-10, required)
- category: str (optional)

**Success Output**:

```
📊 Tool 3: Get Difficulty Keywords
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Difficulty: 7/10 (Intermediate-Advanced)
Cache Hit: Yes (TTL: 59m 45s remaining)

Keywords (24 total):
  • Asynchronous programming
  • Context managers
  • Decorators
  • Descriptors
  • Exception handling (advanced)
  • Generator expressions
  • Metaclasses
  • Module system
  • Multithreading
  • Type hints
  [... 14 more]

Categories:
  • Backend (12 keywords)
  • Data Science (8 keywords)
  • DevOps (4 keywords)
```

**Error Cases**:

- Missing difficulty
- Invalid difficulty (not 1-10)
- Cache error (fallback to defaults)

---

#### Tool 4: Validate Question Quality

**Command**:

```bash
agent tools t4 --question TEXT --type TYPE [--help]
```

**Options**:

- `--question TEXT` - Question stem (required)
- `--type TEXT` - Question type: multiple_choice, short_answer, true_false (required)
- `--help` - Show help

**Input**:

- question_stem: str (required)
- question_type: str (required, enum)

**Success Output** (Pass):

```
✅ Tool 4: Validate Question Quality
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Question: "Explain the difference between list and tuple in Python"
Type: short_answer
Status: ✅ PASS

Validation Score: 0.92 / 1.0
  • Clarity: 0.95 ✅
  • Specificity: 0.90 ✅
  • Grammar: 0.98 ✅
  • Feasibility: 0.88 ✅

Decision: ACCEPT
Feedback: Well-structured question with clear intent
Estimated Time: 3-5 minutes
```

**Success Output** (Revise):

```
⚠️  Tool 4: Validate Question Quality
Status: REVISE (Score: 0.75 / 1.0)

Feedback:
  • Question is too open-ended
  • Add constraints for scope
  • Consider adding context

Suggested Revision:
  "Explain the key differences between list and tuple in Python,
   focusing on mutability and performance implications"
```

**Error Cases**:

- Missing required parameters
- Invalid question type
- Invalid question (empty/null)

---

#### Tool 5: Save Generated Question

**Command**:

```bash
agent tools t5 --stem TEXT --type TYPE --difficulty INT --categories TEXT --round-id TEXT [--help]
```

**Options**:

- `--stem TEXT` - Question stem (required)
- `--type TEXT` - Question type (required)
- `--difficulty INT` - Difficulty 1-10 (required)
- `--categories TEXT` - Comma-separated categories (required)
- `--round-id TEXT` - Round ID (required)
- `--help` - Show help

**Input**:

- stem: str (required)
- question_type: str (required, enum)
- difficulty: int (1-10, required)
- categories: list[str] (required, comma-separated)
- round_id: str (required)

**Success Output**:

```
💾 Tool 5: Save Generated Question
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Question Saved Successfully

Item ID: item_abc123def456
Round ID: round_001_python
Status: SAVED

Question Details:
  • Type: multiple_choice
  • Difficulty: 7/10
  • Categories: [Python, Functions, Intermediate]
  • Stem: "Which keyword creates an anonymous function in Python?"

Database Record:
  • Saved at: 2025-11-12T14:30:45Z
  • Table: test_questions
  • Row ID: 12847
```

**Error Cases**:

- Missing required parameters
- Invalid difficulty
- Invalid question type
- Database write error
- Duplicate question

---

#### Tool 6: Score & Generate Explanation

**Command**:

```bash
agent tools t6 --question-id ID --question TEXT --answer-type TYPE \
             --user-answer TEXT --correct-answer TEXT [--help]
```

**Options**:

- `--question-id TEXT` - Question ID (required)
- `--question TEXT` - Question stem (required)
- `--answer-type TEXT` - Question type (required)
- `--user-answer TEXT` - User's answer (required)
- `--correct-answer TEXT` - Correct answer (required)
- `--help` - Show help

**Input**:

- item_id: str (question ID, required)
- question_stem: str (required)
- question_type: str (required, enum)
- user_answer: str (required)
- correct_answer: str (required)

**Success Output** (Correct):

```
🎯 Tool 6: Score & Generate Explanation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Question: "What is a decorator in Python?"
User Answer: "A decorator is a function that modifies another function"
Score: ✅ 100/100 (CORRECT)

Explanation:
Excellent answer! You've correctly identified that decorators are functions
that modify or enhance other functions. This is a fundamental concept in
Python that enables cleaner, more readable code through function composition.

Key Points Matched:
  ✅ Functions that modify functions
  ✅ Core concept understanding
  ✅ Relevant example understanding

Confidence: 95% (Very High)
```

**Success Output** (Partial):

```
⚠️  Tool 6: Score & Generate Explanation
Status: PARTIAL (Score: 65/100)

Explanation:
Your answer captures the main idea but misses some important nuances.
Decorators not only modify functions but also preserve their metadata and
can be stacked/chained for multiple modifications.

Missing Points:
  • Metadata preservation (@wraps)
  • Decorator chaining
  • Use with classes

Confidence: 78% (High)
```

**Error Cases**:

- Missing required parameters
- Invalid question type
- LLM API error
- Timeout (15 seconds)

---

#### Validation & Requirements

1. **Parameter Validation**:
   - Each tool validates required parameters
   - Type checking (str, int, list)
   - Range validation (difficulty 1-10)
   - Enum validation (question types)

2. **Error Handling**:
   - User-friendly error messages
   - Suggestion for fixes
   - Graceful fallback for cached data
   - Proper exit codes

3. **Output Formatting**:
   - Rich panels and tables
   - Color-coded status (✅ ❌ ⚠️)
   - Indented hierarchical data
   - Emoji indicators

4. **Performance**:
   - Timeout per tool (2-15 seconds)
   - Cache hits (Tool 3 only)
   - Async execution where applicable

#### Dependencies

- **Internal**: ItemGenAgent, FastMCP Tool implementations
- **External**: LangChain, Rich, Google Gemini API

---

## 🧪 Phase 2: TEST DESIGN

### 2.1 Test Execution Strategy

Create `tests/cli/test_agent_tools.py` with:

- Help and error handling tests (9 tests: 1 help + 8 error tests)
- Success scenario tests for each tool (6 tests)
- Mock tool responses and edge cases
- Output formatting validation

### 2.2 Test Cases

#### Tool 1 Tests (3 total: 1 help + 1 success + 1 error)

**TC-1**: `agent tools t1 --help`

- Verify help displays usage and options

**TC-2**: `agent tools t1 --user-id user_123` (success)

- Mock ItemGenAgent.get_user_profile()
- Verify output contains user data

**TC-3**: `agent tools t1` (missing --user-id)

- Verify error message and usage hint

---

#### Tool 2 Tests (3 total)

**TC-4**: `agent tools t2 --help`

- Verify help displays usage

**TC-5**: `agent tools t2 --interests Python,Data --difficulty 7` (success)

- Mock search_question_templates()
- Verify table output with templates

**TC-6**: `agent tools t2 --difficulty 15` (invalid difficulty)

- Verify error for out-of-range difficulty

---

#### Tool 3 Tests (3 total)

**TC-7**: `agent tools t3 --help`

- Verify help

**TC-8**: `agent tools t3 --difficulty 7` (success)

- Mock get_difficulty_keywords()
- Verify keywords list output

**TC-9**: `agent tools t3 --difficulty abc` (invalid type)

- Verify error for non-integer difficulty

---

#### Tool 4 Tests (3 total)

**TC-10**: `agent tools t4 --help`

- Verify help

**TC-11**: `agent tools t4 --question "What is X?" --type multiple_choice` (success)

- Mock validate_question_quality()
- Verify scoring display

**TC-12**: `agent tools t4 --question "What?" --type invalid_type` (invalid type)

- Verify error for invalid question type

---

#### Tool 5 Tests (3 total)

**TC-13**: `agent tools t5 --help`

- Verify help

**TC-14**: `agent tools t5 --stem "Q?" --type mc --difficulty 5 --categories Python --round-id r1` (success)

- Mock save_generated_question()
- Verify success message with item ID

**TC-15**: `agent tools t5 --stem "Q?" --difficulty 15` (invalid difficulty)

- Verify error

---

#### Tool 6 Tests (3 total)

**TC-16**: `agent tools t6 --help`

- Verify help

**TC-17**: `agent tools t6 --question-id q1 --question "Q?" --answer-type mc --user-answer "A" --correct-answer "A"` (success)

- Mock score_and_explain()
- Verify scoring and explanation

**TC-18**: `agent tools t6 --question-id q1 --question "Q?"` (missing answers)

- Verify error for missing parameters

---

#### Additional Tests (3 total)

**TC-19**: Main `agent tools --help`

- Verify tools menu displays all 6 tools

**TC-20**: `agent tools invalid_tool`

- Verify error for invalid subcommand

**TC-21**: Agent initialization failure

- Mock ItemGenAgent() to raise exception
- Verify error handling

---

### 2.3 Test Implementation Structure

**File**: `tests/cli/test_agent_tools.py` (~600 LOC)

**Test Classes**:

- `TestToolsHelp` (2 tests: main help + individual help)
- `TestTool1GetUserProfile` (3 tests)
- `TestTool2SearchTemplates` (3 tests)
- `TestTool3GetKeywords` (3 tests)
- `TestTool4ValidateQuality` (3 tests)
- `TestTool5SaveQuestion` (3 tests)
- `TestTool6ScoreAnswer` (3 tests)
- `TestToolsErrors` (2 tests: invalid subcommand, agent init failure)

**Mocking Strategy**:

- Mock `src.cli.actions.agent.ItemGenAgent` constructor
- Mock each tool method: get_user_profile(), search_question_templates(), etc.
- Return realistic mock responses for each tool
- Use AsyncMock for async methods

### 2.4 Acceptance Criteria (Phase 2) ✅ COMPLETE

- [x] 21 test cases designed with clear assertions
- [x] Mock strategy defined for all tools
- [x] Test file location and class structure identified
- [x] Fixture setup documented
- [x] **All 21 tests passing** (2.48s execution)

**Phase 2 Status**: ✅ COMPLETE

Test Classes:

- TestToolsHelp (1 test)
- TestTool1GetUserProfile (3 tests)
- TestTool2SearchTemplates (3 tests)
- TestTool3GetKeywords (3 tests)
- TestTool4ValidateQuality (3 tests)
- TestTool5SaveQuestion (3 tests)
- TestTool6ScoreAnswer (3 tests)
- TestToolsErrors (2 tests)

Total: 21 tests (100% passing)

---

## 💻 Phase 3: IMPLEMENTATION ✅ COMPLETE

### 3.1 Implementation Summary

Implemented all 6 tool functions with complete functionality:

1. **src/cli/actions/agent.py**:
   - Replaced `t1_get_user_profile()` (52 lines) with full implementation
   - Replaced `t2_search_question_templates()` (58 lines) with full implementation
   - Replaced `t3_get_difficulty_keywords()` (56 lines) with full implementation
   - Replaced `t4_validate_question_quality()` (52 lines) with full implementation
   - Replaced `t5_save_generated_question()` (68 lines) with full implementation
   - Replaced `t6_score_and_explain()` (72 lines) with full implementation
   - Added 6 help functions (_print_t1_help through_print_t6_help, ~52 lines total)

2. **tests/cli/test_agent_tools.py** ✅ ALL 21 TESTS PASSING:
   - TestToolsHelp (1 test)
   - TestTool1GetUserProfile (3 tests)
   - TestTool2SearchTemplates (3 tests)
   - TestTool3GetKeywords (3 tests)
   - TestTool4ValidateQuality (3 tests)
   - TestTool5SaveQuestion (3 tests)
   - TestTool6ScoreAnswer (3 tests)
   - TestToolsErrors (2 tests)

### 3.2 Key Implementation Details

**Argument Parsing Pattern**:

```python
i = 0
while i < len(args):
    arg = args[i]
    if arg == "--option" and i + 1 < len(args):
        value = args[i + 1]
        i += 2
    elif arg == "--help":
        _print_help(context)
        return
    else:
        i += 1
```

**Parameter Validation**:

- Type checking (str, int conversions)
- Range validation (difficulty 1-10)
- Enum validation (question types)
- Required field checking with helpful error messages

**Agent Initialization**:

- Try-except wrapping for graceful error handling
- asyncio.run() for executing async agent methods from sync context
- Proper error messaging for missing GEMINI_API_KEY

**Output Formatting**:

- Rich console panels with emoji headers (📚 🔍 ✅ 💾 🎯)
- Divider lines (━━━) for visual separation
- Hasattr() checks for optional response fields
- Color-coded error messages ([bold red]❌ Error:[/bold red])

**Test Assertions**:

- Uses strip_ansi() helper to remove ANSI color codes from output
- Validates actual implementation output instead of placeholder messages
- Checks for expected tool names, titles, and error messages

### 3.3 Code Quality

**Docstrings**: All functions properly documented per PEP 257
**Type Hints**: All parameters and return types annotated
**Error Handling**: Comprehensive error cases with user-friendly messages
**Testing**: 100% test passing rate (21/21 tests)

---

## 📊 Implementation Roadmap

| Phase | Task | Status |
|-------|------|--------|
| 1 | Specification ✓ | ✅ Complete |
| 2 | Test Design ✓ | ✅ Complete (21/21 passing) |
| 3 | Implementation ✓ | ✅ Complete (21/21 tests passing) |
| 4 | Summary & Commit | **In Progress** |

---

## ✅ Phase 1-3 Complete

- Phase 1: ✓ Comprehensive specification for all 6 tools with parameters and outputs
- Phase 2: ✓ 21 detailed test cases with full mocking strategy - **ALL 21 TESTS PASSING** ✅
- Phase 3: ✓ Full implementation of all 6 tool functions - **ALL 21 TESTS PASSING** ✅

**Ready for Phase 4 (Summary & Commit).**
