# Makefile 사용 가이드

**목적**: 모든 개발 작업을 간단한 `make` 명령어로 관리
**기반**: 회사에서 사용하는 Makefile 패턴 + slea-ssem 특화

---

## 🎯 왜 Makefile인가?

### 문제: 복잡한 명령어

```bash
# ❌ 이런 명령어를 매번 입력?
docker-compose exec backend pytest tests/backend/ -v --tb=short

# 또는
docker build --build-arg HTTP_PROXY=$HTTP_PROXY ... -t slea-backend:0.1.0 .

# 또는
git fetch upstream develop && git checkout develop && git merge upstream/develop
```

### 해결: 한 줄 명령어

```bash
# ✅ 간단한 Makefile 명령어
make test
make build
make sync
```

---

## 📋 전체 명령어 목록

```bash
make help              # 이 도움말 보기
```

### 초기 설정

```bash
make init              # .env 파일 생성
make init ENVIRONMENT=company  # 사내 환경 초기화
```

### Docker 관리

```bash
make build             # 이미지 빌드
make up                # 환경 시작
make down              # 환경 정지
make restart           # 환경 재시작
make rebuild           # fresh 시작 (clean + build + up)
```

### 로깅 & 모니터링

```bash
make logs              # Backend 로그
make logs-db           # Database 로그
make logs-all          # 모든 서비스 로그
make ps                # 실행 중인 서비스 목록
```

### 컨테이너 접속

```bash
make shell             # Backend 셸
make shell-db          # Database 셸
```

### 개발 작업

```bash
make test              # 테스트 실행
make test-watch        # 감시 모드 (변경감지)
make test-coverage     # 커버리지 분석
make format            # 코드 포맷팅
make lint              # 코드 검사 (Ruff)
make type-check        # 타입 검사 (mypy)
make quality           # 전체 품질 검사
```

### 데이터베이스

```bash
make migrate           # 마이그레이션 실행
make migration-new MSG='add user'  # 새 마이그레이션 생성
make migration-history # 마이그레이션 이력
make db-reset          # DB 초기화 (⚠️ 위험!)
```

### Git & 동기화

```bash
make sync              # Upstream 동기화 (사내용)
make status            # Git 상태 확인
```

### 정리

```bash
make clean             # 미사용 Docker 리소스 삭제
make clean-all         # 전체 삭제 (⚠️ 위험!)
```

### 유틸리티

```bash
make info              # 프로젝트 정보
make version           # 버전 확인
make health            # 시스템 상태
make docs              # 문서 안내
```

---

## 🚀 실전 워크플로우

### 개발 시작

```bash
# 1. 환경 초기화
make init

# 2. 환경 시작
make up

# 3. 로그 확인
make logs

# 4. 테스트
make test
```

### 코드 작성 및 검증

```bash
# 1. 코드 작성 (에디터에서)

# 2. 포맷팅
make format

# 3. 테스트
make test

# 4. 품질 검사
make quality
```

### 마이그레이션 작업

```bash
# 1. 새 마이그레이션 생성
make migration-new MSG='add users table'

# 2. 마이그레이션 검토 (alembic/versions/ 확인)

# 3. 마이그레이션 실행
make migrate
```

### 주간 동기화 (사내)

```bash
# 1. Upstream에서 최신 코드 가져오기
make sync

# 2. 테스트
make test

# 3. 완료
git status
```

---

## 🔧 환경별 사용법

### 사외 개발자

```bash
# 기본 설정 (사외)
make init
make up

# 개발
make test
make format
```

### 사내 개발자

```bash
# 회사 환경 초기화
make init ENVIRONMENT=company

# 환경 시작 (자동으로 override 파일 적용)
make up ENVIRONMENT=company

# 개발
make test
```

---

## 💡 Makefile 변수 지정

### 포트 변경

```bash
# Backend 포트 8000 → 8001로 변경
make up BACKEND_PORT=8001
```

### DB 포트 변경

```bash
make up DB_PORT=5433
```

### 여러 변수 함께 사용

```bash
make up ENVIRONMENT=company BACKEND_PORT=8001 DB_PORT=5433
```

---

## 📊 자주 사용하는 조합

### 처음부터 깨끗하게 시작

```bash
make clean-all
make init
make rebuild
make test
```

### 문제 해결 후 재시작

```bash
make down
make build
make up
make logs
```

### 일일 개발 루틴

```bash
# 아침: 최신 코드 동기화 (사내)
make sync
make test

# 낮: 개발
# (에디터에서 코드 작성)

# 저녁: 품질 검사
make quality
```

### 배포 전 최종 검증

```bash
make clean
make rebuild
make quality
make test-coverage
```

---

## 🎨 색상 출력

Makefile은 다음과 같이 색상으로 출력됩니다:

