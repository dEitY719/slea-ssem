# Postmortem: Docker Compose 환경 변수 우선순위 문제

**작성일**: 2025-12-04
**문제 발견**: 사내 PC 빌드 후 LITELLM_API_KEY 값이 예상과 다르게 로드됨
**해결 소요 시간**: ~3시간 (원인 분석 + 디버깅 + 수정)

---

## 📊 요약

**문제**: 사내 PC에서 docker/.env.internal의 올바른 값이 무시되고, docker/.env의 이전 값이 사용됨

**근본 원인**: Docker Compose의 환경 변수 우선순위 메커니즘 오해
- docker-compose.yml/internal.yml의 **environment 섹션이 env_file을 덮어씀**

**해결책**: LLM 설정 변수를 environment 섹션에서 제거하고 env_file만 사용

**영향도**: 높음 (사내 PC 개발 환경 전체)

---

## 🔴 문제의 증상

```
# 예상
컨테이너: LITELLM_API_KEY=5d355aa68444f42fb545bd0ceac3bcc859f3cca5 ✓

# 실제
컨테이너: LITELLM_API_KEY=sk-4444 ❌
```

### 상황
- docker/.env.internal: `LITELLM_API_KEY=5d355aa...` (올바른 값)
- 루트 .env: `LITELLM_API_KEY=5d355aa...` (올바른 값)
- 컨테이너 로드: `LITELLM_API_KEY=sk-4444` (어디서 온 값?)
- `make clean; make build-internal; make up-internal` 모두 실행했는데도 미해결

---

## 🔍 디버깅 과정

### 1단계: 초기 분석 (틀린 방향)

**가설**: 루트 .env 파일이 Docker Compose 자동 로드로 인해 우선되는 것?

```bash
$ ls -la .env                    # 루트에 .env 있음
$ cat docker/.env.internal       # 올바른 값 있음
```

**결론**: 루트 .env 파일이 문제인 것 같음... (틀림)

---

### 2단계: Makefile 경로 확인 (틀린 방향)

**가설**: `--env-file` 플래그 경로가 잘못됨?

```bash
$ grep "env-file" Makefile       # 경로 확인
```

**결론**: Makefile의 `--env-file $(ENV_FILE)` 경로는 정상... (틀림)

---

### 3단계: 동료 피드백으로 올바른 원인 발견 ⭐

**동료의 분석**:
> docker-compose.internal.yml의 environment 섹션에서 `LITELLM_API_KEY=${LITELLM_API_KEY}`로 치환됩니다.
> 이 치환은 .env.internal이 아니라 **compose가 기본으로 읽는 docker/.env(또는 쉘 환경) 값**을 씁니다.
> Docker Compose 우선순위: **쉘/.env > environment > env_file**

**검증**:
```bash
$ docker compose config | grep LITELLM_API_KEY
LITELLM_API_KEY: sk-4444   # ← environment 섹션의 기본값이 우선됨
```

---

## 🎯 근본 원인

### Docker Compose 환경 변수 로드 순서

```
1. 호스트 환경 변수 (HIGHEST)
2. docker/.env 파일 (자동 로드)
3. --env-file 플래그 (-env.internal)
4. docker-compose 파일의 environment 섹션 (변수 치환)
5. docker-compose 파일의 env_file 섹션 (LOWEST)
```

### 문제의 정확한 메커니즘

```yaml
# docker-compose.yml/internal.yml
environment:
  - LITELLM_API_KEY=${LITELLM_API_KEY:-sk-test}
  #                  ↑ 이 변수를 찾을 때:
  #                  1. docker/.env에서 찾음 (sk-4444) ← 이것이 우선됨!
  #                  2. env_file은 이미 늦음 (우선순위 낮음)
env_file:
  - .env.internal  # ← 이 값은 무시됨
```

### 왜 이런 일이 발생했나?

**설계 의도**:
- environment 섹션에 기본값을 넣어서 env_file이 없을 때 대비
- `LITELLM_API_KEY=${LITELLM_API_KEY:-sk-test}` ← 유연한 설정

**예상치 못한 동작**:
- docker/.env가 있으면, 그것이 변수 치환의 소스가 됨
- env_file의 값이 우선되지 않음 (우선순위가 낮음)

---

## ✅ 해결책

### 구현한 해결책: environment 섹션 제거

