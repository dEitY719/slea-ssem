# Frontend Architecture

SLEA-SSEM 프론트엔드 아키텍처 가이드

## 기술 스택

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Router**: React Router v6
- **Testing**: Vitest + Testing Library
- **Styling**: CSS (vanilla)

## 디렉토리 구조

```
src/frontend/src/
├── components/        # 재사용 가능한 UI 컴포넌트
├── hooks/            # Custom React Hooks
├── lib/              # 라이브러리 래퍼
│   └── transport/    # HTTP 통신 레이어 (Real/Mock 전환)
├── pages/            # 페이지 컴포넌트 (라우트별)
├── services/         # API 호출 서비스 레이어
├── utils/            # 유틸리티 함수
├── mocks/            # Mock 데이터
└── test/             # 테스트 설정
```

## 아키텍처 레이어

### 레이어 다이어그램

```
┌─────────────────────────────────────────────────┐
│  Page/Component Layer                            │
│  - UI 로직, 이벤트 핸들러                         │
│  - 사용자 인터랙션 처리                           │
│  - 컴포넌트 레벨 상태 관리                        │
└───────────────┬─────────────────────────────────┘
                │
                ├──────────┐
                │          │
         ┌──────▼────┐  ┌──▼──────────┐
         │  Hooks    │  │  Services    │
         │  (선택)    │  │  (필수)       │
         └─────┬─────┘  └──┬───────────┘
               │           │
               └─────┬─────┘
                     │
         ┌───────────▼───────────┐
         │  Service Layer         │
         │  - API 호출 중앙 집중화 │
         │  - 타입 정의            │
         │  - 비즈니스 로직        │
         └───────────┬────────────┘
                     │
         ┌───────────▼───────────┐
         │  Transport Layer       │
         │  - HTTP 통신           │
         │  - Real/Mock 전환      │
         │  - fetch wrapper       │
         └────────────────────────┘
```

## 데이터 흐름 패턴

### 패턴 1: Page → Hooks → Service → Transport

**언제 사용**: 복잡한 상태 관리가 필요하거나 여러 컴포넌트에서 재사용할 때

**예시: 닉네임 중복 확인**

```typescript
// ============================================================
// Page: UI 로직
// ============================================================
const NicknameSetupPage: React.FC = () => {
  // Hook을 통해 상태와 로직 캡슐화
  const { nickname, checkNickname, checkStatus } = useNicknameCheck()

  return (
    <div>
      <input value={nickname} onChange={(e) => setNickname(e.target.value)} />
      <button onClick={checkNickname}>중복 확인</button>
      {checkStatus === 'available' && <span>✓ 사용 가능</span>}
    </div>
  )
}

// ============================================================
// Hook: 상태 관리 + 비즈니스 로직
// ============================================================
export function useNicknameCheck() {
  const [nickname, setNickname] = useState('')
  const [checkStatus, setCheckStatus] = useState<'idle' | 'available' | 'taken'>('idle')

  const checkNickname = async () => {
    // 클라이언트 측 validation
    if (nickname.length < 3) {
      setError('닉네임은 3자 이상이어야 합니다.')
      return
    }

    // Service 호출
    const response = await profileService.checkNickname(nickname)
    setCheckStatus(response.available ? 'available' : 'taken')
  }

  return { nickname, setNickname, checkNickname, checkStatus }
}

// ============================================================
// Service: API 호출 중앙화
// ============================================================
export const profileService = {
  checkNickname(nickname: string): Promise<NicknameCheckResponse> {
    return transport.post('/profile/nickname/check', { nickname })
  }
}

// ============================================================
// Transport: HTTP 통신
// ============================================================
class RealTransport {
  async post<T>(url: string, data: any): Promise<T> {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    return response.json()
  }
}
```

**Hook을 사용하는 이유:**
- 복잡한 상태 관리 (nickname, checkStatus, errorMessage, suggestions)
- 클라이언트 측 validation 로직
- 여러 컴포넌트에서 재사용 가능
- 테스트 용이성 (Hook 단위 테스트 가능)

---

### 패턴 2: Page → Service → Transport

**언제 사용**: 단순 API 호출 (상태 관리 불필요, 한 곳에서만 사용)

**예시: 닉네임 등록**

