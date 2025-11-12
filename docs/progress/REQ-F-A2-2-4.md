# REQ-F-A2-2-4 Progress Report

**Feature**: 자기평가 완료 시 프로필 저장 및 리뷰 화면 이동  
**Developer**: youkyoung kim (Cursor IDE)  
**Status**: ✅ Phase 4 Complete  
**Date**: 2025-11-12

---

## Phase 1: Specification

### Requirements

- **REQ ID**: REQ-F-A2-2-4
- **Description**: "완료" 버튼 클릭 시 자기평가 정보를 `user_profile`(survey) API로 저장하고 프로필 리뷰 페이지로 리다이렉트한다.
- **Priority**: M (Must)

### Acceptance Criteria

- "완료" 버튼을 클릭하면 `PUT /profile/survey` 호출에 성공해야 한다.
- 응답이 성공하면 `/profile-review` 페이지로 이동한다(브라우저 히스토리 교체 및 선택한 level 전달).
- 실패 시 오류 메시지를 사용자에게 표시하고 현재 페이지에 유지한다.
- 프로필 리뷰 페이지는 닉네임 정보를 불러오고(없을 경우 "정보 없음"), 전달받은 level을 한국어 표현으로 보여준다.
- "시작하기" 클릭 시 홈(`/home`), "수정하기" 클릭 시 자기평가(`/self-assessment`)로 이동한다.

### Technical Specification

- **API Integration**: `transport.put('/profile/survey', { level })`로 저장 후 성공 시 `navigate('/profile-review', { replace: true, state: { level } })`.
- **Review Page 데이터**: `ProfileReviewPage.tsx`에서 `transport.get('/profile/nickname')` 호출로 닉네임을 로드하고, `useLocation()` 상태로 level 표시.
- **Routing**: `App.tsx`에 `/profile-review` 라우트를 추가하여 새 페이지를 노출.
- **Mock Support**: `mockTransport`에 `/profile/survey` PUT 처리 및 `/profile/nickname` GET 응답을 정의해 Vitest에서 일관된 결과를 보장.

### Files Updated

- `src/frontend/src/pages/SelfAssessmentPage.tsx`
- `src/frontend/src/pages/ProfileReviewPage.tsx`
- `src/frontend/src/pages/ProfileReviewPage.css`
- `src/frontend/src/pages/__tests__/SelfAssessmentPage.test.tsx`
- `src/frontend/src/pages/__tests__/ProfileReviewPage.test.tsx`
- `src/frontend/src/App.tsx`
- `src/frontend/src/lib/transport/mockTransport.ts`

---

## Phase 2: Test Design

### Test Cases (6 key scenarios)

1. ✅ `SelfAssessmentPage` — navigates to profile review page after successful submission
2. ✅ `SelfAssessmentPage` — shows error message when API call fails
3. ✅ `ProfileReviewPage` — fetches and displays user nickname on mount
4. ✅ `ProfileReviewPage` — displays level information passed via navigation state
5. ✅ `ProfileReviewPage` — "시작하기" 버튼 클릭 시 `/home` 으로 이동
6. ✅ `ProfileReviewPage` — "수정하기" 버튼 클릭 시 `/self-assessment` 으로 이동

**Additional Coverage**:

- 로딩 상태 및 오류 메시지 표시 검증 2건
- 레벨 텍스트 변환 로직 검증 1건
- 전체 Vitest 스위트: `SelfAssessmentPage.test.tsx` 10건, `ProfileReviewPage.test.tsx` 8건

---

## Phase 3: Implementation

### SelfAssessmentPage → API 저장 및 라우팅

자기평가 제출 시 `PUT /profile/survey` 요청을 보낸 뒤 성공하면 리뷰 페이지로 이동하며, 선택한 level을 `location.state`에 담아 전달한다.

```60:86:src/frontend/src/pages/SelfAssessmentPage.tsx
const handleCompleteClick = useCallback(async () => {
  if (level === null || isSubmitting) {
    return
  }

  setIsSubmitting(true)
  setErrorMessage(null)

  try {
    const backendLevel = convertLevelToBackend(level)
    await transport.put('/profile/survey', {
      level: backendLevel,
    })

    setIsSubmitting(false)
    navigate('/profile-review', { replace: true, state: { level } })
  } catch (error) {
    const message =
      error instanceof Error ? error.message : '자기평가 정보 저장에 실패했습니다.'
    setErrorMessage(message)
    setIsSubmitting(false)
  }
}, [level, isSubmitting, navigate])
```

### ProfileReviewPage → 닉네임 로드 및 버튼 동작

