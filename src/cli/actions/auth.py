"""Authentication-related CLI actions."""

from src.cli.context import CLIContext


def auth_help(context: CLIContext, *args: str) -> None:
    """Auth 도메인의 사용 가능한 명령어를 보여줍니다."""
    context.console.print("[bold yellow]Auth Commands:[/bold yellow]")
    context.console.print("  auth login [username] - Samsung AD 로그인 (JWT 토큰 발급)")
    context.console.print("  auth oidc-callback [code] [code_verifier] - OIDC 콜백 (Azure AD 인증, JWT 쿠키 발급)")


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
    token_length = len(token)
    token_display = f"{token[:8]}...{token[-8:]}"
    context.console.print(f"[dim]  Token (Total {token_length} chars): {token_display}[/dim]")
    context.logger.info(f"User '{username}' logged in successfully.")


def oidc_callback(context: CLIContext, *args: str) -> None:
    """OIDC 콜백을 처리합니다 (Azure AD 인증)."""
    if len(args) < 2:
        context.console.print("[bold yellow]Usage:[/bold yellow] auth oidc-callback [code] [code_verifier]")
        context.console.print("[bold cyan]Example:[/bold cyan] auth oidc-callback M.R3_BAY.test_code test_verifier")
        return

    code = args[0]
    code_verifier = args[1]

    context.console.print(f"[dim]OIDC 콜백 처리 중... (code: {code[:20]}..., verifier: {code_verifier[:20]}...)[/dim]")

    # API 호출
    status_code, response, error = context.client.make_request(
        "POST",
        "/auth/oidc/callback",
        json_data={
            "code": code,
            "code_verifier": code_verifier,
        },
    )

    if error:
        context.console.print("[bold red]✗ OIDC Callback failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        context.logger.error(f"OIDC callback failed: {error}")
        return

    if status_code not in (200, 201):
        context.console.print(f"[bold red]✗ OIDC Callback failed (HTTP {status_code})[/bold red]")
        context.logger.error(f"OIDC callback failed with status {status_code}")
        return

    # 응답 처리
    token = response.get("access_token")
    user_id = response.get("user_id")
    is_new_user = response.get("is_new_user", False)

    if not token:
        context.console.print("[bold red]✗ No token in response[/bold red]")
        return

    # 세션 상태 저장
    context.client.set_token(token)
    context.session.token = token
    context.session.user_id = user_id

    # 결과 출력
    context.console.print("[bold green]✓ OIDC 콜백 성공[/bold green]")
    context.console.print(f"[dim]  Status: {'신규 사용자' if is_new_user else '기존 사용자'}[/dim]")
    context.console.print(f"[dim]  User ID: {user_id}[/dim]")
    token_length = len(token)
    token_display = f"{token[:8]}...{token[-8:]}"
    context.console.print(f"[dim]  Token (Total {token_length} chars): {token_display}[/dim]")
    context.logger.info(f"OIDC callback successful. User ID: {user_id}, Is new: {is_new_user}")
