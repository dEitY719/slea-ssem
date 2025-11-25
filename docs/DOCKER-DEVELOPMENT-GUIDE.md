# Docker 기반 개발 환경 가이드

**대상**: Docker 경험이 부족한 개발자
**목표**: 효율적인 Docker 사용으로 "내 환경에서는 되는데..."문제 해결

---

## 🎯 Docker가 필요한 이유

### 현재 상황: 환경 불일치 문제

```
개인 환경 (WSL)             회사 환경 (WSL)
┌──────────────────┐       ┌──────────────────┐
│ Python 3.11      │       │ Python 3.10?     │
│ PostgreSQL 15    │       │ PostgreSQL 13?   │
│ Redis 최신버전   │       │ Redis 없음?      │
│ 로컬 설정 X      │       │ 프록시 설정 필요 │
└──────────────────┘       └──────────────────┘
        ↓                          ↓
    "돌아감!"              "왜 안 돼?"
```

**Docker 사용 후**:

```
┌─────────────────────────────────────┐
│   Docker Container (격리된 환경)    │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Python 3.11                     │ │
│ │ PostgreSQL 15                   │ │
│ │ Redis 7                         │ │
│ │ 애플리케이션                     │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
   호스트: Windows/WSL/Linux
   "어디서나 동일하게 작동!"
```

---

## 📚 Docker 핵심 개념 (쉽게 설명)

### 1. Dockerfile = 요리 레시피

```dockerfile
FROM python:3.11-slim           # 기본 재료: Python 3.11 시작
WORKDIR /app                    # 주방: /app 디렉토리

RUN apt-get update && \         # 시스템 재료 준비
    apt-get install -y postgresql-client

COPY pyproject.toml uv.lock ./  # 재료: 의존성 파일
RUN pip install uv && uv sync   # 조리: 의존성 설치

COPY . .                        # 코드 복사

CMD ["uvicorn", "..."]          # 서빙: 실행 명령
```

**핵심**:
- 모든 개발자가 같은 "레시피"로 같은 환경을 만듦
- 재현 가능하고 일관된 환경 보장

### 2. Image = 스냅샷 (실행 불가)

```bash
# Image 빌드 (요리 전 재료 준비)
docker build -t slea:1.0 .
# 결과: slea:1.0 이미지 생성 (저장되어 있음, 실행 안 함)

# Image 조회
docker images
```

### 3. Container = 실행 중인 인스턴스

```bash
# Image → Container 실행
docker run -p 8000:8000 slea:1.0
# 결과: Container가 실행되고 있음 (프로세스처럼)

# 실행 중인 Container 조회
docker ps
```

### 4. Volume = 호스트와의 저장소 공유

```dockerfile
# docker-compose.yml
services:
  backend:
    volumes:
      - .:/app  # 호스트 현재 디렉토리 = 컨테이너 /app
```

**효과**:
```
호스트에서 파일 수정
    ↓
/app에 자동 반영
    ↓
애플리케이션이 변경된 파일 로드
    ↓
실시간으로 변경 사항 확인 (자동 다시로드)
```

### 5. Docker Compose = 여러 컨테이너 관리

```yaml
# docker-compose.yml
services:
  backend:     # 컨테이너 1: FastAPI
  db:          # 컨테이너 2: PostgreSQL
  redis:       # 컨테이너 3: Redis
  # 자동으로 네트워크 구성 + 통신 설정
```

**효과**:
- `docker run ...` 명령 여러 개 대신 → `docker-compose up` 한 번
- 컨테이너 간 자동 네트워킹

---

## 🚀 실습 1: 기본 Docker 명령어 (10분)

### 설치 확인

```bash
# Docker 설치 확인
docker --version
# Docker version 24.0.x, build ...

docker compose version
# Docker Compose version 2.x.x, build ...
```

### Image 빌드