프로필 리뷰 페이지는 진입 시 닉네임을 비동기로 로드하고, 전달받은 level 숫자를 한국어 문자열로 변환해 표시한다. 버튼 클릭에 따라 홈 또는 자기평가 페이지로 라우팅한다.

```47:137:src/frontend/src/pages/ProfileReviewPage.tsx
useEffect(() => {
  const fetchNickname = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await transport.get<NicknameResponse>('/profile/nickname')
      setNickname(response.nickname)
    } catch (err) {
      const message =
        err instanceof Error ? err.message : '닉네임 정보를 불러오는데 실패했습니다.'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  fetchNickname()
}, [])

const handleStartClick = useCallback(() => {
  navigate('/home', { replace: true })
}, [navigate])

const handleEditClick = useCallback(() => {
  navigate('/self-assessment')
}, [navigate])
```

### UI/Mock 보조 구성요소

- `ProfileReviewPage.css`: 리뷰 카드, 버튼 그룹, 로딩/오류 메시지 스타일 정의
- `mockTransport.ts`: `/profile/survey` 요청 시 유효성 검사 및 모의 응답 생성, `/profile/nickname` GET 응답 제공
- `App.tsx`: `/profile-review` 라우트 등록으로 네비게이션 가능

---

## Phase 4: Summary & Traceability

### Test Results

```
✓ src/pages/__tests__/SelfAssessmentPage.test.tsx (10 tests)
  ✓ navigates to profile review page after successful submission
  ✓ shows error message when API call fails
  ✓ disables complete button while submitting

✓ src/pages/__tests__/ProfileReviewPage.test.tsx (8 tests)
  ✓ renders page with title, description, and buttons
  ✓ fetches and displays user nickname on mount
  ✓ displays level information passed via navigation state
  ✓ navigates to /home when "시작하기" 버튼 클릭
  ✓ navigates back to /self-assessment when "수정하기" 버튼 클릭
  ✓ shows loading state while fetching nickname
  ✓ shows error message if nickname fetch fails
```

### Requirements → Implementation Mapping

| REQ | Implementation | Test Coverage |
|-----|----------------|---------------|
| REQ-F-A2-2-4 | `SelfAssessmentPage.tsx`: `transport.put` 호출 및 `/profile-review` 이동 | `SelfAssessmentPage.test.tsx`: tests 187, 212, 243 |
| REQ-F-A2-2-4 | `ProfileReviewPage.tsx`: 닉네임 로드, level 표시, 버튼 네비게이션 | `ProfileReviewPage.test.tsx`: tests 41-187 |
| REQ-F-A2-2-4 | `App.tsx`, `mockTransport.ts`: 라우팅/모의 API 구성 | 통합: 위 두 테스트 파일 전체 |

### Modified Files

1. `src/frontend/src/pages/SelfAssessmentPage.tsx` - API 연동 및 리뷰 페이지 네비게이션
2. `src/frontend/src/pages/ProfileReviewPage.tsx` - 신규 리뷰 화면 구성
3. `src/frontend/src/pages/ProfileReviewPage.css` - 리뷰 UI 스타일
4. `src/frontend/src/pages/__tests__/SelfAssessmentPage.test.tsx` - 성공/실패 플로우 테스트 추가
5. `src/frontend/src/pages/__tests__/ProfileReviewPage.test.tsx` - 리뷰 페이지 기능 테스트 8건
6. `src/frontend/src/App.tsx` - `/profile-review` 라우트 등록
7. `src/frontend/src/lib/transport/mockTransport.ts` - 프로필 관련 모의 응답 확장

### Git Commit

```
update REQ-F-A2-2-4

- Add profile review page with nickname fetch and level summary
- Wire self-assessment completion to survey API + redirect
- Extend mock transport and router configuration for new flow
- Add comprehensive vitest coverage for review page interactions

Commit SHA: d401eed
```

---

## Next Steps

- [ ] 자기평가 입력에서 추가 필드(경력, 직군 등)를 저장하도록 요청 페이로드 확장
- [ ] 프로필 리뷰 페이지에서 저장된 다른 프로필 속성(경력, 관심분야 등)도 표시
- [ ] E2E 테스트로 자기평가 → 리뷰 → 홈 이동 플로우 검증

---

## Notes

- 현재는 `level`만 전달하지만, `navigate`에 객체를 전달하는 구조로 확장성을 확보했다.
- `replace: true`를 사용해 리뷰 페이지에서 뒤로가기 시 이전 단계로 돌아가지 않도록 UX를 정교화했다.
- Mock 환경에서도 동일한 플로우를 검증할 수 있도록 `/profile/survey` 유효성 검사를 구성했다.
