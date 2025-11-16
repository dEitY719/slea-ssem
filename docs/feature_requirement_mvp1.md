# Feature Requirement - MVP 1.0.0

**Project**: SLEA-SSEM (S.LSI Education AI Teacher)
**Version**: 1.0
**Last Updated**: 2025-11-06
**Status**: In Development

---

## 📌 Executive Summary

SLEA-SSEM MVP 1.0.0은 S.LSI 임직원의 **AI 역량 수준을 객관적으로 측정하고 등급화**하는 시스템입니다. Samsung AD SSO를 통한 가입, 적응형 2단계 레벨 테스트, LLM 기반 자동 채점·해설, 그리고 상대 순위 제시로 구성됩니다. 핵심 기능(문제 생성/채점)은 **Multi-AI-Agent 아키텍처**로 자동화되며, 관리자 개입을 최소화합니다.

**Target Users**: S.LSI 전사 임직원(총 ~7000명 기준)

---

## 🎯 Scope (MVP 1.0.0)

### 포함 (In Scope)

- ✅ Samsung AD 기반 사용자 인증
- ✅ 닉네임 등록 및 중복 검증
- ✅ **닉네임 재설정 (기존 사용자 프로필 수정)**
- ✅ **자기평가 정보 수정**
- ✅ 자기평가 정보 수집 (수준, 경력, 직군, 업무, 관심분야)
- ✅ LLM 기반 동적 문항 생성 (1~n차 적응형)
- ✅ 객관식/OX/주관식 혼합 문항 지원
- ✅ LLM 기반 자동 채점 및 부분점수
- ✅ 즉시 피드백 및 해설 생성
- ✅ 5등급 체계 산출 (Beginner ~ Elite)
- ✅ 상대 순위 및 백분위 표시
- ✅ 결과 저장 및 재응시 기능
- ✅ **테스트 진행 중 실시간 응답 저장**
- ✅ **중단 후 재개 기능 (20분 초과 시 재개 안내)**
- ✅ **20분 시간 제한 타이머 및 초과 처리**
- ✅ 결과 공유용 배지/이미지 (사내 + 특수 배지)
- ✅ **재미 모드 (카테고리 선택형 퀴즈 + 참여 배지/포인트)**
- ✅ 마케팅, 반도체, 센서, RTL 등 "재미" 카테고리 문항
- ✅ **학습 일정 예고 프리뷰 (MVP 2.0 미리보기)**

### 미포함 (Out of Scope)

- ❌ 정식 학습 일정 자동 생성 및 코디네이팅 (MVP 2.0)
- ❌ RAG 기반 문항 생성 (MVP 2.0)
- ❌ 외부 결제/과금 시스템
- ❌ 관리자 콘솔 고도화
- ❌ 학습 아이템 등록/검색 (MVP 2.0)
- ❌ 커뮤니티 기능 (MVP 2.0)

---

## 👥 Key Roles & System Components

### 사용자

- **임직원 (Employee)**: 가입, 레벨 테스트 응시, 결과 확인

### LLM 기반 에이전트 (Intelligent Components)

| 에이전트 | 역할 | 담당 시나리오 | 책임 |
|---------|------|---------|--------|
| **Item-Gen-Agent** | 문항 생성 | 시나리오 1-2 | LLM + Prompt를 통한 동적 문항 생성 (적응형 조정) |
| **Scoring-Agent** | 주관식 채점 | 시나리오 1-3 | LLM + Prompt를 통한 주관식 답변 평가 및 부분점수 산출 |
| **Explain-Agent** | 해설 생성 | 시나리오 1-3 | LLM + Prompt를 통한 정답/오답 해설 및 학습 자료 생성 |

### 비즈니스 로직 서비스 (Legacy Components)

| 서비스 | 역할 | 담당 시나리오 | 책임 |
|------|------|---------|--------|
| **Auth-Service** | 인증 관리 | 시나리오 0 | Samsung AD 통합, 토큰 발급, 세션 관리 |
| **Profile-Service** | 프로필 관리 | 시나리오 0 | 닉네임 검증, 중복 체크, 사용자 프로필 저장 |
| **Survey-Service** | 자기평가 관리 | 시나리오 1-1 | 폼 데이터 검증, DB 저장 |
| **Rank-Service** | 순위 산출 | 시나리오 1-5 | 최종 등급 계산, 상대 순위 및 백분위 산출 |
| **History-Service** | 이력 관리 | 시나리오 1-6 | 응시 이력 조회, 비교 분석 |

### 운영자 (선택)

- **관리자**: (향후) 문항 품질 모니터링, 신고 처리, 보정

---

# 📋 FRONTEND REQUIREMENTS

## REQ-F-A1: 로그인 화면 (Samsung AD)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-F-A1-1** | 로그인 페이지에 "Samsung AD로 로그인" 버튼을 명확하게 표시해야 한다. | **M** |
| **REQ-F-A1-2** | SSO 콜백 페이지를 구현하여 토큰을 안전하게 저장하고 홈화면으로 리다이렉트해야 한다. | **M** |
| **REQ-F-A1-3** | **로그인 실패 시 명확한 에러 메시지를 표시하고, "계정 정보 확인" 링크 및 "관리자 문의" 헬프 링크를 함께 제공해야 한다.** | **M** |

**수용 기준**:

- "로그인 버튼 클릭 후 Samsung AD 로그인 페이지로 리다이렉트된다."
- "로그인 성공 후 3초 내 홈화면으로 이동한다."
- "**로그인 실패 시, 에러 메시지와 함께 '계정 정보 확인', '관리자 문의' 두 링크가 표시된다.**"

---

## REQ-F-A2: 닉네임 설정 화면

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-F-A2-1** | 홈화면에서 "시작하기" 클릭 시, nickname == NULL인 경우 닉네임 설정 페이지로 리다이렉트해야 한다. | **M** |
| **REQ-F-A2-2** | 닉네임 입력 필드와 "중복 확인" 버튼을 제공해야 한다. | **M** |
| **REQ-F-A2-3** | 유효하지 않은 닉네임(너무 짧음, 특수문자 등) 입력 시 실시간으로 에러 메시지를 표시해야 한다. | **M** |
| **REQ-F-A2-4** | 닉네임 중복 시 대안 3개를 시각적으로 제안해야 한다. | **S** |
| **REQ-F-A2-5** | 금칙어를 포함한 닉네임 거부 시, 거부 사유를 명확하게 안내해야 한다. | **S** |
| **REQ-F-A2-6** | 중복이 없을 때 "사용 가능" 상태를 표시하고, "다음" 버튼을 활성화해야 한다. | **M** |
| **REQ-F-A2-7** | "다음" 버튼 클릭 시, users.nickname을 업데이트하고 자기평가 입력 페이지로 리다이렉트해야 한다. | **M** |

**수용 기준**:

- "홈화면 '시작하기' 클릭 시, nickname이 NULL이면 닉네임 설정 페이지로 이동한다."
- "닉네임 입력 후 1초 내 '중복 확인' 결과가 표시된다."
- "중복 시 3개의 대안이 제안된다."
- "금칙어 포함 시 거부 사유가 표시된다."
- "'다음' 버튼 클릭 시, users.nickname이 업데이트되고 자기평가 입력 페이지로 이동한다."

---

## REQ-F-A2-2: 자기평가 입력 화면 (프로필 설정)

**Note**: 이 화면은 프로필 설정의 일부로, 레벨 테스트 직전에 수행됩니다. REQ-F-B1과 동일한 기능입니다.

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-F-A2-2-1** | 닉네임 설정 완료 후 또는 "시작하기" 클릭 시 (nickname 있고 profile 없음), 자기평가 입력 페이지로 이동해야 한다. | **M** |
| **REQ-F-A2-2-2** | 입력 항목을 명확하게 레이아웃하고 다음을 포함해야 한다: <br> - 본인이 생각하는 수준 (1~5 슬라이더, 숫자가 클수록 수준이 높음) <br> - 경력(연차): 회사에 입사한 연차 입력 (숫자 또는 범위 선택 드롭다운) <br> - 직군: SW, HW, 마케팅, 기획, 인사 등 드롭다운 <br> - 담당 업무: 텍스트 입력 필드 <br> - 관심분야: AI, Backend, Frontend 등 체크박스 다중 선택 | **M** |
| **REQ-F-A2-2-3** | 필수 필드 누락 시, 누락된 필드를 명확히 표시하고 오류 메시지를 보여야 한다. | **M** |
| **REQ-F-A2-2-4** | 모든 필수 필드가 입력되면 "완료" 버튼이 활성화되어야 한다. | **M** |
| **REQ-F-A2-2-5** | "완료" 버튼 클릭 시, user_profile 테이블에 저장하고 프로필 리뷰 페이지로 리다이렉트해야 한다. | **M** |

**수용 기준**:

- "닉네임 설정 완료 후 자기평가 입력 페이지로 자동 이동한다."
- "모든 필수 필드를 입력한 후 '완료' 버튼이 활성화된다."
- "유효하지 않은 값 입력 시 필드 옆에 에러 메시지가 표시된다."
- "제출 후 로딩 상태를 표시한다."
- "'완료' 버튼 클릭 시, user_profile이 저장되고 프로필 리뷰 페이지로 이동한다."

---

## REQ-F-A2-Signup: 통합 회원가입 화면 (헤더 "회원가입" 버튼)

**Note**: 홈화면 헤더의 "회원가입" 버튼을 통해 닉네임 + 자기평가를 한 페이지에서 입력하는 대체 가입 플로우입니다. "시작하기" 플로우(닉네임 → 자기평가 → 프로필 리뷰)와는 별도로 제공됩니다.

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-F-A2-Signup-1** | 홈화면 헤더 오른쪽 상단에 "회원가입" 버튼을 표시해야 한다. nickname == NULL일 때만 표시하고, nickname != NULL일 때는 숨김 처리해야 한다. | **M** |
| **REQ-F-A2-Signup-2** | "회원가입" 버튼 클릭 시, 통합 회원가입 페이지(/signup)로 이동해야 한다. | **M** |
| **REQ-F-A2-Signup-3** | 통합 회원가입 페이지에 닉네임 입력 섹션을 표시해야 한다: <br> - 닉네임 입력 필드 <br> - "중복 확인" 버튼 <br> - 실시간 유효성 검사 및 에러 메시지 <br> - 중복 시 대안 3개 제안 (선택) | **M** |
| **REQ-F-A2-Signup-4** | 통합 회원가입 페이지에 자기평가 입력 섹션을 표시해야 한다: <br> - 수준 (1~5 슬라이더) <br> - 경력(연차) <br> - 직군 <br> - 담당 업무 <br> - 관심분야 (다중 선택) | **M** |
| **REQ-F-A2-Signup-5** | 닉네임 중복 확인 완료 + 모든 필수 필드 입력 시 "가입 완료" 버튼을 활성화해야 한다. | **M** |
| **REQ-F-A2-Signup-6** | "가입 완료" 버튼 클릭 시, users.nickname 업데이트 + user_profile 저장을 동시에 수행하고, 홈화면으로 리다이렉트해야 한다. | **M** |
| **REQ-F-A2-Signup-7** | 가입 완료 후 홈화면 재진입 시, 헤더의 "회원가입" 버튼이 사라져야 한다. (nickname != NULL) | **M** |

**수용 기준**:

- "nickname == NULL 상태에서만 헤더에 '회원가입' 버튼이 표시된다."
- "'회원가입' 버튼 클릭 시 통합 회원가입 페이지로 이동한다."
- "한 페이지에서 닉네임과 자기평가를 모두 입력할 수 있다."
- "닉네임 중복 확인이 정상 작동한다."
- "필수 필드 누락 시 '가입 완료' 버튼이 비활성화된다."
- "'가입 완료' 클릭 시 nickname + profile이 모두 저장되고 홈화면으로 리다이렉트된다."
- "nickname != NULL 상태에서는 '회원가입' 버튼이 숨겨진다."

**UX 이점**:

- "시작하기" 플로우(닉네임 → 자기평가 → 프로필 리뷰)보다 단계가 적어 빠른 가입 가능
- 가입 후 바로 테스트를 시작하지 않아도 되므로, 플랫폼 탐색이 자유로움
- 2가지 진입 경로 제공으로 사용자 선택권 향상

---

## REQ-F-A2-Profile-Access: 헤더 닉네임 표시 및 드롭다운 메뉴

**Note**: 로그인 완료 후 (nickname != NULL), 원래 "회원가입" 버튼이 있던 헤더 위치에 사용자의 닉네임을 표시하고, 클릭 시 드롭다운 메뉴를 표시하여 프로필 수정 등의 기능에 접근할 수 있도록 합니다.

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-F-A2-Profile-Access-1** | 로그인 완료 후 (nickname != NULL), 홈화면 헤더 오른쪽 상단에 사용자의 닉네임을 표시해야 한다. "회원가입" 버튼이 있던 위치에 표시한다. | **M** |
| **REQ-F-A2-Profile-Access-2** | 헤더의 닉네임은 클릭 가능한 버튼 형태로 표시되어야 한다. (호버 시 시각적 피드백 제공: 색상 변경, 배경 강조 등) | **M** |
| **REQ-F-A2-Profile-Access-3** | 닉네임 클릭 시, 드롭다운 메뉴가 닉네임 아래에 표시되어야 한다. | **M** |
| **REQ-F-A2-Profile-Access-4** | 드롭다운 메뉴에는 다음 항목들이 포함되어야 한다: <br> - "프로필 수정" (필수) <br> - "로그아웃" (선택, 향후 추가 가능) <br> - 기타 사용자 관련 기능 (선택) | **M** |
| **REQ-F-A2-Profile-Access-5** | 드롭다운 메뉴의 "프로필 수정" 항목 클릭 시, 프로필 수정 페이지(/profile/edit)로 리다이렉트해야 한다. | **M** |
| **REQ-F-A2-Profile-Access-6** | 드롭다운 메뉴 외부 클릭 시, 메뉴가 자동으로 닫혀야 한다. | **M** |
| **REQ-F-A2-Profile-Access-7** | nickname == NULL 상태에서는 "회원가입" 버튼을 표시하고, nickname != NULL 상태에서는 닉네임을 표시해야 한다. (상호 배타적) | **M** |
| **REQ-F-A2-Profile-Access-8** | 모든 페이지에서 헤더의 닉네임이 일관되게 표시되어야 한다. (전역 헤더 컴포넌트) | **M** |

**수용 기준**:

- "nickname != NULL 상태에서 헤더 오른쪽 상단에 닉네임이 표시된다."
- "nickname == NULL 상태에서는 '회원가입' 버튼이 표시되고, nickname != NULL 상태에서는 닉네임이 표시된다."
- "닉네임 클릭 시 드롭다운 메뉴가 표시된다."
- "드롭다운 메뉴에 '프로필 수정' 항목이 포함된다."
- "'프로필 수정' 클릭 시 프로필 수정 페이지로 이동한다."
- "드롭다운 메뉴 외부 클릭 시 메뉴가 닫힌다."
- "닉네임 호버 시 시각적 피드백(색상 변경, 배경 강조 등)이 제공된다."
- "모든 페이지에서 헤더의 닉네임이 일관되게 표시된다."

**UX 이점**:

- 사용자가 현재 로그인 상태와 닉네임을 한눈에 확인 가능
- 드롭다운 메뉴 패턴으로 프로필 관련 기능을 그룹화하여 직관적인 접근 제공
- 향후 로그아웃, 설정 등 추가 기능을 쉽게 확장 가능
- "회원가입" → "닉네임" 전환으로 가입 상태 변화를 시각적으로 표현

---

## REQ-F-A2-Edit: 프로필 수정 화면 (닉네임/자기평가 변경)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-F-A2-Edit-1** | 대시보드 또는 프로필 메뉴에서 "프로필 수정" 옵션을 제공해야 한다. 헤더의 닉네임 클릭 → 드롭다운 메뉴 → "프로필 수정" 클릭으로도 접근 가능해야 한다. | **M** |
| **REQ-F-A2-Edit-2** | 기존 닉네임을 표시하고, 사용자가 새로운 닉네임으로 변경할 수 있어야 한다. | **M** |
| **REQ-F-A2-Edit-3** | 닉네임 중복 확인 시, 기존 닉네임(현재 사용 중)은 제외하고 검증해야 한다. | **M** |
| **REQ-F-A2-Edit-4** | 닉네임 변경 후 "저장" 버튼 클릭 시, DB에 업데이트되고 "저장되었습니다" 메시지를 표시해야 한다. | **M** |
| **REQ-F-A2-Edit-5** | 자기평가 정보(수준, 경력, 직군, 업무, 관심분야)도 수정할 수 있어야 한다. | **M** |
| **REQ-F-A2-Edit-6** | 수정된 자기평가 정보는 다음 테스트 응시 시 자동으로 반영되어야 한다. | **M** |

**수용 기준**:

- "프로필 수정 페이지에서 현재 닉네임이 표시된다."
- "헤더의 닉네임 클릭 → 드롭다운 메뉴 → '프로필 수정' 클릭으로 프로필 수정 페이지에 접근할 수 있다."
- "새 닉네임 입력 후 중복 확인 시, 기존 닉네임과의 충돌을 무시하고 검증한다."
- "저장 버튼 클릭 후 1초 내 확인 메시지가 표시된다."
- "페이지 새로고침 시 변경된 닉네임이 반영된다."

---

## REQ-F-A3: 개인정보 수집 및 이용 동의

**Note**: 홈화면에서 "시작하기" 클릭 시, 개인정보 동의를 먼저 확인합니다.

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-F-A3-1** | 홈화면에서 "시작하기" 클릭 시, 개인정보 수집·이용 동의 모달/페이지를 표시해야 한다. | **M** |
| **REQ-F-A3-2** | 동의 내용에는 수집 항목(닉네임, 자기평가 정보, 테스트 응답, 결과), 이용 목적, 보유 기간을 명시해야 한다. | **M** |
| **REQ-F-A3-3** | 사용자가 "동의함" 선택 시에만 다음 단계(닉네임 설정 또는 프로필 확인)로 진행할 수 있어야 한다. | **M** |
| **REQ-F-A3-4** | 사용자가 "동의하지 않음" 선택 시, 홈화면으로 돌아가며 테스트를 진행할 수 없어야 한다. | **M** |
| **REQ-F-A3-5** | 동의 여부는 user 테이블에 저장되고, 이미 동의한 사용자는 다시 표시하지 않아야 한다. | **M** |

**수용 기준**:

- "홈화면 '시작하기' 클릭 시, 동의하지 않은 사용자에게만 개인정보 동의 모달/페이지가 표시된다."
- "동의 내용이 명확하게 표시된다."
- "'동의함' 선택 시, 동의 여부가 DB에 저장되고 다음 단계로 진행한다."
- "'동의하지 않음' 선택 시, 홈화면으로 돌아간다."
- "이미 동의한 사용자는 개인정보 동의 단계를 건너뛴다."

**현재 흐름**:
- 홈화면 → "시작하기" 클릭 → **개인정보 동의 확인** → 닉네임 설정/프로필 확인 → 자기평가 입력 → 프로필 리뷰 → 레벨 테스트

---

## REQ-F-B1: 자기평가 입력 화면 (Deprecated - REQ-F-A2-2로 통합)

**⚠️ Note**: 이 요구사항은 **REQ-F-A2-2**로 통합되었습니다.

REQ-F-B1은 원래 "레벨 테스트 시작 전 자기평가 입력"으로 정의되었으나, 실제로는 **프로필 설정의 일부**입니다.
홈화면 "시작하기" → 닉네임 설정 → **자기평가 입력 (REQ-F-A2-2)** → 프로필 리뷰 → 레벨 테스트 시작 순서로 진행됩니다.

**REQ-F-B1-1, REQ-F-B1-2, REQ-F-B1-3는 REQ-F-A2-2-1, REQ-F-A2-2-2, REQ-F-A2-2-3에 해당합니다.**

자세한 내용은 **REQ-F-A2-2: 자기평가 입력 화면 (프로필 설정)** 섹션을 참조하세요.

---

