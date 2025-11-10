"""Survey-related CLI actions."""

from src.cli.context import CLIContext


def survey_help(context: CLIContext, *args: str) -> None:
    """Survey 도메인의 사용 가능한 명령어를 보여줍니다."""
    context.console.print("[bold yellow]Survey Commands:[/bold yellow]")
    context.console.print("  survey schema     - Survey 폼 스키마 조회")
    context.console.print("  survey submit     - Survey 데이터 제출 및 저장")


def get_survey_schema(context: CLIContext, *args: str) -> None:
    """Survey 폼 스키마를 조회합니다."""
    context.console.print("[dim]Fetching survey schema...[/dim]")

    # API 호출
    status_code, response, error = context.client.make_request("GET", "/survey/schema")

    if error:
        context.console.print("[bold red]✗ Failed to fetch schema[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        context.logger.error(f"Failed to fetch survey schema: {error}")
        return

    if status_code != 200:
        context.console.print(f"[bold red]✗ Failed (HTTP {status_code})[/bold red]")
        return

    # 응답 처리
    context.console.print("[bold green]✓ Survey schema retrieved[/bold green]")
    schema = response.get("schema", {})
    for field_name, field_info in schema.items():
        required = "[bold]required[/bold]" if field_info.get("required") else ""
        context.console.print(f"[dim]  - {field_name}: {field_info.get('type')} {required}[/dim]")
    context.logger.info("Survey schema retrieved.")


def submit_survey(context: CLIContext, *args: str) -> None:
    """Survey 데이터를 제출합니다."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        context.console.print("[yellow]Please login first: auth login [username][/yellow]")
        return

    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] survey submit [level] [career] [interests]")
        context.console.print("[bold cyan]Example:[/bold cyan] survey submit 'intermediate' '5years' 'AI,ML'")
        return

    level = args[0] if len(args) > 0 else ""
    career = args[1] if len(args) > 1 else ""
    interests = args[2] if len(args) > 2 else ""

    context.console.print("[dim]Submitting survey...[/dim]")

    # API 호출
    status_code, response, error = context.client.make_request(
        "POST",
        "/survey/submit",
        json_data={
            "level": level,
            "career": career,
            "interests": interests,
        },
    )

    if error:
        context.console.print("[bold red]✗ Submission failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        context.logger.error(f"Survey submission failed: {error}")
        return

    if status_code not in (200, 201):
        context.console.print(f"[bold red]✗ Submission failed (HTTP {status_code})[/bold red]")
        return

    context.console.print("[bold green]✓ Survey submitted[/bold green]")
    context.console.print(f"[dim]  Level: {level}[/dim]")
    context.console.print(f"[dim]  Career: {career}[/dim]")
    context.console.print(f"[dim]  Interests: {interests}[/dim]")
    context.logger.info(f"Survey submitted: level={level}, career={career}, interests={interests}")
