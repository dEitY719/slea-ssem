# 협업 워크플로우 구현 체크리스트

**목적**: COLLABORATION-WORKFLOW.md의 권장사항을 실제로 구현하기
**예상 소요 시간**: 2-3시간
**완료 후**: 팀 전체가 동일한 개발 환경에서 작업 가능

---

## Phase 1: 기초 설정 (30분)

### ✅ 1.1 Git 저장소 정리

- [ ] 현재 branch 확인
  ```bash
  git branch -a
  ```

- [ ] 작업 중인 내용 저장
  ```bash
  git stash  # 또는 커밋
  ```

- [ ] Origin 원본 확인 (사외 저장소)
  ```bash
  git remote -v
  # origin  https://github.com/dEitY719/slea-ssem.git (fetch)
  # origin  https://github.com/dEitY719/slea-ssem.git (push)
  ```

### ✅ 1.2 Upstream 추가 (사외 저장소)

이미 fork/clone 된 경우만:

```bash
# 개인 Fork 저장소가 있으면
git remote add upstream https://github.com/dEitY719/slea-ssem.git
git fetch upstream
git branch -avv  # 확인
```

**확인 사항**:
- [ ] `upstream/main` 브랜치 보임
- [ ] `upstream/develop` 브랜치 보임
- [ ] `origin`은 본인의 Fork 저장소

### ✅ 1.3 Develop 브랜치 기반 설정

```bash
# Develop을 default 브랜치로 추적
git checkout develop
git pull origin develop

# 또는 Upstream에서 최신 받기
git pull upstream develop
```

**확인 사항**:
- [ ] 현재 branch: `develop`
- [ ] 최신 커밋: `git log --oneline -5` 확인

---

## Phase 2: Docker 환경 구성 (1시간)

### ✅ 2.1 Dockerfile 검증

**파일**: `Dockerfile` (프로젝트 루트)

- [ ] 파일 존재 확인
  ```bash
  cat Dockerfile
  ```

- [ ] 핵심 요소 확인
  - [ ] `FROM python:3.11-slim` 또는 3.10+
  - [ ] `WORKDIR /app`
  - [ ] 의존성 설치: `pip install uv && uv sync`
  - [ ] `EXPOSE 8000`
  - [ ] `CMD` 정의

**작성이 필요한 경우**:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync

COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] 파일 저장
- [ ] `.dockerignore` 파일도 작성:
  ```
  .git
  .gitignore
  __pycache__
  .pytest_cache
  .venv
  .env
  .env.*
  *.pyc
  .DS_Store
  ```

### ✅ 2.2 docker-compose.yml 생성

**파일**: `docker-compose.yml` (프로젝트 루트)

- [ ] 파일 존재 확인
  ```bash
  cat docker-compose.yml
  ```

- [ ] 필수 서비스 확인
  - [ ] `db` 서비스 (PostgreSQL 15)
  - [ ] `backend` 서비스 (FastAPI)
  - [ ] `volumes` 섹션 (postgres_data)

**작성이 필요한 경우**:

```yaml
version: '3.8'

services:
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
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U slea_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: .
    container_name: slea-backend
    environment:
      DATABASE_URL: postgresql://slea_user:change_me_dev_password@db:5432/sleassem_dev
      PYTHONUNBUFFERED: 1
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app
    command: >
      sh -c "
        alembic upgrade head &&
        uv run uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload
      "

volumes:
  postgres_data:
```

- [ ] 파일 저장
- [ ] Git에 추가 (민감 정보 아님):
  ```bash
  git add docker-compose.yml Dockerfile .dockerignore
  ```

### ✅ 2.3 회사 환경 설정 파일 생성

**파일**: `.env.company` (gitignore 처리)