## REQ-F-B2: 레벨테스트용 문항 풀이 화면

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-F-B2-1** | 생성된 문항을 순차적으로 표시하고, 사용자가 답안을 입력하고 제출할 수 있는 UI를 제공해야 한다. | **M** |
| **REQ-F-B2-2** | 문항 풀이 중 진행률 표시(예: 3/5), 응답 입력 필드, "다음" 버튼, 남은 시간(타이머)을 제공해야 한다. | **M** |
| **REQ-F-B2-3** | 각 문항 제출 후 1초 내에 "정답입니다" 또는 "오답입니다" 토스트/피드백을 표시해야 한다. | **M** |
| **REQ-F-B2-4** | 주관식 답변의 부분점수(예: 70점)를 명확하게 표시해야 한다. | **M** |
| **REQ-F-B2-5** | **20분 제한 타이머를 화면 상단에 표시**하고, 시간이 지날수록 색상이 변해야 한다(녹색 → 주황색 → 빨간색). | **M** |
| **REQ-F-B2-6** | **테스트 진행 중 각 응답은 자동으로 실시간 저장(Autosave)되어야 한다.** 저장 완료 시 화면에 "저장됨" 표시를 해야 한다. | **M** |
| **REQ-F-B2-7** | **20분 초과 시, "시간이 초과되었습니다" 모달을 표시하고, 기존 진행 상황에서 재개할 수 있는 버튼을 제공해야 한다.** | **M** |

**수용 기준**:

- "문항이 1개씩 순차적으로 표시된다."
- "각 문항 제출 후 1초 내 피드백이 표시된다."
- "진행률이 실시간으로 업데이트된다."
- "**20분 타이머가 화면 상단에 표시되고, 시간이 감소함에 따라 색상이 변한다.**"
- "**각 응답 입력 후 2초 내에 '저장됨' 메시지가 표시된다.**"
- "**시간 초과 시 현재 상태가 저장되고, 재개 옵션이 제공된다.**"

---

## REQ-F-B3: 해설 화면

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-F-B3-1** | 각 문항의 정답/오답 해설과 참고 링크를 보기 좋게 표시해야 한다. | **M** |
| **REQ-F-B3-2** | 해설 페이지에서 "다음 문항" 또는 "결과 보기" 네비게이션을 제공해야 한다. | **M** |

**수용 기준**:

- "해설에 정답 설명과 참고 링크가 포함되어 있다."
- "링크가 새 탭에서 열린다."

---

## REQ-F-B4: 최종 결과 페이지

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-F-B4-1** | 최종 등급(1~5), 점수, 상대 순위, 백분위를 시각적으로 표시해야 한다. | **M** |
| **REQ-F-B4-2** | **사용자의 등급에 따른 배지(시작자/중급자/엘리트 등)를 결과 페이지에 시각적으로 표시해야 한다.** 엘리트 등급인 경우, 추가 특수 배지(Agent Specialist 등)도 함께 표시하고, "마스터 클래스 강사 추천" 또는 "커뮤니티 기여자 등록" 링크를 제공해야 한다. | **M** |
| **REQ-F-B4-3** | **결과 화면에 "전사 상대 순위 및 분포" 시각화를 표시해야 한다:** <br> - 최근 90일 응시자의 등급 분포 막대 차트 (Beginner ~ Elite) <br> - 사용자의 현재 위치를 차트에 하이라이트 <br> - "상위 28% (순위 3/506)"과 같은 텍스트 요약 | **M** |
| **REQ-F-B4-4** | 모집단 < 100일 경우, "분포 신뢰도 낮음" 라벨을 눈에 띄게 표시해야 한다. | **S** |
| **REQ-F-B4-5** | 결과 페이지에 "향후 학습 계획" 안내 문구 및 MVP 2.0 예고를 포함해야 한다. | **S** |
| **REQ-F-B4-6** | 사용자가 공유용 배지/이미지를 다운로드할 수 있는 버튼을 제공해야 한다. | **S** |

**수용 기준**:

- "등급(1~5), 점수, 순위/모집단, 백분위가 동시에 표시된다."
- "**등급 배지가 시각적으로 표시되고, 엘리트 등급인 경우 특수 배지가 함께 표시된다.**"
- "**분포 차트에 사용자 위치가 하이라이트되고, 텍스트 요약이 표시된다.**"
- "배지 다운로드 버튼이 클릭 가능하다."

---

## REQ-F-B5: 재응시 및 비교 화면

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-F-B5-1** | 결과 페이지에 "이전 응시 정보 비교" 섹션을 표시하고, 이전 등급/점수와 현재 정보를 간단한 차트/텍스트로 비교해야 한다. | **S** |
| **REQ-F-B5-2** | 대시보드 또는 결과 페이지에 "레벨 테스트 재응시" 버튼을 제공해야 한다. | **M** |
| **REQ-F-B5-3** | 재응시 시, 이전 닉네임과 자기평가 정보가 자동으로 입력되어 있어야 한다. | **S** |

**수용 기준**:

- "이전 결과 vs 현재 결과 비교가 시각적으로 표시된다."
- "재응시 버튼 클릭 시 이전 정보가 미리 로드된다."

---

## REQ-F-B6: 재미 모드 (카테고리 선택형 퀴즈)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-F-B6-1** | 대시보드에 "재미 모드" 버튼 또는 메뉴를 별도로 제공해야 한다. | **M** |
| **REQ-F-B6-2** | "재미 모드" 클릭 시, 카테고리 선택 페이지를 표시하여 사용자가 선택할 수 있게 해야 한다: <br> - 마케팅 <br> - 반도체 <br> - 센서 <br> - RTL <br> - 기타 | **M** |
| **REQ-F-B6-3** | 카테고리 선택 후 "시작" 버튼 클릭 시, 3~5개의 라이트 퀴즈 문항이 로드되어야 한다. | **M** |
| **REQ-F-B6-4** | 퀴즈 풀이는 5~10분 내에 완료되도록 가벼운 형식이어야 하며, 시간 제한이 없어야 한다. | **M** |
| **REQ-F-B6-5** | 모든 문항 제출 후 "결과 페이지"를 표시하여 점수, 짧은 해설, 참고 링크를 제시해야 한다. | **M** |
| **REQ-F-B6-6** | 결과 페이지에 "참여 배지" 및 "포인트 획득" 정보를 표시해야 한다. (예: "반도체 마스터 배지 +50포인트") | **M** |
| **REQ-F-B6-7** | "결과 공유" 버튼을 제공하여 사내 피드(카카오톡, 사내 SNS 등)에 공유할 수 있어야 한다. | **S** |

**수용 기준**:

- "대시보드에서 '재미 모드' 버튼이 쉽게 접근 가능하다."
- "카테고리 선택 후 3초 내 퀴즈 문항이 로드된다."
- "모든 문항 제출 후 점수와 배지 정보가 표시된다."
- "공유 버튼 클릭 시 공유 대상 선택 다이얼로그가 나타난다."

---

## REQ-F-B7: 학습 일정 예고 (MVP 2.0 프리뷰)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-F-B7-1** | 레벨 테스트 최종 결과 페이지의 하단에 **"학습 일정 초안 보기 (MVP 2.0 미리보기)"** CTA 버튼을 제공해야 한다. | **M** |
| **REQ-F-B7-2** | 버튼 클릭 시, **2~4주 맞춤 학습 계획 초안**을 표시해야 한다: <br> - 주당 학습 시간 <br> - 카테고리별 추천 자료 (사내/사외/영상/블로그) <br> - 예상 소요 시간 <br> - 학습 경로 | **M** |
| **REQ-F-B7-3** | 학습 계획 초안 페이지에 **"관심 있음" 버튼**을 제공하여, 사용자가 대기리스트에 등록할 수 있게 해야 한다. | **M** |
| **REQ-F-B7-4** | "관심 있음" 버튼 클릭 시, **"MVP 2.0 학습 코디네이터 오픈 시 자동 알림"** 확인 모달을 표시하고, 이메일 구독 옵션을 제공해야 한다. | **M** |
| **REQ-F-B7-5** | (선택) "다시 보지 않기" 체크박스를 제공하여 이 프리뷰를 숨길 수 있어야 한다. | **S** |

**수용 기준**:

- "결과 페이지에 '학습 일정 초안 보기' 버튼이 보인다."
- "버튼 클릭 후 2초 내 학습 계획 초안이 로드된다."
- "'관심 있음' 버튼 클릭 시 대기리스트 등록 확인 메시지가 나타난다."

---

## 📱 UX 요구사항

### 핵심 화면 및 기능

| 화면 | 주요 요소 | 필수 기능 |
|------|---------|---------|
| **로그인** | Samsung AD 로그인 버튼, 에러 메시지 | SSO 리다이렉트, 토큰 발급 |
| **닉네임 등록** | 입력 필드, 중복 체크 버튼, 제안 목록 | 실시간 중복 검증, 자동 제안 |
| **온보딩 모달** | 요약 텍스트, "시작하기" CTA | 웰컴 메시지 표시 |
| **자기평가 폼** | 수준/경력/직군/업무/관심분야 입력 | 유효성 검사, 제출 |
| **테스트 화면** | 문항 네비게이션, 진행률, 남은 시간(선택), 임시 저장 | 순차 풀이, 실시간 저장 |
| **즉시 피드백** | 정오답 표시, 점수, 짧은 해설 | 토스트/패널 알림 |
| **결과 페이지** | 등급, 점수, 순위, 백분위, 분야별 분석, 해설 리스트 | 공유 배지 다운로드, 재응시 CTA |
| **재응시 비교** | 이전 결과 vs 현재, 차트/텍스트 비교 | History-Agent 데이터 표시 |

---

# 🔧 BACKEND REQUIREMENTS

## REQ-B-A1: Samsung AD 인증 및 사용자 세션 관리 (Backend)

> **⚠️ 중요**: Samsung AD SSO 인증 자체는 기존 기업 서비스를 이용합니다. Backend의 책임은 **인증 후 사용자 정보 수신 및 세션 관리**입니다.

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-A1-1** | Auth-Service가 Frontend로부터 Samsung AD 인증 후 사용자 정보(name, knox-id, dept, business_unit, email)를 수신하여 users 테이블에 저장해야 한다. | **M** |
| **REQ-B-A1-2** | **JWT 토큰을 knox_id만으로 단순하게 생성 및 발급**해야 한다. (JWT 페이로드: {knox_id, iat, exp}) | **M** |
| **REQ-B-A1-3** | 신규 사용자는 users 테이블에 새 레코드를 생성하고, JWT 토큰 + is_new_user=true 플래그와 함께 응답해야 한다. | **M** |
| **REQ-B-A1-4** | 기존 사용자가 재로그인하는 경우, JWT 토큰을 새로 생성하고 is_new_user=false로 설정하며 last_login을 현재 시간으로 업데이트해야 한다. | **M** |

**구현 상세**:

- **Samsung AD 연동**: Frontend에서 Samsung AD SSO 완료 후 사용자 정보(name, knox-id, dept, business_unit, email) 전달
- **사용자 정보 저장**: users 테이블에 전체 정보 저장 (emp_no=knox_id, email, dept, business_unit, status='active', created_at=현재시간)
- **JWT 토큰 생성**:

  ```json
  header: {alg: "HS256", typ: "JWT"}
  payload: {knox_id: string, iat: timestamp, exp: timestamp+86400}
  signature: HMAC-SHA256(secret_key)
  ```

  **→ 단순함을 위해 knox_id만 포함** (unique하므로 충분)
- **로그인 히스토리 관리** (SQLModel Relation 구조):
  - 매 로그인 시 `login_history` 테이블에 레코드 생성
  - `users` 테이블의 `last_login` 필드는 SQLModel Relation으로 `login_history`의 최신 레코드 참조
  - 목적: 모든 접속 히스토리 추적 + 성능 최적화 (last_login은 JOIN 없이 빠른 조회)
- **접속 히스토리 추적**: 모든 로그인 기록을 login_history에 저장하여 사용자 접속 빈도 및 학습 활동 분석 가능

**수용 기준**:

- "Frontend로부터 AD 정보(knox_id, name, email, dept, business_unit) 수신 후 1초 내 JWT 토큰이 발급된다."
- "JWT 페이로드는 {knox_id, iat, exp}만 포함한다."
- "신규 사용자 생성 후:"
  - "users 테이블에 모든 사용자 정보가 저장된다."
  - "login_history 테이블에 첫 로그인 레코드가 생성된다."
  - "JWT 토큰 + is_new_user=true로 반환된다."
- "재로그인 시:"
  - "새로운 JWT 토큰이 생성된다."
  - "login_history 테이블에 새로운 로그인 레코드가 추가된다."
  - "users 테이블의 last_login이 SQLModel Relation으로 최신 login_history 레코드를 참조한다."
  - "is_new_user=false로 반환된다."
- "JWT 검증 시 knox_id를 이용해 사용자를 식별할 수 있다."
- "login_history 조회를 통해 전체 접속 히스토리 분석 가능하다."
- "users.last_login(SQLModel Relation)을 통해 가장 최근 로그인 정보를 성능 저하 없이 조회 가능하다."

---

## REQ-B-A2: 닉네임 관리 (Backend)

### REQ-B-A2-Availability: 닉네임 중복 확인

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-A2-Avail-1** | Profile-Service가 특정 닉네임의 중복 여부를 1초 내에 확인하고 응답해야 한다. (인증 불필요) | **M** |
| **REQ-B-A2-Avail-2** | 닉네임 유효성 검사(길이 3-20자, 특수문자 제외, 금칙어 필터)를 구현해야 한다. | **M** |
| **REQ-B-A2-Avail-3** | 중복 시 대안 3개를 자동으로 생성해서 제안해야 한다. (예: 사용자명_1, 사용자명_2, 사용자명_3) | **S** |
| **REQ-B-A2-Avail-4** | 금칙어 필터 목록을 유지하고, 위반 시 명확한 거부 사유를 반환해야 한다. | **S** |

**API 엔드포인트**: `POST /profile/nickname/check` (인증 불필요)

**수용 기준**:

- "POST /profile/nickname/check?nickname=test123 요청 후 1초 내 {available: true/false} 응답"
- "중복 시 3개 이상의 대안 제안"
- "금칙어 위반 시 이유 명시"

---

### REQ-B-A2-Register: 닉네임 등록

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-A2-Reg-1** | JWT 토큰으로 현재 사용자를 식별하여 닉네임 등록 요청을 처리해야 한다. (인증 필수) | **M** |
| **REQ-B-A2-Reg-2** | 닉네임 검증 후 users 테이블의 nickname 필드를 업데이트하고, updated_at 타임스탬프를 갱신해야 한다. | **M** |
| **REQ-B-A2-Reg-3** | 같은 사용자가 중복 등록을 시도할 경우, 기존 닉네임을 제외하고 중복 여부를 확인해야 한다. | **M** |

**API 엔드포인트**: `POST /profile/register` (인증 필수: Authorization 헤더의 JWT)

**응답**:

```json
{
  "success": true,
  "message": "닉네임 등록 완료",
  "user_id": "bwyoon",
  "nickname": "test123",
  "registered_at": "2025-11-10T12:00:00Z"
}
```

**수용 기준**:

- "JWT 토큰 없이 요청 시 401 Unauthorized 응답"
- "등록 후 1초 내에 결과 반환"
- "DB 조회 시 users.nickname이 정확히 업데이트됨"

---

### REQ-B-A2-View: 닉네임 조회

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-A2-View-1** | JWT 토큰으로 현재 사용자의 닉네임 정보를 조회해야 한다. (인증 필수) | **M** |
| **REQ-B-A2-View-2** | 조회 응답에 사용자 ID, 현재 닉네임, 등록 일시, 수정 일시를 포함해야 한다. | **M** |

**API 엔드포인트**: `GET /profile/nickname` (인증 필수: Authorization 헤더의 JWT)

**응답**:

```json
{
  "user_id": "bwyoon",
  "knox_id": "bwyoon",
  "nickname": "test123",
  "registered_at": "2025-11-10T10:30:00Z",
  "updated_at": "2025-11-10T12:00:00Z"
}
```

**에러 응답**:

```json
{
  "error": "Nickname not set",
  "detail": "User has not registered a nickname yet"
}
```

**수용 기준**:

- "JWT 토큰 없이 요청 시 401 Unauthorized 응답"
- "GET 요청 후 1초 내에 현재 사용자의 닉네임 정보 반환"
- "다른 사용자의 정보는 조회 불가"

---

## REQ-B-A3: 개인정보 동의 관리 (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-A3-1** | JWT 토큰으로 현재 사용자를 식별하여 개인정보 동의 여부를 확인하는 API를 제공해야 한다. | **M** |
| **REQ-B-A3-2** | 개인정보 동의 시, users 테이블의 privacy_consent 필드를 업데이트하고 consent_at 타임스탬프를 기록해야 한다. | **M** |

**API 엔드포인트 1**: `GET /profile/consent` (인증 필수: Authorization 헤더의 JWT)

**응답**:

```json
{
  "consented": true,
  "consent_at": "2025-11-10T10:30:00Z"
}
```

또는 동의하지 않은 경우:

```json
{
  "consented": false,
  "consent_at": null
}
```

**API 엔드포인트 2**: `POST /profile/consent` (인증 필수: Authorization 헤더의 JWT)

**요청**:

```json
{
  "consent": true
}
```

**응답**:

```json
{
  "success": true,
  "message": "개인정보 동의 완료",
  "user_id": "kim.taeho",
  "consent_at": "2025-11-12T14:30:00Z"
}
```

**수용 기준**:

- "JWT 토큰 없이 요청 시 401 Unauthorized 응답"
- "GET /profile/consent 요청 후 1초 내에 동의 여부 반환"
- "POST /profile/consent 요청 시 users.privacy_consent 업데이트 및 consent_at 기록"
- "동의 철회(consent: false) 시에도 정상 처리"

---

## REQ-B-A2-Edit: 닉네임 수정 (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-A2-Edit-1** | JWT 토큰으로 현재 사용자를 식별하여 닉네임 변경 요청을 처리해야 한다. (인증 필수) | **M** |
| **REQ-B-A2-Edit-2** | 기존 닉네임은 제외하고 새로운 닉네임의 중복 여부를 확인해야 한다. | **M** |
| **REQ-B-A2-Edit-3** | 닉네임 변경 시 users 테이블의 nickname 필드를 업데이트하고, updated_at 타임스탬프를 갱신해야 한다. | **M** |
| **REQ-B-A2-Edit-4** | 닉네임 수정 API는 1초 내에 응답해야 한다. | **M** |

**API 엔드포인트**: `PUT /profile/nickname` (인증 필수: Authorization 헤더의 JWT)

**요청**:

```json
{
  "nickname": "newname123"
}
```

**응답**:

```json
{
  "success": true,
  "message": "닉네임 수정 완료",
  "user_id": "bwyoon",
  "old_nickname": "test123",
  "new_nickname": "newname123",
  "updated_at": "2025-11-10T12:30:00Z"
}
```

**수용 기준**:

- "JWT 토큰 없이 요청 시 401 Unauthorized 응답"
- "닉네임 변경 요청 후 1초 내 성공/실패 응답이 반환된다."
- "DB 조회 시 users.nickname이 새로운 값으로 업데이트됨"
- "updated_at이 최신 타임스탬프로 갱신되어 있다."

---

## REQ-B-A2-Signup: 통합 회원가입 (닉네임 + 프로필 저장)

**Note**: 헤더 "회원가입" 버튼을 통한 통합 가입 플로우입니다. 프론트엔드에서는 기존 API(`POST /api/profile/register`, `PUT /api/profile/survey`)를 순차 호출하여 닉네임 등록과 자기평가 저장을 처리하며, 추후 단일 트랜잭션 API가 준비되면 교체할 수 있도록 구조화되어 있습니다.

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-A2-Signup-1** | JWT 토큰으로 현재 사용자를 식별하여 통합 회원가입 요청을 처리해야 한다. (인증 필수) | **M** |
| **REQ-B-A2-Signup-2** | 닉네임 중복 확인을 먼저 수행하고, 중복 시 400 에러를 반환해야 한다. | **M** |
| **REQ-B-A2-Signup-3** | users.nickname 업데이트와 user_profile_surveys 생성을 **하나의 트랜잭션**으로 처리해야 한다. | **M** |
| **REQ-B-A2-Signup-4** | 트랜잭션 실패 시 롤백하고, 적절한 에러 메시지를 반환해야 한다. | **M** |
| **REQ-B-A2-Signup-5** | 통합 회원가입 API는 2초 내에 응답해야 한다. (DB 트랜잭션 포함) | **M** |

**현재 구현 경로 (MVP)**:

1. `POST /api/profile/register` – 닉네임 검증 및 저장  
2. `PUT /api/profile/survey` – LEVEL_MAPPING 적용 후 자기평가 저장  

> 두 API가 모두 성공해야 홈으로 리다이렉트되며, 실패 시 각각의 오류를 사용자에게 노출합니다. 단일 `/api/signup` 엔드포인트가 준비되면 위 단계들을 대체하는 형태로 연결할 수 있습니다.

