# REQ-F-A2-Edit-1: 프로필 수정 메뉴 진입점

**Feature**: Profile review screen entry point for editing profile  
**Developer**: youkyoung kim (Cursor IDE)  
**Status**: ✅ Phase 4 Complete  
**Date**: 2025-11-12  
**Priority**: M (Must)

---

## 📋 Phase 1: Specification

### Requirements & Acceptance Criteria

- Provide an explicit action in the profile flow that lets users return to the profile editing experience (docs/feature_requirement_mvp1.md, REQ-F-A2-Edit-1).
- Surface the option alongside current profile context (nickname + level) so users understand what will be edited.
- Triggering the action must navigate to the self-assessment/profile edit form without a full page reload.
- The option should remain accessible immediately after profile review so users can make corrections before starting the test.

### UX Flow

1. 사용자가 자기평가 제출을 완료하면 `/profile-review` 페이지로 이동한다.
2. 리뷰 페이지 상단에서 현재 닉네임과 수준을 확인할 수 있고, 안내 문구로 수정 가능함을 알린다.
3. `수정하기` 버튼을 누르면 `/self-assessment`로 이동하여 프로필을 즉시 수정할 수 있다.
4. 수정이 필요 없다면 `시작하기` 버튼으로 홈/대시보드로 이동한다.

### Implementation Scope

- `src/frontend/src/pages/ProfileReviewPage.tsx`: Fetch nickname, show profile summary, expose `수정하기` CTA, wire navigation to `/self-assessment`.
- `src/frontend/src/pages/ProfileReviewPage.css`: 스타일링 (카드 레이아웃, 버튼 그룹, 안내 문구).
- `src/frontend/src/pages/__tests__/ProfileReviewPage.test.tsx`: UI 및 네비게이션 테스트 8건.
- `src/frontend/src/App.tsx`: `/profile-review` 라우트 등록.

### Dependencies

- `react-router-dom` `useNavigate` / `useLocation`.
- `transport.get('/profile/nickname')` for nickname hydration (existing mock & backend endpoint).
- Existing SelfAssessment flow (`/self-assessment`) handles the actual editing.

### Non-Functional Notes

- Navigation happens client-side (<1s) and reuses existing router state.
- Copy 및 버튼 레이블은 한국어로 통일, 접근성 위해 버튼에 `type="button"` 지정.
- 로딩/에러 상태 포함하여 실패 시 명확한 피드백 제공.

---

## 🧪 Phase 2: Test Design

### Target Suites

- `src/frontend/src/pages/__tests__/ProfileReviewPage.test.tsx`
  - Renders profile review page with both buttons visible (happy path).
  - Verifies nickname fetch occurs on mount.
  - Confirms `수정하기` 클릭 시 `/self-assessment`으로 네비게이트 (**REQ 핵심 검증**).
  - Ensures `시작하기` 클릭 시 홈으로 이동 (complementary flow).
  - Covers 로딩 및 에러 상태 표시.
- Supporting suite: `SelfAssessmentPage.test.tsx` (이미 존재) - profile review 페이지 진입 자체가 정상 동작하는지 검증.

### Coverage Summary

- 8 Vitest cases on ProfileReviewPage (navigation, data fetch, state handling).
- 10 Vitest cases on SelfAssessmentPage (submission → profile review 전환).
- Focused assertion ensures edit option is always visible and functional.

---

## 💻 Phase 3: Implementation Highlights

### Profile Review Page – Edit CTA & Navigation

```74:128:src/frontend/src/pages/ProfileReviewPage.tsx
  const handleEditClick = useCallback(() => {
    navigate('/self-assessment')
  }, [navigate])

  // ... existing code ...

          <button
            type="button"
            className="edit-button"
            onClick={handleEditClick}
          >
            수정하기
          </button>
```

### Vitest – Ensuring Edit Button Navigates to Editor

```133:152:src/frontend/src/pages/__tests__/ProfileReviewPage.test.tsx
test('navigates back to /self-assessment when "수정하기" button is clicked', async () => {
  // ... existing code ...
  const editButton = screen.getByRole('button', { name: /수정하기/i })
  await user.click(editButton)

  expect(mockNavigate).toHaveBeenCalledWith('/self-assessment')
})
```

### Router Exposure

```14:20:src/frontend/src/App.tsx
        <Route path="/nickname-setup" element={<NicknameSetupPage />} />
        <Route path="/self-assessment" element={<SelfAssessmentPage />} />
        <Route path="/profile-review" element={<ProfileReviewPage />} />
```

---

## ✅ Phase 4: Summary & Traceability

### Test Results

```
✓ src/pages/__tests__/ProfileReviewPage.test.tsx (8 tests)
✓ src/pages/__tests__/SelfAssessmentPage.test.tsx (10 tests)
```

### Traceability Matrix

| REQ | Implementation | Test Coverage | Status |
|-----|----------------|---------------|--------|
| REQ-F-A2-Edit-1 | Profile review page exposes `수정하기` CTA returning to edit flow | `ProfileReviewPage.test.tsx::test('navigates back to /self-assessment…')` | ✅ |
| REQ-F-A2-Edit-1 | Current nickname + 안내 문구로 수정 컨텍스트 표시 | `ProfileReviewPage.tsx` render section (lines 103-138) | ✅ |
| REQ-F-A2-Edit-1 | Routing wired so edit option is accessible post-review | `App.tsx` route + `SelfAssessmentPage` redirect | ✅ |

### Files Touched

- `src/frontend/src/pages/ProfileReviewPage.tsx`
- `src/frontend/src/pages/ProfileReviewPage.css`
- `src/frontend/src/pages/__tests__/ProfileReviewPage.test.tsx`
- `src/frontend/src/App.tsx`
- `src/frontend/src/pages/SelfAssessmentPage.tsx` (flow integration)
- `src/frontend/src/lib/transport/mockTransport.ts` (profile endpoints mocked)

### Git Reference

```
commit d401eedf0fda39555dc89c82376e23fd2d9bef1c
Author: youkyoung kim <jeane2003@naver.com>
Date:   2025-11-12

    update REQ-F-A2-2-4

    - Introduce profile review page with edit CTA
    - Wire navigation back to self-assessment for profile editing
    - Add comprehensive Vitest coverage for review buttons
```

---

## 📝 Notes & Next Steps

- Copy currently 표기된 버튼 레이블은 `수정하기`; 향후 `프로필 수정` 텍스트로 변경할지 UI 리뷰 필요.
- Profile review는 닉네임과 수준만 노출 → REQ-F-A2-Edit-5 이후 경력/관심분야까지 확장 예정.
- Consider global header 진입점 추가 (대시보드 상단) once dashboard skeleton lands.
