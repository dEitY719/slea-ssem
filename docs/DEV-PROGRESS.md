# Team Development Progress

Overall progress tracking for MVP 1.0 development across all developers.

---

## 📊 Development Status (MVP 1.0)

### Frontend (lavine)

| REQ ID | Feature | Phase | Status | Notes |
|--------|---------|-------|--------|-------|
| REQ-F-A1 | 로그인 화면 (Samsung AD) | 0 | ⏳ Backlog | 3개 sub-tasks |
| REQ-F-A1-1 | "Samsung AD로 로그인" 버튼 표시 | 4 | ✅ Done | 5 tests (100%), Commit: 744fc3e, Progress: docs/progress/REQ-F-A1-1.md |
| REQ-F-A1-2 | SSO 콜백 페이지 구현 | 4 | ✅ Done | 15 tests (100%), Commit: 3eeff9d, Progress: docs/progress/REQ-F-A1-2.md |
| REQ-F-A1-3 | 로그인 실패 시 에러 메시지 및 헬프 링크 | 4 | ✅ Done | 2 tests (100%), Commit: 2bd263b, Progress: docs/progress/REQ-F-A1-3.md |
| REQ-F-A2 | 회원가입 화면 (닉네임 등록) | 4 | ✅ Done | 7개 sub-tasks |
| REQ-F-A2-1 | 홈화면 "시작하기" 클릭 시 닉네임 체크 | 4 | ✅ Done | 7 tests (100%), Commit: fa43b6d, Progress: docs/progress/REQ-F-A2-1.md |
| REQ-F-A2-2 | 닉네임 입력 필드와 "중복 확인" 버튼 제공 | 4 | ✅ Done | Commit: 2190e73, Progress: docs/progress/REQ-F-A2-2.md |
| REQ-F-A2-3 | 실시간 유효성 검사 및 에러 메시지 표시 | 4 | ✅ Done | Commit: 2190e73, Progress: docs/progress/REQ-F-A2-3.md |
| REQ-F-A2-4 | 닉네임 중복 시 대안 3개 시각적 제안 | 4 | ✅ Done | 3 tests (100%), Commit: 8a43119, Progress: docs/progress/REQ-F-A2-4.md |
| REQ-F-A2-6 | "사용 가능" 상태 표시 및 "다음" 버튼 활성화 | 4 | ✅ Done | Commit: 21243fd, Progress: docs/progress/REQ-F-A2-6.md |
| REQ-F-A2-7 | "다음" 버튼 클릭 시 nickname 업데이트 및 리다이렉트 | 4 | ✅ Done | Commit: c3e06ea, Progress: docs/progress/REQ-F-A2-7.md |
| REQ-F-A2-2 | 자기평가 입력 화면 (프로필 설정) | 0 | ⏳ Backlog | 5개 sub-tasks (REQ-F-B1 통합) |
| REQ-F-A2-2-1 | 닉네임 설정 완료 후 자기평가 입력 페이지로 이동 | 4 | ✅ Done | 7 tests (100%), Commit: 8034886, Progress: docs/progress/REQ-F-A2-2-1.md |
| REQ-F-A2-2-2 | 자기평가 정보(수준) 입력 | 4 | ✅ Done | 10 tests (100%), Commit: bd3c7ec, Progress: docs/progress/REQ-F-A2-2-2.md |
| REQ-F-A2-2-3 | 필수 필드 입력 시 "완료" 버튼 활성화 | 4 | ✅ Done | Commit: bd3c7ec, Progress: docs/progress/REQ-F-A2-2-3.md |
| REQ-F-A2-2-4 | "완료" 클릭 시 프로필 저장 및 리뷰 페이지 이동 | 4 | ✅ Done | Commit: d401eed, Progress: docs/progress/REQ-F-A2-2-4.md |
| REQ-F-A2-Signup | 통합 회원가입 화면 (헤더 "회원가입" 버튼) | 0 | ⏳ Backlog | 7개 sub-tasks (닉네임 + 자기평가 한 페이지) |
| REQ-F-A2-Signup-1 | 홈화면 헤더 오른쪽 상단에 "회원가입" 버튼 표시 | 4 | ✅ Done | 6 tests (100%), Commit: b757745, Progress: docs/progress/REQ-F-A2-Signup-1.md |
| REQ-F-A2-Signup-2 | "회원가입" 버튼 클릭 시 /signup 페이지로 이동 | 4 | ✅ Done | 1 test (100%), Commit: b757745, Progress: docs/progress/REQ-F-A2-Signup-2.md |
| REQ-F-A2-Signup-3 | 통합 회원가입 페이지에 닉네임 입력 섹션 표시 | 4 | ✅ Done | 11 tests (100%), Commit: 273c30a, Progress: docs/progress/REQ-F-A2-Signup-3.md |
| REQ-F-A2-Profile-Access | 헤더 닉네임 표시 및 드롭다운 메뉴 | 1 | 🚧 In Progress | 8개 sub-tasks (닉네임 표시 → 드롭다운 → 프로필 수정) |
| REQ-F-A2-Profile-Access-1 | 헤더에 닉네임 표시 (nickname != null) | 4 | ✅ Done | 8 tests (100%), Commit: 16bbf7f, Progress: docs/progress/REQ-F-A2-Profile-Access-1.md |
| REQ-F-A2-Edit | 프로필 수정 화면 | 0 | ⏳ Backlog | 6개 sub-tasks |
| REQ-F-A2-Edit-1 | 프로필 리뷰 화면에 "프로필 수정" 버튼 제공 | 4 | ✅ Done | Commit: d401eed, Progress: docs/progress/REQ-F-A2-Edit-1.md |
| REQ-F-A3 | 개인정보 수집 및 이용 동의 | 0 | ⏳ Backlog | 5개 sub-tasks |
| REQ-F-B1 | ⚠️ Deprecated - REQ-F-A2-2 참조 | N/A | ⚠️ Merged | REQ-F-A2-2로 통합됨 |
| REQ-F-B2 | 문항 풀이 화면 | 0 | ⏳ Backlog | 7개 sub-tasks |
| REQ-F-B2-1 | 문항 순차 표시 및 답변 제출 UI | 4 | ✅ Done | 9 tests (100%), Commit: f852dfe, Progress: docs/progress/REQ-F-B2-1.md |
| REQ-F-B2-2 | 남은 시간(타이머) 표시 (20분 제한, 색상 변화) | 4 | ✅ Done | 5 tests (100%), Commit: dd7cbe3, Progress: docs/progress/REQ-F-B2-2.md |
| REQ-F-B2-6 | 자동 저장 및 "저장됨" 표시 (실시간 저장) | 4 | ✅ Done | 5 tests (100%), Commit: 068b2ff, Progress: docs/progress/REQ-F-B2-6.md |
| REQ-F-B3 | 해설 화면 | 0 | ⏳ Backlog | 2개 sub-tasks |
| REQ-F-B4 | 최종 결과 페이지 | 0 | ⏳ Backlog | 6개 sub-tasks |
| REQ-F-B4-1 | 등급/점수/순위/백분위 표시 | 4 | ✅ Done | Tests designed (16 cases), Commit: a22319f, Progress: docs/progress/REQ-F-B4-1.md |
| REQ-F-B4-3 | 전사 상대 순위 및 분포 시각화 (막대 차트) | 4 | ✅ Done | 5 tests (100%), Commit: 6c22a41, Progress: docs/progress/REQ-F-B4-3.md |
| REQ-F-B4-4 | 모집단 < 100일 경우 분포 신뢰도 낮음 경고 표시 | 4 | ✅ Done | 4 tests (100%), Commit: b6c17b0, Progress: docs/progress/REQ-F-B4-4.md |
| REQ-F-B5 | 재응시 및 비교 화면 | 0 | ⏳ Backlog | 3개 sub-tasks |
| REQ-F-B5-1 | 이전 응시 정보 비교 섹션 | 4 | ✅ Done | 9 tests (100%), Progress: docs/progress/REQ-F-B5-1.md |
| REQ-F-B5-2 | 레벨 테스트 재응시 버튼 | 4 | ✅ Done | 5 tests (100%), Progress: docs/progress/REQ-F-B5-2.md |
| REQ-F-B5-3 | 재응시 시 이전 정보 자동 입력 | 4 | ✅ Done | 9 tests (100%), Commit: 4f404ac, Progress: docs/progress/REQ-F-B5-3.md |
| REQ-F-B6 | 재미 모드 (카테고리 선택형 퀴즈) | 0 | 📦 MVP 2.0 | Deferred to MVP 2.0 |

