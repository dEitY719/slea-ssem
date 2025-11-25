# Git Patch 방식: 사내 수정 사항을 사외로 안전하게 공유

**상황**: 사내 보안 정책상 사내망 → 사외 GitHub로 직접 push 불가
**해결책**: Git `format-patch` 및 `am` 명령어를 사용한 안전한 코드 공유

---

## 📋 문제 상황

### 일반적인 시나리오

```
사내 개발
    ↓
버그 발견 또는 기능 추가
    ↓
❌ git push origin feature  (보안 정책 위반)
    ↓
"코드를 사외에 공유하려면?"
```

### 단순 파일 복사의 문제

```bash
# ❌ 나쁜 예: 파일만 복사
1. 파일 복사/붙여넣기
2. 수동으로 다시 수정
3. 커밋 히스토리 누락
4. TDD 테스트 코드 누락
5. 리팩토링 과정 누락
```

---

## ✅ 해결책: Git Patch 방식

### 핵심 원칙

```
사내에서 수정한 커밋
    ↓
Patch 파일로 생성 (git format-patch)
    ↓
회사 보안 절차를 통해 반출
(메일 승인, 파일 전송 시스템 등)
    ↓
사외에서 Patch 적용 (git am)
    ↓
✅ 커밋 히스토리, 메타데이터 모두 보존
```

---

## 🔧 단계별 가이드

### Step 1: 사내에서 Patch 파일 생성

#### A. 최근 1개 커밋 패치 생성

```bash
# 현재 HEAD 커밋을 패치 파일로 생성
git format-patch -1 HEAD

# 결과:
# 0001-commit-message.patch 파일 생성됨
```

#### B. 여러 커밋을 하나의 패치로 생성

```bash
# 최근 3개 커밋을 패치로 생성
git format-patch -3 HEAD

# 결과:
# 0001-first-commit.patch
# 0002-second-commit.patch
# 0003-third-commit.patch
```

#### C. 특정 범위의 커밋 생성

```bash
# upstream/develop 이후로 추가된 모든 커밋
git format-patch upstream/develop

# 또는 특정 커밋 범위
git format-patch abc1234..HEAD
```

#### D. Patch 파일 내용 확인

```bash
# 생성된 패치 파일 내용 확인
cat 0001-fix-bug.patch

# 예상 형식:
# From: Developer Name <email@example.com>
# Date: Mon Nov 25 10:00:00 2025 +0900
# Subject: [PATCH] fix: bug in user authentication
#
# This commit fixes the authentication bug...
# ---
#  src/auth/login.py | 5 +++++
#  tests/auth/test_login.py | 10 ++++++++
#  2 files changed, 15 insertions(+)
# ...
```

---

### Step 2: 회사 보안 절차를 통해 반출

#### 허용 방식 (회사 정책 확인 필수)

```
1️⃣ 메일로 첨부 (보안팀 승인 후)
2️⃣ 파일 전송 시스템 (예: 회사 Dropbox/OneDrive)
3️⃣ 암호화된 USB (인수인계)
4️⃣ 내부 Wiki에 paste (사람들 통해)
```

#### 주의사항

```
❌ 절대 하면 안 되는 것:
- 사내망 VPN/Proxy를 통한 GitHub에 직접 push
- 보안팀 승인 없이 외부로 데이터 반출
- 민감한 정보(암호, API key)가 포함된 패치

✅ 패치에 포함 가능한 것:
- 비즈니스 로직 개선
- 버그 수정
- 테스트 코드
- 문서
```

---

### Step 3: 사외에서 Patch 적용

#### A. Patch 파일 수신 후 확인

```bash
# 패치 파일 내용 확인 (안전성 검사)
cat 0001-fix-bug.patch

# 또는 Patch 적용 전 Dry-run 실행
git apply --check 0001-fix-bug.patch
# 충돌이 없으면 성공, 있으면 오류 표시
```

#### B. Patch 적용 (git am)

```bash
# 단일 패치 적용
git am < 0001-fix-bug.patch

# 또는 여러 패치 한 번에 적용
git am *.patch

# 결과:
# Applying: fix: bug in user authentication
# ✅ 커밋이 그대로 재생됨
```

#### C. 충돌 발생 시 처리

```bash
# 충돌이 발생했다면
# 1. 파일 확인
git status

# 2. 파일 편집하여 충돌 해결
nano src/auth/login.py

# 3. 해결 완료 후
git add .
git am --continue

# 또는 포기하고 다시 시작
git am --abort
```

---

## 📚 실제 예시

### 시나리오: 회사에서 버그를 발견하고 사외에 공유

#### 사내 (회사 GitLab)

```bash
# 1. 버그 수정
git checkout -b fix/auth-bug origin/develop

# ... 코드 수정 및 테스트 ...

# 2. 커밋
git add src/auth/login.py tests/auth/test_login.py
git commit -m "fix: authentication bug in login flow

Fixes issue where users with special characters in password
couldn't log in."

# 3. Patch 생성
git format-patch -1 HEAD
# 결과: 0001-fix-authentication-bug-in-login-flow.patch

# 4. 패치 파일 확인
cat 0001-fix-authentication-bug-in-login-flow.patch
```

#### 회사 보안 절차

```
1. 팀 리드에게 보고
2. 보안팀에 승인 요청
3. Patch 파일을 메일로 전송
   (또는 안전한 채널)
```