**수용 기준**:

- "JWT 토큰 없이 요청 시 401 Unauthorized 응답"
- "닉네임 중복 시 400 에러 + 대안 제안 3개 반환"
- "users.nickname 업데이트 + user_profile_surveys 생성이 하나의 트랜잭션으로 처리됨"
- "트랜잭션 실패 시 둘 다 롤백됨"
- "통합 회원가입 API는 2초 내에 응답함"

**향후 과제(백엔드)**: 닉네임 + 프로필을 하나의 트랜잭션으로 처리하는 `/api/signup` 신설. 실패 시 롤백 및 2초 이내 응답을 보장해야 합니다.

---

## REQ-B-A2-Profile: 자기평가 정보 수정 (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-A2-Prof-1** | JWT 토큰으로 현재 사용자를 식별하여 자기평가 정보 변경 요청을 처리해야 한다. (인증 필수) | **M** |
| **REQ-B-A2-Prof-2** | 자기평가 정보(수준, 경력, 직군, 업무, 관심분야) 변경 요청을 받아, user_profile_surveys 테이블에 새 레코드를 생성해야 한다. | **M** |
| **REQ-B-A2-Prof-3** | 자기평가 수정 API는 1초 내에 응답해야 한다. | **M** |

**API 엔드포인트**: `PUT /profile/survey` (인증 필수: Authorization 헤더의 JWT)

**요청**:

```json
{
  "level": "advanced",
  "career": "10years",
  "job_role": "Senior Engineer",
  "duty": "System Architecture",
  "interests": ["AI", "Cloud", "ML"]
}
```

**응답**:

```json
{
  "success": true,
  "message": "자기평가 정보 업데이트 완료",
  "user_id": "bwyoon",
  "survey_id": "survey_xyz123",
  "updated_at": "2025-11-10T12:35:00Z"
}
```

**수용 기준**:

- "JWT 토큰 없이 요청 시 401 Unauthorized 응답"
- "자기평가 수정 요청 후 1초 내 성공/실패 응답이 반환된다."
- "DB 조회 시 새로운 user_profile_surveys 레코드가 생성됨"
- "이전 레코드는 유지되어 히스토리 추적 가능"

---

## REQ-B-B1: 자기평가 데이터 수집 및 저장 (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-B1-1** | Survey-Service가 자기평가 폼 스키마(필드 정의, 검증 규칙, 선택지)를 API로 제공해야 한다. | **M** |
| **REQ-B-B1-2** | Survey-Service가 제출된 자기평가 데이터를 검증하고 user_profile_surveys 테이블에 저장해야 한다. | **M** |

**수용 기준**:

- "제출 후 3초 내 데이터가 DB에 저장된다."
- "저장된 데이터가 다음 단계(문항 생성)에 정상적으로 전달된다."

---

## REQ-B-B2-Gen: 1차 문항 생성 (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-B2-Gen-1** | Item-Gen-Agent가 사용자의 자기평가 정보(수준, 관심분야)를 기반으로 1차 문항 세트(5문항)를 동적으로 LLM으로 생성해야 한다. | **M** |
| **REQ-B-B2-Gen-2** | 생성된 각 문항은 다음 정보를 포함해야 한다: <br> - 유형: multiple_choice, true_false, short_answer <br> - stem: 문항 내용 <br> - choices: 객관식 선택지 (객관식인 경우) <br> - answer_schema: 정답 기준 정보 <br> - difficulty: 난이도 (1~10) <br> - category: 사용자의 관심분야 반영 | **M** |
| **REQ-B-B2-Gen-3** | LLM 프롬프트에 마케팅, 반도체, 센서, RTL 등 특정 카테고리에 대한 "재미" 요소를 반영해야 한다. | **S** |

**수용 기준**:

- "자기평가 제출 후 3초 내 1차 문항이 API로 반환된다."
- "생성된 각 문항이 난이도와 카테고리 정보를 포함한다."

---

## REQ-B-B2-Adapt: 2차 적응형 난이도 조정 (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-B2-Adapt-1** | 1차 풀이 결과(점수, 오답 카테고리)를 분석하여, Item-Gen-Agent가 난이도를 조정한 2차 문항 세트를 생성해야 한다. | **M** |
| **REQ-B-B2-Adapt-2** | 적응형 난이도 조정 로직을 구현해야 한다: <br> - 점수 0~40: 난이도 유지 또는 감소 <br> - 점수 40~70: 난이도 유지 또는 약간 증가 <br> - 점수 70+: 난이도 상향 또는 초상급 활성화 | **M** |
| **REQ-B-B2-Adapt-3** | 2차 문항 생성 시, 1차 오답 분야를 우선적으로 강화하여 생성해야 한다. | **M** |
| **REQ-B-B2-Adapt-4** | (선택) 3차 이상 진행 가능하나, 최소 2회 및 최대 3회로 제한하는 로직을 구현할 수 있다. | **S** |

**수용 기준**:

- "1차 점수 60점 시, 2차는 중급 난이도로 생성된다."
- "1차 오답 카테고리가 2차에서 50% 이상 포함된다."
- "2차 문항이 3초 내에 생성된다.|-## REQ-B-B2-Gen: 1차 문항 생성 (Backend)

---

## REQ-B-B2-Plus: 테스트 진행 중 실시간 저장 및 재개 (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-B2-Plus-1** | 사용자가 각 문항에 답변을 입력할 때마다, 해당 응답을 자동으로 임시 저장해야 한다. (실시간 Autosave) | **M** |
| **REQ-B-B2-Plus-2** | 20분 제한 시간이 초과될 때, 현재까지의 모든 응답 상태를 자동으로 저장하고, 사용자에게 재개 옵션을 제공해야 한다. | **M** |
| **REQ-B-B2-Plus-3** | 사용자가 시간 초과 후 재개를 선택할 시, 이전 진행 상황(답변, 라운드, 점수)을 복원하여 이어서 풀 수 있어야 한다. | **M** |
| **REQ-B-B2-Plus-4** | attempt_answers 테이블에 저장 시, response_time_ms(응답 시간), saved_at(저장 타임스탬프) 등의 메타데이터도 함께 기록해야 한다. | **M** |
| **REQ-B-B2-Plus-5** | 실시간 저장은 최대 2초 이내에 완료되어야 한다. | **M** |

**수용 기준**:

- "**각 문항 답변 입력 후 2초 내에 자동 저장이 완료된다.**"
- "**시간 초과 시 현재까지의 모든 응답이 DB에 저장된다.**"
- "**재개 시 이전 답변이 모두 복원되고, 마지막으로 풀던 문항부터 이어서 진행 가능하다.**"

---

## REQ-B-B3-Score: 채점 (정오답 판정) (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-B3-Score-1** | Scoring-Agent가 각 문항 제출 시 1초 내에 정오답 판정 및 점수를 계산해야 한다. | **M** |
| **REQ-B-B3-Score-2** | 채점 로직을 구현해야 한다: <br> - 객관식/OX: 정답 일치 판정 (정답 1점, 오답 0점) <br> - 주관식: LLM 기반 키워드 매칭으로 부분점수 지원 (예: 0~100점) | **M** |
| **REQ-B-B3-Score-3** | **20분 초과 시 응답 시간에 따른 페널티를 적용해야 한다.** (예: 20분을 초과한 경우, 초과분만큼 감점 처리) | **M** |

**수용 기준**:

- "각 문항 제출 후 1초 내 '정답입니다' 또는 '오답입니다' 피드백이 반환된다."
- "주관식 채점 후 부분점수(예: 70점)가 반환된다."

---

## REQ-B-B3-Explain: 해설 생성 (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-B3-Explain-1** | Explain-Agent가 각 문항에 대해 정답/오답 해설(500자 이상) 및 참고 링크(3개 이상)를 생성해야 한다. | **M** |

**수용 기준**:

- "각 문항의 해설에 500자 이상의 설명이 포함된다."
- "해설에 참고 링크 3개 이상이 포함되어 있다."
- "해설은 채점 후 2초 내에 생성된다.|

## REQ-B-B3-Score: 채점 (정오답 판정) (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-B3-Score-1** | Scoring-Agent가 각 문항 제출 시 1초 내에 정오답 판정 및 점수를 계산해야 한다. | **M** |
| **REQ-B-B3-Score-2** | 채점 로직을 구현해야 한다: <br> - 객관식/OX: 정답 일치 판정 (정답 1점, 오답 0점) <br> - 주관식: LLM 기반 키워드 매칭으로 부분점수 지원 (예: 0~100점) | **M** |
| **REQ-B-B3-Score-3** | **20분 초과 시 응답 시간에 따른 페널티를 적용해야 한다.** (예: 20분을 초과한 경우, 초과분만큼 감점 처리) | **M** |

**수용 기준**:

- "각 문항 제출 후 1초 내 '정답입니다' 또는 '오답입니다' 피드백이 반환된다."
- "주관식 채점 후 부분점수(예: 70점)가 반환된다."

---

## REQ-B-B4: 최종 등급 및 순위 산출 (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-B4-1** | Rank-Service가 모든 응시 회차의 점수를 종합하여 최종 등급을 산출해야 한다. | **M** |
| **REQ-B-B4-2** | 5등급 체계를 정의해야 한다: Beginner, Intermediate, Intermediate-Advanced, Advanced, Elite | **M** |
| **REQ-B-B4-3** | 등급 산출 로직을 구현해야 한다: <br> - 기본: 종합 점수 + 난이도 보정 (문항별 정답률 기반 가중) <br> - 초기: 베이지안 평활로 컷오프 업데이트 | **M** |
| **REQ-B-B4-4** | 동일 기간(최근 90일) 응시자 풀을 기준으로 상대 순위(RANK() OVER)와 백분위(percentile)를 계산해야 한다. | **M** |
| **REQ-B-B4-5** | 모집단 < 100일 경우, percentile_confidence를 "medium"으로 설정해야 한다. | **S** |

**수용 기준**:

- "최종 점수 80/100 시 등급이 'Advanced'로 정확히 산출된다."
- "점수 80일 때 상대 순위(예: 3/506)와 백분위(상위 28%)가 정확히 계산된다."

---

## REQ-B-B4-Plus: 등급 기반 배지 부여 (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-B4-Plus-1** | **Rank-Service가 최종 등급을 산출한 후, 등급에 따라 자동으로 배지를 부여해야 한다.** 배지 종류: <br> - Beginner: "시작자 배지" <br> - Intermediate: "중급자 배지" <br> - Intermediate-Advanced: "중상급자 배지" <br> - Advanced: "고급자 배지" <br> - Elite: "엘리트 배지" (특수 배지) | **M** |
| **REQ-B-B4-Plus-2** | **엘리트 등급 사용자에게는 추가로 "Agent Specialist 배지"(또는 해당 분야 전문가 배지)를 부여해야 한다.** (예: Agent Architecture 분야 상위 5% → "Agent Specialist 배지") | **M** |
| **REQ-B-B4-Plus-3** | 부여된 배지는 user_badges 테이블에 저장되고, profile 조회 API에 포함되어야 한다. | **M** |

**수용 기준**:

- "등급 산출 후 자동으로 해당 등급 배지가 user_badges에 저장된다."
- "엘리트 등급 사용자는 일반 배지 + 특수 배지(Agent Specialist 등) 2개 이상이 부여된다."

---

## REQ-B-B5: 응시 이력 저장 및 조회 (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-B5-1** | History-Service가 모든 응시 데이터(자기평가, 문항/응답, 채점결과, 소요시간)를 attempts, attempt_rounds, attempt_answers 테이블에 저장해야 한다. | **M** |
| **REQ-B-B5-2** | History-Service가 직전 응시 이력을 조회하여 개선도(점수 변화, 등급 변화, 소요 시간 비교)를 계산해서 반환해야 한다. | **S** |
| **REQ-B-B5-3** | 사용자는 언제든 레벨 테스트를 반복 응시할 수 있는 API를 제공해야 한다. | **M** |
| **REQ-B-B5-4** | 재응시 시, History-Service가 이전 자기평가 정보를 자동으로 로드하여 반환해야 한다. | **S** |
| **REQ-B-B5-5** | **재응시 시 자기평가 폼을 수정하고 제출하면, user_profile_surveys 테이블에 새로운 레코드를 생성하고, 새로운 attempts와 연결해야 한다.** 이전 프로필 정보는 유지되며, 새로운 정보는 이번 응시에만 적용된다. | **M** |

**수용 기준**:

- "결과 저장 후 DB 조회 시 응시 이력이 정확히 저장되어 있다."
- "이전 응시 정보 조회 요청 시 1초 내 응답한다."
- "**재응시 시 새로운 자기평가를 제출하면, user_profile_surveys 테이블에 새 레코드가 생성되고 attempts와 연결된다.**"
- "**이전 자기평가는 변경되지 않으며, 새로운 자기평가는 새로운 문항 생성에만 적용된다.**"

---

## REQ-B-B6: 문항 품질 - 콘텐츠 필터 (Backend, MVP 1.0)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-B6-2** | 부정확/유해 콘텐츠 필터(비속어, 편향, 저작권 의심)로 부적절 문항을 자동 차단해야 한다. | **M** |

**수용 기준**:

- "문항 생성 후, 콘텐츠 필터링이 적용되어 부정확한 문항이 차단된다."
- "필터링된 문항은 자동으로 재생성 요청이 발생한다."

---

## 📋 REQ-B-B6-MVP2 (MVP 2.0으로 이관)

다음 REQ들은 MVP 2.0 로드맵에 포함됩니다:

| REQ ID | 요구사항 | 범주 |
|--------|---------|------|
| **REQ-B-B6-1** | RAG 소스 메타(문헌명, URL 해시, 버전, 타임스탐프) 저장 추적 | MVP 2.0 - 소스 추적 |
| **REQ-B-B6-3** | 사용자 신고 데이터 큐 적재 및 자동 재생성 | MVP 2.0 - 피드백 루프 |
| **REQ-B-B6-4** | 문항 난이도 균형(정답률) 모니터링 | MVP 2.0 - 품질 모니터링 |
| **REQ-B-B6-1** | (MVP 2.0) RAG 소스 메타(문헌명, URL 해시, 버전, 타임스탬프)를 저장하여 추적 가능해야 한다. | **M** |
| **REQ-B-B6-2** | 부정확/유해 콘텐츠 필터(비속어, 편향, 저작권 의심)로 부적절 문항을 자동 차단해야 한다. | **M** |
| **REQ-B-B6-3** | 사용자 신고 데이터를 큐에 적재하고, 신고된 문항에 대해 자동 재생성을 시도해야 한다. | **S** |
| **REQ-B-B6-4** | 문항의 난이도 균형(정답률)을 모니터링하여 극단값(정답률 < 10% 또는 > 95%)을 사전 차단해야 한다. | **S** |

**수용 기준**:

- "신고된 문항이 큐에 기록되고, 다음 배치에서 재생성된다."
- "정답률 < 10%인 문항은 추천하지 않는다."

---

## REQ-B-B6-Plus: 재미 모드 (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-B6-Plus-1** | Fun-Gen-Agent가 사용자가 선택한 카테고리(마케팅, 반도체, 센서, RTL 등)에 맞춰 3~5개의 라이트 퀴즈 문항을 동적으로 생성해야 한다. | **M** |
| **REQ-B-B6-Plus-2** | 재미 모드의 문항은 시간 제한이 없고, 가벼운 형식(객관식/OX)이어야 한다. | **M** |
| **REQ-B-B6-Plus-3** | Scoring-Agent가 즉시 채점하고 점수를 반환해야 한다. | **M** |
| **REQ-B-B6-Plus-4** | Badge-Service가 재미 모드 참여에 따른 배지와 포인트를 지급해야 한다: <br> - 카테고리별 "마스터 배지" (각 카테고리 3회 이상 참여 시) <br> - 특정 점수 달성 시 "전문가 배지" <br> - 참여 횟수별 "포인트" (1회 참여 +10포인트, 누적 가능) | **M** |
| **REQ-B-B6-Plus-5** | 사용자가 획득한 배지와 포인트는 profile 조회 API에서 함께 반환되어야 한다. | **M** |

**수용 기준**:

- "카테고리 선택 후 3초 내 문항이 생성된다."
- "모든 문항 제출 후 1초 내 채점 결과와 배지 정보가 반환된다."
- "배지와 포인트 정보가 사용자 프로필에 누적된다."

---

## REQ-B-B7: 학습 일정 예고 프리뷰 (Backend, MVP 1.0 - 프리뷰만)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-B7-1** | Plan-Preview-Agent가 사용자의 레벨 테스트 결과(점수, 등급, 약점 분야)를 분석하여, **2~4주의 맞춤 학습 계획 초안**을 자동으로 생성해야 한다. | **M** |
| **REQ-B-B7-2** | 학습 계획은 다음 정보를 포함해야 한다: <br> - 주당 추천 학습 시간 <br> - 카테고리별 추천 자료 (사내/사외, 동영상/블로그/문서) <br> - 각 자료의 예상 소요 시간 <br> - 학습 순서 및 우선순위 | **M** |
| **REQ-B-B7-3** | 사용자가 "관심 있음" 버튼을 클릭할 시, 해당 사용자를 **대기리스트 테이블(waitlist)** 에 등록해야 한다. | **M** |

**수용 기준** (MVP 1.0 - 프리뷰):

- "레벨 테스트 완료 후 3초 내 학습 계획 초안이 생성된다."
- "대기리스트 등록 요청 후 1초 내 확인 응답이 반환된다."
- "등록된 사용자 정보가 DB에 저장된다."

---

## 📋 REQ-B-B7-MVP2 (MVP 2.0으로 이관)

다음 REQ들은 MVP 2.0 로드맵에 포함됩니다:

| REQ ID | 요구사항 | 범주 |
|--------|---------|------|
| **REQ-B-B7-4** | Nudge-Service가 대기리스트에 등록된 사용자에게 MVP 2.0 오픈 시 **이메일 알림**을 자동으로 발송 | MVP 2.0 - 알림 서비스 |
| **REQ-B-B7-5** | 사용자의 대기리스트 등록 상태를 profile 조회 API에 포함 | MVP 2.0 - 프로필 통합 |

## REQ-B-B7: 학습 일정 예고 프리뷰 (Backend, MVP 1.0 - 프리뷰만)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-B7-1** | Plan-Preview-Agent가 사용자의 레벨 테스트 결과(점수, 등급, 약점 분야)를 분석하여, **2~4주의 맞춤 학습 계획 초안**을 자동으로 생성해야 한다. | **M** |
| **REQ-B-B7-2** | 학습 계획은 다음 정보를 포함해야 한다: <br> - 주당 추천 학습 시간 <br> - 카테고리별 추천 자료 (사내/사외, 동영상/블로그/문서) <br> - 각 자료의 예상 소요 시간 <br> - 학습 순서 및 우선순위 | **M** |
| **REQ-B-B7-3** | 사용자가 "관심 있음" 버튼을 클릭할 시, 해당 사용자를 **대기리스트 테이블(waitlist)** 에 등록해야 한다. | **M** |

**수용 기준** (MVP 1.0 - 프리뷰):

- "레벨 테스트 완료 후 3초 내 학습 계획 초안이 생성된다."
- "대기리스트 등록 요청 후 1초 내 확인 응답이 반환된다."
- "등록된 사용자 정보가 DB에 저장된다."

---

## 📋 REQ-B-B7-MVP2 (MVP 2.0으로 이관)

다음 REQ들은 MVP 2.0 로드맵에 포함됩니다:

| REQ ID | 요구사항 | 범주 |
|--------|---------|------|
| **REQ-B-B7-4** | Nudge-Service가 대기리스트에 등록된 사용자에게 MVP 2.0 오픈 시 **이메일 알림**을 자동으로 발송 | MVP 2.0 - 알림 서비스 |
| **REQ-B-B7-5** | 사용자의 대기리스트 등록 상태를 profile 조회 API에 포함 | MVP 2.0 - 프로필 통합 |

---

# 📡 API Specification (Backend)

## Auth-Service

```http
POST /api/v1/auth/callback
  설명: Frontend에서 Samsung AD SSO 완료 후 사용자 정보 전달
  요청: {
    knox_id: string,           // 고유한 회사 ID (unique)
    name: string,              // 사용자명
    email: string,             // 이메일
    dept: string,              // 부서
    business_unit: string      // 사업부
  }
  → {
    access_token: string,      // JWT 토큰 (페이로드: {knox_id, iat, exp})
    user_id: string,           // DB 사용자 ID (UUID)
    knox_id: string,           // 반복 확인용
    is_new_user: boolean,      // true: 신규, false: 기존
    created_at?: timestamp     // 신규 사용자인 경우만 포함
  }

POST /api/v1/auth/logout
  설명: 로그아웃
  요청: {access_token: string}
  → {success: boolean}
```

