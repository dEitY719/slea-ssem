# REQ-F-A2-4: 닉네임 중복 시 대안 3개 시각적 제안

**Developer**: lavine (Claude Code)
**Status**: ✅ Done
**Phase**: 4
**Date**: 2025-11-12

---

## Phase 1: SPECIFICATION

### 📋 요구사항

**REQ ID**: REQ-F-A2-4
**요구사항**: 닉네임 중복 시 대안 3개를 시각적으로 제안해야 한다
**우선순위**: S (Should have)
**수용 기준**: "중복 시 3개의 대안이 제안된다"

### 🎯 구현 스펙

#### Location
- **Component**: `src/frontend/src/pages/NicknameSetupPage.tsx:122-138`
- **Hook**: `src/frontend/src/hooks/useNicknameCheck.ts:52,109`
- **Backend**: `src/backend/services/profile_service.py:76-106`

#### Signature
```typescript
// Frontend Hook
interface UseNicknameCheckResult {
  suggestions: string[]  // Array of 3 alternative nicknames
  checkStatus: 'taken' | 'available' | 'checking' | 'idle' | 'error'
}

// Backend API Response
interface NicknameCheckResponse {
  available: boolean
  suggestions: string[]  // Empty if available, 3 alternatives if taken
}
```

#### Behavior
1. **Backend**: When nickname is taken, generate 3 alternatives in format `base_nickname_N`
2. **Frontend**: Display suggestions only when `checkStatus === 'taken' && suggestions.length > 0`
3. **UI**: Render as clickable buttons that auto-fill the input field
4. **State Reset**: Clicking suggestion resets status to 'idle' and clears suggestions

#### Dependencies
- **Backend**: `ProfileService.generate_nickname_alternatives()` (REQ-B-A2-3)
- **API**: `POST /profile/nickname/check` endpoint

#### Non-functional
- **Performance**: Suggestions generated in <100ms
- **UX**: Visual separation between error message and suggestions
- **Accessibility**: Suggestions are keyboard-navigable buttons

---

## Phase 2: TEST DESIGN

### 📍 Test File
`src/frontend/src/pages/__tests__/NicknameSetupPage.test.tsx:254-348`

### ✅ Test Cases (3)

#### Test 1: Shows 3 alternative suggestions when nickname is taken
```typescript
test('shows 3 alternative suggestions when nickname is taken', async () => {
  // REQ: REQ-F-A2-4
  // Verifies: 3 suggestions rendered, "추천 닉네임" label displayed
})
```

**Coverage**:
- ✓ "추천 닉네임:" label appears
- ✓ All 3 suggestions rendered as text
- ✓ Displayed only when nickname is taken

#### Test 2: Fills input field when suggestion is clicked
```typescript
test('fills input field when suggestion is clicked', async () => {
  // REQ: REQ-F-A2-4
  // Verifies: Click updates input, status resets, suggestions disappear
})
```

**Coverage**:
- ✓ Input field value updates to clicked suggestion
- ✓ Error message disappears
- ✓ Other suggestions disappear

#### Test 3: Allows re-checking after selecting a suggestion
```typescript
test('allows re-checking after selecting a suggestion', async () => {
  // REQ: REQ-F-A2-4
  // Verifies: End-to-end flow from duplicate → suggestion → re-check → available
})
```

**Coverage**:
- ✓ Check button re-enabled after selection
- ✓ New API call with selected nickname
- ✓ Transitions to 'available' status

---

## Phase 3: IMPLEMENTATION

### 📂 Modified Files

#### 1. `src/frontend/src/pages/__tests__/NicknameSetupPage.test.tsx`
- **Lines**: 254-348 (95 lines added)
- **Changes**: Added 3 test cases for REQ-F-A2-4
- **Rationale**: Verify visual rendering and interaction of nickname suggestions

### 🧪 Test Results

```
✓ src/pages/__tests__/NicknameSetupPage.test.tsx (13 tests) 1181ms

Test Files  1 passed (1)
     Tests  13 passed (13)
```

**New Tests**:
- ✅ `shows 3 alternative suggestions when nickname is taken`
- ✅ `fills input field when suggestion is clicked`
- ✅ `allows re-checking after selecting a suggestion`

**Coverage**: 100% (3/3 test cases passed)

### 🔗 Implementation Already Complete

**Note**: UI implementation was already done in previous commits. This REQ focused on **adding comprehensive tests** for the existing suggestion feature.

**Existing Implementation**:
- `NicknameSetupPage.tsx:122-138` - Suggestions rendering
- `useNicknameCheck.ts:109` - Suggestions state management
- Backend `generate_nickname_alternatives()` - Already tested in `test_profile_service.py`

---

## Phase 4: TRACEABILITY

### 📊 REQ ↔ Implementation ↔ Tests

| REQ | Implementation | Test Coverage |
|-----|----------------|---------------|
| REQ-F-A2-4 | `NicknameSetupPage.tsx:122-138` | 3 tests (100%) |
| REQ-F-A2-4 | `useNicknameCheck.ts:52,109` | 3 tests (100%) |
| REQ-B-A2-3 | `profile_service.py:76-106` | 3 backend tests (100%) |

### 🔗 Traceability Matrix

```
REQ-F-A2-4 (닉네임 중복 시 대안 3개 시각적 제안)
  ├─ Frontend Tests (src/frontend/src/pages/__tests__/NicknameSetupPage.test.tsx)
  │   ├─ Line 254-277: Shows 3 suggestions when taken
  │   ├─ Line 279-306: Fills input on suggestion click
  │   └─ Line 308-348: Re-check after selection
  ├─ Frontend Implementation (src/frontend/src/pages/NicknameSetupPage.tsx)
  │   └─ Line 122-138: Suggestions UI rendering
  ├─ Frontend Hook (src/frontend/src/hooks/useNicknameCheck.ts)
  │   ├─ Line 52: suggestions state
  │   └─ Line 109: suggestions update from API
  └─ Backend Implementation (src/backend/services/profile_service.py)
      └─ Line 76-106: generate_nickname_alternatives() (REQ-B-A2-3)
```

---

## 📝 Notes

### ✅ Acceptance Criteria Met

- [x] "중복 시 3개의 대안이 제안된다" - ✅ Verified by Test 1
- [x] Suggestions are clickable - ✅ Verified by Test 2
- [x] Selected suggestion can be re-checked - ✅ Verified by Test 3

### 🚀 Next Steps

No follow-up required. Feature complete.

### 🐛 Known Issues

- TypeScript build errors exist in other files (not related to this REQ)
- React `act()` warnings in test output (non-blocking, tests pass)

---

**Git Commit**: 8a43119
**Merge Date**: 2025-11-12
