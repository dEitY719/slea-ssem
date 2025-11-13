# SLEA-SSEM Frontend

React + Vite 기반의 프론트엔드 애플리케이션

## Tech Stack

- **Framework**: React 18.2
- **Build Tool**: Vite 5.0
- **Language**: TypeScript 5.3
- **Router**: React Router DOM 6.20
- **Testing**: Vitest + Testing Library

## Quick Start

### 개발 서버 시작

```bash
cd src/frontend
npm run dev
```

개발 서버가 실행되면 `http://localhost:5173`에서 접속 가능합니다.

### 패키지 설치 (필요 시)

```bash
npm install
```

## Available Scripts

### `npm run dev`

개발 서버를 시작합니다. (기본 포트: 5173)

### `npm run build`

프로덕션 빌드를 생성합니다.

```bash
npm run build
```

- TypeScript 컴파일 후 Vite 빌드 실행
- 결과물은 `dist/` 디렉토리에 생성됩니다

### `npm run preview`

빌드된 결과물을 로컬 서버에서 미리보기합니다.

```bash
npm run preview
```

### `npm run test`

Vitest 테스트를 실행합니다.

```bash
npm run test
```

### `npm run test:ui`

Vitest UI 모드로 테스트를 실행합니다.

```bash
npm run test:ui
```

## 프론트엔드 + 백엔드 동시 실행

프로젝트를 풀스택으로 실행하려면 두 개의 터미널이 필요합니다:

```bash
# 터미널 1: 백엔드 (FastAPI)
./tools/dev.sh up              # http://localhost:8000

# 터미널 2: 프론트엔드 (React + Vite)
cd src/frontend
npm run dev                     # http://localhost:5173
```

## 프로젝트 구조

```text
src/frontend/
├── src/
│   ├── main.tsx           # 애플리케이션 진입점
│   ├── App.tsx            # 루트 컴포넌트
│   ├── index.css          # 글로벌 스타일
│   ├── components/        # 재사용 가능한 UI 컴포넌트
│   ├── hooks/             # Custom React Hooks
│   ├── lib/               # 라이브러리 래퍼
│   │   └── transport/     # HTTP 통신 레이어 (Real/Mock 전환)
│   ├── pages/             # 페이지 컴포넌트 (라우트별)
│   │   ├── LoginPage.tsx
│   │   └── LoginPage.css
│   ├── services/          # ⭐ API 서비스 레이어
│   │   ├── authService.ts
│   │   ├── profileService.ts
│   │   └── questionService.ts
│   ├── utils/             # 유틸리티 함수
│   ├── mocks/             # Mock 데이터
│   └── test/
│       └── setup.ts       # 테스트 설정
├── index.html             # HTML 템플릿
├── vite.config.ts         # Vite 설정 (proxy 포함)
├── tsconfig.json          # TypeScript 설정
├── package.json           # 의존성 관리
├── ARCHITECTURE.md        # ⭐ 아키텍처 가이드
└── README.md              # 이 문서
```

## 아키텍처

### 데이터 흐름 패턴

```
Page/Component
     ↓
   Hooks (선택)
     ↓
 Services (필수) ⭐
     ↓
  Transport
```

### API 호출 예시

```typescript
// ✅ Good: Service 사용
const data = await profileService.checkNickname('testuser')

// ❌ Bad: transport 직접 사용 금지
const data = await transport.post('/profile/nickname/check', ...)
```

### 패턴 선택 가이드

| 상황 | 패턴 |
|------|------|
| 복잡한 상태 관리 필요 | Page → **Hook** → Service → Transport |
| 여러 컴포넌트에서 재사용 | Page → **Hook** → Service → Transport |
| 단순 CRUD 호출 | Page → Service → Transport |
| Form 제출 | Page → Service → Transport |

**상세 내용**: [ARCHITECTURE.md](./ARCHITECTURE.md) 참고 ⭐

## 개발 가이드

### API 호출하기

**복잡한 상태 관리가 필요한 경우** (Hook 사용):
```typescript
const { nickname, checkNickname, checkStatus } = useNicknameCheck()
```

**단순 API 호출** (Service 직접 사용):
```typescript
await profileService.registerNickname(nickname)
```

### 새로운 API 추가하기

1. **services/에 타입 정의**
   ```typescript
   export interface NewFeatureRequest { ... }
   export interface NewFeatureResponse { ... }
   ```

2. **Service에 메서드 추가**
   ```typescript
   export const profileService = {
     newFeature(data: NewFeatureRequest): Promise<NewFeatureResponse> {
       return transport.post('/api/new-feature', data)
     }
   }
   ```

3. **Page/Component에서 사용**
   ```typescript
   const result = await profileService.newFeature(data)
   ```

### TypeScript 사용

모든 컴포넌트는 TypeScript로 작성되어야 합니다:

```tsx
// 타입 정의 예시
interface Props {
  title: string;
  onSubmit: () => void;
}

const Component: React.FC<Props> = ({ title, onSubmit }) => {
  // ...
}
```

### 테스트 작성

컴포넌트 테스트는 Testing Library를 사용합니다:

```tsx
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'

describe('Component', () => {
  it('renders correctly', () => {
    render(<Component />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

## 환경 설정

### Mock/Real 백엔드 전환

#### Real 백엔드 사용 (개발 권장)

```bash
# .env
VITE_MOCK_API=false
# VITE_API_BASE_URL은 주석 처리 (Vite proxy 사용)
```

#### Mock 모드 사용 (백엔드 없이 테스트)

**방법 1: 환경변수**
```bash
# .env
VITE_MOCK_API=true
```

**방법 2: URL 파라미터**
```
http://localhost:3000?mock=true
```

### Vite Proxy 설정

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',  // 백엔드 서버
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
```

### 기타 환경 변수

`.env` 파일에 환경 변수 추가:

```bash
VITE_MOCK_API=false
VITE_API_BASE_URL=/api  # 또는 http://localhost:8000
```

코드에서 사용:

```tsx
const apiUrl = import.meta.env.VITE_API_BASE_URL
```

## 트러블슈팅

### 포트가 이미 사용 중인 경우

```bash
# 다른 포트로 실행
PORT=3000 npm run dev
```

또는 `vite.config.ts`에서 포트 변경:

```typescript
export default defineConfig({
  server: {
    port: 3000
  }
})
```

### 타입 에러

```bash
# TypeScript 타입 체크
npx tsc --noEmit
```

## 참고 문서

- [Vite Documentation](https://vitejs.dev/)
- [React Documentation](https://react.dev/)
- [Vitest Documentation](https://vitest.dev/)
- [React Router Documentation](https://reactrouter.com/)
