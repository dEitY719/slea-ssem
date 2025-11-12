# REQ-F-A2-6: "사용 가능" 상태 표시 및 "다음" 버튼 활성화

**날짜**: 2025-11-11
**담당자**: lavine (Cursor IDE)
**우선순위**: M (Must)
**상태**: ✅ 완료

---

## 📋 요구사항

### 요약

닉네임 중복 확인 결과가 "사용 가능"일 때, 성공 메시지를 표시하고 "다음" 버튼을 활성화하여 사용자가 다음 단계로 진행할 수 있도록 함

### 수용 기준

- ✅ 중복 없음 → "사용 가능한 닉네임입니다" 메시지 표시
- ✅ "다음" 버튼 활성화 (사용 가능 상태일 때만)
- ✅ 닉네임 변경 시 → "다음" 버튼 비활성화 (재확인 필요)

### 관련 문서

- `docs/feature_requirement_mvp1.md` - REQ-F-A2-6 (Line 110)

---

## 🎯 Phase 1: Specification

### Intent

닉네임이 사용 가능함을 명확하게 사용자에게 알리고, "다음" 버튼을 통해 자기평가 입력 단계로 진행할 수 있는 UI/UX 제공

### Button State Logic

```
"다음" 버튼 활성화 조건:
  checkStatus === 'available' AND NOT isSubmitting

"다음" 버튼 비활성화 조건:
  - checkStatus !== 'available'
  - isSubmitting === true
  - 닉네임 입력 필드 변경 시 (status → 'idle')
```

### 구현 위치

- `src/frontend/src/pages/NicknameSetupPage.tsx` - **IMPLEMENTED** - Button state & message display
- `src/frontend/src/hooks/useNicknameCheck.ts` - **IMPLEMENTED** - State management
- `src/frontend/src/pages/__tests__/NicknameSetupPage.test.tsx` - **IMPLEMENTED** - Tests

---

## 🧪 Phase 2: Test Design

### 테스트 파일

**`src/frontend/src/pages/__tests__/NicknameSetupPage.test.tsx`**

### 테스트 커버리지

#### Test: "keeps next button disabled initially"

- Render NicknameSetupPage
- Verify "다음" button is disabled
- **Purpose**: 초기 상태 검증 ✅ REQ-F-A2-6

#### Test: "shows available message when nickname is not taken"

- Mock API response: `{ available: true }`
- Click "중복 확인"
- Verify "사용 가능한 닉네임입니다" message displayed
- Verify "다음" button enabled
- **Purpose**: 사용 가능 상태 검증 ✅ REQ-F-A2-6

#### Test: "re-disables next button when nickname changes after success"

- Mock successful check (available)
- Verify "다음" button enabled
- Change nickname input
- Verify "다음" button disabled again
- **Purpose**: 재확인 필요성 검증 ✅ REQ-F-A2-6

---

## 💻 Phase 3: Implementation

### 1. `src/frontend/src/pages/NicknameSetupPage.tsx` (Lines 57-84)

**Success Message Display**:

```typescript
const getStatusMessage = () => {
  if (checkStatus === 'available') {
    return {
      text: '사용 가능한 닉네임입니다.',  // ✅ REQ-F-A2-6
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
      text: errorMessage,
      className: 'status-message error',
    }
  }
  return null
}

const statusMessage = getStatusMessage()
const isNextEnabled = checkStatus === 'available'  // ✅ Button enable logic
const isNextDisabled = !isNextEnabled || isInputDisabled
```

**Button Rendering**:

```typescript
<button
  type="button"
  className="next-button"
  onClick={handleNextClick}
  disabled={isNextDisabled}  // ✅ REQ-F-A2-6: Only enabled when available
>
  {isSubmitting ? '저장 중...' : '다음'}
</button>
```

### 2. `src/frontend/src/hooks/useNicknameCheck.ts` (Lines 54-62)

**State Reset on Input Change**:

```typescript
const setNickname = useCallback(
  (value: string) => {
    setNicknameState(value)
    setCheckStatus('idle')  // ✅ Reset to idle → button disabled
    setErrorMessage(null)
    setSuggestions([])
  },
  []
)
```

**Key Behavior**:

- Any change to nickname input → `checkStatus` reset to `'idle'`
- `'idle'` status → "다음" button disabled
- Forces user to re-check nickname after editing

---

## ✅ Phase 4: Test Results

### 테스트 실행 결과

```
✓ src/pages/__tests__/NicknameSetupPage.test.tsx (13 tests) 1181ms
  ✓ keeps next button disabled initially ✅
  ✓ shows available message when nickname is not taken ✅
  ✓ re-disables next button when nickname changes after success ✅
```

**✅ 관련 테스트 통과 (3/13)**

---

## 📊 Traceability Matrix

| REQ ID | Specification | Implementation | Test | Status |
|--------|--------------|----------------|------|--------|
| REQ-F-A2-6 | "사용 가능" 메시지 표시 | `NicknameSetupPage.tsx:58-62` | Test line 60 | ✅ |
| REQ-F-A2-6 | "다음" 버튼 활성화 | `NicknameSetupPage.tsx:81,144` | Test line 76 | ✅ |
| REQ-F-A2-6 | 입력 변경 시 버튼 비활성화 | `useNicknameCheck.ts:57` | Test line 80 | ✅ |

---

## 📁 변경된 파일 목록

### 수정

- `src/frontend/src/pages/NicknameSetupPage.tsx` (+15 lines) - Button logic & message
- `src/frontend/src/hooks/useNicknameCheck.ts` (+5 lines) - State reset logic
- `src/frontend/src/pages/__tests__/NicknameSetupPage.test.tsx` (+40 lines) - Tests

**Total**: +60 lines

---

## 🎨 UI/UX Flow

```
Initial State:
  └─→ "다음" button: DISABLED

User enters nickname → "중복 확인" click:
  ├─→ available: true
  │   └─→ "사용 가능한 닉네임입니다" (green)
  │       └─→ "다음" button: ENABLED ✅
  │
  └─→ available: false
      └─→ "이미 사용 중인 닉네임입니다" (red)
          └─→ "다음" button: DISABLED

User edits nickname after success:
  └─→ checkStatus → 'idle'
      └─→ "다음" button: DISABLED (재확인 필요)
```

---

## ✅ Acceptance Criteria 검증

- ✅ 사용 가능 시 성공 메시지 표시
- ✅ 사용 가능 시 "다음" 버튼 활성화
- ✅ 닉네임 변경 시 버튼 비활성화
- ✅ 초기 로드 시 버튼 비활성화

---

## 🎓 Button State Matrix

| Check Status | isSubmitting | Button Enabled? |
|-------------|--------------|-----------------|
| `idle` | false | ❌ No |
| `checking` | false | ❌ No |
| `available` | false | ✅ Yes |
| `available` | true | ❌ No (saving) |
| `taken` | false | ❌ No |
| `error` | false | ❌ No |

---

## 📝 관련 요구사항

**의존성**:

- **REQ-F-A2-2**: 닉네임 입력 필드 & 중복 확인 버튼
- **REQ-F-A2-3**: 실시간 유효성 검사

**관련 작업**:

- **REQ-F-A2-7**: "다음" 버튼 클릭 시 닉네임 등록

---

**구현 완료일**: 2025-11-11
**Commit**: 21243fd (Merge pull request #14 - implement frontend feature REQ-F-A2-6)
**상태**: ✅ Done