## Profile-Service

```http
GET /api/v1/profile/nickname/check
  요청: {nickname: string}
  → {available: boolean, suggestions: [string], message: string}

POST /api/v1/profile/register
  요청: {user_id: string, nickname: string}
  → {user_id: string, profile_id: string, success: boolean}

GET /api/v1/profile/{user_id}
  → {user_id, email, nickname, dept, created_at, status, badges: [{badge_id, name, category}], points: number, waitlist_registered: boolean}

PUT /api/v1/profile/{user_id}/nickname
  요청: {nickname: string}
  → {success: boolean, message: string, updated_at: timestamp}

PUT /api/v1/profile/{user_id}/survey
  설명: 자기평가 정보 수정
  요청: {level, years, job_role, duty, interests: [string]}
  → {survey_id: string, success: boolean, updated_at: timestamp}
```

## Survey-Service

```http
GET /api/v1/survey/schema
  → {fields: [{name, type, options?, required, validation}]}

POST /api/v1/survey/submit
  요청: {user_id, level, years, job_role, duty, interests: [string]}
  → {survey_id: string, validation_errors?: [], submitted_at: string}
```

## Item-Gen-Agent

```http
POST /api/v1/items/generate
  요청: {survey_id: string, round_idx: number, prev_answers?: []}
  → {
    round_id: string,
    items: [{
      id: string,
      type: enum(multiple_choice, true_false, short_answer),
      stem: string,
      choices?: [string],
      answer_schema: {type, keywords?, correct_answer?},
      difficulty: number,
      category: string,
      rag_source_hash: string // MVP 2.0: RAG 소스 추적용
    }],
    time_limit_seconds: number
  }

GET /api/v1/items/{item_id}
  → {id, stem, choices, type, difficulty, category}
```

## Scoring-Agent

```http
POST /api/v1/scoring/submit-answers
  요청: {
    round_id: string,
    answers: [{item_id, user_answer, response_time_ms}]
  }
  → {
    round_id: string,
    per_item: [{
      item_id,
      correct: boolean,
      score: number,
      extracted_keywords?: [string],
      feedback: string
    }],
    round_score: number,
    round_stats: {avg_response_time, correct_count, total_count}
  }
```

## Explain-Agent

```http
POST /api/v1/explanation/generate
  요청: {
    item_id: string,
    user_answer: string,
    correct_answer: string,
    rag_refs?: [string]
  }
  → {
    explanation: string,
    reference_links: [{title, url, source}],
    key_concepts: [string]
  }
```

## Rank-Service

```http
POST /api/v1/ranking/finalize
  요청: {
    user_id: string,
    attempt_id: string,
    rounds: [{idx, score, difficulty_stats}]
  }
  → {
    grade: enum(beginner, intermediate, intermediate_advanced, advanced, elite),
    overall_score: number,
    percentile: number,
    position: number,
    total_candidates: number,
    grade_explanation: string,
    cutoff_info: {grade, min_score, max_score}
  }
```

## Test-Autosave-Service

```http
POST /api/v1/tests/{session_id}/autosave-answer
  설명: 각 문항 응답 자동 저장 (실시간 Autosave)
  요청: {
    question_id: string,
    user_answer: string,
    response_time_ms: number
  }
  → {saved: boolean, saved_at: timestamp}

GET /api/v1/tests/{session_id}/progress
  설명: 현재 테스트 진행 상황 조회 (중단 후 재개 시)
  → {
    session_id: string,
    current_round: number,
    completed_questions: number,
    total_questions: number,
    answers: [{question_id, user_answer}],
    time_elapsed_seconds: number,
    time_remaining_seconds: number
  }

POST /api/v1/tests/{session_id}/resume
  설명: 중단된 테스트 재개
  요청: {session_id: string}
  → {success: boolean, resumed_at: timestamp, time_remaining_seconds: number}
```

## Fun-Mode-Service

```http
POST /api/v1/fun-mode/generate
  설명: 재미 모드 문항 생성
  요청: {user_id: string, category: string}
  → {
    session_id: string,
    category: string,
    items: [{
      id: string,
      type: enum(multiple_choice, true_false),
      stem: string,
      choices: [string],
      difficulty: number
    }]
  }

POST /api/v1/fun-mode/{session_id}/submit
  설명: 재미 모드 채점 및 배지 지급
  요청: {
    answers: [{item_id, user_answer}]
  }
  → {
    score: number,
    total_score: number,
    per_item: [{item_id, correct: boolean, score: number}],
    badges_earned: [{badge_id, name, category}],
    points_earned: number
  }
```

## Learning-Plan-Service

```http
POST /api/v1/learning-plan/preview
  설명: 학습 일정 예고 초안 생성
  요청: {user_id: string, attempt_id: string}
  → {
    plan_id: string,
    duration_weeks: number,
    weekly_hours: number,
    categories: [{name, resources: [{title, url, type, estimated_hours}]}],
    created_at: timestamp
  }

POST /api/v1/waitlist/register
  설명: MVP 2.0 대기리스트 등록
  요청: {user_id: string, plan_id: string, email: string}
  → {success: boolean, registered_at: timestamp, notification_enabled: boolean}

GET /api/v1/waitlist/status
  설명: 대기리스트 등록 상태 조회
  요청: {user_id: string}
  → {registered: boolean, registered_at: timestamp, position: number}
```

## History-Service

```http
GET /api/v1/history/latest
  요청: {user_id: string}
  → {
    last_attempt: {
      attempt_id, grade, score, percentile, completed_at
    },
    previous_attempts: [{id, grade, score, completed_at}],
    improvement: {grade_change, score_change, date_diff_days}
  }

POST /api/v1/history/save
  요청: {
    user_id: string,
    survey_id: string,
    rounds: [{round_id, items, answers, score}],
    final_result: {grade, score, rank}
  }
  → {attempt_id: string, success: boolean}
```

---

# 💾 Data Model (Backend)

## users

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  knox_id VARCHAR(100) UNIQUE NOT NULL,      -- Samsung AD 고유 ID
  email VARCHAR(255) UNIQUE NOT NULL,
  emp_no VARCHAR(50) UNIQUE,
  name VARCHAR(100) NOT NULL,                -- 사용자명
  dept VARCHAR(100),
  business_unit VARCHAR(100),                -- 사업부
  nickname VARCHAR(50) UNIQUE,               -- 별도로 등록 (nullable: 초기 미등록)
  status ENUM('active', 'inactive'),
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP,                      -- 프로필 수정 시 갱신
  last_login_id UUID,                        -- login_history와의 Relation (최신 로그인)
  total_points INT DEFAULT 0,                -- 누적 포인트
  FOREIGN KEY(last_login_id) REFERENCES login_history(id),
  INDEX(knox_id, email, nickname),
  INDEX(created_at)
);
```

## login_history

> **로그인 히스토리 추적 테이블** (SQLModel Relation으로 users.last_login 관리)

```sql
CREATE TABLE login_history (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  knox_id VARCHAR(100) NOT NULL,             -- 빠른 조회용 (denormalized)
  ip_address VARCHAR(45),                    -- 선택: IPv4/IPv6
  user_agent VARCHAR(500),                   -- 선택: 브라우저 정보
  login_timestamp TIMESTAMP NOT NULL,
  created_at TIMESTAMP NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id),
  INDEX(user_id, login_timestamp DESC),
  INDEX(knox_id, login_timestamp DESC)
);
```

**설명**:

- 매 로그인 시마다 새로운 레코드 생성
- users 테이블의 `last_login_id` 필드로 최신 로그인 레코드 참조 (SQLModel Relation)
- 모든 접속 히스토리 추적 가능
- INDEX: (user_id, login_timestamp DESC) → 특정 사용자의 최신 로그인 빠른 조회

---

## user_profile_surveys

> **설명**: 사용자의 자기평가 정보를 시계열로 저장하는 테이블입니다. **재응시할 때마다 새로운 레코드가 생성**되므로, 각 응시(attempts)는 특정 자기평가 스냅샷과 연결됩니다.
>
> **설계 원칙**:
>
> - 사용자가 닉네임을 수정해도, 자기평가 이력은 유지됨
> - 재응시 시 자기평가를 수정하면 새 레코드 생성 (이전 레코드는 유지)
> - 각 attempts는 해당 시점의 survey_id와 연결되어, 어떤 자기평가로 테스트를 봤는지 추적 가능

```sql
CREATE TABLE user_profile_surveys (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  self_level ENUM('beginner', 'intermediate', 'advanced'),
  years_experience INT,
  job_role VARCHAR(100),
  duty TEXT,
  interests JSON, -- ["LLM", "RAG", ...]
  submitted_at TIMESTAMP NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id),
  INDEX(user_id, submitted_at DESC)  -- 특정 사용자의 최신 자기평가 조회
);
```

## question_bank

> **목적**: Item-Gen-Agent가 동적으로 생성한 문제와 메타데이터를 **캐싱하고 분석**하기 위한 테이블입니다.
> 역할:
>
> 1. **생성된 문제 캐싱**: LLM 생성 비용 절감 및 성능 향상
> 2. **품질 검증 완료 문제 저장**: 정답률 분석 후 검증된 문제만 재사용
> 3. **LLM 장애 시 대체재**: 캐시된 문제로 서비스 연속성 보장
> 4. **분석/모니터링**: 문제별 정답률, 난이도 유효성, 카테고리 분포 분석

```sql
CREATE TABLE question_bank (
  id UUID PRIMARY KEY,
  round_id UUID,
  item_type ENUM('multiple_choice', 'true_false', 'short_answer'),
  stem TEXT NOT NULL,
  choices JSON, -- for multiple_choice
  correct_key VARCHAR(500), -- for multiple_choice/true_false
  correct_keywords JSON, -- for short_answer
  difficulty INT, -- 1~10
  categories JSON, -- ["LLM", "RAG", ...]
  rag_source_hash VARCHAR(255), -- MVP 2.0: RAG 소스 추적용
  is_validated BOOLEAN DEFAULT FALSE, -- 품질 검증 완료 여부
  correct_rate DECIMAL(5,2), -- 사용자별 정답률 (모니터링용)
  usage_count INT DEFAULT 0, -- 재사용 횟수
  created_at TIMESTAMP,
  last_used_at TIMESTAMP,
  INDEX(difficulty, categories),
  INDEX(is_validated, usage_count DESC),  -- 품질 검증 완료 & 자주 사용된 문제 조회
  INDEX(correct_rate)  -- 정답률 분석
);
```

## attempts

```sql
CREATE TABLE attempts (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  survey_id UUID REFERENCES user_profile_surveys(id),
  test_type ENUM('level_test', 'fun_quiz') DEFAULT 'level_test',  -- 레벨 테스트 vs 재미 모드 구분
  started_at TIMESTAMP NOT NULL,
  finished_at TIMESTAMP,
  final_grade ENUM('beginner', 'intermediate', 'intermediate_advanced', 'advanced', 'elite'),  -- fun_quiz는 null 가능
  final_score DECIMAL(5,2),
  percentile INT,  -- fun_quiz는 null 가능
  rank INT,        -- fun_quiz는 null 가능
  total_candidates INT,  -- fun_quiz는 null 가능
  status ENUM('in_progress', 'completed'),
  FOREIGN KEY(user_id) REFERENCES users(id),
  INDEX(user_id, finished_at),
  INDEX(test_type, finished_at)  -- 테스트 유형별 조회 최적화
);
```

## attempt_rounds

```sql
CREATE TABLE attempt_rounds (
  id UUID PRIMARY KEY,
  attempt_id UUID NOT NULL REFERENCES attempts(id),
  round_idx INT,
  score DECIMAL(5,2),
  time_spent_seconds INT,
  created_at TIMESTAMP,
  FOREIGN KEY(attempt_id) REFERENCES attempts(id)
);
```

## attempt_answers

```sql
CREATE TABLE attempt_answers (
  id UUID PRIMARY KEY,
  round_id UUID NOT NULL REFERENCES attempt_rounds(id),
  item_id UUID REFERENCES question_bank(id),
  user_answer_raw TEXT,
  score DECIMAL(5,2),
  is_correct BOOLEAN,
  response_time_ms INT,           -- 사용자의 응답 시간 (단위: 밀리초)
  saved_at TIMESTAMP NOT NULL,    -- 실시간 저장 완료 시간 (Autosave 기록)
  created_at TIMESTAMP,
  FOREIGN KEY(round_id) REFERENCES attempt_rounds(id),
  INDEX(round_id, saved_at DESC)  -- 라운드별 저장 순서 추적
);
```

## analytics

```sql
CREATE TABLE analytics (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  event_type VARCHAR(100), -- 'signup', 'survey_submit', 'attempt_start', 'answer_submit', 'result_view'
  payload JSON,
  created_at TIMESTAMP,
  INDEX(user_id, event_type, created_at)
);
```

## ranking_snapshots

```sql
CREATE TABLE ranking_snapshots (
  id UUID PRIMARY KEY,
  snapshot_date DATE NOT NULL,
  grade_cutoffs JSON, -- {beginner: 0, intermediate: 40, ...}
  grade_distribution JSON, -- {beginner: 45, intermediate: 150, ...}
  total_population INT,
  created_at TIMESTAMP,
  UNIQUE(snapshot_date)
);
```

## badges

```sql
CREATE TABLE badges (
  id UUID PRIMARY KEY,
  name VARCHAR(100) NOT NULL,        -- 배지명 (예: "반도체 마스터", "전문가")
  category VARCHAR(50) NOT NULL,     -- 카테고리 (레벨테스트 등급 / fun-mode 카테고리)
  description TEXT,
  icon_url VARCHAR(255),             -- 배지 이미지 URL
  criteria JSON,                     -- 배지 획득 조건 (예: {type: "category_3times", category: "반도체"})
  created_at TIMESTAMP NOT NULL,
  INDEX(category)
);
```

## user_badges

```sql
CREATE TABLE user_badges (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  badge_id UUID NOT NULL REFERENCES badges(id),
  earned_at TIMESTAMP NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id),
  FOREIGN KEY(badge_id) REFERENCES badges(id),
  INDEX(user_id, earned_at DESC),
  UNIQUE(user_id, badge_id)  -- 동일 사용자는 같은 배지 중복 획득 안 함
);
```

## fun_mode_sessions

> **설명**: 재미 모드 퀴즈 세션을 추적하는 테이블입니다. attempts 테이블의 test_type='fun_quiz'와 연동됩니다.

```sql
CREATE TABLE fun_mode_sessions (
  id UUID PRIMARY KEY,
  attempt_id UUID UNIQUE REFERENCES attempts(id),  -- attempts 테이블과의 1:1 관계
  user_id UUID NOT NULL REFERENCES users(id),
  category VARCHAR(50) NOT NULL,     -- 선택한 카테고리 (마케팅, 반도체, 센서, RTL 등)
  started_at TIMESTAMP NOT NULL,
  finished_at TIMESTAMP,
  score DECIMAL(5,2),                -- 100점 만점
  time_spent_seconds INT,            -- 실제 소요 시간 (시간 제한 없음)
  status ENUM('in_progress', 'completed'),
  FOREIGN KEY(attempt_id) REFERENCES attempts(id),
  FOREIGN KEY(user_id) REFERENCES users(id),
  INDEX(user_id, finished_at DESC),
  INDEX(category, finished_at DESC)  -- 카테고리별 집계 분석
);
```

**비고**: 재미 모드 응답은 attempt_answers 테이블에 저장되며, attempt_rounds는 재미 모드에서는 사용하지 않습니다(라운드 개념 없음).

## learning_plan_previews

```sql
CREATE TABLE learning_plan_previews (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  attempt_id UUID REFERENCES attempts(id),
  plan_data JSON,                    -- {duration_weeks, weekly_hours, categories: [...]}
  created_at TIMESTAMP NOT NULL,
  FOREIGN KEY(user_id) REFERENCES users(id),
  INDEX(user_id, created_at DESC)
);
```

## waitlist

```sql
CREATE TABLE waitlist (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  plan_id UUID REFERENCES learning_plan_previews(id),
  email VARCHAR(255) NOT NULL,
  registered_at TIMESTAMP NOT NULL,
  notification_sent BOOLEAN DEFAULT FALSE,
  notification_sent_at TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES users(id),
  FOREIGN KEY(plan_id) REFERENCES learning_plan_previews(id),
  INDEX(user_id),
  INDEX(registered_at),
  UNIQUE(user_id)  -- 한 사용자는 한 번만 등록
);
```

---

## 🎓 등급 및 랭킹 로직

### 5등급 컷오프 방식

```plain
점수 범위 (초기 정의, 운영 중 동적 조정):
  Beginner:               0 ~ 40점
  Intermediate:         40 ~ 60점
  Intermediate-Advanced: 60 ~ 75점
  Advanced:             75 ~ 90점
  Elite:                90 ~ 100점

최종 점수 계산:
  final_score = (round1_score × 0.4) + (round2_score × 0.6) + difficulty_bonus

  난이도 보정(difficulty_bonus):
    - 평균 정답률 > 80%: +5점
    - 평균 정답률 40~80%: ±0점
    - 평균 정답률 < 40%: -5점
```

### 상대 순위 및 백분위

```sql
계산 기준: 최근 90일 응시자 풀
순위 = RANK() OVER (ORDER BY final_score DESC)
백분위 = (순위 - 1) / (총 응시자 수) × 100

예시:
  순위: 3/506명
  백분위: (3-1)/506 × 100 = 0.4% (상위 0.4%)
```

### 신뢰도 관리

```python
IF total_candidates < 100:
  label = "분포 신뢰도 낮음 (샘플 부족)"
  percentile_confidence = "medium"
ELSE IF total_candidates >= 100:
  percentile_confidence = "high"