```typescript
// ============================================================
// Page: Service 직접 호출
// ============================================================
const NicknameSetupPage: React.FC = () => {
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleNextClick = async () => {
    setIsSubmitting(true)
    try {
      // Hook 없이 Service 직접 호출
      await profileService.registerNickname(nickname)
      navigate('/self-assessment')
    } catch (error) {
      alert('등록 실패')
    } finally {
      setIsSubmitting(false)
    }
  }

  return <button onClick={handleNextClick}>다음</button>
}

// ============================================================
// Service
// ============================================================
export const profileService = {
  registerNickname(nickname: string): Promise<NicknameRegisterResponse> {
    return transport.post('/profile/register', { nickname })
  }
}

// ============================================================
// Transport
// ============================================================
transport.post('/profile/register', { nickname })
```

**Hook을 생략하는 이유:**
- 단순 CRUD 호출 (추가 상태 관리 불필요)
- 한 곳에서만 사용 (재사용성 불필요)
- 컴포넌트 내에서 충분히 처리 가능
- Hook 오버헤드 불필요

---

### 패턴 3: Hook만 독립적으로 사용

**언제 사용**: 여러 페이지에서 공통으로 사용하는 로직

**예시: 인증 콜백 처리**

```typescript
// ============================================================
// Hook: 인증 로직 캡슐화
// ============================================================
export function useAuthCallback(searchParams: URLSearchParams) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const userData = parseUserData(searchParams)
        const data = await authService.login(userData)
        saveToken(data.access_token)
        navigate('/home')
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    handleCallback()
  }, [searchParams])

  return { loading, error }
}

// ============================================================
// Page: Hook만 사용
// ============================================================
const CallbackPage: React.FC = () => {
  const [searchParams] = useSearchParams()
  const { loading, error } = useAuthCallback(searchParams)

  if (loading) return <LoadingSpinner />
  if (error) return <ErrorMessage message={error} />
  return null
}
```

---

## Service Layer 상세

### 구조

```typescript
// services/index.ts - 중앙 export
export * from './authService'
export * from './profileService'
export * from './questionService'

// services/profileService.ts
export interface NicknameCheckResponse {
  available: boolean
  suggestions: string[]
}

export const profileService = {
  getNickname(): Promise<UserProfileResponse> {
    return transport.get('/api/profile/nickname')
  },

  checkNickname(nickname: string): Promise<NicknameCheckResponse> {
    return transport.post('/profile/nickname/check', { nickname })
  },

  registerNickname(nickname: string): Promise<NicknameRegisterResponse> {
    return transport.post('/profile/register', { nickname })
  },

  updateSurvey(surveyData: SurveyUpdateRequest): Promise<SurveyUpdateResponse> {
    return transport.put('/profile/survey', surveyData)
  }
}
```

### Service Layer의 역할

1. **API 호출 중앙 집중화**: 모든 HTTP 요청은 Service를 통해 실행
2. **타입 안정성**: Request/Response 인터페이스 정의
3. **비즈니스 로직**: 데이터 변환, validation
4. **테스트 용이성**: Service만 mock하면 전체 API 테스트 가능

### Service 사용 예시

```typescript
// ❌ Bad: transport 직접 사용
const data = await transport.post('/api/auth/login', userData)

// ✅ Good: service 사용
const data = await authService.login(userData)
```

---

## Transport Layer 상세

### Mock/Real 전환 시스템

```typescript
// lib/transport/index.ts
function isMockMode(): boolean {
  // 1순위: URL 파라미터 (?mock=true)
  if (new URLSearchParams(window.location.search).get('mock') === 'true') {
    return true
  }

  // 2순위: 환경변수 (VITE_MOCK_API=true)
  return import.meta.env.VITE_MOCK_API === 'true'
}

export const transport = isMockMode() ? mockTransport : realTransport
```

### Real Transport

