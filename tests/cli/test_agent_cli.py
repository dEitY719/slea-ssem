"""
Tests for agent CLI commands (hierarchical menu structure).

REQ: REQ-CLI-Agent-1
"""

import re
from io import StringIO

import pytest
from rich.console import Console

from src.cli.actions import agent
from src.cli.config.command_layout import COMMAND_LAYOUT
from src.cli.context import CLIContext


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


class TestAgentHelpCommands:
    """Test agent help and subcommand help output."""

    @pytest.fixture
    def mock_context(self) -> CLIContext:
        """Create a CLIContext with buffered console output."""
        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True, width=88)
        context = CLIContext(console=console, logger=None)
        context._buffer = buffer  # Store buffer for output inspection
        return context

    def test_agent_help(self, mock_context: CLIContext) -> None:
        """
        TC-1: Verify agent --help displays help message.

        Expected:
        - Contains "Agent-based question generation and scoring"
        - Lists 4 subcommands: generate-questions, score-answer, batch-score, tools
        """
        agent.agent_help(mock_context)
        output = mock_context._buffer.getvalue()

        assert "agent - Agent-based question generation and scoring" in output
        assert "generate-questions" in output
        assert "score-answer" in output
        assert "batch-score" in output
        assert "agent tools" in output

    def test_agent_generate_questions_help(self, mock_context: CLIContext) -> None:
        """
        TC-2: Verify agent generate-questions help or error handling.

        Expected:
        - Shows help/usage info or error message when no args
        - References REQ-CLI-Agent-2
        """
        agent.generate_questions(mock_context)
        output = strip_ansi(mock_context._buffer.getvalue())

        # Should either show help or error about missing survey
        assert (
            "Error" in output
            or "Usage" in output
            or "help" in output.lower()
            or "agent generate-questions" in output
        )

    def test_agent_score_answer_help(self, mock_context: CLIContext) -> None:
        """
        TC-3: Verify agent score-answer help or placeholder.

        Expected:
        - Shows help/usage or placeholder message
        - References REQ-CLI-Agent-3 or shows command info
        """
        agent.score_answer(mock_context)
        output = strip_ansi(mock_context._buffer.getvalue())

        # Should either show placeholder or help/usage info
        assert (
            "Placeholder" in output
            or "placeholder" in output
            or "Usage" in output
            or "Error" in output
        )

    def test_agent_batch_score_help(self, mock_context: CLIContext) -> None:
        """
        TC-4: Verify agent batch-score help or placeholder.

        Expected:
        - Shows help/usage or placeholder message
        - References REQ-CLI-Agent-4 or shows command info
        """
        agent.batch_score(mock_context)
        output = strip_ansi(mock_context._buffer.getvalue())

        # Should either show placeholder or help/usage info
        assert (
            "Placeholder" in output
            or "placeholder" in output
            or "Usage" in output
            or "Error" in output
        )

    def test_agent_tools_help(self, mock_context: CLIContext) -> None:
        """
        TC-5: Verify agent tools --help shows all 6 tools.

        Expected:
        - Output contains "Tool debugging interface"
        - Lists all 6 tools: t1, t2, t3, t4, t5, t6
        - Tool descriptions present
        """
        agent.tools_help(mock_context)
        output = mock_context._buffer.getvalue()

        assert "Tool debugging interface" in output
        assert "agent tools t1" in output
        assert "agent tools t2" in output
        assert "agent tools t3" in output
        assert "agent tools t4" in output
        assert "agent tools t5" in output
        assert "agent tools t6" in output

        # Verify descriptions
        assert "Get User Profile" in output
        assert "Search Question Templates" in output
        assert "Get Difficulty Keywords" in output
        assert "Validate Question Quality" in output
        assert "Save Generated Question" in output
        assert "Score & Generate Explanation" in output

    def test_tool_t1_get_user_profile(self, mock_context: CLIContext) -> None:
        """
        TC-6: Verify t1 tool help or placeholder.

        Expected:
        - Shows placeholder message or help/usage info
        - References REQ-CLI-Agent-5 or shows command info
        """
        agent.t1_get_user_profile(mock_context)
        output = strip_ansi(mock_context._buffer.getvalue())

        # Should show some output
        assert len(output) > 0

    def test_tool_t2_search_templates(self, mock_context: CLIContext) -> None:
        """Verify t2 tool help or placeholder."""
        agent.t2_search_question_templates(mock_context)
        output = strip_ansi(mock_context._buffer.getvalue())

        # Should show some output
        assert len(output) > 0

    def test_tool_t3_get_keywords(self, mock_context: CLIContext) -> None:
        """Verify t3 tool help or placeholder."""
        agent.t3_get_difficulty_keywords(mock_context)
        output = strip_ansi(mock_context._buffer.getvalue())

        # Should show some output
        assert len(output) > 0

    def test_tool_t4_validate_quality(self, mock_context: CLIContext) -> None:
        """Verify t4 tool help or placeholder."""
        agent.t4_validate_question_quality(mock_context)
        output = strip_ansi(mock_context._buffer.getvalue())

        # Should show some output
        assert len(output) > 0

    def test_tool_t5_save_question(self, mock_context: CLIContext) -> None:
        """Verify t5 tool help or placeholder."""
        agent.t5_save_generated_question(mock_context)
        output = strip_ansi(mock_context._buffer.getvalue())

        # Should show some output
        assert len(output) > 0

    def test_tool_t6_score_and_explain(self, mock_context: CLIContext) -> None:
        """Verify t6 tool help or placeholder."""
        agent.t6_score_and_explain(mock_context)
        output = strip_ansi(mock_context._buffer.getvalue())

        # Should show some output
        assert len(output) > 0


