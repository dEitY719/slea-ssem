# REQ-F-B2-1: 문항 순차 표시 및 답변 제출 UI

**Developer**: Claude Code
**Status**: ✅ Done
**Phase**: 4
**Date**: 2025-11-12

---

## 📋 Phase 1: Specification

### 요구사항

**REQ ID**: REQ-F-B2-1
**요구사항**: 생성된 문항을 순차적으로 표시하고, 사용자가 답안을 입력하고 제출할 수 있는 UI를 제공해야 한다.
**우선순위**: M (Must)

### Acceptance Criteria

- "문항이 1개씩 순차적으로 표시된다."
- "진행률이 실시간으로 업데이트된다."

### Implementation Specification

#### Location
- **File**: `src/frontend/src/pages/TestPage.tsx`
- **Function**: `handleNextClick` (line 100-143)

#### Behavior
1. 사용자가 답변 선택/입력
2. "다음" 버튼 클릭 시:
   - `user_answer` 객체 생성 (`{ selected: ... }` 또는 `{ text: ... }`)
   - `POST /questions/autosave` API 호출
   - `response_time_ms` 측정 (문항 표시 시점부터 제출까지)
3. 성공 시:
   - 다음 문항으로 이동 (`currentIndex + 1`)
   - 답변 상태 초기화
4. 마지막 문항 완료 시:
   - `/test-results` 페이지로 이동
5. 실패 시:
   - 에러 메시지 표시 (현재 화면에서)
   - 재시도 가능

#### Non-functional Requirements
- **Performance**: API 응답 2초 이내
- **UX**: 제출 중 버튼 비활성화
- **Error Handling**: 네트워크 오류 시 에러 메시지 + 재시도

---

## 🧪 Phase 2: Test Design

### Test File
`src/frontend/src/pages/__tests__/TestPage.test.tsx`

### Test Cases (9개)

| Category | Test | Description |
|----------|------|-------------|
| **AC Verification** | AC1: 문항 순차 표시 | 첫 번째 문항만 표시되는지 확인 |
| **AC Verification** | AC2: 진행률 업데이트 | "1/3" → "2/3" 진행률 업데이트 검증 |
| **Happy Path** | Multiple Choice 제출 | `{ selected: 'Option B' }` 형식으로 autosave API 호출 |
| **Happy Path** | Short Answer 제출 | `{ text: '...' }` 형식으로 autosave API 호출 |
| **Validation** | 빈 답변 방지 | 답변 없으면 "다음" 버튼 비활성화 |
| **Edge Case** | 마지막 문항 완료 | `/test-results`로 네비게이션 |
| **Edge Case** | Response Time 측정 | `response_time_ms ≥ 100ms` 검증 |
| **Edge Case** | 제출 중 버튼 상태 | `isSubmitting=true` 시 버튼 비활성화 |
| **Error Handling** | API 실패 처리 | 에러 메시지 표시 + 현재 문항 유지 |

### Test Results
```
✅ 9 passed (9)
Duration: 2.24s
```

---

## 💻 Phase 3: Implementation

### Modified Files

#### 1. `src/frontend/src/pages/TestPage.tsx`

**Changes**:
- `questionStartTime` 상태 추가 (응답 시간 측정)
- `loadingError`와 `submitError` 분리 (에러 상태 구분)
- `handleNextClick` 함수 구현:
  - `user_answer` 객체 생성 (item_type에 따라)
  - `POST /questions/autosave` API 호출
  - `response_time_ms` 계산 및 전송
  - 성공 시 다음 문항 이동 또는 결과 페이지로 네비게이션
  - 실패 시 에러 메시지 표시 (인라인)
- `currentIndex` 변경 시 타이머 리셋 및 에러 초기화
- 제출 에러 UI 추가 (`error-box`)

**Key Code Snippets**:

```typescript
// State management
const [questionStartTime, setQuestionStartTime] = useState<number>(Date.now())
const [submitError, setSubmitError] = useState<string | null>(null)

// Answer submission
const userAnswer = currentQuestion.item_type === 'short_answer'
  ? { text: answer }
  : { selected: answer }

await transport.post('/questions/autosave', {
  session_id: sessionId,
  question_id: currentQuestion.id,
  user_answer: userAnswer,
  response_time_ms: Date.now() - questionStartTime,
})
```