- [ ] 파일 생성:
  ```bash
  cp .env.example .env.company 2>/dev/null || cat > .env.company << 'EOF'
  # 회사 환경 변수
  DB_HOST=db  # 로컬 Docker 환경
  DB_PORT=5432
  DB_USER=slea_user
  DB_PASSWORD=change_me_dev_password
  HTTP_PROXY=  # 회사 proxy 정보 있으면 추가
  HTTPS_PROXY=  # 회사 proxy 정보 있으면 추가
  EOF
  ```

- [ ] `.gitignore`에 추가 확인:
  ```bash
  echo ".env" >> .gitignore
  echo ".env.*" >> .gitignore
  git add .gitignore
  ```

### ✅ 2.4 Docker 빌드 테스트

```bash
# 1. 이미지 빌드 (처음 실행 시 3-5분)
docker build -t slea-backend:dev .

# 2. 빌드 성공 확인
docker images | grep slea-backend
```

**문제 해결**:
```bash
# Docker daemon이 실행 중인지 확인
docker ps

# 캐시 무시하고 재빌드
docker build --no-cache -t slea-backend:dev .
```

- [ ] 빌드 성공
- [ ] Image 생성됨 (`docker images` 확인)

---

## Phase 3: Docker Compose 테스트 (30분)

### ✅ 3.1 환경 시작

```bash
# 1. 컨테이너 시작 (첫 실행이면 5분+)
docker-compose up -d

# 2. 상태 확인
docker-compose ps
```

**예상 출력**:
```
NAME            STATUS
slea-db         Up (healthy)
slea-backend    Up
```

**문제 해결**:
- [ ] Port 5432 충돌 → WSL에서 PostgreSQL 종료
  ```bash
  wsl -d <distro>
  sudo service postgresql stop
  ```

- [ ] Image 없음 → `docker-compose build` 실행

- [ ] DB 초기화 실패 → 로그 확인
  ```bash
  docker-compose logs db
  ```

### ✅ 3.2 로그 확인

```bash
# 실시간 로그
docker-compose logs -f backend
```

**확인 사항**:
- [ ] "Uvicorn running on..." 메시지 보임
- [ ] 에러 메시지 없음
- [ ] DB 마이그레이션 완료: "Alembic upgrade head" 성공

### ✅ 3.3 API 테스트

```bash
# 1. 헬스 체크
curl http://localhost:8000/api/health

# 2. DB 연결 확인
curl http://localhost:8000/api/db-status

# 3. Python 패키지 확인
docker-compose exec backend python -c "import src.backend.main; print('OK')"
```

**확인 사항**:
- [ ] HTTP 200 응답
- [ ] DB 연결 성공

### ✅ 3.4 테스트 실행

```bash
# 방법 1: 컨테이너에서 실행 (권장)
docker-compose exec backend pytest tests/backend/ -v --tb=short

# 방법 2: 호스트에서 실행 (venv 필요)
pytest tests/backend/ -v
```

**확인 사항**:
- [ ] 최소 50% 이상 테스트 통과
- [ ] 심각한 에러 없음

### ✅ 3.5 정리

```bash
# 컨테이너 정지 (데이터 유지)
docker-compose down

# 재시작 확인
docker-compose up -d
docker-compose logs -f backend
```

- [ ] 정지/시작 성공
- [ ] 데이터 유지됨 (DB 내용 그대로)

---

## Phase 4: Git 워크플로우 설정 (30분)

### ✅ 4.1 Feature 브랜치 전략 문서화

**파일**: `BRANCH-STRATEGY.md` 생성

```bash
cat > docs/BRANCH-STRATEGY.md << 'EOF'
# Git Branch 전략

## 브랜치 구조

```
main (프로덕션)
  ↑
develop (개발 통합)
  ↑
