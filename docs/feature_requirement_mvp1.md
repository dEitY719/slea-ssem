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
| **REQ-F-A1-2** | SSO 콜백 페이지를 구현하여 토큰을 안전하게 저장하고 대시보드로 리다이렉트해야 한다. | **M** |
| **REQ-F-A1-3** | **로그인 실패 시 명확한 에러 메시지를 표시하고, "계정 정보 확인" 링크 및 "관리자 문의" 헬프 링크를 함께 제공해야 한다.** | **M** |

**수용 기준**:

- "로그인 버튼 클릭 후 Samsung AD 로그인 페이지로 리다이렉트된다."
- "로그인 성공 후 3초 내 대시보드로 이동한다."
- "**로그인 실패 시, 에러 메시지와 함께 '계정 정보 확인', '관리자 문의' 두 링크가 표시된다.**"

---

## REQ-F-A2: 닉네임 등록 화면

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-F-A2-1** | 닉네임 입력 필드와 "중복 확인" 버튼을 제공해야 한다. | **M** |
| **REQ-F-A2-2** | 유효하지 않은 닉네임(너무 짧음, 특수문자 등) 입력 시 실시간으로 에러 메시지를 표시해야 한다. | **M** |
| **REQ-F-A2-3** | 닉네임 중복 시 대안 3개를 시각적으로 제안해야 한다. | **S** |
| **REQ-F-A2-4** | 금칙어를 포함한 닉네임 거부 시, 거부 사유를 명확하게 안내해야 한다. | **S** |
| **REQ-F-A2-5** | 중복이 없을 때 "사용 가능" 상태를 표시하고, "가입 완료" 버튼을 활성화해야 한다. | **M** |

**수용 기준**:

- "닉네임 입력 후 1초 내 "중복 확인" 결과가 표시된다."
- "중복 시 3개의 대안이 제안된다."
- "금칙어 포함 시 거부 사유가 표시된다."

---

## REQ-F-A2-Edit: 프로필 수정 화면 (닉네임/자기평가 변경)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-F-A2-Edit-1** | 대시보드 또는 프로필 메뉴에서 "프로필 수정" 옵션을 제공해야 한다. | **M** |
| **REQ-F-A2-Edit-2** | 기존 닉네임을 표시하고, 사용자가 새로운 닉네임으로 변경할 수 있어야 한다. | **M** |
| **REQ-F-A2-Edit-3** | 닉네임 중복 확인 시, 기존 닉네임(현재 사용 중)은 제외하고 검증해야 한다. | **M** |
| **REQ-F-A2-Edit-4** | 닉네임 변경 후 "저장" 버튼 클릭 시, DB에 업데이트되고 "저장되었습니다" 메시지를 표시해야 한다. | **M** |
| **REQ-F-A2-Edit-5** | 자기평가 정보(수준, 경력, 직군, 업무, 관심분야)도 수정할 수 있어야 한다. | **M** |
| **REQ-F-A2-Edit-6** | 수정된 자기평가 정보는 다음 테스트 응시 시 자동으로 반영되어야 한다. | **M** |

**수용 기준**:

- "프로필 수정 페이지에서 현재 닉네임이 표시된다."
- "새 닉네임 입력 후 중복 확인 시, 기존 닉네임과의 충돌을 무시하고 검증한다."
- "저장 버튼 클릭 후 1초 내 확인 메시지가 표시된다."
- "페이지 새로고침 시 변경된 닉네임이 반영된다."

---

## REQ-F-A3: 온보딩 모달

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-F-A3-1** | 가입 완료 후 웰컴 모달을 표시하여 요약 가이드와 "레벨 테스트 시작" CTA를 제공해야 한다. | **S** |
| **REQ-F-A3-2** | (선택) 개인정보·로그 수집에 대한 동의 배너를 표시할 수 있다. | **C** |

**수용 기준**:

- "가입 완료 후 즉시 웰컴 모달이 나타난다."
- ""레벨 테스트 시작" 버튼 클릭 시 자기평가 폼으로 진행된다."

---

## REQ-F-B1: 자기평가 입력 화면

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-F-B1-1** | 레벨 테스트 시작 전, 사용자의 자기평가 폼(Form)을 제공해야 한다. | **M** |
| **REQ-F-B1-2** | 입력 항목을 명확하게 레이아웃하고 다음을 포함해야 한다: <br> - 본인이 생각하는 수준 (초급/중급/상급) 라디오 버튼 <br> - 경력(연차): 숫자 또는 범위 선택 드롭다운 <br> - 직군: 백엔드, 프론트엔드, DevOps, 데이터, 마케팅 등 드롭다운 <br> - 담당 업무: 텍스트 입력 필드 <br> - 관심분야: 체크박스 다중 선택 (LLM, RAG, Agent Architecture, Prompt Engineering, Deep Learning 등) | **M** |
| **REQ-F-B1-3** | 필수 필드 누락 시, 누락된 필드를 명확히 표시하고 오류 메시지를 보여야 한다. | **M** |

