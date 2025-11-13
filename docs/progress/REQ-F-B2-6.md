# REQ-F-B2-6: 문항 풀이 화면 - 자동 저장 및 "저장됨" 표시 구현

**Date**: 2025-11-13
**Status**: ✅ Completed (Phase 4)
**REQ ID**: REQ-F-B2-6
**Priority**: M (Must)

---

## 📋 Phase 1: SPECIFICATION

### Requirements

**REQ-F-B2-6**: **테스트 진행 중 각 응답은 자동으로 실시간 저장(Autosave)되어야 한다.** 저장 완료 시 화면에 "저장됨" 표시를 해야 한다.

### Acceptance Criteria

- [x] 답변 입력 시 1초 후 자동으로 저장 시작
- [x] 저장 중 "저장 중..." 메시지 표시
- [x] 저장 완료 시 "✓ 저장됨" 메시지 표시
- [x] 저장 완료 후 2초 후 메시지 자동 숨김
- [x] 동일한 답변은 중복 저장하지 않음
- [x] 다음 문제로 이동 시 저장 상태 초기화
- [x] 에러 발생 시 "저장 실패" 메시지 표시

### Technical Specification

**Location**: `src/frontend/src/pages/TestPage.tsx`

**State Additions**:
```typescript
const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')
const [lastSavedAnswer, setLastSavedAnswer] = useState<string>('')
```

**Autosave Logic**:
```typescript
useEffect(() => {
  if (!answer.trim() || answer === lastSavedAnswer || !sessionId || !questions || questions.length === 0) {
    return
  }

  const timer = setTimeout(async () => {
    setSaveStatus('saving')
    try {
      await transport.post('/questions/autosave', {
        session_id: sessionId,
        question_id: currentQuestion.id,
        user_answer: userAnswer,
        response_time_ms: responseTimeMs,
      })

      setLastSavedAnswer(answer)
      setSaveStatus('saved')
      setTimeout(() => setSaveStatus('idle'), 2000)
    } catch (err) {
      setSaveStatus('error')
    }
  }, 1000) // 1 second debounce

  return () => clearTimeout(timer)
}, [answer, sessionId, questions, currentIndex, questionStartTime, lastSavedAnswer])
```

**UI Integration**:
```tsx
{saveStatus === 'saving' && <div className="save-status save-status-saving">저장 중...</div>}
{saveStatus === 'saved' && <div className="save-status save-status-saved">✓ 저장됨</div>}
{saveStatus === 'error' && <div className="save-status save-status-error">저장 실패</div>}
```

---

## 🧪 Phase 2: TEST DESIGN

### Test Cases

| Test Case | Purpose | Status |
|-----------|---------|--------|
| Autosave: 답변 입력 시 자동 저장 | 1초 debounce 후 저장 | ✅ Pass |
| Autosave: 저장 완료 시 "저장됨" 표시 | 저장 완료 메시지 표시 | ✅ Pass |
| Autosave: 저장 완료 후 메시지 자동 숨김 | 2초 후 메시지 숨김 | ✅ Pass |
| Autosave: 동일한 답변은 중복 저장하지 않음 | 중복 저장 방지 | ✅ Pass |
| Autosave: 저장 실패 시 에러 메시지 표시 | 에러 처리 | ✅ Pass |

**Test File**: `src/frontend/src/pages/__tests__/TestPage.test.tsx`

**Test Coverage**:
- ✅ Happy path (자동 저장 동작)
- ✅ Save status display (저장 중/완료/실패)
- ✅ Auto-hide after 2 seconds (메시지 자동 숨김)
- ✅ Duplicate save prevention (중복 방지)
- ✅ Error handling (에러 표시)

---

## 💻 Phase 3: IMPLEMENTATION

### Files Modified

1. **`src/frontend/src/pages/TestPage.tsx`**
   - Added `saveStatus` state ('idle' | 'saving' | 'saved' | 'error')
   - Added `lastSavedAnswer` state for duplicate detection
   - Added autosave `useEffect` with 1-second debounce
   - Updated question change `useEffect` to reset save status
   - Added save status indicator UI (fixed position, top-right)

2. **`src/frontend/src/pages/TestPage.css`**
   - Added `.save-status` base styles (fixed position)
   - Added `.save-status-saving` (blue background)
   - Added `.save-status-saved` (green background)
   - Added `.save-status-error` (red background)
   - Added `slideIn` animation for smooth appearance

