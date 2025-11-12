"""Questions and test-related CLI actions."""

import re
from typing import Any

from rich.table import Table

from src.backend.database import SessionLocal
from src.backend.models.attempt_answer import AttemptAnswer
from src.backend.models.question import Question
from src.backend.models.test_session import TestSession
from src.backend.models.user_profile import UserProfileSurvey
from src.cli.context import CLIContext

# ============================================================================
# DB Helper Functions for Latest Data Retrieval
# ============================================================================


def _get_latest_survey(user_id: str | int | None) -> str | None:
    """Get latest survey ID for user from DB."""
    try:
        if not user_id:
            return None

        # Convert to int if string
        user_id_int = int(user_id) if isinstance(user_id, str) else user_id

        db = SessionLocal()
        survey = (
            db.query(UserProfileSurvey)
            .filter_by(user_id=user_id_int)
            .order_by(UserProfileSurvey.submitted_at.desc())
            .first()
        )
        db.close()
        return survey.id if survey else None
    except Exception:
        return None


def _get_latest_session(user_id: str | int | None) -> tuple[str | None, str | None]:
    """
    Get latest session ID and session info from DB.

    Returns: (session_id, session_info_str)
    """
    try:
        if not user_id:
            return None, ""

        # Convert to int if string
        user_id_int = int(user_id) if isinstance(user_id, str) else user_id

        db = SessionLocal()
        session = db.query(TestSession).filter_by(user_id=user_id_int).order_by(TestSession.created_at.desc()).first()
        db.close()
        if session:
            info_str = f"[dim](round {session.round}, {session.status})[/dim]"
            return session.id, info_str
        return None, ""
    except Exception:
        return None, ""


def _get_latest_question(session_id: str | None = None) -> tuple[str | None, str | None, str | None]:
    """
    Get latest question ID, info, and its actual session_id from DB.

    If session_id is provided, gets latest question from that session.
    If session_id has no questions, finds the latest session that has questions.

    Returns: (question_id, question_info_str, actual_session_id)
    """
    try:
        db = SessionLocal()

        # Try to get from specified session first
        if session_id:
            question = db.query(Question).filter_by(session_id=session_id).order_by(Question.id.desc()).first()
            if question:
                db.close()
                info_str = f"[dim]({question.item_type}, {question.stem[:40]}...)[/dim]"
                return question.id, info_str, question.session_id

            # If no questions in specified session, try to find a session with questions
            # Get sessions ordered by created_at descending, and find one with questions

            session_with_q = (
                db.query(TestSession)
                .join(Question, TestSession.id == Question.session_id)
                .order_by(TestSession.created_at.desc())
                .first()
            )
            if session_with_q:
                question = (
                    db.query(Question).filter_by(session_id=session_with_q.id).order_by(Question.id.desc()).first()
                )
                if question:
                    db.close()
                    info_str = f"[dim]({question.item_type}, {question.stem[:40]}...)[/dim]"
                    return question.id, info_str, question.session_id
        else:
            # Get latest question from any session
            question = db.query(Question).order_by(Question.id.desc()).first()
            if question:
                db.close()
                info_str = f"[dim]({question.item_type}, {question.stem[:40]}...)[/dim]"
                return question.id, info_str, question.session_id

        db.close()
        return None, "", None
    except Exception:
        return None, "", None


def _get_unscored_answers(session_id: str | None) -> list[dict[str, Any]]:
    """
    Get all unscored attempt answers from a session.

    Returns list of dicts with keys: id, question_id, user_answer, session_id
    """
    try:
        if not session_id:
            return []

        db = SessionLocal()
        # Query attempt_answers where score is 0 (unscored) or NULL
        unscored = (
            db.query(AttemptAnswer)
            .filter_by(session_id=session_id)
            .filter((AttemptAnswer.score == 0.0) | (AttemptAnswer.score.is_(None)))
            .order_by(AttemptAnswer.created_at.asc())
            .all()
        )
        db.close()

        result = []
        for answer in unscored:
            result.append(
                {
                    "id": answer.id,
                    "question_id": answer.question_id,
                    "user_answer": answer.user_answer,
                    "session_id": answer.session_id,
                }
            )
        return result
    except Exception:
        return []


