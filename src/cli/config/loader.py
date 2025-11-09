"""
Load and validate CLI configuration.

This module loads the COMMAND_LAYOUT dictionary from command_layout.py
and validates it using Pydantic models.
"""

from src.cli.config.command_layout import COMMAND_LAYOUT
from src.cli.config.models import CommandConfig


def load_config() -> CommandConfig:
    """
    Load and validate command configuration.

    Loads COMMAND_LAYOUT dictionary from command_layout.py and validates
    its structure and data types using Pydantic's CommandConfig model.

    Returns:
        Validated CommandConfig object.

    Raises:
        pydantic.ValidationError: If configuration structure doesn't match the model.

    """
    return CommandConfig(commands=COMMAND_LAYOUT)
