# REQ-F-A2-2-5 Progress Report

**Feature**: "완료" 버튼 클릭 시 user_profile 저장 및 프로필 리뷰 페이지 리다이렉트
**Developer**: youkyoung kim (Cursor IDE)
**Status**: ✅ Phase 4 Complete
**Date**: 2025-11-17

---

## Phase 1: Specification

### Requirements

- **REQ ID**: REQ-F-A2-2-5
- **Description**: "완료" 버튼 클릭 시, user_profile 테이블에 저장하고 프로필 리뷰 페이지로 리다이렉트해야 한다.
- **Priority**: M (Must)

### Acceptance Criteria

- "완료" 버튼 클릭 시 자기평가 정보가 API를 통해 저장된다.
- 저장 성공 시 `/profile-review` 페이지로 자동 이동한다.
- 이동 시 선택한 level과 surveyId를 navigation state로 전달한다.
- 리다이렉트는 `replace: true`로 브라우저 히스토리를 교체한다.
- 프로필 리뷰 페이지에서 저장된 정보를 확인할 수 있다.

### Technical Specification

- **API Call**: `submitProfileSurvey({ level })` 호출하여 user_profile 저장
- **Navigation**: `navigate('/profile-review', { replace: true, state: { level, surveyId } })`
- **Error Handling**: 저장 실패 시 에러 메시지 표시, 페이지 이동 없음
- **Loading State**: 제출 중 버튼 비활성화 및 "제출 중..." 표시
- **Data Persistence**: localStorage에 surveyId와 level 캐싱 (재방문 지원)

---

## Phase 2: Test Design

### Test Cases (Directly Related to REQ-F-A2-2-5)

1. ✅ `navigates to profile review page after successful submission` - 성공적인 저장 후 리다이렉트
2. ✅ `shows error message when API call fails` - API 실패 시 에러 메시지 표시
3. ✅ `disables complete button while submitting` - 제출 중 버튼 비활성화

### Test File

- **Location**: `src/frontend/src/pages/__tests__/SelfAssessmentPage.test.tsx`
- **Test Lines**: 161-184 (주요 리다이렉트 테스트)

### Key Test Verification

```typescript
// Line 161-184: REQ-F-A2-2-5 핵심 테스트
test('navigates to profile review page after successful submission', async () => {
  // 1. Level 선택
  await user.click(level3Radio)

  // 2. "완료" 버튼 클릭
  await user.click(completeButton)

  // 3. 저장 성공 후 리다이렉트 검증
  await waitFor(() => {
    expect(mockNavigate).toHaveBeenCalledWith(
      '/profile-review',
      expect.objectContaining({
        replace: true,
        state: expect.objectContaining({
          level: 3,
          surveyId: expect.any(String),
        }),
      })
    )
  })
})
```

---

## Phase 3: Implementation

### Core Implementation (SelfAssessmentPage.tsx)

**File**: `src/frontend/src/pages/SelfAssessmentPage.tsx`
**Lines**: 40-62

```typescript
const handleCompleteClick = useCallback(async () => {
  if (level === null || isSubmitting) {
    return
  }

  setIsSubmitting(true)
  setErrorMessage(null)

  try {
    // REQ-F-A2-2-5: user_profile 저장
    const response = await submitProfileSurvey({ level })

    setIsSubmitting(false)
    // REQ-F-A2-2-5: 프로필 리뷰 페이지로 리다이렉트
    navigate('/profile-review', {
      replace: true,
      state: { level, surveyId: response.surveyId },
    })
  } catch (error) {
    const message =
      error instanceof Error ? error.message : '자기평가 정보 저장에 실패했습니다.'
    setErrorMessage(message)
    setIsSubmitting(false)
  }
}, [level, isSubmitting, navigate])
```

### Redirect Target (ProfileReviewPage.tsx)

**File**: `src/frontend/src/pages/ProfileReviewPage.tsx`

- Level 정보 표시 (lines 40-48: `getLevelText()`)
- SurveyId 캐싱 (lines 63-85: localStorage 저장)
- 닉네임 API 조회 (lines 87-119)
- 테스트 시작 버튼 연동 (lines 121-146)

