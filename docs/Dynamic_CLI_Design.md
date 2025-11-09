# Dynamic CLI Design Specification (V3.0, Prompt-Based)

## 1. 개요 (Overview)

본 문서는 Python을 활용하여, Gemini CLI와 유사한 동적이고 인터랙티브한 **프롬프트(Prompt) 기반 CLI 애플리케이션**을 구축하기 위한 고급 설계 명세입니다. 이 설계의 핵심 목표는 **명령어 구조(Command Structure)**를 외부 설정 파일로부터 동적으로 로드하고, **Pydantic을 통한 강력한 유효성 검사**, **액션의 동적 임포트**, **컨텍스트 객체를 통한 의존성 주입**을 구현하여, 유지보수성과 확장성이 뛰어난 프레임워크를 제공하는 것입니다.

**최종 목표:**

- 계층적 명령어 구조를 정의한 설정 파일을 기반으로 동적 CLI 인터페이스를 생성합니다.
- `prompt_toolkit`을 활용하여 **자동 완성(auto-completion)**, **명령어 히스토리(history)** 등 풍부한 기능을 갖춘 인터랙티브 프롬프트를 제공합니다.
- 각 명령어에 연결된 특정 Python 함수(액션)를 **동적으로 로드하고 실행**합니다.
- 에러 핸들링, 로깅, 테스트 용이성을 포함한 견고한 애플리케이션을 구축합니다.

## 2. 핵심 요구사항 (Core Requirements)

- **설정 기반 동적 명령어 (Config-Driven Dynamic Commands):** CLI의 모든 명령어는 Pydantic 모델로 검증된 설정 객체로부터 런타임에 생성되어야 한다.
- **계층적 명령어 파싱 (Hierarchical Command Parsing):** `profile nickname check`와 같은 계층적 명령어를 파싱하고, 해당하는 액션을 정확히 찾아 실행할 수 있어야 한다.
- **인터랙티브 프롬프트 (Interactive Prompt):** `prompt_toolkit`을 통해 자동 완성, 명령어 히스토리 등 사용자 친화적인 프롬프트 환경을 제공해야 한다.
- **동적 액션 디스패치 (Dynamic Action Dispatching):** 설정에 명시된 액션을 동적으로 임포트하여 실행해야 한다.
- **의존성 주입 (Dependency Injection):** `CLIContext` 데이터 클래스를 통해 콘솔, 로거, 설정 등 공용 객체를 각 액션 함수에 주입해야 한다.
- **견고성 및 회복성 (Robustness & Resilience):** 액션 실행 중 발생하는 예외를 우아하게 처리하고, 모든 중요한 이벤트를 로깅해야 한다.
- **테스트 용이성 (Testability):** 각 컴포넌트(액션, 설정 로더 등)는 단위 테스트가 가능해야 하며, 전체 CLI 흐름은 기능 테스트가 가능해야 한다.

## 3. 주요 기술 스택 (Key Technologies)

- **Python 3.9+:** 핵심 프로그래밍 언어.
- **`rich`:** 터미널 UI 렌더링 (출력 포맷팅).
- **`prompt_toolkit`:** 인터랙티브 프롬프트, 자동 완성, 히스토리 기능 제공.
- **`pydantic`:** 설정 파일의 구조와 값에 대한 강력한 유효성 검사를 위함.
- **`importlib` (Standard Library):** 액션 함수를 문자열 경로로부터 동적으로 임포트하기 위함.

## 4. 아키텍처 설계 (Architectural Design)

애플리케이션은 **설정 기반(Configuration-Driven)** 아키텍처를 따르며, 각 컴포넌트는 명확히 분리된 역할을 수행합니다.

