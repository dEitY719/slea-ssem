# REQ-F-A2-Profile-Access-3-6 Implementation Progress

**Date**: 2025-11-17
**REQ ID**: REQ-F-A2-Profile-Access-3, REQ-F-A2-Profile-Access-4, REQ-F-A2-Profile-Access-5, REQ-F-A2-Profile-Access-6
**Status**: ✅ Done
**Priority**: M (Must have)

---

## 📋 Phase 1: Specification

### Requirements

**요구사항**:

- **REQ-F-A2-Profile-Access-3**: 닉네임 클릭 시, 드롭다운 메뉴가 닉네임 아래에 표시되어야 한다.
- **REQ-F-A2-Profile-Access-4**: 드롭다운 메뉴에는 다음 항목들이 포함되어야 한다: "프로필 수정" (필수), "로그아웃" (선택, 향후 추가 가능)
- **REQ-F-A2-Profile-Access-5**: 드롭다운 메뉴의 "프로필 수정" 항목 클릭 시, 프로필 수정 페이지(/profile/edit)로 리다이렉트해야 한다.
- **REQ-F-A2-Profile-Access-6**: 드롭다운 메뉴 외부 클릭 시, 메뉴가 자동으로 닫혀야 한다.

**Acceptance Criteria**:

- ✅ 닉네임 클릭 시 드롭다운 메뉴가 표시된다
- ✅ 드롭다운 메뉴가 닉네임 아래에 위치한다
- ✅ 드롭다운 메뉴에 "프로필 수정" 항목이 포함된다
- ✅ "프로필 수정" 클릭 시 /profile/edit로 이동한다
- ✅ 드롭다운 메뉴 외부 클릭 시 메뉴가 자동으로 닫힌다
- ✅ 드롭다운 메뉴 열린 상태에서 닉네임 다시 클릭 시 메뉴가 닫힌다 (토글)
- ✅ 초기 상태에서는 드롭다운이 닫혀 있다

### Implementation Locations

| Component | File Path | Purpose |
|-----------|-----------|---------|
| Header Component | `/workspace/src/frontend/src/components/Header.tsx` | 드롭다운 상태 관리 및 렌더링 |
| Header Styles | `/workspace/src/frontend/src/components/Header.css` | 드롭다운 메뉴 스타일 및 애니메이션 |
| Header Tests | `/workspace/src/frontend/src/components/__tests__/Header.test.tsx` | 6개 테스트 케이스 추가 |

### Behavior Specification

**주요 구현 사항**:

1. **상태 관리 (useState)**:
   - `isDropdownOpen`: 드롭다운 열림/닫힘 상태
   - 초기값: `false` (닫힘)

2. **Ref 관리 (useRef)**:
   - `dropdownRef`: 드롭다운 컨테이너 참조
   - 외부 클릭 감지에 사용

3. **이벤트 핸들러**:
   - `handleNicknameClick()`: 드롭다운 토글 (console.log 제거)
   - `handleEditProfileClick()`: /profile/edit로 이동 + 드롭다운 닫기

4. **외부 클릭 감지 (useEffect)**:
   - `document.addEventListener('click', handleClickOutside)`
   - 드롭다운 외부 클릭 시 `setIsDropdownOpen(false)`
   - cleanup: `removeEventListener`

5. **드롭다운 메뉴 구조**:

   ```tsx
   <div className="profile-menu-container" ref={dropdownRef}>
     <button onClick={handleNicknameClick} aria-expanded={isDropdownOpen}>
       {/* nickname display */}
     </button>
     {isDropdownOpen && (
       <div className="dropdown-menu" role="menu">
         <button onClick={handleEditProfileClick} role="menuitem">
           프로필 수정
         </button>
       </div>
     )}
   </div>
   ```

6. **CSS 애니메이션**:
   - Fade-in: opacity 0 → 1
   - Slide-down: translateY -10px → 0
   - Duration: 0.2s ease

### Dependencies

- **Prerequisite**:
  - REQ-F-A2-Profile-Access-1 (닉네임 표시) ✅
  - REQ-F-A2-Profile-Access-2 (클릭 가능 버튼) ✅
- **React Hooks**: `useState`, `useEffect`, `useRef`
- **React Router**: `useNavigate`
- **Icons**: `PencilSquareIcon` from `@heroicons/react/24/outline`

