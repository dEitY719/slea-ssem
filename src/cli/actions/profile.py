"""Profile-related CLI actions."""

from src.cli.context import CLIContext


def profile_help(context: CLIContext, *args: str) -> None:
    """Profile 도메인의 사용 가능한 명령어를 보여줍니다."""
    context.console.print("[bold yellow]Profile Commands:[/bold yellow]")
    context.console.print("  profile nickname check        - 닉네임 중복 확인 (인증 불필요)")
    context.console.print("  profile nickname view         - 닉네임 조회 (인증 필요)")
    context.console.print("  profile nickname register     - 닉네임 등록 (인증 필요)")
    context.console.print("  profile nickname edit         - 닉네임 수정 (인증 필요)")
    context.console.print("  profile update_survey         - Survey 업데이트 (인증 필요, 새 프로필 레코드 생성)")


def check_nickname_availability(context: CLIContext, *args: str) -> None:
    """닉네임 중복 가능 여부를 확인합니다."""
    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] profile nickname check [nickname]")
        context.console.print("[bold cyan]Example:[/bold cyan] profile nickname check myname")
        return

    nickname = args[0]
    context.console.print("[dim]Checking nickname availability...[/dim]")

    # API 호출
    status_code, response, error = context.client.make_request(
        "POST",
        "/profile/nickname/check",
        json_data={"nickname": nickname},
    )

    if error:
        context.console.print("[bold red]✗ Check failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        context.logger.error(f"Nickname check failed: {error}")
        return

    if status_code not in (200, 201):
        context.console.print(f"[bold red]✗ Check failed (HTTP {status_code})[/bold red]")
        return

    is_available = response.get("available", False)
    if is_available:
        context.console.print(f"[bold green]✓ Nickname '{nickname}' is available[/bold green]")
    else:
        suggestions = response.get("suggestions", [])
        context.console.print(f"[bold red]✗ Nickname '{nickname}' is not available[/bold red]")
        if suggestions:
            context.console.print("[dim]  Suggestions:[/dim]")
            for suggestion in suggestions:
                context.console.print(f"[dim]    - {suggestion}[/dim]")
    context.logger.info(f"Checked nickname availability for: {nickname}.")


def view_nickname(context: CLIContext, *args: str) -> None:
    """현재 사용자의 닉네임 정보를 조회합니다."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        context.console.print("[yellow]Please login first: auth login [username][/yellow]")
        return

    context.console.print("[dim]Fetching nickname information...[/dim]")

    # JWT 토큰을 client에 설정
    context.client.set_token(context.session.token)

    # API 호출
    status_code, response, error = context.client.make_request(
        "GET",
        "/profile/nickname",
    )

    if error:
        context.console.print("[bold red]✗ Failed to fetch nickname[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        context.logger.error(f"Nickname fetch failed: {error}")
        return

    if status_code != 200:
        context.console.print(f"[bold red]✗ Failed (HTTP {status_code})[/bold red]")
        return

    nickname = response.get("nickname")
    registered_at = response.get("registered_at")
    updated_at = response.get("updated_at")

    if nickname:
        context.console.print(f"[bold green]✓ Nickname:[/bold green] {nickname}")
        if registered_at:
            context.console.print(f"[dim]  Registered: {registered_at}[/dim]")
        if updated_at:
            context.console.print(f"[dim]  Updated: {updated_at}[/dim]")
    else:
        context.console.print("[bold yellow]✓ No nickname set yet[/bold yellow]")
    context.logger.info("Fetched nickname information.")


def register_nickname(context: CLIContext, *args: str) -> None:
    """닉네임을 등록합니다."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        context.console.print("[yellow]Please login first: auth login [username][/yellow]")
        return

    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] profile nickname register [nickname]")
        context.console.print("[bold cyan]Example:[/bold cyan] profile nickname register myname")
        return

    nickname = args[0]
    context.console.print(f"[dim]Registering nickname '{nickname}'...[/dim]")

    # JWT 토큰을 client에 설정
    context.client.set_token(context.session.token)

    # API 호출
    status_code, response, error = context.client.make_request(
        "POST",
        "/profile/register",
        json_data={"nickname": nickname},
    )

    if error:
        context.console.print("[bold red]✗ Registration failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        context.logger.error(f"Nickname registration failed: {error}")
        return

    if status_code not in (200, 201):
        context.console.print(f"[bold red]✗ Registration failed (HTTP {status_code})[/bold red]")
        return

    context.console.print(f"[bold green]✓ Nickname '{nickname}' registered[/bold green]")
    context.logger.info(f"Registered nickname: {nickname}.")


def edit_nickname(context: CLIContext, *args: str) -> None:
    """닉네임을 수정합니다."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        context.console.print("[yellow]Please login first: auth login [username][/yellow]")
        return

    if len(args) < 1:
        context.console.print("[bold yellow]Usage:[/bold yellow] profile nickname edit [new_nickname]")
        context.console.print("[bold cyan]Example:[/bold cyan] profile nickname edit newname")
        return

    new_nickname = args[0]
    context.console.print(f"[dim]Updating nickname to '{new_nickname}'...[/dim]")

    # JWT 토큰을 client에 설정
    context.client.set_token(context.session.token)

    # API 호출
    status_code, response, error = context.client.make_request(
        "PUT",
        "/profile/nickname",
        json_data={"nickname": new_nickname},
    )

    if error:
        context.console.print("[bold red]✗ Update failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        context.logger.error(f"Nickname update failed: {error}")
        return

    if status_code not in (200, 201):
        context.console.print(f"[bold red]✗ Update failed (HTTP {status_code})[/bold red]")
        return

    context.console.print(f"[bold green]✓ Nickname updated to '{new_nickname}'[/bold green]")
    context.logger.info(f"Nickname changed to {new_nickname}.")


def update_survey(context: CLIContext, *args: str) -> None:
    """Survey를 업데이트하여 새 프로필 레코드를 생성합니다."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        context.console.print("[yellow]Please login first: auth login [username][/yellow]")
        return

    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] profile update_survey [level] [career] [interests]")
        context.console.print("[bold cyan]Example:[/bold cyan] profile update_survey 'intermediate' '5years' 'AI,ML'")
        return

    level = args[0] if len(args) > 0 else ""
    career = args[1] if len(args) > 1 else ""
    interests = args[2] if len(args) > 2 else ""

    context.console.print("[dim]Updating survey...[/dim]")

    # JWT 토큰을 client에 설정
    context.client.set_token(context.session.token)

    # API 호출
    status_code, response, error = context.client.make_request(
        "PUT",
        "/profile/survey",
        json_data={
            "level": level,
            "career": career,
            "interests": interests,
        },
    )

    if error:
        context.console.print("[bold red]✗ Update failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        context.logger.error(f"Survey update failed: {error}")
        return

    if status_code not in (200, 201):
        context.console.print(f"[bold red]✗ Update failed (HTTP {status_code})[/bold red]")
        return

    context.console.print("[bold green]✓ Profile survey updated[/bold green]")
    context.console.print("[dim]  New profile record created[/dim]")
    context.logger.info(f"Survey updated: level={level}, career={career}, interests={interests}.")