### Backend (bwyoon)

| REQ ID | Feature | Phase | Status | Notes |
|--------|---------|-------|--------|-------|
| REQ-B-A1 | Samsung AD 인증 & 세션 관리 | 4 | ✅ Done | Commit: f5412e9 |
| REQ-B-A3 | 개인정보 동의 관리 | 0 | ⏳ Backlog | 2개 sub-tasks |
| REQ-B-A2 | 닉네임 등록 | 4 | ✅ Done | 23 tests (100%), Commit: 5e6c373 |
| REQ-B-A2-Signup | 통합 회원가입 API (닉네임 + 프로필 한 번에 저장) | 0 | ⏳ Backlog | 5개 sub-tasks (트랜잭션 처리) |
| REQ-B-A2-Edit | 프로필 수정 | 4 | ✅ Done | 28 tests (100%), Commit: fdb3896 |
| REQ-B-B1 | 자기평가 데이터 수집 & 저장 | 4 | ✅ Done | 14 tests (100%), Commit: (pending) |
| REQ-B-B2-Gen | 1차 문항 생성 | 4 | ✅ Done | 12 tests (100%), Mock data, Commit: (pending) |
| REQ-B-B2-Adapt | 2차 적응형 난이도 조정 | 4 | ✅ Done | 41 tests (100%), Commit: 9608f57 |
| REQ-B-B2-Plus | 실시간 저장 & 재개 | 4 | ✅ Done | 33 tests (100%), Commit: c95dfcb |
| REQ-B-B3-Score | 채점 (정오답 판정) | 4 | ✅ Done | 36 tests (100%), Commit: (pending) |
| REQ-B-B3-Explain | 해설 생성 | 4 | ✅ Done | 15 tests (100%), Commit: f653be5 |
| REQ-B-B4 | 최종 등급 & 순위 산출 | 4 | ✅ Done | 21 tests (100%), Commit: 1de9a2d |
| REQ-B-B4-Plus | 등급 기반 배지 부여 | 4 | ✅ Done | 6 badge tests included, Commit: 1de9a2d, Progress: docs/progress/REQ-B-B4-Plus.md |
| REQ-B-B5 | 응시 이력 저장 & 조회 | 4 | ✅ Done | 16 tests (100%), Commit: d400aa8, Progress: docs/progress/REQ-B-B5.md |
| REQ-B-B6-2 | 콘텐츠 필터링 (비속어/편향/저작권) | 4 | ✅ Done | 26 tests (100%), Commit: (pending), Progress: docs/progress/REQ-B-B6-2.md |
| REQ-B-B6-Plus | 재미 모드 (Backend) | 0 | 📦 MVP 2.0 | Deferred to MVP 2.0 |

