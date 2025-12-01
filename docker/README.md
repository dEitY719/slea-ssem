# SLEA-SSEM Docker 표준 템플릿

**외부(집/공개망) + 사내(회사/폐쇄망)** 환경을 하나의 Dockerfile로 관리하는 표준 템플릿입니다.

## 🎯 핵심 설계 원칙 (SOLID)

1. **Single Responsibility**: Dockerfile은 앱 빌드만, 환경 설정은 .env로 분리
2. **Open/Closed**: 환경 추가 시 Dockerfile 수정 없이 .env + override만 추가
3. **Dependency Inversion**: 구체적 URL/IP가 아닌 ARG/ENV 추상화에 의존

## 📁 디렉토리 구조

```
docker/
├── Dockerfile                    # 단일 통합 Dockerfile
├── docker-compose.yml            # Base compose
├── docker-compose.internal.yml   # 사내 override (선택적)
├── .env.example                  # 외부 환경 예시
├── .env.internal.example         # 사내 환경 예시
├── certs/                        # 인증서 폴더
│   ├── README.md
│   ├── .gitkeep
│   └── internal/                 # 사내 전용 (gitignore)
│       └── *.crt
└── README.md                     # 이 파일
```

---

## 🚀 빠른 시작

### 외부 환경 (집/공개망)

```bash
cd docker

# 1. 환경 설정
cp .env.example .env

# 2. 빌드 & 실행
docker-compose up --build

# 3. 확인
curl http://localhost:8000/health
```

### 사내 환경 (회사/폐쇄망)

```bash
cd docker

# 1. 환경 설정
cp .env.internal.example .env

# 2. 인증서 복사 (최초 1회)
mkdir -p certs/internal
cp ~/path/to/certs/*.crt certs/internal/

# 3. 빌드 & 실행 (override 사용)
docker-compose -f docker-compose.yml -f docker-compose.internal.yml up --build

# 4. 확인
curl http://localhost:8000/health
```

---

## 🔧 자주 사용하는 명령어

### 개발 모드 (코드 변경 자동 반영)

```bash
# 외부
docker-compose up

# 사내
docker-compose -f docker-compose.yml -f docker-compose.internal.yml up
```

### 프로덕션 빌드

```bash
# 외부
docker-compose up --build -d

# 사내
docker-compose -f docker-compose.yml -f docker-compose.internal.yml up --build -d
```

### 서비스 중단

```bash
# 외부
docker-compose down

# 사내
docker-compose -f docker-compose.yml -f docker-compose.internal.yml down
```

### 로그 확인

```bash
# 전체 로그
docker-compose logs -f

# Backend만
docker-compose logs -f slea-backend

# DB만
docker-compose logs -f slea-db
```

### 컨테이너 진입

```bash
# Backend
docker exec -it slea-backend sh

# DB
docker exec -it slea-db psql -U himena -d sleassem_dev
```

---

## 🌍 다른 환경 추가하기

새로운 환경(예: 클라우드, 다른 회사망) 추가 시:

```bash
# 1. .env 파일 생성
cp .env.example .env.cloud

# 2. 필요 시 override 파일 생성
cat > docker-compose.cloud.yml <<EOF
version: '3.9'
services:
  slea-backend:
    build:
      args:
        HTTP_PROXY: http://cloud-proxy:3128
        PIP_INDEX_URL: https://cloud-pypi-mirror/simple
EOF

# 3. 실행
docker-compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.cloud up
```

**Dockerfile 수정 없음** ✅

---

## 🐛 트러블슈팅

### 1. 인증서 오류 (사내 환경)

**증상**: `SSL: CERTIFICATE_VERIFY_FAILED`

**해결**:
```bash
# 인증서 파일 확인
ls -la docker/certs/internal/

# 없으면 복사
cp ~/path/to/*.crt docker/certs/internal/

# 재빌드
docker-compose -f docker-compose.yml -f docker-compose.internal.yml up --build
```

### 2. 프록시 오류 (사내 환경)

**증상**: `Connection timeout`, `Could not resolve host`

**해결**:
```bash
# .env 파일의 프록시 설정 확인
grep PROXY docker/.env

# 올바른 값:
# HTTP_PROXY=http://12.26.204.100:8080
# HTTPS_PROXY=http://12.26.204.100:8080
```

### 3. Frontend 빌드 실패

**증상**: `npm ci` 실패

**해결**:
```bash
# Frontend 없이 빌드 (Backend만)
echo "BUILD_FRONTEND=false" >> docker/.env
docker-compose up --build
```

### 4. 포트 충돌

**증상**: `port is already allocated`

**해결**:
```bash
# .env 파일에서 포트 변경
echo "PORT=8100" >> docker/.env
echo "DB_PORT=5434" >> docker/.env

docker-compose up
```

---

## 📚 참고 자료

- [Docker Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker Compose Override](https://docs.docker.com/compose/extends/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

---

## 🤝 팀원과 공유하기

### 외부 동료 (공개 저장소)

```bash
# Git에 커밋
git add docker/
git commit -m "feat: Add Docker standard template (external + internal)"
git push
```

### 사내 동료 (폐쇄망)

1. **코드 공유**: Git으로 공유 (인증서 제외)
2. **인증서 공유**: 별도 채널 (사내 메일, Confluence 등)
3. **가이드 공유**: `docker/README.md` + `.env.internal.example`

**주의**: `docker/certs/internal/*.crt`는 Git에 포함되지 않음 (gitignore)
