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
│   └── test/         # 테스트 페이지 전용 컴포넌트
│       ├── Timer.tsx            # 타이머 컴포넌트
│       ├── SaveStatus.tsx       # 자동 저장 상태 표시
│       ├── Question.tsx         # 문제 표시 컴포넌트
│       └── index.ts             # 중앙 export
├── hooks/            # Custom React Hooks
│   ├── useAuthCallback.ts
│   ├── useUserProfile.ts
│   ├── useNicknameCheck.ts
│   └── useAutosave.ts           # 자동 저장 로직 (NEW)
├── lib/              # 라이브러리 래퍼
│   └── transport/    # HTTP 통신 레이어 (Real/Mock 전환)
├── pages/            # 페이지 컴포넌트 (라우트별)
├── services/         # API 호출 서비스 레이어
│   ├── authService.ts
│   ├── profileService.ts
│   ├── questionService.ts
│   └── index.ts
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

## 성능 최적화

### 헬퍼 함수 최적화

#### 원칙: 컴포넌트 외부로 추출

렌더링할 때마다 재생성되는 헬퍼 함수는 컴포넌트 외부로 추출해야 합니다.

**❌ Bad: 컴포넌트 내부에 정의**

```typescript
const TestPage: React.FC = () => {
  // 매 렌더링마다 재생성됨
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return <div>{formatTime(timeRemaining)}</div>
}
```

**✅ Good: 컴포넌트 외부로 추출**

```typescript
/**
 * Helper: Format time as MM:SS
 * @param seconds - Time in seconds
 * @returns Formatted time string (e.g., "20:00")
 */
const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const TestPage: React.FC = () => {
  return <div>{formatTime(timeRemaining)}</div>
}
```

#### 언제 사용하는가?

| 패턴 | 사용 시기 | 예시 |
|------|-----------|------|
| **컴포넌트 외부 추출** | 순수 함수 (props/state에 의존하지 않음) | `formatTime`, `getTimerColor`, `convertLevelToBackend` |
| **useMemo** | state/props에 의존하는 계산 | `getStatusMessage` (checkStatus, errorMessage 의존) |
| **useCallback** | 이벤트 핸들러 | `handleNextClick`, `handleCheckClick` |

### 실제 예시

#### 예시 1: TestPage.tsx

```typescript
// ✅ 컴포넌트 외부로 추출 (순수 함수)
const getTimerColor = (seconds: number): string => {
  if (seconds > 15 * 60) return 'green'
  if (seconds > 5 * 60) return 'orange'
  return 'red'
}

const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const TestPage: React.FC = () => {
  const [timeRemaining, setTimeRemaining] = useState(1200)

  return (
    <div className={`timer ${getTimerColor(timeRemaining)}`}>
      {formatTime(timeRemaining)}
    </div>
  )
}
```

#### 예시 2: NicknameSetupPage.tsx

```typescript
const NicknameSetupPage: React.FC = () => {
  const { checkStatus, errorMessage } = useNicknameCheck()

  // ✅ useMemo로 메모이제이션 (state 의존)
  const statusMessage = useMemo(() => {
    if (checkStatus === 'available') {
      return {
        text: '사용 가능한 닉네임입니다.',
        className: 'status-message success',
      }
    }
    if (checkStatus === 'taken') {
      return {
        text: '이미 사용 중인 닉네임입니다.',
        className: 'status-message error',
      }
    }
    if (checkStatus === 'error' && errorMessage) {
      return {
        text: errorMessage,
        className: 'status-message error',
      }
    }
    return null
  }, [checkStatus, errorMessage])

  return <div>{statusMessage && <p>{statusMessage.text}</p>}</div>
}
```

#### 예시 3: SelfAssessmentPage.tsx

```typescript
// ✅ 컴포넌트 외부로 추출 (순수 함수 + 정적 상수)
const LEVEL_OPTIONS = [
  { value: 1, label: '1 - 입문', description: '기초 개념 학습 중' },
  { value: 2, label: '2 - 초급', description: '기본 업무 수행 가능' },
  // ...
]

const convertLevelToBackend = (level: number): string => {
  if (level === 1) return 'beginner'
  if (level === 2 || level === 3) return 'intermediate'
  if (level === 4 || level === 5) return 'advanced'
  throw new Error(`Invalid level: ${level}`)
}

const SelfAssessmentPage: React.FC = () => {
  const [level, setLevel] = useState<number | null>(null)

  const handleSubmit = async () => {
    const backendLevel = convertLevelToBackend(level!)
    await profileService.updateSurvey({ level: backendLevel, ... })
  }

  return <div>...</div>
}
```

