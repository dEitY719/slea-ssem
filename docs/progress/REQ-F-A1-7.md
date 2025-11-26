# REQ-F-A1-7: 로그인 실패 시 명확한 에러 메시지 및 헬프 링크 표시

**날짜**: 2025-11-26
**담당자**: Claude Code
**우선순위**: M (Must)
**상태**: ✅ 완료 (이미 구현됨)

---

## 📋 요구사항

### 요약

로그인 실패 시 명확한 에러 메시지를 표시하고, "계정 정보 확인" 링크 및 "관리자 문의" 헬프 링크를 함께 제공해야 한다.

### 수용 기준

- ✅ "로그인 실패 시, 에러 메시지와 함께 '계정 정보 확인', '관리자 문의' 두 링크가 표시된다."

### 관련 문서

- `docs/feature_requirement_mvp1.md` - REQ-F-A1-7 (Line 100)
- `docs/progress/REQ-F-A1-3.md` - 실제 구현 문서

---

## 🔍 구현 상태

### REQ-F-A1-3과의 관계

**REQ-F-A1-7은 이미 REQ-F-A1-3으로 구현되어 있습니다.**

- **REQ-F-A1-3**: "로그인 실패 시 에러 메시지 및 헬프 링크 표시"
- **REQ-F-A1-7**: "로그인 실패 시 명확한 에러 메시지를 표시하고, '계정 정보 확인' 링크 및 '관리자 문의' 헬프 링크를 함께 제공해야 한다."

두 요구사항은 **동일한 기능**을 설명하고 있으며, REQ-F-A1-3에서 이미 완벽하게 구현되었습니다.

---

## 🎯 Phase 1: Specification

### Intent

로그인 실패 시 사용자에게 명확한 피드백을 제공하고, 문제 해결을 위한 도움말 링크 제공

### 구현 위치

- `src/frontend/src/components/ErrorMessage.tsx` - 재사용 가능한 에러 메시지 컴포넌트
- `src/frontend/src/components/ErrorMessage.css` - 에러 메시지 스타일
- `src/frontend/src/pages/CallbackPage.tsx` - ErrorMessage 사용 (Line 37-56)

### 주요 기능

