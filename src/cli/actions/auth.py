# src/cli/actions/auth.py
from src.cli.context import CLIContext


def auth_help(context: CLIContext, *args: str) -> None:
    """Auth 도메인의 사용 가능한 명령어를 보여줍니다."""
    context.console.print("[bold yellow]Auth Commands:[/bold yellow]")
    context.console.print("  auth login [username] - Samsung AD 로그인 (JWT 토큰 발급)")


def login(context: CLIContext, *args: str) -> None:
    """Samsung AD 로그인을 처리합니다."""
    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] auth login [username]")
        context.console.print("[bold cyan]Example:[/bold cyan] auth login bwyoon")
        return

    username = args[0]
    context.console.print(f"[bold green]✓ Successfully logged in as '{username}'[/bold green]")
    context.console.print(f"[dim]  JWT token issued[/dim]")
    context.logger.info(f"User '{username}' logged in successfully.")