**수용 기준**:

- "모든 필수 필드를 입력한 후 '다음' 버튼이 활성화된다."
- "유효하지 않은 값 입력 시 필드 옆에 에러 메시지가 표시된다."
- "제출 후 로딩 상태를 표시한다."

---

## REQ-F-B2: 문항 풀이 화면

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

## REQ-B-A2: 닉네임 등록 (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-A2-1** | Profile-Service가 닉네임 중복 여부를 1초 내에 확인하고 응답해야 한다. | **M** |
| **REQ-B-A2-2** | 닉네임 유효성 검사(길이, 특수문자, 금칙어 필터)를 구현해야 한다. | **M** |
| **REQ-B-A2-3** | 중복 시 대안 3개를 자동으로 생성해서 제안해야 한다. (예: 사용자명_1, 사용자명_2, 사용자명_3) | **S** |
| **REQ-B-A2-4** | 금칙어 필터 목록을 유지하고, 위반 시 명확한 거부 사유를 반환해야 한다. | **S** |
| **REQ-B-A2-5** | 닉네임 검증 후 users 테이블에 사용자 레코드를 저장해야 한다. | **M** |

**수용 기준**:

- "닉네임 중복 확인 요청 후 1초 내 결과가 반환된다."
- "가입 완료 후 DB 조회 시 사용자 레코드가 정확히 생성되어 있다."

---

## REQ-B-A2-Edit: 프로필 수정 (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-A2-Edit-1** | Profile-Service가 사용자의 닉네임 변경 요청을 받아, 기존 닉네임은 제외하고 중복 여부를 확인해야 한다. | **M** |
| **REQ-B-A2-Edit-2** | 닉네임 변경 시 users 테이블의 nickname 필드를 업데이트하고, updated_at 타임스탬프를 갱신해야 한다. | **M** |
| **REQ-B-A2-Edit-3** | 자기평가 정보(수준, 경력, 직군, 업무, 관심분야) 변경 요청을 받아, user_profile_surveys 테이블에 새 레코드를 생성하거나 기존 레코드를 업데이트해야 한다. | **M** |
| **REQ-B-A2-Edit-4** | 프로필 수정 API는 1초 내에 응답해야 한다. | **M** |

**수용 기준**:

- "닉네임 변경 요청 후 1초 내 성공/실패 응답이 반환된다."
- "DB 조회 시 updated_at이 최신 타임스탬프로 갱신되어 있다."

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

## REQ-B-B2: 적응형 문항 생성 (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-B2-1** | Item-Gen-Agent가 사용자의 자기평가 정보(수준, 관심분야)를 기반으로 1차 문항 세트(5문항)를 동적으로 LLM으로 생성해야 한다. | **M** |
| **REQ-B-B2-2** | 생성된 각 문항은 다음 정보를 포함해야 한다: <br> - 유형: multiple_choice, true_false, short_answer <br> - stem: 문항 내용 <br> - choices: 객관식 선택지 (객관식인 경우) <br> - answer_schema: 정답 기준 정보 <br> - difficulty: 난이도 (1~10) <br> - category: 사용자의 관심분야 반영 | **M** |
| **REQ-B-B2-3** | LLM 프롬프트에 마케팅, 반도체, 센서, RTL 등 특정 카테고리에 대한 "재미" 요소를 반영해야 한다. | **S** |
| **REQ-B-B2-4** | 1차 풀이 결과(점수, 오답 카테고리)를 분석하여, Item-Gen-Agent가 난이도를 조정한 2차 문항 세트를 생성해야 한다. | **M** |
| **REQ-B-B2-5** | 적응형 난이도 조정 로직을 구현해야 한다: <br> - 점수 0~40: 난이도 유지 또는 감소 <br> - 점수 40~70: 난이도 유지 또는 약간 증가 <br> - 점수 70+: 난이도 상향 또는 초상급 활성화 | **M** |
| **REQ-B-B2-6** | 2차 문항 생성 시, 1차 오답 분야를 우선적으로 강화하여 생성해야 한다. | **M** |
| **REQ-B-B2-7** | (선택) 3차 이상 진행 가능하나, 최소 2회 및 최대 3회로 제한하는 로직을 구현할 수 있다. | **S** |

**수용 기준**:

- "자기평가 제출 후 3초 내 1차 문항이 API로 반환된다."
- "1차 점수 60점 시, 2차는 중급 난이도로 생성된다."
- "1차 오답 카테고리가 2차에서 50% 이상 포함된다."

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

