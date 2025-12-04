# Docker 구조 리팩토링 계획

## 📊 현재 상황 분석

### 현재 디렉토리 구조 (문제점 포함)

```
slea-ssem/
├── Dockerfile                          ❌ 루트에 있음
├── docker-compose.yml                  ❌ 루트에도 있음 (실제 사용 안 함)
├── .dockerignore
├── docker/
│   ├── docker-compose.yml              ❌ 루트와 중복!
│   ├── docker-compose.internal.yml     ✓ 사내 환경 override
│   ├── .env.example                    ✓ 외부 환경 기본값
│   ├── .env                            ✓ 생성된 외부 환경
│   ├── .env.internal.example           ✓ 사내 환경 기본값
│   ├── .env.internal                   ✓ 생성된 사내 환경
│   └── certs/                          ✓ 인증서 (사내)
└── tmp/
    └── Dockerfile-internal             ❌ 사용되지 않는 파일

```

### 핵심 문제점

| 문제 | 현황 | 영향 |
|------|------|------|
| **파일 위치 분산** | Dockerfile, docker-compose.yml이 루트와 docker/에 혼재 | 어디를 수정해야 하는지 불명확 |
| **docker-compose 중복** | 루트의 docker-compose.yml은 사용되지 않음 | 유지보수 부담, 혼동 |
| **Dockerfile 환경 구분 부족** | 루트의 단일 Dockerfile만 존재 (사내/사외 구분 없음) | 빌드 args로만 구분하므로 관리 복잡 |
| **환경 설정 관리** | .env vs .env.internal 개념 불명확 | 신규 팀원의 실수 위험 |
| **임시 파일** | tmp/Dockerfile-internal이 방치됨 | 불필요한 파일, 혼동 유발 |
| **Makefile 복잡성** | ENV=internal/external, --env-file, cd docker 등 여러 로직 | 명령어 실행 흐름 이해 어려움 |

---

## 🎯 SOLID 원칙 기반 리팩토링 목표

### 목표
- 🧹 **명확성**: 누구든 구조를 한눈에 이해하기
- 🔒 **안정성**: 실수 방지 (외부 PC에서 내부 빌드 등)
- 📈 **확장성**: 새로운 환경 추가 시 기존 코드 영향 최소화
- 🛠️ **유지보수성**: 한 곳만 수정하면 모든 곳에 반영

### SOLID 원칙 적용

| 원칙 | 목표 | 구현 방법 |
|------|------|----------|
| **SRP** (Single Responsibility) | 각 파일은 하나의 목적만 수행 | 환경별 Docker 파일 명확 분리 |
| **OCP** (Open/Closed) | 확장에 열려있고 수정에 닫혀있음 | docker-compose 확장 구조 (.override.yml) |
| **LSP** (Liskov Substitution) | 환경별 파일 교체 가능 | 공통 인터페이스 (compose 기본값) |
| **ISP** (Interface Segregation) | 필요한 설정만 로드 | 환경별 .env 파일 분리 |
| **DIP** (Dependency Inversion) | 구체적 파일명에 덜 의존 | Makefile이 환경 추상화 |

---

## 💡 리팩토링 옵션 비교

### 옵션 A: 루트 중심 구조 (권장) ⭐

```
slea-ssem/
├── Dockerfile                          ← 단일 Dockerfile (BUILD_ENV arg로 구분)
├── docker-compose.yml                  ← 기본 (공개망)
├── docker-compose.internal.yml         ← 사내 override
├── .dockerignore
├── docker/
│   ├── .env.example                    ← 기본값 문서화
│   ├── .env.internal.example           ← 사내 기본값 문서화
│   └── certs/
```

**장점**:
- ✅ 표준 Docker 관례 준수 (루트에 Dockerfile, docker-compose.yml)
- ✅ 간결한 구조
- ✅ Makefile에서 cd docker 불필요
- ✅ 신규 팀원도 직관적으로 이해

