# SLEA-SSEM (S.LSI Education AI Teacher)

**[kr-한국어]** | [en-English](README.en.md)

S.LSI 임직원을 위한 AI 교육 코칭 에이전트 'slea-ssem(슬아쌤)' 프로젝트입니다.
S.LSI의 AI 역량(EA: Education/AI)을 높이는 '쌤(SSEM)'이 되겠다는 의미를 담고 있습니다.

---

## 🚀 Quick Start (개발자용)

### 1. Claude Code CLI 설치

```bash
# Homebrew (macOS)
brew install anthropics/tap/claude

# npm (Windows/Linux)
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version
```

### 2. 프로젝트 설정

```bash
# Repository clone
git clone <repo-url>
cd slea-ssem

# 개발 환경 설정
cp .env.example .env

# .env 파일에서 DEVELOPER_NAME을 수정
# 예: DEVELOPER_NAME=bwyoon → DEVELOPER_NAME=<your-name>
nano .env  # 또는 원하는 에디터 사용
```

### 3. 의존성 설치 및 개발 서버 시작

```bash
# 의존성 설치
pip install .[dev]             # pyproject.toml 파일 경로에서 수행

# alembic 준비
alembic init alembic

# 첫 실행
./tools/dev.sh up              # 개발 서버 시작 (localhost:8000)

# 다른 터미널에서
./tools/dev.sh test            # 테스트 실행
./tools/dev.sh format          # 코드 포맷 + 린트
```

### 4. REQ 기반 개발 (main workflow)

**1문장으로 기능 구현 요청하기:**

```bash
# Claude Code CLI에서
claude

# 프롬프트에서:
> REQ-B-A2-Edit-1 기능 구현해

# 자동 실행:
# Phase 1: Specification (명세 작성) → 당신의 승인 대기
# Phase 2: Test Design (테스트 설계) → 당신의 승인 대기
# Phase 3: Implementation (코드 구현) + 검증
# Phase 4: Summary (결과 보고) + git commit
```

---

## 📋 개발 프로세스 상세

### REQ 기반 개발 (Requirement-Driven Development)

모든 기능은 `docs/feature_requirement_mvp1.md`에 정의된 REQ ID를 기준으로 개발됩니다.

**Request Format:**

```
REQ-[Domain]-[Feature] 기능 구현해
```

**Example:**

```
REQ-B-A2-Edit-1 기능 구현해         # 닉네임 변경 기능
REQ-F-1-Login 기능 구현해           # 로그인 기능
REQ-A-1-Dashboard 기능 구현해       # 대시보드 기능
```

### 개발자 진행상황 추적

각 REQ 개발 시 진행상황은 자동으로 `docs/progress/` 디렉토리에 기록됩니다:

```
docs/
└── progress/
    ├── REQ-B-A2-Edit-1.md         # bwyoon 개발 중
    ├── REQ-F-1-Login.md           # lavine 개발 중
    └── REQ-A-1-Dashboard.md       # team progress
```

전체 팀 진행상황은 `docs/DEV-PROGRESS.md`에서 확인할 수 있습니다.

---

## 📚 Main Feature

Two-round adaptive testing with RAG-based dynamic question generation, LLM auto-scoring, and ranking system.

**Key Components:**

- 🎯 **Adaptive Testing**: 라운드별 난이도 조정
- 🤖 **AI Question Generation**: LLM 기반 동적 문항 생성
- 📊 **Auto-Scoring**: MC (정확 매칭) + Short Answer (LLM 채점)
- 🏆 **Ranking System**: 글로벌 순위, 백분위수, 카테고리별 분석

---

## 📖 Documentation

- **Requirements**: [`docs/feature_requirement_mvp1.md`](docs/feature_requirement_mvp1.md) - MVP 1.0 전체 요구사항
- **Development Guide**: [`CLAUDE.md`](CLAUDE.md) - 개발 규칙, 컨벤션, 워크플로우
- **User Scenarios**: [`docs/user_scenarios_mvp1.md`](docs/user_scenarios_mvp1.md) - 사용자 시나리오
- **Progress**: [`docs/DEV-PROGRESS.md`](docs/DEV-PROGRESS.md) - 팀 개발 진행상황

---

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + Alembic (migrations)
- **Package Manager**: uv
- **Testing**: pytest
- **Code Quality**: ruff, black, mypy (strict), pylint
- **AI**: LangChain + FastMCP

---

## 💬 Development Guidelines

모든 개발은 `CLAUDE.md`에 정의된 컨벤션을 따릅니다:

- **Type Hints**: 모든 public 함수에 필수
- **Docstrings**: Google 스타일
- **Line Length**: ≤ 120 chars
- **Testing**: TDD (Test-Driven Development)
- **Commits**: Conventional Commits (`feat:`, `fix:`, `test:` 등)

---

## Contributing

We welcome contributions from all developers!

**How to Contribute:**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Implement REQ with: `claude` → `REQ-X-Y 기능 구현해`
4. Push and open a Pull Request

For more details, see [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## 📝 License

[MIT License](LICENSE)