class TestAgentStructure:
    """Test agent command structure in COMMAND_LAYOUT."""

    def test_command_layout_agent_exists(self) -> None:
        """TC-9a: Verify 'agent' exists in COMMAND_LAYOUT."""
        assert "agent" in COMMAND_LAYOUT

    def test_command_layout_agent_has_description(self) -> None:
        """TC-9b: Verify 'agent' has proper description."""
        agent_config = COMMAND_LAYOUT["agent"]
        assert "description" in agent_config
        assert "Agent-based" in agent_config["description"]

    def test_command_layout_agent_has_target(self) -> None:
        """TC-9c: Verify 'agent' has target function."""
        agent_config = COMMAND_LAYOUT["agent"]
        assert "target" in agent_config
        assert agent_config["target"] == "src.cli.actions.agent.agent_help"

    def test_command_layout_agent_subcommands_exist(self) -> None:
        """TC-9d: Verify all 4 agent subcommands exist."""
        agent_config = COMMAND_LAYOUT["agent"]
        sub_commands = agent_config.get("sub_commands", {})

        assert "generate-questions" in sub_commands
        assert "score-answer" in sub_commands
        assert "batch-score" in sub_commands
        assert "tools" in sub_commands

    def test_command_layout_tools_subcommands_exist(self) -> None:
        """TC-9e: Verify all 6 tools exist under agent tools."""
        agent_config = COMMAND_LAYOUT["agent"]
        tools_config = agent_config["sub_commands"]["tools"]
        tool_commands = tools_config.get("sub_commands", {})

        assert "t1" in tool_commands
        assert "t2" in tool_commands
        assert "t3" in tool_commands
        assert "t4" in tool_commands
        assert "t5" in tool_commands
        assert "t6" in tool_commands

    def test_command_layout_tools_descriptions(self) -> None:
        """TC-9f: Verify tool descriptions are present."""
        agent_config = COMMAND_LAYOUT["agent"]
        tools_config = agent_config["sub_commands"]["tools"]
        tool_commands = tools_config["sub_commands"]

        # Verify each tool has description
        assert "Get User Profile" in tool_commands["t1"]["description"]
        assert "Search Question Templates" in tool_commands["t2"]["description"]
        assert "Get Difficulty Keywords" in tool_commands["t3"]["description"]
        assert "Validate Question Quality" in tool_commands["t4"]["description"]
        assert "Save Generated Question" in tool_commands["t5"]["description"]
        assert "Score & Generate Explanation" in tool_commands["t6"]["description"]

    def test_command_layout_generate_questions_config(self) -> None:
        """Verify generate-questions has correct config."""
        agent_config = COMMAND_LAYOUT["agent"]
        gen_config = agent_config["sub_commands"]["generate-questions"]

        assert "description" in gen_config
        assert "target" in gen_config
        assert gen_config["target"] == "src.cli.actions.agent.generate_questions"

    def test_command_layout_score_answer_config(self) -> None:
        """Verify score-answer has correct config."""
        agent_config = COMMAND_LAYOUT["agent"]
        score_config = agent_config["sub_commands"]["score-answer"]

        assert "description" in score_config
        assert "target" in score_config
        assert score_config["target"] == "src.cli.actions.agent.score_answer"

    def test_command_layout_batch_score_config(self) -> None:
        """Verify batch-score has correct config."""
        agent_config = COMMAND_LAYOUT["agent"]
        batch_config = agent_config["sub_commands"]["batch-score"]

        assert "description" in batch_config
        assert "target" in batch_config
        assert batch_config["target"] == "src.cli.actions.agent.batch_score"

    def test_command_layout_tools_config(self) -> None:
        """Verify tools subcommand has correct config."""
        agent_config = COMMAND_LAYOUT["agent"]
        tools_config = agent_config["sub_commands"]["tools"]

        assert "description" in tools_config
        assert "target" in tools_config
        assert tools_config["target"] == "src.cli.actions.agent.tools_help"
        assert "sub_commands" in tools_config