**docker/docker-compose.yml**:
```yaml
# 수정 전
environment:
  - LITELLM_API_KEY=${LITELLM_API_KEY:-sk-test}
  - LITELLM_BASE_URL=${LITELLM_BASE_URL:-http://...}
  - LITELLM_MODEL=${LITELLM_MODEL:-gpt-4}
  - GEMINI_API_KEY=${GEMINI_API_KEY:-}
env_file:
  - ${ENV_FILE:-.env}

# 수정 후
environment:
  # LLM variables removed - use env_file only
env_file:
  - ${ENV_FILE:-.env}
```

**동일하게 docker-compose.internal.yml도 수정**

### 왜 이 방법이 최고?

| 방법 | 장점 | 단점 |
|------|------|------|
| **env_file만 사용** ⭐ | 명확함, 외부/내부 분리 간단 | 기본값 없음 |
| docker/.env 동기화 | 작은 수정 | 외부/내부 구분 어려움 |
| 환경 변수 export | 임시 해결 가능 | 재현성 낮음 |

---

## 📚 결과

### 검증 (사내 PC)

```bash
$ git pull origin main
$ make clean
$ make build-internal
$ make up-internal
$ docker exec slea-backend env | grep LITELLM_API_KEY
LITELLM_API_KEY=5d355aa68444f42fb545bd0ceac3bcc859f3cca5  ✅ 올바른 값!
```

### 변경된 파일

```
docker/docker-compose.yml              (LLM vars removed from environment)
docker/docker-compose.internal.yml     (LLM vars removed from environment)
```

### Git Commit

```
83806a6 fix: Remove LLM variables from environment section, use env_file only
```

---

## 🎓 교훈 및 예방

### 이번 문제의 근본 원인

1. **Docker Compose 우선순위 오해**
   - environment 섹션이 env_file을 덮어쓴다는 것을 모름
   - 설정이 여러 곳에 분산되어 있음

2. **구조적 문제**
   - docker/.env와 docker/.env.internal이 공존
   - LLM 설정이 여러 곳에서 정의됨
   - 어디가 "진실의 원천(source of truth)"인지 불명확

3. **디버깅 어려움**
   - `docker compose config`로 최종 결과 확인할 때까지 원인 파악 어려움
   - 로그에서 직접 보이지 않음 (environment 섹션이 env_file 뒤에 평가됨)

### 예방 방법

#### 즉시 (지금)
- ✅ **이미 적용됨**: env_file만 사용 (environment 섹션에서 제거)
- ✅ **구조 명확화**: 외부/내부 설정 파일 분리

#### 리팩토링 단계에서
- [ ] docker/.env와 docker/.env.internal을 완전히 분리
- [ ] 루트 .env와 docker/ .env의 충돌 제거
- [ ] 환경 변수 로드 순서를 명확하게 문서화

#### 팀 관례
```markdown
## Docker Compose 환경 변수 규칙

1. **env_file에만 정의**: 모든 환경별 설정은 .env.internal / .env.example에만
2. **environment 섹션**: 고정값(PORT, HOST 등)만, 변수는 불사용
3. **기본값 제공**: docker-compose 파일에서 기본값을 주지 말 것
   - 대신 .env.example에 명확한 예시 제공
```

---

## 🚨 비슷한 패턴의 다른 문제들

현재 코드베이스에서 발견된 유사한 구조적 문제:

1. **파일 위치 분산**: 루트 vs docker/ 혼재
2. **설정 중복**: docker-compose.yml과 docker-compose.internal.yml이 유사
3. **우선순위 불명확**: 어떤 파일이 로드되는지 불분명

→ **이것이 Docker 리팩토링의 핵심 이유**

---

## 🔗 참고 자료

- Docker Compose 문서: https://docs.docker.com/compose/environment-variables/
- 우선순위 규칙: Shell env > .env > env_file

**생성된 리팩토링 계획**:
- `docs/DOCKER-REFACTORING-PLAN.md`
- `docs/DOCKER-STRUCTURE-COMPARISON.md`
- `docs/DOCKER-DECISION-GUIDE.md`

---

## 💬 최종 의견

이 문제는 **설계 단계에서 비용을 아끼려다가 생긴 전형적인 예시**입니다.

- **즉흥적 확장**: environment 섹션에 변수 추가 (쉬워 보였음)
- **예상치 못한 부작용**: Docker Compose 우선순위로 인한 동작 불일치
- **장기 비용**: 3시간 디버깅 + 팀 혼동

**리팩토링이 필수인 이유:**
구조를 명확하게 하면, 이런 식의 실수가 원천 차단됩니다.
