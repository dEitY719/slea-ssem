# Docker 구조 비교: 현재 vs 리팩토링 후

## 현재 구조의 혼동점

### 실제 흐름 추적 (현재)

```
$ make build-internal

┌─────────────────────────────────────────────────┐
│ 사용자가 make build-internal 실행               │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ Makefile: build-internal → build ENV=internal   │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ ENV_FILE=.env.internal으로 설정                 │
│ COMPOSE_FILES=docker-compose.yml +              │
│              docker-compose.internal.yml        │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ cd docker/                                       │ ← 중요!
│ docker compose --env-file .env.internal \        │
│                -f docker-compose.yml \           │
│                -f docker-compose.internal.yml \  │
│                build                             │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ 루트의 Dockerfile 참조:                          │
│ context: ..                                      │
│ dockerfile: Dockerfile                           │
│ 사용 ✓                                            │
└─────────────────────────────────────────────────┘
```

### 문제점 표시

```
slea-ssem/ (프로젝트 루트)
├── Dockerfile                    ← 이것을 사용
│   (docker/docker-compose.yml의 context: .. 에서 참조)
│
├── docker-compose.yml            ← 이것은 사용 안 함!
│   (혼동 발생: 왜 루트에도 있지?)
│
├── docker/
│   ├── docker-compose.yml        ← 이것을 사용
│   │   (cd docker에서 실행되므로)
│   │
│   ├── docker-compose.internal.yml
│   │   (이것도 사용)
│   │
│   ├── .env.example              ← 외부 환경 문서
│   ├── .env.internal.example     ← 사내 환경 문서
│   ├── .env                      ← 생성: make init
│   └── .env.internal             ← 생성: make init-internal
│
└── tmp/
    └── Dockerfile-internal       ← 이것은 누구 거?
        (사용되지 않는 파일)
```

### 신규 팀원의 혼동

```
Q1: 루트의 docker-compose.yml은 뭐지?
   → A: 사용 안 함 (docker/ 것을 씀)
   Q2: 왜 루트에도 있어?
   → A: (침묵...)

Q3: Dockerfile이 루트에 있는데, 사내 빌드할 때도 이걸 써?
   → A: 네, 이것만 있음
   Q4: Dockerfile.internal 같은 건 없나?
   → A: tmp/Dockerfile-internal이 있긴 한데...
   Q5: 그럼 뭐 하는 건데?
   → A: 몰라... (실제로 사용 안 함)

Q6: .env와 .env.internal의 차이가 뭐야?
   → A: 외부는 공식 PyPI, 사내는 Artifactory
   Q7: 근데 docker-compose.yml과 docker-compose.internal.yml는 뭐가 달라?
   → A: docker-compose.internal.yml이 기본값을 override함
   Q8: 뭘 override 하는데?
   → A: (복잡함... 읽어봐야 할 것 같다)
```

---

## 리팩토링 후 구조 (옵션 A: 권장)

### 간단한 구조

```
slea-ssem/
├── Dockerfile                          ← 여기만 있음 (명확!)
├── docker-compose.yml                  ← 기본 (외부 환경)
├── docker-compose.internal.yml         ← 사내 환경 (override)
├── .dockerignore
├── docker/
│   ├── README.md                       ← 구조 설명
│   ├── .env.example                    ← 외부 기본값
│   ├── .env.internal.example           ← 사내 기본값
│   ├── .env                            ← 생성: make init
│   ├── .env.internal                   ← 생성: make init-internal
│   └── certs/
│       └── (인증서 파일들)
│
└── (tmp/ 없음 - 정리됨)
```

### 명확한 흐름

```
$ make build-internal

┌─────────────────────────────────────────────────┐
│ make build-internal                              │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ Makefile: build-internal → build ENV=internal   │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ ENV_FILE=.env.internal으로 설정                 │
│ COMPOSE_FILES=-f docker-compose.yml \           │
│              -f docker-compose.internal.yml     │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ (cd 불필요)                                     │
│ docker compose --env-file docker/.env.internal  │
│                -f docker-compose.yml \           │
│                -f docker-compose.internal.yml \  │
│                build                             │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ 루트의 Dockerfile 참조:                          │
│ context: .                                       │
│ dockerfile: Dockerfile                           │
│ 사용 ✓                                            │
└─────────────────────────────────────────────────┘
```

### 신규 팀원의 이해

```
Q1: docker-compose.yml은 몇 개야?
   → A: 2개 (기본 + 사내 override)
   Q2: 왜 2개?
   → A: 외부/사내 환경이 다르기 때문
   Q3: 어느 걸 써?
   → A: make build는 기본, make build-internal은 둘 다 (override)

Q4: Dockerfile은?
   → A: 루트에 하나만 있음
   Q5: 사내 빌드할 때도 이걸 써?
   → A: 네, 동일한 Dockerfile을 환경 변수로 구분

Q6: .env와 .env.internal?
   → A: 외부(공식 PyPI) vs 사내(Artifactory)
   Q7: 모두 docker/ 디렉토리에?
   → A: 네, docker/ 안에 모두 정의됨

Q8: tmp/는?
   → A: (없음 - 정리됨)
```