### Non-functional Requirements

- **성능**: 드롭다운 열기/닫기 < 200ms (CSS 애니메이션)
- **접근성**:
  - `role="menu"` for dropdown
  - `role="menuitem"` for menu items
  - `aria-expanded={isDropdownOpen}` on nickname button
- **반응형**: 모바일/데스크톱 모두 지원
- **브라우저 호환성**: 모던 브라우저

---

## 🧪 Phase 2: Test Design

### Test Cases (6 tests)

1. ✅ **닉네임 클릭 시 드롭다운 메뉴 표시**
   - `screen.getByRole('menu')` 존재 확인

2. ✅ **드롭다운에 "프로필 수정" 항목 포함**
   - `screen.getByRole('menuitem', { name: /프로필 수정/i })` 존재 확인

3. ✅ **"프로필 수정" 클릭 시 /profile/edit로 이동**
   - `mockNavigate('/profile/edit')` 호출 확인

4. ✅ **외부 클릭 시 드롭다운 자동 닫힘**
   - `user.click(document.body)` 후 `screen.queryByRole('menu')` 없음 확인

5. ✅ **닉네임 재클릭 시 드롭다운 닫힘 (토글)**
   - 두 번 클릭 후 `screen.queryByRole('menu')` 없음 확인

6. ✅ **초기 상태에서는 드롭다운 닫힘**
   - 렌더링 직후 `screen.queryByRole('menu')` 없음 확인

### Test Files

- **Test Code**: `/workspace/src/frontend/src/components/__tests__/Header.test.tsx`
- **New describe block**: `describe('Header - REQ-F-A2-Profile-Access-3-6 (Dropdown)', () => { ... })`

---

## ⚙️ Phase 3: Implementation

### Modified Files

#### 1. Header.tsx

**Changes**:

- Import 추가: `useState`, `useEffect`, `useRef`, `PencilSquareIcon`
- State 추가: `isDropdownOpen`, `dropdownRef`
- `handleNicknameClick()` 변경: console.log → 토글 로직
- `handleEditProfileClick()` 추가: navigate + 드롭다운 닫기
- `useEffect` 추가: 외부 클릭 감지
- JSX 변경:
  - `<div className="profile-menu-container">` 래퍼 추가
  - `aria-expanded` 속성 추가
  - 드롭다운 메뉴 조건부 렌더링
- REQ comment 업데이트: REQ-F-A2-Profile-Access-3-6 추가

**Key Code**:

```tsx
const [isDropdownOpen, setIsDropdownOpen] = useState(false)
const dropdownRef = useRef<HTMLDivElement>(null)

const handleNicknameClick = () => {
  setIsDropdownOpen(prev => !prev)
}

const handleEditProfileClick = () => {
  navigate('/profile/edit')
  setIsDropdownOpen(false)
}

useEffect(() => {
  const handleClickOutside = (event: MouseEvent) => {
    if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
      setIsDropdownOpen(false)
    }
  }

  if (isDropdownOpen) {
    document.addEventListener('click', handleClickOutside)
  }

  return () => {
    document.removeEventListener('click', handleClickOutside)
  }
}, [isDropdownOpen])
```

#### 2. Header.css

**Changes**:

- `.profile-menu-container` 추가: `position: relative` (드롭다운 위치 기준)
- `.dropdown-menu` 추가:
  - `position: absolute`, `top: calc(100% + 0.5rem)`, `right: 0`
  - 흰색 배경, 테두리, 그림자
  - `z-index: 1000`
  - `animation: dropdown-fade-in 0.2s ease`
- `@keyframes dropdown-fade-in` 추가:
  - from: `opacity: 0`, `translateY(-10px)`
  - to: `opacity: 1`, `translateY(0)`
- `.dropdown-item` 추가:
  - flex 레이아웃, icon + text
  - hover/active 상태 스타일
  - `transition: background-color 0.15s ease`
- `.dropdown-item .menu-icon` 추가: 아이콘 크기 및 색상

#### 3. Header.test.tsx

**Changes**:

- REQ-F-A2-Profile-Access-2의 "닉네임 클릭 시 이벤트 핸들러" 테스트 수정:
  - console.log spy 제거
  - 드롭다운 표시 확인으로 변경
- 새로운 `describe('Header - REQ-F-A2-Profile-Access-3-6 (Dropdown)', () => { ... })` 블록 추가
- 6개 테스트 케이스 추가