```
🔵 파란색 (BLUE):    정보 제목
🟢 초록색 (GREEN):   성공 메시지
🟡 노란색 (YELLOW):  진행 중
🔴 빨간색 (RED):     오류 또는 경고
```

---

## 💻 실행 예시

### 예시 1: 처음 환경 구축

```bash
$ make init
✅ 초기 설정 완료

$ make up
🚀 환경 시작 중 (default)...

✅ 시작 완료!

포트:
  Backend:  http://localhost:8000
  Database: localhost:5432

다음 명령을 실행하세요:
  make logs      # 로그 확인
  make test      # 테스트 실행
  make shell     # Backend 셸
```

### 예시 2: 테스트 실행

```bash
$ make test
🧪 테스트 실행 중 (Backend)
======================== test session starts =========================
...
======================== 45 passed in 2.34s ==========================
```

### 예시 3: 코드 품질 검사

```bash
$ make quality
🔍 코드 품질 검사 (lint + format + type-check)
→ Lint 검사...
🔎 코드 검사 중 (Ruff)
✅ 검사 완료

→ 타입 검사...
✅ 타입 검사 중 (mypy strict)
✅ 품질 검사 완료
```

---

## ⚠️ 위험 명령어

### DB 초기화 (모든 데이터 삭제)

```bash
make db-reset
# 확인 메시지: "정말 초기화하시겠습니까? (yes/no): "
```

### 전체 정리 (모든 컨테이너, 볼륨, 이미지 삭제)

```bash
make clean-all
# 확인 메시지: "정말 진행하시겠습니까? (yes/no): "
```

**주의**: 위 명령어는 **확인 후 실행됩니다**. 실수로 치운 데이터는 복구되지 않습니다.

---

## 🔧 Makefile 수정 (고급)

### 새 명령어 추가

```makefile
# Makefile의 끝에 추가
my-command:
	@echo "실행 중..."
	docker-compose exec backend python -c "..."
	@echo "완료!"
```

### 기존 명령어 수정

```makefile
# test 명령어를 수정하려면
test:
	@echo "🧪 테스트 실행 중 (Custom)"
	docker-compose exec backend pytest tests/ -v
```

---

## 📚 관련 명령어

### `make help` 출력

```bash
$ make help

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
slea-ssem - Docker 개발 환경 관리
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

초기 설정:
  make init              🔧 환경 파일 초기화

Docker 관리:
  make build             🔨 이미지 빌드
  make up                🚀 환경 시작
  ...
```

### `make info` 확인

```bash
$ make info
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
프로젝트 정보
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
프로젝트: slea-ssem
이미지: slea-backend:0.1.0
환경: default
Backend 포트: 8000
DB 포트: 5432

Docker version 24.0.x, build xxx
Docker Compose version 2.x.x, build xxx
```

### `make health` 상태 확인

```bash
$ make health
🏥 시스템 상태 확인 중...

Docker:
  ✅ Docker running

Services:
  slea-db                 Up (healthy)
  slea-backend            Up

Network:
  ✅ Backend responding
```

---

## 🎓 학습 순서

### Day 1: 기본 명령어

```bash
make help              # 도움말 보기
make init              # 초기 설정
make up                # 환경 시작
make logs              # 로그 확인
make down              # 환경 정지
```

### Day 2: 개발 작업

```bash
make test              # 테스트
make format            # 포맷팅
make lint              # 검사
```

### Day 3: 고급 작업

```bash
make quality           # 종합 검사
make test-coverage     # 커버리지
make migrate           # 마이그레이션
```

### Day 4: 유지보수

```bash
make sync              # 동기화 (사내)
make health            # 상태 확인
make clean             # 정리
```

---

## ✅ 체크리스트

- [ ] Makefile이 프로젝트 루트에 있음
- [ ] `make help` 실행 가능
- [ ] `make init` 성공
- [ ] `make up` 성공
- [ ] `make test` 성공
- [ ] `make down` 성공

---

## 🆘 문제 해결

### "make: command not found"

**해결**: Make 설치
```bash
# macOS
brew install make

# Ubuntu/Debian
sudo apt-get install make

# Windows (WSL)
sudo apt-get install make
```

### "docker: command not found"

**해결**: Docker 설치
```bash
# https://www.docker.com/products/docker-desktop
```

### "Permission denied"

**해결**: 스크립트 권한 확보
```bash
chmod +x tools/sync-with-upstream.sh
```

---

## 📝 요약

| 상황 | 명령어 |
|------|--------|
| 처음 시작 | `make init && make up` |
| 개발 | `make test && make format` |
| 품질 검사 | `make quality` |
| 로그 확인 | `make logs` |
| 정리 | `make clean` |
| 동기화 | `make sync` |

---

**작성**: 2025-11-25
**버전**: 1.0
**참고**: 회사 youtube-summary-mcp Makefile 패턴 기반