```bash
# 프로젝트 디렉토리로 이동
cd ~/path/to/slea-ssem

# Dockerfile로부터 Image 빌드
docker build -t slea-backend:dev .
# 결과:
# Step 1/7 : FROM python:3.11-slim
# Step 2/7 : WORKDIR /app
# ...
# Successfully tagged slea-backend:dev

# 빌드 확인
docker images | grep slea-backend
# slea-backend    dev     abc123def456    5 minutes ago    500MB
```

### Container 실행

```bash
# Container 실행 (Image → 실행 중인 프로세스)
docker run --name slea-test slea-backend:dev python --version
# Python 3.11.x

# 컨테이너 상태 확인
docker ps -a  # 종료된 컨테이너 포함
docker ps     # 실행 중인 컨테이너만

# 컨테이너 내부 접속
docker exec -it slea-test bash
# $ ls
# $ exit
```

---

## 🚀 실습 2: Docker Compose로 전체 환경 구성 (20분)

### docker-compose.yml 생성

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
      POSTGRES_USER: dev_user
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI 백엔드
  backend:
    build: .
    container_name: slea-backend
    environment:
      DATABASE_URL: postgresql://dev_user:dev_password@db:5432/sleassem_dev
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

### 환경 시작

```bash
# 1. 컨테이너 빌드 및 시작 (처음 한 번만 시간 걸림)
docker-compose up -d
# Creating slea-db ...
# Creating slea-backend ...
# Done

# 2. 상태 확인
docker-compose ps
# NAME          IMAGE              STATUS
# slea-db       postgres:15-alpine Up (healthy)
# slea-backend  slea-backend:dev   Up

# 3. 로그 확인 (실시간)
docker-compose logs -f backend
# [+] Running 2/2
# INFO:     Uvicorn running on http://0.0.0.0:8000

# 4. 테스트
curl http://localhost:8000/api/health
# {"status": "ok"}
```

### 코드 변경 테스트

```bash
# 1. 파일 수정 (호스트에서)
echo 'print("Hello from Docker!")' >> src/backend/main.py

# 2. 다시 로드 (컨테이너가 자동으로 감지)
docker-compose logs -f backend
# [+] Reloading server...
# [OK] Reloaded.

# 3. 변경 사항 반영됨!
```

### 컨테이너 내부 작업

```bash
# 컨테이너 셸 접속
docker-compose exec backend bash

# 컨테이너 내부에서:
$ ls -la
$ pytest tests/backend/ -v
$ python -c "import src.backend.main"
$ exit
```

### 정리

```bash
# 컨테이너 중지 (데이터 보존)
docker-compose down
# Stopping slea-backend ... Done
# Stopping slea-db ... Done
# Removing volumes ...

# 컨테이너 + 볼륨 모두 삭제 (주의!)
docker-compose down -v
```

---

## 🎯 개발 워크플로우 예시

### 아침: 개발 시작

```bash
# 1. 최신 코드 가져오기
git pull origin develop

# 2. Docker 환경 시작
docker-compose up -d

# 3. 상태 확인
docker-compose ps
# CONTAINER   STATUS
# slea-db     Up (healthy)
# slea-backend Up
```

### 개발 중: 코드 수정

```bash
# 호스트에서 일반적인 편집기(VSCode 등)로 코드 수정
# /src/backend/services/question_gen_service.py 수정

# 자동으로 컨테이너 내부 /app 폴더에 반영됨!
# 애플리케이션이 자동 다시로드됨
docker-compose logs -f backend
# [Reloading server...]
# [OK] Reloaded.
```

### 테스트

```bash
# 방법 1: 호스트에서 (venv 설정됨)
pytest tests/backend/ -v

# 방법 2: 컨테이너에서
docker-compose exec backend pytest tests/backend/ -v

# 테스트 실패한 경우
docker-compose exec backend bash
$ python -c "import src.backend.main"  # 문제 확인
$ exit
```

### 정리: 개발 종료

```bash
# 컨테이너 정지 (데이터 유지)
docker-compose down
# 다음 날 docker-compose up -d로 복구 가능

# 장기 미사용 시 볼륨도 삭제
docker-compose down -v
# 다음 시작 시 새로운 DB 생성됨 (마이그레이션 재실행)
```

---

## 🔧 실제 마주치는 문제와 해결

