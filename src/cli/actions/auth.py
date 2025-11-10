"""Authentication-related CLI actions."""

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
    context.console.print(f"[dim]Logging in as '{username}'...[/dim]")

    # API 호출
    status_code, response, error = context.client.make_request(
        "POST",
        "/auth/login",
        json_data={
            "knox_id": username,
            "name": username,
            "email": f"{username}@samsung.com",
            "dept": "Engineering",
            "business_unit": "S.LSI",
        },
    )

    if error:
        context.console.print("[bold red]✗ Login failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        context.logger.error(f"Login failed for user '{username}': {error}")
        return

    if status_code not in (200, 201):
        context.console.print(f"[bold red]✗ Login failed (HTTP {status_code})[/bold red]")
        context.logger.error(f"Login failed with status {status_code}")
        return

    # 응답 처리
    token = response.get("access_token")
    is_new_user = response.get("is_new_user", False)

    if not token:
        context.console.print("[bold red]✗ No token in response[/bold red]")
        return

    # 세션 상태 저장
    context.client.set_token(token)
    context.session.token = token
    context.session.username = username
    context.session.user_id = response.get("user_id")

    # 결과 출력
    context.console.print(f"[bold green]✓ Successfully logged in as '{username}'[/bold green]")
    context.console.print(f"[dim]  Status: {'New user' if is_new_user else 'Returning user'}[/dim]")
    context.console.print(f"[dim]  User ID: {context.session.user_id}[/dim]")
    context.console.print(f"[dim]  Token (first 20 chars): {token[:20]}...[/dim]")
    context.logger.info(f"User '{username}' logged in successfully.")
