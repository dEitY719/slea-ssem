"""Profile-related CLI actions."""

import re

from sqlalchemy import text

from src.backend.database import SessionLocal
from src.cli.context import CLIContext


def profile_help(context: CLIContext, *args: str) -> None:
    """Profile 도메인의 사용 가능한 명령어를 보여줍니다."""
    context.console.print("[bold yellow]Profile Commands:[/bold yellow]")
    context.console.print("  profile nickname check        - 닉네임 중복 확인 (인증 불필요)")
    context.console.print("  profile nickname view         - 닉네임 조회 (인증 필요)")
    context.console.print("  profile nickname register     - 닉네임 등록 (인증 필요)")
    context.console.print("  profile nickname edit         - 닉네임 수정 (인증 필요)")
    context.console.print(
        "  profile update_survey         - Survey 업데이트 (인증 필요, 옵션: job_role, duty, interests)"
    )
    context.console.print("  profile get-survey            - 최근 자기평가 정보 조회 (인증 필요)")
    context.console.print("  profile reset_surveys         - 모든 Survey 기록 강제 삭제 (FK 무시, DEV용)")
    context.console.print("  profile get-consent           - 개인정보 동의 여부 확인 (인증 필요)")
    context.console.print("  profile set-consent           - 개인정보 동의 상태 변경 (인증 필요)")
    context.console.print("  profile get-ranking           - 등급 및 랭킹 조회 (인증 필요)")


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

    if len(args) < 2:
        context.console.print("[bold yellow]Usage:[/bold yellow]")
        context.console.print(
            "  profile update_survey [level] [years] [--job_role ROLE] [--duty DUTY] [--interests ITEM1,ITEM2,...]",
            markup=False,
        )
        context.console.print("[bold dim]level:[/bold dim] beginner | intermediate | advanced")
        context.console.print("[bold dim]years:[/bold dim] 0-60 (years of experience)")
        context.console.print("[bold cyan]Examples:[/bold cyan]")
        context.console.print("  profile update_survey beginner 0")
        context.console.print("  profile update_survey intermediate 5 --interests 'AI,ML,NLP'")
        context.console.print(
            "  profile update_survey advanced 10 --job_role 'Senior Dev' --duty 'Architecture' --interests 'AI,ML'"
        )
        return

    level = args[0]
    career_input = args[1]

    # Parse career (years_experience) - extract integer from input
    try:
        # Try to parse as integer directly first
        years_experience = int(career_input)
    except ValueError:
        # If that fails, try to extract number from string like "5years"
        match = re.search(r"\d+", career_input)
        if match:
            years_experience = int(match.group())
        else:
            context.console.print("[bold red]✗ Invalid career value[/bold red]")
            context.console.print("[yellow]Career must be a number (0-60) or string like '5years'[/yellow]")
            return

    # Validate range
    if not (0 <= years_experience <= 60):
        context.console.print("[bold red]✗ Invalid career value[/bold red]")
        context.console.print("[yellow]Years of experience must be between 0 and 60[/yellow]")
        return

    career = years_experience
    job_role = None
    duty = None
    interests_str = None

    # Parse optional flags
    i = 2
    while i < len(args):
        if args[i] == "--job_role" and i + 1 < len(args):
            job_role = args[i + 1]
            i += 2
        elif args[i] == "--duty" and i + 1 < len(args):
            duty = args[i + 1]
            i += 2
        elif args[i] == "--interests" and i + 1 < len(args):
            interests_str = args[i + 1]
            i += 2
        else:
            context.console.print(f"[yellow]Unknown option: {args[i]}[/yellow]")
            i += 1

    context.console.print("[dim]Updating survey...[/dim]")

    # JWT 토큰을 client에 설정
    context.client.set_token(context.session.token)

    # Prepare JSON data
    json_data = {
        "level": level,
        "career": career,
    }

    # Add optional fields if provided
    if job_role:
        json_data["job_role"] = job_role
    if duty:
        json_data["duty"] = duty
    if interests_str:
        # Convert comma-separated string to list
        interests = [item.strip() for item in interests_str.split(",")]
        json_data["interests"] = interests

    # API 호출
    status_code, response, error = context.client.make_request(
        "PUT",
        "/profile/survey",
        json_data=json_data,
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
    context.logger.info(
        f"Survey updated: level={level}, career={career}, job_role={job_role}, duty={duty}, interests={interests_str}."
    )


def get_survey(context: CLIContext, *args: str) -> None:
    """현재 사용자의 최근 자기평가 정보를 조회합니다."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        context.console.print("[yellow]Please login first: auth login [username][/yellow]")
        return

    context.console.print("[dim]Fetching profile survey...[/dim]")

    # JWT 토큰을 client에 설정
    context.client.set_token(context.session.token)

    # API 호출
    status_code, response, error = context.client.make_request(
        "GET",
        "/profile/survey",
    )

    if error:
        context.console.print("[bold red]✗ Failed to fetch survey[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        context.logger.error(f"Survey fetch failed: {error}")
        return

    if status_code != 200:
        context.console.print(f"[bold red]✗ Failed (HTTP {status_code})[/bold red]")
        return

    # Extract survey data
    level = response.get("level")
    career = response.get("career")
    job_role = response.get("job_role")
    duty = response.get("duty")
    interests = response.get("interests")

    # Display survey information
    context.console.print()
    context.console.print("[bold cyan]═════════════════════════════════════════════[/bold cyan]")
    context.console.print("[bold cyan]📋 Your Profile Survey[/bold cyan]")
    context.console.print("[bold cyan]═════════════════════════════════════════════[/bold cyan]")
    context.console.print()

    # Check if any data exists
    if level is None and career is None and job_role is None and duty is None and interests is None:
        context.console.print("[bold yellow]ℹ️  No profile survey found[/bold yellow]")
        context.console.print("[dim]  You have not submitted a profile survey yet[/dim]")
    else:
        # Display each field
        if level is not None:
            context.console.print(f"[bold]Level:[/bold] {level}")
        else:
            context.console.print("[bold]Level:[/bold] [dim]Not set[/dim]")

        if career is not None:
            context.console.print(f"[bold]Career:[/bold] {career} years")
        else:
            context.console.print("[bold]Career:[/bold] [dim]Not set[/dim]")

        if job_role is not None:
            context.console.print(f"[bold]Job Role:[/bold] {job_role}")
        else:
            context.console.print("[bold]Job Role:[/bold] [dim]Not set[/dim]")

        if duty is not None:
            context.console.print(f"[bold]Duty:[/bold] {duty}")
        else:
            context.console.print("[bold]Duty:[/bold] [dim]Not set[/dim]")

        if interests is not None:
            interests_str = ", ".join(interests) if isinstance(interests, list) else interests
            context.console.print(f"[bold]Interests:[/bold] {interests_str}")
        else:
            context.console.print("[bold]Interests:[/bold] [dim]Not set[/dim]")

    context.console.print()
    context.console.print("[bold cyan]═════════════════════════════════════════════[/bold cyan]")
    context.console.print()

    context.logger.info(
        f"Fetched survey: level={level}, career={career}, job_role={job_role}, duty={duty}, interests={interests}."
    )


def reset_surveys(context: CLIContext, *args: str) -> None:
    """모든 Survey 기록을 강제로 삭제합니다 (Foreign Key 제약 무시, DEV용)."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        context.console.print("[yellow]Please login first: auth login [username][/yellow]")
        return

    if not context.session.user_id:
        context.console.print("[bold red]✗ User ID not found[/bold red]")
        return

    # Confirm deletion
    context.console.print(
        "[bold yellow]⚠️  WARNING: This will permanently delete all survey records for this user[/bold yellow]"
    )
    context.console.print("[dim]This will bypass foreign key constraints[/dim]")
    context.console.print("[bold yellow]Type 'yes' to confirm:[/bold yellow]")

    # In CLI mode, we'll just proceed (can add confirmation logic if needed)
    try:
        db = SessionLocal()

        # Convert user_id to int if it's a string
        user_id_int = (
            int(context.session.user_id) if isinstance(context.session.user_id, str) else context.session.user_id
        )

        context.console.print(f"[dim]Deleting surveys for user_id={user_id_int}...[/dim]")

        # Step 1: Get all survey IDs for this user
        survey_ids_result = db.execute(
            text("SELECT id FROM user_profile_surveys WHERE user_id = :user_id"),
            {"user_id": user_id_int},
        )
        survey_ids = [row[0] for row in survey_ids_result.fetchall()]
        context.console.print(f"[dim]Found {len(survey_ids)} survey record(s) to delete[/dim]")

        # Step 2: Delete related records in cascade order (respecting FK constraints)
        deleted_answers = 0
        deleted_questions = 0
        deleted_sessions = 0

        for survey_id in survey_ids:
            # Step 2.1: Delete attempt_answers (references questions)
            aa_result = db.execute(
                text(
                    "DELETE FROM attempt_answers WHERE question_id IN "
                    "(SELECT id FROM questions WHERE session_id IN "
                    "(SELECT id FROM test_sessions WHERE survey_id = :survey_id))"
                ),
                {"survey_id": survey_id},
            )
            deleted_answers += aa_result.rowcount

            # Step 2.2: Delete questions (references test_sessions)
            q_result = db.execute(
                text(
                    "DELETE FROM questions WHERE session_id IN (SELECT id FROM test_sessions WHERE survey_id = :survey_id)"
                ),
                {"survey_id": survey_id},
            )
            deleted_questions += q_result.rowcount

            # Step 2.3: Delete test sessions (references user_profile_surveys)
            s_result = db.execute(
                text("DELETE FROM test_sessions WHERE survey_id = :survey_id"),
                {"survey_id": survey_id},
            )
            deleted_sessions += s_result.rowcount

        if deleted_answers > 0 or deleted_questions > 0 or deleted_sessions > 0:
            context.console.print(
                f"[dim]  Deleted {deleted_answers} answer(s), {deleted_questions} question(s), and {deleted_sessions} session(s)[/dim]"
            )

        # Step 3: Delete surveys
        result = db.execute(
            text("DELETE FROM user_profile_surveys WHERE user_id = :user_id"),
            {"user_id": user_id_int},
        )
        deleted_surveys = result.rowcount

        # Step 4: Commit
        db.commit()

        context.console.print(
            f"[bold green]✓ Deleted {deleted_surveys} survey(s), {deleted_sessions} session(s), {deleted_questions} question(s), {deleted_answers} answer(s)[/bold green]"
        )
        context.logger.info(
            f"Reset surveys: deleted {deleted_surveys} surveys, {deleted_sessions} sessions, {deleted_questions} questions, {deleted_answers} answers for user_id={user_id_int}"
        )

    except Exception as e:
        db.rollback()
        context.console.print("[bold red]✗ Deletion failed[/bold red]")
        context.console.print(f"[red]  Error: {str(e)}[/red]")
        context.logger.error(f"Failed to reset surveys: {e}", exc_info=True)
    finally:
        db.close()


def get_consent(context: CLIContext, *args: str) -> None:
    """현재 사용자의 개인정보 동의 여부를 확인합니다."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        context.console.print("[yellow]Please login first: auth login [username][/yellow]")
        return

    context.console.print("[dim]Fetching privacy consent status...[/dim]")

    # JWT 토큰을 client에 설정
    context.client.set_token(context.session.token)

    # API 호출
    status_code, response, error = context.client.make_request(
        "GET",
        "/profile/consent",
    )

    if error:
        context.console.print("[bold red]✗ Failed to fetch consent status[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        context.logger.error(f"Consent status fetch failed: {error}")
        return

    if status_code != 200:
        context.console.print(f"[bold red]✗ Failed (HTTP {status_code})[/bold red]")
        return

    consented = response.get("consented", False)
    consent_at = response.get("consent_at")

    if consented:
        context.console.print("[bold green]✓ Consent Status: GRANTED[/bold green]")
        if consent_at:
            context.console.print(f"[dim]  Consented at: {consent_at}[/dim]")
    else:
        context.console.print("[bold yellow]✓ Consent Status: NOT GRANTED[/bold yellow]")
        context.console.print("[dim]  You have not granted privacy consent yet[/dim]")

    context.logger.info("Fetched privacy consent status.")


def set_consent(context: CLIContext, *args: str) -> None:
    """개인정보 동의 상태를 변경합니다."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        context.console.print("[yellow]Please login first: auth login [username][/yellow]")
        return

    if not args:
        context.console.print("[bold yellow]Usage:[/bold yellow] profile set-consent [true|false]")
        context.console.print("[bold cyan]Examples:[/bold cyan]")
        context.console.print("  profile set-consent true       - Grant privacy consent")
        context.console.print("  profile set-consent false      - Withdraw privacy consent")
        return

    consent_str = args[0].lower()
    if consent_str in ("true", "yes", "y", "1"):
        consent = True
        action = "Grant"
    elif consent_str in ("false", "no", "n", "0"):
        consent = False
        action = "Withdraw"
    else:
        context.console.print(f"[bold red]✗ Invalid consent value: '{consent_str}'[/bold red]")
        context.console.print("[yellow]Use: true/yes/y/1 or false/no/n/0[/yellow]")
        return

    context.console.print(f"[dim]{action}ing privacy consent...[/dim]")

    # JWT 토큰을 client에 설정
    context.client.set_token(context.session.token)

    # API 호출
    status_code, response, error = context.client.make_request(
        "POST",
        "/profile/consent",
        json_data={"consent": consent},
    )

    if error:
        context.console.print("[bold red]✗ Consent update failed[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        context.logger.error(f"Consent update failed: {error}")
        return

    if status_code != 200:
        context.console.print(f"[bold red]✗ Consent update failed (HTTP {status_code})[/bold red]")
        return

    message = response.get("message", "Consent updated")
    context.console.print(f"[bold green]✓ {message}[/bold green]")

    if consent:
        consent_at = response.get("consent_at")
        if consent_at:
            context.console.print(f"[dim]  Consented at: {consent_at}[/dim]")
    else:
        context.console.print("[dim]  Privacy consent withdrawn[/dim]")

    context.logger.info(f"Consent status changed: consent={consent}.")


def get_ranking(context: CLIContext, *args: str) -> None:
    """Get current user's grade and ranking."""
    if not context.session.token:
        context.console.print("[bold red]✗ Not authenticated[/bold red]")
        context.console.print("[yellow]Please login first: auth login [username][/yellow]")
        return

    context.console.print("[dim]Fetching ranking and grade...[/dim]")

    # JWT 토큰을 client에 설정
    context.client.set_token(context.session.token)

    # API 호출
    status_code, response, error = context.client.make_request(
        "GET",
        "/profile/ranking",
    )

    if error:
        context.console.print("[bold red]✗ Failed to fetch ranking[/bold red]")
        context.console.print(f"[red]  Error: {error}[/red]")
        context.logger.error(f"Ranking fetch failed: {error}")
        return

    if status_code != 200:
        context.console.print(f"[bold red]✗ Failed (HTTP {status_code})[/bold red]")
        if isinstance(response, dict) and "detail" in response:
            context.console.print(f"[red]  {response['detail']}[/red]")
        return

    # Extract ranking data
    grade = response.get("grade", "Unknown")
    score = response.get("score", 0)
    rank = response.get("rank", 0)
    total_cohort_size = response.get("total_cohort_size", 0)
    percentile_description = response.get("percentile_description", "")
    percentile_confidence = response.get("percentile_confidence", "unknown")
    grade_distribution = response.get("grade_distribution", [])

    # Display ranking information
    context.console.print()
    context.console.print("[bold cyan]═════════════════════════════════════════════[/bold cyan]")
    context.console.print("[bold cyan]📊 Your Ranking and Grade[/bold cyan]")
    context.console.print("[bold cyan]═════════════════════════════════════════════[/bold cyan]")
    context.console.print()

    # Grade
    context.console.print(f"[bold]Grade:[/bold] [bold yellow]{grade}[/bold yellow]")

    # Score
    context.console.print(f"[bold]Composite Score:[/bold] [bold green]{score}/100[/bold green]")

    # Rank
    context.console.print(f"[bold]Rank:[/bold] [bold cyan]#{rank}[/bold cyan] out of {total_cohort_size}")

    # Percentile
    context.console.print(f"[bold]Percentile:[/bold] {percentile_description}")
    context.console.print(f"[dim]  (Confidence: {percentile_confidence})[/dim]")

    context.console.print()
    context.console.print("[bold cyan]═════════════════════════════════════════════[/bold cyan]")

    # Display grade distribution if available
    if grade_distribution:
        context.console.print()
        context.console.print("[bold cyan]📈 Grade Distribution[/bold cyan]")
        context.console.print("[bold cyan]═════════════════════════════════════════════[/bold cyan]")
        context.console.print()

        for dist in grade_distribution:
            dist_grade = dist.get("grade", "Unknown")
            dist_count = dist.get("count", 0)
            dist_percentage = dist.get("percentage", 0)

            # Create a simple bar chart
            bar_length = int(dist_percentage / 2)  # Scale to 50 chars max
            bar = "█" * bar_length
            spaces = " " * (25 - bar_length)

            # Color based on grade
            if dist_grade == "Elite":
                color = "bold magenta"
            elif dist_grade == "Advanced":
                color = "bold yellow"
            elif dist_grade == "Inter-Advanced":
                color = "bold cyan"
            elif dist_grade == "Intermediate":
                color = "bold green"
            else:  # Beginner
                color = "bold blue"

            context.console.print(
                f"[{color}]{dist_grade:15}[/{color}] {bar}{spaces} {dist_count:3} ({dist_percentage:5.1f}%)"
            )

        context.console.print()
        context.console.print("[bold cyan]═════════════════════════════════════════════[/bold cyan]")

    context.console.print()

    context.logger.info(f"Fetched ranking: grade={grade}, score={score}, rank={rank}")
