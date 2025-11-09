# src/cli/actions/auth.py
from src.cli.context import CLIContext


def auth_help(context: CLIContext, *args: str) -> None:
    """Auth 도메인의 사용 가능한 명령어를 보여줍니다."""
    context.console.print("[bold yellow]Auth Commands:[/bold yellow]")
    context.console.print("  auth login - Samsung AD 로그인 (JWT 토큰 발급)")


def login(context: CLIContext, *args: str) -> None:
    """Samsung AD 로그인을 처리합니다."""
    context.console.print(f"[bold green]Executing: login with args: {args}[/bold green]")
    context.logger.info(f"Ran login action with args: {args}.")
    # TODO: 실제 로그인 로직 구현
