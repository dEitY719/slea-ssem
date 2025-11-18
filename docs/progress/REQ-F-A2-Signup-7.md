# REQ-F-A2-Signup-7 Progress Report

**Feature**: 가입 완료 후 홈화면 재진입 시 "회원가입" 버튼 숨김
**Developer**: youkyoung kim (Cursor IDE)
**Status**: ✅ Phase 4 Complete
**Date**: 2025-11-17

---

## Phase 1: Specification

### Requirements

- **REQ ID**: REQ-F-A2-Signup-7
- **Description**: 가입 완료 후 홈화면 재진입 시, 헤더의 "회원가입" 버튼이 사라져야 한다. (nickname != NULL)
- **Priority**: M (Must)

### Acceptance Criteria

- 가입 완료 후 홈화면 진입 시 헤더에 "회원가입" 버튼이 표시되지 않는다
- nickname이 존재하면 "회원가입" 버튼 대신 닉네임이 표시된다
- localStorage에 캐싱된 닉네임을 사용하여 즉시 상태 반영
- 페이지 새로고침 후에도 상태가 유지된다

### Technical Specification

- **State Management**:
  - `useUserProfile` hook에서 localStorage 캐시 우선 로드
  - `getCachedNickname()` → 초기값으로 설정
  - API 호출 후 `setCachedNickname()` 업데이트
- **Header Logic**:
  - `nickname === null` → "회원가입" 버튼 표시
  - `nickname !== null` → 닉네임 표시, 버튼 숨김
- **Integration with REQ-F-A2-Signup-6**:
  - 가입 완료 시 `setCachedNickname(nickname)` 호출
  - HomePage 진입 시 캐시된 값 즉시 사용

---

## Phase 2: Test Design

### Test Cases (REQ-F-A2-Signup-7 직접 관련)

1. ✅ `Header` - nickname이 존재할 때 "회원가입" 버튼 숨김 (line 38-46)
2. ✅ `Header` - nickname 표시 시 "회원가입" 버튼 숨김 (상호 배타성) (line 106-117)
3. ✅ `Header` - loading 중에는 "회원가입" 버튼 숨김 (line 62-70)
4. ✅ `Header` - nickname 동적 업데이트 (line 134-150)
5. ✅ `HomePage` - 페이지 로드 시 닉네임 체크 API 호출 (line 87-106)

### Test Files

- **Header Tests**: `src/frontend/src/components/__tests__/Header.test.tsx` (14 tests)
- **HomePage Tests**: `src/frontend/src/pages/__tests__/HomePage.test.tsx`

### Key Test Verification

```typescript
// Header.test.tsx line 38-46
test('nickname이 존재할 때 "회원가입" 버튼 숨김', () => {
  // Given: nickname exists (user already signed up)
  renderWithRouter(<Header nickname="테스터123" />)

  // Then: "회원가입" button should not be visible
  const signupButton = screen.queryByRole('button', { name: /회원가입/i })
  expect(signupButton).not.toBeInTheDocument()
})

// Header.test.tsx line 106-117
test('nickname 표시 시 "회원가입" 버튼 숨김 (상호 배타성)', () => {
  // Given: nickname exists
  renderWithRouter(<Header nickname="민준" />)

  // Then: Signup button should not be visible
  expect(signupButton).not.toBeInTheDocument()

  // And: Nickname should be visible
  expect(screen.getByText('민준')).toBeInTheDocument()
})
```

---

## Phase 3: Implementation

### Core Logic Flow

```
1. SignupPage (REQ-F-A2-Signup-6)
   ├── completeProfileSignup() 성공
   ├── setCachedNickname(nickname) → localStorage에 저장
   └── navigate('/home') → 홈화면으로 이동

2. HomePage (진입)
   ├── useUserProfile() hook 초기화
   │   └── getCachedNickname() → localStorage에서 즉시 로드
   ├── Header에 nickname 전달
   └── API 호출로 최신 정보 확인

3. Header (렌더링)
   ├── nickname !== null 확인
   ├── "회원가입" 버튼 숨김
   └── 닉네임 표시
```

### Header Component

**File**: `src/frontend/src/components/Header.tsx`
**Lines**: 53-77

```tsx
<div className="header-right">
  {shouldRenderControls && (
    <>
      {/* REQ-F-A2-Signup-1: Show "회원가입" button only when nickname is null */}
      {nickname === null && (
        <button className="signup-button" onClick={handleSignupClick}>
          <UserPlusIcon className="button-icon" />
          회원가입
        </button>
      )}

      {/* REQ-F-A2-Profile-Access-1: Show nickname when not null */}
      {nickname !== null && (
        <div className="nickname-display">
          <UserCircleIcon />
          <span className="nickname-text">{nickname}</span>
        </div>
      )}
    </>
  )}
</div>
```

### HomePage Integration

**File**: `src/frontend/src/pages/HomePage.tsx`
**Lines**: 31, 34-46, 89

