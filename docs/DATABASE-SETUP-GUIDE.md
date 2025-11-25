# DATABASE_URL 설정 가이드

**중요**: `postgresql+asyncpg` vs `postgresql` 차이 이해하기

---

## 🔴 핵심: +asyncpg가 필수인 이유

### 현재 프로젝트 스택

```
FastAPI (비동기 웹프레임워크)
    ↓
SQLAlchemy 2.0 (비동기 ORM 지원)
    ↓
PostgreSQL 데이터베이스
```

### DATABASE_URL 비교

| 설정 | 드라이버 | 용도 | FastAPI와의 호환 |
|------|---------|------|-----------------|
| `postgresql+asyncpg://...` | Async | **권장** | ✅ 완벽 호환 |
| `postgresql://...` | Sync | ❌ 사용 금지 | 🔴 블로킹 발생 |

---

## ✅ 올바른 설정: postgresql+asyncpg

### What is asyncpg?

```python
# asyncpg = Async PostgreSQL driver for Python
# - Non-blocking I/O
# - Works with async/await
# - Fast and efficient

import asyncpg

async def fetch_user():
    conn = await asyncpg.connect('postgresql://localhost/db')
    user = await conn.fetchrow('SELECT * FROM users WHERE id = $1', 1)
    await conn.close()
```

### DATABASE_URL 형식

```
postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DBNAME
          ↑
      드라이버 명시
```

### 현재 프로젝트 설정 (정답)

```
DATABASE_URL=postgresql+asyncpg://himena:change_me_strong_pw@localhost:5432/sleassem_dev
                      ↑
        FastAPI + SQLAlchemy 2.0과 호환
```

---

## ❌ 잘못된 설정: postgresql (동기 드라이버)

### 문제점

```python
# ❌ 동기 드라이버 사용
DATABASE_URL = "postgresql://user:pw@localhost:5432/db"

# SQLAlchemy에서 동기 방식으로 DB 접근
with Session(engine) as session:
    user = session.query(User).first()  # 블로킹!
    # 이 동안 FastAPI는 다른 요청을 처리할 수 없음
```

### 결과

```
FastAPI 요청 1 (DB 쿼리 중)
    ↓
❌ 블로킹 (다른 요청 대기)
    ↓
FastAPI 요청 2, 3, 4, ... (모두 대기)
    ↓
성능 저하, 동시성 상실
```

---

## 🔧 설정 방식

### 현재 상황: 로컬 PostgreSQL 사용

```bash
# Windows WSL에 PostgreSQL 설치됨
# localhost에서 직접 접근 가능

# .env 설정
DATABASE_URL=postgresql+asyncpg://himena:change_me_strong_pw@localhost:5432/sleassem_dev
            ↑ 필수                                           ↑ 로컬
```

### 향후: Docker PostgreSQL 사용 (선택사항)

```bash
# Docker Compose에서 PostgreSQL 실행
# 컨테이너 이름으로 접근

# .env 설정
DATABASE_URL=postgresql+asyncpg://slea_user:password@db:5432/sleassem_dev
            ↑ 필수                                    ↑ Docker 서비스명
```

---

## 📋 .env.example 설정

### Option 1: 로컬 PostgreSQL (현재 - 권장)

```env
# WSL에 PostgreSQL 설치되어 있는 경우
DATABASE_URL=postgresql+asyncpg://himena:change_me_strong_pw@localhost:5432/sleassem_dev
TEST_DATABASE_URL=postgresql+asyncpg://himena:change_me_strong_pw@localhost:5432/sleassem_test
PROD_DATABASE_URL=postgresql+asyncpg://himena:change_me_strong_pw@localhost:5432/sleassem_prod

# 주의: 비밀번호는 .env에만 있고 git에는 커밋되지 않음
```

### Option 2: Docker PostgreSQL (향후)

```env
# docker-compose up 실행하는 경우
DATABASE_URL=postgresql+asyncpg://slea_user:change_me_dev_password@db:5432/sleassem_dev
TEST_DATABASE_URL=postgresql+asyncpg://slea_user:change_me_dev_password@db:5432/sleassem_test
PROD_DATABASE_URL=postgresql+asyncpg://slea_user:change_me_dev_password@db:5432/sleassem_prod

# docker-compose.yml의 서비스명 'db' 사용
```

---

## ⚠️ 마이그레이션 주의사항

### 로컬 → Docker로 전환할 때

```bash
# 기존: 로컬 PostgreSQL에서 데이터 백업
pg_dump -U himena -h localhost sleassem_dev > backup.sql

# 새로운: Docker PostgreSQL에 복원
# docker-compose up -d
# psql -U slea_user -h localhost -d sleassem_dev < backup.sql
```

---

## 🔍 DB 연결 테스트

### Python 코드에서 확인

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 현재 설정 확인
DATABASE_URL = "postgresql+asyncpg://himena:change_me_strong_pw@localhost:5432/sleassem_dev"

# 엔진 생성
engine = create_async_engine(DATABASE_URL, echo=True)

# 세션 팩토리
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 테스트
async def test_connection():
    async with async_session() as session:
        result = await session.execute("SELECT 1")
        print("✅ 연결 성공")
```

### CLI에서 확인

```bash
# psql로 직접 테스트
psql -U himena -h localhost -d sleassem_dev -c "SELECT version();"

# 또는 Python asyncpg 사용
python -c "
import asyncio
import asyncpg

async def test():
    conn = await asyncpg.connect('postgresql://himena:change_me_strong_pw@localhost:5432/sleassem_dev')
    result = await conn.fetchrow('SELECT 1')
    print('✅ asyncpg 연결 성공')
    await conn.close()

asyncio.run(test())
"
```

---

## 📊 설정 결정 가이드

### 당신은 어느 것을 사용하나요?

```
Q1: Windows WSL에서 PostgreSQL을 직접 설치했나요?
  ├─ YES → Option 1: 로컬 PostgreSQL (localhost)
  └─ NO  → Q2로

Q2: Docker를 사용해서 PostgreSQL을 실행하나요?
  ├─ YES → Option 2: Docker PostgreSQL (db)
  └─ NO  → PostgreSQL이 필요합니다 (설치 또는 원격 서버)
```

---

## ✅ 확인 체크리스트

### DATABASE_URL 설정 전

- [ ] `postgresql+asyncpg://` 로 시작하나? (필수!)
- [ ] 사용자명/비밀번호 맞나? (himena vs slea_user)
- [ ] 호스트 맞나? (localhost vs db)
- [ ] 포트 맞나? (보통 5432)
- [ ] 데이터베이스 이름 맞나? (sleassem_dev)

### 설정 후

- [ ] `.env`에만 있고 git에는 없나? (민감 정보)
- [ ] `.env.example`은 공개 템플릿이나? (비밀번호 없음)
- [ ] 연결 테스트 성공했나?
- [ ] FastAPI 서버 시작 성공?

---

## 🎯 결론

### 핵심 규칙

```
✅ 필수: postgresql+asyncpg (FastAPI 호환)
❌ 금지: postgresql (블로킹 발생)
```

### 선택지

```
1️⃣ 로컬 PostgreSQL (현재)
   → DATABASE_URL=postgresql+asyncpg://himena:change_me_strong_pw@localhost:5432/sleassem_dev

2️⃣ Docker PostgreSQL (향후)
   → DATABASE_URL=postgresql+asyncpg://slea_user:change_me_dev_password@db:5432/sleassem_dev

둘 다 +asyncpg 필수!
```

---

**작성**: 2025-11-25
**중요도**: 🔴 매우 높음
**검토 필요**: 팀의 DB 설정 방식 확인
