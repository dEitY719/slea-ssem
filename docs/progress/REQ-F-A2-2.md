# REQ-F-A2-2: 닉네임 입력 필드와 "중복 확인" 버튼 제공

**날짜**: 2025-11-11
**담당자**: lavine (Cursor IDE)
**우선순위**: M (Must)
**상태**: ✅ 완료

---

## 📋 요구사항

### 요약

닉네임 설정 페이지에서 사용자가 닉네임을 입력할 수 있는 필드와 "중복 확인" 버튼을 제공하여, 백엔드 API를 호출해 닉네임 사용 가능 여부를 확인

### 수용 기준

- ✅ "닉네임 입력 후 1초 내 '중복 확인' 결과가 표시된다"
- ✅ 입력 필드 (3-30자 제한)
- ✅ "중복 확인" 버튼 (클릭 시 API 호출)

### 관련 문서

- `docs/feature_requirement_mvp1.md` - REQ-F-A2-2 (Line 106)

---

## 🎯 Phase 1: Specification

### Intent

사용자가 원하는 닉네임을 입력하고, 중복 확인 버튼을 클릭하여 사용 가능 여부를 즉시 확인할 수 있는 UI 제공

### 구현 위치

- `src/frontend/src/pages/NicknameSetupPage.tsx` - **IMPLEMENTED** - 닉네임 입력 UI
- `src/frontend/src/hooks/useNicknameCheck.ts` - **IMPLEMENTED** - 닉네임 체크 로직
- `src/frontend/src/pages/__tests__/NicknameSetupPage.test.tsx` - **IMPLEMENTED** - Test suite

### Backend API (이미 구현됨 ✅)

**Endpoint**: `POST /profile/nickname/check`

- **File**: `src/backend/api/profile.py:120-148`
- **Authentication**: Not required (public endpoint)

**Request**:

```json
{
  "nickname": "john_doe"
}
```

**Response**:

```json
{
  "available": true,
  "suggestions": []
}
```

---

## 🧪 Phase 2: Test Design

### 테스트 파일

**`src/frontend/src/pages/__tests__/NicknameSetupPage.test.tsx`**

### 테스트 커버리지

#### Test: "renders nickname input field, check button, and next button"

- Verify input field, "중복 확인" button, "다음" button rendered
- **Purpose**: UI 렌더링 검증 ✅ REQ-F-A2-2

#### Test: "shows available message when nickname is not taken"

- Mock API response: `{ available: true }`
- Click "중복 확인" button
- Verify "사용 가능한 닉네임입니다" message displayed
- **Purpose**: 사용 가능 메시지 표시 검증 ✅ REQ-F-A2-2

#### Test: "shows taken message when nickname is already used"

- Mock API response: `{ available: false, suggestions: [...] }`
- Click "중복 확인" button
- Verify "이미 사용 중인 닉네임입니다" message displayed
- **Purpose**: 중복 메시지 표시 검증 ✅ REQ-F-A2-2

---

## 💻 Phase 3: Implementation

### 1. `src/frontend/src/pages/NicknameSetupPage.tsx` (Lines 94-117)

**UI Components**:

```typescript
<div className="input-group">
  <input
    id="nickname-input"
    type="text"
    className="nickname-input"
    value={nickname}
    onChange={(e) => setNickname(e.target.value)}
    placeholder="영문자, 숫자, 언더스코어 (3-30자)"
    maxLength={30}
    disabled={isInputDisabled}
  />
  <button
    className="check-button"
    onClick={handleCheckClick}
    disabled={isCheckButtonDisabled}
  >
    {isChecking ? '확인 중...' : '중복 확인'}
  </button>
</div>
```

**Features**:

- Input field with 30-character limit
- "중복 확인" button with loading state
- Disabled states during checking/submission

### 2. `src/frontend/src/hooks/useNicknameCheck.ts` (Lines 70-116)

**checkNickname function**:

```typescript
const checkNickname = useCallback(async (): Promise<void> => {
  // Validate length (3-30 characters)
  if (nickname.length < 3) {
    setCheckStatus('error')
    setErrorMessage('닉네임은 3자 이상이어야 합니다.')
    return
  }

  // Validate characters
  const validPattern = /^[a-zA-Z0-9_]+$/
  if (!validPattern.test(nickname)) {
    setCheckStatus('error')
    setErrorMessage('닉네임은 영문자, 숫자, 언더스코어만 사용 가능합니다.')
    return
  }

  // Call API
  setCheckStatus('checking')
  try {
    const response = await transport.post<NicknameCheckResponse>(
      '/profile/nickname/check',
      { nickname }
    )

    if (response.available) {
      setCheckStatus('available')
    } else {
      setCheckStatus('taken')
      setSuggestions(response.suggestions)
    }
  } catch (err) {
    setCheckStatus('error')
    setErrorMessage('닉네임 확인에 실패했습니다.')
  }
}, [nickname])
```

---

## ✅ Phase 4: Test Results

### 테스트 실행 결과

```
✓ src/pages/__tests__/NicknameSetupPage.test.tsx (13 tests) 1181ms
  ✓ renders nickname input field, check button, and next button ✅
  ✓ shows available message when nickname is not taken ✅
  ✓ shows taken message when nickname is already used ✅
```

**✅ 관련 테스트 통과 (3/13)**

---

## 📊 Traceability Matrix

| REQ ID | Specification | Implementation | Test | Status |
|--------|--------------|----------------|------|--------|
| REQ-F-A2-2 | 닉네임 입력 필드 제공 | `NicknameSetupPage.tsx:99-108` | Test line 43 | ✅ |
| REQ-F-A2-2 | "중복 확인" 버튼 제공 | `NicknameSetupPage.tsx:109-116` | Test line 43 | ✅ |
| REQ-F-A2-2 | API 호출 및 결과 표시 | `useNicknameCheck.ts:100-110` | Tests 60, 105 | ✅ |

---

## 📁 변경된 파일 목록

### 신규 생성

- `src/frontend/src/pages/NicknameSetupPage.tsx` (166 lines)
- `src/frontend/src/pages/NicknameSetupPage.css` (CSS styles)
- `src/frontend/src/hooks/useNicknameCheck.ts` (128 lines)

### 수정

- `src/frontend/src/pages/__tests__/NicknameSetupPage.test.tsx` (테스트 추가)

---

## ✅ Acceptance Criteria 검증

- ✅ 닉네임 입력 필드 표시 (3-30자 제한)
- ✅ "중복 확인" 버튼 클릭 시 API 호출
- ✅ 사용 가능/중복 메시지 표시

---

## 📝 관련 요구사항

**의존성**:

- **REQ-B-A2-Avail-1**: `POST /profile/nickname/check` 엔드포인트 - ✅ 완료

**관련 작업**:

- **REQ-F-A2-3**: 실시간 유효성 검사 (같은 커밋에 구현)
- **REQ-F-A2-4**: 닉네임 대안 제안 (이후 구현)

---

**구현 완료일**: 2025-11-11
**Commit**: 2190e73 (feat: Add nickname setup page with validation and next button)
**상태**: ✅ Done