```

---

## ⚡ 비기능 요구사항

| 항목 | 요구사항 | 목표 |
|------|---------|------|
| **성능** | 문항 생성 ≤ 3s/세트 | 99th percentile |
| | 채점/해설 ≤ 1s/문항 | 99th percentile |
| | 결과 페이지 로드 ≤ 2s | 99th percentile |
| **가용성** | 시스템 가동률 | 99.5%+ |
| **보안** | Samsung AD, JWT 토큰 관리, 역할기반 접근 | 표준 준수 |
| | 개인정보 최소 수집, 암호화 저장 | GDPR/개인정보보호법 준수 |
| **감사/로깅** | 모든 생성·채점·결과 이벤트 추적 | Event ID, User ID, Timestamp |
| **접근성** | 키보드 전용 탐색, 명도 대비 | WCAG 2.1 AA 준수 |
| **국제화** | 한국어 기본, 영어 확장 지원 | 문항·해설 다국어 플래그 |

---

## 🚨 에러 & 엣지 케이스

| 시나리오 | 처리 방식 | 사용자 안내 |
|---------|---------|-----------|
| **Samsung AD 인증 실패** | 재시도 1회 + 헬프 링크 제공 | "계정 정보를 다시 확인해주세요" |
| **닉네임 중복** | 대안 3개 자동 제안 | "다음 닉네임을 추천합니다" |
| **닉네임 금칙어** | 거부 + 이유 안내 | "부적절한 단어가 포함되었습니다" |
| **테스트 중 이탈/새로고침** | 자동 저장 후 재개 | "이전 진행 상황에서 재개됩니다" |
| **문항 생성 타임아웃** | 재시도 1회 + 캐시 세트 대체 | "문항을 불러오는 중입니다" |
| **채점 오류** | 서버 로그 기록 + 안내 | "일시적 오류입니다. 관리자에 문의해주세요" |
| **표본 부족(< 100)** | 신뢰도 라벨 표시 | "현재 응시자가 적어 분포 신뢰도가 낮습니다" |

---

## 🎯 우선순위 (MoSCoW)

### Must (필수)

- ✅ **REQ-F-A1-1~3, REQ-B-A1-1~4: Samsung AD 로그인 + 실패 시 헬프 링크 (F/B)**
- ✅ **REQ-F-A3-1~5, REQ-B-A3-1~2: 개인정보 수집 및 이용 동의 (F/B)**
- ✅ REQ-F-A2-1~5, REQ-B-A2-1~5: 닉네임 등록 (F/B)
- ✅ **REQ-F-A2-Edit-1~6, REQ-B-A2-Edit-1~4: 프로필 수정 (닉네임/자기평가) (F/B)**
- ✅ REQ-F-A2-2-1~5, REQ-B-B1-1~2: 자기평가 입력 (프로필 설정) (F/B) [이전 REQ-F-B1]
- ✅ REQ-F-B2-1~7, REQ-B-B2-1~6: 문항 생성 및 풀이 (F/B)
- ✅ **REQ-B-B2-Plus-1~5: 테스트 진행 중 실시간 저장 및 재개 (B)**
- ✅ REQ-F-B3-1~2, REQ-B-B3-1~4: 채점 및 해설 (F/B)
- ✅ **REQ-F-B4-1~3, REQ-B-B4-1~5: 등급 및 순위 산출 + 분포 시각화 (F/B)**
- ✅ **REQ-B-B4-Plus-1~3: 등급 기반 배지 부여 (B)**
- ✅ REQ-F-B5-2, REQ-B-B5-1,3: 이력 저장 및 재응시 (F/B)
- ✅ **REQ-F-B6-1~6, REQ-B-B6-Plus-1~5: 재미 모드 (F/B)**
- ✅ **REQ-F-B7-1~4, REQ-B-B7-1~4: 학습 일정 예고 프리뷰 (F/B)**
- ✅ REQ-B-B6-1~2: 콘텐츠 품질 & 필터링 (B)

### Should (권장)

- ✅ REQ-F-A2-3~4, REQ-B-A2-3~4: 닉네임 제안, 금칙어 필터 (F/B)
- ✅ REQ-B-B2-3: 재미 카테고리 (B)
- ✅ REQ-B-B2-7: 3차 이상 적응형 (B)
- ✅ REQ-F-B4-2~4: 신뢰도 라벨, 학습 예고, 공유 배지 (F)
- ✅ REQ-F-B5-1,3, REQ-B-B5-2,4: 비교 분석, 자동 로드 (F/B)
- ✅ REQ-B-B6-3~4: 신고 처리, 난이도 모니터링 (B)

### Could (선택)

- ✅ REQ-F-B2-5, REQ-B-B3-3: 시간 제한 표시 및 페널티 (F/B)

---

## 📊 성공 지표 (KPI)

| 지표 | 목표값 | 측정 주기 |
|------|--------|---------|
| 가입 완료율 | ≥ 90% | 주간 |
| 레벨 테스트 완료율 | ≥ 70% | 주간 |
| 평균 테스트 소요 시간 | 15~20분 | 주간 |
| 문항 생성 실패 대체율 | ≤ 3% | 일간 |
| 평균 응답 시간/문항 | ≤ 3분 | 주간 |
| 결과 공유 클릭률 | ≥ 20% | 주간 |
| 재응시 전환율 | ≥ 25% | 월간 |
| 시스템 가동률 | ≥ 99.5% | 일간 |

---

## ✅ 수용 기준 (Acceptance Criteria) 예시

1. **가입 완료**
   - "사용자가 Samsung AD 로그인 후 3초 내 토큰이 발급된다."
   - "닉네임 중복 시 1초 내 대안 3개가 제안된다."
   - "가입 완료 후 DB에 사용자 레코드가 생성된다."

2. **문항 생성**
   - "자기평가 제출 후 3초 내 1차 문항이 화면에 노출된다."
   - "마케팅, 반도체 등 특화 카테고리 문항이 포함된다."

3. **채점 & 해설**
   - "각 문항 제출 후 1초 내 '정답/오답' 피드백이 표시된다."
   - "해설에 참고 링크가 포함되어 있다."

4. **결과 페이지**
   - "등급(1~5), 점수, 순위/모집단, 백분위가 동시에 표시된다."
   - "배지 이미지를 다운로드할 수 있다."

5. **재응시**
   - "대시보드에서 '재응시' 버튼이 노출되고, 클릭 시 직전 정보가 로드된다."

---

## 🚀 릴리스 슬라이스 (Release Plan)

### R1: 기본 가입 및 프로필 설정

- Samsung AD 로그인/SSO (REQ-F-A1-1~3, REQ-B-A1-1~4)
- 개인정보 동의 (REQ-F-A3-1~5, REQ-B-A3-1~2)
- 닉네임 등록 (중복 체크) (REQ-F-A2-1~5, REQ-B-A2-1~5)
- 자기평가 입력 (REQ-F-A2-2-1~5, REQ-B-B1-1~2)
- **프로필 수정 기능 (REQ-F-A2-Edit-1~6, REQ-B-A2-Edit-1~4)**

**완료 기준**: 사용자가 개인정보 동의 후 가입을 완료하고, 자기평가를 포함한 프로필을 설정하며, 프로필 리뷰 페이지에서 테스트를 시작할 수 있음

---

### R2: 1차 테스트 & 저장/재개

- Item-Gen-Agent 1차 문항 생성 (REQ-B-B2-1~2)
- **20분 제한 타이머 (REQ-F-B2-5, REQ-F-B2-6)**
- **테스트 진행 중 실시간 저장 및 재개 (REQ-F-B2-6~7, REQ-B-B2-Plus-1~5)**
- 순차적 문항 풀이 (REQ-F-B2-1~4)
- Scoring-Agent 채점 (REQ-B-B3-1~2)
- **20분 초과 시 페널티 적용 (REQ-B-B3-3)**
- Explain-Agent 해설 생성 (REQ-B-B3-4, REQ-F-B3-1~2)

**완료 기준**: 사용자가 1차 테스트를 완료하고 중단 후 재개 가능하며, 각 문항의 해설을 확인

---

### R3: 적응형 2차 & 최종 결과 & 추가 기능

- 난이도 조정 로직 (REQ-B-B2-4~6)
- Rank-Service 등급/순위 산출 (REQ-B-B4-1~5)
- **등급 기반 배지 부여 (REQ-B-B4-Plus-1~3)**
- 최종 결과 페이지 (REQ-F-B4-1~6)
  - **등급별 배지 시각화 + 엘리트 특수 배지 (REQ-F-B4-2)**
  - **분포 차트 및 사용자 위치 하이라이트 (REQ-F-B4-3)**
- **학습 일정 예고 프리뷰 (REQ-F-B7-1~5, REQ-B-B7-1~4)**
- **재미 모드 (카테고리 선택형 퀴즈) (REQ-F-B6-1~7, REQ-B-B6-Plus-1~5)**
- History-Service 비교 (REQ-F-B5-1, REQ-B-B5-2)

**완료 기준**: 사용자가 최종 등급, 배지를 시각적으로 확인하고, 분포 차트를 통해 전사 상대 순위를 이해하며, 공유 가능하고, 재미 모드에 참여하고 학습 일정을 확인 가능

---

### R4: 품질 & 성능 최적화

- 콘텐츠 필터링 (REQ-B-B6-2)
- 난이도 모니터링 (REQ-B-B6-4)
- 문항 신고 및 재생성 (REQ-B-B6-3)
- 배지 시스템 최적화
- 성능 최적화 (≤ 3s 문항 생성, ≤ 1s 채점, ≤ 2s 저장)
- 에러 핸들링 및 로깅

**완료 기준**: 시스템이 99.5% 가용성 유지, 모든 비기능 요구사항 충족

---

## 📝 개발 담당자 가이드

### Frontend 팀 체크리스트

```markdown
## Frontend (F 태그)

로그인 화면:
- [ ] REQ-F-A1-1: Samsung AD 로그인 버튼 구현
- [ ] REQ-F-A1-2: SSO 콜백 페이지 구현
- [ ] REQ-F-A1-3: 에러 메시지 표시

회원가입 (닉네임 등록):
- [ ] REQ-F-A2-1: 입력 필드 & 중복 확인 버튼
- [ ] REQ-F-A2-2: 실시간 유효성 검사
- [ ] REQ-F-A2-3: 대안 3개 제안 표시
- [ ] REQ-F-A2-4: 금칙어 거부 메시지
- [ ] REQ-F-A2-5: 가입 완료 버튼 활성화

프로필 수정:
- [ ] REQ-F-A2-Edit-1: 프로필 수정 메뉴
- [ ] REQ-F-A2-Edit-2: 닉네임 변경 입력 필드
- [ ] REQ-F-A2-Edit-3: 기존 닉네임 제외 중복 확인
- [ ] REQ-F-A2-Edit-4: 저장 완료 메시지
- [ ] REQ-F-A2-Edit-5: 자기평가 정보 수정 폼
- [ ] REQ-F-A2-Edit-6: 수정 정보 다음 테스트에 반영

개인정보 동의:
- [ ] REQ-F-A3-1: 개인정보 동의 모달/페이지 표시
- [ ] REQ-F-A3-2: 동의 내용 명시 (수집 항목, 이용 목적, 보유 기간)
- [ ] REQ-F-A3-3: 동의 시에만 다음 단계 진행
- [ ] REQ-F-A3-4: 비동의 시 홈화면 복귀
- [ ] REQ-F-A3-5: 동의 여부 DB 저장 및 중복 확인 방지

자기평가 폼 (프로필 설정):
- [ ] REQ-F-A2-2-1: 자기평가 입력 페이지로 이동
- [ ] REQ-F-A2-2-2: 입력 항목 레이아웃 및 필드 배치
- [ ] REQ-F-A2-2-3: 필드 검증 및 오류 메시지 표시
- [ ] REQ-F-A2-2-4: "완료" 버튼 활성화
- [ ] REQ-F-A2-2-5: 프로필 리뷰 페이지로 리다이렉트

테스트 화면:
- [ ] REQ-F-B2-1: 문항 순차 표시
- [ ] REQ-F-B2-2: 진행률, 남은 시간 표시
- [ ] REQ-F-B2-3: 정오답 피드백
- [ ] REQ-F-B2-4: 부분점수 표시
- [ ] REQ-F-B2-5: 20분 제한 타이머 (색상 변화: 녹색→주황색→빨간색)
- [ ] REQ-F-B2-6: 각 응답 자동 저장 & "저장됨" 표시
- [ ] REQ-F-B2-7: 20분 초과 시 재개 모달

해설 화면:
- [ ] REQ-F-B3-1: 해설 및 참고 링크 표시
- [ ] REQ-F-B3-2: 다음 문항/결과 보기 네비게이션

결과 페이지:
- [ ] REQ-F-B4-1: 등급, 점수, 순위, 백분위 표시
- [ ] REQ-F-B4-2: 등급별 배지 시각화 + 엘리트 특수 배지 + 추천 링크
- [ ] REQ-F-B4-3: 분포 차트 및 사용자 위치 하이라이트 + 텍스트 요약
- [ ] REQ-F-B4-4: 신뢰도 라벨 표시
- [ ] REQ-F-B4-5: 학습 예고 문구
- [ ] REQ-F-B4-6: 배지 다운로드 버튼

재응시:
- [ ] REQ-F-B5-1: 이전 결과 비교 표시
- [ ] REQ-F-B5-2: 재응시 버튼
- [ ] REQ-F-B5-3: 이전 정보 자동 로드

재미 모드:
- [ ] REQ-F-B6-1: 대시보드에 "재미 모드" 버튼
- [ ] REQ-F-B6-2: 카테고리 선택 페이지 (마케팅/반도체/센서/RTL/기타)
- [ ] REQ-F-B6-3: "시작" 버튼 클릭 시 문항 로드
- [ ] REQ-F-B6-4: 가벼운 형식 (시간 제한 없음)
- [ ] REQ-F-B6-5: 결과 페이지 (점수, 해설, 링크)
- [ ] REQ-F-B6-6: 배지 & 포인트 획득 정보 표시
- [ ] REQ-F-B6-7: "결과 공유" 버튼

학습 일정 예고:
- [ ] REQ-F-B7-1: 레벨 테스트 결과 페이지에 "학습 일정 초안 보기" 버튼
- [ ] REQ-F-B7-2: 2~4주 맞춤 학습 계획 초안 표시
- [ ] REQ-F-B7-3: "관심 있음" 버튼
- [ ] REQ-F-B7-4: 대기리스트 등록 확인 모달 & 이메일 구독 옵션
- [ ] REQ-F-B7-5: "다시 보지 않기" 옵션
```

### Backend 팀 체크리스트

```markdown
## Backend (B 태그)

인증:
- [ ] REQ-B-A1-1: Samsung AD 사용자 정보 수신 및 저장
- [ ] REQ-B-A1-2: JWT 토큰 생성
- [ ] REQ-B-A1-3: 신규 사용자 처리
- [ ] REQ-B-A1-4: 기존 사용자 재로그인 처리
- [ ] REQ-F-A1-3 Backend: 로그인 실패 시 에러 응답 + 헬프 링크 정보 전달

개인정보 동의:
- [ ] REQ-B-A3-1: 개인정보 동의 여부 확인 API (GET /profile/consent)
- [ ] REQ-B-A3-2: 개인정보 동의 저장 API (POST /profile/consent)

프로필:
- [ ] REQ-B-A2-1: 닉네임 중복 확인 API
- [ ] REQ-B-A2-2: 유효성 검사 로직
- [ ] REQ-B-A2-3: 대안 생성 로직
- [ ] REQ-B-A2-4: 금칙어 필터
- [ ] REQ-B-A2-5: 사용자 레코드 저장

프로필 수정:
- [ ] REQ-B-A2-Edit-1: 닉네임 변경 API (기존 닉네임 제외)
- [ ] REQ-B-A2-Edit-2: 닉네임 업데이트 & updated_at 갱신
- [ ] REQ-B-A2-Edit-3: 자기평가 정보 수정 API
- [ ] REQ-B-A2-Edit-4: 1초 내 응답

자기평가:
- [ ] REQ-B-B1-1: Survey 스키마 API
- [ ] REQ-B-B1-2: 데이터 저장

문항 생성:
- [ ] REQ-B-B2-1: Item-Gen-Agent 1차 문항 생성
- [ ] REQ-B-B2-2: 문항 정보 구조 정의
- [ ] REQ-B-B2-3: 재미 카테고리 프롬프트
- [ ] REQ-B-B2-4: 2차 난이도 조정
- [ ] REQ-B-B2-5: 조정 로직 구현
- [ ] REQ-B-B2-6: 오답 카테고리 강화
- [ ] REQ-B-B2-7: 3차 이상 제한 로직

테스트 진행 중 저장/재개:
- [ ] REQ-B-B2-Plus-1: 실시간 응답 자동 저장 API
- [ ] REQ-B-B2-Plus-2: 20분 초과 시 상태 저장
- [ ] REQ-B-B2-Plus-3: 재개 기능 구현
- [ ] REQ-B-B2-Plus-4: 메타데이터 기록 (response_time, saved_at)
- [ ] REQ-B-B2-Plus-5: 2초 내 저장 완료

채점:
- [ ] REQ-B-B3-1: Scoring-Agent 채점
- [ ] REQ-B-B3-2: 채점 로직 (객관식, 주관식)
- [ ] REQ-B-B3-3: 20분 초과 시 페널티 로직
- [ ] REQ-B-B3-4: Explain-Agent 해설 생성

등급:
- [ ] REQ-B-B4-1: Rank-Service 구현
- [ ] REQ-B-B4-2: 5등급 정의
- [ ] REQ-B-B4-3: 등급 산출 로직
- [ ] REQ-B-B4-4: 순위 & 백분위 계산
- [ ] REQ-B-B4-5: 신뢰도 라벨
- [ ] REQ-B-B4-Plus-1: 등급별 배지 자동 부여
- [ ] REQ-B-B4-Plus-2: 엘리트 등급 특수 배지 (Agent Specialist 등)
- [ ] REQ-B-B4-Plus-3: 배지 저장 & Profile API 포함

이력:
- [ ] REQ-B-B5-1: 응시 데이터 저장
- [ ] REQ-B-B5-2: 이력 조회 & 비교
- [ ] REQ-B-B5-3: 재응시 API
- [ ] REQ-B-B5-4: 이전 정보 로드
- [ ] REQ-B-B5-5: 재응시 시 새로운 자기평가 레코드 생성 & attempts와 연결

품질:
- [ ] REQ-B-B6-1: RAG 소스 메타 저장
- [ ] REQ-B-B6-2: 콘텐츠 필터링
- [ ] REQ-B-B6-3: 신고 큐 처리
- [ ] REQ-B-B6-4: 난이도 모니터링

재미 모드:
- [ ] REQ-B-B6-Plus-1: Fun-Gen-Agent 문항 생성
- [ ] REQ-B-B6-Plus-2: 가벼운 형식 (시간 제한 없음)
- [ ] REQ-B-B6-Plus-3: 채점 로직
- [ ] REQ-B-B6-Plus-4: Badge-Service 배지/포인트 지급
- [ ] REQ-B-B6-Plus-5: 프로필 API에 배지/포인트 포함

학습 일정 예고:
- [ ] REQ-B-B7-1: Plan-Preview-Agent 학습 계획 생성
- [ ] REQ-B-B7-2: 맞춤 학습 계획 데이터 구성
- [ ] REQ-B-B7-3: 대기리스트 등록 API
- [ ] REQ-B-B7-4: 이메일 알림 발송
- [ ] REQ-B-B7-5: 대기리스트 상태 조회 API
```

---

# 🤖 AGENT REQUIREMENT

## 개요

**Item-Gen-Agent**는 LLM을 기반으로 **동적 문항 생성, 자동 채점, 해설 생성**을 수행하는 자율 AI 에이전트입니다. LangChain의 최신 Agent 패턴과 FastMCP (Model Context Protocol) 프레임워크를 활용하여, Backend API를 도구화하고, 에이전트가 상황에 따라 최적의 도구를 선택·활용하면서 주어진 작업을 완료합니다.

**핵심 특징:**

- **위치**: `./src/agent` 폴더
- **프레임워크**: LangChain + FastMCP
- **LLM**: 사내 Local LLM
- **도구**: Backend API를 FastMCP @tool로 등록 (6개)
  - 도구 1-5: 문항 생성 파이프라인
  - 도구 6: 자동 채점 & 해설 생성 (응시자 답변 평가)
- **의사결정**: 에이전트가 상황에 따라 도구를 선택·활용 (ReAct 패턴)
- **확장 가능**: Tool 6의 설계로 향후 배지·랭킹 도구 추가 용이

---

## 아키텍처

```text
┌──────────────────────────────────────────────────────────┐
│                  Client (Frontend)                       │
└──────────────┬──────────────────────┬────────────────────┘
               │                      │
               │ 1. 문항 요청          │ 2. 답변 제출
               ▼                      ▼
┌──────────────────────────────────────────────────────────┐
│            FastAPI Backend Server                        │
│  ┌────────────────────────────────────────────────┐     │
│  │  Item-Gen-Agent (LangChain)                    │     │
│  │  - Mode 1: 문항 생성 (Tool 1-5)               │     │
│  │  - Mode 2: 채점 & 해설 (Tool 6)               │     │
│  │  - ReAct: 상황에 따라 도구 선택               │     │
│  └────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────┐     │
│  │  FastMCP Server (@tool 등록, 6개)              │     │
│  │  ─── 문항 생성 파이프라인 (Mode 1) ────────   │     │
│  │  - Tool 1: 사용자 정보 조회                   │     │
│  │  - Tool 2: 관심분야별 문항 템플릿 검색        │     │
│  │  - Tool 3: 난이도별 키워드 조회               │     │
│  │  - Tool 4: 문항 품질 검증 (LLM 기반)          │     │
│  │  - Tool 5: 생성된 문항 저장                   │     │
│  │  ─── 채점 파이프라인 (Mode 2) ──────────────  │     │
│  │  - Tool 6: 응답 채점 & 해설 생성 (LLM 기반)  │     │
│  └────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────┘
                     │ SQL
                     ▼
┌──────────────────────────────────────────────────────────┐
│            PostgreSQL Database                           │
│  - question_bank: 생성된 문항 저장소                    │
│  - test_responses: 응시자 답변 & 채점 결과              │
│  - attempt_answers: 자세한 응답 기록                    │
└──────────────────────────────────────────────────────────┘
                     │ HTTP
                     ▼