feature/xxx (기능 개발)
```

## 워크플로우

### 1. Feature 브랜치 생성
```bash
git checkout develop
git pull upstream develop
git checkout -b feature/my-feature
```

### 2. 개발
```bash
# 코드 수정
# docker-compose exec backend pytest tests/ -v
# ./tools/dev.sh format
git add .
./tools/commit.sh
```

### 3. Push & PR
```bash
git push origin feature/my-feature
# GitHub에서 Pull Request 생성
```

### 4. Review & Merge
- Code Review 후 develop에 merge
- Squash commit 권장 (히스토리 깔끔)

### 5. 회사 내부 동기화
```bash
cd slea-company
git fetch upstream develop
git merge upstream/develop
```

## 주요 규칙

- main: 프로덕션 배포, 태그 필수
- develop: QA/스테이징, 항상 안정적
- feature/*: 개발 중, PR 필수
- hotfix/*: 긴급 버그, main에서 분기

## 커밋 메시지

```
feat: 새 기능
fix: 버그 수정
docs: 문서
refactor: 코드 정리
test: 테스트
chore: 기타
```
EOF
git add docs/BRANCH-STRATEGY.md
```

- [ ] 파일 생성
- [ ] Git 추가

### ✅ 4.2 팀 가이드 문서 공유

```bash
# 주요 파일 확인
ls -la docs/COLLABORATION-WORKFLOW.md
ls -la docs/DOCKER-DEVELOPMENT-GUIDE.md
ls -la docs/BRANCH-STRATEGY.md
```

- [ ] COLLABORATION-WORKFLOW.md 존재
- [ ] DOCKER-DEVELOPMENT-GUIDE.md 존재
- [ ] BRANCH-STRATEGY.md 존재

### ✅ 4.3 동료 협업 설정 계획

**체크리스트** (동료 각각이 실행):

```markdown
## 동료 A, B 체크리스트

### 단계 1: 저장소 설정 (10분)
- [ ] 본 가이드 문서 읽음
- [ ] Dockerfile 확인 (git pull)
- [ ] docker-compose.yml 확인 (git pull)

### 단계 2: Docker 환경 (15분)
- [ ] Docker 설치 확인
- [ ] docker-compose up -d 성공
- [ ] 테스트 실행 성공

### 단계 3: Feature 개발 (진행 중)
- [ ] feature 브랜치 생성
- [ ] docker-compose 에서 코드 작성
- [ ] 테스트 통과 후 PR 생성

### 단계 4: 회사 내부 (회사 진입 시)
- [ ] 회사 저장소 clone
- [ ] upstream 추가
- [ ] 동기화 스크립트 실행
```

- [ ] 위 체크리스트 문서화
- [ ] 동료에게 공유

---

## Phase 5: 회사 환경 준비 (30분)

### ✅ 5.1 회사 저장소 초기화 계획

**이후 회사에서 실행할 명령어 모음**:

```bash
#!/bin/bash
# setup-company-env.sh

echo "🏢 회사 환경 설정 시작..."

# 1. 회사 저장소 클론
git clone https://github.company.com/aig/slea-ssem.git slea-company
cd slea-company

# 2. Upstream 추가
git remote add upstream https://github.com/dEitY719/slea-ssem.git

# 3. 최신 코드 가져오기
git fetch upstream develop
git checkout develop
git merge upstream/develop

# 4. 회사 환경 변수 설정
cat > .env.company << 'EOF'
DB_HOST=company-db.internal.com  # 회사 DB 정보
DB_PORT=5432
DB_USER=internal_user
DB_PASSWORD=<strong_password>
HTTP_PROXY=proxy.company.com:8080
HTTPS_PROXY=proxy.company.com:8080
EOF

# 5. Docker 환경 시작
docker-compose up -d

# 6. 테스트
docker-compose exec backend pytest tests/backend/ -v

echo "✅ 회사 환경 설정 완료!"
```

**저장**:
```bash
cat > setup-company-env.sh << 'SCRIPT'
#!/bin/bash
...
SCRIPT
chmod +x setup-company-env.sh
git add setup-company-env.sh
```

- [ ] 스크립트 생성
- [ ] Git 추가

### ✅ 5.2 주기적 동기화 스크립트

**파일**: `tools/sync-with-upstream.sh`

