# 이중 저장소 환경 협업 워크플로우

**상황**: 사외(공개 GitHub) + 회사 내(폐쇄 GitLab) 이중 저장소 환경에서 동료 2명과 협업
**목표**: 효율적인 코드 공유 및 개발 환경 관리

---

## 📋 현재 상황 분석

```
사외 환경 (공개)
  https://github.com/dEitY719/slea-ssem.git
       ↓ (clone 가능)
  회사 내 환경 (폐쇄)
  https://github.company.com/aig/slea-ssem.git
       ↓ (push 불가)
       ❌ 다시 사외로 공유 불가능
```

**문제점**:
- 일방향 흐름: 사외 → 회사만 가능
- 회사에서 개선된 코드를 사외로 공유 불가능
- 코드 동기화 오버헤드 증가

---

## ✅ 추천 워크플로우: Upstream/Downstream 모델

### 전체 흐름

```
┌─────────────────────────────────────────────────────────────┐
│ UPSTREAM (사외 공개 저장소)                                  │
│ https://github.com/dEitY719/slea-ssem.git                   │
│ ├─ main 브랜치 (안정적 릴리스)                               │
│ └─ develop 브랜치 (개발 통합)                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ↓                           ↓
┌──────────────────────┐   ┌──────────────────────┐
│ 개인 개발 환경        │   │ 회사 내부 환경        │
│ (로컬/WSL)          │   │ (회사 GitLab)        │
│                      │   │                      │
│ 사외 저장소 Clone    │   │ 1. 사외 clone       │
│ + upstream fetch     │   │ 2. 회사 설정 추가   │
│ + 기능 개발          │   │    (proxy, DB)      │
│ + Pull Request       │   │ 3. 회사 제약사항    │
│                      │   │    고려한 개발      │
└──────────────────────┘   └──────────────────────┘
        │                           │
        └─────────────┬─────────────┘
                      ↓
        📋 코드 리뷰 및 승인
        (사외 저장소에서 진행)
```

### 3가지 협업 모드

#### Mode 1: 사외에서만 개발 (권장 - 간단)

**언제 사용**: 회사 제약이 없거나, 회사에서도 공개 코드 개발 정책이 있을 때

```bash
# 모든 개발을 사외 저장소에서만 진행
1. 사외 저장소 clone
2. feature 브랜치에서 개발
3. Pull Request → Review → Merge to develop
4. Develop에서 검증 후 main으로 Release
5. (선택) 회사 내부 저장소에도 Mirror로 관리
```

**장점**: 간단함, 모든 협업 기록이 하나의 저장소에 중앙화
**단점**: 회사 내부 정책이 엄격하면 불가능

---

#### Mode 2: 회사 내에서는 Patch/Cherry-pick 방식 (중간 수준)

**언제 사용**: 회사에서는 폐쇄된 저장소를 써야 할 때, 기능별로 사외로 기여 가능

```bash
# 개인 개발 환경
$ git clone https://github.com/dEitY719/slea-ssem.git personal-slea
$ cd personal-slea
$ git remote add upstream https://github.com/dEitY719/slea-ssem.git
$ git fetch upstream
$ git checkout -b feature/my-feature upstream/develop

# 기능 개발 및 커밋
$ git add .
$ ./tools/commit.sh
$ git push origin feature/my-feature

# Pull Request 생성 (사외 저장소)
$ gh pr create --base develop

# 승인 후 Merge
```

```bash
# 회사 내부 환경 (매주 또는 월 1회)
$ cd company-slea
$ git remote add upstream https://github.com/dEitY719/slea-ssem.git
$ git fetch upstream develop

# 사외 저장소의 최신 코드를 회사 저장소에 가져오기
$ git merge upstream/develop
# (또는) git rebase upstream/develop

# 회사 DB 설정, proxy 등 적용
$ git add .
$ ./tools/commit.sh
$ git push origin develop
```

**장점**:
- 명확한 책임 분리 (사외: 공개 기능, 회사: 내부 설정)
- 사외 기여 가능
- 비용이 작음

**단점**:
- 수동 동기화 필요
- 버전 차이 발생 가능

---

#### Mode 3: 완전 분리 (고급 - 권장 안함)

**언제 사용**: 회사 코드와 사외 코드가 완전히 달라야 할 때 (드문 경우)

```bash
# 개별 Patch 파일로 공유
$ cd personal-slea
$ git format-patch upstream/develop..origin/feature/new-scoring
$ # 0001-feature-new-scoring.patch 생성

# 회사 저장소에서 Patch 적용
$ cd company-slea
$ git apply /path/to/0001-feature-new-scoring.patch
```

**단점**: 매우 복잡함, 권장하지 않음

---

## 🎯 권장안: Mode 2 + Docker

### 단계별 구현

#### Step 1: 개인 개발 환경 설정 (사외)