┌──────────────────────────────────────────────────────────┐
│           LLM Server (Google Gemini)                     │
│  - 문항 생성 (Tool 4의 의미 검증 포함)                  │
│  - 채점 & 해설 생성 (Tool 6)                           │
└──────────────────────────────────────────────────────────┘
```

---

## LLM 설정

### LLM 선택

**MVP 1.0**: Google Gemini API 사용

| 항목 | 값 | 비고 |
|------|-----|------|
| **LLM Provider** | Google Gemini API | 클라우드 기반 LLM |
| **API Key** | `GEMINI_API_KEY` (`.env`에 저장) | 환경 변수로 관리 |
| **LLM Model** | `gemini-1.5-pro` (또는 최신 모델) | Tool 4, Tool 6에서 사용 |
| **호출 방식** | LangChain `ChatGoogle` | `langchain_google_genai` 라이브러리 |

### 설정 방법

**1. `.env` 파일에 API Key 저장**:

```bash
# .env
GEMINI_API_KEY=AIzaSyCE2Hyk-xLl3Mq1BMGtOSZEOCo0HjtAK6s
```

**2. LangChain에서 LLM 초기화**:

```python
from langchain_google_genai import ChatGoogle
from os import getenv

llm = ChatGoogle(
    api_key=getenv("GEMINI_API_KEY"),
    model="gemini-1.5-pro",
    temperature=0.7,  # 창의성 vs 정확성 균형
    max_tokens=2048   # 응답 최대 길이
)
```

**3. Tool 4 (문항 검증) & Tool 6 (채점)에서 사용**:

```python
# Tool 4: 문항 품질 검증 (LLM 기반)
def validate_question_quality(stem, question_type, ...):
    prompt = f"문항을 평가하세요: {stem}"
    response = llm.invoke(prompt)
    # LLM 점수 (0~1) 반환

# Tool 6: 자동 채점 & 해설
def score_and_explain(question_id, user_answer, correct_answer, ...):
    prompt = f"주관식 답변을 평가하세요: {user_answer}"
    response = llm.invoke(prompt)
    # 점수 & 해설 반환
```

### MVP 1.0 vs MVP 2.0 LLM 전환 계획

| 버전 | LLM | 사용처 | 비고 |
|------|-----|-------|------|
| **MVP 1.0** | Google Gemini (클라우드) | Tool 4, Tool 6 | 빠른 개발, API 비용 |
| **MVP 2.0** | 사내 Local LLM (선택사항) | Tool 4, Tool 6 | 비용 절감, 지연시간 감소 |

**전환 시 변경 사항**:

- LangChain `ChatGoogle` → `ChatOllama` 또는 `ChatOpenAI` (로컬 서버)
- API Key → 로컬 LLM 엔드포인트 URL
- 프롬프트 튜닝 (로컬 모델 특성에 맞춰)

---

## FastMCP Tool 정의 (6개)

### 도구 분류

| 카테고리 | 도구 | 목적 | LLM 사용 |
|---------|------|------|---------|
| **문항 생성** | Tool 1 | 사용자 정보 조회 | ❌ (DB 조회) |
| | Tool 2 | 템플릿 검색 | ❌ (Vector DB 검색) |
| | Tool 3 | 키워드 조회 | ❌ (DB 조회) |
| | Tool 4 | 품질 검증 | ✅ **LLM 기반** |
| | Tool 5 | 문항 저장 | ❌ (DB 저장) |
| **자동 채점** | Tool 6 | 답변 채점 & 해설 | ✅ **LLM 기반** |

### Tool 1: Get User Profile

**목적**: 사용자의 자기평가 정보 조회

```python
@tool
def get_user_profile(user_id: str) -> dict:
    """
    사용자의 자기평가 정보를 조회합니다.

    Args:
        user_id: 사용자 ID (UUID)

    Returns:
        {
            "user_id": "uuid",
            "self_level": "beginner|intermediate|advanced",
            "years_experience": 3,
            "job_role": "Backend Engineer",
            "duty": "FastAPI 개발",
            "interests": ["LLM", "RAG", "Agent Architecture"],
            "previous_score": 72  # 이전 응시 점수 (있을 경우)
        }
    """
    # FastAPI Endpoint: GET /api/v1/profile/{user_id}
```

### Tool 2: Search Question Templates

**목적**: 관심분야별 문항 템플릿 검색 → **Few-shot 예시로 에이전트 의사결정 가이드**

**핵심 역할**:

- 이미 검증된 고품질 문항들을 검색
- 이 문항들이 **LLM의 프롬프트에 Few-shot 예시로 동적 추가됨**
- 에이전트가 이 템플릿들을 참고하여 **유사한 구조와 난이도로 새 문항 생성**
- 결과: 일관된 품질 유지 + 문항 다양성 확보

**데이터 흐름**:

```
generate_questions() 호출
    ↓
search_question_templates() 실행 (Tool 2)
    ↓
[검색된 5개 템플릿] → LLM 프롬프트에 Few-shot 예시로 삽입
    ↓
LLM이 템플릿 스타일을 참고하여 새 문항 생성 (Tool 4,5로 검증/저장)
```

```python
@tool
def search_question_templates(
    interests: list[str],
    difficulty: int,
    category: str
) -> list[dict]:
    """
    관심분야와 난이도에 맞는 검증된 문항 템플릿을 검색합니다.
    (Few-shot 예시로 사용)

    Args:
        interests: ["LLM", "RAG", ...] - 관심분야 목록
        difficulty: 1~10 - 난이도 (±1 범위 허용)
        category: "technical" | "business" | "general"

    Returns:
        [
            {
                "id": "question_id",
                "stem": "LLM과 RAG의 차이점은?",
                "type": "short_answer",
                "choices": [...],  # 객관식인 경우
                "correct_answer": "정답",
                "correct_rate": 0.75,  # 정답률 (품질 지표)
                "usage_count": 5,  # 사용 횟수
                "avg_difficulty_score": 5  # 실제 체감 난이도
            },
            ...
        ]
    """
    # FastAPI Endpoint: POST /api/v1/tools/search-templates

    # 응답 (최대 5개 템플릿)
    # 품질 순서: correct_rate 높은 순 → usage_count 높은 순
```

**Few-shot 활용 예시**:

에이전트가 생성 프롬프트에서 다음과 같이 활용:

```
검색된 Few-shot 템플릿 (이 스타일로 생성하세요):

예시 1 - 주관식 (LLM, 난이도 5):
Q: "Retrieval-Augmented Generation에서 Augmentation의 역할은?"
A: "외부 지식베이스에서 검색한 관련 정보를 LLM 프롬프트에 추가"
정답률: 0.75 (검증됨)

예시 2 - 객관식 (LLM, 난이도 5):
Q: "LLM의 Context Window 제한을 극복하는 방법?"
A) Prompt Engineering  B) RAG  C) Fine-tuning  D) 모두 가능
정답: D) 정답률: 0.82 (검증됨)

...위 스타일을 참고하여 새 문항을 생성하세요...
```

### Tool 3: Get Difficulty Keywords

**목적**: 난이도별 키워드 및 개념 조회

```python
@tool
def get_difficulty_keywords(
    difficulty: int,
    category: str
) -> dict:
    """
    특정 난이도와 카테고리에 맞는 핵심 키워드와 개념을 조회합니다.
    (문항 생성 시 포함할 주요 개념을 파악하기 위함)

    Args:
        difficulty: 1~10 - 난이도
        category: 카테고리 (e.g., "LLM", "RAG", "Agent Architecture")

    Returns:
        {
            "keywords": ["prompt engineering", "token window", "hallucination"],
            "concepts": ["Context Window", "Attention Mechanism"],
            "example_questions": [
                "What is prompt engineering and why is it important?"
            ]
        }
    """
    # FastAPI Endpoint: POST /api/v1/tools/difficulty-keywords
```

### Tool 4: Validate Question Quality

**목적**: 생성된 문항의 품질 검증 (LLM 의미 검증 + 규칙 기반 검증)

**검증 방식** (2단계 접근):

1. **LLM 기반 의미 검증** (semantic evaluation)
   - 문항이 명확하고 의도된 학습목표를 평가하는가?
   - 문항의 난이도가 사용자 수준과 적절한가?
   - 정답이 객관적이고 검증 가능한가?
   - 편향이나 부적절한 표현은 없는가?
   - 점수: 0.0 ~ 1.0

2. **규칙 기반 품질 검증** (rule-based validation)
   - 문항 길이: 250자 이내 ✓
   - 선택지 수: 객관식은 4~5개 ✓
   - 정답 형식: 유효하고 명확한가? ✓
   - 중복/유사 문항: 기존 문항과 유사도 < 70% ✓
   - 최소 점수 threshold: 0.7 이상

```python
@tool
def validate_question_quality(
    stem: str,
    question_type: str,
    choices: list[str] = None,
    correct_answer: str = None,
    batch: bool = False  # 배치 처리 지원
) -> dict | list[dict]:
    """
    생성된 문항이 요구사항을 충족하는지 검증합니다.
    LLM 기반 의미 검증 + 규칙 기반 품질 검증 조합.

    Args:
        stem: 문항 내용
        question_type: "multiple_choice" | "true_false" | "short_answer"
        choices: 객관식 선택지 (해당하는 경우)
        correct_answer: 정답
        batch: True인 경우 여러 문항을 한 번에 검증 (성능 향상)

    Returns (단일):
        {
            "is_valid": True,  # 최소 기준(final_score >= 0.7) 통과 여부
            "score": 0.92,  # LLM 의미 점수 (0~1)
            "rule_score": 0.95,  # 규칙 기반 점수 (0~1)
            "final_score": 0.92,  # min(score, rule_score)
            "feedback": "명확하고 적절한 난이도의 문항입니다.",
            "issues": [],  # 발견된 문제점
            "recommendation": "pass" | "revise" | "reject"
            # pass: final_score >= 0.85 → 즉시 저장
            # revise: 0.70 <= final_score < 0.85 → 피드백 후 재생성
            # reject: final_score < 0.70 → 폐기, 새 문항 생성
        }

    Returns (배치):
        [
            {...single result...},
            {...single result...}
        ]
    """
    # FastAPI Endpoint: POST /api/v1/tools/validate-question
    # Batch 처리 시: POST /api/v1/tools/validate-question/batch
```

**배치 처리 예시**:

```python
# 5개 문항을 한 번에 검증 (효율성 향상)
validation_results = validate_question_quality(
    stem=[q1, q2, q3, q4, q5],
    question_type=["multiple_choice", "short_answer", "multiple_choice", "true_false", "short_answer"],
    batch=True
)
# 응답: [result1, result2, result3, result4, result5]
```

### Tool 5: Save Generated Question

**목적**: 검증 통과한 문항을 question_bank에 저장

**스키마 상세**: "배치 처리 & 데이터 계약" 섹션의 **"데이터 계약: save_generated_question 재정의"** (line 2012-2039) 참조

- **요약**: validation_score, explanation 메타데이터 포함하여 저장
- **FastAPI Endpoint**: POST /api/v1/tools/save-question
- **반환값**: question_id, round_id, saved_at, success

### Tool 6: Score & Generate Explanation

**목적**: 응시자의 답변을 자동 채점하고 해설 생성 (LLM 기반)

**핵심 역할**:

- 객관식/OX: 정답과 대조하여 자동 채점 (규칙 기반)
- 주관식: LLM을 사용하여 의미 기반 채점 (키워드 포함도, 문맥 이해도 등)
- 모든 문항: 왜 이것이 정답인지 해설 자동 생성 (학습 효과 극대화)
- 채점 결과와 해설을 test_responses & attempt_answers 테이블에 저장

```python
@tool
def score_and_explain(
    session_id: str,
    user_id: str,
    question_id: str,
    question_type: str,
    user_answer: str,
    correct_answer: str = None,
    correct_keywords: list[str] = None,
    difficulty: int = None,
    category: str = None
) -> dict:
    """
    응시자의 답변을 채점하고 해설을 생성합니다.

    Args:
        session_id: 시험 세션 ID (test_responses & attempt_answers와 연결)
        user_id: 응시자 ID
        question_id: 문항 ID (question_bank의 ID)
        question_type: "multiple_choice" | "true_false" | "short_answer"
        user_answer: 응시자의 답변
        correct_answer: 정답 (객관식/OX용)
        correct_keywords: 정답 키워드 (주관식용)
        difficulty: 난이도 (LLM 프롬프트 컨텍스트용)
        category: 카테고리 (LLM 프롬프트 컨텍스트용)

    Returns:
        {
            "attempt_id": "uuid",  # Tool 6가 자동 생성 (attempt_answers 저장 시 사용)
            "session_id": "uuid",  # 채점 결과를 test_responses & attempt_answers와 연결
            "question_id": "uuid",
            "user_id": "uuid",
            "is_correct": True,
            "score": 100,  # 0~100 (객관식/OX) 또는 0~100 (주관식, LLM 채점)
            "explanation": "정답 해설: 이것이 정답인 이유는...",
            "keyword_matches": ["keyword1", "keyword2"],  # 주관식일 경우
            "feedback": "더 나은 답변을 위한 피드백...",  # 부분 정답 시
            "graded_at": "2025-11-06T10:35:00Z"
        }
    """
    # FastAPI Endpoint: POST /api/v1/tools/score-and-explain

    # 채점 로직:
    # 1. 객관식/OX: user_answer == correct_answer → is_correct = True, score = 100
    # 2. 주관식:
    #    a) LLM 호출: 키워드 포함도, 문맥 이해도 평가 (0~100)
    #    b) is_correct = (score >= 80) 로 판단 (80 이상만 정답, 70-79는 부분 정답)
    # 3. 해설 생성 (모든 타입):
    #    - 정답 이유, 자주 하는 실수, 관련 개념 설명
    # 4. attempt_id 자동 생성 및 test_responses & attempt_answers에 저장
    #    - attempt_id = uuid.uuid4()
    #    - attempt_answers.attempt_id에 저장되어 응시 기록 추적에 사용
```

**채점 기준**:

| 문항 유형 | 채점 방식 | 기준 | is_correct 판정 |
|---------|---------|------|----------------|
| **객관식** | 규칙 기반 (정확 매칭) | user_answer == correct_answer | score = 100 → True, else 0 → False |
| **OX (참거짓)** | 규칙 기반 (정확 매칭) | user_answer == correct_answer | score = 100 → True, else 0 → False |
| **주관식** | **LLM 기반** (의미 평가) | 키워드 포함도, 문맥 이해도, 정확성 | score >= 80 → True, 70~79 → False (부분), < 70 → False |

**반환 데이터 저장**:

```python
# test_responses 테이블에 저장
{
    "session_id": "...",
    "question_id": "...",
    "user_id": "...",
    "is_correct": True|False,
    "score": 85,
    "graded_at": "..."
}

# attempt_answers 테이블에 저장
{
    "attempt_id": "...",
    "session_id": "...",  # test_responses와 연결
    "question_id": "...",
    "user_answer": "...",
    "is_correct": True|False,
    "score": 85,
    "explanation": "정답 해설: ...",
    "feedback": "부분 정답 피드백 (있을 경우)",
    "keyword_matches": ["key1", "key2"],  # 주관식 경우
    "graded_at": "..."
}
```

---

## Tool 선택 조건 (ReAct 패턴)

에이전트는 다음 **결정 규칙**에 따라 도구를 선택합니다. 강제 시퀀스가 아니라, 상황에 따른 유연한 선택을 지원합니다.

### Mode 1: 문항 생성 (generate_questions)

| 단계 | 도구 | 호출 조건 | 입력 | 예외 처리 |
|-----|------|---------|------|---------|
| 1 | Tool 1: get_user_profile | **항상** (필수) | user_id | 실패 → 재시도 3회 → 기본값 사용 |
| 2 | Tool 2: search_question_templates | 관심분야 O | interests | 검색 결과 없음 → 스킵 (Tool 3으로 진행) |
| 3 | Tool 3: get_difficulty_keywords | **항상** (필수) | difficulty, category | 실패 → 캐시된 키워드 반환 |
| 4 | LLM: 문항 생성 | **항상** (필수) | 프롬프트 (Tool 1,2,3 결과 포함) | LLM 응답 오류 → 자동 교정 루프 (최대 3회) |
| 5 | Tool 4: validate_question_quality | **각 문항마다** | stem, type, choices | >= 0.85 → pass / 0.70-0.84 → revise (최대 2회) / < 0.70 → reject 폐기 |
| 6 | Tool 5: save_generated_question | 검증 통과 시만 | 생성된 문항 메타데이터 | 저장 실패 → 메모리 큐 임시 저장 → 배치 재시도 |

### Mode 2: 자동 채점 (score_and_explain)

| 단계 | 도구 | 호출 조건 | 입력 |
|-----|------|---------|------|
| 1 | Tool 6: score_and_explain | 답변 제출 시 | 사용자 답변 + 정답 정보 |

---

## 카테고리 & 난이도 체계 통일

### 카테고리 정의

전체 시스템에서 **단일 카테고리 체계** 사용:

```
기술: "LLM", "RAG", "Agent Architecture", "Prompt Engineering", "Fine-tuning"
업무: "Product Strategy", "Team Management", "Project Planning"
일반: "Communication", "Problem Solving"
```

### 카테고리 매핑 규칙

| 도구 | 사용 파라미터 | 매핑 방식 |
|-----|--------------|---------|
| Tool 2 (search_templates) | `category: str` ("technical\|business\|general") | 도메인 → 상위 카테고리 자동 변환 |
| Tool 3 (get_keywords) | `category: str` (도메인, e.g., "LLM") | 직접 도메인 사용 |
| Tool 4 (validate_quality) | `category: str` (도메인, e.g., "RAG") | 직접 도메인 사용 |
| Tool 6 (score_and_explain) | `category: str` (도메인) | 직접 도메인 사용 |

**변환 로직**:

```python
def get_top_category(domain: str) -> str:
    """도메인 → 상위 카테고리"""
    technical_domains = ["LLM", "RAG", "Agent Architecture", "Prompt Engineering", "Fine-tuning"]
    business_domains = ["Product Strategy", "Team Management", "Project Planning"]

    if domain in technical_domains:
        return "technical"
    elif domain in business_domains:
        return "business"
    else:
        return "general"
```

---

## 배치 처리 & 데이터 계약

### 배치 처리 API 명확화

#### Tool 4 (validate_question_quality) - 단일 vs 배치

**단일 호출**:

```python
# POST /api/v1/tools/validate-question
{
    "stem": "문항 내용",
    "question_type": "multiple_choice",
    "choices": ["A", "B", "C", "D"],
    "correct_answer": "A"
}

# 응답
{
    "is_valid": True,
    "score": 0.92,
    "rule_score": 0.95,
    "final_score": 0.92,
    "recommendation": "pass"
}
```

**배치 호출** (5개 문항 한 번에):

```python
# POST /api/v1/tools/validate-question/batch
{
    "questions": [
        {
            "stem": "Q1",
            "question_type": "multiple_choice",
            "choices": [...],
            "correct_answer": "A"
        },
        ...
    ]
}

# 응답
[
    {"is_valid": True, "score": 0.92, ...},
    {"is_valid": True, "score": 0.88, ...},
    ...
]
```

### round_id 생성 규칙

```python
# generate_questions() 호출 시 round_id 자동 생성
round_id = f"{test_session_id}_{round_number}_{datetime.utcnow().isoformat()}"

# 예시: "sess_abc123_1_2025-11-06T10:30:00.000Z"

# save_generated_question의 입력에 자동 포함
save_generated_question(
    ...,
    round_id=round_id  # 자동 생성됨
)
```

### 데이터 계약: save_generated_question 재정의

**통일된 입출력 스키마**:

```python
@tool
def save_generated_question(
    item_type: str,  # "multiple_choice" | "true_false" | "short_answer"
    stem: str,
    choices: list[str] = None,
    correct_key: str = None,  # 객관식/OX 정답
    correct_keywords: list[str] = None,  # 주관식 키워드
    difficulty: int,
    categories: list[str],  # 도메인 카테고리 (e.g., ["LLM", "RAG"])
    round_id: str,
    validation_score: float = None,  # Tool 4의 final_score (메타)
    explanation: str = None  # 선택사항 (향후 추가 가능)
) -> dict:
    """
    Returns:
    {
        "question_id": "uuid",
        "round_id": "...",  # 입력받은 round_id
        "saved_at": "2025-11-06T10:30:00Z",
        "success": True
    }
    """
```

### _parse_agent_output 데이터 계약 수정

```python
def _parse_agent_output(self, result: dict) -> list[dict]:
    """
    최종 반환값 (모든 도구 호출 완료 후):
    [
        {
            "question_id": "uuid",  # Tool 5에서 받은 ID
            "stem": "문항 내용",
            "type": "multiple_choice|true_false|short_answer",
            "choices": [...],  # 객관식 선택지
            "correct_answer": "정답",  # Tool 5 입력
            "difficulty": 5,
            "category": "LLM",
            "round_id": "sess_abc_1_...",
            "validation_score": 0.92,  # Tool 4의 final_score
            "saved_at": "2025-11-06T10:30:00Z"  # Tool 5 응답
        },
        ...
    ]
    """
