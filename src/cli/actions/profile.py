# src/cli/actions/profile.py
from src.cli.context import CLIContext


def profile_help(context: CLIContext, *args) -> None:
    """Profile 도메인의 사용 가능한 명령어를 보여줍니다."""
    context.console.print("[bold yellow]Profile Commands:[/bold yellow]")
    context.console.print("  profile nickname check        - 닉네임 중복 확인")
    context.console.print("  profile nickname register     - 닉네임 등록")
    context.console.print("  profile nickname edit         - 닉네임 수정")
    context.console.print("  profile update_survey         - Survey 업데이트 (새 프로필 레코드 생성)")


def check_nickname_availability(context: CLIContext, *args) -> None:
    """닉네임 중복 가능 여부를 확인합니다."""
    context.console.print(f"[bold green]Executing: check_nickname_availability with args: {args}[/bold green]")
    context.logger.info(f"Ran check_nickname_availability action with args: {args}.")
    # TODO: 실제 닉네임 중복 확인 로직 구현


def register_nickname(context: CLIContext, *args) -> None:
    """닉네임을 등록합니다."""
    context.console.print(f"[bold green]Executing: register_nickname with args: {args}[/bold green]")
    context.logger.info(f"Ran register_nickname action with args: {args}.")
    # TODO: 실제 닉네임 등록 로직 구현


def edit_nickname(context: CLIContext, *args) -> None:
    """닉네임을 수정합니다."""
    context.console.print(f"[bold green]Executing: edit_nickname with args: {args}[/bold green]")
    context.logger.info(f"Ran edit_nickname action with args: {args}.")
    # TODO: 실제 닉네임 수정 로직 구현


def update_survey(context: CLIContext, *args) -> None:
    """Survey를 업데이트하여 새 프로필 레코드를 생성합니다."""
    context.console.print(f"[bold green]Executing: update_survey with args: {args}[/bold green]")
    context.logger.info(f"Ran update_survey action with args: {args}.")
    # TODO: 실제 survey 업데이트 로직 구현