### Data Flow

1. User clicks "완료" button
2. `submitProfileSurvey({ level })` → API 호출 → user_profile 저장
3. Response에서 surveyId 수신
4. `navigate('/profile-review')` → state에 { level, surveyId } 전달
5. ProfileReviewPage에서 정보 표시 및 localStorage 캐싱

---

## Phase 4: Summary & Traceability

### Test Results

```
✓ src/pages/__tests__/SelfAssessmentPage.test.tsx (10 tests)
  ✓ renders level selection with 5 options and complete button
  ✓ keeps complete button disabled when no level is selected
  ✓ enables complete button after selecting a level
  ✓ converts level 1 to "beginner" when submitting
  ✓ converts level 2 and 3 to "intermediate" when submitting
  ✓ converts level 4 and 5 to "advanced" when submitting
  ✓ navigates to profile review page after successful submission  ← REQ-F-A2-2-5
  ✓ shows error message when API call fails  ← REQ-F-A2-2-5
  ✓ shows description for each level (1-5)
  ✓ disables complete button while submitting  ← REQ-F-A2-2-5
```

### Requirements → Implementation Mapping

| REQ | Implementation | Test Coverage |
|-----|----------------|---------------|
| REQ-F-A2-2-5 | `SelfAssessmentPage.tsx:40-62` - `submitProfileSurvey` 호출 및 `/profile-review` 리다이렉트 | `SelfAssessmentPage.test.tsx:161-184` |
| REQ-F-A2-2-5 | `ProfileReviewPage.tsx:63-85` - surveyId/level 캐싱 | `ProfileReviewPage.test.tsx` (8 tests) |
| REQ-F-A2-2-5 | `profileSubmission.ts` - API 통합 및 LEVEL_MAPPING | `SelfAssessmentPage.test.tsx:81-159` |

### Modified Files

1. `src/frontend/src/pages/SelfAssessmentPage.tsx` - 완료 버튼 클릭 핸들러 및 리다이렉트 로직
2. `src/frontend/src/pages/ProfileReviewPage.tsx` - 리다이렉트 대상 페이지, state 수신 및 표시
3. `src/frontend/src/pages/__tests__/SelfAssessmentPage.test.tsx` - 저장 및 리다이렉트 테스트
4. `src/frontend/src/features/profile/profileSubmission.ts` - API 저장 로직
5. `src/frontend/src/lib/transport/mockTransport.ts` - 테스트용 mock API 응답

### Git Commit

**Primary Commits**:

- `8a06b74` - feat: Add self-assessment completion and profile review (초기 구현)
- `2661b60` - Refactor: Improve profile survey and navigation logic (리팩토링 및 개선)
- `aa04368` - Feat: Cache and display survey level on profile review page (캐싱 추가)
- `8c4b5c6` - Feat: Cache nickname in localStorage for persistence (닉네임 캐싱)

---

## Relationship to REQ-F-A2-2-4

REQ-F-A2-2-5는 REQ-F-A2-2-4의 직접적인 연장선입니다:

- **REQ-F-A2-2-4**: "완료" 버튼이 모든 필수 필드 입력 시 활성화
- **REQ-F-A2-2-5**: "완료" 버튼 클릭 시 저장 및 리다이렉트 **(현재 문서)**

두 요구사항 모두 동일한 코드베이스(`SelfAssessmentPage.tsx`, `ProfileReviewPage.tsx`)에서 구현되었으며, 같은 커밋들로 완료되었습니다.

---

## Notes

- REQ-F-A2-2-4와 REQ-F-A2-2-5는 동일한 기능 플로우의 일부로 함께 구현됨
- `replace: true` 옵션으로 브라우저 뒤로가기 시 이전 단계로 돌아가지 않도록 UX 개선
- localStorage 캐싱으로 페이지 새로고침 시에도 정보 유지
- Mock 환경에서도 실제 API 플로우와 동일하게 동작하도록 구현