### 문제 1: "Port 5432 already in use"

**원인**: PostgreSQL이 이미 실행 중

**해결**:

```bash
# WSL에서 기존 PostgreSQL 중지
wsl -d <distro>  # WSL 접속
sudo service postgresql stop

# 또는 다른 포트 사용
docker-compose.yml 수정:
services:
  db:
    ports:
      - "5433:5432"  # 호스트 포트 변경
```

### 문제 2: "Container exited with code 1"

**원인**: 컨테이너가 시작 중 에러로 종료

**해결**:

```bash
# 1. 로그 확인
docker-compose logs backend
# ERROR: ModuleNotFoundError: No module named 'xxx'

# 2. 원인 파악 후:
# Dockerfile 수정 또는 의존성 업데이트

# 3. 이미지 재빌드 (캐시 무시)
docker-compose build --no-cache

# 4. 다시 시작
docker-compose up -d
```

### 문제 3: "Database is locked"

**원인**: 컨테이너가 예상치 못하게 종료되어 DB 손상

**해결**:

```bash
# 1. 컨테이너 정지
docker-compose down

# 2. 볼륨 삭제 (DB 초기화)
docker volume rm postgres_data

# 3. 다시 시작 (fresh DB)
docker-compose up -d
```

### 문제 4: 파일 변경이 컨테이너에 반영 안 됨

**원인**: Volume 마운트 문제 (특히 WSL)

**해결**:

```bash
# 1. WSL에서 마운트 상태 확인
docker-compose exec backend df -h
# /app이 마운트 되어있는지 확인

# 2. Dockerfile의 COPY 명령 때문일 수 있음
# COPY . . 가 빌드 시점의 파일을 고정하므로
# Volume 마운트 이후에는 영향 없음

# 3. 강제 재시작
docker-compose restart backend
```

### 문제 5: "Out of disk space"

**원인**: Docker 이미지/컨테이너/볼륨 적립

**해결**:

```bash
# 현재 사용량 확인
docker system df
# Images      5       3       2.3GB   1.2GB
# Containers  8       2       1.5GB   0B
# Volumes     3       1       0.5GB   0B

# 정리: 사용되지 않는 리소스 삭제
docker system prune
# WARNING! This will remove:
# - all stopped containers
# - all networks not used by at least one container
# - all dangling images
# Continue? [y/N] y

# 강제 정리 (주의)
docker system prune -a --volumes
```

---

## 📝 Dockerfile 최적화

### 초급: 기본 구조

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 의존성 설치
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync

# 코드 복사
COPY . .

# 실행
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0"]
```

**문제**: Image 크기 500MB+ (느린 빌드)

### 중급: 멀티스테이지 빌드

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# 의존성 설치 (큰 단계)
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync

# Stage 2: Runtime (작은 이미지)
FROM python:3.11-slim

WORKDIR /app

# Builder에서 최소한의 파일만 복사
COPY --from=builder /app/.venv .venv
COPY . .

ENV PATH="/app/.venv/bin:$PATH"
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0"]
```

**효과**: Image 크기 200MB (50% 감소!)

### 고급: 캐싱 최적화

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 먼저 의존성 설치 (거의 변하지 않음)
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync

# 그 다음 코드 복사 (자주 변함)
COPY . .

CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0"]
```

**효과**: 코드 변경 시 의존성 재설치 안 함 (빌드 시간 10초 → 1초)

---

## 🌍 환경별 docker-compose 파일

### 개발 환경: `docker-compose.yml`

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"  # 호스트에서 접근 가능
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: .
    environment:
      DATABASE_URL: postgresql://user:dev_password@db/sleassem_dev
      DEBUG: "true"  # 개발 모드
    ports:
      - "8000:8000"
    volumes:
      - .:/app  # 실시간 코드 반영

volumes:
  postgres_data:
```

### 테스트 환경: `docker-compose.test.yml`

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: test_password
    # ports 없음 (내부 통신만)

  backend:
    build: .
    environment:
      DATABASE_URL: postgresql://user:test_password@db/sleassem_test
      DEBUG: "false"
    depends_on:
      db:
        condition: service_healthy
    command: pytest tests/ -v  # 테스트 실행