def _get_question_type(question_id: str | None) -> str | None:
    """
    Get question type from database.

    Returns: item_type (e.g., 'multiple_choice', 'true_false', 'short_answer')
    """
    try:
        if not question_id:
            return None

        db = SessionLocal()
        question = db.query(Question).filter_by(id=question_id).first()
        db.close()

        return question.item_type if question else None
    except Exception:
        return None


def _format_user_answer(user_answer: str, question_type: str | None) -> dict[str, Any]:
    """
    Format user answer dict based on question type.

    Args:
        user_answer: Raw answer text from user
        question_type: Type of question (multiple_choice, true_false, short_answer)

    Returns:
        Properly formatted user_answer dict with correct field name

    """
    # If we don't know the type, default to short answer format (most permissive)
    if not question_type:
        return {"text": user_answer}

    question_type_lower = question_type.lower()

    # Multiple choice: use selected_key for the choice
    if "multiple" in question_type_lower or "choice" in question_type_lower:
        return {"selected_key": user_answer}

    # True/False: convert to boolean if possible, otherwise keep as string
    if "true" in question_type_lower or "false" in question_type_lower:
        if user_answer.lower() in ("true", "yes", "1", "y"):
            return {"answer": True}
        elif user_answer.lower() in ("false", "no", "0", "n"):
            return {"answer": False}
        else:
            # If unclear, store as-is (backend will handle)
            return {"answer": user_answer}

    # Short answer: use text field
    return {"text": user_answer}


# ============================================================================
# Help Functions
# ============================================================================


def _print_generate_questions_help(context: CLIContext) -> None:
    """Print help for questions generate command."""
    context.console.print()
    context.console.print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    context.console.print("║  questions generate - Generate Test Questions (Round 1)                     ║")
    context.console.print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    context.console.print()
    context.console.print("[bold cyan]Usage:[/bold cyan]")
    context.console.print("  questions generate [--survey-id ID] [--domain DOMAIN] [--round 1|2]")
    context.console.print()
    context.console.print("[bold cyan]Options:[/bold cyan]")
    context.console.print("  --survey-id TEXT   Survey ID (auto-uses latest if not provided)")
    context.console.print("  --domain TEXT      Question domain: AI, food, science, etc.")
    context.console.print("                     Default: AI")
    context.console.print("  --round INTEGER    Round number: 1 (initial) or 2 (adaptive)")
    context.console.print("                     Default: 1")
    context.console.print("  --help             Show this help message")
    context.console.print()
    context.console.print("[bold cyan]Examples:[/bold cyan]")
    context.console.print("  # Generate Round 1 with default AI domain, using latest survey")
    context.console.print("  questions generate")
    context.console.print()
    context.console.print("  # Generate with specific domain")
    context.console.print("  questions generate --domain food")
    context.console.print()
    context.console.print("  # Generate with specific survey and domain")
    context.console.print("  questions generate --survey-id survey_abc --domain science")
    context.console.print()
    context.console.print("  # Show this help message")
    context.console.print("  questions generate --help")
    context.console.print()


def _print_autosave_answer_help(context: CLIContext) -> None:
    """Print help for questions answer autosave command."""
    context.console.print()
    context.console.print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    context.console.print("║  questions answer autosave - Auto-save Answer                               ║")
    context.console.print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    context.console.print()
    context.console.print("[bold cyan]Usage:[/bold cyan]")
    context.console.print("  questions answer autosave [--session-id ID] [--question-id ID] [--answer TEXT]")
    context.console.print()
    context.console.print("[bold cyan]Options:[/bold cyan]")
    context.console.print("  --session-id ID     Session ID (auto-uses latest if not provided)")
    context.console.print("  --question-id ID    Question ID (auto-uses latest if not provided)")
    context.console.print("  --answer TEXT       Answer text (required)")
    context.console.print("  --help              Show this help message")
    context.console.print()
    context.console.print("[bold cyan]Examples:[/bold cyan]")
    context.console.print("  # Auto-save using latest session and question from DB")
    context.console.print("  questions answer autosave --answer 'A'")
    context.console.print()
    context.console.print("  # Auto-save with specific question ID, latest session")
    context.console.print("  questions answer autosave --question-id q_abc --answer 'keyword1'")
    context.console.print()
    context.console.print("  # Auto-save with all parameters")
    context.console.print("  questions answer autosave --session-id s_xyz --question-id q_abc --answer 'my answer'")
    context.console.print()
    context.console.print("  # Show this help message")
    context.console.print("  questions answer autosave --help")
    context.console.print()


