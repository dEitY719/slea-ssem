# REQ-F-A2-2-3 Progress Report

**Feature**: 자기평가 필수 입력 완료 시 "완료" 버튼 활성화  
**Developer**: youkyoung kim (Cursor IDE)  
**Status**: ✅ Phase 4 Complete  
**Date**: 2025-11-12

---

## Phase 1: Specification

### Requirements

- **REQ ID**: REQ-F-A2-2-3
- **Description**: 모든 필수 필드가 입력되면 "완료" 버튼이 활성화되어야 한다.
- **Priority**: M (Must)
- **Release Scope**: 현재 스프린트에서는 `기술 수준(level)` 필드를 필수 항목으로 처리하며, 이후 경력/직군/업무/관심분야 필드를 추가해도 동일한 상태 관리 패턴을 재사용한다.

### Acceptance Criteria

- 필수 값이 선택되기 전까지는 "완료" 버튼이 비활성화 상태를 유지한다.
- 필수 값이 모두 채워지면 버튼이 즉시 활성화된다.
- 제출 중에는 버튼이 다시 비활성화되어 중복 제출을 방지한다.
- 제출 실패 시 오류 메시지를 표시하고 버튼을 재활성화한다.

### Technical Specification

- **Frontend State**: `SelfAssessmentPage.tsx`에서 `level`과 `isSubmitting` 상태를 사용해 버튼 활성화 여부를 계산한다.
- **Guard Clause**: `handleCompleteClick` 콜백에서 `level === null` 또는 `isSubmitting`인 경우 조기 반환한다.
- **UI Feedback**: CSS에서 비활성화된 버튼 스타일과 로딩 텍스트(`"제출 중..."`)를 제공한다.

### Files Updated

- `src/frontend/src/pages/SelfAssessmentPage.tsx`
- `src/frontend/src/pages/SelfAssessmentPage.css`
- `src/frontend/src/pages/__tests__/SelfAssessmentPage.test.tsx`

---

## Phase 2: Test Design

### Test Cases (3 total)

1. ✅ `keeps complete button disabled when no level is selected`
2. ✅ `enables complete button after selecting a level`
3. ✅ `disables complete button while submitting`

**Test Coverage**:

- 상태 전이 검증: 2건
- 로딩/비활성화 유지: 1건
- 전체 Vitest 스위트: `SelfAssessmentPage.test.tsx` 내 10개 테스트 중 3개가 본 REQ를 직접 검증

---

## Phase 3: Implementation

### SelfAssessmentPage 상태 관리

필수 입력 여부와 제출 상태를 바탕으로 버튼 활성화 여부를 계산하고, 제출 시 중복 실행을 차단한다.

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

const isCompleteEnabled = level !== null && !isSubmitting
```

### 버튼 UI 피드백

CSS에서 활성/비활성 색상과 커서 상태를 명시해 사용자가 현재 입력 상태를 시각적으로 인지할 수 있게 했다.

```118:139:src/frontend/src/pages/SelfAssessmentPage.css
.complete-button {
  width: 100%;
  padding: 0.9rem;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  background-color: #28a745;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.complete-button:hover:not(:disabled) {
  background-color: #1c7c32;
}

.complete-button:disabled {
  background-color: #b7d7bc;
  cursor: not-allowed;
  color: #f8f9fa;
}
```

---

## Phase 4: Summary & Traceability

### Test Results

```
✓ src/pages/__tests__/SelfAssessmentPage.test.tsx (10 tests)
  ✓ keeps complete button disabled when no level is selected
  ✓ enables complete button after selecting a level
  ✓ disables complete button while submitting
```

### Requirements → Implementation Mapping

| REQ | Implementation | Test Coverage |
|-----|----------------|---------------|
| REQ-F-A2-2-3 | `SelfAssessmentPage.tsx`: 상태 가드 및 `isCompleteEnabled` 계산 | `SelfAssessmentPage.test.tsx`: tests 56, 64, 243 |
| REQ-F-A2-2-3 | `SelfAssessmentPage.css`: 비활성화 버튼 스타일 | `SelfAssessmentPage.test.tsx`: tests 56, 243 |

### Modified Files

1. `src/frontend/src/pages/SelfAssessmentPage.tsx` - 필수 입력 상태 관리 및 버튼 가드
2. `src/frontend/src/pages/SelfAssessmentPage.css` - 버튼 활성/비활성 스타일 추가
3. `src/frontend/src/pages/__tests__/SelfAssessmentPage.test.tsx` - 버튼 상태 테스트 3건 추가

### Git Commit

```
feat: Implement REQ-F-A2-2-2 level field in self-assessment page

- Add level selection (1-5) with radio buttons
- Guard complete button until mandatory input is provided
- Prevent duplicate submissions while API call is in-flight
- Extend vitest coverage for button enablement rules

Commit SHA: bd3c7ec
```

---

## Next Steps

- [ ] 추가 필드(경력, 직군 등) 도입 시 동일한 `isCompleteEnabled` 계산 로직에 포함
- [ ] 다중 필드 검증을 공통 훅으로 분리하는 방안 검토

---

## Notes

- 버튼 활성화 로직은 `level` 외의 필수 입력이 추가되더라도 `null` 체크만 확장하면 쉽게 재사용 가능하다.
- 제출 실패 시 오류 메시지를 노출한 뒤 버튼을 재활성화해 재시도를 허용한다.
