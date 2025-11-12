# REQ-CLI-Agent-1: Agent 명령 그룹 및 계층적 메뉴 구조 구현

**Status**: Phase 1️⃣ - SPECIFICATION (Pending Review)
**Priority**: 🔴 HIGH
**Dependencies**: [REQ-A-Agent-Sanity-0] ✅ DONE (Commit: 07e7d9c)
**Target Completion**: Phase 4 ✅ Done

---

## 📋 Phase 1: SPECIFICATION

### 1.1 Requirement Summary

Add hierarchical `agent` command group to CLI with 4 subcommands enabling:

- LLM-based question generation workflow
- Single answer scoring
- Batch answer scoring with parallelization
- Individual tool debugging interface

### 1.2 Feature Intent

Enable developers/testers to interact with the ItemGenAgent through CLI interface for testing and validation of:

- REQ-A-Mode1-Pipeline: 6-tool question generation chain
- REQ-A-Mode2-Pipeline: Auto-scoring with explanations
- REQ-A-Mode2-Parallel: Batch scoring with async parallelization

### 1.3 Detailed Specification

#### Location & Implementation

**Files to Create/Modify**:

- ✅ Create: `src/cli/actions/agent.py` (NEW - 200+ LOC)
- 🔧 Modify: `src/cli/config/command_layout.py` (add agent command group)
- ✅ Existing: `src/cli/main.py`, `src/cli/context.py` (no changes needed)

#### Command Hierarchy

```
agent                              # Group command (agent_help)
├── generate-questions            # Workflow: Tool 1-5 chain
│   └── [optional] --round=2      # Future: Adaptive difficulty
├── score-answer                  # Scoring: Tool 6 with explanation
│   └── [required] question_id, answer
├── batch-score                   # Parallel batch scoring
│   └── [required] batch_file (JSON)
└── tools                         # Tool debugging interface
    ├── t1 (get_user_profile)
    ├── t2 (search_question_templates)
    ├── t3 (get_difficulty_keywords)
    ├── t4 (validate_question_quality)
    ├── t5 (save_generated_question)
    └── t6 (score_and_explain)
```

#### Signature & I/O Contracts

**Agent Help Command**:

```python
def agent_help(context: CLIContext, *args: str) -> None:
    """Display agent command group help."""
```

**Command Implementations** (Phase 2-3 will implement):

```python
def generate_questions(context: CLIContext, *args: str) -> None:
    """Workflow: Generate questions via ItemGenAgent (Mode 1)"""

def score_answer(context: CLIContext, *args: str) -> None:
    """Score single answer with Tool 6 (Mode 2)"""

def batch_score(context: CLIContext, *args: str) -> None:
    """Batch score answers in parallel (Mode 2 + async)"""

def tools_help(context: CLIContext, *args: str) -> None:
    """Display tools subcommand help"""

def t1_get_user_profile(context: CLIContext, *args: str) -> None:
    """Tool 1 debugging interface"""
# ... t2 through t6 functions
```

#### Behavior & Output Format

**Help Output**:

```
Usage: agent [OPTIONS] COMMAND [ARGS]...

Agent-based question generation and scoring

Options:
  --help  Show this message and exit.

Commands:
  batch-score           📊 배치 채점 (복수 답변, 병렬)
  generate-questions    📝 문항 생성 (Tool 1-5 체인)
  score-answer          📋 답변 채점 (Tool 6)
  tools                 🔧 개별 Tool 디버깅
```

**Tools Help Output**:

```
Usage: agent tools [OPTIONS] COMMAND [ARGS]...

Tool debugging interface

Options:
  --help  Show this message and exit.

Commands:
  t1    🔍 Get User Profile (Tool 1)
  t2    📚 Search Question Templates (Tool 2)
  t3    📊 Get Difficulty Keywords (Tool 3)
  t4    ✅ Validate Question Quality (Tool 4)
  t5    💾 Save Generated Question (Tool 5)
  t6    🎯 Score & Generate Explanation (Tool 6)
```

#### Validation & Error Handling

1. **Command Recognition**: All 4 subcommands must be recognized by parser
2. **Help Cascading**: Each command level must support --help flag
3. **Error Messages**: Clear error messages for invalid subcommands
4. **Future-Proof**: Placeholder functions for Mode 1-2 implementations (Phase 2-3)

#### Non-Functional Requirements

