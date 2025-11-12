"""Questions and test-related CLI actions."""

import re

from rich.table import Table

from src.backend.database import SessionLocal
from src.backend.models.question import Question
from src.cli.context import CLIContext


def _is_valid_session_id(value: str) -> bool:
    """Check if value looks like a valid UUID (session ID)."""
    uuid_pattern = r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
    return bool(re.match(uuid_pattern, value.lower()))


def questions_help(context: CLIContext, *args: str) -> None:
    """Questions 도메인의 사용 가능한 명령어를 보여줍니다."""
    # If session_id is provided, show questions instead
    if args and _is_valid_session_id(args[0]):
        show_session_questions(context, *args)
        return

    context.console.print("[bold yellow]Questions Commands:[/bold yellow]")
    context.console.print("  questions [session_id]         - 세션의 문항 조회")
    context.console.print("  questions session resume        - 테스트 세션 재개")
    context.console.print("  questions session status        - 세션 상태 변경 (일시중지/재개)")
    context.console.print("  questions session time_status   - 세션 시간 제한 확인")
    context.console.print("  questions generate              - 테스트 문항 생성 (Round 1)")
    context.console.print("  questions generate adaptive     - 적응형 문항 생성 (Round 2+)")
    context.console.print("  questions answer autosave       - 답변 자동 저장")
    context.console.print("  questions answer score          - 단일 답변 채점")
    context.console.print("  questions score                 - 라운드 점수 계산 및 저장")
    context.console.print("  questions explanation generate  - 해설 생성")


def show_session_questions(context: CLIContext, *args: str) -> None:
    """세션에 포함된 문항을 조회하고 표시합니다."""
    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] questions [session_id]")
        context.console.print("[bold cyan]Example:[/bold cyan] questions 8c288904-bbf4-4d60-a5da-988ee538e0c8")
        return

    session_id = args[0]

    if not _is_valid_session_id(session_id):
        context.console.print("[bold red]✗ Invalid session ID format[/bold red]")
        context.console.print(f"[yellow]Expected UUID format, got: {session_id}[/yellow]")
        return

    db_session = None
    try:
        # Get database session
        db_session = SessionLocal()

        # Query questions for this session
        questions = db_session.query(Question).filter_by(session_id=session_id).all()

        if not questions:
            context.console.print(f"[bold yellow]⚠️  No questions found for session {session_id}[/bold yellow]")
            return

        # Display title
        context.console.print(f"[bold cyan]Questions in Session {session_id}[/bold cyan]")
        context.console.print(f"[dim]Total: {len(questions)} question(s)[/dim]")
        context.console.print()

        # Create and populate table (simplified: ID, Stem, Choices, Answer only)
        table = Table(title=None, show_header=True, header_style="bold cyan")
        table.add_column("ID", style="magenta", max_width=20)
        table.add_column("Stem", style="white")
        table.add_column("Choices", style="green")
        table.add_column("Answer", style="yellow")

        for q in questions:
            # Truncate stem if too long
            stem = q.stem[:50] + "..." if len(q.stem) > 50 else q.stem

            # Format choices
            choices_str = ""
            if q.choices:
                choices_str = ", ".join(q.choices[:3])
                if len(q.choices) > 3:
                    choices_str += ", ..."

            # Format answer from answer_schema
            answer_str = ""
            if isinstance(q.answer_schema, dict):
                # Try correct_answer first (newer format), then correct_key (legacy)
                if "correct_answer" in q.answer_schema:
                    answer_str = str(q.answer_schema["correct_answer"])[:40]  # Truncate long answers
                elif "correct_key" in q.answer_schema:
                    answer_str = q.answer_schema["correct_key"]
                    validation_score = q.answer_schema.get("validation_score")
                    if validation_score is not None:
                        answer_str += f" ({validation_score:.2f})"
                elif "correct_keywords" in q.answer_schema:
                    keywords = q.answer_schema["correct_keywords"]
                    answer_str = ", ".join(keywords[:2])
                    if len(keywords) > 2:
                        answer_str += ", ..."

            table.add_row(
                q.id[:12] + "...",
                stem,
                choices_str,
                answer_str,
            )

        context.console.print(table)
        context.console.print()

        # Display first question details
        if questions:
            first_q = questions[0]
            context.console.print("[bold cyan]📄 First Question Details:[/bold cyan]")
            context.console.print(f"  ID: {first_q.id}")
            context.console.print(f"  Type: {first_q.item_type}")
            context.console.print(f"  Stem: {first_q.stem}")
            context.console.print(f"  Difficulty: {first_q.difficulty}/10")
            context.console.print(f"  Category: {first_q.category}")
            if first_q.choices:
                context.console.print(f"  Choices: {first_q.choices}")

            # Display answer information
            if isinstance(first_q.answer_schema, dict):
                context.console.print("  Answer Schema:")
                if "correct_key" in first_q.answer_schema:
                    context.console.print(f"    Correct Answer: {first_q.answer_schema['correct_key']}")
                if "correct_keywords" in first_q.answer_schema:
                    context.console.print(f"    Keywords: {first_q.answer_schema['correct_keywords']}")
                if "validation_score" in first_q.answer_schema:
                    context.console.print(f"    Validation Score: {first_q.answer_schema['validation_score']:.2f}")
                if "explanation" in first_q.answer_schema:
                    context.console.print(f"    Explanation: {first_q.answer_schema['explanation']}")
            context.console.print()

    except Exception as e:
        context.console.print("[bold red]✗ Error retrieving questions[/bold red]")
        context.console.print(f"[red]  {str(e)}[/red]")
        context.logger.error(f"Error retrieving questions for session {session_id}: {e}", exc_info=True)
    finally:
        if db_session:
            db_session.close()


