# Outside-In 전략: 사외 GitHub → 사내 GitHub 단방향 동기화

**상황**: 사외(공개 GitHub) + 사내(폐쇄 GitLab) 이중 저장소 환경
**전략**: Upstream(사외) 중심으로 Downstream(사내)이 자동 추적
**목표**: 효율적인 코드 공유 + 안전한 환경 격리

---

## 🎯 전략의 핵심

```
UPSTREAM (사외, 공개)
https://github.com/dEitY719/slea-ssem
├─ main 브랜치
└─ develop 브랜치 (기능 통합)

        ↓ (git fetch + merge, 주 1회)

DOWNSTREAM (사내, 폐쇄)
https://github.company.com/aig/slea-ssem
├─ 사외 모든 코드 포함
├─ + 사내 환경 설정 (proxy, DB, 규정)
└─ → 팀 개발 환경
```

### 핵심 원칙

1. **단방향**: 사외 → 사내 (사내 → 사외는 불가능)
2. **자동 동기화**: 주 1회 또는 필요시
3. **환경 격리**: 사외 코드 + 사내 설정 명확히 분리
4. **버전 통일**: 모든 개발자가 같은 environment로 작업

---

## 📦 환경별 파일 구조

### 공통 (Upstream - 사외에 커밋)

```
slea-ssem/
├─ Dockerfile              # 프로덕션급, ARG로 환경 전달
├─ docker-compose.yml      # 사외 개발 환경 (기본값 포함)
├─ .dockerignore
├─ pyproject.toml
├─ src/
├─ tests/
└─ docs/
```

### 사내용 (Downstream - 사내에만 존재)

```
slea-ssem/
├─ docker-compose.override.yml  # 사내 설정 (gitignore 처리)
├─ .env.company                 # 회사 환경 변수 (gitignore 처리)
├─ setup-company-env.sh         # 초기 설정 스크립트
└─ infra/
   ├─ pip.conf                  # 사내 PyPI 미러 설정
   └─ Dockerfile_example        # 참고용 회사 예제
```

---

## 🔧 Docker를 통한 환경 통일

### 왜 Docker가 필요한가?

**문제**:
```
개인 환경: Python 3.11 + PostgreSQL 15 + 프록시 X
회사 환경: Python 3.10 + PostgreSQL 13 + 프록시 O + 내부 미러

→ "개인 환경에서는 되는데 회사에서는 안 돼!"
```

**해결**: Docker Container = 표준화된 환경

```
┌─────────────────────────────┐
│ Docker Container            │
│ Python 3.11                 │
│ PostgreSQL 15               │
│ (프록시/미러 설정됨)         │
└─────────────────────────────┘
Windows / WSL / Linux / macOS
→ 모두 동일한 환경!
```

### Dockerfile의 3가지 구성

#### 1️⃣ ARG (빌드 시점 설정)

사외에서는 기본값, 사내에서는 회사 정보로 오버라이드:

```dockerfile
# Dockerfile
ARG PIP_INDEX_URL
ARG HTTP_PROXY
ARG HTTPS_PROXY
```

```yaml
# docker-compose.yml (사외, 기본값)
build:
  args:
    PIP_INDEX_URL:    # 비워둠
    HTTP_PROXY:       # 비워둠
```

```yaml
# docker-compose.override.yml (사내, 회사 정보)
build:
  args:
    PIP_INDEX_URL: http://pypi.company.internal:8080/simple
    HTTP_PROXY: http://proxy.company.com:8080
```

#### 2️⃣ ENV (런타임 설정)

```dockerfile
# Dockerfile (기본값만)
ENV PYTHONUNBUFFERED=1 \
    TZ=Asia/Seoul \
    ENVIRONMENT=development \
    PORT=8000
```

```yaml
# docker-compose.yml (사외, 개발 환경)
services:
  backend:
    environment:
      DATABASE_URL: postgresql://slea_user:change_me@db/sleassem_dev
      ENVIRONMENT: development
```

```yaml
# docker-compose.override.yml (사내, 프로덕션 환경)
services:
  backend:
    environment:
      DATABASE_URL: postgresql://internal_user:PASSWORD@postgres.company.internal/sleassem
      ENVIRONMENT: production
```

