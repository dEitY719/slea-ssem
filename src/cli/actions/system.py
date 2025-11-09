# src/cli/actions/system.py
import os
from src.cli.context import CLIContext


def help(context: CLIContext, *args: str) -> None:
    """사용 가능한 명령어 목록을 보여줍니다."""
    context.console.print("[bold yellow]Available commands:[/bold yellow]")
    context.console.print("  auth login")
    context.console.print("  survey schema")
    context.console.print("  survey submit")
    context.console.print("  profile nickname check")
    context.console.print("  profile nickname register")
    context.console.print("  profile nickname edit")
    context.console.print("  profile update_survey")
    context.console.print("  questions session resume")
    context.console.print("  questions session status")
    context.console.print("  questions session time_status")
    context.console.print("  questions generate")
    context.console.print("  questions generate adaptive")
    context.console.print("  questions answer autosave")
    context.console.print("  questions answer score")
    context.console.print("  questions score")
    context.console.print("  questions explanation generate")
    context.console.print("  help")
    context.console.print("  clear")
    context.console.print("  exit")


def clear(context: CLIContext, *args: str) -> None:
    """터미널 화면을 정리하고 시작 메시지를 표시합니다."""
    # Clear terminal screen
    os.system("clear" if os.name == "posix" else "cls")
    # Show welcome message again
    context.console.print("[bold green]Welcome to the SLEA-SSEM CLI![/bold green]")
    context.console.print("[bold yellow]Type 'help' for a list of commands, or 'exit' to quit.[/bold yellow]")


def exit_cli(context: CLIContext, *args: str) -> None:
    """CLI를 종료합니다."""
    # 이 함수는 main.py의 루프를 중단시키는 용도로, 직접 호출되기보다는
    # 'exit' 명령어에 대한 트리거로 사용됩니다.
    context.console.print("Exiting CLI...")