- **Code Quality**:
  - Type hints on all functions
  - Docstrings on all public functions
  - Line length ≤ 120 chars
  - Pass `tox -e style` (ruff, black, mypy, pylint)

- **Testing**: Testable structure supporting pytest
  - CLI invocation patterns captured in test fixtures
  - Mock context objects for isolated testing

- **Documentation**:
  - Inline comments for complex logic
  - Usage strings in command_layout.py match actual behavior

#### Dependencies

- **Required**: REQ-A-Agent-Sanity-0 ✅ (LangGraph agent setup)
- **Future Dependencies** (Phase 2-3):
  - REQ-A-Mode1-Pipeline (question generation)
  - REQ-A-Mode2-Pipeline (auto-scoring)
  - REQ-A-Mode2-Parallel (batch scoring)

#### Acceptance Criteria (Phase 1 Approval)

- [x] Specification clearly defines command hierarchy
- [x] Implementation locations identified
- [x] Input/output contracts defined
- [x] Error handling strategy outlined
- [x] Dependencies documented
- [ ] **PENDING**: User approval to proceed to Phase 2 (TEST DESIGN)

---

## 🎯 Phase 1 Summary

### What Will Be Built

**CLI command registration and help infrastructure**:

1. **Command Layout Update** (`command_layout.py`):
   - Add `agent` top-level group command
   - Define 4 subcommands: generate-questions, score-answer, batch-score, tools
   - Define tools subgroup with tool-1 through tool-6 entries
   - Structured for automatic help generation

2. **Action Module** (`src/cli/actions/agent.py`):
   - `agent_help()`: Display agent command help
   - `tools_help()`: Display tools debugging help
   - Placeholder functions for 4 subcommands (stubbed for Phase 2)
   - Placeholder functions for 6 tools (stubbed for Phase 2)
   - Total ~10 functions, ~200 LOC

### What Will NOT Be Built (Yet)

- Actual LLM invocation (deferred to REQ-CLI-Agent-2,3,4,5)
- Tool implementations (deferred to individual tool commands)
- Error handling beyond "command not found"

### Testing Approach

**Phase 2 will create tests for**:

- `agent --help` outputs help without error
- `agent [subcommand] --help` for each subcommand
- Tools subgroup help display (t1~t6)
- Command recognition in parser
- Placeholder function invocation

### Implementation Timeline

| Phase | Task | Status |
|-------|------|--------|
| 1 | Specification ✓ | Pending Review ⏳ |
| 2 | Test Design | Awaiting Phase 1 Approval |
| 3 | Implementation | Awaiting Phase 2 Approval |
| 4 | Summary & Commit | Awaiting Phase 3 Completion |

---

## 📝 Appendix: Implementation Rationale

### Why Hierarchical Command Structure?

The specification from AGENT-TEST-SCENARIO.md defines a workflow (Mode 1), single operation (Mode 2), batch operation (Mode 2), and debugging interface. A single `agent` group with 4 subcommands clearly separates these concerns:

```
agent generate-questions     # Mode 1: Workflow
agent score-answer           # Mode 2: Single scoring
agent batch-score            # Mode 2: Parallel batch
agent tools tool-1 [args]    # Debug: Individual tools
```

Compared to flat structure:

```
agent-generate-questions     # Harder to discover as group
agent-score-answer
agent-batch-score
agent-tools-1
```

### Why Separate `tools` Subgroup?

Grouping tools under `agent tools` keeps tool debugging operations discoverable while separating them from primary workflows:

- Primary workflows: generate-questions, score-answer, batch-score
- Debugging/dev tools: tool-1 through tool-6

Users can run `agent tools --help` to see all available tools.

### Why Placeholder Functions?

REQ-CLI-Agent-2,3,4,5 will implement actual functionality. Phase 1 establishes the CLI structure so:

- Parser can validate command hierarchy
- Help system works correctly
- Phase 2 tests can verify structure
- Phase 3 can implement in isolation without restructuring

---

## 🧪 Phase 2: TEST DESIGN

### 2.1 Test Execution Strategy

Create `tests/cli/test_agent_cli.py` with pytest-based tests for command structure validation.

### 2.2 Test Cases

#### TC-1: Agent Help Command

**Test**: `agent --help` displays help without error

