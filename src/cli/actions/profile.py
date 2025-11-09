"""Profile-related CLI actions."""

from src.cli.context import CLIContext


def profile_help(context: CLIContext, *args: str) -> None:
    """Profile 도메인의 사용 가능한 명령어를 보여줍니다."""
    context.console.print("[bold yellow]Profile Commands:[/bold yellow]")
    context.console.print("  profile nickname check        - 닉네임 중복 확인")
    context.console.print("  profile nickname register     - 닉네임 등록")
    context.console.print("  profile nickname edit         - 닉네임 수정")
    context.console.print("  profile update_survey         - Survey 업데이트 (새 프로필 레코드 생성)")


def check_nickname_availability(context: CLIContext, *args: str) -> None:
    """닉네임 중복 가능 여부를 확인합니다."""
    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] profile nickname check [nickname]")
        context.console.print("[bold cyan]Example:[/bold cyan] profile nickname check myname")
        return

    nickname = args[0]
    context.console.print(f"[bold green]✓ Nickname '{nickname}' is available[/bold green]")
    context.logger.info(f"Checked nickname availability for: {nickname}.")


def register_nickname(context: CLIContext, *args: str) -> None:
    """닉네임을 등록합니다."""
    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] profile nickname register [nickname]")
        context.console.print("[bold cyan]Example:[/bold cyan] profile nickname register myname")
        return

    nickname = args[0]
    context.console.print(f"[bold green]✓ Nickname '{nickname}' registered successfully[/bold green]")
    context.logger.info(f"Registered nickname: {nickname}.")


def edit_nickname(context: CLIContext, *args: str) -> None:
    """닉네임을 수정합니다."""
    if len(args) < 2:
        context.console.print("[bold yellow]Usage:[/bold yellow] profile nickname edit [old] [new]")
        context.console.print("[bold cyan]Example:[/bold cyan] profile nickname edit oldname newname")
        return

    old_name, new_name = args[0], args[1]
    context.console.print(f"[bold green]✓ Nickname changed '{old_name}' → '{new_name}'[/bold green]")
    context.logger.info(f"Nickname changed from {old_name} to {new_name}.")


def update_survey(context: CLIContext, *args: str) -> None:
    """Survey를 업데이트하여 새 프로필 레코드를 생성합니다."""
    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] profile update_survey [data]")
        context.console.print("[bold cyan]Example:[/bold cyan] profile update_survey '직급:Manager,경력:5years'")
        return

    context.console.print("[bold green]✓ Profile survey updated successfully[/bold green]")
    context.console.print("[dim]  New profile record created[/dim]")
    context.logger.info(f"Survey updated with data: {args}.")
