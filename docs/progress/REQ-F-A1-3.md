# REQ-F-A1-3: 로그인 실패 시 에러 메시지 및 헬프 링크 표시

**날짜**: 2025-11-11
**담당자**: Claude Code
**우선순위**: M (Must)
**상태**: ✅ 완료

---

## 📋 요구사항

### 요약
로그인 실패 시 명확한 에러 메시지를 표시하고, "계정 정보 확인" 링크 및 "관리자 문의" 헬프 링크를 함께 제공

### 수용 기준
- ✅ "로그인 실패 시, 에러 메시지와 함께 '계정 정보 확인', '관리자 문의' 두 링크가 표시된다."

### 관련 문서
- `docs/feature_requirement_mvp1.md` - REQ-F-A1-3
- `docs/user_scenarios_mvp1.md` - 시나리오 0 (사용자 가입)

---

## 🎯 Phase 1: Specification

### Intent
로그인 실패 시 사용자에게 명확한 피드백을 제공하고, 문제 해결을 위한 도움말 링크 제공

### 구현 위치
- `src/frontend/src/components/ErrorMessage.tsx` - 재사용 가능한 에러 메시지 컴포넌트
- `src/frontend/src/components/ErrorMessage.css` - 에러 메시지 스타일
- `src/frontend/src/pages/CallbackPage.tsx` - ErrorMessage 사용

