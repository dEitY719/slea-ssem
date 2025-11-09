# Dynamic CLI Design Specification (V2.1)

## 1. 개요 (Overview)

본 문서는 Python을 활용하여, Gemini CLI와 유사한 동적이고 인터랙티브한 CLI 애플리케이션을 구축하기 위한 **고급 설계 명세**입니다. 이 설계의 핵심 목표는 메뉴 구조를 외부 설정 파일로부터 동적으로 로드하고, **Pydantic을 통한 강력한 유효성 검사**, **액션의 동적 임포트**, **컨텍스트 객체를 통한 의존성 주입**을 구현하여, 유지보수성과 확장성이 뛰어난 프레임워크를 제공하는 것입니다.

**최종 목표:**

- 대메뉴/중메뉴 구조를 정의한 설정 파일을 기반으로 동적 CLI 인터페이스를 생성합니다.
- `rich`를 활용하여 시각적으로 미려하고 사용자 친화적인 UI(Breadcrumbs 포함)를 제공합니다.
- 각 메뉴 항목에 연결된 특정 Python 함수(액션)를 **동적으로 로드하고 실행**합니다.
- 에러 핸들링, 로깅, 테스트 용이성을 포함한 견고한 애플리케이션을 구축합니다.

## 2. 핵심 요구사항 (Core Requirements)

- **설정 기반 동적 메뉴 (Config-Driven Dynamic Menus):** CLI 구조는 Pydantic 모델로 검증된 설정 객체로부터 런타임에 생성되어야 한다.
- **계층적 탐색 및 상태 (Hierarchical Navigation & State):** Breadcrumbs를 포함한 계층적 탐색을 지원하며, 메뉴 이동은 스택(Stack)을 통해 결정론적으로 관리되어야 한다.
- **인터랙티브 컨트롤 (Interactive Control):** `questionary`를 통해 키보드로 메뉴를 선택해야 한다.
- **동적 액션 디스패치 (Dynamic Action Dispatching):** 설정에 명시된 액션을 동적으로 임포트하여 실행해야 한다.
- **의존성 주입 (Dependency Injection):** `CLIContext` 데이터 클래스를 통해 콘솔, 로거, 설정 등 공용 객체를 각 액션 함수에 주입해야 한다.
- **견고성 및 회복성 (Robustness & Resilience):** 액션 실행 중 발생하는 예외를 우아하게 처리하고, 모든 중요한 이벤트를 로깅해야 한다.
- **테스트 용이성 (Testability):** 각 컴포넌트(액션, 설정 로더 등)는 단위 테스트가 가능해야 하며, 전체 CLI 흐름은 기능 테스트가 가능해야 한다.

## 3. 주요 기술 스택 (Key Technologies)

- **Python 3.9+:** 핵심 프로그래밍 언어.
- **`rich`:** 터미널 UI 렌더링.
- **`questionary`:** 인터랙티브 사용자 입력 처리.
- **`pydantic`:** 설정 파일의 구조와 값에 대한 강력한 유효성 검사를 위함.
- **`importlib` (Standard Library):** 액션 함수를 문자열 경로로부터 동적으로 임포트하기 위함.

## 4. 아키텍처 설계 (Architectural Design)

애플리케이션은 **설정 기반(Configuration-Driven)** 아키텍처를 따르며, 각 컴포넌트는 명확히 분리된 역할을 수행합니다.

