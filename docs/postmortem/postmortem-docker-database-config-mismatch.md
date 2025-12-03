# Postmortem: Docker Database Configuration Mismatch

**Date**: 2025-11-25
**Issue**: Database connectivity errors in Docker environment due to .env ↔ docker-compose.yml configuration mismatch
**Time spent**: ~2+ hours of debugging
**Severity**: High (prevents Docker development workflow)

---

## 📋 Summary

Docker 환경에서 데이터베이스 연결 실패로 인한 404 및 FATAL 에러. 근본 원인은 로컬 .env 파일이 Docker 컨테이너로 복사되면서 docker-compose.yml의 환경변수를 덮어썼기 때문.

**Key Issues**:
1. `.env` 파일이 Docker 컨테이너에 복사됨 (의도하지 않음)
2. Docker와 로컬 개발의 데이터베이스 사용자 정보가 일관되지 않음
3. 환경 감지 메커니즘 부재 (Docker vs 로컬 개발 구분 안 됨)

---

## 🔴 Errors Observed

### 1️⃣ 404 Error: `/api/health` Not Found
```
GET /api/health HTTP/1.1" 404 Not Found
```
**Root Cause**: Dockerfile HEALTHCHECK가 존재하지 않는 `/api/health` 요청
**Fix**: HEALTHCHECK 엔드포인트를 `/health`로 수정

### 2️⃣ FATAL Error: `database "slea_user" does not exist`
```
2025-11-25 18:25:11.257 KST [68] FATAL:  database "slea_user" does not exist
```
**Root Cause**: PostgreSQL healthcheck에서 `-d sleassem_dev` 누락
**Fix**: `pg_isready -U slea_user -d sleassem_dev` 추가

### 3️⃣ .env File Loaded in Docker (The Real Problem!)
```
docker exec slea-backend ls -la /app/.env
-rw-r--r-- 1 appuser appuser 1981 Nov 25 15:00 /app/.env
```
**Root Cause**: `.env` 파일이 컨테이너에 복사되면서:
- 로컬 DB 사용자 (`slea_user`) ≠ Docker DB 사용자 (`slea_user`)
- localhost (로컬 컨테이너) ≠ db (Docker 네트워크 호스트명)
- 따라서 DATABASE_URL이 docker-compose.yml 설정을 무시

---

## 🔍 Root Cause Analysis

### Problem 1: .env File Inclusion in Docker Image

**Current State**:
```dockerfile
COPY . .  # .dockerignore는 무시됨 (BuildKit 미지원 또는 ConfigError)
```

**Why this happened**:
- `.dockerignore`에 `.env` 포함되어 있었음
- 하지만 Docker BuildKit이 제대로 적용되지 않음
- 결과: `.env` 파일이 컨테이너로 복사됨

### Problem 2: Configuration Inconsistency

**Local Development (.env)**:
```
DATABASE_URL=postgresql+asyncpg://slea_user:change_me_dev_password@localhost:5432/sleassem_dev
```

**Docker Environment (docker-compose.yml)**:
```yaml
environment:
  DATABASE_URL: postgresql://slea_user:change_me_dev_password@db:5432/sleassem_dev
```

**문제점**:
| 항목 | .env (로컬) | docker-compose.yml (Docker) |
|------|-----------|---------------------------|
| 사용자 | `slea_user` | `slea_user` |
| 호스트 | `localhost` | `db` |
| 암호 | `change_me_dev_password` | `change_me_dev_password` |

### Problem 3: No Environment Detection

**database.py**:
```python
# 원래 코드
env_file = Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)  # 항상 로드됨!
```

**문제**: Docker 환경인지 로컬 개발 환경인지 구분 안 함

---

## ✅ Solutions Implemented

### 1. Add Docker Environment Detection (database.py)
```python
# ✅ 수정됨
env_file = Path(__file__).parent.parent.parent / ".env"
is_docker = bool(os.getenv("ENVIRONMENT"))  # docker-compose.yml에서 설정됨
if env_file.exists() and not is_docker:
    load_dotenv(dotenv_path=env_file)
```

**Logic**:
- Docker Compose는 항상 `ENVIRONMENT` 변수를 설정
- 로컬 개발에서는 설정되지 않음
- 따라서 Docker 환경을 정확히 감지

### 2. Fix PostgreSQL Healthcheck (docker-compose.yml)
```yaml
# ❌ 이전
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U slea_user"]

# ✅ 수정됨
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U slea_user -d sleassem_dev"]
```

### 3. Fix Dockerfile HEALTHCHECK
```dockerfile
# ❌ 이전
HEALTHCHECK ... CMD curl -f http://localhost:${PORT}/api/health || exit 1

# ✅ 수정됨
HEALTHCHECK ... CMD curl -f http://localhost:${PORT}/health || exit 1
```

---

## 🚨 What If .env Had Correct User?

**질문**: 만약 `.env` 파일의 사용자가 `slea_user`가 아니라 `slea_user`였다면 문제가 없었을까?

**답변**: **No, 여전히 문제 발생**

**이유**:
```
.env DATABASE_URL=postgresql+asyncpg://slea_user:change_me_dev_password@localhost:5432/sleassem_dev
                                                       ↓
Docker Container에서는 localhost = 컨테이너 자신 (DB 컨테이너 아님!)
                                                       ↓
연결 실패: PostgreSQL 컨테이너에 도달 불가
```