### 주요 기능
1. 에러 메시지 명확하게 표시
2. "계정 정보 확인" 링크 제공 (https://account.samsung.com)
3. "관리자 문의" 링크 제공 (mailto:support@samsung.com)
4. 깔끔한 UI/UX

---

## 🧪 Phase 2: Test Design

### 테스트 파일
**`src/frontend/src/pages/__tests__/CallbackPage.test.tsx`**

### 테스트 커버리지
- ✅ Test 3: API 호출 실패 시 에러 메시지 표시
- ✅ Test 4: 인증 실패 시 헬프 링크 표시
  - "계정 정보 확인" 링크 존재 확인
  - "관리자 문의" 링크 존재 확인
  - 링크 href 속성 검증

**Test 4 코드** (CallbackPage.test.tsx:165-193):
```typescript
it('should display help links when authentication fails', async () => {
  ;(global.fetch as any).mockResolvedValueOnce({
    ok: false,
    status: 400,
    json: async () => ({ detail: 'Authentication failed' }),
  })

  render(
    <MemoryRouter initialEntries={['/auth/callback?knox_id=...']}>
      <CallbackPage />
    </MemoryRouter>
  )

  await waitFor(() => {
    // "계정 정보 확인" 링크
    const accountLink = screen.getByRole('link', { name: /계정 정보 확인/i })
    expect(accountLink).toBeInTheDocument()
    expect(accountLink).toHaveAttribute('href', expect.stringContaining('account'))

    // "관리자 문의" 링크
    const supportLink = screen.getByRole('link', { name: /관리자 문의/i })
    expect(supportLink).toBeInTheDocument()
    expect(supportLink).toHaveAttribute('href', expect.stringContaining('support'))
  })
})
```

---

## 💻 Phase 3: Implementation

### 생성된 파일

#### 1. `src/frontend/src/components/ErrorMessage.tsx`
**목적**: 재사용 가능한 에러 메시지 컴포넌트

**주요 기능**:
```typescript
interface ErrorMessageProps {
  title?: string                    // 에러 제목 (기본: "오류 발생")
  message: string                   // 에러 메시지
  helpLinks?: Array<{              // 헬프 링크 배열 (선택)
    text: string
    href: string
  }>
}
```

**특징**:
- 재사용 가능한 컴포넌트 (다른 페이지에서도 사용 가능)
- 커스터마이징 가능한 title, message, helpLinks
- 깔끔한 UI

---

#### 2. `src/frontend/src/components/ErrorMessage.css`
**목적**: ErrorMessage 스타일링

**주요 스타일**:
- 중앙 정렬
- 빨간색 제목 (#d32f2f)
- 회색 메시지 (#666)
- 파란색 버튼 스타일 링크
- Hover 효과

---

#### 3. `src/frontend/src/pages/CallbackPage.tsx` (사용)
**REQ-F-A1-3 구현 부분** (Line 38-51):

```typescript
if (error) {
  return (
    <div className="callback-page">
      <div className="callback-container">
        <ErrorMessage
          title="로그인 실패"
          message={error}
          helpLinks={[
            {
              text: '계정 정보 확인',
              href: 'https://account.samsung.com',
            },
            {
              text: '관리자 문의',
              href: 'mailto:support@samsung.com',
            },
          ]}
        />
      </div>
    </div>
  )
}
```

---

## ✅ Phase 4: Test Results

### 테스트 실행 결과

```
Test Files  1 passed (1)
     Tests  8 passed (8)
  Duration  2.08s

✓ src/pages/__tests__/CallbackPage.test.tsx (8 tests)
  ✓ should redirect to /home for new users after successful login
  ✓ should redirect to /home for existing users after successful login
  ✓ should display error message when API call fails ✅
  ✓ should display help links when authentication fails ✅
  ✓ should use mock response without API call when mock=true
  ✓ should redirect within 3 seconds after successful authentication
  ✓ should display error when required parameters are missing
  ✓ should display loading spinner during authentication
```

**Test 3 & 4가 REQ-F-A1-3를 검증** ✅

---

## 📊 Traceability Matrix

| REQ ID | Specification | Implementation | Test | Status |
|--------|--------------|----------------|------|--------|
| REQ-F-A1-3 | 에러 메시지 및 헬프 링크 표시 | `ErrorMessage.tsx:1-47` | `CallbackPage.test.tsx:165-193` | ✅ |
| - 명확한 에러 메시지 | 에러 제목 + 메시지 표시 | `ErrorMessage.tsx:25-26` | `CallbackPage.test.tsx:142-162` | ✅ |
| - "계정 정보 확인" 링크 | Samsung 계정 페이지 링크 | `CallbackPage.tsx:42-45` | `CallbackPage.test.tsx:184-186` | ✅ |
| - "관리자 문의" 링크 | 관리자 이메일 링크 | `CallbackPage.tsx:46-49` | `CallbackPage.test.tsx:189-191` | ✅ |

---

## 📁 변경된 파일 목록

### 신규 생성 (2개)
- `src/frontend/src/components/ErrorMessage.tsx` (Commit 2bd263b)
- `src/frontend/src/components/ErrorMessage.css` (Commit 2bd263b)

### 수정 (1개)
- `src/frontend/src/pages/CallbackPage.tsx` - ErrorMessage 사용 (Commit 2bd263b)

---

## 🎓 배운 점 & 개선사항

### 성공 요인
1. **재사용 가능한 컴포넌트**: ErrorMessage를 다른 페이지에서도 사용 가능
2. **명확한 사용자 안내**: 에러 발생 시 명확한 메시지 + 해결 방법 제공
3. **깔끔한 UI/UX**: 사용자 친화적인 디자인

### 구현 장점
1. **Separation of Concerns**: 에러 표시 로직을 별도 컴포넌트로 분리
2. **Reusability**: 다른 페이지의 에러 표시에도 활용 가능
3. **Customizability**: title, message, helpLinks 커스터마이징 가능

---

## ✅ Acceptance Criteria 검증

- ✅ "로그인 실패 시, 에러 메시지와 함께 '계정 정보 확인', '관리자 문의' 두 링크가 표시된다."
  - 구현: `CallbackPage.tsx:38-51` - ErrorMessage with helpLinks
  - 검증: `CallbackPage.test.tsx:165-193` (Help links test)

---

## 📝 관련 요구사항

**함께 구현됨**:
- **REQ-F-A1-2**: SSO 콜백 페이지 구현 (Commit fdee134)
  - REQ-F-A1-3는 REQ-F-A1-2의 에러 처리 부분

**의존성**:
- REQ-F-A1-1: 로그인 페이지 (사전 구현 완료)

---

**구현 완료일**: 2025-11-11
**Commit**: 2bd263b (refactor: Extract CallbackPage logic)
**총 소요 시간**: REQ-F-A1-2와 함께 구현 (~1.5시간)
**상태**: ✅ Done