#### 3️⃣ 볼륨 마운트 (개발 vs 프로덕션)

```yaml
# docker-compose.yml (사외, 개발 중 코드 변경 감지)
volumes:
  - .:/app  # 호스트의 모든 파일 마운트 (자동 다시로드)
```

```yaml
# docker-compose.override.yml (사내, 프로덕션 읽기 전용)
volumes:
  - /app:/app  # 또는 비활성화 (변경 불가)
```

---

## 🔄 Git Workflow

### 사외 환경 (공개 협업)

```bash
# 1. 개인 Fork 저장소 clone
git clone https://github.com/{YOUR-ID}/slea-ssem.git
cd slea-ssem

# 2. Upstream 추가 (원본 저장소)
git remote add upstream https://github.com/dEitY719/slea-ssem.git

# 3. Feature 브랜치 생성
git checkout -b feature/my-feature upstream/develop

# 4. 개발 + 커밋
# ... 코드 작성 ...
git add .
./tools/commit.sh

# 5. Push & Pull Request
git push origin feature/my-feature
# GitHub에서 PR 생성
```

**리뷰 후 Merge**:
```bash
# develop 브랜치에 merge (자동 또는 수동)
git checkout develop
git pull upstream develop  # 최신 코드
```

### 사내 환경 (폐쇄 개발)

```bash
# 1. 사내 저장소 clone
git clone https://github.company.com/aig/slea-ssem.git
cd slea-ssem

# 2. Upstream 추가 (사외 공개 저장소)
git remote add upstream https://github.com/dEitY719/slea-ssem.git

# 3. 초기 동기화 (한 번만)
git fetch upstream develop
git merge upstream/develop

# 4. 회사 설정 추가
cp docker-compose.override.yml.example docker-compose.override.yml
# → .env.company, .env 파일 작성
```

**주간 동기화 (매주 금요일)**:

```bash
# 스크립트 사용 (권장)
./tools/sync-with-upstream.sh

# 또는 수동
git fetch upstream develop
git checkout develop
git merge upstream/develop  # 또는 git rebase
git push origin develop
```

---

## 📋 Docker Compose의 동작 원리

### 파일 머징

Docker Compose는 자동으로 파일을 병합합니다:

```bash
# 사외 환경
docker-compose up -d
# → docker-compose.yml만 로드

# 사내 환경
docker-compose up -d
# → docker-compose.yml + docker-compose.override.yml 자동 병합
```

### 예시: 환경별 설정 비교

**사외 (기본값)**:
```yaml
# docker-compose.yml
services:
  backend:
    ports:
      - "8000:8000"  # 로컬에서 접근 가능
    environment:
      DATABASE_URL: postgresql://slea_user:change_me@db/sleassem_dev
```

**사내 (Override)**:
```yaml
# docker-compose.override.yml
services:
  backend:
    ports:
      - "8000:8000"  # 또는 제거 (내부 트래픽만)
    environment:
      DATABASE_URL: postgresql://internal_user:password@postgres.company.internal/sleassem
```

**결과 (병합됨)**:
```yaml
# 최종 동작
services:
  backend:
    ports:
      - "8000:8000"  # docker-compose.override.yml의 값으로 덮어씀
    environment:
      DATABASE_URL: postgresql://internal_user:password@postgres.company.internal/sleassem
```

---

## 🛠️ 실전 설정

### Step 1: 사외 환경 (공개)

**Dockerfile**: ARG로 환경 수용
```dockerfile
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG PIP_INDEX_URL
ENV http_proxy=${HTTP_PROXY} https_proxy=${HTTPS_PROXY}
```

**docker-compose.yml**: 기본값 + 사외 설정
```yaml
version: '3.8'
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: sleassem_dev
      POSTGRES_PASSWORD: change_me_dev_password
  backend:
    build:
      args:
        PIP_INDEX_URL: ${PIP_INDEX_URL:-}  # 기본값 없음
        HTTP_PROXY: ${HTTP_PROXY:-}
```

### Step 2: 사내 환경 (폐쇄)