```typescript
// lib/transport/realTransport.ts
class RealTransport implements HttpTransport {
  private baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

  async post<T>(url: string, data: any): Promise<T> {
    const token = getToken()
    const response = await fetch(`${this.baseURL}${url}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: JSON.stringify(data)
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    return response.json()
  }
}
```

### Mock Transport

```typescript
// lib/transport/mockTransport.ts
class MockTransport implements HttpTransport {
  async post<T>(url: string, data: any): Promise<T> {
    await delay(500) // 실제 네트워크 딜레이 시뮬레이션

    if (url === '/profile/nickname/check') {
      return {
        available: true,
        suggestions: []
      } as T
    }

    throw new Error('Mock endpoint not configured')
  }
}
```

---

## 패턴 선택 가이드

| 상황 | 패턴 | 이유 |
|------|------|------|
| 복잡한 상태 관리 (여러 useState, useEffect) | Page → **Hook** → Service → Transport | Hook으로 상태 로직 캡슐화 |
| 클라이언트 측 validation 필요 | Page → **Hook** → Service → Transport | Hook에서 validation 처리 |
| 여러 컴포넌트에서 재사용 | Page → **Hook** → Service → Transport | Hook으로 로직 공유 |
| 단순 CRUD (Create, Read, Update, Delete) | Page → Service → Transport | Hook 오버헤드 불필요 |
| Form 제출 후 네비게이션 | Page → Service → Transport | 컴포넌트 내에서 직접 처리 |
| 한 번만 호출하는 API | Page → Service → Transport | 재사용성 불필요 |

---

## 실제 코드 예시

### 현재 프로젝트의 패턴 사용 현황

| 파일 | 패턴 | 복잡도 |
|------|------|--------|
| `NicknameSetupPage.tsx` | Hook (useNicknameCheck) + Service (registerNickname) | 중간 |
| `SelfAssessmentPage.tsx` | Service 직접 호출 | 낮음 |
| `TestPage.tsx` | Service 직접 호출 | 중간 |
| `ProfileReviewPage.tsx` | Service 직접 호출 | 낮음 |
| `CallbackPage.tsx` | Hook (useAuthCallback) | 중간 |
| `HomePage.tsx` | Hook (useUserProfile) | 중간 |

---

## 핵심 원칙

### ✅ DO

1. **모든 API 호출은 Service를 통해 실행**
   ```typescript
   await authService.login(userData)  // ✓
   ```

2. **복잡한 상태 관리는 Hook으로 캡슐화**
   ```typescript
   const { nickname, checkNickname } = useNicknameCheck()  // ✓
   ```

3. **타입 정의는 Service에 배치**
   ```typescript
   export interface LoginResponse { ... }  // ✓
   ```

4. **Transport는 Mock/Real 전환만 담당**
   ```typescript
   export const transport = isMockMode() ? mockTransport : realTransport  // ✓
   ```

### ❌ DON'T

1. **Page에서 transport 직접 호출 금지**
   ```typescript
   await transport.post('/api/auth/login', data)  // ✗
   ```

2. **불필요한 Hook 생성 금지**
   ```typescript
   // 단순 API 호출인데 Hook으로 만들 필요 없음
   function useRegisterNickname() { ... }  // ✗
   ```

3. **Service 없이 Hook에서 transport 직접 호출 금지**
   ```typescript
   // Hook 내에서
   await transport.post(...)  // ✗ - Service를 거쳐야 함
   ```

---

## 테스트 전략

### Service Layer 테스트

```typescript
import { vi } from 'vitest'
import { profileService } from './profileService'
import * as transport from '../lib/transport'

vi.mock('../lib/transport', () => ({
  transport: {
    post: vi.fn()
  }
}))

describe('profileService', () => {
  it('checkNickname calls correct endpoint', async () => {
    vi.mocked(transport.transport.post).mockResolvedValue({
      available: true,
      suggestions: []
    })

    const result = await profileService.checkNickname('testuser')

    expect(transport.transport.post).toHaveBeenCalledWith(
      '/profile/nickname/check',
      { nickname: 'testuser' }
    )
    expect(result.available).toBe(true)
  })
})
```

### Hook 테스트

```typescript
import { renderHook, waitFor } from '@testing-library/react'
import { useNicknameCheck } from './useNicknameCheck'
import * as profileService from '../services/profileService'

vi.mock('../services/profileService')

describe('useNicknameCheck', () => {
  it('checkNickname updates status to available', async () => {
    vi.mocked(profileService.profileService.checkNickname).mockResolvedValue({
      available: true,
      suggestions: []
    })

    const { result } = renderHook(() => useNicknameCheck())
    result.current.setNickname('testuser')
    await result.current.checkNickname()

    await waitFor(() => {
      expect(result.current.checkStatus).toBe('available')
    })
  })
})
```

---

## 환경 설정

### 개발 환경

```bash
# .env
VITE_MOCK_API=false  # Real 백엔드 사용
# VITE_API_BASE_URL은 주석 처리 (Vite proxy 사용)
```

### Vite Proxy 설정

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
```

### Mock 모드 활성화

**방법 1: 환경변수**
```bash
# .env
VITE_MOCK_API=true
```

**방법 2: URL 파라미터**
```
http://localhost:3000?mock=true
```

---

## 참고 자료

- **CLAUDE.md**: 프로젝트 전반적인 개발 가이드
- **docs/feature_requirement_mvp1.md**: MVP 기능 요구사항
- **tests/**: 테스트 예시 코드

---

## 버전 히스토리

- **v1.0** (2025-01-13): 초기 아키텍처 정의
  - Service Layer 도입
  - Page → Hooks → Service → Transport 패턴 확립
  - Mock/Real Transport 전환 시스템 구축