```

**사용**:

```bash
# 테스트 실행
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

### 프로덕션 환경: `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}  # 환경 변수에서 읽음
    # 외부 노출 안 함
    restart: always

  backend:
    build: .
    environment:
      DATABASE_URL: postgresql://user:${DB_PASSWORD}@db/sleassem
      DEBUG: "false"
    restart: always
    # 로드 밸런서 뒤에서 실행
```

---

## 🔐 보안 고려사항

### 암호 관리

```bash
# ❌ 나쁜 예
docker-compose.yml:
  POSTGRES_PASSWORD: "admin123"

# ✅ 좋은 예
.env 파일:
  DB_PASSWORD=<strong_password_here>

docker-compose.yml:
  POSTGRES_PASSWORD: ${DB_PASSWORD}

.gitignore:
  .env
```

### 루트 권한 피하기

```dockerfile
# ❌ 나쁜 예
RUN apt-get install ...
# root 권한으로 실행

# ✅ 좋은 예
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```

---

## 📊 자주 사용하는 명령어 요약

| 명령어 | 목적 |
|--------|------|
| `docker build -t image:tag .` | Image 빌드 |
| `docker run image` | Container 실행 |
| `docker ps` | 실행 중인 Container 목록 |
| `docker exec -it container bash` | Container 셸 접속 |
| `docker compose up -d` | 모든 서비스 시작 |
| `docker compose down` | 모든 서비스 정지 |
| `docker compose logs -f` | 실시간 로그 |
| `docker compose exec service cmd` | Service에서 명령 실행 |
| `docker system prune` | 미사용 리소스 삭제 |

---

## 🎓 학습 경로

### Day 1 (30분): 개념 이해
- [ ] Docker vs VM 차이점
- [ ] Image, Container, Volume 개념
- [ ] 위 "핵심 개념" 섹션 읽기

### Day 2 (1시간): 실습
- [ ] `docker build` 명령으로 Image 생성
- [ ] `docker run` 명령으로 Container 실행
- [ ] "실습 1" 완료

### Day 3 (1.5시간): Docker Compose
- [ ] docker-compose.yml 작성
- [ ] `docker-compose up` 실행
- [ ] "실습 2" 완료

### Day 4 (1시간): 개발 워크플로우
- [ ] 코드 수정 → 자동 반영 테스트
- [ ] 컨테이너 내부에서 테스트 실행
- [ ] "개발 워크플로우" 섹션 완료

### Day 5 (1시간): 문제 해결
- [ ] 실제 문제 10가지 마주치기
- [ ] "실제 마주치는 문제" 섹션 마스터

---

## ✅ 체크리스트

개발 환경 설정 완료 여부 확인:

```markdown
- [ ] Docker 설치 (docker --version으로 확인)
- [ ] Docker Compose 설치 (docker compose version으로 확인)
- [ ] Dockerfile 작성 (프로젝트 루트)
- [ ] docker-compose.yml 작성 (프로젝트 루트)
- [ ] docker-compose up -d 성공
- [ ] http://localhost:8000 접근 가능
- [ ] 테스트 실행 성공 (docker-compose exec backend pytest)
- [ ] docker-compose.yml을 .gitignore에 추가하지 않음 (버전 관리 필요)
- [ ] .env 파일을 .gitignore에 추가 (보안)
```

---

## 🆘 추가 도움말

**더 배우기**:
- Docker 공식 가이드: https://docs.docker.com/get-started/
- Docker Compose 예제: https://docs.docker.com/compose/gettingstarted/

**문제 해결**:
1. 로그 확인 (`docker-compose logs -f`)
2. Container 상태 확인 (`docker-compose ps`)
3. 강제 재빌드 (`docker-compose build --no-cache`)
4. 정리 후 재시작 (`docker system prune && docker-compose up -d`)

---

**문서 작성일**: 2025-11-25
**버전**: 1.0
**대상**: Docker 초급자