### Agent (Claude Code)

| REQ ID | Feature | Phase | Status | Notes |
|--------|---------|-------|--------|-------|
| REQ-A-Agent-Sanity-0 | Agent 기본 동작 검증 (LangGraph v2) | 4 | ✅ Done | 5 steps verified, 9 tests (100%), Commit: (pending), Progress: docs/progress/REQ-A-Agent-Sanity-0.md |
| REQ-A-ItemGen | Item-Gen-Agent (통합) | 4 | ✅ Done | 24 tests (100%), Commit: a9b1597, Progress: docs/progress/REQ-A-ItemGen.md |
| REQ-A-Mode1-Tool1 | Get User Profile | 4 | ✅ Done | 13 tests (100%), Commit: 93136e6, Progress: docs/progress/REQ-A-Mode1-Tool1-PHASE3.md |
| REQ-A-Mode1-Tool2 | Search Question Templates | 4 | ✅ Done | 13 tests (100%), Commit: (pending), Progress: docs/progress/REQ-A-Mode1-Tool2.md |
| REQ-A-Mode1-Tool3 | Get Difficulty Keywords | 4 | ✅ Done | 11 tests (100%), Commit: (pending), Progress: docs/progress/REQ-A-Mode1-Tool3.md |
| REQ-A-Mode1-Tool4 | Validate Question Quality | 4 | ✅ Done | 23 tests (100%), Commit: 2e8a480, Progress: docs/progress/REQ-A-Mode1-Tool4.md |
| REQ-A-Mode1-Tool5 | Save Generated Question | 4 | ✅ Done | 15 tests (100%), Commit: 9155831, Progress: docs/progress/REQ-A-Mode1-Tool5.md |
| REQ-A-Mode1-Pipeline | Mode 1 Pipeline Orchestrator | 4 | ✅ Done | 16 tests (100%), Commit: 13e5c63, Progress: docs/progress/REQ-A-Mode1-Pipeline.md |
| REQ-A-Mode2-Tool6 | Score & Generate Explanation | 4 | ✅ Done | 36 tests (100%), Commit: (pending), Progress: docs/progress/REQ-A-Mode2-Tool6.md |
| REQ-A-Mode2-Pipeline | Auto-Scoring Pipeline | 4 | ✅ Done | 34 tests (100%), Commit: (pending), Progress: docs/progress/REQ-A-Mode2-Pipeline.md |
| REQ-A-Mode2-Parallel | Parallel Batch Scoring (Phase 3) | 3 | 💻 Impl | 16 tests (designed), Progress: docs/progress/REQ-A-Mode2-Parallel.md |
| REQ-A-Mode1-Test | Mode 1 통합 테스트 | 4 | ✅ Done | 26 tests (100%), Commit: (pending), Progress: docs/progress/REQ-A-Mode1-Test.md |
| REQ-A-Mode2-Test | Mode 2 통합 테스트 | 4 | ✅ Done | 19 tests (100%), Commit: (pending), Progress: docs/progress/REQ-A-Mode2-Test.md |
| REQ-A-ErrorHandling | 통합 에러 처리 | 4 | ✅ Done | 31 tests (100%), Commit: (pending), Progress: docs/progress/REQ-A-ErrorHandling.md |
| REQ-A-RoundID | Round ID 생성 & 추적 | 4 | ✅ Done | 28 tests (100%), Commit: (pending), Progress: docs/progress/REQ-A-RoundID.md |
| REQ-A-FastMCP | FastMCP 서버 구현 | 4 | ✅ Done | 26 tests (100%), Commit: 006dc68, Progress: docs/progress/REQ-A-FastMCP.md |
| REQ-A-DataContract | Tool 입출력 데이터 계약 | 4 | ✅ Done | 27 tests (100%), Commit: [pending], Progress: docs/progress/REQ-A-DataContract.md |
| REQ-A-LangChain | LangChain Agent 구현 | 4 | ✅ Done | 13 tests (100%), Commit: [pending], Progress: docs/progress/REQ-A-LangChain.md |
| REQ-A-Agent-Backend-1 | QuestionGenerationService Real Agent 통합 + CLI Integration | 4 | ✅ Done | 12+12 tests (100%), Commits: 61c6449 (CLI), f53df96 (docs), Progress: docs/progress/REQ-A-Agent-Backend-1.md |
| REQ-B-B7 | 학습 일정 예고 프리뷰 | 0 | 📦 MVP 2.0 | Deferred to MVP 2.0 |

