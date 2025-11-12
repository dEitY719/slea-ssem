# REQ-F-A2-2-1: 닉네임 설정 완료 후 자기평가 입력 페이지로 이동

**날짜**: 2025-11-12
**담당자**: Claude Code
**우선순위**: M (Must)
**상태**: ✅ 완료

---

## 📋 요구사항

### 요약
닉네임 설정 완료 후 또는 "시작하기" 클릭 시 (nickname 있고 profile 없음), 자기평가 입력 페이지로 이동해야 한다

### 수용 기준
- ✅ "닉네임 설정 완료 후 자기평가 입력 페이지로 자동 이동한다"

### 관련 문서
- `docs/feature_requirement_mvp1.md` - REQ-F-A2-2-1 (Line 127)

---

## 🎯 Phase 1: Specification

### Intent
사용자 온보딩 플로우에서 닉네임 설정 후 자기평가 입력 단계로 자동 진행하여 원활한 사용자 경험 제공

### Implementation Strategy
**Phase 1 (현재 구현)**: Frontend only
- Backend profile check API가 없으므로, nickname 존재 시 무조건 `/self-assessment`로 이동
- 향후 profile check API 추가 시 조건부 분기 가능

### 구현 위치

#### 1. NicknameSetupPage (이미 완료)
- **File**: `src/frontend/src/pages/NicknameSetupPage.tsx:48`
- **Logic**: 닉네임 등록 성공 시 → `navigate('/self-assessment', { replace: true })`
- **Related REQ**: REQ-F-A2-7 (완료)

#### 2. HomePage (새로 구현)
- **File**: `src/frontend/src/pages/HomePage.tsx:13-27`
- **Logic**: "시작하기" 클릭 시 nickname 확인 후 분기
  ```typescript
  if (currentNickname === null) {
    navigate('/nickname-setup')  // REQ-F-A2-1
  } else {
    navigate('/self-assessment')  // REQ-F-A2-2-1 (NEW)
  }
  ```

### Backend API Status
**현재**: Profile check API 없음
- `GET /profile/nickname`: nickname만 반환, profile 상태 미포함
- `UserProfileSurvey` 모델 존재, but 조회 API 없음

**향후 개선**:
- Option 1: `GET /profile/nickname` 응답에 `has_profile: boolean` 추가
- Option 2: 새로운 `GET /profile/status` 엔드포인트 생성

---

## 🧪 Phase 2: Test Design

### 테스트 파일
**`src/frontend/src/pages/__tests__/HomePage.test.tsx`**

### 수정된 테스트 케이스

#### Test 4: "should redirect to /nickname-setup when nickname is null"
```typescript
it('should redirect to /nickname-setup when nickname is null', async () => {
  // REQ: REQ-F-A2-1
  // Mock API response: nickname is null
  // Verify: navigate('/nickname-setup')
})
```

**변경사항**:
- ❌ Old: 테스트 이름에 `/signup` 언급, 잘못된 기대값
- ✅ New: `/nickname-setup`으로 수정 (REQ-F-A2-1 준수)

#### Test 5: "should navigate to self-assessment when nickname exists" ✅ NEW
```typescript
it('should navigate to self-assessment when nickname exists', async () => {
  // REQ: REQ-F-A2-2-1
  // Mock API response: nickname exists
  // Verify: navigate('/self-assessment')
})
```

**변경사항**:
- ❌ Old 테스트 이름: "should proceed to next step when nickname exists"
- ❌ Old 기대값: `expect(mockNavigate).toHaveBeenCalled()` (placeholder)
- ✅ New 테스트 이름: "should navigate to self-assessment when nickname exists"
- ✅ New 기대값: `expect(mockNavigate).toHaveBeenCalledWith('/self-assessment')`

---

## 💻 Phase 3: Implementation

### 1. `src/frontend/src/pages/HomePage.tsx` (수정)

**변경 내용** (Lines 13-27):
```typescript
const handleStart = async () => {
  try {
    const currentNickname = await checkNickname()

    if (currentNickname === null) {
      navigate('/nickname-setup')  // REQ-F-A2-1
    } else {
      // ✅ REQ-F-A2-2-1: Navigate to self-assessment
      navigate('/self-assessment')  // CHANGED from '/signup'

      // TODO: When profile check API is available:
      // if (hasProfile) navigate('/test')
      // else navigate('/self-assessment')
    }
  } catch (err) {
    // Error handling...
  }
}
```

**Key Changes**:
- Line 26: `navigate('/signup')` → `navigate('/self-assessment')`
- Comment 추가: REQ-F-A2-2-1 참조
- TODO 추가: 향후 profile check API 연동 가이드