### 최적화 체크리스트

- [ ] 순수 함수는 컴포넌트 외부로 추출
- [ ] 정적 상수 (LEVEL_OPTIONS, TIMER_THRESHOLDS 등)는 컴포넌트 외부에 정의
- [ ] state/props에 의존하는 계산은 `useMemo`
- [ ] 이벤트 핸들러는 `useCallback`
- [ ] 매 렌더링마다 새로운 객체/배열 생성 지양

---

## 컴포넌트 분할

### 원칙: 단일 책임 원칙 (Single Responsibility Principle)

큰 컴포넌트는 더 작고 집중된 컴포넌트로 분할하여 가독성과 유지보수성을 향상시킵니다.

### 언제 분할해야 하는가?

| 신호 | 조치 |
|------|------|
| 컴포넌트가 300줄 이상 | 하위 컴포넌트로 분할 고려 |
| 여러 가지 역할을 수행 | 각 역할을 별도 컴포넌트로 분리 |
| 복잡한 로직이 섞여 있음 | 커스텀 Hook으로 로직 추출 |
| 재사용 가능한 UI 패턴 | 공통 컴포넌트로 추출 |

### 실제 예시: TestPage 리팩토링

#### Before (386줄, 모든 로직이 한 파일)

```typescript
const TestPage: React.FC = () => {
  // 타이머 로직
  const [timeRemaining, setTimeRemaining] = useState(1200)
  const formatTime = (seconds) => { ... }
  const getTimerColor = (seconds) => { ... }

  // 자동 저장 로직
  const [saveStatus, setSaveStatus] = useState('idle')
  const [lastSavedAnswer, setLastSavedAnswer] = useState('')
  useEffect(() => {
    // 복잡한 autosave 로직...
  }, [answer])

  // 문제 렌더링 로직
  const renderQuestion = () => {
    if (question.item_type === 'multiple_choice') { ... }
    if (question.item_type === 'true_false') { ... }
    return <textarea />
  }

  return (
    <div>
      {/* 타이머 */}
      <div className={`timer ${getTimerColor(timeRemaining)}`}>
        {formatTime(timeRemaining)}
      </div>

      {/* 저장 상태 */}
      {saveStatus === 'saved' && <span>저장됨</span>}

      {/* 문제 */}
      {renderQuestion()}

      {/* 버튼 */}
      <button>다음</button>
    </div>
  )
}
```

#### After (분할된 구조)

**1. Timer 컴포넌트 (components/test/Timer.tsx)**
```typescript
interface TimerProps {
  timeRemaining: number
}

export const Timer: React.FC<TimerProps> = ({ timeRemaining }) => {
  const color = getTimerColor(timeRemaining)
  const formattedTime = formatTime(timeRemaining)

  return (
    <div className={`timer timer-${color}`}>
      <span className="timer-icon">⏱</span>
      <span className="timer-text">{formattedTime}</span>
    </div>
  )
}
```

**2. SaveStatus 컴포넌트 (components/test/SaveStatus.tsx)**
```typescript
export type SaveStatusType = 'idle' | 'saving' | 'saved' | 'error'

interface SaveStatusProps {
  status: SaveStatusType
}

export const SaveStatus: React.FC<SaveStatusProps> = ({ status }) => {
  if (status === 'idle') return null

  return (
    <div className={`save-status save-status-${status}`}>
      {status === 'saving' && <span>저장 중...</span>}
      {status === 'saved' && <span>저장됨</span>}
      {status === 'error' && <span>저장 실패</span>}
    </div>
  )
}
```

**3. Question 컴포넌트 (components/test/Question.tsx)**
```typescript
interface QuestionProps {
  question: QuestionData
  currentIndex: number
  totalQuestions: number
  answer: string
  onAnswerChange: (answer: string) => void
  disabled?: boolean
}

export const Question: React.FC<QuestionProps> = ({
  question,
  answer,
  onAnswerChange,
  ...props
}) => {
  // 문제 타입별 렌더링 로직만 집중
  return (
    <div className="question-container">
      <div className="question-stem">{question.stem}</div>
      {renderAnswerInput()}
    </div>
  )
}
```