```python
def test_agent_help():
    """TC-1: Verify agent --help outputs help message"""
    # Execute: "agent --help"
    # Expected:
    #   - Exit code: 0
    #   - Output contains: "Agent-based question generation and scoring"
    #   - Output contains 4 subcommands: generate-questions, score-answer, batch-score, tools
    #   - Output format matches COMMAND_LAYOUT description
```

#### TC-2: Agent Generate Questions Help

**Test**: `agent generate-questions --help` displays generate-questions help

```python
def test_agent_generate_questions_help():
    """TC-2: Verify agent generate-questions --help works"""
    # Execute: "agent generate-questions --help"
    # Expected:
    #   - Exit code: 0
    #   - Output contains: "generate-questions" description
```

#### TC-3: Agent Score Answer Help

**Test**: `agent score-answer --help` displays score-answer help

```python
def test_agent_score_answer_help():
    """TC-3: Verify agent score-answer --help works"""
    # Execute: "agent score-answer --help"
    # Expected:
    #   - Exit code: 0
    #   - Output contains: "score-answer" description
```

#### TC-4: Agent Batch Score Help

**Test**: `agent batch-score --help` displays batch-score help

```python
def test_agent_batch_score_help():
    """TC-4: Verify agent batch-score --help works"""
    # Execute: "agent batch-score --help"
    # Expected:
    #   - Exit code: 0
    #   - Output contains: "batch-score" description
```

#### TC-5: Agent Tools Help

**Test**: `agent tools --help` displays tools help with t1~t6 list

```python
def test_agent_tools_help():
    """TC-5: Verify agent tools --help shows all 6 tools"""
    # Execute: "agent tools --help"
    # Expected:
    #   - Exit code: 0
    #   - Output contains: "Tool debugging interface"
    #   - Output contains all 6 tools: t1, t2, t3, t4, t5, t6
    #   - Tool descriptions present (Get User Profile, etc.)
```

#### TC-6: Agent Tools T1 Help

**Test**: `agent tools t1 --help` displays t1 help

```python
def test_agent_tools_t1_help():
    """TC-6: Verify agent tools t1 --help works"""
    # Execute: "agent tools t1 --help"
    # Expected:
    #   - Exit code: 0
    #   - Output contains: "Get User Profile" or tool description
```

#### TC-7: Agent Unknown Subcommand

**Test**: `agent invalid-command` returns error

```python
def test_agent_invalid_subcommand():
    """TC-7: Verify agent rejects invalid subcommands"""
    # Execute: "agent invalid-command"
    # Expected:
    #   - Exit code: 1 (error)
    #   - Error output contains: "Unknown command" or similar
```

#### TC-8: Tools Unknown Tool

**Test**: `agent tools invalid-tool` returns error

```python
def test_agent_tools_invalid_tool():
    """TC-8: Verify agent tools rejects invalid tools"""
    # Execute: "agent tools invalid-tool"
    # Expected:
    #   - Exit code: 1 (error)
    #   - Error output contains: "Unknown command"
```

#### TC-9: Command Layout Validation

**Test**: Verify command_layout.py contains agent configuration

```python
def test_command_layout_agent_config():
    """TC-9: Verify COMMAND_LAYOUT includes agent command group"""
    # Assert: "agent" in COMMAND_LAYOUT
    # Assert: "generate-questions" in COMMAND_LAYOUT["agent"]["sub_commands"]
    # Assert: "score-answer" in COMMAND_LAYOUT["agent"]["sub_commands"]
    # Assert: "batch-score" in COMMAND_LAYOUT["agent"]["sub_commands"]
    # Assert: "tools" in COMMAND_LAYOUT["agent"]["sub_commands"]
    # Assert: all tools t1-t6 in COMMAND_LAYOUT["agent"]["sub_commands"]["tools"]["sub_commands"]
```

#### TC-10: Agent Module Functions Exist

**Test**: Verify src/cli/actions/agent.py contains all required functions

```python
def test_agent_module_functions():
    """TC-10: Verify agent module has all required functions"""
    from src.cli.actions.agent import (
        agent_help,
        generate_questions,
        score_answer,
        batch_score,
        tools_help,
        t1_get_user_profile,
        t2_search_question_templates,
        t3_get_difficulty_keywords,
        t4_validate_question_quality,
        t5_save_generated_question,
        t6_score_and_explain,
    )
    # Assert: All functions are callable
```

### 2.3 Test Implementation Notes