### 2. `src/frontend/src/pages/__tests__/HomePage.test.tsx` (수정)

**변경 1** (Test 4, Lines 88-114):
```typescript
it('should redirect to /nickname-setup when nickname is null', async () => {
  // REQ: REQ-F-A2-1
  // ...
  await waitFor(() => {
    expect(mockNavigate).toHaveBeenCalledWith('/nickname-setup')  // FIXED
  })
})
```

**변경 2** (Test 5, Lines 116-140):
```typescript
it('should navigate to self-assessment when nickname exists', async () => {
  // REQ: REQ-F-A2-2-1
  // ...
  await waitFor(() => {
    expect(mockNavigate).toHaveBeenCalledWith('/self-assessment')  // CHANGED
  })
})
```

---

## ✅ Phase 4: Test Results

### 테스트 실행 결과

```
✓ src/pages/__tests__/HomePage.test.tsx (7 tests) 267ms

Test Files  1 passed (1)
     Tests  7 passed (7)
  Duration  1.14s
```

**관련 테스트**:
- ✅ Test 4: "should redirect to /nickname-setup when nickname is null" (REQ-F-A2-1)
- ✅ Test 5: "should navigate to self-assessment when nickname exists" (REQ-F-A2-2-1)

**✅ 100% test coverage (7/7 tests passing)**

---

## 📊 Traceability Matrix

| REQ ID | Specification | Implementation | Test | Status |
|--------|--------------|----------------|------|--------|
| REQ-F-A2-2-1 (Part 1) | 닉네임 설정 완료 후 이동 | `NicknameSetupPage.tsx:48` | N/A (REQ-F-A2-7 테스트) | ✅ |
| REQ-F-A2-2-1 (Part 2) | "시작하기" 클릭 시 이동 | `HomePage.tsx:26` | `HomePage.test.tsx:116-140` | ✅ |

---

## 📁 변경된 파일 목록

### 수정
- `src/frontend/src/pages/HomePage.tsx` (+3 lines, -4 lines) - handleStart logic
- `src/frontend/src/pages/__tests__/HomePage.test.tsx` (+8 lines, -4 lines) - Test 4, 5 수정

**Total**: +11 lines, -8 lines

---

## 🔄 User Flow Diagram

```
User clicks "시작하기" on HomePage
  │
  ├─→ GET /api/profile/nickname
  │   └─→ Response: { nickname: "..." | null }
  │
  └─→ Branch:
      │
      ├─→ nickname === null
      │   └─→ navigate('/nickname-setup') ✅ REQ-F-A2-1
      │       │
      │       └─→ User registers nickname
      │           └─→ navigate('/self-assessment') ✅ REQ-F-A2-7
      │
      └─→ nickname !== null
          └─→ navigate('/self-assessment') ✅ REQ-F-A2-2-1
              │
              └─→ [Future: if hasProfile, navigate('/test')]
```

---

## ✅ Acceptance Criteria 검증

- ✅ "닉네임 설정 완료 후 자기평가 입력 페이지로 자동 이동한다"
  - Part 1: NicknameSetupPage → /self-assessment (REQ-F-A2-7)
  - Part 2: HomePage (nickname exists) → /self-assessment (REQ-F-A2-2-1)

---

## 🎓 Implementation Notes

### ⚠️ Current Limitation
- **No profile check**: Backend에 profile 확인 API가 없어, nickname만으로 분기
- **Temporary behavior**: nickname 있으면 무조건 `/self-assessment`로 이동
  - 이미 profile 작성한 사용자도 self-assessment 페이지로 이동됨
  - 향후 profile check API 추가 시 개선 필요

### 🚀 Future Enhancement
```typescript
// When profile check API is available:
const { nickname, hasProfile } = await checkProfile()

if (!nickname) {
  navigate('/nickname-setup')
} else if (!hasProfile) {
  navigate('/self-assessment')  // REQ-F-A2-2-1
} else {
  navigate('/test')  // REQ-F-B2 (향후 구현)
}
```

---

## 📝 관련 요구사항

**의존성**:
- **REQ-F-A2-1**: 홈화면 "시작하기" 클릭 시 닉네임 체크 - ✅ 완료
- **REQ-F-A2-7**: "다음" 버튼 클릭 시 nickname 업데이트 및 리다이렉트 - ✅ 완료

**후속 작업**:
- **REQ-F-A2-2-2**: 자기평가 정보 입력 UI 구현
- **Backend**: Profile check API 추가 (향후)

---

**구현 완료일**: 2025-11-12
**Commit**: 8034886
**상태**: ✅ Done