**docker-compose.override.yml**: 회사 정보로 오버라이드
```yaml
version: '3.8'
services:
  backend:
    build:
      args:
        PIP_INDEX_URL: http://pypi.company.internal:8080/simple
        HTTP_PROXY: http://proxy.company.com:8080
        HTTPS_PROXY: http://proxy.company.com:8080
        NO_PROXY: localhost,127.0.0.1,.company.com
    environment:
      DATABASE_URL: postgresql://user:pass@db.company.internal/sleassem
      ENVIRONMENT: production
```

**.gitignore**: 사내 설정은 커밋 안 함
```
.env
.env.*
docker-compose.override.yml
infra/pip.conf
```

---

## 📊 데이터 흐름

### 코드 흐름

```
사외 개발자 (GitHub.com)
    ↓
feature 브랜치 작성
    ↓
Pull Request
    ↓
Code Review (사외 팀)
    ↓
Merge to develop
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ↓
사내 저장소 (GitHub.company.com)
    ↓
주 1회 자동 동기화
git pull upstream develop
    ↓
사내 설정 추가 (docker-compose.override.yml)
    ↓
Docker 환경에서 테스트
    ↓
사내 팀이 사용
```

### 환경 격리

```
사외 GitHub
├─ 공개 기능만
├─ 기본 Dockerfile/docker-compose.yml
└─ 외부 기여 환영

회사 GitHub
├─ 사외 코드 100% 포함
├─ + docker-compose.override.yml (프록시, DB)
├─ + .env.company (민감 정보)
├─ + infra/pip.conf (사내 미러)
└─ 폐쇄 개발
```

---

## 🔐 보안

### 민감 정보 관리

```bash
# ✅ 올바른 방법
.env.company          # gitignore 처리 (커밋 X)
docker-compose.override.yml  # gitignore 처리
infra/pip.conf        # gitignore 처리

# 공유 방법:
# → 1on1로 정보 전달 또는
# → 회사 내부 Wiki에 기록
# → 암호화된 채널(1Password, Vault 등)로 공유
```

### 비루트 사용자

Dockerfile에서 비루트 사용자로 실행:
```dockerfile
RUN useradd -u 10001 -m appuser
USER appuser
```

---

## 🚀 실행 흐름

### 사외 개발자

```bash
# 1. 초기 설정 (한 번만)
git clone https://github.com/{YOUR-ID}/slea-ssem.git
cd slea-ssem
git remote add upstream https://github.com/dEitY719/slea-ssem.git

# 2. Feature 개발
git checkout -b feature/my-feature upstream/develop
docker-compose up -d
# ... 코드 작성 ...
docker-compose exec backend pytest tests/backend/ -v

# 3. PR 생성
git push origin feature/my-feature
# GitHub에서 PR 생성 및 리뷰

# 4. 최신 코드 유지
git fetch upstream develop
git pull upstream develop
```

### 사내 개발자

```bash
# 1. 초기 설정 (회사 진입 시)
git clone https://github.company.com/aig/slea-ssem.git
cd slea-ssem
git remote add upstream https://github.com/dEitY719/slea-ssem.git

# 2. 회사 환경 설정
cp docker-compose.override.yml.example docker-compose.override.yml
# → proxy, DB 정보 수정

# 3. 환경 시작
docker-compose up -d

# 4. 개발
git checkout -b feature/my-feature origin/develop
# ... 코드 작성 ...

# 5. 커밋 및 Push (사내 저장소)
git add .
git commit -m "feat: ..."
git push origin feature/my-feature

# 6. PR 생성 (사내 GitLab)

# 7. 주간 동기화 (사외 최신 코드)
./tools/sync-with-upstream.sh  # 금요일 오후 (예)
git push origin develop
```

---

## ❓ FAQ

### Q1: 사외에서 사내 코드를 볼 수 없나요?

**A**: 맞습니다. 사내 저장소는 폐쇄되어 있어 사외 팀은 볼 수 없습니다.
- 사외: 공개 코드만 개발
- 사내: 사외 코드 + 회사 설정

---

### Q2: 두 저장소 간 코드 차이가 생기면?

**A**: 사외를 "진실의 원천(source of truth)"으로 취급합니다.

