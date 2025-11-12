"""System-level CLI actions."""

import os
from collections import defaultdict

from rich.rule import Rule
from rich.table import Table

from src.cli.config.command_layout import COMMAND_LAYOUT
from src.cli.context import CLIContext


def _flatten_commands(commands: dict, prefix: str = "") -> list[tuple[str, str | None, str]]:
    """
    Flatten hierarchical command structure into list of (full_cmd, usage, description).

    Args:
        commands: Command dictionary from COMMAND_LAYOUT
        prefix: Current command prefix for nested commands

    Returns:
        List of (full_command, usage, description) tuples

    """
    result: list[tuple[str, str | None, str]] = []

    for cmd_name, cmd_obj in commands.items():
        full_cmd = f"{prefix}{cmd_name}".strip()

        result.append(
            (
                full_cmd,
                cmd_obj.get("usage") or full_cmd,
                cmd_obj.get("description", ""),
            )
        )

        # Recursively add sub-commands
        if "sub_commands" in cmd_obj and cmd_obj["sub_commands"]:
            sub_commands = _flatten_commands(cmd_obj["sub_commands"], f"{full_cmd} ")
            result.extend(sub_commands)

    return result


def help(context: CLIContext, *args: str) -> None:
    """사용 가능한 명령어 목록을 보여줍니다."""
    context.console.print()
    context.console.print(
        "[bold cyan]╔════════════════════════════════════════════════════════════════════════════════╗[/bold cyan]"
    )
    context.console.print(
        "[bold cyan]║  SLEA-SSEM CLI - Available Commands                                            ║[/bold cyan]"
    )
    context.console.print(
        "[bold cyan]╚════════════════════════════════════════════════════════════════════════════════╝[/bold cyan]"
    )
    context.console.print()

    # Flatten and collect all commands
    all_commands = _flatten_commands(COMMAND_LAYOUT)

    # Sort by command name
    all_commands.sort(key=lambda x: x[0])

    # Separate CLI system commands from API commands
    cli_system_commands = {"help", "clear", "exit"}
    api_commands = []
    system_commands = []

    for cmd, usage, description in all_commands:
        # Get the root command name (first word)
        root_cmd = cmd.split()[0]
        if root_cmd in cli_system_commands:
            system_commands.append((cmd, usage, description))
        else:
            api_commands.append((cmd, usage, description))

    # Calculate max command width for proper alignment
    all_usages = [usage for _cmd, usage, _desc in api_commands + system_commands if usage]
    max_width = max(len(usage) for usage in all_usages) if all_usages else 20

    # Group API commands by their root command
    api_groups = defaultdict(list)
    for cmd, usage, description in api_commands:
        root_cmd = cmd.split(" ")[0]
        api_groups[root_cmd].append((usage, description))

    sorted_group_names = sorted(api_groups.keys())

    for i, group_name in enumerate(sorted_group_names):
        group_commands = api_groups[group_name]
        group_table = Table(show_header=False, box=None, padding=(0, 1))
        group_table.add_column(width=max_width)  # Column for command usage
        group_table.add_column()  # Column for description

        for usage, description in group_commands:
            group_table.add_row(usage, f"[dim]{description}[/dim]")

        context.console.print(group_table)

        # Add a separator if it's not the last API group
        if i < len(sorted_group_names) - 1:
            context.console.print(Rule(style="dim"))

    # --- Separator before system commands ---
    context.console.print(Rule(style="dim"))

    # --- System Commands Table ---
    system_table = Table(show_header=False, box=None, padding=(0, 1))
    system_table.add_column(width=max_width)  # Column for command usage
    system_table.add_column()  # Column for description

    for _cmd, usage, description in system_commands:
        # Usage in normal style (white), description in dim style
        system_table.add_row(usage, f"[dim]{description}[/dim]")

    context.console.print(system_table)

    context.console.print()
    context.console.print("[bold yellow]💡 팁:[/bold yellow] 명령어를 입력하거나 'help'를 다시 입력하세요")
    context.console.print("[dim]괄호 [] 안의 인자는 필수입니다[/dim]")
    context.console.print()


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