#### 2. `src/frontend/src/pages/__tests__/TestPage.test.tsx`

**New Test File**: 9 test cases covering all requirements

---

## 📊 Traceability

### Requirements → Implementation

| REQ | Implementation | Location |
|-----|----------------|----------|
| **REQ-F-B2-1** | 문항 순차 표시 | `TestPage.tsx:161-189` (currentIndex 기반 렌더링) |
| **REQ-F-B2-1** | 진행률 표시 | `TestPage.tsx:182-189` (`${currentIndex + 1}/${questions.length}`) |
| **REQ-F-B2-1** | 답변 입력 UI | `TestPage.tsx:196-247` (multiple_choice, true_false, short_answer) |
| **REQ-F-B2-1** | 답변 제출 | `TestPage.tsx:100-143` (handleNextClick + autosave API) |

### Implementation → Test Coverage

| Implementation | Test |
|----------------|------|
| 문항 순차 표시 | `AC1: 문항이 1개씩 순차적으로 표시된다` |
| 진행률 업데이트 | `AC2: 진행률이 실시간으로 업데이트된다` |
| Multiple Choice 제출 | `Happy Path: multiple choice 답변 제출 성공` |
| Short Answer 제출 | `Happy Path: short answer 답변 제출 성공` |
| 빈 답변 검증 | `Input Validation: 빈 답변 제출 방지` |
| 마지막 문항 처리 | `Edge Case: 마지막 문항 완료 시 results 페이지 이동` |
| Response Time | `Response Time Tracking: response_time_ms 정확히 측정` |
| 제출 중 상태 | `Button State: 제출 중 버튼 비활성화` |
| 에러 처리 | `Error Handling: API 실패 시 에러 메시지 표시` |

---

## 🔍 Testing Results

### Test Execution
```bash
cd src/frontend
npm test -- src/pages/__tests__/TestPage.test.tsx --run
```

### Results
```
✅ Test Files: 1 passed (1)
✅ Tests: 9 passed (9)
⏱️  Duration: 2.24s
```

### Coverage
- **Acceptance Criteria**: 2/2 ✅
- **Happy Path**: 2/2 ✅
- **Validation**: 1/1 ✅
- **Edge Cases**: 3/3 ✅
- **Error Handling**: 1/1 ✅

---

## 📝 Summary

### Completed Tasks
1. ✅ Specification 작성 및 승인
2. ✅ Test design (9 test cases)
3. ✅ Implementation:
   - `handleNextClick` 함수 구현
   - Response time tracking
   - Error handling (loading vs submit errors)
   - API integration (`POST /questions/autosave`)
4. ✅ All tests passing (9/9)

### Files Modified
- `src/frontend/src/pages/TestPage.tsx`
- `src/frontend/src/pages/__tests__/TestPage.test.tsx` (new)

### API Integration
- **Endpoint**: `POST /questions/autosave`
- **Request**:
  ```json
  {
    "session_id": "string",
    "question_id": "string",
    "user_answer": {
      "selected": "string",  // for multiple_choice, true_false
      "text": "string"       // for short_answer
    },
    "response_time_ms": 1234
  }
  ```
- **Response**:
  ```json
  {
    "saved": true,
    "session_id": "string",
    "question_id": "string",
    "saved_at": "2025-11-12T00:00:00Z"
  }
  ```

### Next Steps
- ✅ REQ-F-B2-1 완료
- 🔜 REQ-F-B2-2: 진행률, 응답 입력, "다음" 버튼, 타이머 (일부 완료, 타이머 추가 필요)
- 🔜 REQ-F-B2-3: 정오답 피드백
- 🔜 REQ-F-B2-4: 부분점수 표시
- 🔜 REQ-F-B2-5~7: 타이머, 자동저장, 시간 초과 처리

---

**Approved**: ✅
**Merged**: Pending commit