```bash
# 1. 사외 저장소 클론
git clone https://github.com/dEitY719/slea-ssem.git slea-personal
cd slea-personal

# 2. 원본 저장소 추적 설정
git remote add upstream https://github.com/dEitY719/slea-ssem.git
git remote set-url origin https://github.com/{YOUR-FORK}/slea-ssem.git

# 3. 최신 코드 가져오기
git fetch upstream
git checkout develop
git pull upstream develop

# 4. Feature 브랜치 생성
git checkout -b feature/new-feature upstream/develop
```

#### Step 2: 회사 내부 환경 설정

```bash
# 1. 회사 저장소 클론
git clone https://github.company.com/aig/slea-ssem.git slea-company
cd slea-company

# 2. Upstream으로 사외 저장소 추가
git remote add upstream https://github.com/dEitY719/slea-ssem.git

# 3. 초기 동기화
git fetch upstream develop
git merge upstream/develop
```

#### Step 3: 주기적 동기화 스크립트

**파일**: `tools/sync-with-upstream.sh`

```bash
#!/bin/bash
# 사외 저장소의 최신 코드를 가져오기

set -e

echo "🔄 Upstream에서 최신 코드 가져오는 중..."
git fetch upstream develop

echo "📝 Develop 브랜치로 전환..."
git checkout develop

echo "🔀 Upstream/develop과 머지..."
git merge upstream/develop

echo "✅ 동기화 완료!"
echo "💾 푸시하기: git push origin develop"
```

**사용**:
```bash
cd slea-company
chmod +x tools/sync-with-upstream.sh
./tools/sync-with-upstream.sh
git push origin develop
```

#### Step 4: 회사 특화 설정 관리

**파일**: `.env.company` (gitignore 처리)

```bash
# 회사 환경 변수
DB_HOST=company-db.internal.com
DB_PORT=5432
DB_USER=internal_user
HTTP_PROXY=proxy.company.com:8080
HTTPS_PROXY=proxy.company.com:8080
```

**파일**: `config/company.yaml` (gitignore 처리)

```yaml
# 회사 내부 설정
environment: company
database:
  host: company-db.internal.com
  pool_size: 10
features:
  enable_company_auth: true
  enable_metrics_export: true
```

---

## 🐳 Docker 기반 개발 환경 관리

### 문제: WSL 환경에서의 일관성

**현재 상황**:
- 개인: WSL + 로컬 PostgreSQL + Python venv
- 회사: WSL + 다른 PostgreSQL 버전 + 다른 Python 버전?
- 동료: 또 다른 OS/버전 조합?

→ **"내 환경에서는 되는데 회사에서는 안 됨" 문제 발생**

### 해결책: Docker + Docker Compose

#### 1단계: Docker 기본 개념

```
✅ Docker Image (청사진)
   = 애플리케이션 + 의존성 + 환경 설정

✅ Docker Container (실행 중인 인스턴스)
   = Image에서 만든 격리된 환경

✅ Docker Compose (다중 컨테이너 오케스트레이션)
   = Image들을 한 번에 실행 (DB + Backend + Redis 등)
```

#### 2단계: 프로젝트 Docker 구성

**파일 구조**:

```
slea-ssem/
├── Dockerfile              # Backend 이미지 정의
├── docker-compose.yml      # 모든 서비스 정의
├── docker-compose.prod.yml # 프로덕션용 (선택)
└── .dockerignore
```

#### 3단계: Dockerfile 작성

**파일**: `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    postgresql-client \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync

# 애플리케이션 복사
COPY . .

# 포트 노출
EXPOSE 8000

# 실행
CMD ["uv", "run", "uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 4단계: docker-compose.yml 작성

**파일**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL 데이터베이스
  db:
    image: postgres:15-alpine
    container_name: slea-db
    environment:
      POSTGRES_DB: sleassem_dev
      POSTGRES_USER: slea_user
      POSTGRES_PASSWORD: change_me_dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      # (선택) 초기 SQL 스크립트
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U slea_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI 백엔드
  backend:
    build: .
    container_name: slea-backend
    environment:
      DATABASE_URL: postgresql://slea_user:change_me_dev_password@db:5432/sleassem_dev
      PYTHONUNBUFFERED: 1
      LOG_LEVEL: INFO
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      # 개발 중 코드 변경 자동 반영
      - .:/app
    command: >
      sh -c "
        alembic upgrade head &&
        uv run uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload
      "

  # (선택) Redis 캐시
  redis:
    image: redis:7-alpine
    container_name: slea-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

#### 5단계: 개발 명령어 추가

**파일**: `tools/dev.sh` (기존에 추가)

```bash
#!/bin/bash