**단점**:
- Dockerfile이 하나여서 BUILD_ENV arg 처리 필요

---

### 옵션 B: docker/ 디렉토리 중심 구조

```
slea-ssem/
└── docker/
    ├── Dockerfile                      ← 루트에서 복사/링크
    ├── docker-compose.yml              ← 기본
    ├── docker-compose.internal.yml     ← 사내 override
    ├── .env.example
    ├── .env.internal.example
    └── certs/
```

**장점**:
- ✅ 모든 Docker 관련 파일이 한 곳에 집중

**단점**:
- ❌ 표준 Docker 관례 위반
- ❌ Docker 도구들(IDE, CLI)이 docker/ 디렉토리의 Dockerfile 감지 못함

---

### 옵션 C: docker/build/ 계층화 구조

```
slea-ssem/
├── Dockerfile
└── docker/
    ├── build/
    │   ├── Dockerfile.internal         ← 사내 전용 Dockerfile
    │   └── .dockerignore
    ├── docker-compose.yml              ← 기본
    ├── docker-compose.internal.yml     ← 사내 override
    ├── .env.example
    └── .env.internal.example
```

**장점**:
- ✅ Dockerfile을 명확히 분리
- ✅ 환경별 설정 명확

**단점**:
- ❌ 복잡도 증가
- ❌ Makefile에서 context 경로 더 복잡

---

## 🏗️ 권장 안: 옵션 A 상세 계획

### Phase 1: 파일 정리 (영향 최소)

**1-1. 임시 파일 정리**
- `tmp/Dockerfile-internal` 제거 (사용 안 함)
- 목적: 혼동 제거

**1-2. 루트 docker-compose.yml 정리**
```bash
# 현재 루트의 docker-compose.yml은 사용되지 않음
# 확인 후 제거 또는 보관
```
- 목적: 중복 제거, 혼동 방지

**1-3. Dockerfile → 루트로 통합 (이미 루트에 있음)**
- 현재: 루트에 이미 있음 ✓
- 추가 작업: 없음

---

### Phase 2: docker-compose 파일 정리

**2-1. 루트로 이동/복사**
```bash
# docker/docker-compose.yml → 루트 (기본)
# docker/docker-compose.internal.yml → 루트 (사내)
```

**2-2. 파일 구조**
```
slea-ssem/
├── docker-compose.yml                 (기본 = 현재 docker/.env 사용)
├── docker-compose.internal.yml        (사내 = 현재 docker/.env.internal 사용)
└── docker/
    ├── .env.example
    ├── .env.internal.example
    └── certs/
```

**2-3. Makefile 단순화**
```makefile
# 수정 전: cd $(DOCKER_DIR) 필수
ENV_FILE=$(ENV_FILE) $(DC) $(COMPOSE_FILES) build

# 수정 후: 루트 디렉토리에서 실행 가능
$(DC) --env-file docker/$(ENV_FILE) $(COMPOSE_FILES) build
```

---

### Phase 3: 환경 설정 표준화

**3-1. .env 파일 정위치**
```
docker/
├── .env.example        ← 외부(공개망) 기본값
├── .env.internal.example  ← 사내(폐쇄망) 기본값
└── .env               ← make init으로 생성
└── .env.internal      ← make init-internal으로 생성
```

**3-2. Makefile 규칙**
```makefile
init:
    cp docker/.env.example docker/.env

init-internal:
    cp docker/.env.internal.example docker/.env.internal
```

---

### Phase 4: 문서화 & 검증

**4-1. 구조도 업데이트**
- README.md에 최상위 수준 다이어그램
- CLAUDE.md의 Quick Start 단순화

**4-2. 팀원 교육**
- 구조 설명 (5분)
- make help 확인
- 샘플 빌드 실행

---

## 📋 작업 체크리스트

### Phase 1: 파일 정리 (실행 쉬움)
- [ ] `tmp/Dockerfile-internal` 제거
- [ ] 루트의 사용 안 하는 `docker-compose.yml` 제거 또는 보관
- [ ] git commit: "chore: Clean up unused Docker files"

