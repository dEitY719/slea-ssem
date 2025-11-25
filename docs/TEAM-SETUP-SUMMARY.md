# 팀 협업 환경 설정 - 최종 요약

**상황**: 사외(공개) + 회사(폐쇄) 이중 저장소 환경
**목표**: 효율적이고 안전한 협업 구조 수립
**완료 시간**: 2-3시간 (초기 설정) + 1주 (팀 전체 적용)

---

## 📋 한눈에 보는 구조

### 현재 문제

```
❌ 일방향 흐름
사외 (github.com)   →  회사 (github.company.com)
(공개, 협업 가능)      (폐쇄, push 불가)
        ↓
회사에서 수정된 코드를 사외로 다시 공유 불가능
```

### 권장 해결책: Upstream/Downstream 모델

```
✅ 양방향 협업 + 안전한 격리

┌──────────────────────────────────────────────────┐
│ UPSTREAM (사외 공개)                              │
│ https://github.com/dEitY719/slea-ssem.git         │
│ ├─ main (프로덕션)                                │
│ └─ develop (개발 통합, PR 병합)                   │
└──────────────────┬───────────────────────────────┘
                   │ (주 1회 동기화)
        ┌──────────┴──────────┐
        ↓                     ↓
┌──────────────────┐  ┌──────────────────┐
│ 개인 환경         │  │ 회사 내부        │
│ (사외 Fork)      │  │ (내부 GitLab)   │
│                  │  │                  │
│ feature 개발     │  │ proxy 설정       │
│ PR 생성          │  │ DB 연결          │
│ 리뷰             │  │ 회사 규정        │
└──────────────────┘  └──────────────────┘
        │                     │
        └─────────────┬───────┘
                      ↓
              📚 Git Workflow
         (BRANCH-STRATEGY.md 참조)
```

---

## 🎯 3가지 핵심 해결책

### 1️⃣ Docker를 통한 환경 통일

**문제**: "내 환경에서는 되는데 회사에서는 안 돼"

**해결책**:
```bash
# 모든 개발자 동일한 환경
docker-compose up -d
# → Python 3.11 + PostgreSQL 15 + Redis 7

# WSL/Windows/Linux 상관없음 - 모두 동일
```

**이점**:
- ✅ 환경 일관성
- ✅ 신규 개발자 빠른 온보딩
- ✅ "환경 문제"로 인한 버그 감소

**참고**: `DOCKER-DEVELOPMENT-GUIDE.md`

---

### 2️⃣ Git Upstream 모델로 코드 동기화

**문제**: 회사 코드를 사외로 공유 불가능

**해결책**:

```bash
# 개인 환경 (사외)
git remote add upstream https://github.com/dEitY719/slea-ssem.git
# feature 개발 → PR → Merge to develop

# 회사 환경 (폐쇄)
git remote add upstream https://github.com/dEitY719/slea-ssem.git
# 주 1회: git pull upstream develop
# 회사 설정 (proxy, DB) 추가 후 push origin develop
```

**이점**:
- ✅ 사외에서는 공개 협업 가능
- ✅ 회사에서는 폐쇄 환경 유지
- ✅ 두 저장소 간 코드 동기화

**참고**: `COLLABORATION-WORKFLOW.md`

---

### 3️⃣ 단계별 구현 체크리스트

**문제**: "어떤 파일을 만들어야 하는데?"

**해결책**: 단계별 체크리스트 제공

```bash
Phase 1: Git 저장소 설정 (30분)
Phase 2: Docker 환경 구성 (1시간)
Phase 3: Docker Compose 테스트 (30분)
Phase 4: Git 워크플로우 설정 (30분)
Phase 5: 회사 환경 준비 (30분)
Phase 6: 최종 검증 (30분)
```

**참고**: `IMPLEMENTATION-CHECKLIST.md`

---

## 📁 새로 추가되는 파일

### Docker 관련

