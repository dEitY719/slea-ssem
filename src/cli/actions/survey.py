# src/cli/actions/survey.py
from src.cli.context import CLIContext


def survey_help(context: CLIContext, *args) -> None:
    """Survey 도메인의 사용 가능한 명령어를 보여줍니다."""
    context.console.print("[bold yellow]Survey Commands:[/bold yellow]")
    context.console.print("  survey schema     - Survey 폼 스키마 조회")
    context.console.print("  survey submit     - Survey 데이터 제출 및 저장")


def get_survey_schema(context: CLIContext, *args) -> None:
    """Survey 폼 스키마를 조회합니다."""
    context.console.print(f"[bold green]Executing: get_survey_schema with args: {args}[/bold green]")
    context.logger.info(f"Ran get_survey_schema action with args: {args}.")
    # TODO: 실제 스키마 조회 로직 구현


def submit_survey(context: CLIContext, *args) -> None:
    """Survey 데이터를 제출합니다."""
    context.console.print(f"[bold green]Executing: submit_survey with args: {args}[/bold green]")
    context.logger.info(f"Ran submit_survey action with args: {args}.")
    # TODO: 실제 데이터 제출 로직 구현