---

## 현재 vs 리팩토링 비교표

| 항목 | 현재 | 리팩토링 후 |
|------|------|-----------|
| **Dockerfile 위치** | 루트 ✓ | 루트 ✓ (동일) |
| **docker-compose.yml 개수** | 루트 + docker/ 중복 ❌ | 루트만 2개 (기본 + override) ✓ |
| **구조 복잡도** | 높음 ❌ | 낮음 ✓ |
| **파일 분산** | 루트 + docker/ + tmp ❌ | docker/ 중심 ✓ |
| **신규팀원 이해도** | 낮음 ❌ | 높음 ✓ |
| **표준 Docker 관례** | 준수 ✓ | 준수 ✓ (더 명확) |
| **Makefile 단순성** | cd docker 필요 ❌ | 루트에서 실행 ✓ |
| **확장성 (환경 추가)** | docker-compose.새환경.yml 추가 | docker-compose.새환경.yml 추가 (동일) |

---

## SOLID 원칙 적용 비교

### SRP (Single Responsibility)

**현재**:
- docker/docker-compose.yml과 루트의 docker-compose.yml이 역할 분담 불명확

**리팩토링 후**:
- 루트: docker-compose.yml (기본), docker-compose.internal.yml (사내)
- 역할 명확

### OCP (Open/Closed)

**현재**:
```makefile
# 환경 추가 시 Makefile도 수정해야 함 ❌
ifeq ($(ENV),internal)
    COMPOSE_FILES := $(COMPOSE_BASE) -f docker-compose.internal.yml
else
    COMPOSE_FILES := $(COMPOSE_BASE)
endif
```

**리팩토링 후**:
```makefile
# docker-compose.new-env.yml만 추가하면 됨 ✓
COMPOSE_FILES := $(COMPOSE_BASE) $(COMPOSE_OVERRIDES)
```

### ISP (Interface Segregation)

**현재**:
- Dockerfile 하나가 모든 것을 처리 (모든 ARG 포함)

**리팩토링 후**:
- Dockerfile 하나 (필요한 것만 ARG로 받음)
- docker-compose.yml이 실제 필요한 값만 전달

---

## 마이그레이션 영향 분석

### 사용자 명령어 변화

```bash
# 외부 PC - 변화 없음 ✓
make build
make up

# 사내 PC - 변화 없음 ✓
make build-internal
make up-internal

# 내부 동작 - 변화 (투명) ✓
# cd docker가 없어져서 더 빠름
# 경로 관리가 단순해짐
```

### CI/CD 영향

```bash
# GitHub Actions 등의 스크립트
# docker-compose.yml 경로 확인 필요

# 현재:
cd docker
docker compose -f docker-compose.yml build

# 리팩토링 후:
docker compose -f docker-compose.yml build
```

---

## 위험 요소 및 대응

| 위험 | 심각도 | 대응책 |
|------|--------|--------|
| 마이그레이션 중 빌드 깨짐 | 높음 | Phase별 진행, 각 Phase에서 검증 |
| 기존 스크립트 경로 참조 | 중간 | git grep으로 docker/ 경로 검색 후 수정 |
| CI/CD 환경 변수 경로 | 중간 | 사전 테스트 (GitHub Actions 테스트) |
| 팀원 혼동 | 낮음 | 명확한 문서화 + 온보딩 |

---

## 검증 체크리스트

### Phase 1-2 후 검증

```bash
# 테스트 환경: WSL2 (사외 PC)
make build                     # ✓ 성공
make up                        # ✓ 성공
curl http://localhost:8000/health  # ✓ 응답

# 테스트 환경: 사내 PC
make build-internal            # ✓ 성공 (경고 정상)
make up-internal               # ✓ 성공
curl http://localhost:8000/health  # ✓ 응답
```

### Phase 3-4 후 검증

```bash
# 신규 팀원 온보딩 (README만 읽음)
git clone ...
make help                      # 구조 이해 가능?
make init                      # 설정 가능?
make build                     # 빌드 가능?
make up                        # 시작 가능?
```

---

## 예상 효과

### 개선 전

```
개발자: "Docker 구조가 왜 이렇게 복잡해?"
신규팀원: "make init 한 후 뭘 해야 하는데?"
매니저: "환경 설정에서 자꾸 문제가 나는데?"
```

### 개선 후

```
개발자: "아, 루트에 docker-compose.yml 두 개구나"
신규팀원: "make help로 충분하네"
매니저: "빌드 실패율 감소"
```
