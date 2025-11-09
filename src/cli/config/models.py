"""Pydantic models for CLI configuration validation."""

from pydantic import BaseModel, Field


class Command(BaseModel):
    """Represents a CLI command with optional sub-commands."""

    description: str = Field(..., description="명령어에 대한 설명 (help 메시지에 사용)")
    target: str | None = Field(None, min_length=1, description="'module.function' 형태의 실행 함수 경로")
    sub_commands: dict[str, "Command"] | None = Field(None, description="하위 명령어 딕셔너리")


class CommandConfig(BaseModel):
    """Top-level configuration model for CLI commands."""

    commands: dict[str, Command]