```

---

## 문항 구성 규칙

### 문항 유형 비율

```
객관식 (Multiple Choice): 40%
OX 참거짓 (True/False): 20%
주관식 (Short Answer): 40%

예시 (5개 문항):
- 객관식: 2개
- OX: 1개
- 주관식: 2개
```

### 난이도 분포

```
라운드 1 (기초 평가):
- 사용자 자기평가 수준을 기준으로 ±1 범위
- 예: 중급(5) 선택 → 4, 5, 5, 6, 6

라운드 2 (적응형 평가):
- 라운드 1 점수 기반 동적 결정
- 점수 >= 80: 난이도 +1
- 점수 60~79: 난이도 동일
- 점수 < 60: 난이도 -1
```

### 문항 제시 순서

```
쉬운 것 → 어려운 것 (점진 증가)

예시 (난이도 4, 5, 5, 6, 6):
Q1: 난이도 4 (기본 개념)
Q2: 난이도 5 (개념 이해)
Q3: 난이도 5 (개념 응용)
Q4: 난이도 6 (심화 개념)
Q5: 난이도 6 (시스템 설계)
```

---

## 질 검증 기준표

### validate_question_quality의 recommendation 결정 규칙

| final_score | 상태 | 액션 | 최대 재시도 |
|------------|------|------|-----------|
| >= 0.85 | **PASS** | 즉시 저장 (Tool 5) | 0회 |
| 0.70 ~ 0.84 | **REVISE** | LLM에 피드백 제공 후 재생성 | 최대 2회 |
| < 0.70 | **REJECT** | 폐기, 새 문항 생성 요청 | - |

### Revise 루프 피드백 예시

```
초차 생성: final_score = 0.75 → REVISE
LLM 피드백:
"문항이 명확하지만 난이도가 낮게 평가됨. 더 깊이 있는 개념을 포함해주세요."

재생성: final_score = 0.88 → PASS
```

---

## 난이도 결정 전략

### 라운드별 난이도 결정

**라운드 1 (기초 평가)**:

```python
user_level = get_user_self_level()  # beginner(3) | intermediate(5) | advanced(7)
base_difficulty = user_level
round1_difficulties = [
    base_difficulty - 1,  # 1번 문항
    base_difficulty,      # 2번 문항
    base_difficulty,      # 3번 문항
    base_difficulty + 1,  # 4번 문항
    base_difficulty + 1   # 5번 문항
]
```

**라운드 2 (적응형 평가)**:

```python
round1_score = get_round1_score()
if round1_score >= 80:
    adjustment = +1  # 어려워짐
elif round1_score < 60:
    adjustment = -1  # 쉬워짐
else:
    adjustment = 0   # 유지

round2_difficulties = [
    base_difficulty + adjustment - 1,
    base_difficulty + adjustment,
    base_difficulty + adjustment,
    base_difficulty + adjustment + 1,
    base_difficulty + adjustment + 1
]
```

---

## 에이전트 실행 전략

### 전략: 배치 생성 + 배치 검증 (LLM 호출 최적화)

**목표**: 5개 문항 생성 시 LLM 호출 최소화

**단계별 실행**:

```
Step 1: 사용자/템플릿/키워드 조회 (Tool 1,2,3)
         └─ API 호출 3~4회 (병렬 가능)

Step 2: 5개 문항 일괄 생성 (LLM 1회 호출)
         └─ 프롬프트: "다음 5개 문항을 한 번에 생성하세요" (난이도 분포 포함)
         └─ 응답: JSON 배열 [Q1, Q2, Q3, Q4, Q5]

Step 3: 5개 문항 일괄 검증 (Tool 4 배치 호출 1회)
         └─ POST /api/v1/tools/validate-question/batch
         └─ 응답: [result1, result2, result3, result4, result5]

Step 4: 검증 통과 문항 저장 (Tool 5, 병렬 5회)
         └─ 각 문항별 저장 (optional: 배치 저장 API 추가 가능)

