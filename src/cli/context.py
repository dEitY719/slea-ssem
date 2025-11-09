"""
CLI context and dependency injection.

This module defines the CLIContext dataclass which serves as a dependency
injection container for CLI components.
"""

from dataclasses import dataclass
from logging import Logger

from rich.console import Console


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
