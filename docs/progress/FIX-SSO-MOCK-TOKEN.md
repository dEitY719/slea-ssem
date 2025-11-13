# Fix: Profile Loading with SSO Mock Authentication

**Issue**: 프로필 정보를 불러오는데 실패: `Unexpected token '<', "<!doctype "... is not valid JSON`

**Root Cause**:
- `VITE_MOCK_API=false` + `?sso_mock=true` 환경에서
- 프론트엔드가 가짜 JWT 토큰(`mock_jwt_token_...`)을 생성하여 localStorage에 저장
- 이후 API 호출 시 백엔드가 이 가짜 토큰을 인증할 수 없어서 HTML 에러 페이지 반환
- 페이지 이동 시 URL 파라미터(`?api_mock=true`)가 사라지면서 mock 모드가 해제되어 실제 백엔드 호출 시도

## Solution Overview

### 1. SSO Mock 모드 분리 (`useAuthCallback.ts`)

**변경 전:**
- `api_mock=true`: 프론트엔드 mock (가짜 토큰 생성)
- 나머지: 실제 백엔드 호출

**변경 후:**
- `api_mock=true`: 프론트엔드 mock (백엔드 호출 없음, 가짜 토큰 생성)
- `sso_mock=true` + `api_mock=false`: **가짜 SSO 데이터를 백엔드에 전달하여 실제 JWT 토큰 받기**
- 둘 다 false: 실제 SSO 데이터로 백엔드 호출

```typescript
if (isSsoMock) {
  // SSO mock mode: 가짜 SSO 데이터를 생성하여 백엔드에 전달
  // 백엔드는 이를 처리하여 실제 JWT 토큰 반환
  console.log('🎭 SSO mock mode: 가짜 SSO 데이터로 백엔드 호출')
  userData = {
    knox_id: 'test_mock_user_' + Date.now(),
    name: 'Test Mock User',
    dept: 'Engineering',
    business_unit: 'S.LSI',
    email: `test_mock_${Date.now()}@samsung.com`,
  }
}
```

### 2. Mock 모드 지속성 (`transport/index.ts`)

**문제:** URL 파라미터(`?api_mock=true`)가 페이지 이동 시 사라지면 mock 모드 해제

**해결:** localStorage에 mock 플래그 저장

```typescript
function isMockMode(): boolean {
  // Priority: URL param > localStorage > Environment variable
  const urlParams = new URLSearchParams(window.location.search)
  const mockFlag = urlParams.get('api_mock') ?? urlParams.get('mock')
  if (mockFlag === 'true') {
    localStorage.setItem('slea_ssem_api_mock', 'true')
    return true
  }

  // Check localStorage (persists across page navigation)
  const storedMockFlag = localStorage.getItem('slea_ssem_api_mock')
  if (storedMockFlag === 'true') return true

  return import.meta.env.VITE_MOCK_API === 'true'
}
```

### 3. 로그아웃 시 Mock 플래그 제거 (`auth.ts`)

```typescript
export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem('slea_ssem_api_mock')  // 추가
}
```

## Implementation Details

### Modified Files

1. **`src/frontend/src/hooks/useAuthCallback.ts`**
   - `sso_mock=true`일 때 가짜 SSO 데이터 생성하여 백엔드 호출
   - 백엔드에서 실제 JWT 토큰 받기

2. **`src/frontend/src/lib/transport/index.ts`**
   - localStorage에 mock 플래그 저장하여 페이지 이동 후에도 유지
   - 우선순위: URL param > localStorage > Environment variable

3. **`src/frontend/src/utils/auth.ts`**
   - `removeToken()`이 mock 플래그도 함께 제거

### Test Coverage

#### New Tests

1. **`src/frontend/src/lib/transport/__tests__/mockPersistence.test.ts`** (신규 파일)
   - Mock 모드가 localStorage를 통해 지속되는지 테스트
   - URL 파라미터 우선순위 테스트

2. **`src/frontend/src/pages/__tests__/CallbackPage.test.tsx`**
   - `sso_mock=true` 케이스 추가: 백엔드 호출 및 실제 JWT 수신 확인

3. **`src/frontend/src/utils/__tests__/auth.test.ts`**
   - `removeToken()`이 mock 플래그도 제거하는지 테스트

#### Test Results

```bash
✓ src/pages/__tests__/CallbackPage.test.tsx (10 tests)
✓ src/utils/__tests__/auth.test.ts (8 tests)
✓ src/lib/transport/__tests__/mockPersistence.test.ts (5 tests)
```

## Usage Scenarios

### Scenario 1: 프론트엔드만 테스트 (백엔드 없음)
```
URL: /auth/callback?api_mock=true
결과: 
- 백엔드 호출 없음
- 가짜 JWT 토큰 생성
- 모든 API가 mock 응답 반환
```

### Scenario 2: SSO Mock + 실제 백엔드
```
URL: /auth/callback?sso_mock=true
결과:
- 가짜 SSO 데이터 생성
- 백엔드 /api/auth/login 호출
- 실제 JWT 토큰 받음
- 이후 모든 API는 실제 백엔드 호출
```

### Scenario 3: 실제 SSO + 실제 백엔드 (프로덕션)
```
URL: /auth/callback?knox_id=...&name=...&...
결과:
- 실제 SSO 데이터 파싱
- 백엔드 /api/auth/login 호출
- 실제 JWT 토큰 받음
```

## Backward Compatibility

- ✅ 기존 `mock=true` 파라미터 계속 지원 (`api_mock=true`와 동일)
- ✅ 기존 테스트 모두 통과
- ✅ 기존 mock transport 로직 변경 없음

## Benefits

1. **개발 환경 유연성**: 백엔드 없이도 프론트엔드 테스트 가능
2. **백엔드 통합 테스트**: SSO mock으로 백엔드 연동 테스트 가능
3. **상태 지속성**: 페이지 이동 후에도 mock 모드 유지
4. **명확한 분리**: API mock vs SSO mock 명확히 구분

## Future Improvements

1. Mock 모드 UI 표시 (개발 환경에서 현재 모드 확인)
2. Mock 데이터 커스터마이징 (URL 파라미터로 사용자 지정)
3. Mock 모드 만료 시간 설정 (자동 해제)

## Related Issues

- Branch: `cursor/fix-profile-loading-due-to-fake-sso-token-0ae3`
- Original Error: `Unexpected token '<', "<!doctype "... is not valid JSON`
