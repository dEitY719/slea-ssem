# src/cli/actions/survey.py
from src.cli.context import CLIContext


def survey_help(context: CLIContext, *args: str) -> None:
    """Survey 도메인의 사용 가능한 명령어를 보여줍니다."""
    context.console.print("[bold yellow]Survey Commands:[/bold yellow]")
    context.console.print("  survey schema     - Survey 폼 스키마 조회")
    context.console.print("  survey submit     - Survey 데이터 제출 및 저장")


def get_survey_schema(context: CLIContext, *args: str) -> None:
    """Survey 폼 스키마를 조회합니다."""
    context.console.print("[bold green]✓ Survey schema retrieved successfully[/bold green]")
    context.console.print("[dim]  Field 1: 직급 (required)[/dim]")
    context.console.print("[dim]  Field 2: 경력 (optional)[/dim]")
    context.console.print("[dim]  Field 3: 관심사 (optional)[/dim]")
    context.logger.info("Survey schema retrieved.")


def submit_survey(context: CLIContext, *args: str) -> None:
    """Survey 데이터를 제출합니다."""
    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] survey submit [data]")
        context.console.print("[bold cyan]Example:[/bold cyan] survey submit '직급:Manager,경력:5years'")
        return

    context.console.print("[bold green]✓ Survey submitted successfully[/bold green]")
    context.console.print(f"[dim]  Data: {' '.join(args)}[/dim]")
    context.logger.info(f"Survey submitted with data: {args}.")