case "$1" in
  # 기존 명령어...

  docker-up)
    echo "🐳 Docker 환경 시작..."
    docker-compose up -d
    echo "✅ Backend: http://localhost:8000"
    echo "✅ DB: localhost:5432"
    ;;

  docker-down)
    echo "🛑 Docker 환경 중지..."
    docker-compose down
    ;;

  docker-logs)
    echo "📊 로그 보기..."
    docker-compose logs -f backend
    ;;

  docker-shell)
    echo "💻 컨테이너 셸 접속..."
    docker-compose exec backend bash
    ;;

  docker-test)
    echo "🧪 Docker 환경에서 테스트 실행..."
    docker-compose exec backend pytest tests/backend/ -v
    ;;

  *)
    echo "Docker 명령어:"
    echo "  docker-up     - Docker 환경 시작"
    echo "  docker-down   - Docker 환경 중지"
    echo "  docker-logs   - 실시간 로그"
    echo "  docker-shell  - 컨테이너 셸 접속"
    echo "  docker-test   - 테스트 실행"
    ;;
esac
```

#### 6단계: 회사 환경용 Compose 파일 (선택)

**파일**: `docker-compose.company.yml`

```yaml
version: '3.8'

# 기본 docker-compose.yml의 내용 + 회사 특화 설정
services:
  db:
    # 회사 DB 서버 연결
    image: postgres:15-alpine
    environment:
      # 회사 환경 변수
      POSTGRES_DB: sleassem_company
      POSTGRES_PASSWORD: ${DB_PASSWORD}  # .env.company에서 읽음
    ports:
      - "5432:5432"

  backend:
    environment:
      DATABASE_URL: postgresql://slea_user:${DB_PASSWORD}@db:5432/sleassem_company
      HTTP_PROXY: ${HTTP_PROXY}
      HTTPS_PROXY: ${HTTPS_PROXY}
```

**사용**:
```bash
# 회사 환경에서
./tools/dev.sh docker-up --company  # 아직 구현 필요
# 또는
docker-compose -f docker-compose.yml -f docker-compose.company.yml up -d
```

---

## 📊 Docker를 효율적으로 사용하기

### 핵심 개념

| 개념 | 설명 | 언제 사용 |
|------|------|---------|
| **Image** | 애플리케이션 + 의존성을 담은 스냅샷 | 빌드 시 |
| **Container** | 실행 중인 Image (격리된 프로세스) | 개발/테스트 |
| **Volume** | 호스트와 컨테이너 간 저장소 공유 | 데이터 영속성 |
| **Network** | 컨테이너 간 통신 | 서비스 연결 |
| **Compose** | YAML로 여러 컨테이너 정의 | 로컬/테스트 환경 |

### 개발 워크플로우

```bash
# 1. 초기 설정 (한 번만)
./tools/dev.sh docker-up

# 2. 코드 작성 (실시간 반영)
# docker-compose.yml의 volumes 섹션 때문에 자동 반영

# 3. 테스트
./tools/dev.sh docker-test

# 4. 로그 확인
./tools/dev.sh docker-logs

# 5. 문제 해결 (컨테이너 접속)
./tools/dev.sh docker-shell
$ pytest tests/backend/ -v  # 컨테이너 내부에서 실행

# 6. 종료
./tools/dev.sh docker-down
```

### 자주 하는 실수 및 해결

| 문제 | 원인 | 해결 |
|------|------|------|
| "Port 5432 already in use" | 기존 PostgreSQL이 실행 중 | `lsof -i :5432` 후 종료 |
| 컨테이너 실행 안 됨 | 이미지 오래됨 | `docker-compose build --no-cache` |
| 파일 변경이 반영 안 됨 | Volume 설정 문제 | `docker-compose exec backend ls` 확인 |
| DB 마이그레이션 실패 | 초기화 문제 | `docker-compose exec backend alembic upgrade head` |

---

## 🔄 회사 ↔ 사외 코드 동기화 전략

### Timeline (권장)

```
매주 금요일 (또는 스프린트 끝)
│
├─ 개인 환경에서 기능 개발 완료 (사외)
│  └─ Pull Request 생성 및 리뷰
│
├─ 승인 후 main 또는 develop에 Merge
│  └─ Tag 생성 (v1.0.0-rc1 등)
│
└─ 회사 내부 저장소에 동기화
   └─ git pull upstream develop
   └─ 회사 설정 + 프록시 적용
   └─ 테스트 검증
   └─ git push origin develop
```

### 동기화 체크리스트

```markdown
- [ ] 사외 저장소에서 최신 코드 확인
  ```bash
  cd slea-personal
  git fetch upstream
  git log upstream/develop -5 --oneline
  ```

- [ ] 회사 저장소에서 Upstream 추가 (한 번만)
  ```bash
  cd slea-company
  git remote add upstream https://github.com/dEitY719/slea-ssem.git
  ```