def resume_session(context: CLIContext, *args: str) -> None:
    """테스트 세션을 재개합니다."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        context.console.print("[yellow]Please login first: auth login [username][/yellow]")
        return

    context.console.print("[dim]Resuming test session...[/dim]")

    # API 호출
    status_code, response, error = context.client.make_request("GET", "/questions/resume")

    if error:
        context.console.print("[bold red]✗ Resume failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        context.logger.error(f"Session resume failed: {error}")
        return

    if status_code != 200:
        context.console.print(f"[bold red]✗ Resume failed (HTTP {status_code})[/bold red]")
        return

    session_id = response.get("session_id")
    questions_count = response.get("questions_count", 0)
    context.session.current_session_id = session_id

    context.console.print("[bold green]✓ Test session resumed[/bold green]")
    context.console.print(f"[dim]  Session ID: {session_id}[/dim]")
    context.console.print(f"[dim]  Questions: {questions_count}[/dim]")
    context.logger.info("Test session resumed.")


def update_session_status(context: CLIContext, *args: str) -> None:
    """세션 상태를 변경합니다 (일시중지/재개)."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        return

    if not context.session.current_session_id:
        context.console.print("[bold red]✗ No active session[/bold red]")
        return

    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] questions session status [pause|resume]")
        context.console.print("[bold cyan]Example:[/bold cyan] questions session status pause")
        return

    new_status = args[0]
    context.console.print(f"[dim]Updating session status to '{new_status}'...[/dim]")

    # API 호출
    status_code, response, error = context.client.make_request(
        "PUT",
        f"/questions/session/{context.session.current_session_id}/status",
        json_data={"status": new_status},
    )

    if error:
        context.console.print("[bold red]✗ Update failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        return

    if status_code not in (200, 201):
        context.console.print(f"[bold red]✗ Update failed (HTTP {status_code})[/bold red]")
        return

    context.console.print(f"[bold green]✓ Session status changed to '{new_status}'[/bold green]")
    context.logger.info(f"Session status updated to: {new_status}.")


def check_time_status(context: CLIContext, *args: str) -> None:
    """세션 시간 제한을 확인합니다."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        return

    if not context.session.current_session_id:
        context.console.print("[bold red]✗ No active session[/bold red]")
        return

    context.console.print("[dim]Checking time status...[/dim]")

    # API 호출
    status_code, response, error = context.client.make_request(
        "GET",
        f"/questions/session/{context.session.current_session_id}/time-status",
    )

    if error:
        context.console.print("[bold red]✗ Check failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        return

    if status_code != 200:
        context.console.print(f"[bold red]✗ Check failed (HTTP {status_code})[/bold red]")
        return

    elapsed = response.get("elapsed_seconds", 0)
    remaining = response.get("remaining_seconds", 0)
    is_expired = response.get("is_expired", False)

    context.console.print("[bold green]✓ Time status checked[/bold green]")
    context.console.print(f"[dim]  Elapsed: {elapsed}s | Remaining: {remaining}s[/dim]")
    if is_expired:
        context.console.print("[bold red]  ⚠️  Time limit exceeded![/bold red]")
    context.logger.info("Time status checked.")


def generate_questions(context: CLIContext, *args: str) -> None:
    """테스트 문항을 생성합니다 (Round 1)."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        return

    context.console.print("[dim]Generating Round 1 questions...[/dim]")

    # API 호출
    status_code, response, error = context.client.make_request(
        "POST",
        "/questions/generate",
    )

    if error:
        context.console.print("[bold red]✗ Generation failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        return

    if status_code not in (200, 201):
        context.console.print(f"[bold red]✗ Generation failed (HTTP {status_code})[/bold red]")
        return

    session_id = response.get("session_id")
    questions_count = response.get("questions_count", 0)
    context.session.current_session_id = session_id
    context.session.current_round = 1

    context.console.print("[bold green]✓ Round 1 questions generated[/bold green]")
    context.console.print(f"[dim]  Session: {session_id}[/dim]")
    context.console.print(f"[dim]  Questions: {questions_count}[/dim]")
    context.logger.info("Round 1 questions generated.")


def generate_adaptive_questions(context: CLIContext, *args: str) -> None:
    """적응형 문항을 생성합니다 (Round 2+)."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        return

    if not context.session.current_session_id:
        context.console.print("[bold red]✗ No active session[/bold red]")
        return

    context.console.print("[dim]Generating adaptive questions...[/dim]")

    # API 호출
    status_code, response, error = context.client.make_request(
        "POST",
        "/questions/generate-adaptive",
        json_data={"session_id": context.session.current_session_id},
    )

    if error:
        context.console.print("[bold red]✗ Generation failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        return

    if status_code not in (200, 201):
        context.console.print(f"[bold red]✗ Generation failed (HTTP {status_code})[/bold red]")
        return

    questions_count = response.get("questions_count", 0)
    difficulty = response.get("difficulty_level", "Unknown")
    context.session.current_round = 2

    context.console.print("[bold green]✓ Adaptive questions generated[/bold green]")
    context.console.print(f"[dim]  Questions: {questions_count}[/dim]")
    context.console.print(f"[dim]  Difficulty: {difficulty}[/dim]")
    context.logger.info("Adaptive questions generated.")


def autosave_answer(context: CLIContext, *args: str) -> None:
    """답변을 자동 저장합니다."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        return

    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] questions answer autosave [question_id] [answer]")
        context.console.print("[bold cyan]Example:[/bold cyan] questions answer autosave q1 'my answer'")
        return

    question_id = args[0]
    answer = " ".join(args[1:]) if len(args) > 1 else ""

    context.console.print("[dim]Autosaving answer...[/dim]")

    # API 호출
    status_code, response, error = context.client.make_request(
        "POST",
        "/questions/autosave",
        json_data={
            "question_id": question_id,
            "answer": answer,
        },
    )

    if error:
        context.console.print("[bold red]✗ Autosave failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        return

    if status_code not in (200, 201):
        context.console.print(f"[bold red]✗ Autosave failed (HTTP {status_code})[/bold red]")
        return

    context.console.print("[bold green]✓ Answer autosaved[/bold green]")
    context.logger.info(f"Answer autosaved for question {question_id}.")


def score_answer(context: CLIContext, *args: str) -> None:
    """단일 답변을 채점합니다."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        return

    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] questions answer score [question_id] [answer]")
        context.console.print("[bold cyan]Example:[/bold cyan] questions answer score q1 'my answer'")
        return

    question_id = args[0]
    answer = " ".join(args[1:]) if len(args) > 1 else ""

    context.console.print("[dim]Scoring answer...[/dim]")

    # API 호출
    status_code, response, error = context.client.make_request(
        "POST",
        "/questions/answer/score",
        json_data={
            "question_id": question_id,
            "answer": answer,
        },
    )

    if error:
        context.console.print("[bold red]✗ Scoring failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        return

    if status_code not in (200, 201):
        context.console.print(f"[bold red]✗ Scoring failed (HTTP {status_code})[/bold red]")
        return

    score = response.get("score", 0)
    is_correct = response.get("is_correct", False)

    context.console.print(f"[bold green]✓ Answer scored: {score}%[/bold green]")
    if is_correct:
        context.console.print("[dim]  ✓ Correct[/dim]")
    else:
        context.console.print("[dim]  ✗ Incorrect[/dim]")
    context.logger.info(f"Answer scored: {score}% for question {question_id}.")


def calculate_round_score(context: CLIContext, *args: str) -> None:
    """라운드 점수를 계산하고 저장합니다."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        return

    context.console.print("[dim]Calculating round score...[/dim]")

    # API 호출
    status_code, response, error = context.client.make_request(
        "POST",
        "/questions/score",
    )

    if error:
        context.console.print("[bold red]✗ Calculation failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        return

    if status_code not in (200, 201):
        context.console.print(f"[bold red]✗ Calculation failed (HTTP {status_code})[/bold red]")
        return

    total_score = response.get("total_score", 0)
    correct_count = response.get("correct_count", 0)
    total_count = response.get("total_count", 0)

    context.console.print("[bold green]✓ Round score calculated[/bold green]")
    context.console.print(f"[dim]  Total: {total_score}/100[/dim]")
    context.console.print(f"[dim]  Correct: {correct_count}/{total_count}[/dim]")
    context.logger.info("Round score calculated and saved.")


def generate_explanation(context: CLIContext, *args: str) -> None:
    """해설을 생성합니다."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        return

    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] questions explanation generate [question_id]")
        context.console.print("[bold cyan]Example:[/bold cyan] questions explanation generate q1")
        return

    question_id = args[0]
    context.console.print("[dim]Generating explanation...[/dim]")

    # API 호출
    status_code, response, error = context.client.make_request(
        "POST",
        "/questions/explanations",
        json_data={"question_id": question_id},
    )

    if error:
        context.console.print("[bold red]✗ Generation failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        return

    if status_code not in (200, 201):
        context.console.print(f"[bold red]✗ Generation failed (HTTP {status_code})[/bold red]")
        return

    explanation = response.get("explanation", "")

    context.console.print("[bold green]✓ Explanation generated[/bold green]")
    if explanation:
        context.console.print(f"[dim]{explanation[:100]}...[/dim]")
    context.logger.info(f"Explanation generated for question {question_id}.")