총 LLM 호출: 1회 (문항 생성)
총 Tool 호출: ~10회 (Tool 1,2,3,4,5)
총 시간: ~3초 (LLM 2초 + Tool 1초)
```

### 에이전트 상태 관리

```python
# 에이전트 프롬프트에 명시된 생성 전략:
"""
당신은 다음 5개의 문항을 한 번에 생성해야 합니다:

문항 1: 난이도 {d1}, 주제: {topic1}, 유형: {type1}
문항 2: 난이도 {d2}, 주제: {topic2}, 유형: {type2}
...
문항 5: 난이도 {d5}, 주제: {topic5}, 유형: {type5}

생성 결과를 다음 JSON 형식으로 반환하세요:
{
    "questions": [
        {
            "stem": "Q1 내용",
            "type": "multiple_choice",
            "choices": [...],
            "correct_answer": "A",
            "difficulty": 4,
            "category": "LLM"
        },
        ...
    ]
}
"""
```

---

## LLM 호출 최적화 전략

### 현황 분석

- **나이브 구현**: 문항 생성 (5회) + 검증 (5회) = 10+ LLM 호출
- **최적화 후**: 생성 (1회) + 검증 (API, LLM 없음 or 배치) = 1~2회
- **감소율**: 80~90%

### 최적화 기법

#### 1단계: 배치 생성

- LLM에 "5개 문항을 한 번에 생성" 요청
- 프롬프트: 난이도/주제/유형 명시 포함
- 응답: JSON 배열로 구조화

#### 2단계: 배치 검증

- Tool 4의 배치 모드 사용 (`validate_question_quality(..., batch=True)`)
- 5개 문항을 1회 API 호출로 검증

#### 3단계: 스마트 재생성

- 검증 실패 시 전체 재생성이 아닌, 실패한 문항만 개별 재생성
- 최대 1회 추가 LLM 호출로 제한

---

## Agent 스펙

### Agent 클래스: `ItemGenAgent`

```python
class ItemGenAgent:
    """
    LangChain을 기반으로 하는 Item 생성 에이전트
    """

    def __init__(
        self,
        llm_endpoint: str,
        mcp_server: FastMCPServer,
        model_name: str = "local-llm",
        temperature: float = 0.7,
        max_iterations: int = 10
    ):
        """
        Args:
            llm_endpoint: 사내 Local LLM 엔드포인트
            mcp_server: FastMCP 서버 인스턴스
            model_name: LLM 모델명
            temperature: LLM 생성 시 창의성 (0~1)
            max_iterations: 최대 반복 시도 횟수
        """
        self.llm = ChatLocal(
            endpoint=llm_endpoint,
            model=model_name,
            temperature=temperature
        )
        self.tools = self._register_tools(mcp_server)
        self.agent = self._create_agent()
        self.max_iterations = max_iterations

    def _register_tools(self, mcp_server: FastMCPServer) -> list:
        """FastMCP에서 6개의 도구를 가져옵니다."""
        return [
            mcp_server.get_tool("get_user_profile"),
            mcp_server.get_tool("search_question_templates"),
            mcp_server.get_tool("get_difficulty_keywords"),
            mcp_server.get_tool("validate_question_quality"),
            mcp_server.get_tool("save_generated_question"),
            mcp_server.get_tool("score_and_explain")  # Tool 6: 자동 채점 & 해설
        ]

    def generate_questions(
        self,
        user_id: str,
        round_number: int,
        count: int = 5,
        previous_score: int = None
    ) -> list[dict]:
        """
        Mode 1: 문항을 생성합니다. (ReAct 패턴 - 도구 선택 규칙 따름)

        실행 흐름:
        1. ✓ REQUIRED: get_user_profile → 사용자 정보 조회
        2. ⊗ CONDITIONAL: search_question_templates
           - 관심분야 있으면 → 검색해서 Few-shot 예시로 활용
           - 검색 결과 없으면 → 스킵
        3. ✓ REQUIRED: get_difficulty_keywords → 난이도별 핵심 개념 파악
        4. ✓ REQUIRED: LLM이 {count}개 문항 배치 생성
           - 난이도 분포 적용
           - 유형 비율 적용 (객관식 40%, OX 20%, 주관식 40%)
        5. ✓ REQUIRED: validate_question_quality (배치 검증)
           - 점수 >= 0.85: PASS → 즉시 저장
           - 0.70~0.84: REVISE → 피드백 후 재생성 (최대 2회)
           - < 0.70: REJECT → 폐기, 다른 문항 생성
        6. ✓ REQUIRED: save_generated_question (검증 통과 문항만)
        7. ✓ REQUIRED: _parse_agent_output → 최종 결과 파싱

        Args:
            user_id: 사용자 ID
            round_number: 라운드 번호 (1 또는 2)
            count: 생성할 문항 수 (기본 5개)
            previous_score: 이전 라운드 점수 (2라운드인 경우)

        Returns:
            생성된 문항 리스트 (검증 통과한 것만)
        """
        input_prompt = f"""
        Task: 사용자를 위한 {count}개의 적응형 문항 생성 및 저장

        Context:
        - 사용자 ID: {user_id}
        - 라운드: {round_number}
        - 필요한 문항 수: {count}개
        {'- 이전 라운드 점수: ' + str(previous_score) if previous_score else '- 첫 라운드 기초 평가'}

        Tool 호출 규칙 (ReAct 패턴 - 상황에 따라 선택):

        ✓ 필수 (항상 호출):
          1. get_user_profile: 사용자 정보 조회
          2. get_difficulty_keywords: 난이도별 핵심 개념 파악

        ⊗ 조건부 (상황에 따라 선택):
          2.1. search_question_templates: 사용자 관심분야가 있으면 → 검색해서 Few-shot 활용
          2.2. search_question_templates: 검색 결과 없으면 → 스킵하고 다음 진행

        ✓ 필수 (생성 후):
          3. LLM으로 {count}개 문항 생성 (배치):
             - 난이도 분포: {round_number}라운드 규칙 적용
             - 유형 비율: 객관식 40%, OX 20%, 주관식 40%
             - 응답 형식: JSON 배열

          4. validate_question_quality: 5개 문항 배치 검증
             - 통과 (점수 >= 0.85): 즉시 저장
             - 수정 (점수 0.70~0.84): LLM 피드백 후 재생성 (최대 2회)
             - 거부 (점수 < 0.70): 폐기하고 다른 문항 생성

          5. save_generated_question: 검증 통과 문항만 저장
             - validation_score 메타데이터 포함

        최종 결과를 JSON 형식으로 반환하세요:
        {{
            "status": "success" | "partial" | "failed",
            "generated_count": N,
            "questions": [...]
        }}
        """

        from langchain.agents import AgentExecutor

        # Mode 1: self.agent는 _get_generation_system_prompt()로 초기화됨
        # (Mode 2와 구분하여 생성 전용 프롬프트 사용)
        executor = AgentExecutor(
            agent=self.agent,  # Mode 1: 생성 전용 에이전트
            tools=self.tools,
            max_iterations=self.max_iterations,
            verbose=True
        )

        result = executor.invoke({"input": input_prompt})
        return self._parse_agent_output(result)

    def _create_agent(self):
        """
        Mode 1 전용 Agent 생성 (문항 생성용)

        __init__에서 self.agent 초기화 시 호출됨.
        Mode 2 (자동 채점)는 score_and_explain() 메서드에서
        별도의 에이전트를 생성하므로 이 메서드와 독립적으로 동작함.
        """
        from langchain.agents import create_tool_calling_agent

        return create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self._get_generation_system_prompt()  # Mode 1: 생성용 프롬프트
        )

    def _get_generation_system_prompt(self) -> str:
        """
        Mode 1: 문항 생성 전용 시스템 프롬프트

        주의: 이 프롬프트는 generate_questions() 실행 시,
        search_question_templates()로 검색된 템플릿들이
        Few-shot 예시로 동적으로 추가됩니다.
        """
        return """당신은 AI 역량 평가 시스템의 지능형 문항 생성 에이전트입니다.

당신의 역할:
- 사용자의 경력, 직군, 관심분야에 맞춰진 문항을 동적으로 생성
- 난이도를 적절히 조정하여 도전적이면서도 공정한 평가 보장
- 객관식, OX, 주관식을 적절히 혼합
- search_question_templates에서 검색된 템플릿을 참고하여 유사 구조로 생성
- 생성된 문항의 품질을 검증한 후 저장

제약사항:
- 각 문항은 250자 이내
- 정답은 명확하고 검증 가능해야 함
- 편향된 표현이나 부적절한 내용 금지
- 한국어 기본, 명확한 표현 사용

생성 규칙:
- 난이도 1~3: 기본 개념 정의, 단순 적용
- 난이도 4~6: 개념 이해, 실무 적용
- 난이도 7~10: 심화 개념, 시스템 설계, 엣지 케이스"""

    def _get_scoring_system_prompt(self) -> str:
        """
        Mode 2: 자동 채점 & 해설 생성 전용 시스템 프롬프트
        """
        return """당신은 AI 역량 평가 시스템의 자동 채점 및 해설 생성 에이전트입니다.

당신의 역할:
- 응시자의 답변을 문항 유형에 맞게 채점
- 객관식/OX: 정답 대조로 정확한 채점
- 주관식: 의미 기반 평가로 키워드 포함도 및 문맥 이해도 판단
- 모든 문항에 대해 학습 효과를 높이는 해설 생성
- 틀린 답변에 대해 건설적인 피드백 제공

채점 기준:
- 채점 점수는 0~100 범위
- 객관식/OX: 정답 매칭 시 100점, 오답 0점
- 주관식: 키워드 포함도/문맥 이해도 평가 (0~100)
- is_correct: 주관식은 점수 >= 70일 때만 True

제약사항:
- 객관적이고 공정한 채점
- 해설은 250자 이내, 명확하고 이해하기 쉬운 언어 사용
- 한국어 기본, 명확한 표현 사용

해설 구성:
- 정답 이유
- 자주 하는 실수
- 관련된 개념 설명"""

    def _get_system_prompt(self) -> str:
        """
        Deprecated: 하위호환성용. _get_generation_system_prompt() 사용 권장
        """
        return self._get_generation_system_prompt()

    def _parse_agent_output(self, result: dict) -> list[dict]:
        """
        에이전트 출력을 문항 리스트로 파싱합니다.

        AgentExecutor의 output 형식:
        {
            "output": "최종 응답 텍스트",
            "intermediate_steps": [...]  # 도구 호출 기록
        }

        이를 다음 형식으로 변환:
        [
            {
                "question_id": "uuid",
                "stem": "문항 내용",
                "type": "multiple_choice|true_false|short_answer",
                "choices": [...],
                "correct_answer": "정답",
                "difficulty": 5,
                "category": "LLM",
                "explanation": "해설",
                "validation_score": 0.92,
                "saved_at": "2025-11-06T10:30:00Z"
            },
            ...
        ]
        """
        import json
        import logging

        logger = logging.getLogger("item_gen_agent")

        try:
            # AgentExecutor의 "output" 필드에서 최종 JSON 추출
            raw_output = result.get("output", "")

            # JSON 블록 찾기 (```json ... ``` 형식)
            if "```json" in raw_output:
                json_start = raw_output.index("```json") + 7
                json_end = raw_output.index("```", json_start)
                json_str = raw_output[json_start:json_end].strip()
            elif "{" in raw_output:
                # JSON 객체 직접 추출
                json_start = raw_output.index("{")
                json_end = raw_output.rindex("}") + 1
                json_str = raw_output[json_start:json_end]
            else:
                logger.error("No JSON found in agent output")
                return []

            parsed = json.loads(json_str)
            questions = parsed.get("questions", [])

            logger.info(f"Successfully parsed {len(questions)} questions")
            return questions

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}, raw_output: {raw_output}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in _parse_agent_output: {e}")
            return []

    def score_and_explain(
        self,
        user_id: str,
        session_id: str,
        question_id: str,
        question_type: str,
        user_answer: str,
        correct_answer: str = None,
        correct_keywords: list[str] = None,
        difficulty: int = None,
        category: str = None
    ) -> dict:
        """
        응시자의 답변을 채점하고 해설을 생성합니다. (Mode 2: 채점)

        Args:
            user_id: 응시자 ID
            session_id: 테스트 세션 ID (답변 기록 추적용)
            question_id: 문항 ID (question_bank의 ID)
            question_type: "multiple_choice" | "true_false" | "short_answer"
            user_answer: 응시자의 답변
            correct_answer: 정답 (필수 if question_type in ['multiple_choice', 'true_false'], 객관식/OX용)
            correct_keywords: 정답 키워드 (필수 if question_type == 'short_answer', 주관식용)
            difficulty: 난이도 (LLM 프롬프트 컨텍스트용)
            category: 카테고리 (LLM 프롬프트 컨텍스트용)

        Returns:
            {
                "attempt_id": "uuid",  # Tool 6이 자동 생성
                "session_id": "...",  # 입력받은 session_id
                "question_id": "uuid",
                "user_id": "uuid",
                "is_correct": True|False,
                "score": 85,  # 0~100
                "explanation": "정답 해설: 이것이 정답인 이유는...",
                "keyword_matches": ["keyword1", "keyword2"] | null,  # 주관식인 경우만 배열, 아니면 null
                "feedback": "더 나은 답변을 위한 피드백..." | null,  # 부분 정답 시에만, 아니면 null
                "graded_at": "2025-11-06T10:35:00Z"
            }

        **반환 필드 조건부 설정**:
        - keyword_matches: question_type == 'short_answer'일 때만 배열 (다른 타입: null)
        - feedback: 주관식에서 부분 정답 (70 <= score < 80)일 때만 값 포함
          (완전 정답 또는 완전 오답 시: null)
        """
        # 정답 정보를 안전하게 처리
        correct_value = correct_answer if question_type != "short_answer" else None
        correct_kw = correct_keywords if question_type == "short_answer" else None

        scoring_prompt = f"""
        Task: 응시자의 답변을 채점하고 학습용 해설 생성

        Context:
        - 세션 ID: {session_id}
        - 문항 ID: {question_id}
        - 문항 유형: {question_type}
        - 사용자 답변: {user_answer}
        - 난이도: {difficulty}
        - 카테고리: {category}

        Scoring Reference (Tool 6에 전달할 정보):
        - 객관식/OX 정답: {correct_value}
        - 주관식 정답 키워드: {correct_kw}

        Action:
        1. score_and_explain 도구 호출 (필수 인자):
           - user_id: {user_id}
           - session_id: {session_id}
           - question_id: {question_id}
           - question_type: {question_type}
           - user_answer: {user_answer}
           - correct_answer: {correct_value}
           - correct_keywords: {correct_kw}
           - difficulty: {difficulty}
           - category: {category}

        2. 채점 로직:
           - 객관식/OX: 정답 매칭 (user_answer == correct_answer → 100 or 0)
           - 주관식: LLM 의미 평가 (키워드 포함도, 문맥 이해도)

        3. 결과:
           - attempt_id: Tool 6이 자동 생성 (uuid)
           - keyword_matches, feedback: 주관식인 경우만 반환
           - test_responses & attempt_answers에 session_id와 함께 저장

        JSON 형식으로 반환하세요 (Tool 6 스키마와 일치):

        **예시 1: 객관식 정답**
        {{
            "attempt_id": "uuid",
            "session_id": "{session_id}",
            "question_id": "{question_id}",
            "user_id": "{user_id}",
            "is_correct": True,
            "score": 100,
            "explanation": "정답 해설: ...",
            "keyword_matches": null,  # 객관식이므로 null
            "feedback": null,  # 정답이므로 null
            "graded_at": "2025-11-06T10:35:00Z"
        }}

        **예시 2: 주관식 정답**
        {{
            "attempt_id": "uuid",
            "session_id": "{session_id}",
            "question_id": "{question_id}",
            "user_id": "{user_id}",
            "is_correct": True,
            "score": 95,
            "explanation": "정답 해설: ...",
            "keyword_matches": ["keyword1", "keyword2"],  # 주관식이므로 배열
            "feedback": null,  # 정답이므로 null
            "graded_at": "2025-11-06T10:35:00Z"
        }}

        **예시 3: 주관식 부분 정답**
        {{
            "attempt_id": "uuid",
            "session_id": "{session_id}",
            "question_id": "{question_id}",
            "user_id": "{user_id}",
            "is_correct": False,
            "score": 75,
            "explanation": "정답 해설: ...",
            "keyword_matches": ["keyword1"],  # 주관식이므로 배열 (부분 매칭)
            "feedback": "더 나은 답변을 위한 피드백 (부분 정답 시에만)",
            "graded_at": "2025-11-06T10:35:00Z"
        }}
        """

        from langchain.agents import AgentExecutor, create_tool_calling_agent

        # Mode 2: 별도의 에이전트 생성 (Tool 6만 사용)
        # 중요: Tool 6 (score_and_explain)만 사용하도록 제한
        # Mode 1과 달리 채점은 단일 Tool 호출로 완료 (다른 도구 불필요)
        tool_6_only = [t for t in self.tools if "score_and_explain" in getattr(t, 'name', '')]

        if not tool_6_only:
            raise ValueError("Tool 6 (score_and_explain) not found in tool list")

        scoring_agent = create_tool_calling_agent(
            llm=self.llm,
            tools=tool_6_only,  # ← Tool 6만 사용
            prompt=self._get_scoring_system_prompt()  # ← Mode 2 전용 프롬프트
        )

        executor = AgentExecutor(
            agent=scoring_agent,
            tools=tool_6_only,  # ← Tool 6만 사용
            max_iterations=2,  # 채점은 1회 호출로 충분 (retry 1회)
            verbose=True
        )

        result = executor.invoke({"input": scoring_prompt})
        return self._parse_scoring_output(result)

    def _parse_scoring_output(self, result: dict) -> dict:
        """
        채점 에이전트 출력을 파싱합니다.

        Returns: score_and_explain 도구의 반환값
        """
        import json
        import logging

        logger = logging.getLogger("item_gen_agent")

        try:
            raw_output = result.get("output", "")

            # JSON 추출
            if "```json" in raw_output:
                json_start = raw_output.index("```json") + 7
                json_end = raw_output.index("```", json_start)
                json_str = raw_output[json_start:json_end].strip()
            elif "{" in raw_output:
                json_start = raw_output.index("{")
                json_end = raw_output.rindex("}") + 1
                json_str = raw_output[json_start:json_end]
            else:
                logger.error("No JSON found in scoring output")
                return {"is_correct": False, "score": 0, "error": "파싱 실패"}

            parsed = json.loads(json_str)
            logger.info(f"Scoring result: question={parsed.get('question_id')}, score={parsed.get('score')}")
            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in scoring: {e}")
            return {"is_correct": False, "score": 0, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in _parse_scoring_output: {e}")
            return {"is_correct": False, "score": 0, "error": str(e)}
```

---

## 테스트 전략

### 비결정적 LLM 에이전트 테스트 문제

LLM 기반 에이전트는 매 실행마다 다른 응답을 생성하므로, 일반적인 단위 테스트로는 안정적인 검증이 불가능합니다. 따라서 **Mocking 기반 로직 검증** + **Evaluation 기반 품질 검증** 방식을 함께 사용합니다.

### 1. Mocking 기반 단위 테스트

**목적**: 에이전트의 **로직** (Tool 선택, 데이터 흐름, 에러 처리)이 예상대로 동작하는지 검증

**테스트 대상**:

- Tool 호출 순서 및 조건
- 파라미터 전달 정합성
- 예외 처리 및 재시도 로직
- 파싱 및 데이터 변환 로직

**예시 코드**:

```python
def test_generate_questions_tool_sequence():
    """Tool 호출 순서 검증"""
    mock_user_profile = {"interests": ["LLM", "RAG"], "self_level": "intermediate"}
    mock_templates = [{"stem": "Template 1", "correct_rate": 0.8}]
    mock_keywords = {"keywords": ["prompt", "context"]}

    with patch("agent.get_user_profile", return_value=mock_user_profile) as mock_tool1:
        with patch("agent.search_question_templates", return_value=mock_templates) as mock_tool2:
            with patch("agent.get_difficulty_keywords", return_value=mock_keywords) as mock_tool3:
                agent = ItemGenAgent(...)
                agent.generate_questions("user123", 1)

                # 검증: Tool 호출 순서
                assert mock_tool1.called
                assert mock_tool2.called
                assert mock_tool3.called
                assert mock_tool1.call_count == 1

def test_validate_and_revise_loop():
    """검증 실패 시 재생성 루프 검증"""
    mock_validate_fail_then_pass = [
        {"is_valid": False, "score": 0.65},  # 첫 시도: 실패
        {"is_valid": True, "score": 0.88}    # 재시도: 통과
    ]

    with patch("agent.validate_question_quality", side_effect=mock_validate_fail_then_pass):
        # 재생성이 자동으로 일어나는지 검증
        ...
```

### 2. Evaluation 기반 품질 검증

**목적**: 생성된 문항이 **요구 사항**을 만족하는지 평가

**테스트 방식**: "Golden Dataset" (금표준 입력) + 평가 기준

**Golden Dataset 예시**:

```python
GOLDEN_TEST_CASES = [
    {
        "user_id": "user_beginner",
        "profile": {
            "self_level": "beginner",
            "interests": ["LLM"],
            "years_experience": 1
        },
        "expected": {
            "min_questions": 3,
            "avg_difficulty_range": (2, 4),
            "keyword_coverage": ["prompt", "token"]  # 포함되어야 할 키워드
        }
    },
    {
        "user_id": "user_advanced",
        "profile": {
            "self_level": "advanced",
            "interests": ["Agent Architecture", "Fine-tuning"],
            "years_experience": 5
        },
        "expected": {
            "min_questions": 3,
            "avg_difficulty_range": (6, 8),
            "keyword_coverage": ["decision tree", "dynamic routing"]
        }
    }
]
```

**평가 기준**:

| 평가 항목 | 기준 | 통과율 목표 |
|---------|------|-----------|
| **난이도 정확성** | 생성된 문항의 평균 난이도가 기대값 ±1 범위 내 | >= 90% |
| **키워드 포함도** | 생성된 문항에 기대 키워드 3개 중 2개 이상 포함 | >= 80% |
| **유형 다양성** | 객관식:OX:주관식 = 40:20:40 ±10% | >= 85% |
| **형식 준수** | 모든 문항이 스키마 검증 통과 | 100% |
| **중복 없음** | 같은 라운드 내 유사도 > 90%인 문항 없음 | 100% |

**테스트 구현**:

```python
def test_agent_with_golden_dataset():
    """Golden dataset로 에이전트 평가"""
    for test_case in GOLDEN_TEST_CASES:
        questions = agent.generate_questions(
            test_case["user_id"],
            round_number=1,
            count=5
        )

        # 평가 1: 난이도
        avg_difficulty = sum(q["difficulty"] for q in questions) / len(questions)
        assert test_case["expected"]["avg_difficulty_range"][0] <= avg_difficulty \
               <= test_case["expected"]["avg_difficulty_range"][1]

        # 평가 2: 키워드 포함도
        all_stems = " ".join(q["stem"] for q in questions)
        keyword_matches = sum(1 for kw in test_case["expected"]["keyword_coverage"]
                             if kw.lower() in all_stems.lower())
        assert keyword_matches >= 2

        # 평가 3: 형식 검증
        for q in questions:
            assert "stem" in q and "type" in q and "correct_answer" in q
```

### 3. 통합 테스트 (End-to-End)

**목적**: 전체 파이프라인이 정상 작동하는지 검증

**테스트 시나리오**:

```python
def test_end_to_end_question_generation():
    """전체 파이프라인 통합 테스트"""
    # 1. 에이전트 초기화
    agent = ItemGenAgent(
        llm_endpoint="http://localhost:8888",
        mcp_server=mcp_server
    )

    # 2. 실제 generate_questions 호출 (모의 LLM 사용 가능)
    questions = agent.generate_questions(
        user_id="test_user_001",
        round_number=1,
        count=5
    )

    # 3. 검증
    assert len(questions) >= 3, "최소 3개 문항 생성 필요"
    assert all("question_id" in q for q in questions), "모든 문항에 ID 필요"
    assert all(q["difficulty"] in range(1, 11) for q in questions), "난이도 범위 검증"

def test_end_to_end_scoring():
    """채점 파이프라인 통합 테스트"""

    # 테스트 1: 객관식 정답
    print("=== Test 1: Multiple Choice (Correct) ===")
    result = agent.score_and_explain(
        session_id="sess_001",
        user_id="user123",
        question_id="q123",
        question_type="multiple_choice",
        user_answer="A",
        correct_answer="A"  # 객관식이므로 correct_answer 필수
    )
    assert result["is_correct"] == True
    assert result["score"] == 100
    assert result["keyword_matches"] is None  # 객관식이므로 null
    assert result["feedback"] is None  # 정답이므로 null
    assert "explanation" in result

    # 테스트 2: 주관식 정답
    print("=== Test 2: Short Answer (Correct) ===")
    result = agent.score_and_explain(
        session_id="sess_001",
        user_id="user123",
        question_id="q456",
        question_type="short_answer",
        user_answer="The answer is comprehensive and accurate",
        correct_keywords=["comprehensive", "accurate", "key_concept"]  # 주관식이므로 correct_keywords 필수
    )
    assert result["is_correct"] == True
    assert result["score"] >= 80
    assert isinstance(result["keyword_matches"], list)  # 주관식이므로 배열
    assert result["feedback"] is None  # 정답이므로 null
    assert "explanation" in result

    # 테스트 3: 주관식 부분 정답 (학습 기회 제공)
    print("=== Test 3: Short Answer (Partial) ===")
    result = agent.score_and_explain(
        session_id="sess_001",
        user_id="user123",
        question_id="q456",
        question_type="short_answer",
        user_answer="The answer is somewhat accurate",
        correct_keywords=["comprehensive", "accurate", "key_concept"]
    )
    assert result["is_correct"] == False  # score 70-79이므로 부분 정답
    assert 70 <= result["score"] < 80
    assert isinstance(result["keyword_matches"], list)  # 주관식이므로 배열
    assert result["feedback"] is not None  # 부분 정답이므로 피드백 제공
    assert "explanation" in result
```

### 4. 지속적 평가 (CI/CD)

**권장사항**:

```yaml
# .github/workflows/agent-test.yml
name: Agent Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Mock Tests
        run: pytest tests/test_agent_mocking.py -v
      - name: Run Golden Dataset Evaluation
        run: python scripts/evaluate_golden_dataset.py --threshold=0.85
      - name: Run Integration Tests
        run: pytest tests/test_agent_integration.py -v
```

---

## Prompt Engineering 가이드

### 1. 문항 생성 프롬프트 패턴

```python
QUESTION_GENERATION_TEMPLATE = """
사용자 프로필 분석:
- 수준: {self_level}
- 경력: {years_experience}년
- 관심분야: {interests}
- 직군: {job_role}

생성 조건:
- 라운드: {round_number}
- 난이도: {difficulty}/10
- 타입: {question_type}
- 최근 점수: {previous_score}

요구사항:
1. 사용자의 경력과 관심분야를 반영한 현실적인 시나리오 사용
2. 난이도에 맞춘 개념 깊이 조정
   - 초급(1~3): 기본 개념 정의, 단순 적용
   - 중급(4~6): 개념 이해, 실무 적용
   - 고급(7~10): 심화 개념, 시스템 설계, 엣지 케이스
3. 객관식: 4~5개 선택지, 명확한 정답
4. 주관식: 30자 이상 100자 이내 답변 기대
5. OX: 자주 헷갈리는 개념 활용

생성 결과 JSON:
{{
    "stem": "문항 내용",
    "type": "multiple_choice|true_false|short_answer",
    "choices": [...],  # 객관식인 경우
    "correct_answer": "정답",
    "difficulty": {difficulty},
    "category": "{interests[0]}",
    "explanation": "왜 이것이 정답인가?"
}}
"""
```

### 2. Few-Shot 프롬프트 (예시 기반)

```python
FEW_SHOT_EXAMPLES = """
예시 1 - 객관식:
사용자: LLM 관심, 3년 경력, 초급
Q: LLM과 traditional NLP 모델의 주요 차이점은?
A) Parameter 수와 학습 데이터 규모
B) 사용하는 프로그래밍 언어
C) 구동 환경 (GPU vs CPU)
정답: A) - transformer 기반 대규모 매개변수

예시 2 - 주관식:
사용자: RAG 관심, 5년 경력, 중급
Q: Retrieval-Augmented Generation에서 "Augmentation"은 무엇인가?
정답: 외부 지식베이스에서 검색한 관련 정보를 LLM의 프롬프트에 추가하여 응답 정확도를 높이는 것
"""
```

---

## 에러 처리 & 복원력

### 자동 복구 전략 (Self-Correction Loop)

```python
# 에러 처리 흐름:
# 1. 초기 LLM 응답 시도
# 2. JSON 파싱 실패 시 → 에러 피드백을 프롬프트에 추가하여 LLM에 재요청
# 3. 재시도 최대 3회
# 4. 3회 초과 시 → 부분 성공 또는 실패 처리
```

### 에러별 처리 방식

| 시나리오 | 처리 방식 |
|---------|---------|
| **Tool 호출 실패** | 최대 3회 재시도. 최종 실패 시 캐시된 템플릿/키워드 반환 (fallback) |
| **LLM 응답 형식 오류** | ⭐ **자동 교정 루프**: 파싱 에러 메시지를 새 프롬프트에 포함하여 LLM이 자체 수정하도록 유도. 최대 3회 재시도 |
| **문항 품질 검증 실패** | 검증 점수 < 0.7일 경우, validate_question_quality의 feedback을 LLM에 제공하여 프롬프트 개선 후 재생성 (최대 2회) |
| **DB 저장 실패** | 로그 기록 후, 메모리 큐에 임시 저장. 다음 배치 처리 시 재시도 |
| **LLM 타임아웃 (>30s)** | 중단 후, AgentExecutor의 intermediate_steps에서 부분 생성 문항 추출. 유효한 것만 저장 |

### 자동 교정 루프 상세 구현

**예시: JSON 파싱 오류 복구**

```python
def generate_questions(self, user_id, round_number, count=5, previous_score=None):
    max_retries = 3
    attempt = 0

    while attempt < max_retries:
        result = executor.invoke({"input": input_prompt})
        questions = self._parse_agent_output(result)

        if questions:  # 파싱 성공
            return questions

        # 파싱 실패 → 에러 피드백을 새 프롬프트에 추가
        attempt += 1
        if attempt < max_retries:
            last_output = result.get("output", "")
            correction_prompt = f"""
            이전 응답에서 JSON 형식 오류가 발생했습니다:
            {last_output[:200]}...

            다시 시도하세요. 반드시 다음 JSON 형식으로 반환하세요:
            {{
                "status": "success|partial|failed",
                "generated_count": N,
                "questions": [...]
            }}
            """
            input_prompt = correction_prompt
        else:
            logger.error(f"Max retries exceeded for user {user_id}")
            return []

    return []
```

**예시: 문항 품질 검증 오류 복구**

```python
# validate_question_quality에서 점수 < 0.7인 경우
if validation_score < 0.7:
    feedback = f"문항 품질 점수: {validation_score:.2f}. 피드백: {feedback_text}"

    # 에이전트에 피드백 제공하여 재생성 유도
    revision_prompt = f"""
    생성한 문항의 품질 검증 결과:
    {feedback}

    위 피드백을 반영하여 문항을 개선해주세요.
    """
    # 새로운 문항 생성 요청
```

---

## 개발 가이드

### 프로젝트 구조

```
./src/agent/
├── __init__.py
├── agent.py              # ItemGenAgent 클래스
├── mcp_server.py         # FastMCP 서버 설정
├── tools/
│   ├── __init__.py
│   ├── user_tools.py     # Tool 1: User Profile
│   ├── template_tools.py # Tool 2: Templates
│   ├── keyword_tools.py  # Tool 3: Keywords
│   ├── validation_tools.py # Tool 4: Validation
│   └── storage_tools.py  # Tool 5: Storage
├── prompts/
│   ├── system.py
│   ├── generation.py
│   └── few_shot.py
├── config.py
├── logger.py
└── tests/
    ├── test_agent.py
    ├── test_tools.py
    └── test_integration.py
```

### 핵심 개발 단계

1. **FastMCP 서버 설정** (`mcp_server.py`)
   - Backend API와 통신하는 도구 등록
   - 에러 처리 및 재시도 로직

2. **Tool 구현** (`tools/` 폴더)
   - 각 도구는 독립적인 모듈로 구현
   - 도구별 단위 테스트 작성

3. **Agent 초기화** (`agent.py`)
   - LangChain Agent 생성
   - 도구 바인딩
   - 프롬프트 로딩

4. **테스트 주도 개발 (TDD)**
   - 각 도구별 단위 테스트
   - 에이전트 통합 테스트
   - 엣지 케이스 시뮬레이션

---

## 배포 & 운영

### 환경 변수 (.env)

```bash
# LLM 설정
LOCAL_LLM_ENDPOINT=http://localhost:8888
LOCAL_LLM_MODEL=qwen-14b-chat
LOCAL_LLM_TIMEOUT=30

# FastMCP 설정
MCP_SERVER_PORT=8889
MCP_DEBUG=false

# Agent 설정
AGENT_TEMPERATURE=0.7
AGENT_MAX_ITERATIONS=10
AGENT_VERBOSE=true

# 캐시 설정
CACHE_ENABLED=true
CACHE_TTL=3600
```

### 모니터링 & 로깅

```python
import logging

logger = logging.getLogger("item_gen_agent")
logger.setLevel(logging.INFO)

# 로깅 항목:
# - 도구 호출 시간
# - LLM 응답 토큰 수
# - 문항 생성 성공/실패율
# - 품질 검증 점수
```

---

## 참고 자료 & 학습 가이드

### 1. MCP (Model Context Protocol) 학습

**문제**: MCP 개발 경험이 1번만 있는 상황

**해결책**:

- [Anthropic MCP 공식 문서](https://modelcontextprotocol.io)
  - SSE 기반 통신 이해
  - Tool 등록 패턴
  - Error Handling
- FastMCP 라이브러리 예제:

  ```python
  from fastmcp import FastMCP

  app = FastMCP()

  @app.tool()
  def my_tool(param: str) -> dict:
      return {"result": "output"}
  ```

### 2. LangChain Agent 최신 기술

**문제**: LangChain Agent 최신 개발 경험 부족

**해결책**:

- LangChain v0.2+ 문서 (ReAct 패턴, Tool Calling)
- 권장 튜토리얼:
  1. [LangChain Agents](https://python.langchain.com/docs/modules/agents/)
  2. [Tool Calling Agent](https://python.langchain.com/docs/modules/agents/concepts)
  3. [AgentExecutor Deep Dive](https://python.langchain.com/docs/modules/agents/agent_types/tool_calling_agent)

**핵심 개념**:

- `create_tool_calling_agent`: LLM의 native tool calling 활용
- `AgentExecutor`: 에이전트 실행 엔진
- `Tool.from_function`: 함수를 도구로 변환

### 3. 효율적인 AI Agent 개발

**문제**: 효율적인 AI Agent 개발 경험 부족

**권장 사항**:

1. **작은 것부터 시작**
   - 단일 도구로 시작 → 점진적 복잡도 증가
   - 모의 LLM 사용 (프롬프트 테스트 시)

2. **Prompt Engineering 최적화**
   - Few-shot 예시 사용
   - Chain-of-Thought (CoT) 프롬프팅
   - 역할 정의 (Role Playing)

3. **테스트 주도 개발**

   ```python
   # 1. 도구별 단위 테스트
   def test_get_user_profile():
       result = get_user_profile("user123")
       assert "interests" in result

   # 2. 에이전트 통합 테스트
   def test_agent_generates_questions():
       agent = ItemGenAgent(...)
       questions = agent.generate_questions("user123", 1, count=5)
       assert len(questions) == 5

   # 3. 프롬프트 검증
   def test_prompt_format():
       prompt = agent._get_system_prompt()
       assert "동적 생성" in prompt
   ```

4. **디버깅 전략**
   - `AgentExecutor` verbose=True로 실행 흐름 추적
   - 각 도구의 입출력 로깅
   - LLM 응답 내용 분석

---

## 성능 목표

| 지표 | 목표 |
|------|------|
| **문항 생성 시간** | ≤ 3초/세트 (5문항) |
| **도구 호출 성공률** | ≥ 99% |
| **문항 품질 검증 통과율** | ≥ 95% |
| **LLM 응답 정확도** | 일관된 JSON 형식 |
| **캐시 hit rate** | ≥ 80% (템플릿 재사용) |

---

**주의사항**:

- Local LLM 성능에 따라 조정 필요
- 초기 운영 중 프롬프트 최적화 지속
- 도구 응답 시간 모니터링 필수

---

**Version History**:

- v1.0 (2025-11-06): Initial Feature Requirement with Frontend/Backend split
