"""
Agent-based question generation and scoring CLI actions.

REQ: REQ-CLI-Agent-1, REQ-CLI-Agent-2
"""

import asyncio
import json
import logging

from rich.table import Table

from src.agent.llm_agent import GenerateQuestionsRequest, ItemGenAgent
from src.cli.context import CLIContext

logger = logging.getLogger(__name__)


def agent_help(context: CLIContext, *args: str) -> None:
    """
    Display help for agent command group.

    Shows available subcommands:
    - generate-questions: Question generation workflow (Mode 1)
    - score-answer: Single answer scoring (Mode 2)
    - batch-score: Parallel batch scoring (Mode 2)
    - tools: Individual tool debugging interface

    Args:
        context: CLI context with console and logger.
        *args: Additional arguments (ignored).

    """
    context.console.print()
    context.console.print(
        "[bold cyan]╔════════════════════════════════════════════════════════════════════════════════╗[/bold cyan]"
    )
    context.console.print(
        "[bold cyan]║  agent - Agent-based question generation and scoring                          ║[/bold cyan]"
    )
    context.console.print(
        "[bold cyan]╚════════════════════════════════════════════════════════════════════════════════╝[/bold cyan]"
    )
    context.console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))

    # Add subcommands
    subcommands = [
        ("agent generate-questions", "[dim]📝 문항 생성 (Tool 1-5 체인)[/dim]"),
        ("agent score-answer", "[dim]📋 답변 채점 (Tool 6)[/dim]"),
        ("agent batch-score", "[dim]📊 배치 채점 (복수 답변, 병렬)[/dim]"),
        ("agent tools", "[dim]🔧 개별 Tool 디버깅[/dim]"),
    ]

    for cmd, desc in subcommands:
        table.add_row(cmd, desc)

    context.console.print(table)
    context.console.print()
    context.console.print("[bold yellow]💡 팁:[/bold yellow] 'agent tools --help'로 디버깅 도구 보기")
    context.console.print()