1. ✅ 명확한 에러 메시지 표시 (title + message)
2. ✅ "계정 정보 확인" 링크 제공 (https://account.samsung.com)
3. ✅ "관리자 문의" 링크 제공 (mailto:support@samsung.com)
4. ✅ 보안 설정 완료 (target="_blank", rel="noopener noreferrer")

---

## 🧪 Phase 2: Test Design

### 테스트 파일

**`src/frontend/src/pages/__tests__/CallbackPage.test.tsx`**

### 테스트 커버리지 (7개 테스트 모두 통과 ✅)

#### Test 5: Backend API 에러 시 helpLinks 표시 (Line 202-243)
```typescript
it('should show error when backend API returns error', async () => {
  // Mock backend error
  vi.mocked(global.fetch).mockResolvedValue({
    ok: false,
    status: 401,
    json: async () => ({
      detail: 'Invalid authorization code',
    }),
  } as Response)

  render(<BrowserRouter><CallbackPage /></BrowserRouter>)

  // Should show error message
  await waitFor(() => {
    expect(screen.getByText('로그인 실패')).toBeInTheDocument()
  })

  // Should show help links ✅
  expect(screen.getByText('계정 정보 확인')).toBeInTheDocument()
  expect(screen.getByText('관리자 문의')).toBeInTheDocument()
})
```

#### Test 6: helpLinks href 속성 검증 (Line 246-269)
```typescript
it('should display help links when authentication fails', async () => {
  // Mock URL without code
  mockSearchParams = new URLSearchParams({
    state: 'mock-state',
  })
  vi.mocked(useSearchParams).mockReturnValue([mockSearchParams, vi.fn()])

  render(<BrowserRouter><CallbackPage /></BrowserRouter>)

  // Should show help links with correct href ✅
  await waitFor(() => {
    const accountLink = screen.getByText('계정 정보 확인')
    expect(accountLink).toBeInTheDocument()
    expect(accountLink.closest('a')).toHaveAttribute('href', 'https://account.samsung.com')

    const supportLink = screen.getByText('관리자 문의')
    expect(supportLink).toBeInTheDocument()
    expect(supportLink.closest('a')).toHaveAttribute('href', 'mailto:support@samsung.com')
  })
})
```

---

## 💻 Phase 3: Implementation

### 구현 완료 확인

#### 1. ErrorMessage 컴포넌트 (`src/frontend/src/components/ErrorMessage.tsx`)

**Interface**:
```typescript
interface ErrorMessageProps {
  title?: string                    // 기본: "오류 발생"
  message: string                   // 에러 메시지 (필수)
  helpLinks?: Array<{              // 헬프 링크 배열 (선택)
    text: string                    // 링크 텍스트
    href: string                    // 링크 URL
  }>
}
```

**특징**:
- ✅ helpLinks 속성 지원
- ✅ 보안 설정 (target="_blank", rel="noopener noreferrer")
- ✅ 깔끔한 UI (ExclamationTriangleIcon 사용)

#### 2. CallbackPage 사용 (`src/frontend/src/pages/CallbackPage.tsx:37-56`)

```typescript
if (error) {
  return (
    <PageLayout mainClassName="callback-page" containerClassName="callback-container">
      <ErrorMessage
        title="로그인 실패"
        message={error}
        helpLinks={[
          {
            text: '계정 정보 확인',
            href: 'https://account.samsung.com',    // ✅ REQ-F-A1-7
          },
          {
            text: '관리자 문의',
            href: 'mailto:support@samsung.com',     // ✅ REQ-F-A1-7
          },
        ]}
      />
    </PageLayout>
  )
}
```

#### 3. 스타일링 (`src/frontend/src/components/ErrorMessage.css`)

**주요 스타일**:
- ✅ 중앙 정렬 에러 컨테이너
- ✅ 빨간색 에러 아이콘 및 제목 (#d32f2f)
- ✅ 회색 메시지 텍스트 (#666)
- ✅ 파란색 버튼 스타일 링크 (#1976d2, #2196f3)
- ✅ Hover 효과 (색상 전환)

---

## ✅ Phase 4: Test Results

### 테스트 실행 결과 (2025-11-26)

```bash
$ npm --prefix src/frontend test -- CallbackPage.test.tsx --run

 ✓ src/pages/__tests__/CallbackPage.test.tsx  (7 tests) 88ms

 Test Files  1 passed (1)
      Tests  7 passed (7)
   Duration  1.45s (transform 150ms, setup 98ms, collect 360ms, tests 88ms)
```

**REQ-F-A1-7 검증 테스트**:
- ✅ Test 5: Backend API 에러 시 helpLinks 표시
- ✅ Test 6: helpLinks href 속성 검증

---

## 📊 Traceability Matrix

| REQ ID | 요구사항 | 구현 위치 | 테스트 위치 | 상태 |
|--------|---------|-----------|------------|------|
| REQ-F-A1-7 | 로그인 실패 시 명확한 에러 메시지 표시 | `CallbackPage.tsx:37-56` | `CallbackPage.test.tsx:202-269` | ✅ |
| - 에러 메시지 표시 | title="로그인 실패" + message | `CallbackPage.tsx:41-42` | `CallbackPage.test.tsx:234` | ✅ |
| - "계정 정보 확인" 링크 | href="https://account.samsung.com" | `CallbackPage.tsx:44-47` | `CallbackPage.test.tsx:238,263` | ✅ |
| - "관리자 문의" 링크 | href="mailto:support@samsung.com" | `CallbackPage.tsx:48-51` | `CallbackPage.test.tsx:239,267` | ✅ |

---

## 📁 관련 파일 목록

### 컴포넌트 (2개)

- `src/frontend/src/components/ErrorMessage.tsx` (Commit: 2bd263b)
- `src/frontend/src/components/ErrorMessage.css` (Commit: 2bd263b)

### 사용처 (1개)

- `src/frontend/src/pages/CallbackPage.tsx` - ErrorMessage 사용 (Commit: 745158b)

### 테스트 (1개)

- `src/frontend/src/pages/__tests__/CallbackPage.test.tsx` (7 tests, 100% pass)

---

## 🎓 배운 점 & 개선사항

### 성공 요인

1. **재사용 가능한 컴포넌트 설계**: ErrorMessage를 범용 컴포넌트로 설계
2. **명확한 사용자 안내**: 에러 발생 시 해결 방법 제공
3. **보안 고려**: target="_blank" + rel="noopener noreferrer"

### 구현 장점

1. **Separation of Concerns**: 에러 표시 로직을 별도 컴포넌트로 분리
2. **Reusability**: 다른 페이지에서도 활용 가능 (LoginPage 등)
3. **Customizability**: title, message, helpLinks 커스터마이징 가능

---

## ✅ Acceptance Criteria 검증

- ✅ "로그인 실패 시, 에러 메시지와 함께 '계정 정보 확인', '관리자 문의' 두 링크가 표시된다."
  - 구현: `CallbackPage.tsx:37-56`
  - 검증: `CallbackPage.test.tsx:202-269` (Test 5, 6)

---

## 📝 관련 요구사항

**함께 구현됨**:

- **REQ-F-A1-3**: 로그인 실패 시 에러 메시지 및 헬프 링크 (동일 기능)
  - Progress: `docs/progress/REQ-F-A1-3.md`
  - Commit: 2bd263b (2025-11-11)

**의존성**:

- REQ-F-A1-1: 로그인 페이지 (사전 구현 완료)
- REQ-F-A1-2: SSO 콜백 페이지 구현 (사전 구현 완료)
- REQ-F-A1-4: OIDC 콜백 처리 (사전 구현 완료)
- REQ-F-A1-5: HttpOnly JWT 쿠키 수신 (사전 구현 완료)

---

**구현 완료일**: 2025-11-11 (REQ-F-A1-3으로 구현)
**검증일**: 2025-11-26
**Commit**: 745158b (feat: Implement OIDC callback with PKCE)
**상태**: ✅ Done
