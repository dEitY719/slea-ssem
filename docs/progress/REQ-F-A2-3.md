# REQ-F-A2-3: 실시간 유효성 검사 및 에러 메시지 표시

**날짜**: 2025-11-11
**담당자**: lavine (Cursor IDE)
**우선순위**: M (Must)
**상태**: ✅ 완료

---

## 📋 요구사항

### 요약
사용자가 유효하지 않은 닉네임(너무 짧음, 특수문자 등)을 입력할 경우, 중복 확인 버튼 클릭 시 즉시 에러 메시지를 표시

### 수용 기준
- ✅ 닉네임 길이 검증 (3-30자)
- ✅ 허용된 문자만 사용 (영문자, 숫자, 언더스코어)
- ✅ 에러 메시지 실시간 표시

### 관련 문서
- `docs/feature_requirement_mvp1.md` - REQ-F-A2-3 (Line 107)

---

## 🎯 Phase 1: Specification

### Intent
입력 검증을 통해 잘못된 닉네임이 백엔드로 전송되는 것을 방지하고, 사용자에게 명확한 피드백 제공

### Validation Rules
1. **Length**: 3-30 characters
2. **Characters**: Letters (a-z, A-Z), numbers (0-9), underscore (_) only
3. **Pattern**: `/^[a-zA-Z0-9_]+$/`

### 구현 위치
- `src/frontend/src/hooks/useNicknameCheck.ts` - **IMPLEMENTED** - Validation logic
- `src/frontend/src/pages/NicknameSetupPage.tsx` - **IMPLEMENTED** - Error message display
- `src/frontend/src/pages/__tests__/NicknameSetupPage.test.tsx` - **IMPLEMENTED** - Validation tests

---

## 🧪 Phase 2: Test Design

### 테스트 파일
**`src/frontend/src/pages/__tests__/NicknameSetupPage.test.tsx`**

### 테스트 커버리지

#### Test: "shows error for nickname shorter than 3 characters"
- Input: "ab" (2 characters)
- Click "중복 확인"
- Verify error: "닉네임은 3자 이상이어야 합니다"
- **Purpose**: 최소 길이 검증 ✅ REQ-F-A2-3

#### Test: "shows error for invalid characters in nickname"
- Input: "john@doe" (contains @)
- Click "중복 확인"
- Verify error: "닉네임은 영문자, 숫자, 언더스코어만 사용 가능합니다"
- **Purpose**: 문자 제한 검증 ✅ REQ-F-A2-3

---

## 💻 Phase 3: Implementation

### 1. `src/frontend/src/hooks/useNicknameCheck.ts` (Lines 75-94)

**Validation Logic**:
```typescript
const checkNickname = useCallback(async (): Promise<void> => {
  setErrorMessage(null)
  setSuggestions([])

  // Validate length (3-30 characters)
  if (nickname.length < 3) {
    setCheckStatus('error')
    setErrorMessage('닉네임은 3자 이상이어야 합니다.')
    return
  }

  if (nickname.length > 30) {
    setCheckStatus('error')
    setErrorMessage('닉네임은 30자 이하여야 합니다.')
    return
  }

  // Validate characters (letters, numbers, underscore only)
  const validPattern = /^[a-zA-Z0-9_]+$/
  if (!validPattern.test(nickname)) {
    setCheckStatus('error')
    setErrorMessage('닉네임은 영문자, 숫자, 언더스코어만 사용 가능합니다.')
    return
  }

  // Proceed to API call if validation passes
  setCheckStatus('checking')
  // ... API call logic
}, [nickname])
```

**Key Features**:
- **Early return** on validation failure (no API call)
- **Clear error messages** in Korean
- **State management** via `setCheckStatus('error')`

### 2. `src/frontend/src/pages/NicknameSetupPage.tsx` (Lines 57-77)

**Error Message Display**:
```typescript
const getStatusMessage = () => {
  if (checkStatus === 'available') {
    return {
      text: '사용 가능한 닉네임입니다.',
      className: 'status-message success',
    }
  }
  if (checkStatus === 'taken') {
    return {
      text: '이미 사용 중인 닉네임입니다.',
      className: 'status-message error',
    }
  }
  if (checkStatus === 'error' && errorMessage) {
    return {
      text: errorMessage,  // ✅ Display validation error
      className: 'status-message error',
    }
  }
  return null
}

// Render error message
{statusMessage && (
  <p className={statusMessage.className}>{statusMessage.text}</p>
)}
```

---

## ✅ Phase 4: Test Results

### 테스트 실행 결과

```
✓ src/pages/__tests__/NicknameSetupPage.test.tsx (13 tests) 1181ms
  ✓ shows error for nickname shorter than 3 characters ✅
  ✓ shows error for invalid characters in nickname ✅
```

**✅ 관련 테스트 통과 (2/13)**

---

## 📊 Traceability Matrix

| REQ ID | Specification | Implementation | Test | Status |
|--------|--------------|----------------|------|--------|
| REQ-F-A2-3 | 길이 검증 (3-30자) | `useNicknameCheck.ts:76-86` | Test line 127 | ✅ |
| REQ-F-A2-3 | 문자 검증 (영문/숫자/_) | `useNicknameCheck.ts:88-94` | Test line 142 | ✅ |
| REQ-F-A2-3 | 에러 메시지 표시 | `NicknameSetupPage.tsx:70-76` | Tests 127, 142 | ✅ |

---

## 📁 변경된 파일 목록

### 수정
- `src/frontend/src/hooks/useNicknameCheck.ts` (+20 lines) - Validation logic
- `src/frontend/src/pages/NicknameSetupPage.tsx` (+10 lines) - Error display
- `src/frontend/src/pages/__tests__/NicknameSetupPage.test.tsx` (+30 lines) - Tests

**Total**: +60 lines

---

## ✅ Acceptance Criteria 검증

- ✅ 3자 미만 닉네임 → 에러 메시지 표시
- ✅ 30자 초과 닉네임 → 에러 메시지 표시
- ✅ 특수문자 포함 → 에러 메시지 표시
- ✅ 유효한 닉네임 → API 호출 진행

---

## 🎓 검증 규칙

### ✅ Valid Nicknames
- `john_doe` (letters + underscore)
- `user123` (letters + numbers)
- `abc` (minimum 3 characters)
- `a_very_long_nickname_123` (up to 30 characters)

### ❌ Invalid Nicknames
- `ab` (too short)
- `john@doe` (contains @)
- `user name` (contains space)
- `한글닉네임` (non-ASCII characters)
- `a_very_long_nickname_that_exceeds_thirty` (too long)

---

## 📝 관련 요구사항

**의존성**:
- **REQ-F-A2-2**: 닉네임 입력 필드 (같은 커밋에 구현)

**관련 작업**:
- **REQ-F-A2-4**: 닉네임 대안 제안
- **REQ-F-A2-6**: "사용 가능" 상태 표시

---

**구현 완료일**: 2025-11-11
**Commit**: 2190e73 (feat: Add nickname setup page with validation and next button)
**상태**: ✅ Done