**4. useAutosave 훅 (hooks/useAutosave.ts)**
```typescript
interface UseAutosaveOptions {
  sessionId: string | null
  currentQuestion: QuestionData | null
  answer: string
  questionStartTime: number
}

export function useAutosave(options: UseAutosaveOptions) {
  const [saveStatus, setSaveStatus] = useState<SaveStatusType>('idle')

  useEffect(() => {
    // 복잡한 autosave 로직 캡슐화
    const timer = setTimeout(async () => {
      setSaveStatus('saving')
      await questionService.autosave({ ... })
      setSaveStatus('saved')
    }, 1000)

    return () => clearTimeout(timer)
  }, [options.answer, ...])

  return { saveStatus }
}
```

**5. 리팩토링된 TestPage (150줄, 간결함)**
```typescript
const TestPage: React.FC = () => {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [questions, setQuestions] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answer, setAnswer] = useState('')
  const [timeRemaining, setTimeRemaining] = useState(1200)

  // Custom hook으로 autosave 로직 추출
  const { saveStatus } = useAutosave({
    sessionId,
    currentQuestion: questions[currentIndex],
    answer,
    questionStartTime,
  })

  return (
    <main className="test-page">
      <div className="test-container">
        {/* 컴포넌트로 분할된 깔끔한 구조 */}
        <div className="test-header">
          <Timer timeRemaining={timeRemaining} />
          <SaveStatus status={saveStatus} />
        </div>

        <Question
          question={questions[currentIndex]}
          currentIndex={currentIndex}
          totalQuestions={questions.length}
          answer={answer}
          onAnswerChange={setAnswer}
        />

        <button onClick={handleNextClick}>다음</button>
      </div>
    </main>
  )
}
```

### 컴포넌트 분할 전략

#### 1. Presentational Components (UI만 담당)

- Props를 받아서 UI만 렌더링
- 비즈니스 로직 없음
- 재사용 가능
- 예: `Timer`, `SaveStatus`, `Question`

#### 2. Container Components (로직 담당)

- 데이터 fetching
- State 관리
- 이벤트 핸들링
- 예: `TestPage`

#### 3. Custom Hooks (로직 재사용)

- 복잡한 상태 로직 캡슐화
- 여러 컴포넌트에서 재사용 가능
- 테스트 용이
- 예: `useAutosave`, `useNicknameCheck`

### 분할 후 이점

| 항목 | Before | After |
|------|--------|-------|
| 파일 크기 | 386줄 | 150줄 (TestPage) |
| 재사용성 | 낮음 | Timer, Question 등 재사용 가능 |
| 테스트 | 어려움 | 각 컴포넌트/훅 독립 테스트 가능 |
| 가독성 | 복잡함 | 명확한 구조 |
| 유지보수 | 어려움 | 각 파일이 단일 책임만 가짐 |

### 컴포넌트 분할 체크리스트

- [ ] 컴포넌트가 300줄 미만인가?
- [ ] 각 컴포넌트가 단일 책임만 가지는가?
- [ ] 복잡한 로직이 Custom Hook으로 분리되었는가?
- [ ] 재사용 가능한 UI가 별도 컴포넌트인가?
- [ ] Props 인터페이스가 명확한가?
- [ ] 각 컴포넌트를 독립적으로 테스트할 수 있는가?

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

- **v1.2** (2025-11-13): 컴포넌트 분할 패턴 추가
  - TestPage 리팩토링 (386줄 → 150줄)
  - Timer, SaveStatus, Question 컴포넌트 분리
  - useAutosave 커스텀 훅 생성
  - 컴포넌트 분할 전략 및 체크리스트 추가

- **v1.1** (2025-11-13): 성능 최적화 패턴 추가
  - 헬퍼 함수 컴포넌트 외부 추출 (TestPage, ProfileReviewPage)
  - useMemo를 활용한 계산 메모이제이션 (NicknameSetupPage)
  - 최적화 체크리스트 및 가이드 추가

- **v1.0** (2025-11-13): 초기 아키텍처 정의
  - Service Layer 도입
  - Page → Hooks → Service → Transport 패턴 확립
  - Mock/Real Transport 전환 시스템 구축
