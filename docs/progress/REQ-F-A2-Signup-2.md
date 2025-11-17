# REQ-F-A2-Signup-2: Navigation to Unified Signup Page

**Status**: ✅ Done  
**Commit**: b757745  
**Phase**: 4 (Complete)

---

## Phase 1️⃣: SPECIFICATION

### Requirement

**REQ ID**: REQ-F-A2-Signup-2  
**Description**: "회원가입" 버튼 클릭 시, 통합 회원가입 페이지(`/signup`)로 이동해야 한다.  
**Priority**: M (Medium)

### Intent

사용자가 헤더의 "회원가입" 버튼을 클릭하면 `/signup` 페이지로 즉시 이동하여, 닉네임과 자기평가를 한 번에 입력할 수 있는 통합 회원가입 flow를 시작한다.

### Implementation Location

**File**: `src/frontend/src/components/Header.tsx`

**Signature**:
```typescript
// "회원가입" 버튼의 onClick 핸들러
const handleSignupClick = () => void

// React Router navigation hook 사용
const navigate = useNavigate()
```

### Behavior

1. **"회원가입" 버튼 클릭 이벤트**:
   - 사용자가 헤더의 "회원가입" 버튼을 클릭
   
2. **Navigation 실행**:
   - `useNavigate()` hook을 사용하여 `/signup` 경로로 이동
   - `navigate('/signup')` 호출

3. **페이지 전환**:
   - React Router가 `/signup` 경로와 매칭되는 `SignupPage` 컴포넌트를 렌더링

### Dependencies

- ✅ **React Router**: `react-router-dom` v6 (navigation)
- ✅ **REQ-F-A2-Signup-1**: "회원가입" 버튼 표시 (선행 요구사항)
- ⏳ **REQ-F-A2-Signup-3**: `/signup` 페이지 구현 (후속 요구사항)

### Non-functional Requirements

- **Performance**: Navigation은 즉각적이어야 함 (< 100ms)
- **Accessibility**: 버튼 클릭 외에도 Enter 키로 활성화 가능
- **UX**: Navigation 중 loading indicator 불필요 (즉시 전환)

---

## Phase 2️⃣: TEST DESIGN

### Test Location

**File**: `src/frontend/src/components/__tests__/Header.test.tsx`  
**Test ID**: Test 3

### Test Case: "회원가입" 버튼 클릭 시 /signup으로 이동 ✅

**REQ**: REQ-F-A2-Signup-2

**Setup**:
```typescript
const mockNavigate = jest.fn()
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}))

renderWithRouter(<Header nickname={null} />)
```

**Actions**:
1. Find "회원가입" button
2. Click the button
3. Verify `navigate('/signup')` was called

**Expectation**:
- ✅ `mockNavigate` should be called with `'/signup'`

**Code**:
```typescript
test('"회원가입" 버튼 클릭 시 /signup으로 이동', async () => {
  const user = userEvent.setup()
  renderWithRouter(<Header nickname={null} />)
  
  const signupButton = screen.getByRole('button', { name: /회원가입/i })
  await user.click(signupButton)
  
  expect(mockNavigate).toHaveBeenCalledWith('/signup')
})
```

### Test Coverage

| Test Case | Status | Coverage |
|-----------|--------|----------|
| "회원가입" 버튼 클릭 → `/signup` navigation | ✅ Pass | Navigation logic |

**Test Result**: 1/1 tests passing (100%)

---

## Phase 3️⃣: IMPLEMENTATION

### Implementation Details

#### Component: Header.tsx (lines 35-38)

**Navigation Handler**:
```typescript
const navigate = useNavigate()

const handleSignupClick = () => {
  navigate('/signup')
}
```

**JSX (Button with onClick)**:
```typescript
{!nickname && (
  <button 
    className="signup-button" 
    onClick={handleSignupClick}
  >
    회원가입
  </button>
)}
```

### Code Structure

```
Header Component
├── useNavigate() hook (React Router)
├── handleSignupClick() handler
│   └── navigate('/signup')
└── Render
    └── "회원가입" button (conditional)
        └── onClick={handleSignupClick}
```

### Validation Results

#### Tests (Phase 2 → Phase 3)

```bash
$ npm test -- Header.test.tsx

PASS  src/components/__tests__/Header.test.tsx
  Header Component
    ✓ "회원가입" 버튼 클릭 시 /signup으로 이동 (52ms)

Test Suites: 1 passed, 1 total
Tests:       6 passed (including Signup-2 test), 6 total
```

#### Linting & Type Checking

```bash
$ npm run lint
✓ No linting errors

$ npm run type-check
✓ No type errors
```

---

## Phase 4️⃣: SUMMARY

### Modified Files

1. **`src/frontend/src/components/Header.tsx`**
   - Added `useNavigate()` hook import
   - Added `handleSignupClick()` handler
   - Wired button to navigation handler

2. **`src/frontend/src/components/__tests__/Header.test.tsx`**
   - Added Test 3: Navigation test
   - Mocked `useNavigate()` hook
   - Verified navigation call

### Test Results

✅ **All tests passing** (6/6 in Header.test.tsx)
- Test 3 specifically covers REQ-F-A2-Signup-2 (navigation)

### REQ Traceability

| REQ | Implementation | Test | Status |
|-----|----------------|------|--------|
| **REQ-F-A2-Signup-2** | `Header.tsx:35-38` (handleSignupClick) | `Header.test.tsx:48-60` (Test 3) | ✅ |

### Acceptance Criteria

- ✅ **"회원가입" 버튼 클릭 시 `/signup` 페이지로 이동**
  - Implementation: `navigate('/signup')` in `handleSignupClick()`
  - Test: Test 3 in `Header.test.tsx`
  - Result: ✅ Pass

### Notes

- **Coupled with REQ-F-A2-Signup-1**: Navigation logic is implemented in the same commit as button display logic
- **Depends on REQ-F-A2-Signup-3**: `/signup` route must be configured in React Router (implemented in commit 273c30a)
- **Navigation is instant**: No loading state needed as it's a client-side route change

### Related Requirements

- ✅ **REQ-F-A2-Signup-1**: "회원가입" 버튼 표시 (commit: b757745) - Prerequisite
- ✅ **REQ-F-A2-Signup-3**: `/signup` 페이지 구현 (commit: 273c30a) - Downstream

---

## Git Commit

**Commit**: b757745  
**Message**: `implement REQ-F-A2-Signup-1`  
**Files Changed**: 5 files (+360 lines)
- `Header.tsx`: Added navigation logic
- `Header.test.tsx`: Added navigation test
- `HomePage.tsx`: Updated to use `<Header />` component
- `HomePage.test.tsx`: Updated tests
- `Header.css`: Added button styles

**Note**: REQ-F-A2-Signup-2 (navigation) was implemented together with REQ-F-A2-Signup-1 (button display) in the same commit for code cohesion.

---

**Phase**: 4 → ✅ Done  
**Developer**: lavine  
**Date**: 2025 (backfilled progress doc)
