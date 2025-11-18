# REQ-F-A2-Signup-6 Progress Report

**Feature**: "가입 완료" 버튼 클릭 시 nickname + user_profile 저장 및 홈화면 리다이렉트
**Developer**: youkyoung kim (Cursor IDE)
**Status**: ✅ Phase 4 Complete
**Date**: 2025-11-17

---

## Phase 1: Specification

### Requirements

- **REQ ID**: REQ-F-A2-Signup-6
- **Description**: "가입 완료" 버튼 클릭 시, users.nickname 업데이트 + user_profile 저장을 동시에 수행하고, 홈화면으로 리다이렉트해야 한다.
- **Priority**: M (Must)

### Acceptance Criteria

- "가입 완료" 버튼 클릭 시 nickname이 저장된다 (registerNickname API)
- "가입 완료" 버튼 클릭 시 user_profile이 저장된다 (updateSurvey API)
- LEVEL_MAPPING을 통해 UI level (1-5)을 backend level로 변환한다
- 두 API 호출이 모두 성공하면 `/home`으로 리다이렉트한다
- 리다이렉트는 `replace: true`로 브라우저 히스토리를 교체한다
- 닉네임을 localStorage에 캐싱한다 (재방문 지원)
- API 실패 시 에러 메시지를 표시하고 재시도할 수 있다

### Technical Specification

- **API Calls**:
  1. `profileService.registerNickname(nickname)` - 닉네임 등록
  2. `profileService.updateSurvey({ level, career, interests })` - 프로필 저장
- **Level Mapping**: UI level (1-5) → Backend level (beginner/intermediate/advanced)
  - Level 1 → beginner
  - Level 2, 3 → intermediate
  - Level 4, 5 → advanced
- **Navigation**: `navigate('/home', { replace: true })`
- **Caching**: `setCachedNickname(nickname)` - localStorage에 닉네임 저장
- **Error Handling**: 실패 시 에러 메시지 표시, 버튼 재활성화

---

## Phase 2: Test Design

### Test Cases (REQ-F-A2-Signup-6 직접 관련 - 5개)

1. ✅ `submits nickname and profile, then redirects to home on success` - 성공 플로우
2. ✅ `successfully completes signup with level 5` - 다른 레벨로 가입
3. ✅ `shows loading state during submission` - 제출 중 로딩 상태
4. ✅ `shows error message when nickname registration fails` - 닉네임 등록 실패
5. ✅ `shows error message when API fails` - API 에러 처리

### Test File

- **Location**: `src/frontend/src/pages/__tests__/SignupPage.test.tsx`
- **Test Section**: `describe('SignupPage - REQ-F-A2-Signup-6')` (lines 527-701)

### Key Test Verification

```typescript
// Line 534-572: REQ-F-A2-Signup-6 핵심 테스트
test('submits nickname and profile, then redirects to home on success', async () => {
  // 1. 닉네임 입력 및 중복 확인
  await user.type(nicknameInput, 'signup_user1')
  await user.click(checkButton)
  await waitFor(() => {
    expect(screen.getByText(/사용 가능한 닉네임입니다/i)).toBeInTheDocument()
  })

  // 2. 레벨 선택
  await user.click(level3Radio)

  // 3. "가입 완료" 버튼 클릭
  await user.click(submitButton)

  // 4. 리다이렉트 검증
  await waitFor(() => {
    expect(mockNavigate).toHaveBeenCalledWith('/home', { replace: true })
  })

  // 5. API 호출 검증
  expect(getMockRequests({ url: '/api/profile/register', method: 'POST' })).toHaveLength(1)
  expect(getMockRequests({ url: '/api/profile/survey', method: 'PUT' })).toHaveLength(1)

  // 6. 캐싱 검증
  expect(localStorage.getItem('slea_ssem_cached_nickname')).toBe('signup_user1')
})
```

---

## Phase 3: Implementation

### Core Implementation

**File**: `src/frontend/src/pages/SignupPage.tsx`
**Lines**: 63-83

```typescript
// REQ-F-A2-Signup-6: Submit handler
const handleSubmit = useCallback(async () => {
  if (isSubmitDisabled || isSubmitting) return

  setIsSubmitting(true)
  setSubmitError(null)

  try {
    // nickname + profile 동시 저장
    await completeProfileSignup({
      nickname,
      level: level!,
    })

    // 홈화면으로 리다이렉트
    navigate('/home', { replace: true })
  } catch (error) {
    const message =
      error instanceof Error ? error.message : '가입 완료에 실패했습니다.'
    setSubmitError(message)
    setIsSubmitting(false)
  }
}, [nickname, level, isSubmitting, isSubmitDisabled, navigate])
```