```bash
#!/bin/bash
# 회사 저장소를 사외 upstream과 동기화

set -e

echo "🔄 Upstream (사외)에서 최신 코드 가져오는 중..."
git fetch upstream develop

echo "📝 develop 브랜치로 전환..."
git checkout develop

echo "🔀 Upstream/develop과 머지..."
git merge upstream/develop

echo "✅ 동기화 완료!"
echo "💾 이제 다음을 실행하세요:"
echo "  git push origin develop"
```

**저장**:
```bash
cat > tools/sync-with-upstream.sh << 'SCRIPT'
#!/bin/bash
# ... 위 내용 ...
SCRIPT
chmod +x tools/sync-with-upstream.sh
git add tools/sync-with-upstream.sh
```

- [ ] 스크립트 생성
- [ ] Git 추가

### ✅ 5.3 회사 proxy 설정 (선택)

WSL에서 proxy 설정이 필요한 경우:

**파일**: `setup-proxy.sh`

```bash
#!/bin/bash
# WSL에서 회사 proxy 설정

export HTTP_PROXY="http://proxy.company.com:8080"
export HTTPS_PROXY="http://proxy.company.com:8080"
export NO_PROXY="localhost,127.0.0.1,.company.com"

# Pip proxy 설정
pip config set global.proxy "[user-passwd@]proxy.server:port"

# Git proxy 설정
git config --global http.proxy "http://proxy.company.com:8080"
git config --global https.proxy "http://proxy.company.com:8080"

echo "✅ Proxy 설정 완료"
```

- [ ] (필요한 경우) 파일 생성
- [ ] 실행 권한: `chmod +x setup-proxy.sh`

---

## Phase 6: 최종 검증 (30분)

### ✅ 6.1 완전한 시작부터 끝까지 테스트

```bash
# 1. 시작 전: 모든 컨테이너 정지
docker-compose down -v

# 2. 처음부터 시작
docker-compose up -d

# 3. 마이그레이션 확인
docker-compose logs db | grep "ready"

# 4. Backend 정상 시작
docker-compose logs backend | grep "Uvicorn running"

# 5. API 요청
curl http://localhost:8000/api/health

# 6. 테스트 실행
docker-compose exec backend pytest tests/backend/ -k "test_health" -v

# 7. 정리
docker-compose down
```

**확인 사항**:
- [ ] 모든 단계 성공
- [ ] 재현 가능 (다시 한 번 실행)

### ✅ 6.2 코드 변경 자동 반영 테스트

```bash
# 1. 환경 시작
docker-compose up -d

# 2. 테스트 로그 보기
docker-compose logs -f backend &

# 3. 코드 수정 (예: src/backend/main.py)
echo '# Test' >> src/backend/main.py

# 4. 자동 다시로드 확인 (1-3초 내)
# 로그에 "Reloading server" 메시지 보임

# 5. 테스트 실행
docker-compose exec backend pytest tests/backend/ -v --tb=short

# 6. 정리
docker-compose down
```

**확인 사항**:
- [ ] 파일 변경이 자동 반영됨
- [ ] 테스트 통과
- [ ] 다시로드 시간 < 5초

### ✅ 6.3 Git 상태 확인

```bash
# 최종 status
git status

# 추가된 파일 확인
git diff --cached --name-only
```

**확인 사항**:
```
Changes to be committed:
  - Dockerfile
  - docker-compose.yml
  - .gitignore (수정)
  - docs/COLLABORATION-WORKFLOW.md
  - docs/DOCKER-DEVELOPMENT-GUIDE.md
  - docs/BRANCH-STRATEGY.md
  - tools/sync-with-upstream.sh
  - (선택) setup-company-env.sh
```

- [ ] 민감 정보 없음 (.env 제외)
- [ ] 문서 파일만 commit

### ✅ 6.4 최종 커밋