```
Dockerfile          (Backend 이미지 정의)
docker-compose.yml  (모든 서비스 정의)
.dockerignore       (빌드 제외 파일)
```

### 문서

```
docs/
├─ COLLABORATION-WORKFLOW.md  (이중 저장소 협업 전략)
├─ DOCKER-DEVELOPMENT-GUIDE.md (Docker 개념 + 사용법)
├─ IMPLEMENTATION-CHECKLIST.md (단계별 체크리스트)
├─ BRANCH-STRATEGY.md          (Git 브랜치 전략)
└─ TEAM-SETUP-SUMMARY.md       (이 파일)
```

### 스크립트

```
tools/sync-with-upstream.sh    (주간 동기화)
setup-company-env.sh           (회사 환경 초기화)
setup-proxy.sh                 (proxy 설정, 필요시)
```

---

## 👥 팀별 역할 및 단계

### 1단계: 리드 개발자 (2-3시간)

**당신이 해야 할 일**:

```bash
# 1. 구현 체크리스트 따라 설정
- IMPLEMENTATION-CHECKLIST.md의 Phase 1-6 완료
- Dockerfile, docker-compose.yml 작성
- 각종 스크립트 준비

# 2. 문서 검토
- COLLABORATION-WORKFLOW.md 검토 및 수정
- DOCKER-DEVELOPMENT-GUIDE.md 검토
- 회사 환경에 맞게 customize

# 3. 테스트
- 처음부터 끝까지 한 번 재실행
- 동료가 따라 할 수 있는지 검증

# 4. 팀에 공유
git push origin develop
팀에 공지: "협업 환경 설정 완료, 다음 문서 읽어주세요"
```

### 2단계: 동료 A, B (1시간 각)

**동료들이 해야 할 일**:

```bash
# 1. 문서 읽기 (20분)
- COLLABORATION-WORKFLOW.md: 전체 개요 이해
- DOCKER-DEVELOPMENT-GUIDE.md: Docker 기본 개념
- BRANCH-STRATEGY.md: Git 브랜치 규칙

# 2. 로컬 환경 설정 (30분)
git pull origin develop  # 최신 코드 가져오기
docker-compose up -d     # 환경 시작
docker-compose exec backend pytest tests/backend/ -v  # 테스트

# 3. Feature 개발 시작
git checkout -b feature/my-feature upstream/develop
# ... 코드 작성 ...
git push origin feature/my-feature  # PR 생성
```

### 3단계: 회사 환경 (온보딩 시)

**회사에 입사하면**:

```bash
# 1. 회사 저장소 설정 (setup-company-env.sh)
git clone https://github.company.com/aig/slea-ssem.git
cd slea-ssem
git remote add upstream https://github.com/dEitY719/slea-ssem.git

# 2. 초기 동기화
git fetch upstream develop
git merge upstream/develop

# 3. 회사 설정 추가
.env.company 파일 작성 (proxy, DB 정보)
docker-compose up -d

# 4. 작업 시작
# 개인 저장소처럼 사용, 단 push는 회사 저장소만
```

---

## 📖 문서 읽기 순서

### 빠른 시작 (15분)

1. **이 문서** (TEAM-SETUP-SUMMARY.md) - 현재 읽는 중
2. **COLLABORATION-WORKFLOW.md** - 전체 구조 이해 (5분)
3. **BRANCH-STRATEGY.md** - Git 사용법 (5분)

### 상세 학습 (2시간, 선택)

4. **DOCKER-DEVELOPMENT-GUIDE.md** - Docker 개념 + 실습 (1시간)
5. **IMPLEMENTATION-CHECKLIST.md** - 직접 구현 (1시간)

### 실무 참고 (필요시)

- `tools/sync-with-upstream.sh` - 코드 읽으며 이해
- `setup-company-env.sh` - 회사 환경 설정 때 참고

---

## ❓ 흔한 질문들

### Q1: 사외와 회사 코드가 달라져도 괜찮나요?

**A**: 네, 괜찮습니다!

