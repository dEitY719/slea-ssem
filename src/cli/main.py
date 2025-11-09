"""
Main CLI application module.

This module contains the core CLI implementation including the dispatcher
and interactive prompt loop.
"""

import atexit
import importlib
import logging
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from rich.console import Console

from src.cli.config.loader import load_config
from src.cli.config.models import Command, CommandConfig
from src.cli.context import CLIContext

# Configure logging (WARNING level for user-friendly output)
# Set to DEBUG for troubleshooting, INFO for important events, WARNING for errors only
logging.basicConfig(level=logging.WARNING, stream=sys.stderr, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Suppress asyncio debug logs
logging.getLogger("asyncio").setLevel(logging.WARNING)


class CLIDispatcher:
    """Dispatcher for executing CLI commands based on configuration."""

    def __init__(self, command_config: CommandConfig, context: CLIContext) -> None:
        """
        Initialize the CLI dispatcher.

        Args:
            command_config: Validated command configuration.
            context: CLI context with console and logger.

        """
        self.command_config = command_config
        self.context = context
        self.console = context.console
        self.logger = context.logger

    def _get_command_target(self, command_path: list[str]) -> str | None:
        """주어진 명령어 경로에 해당하는 실행 함수 경로를 찾습니다."""
        current_level = self.command_config.commands
        target = None
        for i, cmd_name in enumerate(command_path):
            if cmd_name in current_level:
                cmd_obj = current_level[cmd_name]
                if i == len(command_path) - 1:  # 마지막 명령어
                    target = cmd_obj.target
                if cmd_obj.sub_commands:
                    current_level = cmd_obj.sub_commands
                else:  # 하위 명령어가 없는데 경로가 더 있으면 잘못된 경로
                    break
            else:
                return None  # 명령어를 찾을 수 없음
        return target

    def _import_and_get_func(self, target_path: str) -> callable | None:
        """
        Import and return a function object from a module path string.

        Args:
            target_path: Module path in 'module.function' format.

        Returns:
            The function object if found, None otherwise.

        """
        try:
            module_path, func_name = target_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            func = getattr(module, func_name)
            return func
        except (ImportError, AttributeError) as e:
            self.logger.error(f"Error loading command: {target_path} - {e}")
            self.console.print(f"[bold red]Error loading command: {target_path} - {e}[/bold red]")
            return None

    def dispatch(self, command_path: list[str], args: list[str]) -> None:
        """
        Execute a CLI command based on path and arguments.

        Args:
            command_path: List of command tokens to find the target function.
            args: Arguments to pass to the target function.

        """
        if not command_path:
            return

        # 'help'와 'exit'는 특별 처리
        if command_path[0] == "help":
            target_path = self._get_command_target(["help"])
            if target_path:
                func = self._import_and_get_func(target_path)
                if func:
                    func(self.context, *args)
            return
        elif command_path[0] == "exit":
            return

        target_path = self._get_command_target(command_path)

        if target_path:
            func = self._import_and_get_func(target_path)
            if func:
                try:
                    # 모든 액션 함수는 CLIContext를 첫 번째 인자로 받도록 가정
                    func(self.context, *args)
                except Exception as e:
                    self.logger.error(f"Error executing command: {e}", exc_info=True)
                    self.console.print(f"[bold red]Error: {e}[/bold red]")
            else:
                self.console.print(
                    f"[bold red]Could not find executable for command: {' '.join(command_path)}[/bold red]"
                )
        else:
            self.console.print(f"[bold red]Unknown command: {' '.join(command_path)}[/bold red]")
            self.console.print("[bold yellow]Type 'help' to see available commands.[/bold yellow]")


class CLI:
    """Interactive CLI application using prompt_toolkit."""

    def __init__(self) -> None:
        """Initialize the CLI application."""
        self.console = Console()
        self.logger = logger  # Use the module-level logger
        self.context = CLIContext(console=self.console, logger=self.logger)
        self.command_config = load_config()
        self.dispatcher = CLIDispatcher(self.command_config, self.context)
        self.session = PromptSession(history=InMemoryHistory())
        self.should_exit = False  # Flag to signal exit

        # Register cleanup handler for graceful shutdown
        atexit.register(self._cleanup)

    def _get_completer(self, current_commands: dict[str, Command]) -> WordCompleter:
        """현재 레벨의 명령어들을 위한 자동 완성 기능을 생성합니다."""
        words = list(current_commands.keys())
        return WordCompleter(words, ignore_case=True)

    def _parse_input(self, text: str) -> tuple[list[str], list[str]]:
        """입력 문자열을 명령어 경로와 인자로 분리합니다."""
        parts = text.strip().split()
        if not parts:
            return [], []

        command_path = []
        args = []
        current_level = self.command_config.commands

        for i, part in enumerate(parts):
            if part in current_level:
                command_path.append(part)
                if current_level[part].sub_commands:
                    current_level = current_level[part].sub_commands
                else:  # 더 이상 하위 명령어가 없으면 나머지는 모두 인자
                    args = parts[i + 1 :]
                    break
            else:  # 현재 레벨에서 명령어를 찾을 수 없으면 나머지는 모두 인자
                args = parts[i:]
                break
        return command_path, args

    def _cleanup(self) -> None:
        """CLI 종료 시 정리 작업을 수행합니다."""
        # prompt_toolkit 리소스 정리
        try:
            # PromptSession 종료 (있다면)
            if hasattr(self.session, "app") and self.session.app:
                self.session.app.exit()
        except Exception:
            pass  # Silently ignore cleanup errors

    def run(self) -> None:
        """Run the interactive CLI main loop."""
        self.console.print("[bold green]Welcome to the SLEA-SSEM CLI![/bold green]")
        self.console.print("[bold yellow]Type 'help' for a list of commands, or 'exit' to quit.[/bold yellow]")

        exit_count = 0  # Track consecutive Ctrl+C presses

        while True:
            try:
                # Check if exit flag was set
                if self.should_exit:
                    break

                completer = self._get_completer(self.command_config.commands)
                text = self.session.prompt("> ", completer=completer)

                # Reset exit counter on successful input
                exit_count = 0

                command_path, args = self._parse_input(text)

                if not command_path:
                    continue

                if command_path[0] == "exit":
                    self.dispatcher.dispatch(command_path, args)
                    self.should_exit = True
                    break

                # Execute command and display results on same screen
                self.dispatcher.dispatch(command_path, args)

            except KeyboardInterrupt:
                exit_count += 1
                if exit_count >= 2:
                    self.console.print("\n[bold red]Exiting...[/bold red]")
                    self.should_exit = True
                    break
                msg = "\n[bold yellow]Ctrl-C pressed. Press again to force exit, or type 'exit'.[/bold yellow]"
                self.console.print(msg)
            except EOFError:
                self.console.print("\n[bold yellow]Exiting...[/bold yellow]")
                self.should_exit = True
                break
            except Exception as e:
                self.logger.error(f"An unexpected error occurred: {e}", exc_info=True)
                self.console.print(f"[bold red]Error: {e}[/bold red]")


def main() -> None:
    """Start the interactive CLI."""
    try:
        cli = CLI()
        cli.run()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error in CLI: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Ensure clean exit
        sys.exit(0)


if __name__ == "__main__":
    main()