```tsx
// Line 31: useUserProfile hook 사용
const { nickname, loading: nicknameLoading, checkNickname } = useUserProfile()

// Lines 34-46: 컴포넌트 마운트 시 닉네임 로드
useEffect(() => {
  const loadNickname = async () => {
    try {
      await checkNickname()
    } catch (err) {
      console.error('Failed to load nickname:', err)
    }
  }
  loadNickname()
}, [checkNickname])

// Line 89: Header에 nickname 전달
<Header nickname={nickname} isLoading={nicknameLoading} />
```

### Nickname Caching (REQ-F-A2-Signup-6 연계)

**File**: `src/frontend/src/utils/nicknameCache.ts`

```typescript
export const setCachedNickname = (nickname: string): void => {
  localStorage.setItem(CACHE_KEY, nickname)
}

export const getCachedNickname = (): string | null => {
  return localStorage.getItem(CACHE_KEY)
}
```

**File**: `src/frontend/src/hooks/useUserProfile.ts`
**Line**: 29

```typescript
// 초기값으로 캐시된 닉네임 사용 → 즉시 상태 반영
const [nickname, setNickname] = useState<string | null>(() => getCachedNickname())
```

---

## Phase 4: Summary & Traceability

### Test Results

```
✓ src/components/__tests__/Header.test.tsx (14 tests)
  REQ-F-A2-Signup-1 - 6 tests
  ✓ nickname이 null일 때 "회원가입" 버튼 표시
  ✓ nickname이 존재할 때 "회원가입" 버튼 숨김  ← REQ-F-A2-Signup-7
  ✓ "회원가입" 버튼 클릭 시 /signup으로 이동
  ✓ nickname loading 중에는 "회원가입" 버튼 숨김

  REQ-F-A2-Profile-Access-1 - 8 tests
  ✓ nickname 표시 시 "회원가입" 버튼 숨김 (상호 배타성)  ← REQ-F-A2-Signup-7
  ✓ nickname 동적 업데이트  ← REQ-F-A2-Signup-7

✓ src/pages/__tests__/HomePage.test.tsx
  ✓ API 호출로 닉네임 상태 확인
```

### Requirements → Implementation Mapping

| REQ | Implementation | Test Coverage |
|-----|----------------|---------------|
| REQ-F-A2-Signup-7 | `Header.tsx:57-66` - nickname null 조건부 렌더링 | `Header.test.tsx:38-46` |
| REQ-F-A2-Signup-7 | `Header.tsx:69-76` - nickname 표시 로직 | `Header.test.tsx:106-117` |
| REQ-F-A2-Signup-7 | `useUserProfile.ts:29` - 캐시 기반 초기값 | `HomePage.test.tsx:71-85` |
| REQ-F-A2-Signup-7 | `HomePage.tsx:89` - Header에 nickname 전달 | `HomePage.test.tsx:87-106` |

### Modified Files

1. `src/frontend/src/components/Header.tsx` - 조건부 버튼/닉네임 렌더링 (lines 53-77)
2. `src/frontend/src/pages/HomePage.tsx` - useUserProfile 통합 및 Header 연결 (lines 31, 89)
3. `src/frontend/src/hooks/useUserProfile.ts` - localStorage 캐시 기반 초기화 (line 29)
4. `src/frontend/src/utils/nicknameCache.ts` - 닉네임 캐싱 유틸리티
5. `src/frontend/src/components/__tests__/Header.test.tsx` - 버튼 숨김 테스트 (14 tests)
6. `src/frontend/src/pages/__tests__/HomePage.test.tsx` - 통합 테스트

### Git Commits

**Primary Commits**:

- `8b9c70c` - feat: Add unified signup flow with header button (Scenario 0-4, REQ-F/B-A2-Signup)
- `97fb27c` - Merge pull request #10 for REQ-F-A2-Signup-6 (캐싱 연계)
- `47a8b84` - Refactor: Introduce nickname caching and separate signup logic
- `8c4b5c6` - Feat: Cache nickname in localStorage for persistence

---

## Integration Points

### REQ-F-A2-Signup-1 연계

- Header 컴포넌트가 nickname 상태에 따라 버튼 표시/숨김
- 동일한 조건부 렌더링 로직 공유

### REQ-F-A2-Signup-6 연계

- 가입 완료 시 `setCachedNickname()` 호출
- localStorage에 닉네임 저장 → 즉시 상태 반영

### REQ-F-A2-Profile-Access-1 연계

- 버튼 대신 닉네임 표시
- 상호 배타적 UI (버튼 OR 닉네임)

---

## Notes

- localStorage 캐싱으로 페이지 새로고침 시에도 상태 즉시 반영
- `isLoading` 플래그로 로딩 중 UI 깜빡임 방지
- 조건부 렌더링(`nickname === null`)으로 명확한 상태 분기
- API 호출 없이도 캐시된 값으로 즉시 UI 업데이트
- REQ-F-A2-Signup-1, 6, 7이 함께 통합 가입 플로우를 완성
