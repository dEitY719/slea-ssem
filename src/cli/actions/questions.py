"""Questions and test-related CLI actions."""

from src.cli.context import CLIContext


def questions_help(context: CLIContext, *args: str) -> None:
    """Questions 도메인의 사용 가능한 명령어를 보여줍니다."""
    context.console.print("[bold yellow]Questions Commands:[/bold yellow]")
    context.console.print("  questions session resume      - 테스트 세션 재개")
    context.console.print("  questions session status      - 세션 상태 변경 (일시중지/재개)")
    context.console.print("  questions session time_status - 세션 시간 제한 확인")
    context.console.print("  questions generate            - 테스트 문항 생성 (Round 1)")
    context.console.print("  questions generate adaptive   - 적응형 문항 생성 (Round 2+)")
    context.console.print("  questions answer autosave     - 답변 자동 저장")
    context.console.print("  questions answer score        - 단일 답변 채점")
    context.console.print("  questions score               - 라운드 점수 계산 및 저장")
    context.console.print("  questions explanation generate - 해설 생성")


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