### Profile Submission Logic

**File**: `src/frontend/src/features/profile/profileSubmission.ts`
**Lines**: 42-51

```typescript
export async function completeProfileSignup(input: CompleteSignupInput) {
  // 1. 닉네임 등록
  await profileService.registerNickname(input.nickname)

  // 2. 프로필 저장 (LEVEL_MAPPING 적용)
  const surveyResult = await submitProfileSurvey(input)

  // 3. 닉네임 캐싱
  setCachedNickname(input.nickname)

  return {
    nickname: input.nickname,
    surveyId: surveyResult.surveyId,
  }
}
```

### UI Components

**File**: `src/frontend/src/pages/SignupPage.tsx`
**Lines**: 122-135

```tsx
{/* REQ-F-A2-Signup-6: Submit Button */}
<div className="form-actions">
  {submitError && (
    <p className="submit-error-message">{submitError}</p>
  )}
  <button
    type="button"
    className="submit-button"
    disabled={isSubmitDisabled}
    onClick={handleSubmit}
  >
    {isSubmitting ? '가입 중...' : '가입 완료'}
  </button>
</div>
```

---

## Phase 4: Summary & Traceability

### Test Results

```
✓ src/pages/__tests__/SignupPage.test.tsx (32 tests)
  REQ-F-A2-Signup-6 (Signup Submission) - 5 tests
  ✓ submits nickname and profile, then redirects to home on success
  ✓ successfully completes signup with level 5
  ✓ shows loading state during submission
  ✓ shows error message when nickname registration fails
  ✓ shows error message when API fails
```

### Requirements → Implementation Mapping

| REQ | Implementation | Test Coverage |
|-----|----------------|---------------|
| REQ-F-A2-Signup-6 | `SignupPage.tsx:63-83` - handleSubmit 함수 | `SignupPage.test.tsx:534-572` (성공 플로우) |
| REQ-F-A2-Signup-6 | `profileSubmission.ts:42-51` - completeProfileSignup | `SignupPage.test.tsx:574-605` (레벨별 테스트) |
| REQ-F-A2-Signup-6 | `navigate('/home', { replace: true })` | `SignupPage.test.tsx:559-561` (리다이렉트 검증) |
| REQ-F-A2-Signup-6 | `setCachedNickname()` - localStorage 캐싱 | `SignupPage.test.tsx:571` (캐싱 검증) |

### Modified Files

1. `src/frontend/src/pages/SignupPage.tsx` - 제출 핸들러 및 UI (lines 63-83, 122-135)
2. `src/frontend/src/features/profile/profileSubmission.ts` - completeProfileSignup 함수
3. `src/frontend/src/pages/__tests__/SignupPage.test.tsx` - 제출 테스트 5개 (lines 527-701)
4. `src/frontend/src/services/profileService.ts` - API 서비스 메서드
5. `src/frontend/src/utils/nicknameCache.ts` - 닉네임 캐싱 유틸리티

### Git Commits

**Primary Commits**:

- `97fb27c` - Merge pull request #10 for REQ-F-A2-Signup-6 (최종 병합)
- `156298b` - Fix: Redirect to /home after signup instead of / (리다이렉트 수정)
- `47a8b84` - Refactor: Introduce nickname caching and separate signup logic (캐싱 및 로직 분리)

---

## Integration Points

### REQ-F-A2-Signup-5 연계

- Submit 버튼 활성화 조건: `checkStatus === 'available' && level !== null`
- REQ-F-A2-Signup-5에서 활성화된 버튼을 REQ-F-A2-Signup-6에서 클릭

### REQ-F-A2-Signup-7 연계

- 가입 완료 후 닉네임이 localStorage에 캐싱됨
- HomePage에서 캐싱된 닉네임을 읽어 "회원가입" 버튼 숨김 처리

### API 통합

- `POST /api/profile/register` - 닉네임 등록
- `PUT /api/profile/survey` - 프로필 저장
- 두 API가 순차적으로 호출되어 트랜잭션 일관성 보장

---

## Notes

- `replace: true` 옵션으로 가입 후 뒤로가기 방지
- 닉네임 캐싱으로 헤더 상태 즉시 업데이트 (REQ-F-A2-Signup-7 지원)
- 에러 발생 시 버튼 재활성화로 사용자 재시도 가능
- LEVEL_MAPPING 중앙화로 레벨 변환 로직 일관성 유지
- Mock 환경에서도 실제 API 플로우와 동일하게 테스트 가능
