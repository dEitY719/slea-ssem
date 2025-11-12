"""
Agent-based question generation and scoring CLI actions.

REQ: REQ-CLI-Agent-1, REQ-CLI-Agent-2
REQ: REQ-A-Agent-Backend-1 (CLI → Backend Service → DB integration)
"""

import asyncio
import json
import logging

from rich.table import Table

from src.agent.llm_agent import ItemGenAgent
from src.backend.database import SessionLocal
from src.backend.services.question_gen_service import QuestionGenerationService
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

    # Validate user context
    if not context.session.user_id:
        context.console.print("[bold red]❌ Error:[/bold red] No user logged in")
        context.console.print("[dim]Please run 'auth login' first[/dim]")
        return

    try:
        user_id = int(context.session.user_id)
    except (ValueError, TypeError):
        context.console.print(f"[bold red]❌ Error:[/bold red] Invalid user_id: {context.session.user_id}")
        return

    # Generate questions via Backend Service (saves to DB)
    context.console.print()
    context.console.print("📝 Generating questions...")
    context.console.print(f"   survey_id={survey_id}, round={round_idx}")

    # REQ-A-Agent-Backend-1: CLI → Backend Service → DB integration
    db_session = SessionLocal()
    try:
        service = QuestionGenerationService(db_session)
        response = asyncio.run(service.generate_questions(
            user_id=user_id,
            survey_id=survey_id,
            round_num=round_idx
        ))
    except Exception as e:
        context.console.print()
        context.console.print("[bold red]❌ Error:[/bold red] Question generation failed")
        context.console.print(f"[dim]Reason: {e}[/dim]")
        return
    finally:
        db_session.close()

    # Display results
    context.console.print()
    context.console.print("✅ Generation Complete")
    context.console.print(f"   session_id: {response['session_id']}")
    questions_list = response.get("questions", [])
    context.console.print(f"   items generated: {len(questions_list)}")
    if "error" in response:
        context.console.print(f"   error: {response['error']}")
    context.console.print()

    # Display table
    if questions_list:
        table = Table(title="Generated Items", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim")
        table.add_column("Type")
        table.add_column("Difficulty", justify="right")
        table.add_column("Category")

        for item in questions_list:
            item_id_short = item["id"][:12] + "..." if len(item["id"]) > 12 else item["id"]
            table.add_row(
                item_id_short,
                item["item_type"],
                str(item["difficulty"]),
                item["category"],
            )

        context.console.print("📋 Generated Items:")
        context.console.print(table)
        context.console.print()

        # Display first item details
        first_item = questions_list[0]
        context.console.print("📄 First Item Details:")
        context.console.print(f"   Stem: {first_item['stem']}")
        context.console.print(f"   Answer Schema: {first_item['answer_schema']}")
        context.console.print()
    else:
        context.console.print("[dim]No questions were generated[/dim]")
        context.console.print()


def score_answer(context: CLIContext, *args: str) -> None:
    """
    Score a single answer using Tool 6 with explanation generation.

    Supports multiple question types (MC, short answer, true/false) and returns
    detailed scoring with LLM-generated explanation.

    Args:
        context: CLI context with console and logger.
        *args: Parsed arguments (--question-id, --question, --answer-type,
                                 --user-answer, --correct-answer, --context).

    REQ: REQ-CLI-Agent-3

    """
    # Parse arguments
    question_id = None
    question_stem = None
    answer_type = None
    user_answer = None
    correct_answer = None
    context_str = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--question-id" and i + 1 < len(args):
            question_id = args[i + 1]
            i += 2
        elif arg == "--question" and i + 1 < len(args):
            question_stem = args[i + 1]
            i += 2
        elif arg == "--answer-type" and i + 1 < len(args):
            answer_type = args[i + 1]
            i += 2
        elif arg == "--user-answer" and i + 1 < len(args):
            user_answer = args[i + 1]
            i += 2
        elif arg == "--correct-answer" and i + 1 < len(args):
            correct_answer = args[i + 1]
            i += 2
        elif arg == "--context" and i + 1 < len(args):
            context_str = args[i + 1]
            i += 2
        elif arg == "--help":
            _print_score_answer_help(context)
            return
        else:
            i += 1

    # Validate required parameters
    if not question_id:
        context.console.print("[bold red]❌ Error:[/bold red] --question-id is required")
        _print_score_answer_help(context)
        return

    if not question_stem:
        context.console.print("[bold red]❌ Error:[/bold red] --question is required")
        _print_score_answer_help(context)
        return

    if not answer_type:
        context.console.print("[bold red]❌ Error:[/bold red] --answer-type is required")
        _print_score_answer_help(context)
        return

    if not user_answer:
        context.console.print("[bold red]❌ Error:[/bold red] --user-answer is required")
        _print_score_answer_help(context)
        return

    if not correct_answer:
        context.console.print("[bold red]❌ Error:[/bold red] --correct-answer is required")
        _print_score_answer_help(context)
        return

    # Validate answer-type
    valid_types = ["multiple_choice", "short_answer", "true_false"]
    if answer_type not in valid_types:
        context.console.print(f"[bold red]❌ Error:[/bold red] --answer-type must be one of: {', '.join(valid_types)}")
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
    context.console.print("🎯 Scoring answer...")
    context.console.print(f"   question_id={question_id}, type={answer_type}")

    from src.agent.llm_agent import ScoreAnswerRequest

    request = ScoreAnswerRequest(
        item_id=question_id,
        question_stem=question_stem,
        question_type=answer_type,
        user_answer=user_answer,
        correct_answer=correct_answer,
        context=context_str,
    )

    # Execute agent (async)
    try:
        response = asyncio.run(agent.score_answer(request))
    except Exception as e:
        context.console.print()
        context.console.print("[bold red]❌ Error:[/bold red] Answer scoring failed")
        context.console.print(f"[dim]Reason: {e}[/dim]")
        return

    # Display results
    context.console.print()
    context.console.print("✅ Scoring Complete")
    context.console.print(f"   correct: {response.correct}")
    context.console.print(f"   score: {response.score}")
    if hasattr(response, "confidence") and response.confidence is not None:
        context.console.print(f"   confidence: {response.confidence:.2f}")
    context.console.print()

    # Display scoring result panel
    correctness_status = "✅ CORRECT" if response.correct else "❌ INCORRECT"
    panel_content = f"""
Question: {question_stem[:60]}...
User Answer: {user_answer}
Correct Answer: {correct_answer}
Score: {response.score}/100
Status: {correctness_status}"""

    from rich.panel import Panel

    context.console.print(Panel(panel_content, title="📊 Scoring Result", style="cyan"))

    # Display explanation
    if response.explanation:
        context.console.print()
        context.console.print("📝 Explanation:")
        context.console.print(response.explanation)

    # Display matched keywords if available
    if hasattr(response, "keyword_matches") and response.keyword_matches:
        context.console.print()
        context.console.print(f"💡 Keywords Matched: {response.keyword_matches}")

    # Display confidence
    if hasattr(response, "confidence") and response.confidence is not None:
        context.console.print()
        context.console.print(f"🎯 Confidence: {response.confidence * 100:.0f}%")

    context.console.print()


def batch_score(context: CLIContext, *args: str) -> None:
    """
    Score multiple answers in parallel using Tool 6.

    Processes batch JSON file with array of scoring items and executes
    scoring concurrently using asyncio.gather() for improved performance.

    Args:
        context: CLI context with console and logger.
        *args: Parsed arguments (--batch-file, --parallel, --output).

    REQ: REQ-CLI-Agent-4

    """
    from pathlib import Path
    from time import time

    from rich.progress import Progress

    from src.agent.llm_agent import ScoreAnswerRequest

    # Parse arguments
    batch_file = None
    parallel_workers = 3
    output_file = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--batch-file" and i + 1 < len(args):
            batch_file = args[i + 1]
            i += 2
        elif arg == "--parallel" and i + 1 < len(args):
            try:
                parallel_workers = int(args[i + 1])
                if parallel_workers < 1 or parallel_workers > 10:
                    context.console.print(
                        f"[bold red]❌ Error:[/bold red] --parallel must be between 1-10 (got: {parallel_workers})"
                    )
                    return
                i += 2
            except ValueError:
                context.console.print(f"[bold red]❌ Error:[/bold red] --parallel must be integer (got: {args[i + 1]})")
                return
        elif arg == "--output" and i + 1 < len(args):
            output_file = args[i + 1]
            i += 2
        elif arg == "--help":
            _print_batch_score_help(context)
            return
        else:
            i += 1

    # Validate required batch-file
    if not batch_file:
        context.console.print("[bold red]❌ Error:[/bold red] --batch-file is required")
        _print_batch_score_help(context)
        return

    # Load batch file
    context.console.print("📂 Loading batch file...")
    batch_path = Path(batch_file)

    if not batch_path.exists():
        context.console.print(f"[bold red]❌ Error:[/bold red] Batch file not found: {batch_file}")
        return

    try:
        with open(batch_path) as f:
            batch_data = json.load(f)
    except json.JSONDecodeError as e:
        context.console.print("[bold red]❌ Error:[/bold red] Invalid JSON in batch file")
        context.console.print(f"[dim]Reason: {e}[/dim]")
        return
    except Exception as e:
        context.console.print(f"[bold red]❌ Error:[/bold red] Failed to read batch file: {e}")
        return

    # Validate batch is array
    if not isinstance(batch_data, list):
        context.console.print("[bold red]❌ Error:[/bold red] Batch file must contain JSON array")
        return

    # Validate batch is not empty
    if not batch_data:
        context.console.print("[bold red]❌ Error:[/bold red] Batch file contains no items (empty array)")
        return

    # Validate each item has required fields
    required_fields = {"question_id", "question", "answer_type", "user_answer", "correct_answer"}
    for idx, item in enumerate(batch_data):
        if not isinstance(item, dict):
            context.console.print(
                f"[bold red]❌ Error:[/bold red] Item at index {idx} is not a dict (got: {type(item).__name__})"
            )
            return

        missing_fields = required_fields - set(item.keys())
        if missing_fields:
            context.console.print(f"[bold red]❌ Error:[/bold red] Item at index {idx} missing required fields")
            context.console.print(f"[dim]Required: {', '.join(sorted(required_fields))}[/dim]")
            context.console.print(f"[dim]Missing: {', '.join(sorted(missing_fields))}[/dim]")
            return

        # Validate answer_type
        valid_types = ["multiple_choice", "short_answer", "true_false"]
        if item["answer_type"] not in valid_types:
            context.console.print(
                f"[bold red]❌ Error:[/bold red] Item at index {idx} has invalid answer_type: {item['answer_type']}"
            )
            context.console.print(f"[dim]Must be one of: {', '.join(valid_types)}[/dim]")
            return

    context.console.print(f"   File: {batch_file}")
    context.console.print(f"   Items: {len(batch_data)}")
    context.console.print("✅ Batch loaded")

    # Initialize agent
    context.console.print()
    context.console.print("🚀 Initializing Agent... (GEMINI_API_KEY required)")
    try:
        agent = ItemGenAgent()
    except Exception as e:
        context.console.print("[bold red]❌ Error:[/bold red] Agent initialization failed")
        context.console.print(f"[dim]Reason: {e}[/dim]")
        return

    context.console.print("✅ Agent initialized")

    # Score answers in parallel
    context.console.print()
    context.console.print("🔄 Scoring answers in parallel...")
    context.console.print(f"   Workers: {parallel_workers}")
    context.console.print(f"   Processing: {', '.join(item['question_id'] for item in batch_data[:3])}, ...")
    context.console.print()

    start_time = time()

    async def score_single_item(item: dict) -> tuple:
        """Score a single item and return result tuple."""
        try:
            request = ScoreAnswerRequest(
                item_id=item["question_id"],
                question_type=item["answer_type"],
                user_answer=item["user_answer"],
                correct_answer=item["correct_answer"],
            )
            response = await agent.score_answer(request)
            return (True, item, response)
        except Exception as e:
            return (False, item, str(e))

    async def score_batch_parallel() -> tuple:
        """Score all items in batch with controlled concurrency."""
        tasks = [score_single_item(item) for item in batch_data]

        # Use semaphore to control concurrency
        results_list = []
        errors_list = []

        with Progress(transient=True) as progress:
            task = progress.add_task("[cyan]Scoring...", total=len(tasks))

            # Execute tasks with limited concurrency
            for i in range(0, len(tasks), parallel_workers):
                chunk = tasks[i : i + parallel_workers]
                chunk_results = await asyncio.gather(*chunk)

                for success, item, response in chunk_results:
                    if success:
                        results_list.append((item, response))
                    else:
                        errors_list.append((item, response))
                    progress.update(task, advance=1)

        return results_list, errors_list

    # Execute async scoring
    try:
        completed_results, failed = asyncio.run(score_batch_parallel())
    except Exception as e:
        context.console.print()
        context.console.print("[bold red]❌ Error:[/bold red] Batch scoring failed")
        context.console.print(f"[dim]Reason: {e}[/dim]")
        return

    # Calculate statistics
    total_items = len(batch_data)
    failed_count = len(failed)
    passed_count = sum(1 for _, resp in completed_results if resp.correct)
    partial_count = sum(1 for _, resp in completed_results if not resp.correct and resp.score > 0)
    failed_only_count = sum(1 for _, resp in completed_results if resp.score == 0)

    scores = [resp.score for _, resp in completed_results]
    avg_score = sum(scores) / len(scores) if scores else 0

    elapsed_time = time() - start_time

    # Display results summary
    context.console.print()
    context.console.print("✅ Batch Scoring Complete")
    context.console.print(f"   Total: {total_items} items")
    context.console.print(f"   Passed (100): {passed_count}")
    context.console.print(f"   Partial (1-99): {partial_count}")
    context.console.print(f"   Failed (0): {failed_only_count}")
    context.console.print(f"   Scoring failures: {failed_count}")
    context.console.print(f"   Average Score: {avg_score:.1f}")
    context.console.print(f"   Execution Time: {elapsed_time:.2f}s")
    context.console.print()

    # Display results table
    table = Table(title="Batch Scoring Results", show_header=True, header_style="bold cyan")
    table.add_column("ID", style="dim")
    table.add_column("Type")
    table.add_column("Score", justify="right")
    table.add_column("Status")

    for item, response in completed_results:
        question_id = item["question_id"]
        question_id_short = question_id[:12] + "..." if len(question_id) > 12 else question_id

        if response.correct:
            status_icon = "✅"
        elif response.score > 0:
            status_icon = "⚠️ "
        else:
            status_icon = "❌"

        table.add_row(
            question_id_short,
            item["answer_type"][:5],  # MC, SA, T/F abbreviation
            str(response.score),
            status_icon,
        )

    # Add failed items to table
    for item, _error in failed:
        question_id = item["question_id"]
        question_id_short = question_id[:12] + "..." if len(question_id) > 12 else question_id
        table.add_row(question_id_short, item["answer_type"][:5], "ERROR", "❌")

    context.console.print("📊 Batch Results:")
    context.console.print(table)
    context.console.print()

    # Save results to file if output specified
    if output_file:
        output_path = Path(output_file)
        output_data = {
            "metadata": {
                "total_items": total_items,
                "passed_count": passed_count,
                "partial_count": partial_count,
                "failed_count": failed_only_count,
                "errors_count": failed_count,
                "average_score": avg_score,
                "execution_time": elapsed_time,
            },
            "results": [
                {
                    "question_id": item["question_id"],
                    "answer_type": item["answer_type"],
                    "score": response.score,
                    "correct": response.correct,
                    "explanation": response.explanation,
                }
                for item, response in completed_results
            ],
            "errors": [{"question_id": item["question_id"], "error": error} for item, error in failed],
        }

        try:
            with open(output_path, "w") as f:
                json.dump(output_data, f, indent=2)
            context.console.print(f"📁 Results saved to: {output_file}")
        except Exception as e:
            context.console.print(f"[bold yellow]⚠️  Warning:[/bold yellow] Failed to save results: {e}")
        context.console.print()


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
        *args: Additional arguments (--user-id, --help).

    REQ: REQ-CLI-Agent-5

    """
    # Parse arguments
    user_id = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--user-id" and i + 1 < len(args):
            user_id = args[i + 1]
            i += 2
        elif arg == "--help":
            _print_t1_help(context)
            return
        else:
            i += 1

    # Validate required parameters
    if not user_id:
        context.console.print("[bold red]❌ Error:[/bold red] --user-id is required")
        _print_t1_help(context)
        return

    # Initialize agent
    context.console.print("🔍 Tool 1: Get User Profile")
    context.console.print("━" * 88)
    context.console.print()
    context.console.print(f"🚀 Retrieving profile for user: {user_id}")

    try:
        agent = ItemGenAgent()
    except Exception as e:
        context.console.print("[bold red]❌ Error:[/bold red] Agent initialization failed")
        context.console.print(f"[dim]Reason: {e}[/dim]")
        return

    # Execute tool
    try:
        response = asyncio.run(agent.get_user_profile(user_id))
    except Exception as e:
        context.console.print()
        context.console.print("[bold red]❌ Error:[/bold red] Tool 1 invocation failed")
        context.console.print(f"[dim]Reason: {e}[/dim]")
        return

    # Display results
    context.console.print()
    if hasattr(response, "user_id"):
        context.console.print(f"User ID: {response.user_id}")
    if hasattr(response, "skill_level"):
        context.console.print(f"Skill Level: {response.skill_level}/10")
    if hasattr(response, "experience_years"):
        context.console.print(f"Experience (Years): {response.experience_years}")
    if hasattr(response, "interests"):
        interests_str = ", ".join(response.interests) if response.interests else "N/A"
        context.console.print(f"Interests: {interests_str}")
    if hasattr(response, "job_role"):
        context.console.print(f"Job Role: {response.job_role}")

    context.console.print()


def t2_search_question_templates(context: CLIContext, *args: str) -> None:
    """Tool 2: Search Question Templates (debugging interface). REQ: REQ-CLI-Agent-5."""
    interests = None
    difficulty = None
    category = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--interests" and i + 1 < len(args):
            interests = args[i + 1]
            i += 2
        elif arg == "--difficulty" and i + 1 < len(args):
            try:
                difficulty = int(args[i + 1])
                i += 2
            except ValueError:
                context.console.print("[bold red]❌ Error:[/bold red] --difficulty must be integer")
                return
        elif arg == "--category" and i + 1 < len(args):
            category = args[i + 1]
            i += 2
        elif arg == "--help":
            _print_t2_help(context)
            return
        else:
            i += 1

    if not interests or difficulty is None:
        context.console.print("[bold red]❌ Error:[/bold red] --interests and --difficulty required")
        _print_t2_help(context)
        return

    if difficulty < 1 or difficulty > 10:
        context.console.print("[bold red]❌ Error:[/bold red] --difficulty must be 1-10")
        return

    context.console.print("📚 Tool 2: Search Question Templates")
    context.console.print("━" * 88)
    context.console.print(f"🔍 Searching templates for: {interests}, Difficulty: {difficulty}")

    try:
        agent = ItemGenAgent()
    except Exception:
        context.console.print("[bold red]❌ Error:[/bold red] Agent initialization failed")
        return

    try:
        response = asyncio.run(agent.search_question_templates(interests, difficulty, category))
    except Exception as e:
        context.console.print(f"[bold red]❌ Error:[/bold red] Tool 2 invocation failed: {e}")
        return

    context.console.print()
    if hasattr(response, "templates"):
        context.console.print(f"Templates Found: {len(response.templates)}")
        for tmpl in response.templates[:5]:
            if hasattr(tmpl, "id") and hasattr(tmpl, "stem"):
                context.console.print(f"  • {tmpl.id}: {tmpl.stem}")
    context.console.print()


def t3_get_difficulty_keywords(context: CLIContext, *args: str) -> None:
    """Tool 3: Get Difficulty Keywords (debugging interface). REQ: REQ-CLI-Agent-5."""
    difficulty = None
    category = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--difficulty" and i + 1 < len(args):
            try:
                difficulty = int(args[i + 1])
                i += 2
            except ValueError:
                context.console.print("[bold red]❌ Error:[/bold red] --difficulty must be integer")
                return
        elif arg == "--category" and i + 1 < len(args):
            category = args[i + 1]
            i += 2
        elif arg == "--help":
            _print_t3_help(context)
            return
        else:
            i += 1

    if difficulty is None:
        context.console.print("[bold red]❌ Error:[/bold red] --difficulty required")
        _print_t3_help(context)
        return

    if difficulty < 1 or difficulty > 10:
        context.console.print("[bold red]❌ Error:[/bold red] --difficulty must be 1-10")
        return

    context.console.print("📊 Tool 3: Get Difficulty Keywords")
    context.console.print("━" * 88)
    context.console.print(f"🔍 Keywords for difficulty: {difficulty}")

    try:
        agent = ItemGenAgent()
    except Exception:
        context.console.print("[bold red]❌ Error:[/bold red] Agent initialization failed")
        return

    try:
        response = asyncio.run(agent.get_difficulty_keywords(difficulty, category))
    except Exception as e:
        context.console.print(f"[bold red]❌ Error:[/bold red] Tool 3 invocation failed: {e}")
        return

    context.console.print()
    if hasattr(response, "keywords"):
        context.console.print(f"Keywords ({len(response.keywords)} total):")
        for keyword in response.keywords[:10]:
            context.console.print(f"  • {keyword}")
        if len(response.keywords) > 10:
            context.console.print(f"  ... and {len(response.keywords) - 10} more")
    context.console.print()


def t4_validate_question_quality(context: CLIContext, *args: str) -> None:
    """Tool 4: Validate Question Quality (debugging interface). REQ: REQ-CLI-Agent-5."""
    question = None
    question_type = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--question" and i + 1 < len(args):
            question = args[i + 1]
            i += 2
        elif arg == "--type" and i + 1 < len(args):
            question_type = args[i + 1]
            i += 2
        elif arg == "--help":
            _print_t4_help(context)
            return
        else:
            i += 1

    if not question or not question_type:
        context.console.print("[bold red]❌ Error:[/bold red] --question and --type required")
        _print_t4_help(context)
        return

    valid_types = ["multiple_choice", "short_answer", "true_false"]
    if question_type not in valid_types:
        context.console.print(f"[bold red]❌ Error:[/bold red] Invalid type: {question_type}")
        return

    context.console.print("✅ Tool 4: Validate Question Quality")
    context.console.print("━" * 88)

    try:
        agent = ItemGenAgent()
    except Exception:
        context.console.print("[bold red]❌ Error:[/bold red] Agent initialization failed")
        return

    try:
        response = asyncio.run(agent.validate_question_quality(question, question_type))
    except Exception as e:
        context.console.print(f"[bold red]❌ Error:[/bold red] Tool 4 invocation failed: {e}")
        return

    context.console.print()
    if hasattr(response, "score"):
        context.console.print(f"Score: {response.score:.2f}/1.0")
    if hasattr(response, "status"):
        context.console.print(f"Status: {response.status}")
    if hasattr(response, "feedback"):
        context.console.print(f"Feedback: {response.feedback}")
    context.console.print()


def t5_save_generated_question(context: CLIContext, *args: str) -> None:
    """Tool 5: Save Generated Question (debugging interface). REQ: REQ-CLI-Agent-5."""
    stem = None
    q_type = None
    difficulty = None
    categories = None
    round_id = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--stem" and i + 1 < len(args):
            stem = args[i + 1]
            i += 2
        elif arg == "--type" and i + 1 < len(args):
            q_type = args[i + 1]
            i += 2
        elif arg == "--difficulty" and i + 1 < len(args):
            try:
                difficulty = int(args[i + 1])
                i += 2
            except ValueError:
                context.console.print("[bold red]❌ Error:[/bold red] --difficulty must be integer")
                return
        elif arg == "--categories" and i + 1 < len(args):
            categories = args[i + 1]
            i += 2
        elif arg == "--round-id" and i + 1 < len(args):
            round_id = args[i + 1]
            i += 2
        elif arg == "--help":
            _print_t5_help(context)
            return
        else:
            i += 1

    if not all([stem, q_type, difficulty, categories, round_id]):
        context.console.print("[bold red]❌ Error:[/bold red] All parameters required")
        _print_t5_help(context)
        return

    if difficulty < 1 or difficulty > 10:
        context.console.print("[bold red]❌ Error:[/bold red] --difficulty must be 1-10")
        return

    context.console.print("💾 Tool 5: Save Generated Question")
    context.console.print("━" * 88)

    try:
        agent = ItemGenAgent()
    except Exception:
        context.console.print("[bold red]❌ Error:[/bold red] Agent initialization failed")
        return

    try:
        cats = [c.strip() for c in categories.split(",")]
        response = asyncio.run(agent.save_generated_question(stem, q_type, difficulty, cats, round_id))
    except Exception as e:
        context.console.print(f"[bold red]❌ Error:[/bold red] Tool 5 invocation failed: {e}")
        return

    context.console.print()
    context.console.print("✅ Question Saved Successfully")
    if hasattr(response, "item_id"):
        context.console.print(f"Item ID: {response.item_id}")
    if hasattr(response, "status"):
        context.console.print(f"Status: {response.status}")
    context.console.print()


def t6_score_and_explain(context: CLIContext, *args: str) -> None:
    """Tool 6: Score & Generate Explanation (debugging interface). REQ: REQ-CLI-Agent-5."""
    question_id = None
    question = None
    answer_type = None
    user_answer = None
    correct_answer = None
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--question-id" and i + 1 < len(args):
            question_id = args[i + 1]
            i += 2
        elif arg == "--question" and i + 1 < len(args):
            question = args[i + 1]
            i += 2
        elif arg == "--answer-type" and i + 1 < len(args):
            answer_type = args[i + 1]
            i += 2
        elif arg == "--user-answer" and i + 1 < len(args):
            user_answer = args[i + 1]
            i += 2
        elif arg == "--correct-answer" and i + 1 < len(args):
            correct_answer = args[i + 1]
            i += 2
        elif arg == "--help":
            _print_t6_help(context)
            return
        else:
            i += 1

    required = [question_id, question, answer_type, user_answer, correct_answer]
    if not all(required):
        context.console.print("[bold red]❌ Error:[/bold red] All parameters required")
        _print_t6_help(context)
        return

    valid_types = ["multiple_choice", "short_answer", "true_false"]
    if answer_type not in valid_types:
        context.console.print(f"[bold red]❌ Error:[/bold red] Invalid answer_type: {answer_type}")
        return

    context.console.print("🎯 Tool 6: Score & Generate Explanation")
    context.console.print("━" * 88)

    try:
        agent = ItemGenAgent()
    except Exception:
        context.console.print("[bold red]❌ Error:[/bold red] Agent initialization failed")
        return

    try:
        from src.agent.llm_agent import ScoreAnswerRequest

        request = ScoreAnswerRequest(
            item_id=question_id,
            question_stem=question,
            question_type=answer_type,
            user_answer=user_answer,
            correct_answer=correct_answer,
        )
        response = asyncio.run(agent.score_answer(request))
    except Exception as e:
        context.console.print(f"[bold red]❌ Error:[/bold red] Tool 6 invocation failed: {e}")
        return

    context.console.print()
    if hasattr(response, "score"):
        status = "✅ CORRECT" if response.correct else "❌ INCORRECT"
        context.console.print(f"Score: {response.score}/100 {status}")
    if hasattr(response, "explanation"):
        context.console.print(f"Explanation: {response.explanation}")
    context.console.print()


def _print_t1_help(context: CLIContext) -> None:
    """Display help for Tool 1."""
    context.console.print()
    context.console.print("[bold cyan]Tool 1: Get User Profile[/bold cyan]")
    context.console.print("Usage: agent tools t1 --user-id USER_ID")
    context.console.print()


def _print_t2_help(context: CLIContext) -> None:
    """Display help for Tool 2."""
    context.console.print()
    context.console.print("[bold cyan]Tool 2: Search Question Templates[/bold cyan]")
    context.console.print("Usage: agent tools t2 --interests TEXT --difficulty INT [--category TEXT]")
    context.console.print()


def _print_t3_help(context: CLIContext) -> None:
    """Display help for Tool 3."""
    context.console.print()
    context.console.print("[bold cyan]Tool 3: Get Difficulty Keywords[/bold cyan]")
    context.console.print("Usage: agent tools t3 --difficulty INT [--category TEXT]")
    context.console.print()


def _print_t4_help(context: CLIContext) -> None:
    """Display help for Tool 4."""
    context.console.print()
    context.console.print("[bold cyan]Tool 4: Validate Question Quality[/bold cyan]")
    context.console.print("Usage: agent tools t4 --question TEXT --type TYPE")
    context.console.print()


def _print_t5_help(context: CLIContext) -> None:
    """Display help for Tool 5."""
    context.console.print()
    context.console.print("[bold cyan]Tool 5: Save Generated Question[/bold cyan]")
    context.console.print(
        "Usage: agent tools t5 --stem TEXT --type TYPE --difficulty INT --categories TEXT --round-id TEXT"
    )
    context.console.print()


def _print_t6_help(context: CLIContext) -> None:
    """Display help for Tool 6."""
    context.console.print()
    context.console.print("[bold cyan]Tool 6: Score & Generate Explanation[/bold cyan]")
    context.console.print(
        "Usage: agent tools t6 --question-id ID --question TEXT --answer-type TYPE "
        "--user-answer TEXT --correct-answer TEXT"
    )
    context.console.print()


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


def _print_score_answer_help(context: CLIContext) -> None:
    """
    Display help for score-answer command.

    Args:
        context: CLI context with console and logger.

    """
    context.console.print()
    context.console.print(
        "[bold cyan]╔════════════════════════════════════════════════════════════════════════════════╗[/bold cyan]"
    )
    context.console.print(
        "[bold cyan]║  agent score-answer - Mode 2 Single Answer Scoring                           ║[/bold cyan]"
    )
    context.console.print(
        "[bold cyan]╚════════════════════════════════════════════════════════════════════════════════╝[/bold cyan]"
    )
    context.console.print()
    context.console.print("[bold white]Usage:[/bold white]")
    context.console.print("  agent score-answer --question-id ID --question STEM --answer-type TYPE")
    context.console.print("                     --user-answer ANSWER --correct-answer CORRECT [--context TEXT]")
    context.console.print()
    context.console.print("[bold white]Options:[/bold white]")
    context.console.print("  --question-id TEXT       Question ID (required)")
    context.console.print("  --question TEXT          Question stem (required)")
    context.console.print(
        "  --answer-type TEXT       Question type (required): multiple_choice, short_answer, true_false"
    )
    context.console.print("  --user-answer TEXT       User's answer (required)")
    context.console.print("  --correct-answer TEXT    Correct answer (required)")
    context.console.print("  --context TEXT           Additional context (optional)")
    context.console.print("  --help                   Show this help message")
    context.console.print()
    context.console.print("[bold white]Examples:[/bold white]")
    context.console.print("  # Score a multiple choice answer")
    context.console.print(
        "  agent score-answer --question-id q_001 --question 'What is X?' \\\n"
        "                     --answer-type multiple_choice --user-answer 'Option A' \\\n"
        "                     --correct-answer 'Option A'"
    )
    context.console.print()
    context.console.print("  # Score a short answer")
    context.console.print(
        "  agent score-answer --question-id q_002 --question 'Explain Y' \\\n"
        "                     --answer-type short_answer --user-answer 'My explanation' \\\n"
        "                     --correct-answer 'Complete explanation'"
    )
    context.console.print()


def _print_batch_score_help(context: CLIContext) -> None:
    """
    Display help for batch-score command.

    Args:
        context: CLI context with console and logger.

    """
    context.console.print()
    context.console.print(
        "[bold cyan]╔════════════════════════════════════════════════════════════════════════════════╗[/bold cyan]"
    )
    context.console.print(
        "[bold cyan]║  agent batch-score - Mode 2 Parallel Batch Scoring                           ║[/bold cyan]"
    )
    context.console.print(
        "[bold cyan]╚════════════════════════════════════════════════════════════════════════════════╝[/bold cyan]"
    )
    context.console.print()
    context.console.print("[bold white]Usage:[/bold white]")
    context.console.print("  agent batch-score --batch-file FILE [--parallel N] [--output FILE]")
    context.console.print()
    context.console.print("[bold white]Options:[/bold white]")
    context.console.print("  --batch-file TEXT      Path to JSON file with batch array (required)")
    context.console.print("  --parallel INTEGER     Number of parallel workers 1-10 (default: 3)")
    context.console.print("  --output TEXT          Output file path for results in JSON (optional)")
    context.console.print("  --help                 Show this help message")
    context.console.print()
    context.console.print("[bold white]Batch File Format:[/bold white]")
    context.console.print("JSON array of scoring items:")
    context.console.print()
    context.console.print(
        "  [\\n"
        "    {\\n"
        '      "question_id": "q_001",\\n'
        '      "question": "What is X?",\\n'
        '      "answer_type": "multiple_choice",\\n'
        '      "user_answer": "Option A",\\n'
        '      "correct_answer": "Option A",\\n'
        '      "context": "optional context"\\n'
        "    },\\n"
        "    ...\\n"
        "  ]"
    )
    context.console.print()
    context.console.print("[bold white]Examples:[/bold white]")
    context.console.print("  # Score batch with default 3 workers")
    context.console.print("  agent batch-score --batch-file batch.json")
    context.console.print()
    context.console.print("  # Score batch with 5 workers and save results")
    context.console.print("  agent batch-score --batch-file batch.json --parallel 5 --output results.json")
    context.console.print()