```
사외 (upstream/develop)
├─ 공개 기능만 (RAG, 스코어링 등)
└─ 외부 기여 환영

회사 (origin/develop)
├─ 사외 모든 코드 포함
├─ + 회사 설정 (proxy, 내부 DB)
├─ + 회사 규정 준수 코드
└─ 내부 폐쇄
```

주 1회 `sync-with-upstream.sh`로 사외 최신 코드 가져옵니다.

---

### Q2: Docker 경험이 없으신데요?

**A**: `DOCKER-DEVELOPMENT-GUIDE.md`에서 배울 수 있습니다!

```
Day 1: 개념 (30분)
Day 2: 실습 1 (1시간)
Day 3: 실습 2 (1.5시간)
Day 4: 워크플로우 (1시간)
Day 5: 문제 해결 (1시간)
→ 1주일 후 전문가 수준

아니면, 지금 당장:
docker-compose up -d
docker-compose logs -f backend
# 3개 명령어만 알면 80% 충분!
```

---

### Q3: 회사에서 proxy/방화벽이 있어요

**A**: `setup-proxy.sh`로 설정 후 정상 작동합니다

```bash
# setup-proxy.sh 수정
export HTTP_PROXY="http://proxy.company.com:8080"

# Docker도 proxy 설정
~/.docker/config.json:
{
  "httpProxy": "http://proxy.company.com:8080"
}
```

---

### Q4: 어떤 작업이 필요한가요?

**A**: 아래 표를 참고하세요

| 작업 | 리드 | 동료A | 동료B | 회사 진입 |
|------|------|-------|-------|---------|
| 문서 읽기 | ✅ | ✅ | ✅ | ✅ |
| Dockerfile 작성 | ✅ | - | - | - |
| docker-compose.yml 작성 | ✅ | - | - | - |
| 로컬 테스트 | ✅ | ✅ | ✅ | ✅ |
| 회사 환경 설정 | - | - | - | ✅ |
| 코드 리뷰 | - | 상호 | 상호 | ✅ |

---

## 🚀 즉시 실행 가능한 명령어

### 환경 시작

```bash
docker-compose up -d
```

### 상태 확인

```bash
docker-compose ps
docker-compose logs -f backend
```

### 테스트 실행

```bash
docker-compose exec backend pytest tests/backend/ -v
```

### 코드 변경 감지

```bash
# 호스트에서 파일 수정 → 컨테이너에 자동 반영
# editor에서 src/backend/main.py 수정
# logs에 "Reloading server" 메시지 보임
```

### 정리

```bash
docker-compose down       # 데이터 유지
docker-compose down -v    # 초기화
```

---

## 📊 예상 효과

### Before (현재)

```
❌ 환경 불일치
- Python 버전 다름
- DB 버전 다름
- "내 환경에서는 되는데..."

❌ 협업 어려움
- 사외에만 push 가능
- 회사 코드 사외 공유 불가능
- 버전 관리 복잡

❌ 신규 개발자 온보딩
- 환경 설정 1-2일
- 이슈 해결 추가 시간
```

### After (Docker + Workflow 적용)

```
✅ 환경 일관성
- 모두 Docker 컨테이너
- Windows/WSL/Linux 구분 없음
- "내 환경에서는..." 문제 제로

✅ 효율적 협업
- 사외: 공개 협업 (PR 리뷰)
- 회사: 폐쇄 개발 (내부 규정)
- 주 1회 자동 동기화

✅ 빠른 온보딩
- docker-compose up -d
- 3개 명령어로 환경 완성
- 개발 시작 15분
```

---

## ✅ 체크리스트: 지금 바로 시작하기

### Step 1: 이해 (15분)

- [ ] 이 문서 읽음
- [ ] "3가지 핵심 해결책" 이해
- [ ] 팀 역할 이해

### Step 2: 학습 (1시간)

- [ ] COLLABORATION-WORKFLOW.md 읽음
- [ ] DOCKER-DEVELOPMENT-GUIDE.md 읽음
- [ ] BRANCH-STRATEGY.md 읽음

