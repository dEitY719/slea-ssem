# Team Development Progress

Overall progress tracking for MVP 1.0 development across all developers.

---

## 📊 Development Status (MVP 1.0)

### Frontend (lavine)

| REQ ID | Feature | Phase | Status | Notes |
|--------|---------|-------|--------|-------|
| REQ-F-A1 | 로그인 화면 (Samsung AD) | 0 | ⏳ Backlog | 3개 sub-tasks |
| REQ-F-A2 | 닉네임 등록 화면 | 0 | ⏳ Backlog | 5개 sub-tasks |
| REQ-F-A2-Edit | 프로필 수정 화면 | 0 | ⏳ Backlog | 6개 sub-tasks |
| REQ-F-A3 | 온보딩 모달 | 0 | ⏳ Backlog | 2개 sub-tasks |
| REQ-F-B1 | 자기평가 입력 화면 | 0 | ⏳ Backlog | 3개 sub-tasks |
| REQ-F-B2 | 문항 풀이 화면 | 0 | ⏳ Backlog | 7개 sub-tasks |
| REQ-F-B3 | 해설 화면 | 0 | ⏳ Backlog | 2개 sub-tasks |
| REQ-F-B4 | 최종 결과 페이지 | 0 | ⏳ Backlog | 3개 sub-tasks |
| REQ-F-B5 | 재응시 및 비교 화면 | 0 | ⏳ Backlog | 3개 sub-tasks |
| REQ-F-B6 | 재미 모드 (카테고리 선택형 퀴즈) | 0 | ⏳ Backlog | 3개 sub-tasks |

### Backend (bwyoon)

| REQ ID | Feature | Phase | Status | Notes |
|--------|---------|-------|--------|-------|
| REQ-B-A1 | Samsung AD 인증 & 세션 관리 | 0 | ⏳ Backlog | 4개 sub-tasks |
| REQ-B-A2 | 닉네임 등록 | 0 | ⏳ Backlog | 5개 sub-tasks |
| REQ-B-A2-Edit | 프로필 수정 | 0 | ⏳ Backlog | 4개 sub-tasks |
| REQ-B-B1 | 자기평가 데이터 수집 & 저장 | 0 | ⏳ Backlog | 2개 sub-tasks |
| REQ-B-B4 | 최종 등급 & 순위 산출 | 0 | ⏳ Backlog | 5개 sub-tasks |
| REQ-B-B4-Plus | 등급 기반 배지 부여 | 0 | ⏳ Backlog | 3개 sub-tasks |
| REQ-B-B5 | 응시 이력 저장 & 조회 | 0 | ⏳ Backlog | 5개 sub-tasks |
| REQ-B-B6 | 문항 품질 - 콘텐츠 필터 | 0 | ⏳ Backlog | 1개 sub-task (MVP 1.0) |
| REQ-B-B6-Plus | 재미 모드 (Backend) | 0 | ⏳ Backlog | 5개 sub-tasks |

### Agent (TBD - person 필요)

| REQ ID | Feature | Phase | Status | Notes |
|--------|---------|-------|--------|-------|
| REQ-B-B2-Plus | 실시간 저장 & 재개 | 0 | ⏳ Backlog | 5개 sub-tasks |
| REQ-B-B2-Gen | 1차 문항 생성 | 0 | ⏳ Backlog | 3개 sub-tasks |
| REQ-B-B2-Adapt | 2차 적응형 난이도 조정 | 0 | ⏳ Backlog | 4개 sub-tasks |
| REQ-B-B3-Score | 채점 (정오답 판정) | 0 | ⏳ Backlog | 3개 sub-tasks |
| REQ-B-B3-Explain | 해설 생성 | 0 | ⏳ Backlog | 1개 sub-task |
| REQ-B-B7 | 학습 일정 예고 프리뷰 | 0 | ⏳ Backlog | 3개 sub-tasks (MVP 1.0) |

---

## 🔍 Phase Legend

| Phase | Status | Description |
|-------|--------|-------------|
| 0 | ⏳ Backlog | Not started |
| 1 | 📝 Spec | Specification written, awaiting review |
| 2 | 🧪 Test | Tests designed, awaiting review |
| 3 | 💻 Impl | Implementation in progress, validation running |
| 4 | ✅ Done | Merged to main branch |

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
**Team**: Backend (bwyoon) / Frontend (lavine) / Agent (TBD)

**Key Milestones**:

- [ ] Phase 1-2: All REQ specs + tests approved (Week 1-2)
- [ ] Phase 3: All implementations complete + CI passing (Week 3-4)
- [ ] Phase 4: All PRs merged, integration tested (Week 5)
- [ ] UAT: User acceptance testing (Week 6)