![CLI Architecture Diagram V3](https://mermaid-js.github.io/mermaid-live-editor/eyJjb2RlIjoiZ3JhcGggVERcbiAgICBzdWJncmFwaCBJbml0aWFsaXphdGlvblxuICAgICAgQVtSYXcgQ29uZmlnIChESUNUKV0gLS0-fFZhbGlkYXRlfCBCW0NvbW1hbmQgTG9hZGVyIChQeWRhbnRpYyldXG4gICAgICBCIC0tPiBDW0NMSUNvbnRleHQgSW5zdGFuY2VdXG4gICAgZW5kXG5cbiAgICBzdWJncmFwaCBNaW4gRXZlbnQgTG9vcFxuICAgICAgQyAtLi0-IEVbUHJvbXB0IFVJIChwcm9tcHRfdG9vbGtpdCldXG4gICAgICBFIC0tPnxHZXQgVXNlciBJbnB1dHwgRltDb21tYW5kIFBhcnNlcl1cbiAgICAgIEYgLS0-fFBhcnNlZCBDb21tYW5kfCBHW0FjdGlvbiBEaXNwYXRjaGVyIChpbXBvcnRsaWIpXVxuICAgICAgRyAtLT58SW5qZWN0IENvbnRleHR8IEhbQWN0aW9uIEZ1bmN0aW9uXVxuICAgICAgSCBLRXhlY3V0ZSBDb21tYW5kXSAtLT58TG9nICYgRXJyb3IgSGFuZGxpbmd8IEVcbiAgICBlbmRcbiIsIm1lcm1haWQiOnsidGhlbWVEcmF3ZEJESiI6dHJ1ZX0sInVwZGF0ZUVkaXRvciI6ZmFsc2UsImF1dG9TeW5jIjp0cnVlLCJ1cGRhdGVEaWFncmFtIjpmYWxzZX0)

### 4.1. 컴포넌트 분리 (Component Breakdown)

1. **Configuration Models (`src/cli/config/models.py`):** Pydantic 모델을 사용하여 명령어 설정의 스키마를 정의하고 유효성을 검사합니다.
2. **Config Loader (`src/cli/config/loader.py`):** 원시 딕셔너리 설정을 로드하고 Pydantic 모델로 파싱하여 검증된 설정 객체를 반환합니다.
3. **CLI Context (`src/cli/context.py`):** 애플리케이션의 전역 상태(콘솔, 로거 등)를 담는 데이터 클래스. 액션 함수에 의존성으로 주입됩니다.
4. **Action Functions (`src/cli/actions/`):** 실제 실행될 함수들을 모듈로 정의합니다. (예: `src/cli/actions/profile_actions.py`)
5. **Command Parser & Dispatcher (`src/cli/main.py`):** 사용자 입력을 파싱하고, 설정에 명시된 액션(`target`)을 `importlib`으로 동적으로 로드하여 실행합니다.
6. **Main CLI Loop (`src/cli/main.py`):** 주 실행 루프. `prompt_toolkit`을 사용하여 사용자에게 프롬프트를 표시하고, 입력을 받아 파서에 전달합니다.

### 4.2. 명령어 설정 스키마 (Command Configuration Schema with Pydantic)

Pydantic 모델을 통해 설정의 무결성을 보장합니다. 계층적 명령어를 지원하기 위해 재귀적 모델 구조를 사용합니다.

```python
# src/cli/config/models.py
from typing import Dict, List, Optional, constr
from pydantic import BaseModel, Field

class Command(BaseModel):
    description: str = Field(..., description="명령어에 대한 설명 (help 메시지에 사용)")
    target: Optional[constr(min_length=1)] = Field(None, description="'module.function' 형태의 실행 함수 경로")
    sub_commands: Optional[Dict[str, 'Command']] = Field(None, description="하위 명령어 딕셔너리")

class CommandConfig(BaseModel):
    commands: Dict[str, Command]
```

**예시 설정 (`src/cli/config/command_layout.py`):**

```python
# Raw Python dictionary
COMMAND_LAYOUT = {
    "profile": {
        "description": "사용자 프로필 관리",
        "sub_commands": {
            "nickname": {
                "description": "닉네임 관련 명령어",
                "sub_commands": {
                    "check": {
                        "description": "닉네임 중복 확인",
                        "target": "src.cli.actions.profile.check_nickname",
                    },
                    "register": {
                        "description": "닉네임 등록",
                        "target": "src.cli.actions.profile.register_nickname",
                    },
                },
            },
        },
    },
    "survey": {
        "description": "설문조사 관리",
        "sub_commands": {
            "schema": {
                "description": "Survey 폼 스키마 조회",
                "target": "src.cli.actions.survey.get_schema",
            }
        }
    },
    "exit": {
        "description": "CLI를 종료합니다.",
        "target": "src.cli.actions.system.exit_cli",
    }
}
```

### 4.3. CLI 상태 흐름 (CLI State Flow)

- **Command Parsing:** 사용자가 `profile nickname check`와 같은 명령어를 입력하면, `main.py`의 파서는 공백을 기준으로 문자열을 분리합니다 (`['profile', 'nickname', 'check']`).
- **Recursive Search:** 파서는 `COMMAND_LAYOUT` 설정을 재귀적으로 탐색하며 각 토큰에 해당하는 `sub_commands`를 찾아 들어갑니다.
- **Action Execution:** 최종 명령어 토큰(`check`)에 도달하면, 해당 `Command` 객체의 `target`(`src.cli.actions.profile.check_nickname`)을 가져와 동적으로 임포트하고 `CLIContext`를 주입하여 실행합니다.

## 5. 단계별 구현 계획 (Step-by-Step Implementation Plan)

### Step 1: 범용 프로젝트 구조 설정

```
/ProjectX/
├── src/
│   └── cli/
│       ├── __init__.py
│       ├── main.py
│       ├── context.py
│       ├── config/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── loader.py
│       │   └── command_layout.py  # 프로젝트별 명령어 레이아웃
│       └── actions/
│           ├── __init__.py
│           ├── profile_actions.py # 도메인별 액션 함수
│           └── survey_actions.py
├── tests/
│   └── cli/
│       ├── __init__.py
│       └── test_cli_flow.py
├── requirements.txt
└── run.py
```

### Step 2: 컨텍스트 및 설정 로더 구현

**`src/cli/context.py`:** (변경 없음)
**`src/cli/config/loader.py`:**

```python
from src.cli.config.models import CommandConfig
from src.cli.config.command_layout import COMMAND_LAYOUT

def load_config() -> CommandConfig:
    """설정을 로드하고 Pydantic 모델로 검증합니다."""
    return CommandConfig(commands=COMMAND_LAYOUT)
```

### Step 3: 액션 함수 정의 (`src/cli/actions/profile_actions.py`)

```python
from src.cli.context import CLIContext

def check_nickname(context: CLIContext, *args):
    """닉네임 중복을 확인하는 액션"""
    context.console.print(f"[bold green]Executing: check_nickname with args: {args}[/bold green]")
    context.logger.info(f"Ran check_nickname action with args: {args}.")
    # 실제 로직 구현...
```

### Step 4: 메인 CLI 루프 구현 (`src/cli/main.py`)

`prompt_toolkit`을 사용한 메인 루프와 명령어 파서를 구현합니다.

```python
import importlib
import logging
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
# ... (기타 imports)
from src.cli.context import CLIContext
from src.cli.config.loader import load_config

def find_command(config, parts):
    # 재귀적으로 설정에서 명령어 찾는 로직
    # ...
    pass

def run_cli():
    # --- 초기화 ---
    console = Console()
    # ... (로거, 컨텍스트 초기화)
    
    try:
        config = load_config()
    except Exception as e:
        # ... (설정 로드 실패 처리)
        return

    session = PromptSession(history=FileHistory('.cli_history'))

    # --- 메인 루프 ---
    while True:
        try:
            text = session.prompt('> ', auto_suggest=AutoSuggestFromHistory())
            parts = text.strip().split()
            if not parts:
                continue
            
            command_key = parts[0]
            if command_key == 'exit':
                break

            # 1. 명령어 파싱 및 액션 찾기
            # ... (find_command 로직 호출)
            
            # 2. 동적 액션 디스패치 및 실행
            # module_path, func_name = target.rsplit('.', 1)
            # ... (importlib 로직)
            # action_func(context, *args)

        except (KeyboardInterrupt, EOFError):
            break # Ctrl-C, Ctrl-D 처리
        except Exception as e:
            console.print(f"[bold red]오류 발생: {e}[/bold red]")

    console.print("CLI를 종료합니다.")
```

## 6. 확장 설계 가이드라인 (Extended Design Guidelines)

### 6.1. 설정 로딩 파이프라인

1. **Load**: `src/cli/config/command_layout.py`에서 원시 딕셔너리를 로드합니다.
2. **Validate**: `src/cli/config/loader.py`의 `load_config` 함수가 이 딕셔너리를 `CommandConfig` Pydantic 모델에 전달하여 구조, 타입, 값의 유효성을 검사합니다.
3. **Return**: 검증된 `CommandConfig` 객체를 반환합니다.

### 6.2. 표준 액션 계약 (Standard Action Contract)

모든 액션 함수는 가변 인자를 받을 수 있도록 시그니처를 정의하는 것이 좋습니다.

```python
def my_action_function(context: CLIContext, *args, **kwargs) -> None:
```

- **`context: CLIContext`**: CLI의 공용 객체에 접근하기 위한 유일한 통로.
- **`*args, **kwargs`**: 명령어 뒤에 따라오는 파라미터나 옵션을 유연하게 처리하기 위함.

### 6.3. `CLIContext` 데이터 클래스

(기존과 동일, 의존성 컨테이너 역할)

## 7. 견고성, UX, 및 테스트 전략

### 7.1. 에러 핸들링 및 로깅

(기존과 동일, `try...except` 블록으로 액션 실행을 감싸고 로깅)

### 7.2. UX 및 접근성

- **자동 완성**: `prompt_toolkit`의 `Completer`를 구현하여, 사용자가 `profile`을 입력하고 탭 키를 누르면 `nickname`과 같은 하위 명령어를 추천해줍니다.
- **명령어 히스토리**: `FileHistory`를 통해 CLI 재시작 시에도 이전 명령어를 기억하고 재사용할 수 있게 합니다.
- **도움말 (`help` 명령어):** `help` 명령어를 구현하여, 현재 컨텍스트에서 사용 가능한 명령어 목록과 설명을 동적으로 생성하여 보여줍니다.

### 7.3. 테스트 전략 (구체적인 파일 예시 포함)

1. **단위 테스트 (`tests/cli/test_unit_actions.py`):** (기존과 동일)
2. **통합 테스트 (`tests/cli/test_integration_config.py`):** (기존과 동일, `CommandConfig` 테스트)
3. **기능(E2E) 테스트 (`tests/cli/test_e2e_commands.py`):**
    - `pexpect` 또는 `pytest-console-scripts`를 사용하여 `run.py`를 자식 프로세스로 실행합니다.
    - `child.sendline('profile nickname check')`와 같이 **명령어 문자열을 직접 전송**하여 시나리오를 테스트합니다.
    - 터미널 출력이 예상과 일치하는지 검증합니다.

## 8. 예시 사용 흐름 (Example Usage Flow)

1. `python run.py` 실행.
2. 프롬프트 `>`가 표시됨.
3. 사용자가 `profile nickname check` 입력 후 엔터.
4. `src.cli.actions.profile.check_nickname` 함수가 동적으로 로드되어 `context` 객체와 함께 실행됨.
5. 콘솔에 실행 결과가 출력되고, `cli.log` 파일에 로그가 기록됨.
6. 다시 프롬프트 `>`가 표시되며 다음 입력을 대기.
7. 사용자가 `exit` 입력 시 CLI 종료.

## 9. 빠른 시작 가이드 (Easy Next Steps)

1. **(1) 환경 설정:** `requirements.txt`에 `rich`, `prompt_toolkit`, `pydantic`을 명시하고 설치합니다. (`pip install rich prompt_toolkit pydantic`)
2. **(2) 명령어 정의:** `src/cli/config/command_layout.py`에 첫 번째 명령어를 정의합니다.
3. **(3) 액션 구현:** `src/cli/actions/` 디렉터리에 명령어에 연결할 함수를 `(context: CLIContext, *args)` 시그니처에 맞게 작성합니다.
4. **(4) 실행 및 확인:** `python run.py`를 실행하여 프롬프트가 표시되고 명령어가 호출되는지 확인합니다.
5. **(5) 테스트 작성:** `tests/cli/` 디렉터리에 방금 작성한 액션에 대한 단위 테스트를 추가합니다.
6. **(6) 반복 및 확장:** 새로운 명령어를 추가하고, 자동 완성 로직을 구현하며 점진적으로 개발합니다.