### CLI (bwyoon)

| REQ ID | Feature | Phase | Status | Notes |
|--------|---------|-------|--------|-------|
| REQ-CLI-AUTH-1 | Login with JWT storage | 4 | ✅ Done | APIClient + token management, Commit: [pending] |
| REQ-CLI-AUTH-2 | Auto token refresh | 0 | ⏳ Backlog | 향후 구현 예정 |
| REQ-CLI-SURVEY-1 | Get survey schema | 4 | ✅ Done | API endpoint 연동 |
| REQ-CLI-SURVEY-2 | Submit survey data | 4 | ✅ Done | 인증 확인, 데이터 제출 |
| REQ-CLI-PROFILE-1 | Check nickname availability | 4 | ✅ Done | 제안 포함 |
| REQ-CLI-PROFILE-2 | Register nickname | 4 | ✅ Done | 인증 필수 |
| REQ-CLI-PROFILE-3 | Edit nickname | 4 | ✅ Done | 기존 닉네임 수정 |
| REQ-CLI-PROFILE-4 | Update survey | 4 | ✅ Done | 프로필 업데이트 |
| REQ-CLI-PROFILE-5 | View user profile | 0 | ⏳ Backlog | 프로필 조회 기능 |
| REQ-CLI-QUESTIONS-1 | Generate Round 1 questions | 4 | ✅ Done | 세션 자동 생성 |
| REQ-CLI-QUESTIONS-2 | Generate adaptive questions | 4 | ✅ Done | Round 2 문항 생성 |
| REQ-CLI-QUESTIONS-3 | Autosave answer | 4 | ✅ Done | 실시간 저장 |
| REQ-CLI-QUESTIONS-4 | Score answer | 4 | ✅ Done | 개별 채점 |
| REQ-CLI-QUESTIONS-5 | Calculate round score | 4 | ✅ Done | 라운드 총점 계산 |
| REQ-CLI-QUESTIONS-6 | Generate explanation | 4 | ✅ Done | 문제 해설 생성 |
| REQ-CLI-QUESTIONS-7 | Resume session | 4 | ✅ Done | 중단된 세션 재개 |
| REQ-CLI-QUESTIONS-8 | Check time status | 4 | ✅ Done | 시간 제한 확인 |
| REQ-CLI-Agent-1 | Agent 명령 그룹 & 계층적 메뉴 | 4 | ✅ Done | 33 tests (100%), Commit: b9f61fe, Progress: docs/progress/REQ-CLI-Agent-1.md |
| REQ-CLI-Agent-2 | generate-questions 명령 구현 | 4 | ✅ Done | 12 tests (100%), Commit: [pending], Progress: docs/progress/REQ-CLI-Agent-2.md |
| REQ-CLI-Agent-3 | score-answer 명령 구현 | 4 | ✅ Done | 15 tests (100%), Commit: [pending], Progress: docs/progress/REQ-CLI-Agent-3.md |
| REQ-CLI-Agent-4 | batch-score 명령 구현 | 4 | ✅ Done | 15 tests (100%), Commit: 719d5c4, Progress: docs/progress/REQ-CLI-Agent-4.md |
| REQ-CLI-Agent-5 | tools (t1-t6) 명령 구현 | 4 | ✅ Done | 21 tests (100%), Commit: 2535036, Progress: docs/progress/REQ-CLI-Agent-5.md |
| REQ-CLI-SESSION-1 | Save session to file | 0 | ⏳ Backlog | JSON 저장 |
| REQ-CLI-SESSION-2 | Load session from file | 0 | ⏳ Backlog | JSON 복구 |
| REQ-CLI-EXPORT-1 | Export results as JSON | 0 | ⏳ Backlog | 결과 내보내기 |
| REQ-CLI-EXPORT-2 | Export results as CSV | 0 | ⏳ Backlog | 결과 내보내기 |