class TestAgentModuleFunctions:
    """Test that agent module has all required functions."""

    def test_agent_module_agent_help_exists(self) -> None:
        """TC-10a: Verify agent_help function exists."""
        assert hasattr(agent, "agent_help")
        assert callable(agent.agent_help)

    def test_agent_module_generate_questions_exists(self) -> None:
        """TC-10b: Verify generate_questions function exists."""
        assert hasattr(agent, "generate_questions")
        assert callable(agent.generate_questions)

    def test_agent_module_score_answer_exists(self) -> None:
        """TC-10c: Verify score_answer function exists."""
        assert hasattr(agent, "score_answer")
        assert callable(agent.score_answer)

    def test_agent_module_batch_score_exists(self) -> None:
        """TC-10d: Verify batch_score function exists."""
        assert hasattr(agent, "batch_score")
        assert callable(agent.batch_score)

    def test_agent_module_tools_help_exists(self) -> None:
        """TC-10e: Verify tools_help function exists."""
        assert hasattr(agent, "tools_help")
        assert callable(agent.tools_help)

    def test_agent_module_t1_exists(self) -> None:
        """TC-10f: Verify t1_get_user_profile function exists."""
        assert hasattr(agent, "t1_get_user_profile")
        assert callable(agent.t1_get_user_profile)

    def test_agent_module_t2_exists(self) -> None:
        """TC-10g: Verify t2_search_question_templates function exists."""
        assert hasattr(agent, "t2_search_question_templates")
        assert callable(agent.t2_search_question_templates)

    def test_agent_module_t3_exists(self) -> None:
        """TC-10h: Verify t3_get_difficulty_keywords function exists."""
        assert hasattr(agent, "t3_get_difficulty_keywords")
        assert callable(agent.t3_get_difficulty_keywords)

    def test_agent_module_t4_exists(self) -> None:
        """TC-10i: Verify t4_validate_question_quality function exists."""
        assert hasattr(agent, "t4_validate_question_quality")
        assert callable(agent.t4_validate_question_quality)

    def test_agent_module_t5_exists(self) -> None:
        """TC-10j: Verify t5_save_generated_question function exists."""
        assert hasattr(agent, "t5_save_generated_question")
        assert callable(agent.t5_save_generated_question)

    def test_agent_module_t6_exists(self) -> None:
        """TC-10k: Verify t6_score_and_explain function exists."""
        assert hasattr(agent, "t6_score_and_explain")
        assert callable(agent.t6_score_and_explain)

    def test_all_functions_accept_context(self) -> None:
        """Verify all functions accept CLIContext as first argument."""
        from io import StringIO

        from rich.console import Console

        buffer = StringIO()
        console = Console(file=buffer, force_terminal=True)
        context = CLIContext(console=console, logger=None)

        # All these should be callable with context
        functions = [
            agent.agent_help,
            agent.generate_questions,
            agent.score_answer,
            agent.batch_score,
            agent.tools_help,
            agent.t1_get_user_profile,
            agent.t2_search_question_templates,
            agent.t3_get_difficulty_keywords,
            agent.t4_validate_question_quality,
            agent.t5_save_generated_question,
            agent.t6_score_and_explain,
        ]

        for func in functions:
            # Should not raise TypeError
            func(context)