### Test Results

```bash
✓ src/components/__tests__/Header.test.tsx  (24 tests) 489ms

Test Files  1 passed (1)
     Tests  24 passed (24)
  Duration  1.16s
```

**All 24 tests passed! ✅**

- 기존 18개 테스트 (REQ-F-A2-Signup-1, REQ-F-A2-Profile-Access-1, REQ-F-A2-Profile-Access-2) ✅
- 신규 6개 테스트 (REQ-F-A2-Profile-Access-3-6) ✅

**Note**: React `act()` 경고는 있지만 테스트는 모두 통과. userEvent가 내부적으로 상태 업데이트를 처리하므로 기능상 문제 없음.

---

## 📊 REQ Traceability

| REQ | Specification | Test | Implementation |
|-----|---------------|------|----------------|
| REQ-F-A2-Profile-Access-3 | ✅ Phase 1 완료 | ✅ 6 tests 작성 | ✅ Header.tsx/css 수정 |
| - 드롭다운 표시/숨김 | 명세 완료 | test 1, 5, 6 | Header.tsx lines 43-44, 51-54, 120-132 |
| - 토글 기능 | 명세 완료 | test 5 | Header.tsx line 53 (prev => !prev) |
| REQ-F-A2-Profile-Access-4 | ✅ Phase 1 완료 | ✅ test 2 | Header.tsx lines 122-130 |
| - "프로필 수정" 항목 | 명세 완료 | test 2 | Header.tsx lines 122-130 |
| REQ-F-A2-Profile-Access-5 | ✅ Phase 1 완료 | ✅ test 3 | Header.tsx lines 56-60 |
| - /profile/edit 이동 | 명세 완료 | test 3 | Header.tsx line 58 |
| REQ-F-A2-Profile-Access-6 | ✅ Phase 1 완료 | ✅ test 4 | Header.tsx lines 63-77 |
| - 외부 클릭 감지 | 명세 완료 | test 4 | Header.tsx lines 63-77 (useEffect) |

---

## 📝 Implementation Summary

### What Changed

1. **Header Component** (Header.tsx):
   - **State 관리**: `useState`로 드롭다운 열림/닫힘 상태 관리
   - **Ref 관리**: `useRef`로 드롭다운 컨테이너 참조
   - **외부 클릭 감지**: `useEffect`로 document 클릭 이벤트 리스너 등록
   - **토글 로직**: `handleNicknameClick`에서 console.log 제거, 토글 구현
   - **네비게이션**: `handleEditProfileClick`에서 /profile/edit 이동
   - **JSX 구조**: 드롭다운 메뉴 조건부 렌더링
   - **접근성**: `aria-expanded`, `role="menu"`, `role="menuitem"` 추가

2. **Styles** (Header.css):
   - **컨테이너**: `.profile-menu-container` (position: relative)
   - **드롭다운 메뉴**: `.dropdown-menu` (absolute, 애니메이션)
   - **애니메이션**: fade-in + slide-down (0.2s)
   - **메뉴 항목**: `.dropdown-item` (hover/active 효과)
   - **아이콘 스타일**: `.menu-icon` (크기 및 색상)

3. **Tests** (Header.test.tsx):
   - 6개 테스트 케이스 추가 (드롭다운 기능 전체)
   - 기존 테스트 1개 수정 (console.log → 드롭다운 확인)
   - 기존 18개 + 신규 6개 = 총 24개 테스트 통과

### Why These Changes

- **REQ-F-A2-Profile-Access-3-6** 요구사항 충족
- 사용자에게 프로필 관련 기능 그룹화된 메뉴 제공
- 직관적인 드롭다운 UI/UX 패턴 구현
- 향후 로그아웃, 설정 등 추가 기능 확장 가능한 구조
- 접근성 강화 (키보드 사용자, 스크린 리더 사용자)

### Validation Evidence

- ✅ 24/24 테스트 통과 (100%)
- ✅ 모든 acceptance criteria 충족
- ✅ Non-breaking change (기존 기능 유지)
- ✅ 드롭다운 애니메이션 구현 (fade-in + slide-down)
- ✅ 외부 클릭 감지 정상 작동
- ✅ 토글 기능 정상 작동
- ✅ 접근성 속성 추가 (aria-expanded, role)

---