#### 사외 (GitHub)

```bash
# 1. 패치 파일 수신
# 메일 또는 파일 시스템에서 0001-fix-authentication-bug-in-login-flow.patch 받음

# 2. 패치 적용 전 확인
git apply --check 0001-fix-authentication-bug-in-login-flow.patch
# 오류 없으면 OK

# 3. Patch 적용
git am < 0001-fix-authentication-bug-in-login-flow.patch

# 4. 결과 확인
git log -1
# Author: 개인명 <email>
# Date:   Mon Nov 25 10:00:00 2025 +0900
#
# fix: authentication bug in login flow

git show
# 변경 사항 전체 표시 (테스트 코드까지!)

# 5. Push
git push origin develop
```

---

## 🔄 일반적인 워크플로우 (권장)

### 권장: Outside-In 전략 + Patch

```
메인 개발: 사외 GitHub
    ↓
기능 완성 및 PR 승인
    ↓
마스터 브랜치에 병합
    ↓
    ⬇️ (주 1회 또는 필요시)
    ⬇️
사내 GitHub
    ↓
git pull upstream develop
    (사외의 최신 코드 자동 가져옴)

불가피한 경우:
    ↓
사내에서 Hotfix 필요
    ↓
Patch 파일 생성
    ↓
사외에 전달 (보안 절차)
    ↓
사외에서 Patch 적용
    ↓
다음 날 사내에서 Pull
```

---

## ⚠️ 주의사항

### 1. 메타데이터 보존

```bash
# ✅ Patch에는 다음 정보가 포함됨
- 커밋 해시
- 커밋자 (Author)
- 날짜
- 커밋 메시지
- 변경된 파일 목록
- Diff (정확한 변경사항)

# ✅ 테스트 코드도 그대로 포함됨
# ✅ 리팩토링 과정도 재현됨
```

### 2. 충돌 최소화

```bash
# Patch를 최신 코드에 적용하려면
# 1. Upstream을 최신으로 유지
git fetch upstream develop

# 2. 현재 브랜치를 업데이트
git rebase upstream/develop

# 3. 그 다음 Patch 적용
git am < patch-file.patch
```

### 3. 민감한 정보 제외

```bash
# ❌ 패치에 포함되면 안 되는 것
- API 키, 토큰
- 데이터베이스 비밀번호
- 회사 내부 설정값
- 개인정보

# 확인 방법
cat 0001-patch.patch | grep -i "password\|secret\|key"
# 아무것도 안 나와야 안전함
```

---

## 🛠️ 고급 사용법

### Patch를 파일이 아닌 스트림으로 전송

```bash
# 사내에서
git format-patch -1 HEAD -o - | mail -s "Patch for review" external@email.com

# 사외에서 메일의 attachment로 받으면
git am patch-file.patch
```

### 여러 패치를 합치기

```bash
# 3개의 패치를 1개로 만들기
git am 0001-*.patch
git reset --soft HEAD~3
git commit -m "combined fix: multiple improvements"
git format-patch -1 HEAD
```

### 특정 커밋만 Cherry-pick

```bash
# 모든 커밋이 아닌 특정 것만
git format-patch -1 <commit-sha>
```

---

## ✅ 체크리스트

### Patch 생성 전

- [ ] 최신 코드 기반 (git pull upstream develop)
- [ ] 테스트 통과 (make quality)
- [ ] 민감 정보 없음 (grep password/secret)
- [ ] 커밋 메시지 명확함

### Patch 적용 전

- [ ] 패치 내용 확인 (cat *.patch)
- [ ] 충돌 여부 확인 (git apply --check)
- [ ] 최신 코드 기반 (git fetch + rebase)

### Patch 적용 후

- [ ] 코드 검증 (git show)
- [ ] 테스트 실행 (make test)
- [ ] 히스토리 확인 (git log)

---

## 📊 비교: Patch vs 다른 방법

| 방법 | 히스토리 | 테스트 | 메타데이터 | 안전성 |
|------|---------|--------|-----------|--------|
| **Patch** | ✅ 보존 | ✅ 포함 | ✅ 전체 | ✅ 안전 |
| 파일 복사 | ❌ 누락 | ❌ 누락 | ❌ 없음 | ⚠️ 위험 |
| USB | ✅ 가능 | ✅ 가능 | ✅ 가능 | ⚠️ 관리 필요 |
| PR (금지) | ✅ 보존 | ✅ 포함 | ✅ 전체 | ❌ 정책 위반 |

---

## 🎯 결론

### Patch 방식의 장점

✅ **커밋 히스토리 보존**: git log에서 온전한 개발 과정 볼 수 있음
✅ **메타데이터 유지**: 작성자, 날짜, 메시지 모두 보존
✅ **테스트 코드 포함**: 버그 수정의 검증 과정이 담김
✅ **회사 보안 정책 준수**: 공식 채널을 통한 안전한 반출
✅ **TDD 원칙 유지**: 테스트가 함께 이동

### 언제 사용할까?

```
✅ 사내에서 버그 발견
✅ 회사 규정상 직접 push 불가
✅ 코드 품질과 히스토리가 중요함
✅ 팀과 협업해야 함
```

---

**작성**: 2025-11-25
**버전**: 1.0
**기반**: 동료 피드백