```bash
# 차이 발생 시
회사 저장소의 develop
    ↑
    └─ 사외 저장소의 develop + 회사 설정

차이가 날 수 있는 경우:
1. 회사 특화 코드 (비공개 기능)
2. 환경 설정 (프록시, DB 정보)

해결책:
- 비공개 기능은 별도 브랜치나 feature flag로 관리
- 환경 설정은 docker-compose.override.yml로 분리
```

---

### Q3: Docker Compose Override는 자동으로 작동하나요?

**A**: 네, 자동으로 머징됩니다.

```bash
# 이 명령어만으로 두 파일 모두 로드
docker-compose up -d

# 내부 동작:
# 1. docker-compose.yml 로드
# 2. docker-compose.override.yml 존재 시 자동으로 병합
# 3. 같은 키는 override 파일의 값으로 덮어씀
```

---

### Q4: 회사 설정을 실수로 사외에 올렸어요

**A**: 즉시 조치:

```bash
# 1. 커밋 취소
git reset HEAD~1  # 또는 git revert

# 2. 민감 정보 제거
git rm --cached docker-compose.override.yml
git rm --cached .env.company

# 3. .gitignore 확인
cat .gitignore | grep -E "(\.env|override)"

# 4. 다시 커밋
git add .
git commit -m "fix: Remove sensitive files from git"
git push
```

---

## 📚 관련 파일

생성된 Docker 관련 파일:

| 파일 | 위치 | 용도 |
|------|------|------|
| Dockerfile | `/` | 프로덕션급 이미지 정의 |
| docker-compose.yml | `/` | 사외 개발 환경 (Git에 커밋) |
| docker-compose.override.yml.example | `/` | 사내 환경 템플릿 |
| .dockerignore | `/` | 빌드 제외 파일 |
| infra/Dockerfile_example | `/infra/` | 회사 참고 Dockerfile |

문서:

| 문서 | 용도 |
|------|------|
| OUTSIDE-IN-STRATEGY.md | 이 문서 (전략) |
| DOCKER-DEVELOPMENT-GUIDE.md | Docker 사용법 |
| IMPLEMENTATION-CHECKLIST.md | 단계별 구현 |
| TEAM-SETUP-SUMMARY.md | 팀 요약 |

---

## 🔗 동기화 스크립트

**파일**: `tools/sync-with-upstream.sh`

```bash
#!/bin/bash
# 사외 저장소 최신 코드를 사내에 가져오기

set -e

echo "🔄 Upstream (사외)에서 develop 가져오는 중..."
git fetch upstream develop

echo "📝 로컬 develop으로 전환..."
git checkout develop

echo "🔀 Merge..."
git merge upstream/develop

echo "✅ 동기화 완료!"
echo "📌 다음 명령 실행:"
echo "   git push origin develop"
```

사용:
```bash
cd slea-company  # 사내 저장소
./tools/sync-with-upstream.sh
```

---

## ✅ 체크리스트

### 사외 저장소 (공개)

- [ ] Dockerfile 작성 (ARG로 환경 설정)
- [ ] docker-compose.yml 작성 (기본값 포함)
- [ ] .dockerignore 작성
- [ ] 문서 포함 (OUTSIDE-IN-STRATEGY.md)
- [ ] Git에 커밋

### 사내 저장소 (폐쇄)

- [ ] 사외 저장소 Upstream 추가
- [ ] docker-compose.override.yml.example 복사 → 수정
- [ ] .env.company 작성 (gitignore 처리)
- [ ] infra/pip.conf 작성 (gitignore 처리)
- [ ] docker-compose up -d 성공
- [ ] 테스트 통과

---

## 🎯 Next Steps

1. **Dockerfile & docker-compose.yml 검증**
   - Docker 빌드 성공 확인
   - 테스트 실행

2. **사내 팀과 공유**
   - docker-compose.override.yml.example 배포
   - 회사 proxy/DB 정보 수집
   - 팀이 환경 구축하도록 안내

3. **자동화**
   - GitHub Actions로 사외 변경사항 자동 감지
   - 사내 repo 자동 동기화 (선택)

4. **모니터링**
   - 주간 동기화 스크린샷 기록
   - 코드 차이 추적

---

**문서 작성**: 2025-11-25
**버전**: 1.0
**전략**: Outside-In (사외 Upstream → 사내 Downstream 단방향)
