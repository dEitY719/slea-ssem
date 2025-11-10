"""
CLI context and dependency injection.

This module defines the CLIContext dataclass which serves as a dependency
injection container for CLI components.
"""

from dataclasses import dataclass, field
from logging import Logger

from rich.console import Console

from src.cli.client import APIClient


@dataclass
class SessionState:
    """Session state managed by CLI."""

    token: str | None = None
    user_id: str | None = None
    username: str | None = None
    current_session_id: str | None = None
    current_round: int | None = None


@dataclass
class CLIContext:
    """
    Dependency injection container for CLI operations.

    This dataclass holds shared CLI state and utilities that are injected
    into action functions to provide consistent access to console output
    and logging capabilities.
    """

    console: Console
    logger: Logger
    client: APIClient = field(default_factory=lambda: APIClient())
    session: SessionState = field(default_factory=SessionState)