def generate_questions(context: CLIContext, *args: str) -> None:
    """
    Generate high-quality questions using ItemGenAgent (Mode 1).

    Workflow: Calls Tool 1-5 in sequence to:
    1. Get user profile (Tool 1)
    2. Search question templates (Tool 2)
    3. Get difficulty keywords (Tool 3)
    4. Generate and validate questions (Tool 4)
    5. Save validated questions (Tool 5)

    Args:
        context: CLI context with console and logger.
        *args: Parsed arguments (--survey-id, --round, --prev-answers).

    REQ: REQ-CLI-Agent-2

    """
    # Parse arguments
    survey_id = None
    round_idx = 1
    prev_answers_json = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--survey-id" and i + 1 < len(args):
            survey_id = args[i + 1]
            i += 2
        elif arg == "--round" and i + 1 < len(args):
            try:
                round_idx = int(args[i + 1])
                i += 2
            except ValueError:
                context.console.print(f"[bold red]❌ Error:[/bold red] --round must be integer (got: {args[i + 1]})")
                return
        elif arg == "--prev-answers" and i + 1 < len(args):
            prev_answers_json = args[i + 1]
            i += 2
        elif arg == "--help":
            _print_generate_questions_help(context)
            return
        else:
            i += 1

    # Validate required survey-id
    if not survey_id:
        context.console.print("[bold red]❌ Error:[/bold red] --survey-id is required")
        _print_generate_questions_help(context)
        return

    # Validate round
    if round_idx not in (1, 2):
        context.console.print(f"[bold red]❌ Error:[/bold red] --round must be 1 or 2 (got: {round_idx})")
        return

    # Parse prev-answers if provided
    prev_answers = None
    if prev_answers_json:
        if round_idx != 2:
            context.console.print("[bold yellow]⚠️  Warning:[/bold yellow] --prev-answers only used in Round 2")
        try:
            prev_answers = json.loads(prev_answers_json)
            if not isinstance(prev_answers, list):
                context.console.print("[bold red]❌ Error:[/bold red] --prev-answers must be JSON array")
                return
        except json.JSONDecodeError as e:
            context.console.print(f"[bold red]❌ Error:[/bold red] Invalid JSON in --prev-answers: {e}")
            return

    # Initialize agent
    context.console.print("🚀 Initializing Agent... (GEMINI_API_KEY required)")
    try:
        agent = ItemGenAgent()
    except Exception as e:
        context.console.print("[bold red]❌ Error:[/bold red] Agent initialization failed")
        context.console.print(f"[dim]Reason: {e}[/dim]")
        return

    context.console.print("✅ Agent initialized")

    # Create request
    context.console.print()
    context.console.print("📝 Generating questions...")
    context.console.print(f"   survey_id={survey_id}, round={round_idx}")

    request = GenerateQuestionsRequest(survey_id=survey_id, round_idx=round_idx, prev_answers=prev_answers)

    # Execute agent (async)
    try:
        response = asyncio.run(agent.generate_questions(request))
    except Exception as e:
        context.console.print()
        context.console.print("[bold red]❌ Error:[/bold red] Question generation failed")
        context.console.print(f"[dim]Reason: {e}[/dim]")
        return

    # Display results
    context.console.print()
    context.console.print("✅ Generation Complete")
    context.console.print(f"   round_id: {response.round_id}")
    context.console.print(f"   items generated: {len(response.items)}, failed: {response.failed_count}")
    context.console.print(f"   agent_steps: {response.agent_steps}")
    context.console.print()

    # Display table
    table = Table(title="Generated Items", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Type")
    table.add_column("Difficulty", justify="right")
    table.add_column("Validation", justify="right")

    for item in response.items:
        item_id_short = item.id[:12] + "..." if len(item.id) > 12 else item.id
        table.add_row(
            item_id_short,
            item.type,
            str(item.difficulty),
            f"{item.validation_score:.2f}",
        )

    context.console.print("📋 Generated Items:")
    context.console.print(table)
    context.console.print()

    # Display first item details
    if response.items:
        first_item = response.items[0]
        context.console.print("📄 First Item Details:")
        context.console.print(f"   Stem: {first_item.stem}")
        context.console.print(f"   Answer Schema: {first_item.answer_schema.type}")
        if first_item.answer_schema.keywords:
            keywords_str = ", ".join(first_item.answer_schema.keywords)
            context.console.print(f"   Keywords: [{keywords_str}]")
        context.console.print()


def score_answer(context: CLIContext, *args: str) -> None:
    """
    Score a single answer using Tool 6 with explanation generation.

    Requires:
    - question_id: ID of the question
    - answer: User's answer text

    Args:
        context: CLI context with console and logger.
        *args: Arguments (question_id, answer).

    """
    msg1 = "[bold yellow]⚠️  Placeholder:[/bold yellow] score-answer implementation "
    msg1 += "pending (REQ-CLI-Agent-3)"
    context.console.print(msg1)
    msg2 = "[dim]REQ-CLI-Agent-3 will implement: Tool 6 (score_and_explain) "
    msg2 += "invocation[/dim]"
    context.console.print(msg2)


def batch_score(context: CLIContext, *args: str) -> None:
    """
    Score multiple answers in parallel using Tool 6.

    Requires:
    - batch_file: JSON file with array of {question_id, answer} objects

    Supports parallel execution for improved performance.

    Args:
        context: CLI context with console and logger.
        *args: Arguments (batch_file path).

    """
    msg1 = "[bold yellow]⚠️  Placeholder:[/bold yellow] batch-score implementation "
    msg1 += "pending (REQ-CLI-Agent-4)"
    context.console.print(msg1)
    msg2 = "[dim]REQ-CLI-Agent-4 will implement: Parallel Tool 6 execution "
    msg2 += "(asyncio.gather)[/dim]"
    context.console.print(msg2)


def tools_help(context: CLIContext, *args: str) -> None:
    """
    Display help for tools debugging interface.

    Shows available tools:
    - t1: Get User Profile
    - t2: Search Question Templates
    - t3: Get Difficulty Keywords
    - t4: Validate Question Quality
    - t5: Save Generated Question
    - t6: Score & Generate Explanation

    Args:
        context: CLI context with console and logger.
        *args: Additional arguments (ignored).

    """
    context.console.print()
    context.console.print(
        "[bold cyan]╔════════════════════════════════════════════════════════════════════════════════╗[/bold cyan]"
    )
    context.console.print(
        "[bold cyan]║  agent tools - Tool debugging interface                                       ║[/bold cyan]"
    )
    context.console.print(
        "[bold cyan]╚════════════════════════════════════════════════════════════════════════════════╝[/bold cyan]"
    )
    context.console.print()

    table = Table(show_header=False, box=None, padding=(0, 2))

    # Add tools
    tools = [
        ("agent tools t1", "[dim]🔍 Get User Profile (Tool 1)[/dim]"),
        ("agent tools t2", "[dim]📚 Search Question Templates (Tool 2)[/dim]"),
        ("agent tools t3", "[dim]📊 Get Difficulty Keywords (Tool 3)[/dim]"),
        ("agent tools t4", "[dim]✅ Validate Question Quality (Tool 4)[/dim]"),
        ("agent tools t5", "[dim]💾 Save Generated Question (Tool 5)[/dim]"),
        ("agent tools t6", "[dim]🎯 Score & Generate Explanation (Tool 6)[/dim]"),
    ]

    for cmd, desc in tools:
        table.add_row(cmd, desc)

    context.console.print(table)
    context.console.print()


def t1_get_user_profile(context: CLIContext, *args: str) -> None:
    """
    Tool 1: Get User Profile (debugging interface).

    Invokes FastMCP Tool 1: get_user_profile
    Returns user's skill level, experience, interests, job role, etc.

    Args:
        context: CLI context with console and logger.
        *args: Additional arguments (user_id - reserved for future).

    """
    msg1 = "[bold yellow]⚠️  Placeholder:[/bold yellow] t1 (get_user_profile) "
    msg1 += "implementation pending (REQ-CLI-Agent-5)"
    context.console.print(msg1)
    msg2 = "[dim]REQ-CLI-Agent-5 will implement: Direct FastMCP Tool 1 "
    msg2 += "invocation[/dim]"
    context.console.print(msg2)


def t2_search_question_templates(context: CLIContext, *args: str) -> None:
    """
    Tool 2: Search Question Templates (debugging interface).

    Invokes FastMCP Tool 2: search_question_templates
    Returns templates matching interests, difficulty, and category.

    Args:
        context: CLI context with console and logger.
        *args: Additional arguments (interests, difficulty, category).

    """
    msg1 = "[bold yellow]⚠️  Placeholder:[/bold yellow] t2 "
    msg1 += "(search_question_templates) implementation pending (REQ-CLI-Agent-5)"
    context.console.print(msg1)
    msg2 = "[dim]REQ-CLI-Agent-5 will implement: Direct FastMCP Tool 2 "
    msg2 += "invocation[/dim]"
    context.console.print(msg2)


def t3_get_difficulty_keywords(context: CLIContext, *args: str) -> None:
    """
    Tool 3: Get Difficulty Keywords (debugging interface).

    Invokes FastMCP Tool 3: get_difficulty_keywords
    Returns keywords and concepts for specified difficulty level.

    Args:
        context: CLI context with console and logger.
        *args: Additional arguments (difficulty, category).

    """
    msg1 = "[bold yellow]⚠️  Placeholder:[/bold yellow] t3 "
    msg1 += "(get_difficulty_keywords) implementation pending (REQ-CLI-Agent-5)"
    context.console.print(msg1)
    msg2 = "[dim]REQ-CLI-Agent-5 will implement: Direct FastMCP Tool 3 "
    msg2 += "invocation[/dim]"
    context.console.print(msg2)


def t4_validate_question_quality(context: CLIContext, *args: str) -> None:
    """
    Tool 4: Validate Question Quality (debugging interface).

    Invokes FastMCP Tool 4: validate_question_quality
    Returns validation score and feedback for a question stem.

    Args:
        context: CLI context with console and logger.
        *args: Additional arguments (question_stem, question_type).

    """
    msg1 = "[bold yellow]⚠️  Placeholder:[/bold yellow] t4 "
    msg1 += "(validate_question_quality) implementation pending (REQ-CLI-Agent-5)"
    context.console.print(msg1)
    msg2 = "[dim]REQ-CLI-Agent-5 will implement: Direct FastMCP Tool 4 "
    msg2 += "invocation[/dim]"
    context.console.print(msg2)


def t5_save_generated_question(context: CLIContext, *args: str) -> None:
    """
    Tool 5: Save Generated Question (debugging interface).

    Invokes FastMCP Tool 5: save_generated_question
    Saves a validated question with metadata to database.

    Args:
        context: CLI context with console and logger.
        *args: Additional arguments (item_type, stem, difficulty, categories,
                round_id).

    """
    msg1 = "[bold yellow]⚠️  Placeholder:[/bold yellow] t5 "
    msg1 += "(save_generated_question) implementation pending (REQ-CLI-Agent-5)"
    context.console.print(msg1)
    msg2 = "[dim]REQ-CLI-Agent-5 will implement: Direct FastMCP Tool 5 "
    msg2 += "invocation[/dim]"
    context.console.print(msg2)


def t6_score_and_explain(context: CLIContext, *args: str) -> None:
    """
    Tool 6: Score Answer & Generate Explanation (debugging interface).

    Invokes FastMCP Tool 6: score_and_explain
    Scores an answer using LLM and generates detailed explanation.

    Args:
        context: CLI context with console and logger.
        *args: Additional arguments (question_id, answer, question_context).

    """
    msg1 = "[bold yellow]⚠️  Placeholder:[/bold yellow] t6 (score_and_explain) "
    msg1 += "implementation pending (REQ-CLI-Agent-5)"
    context.console.print(msg1)
    msg2 = "[dim]REQ-CLI-Agent-5 will implement: Direct FastMCP Tool 6 "
    msg2 += "invocation[/dim]"
    context.console.print(msg2)


def _print_generate_questions_help(context: CLIContext) -> None:
    """
    Display help for generate-questions command.

    Args:
        context: CLI context with console and logger.

    """
    context.console.print()
    context.console.print(
        "[bold cyan]╔════════════════════════════════════════════════════════════════════════════════╗[/bold cyan]"
    )
    context.console.print(
        "[bold cyan]║  agent generate-questions - Mode 1 Question Generation                        ║[/bold cyan]"
    )
    context.console.print(
        "[bold cyan]╚════════════════════════════════════════════════════════════════════════════════╝[/bold cyan]"
    )
    context.console.print()
    context.console.print("[bold white]Usage:[/bold white]")
    context.console.print("  agent generate-questions --survey-id SURVEY_ID [--round 1|2] [--prev-answers JSON]")
    context.console.print()
    context.console.print("[bold white]Options:[/bold white]")
    context.console.print("  --survey-id TEXT         Survey ID (required)")
    context.console.print("  --round INTEGER          Round number: 1 (initial) or 2 (adaptive) [default: 1]")
    context.console.print("  --prev-answers TEXT      JSON array of previous answers (Round 2 only)")
    context.console.print('                           Format: \'[{"item_id":"q1","score":85}]\'')
    context.console.print("  --help                   Show this help message")
    context.console.print()
    context.console.print("[bold white]Examples:[/bold white]")
    context.console.print("  # Generate Round 1 questions")
    context.console.print("  agent generate-questions --survey-id survey_123")
    context.console.print()
    context.console.print("  # Generate Round 2 with adaptive difficulty")
    context.console.print(
        '  agent generate-questions --survey-id survey_123 --round 2 \'--prev-answers [{"item_id":"q1","score":85}]\''
    )
    context.console.print()
