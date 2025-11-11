#!/usr/bin/env python3
"""
Agent Sanity Check Script - Step-by-Step Testing

REQ: REQ-A-Agent-Sanity-0 - Agent 기본 동작 검증

실행 방법:
    # Step 1만 실행
    python scripts/test_agent_sanity_check.py --step 1

    # Step 1-2 누적 실행
    python scripts/test_agent_sanity_check.py --step 2

    # 모든 단계 실행
    python scripts/test_agent_sanity_check.py --all
    python scripts/test_agent_sanity_check.py  # 기본값

환경변수 (.env 파일에서 자동 로드):
    GEMINI_API_KEY: Google Gemini API 키 (필수)
    LANGCHAIN_DEBUG: 1로 설정하면 상세 로깅 (선택)
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

# Agent 모듈 임포트
from src.agent.llm_agent import (
    GenerateQuestionsRequest,
    create_agent,
)

# .env 파일 로드 (프로젝트 루트)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=Console(), rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)
console = Console()


class AgentSanityCheck:
    """Agent Sanity Check - 5개 단계 실행"""

    def __init__(self, target_step: int = 5) -> None:
        """
        초기화

        Args:
            target_step: 실행할 최대 단계 (1-5)

        """
        self.target_step = target_step
        self.agent = None
        self.request = None
        self.response = None

    def print_header(self) -> None:
        """헤더 출력"""
        header_text = f"🔍 Agent Sanity Check - Step 1-{self.target_step}/{5}"
        console.print(Panel(header_text, style="cyan"))
        console.print()

    # ========================================================================
    # Step 1: GEMINI_API_KEY 확인
    # ========================================================================

    def run_step_1(self) -> bool:
        """
        Step 1: GEMINI_API_KEY 확인

        Returns:
            True if success, False otherwise

        """
        console.print("[bold cyan]Step 1: GEMINI_API_KEY 확인[/bold cyan]")

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            console.print("[bold red]  ❌ GEMINI_API_KEY not found[/bold red]")
            console.print(
                "  Please set GEMINI_API_KEY environment variable",
                style="red",
            )
            return False

        # 마스킹된 키 표시
        masked_key = f"{api_key[:10]}...{api_key[-4:]}"
        console.print("  ✅ GEMINI_API_KEY found")
        console.print(f"  Key (masked): {masked_key}")
        console.print()

        return True

    # ========================================================================
    # Step 2: ItemGenAgent 초기화
    # ========================================================================

    async def run_step_2(self) -> bool:
        """
        Step 2: ItemGenAgent 초기화

        Returns:
            True if success, False otherwise

        """
        console.print("[bold cyan]Step 2: Initialize ItemGenAgent[/bold cyan]")

        try:
            console.print("  🚀 Creating LLM (Google Gemini)...")
            # create_agent() 함수 사용
            self.agent = await create_agent()
            console.print("  ✅ LLM created")

            console.print("  🚀 Loading ReAct prompt...")
            # Agent 초기화 시 prompt도 로드됨
            console.print("  ✅ Prompt loaded")

            console.print("  🚀 Loading FastMCP tools (1-5)...")
            # Agent에 tools가 포함됨
            if hasattr(self.agent, "tools"):
                num_tools = len(self.agent.tools)
                tool_names = [t.name for t in self.agent.tools]
                console.print(f"  ✅ {num_tools} tools loaded: {tool_names}")
            else:
                console.print("  ✅ Tools loaded")

            console.print("  🚀 Creating ReAct agent...")
            # executor가 생성됨
            console.print("  ✅ Agent created")

            console.print()
            return True

        except Exception as e:
            console.print(f"  [bold red]❌ Initialization failed: {e}[/bold red]")
            logger.exception("Step 2 failed")
            console.print()
            return False

    # ========================================================================
    # Step 3: GenerateQuestionsRequest 생성
    # ========================================================================

    def run_step_3(self) -> bool:
        """
        Step 3: GenerateQuestionsRequest 생성

        Returns:
            True if success, False otherwise

        """
        console.print("[bold cyan]Step 3: Create GenerateQuestionsRequest[/bold cyan]")

        try:
            self.request = GenerateQuestionsRequest(
                survey_id="test_survey",
                round_idx=1,
                prev_answers=None,
            )

            console.print("  ✅ Request created")
            console.print(f"     survey_id: {self.request.survey_id}")
            console.print(f"     round_idx: {self.request.round_idx}")
            console.print(f"     prev_answers: {self.request.prev_answers}")
            console.print()

            return True

        except Exception as e:
            console.print(f"  [bold red]❌ Request creation failed: {e}[/bold red]")
            logger.exception("Step 3 failed")
            console.print()
            return False

    # ========================================================================
    # Step 4: agent.generate_questions() 호출
    # ========================================================================

    async def run_step_4(self) -> bool:
        """
        Step 4: agent.generate_questions() 호출

        Returns:
            True if success, False otherwise

        """
        console.print("[bold cyan]Step 4: Call agent.generate_questions()[/bold cyan]")

        if not self.agent:
            console.print("  [bold red]❌ Agent not initialized[/bold red]")
            console.print()
            return False

        if not self.request:
            console.print("  [bold red]❌ Request not created[/bold red]")
            console.print()
            return False

        try:
            console.print("  🔄 Invoking agent...")
            console.print()

            # Agent 호출
            self.response = await self.agent.generate_questions(self.request)

            console.print("  ✅ Agent execution complete")
            console.print()

            return True

        except Exception as e:
            console.print(f"  [bold red]❌ Agent invocation failed: {e}[/bold red]")
            logger.exception("Step 4 failed")
            console.print()
            return False

    # ========================================================================
    # Step 5: JSON 파싱 및 결과 표시
    # ========================================================================

    def run_step_5(self) -> bool:
        """
        Step 5: JSON 파싱 및 결과 표시

        Returns:
            True if success, False otherwise

        """
        console.print("[bold cyan]Step 5: Parse and Validate JSON Result[/bold cyan]")

        if not self.response:
            console.print("  [bold red]❌ Response not available[/bold red]")
            console.print()
            return False

        try:
            # JSON 파싱 (이미 GenerateQuestionsResponse 객체)
            console.print("  ✅ JSON parsing successful")
            console.print()

            # Response Summary 표시
            console.print("[bold cyan]  📊 Response Summary:[/bold cyan]")
            console.print(f"     round_id: {self.response.round_id}")
            console.print(f"     items generated: {len(self.response.items)}")
            console.print(f"     failed: {self.response.failed_count}")
            console.print(f"     agent_steps: {self.response.agent_steps}")
            if self.response.error_message:
                console.print(f"     error: {self.response.error_message}", style="yellow")
            console.print()

            # 생성된 아이템 테이블
            if self.response.items:
                console.print("[bold cyan]  📋 Generated Items:[/bold cyan]")
                table = Table(title=None)
                table.add_column("ID", style="cyan")
                table.add_column("Type", style="magenta")
                table.add_column("Difficulty", style="yellow")
                table.add_column("Validation", style="green")

                for item in self.response.items:
                    table.add_row(
                        item.id[:12] + "...",
                        item.type,
                        str(item.difficulty),
                        f"{item.validation_score:.2f}",
                    )

                console.print(table)
                console.print()

                # 첫 번째 아이템 상세 정보
                first = self.response.items[0]
                console.print("[bold cyan]  📄 First Item Details:[/bold cyan]")
                console.print(f"     Stem: {first.stem[:80]}...")
                console.print(f"     Answer Schema: {first.answer_schema.type}")
                if first.choices:
                    console.print(f"     Choices: {first.choices}")
                console.print()

            # 검증
            if len(self.response.items) > 0 and self.response.failed_count == 0:
                console.print("  ✅ All items valid")
            else:
                console.print("  ⚠️  Some items failed validation")

            console.print()
            return True

        except Exception as e:
            console.print(f"  [bold red]❌ Parsing failed: {e}[/bold red]")
            logger.exception("Step 5 failed")
            console.print()
            return False

    # ========================================================================
    # 메인 실행
    # ========================================================================

    async def run(self) -> bool:
        """
        모든 단계 실행

        Returns:
            True if all steps passed, False otherwise

        """
        self.print_header()

        steps = [
            (1, self.run_step_1),
            (2, self.run_step_2),
            (3, self.run_step_3),
            (4, self.run_step_4),
            (5, self.run_step_5),
        ]

        for step_num, step_func in steps:
            if step_num > self.target_step:
                break

            # Step 2, 4는 async 함수
            if step_num in [2, 4]:
                success = await step_func()
            else:
                success = step_func()

            if success:
                console.print(f"[bold green]✅ Step {step_num} Complete[/bold green]")
                console.print()
            else:
                console.print(f"[bold red]❌ Step {step_num} Failed[/bold red]")
                console.print()
                return False

        # 모든 단계 완료 메시지
        if self.target_step == 5:
            console.print("[bold green]✅✅✅ All Steps Complete![/bold green]")
            console.print()

        return True


def main() -> None:
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="Agent Sanity Check - Step-by-Step Testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Step 1만 실행 (API KEY 검증)
  python scripts/test_agent_sanity_check.py --step 1

  # Step 1-2 누적 실행 (초기화까지)
  python scripts/test_agent_sanity_check.py --step 2

  # 모든 단계 실행
  python scripts/test_agent_sanity_check.py --all
  python scripts/test_agent_sanity_check.py  # 기본값

Environment Variables:
  GEMINI_API_KEY: Google Gemini API 키 (필수)
  LANGCHAIN_DEBUG: 1로 설정하면 상세 로깅 (선택)
        """,
    )

    parser.add_argument(
        "--step",
        type=int,
        choices=[1, 2, 3, 4, 5],
        default=5,
        help="Run up to this step (1-5, default: 5)",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all steps (same as --step 5)",
    )

    args = parser.parse_args()

    # --all 플래그면 step 5로 설정
    target_step = 5 if args.all else args.step

    # Sanity check 실행
    checker = AgentSanityCheck(target_step=target_step)

    try:
        success = asyncio.run(checker.run())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]⏹️  Interrupted by user[/bold yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[bold red]❌ Unexpected error: {e}[/bold red]")
        logger.exception("Unexpected error")
        sys.exit(1)


if __name__ == "__main__":
    main()