3. **`src/frontend/src/pages/__tests__/TestPage.test.tsx`**
   - Added `describe` block for REQ-F-B2-6 Autosave tests
   - Added 5 autosave-related test cases
   - All tests use real timers for stability

### Implementation Details

**Autosave Debounce Logic** (src/frontend/src/pages/TestPage.tsx:124-163):
- Waits 1 second after answer change before saving
- Prevents duplicate saves by comparing with `lastSavedAnswer`
- Handles multiple question types (multiple_choice, true_false, short_answer)
- Updates save status through state machine (idle → saving → saved/error)

**State Transitions**:
```
idle → saving → saved → (2s delay) → idle
       ↓
     error
```

**UI Positioning**:
- Fixed position (top: 20px, right: 20px)
- z-index: 1000 (above other content)
- SlideIn animation (0.3s)
- Auto-hide after 2 seconds (for 'saved' status)

### Test Results

```bash
npm test -- TestPage.test.tsx --run

✅ Test Files  1 passed (1)
✅ Tests  19 passed (19)
   - 9 REQ-F-B2-1 tests (기존)
   - 5 REQ-F-B2-2 timer tests (기존)
   - 5 REQ-F-B2-6 autosave tests (신규)
   Duration  12.41s
```

**All tests passing**: 100% success rate

---

## 🔍 Traceability Matrix

| Requirement | Implementation | Test |
|-------------|----------------|------|
| REQ-F-B2-6: 자동 저장 | TestPage.tsx:124-163 | TestPage.test.tsx:452-480 |
| REQ-F-B2-6: "저장됨" 표시 | TestPage.tsx:362-378, TestPage.css:210-248 | TestPage.test.tsx:482-504 |
| REQ-F-B2-6: 2초 후 숨김 | TestPage.tsx:155 | TestPage.test.tsx:506-533 |
| REQ-F-B2-6: 중복 방지 | TestPage.tsx:127, 151 | TestPage.test.tsx:535-566 |
| REQ-F-B2-6: 에러 처리 | TestPage.tsx:156-159 | TestPage.test.tsx:568-590 |

---

## 📊 Summary

### Completed

✅ **Phase 1**: 요구사항 분석 및 스펙 정의
✅ **Phase 2**: 테스트 설계 (5개 테스트 케이스)
✅ **Phase 3**: 구현 및 검증 (19/19 tests pass)
✅ **Phase 4**: Progress 문서 작성

### Modified Files

- `src/frontend/src/pages/TestPage.tsx` (자동 저장 로직 추가)
- `src/frontend/src/pages/TestPage.css` (저장 상태 스타일 추가)
- `src/frontend/src/pages/__tests__/TestPage.test.tsx` (자동 저장 테스트 추가)
- `docs/progress/REQ-F-B2-6.md` (이 파일)

### Code Quality

- ✅ All tests passing (19/19)
- ✅ Type safety (TypeScript strict mode)
- ✅ REQ traceability (주석 포함)
- ✅ Debounce optimization (1초 debounce)
- ✅ Error handling (네트워크 오류 대응)
- ✅ UX optimization (저장 상태 명확하게 표시)

---

## 🎯 Key Features Implemented

1. **Real-time Autosave**:
   - 1초 debounce로 불필요한 API 호출 방지
   - 답변 변경 시 자동으로 저장
   - 중복 저장 방지 (lastSavedAnswer 비교)

2. **Visual Feedback**:
   - "저장 중..." (파란색)
   - "✓ 저장됨" (녹색, 2초 후 자동 숨김)
   - "저장 실패" (빨간색)

3. **Error Resilience**:
   - 네트워크 오류 시 사용자에게 알림
   - 에러 로그 콘솔 출력
   - 실패 상태 명확하게 표시

---

## 🔜 Next Steps

REQ-F-B2-6 완료! 다음 우선순위:

- 🔜 **REQ-F-B2-3**: 정오답 피드백 (1초 내 토스트 표시)
- 🔜 **REQ-F-B2-4**: 주관식 부분점수 표시
- 🔜 **REQ-F-B2-7**: 20분 초과 시 재개 모달

---

**Approved**: ✅
**Git Commit**: 068b2ff
