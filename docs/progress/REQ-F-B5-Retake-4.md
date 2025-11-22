# REQ-F-B5-Retake-4: Round 2 Adaptive Question Generation

**Status**: ✅ Done
**Priority**: M (Medium)
**Completed**: 2025-11-22

---

## 📋 Requirement

**요구사항**: 라운드 1 완료 후 적응형 Round 2 진행 시, `POST /questions/generate-adaptive` 호출 시 `previous_session_id`를 정확히 전달해야 한다. (기존 세션의 completed 상태와 무관)

**Source**: `docs/feature_requirement_mvp1.md` line 564

---

## 🎯 Implementation Summary

### Phase 1: Specification ✅

**Objective**: Round 1 완료 후 결과 페이지에서 "2차 진행" 버튼 클릭 시 Round 2 적응형 문제 생성

**Key Components**:
1. TestResultsPage: Round 1 결과 표시, "2차 진행" 버튼 제공
2. ActionButtons: Round 기반 버튼 조건부 렌더링
3. TestPage: Round 2 시 adaptive endpoint 호출
4. ExplanationPage: 해설 페이지 네비게이션 처리

**State Flow**:
```
ProfileReview → TestPage (Round 1)
    ↓ (surveyId, round: 1)
TestPage completes → TestResultsPage
    ↓ (sessionId, surveyId, round: 1)
User clicks "2차 진행" → TestPage (Round 2)
    ↓ (surveyId, round: 2, previousSessionId)
TestPage calls generateAdaptiveQuestions()
    ↓ (previous_session_id from Round 1)
Backend generates adaptive questions
```

---

### Phase 2: Test Design ✅

**Test Coverage**:
- Round detection in TestResultsPage
- Button visibility based on round (show for Round 1, hide for Round 2)
- State persistence across navigation (sessionStorage)
- surveyId propagation through navigation chain
- Adaptive endpoint call with correct previousSessionId

---

### Phase 3: Implementation ✅

#### 3.1 Core Implementation

**File**: `src/frontend/src/pages/TestPage.tsx`
- Lines 93-108: Round 2 adaptive question generation logic
- Lines 52-66: surveyId persistence to sessionStorage
- Lines 188-194: surveyId validation before navigation

```typescript
// Round 2: Generate adaptive questions based on Round 1 performance
if (state.round === 2 && state.previousSessionId) {
  response = await questionService.generateAdaptiveQuestions({
    previous_session_id: state.previousSessionId,
    round: 2,
  })
} else {
  // Round 1: Generate normal questions
  response = await questionService.generateQuestions({
    survey_id: state.surveyId,
    round: state.round || 1,
    domain: 'AI',
  })
}
```

**File**: `src/frontend/src/pages/TestResultsPage.tsx`
- Lines 38-50: State persistence to sessionStorage
- Lines 52-75: State restoration from sessionStorage
- Lines 83-91: Effective sessionId computation
- Lines 198-244: Round 2 navigation logic

```typescript
// Round 1 → Round 2 adaptive
if (currentRound === 1) {
  navigate('/test', {
    state: {
      surveyId: persistedState.surveyId,
      round: 2,
      previousSessionId: persistedState.sessionId,  // Pass Round 1 session
    },
  })
}
```

**File**: `src/frontend/src/components/TestResults/ActionButtons.tsx`
- Lines 40-46: Conditional button rendering

```typescript
{/* Only show retake button for Round 1 */}
{round === 1 && (
  <button type="button" className="secondary-button" onClick={onRetake}>
    <ArrowPathIcon className="button-icon" />
    2차 진행
  </button>
)}
```

#### 3.2 Bug Fixes

**Issue 1**: surveyId loss after viewing explanations

**Root Cause**: ExplanationPage was passing incomplete state `{ sessionId }` when navigating back to TestResultsPage, which overwrote the complete state in sessionStorage.

**Solution**:
- ExplanationPage navigates without state (line 106)
- TestResultsPage restores from sessionStorage using effectiveSessionId (lines 83-91)

**File**: `src/frontend/src/pages/ExplanationPage.tsx`
```typescript
const handleViewResults = () => {
  // Navigate without state - TestResultsPage will restore from sessionStorage
  navigate('/test-results')
}
```

**Issue 2**: sessionId undefined when returning from ExplanationPage

**Root Cause**: `useTestResults` hook received `undefined` when location.state was null.