### Phase 2: docker-compose 통합
- [ ] `docker/docker-compose.yml` → 루트 (또는 심볼릭 링크)
- [ ] `docker/docker-compose.internal.yml` → 루트 (또는 심볼릭 링크)
- [ ] Makefile에서 `cd docker` 제거
- [ ] Makefile의 COMPOSE_FILES 경로 수정
- [ ] git commit: "refactor: Move docker-compose files to root"

### Phase 3: 환경 설정 정규화
- [ ] `.env` 생성 규칙 Makefile에서 확인
- [ ] `.env.internal` 생성 규칙 Makefile에서 확인
- [ ] 문서화: docker/ 디렉토리 README
- [ ] git commit: "docs: Add docker/ directory structure guide"

### Phase 4: Makefile 단순화
- [ ] Makefile의 모든 docker compose 호출 루트에서 실행하도록 수정
- [ ] --env-file 경로 일관성 확인
- [ ] help 섹션 업데이트
- [ ] git commit: "refactor: Simplify Makefile Docker commands"

### Phase 5: 검증
- [ ] 외부 PC: `make init && make build && make up` 성공
- [ ] 사내 PC: `make init-internal && make build-internal && make up-internal` 성공
- [ ] `make help` 실행해서 명확한지 확인
- [ ] 신규 팀원 테스트 (온보딩)

### Phase 6: 최종 정리
- [ ] 불필요한 docker/ subdirectory 제거 (docker-compose 이동 후)
- [ ] git commit: "chore: Final Docker structure cleanup"

---

## 🎓 신규 팀원 체크리스트

리팩토링 후 신규 팀원이 이해할 수 있는 수준인지 검증:

```
[ ] make help 명령어만으로 외부/사내 구분 가능한가?
[ ] Dockerfile이 루트에 있는 것이 자연스러운가?
[ ] docker-compose.yml 여러 개의 이유가 명확한가?
[ ] .env vs .env.internal 차이가 5초 안에 이해되는가?
[ ] 실수로 외부 PC에서 make build-internal 하려고 할 때 경고가 충분한가?
```

---

## 🚨 주의사항

### 실제 구현 시 고려사항

1. **심볼릭 링크 vs 파일 복사**
   - 심볼릭 링크: 한 곳만 수정 (더 나음)
   - 파일 복사: git 추적 가능

2. **하위호환성**
   - 현재 `make build` 시 `docker/` 참조하고 있음
   - 변경 후에도 동작해야 함

3. **git .gitignore**
   - `.env` / `.env.internal` 파일은 git에 추적 안 함 (이미 설정)
   - `docker/.env*` 확인

4. **CI/CD 영향**
   - GitHub Actions 등에서 경로 확인 필요
   - Dockerfile context 경로 확인

---

## 💬 토론 포인트

1. **옵션 A vs B vs C**: 어떤 구조가 팀에 가장 직관적인가?

2. **단계별 진행 vs 한번에**:
   - 한 번에 하면 빨르지만 위험
   - 단계별이 안전하지만 시간 걸림
   - → 추천: Phase 1-2를 먼저, 검증 후 Phase 3-4

3. **동료 피드백**:
   - 복잡하다고 느끼는 특정 부분이 있는가?
   - 실제 실수는 어디서 발생했는가? (외부/사내 선택, 파일 위치 등)

4. **우선순위**:
   - 즉시 해야 할 것 (파일 정리) vs 나중에 해도 되는 것 (구조 개선)

---

## 📌 최종 목표

```
리팩토링 후의 이상적 상태:

✓ 누구든 README.md 없이도 구조 이해 가능
✓ make help만으로 외부/사내 환경 선택 가능
✓ 파일 위치가 Docker 표준 관례를 따름
✓ 환경 추가 시 기존 코드 수정 최소화
✓ 실수 방지 (경고, 문서화)
```