```bash
# 상태 확인
git status

# 커밋 메시지 작성
./tools/commit.sh

# 또는 수동
git commit -m "chore: Add Docker + collaboration workflow setup

- Add Dockerfile for consistent development environment
- Add docker-compose.yml for local dev with PostgreSQL
- Add COLLABORATION-WORKFLOW.md for team coordination
- Add DOCKER-DEVELOPMENT-GUIDE.md for Docker usage
- Add BRANCH-STRATEGY.md for git workflow
- Add sync-with-upstream.sh for repository synchronization

This enables:
- Unified dev environment (Windows/WSL/Linux)
- Easy onboarding for new team members
- Efficient collaboration between external and internal repos"
```

- [ ] 커밋 완료
- [ ] `git log -1` 확인

### ✅ 6.5 Push

```bash
# 최신 코드 가져오기
git pull origin develop

# 커밋 푸시
git push origin develop
```

- [ ] Push 성공
- [ ] GitHub 에서 커밋 보임

---

## 최종 체크리스트

개발 환경 완전히 설정되었는지 확인:

```markdown
### Infrastructure ✅
- [ ] Dockerfile 작성 및 빌드 성공
- [ ] docker-compose.yml 작성 및 실행 성공
- [ ] PostgreSQL 컨테이너 정상 작동
- [ ] Backend 컨테이너 정상 작동
- [ ] API 응답 확인 (http://localhost:8000/api/health)

### Development ✅
- [ ] 코드 변경 자동 반영
- [ ] 테스트 통과 (docker-compose exec backend pytest)
- [ ] Docker/git 환경 공유 가능 (모든 파일 committed)

### Collaboration ✅
- [ ] COLLABORATION-WORKFLOW.md 작성
- [ ] DOCKER-DEVELOPMENT-GUIDE.md 작성
- [ ] BRANCH-STRATEGY.md 작성
- [ ] 팀에 문서 공유 계획
- [ ] 회사 환경 setup 스크립트 준비

### Documentation ✅
- [ ] README 업데이트 (docker-compose 사용법)
- [ ] CONTRIBUTING.md 업데이트 (개발 환경)
- [ ] 동료들이 따를 수 있는 가이드 완성

### Ready for Team ✅
- [ ] 동료 A가 clone → docker-compose up만으로 개발 가능
- [ ] 동료 B도 동일하게 가능
- [ ] 회사 환경 설정 시 명확한 단계별 가이드 제공
```

---

## 문제가 발생했을 때

### 일반적인 문제

| 문제 | 해결 방법 |
|------|---------|
| "Docker daemon 미실행" | Docker Desktop 시작 |
| "Port 5432 충돌" | WSL PostgreSQL 종료 또는 포트 변경 |
| "Container 시작 안 됨" | `docker-compose logs` 확인 후 Dockerfile 수정 |
| "테스트 실패" | `docker-compose exec backend pytest -v` 디버깅 |
| "파일 변경 미반영" | `docker-compose restart backend` |

### 정보 수집

문제 해결을 위해 다음 정보 수집:

```bash
# 1. Docker 상태
docker --version
docker-compose version
docker ps
docker-compose ps

# 2. 로그
docker-compose logs

# 3. 네트워크
docker network ls
docker network inspect slea-ssem_default

# 4. 볼륨
docker volume ls
docker volume inspect slea-ssem_postgres_data

# 5. 이미지
docker images | grep slea
```

---

## 다음 단계

이 체크리스트를 완료한 후:

1. **동료와 공유**
   - [ ] Git에 push
   - [ ] 팀에 공지
   - [ ] 동료들이 체크리스트 따라 설정

2. **회사 환경 적용**
   - [ ] 회사 DB 정보 수집
   - [ ] Proxy 설정 확인
   - [ ] `setup-company-env.sh` 실행

3. **자동화 개선**
   - [ ] CI/CD 파이프라인 (GitHub Actions)
   - [ ] 자동 테스트 (PR 생성 시)
   - [ ] Linting 자동화

---

**작성일**: 2025-11-25
**버전**: 1.0
**상태**: 검토 예정