**Solution**: Added `effectiveSessionId` computation using `React.useMemo` to fallback to sessionStorage.

---

### Phase 4: Testing & Verification ✅

**Manual Test Flow**:
```
1. Complete Round 1 test
   ✓ Navigate to TestResultsPage with full state
   ✓ State saved to sessionStorage
   ✓ "2차 진행" button visible

2. View explanations
   ✓ Navigate to ExplanationPage
   ✓ View explanations, navigate back
   ✓ State restored from sessionStorage
   ✓ surveyId preserved

3. Click "2차 진행"
   ✓ Navigate to TestPage with Round 2 state
   ✓ previousSessionId passed correctly
   ✓ generateAdaptiveQuestions called
   ✓ Round 2 test starts

4. Complete Round 2 test
   ✓ Navigate to TestResultsPage
   ✓ "2차 진행" button hidden (round === 2)
```

**Logs Verification**:
```
[TestPage] Saved surveyId to sessionStorage: survey_1763816716358
[TestResults] Full saved state: {sessionId, surveyId, round: 1}
[TestResults] Using sessionId from sessionStorage: mock_session_001
[Retake] Round 1 completed, starting Round 2
```

---

## 📁 Modified Files

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `src/pages/TestPage.tsx` | 93-108, 52-66, 188-194, 273-279 | Round 2 adaptive generation, surveyId persistence |
| `src/pages/TestResultsPage.tsx` | 38-50, 52-75, 83-91, 198-244 | State persistence, round-based navigation |
| `src/components/TestResults/ActionButtons.tsx` | 40-46 | Conditional button rendering |
| `src/pages/ExplanationPage.tsx` | 104-106 | Navigation without state |
| `src/services/questionService.ts` | 42-48, 117-130 | generateAdaptiveQuestions service |

---

## 🔄 State Management

### sessionStorage Keys
- `latest_test_session_id`: Most recent session ID (for key lookup)
- `test_results_state_${sessionId}`: Full LocationState object
- `current_test_survey_id`: Current test survey ID

### LocationState Type
```typescript
type LocationState = {
  sessionId: string
  surveyId?: string
  round?: number
  previousSessionId?: string  // For Round 2
}
```

---

## 🐛 Known Issues & Resolutions

### Issue: surveyId undefined in persisted state

**Symptom**: `[TestResults] State has surveyId? false Value: undefined`

**Root Cause**: JSON.stringify omits undefined values, and ExplanationPage was passing incomplete state.

**Resolution**:
1. ExplanationPage navigates without state
2. TestResultsPage uses effectiveSessionId
3. Added surveyId validation in TestPage

**Commits**:
- `64f9c27`: Add surveyId validation before navigating to results
- `3468c45`: Prevent state overwrite when returning from ExplanationPage

---

## ✅ Acceptance Criteria

- [x] Round 1 완료 후 결과 페이지에서 "2차 진행" 버튼 표시
- [x] "2차 진행" 버튼 클릭 시 Round 2 adaptive 문제 생성
- [x] `previous_session_id` 정확히 전달 (Round 1 session ID)
- [x] Round 2 완료 후 "2차 진행" 버튼 숨김
- [x] 해설 페이지 이동 후 돌아와도 state 유지
- [x] surveyId, round, previousSessionId 모두 정확히 전달

---

## 📝 Notes

### Design Decisions

1. **sessionStorage over localStorage**: Session-scoped data, cleared on tab close
2. **Dual key strategy**: `latest_test_session_id` + `test_results_state_${sessionId}` for reliable restoration
3. **useMemo for effectiveSessionId**: Prevents unnecessary re-computation and hook call issues
4. **Navigate without state from ExplanationPage**: Avoids overwriting sessionStorage with incomplete data

### Future Improvements

- Consider adding TTL for sessionStorage data
- Add error boundary for state restoration failures
- Implement state migration if LocationState schema changes
- Add analytics tracking for Round 1→2 conversion rate

---

## 🔗 Related Requirements

- REQ-F-B5-Retake-1: 재응시 버튼 클릭 시 이전 정보 로드
- REQ-F-B5-Retake-2: 재응시 자기평가 폼 수정 가능
- REQ-F-B4-7: 문항별 해설 보기 기능

---

## 📊 Git History

```bash
64f9c27 fix: Add surveyId validation before navigating to results
3468c45 fix: Prevent state overwrite when returning from ExplanationPage
```

**Author**: Claude Code
**Date**: 2025-11-22