- [ ] 동기화 실행
  ```bash
  git fetch upstream develop
  git checkout develop
  git merge upstream/develop
  ```

- [ ] 회사 설정 파일 확인
  ```bash
  ls -la .env.company config/company.yaml
  git status  # Untracked인지 확인 (절대 커밋하면 안 됨)
  ```

- [ ] 테스트 실행
  ```bash
  ./tools/dev.sh docker-up
  ./tools/dev.sh docker-test
  ```

- [ ] 완료 후 푸시
  ```bash
  git push origin develop
  ```
```

---

## 📋 마이그레이션 체크리스트

### 개인 개발 환경 (사외)

- [ ] Fork 생성: https://github.com/{YOUR-ID}/slea-ssem.git
- [ ] 로컬 클론:
  ```bash
  git clone https://github.com/{YOUR-ID}/slea-ssem.git
  cd slea-ssem
  git remote add upstream https://github.com/dEitY719/slea-ssem.git
  ```
- [ ] Develop 브랜치 추적:
  ```bash
  git checkout develop
  git pull upstream develop
  ```
- [ ] Feature 브랜치 생성:
  ```bash
  git checkout -b feature/my-feature upstream/develop
  ```

### 회사 내부 환경

- [ ] 회사 저장소 클론
- [ ] Upstream 추가:
  ```bash
  git remote add upstream https://github.com/dEitY719/slea-ssem.git
  ```
- [ ] 초기 동기화:
  ```bash
  git fetch upstream develop
  git merge upstream/develop
  ```
- [ ] Docker 설정:
  ```bash
  cp .env.example .env.company
  # .env.company 편집 (DB 정보, 프록시 등)
  git add .gitignore  # .env.company 추가됨 확인
  ```
- [ ] 테스트:
  ```bash
  ./tools/dev.sh docker-up
  ./tools/dev.sh docker-test
  ```

### 동료들과의 협업

- [ ] 브랜치 전략 공유 (이 문서)
- [ ] Git remote 설정 가이드
- [ ] PR 작성 템플릿 (사외):
  ```markdown
  ## 개요
  기능/버그 수정 설명

  ## 변경 사항
  - [ ] 항목 1
  - [ ] 항목 2

  ## 테스트
  ```bash
  ./tools/dev.sh docker-test
  ```
  ```

---

## ❓ FAQ

### Q1: 회사 DB 정보를 실수로 GitHub에 올렸어요!

```bash
# 즉시 reset
git reset HEAD~1
git checkout -- .env.company

# 또는 이미 push했다면
git log --all --oneline | grep "company"
git revert <commit-sha>
git push
```

### Q2: 사외 저장소에서 아직 머지되지 않은 기능을 회사에서 써야 해요

```bash
# 방법 1: 해당 커밋만 cherry-pick
git fetch upstream
git cherry-pick <commit-sha>

# 방법 2: PR 브랜치 임시 가져오기
git fetch upstream pull/123/head:temp-pr-123
git merge temp-pr-123
```

### Q3: Docker 이미지 크기가 너무 커요

```bash
# 멀티스테이지 빌드 사용 (Dockerfile 개선)
FROM python:3.11-slim as builder
# ... 빌드 단계 ...

FROM python:3.11-slim
COPY --from=builder /app /app
# ... 최종 단계 ...
```

### Q4: 어떤 파일을 `.gitignore`에 추가해야 해요?

```
# .gitignore에 추가
.env
.env.company
.env.*.local
config/company.yaml
config/local.yaml
.venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
docker-compose.override.yml
```

### Q5: 회사에서 Python 버전이 3.10인데 프로젝트는 3.11을 요구해요

```dockerfile
# Dockerfile의 Python 버전을 3.10으로 변경
FROM python:3.10-slim

# 테스트
docker-compose up -d
docker-compose exec backend python --version
```

---

## 🚀 다음 단계

### 단기 (이번 주)
1. 이 문서를 팀에 공유
2. Docker 테스트 환경 구성
3. 기존 개발 환경과 동등성 검증

### 중기 (이번 달)
1. CI/CD 파이프라인 추가 (GitHub Actions)
2. 회사 환경용 자동 테스트 구성
3. Docker Hub에 공개 이미지 배포 (선택)

### 장기 (분기별)
1. Kubernetes 환경으로 확장 (선택)
2. 멀티 환경 배포 자동화
3. 성능 모니터링 대시보드

---

## 📚 참고 자료

- Docker 공식 문서: https://docs.docker.com/
- Docker Compose: https://docs.docker.com/compose/
- Git 브랜칭 전략: https://git-scm.com/book/en/v2/Git-Branching-Branching-Workflows
- GitHub Flow: https://guides.github.com/introduction/flow/

---

**문서 작성일**: 2025-11-25
**버전**: 1.0
**최종 검토자**: [팀 검토 예정]
