# Quick Start: Outside-In 전략으로 개발 시작하기

**대상**: 사외 및 사내 개발자
**읽기 시간**: 5분
**목표**: 첫 개발 환경 구축까지의 최단 경로

---

## 🎯 상황 파악 (1분)

### 당신의 위치는?

#### A. 사외 개발자 (GitHub.com 에서 작업)

```
공개 GitHub에서 협업
→ 이 문서의 "사외 개발자" 섹션 보기
```

#### B. 사내 개발자 (GitHub.company.com 에서 작업)

```
회사 내부에서 개발
→ 이 문서의 "사내 개발자" 섹션 보기
```

---

## 👥 사외 개발자

### Step 1: 저장소 설정 (5분)

```bash
# 1. Fork 또는 Clone
git clone https://github.com/{YOUR-ID}/slea-ssem.git
cd slea-ssem

# 2. Upstream 추가 (원본 저장소)
git remote add upstream https://github.com/dEitY719/slea-ssem.git

# 3. 확인
git remote -v
# origin   https://github.com/{YOUR-ID}/slea-ssem.git
# upstream https://github.com/dEitY719/slea-ssem.git
```

### Step 2: Docker 환경 시작 (3분)

```bash
# 1. Docker 설치 확인
docker --version
docker compose version

# 2. 환경 시작
docker-compose up -d

# 3. 상태 확인
docker-compose ps
# NAME            STATUS
# slea-db         Up (healthy)
# slea-backend    Up
```

### Step 3: 개발 시작 (5분)

```bash
# 1. Feature 브랜치 생성
git checkout -b feature/my-feature upstream/develop

# 2. 코드 작성 (에디터에서 수정)
# 자동으로 컨테이너에 반영됨

# 3. 테스트
docker-compose exec backend pytest tests/backend/ -v

# 4. 커밋
git add .
./tools/commit.sh

# 5. Push & PR
git push origin feature/my-feature
# GitHub에서 PR 생성
```

### 주간 정리

```bash
# 최신 코드 유지
git fetch upstream develop
git pull upstream develop

# 또는 rebase (깔끔한 히스토리)
git rebase upstream/develop
```

---

## 🏢 사내 개발자

### Step 1: 저장소 설정 (5분)

```bash
# 1. 사내 저장소 Clone
git clone https://github.company.com/aig/slea-ssem.git
cd slea-ssem

# 2. Upstream 추가 (사외 공개 저장소)
git remote add upstream https://github.com/dEitY719/slea-ssem.git

# 3. 확인
git remote -v
# origin   https://github.company.com/aig/slea-ssem.git
# upstream https://github.com/dEitY719/slea-ssem.git
```

### Step 2: 회사 환경 설정 (5분)

```bash
# 1. Override 파일 생성
cp docker-compose.override.yml.example docker-compose.override.yml

# 2. 회사 정보 입력 (편집기로 열기)
nano docker-compose.override.yml

# 수정 항목:
# - PIP_INDEX_URL: 회사 PyPI 미러 주소
# - HTTP_PROXY / HTTPS_PROXY: 회사 프록시
# - DATABASE_URL: 회사 DB 서버

# 3. 환경 변수 파일
cat > .env.company << 'EOF'
DB_USER=internal_user
DB_PASSWORD=<strong_password>
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
EOF
```

### Step 3: Docker 환경 시작 (3분)

```bash
# 1. 초기 동기화 (첫 실행만)
./tools/sync-with-upstream.sh

# 2. Docker 환경 시작
docker-compose up -d

# 3. 상태 확인
docker-compose ps
docker-compose logs backend | head -20
```

### Step 4: 개발 시작 (5분)

```bash
# 1. Feature 브랜치 생성
git checkout -b feature/my-feature origin/develop

# 2. 코드 작성
# 자동으로 컨테이너에 반영됨

# 3. 테스트
docker-compose exec backend pytest tests/backend/ -v

# 4. 커밋 및 Push
git add .
./tools/commit.sh
git push origin feature/my-feature

# 5. PR 생성 (사내 GitLab)
```

### 주간 동기화 (필수!)

**매주 금요일 오후**:

```bash
# 사외 최신 코드 가져오기
./tools/sync-with-upstream.sh

# 결과 확인
git log --oneline -5

# 테스트
docker-compose exec backend pytest tests/backend/ -v

# 반영
git push origin develop
```

---

## 🔄 환경별 명령어 비교

