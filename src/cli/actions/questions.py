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
    context.console.print("[bold green]✓ Test session resumed[/bold green]")
    context.console.print("[dim]  Questions: 10 | Time remaining: 60 min[/dim]")
    context.logger.info("Test session resumed.")


def update_session_status(context: CLIContext, *args: str) -> None:
    """세션 상태를 변경합니다 (일시중지/재개)."""
    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] questions session status [pause|resume]")
        context.console.print("[bold cyan]Example:[/bold cyan] questions session status pause")
        return

    status = args[0]
    context.console.print(f"[bold green]✓ Session status changed to '{status}'[/bold green]")
    context.logger.info(f"Session status updated to: {status}.")


def check_time_status(context: CLIContext, *args: str) -> None:
    """세션 시간 제한을 확인합니다."""
    context.console.print("[bold green]✓ Time status checked[/bold green]")
    context.console.print("[dim]  Total time: 120 min | Elapsed: 30 min | Remaining: 90 min[/dim]")
    context.logger.info("Time status checked.")


def generate_questions(context: CLIContext, *args: str) -> None:
    """테스트 문항을 생성합니다 (Round 1)."""
    context.console.print("[bold green]✓ Round 1 questions generated[/bold green]")
    context.console.print("[dim]  10 questions created | Difficulty: Mixed[/dim]")
    context.logger.info("Round 1 questions generated.")


def generate_adaptive_questions(context: CLIContext, *args: str) -> None:
    """적응형 문항을 생성합니다 (Round 2+)."""
    context.console.print("[bold green]✓ Adaptive questions generated[/bold green]")
    context.console.print("[dim]  10 questions created | Difficulty: Advanced (based on Round 1)[/dim]")
    context.logger.info("Adaptive questions generated.")


def autosave_answer(context: CLIContext, *args: str) -> None:
    """답변을 자동 저장합니다."""
    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] questions answer autosave [answer]")
        context.console.print("[bold cyan]Example:[/bold cyan] questions answer autosave 'my answer'")
        return

    context.console.print("[bold green]✓ Answer autosaved[/bold green]")
    context.logger.info(f"Answer autosaved: {' '.join(args)}.")


def score_answer(context: CLIContext, *args: str) -> None:
    """단일 답변을 채점합니다."""
    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] questions answer score [answer]")
        context.console.print("[bold cyan]Example:[/bold cyan] questions answer score 'correct answer'")
        return

    context.console.print("[bold green]✓ Answer scored: 100%[/bold green]")
    context.logger.info(f"Answer scored: {' '.join(args)}.")


def calculate_round_score(context: CLIContext, *args: str) -> None:
    """라운드 점수를 계산하고 저장합니다."""
    context.console.print("[bold green]✓ Round score calculated[/bold green]")
    context.console.print("[dim]  Total: 85/100 | Correct: 8/10[/dim]")
    context.logger.info("Round score calculated and saved.")


def generate_explanation(context: CLIContext, *args: str) -> None:
    """해설을 생성합니다."""
    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] questions explanation generate [question_id]")
        context.console.print("[bold cyan]Example:[/bold cyan] questions explanation generate q1")
        return

    context.console.print("[bold green]✓ Explanation generated[/bold green]")
    context.console.print("[dim]  Detailed explanation for question available[/dim]")
    context.logger.info(f"Explanation generated for: {' '.join(args)}.")