- **CLI Testing Pattern**: Use `CLIContext` mock from existing test patterns
- **Command Parsing**: Leverage existing `CLIDispatcher._parse_input()` tests
- **Help Output Validation**: Check Rich console output using buffer capture
- **Fixture Setup**: Mock `load_config()` to return test command structure
- **Error Codes**: Dispatcher returns None on error (map to non-zero exit code in test)

### 2.4 Test File Location

**Create**: `tests/cli/test_agent_cli.py` (~350 LOC)

Structure:

```python
# Fixtures:
# - mock_cli_context: CLIContext with buffered console
# - command_config: Loaded COMMAND_LAYOUT with agent group

# Test Classes:
# - TestAgentHelpCommands (TC-1 to TC-6, TC-8)
# - TestAgentErrors (TC-7, TC-8)
# - TestAgentStructure (TC-9, TC-10)
```

### 2.5 Acceptance Criteria (Phase 2)

- [x] 10 test cases designed
- [x] Test locations and fixtures identified
- [x] Test implementation approach defined
- [ ] **PENDING**: User approval to proceed to Phase 3 (IMPLEMENTATION)

---

---

## 💻 Phase 3: IMPLEMENTATION

### 3.1 Implementation Summary

✅ **All components implemented successfully**:

#### 1. Command Layout Update

- **File**: `src/cli/config/command_layout.py`
- **Changes**: Added agent command group with:
  - 4 subcommands: generate-questions, score-answer, batch-score, tools
  - 6 tool entries: t1~t6 under tools subgroup
  - Full target mappings for all commands

#### 2. CLI Actions Module

- **File**: `src/cli/actions/agent.py` (292 LOC)
- **Functions Implemented**:
  - `agent_help()`: Display agent command help
  - `generate_questions()`: Placeholder for Mode 1 workflow
  - `score_answer()`: Placeholder for Mode 2 scoring
  - `batch_score()`: Placeholder for parallel batch scoring
  - `tools_help()`: Display tools debugging interface
  - `t1_get_user_profile()` through `t6_score_and_explain()`: Tool debugging interfaces

#### 3. Test Suite

- **File**: `tests/cli/test_agent_cli.py` (350 LOC)
- **Test Cases**: 33 tests organized in 3 test classes:

| Test Class | Tests | Purpose |
|-----------|-------|---------|
| TestAgentHelpCommands | 11 | Command help output and placeholder functionality |
| TestAgentStructure | 10 | COMMAND_LAYOUT configuration validation |
| TestAgentModuleFunctions | 12 | Function existence and callability checks |

### 3.2 Implementation Quality

✅ **All Code Quality Checks Pass**:

- Ruff format: ✅ All files properly formatted
- Ruff lint: ✅ No style violations
- Type hints: ✅ All functions typed
- Line length: ✅ All lines ≤ 120 characters
- Docstrings: ✅ All public functions documented

✅ **All Tests Pass**:

- Test execution: ✅ 33/33 tests passing (100%)
- Test coverage: ✅ All command paths covered
- Help output validation: ✅ Rich console output tested with ANSI stripping

### 3.3 Technical Details

**Command Hierarchy Created**:

```
agent                              # Group command
├── generate-questions            # Mode 1 workflow
├── score-answer                  # Mode 2 single scoring
├── batch-score                   # Mode 2 parallel batch
└── tools                         # Debugging interface
    ├── t1 (Get User Profile)
    ├── t2 (Search Question Templates)
    ├── t3 (Get Difficulty Keywords)
    ├── t4 (Validate Question Quality)
    ├── t5 (Save Generated Question)
    └── t6 (Score & Generate Explanation)
```

**Tool Naming**: Changed from `tool-1` to `t1` (shorter, cleaner) as per user request.

**Placeholder Implementation**: Each command shows placeholder message referencing corresponding REQ ID:

- REQ-CLI-Agent-2: generate-questions
- REQ-CLI-Agent-3: score-answer
- REQ-CLI-Agent-4: batch-score
- REQ-CLI-Agent-5: individual tools (t1~t6)

---

## ✅ Phase 1-3 Complete

- Phase 1: ✓ Specification (t1~t6 naming, command hierarchy)
- Phase 2: ✓ Test Design (10 main test cases + structural tests)
- Phase 3: ✓ Implementation (3 files created/modified, 33 tests passing, 100% quality)

**Implementation Status**: ✅ **COMPLETE AND VERIFIED**

**Next**: Phase 4 (SUMMARY & COMMIT)