### Step 3: 구현 (2시간)

- [ ] IMPLEMENTATION-CHECKLIST.md 따라 Phase 1-6 완료
- [ ] Dockerfile, docker-compose.yml 커밋
- [ ] 다른 동료가 clone → 테스트 성공 확인

### Step 4: 공유 (30분)

- [ ] 팀에 공지
- [ ] 동료들이 문서 읽도록 안내
- [ ] Q&A 준비

### Step 5: 회사 준비 (선택)

- [ ] setup-company-env.sh 준비
- [ ] 회사 DB 정보 수집
- [ ] Proxy 설정 테스트

---

## 📞 문제 시 참고

### 가장 많은 문제

| 순위 | 문제 | 해결 |
|------|------|------|
| 1️⃣ | Docker 설치 안 됨 | Docker Desktop 다시 설치 |
| 2️⃣ | Port 5432 충돌 | WSL PostgreSQL 중지 |
| 3️⃣ | 환경 변수 누락 | docker-compose.yml 확인 |
| 4️⃣ | 테스트 실패 | `docker-compose logs` 확인 |
| 5️⃣ | 파일 변경 미반영 | `docker-compose restart` |

**더 많은 문제**: DOCKER-DEVELOPMENT-GUIDE.md의 "실제 마주치는 문제" 섹션

---

## 🎯 다음 마일스톤

### 이번 주
- [ ] 리드 개발자: 초기 설정 완료
- [ ] 동료들: 환경 구축 완료

### 다음 주
- [ ] 모든 개발자: Docker 환경에서 개발 시작
- [ ] 첫 feature PR 생성 및 리뷰

### 2주 후
- [ ] 모든 팀 원이 새로운 워크플로우 숙달
- [ ] 회사 진입 준비 완료

---

## 📚 관련 문서 링크

현재 생성된 문서:

| 문서 | 용도 | 읽기 시간 |
|------|------|---------|
| [COLLABORATION-WORKFLOW.md](/docs/COLLABORATION-WORKFLOW.md) | 전체 협업 구조 | 10분 |
| [DOCKER-DEVELOPMENT-GUIDE.md](/docs/DOCKER-DEVELOPMENT-GUIDE.md) | Docker 학습 + 실습 | 2시간 |
| [BRANCH-STRATEGY.md](/docs/BRANCH-STRATEGY.md) | Git 브랜치 규칙 | 5분 |
| [IMPLEMENTATION-CHECKLIST.md](/docs/IMPLEMENTATION-CHECKLIST.md) | 단계별 구현 | 2시간 |
| [TEAM-SETUP-SUMMARY.md](/docs/TEAM-SETUP-SUMMARY.md) | 이 문서 | 10분 |

---

## 💡 핵심 메시지

> 🎯 **목표**: 어디서나 같은 환경, 효율적인 협업

```
현재: 복잡한 환경 설정 + 협업 복잡성
     ↓
Docker + Git Workflow 적용
     ↓
"docker-compose up -d" = 완벽한 개발 환경
```

> 📝 **원칙**: 문서 먼저, 구현 나중

```
1. 이 문서 읽기
2. COLLABORATION-WORKFLOW.md로 전체 이해
3. IMPLEMENTATION-CHECKLIST.md로 실제 구현
4. 팀과 공유 및 협업 시작
```

---

**최종 목표**:
- ✅ 사외 + 회사 환경 모두 효율적 운영
- ✅ 모든 개발자가 동일한 개발 환경 사용
- ✅ 코드 동기화 자동화
- ✅ 새 개발자 온보딩 15분 내 완료

---

**문서 작성**: 2025-11-25
**버전**: 1.0
**검토 상태**: 팀 검토 예정

**다음 단계**:
1. 이 문서를 팀과 공유
2. IMPLEMENTATION-CHECKLIST.md 실행
3. 동료들과 함께 환경 구축
