# Color Scheme Documentation

이 문서는 프로젝트의 색상 스킴을 정의하고 관리하는 방법을 설명합니다.

## 색상 변수 위치

모든 색상 변수는 `/src/frontend/src/index.css` 파일의 `:root` 선택자에 정의되어 있습니다.

## 색상 체계

### 📄 Background Colors (배경색)

```css
--bg-page: #f9f9f9           /* 페이지 전체 배경 (거의 흰색~아이보리) */
--bg-card: #ffffff           /* 카드/모듈 배경 (흰색) */
--bg-card-hover: #f8f9fa     /* 카드 호버 배경 */
--bg-info: #ede9fe          /* 정보 박스 배경 (연한 보라) */
--bg-suggestion: #f8f9fa     /* 제안/힌트 박스 배경 */
```

### 🎨 Border Colors (테두리색)

```css
--border-card: #e5e7eb       /* 카드 테두리 (gray-200) */
--border-default: #ddd       /* 기본 테두리 */
--border-light: #e0e0e0      /* 밝은 테두리 */
```

### 🌈 Gradient (그라디언트)

```css
--gradient-primary: linear-gradient(90deg, #667eea 0%, #764ba2 100%)    /* 주요 그라디언트 (헤더, 타이틀) */
--gradient-accent: linear-gradient(135deg, #667eea 0%, #764ba2 100%)    /* 강조 그라디언트 (배경) */
```

### 🟠 Primary Colors (주요 색상 - 오렌지)

**용도**: 메인 액션 버튼 (시작하기, 로그인, 회원가입, 제출, 다음, 완료)

```css
--color-primary: #FF9900              /* 기본 오렌지 */
--color-primary-hover: #e68a00        /* 호버 시 */
--color-primary-disabled: #ffd699     /* 비활성화 */
--color-primary-shadow: rgba(255, 153, 0, 0.3)  /* 그림자 */
```

### 🟢 Secondary Colors (보조 색상 - 민트)

**용도**: 보조 액션 버튼 (중복확인, 닉네임 제안, 수정, 뒤로가기)

```css
--color-secondary: #00C7B7            /* 기본 민트 */
--color-secondary-hover: #00b3a5      /* 호버 시 */
--color-secondary-light: #e6f7f5      /* 밝은 민트 (배경) */
```

### 💜 Accent Colors (강조 색상 - 보라)

**용도**: 하이라이트, 선택 상태, 포커스, Info 박스 테두리

```css
--color-accent: #667eea               /* 기본 보라 */
--color-accent-dark: #5568d3          /* 진한 보라 */
--color-accent-light: #ede9fe         /* 연한 보라 (배경) */
--color-accent-hover: #5568d3         /* 호버 시 */
```

### ✏️ Text Colors (텍스트 색상)

```css
--text-primary: #333                  /* 주요 텍스트 (제목, 레이블) */
--text-secondary: #666                /* 보조 텍스트 (설명) */
--text-tertiary: #888                 /* 3차 텍스트 (힌트) */
--text-white: #ffffff                 /* 흰색 텍스트 */
--text-dark: #1a1a1a                  /* 진한 텍스트 */
```

### ⚠️ Status Colors (상태 색상)

```css
/* Success (성공) */
--color-success: #d4edda
--color-success-text: #155724
--color-success-border: #c3e6cb

/* Error (에러) */
--color-error: #f8d7da
--color-error-text: #721c24
--color-error-border: #f5c6cb

/* Warning (경고) */
--color-warning: #fff3cd
--color-warning-text: #856404
```

### 🎭 Shadow (그림자)

```css
--shadow-card: 0 2px 8px rgba(0, 0, 0, 0.08)           /* 카드 기본 그림자 */
--shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.12)         /* 호버 시 그림자 */
--shadow-button: 0 2px 8px rgba(255, 153, 0, 0.3)      /* 버튼 그림자 */
```

## 사용 방법

### CSS에서 사용

```css
.my-button {
  background-color: var(--color-primary);
  color: var(--text-white);
  border: 1px solid var(--border-card);
  box-shadow: var(--shadow-card);
}

.my-button:hover {
  background-color: var(--color-primary-hover);
}

.my-title {
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

### 색상 변경 방법

프로젝트 전체의 색상을 변경하려면 `/src/frontend/src/index.css` 파일의 `:root` 섹션에서 해당 변수 값만 변경하면 됩니다:

```css
/* 예: 오렌지 → 파란색으로 변경 */
:root {
  --color-primary: #0066cc;              /* #FF9900 → #0066cc */
  --color-primary-hover: #0052a3;        /* #e68a00 → #0052a3 */
  --color-primary-disabled: #99c2e6;     /* #ffd699 → #99c2e6 */
}
```

## 업데이트된 파일 목록

다음 파일들이 CSS 변수를 사용하도록 업데이트되었습니다:

- ✅ `src/index.css` - CSS 변수 정의
- ✅ `components/Header.css`
- ✅ `pages/HomePage.css`
- ✅ `pages/LoginPage.css`
- ✅ `pages/SignupPage.css`
- ✅ `pages/SelfAssessmentPage.css`
- ✅ `pages/TestPage.css`
- ✅ `pages/NicknameSetupPage.css`
- ✅ `pages/ProfileReviewPage.css`
- ✅ `pages/CallbackPage.css`
- ✅ `pages/TestResultsPage.css`

## 버튼 사용 가이드

### Primary Button (오렌지)
**사용 대상**: 주요 액션, 페이지 진행, 제출
- 시작하기, 로그인, 회원가입, 완료, 다음

```css
.my-primary-button {
  background-color: var(--color-primary);
  color: var(--text-white);
}
```

### Secondary Button (민트)
**사용 대상**: 보조 액션, 취소, 뒤로가기
- 중복확인, 닉네임 제안, 수정하기, 뒤로

```css
.my-secondary-button {
  background-color: var(--color-secondary);
  color: var(--text-white);
  /* 또는 outline 스타일 */
  background-color: var(--bg-card);
  color: var(--color-secondary);
  border: 2px solid var(--color-secondary);
}
```

### Accent Button (보라)
**사용 대상**: 특별한 상태, 재시도
- 재시도 버튼

```css
.my-accent-button {
  background-color: var(--color-accent);
  color: var(--text-white);
}
```

## 다크 모드 지원 (향후)

CSS 변수를 사용하기 때문에 다크 모드 추가도 쉽습니다:

```css
/* 다크 모드 예시 */
@media (prefers-color-scheme: dark) {
  :root {
    --bg-page: #1a1a1a;
    --bg-card: #2d2d2d;
    --text-primary: #e5e5e5;
    --text-secondary: #b0b0b0;
    /* ... */
  }
}
```

## 주의사항

1. **하드코딩 금지**: 색상은 항상 CSS 변수를 사용하세요. `#FF9900` 대신 `var(--color-primary)` 사용
2. **일관성 유지**: 같은 용도의 색상은 항상 같은 변수를 사용하세요
3. **네이밍 규칙**: 새로운 색상 변수를 추가할 때는 기존 네이밍 규칙을 따르세요
4. **문서 업데이트**: 새로운 변수를 추가하면 이 문서도 업데이트하세요

## 참고

- 현재 색상 스킴은 **밝은 테마 (Light Theme)** 기준입니다
- 모든 색상은 WCAG 접근성 기준을 고려하여 선택되었습니다
- 그라디언트는 헤더와 배경에 일관성 있게 적용되었습니다
