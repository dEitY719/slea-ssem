# PostgreSQL Local Development Setup Guide

**목차:**
- [빠른 시작](#빠른-시작)
- [수동 설정](#수동-설정)
- [문제 해결](#문제-해결)
- [pg_hba.conf 설정](#pg_hbaconf-설정)

---

## 빠른 시작

### 자동 스크립트 사용 (권장)

```bash
# 기본값으로 실행 (slea_user, change_me_dev_password, sleassem_*)
bash scripts/setup-postgresql.sh

# 커스텀 설정
bash scripts/setup-postgresql.sh my_user my_password my_db
```

**스크립트가 수행하는 작업:**
1. PostgreSQL 서비스 확인/시작
2. 데이터베이스 사용자 생성
3. 3개 데이터베이스 생성 (_dev, _test, _prod)
4. 권한 설정
5. 연결 테스트

---

## 수동 설정

### Step 1: PostgreSQL 서비스 확인

```bash
# 상태 확인
sudo systemctl status postgresql

# 시작
sudo systemctl start postgresql
```

### Step 2: pg_hba.conf 설정 (최초 1회만)

PostgreSQL의 기본 인증 방식이 peer인 경우, ident로 변경:

```bash
# ident 방식으로 변경 (비밀번호 불필요)
sudo sed -i 's/^local.*all.*peer/local   all             all                                     ident/' /etc/postgresql/16/main/pg_hba.conf

# 변경 확인
sudo grep "^local" /etc/postgresql/16/main/pg_hba.conf

# 재시작
sudo systemctl restart postgresql
```

### Step 3: 사용자 및 데이터베이스 생성

```bash
# 한 번에 실행
sudo -u postgres psql << 'EOF'
-- 사용자 생성
CREATE USER slea_user WITH PASSWORD 'change_me_dev_password';

-- 데이터베이스 생성
CREATE DATABASE sleassem_dev;
CREATE DATABASE sleassem_test;
CREATE DATABASE sleassem_prod;

-- 소유권 변경
ALTER DATABASE sleassem_dev OWNER TO slea_user;
ALTER DATABASE sleassem_test OWNER TO slea_user;
ALTER DATABASE sleassem_prod OWNER TO slea_user;

-- 권한 설정
GRANT ALL PRIVILEGES ON DATABASE sleassem_dev TO slea_user;
GRANT ALL PRIVILEGES ON DATABASE sleassem_test TO slea_user;
GRANT ALL PRIVILEGES ON DATABASE sleassem_prod TO slea_user;
EOF
```

### Step 4: 확인

```bash
# 모든 데이터베이스 확인
sudo -u postgres psql -c "\l" | grep sleassem

# 사용자로 접속 테스트
psql -U slea_user -d sleassem_dev -h localhost -c "SELECT 1;"
# password: change_me_dev_password
```

---

## 문제 해결

### 문제 1: "role 'username' does not exist"

**원인:** PostgreSQL 사용자가 없음

**해결책:**
```bash
# 사용자 생성
sudo -u postgres createuser -P slea_user
# 프롬프트에서 비밀번호 입력

# 또는 스크립트 사용
bash scripts/setup-postgresql.sh
```

---

### 문제 2: "database 'username' does not exist"

**원인:** peer 인증에서 현재 사용자명의 DB를 찾으려고 함

**해결책:**
```bash
# 방법 1: pg_hba.conf를 ident로 변경 (권장)
sudo sed -i 's/peer/ident/' /etc/postgresql/16/main/pg_hba.conf
sudo systemctl restart postgresql

# 방법 2: 데이터베이스 명시
psql -d postgres -c "SELECT version();"

# 방법 3: 사용자 명시
psql -U postgres -d postgres -c "SELECT version();"
```

---

### 문제 3: "password authentication failed"

**원인:** pg_hba.conf가 md5인데 비밀번호가 없음

**해결책:**
```bash
# pg_hba.conf를 ident로 변경
sudo sed -i 's/^local.*all.*md5/local   all             all                                     ident/' /etc/postgresql/16/main/pg_hba.conf
sudo systemctl restart postgresql

# 이제 sudo -u postgres로 접속 가능
sudo -u postgres psql -c "SELECT version();"
```

---

### 문제 4: "Peer authentication failed for user 'postgres'"

**원인:** postgres 사용자도 peer 또는 md5 인증 중

**해결책:**
```bash
# pg_hba.conf의 postgres 라인을 ident로 변경
sudo sed -i '0,/^local.*postgres.*\(peer\|md5\)/s/\(peer\|md5\)/ident/' /etc/postgresql/16/main/pg_hba.conf

# 재시작
sudo systemctl restart postgresql

# 이제 작동
sudo -u postgres psql -c "SELECT version();"
```

---

## pg_hba.conf 설정

### 인증 방식 이해

| 방식 | 특징 | 사용 경우 |
|------|------|---------|
| **peer** | 시스템 사용자 = DB 사용자 (비밀번호 불필요) | 로컬 개발 (권장) |
| **ident** | TCP 연결도 시스템 사용자 기반 (비밀번호 불필요) | 로컬 개발 + 원격 접속 |
| **md5** | 비밀번호 인증 (legacy, deprecated) | 피할 것 |
| **scram-sha-256** | 비밀번호 인증 (현대적, 안전) | 프로덕션 |

### 현재 설정 확인

```bash
# WSL/Linux 로컬 연결
sudo grep "^local" /etc/postgresql/16/main/pg_hba.conf

# TCP 원격 연결
sudo grep "^host" /etc/postgresql/16/main/pg_hba.conf
```

### 권장 설정 (로컬 개발)

```bash
# /etc/postgresql/16/main/pg_hba.conf

# "local" is for Unix domain socket connections only
local   all             all                                     ident

# IPv4 local connections:
host    all             all             127.0.0.1/32            ident

# IPv6 local connections:
host    all             all             ::1/128                 ident

# Replication
local   replication     all                                     ident
host    replication     all             127.0.0.1/32            ident
host    replication     all             ::1/128                 ident
```

---

## 자주 사용하는 명령어

### 사용자 관리

```bash
# 사용자 생성
sudo -u postgres createuser -P slea_user

# 사용자 목록
sudo -u postgres psql -c "\du"

# 사용자 삭제
sudo -u postgres dropuser slea_user

# 비밀번호 변경
sudo -u postgres psql -c "ALTER USER slea_user WITH PASSWORD 'new_password';"

# Superuser 권한 부여
sudo -u postgres psql -c "ALTER USER slea_user WITH SUPERUSER;"
```

### 데이터베이스 관리

```bash
# 데이터베이스 생성
sudo -u postgres createdb -O slea_user sleassem_dev

# 데이터베이스 목록
sudo -u postgres psql -c "\l"

# 데이터베이스 삭제
sudo -u postgres dropdb sleassem_dev

# 소유자 변경
sudo -u postgres psql -c "ALTER DATABASE sleassem_dev OWNER TO slea_user;"

# 권한 부여
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE sleassem_dev TO slea_user;"
```

### 연결 테스트

```bash
# 비밀번호로 접속
PGPASSWORD='change_me_dev_password' psql -U slea_user -d sleassem_dev -h localhost -c "SELECT 1;"

# 환경변수 사용
export PGPASSWORD='change_me_dev_password'
psql -U slea_user -d sleassem_dev -h localhost

# .env 파일 사용 (.env에 DATABASE_URL 정의)
source .env
psql $DATABASE_URL -c "SELECT 1;"
```

---

## 참고 문서

- **Postmortem**: `docs/postmortem-docker-database-config-mismatch.md`
  - WSL PostgreSQL vs Docker 설정 차이
  - 디버깅 과정 및 해결책

- **.env.example**: `.env.example`
  - 로컬 개발 환경변수 템플릿

- **Dockerfile**: `Dockerfile`
  - Docker PostgreSQL 설정 (참고용)

---

## 팀 온보딩 체크리스트

신규 팀원이 로컬 개발 환경을 설정할 때:

- [ ] WSL PostgreSQL 설치 확인
- [ ] `bash scripts/setup-postgresql.sh` 실행
- [ ] `.env` 파일 확인 (DATABASE_URL 일치)
- [ ] `psql -U slea_user -d sleassem_dev -c "SELECT 1;"` 테스트
- [ ] `./tools/dev.sh up` 로컬 개발 서버 시작
- [ ] `docker-compose up` Docker 검증 (선택사항)

---

## 정리

**이 가이드의 핵심:**
1. **pg_hba.conf를 ident로 설정** → 비밀번호 불필요, 로컬 개발 최적
2. **`bash scripts/setup-postgresql.sh` 사용** → 모든 단계 자동화
3. **`.env` 파일과 docker-compose.yml 일관성 유지** → 설정 혼동 방지
4. **문제 발생 시 이 문서 참고** → 빠른 해결

**다음 번에 새로운 프로젝트:**
- 이 가이드와 스크립트를 템플릿으로 재사용
- PostgreSQL 설정 관련 시간 ~10분으로 단축 가능 ✅