## 🔗 Related Requirements

- **Prerequisite**:
  - REQ-F-A2-Profile-Access-1 (닉네임 표시) ✅ Done
  - REQ-F-A2-Profile-Access-2 (클릭 가능 버튼) ✅ Done
- **Current**:
  - REQ-F-A2-Profile-Access-3 (드롭다운 표시) ✅ Done
  - REQ-F-A2-Profile-Access-4 ("프로필 수정" 항목) ✅ Done
  - REQ-F-A2-Profile-Access-5 (/profile/edit 이동) ✅ Done
  - REQ-F-A2-Profile-Access-6 (외부 클릭 닫기) ✅ Done
- **Next**:
  - REQ-F-A2-Profile-Access-7 (상호 배타성 - 이미 구현됨)
  - REQ-F-A2-Profile-Access-8 (전역 헤더 - 이미 구현됨)
  - 향후: 드롭다운에 "로그아웃" 항목 추가 가능

---

## 📦 Git Commit

**Branch**: `cursor/implement-profile-access-feature-34a6`

**Commit Message**:

```
feat: Implement REQ-F-A2-Profile-Access-3-6 - Add dropdown menu to nickname

- Add dropdown menu toggle on nickname click
- Implement "프로필 수정" menu item with navigation to /profile/edit
- Add outside click detection to close dropdown (useEffect + useRef)
- Add dropdown animations (fade-in + slide-down)
- Add accessibility attributes (aria-expanded, role="menu", role="menuitem")
- Add 6 test cases covering dropdown behavior
- Update 1 existing test (console.log → dropdown display)

Technical changes:
- Header.tsx: Add useState (isDropdownOpen), useRef (dropdownRef), useEffect (outside click)
- Header.tsx: Add handleEditProfileClick(), update handleNicknameClick() (toggle)
- Header.css: Add .profile-menu-container, .dropdown-menu, .dropdown-item styles
- Header.css: Add dropdown-fade-in animation (0.2s ease)
- Header.test.tsx: Add 6 tests in new describe block, update 1 existing test

Test Results:
- All 24 tests passed (18 existing + 6 new)
- 100% coverage of acceptance criteria

REQ: REQ-F-A2-Profile-Access-3, REQ-F-A2-Profile-Access-4, REQ-F-A2-Profile-Access-5, REQ-F-A2-Profile-Access-6
Priority: M (Must have)
Tests: 24 passed (24)
Files: Header.tsx, Header.css, Header.test.tsx, DEV-PROGRESS.md, REQ-F-A2-Profile-Access-3-6.md

Next: Add "로그아웃" menu item (optional, future enhancement)

🤖 Generated with OpenAI Codex
```

**Modified Files**:

- `src/frontend/src/components/Header.tsx`
- `src/frontend/src/components/Header.css`
- `src/frontend/src/components/__tests__/Header.test.tsx`

---

## ✅ Completion Checklist

- [x] Phase 1: Specification 작성 및 승인
- [x] Phase 2: Test Design 작성 및 승인 (6개 테스트)
- [x] Phase 3: Implementation 완료
- [x] Phase 4: Progress 문서 작성
- [x] All tests passing (24/24)
- [x] Code review self-check
- [x] REQ traceability 확인
- [x] Git commit 준비

**Status**: ✅ **DONE**

---

## 🎯 Next Steps

1. **(Optional)** Add "로그아웃" menu item to dropdown
2. **(Optional)** Add ESC key support to close dropdown
3. **(Optional)** Add more menu items (설정, 알림 등)
4. Continue with other MVP 1.0 requirements

---

## 💡 Implementation Notes

### Dropdown Animation

- CSS `@keyframes` 사용으로 GPU 가속 활용
- `transform` + `opacity` 조합으로 부드러운 애니메이션
- Duration 0.2s는 사용자 경험상 최적값

### Outside Click Detection

- `useEffect` + `addEventListener`로 구현
- `useRef`로 드롭다운 영역 참조하여 내부/외부 클릭 구분
- cleanup 함수로 메모리 누수 방지

### Future Enhancements

- ESC 키 지원 (현재는 테스트에서 제외)
- 키보드 네비게이션 (↑↓ 키로 메뉴 항목 이동)
- 드롭다운 위치 자동 조정 (화면 밖으로 나가는 경우)
- "로그아웃" 메뉴 항목 추가