## REQ-B-B3: 채점 및 해설 생성 (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-B3-1** | Scoring-Agent가 각 문항 제출 시 1초 내에 정오답 판정 및 점수를 계산해야 한다. | **M** |
| **REQ-B-B3-2** | 채점 로직을 구현해야 한다: <br> - 객관식/OX: 정답 일치 판정 (정답 1점, 오답 0점) <br> - 주관식: LLM 기반 키워드 매칭으로 부분점수 지원 (예: 0~100점) | **M** |
| **REQ-B-B3-3** | **20분 초과 시 응답 시간에 따른 페널티를 적용해야 한다.** (예: 20분을 초과한 경우, 초과분만큼 감점 처리) | **M** |
| **REQ-B-B3-4** | Explain-Agent가 각 문항에 대해 정답/오답 해설(500자 이상) 및 참고 링크(3개 이상)를 생성해야 한다. | **M** |

**수용 기준**:

- "각 문항 제출 후 1초 내 '정답입니다' 또는 '오답입니다' 피드백이 반환된다."
- "주관식 채점 후 부분점수(예: 70점)가 반환된다."
- "해설에 참고 링크가 포함되어 있다."

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

## REQ-B-B6: 문항 품질 (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
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

## REQ-B-B7: 학습 일정 예고 프리뷰 (Backend)

| REQ ID | 요구사항 | 우선순위 |
|--------|---------|---------|
| **REQ-B-B7-1** | Plan-Preview-Agent가 사용자의 레벨 테스트 결과(점수, 등급, 약점 분야)를 분석하여, **2~4주의 맞춤 학습 계획 초안**을 자동으로 생성해야 한다. | **M** |
| **REQ-B-B7-2** | 학습 계획은 다음 정보를 포함해야 한다: <br> - 주당 추천 학습 시간 <br> - 카테고리별 추천 자료 (사내/사외, 동영상/블로그/문서) <br> - 각 자료의 예상 소요 시간 <br> - 학습 순서 및 우선순위 | **M** |
| **REQ-B-B7-3** | 사용자가 "관심 있음" 버튼을 클릭할 시, 해당 사용자를 **대기리스트 테이블(waitlist)** 에 등록해야 한다. | **M** |
| **REQ-B-B7-4** | Nudge-Service가 대기리스트에 등록된 사용자에게 MVP 2.0 오픈 시 **이메일 알림**을 자동으로 발송해야 한다. | **M** |
| **REQ-B-B7-5** | 사용자의 대기리스트 등록 상태는 profile 조회 API에서 함께 반환되어야 한다. | **S** |

**수용 기준**:

- "레벨 테스트 완료 후 3초 내 학습 계획 초안이 생성된다."
- "대기리스트 등록 요청 후 1초 내 확인 응답이 반환된다."
- "등록된 사용자 정보가 DB에 저장된다."

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
- ✅ REQ-F-A2-1~5, REQ-B-A2-1~5: 닉네임 등록 (F/B)
- ✅ **REQ-F-A2-Edit-1~6, REQ-B-A2-Edit-1~4: 프로필 수정 (닉네임/자기평가) (F/B)**
- ✅ REQ-F-B1-1~3, REQ-B-B1-1~2: 자기평가 입력 (F/B)
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

- ✅ REQ-F-A3-1: 온보딩 모달 (F)
- ✅ REQ-F-A3-2: 개인정보 동의 (F)
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

### R1: 기본 가입 및 온보딩

- Samsung AD 로그인/SSO (REQ-B-A1-1~4, REQ-F-A1-1~3)
- 닉네임 등록 (중복 체크) (REQ-F-A2-1~5, REQ-B-A2-1~5)
- **프로필 수정 기능 (REQ-F-A2-Edit-1~6, REQ-B-A2-Edit-1~4)**
- 온보딩 모달 (REQ-F-A3-1)

**완료 기준**: 사용자가 가입을 완료하고 프로필을 수정할 수 있으며 대시보드에 접근 가능

---

### R2: 자기평가 → 1차 테스트 & 저장/재개

- 자기평가 폼 입력 (REQ-F-B1-1~3, REQ-B-B1-1~2)
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

닉네임 등록:
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

온보딩:
- [ ] REQ-F-A3-1: 웰컴 모달 구현
- [ ] REQ-F-A3-2: 개인정보 동의 배너

자기평가 폼:
- [ ] REQ-F-B1-1: 폼 레이아웃 구현
- [ ] REQ-F-B1-2: 입력 필드 배치
- [ ] REQ-F-B1-3: 필드 검증 표시

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

**Version History**:

- v1.0 (2025-11-06): Initial Feature Requirement with Frontend/Backend split