def _print_score_answer_help(context: CLIContext) -> None:
    """Print help for questions answer score command."""
    context.console.print()
    context.console.print("╔═══════════════════════════════════════════════════════════════════════════════╗")
    context.console.print("║  questions answer score - Score Answers (Single or Batch)                   ║")
    context.console.print("╚═══════════════════════════════════════════════════════════════════════════════╝")
    context.console.print()
    context.console.print("[bold cyan]Usage:[/bold cyan]")
    context.console.print("  questions answer score [--help]")
    context.console.print("  # Auto-batch score all unscored answers from latest session, then calculate round score")
    context.console.print()
    context.console.print("[bold cyan]Mode 1: Auto-Batch Scoring (Default)[/bold cyan]")
    context.console.print("  When run with no arguments:")
    context.console.print("  1. Detects all unscored answers in latest session")
    context.console.print("  2. Scores each answer using agent (Tool 6)")
    context.console.print("  3. Saves scores to database")
    context.console.print("  4. Calculates and saves round score")
    context.console.print()
    context.console.print("[bold cyan]Options:[/bold cyan]")
    context.console.print("  --help    Show this help message")
    context.console.print()
    context.console.print("[bold cyan]Examples:[/bold cyan]")
    context.console.print("  # Auto-batch score all unscored answers from latest session")
    context.console.print("  questions answer score")
    context.console.print()
    context.console.print("  # Show this help message")
    context.console.print("  questions answer score --help")
    context.console.print()


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
    # Check for help first
    if args and args[0] == "help":
        _print_generate_questions_help(context)
        return

    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        return

    # Parse arguments with flags
    survey_id = None
    domain = "AI"  # Default domain
    round_num = 1  # Default round

    i = 0
    while i < len(args):
        if args[i] == "--survey-id" and i + 1 < len(args):
            survey_id = args[i + 1]
            i += 2
        elif args[i] == "--domain" and i + 1 < len(args):
            domain = args[i + 1]
            i += 2
        elif args[i] == "--round" and i + 1 < len(args):
            try:
                round_num = int(args[i + 1])
            except ValueError:
                context.console.print(f"[yellow]⚠ Invalid round number: {args[i + 1]}. Using default: 1[/yellow]")
            i += 2
        elif args[i] == "--help":
            _print_generate_questions_help(context)
            return
        else:
            i += 1

    # Auto-detect survey_id from DB if not provided
    if not survey_id:
        if not context.session.user_id:
            context.console.print("[bold yellow]⚠ Cannot auto-detect survey. Please specify --survey-id[/bold yellow]")
            _print_generate_questions_help(context)
            return

        survey_id = _get_latest_survey(context.session.user_id)

        if not survey_id:
            context.console.print("[bold yellow]⚠ No survey found in DB. Please create a survey first.[/bold yellow]")
            return

        context.console.print(f"[dim]Using latest survey from DB: {survey_id}[/dim]")

    context.console.print(f"[dim]Generating Round {round_num} questions ({domain})...[/dim]")

    # API 호출
    status_code, response, error = context.client.make_request(
        "POST",
        "/questions/generate",
        json_data={
            "survey_id": survey_id,
            "domain": domain,
            "round": round_num,
        },
    )

    if error:
        context.console.print("[bold red]✗ Generation failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        return

    if status_code not in (200, 201):
        context.console.print(f"[bold red]✗ Generation failed (HTTP {status_code})[/bold red]")
        if isinstance(response, dict) and "detail" in response:
            context.console.print(f"[red]  {response['detail']}[/red]")
        return

    session_id = response.get("session_id")
    questions_count = response.get("questions_count", 0)
    context.session.current_session_id = session_id
    context.session.current_round = round_num

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
    # Check for help first
    if args and args[0] == "help":
        _print_autosave_answer_help(context)
        return

    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        return

    # Parse arguments with flags
    session_id = None
    question_id = None
    user_answer = None

    i = 0
    while i < len(args):
        if args[i] == "--session-id" and i + 1 < len(args):
            session_id = args[i + 1]
            i += 2
        elif args[i] == "--question-id" and i + 1 < len(args):
            question_id = args[i + 1]
            i += 2
        elif args[i] == "--answer" and i + 1 < len(args):
            user_answer = args[i + 1]
            i += 2
        elif args[i] == "--help":
            _print_autosave_answer_help(context)
            return
        else:
            i += 1

    # Auto-detect session_id from DB if not provided
    if not session_id:
        if not context.session.user_id:
            context.console.print(
                "[bold yellow]⚠ Cannot auto-detect session. Please specify --session-id[/bold yellow]"
            )
            _print_autosave_answer_help(context)
            return

        session_id, session_info = _get_latest_session(context.session.user_id)
        if not session_id:
            context.console.print(
                "[bold yellow]⚠ No session found in DB. Please run 'questions generate' first.[/bold yellow]"
            )
            return

        context.console.print(f"[dim]Using latest session from DB: {session_id} {session_info}[/dim]")

    # Auto-detect question_id from DB if not provided
    if not question_id:
        # Get latest question from the detected session (or find one with questions)
        question_id, question_info, actual_session_id = _get_latest_question(session_id)
        if not question_id:
            context.console.print("[bold yellow]⚠ No questions found in DB.[/bold yellow]")
            context.console.print(
                "[yellow]Tip: Use 'questions generate --survey-id <id> --domain <domain>' to generate questions[/yellow]"
            )
            return

        # Use the actual session_id from the question's session (may be different from the latest session)
        if actual_session_id and actual_session_id != session_id:
            context.console.print(f"[dim]Using latest question from DB: {question_info}[/dim]")
            context.console.print(
                "[dim](note: question belongs to a different session, using that session for autosave)[/dim]"
            )
            session_id = actual_session_id
        else:
            context.console.print(f"[dim]Using latest question from DB: {question_info}[/dim]")

    # Require answer text
    if not user_answer:
        context.console.print("[bold red]✗ Answer text is required[/bold red]")
        _print_autosave_answer_help(context)
        return

    # Get question type to format answer correctly
    question_type = _get_question_type(question_id)
    formatted_answer = _format_user_answer(user_answer, question_type)

    context.console.print(f"[dim]Autosaving answer for question {question_id}...[/dim]")
    if question_type:
        context.console.print(f"[dim](type: {question_type})[/dim]")

    # API 호출
    status_code, response, error = context.client.make_request(
        "POST",
        "/questions/autosave",
        json_data={
            "session_id": session_id,
            "question_id": question_id,
            "user_answer": formatted_answer,  # Properly formatted based on question type
            "response_time_ms": 0,  # CLI에서는 타이밍 측정 안 함, 기본값 0
        },
    )

    if error:
        context.console.print("[bold red]✗ Autosave failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        return

    if status_code not in (200, 201):
        context.console.print(f"[bold red]✗ Autosave failed (HTTP {status_code})[/bold red]")
        if isinstance(response, dict) and "detail" in response:
            context.console.print(f"[red]  {response['detail']}[/red]")
        return

    context.console.print("[bold green]✓ Answer autosaved[/bold green]")
    context.logger.info(f"Answer autosaved for question {question_id}.")


def score_answer(context: CLIContext, *args: str) -> None:
    """
    Score answers: auto-batch score unscored attempts from latest session.

    When called with --help: Show usage
    When called with no args: Auto-detect unscored answers from latest session
                              and batch score them using agent (Tool 6)
    """
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        return

    # Check for --help flag
    if args and args[0] == "--help":
        _print_score_answer_help(context)
        return

    # Auto-batch scoring mode: no args provided
    if not args:
        context.console.print("[dim]Starting auto-batch scoring...[/dim]")

        # Get latest session
        session_id, session_info = _get_latest_session(context.session.user_id)
        if not session_id:
            context.console.print("[bold yellow]⚠️  No session found[/bold yellow]")
            return

        context.console.print(f"[cyan]Session: {session_id} {session_info}[/cyan]")

        # Get unscored answers
        unscored_answers = _get_unscored_answers(session_id)
        if not unscored_answers:
            context.console.print("[bold yellow]⚠️  No unscored answers found[/bold yellow]")
            context.console.print("[dim]All answers are already scored.[/dim]")
            return

        context.console.print(f"[cyan]Found {len(unscored_answers)} unscored answer(s)[/cyan]")
        context.console.print()

        # Batch score each answer
        scored_count = 0
        failed_count = 0

        for i, answer_data in enumerate(unscored_answers, 1):
            question_id = answer_data["question_id"]

            context.console.print(f"[dim][{i}/{len(unscored_answers)}] Scoring question {question_id[:12]}...[/dim]")

            # Call agent.score_and_explain (Tool 6) via backend
            # POST /questions/answer/score endpoint
            # Note: answer is already in DB from autosave, only need session_id + question_id
            status_code, response, error = context.client.make_request(
                "POST",
                "/questions/answer/score",
                json_data={
                    "session_id": session_id,
                    "question_id": question_id,
                },
            )

            if error:
                context.console.print(f"[red]  ✗ Error: {error}[/red]")
                failed_count += 1
                continue

            if status_code not in (200, 201):
                context.console.print(f"[red]  ✗ Failed (HTTP {status_code})[/red]")
                failed_count += 1
                continue

            score = response.get("score", 0)
            is_correct = response.get("is_correct", False)
            context.console.print(f"[green]  ✓ Scored: {score}% ({'Correct' if is_correct else 'Incorrect'})[/green]")
            scored_count += 1

        context.console.print()
        context.console.print("[bold cyan]Batch Scoring Summary[/bold cyan]")
        context.console.print(f"[dim]  Scored: {scored_count}/{len(unscored_answers)}[/dim]")
        if failed_count > 0:
            context.console.print(f"[dim]  Failed: {failed_count}[/dim]")

        # Calculate round score
        context.console.print()
        context.console.print("[dim]Calculating round score...[/dim]")
        calculate_round_score(context, session_id)


def calculate_round_score(context: CLIContext, *args: str) -> None:
    """
    Calculate and save test result for completed round.

    Args:
        context: CLI context
        args: Optional session_id as first arg; if not provided, uses latest session

    """
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        return

    # Get session_id: either from args or from latest session
    session_id = None
    if args:
        session_id = args[0]
    else:
        session_id, _ = _get_latest_session(context.session.user_id)

    if not session_id:
        context.console.print("[bold yellow]⚠️  No session found[/bold yellow]")
        return

    context.console.print("[dim]Calculating round score...[/dim]")

    # API call: session_id is passed as query parameter
    status_code, response, error = context.client.make_request(
        "POST",
        "/questions/score",
        params={"session_id": session_id},
    )

    if error:
        context.console.print("[bold red]✗ Calculation failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        return

    if status_code not in (200, 201):
        context.console.print(f"[bold red]✗ Calculation failed (HTTP {status_code})[/bold red]")
        return

    # Response keys from API: score, correct_count, total_count
    score = response.get("score", 0)
    correct_count = response.get("correct_count", 0)
    total_count = response.get("total_count", 0)

    context.console.print("[bold green]✓ Round score calculated[/bold green]")
    context.console.print(f"[dim]  Total: {score}/100[/dim]")
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