---

## 🔍 Phase Legend

| Phase | Status | Description |
|-------|--------|-------------|
| 0 | ⏳ Backlog | Not started |
| 1 | 📝 Spec | Specification written, awaiting review |
| 2 | 🧪 Test | Tests designed, awaiting review |
| 3 | 💻 Impl | Implementation in progress, validation running |
| 4 | ✅ Done | Merged to main branch |

## 📦 Status Codes

| Status | Description |
|--------|-------------|
| ⏳ Backlog | Planned for MVP 1.0, not yet started |
| ✅ Done | Completed and merged to main branch |
| ⚠️ Merged | Deprecated or merged into another REQ |
| 📦 MVP 2.0 | Deferred to future release (not in MVP 1.0 scope) |

---

## 📝 Individual Progress Files

For detailed progress on each REQ, see:

- `docs/progress/REQ-X-Y.md` (created when development starts)

Example structure:

```
docs/progress/
├── REQ-B-A2-Edit-1.md    # Developer: bwyoon
├── REQ-F-1-Login.md      # Developer: lavine
└── REQ-A-1-ItemGen.md    # Developer: <person>
```

---

## 🚀 How to Update Progress

After each phase completion:

```bash
# Phase 1-2: Automatically created when you run "REQ-X-Y 기능 구현해"
# docs/progress/REQ-X-Y.md is created automatically

# Phase 4: Update this file manually with:
# - Mark Phase 4 as ✅ Done
# - Add commit SHA and merge date
# - Note any follow-up items
```

---

## 📅 Current Sprint (MVP 1.0)

**Start Date**: 2025-11-07
**Target Date**: 2025-12-31
**Team**: Backend (bwyoon) / Frontend (lavine) / Agent (bwyoon)

**Key Milestones**:

- [ ] Phase 1-2: All REQ specs + tests approved (Week 1-2)
- [ ] Phase 3: All implementations complete + CI passing (Week 3-4)
- [ ] Phase 4: All PRs merged, integration tested (Week 5)
- [ ] UAT: User acceptance testing (Week 6)