**올바른 Docker URL**:
```
postgresql://slea_user:change_me_dev_password@db:5432/sleassem_dev
                                           ↑
                                      Docker network hostname
```

---

## 🎯 Best Practices Going Forward

### 1. ✅ Environment Separation

**로컬 개발용 (.env)**:
```
DATABASE_URL=postgresql+asyncpg://slea_user:change_me_dev_password@localhost:5432/sleassem_dev
```

**Docker용 (docker-compose.yml)**:
```yaml
DATABASE_URL: postgresql://slea_user:change_me_dev_password@db:5432/sleassem_dev
ENVIRONMENT: development  # 환경 감지용 마커
```

### 2. ✅ Explicit Environment Detection

**database.py**에서 환경 감지:
```python
# Docker 환경인지 확인
is_docker = bool(os.getenv("ENVIRONMENT"))
if env_file.exists() and not is_docker:
    load_dotenv(dotenv_path=env_file)
```

### 3. ✅ Configuration Documentation

**각 환경별 설정 매뉴얼**:

| 설정 | 로컬 개발 | Docker |
|------|---------|--------|
| 데이터베이스 | WSL PostgreSQL (localhost:5432) | Docker PostgreSQL (db:5432) |
| 사용자 | slea_user | slea_user |
| .env 로드 | ✅ Yes | ❌ No (ENVIRONMENT 변수) |
| HOST | 127.0.0.1 | 0.0.0.0 |

### 4. ✅ Prevent .env from Docker Build

**Option A**: 명시적으로 .dockerignore에서 제외
```
.env
.env.*
.env.local
```

**Option B**: database.py에서 환경 감지 (현재 구현)
```python
is_docker = bool(os.getenv("ENVIRONMENT"))
if env_file.exists() and not is_docker:
    load_dotenv(dotenv_path=env_file)
```

### 5. ✅ Configuration Validation Script

**새로운 script 추가 권장**:
```bash
# scripts/validate-config.sh
./tools/dev.sh up  # 로컬 개발 검증
docker-compose up  # Docker 검증
```

---

## 📊 Time Breakdown

| 단계 | 시간 | 원인 |
|------|------|------|
| 1. 문제 분석 및 Dockerfile 수정 | 15분 | HEALTHCHECK 엔드포인트 오류 발견 |
| 2. PostgreSQL healthcheck 디버깅 | 20분 | `pg_isready` 옵션 분석 |
| 3. .env 파일 로드 원인 분석 | 45분 | Docker 빌드 캐시, BuildKit 이슈 |
| 4. 환경 감지 메커니즘 구현 | 30분 | database.py 수정 및 테스트 |
| 5. 최종 검증 및 커밋 | 15분 | 모든 변경사항 확인 |
| **총계** | **~2.25 시간** | 설정 불일치로 인한 복합 원인 |

---

## 🔑 Key Learnings

### 1. **Configuration Management is Critical**
- 로컬과 Docker 환경의 설정을 명확하게 분리해야 함
- 암호, 호스트명, 사용자명 모두 일관되어야 함

### 2. **Environment Detection Should Be Explicit**
- 환경(Docker vs 로컬)을 자동으로 감지하는 메커니즘 필요
- 환경변수를 마커로 사용하는 것이 효과적

### 3. **.env Files Must Not Be in Docker Images**
- `.env`는 로컬 개발 전용
- Docker 컨테이너는 환경변수 주입(docker-compose.yml)만 사용해야 함

### 4. **Healthcheck Configuration Matters**
- Dockerfile과 docker-compose.yml의 healthcheck를 신중히 설계
- 특히 데이터베이스 healthcheck는 정확한 호스트명 + DB명 필요

---

## 🛠️ Prevention Checklist

다음 프로젝트에서 반복되지 않도록:

- [ ] `.dockerignore`에 `.env`, `.env.*` 명시적 포함
- [ ] `src/backend/database.py`처럼 환경 감지 로직 추가
- [ ] docker-compose.yml에 명확한 환경 마커 변수 설정
- [ ] 데이터베이스 호스트명 일관성 검증 (localhost vs db)
- [ ] 초기 설정 시 로컬 .env와 docker-compose.yml 비교 리뷰
- [ ] CI/CD에서 Docker 환경 테스트 자동화

---

## 📝 Related Files

| 파일 | 변경사항 |
|------|---------|
| Dockerfile | HEALTHCHECK 엔드포인트: `/api/health` → `/health` |
| docker-compose.yml | PostgreSQL healthcheck: `-d sleassem_dev` 추가 |
| src/backend/database.py | 환경 감지 로직 추가 (ENVIRONMENT 변수 체크) |

---

## 🎓 Conclusion

**이번 이슈의 핵심**:
1. 로컬 개발(WSL PostgreSQL) ≠ Docker 환경(Docker PostgreSQL)
2. 설정 불일치를 조기에 감지할 메커니즘 부재
3. 환경 감지를 명시적으로 구현하면 해결 가능

**적용된 해결책**:
- Docker 환경 자동 감지 (ENVIRONMENT 변수)
- .env 파일이 Docker에서 로드되지 않도록 조건부 처리
- 모든 healthcheck 설정 정확성 검증

**소요 시간을 줄이기 위한 미래 개선사항**:
- 환경 설정 검증 스크립트 자동화
- 초기 프로젝트 템플릿에서 환경 분리 표준화
- Docker vs 로컬 개발 환경을 명확하게 문서화