| 작업 | 사외 | 사내 |
|------|------|------|
| **환경 시작** | `docker-compose up -d` | `docker-compose up -d` (자동 override 적용) |
| **코드 가져오기** | `git pull upstream develop` | `./tools/sync-with-upstream.sh` |
| **특정 파일만 동기화** | `git checkout upstream/develop -- <file>` | `git cherry-pick <commit-id>` |
| **테스트** | `docker-compose exec backend pytest` | `docker-compose exec backend pytest` |
| **로그 확인** | `docker-compose logs -f backend` | `docker-compose logs -f backend` |
| **DB 접속** | `psql -h localhost -U slea_user sleassem_dev` | `psql -h postgres.company.internal -U internal_user sleassem` |

---

## ✅ 체크리스트

### 초기 설정 후

- [ ] `docker-compose ps` → 2개 서비스 실행 중
- [ ] `curl http://localhost:8000/api/health` → 200 OK
- [ ] `docker-compose exec backend pytest tests/backend/ -k test_health -v` → 통과
- [ ] `git remote -v` → origin + upstream 모두 있음

### 주간 유지

- [ ] (사내만) 금요일에 `./tools/sync-with-upstream.sh` 실행
- [ ] 테스트 통과
- [ ] `git push origin develop` 완료

---

## 🆘 자주하는 실수

### 실수 1: "origin에 push했는데 사외에 안 보여"

**원인**: 사내 저장소는 폐쇄되어 있음

**해결**: 사외에서는 사외 fork만 사용
```bash
# 사외: 자신의 fork에만 push
git push origin feature/my-feature  # 개인 fork

# 그 후 GitHub에서 PR 생성
# (upstream/develop으로)
```

---

### 실수 2: "동기화 후 충돌이 난다"

**원인**: 로컬 변경사항과 upstream 변경사항 충돌

**해결**:
```bash
# 1. 현재 변경사항 저장
git stash

# 2. 동기화
./tools/sync-with-upstream.sh

# 3. 변경사항 복원
git stash pop

# 4. 충돌 해결 후
git add .
git commit -m "fix: resolve merge conflict"
```

---

### 실수 3: "민감한 정보를 실수로 커밋했다"

**원인**: docker-compose.override.yml 또는 .env를 커밋

**해결**:
```bash
# 즉시 제거
git rm --cached docker-compose.override.yml
git rm --cached .env.company

# .gitignore 확인
cat .gitignore | grep -E "(override|\.env)"

# 다시 커밋
git commit -m "fix: remove sensitive files"
```

---

## 📚 다음 읽을 문서

| 상황 | 문서 | 읽기시간 |
|------|------|---------|
| **전체 전략 이해** | OUTSIDE-IN-STRATEGY.md | 15분 |
| **Docker 배우기** | DOCKER-DEVELOPMENT-GUIDE.md | 2시간 |
| **단계별 구현** | IMPLEMENTATION-CHECKLIST.md | 2시간 |
| **문제 해결** | 각 문서의 FAQ 섹션 | 5-10분 |

---

## 💬 빠른 FAQ

**Q: Docker 설치는?**
A: https://www.docker.com/products/docker-desktop → 다운로드 후 실행

**Q: Python 버전이 다르면?**
A: Docker를 사용하므로 버전 상관없음 (모두 Python 3.11)

**Q: 로컬에서도 테스트 할 수 있나?**
A: 네, `pytest tests/backend/ -v` (venv 필요)

**Q: 사외에서 사내 코드를 수정할 수 있나?**
A: 아니요, 사내 저장소는 폐쇄됨. 사외 저장소에서만 기여

**Q: 매주 모든 코드를 다시 가져와야 하나?**
A: 아니요, `sync-with-upstream.sh`가 변경사항만 가져옴

---

## 🚀 첫 개발까지의 타임라인

```
사외 개발자:
Step 1 (5분) → Step 2 (3분) → Step 3 (5분) = 13분 ✨

사내 개발자:
Step 1 (5분) → Step 2 (5분) → Step 3 (3분) → Step 4 (5분) = 18분 ✨
```

**지금 시작하세요!**

```bash
# 사외
git clone https://github.com/{YOUR-ID}/slea-ssem.git
cd slea-ssem
git remote add upstream https://github.com/dEitY719/slea-ssem.git
docker-compose up -d

# 사내
git clone https://github.company.com/aig/slea-ssem.git
cd slea-ssem
git remote add upstream https://github.com/dEitY719/slea-ssem.git
cp docker-compose.override.yml.example docker-compose.override.yml
# ↓ 파일 편집
docker-compose up -d
```

---

**작성**: 2025-11-25
**버전**: 1.0
**전략**: Outside-In (사외 Upstream 중심)
