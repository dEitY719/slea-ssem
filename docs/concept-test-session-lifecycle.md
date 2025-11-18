  📊 TestSession 생명주기 (Lifecycle) - 상세 설명

  1️⃣ 상태(Status) 종류

  ┌─────────────────────────────────────────┐
  │     TestSession Status States           │
  ├─────────────────────────────────────────┤
  │ 1. in_progress  → 테스트 진행 중        │
  │ 2. paused       → 일시 중지됨           │
  │ 3. completed    → 완료됨 (미구현)       │
  └─────────────────────────────────────────┘

  2️⃣ 전체 생명주기 흐름

  시작점
    ↓
    ├─────────────────────────────────────────────────────────┐
    │                                                           │
    ▼ [1] questions generate 실행                              │
  ┌──────────────────────────┐                                 │
  │ TestSession 생성         │                                 │
  │ status = in_progress     │                                 │
  │ started_at = NULL        │                                 │
  │ paused_at = NULL         │                                 │
  └──────────────────────────┘                                 │
    │                                                           │
    │ ✅ 질문 5개 생성됨                                       │
    │ ✅ Questions 테이블에 저장                               │
    │                                                           │
    ▼ [2] questions answer autosave 실행 (질문에 답변)        │
  ┌──────────────────────────┐                                 │
  │ AttemptAnswer 생성       │                                 │
  │ is_correct = false       │ ← 기본값 (아직 채점X)        │
  │ score = 0.0              │                                 │
  └──────────────────────────┘                                 │
    │                                                           │
    │ [3-A] 시간 초과 발생                 [3-B] 모든 답변 완료 │
    ▼                                            ▼               │
  ┌──────────────────────────┐          ┌──────────────────────┐
  │ AutoPause (자동)         │          │ questions score 실행 │
  │ status = paused          │          │                      │
  │ paused_at = NOW()        │          │ [배치 채점 시작]    │
  │ (시간 초과 감지)         │          │                      │
  └──────────────────────────┘          │ 1. 미채점 답변 찾음 │
    │                                    │ 2. 각 답변 채점     │
    │ [4] 수동 재개                      │ 3. is_correct 업데이트
    ▼                                    │ 4. score 업데이트   │
  ┌──────────────────────────┐          │ 5. TestResult 생성  │
  │ questions session resume │          │                      │
  │ status = in_progress     │          │ [채점 완료]         │
  │ paused_at = NULL         │          │                      │
  └──────────────────────────┘          └──────────────────────┘
    │                                            │
    ▼ [다시 질문에 답변]                        ▼ [라운드 점수 저장]
   ...                                   ┌──────────────────────┐
                                         │ TestResult 레코드    │
                                         │ - round = 1          │
                                         │ - score = 75.5%      │
                                         │ - correct_count = 3  │
                                         │ - total_count = 5    │
                                         │ - wrong_categories   │
                                         └──────────────────────┘
                                             │
                                             ▼ [라운드 2로 진행]
                                         ┌──────────────────────┐
                                         │ TestSession Round 2  │
                                         │ round = 2            │
                                         │ status = in_progress │
                                         │ (새로운 세션 생성)  │
                                         └──────────────────────┘

  ---
  3️⃣ 각 단계별 상세 설명

  [단계 1] questions generate - 세션 생성

  | 이벤트                        | 조건          | 변경사항                   | 코드위치                            |
  |----------------------------|-------------|------------------------|---------------------------------|
  | CLI 명령: questions generate | 사용자가 테스트 시작 | ✅ TestSession 생성       | question_gen_service.py:307-315 |
  |                            |             | status = "in_progress" |                                 |
  |                            |             | started_at = NULL (아직) |                                 |
  |                            |             | paused_at = NULL       |                                 |
  |                            | ✅ 질문 5개 생성됨 | Questions 테이블에 저장      | question_gen_service.py:350+    |

  Database 변경:
  INSERT INTO test_sessions (id, user_id, round, status, started_at, paused_at)
  VALUES ('<uuid>', 1, 1, 'in_progress', NULL, NULL);

  ---
  [단계 2-A] 자동 일시중지 (시간 초과)

  | 이벤트                            | 조건         | 변경사항                | 코드위치                        |
  |--------------------------------|------------|---------------------|-----------------------------|
  | questions answer autosave 실행 중 | 경과시간 > 20분 | ✅ status = "paused" | autosave_service.py:191     |
  |                                |            | ✅ paused_at = NOW() | autosave_service.py:192     |
  |                                |            | (자동 일시중지)           | autosave_service.py:167-195 |

  트리거 코드:

# src/backend/api/questions.py:487-491

  time_status = autosave_service.check_time_limit(request.session_id)
  if time_status["exceeded"]:
      autosave_service.pause_session(request.session_id, reason="time_limit")

  Database 변경:
  UPDATE test_sessions
  SET status = 'paused', paused_at = NOW()
  WHERE id = '<session_id>';

  ---
  [단계 3] questions score - 배치 채점

  | 이벤트                     | 조건        | 변경사항              | 코드위치                       |
  |-------------------------|-----------|-------------------|----------------------------|
  | CLI 명령: questions score | 라운드 종료 후  | ✅ 모든 미채점 답변 찾음    | scoring_service.py:351-365 |
  |                         |           | ✅ 각 답변별 채점 함수 실행  | scoring_service.py:367-380 |
  |                         |           | ✅ is_correct 업데이트 | scoring_service.py:390     |
  |                         |           | ✅ score 업데이트      | scoring_service.py:391     |
  |                         | ✅ 채점 완료 후 | ✅ TestResult 생성   | scoring_service.py:489     |

  배치 채점 로직:

# src/backend/services/scoring_service.py:337-392

  def _score_all_unscored_answers(self, session_id: str) -> None:
      # 1. is_correct IS NULL OR (is_correct=false AND score=0)인 답변 찾음
      unscored = self.session.query(AttemptAnswer).filter(
          AttemptAnswer.session_id == session_id,
          or_(
              AttemptAnswer.is_correct.is_(None),
              and_(AttemptAnswer.is_correct.is_(False), AttemptAnswer.score == 0.0),
          ),
      ).all()

      # 2. 각 답변 채점
      for attempt in unscored:
          question = self.session.query(Question).filter_by(id=attempt.question_id).first()
          if question.item_type == "multiple_choice":
              is_correct, base_score = self._score_multiple_choice(attempt.user_answer, ...)
          # ... 기타 타입

          # 3. 시간 페널티 적용
          _, final_score = self._apply_time_penalty(base_score, test_session)

          # 4. 데이터베이스 업데이트
          attempt.is_correct = is_correct
          attempt.score = final_score
          self.session.commit()

  Database 변경:
  -- 답변 업데이트
  UPDATE attempt_answers
  SET is_correct = true, score = 100.0, updated_at = NOW()
  WHERE session_id = '<session_id>';

  -- 결과 저장
  INSERT INTO test_results (id, session_id, round, score, correct_count, total_count, wrong_categories)
  VALUES ('<uuid>', '<session_id>', 1, 75.5, 3, 5, '{"LLM": 2}');

  ---
  [단계 2-B] 수동 일시중지 / 재개

  | 이벤트                                         | 조건         | 변경사항                     | 코드위치
  |
  |---------------------------------------------|------------|--------------------------|--------------------------|
  | PUT /session/{id}/status?status=paused      | 사용자가 중지 요청 | ✅ status = "paused"      | api/questions.py:603-604 |
  |                                             |            | ✅ paused_at = NOW()      | autosave_service.py:192  |
  | PUT /session/{id}/status?status=in_progress | 사용자가 재개 요청 | ✅ status = "in_progress" | api/questions.py:606     |
  |                                             |            | ✅ paused_at = NULL       | autosave_service.py:295  |

  ---
  4️⃣ 시간 페널티 메커니즘

  시간 페널티는 questions score 실행 시 적용됨:

  ┌─────────────────────────────────────┐
  │ 세션 경과시간 계산                 │
  │ elapsed_ms = paused_at - started_at │
  └─────────────────────────────────────┘
             ↓
         20분(1200초) 비교
             ↓
      ┌─────────┴──────────┐
      ▼                    ▼
    [≤20분]              [>20분]
    NO PENALTY          시간 페널티 계산
      │                   │
      │              excess_ms = elapsed - 1200000
      │              penalty_ratio = excess / 1200000
      │              penalty_points = ratio * score
      │              final_score = max(0, score - penalty)
      │
      └────────┬──────────┘
               ▼
      최종 점수 저장 (final_score)

  예시:
    기본 점수: 100.0
    경과시간: 3086초 (51분)
    excess_ms: 1886000ms
    penalty_ratio: 1.57
    penalty_points: 157.0
    final_score: max(0, 100 - 157) = 0.0

  ---
  5️⃣ 상태 전이 테이블 (State Transition Matrix)

  | 현재 상태                | 이벤트                | 다음 상태         | 조건                                          |
  |----------------------|--------------------|---------------|---------------------------------------------|
  | in_progress          | 시간 초과 감지           | paused        | elapsed_ms > time_limit_ms                  |
  | in_progress          | 수동 일시중지            | paused        | PUT /session/{id}/status?status=paused      |
  | paused               | 수동 재개              | in_progress   | PUT /session/{id}/status?status=in_progress |
  | paused               | questions score 실행 | paused (변경없음) | 채점만 진행, 상태는 유지                              |
  | in_progress / paused | 라운드 2 생성           | in_progress (새 세션) | 새로운 TestSession 생성                      |

  ---
  6️⃣ 테이블 간 관계도

  users (1 user)
     │
     ├──→ user_profile_surveys (프로필 선택)
     │         │
     │         └─→ test_sessions (테스트 세션)
     │                 │
     │                 ├─→ questions (5개 질문)
     │                 │      └─→ attempt_answers (사용자 답변)
     │                 │             └─→ [채점 데이터]
     │                 │
     │                 └─→ test_results (라운드 결과)
     │                        └─→ [최종 점수 저장]
     │
     └──→ user_rankings (최종 순위)

  ---
  7️⃣ 실제 데이터베이스 값 예시

  TestSession Record:
  {
    "id": "9f13c003-888d-4819-9513-ccf3be721a23",
    "user_id": 1,
    "survey_id": "survey-001",
    "round": 1,
    "status": "paused",           ← 일시중지됨
    "time_limit_ms": 1200000,      ← 20분
    "started_at": "2025-11-17 13:57:29",
    "paused_at": "2025-11-17 14:48:55",   ← 51분 경과
    "created_at": "2025-11-17 13:57:29",
    "updated_at": "2025-11-17 14:48:55"
  }

  AttemptAnswer Record (채점 후):
  {
    "id": "ee95808d-45de-48bc-8910-e5ed00dd98f0",
    "session_id": "9f13c003-888d-4819-9513-ccf3be721a23",
    "question_id": "a6166c75-793e-4351-9182-3b8f82199646",
    "user_answer": {"answer": false},
    "is_correct": true,           ← 채점됨
    "score": 0.0,                 ← 시간 페널티 적용됨
    "created_at": "2025-11-17 14:38:21"
  }

  TestResult Record (라운드 결과):
  {
    "id": "result-001",
    "session_id": "9f13c003-888d-4819-9513-ccf3be721a23",
    "round": 1,
    "score": 0.0,                 ← 시간 페널티로 인한 낮은 점수
    "total_points": 0.0,
    "correct_count": 1,           ← 1개 정답
    "total_count": 3,             ← 3개 답변
    "wrong_categories": {"AI": 1, "ML": 1},
    "created_at": "2025-11-17 14:48:56"
  }

  ---
  ✅ 요약

  1. 생성: questions generate → TestSession 생성 (status=in_progress)
  2. 답변: questions answer autosave → AttemptAnswer 저장 (is_correct=false, score=0)
  3. 자동 중지: 20분 초과 → status=paused, paused_at=NOW()
  4. 채점: questions score → 배치 채점, is_correct/score 업데이트
  5. 결과 저장: TestResult 생성 (시간 페널티 적용된 최종 점수)
  6. 다음 라운드: Round 2 테스트를 위해 새로운 TestSession 생성