![CLI Architecture Diagram V2](https://mermaid-js.github.io/mermaid-live-editor/eyJjb2RlIjoiZ3JhcGggVERcbiAgICBzdWJncmFwaCBJbml0aWFsaXphdGlvblxuICAgICAgQVtSYXcgQ29uZmlnIChESUNUKV0gLS0-fFZhbGlkYXRlfCBCW0NvbmZpZyBMb2FkZXIgKFB5ZGFudGljKV1cbiAgICAgIEIgLS0-IENbQ0xJQ29udGV4dCBJbnN0YW5jZV1cbiAgICBlbmRcblxuICAgIHN1YnJhcGggTWFpbiBFdmVudCBMb29wXG4gICAgICBDIC0uLT4gRFtNYWluIENMSSBMb29wXVxuICAgICAgRCAtLT58RGlzcGxheSBCcmVhZGNydW1ic3wgRVtNZW51IFJlbmRlcmVyIChyaWNoKV1cbiAgICAgIEUgLS0-fERpc3BsYXkgT3B0aW9uc3wgRVxuICAgICAgRCAtLT58R2V0IElucHV0fCBGW0lucHV0IEhhbmRsZXIgKHF1ZXN0aW9uYXJ5KV1cbiAgICAgIEYgLS0-fFVzZXIgU2VsZWN0aW9ufCBEXG4gICAgICBEIC0tPnxFeGVjdXRlfCBHW0FjdGlvbiBEaXNwYXRjaGVyIChpbXBvcnRsaWIpXVxuICAgICAgIEcgLS0-fEluanplY3QgQ29udGV4dHwgSFtBY3Rpb24gRnVuY3Rpb25dXG4gICAgICBIIEtFeGVjdXRlIFdpdGggQ29udGV4dF0gLS0-fExvZyAmIEVycm9yIEhhbmRsaW5nfCBEXG4gICAgZW5kXG4iLCJtZXJtYWlkIjp7InRoZW1EcmF3ZEJESiI6dHJ1ZX0sInVwZGF0ZUVkaXRvciI6ZmFsc2UsImF1dG9TeW5jIjp0cnVlLCJ1cGRhdGVEaWFncmFtIjpmYWxzZX0)

### 4.1. 컴포넌트 분리 (Component Breakdown)

1. **Configuration Models (`src/cli/config/models.py`):** Pydantic 모델을 사용하여 메뉴 설정의 스키마를 정의하고 유효성을 검사합니다.
2. **Config Loader (`src/cli/config/loader.py`):** 원시 딕셔너리 설정을 로드하고 Pydantic 모델로 파싱하여 검증된 설정 객체를 반환합니다.
3. **CLI Context (`src/cli/context.py`):** 애플리케이션의 전역 상태(콘솔, 로거, 사용자 정보 등)를 담는 데이터 클래스. 액션 함수에 의존성으로 주입됩니다.
4. **Action Functions (`src/cli/actions/`):** 실제 실행될 함수들을 모듈로 정의합니다. (예: `src/cli/actions/project_x_actions.py`)
5. **Dynamic Action Dispatcher (`src/cli/main.py`):** `importlib`을 사용하여 설정에 명시된 문자열 경로(예: `src.cli.actions.project_x_actions.list_files`)를 기반으로 함수를 동적으로 로드하고 실행합니다.
6. **Main CLI Loop (`src/cli/main.py`):** 주 실행 루프. **Breadcrumbs**를 포함한 현재 메뉴를 렌더링하고, 사용자 입력을 받아 서브 메뉴 진입/액션 실행을 결정합니다. **Navigation Stack**을 통해 메뉴 이동을 관리합니다.

### 4.2. 메뉴 설정 스키마 (Menu Configuration Schema with Pydantic)

Pydantic 모델을 통해 설정의 무결성을 보장합니다.

```python
# src/cli/config/models.py
from enum import Enum
from typing import Dict, constr
from pydantic import BaseModel, Field, field_validator

class MenuType(str, Enum):
    SUB_MENU = "SUB_MENU"
    ACTION = "ACTION"

class MenuItem(BaseModel):
    name: constr(min_length=1) = Field(..., description="메뉴에 표시될 이름")
    type: MenuType = Field(..., description="메뉴의 타입 (서브메뉴 또는 액션)")
    target: constr(min_length=1) = Field(
        ..., 
        description="SUB_MENU의 경우 다음 메뉴의 키, ACTION의 경우 'module.function' 형태의 경로"
    )

class Menu(BaseModel):
    meta: Dict[str, str] = Field(..., alias="_meta", description="메뉴의 메타 정보 (예: 제목)")
    items: Dict[str, MenuItem]

    @field_validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError("메뉴에는 최소 하나 이상의 항목이 있어야 합니다.")
        return v

class MenuConfig(BaseModel):
    menus: Dict[str, Menu]
```

**예시 설정 (`src/cli/config/menu_layout.py`):**

```python
# Raw Python dictionary
MENU_LAYOUT = {
    "main": {
        "_meta": {"title": "메인 메뉴 (Main Menu)"},
        "items": {
            "file_management": {
                "name": "📁 파일 관리",
                "type": "SUB_MENU",
                "target": "file_menu",
            },
        },
    },
    "file_menu": {
        "_meta": {"title": "파일 관리"},
        "items": {
            "list_files": {
                "name": "📄 파일 목록 보기",
                "type": "ACTION",
                "target": "src.cli.actions.file_ops.list_files", # 동적 임포트를 위한 전체 경로
            },
        },
    },
}
```

### 4.3. CLI 상태 흐름 (CLI State Flow)

- **Navigation Stack:** `['main', 'file_menu']`와 같이 현재 메뉴 경로를 추적하는 리스트. `pop()`으로 '뒤로 가기', `append()`로 '진입'을 결정론적으로 처리합니다.
- **Breadcrumbs:** Navigation Stack을 ` > ` 문자로 조합하여 (`메인 메뉴 > 파일 관리`) 사용자에게 현재 위치를 명확히 알려줍니다.
- **Event Loop:** `while menu_stack:` 루프는 사용자가 '종료'를 선택하거나 스택이 빌 때까지 계속됩니다. 각 루프는 메뉴 렌더링, 입력 대기, 선택 처리를 순차적으로 수행합니다.

## 5. 단계별 구현 계획 (Step-by-Step Implementation Plan)

### Step 1: 범용 프로젝트 구조 설정

이 CLI 프레임워크는 다른 프로젝트에 쉽게 통합될 수 있도록 설계되었습니다. 다음은 `ProjectX`와 같은 신규 프로젝트에 `src/cli`로 통합하는 경우의 권장 구조입니다.

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
│       │   └── menu_layout.py  # 프로젝트별 메뉴 레이아웃
│       └── actions/
│           ├── __init__.py
│           └── project_x_actions.py # 프로젝트별 액션 함수
├── tests/
│   └── cli/
│       ├── __init__.py
│       └── test_cli_flow.py
├── requirements.txt
└── run.py  # CLI 실행 스크립트 (예: `from src.cli import main; main.run_cli()`)
```

**주요 변경 사항:**

- **모듈화**: 기존 `dynamic_cli`는 `src/cli` 디렉토리로 이동하여, 다른 Python 프로젝트에 서브모듈로 쉽게 포함될 수 있습니다.
- **테스트 분리**: CLI 관련 테스트는 프로젝트 레벨의 `tests/cli` 디렉토리로 분리하여, 프로젝트의 다른 테스트와 함께 관리됩니다.
- **실행 진입점**: 프로젝트 루트에 `run.py`와 같은 실행 스크립트를 두어 CLI를 시작합니다.

### Step 2: 컨텍스트 및 설정 로더 구현

**`src/cli/context.py`:**

```python
from dataclasses import dataclass
from logging import Logger
from rich.console import Console

@dataclass
class CLIContext:
    console: Console
    logger: Logger
    # 여기에 사용자 정보 등 추가 가능
```

**`src/cli/config/loader.py`:**

```python
from src.cli.config.models import MenuConfig
from src.cli.config.menu_layout import MENU_LAYOUT

def load_config() -> MenuConfig:
    """설정을 로드하고 Pydantic 모델로 검증합니다."""
    return MenuConfig(menus=MENU_LAYOUT)
```

### Step 3: 액션 함수 정의 (`src/cli/actions/file_ops.py`)

표준화된 액션 계약(Context를 인자로 받음)을 따릅니다.

```python
from src.cli.context import CLIContext

def list_files(context: CLIContext):
    """파일 목록을 보여주는 액션"""
    context.console.print("[bold green]Executing: list_files[/bold green]")
    context.logger.info("Ran list_files action.")
    # 실제 로직 구현...
```

### Step 4: 메인 CLI 루프 구현 (`src/cli/main.py`)

Breadcrumbs, 동적 디스패치, 에러 핸들링을 포함합니다.

```python
import importlib
import logging
from src.cli.context import CLIContext
from src.cli.config.loader import load_config
# ... (기타 imports, 예: from rich.panel import Panel, from .config.models import MenuType)

def run_cli():
    # --- 초기화 ---
    console = Console()
    logging.basicConfig(level="INFO", filename="cli.log", filemode="w")
    logger = logging.getLogger(__name__)
    context = CLIContext(console=console, logger=logger)
    
    try:
        config = load_config()
        logger.info("Configuration loaded and validated successfully.")
    except Exception as e:
        context.console.print(f"[bold red]설정 파일 로드 실패:[/bold red] {e}")
        logger.critical(f"Configuration loading failed: {e}", exc_info=True)
        return

    menu_stack = ["main"]

    # --- 메인 루프 ---
    while menu_stack:
        current_menu_key = menu_stack[-1]
        current_menu = config.menus[current_menu_key]

        # 1. Breadcrumbs 렌더링
        # (rich Panel, questionary 등 UI 관련 로직 필요)
        # breadcrumbs = " > ".join(...)
        # context.console.print(Panel(f"[cyan]{breadcrumbs}[/cyan]"))

        # 2. 옵션 구성 및 사용자 입력
        # ... (questionary 로직)
        # choice_key = ...

        # 3. 선택 처리
        # ... (뒤로가기, 종료 로직)

        selected_item = current_menu.items[choice_key]

        if selected_item.type == MenuType.SUB_MENU:
            menu_stack.append(selected_item.target)
        
        elif selected_item.type == MenuType.ACTION:
            try:
                # 4. 동적 액션 디스패치 및 실행
                module_path, func_name = selected_item.target.rsplit('.', 1)
                module = importlib.import_module(module_path)
                action_func = getattr(module, func_name)
                
                # 의존성 주입
                action_func(context)

            except (ImportError, AttributeError) as e:
                context.logger.error(f"Action loading failed for '{selected_item.target}': {e}")
                context.console.print(f"[bold red]액션 실행 실패: {selected_item.target}[/bold red]")
            except Exception as e:
                context.logger.exception(f"An unexpected error occurred during action '{selected_item.target}'")
                context.console.print(f"[bold red]오류 발생: {e}[/bold red]")
            
            # ... (액션 실행 후 대기)
```

## 6. 확장 설계 가이드라인 (Extended Design Guidelines)

### 6.1. 설정 로딩 파이프라인

1. **Load**: `src/cli/config/menu_layout.py`에서 원시 딕셔너리를 로드합니다.
2. **Validate**: `src/cli/config/loader.py`의 `load_config` 함수가 이 딕셔너리를 `MenuConfig` Pydantic 모델에 전달하여 구조, 타입, 값의 유효성을 검사합니다.
3. **Return**: 검증된 `MenuConfig` 객체를 반환합니다. 실패 시, Pydantic이 상세한 오류를 발생시켜 즉시 문제를 파악할 수 있습니다.

### 6.2. 표준 액션 계약 (Standard Action Contract)

모든 액션 함수는 반드시 아래 시그니처를 따라야 합니다.

```python
def my_action_function(context: CLIContext) -> None:
```

- **`context: CLIContext`**: CLI의 공용 객체(콘솔, 로거 등)에 접근하기 위한 유일한 통로입니다. 전역 변수 사용을 지양하고 테스트 용이성을 높입니다.
- **`-> None`**: 액션 함수는 값을 반환하지 않고, 모든 출력과 상태 변경을 `context`를 통해 수행해야 합니다.

### 6.3. `CLIContext` 데이터 클래스

`CLIContext`는 애플리케이션의 "의존성 컨테이너" 역할을 합니다. 액션 함수에 필요한 모든 것을 이 클래스에 추가하여 전달할 수 있습니다.

- **장점**:
  - **명시적인 의존성**: 함수가 무엇을 필요로 하는지 시그니처만 봐도 알 수 있습니다.
  - **테스트 용이성**: 단위 테스트 시, 실제 객체 대신 Mock `CLIContext` 객체를 쉽게 주입할 수 있습니다.
  - **중앙 관리**: 모든 공용 객체가 한 곳에서 관리됩니다.

## 7. 견고성, UX, 및 테스트 전략

### 7.1. 에러 핸들링 및 로깅

- 모든 액션 실행은 `try...except` 블록으로 감싸, 특정 액션의 실패가 전체 CLI의 중단으로 이어지지 않도록 합니다.
- `logging` 모듈을 사용하여 모든 예외의 전체 트레이스백을 로그 파일(`cli.log`)에 기록하여 사후 분석을 용이하게 합니다.
- 사용자에게는 친절한 오류 메시지(예: "액션 실행 실패")를 보여주고, 상세 내용은 로그 파일을 참조하도록 안내합니다.

### 7.2. UX 및 접근성

- **일관성**: 모든 메뉴와 프롬프트는 일관된 스타일과 구조를 유지합니다.
- **명확성**: Breadcrumbs를 통해 사용자가 현재 위치를 항상 인지할 수 있도록 합니다.
- **색상 대비**: `rich`의 테마 기능을 활용하여 가독성이 좋은 색상 대비를 사용합니다.
- **도움말**: 각 메뉴의 `_meta` 정보에 `description` 필드를 추가하여, 메뉴 진입 시 상단에 간단한 안내 문구를 보여주는 기능을 구현할 수 있습니다.

### 7.3. 테스트 전략 (구체적인 파일 예시 포함)

프로젝트의 최상위 `tests/cli/` 디렉터리에 모든 CLI 관련 테스트를 위치시켜 명확성을 높입니다.

1. **단위 테스트 (`tests/cli/test_unit_actions.py`):**
    - Mock `CLIContext` 객체를 생성하여 `src/cli/actions/`에 있는 개별 액션 함수를 독립적으로 테스트합니다.
    - `context.console.print`와 같은 `rich` 콘솔 호출이 올바른 인자와 함께 발생했는지 검증합니다.
    - `context.logger.info`와 같은 로깅 호출을 검증합니다.

2. **통합 테스트 (`tests/cli/test_integration_config.py`):**
    - 설정 로더(`src/cli/config/loader.py`)가 유효하거나 유효하지 않은 설정 딕셔너리를 올바르게 처리하는지 테스트합니다. 유효하지 않은 스키마에 대해 `Pydantic`의 `ValidationError`가 발생하는지 확인합니다.
    - 동적 임포트 메커니즘이 `target` 경로 (`src.cli.actions.*`)를 기반으로 실제 함수를 정확히 로드하는지 검증합니다.

3. **기능(E2E) 테스트 (`tests/cli/test_e2e_navigation.py`):**
    - `pexpect` 또는 `pytest-console-scripts`와 같은 라이브러리를 사용하여 `run.py`를 자식 프로세스로 실행합니다.
    - 키보드 입력(방향키, 엔터 등)을 시뮬레이션하여 메뉴 탐색, 액션 실행, 뒤로 가기, 종료 등 전체 사용자 시나리오가 예상대로 동작하는지 검증합니다.
    - 최종 터미널 출력이 예상과 일치하는지 스냅샷 테스팅을 활용할 수 있습니다.

## 8. 예시 사용 흐름 (Example Usage Flow)

1. `python run.py` 실행.
2. `[cyan]메인 메뉴 (Main Menu)[/cyan]` Breadcrumbs와 함께 메인 메뉴가 표시됨.
3. 사용자가 `📁 파일 관리` 선택.
4. `[cyan]메인 메뉴 (Main Menu) > 파일 관리[/cyan]` Breadcrumbs와 함께 파일 관리 메뉴가 표시됨.
5. 사용자가 `📄 파일 목록 보기` 선택.
6. `src.cli.actions.file_ops.list_files` 함수가 동적으로 로드되어 `context` 객체와 함께 실행됨.
7. 콘솔에 실행 결과가 출력되고, `cli.log` 파일에 "Ran list_files action." 로그가 기록됨.
8. ... (이하 흐름 동일)

## 9. 빠른 시작 가이드 (Easy Next Steps)

이 설계를 바탕으로 개발을 시작하기 위한 간단한 체크리스트입니다.

1. **(1) 환경 설정:** `requirements.txt`에 명시된 `rich`, `questionary`, `pydantic`을 설치합니다. (`pip install rich questionary pydantic`)
2. **(2) 메뉴 정의:** `src/cli/config/menu_layout.py`에 첫 번째 메뉴와 액션을 정의합니다.
3. **(3) 액션 구현:** `src/cli/actions/` 디렉터리에 메뉴에 연결할 간단한 함수를 `(context: CLIContext)` 시그니처에 맞게 작성합니다.
4. **(4) 실행 및 확인:** `python run.py`를 실행하여 메뉴가 표시되고 액션이 호출되는지 확인합니다.
5. **(5) 테스트 작성:** `tests/cli/` 디렉터리에 방금 작성한 액션에 대한 단위 테스트 (`test_unit_actions.py`)를 추가합니다.
6. **(6) 반복 및 확장:** 새로운 메뉴와 액션을 추가하고, 테스트를 보강하며 점진적으로 개발합니다.
