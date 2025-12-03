attempt_answers.score 필드의 역할

  🎯 핵심 개념

  score 필드는 개별 문제의 점수를 저장합니다:

  | 문제 유형           | score 값    | 의미                                     |
  |-----------------|------------|----------------------------------------|
  | Multiple Choice | 1.0 또는 0.0 | 정답=1, 오답=0                             |
  | True/False      | 1.0 또는 0.0 | 정답=1, 오답=0                             |
  | Short Answer    | 0-100      | 키워드 매칭 비율: (맞은 키워드 수 / 전체 키워드 수) × 100 |

  📋 당신이 본 데이터 분석

  User Answer: {"selected_key": "F1-score"}
  Correct Answer: "F1-score"
  Result: is_correct=true, score=1

  왜 score=1인가?

- MC 문제는 항상 binary (1 또는 0)
- 정답이므로 1이 저장됨
- 부분 점수가 없음

  ---
  📈 N개 문제 풀 때 점수 계산 예제

  예시: 10개 MC 문제 풀이

# 개별 문제 점수 (attempt_answers 테이블)

  Questions:

  1. MC: ✓ (score=1)
  2. MC: ✓ (score=1)
  3. MC: ✗ (score=0)
  4. MC: ✓ (score=1)
  5. MC: ✗ (score=0)
  6. Short Answer (3 keywords):
     - User: "AI, Machine Learning, Data"
     - Keywords needed: ["AI", "ML", "Data Analysis"]
     - Matched: 2/3 → score=66.67
  7. MC: ✓ (score=1)
  8. MC: ✓ (score=1)
  9. MC: ✓ (score=1)
  10. MC: ✗ (score=0)

# 최종 라운드 점수 계산

  Total Score = (1 + 1 + 0 + 1 + 0 + 66.67 + 1 + 1 + 1 + 0) / 10 *100
              = 72.67 / 10* 100
              = 72.67%

  예시 2: Short Answer에서 부분 점수

# Short Answer 문제

  Question: "AI와 Machine Learning의 차이를 설명하세요"
  answer_schema: {
      "keywords": ["AI", "Machine Learning", "subset", "broader", "learning"]
  }

# 사용자 답변

  user_answer: {
      "text": "AI는 Machine Learning을 포함하는 broader 개념이다"
  }

# 점수 계산

  matched_keywords = ["AI", "Machine Learning", "broader"]  # 3개
  total_keywords = 5
  score = (3 / 5) * 100 = 60.0

# 결과

  is_correct = False (완벽하지 않음, 모든 키워드 필요)
  score = 60.0 (부분 점수)

  ---
  🔄 DB 흐름도: Score의 생명주기

  ┌─────────────────────────────────────────────────┐
  │ 1. 사용자가 문제 풀이                          │
  │    (answer autosave)                            │
  └──────────────┬──────────────────────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────────────────────┐
  │ 2. attempt_answers 생성                         │
  │    - is_correct: NULL                           │
  │    - score: 0.0 (기본값)                        │
  │    - user_answer: 저장됨                       │
  └──────────────┬──────────────────────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────────────────────┐
  │ 3. 점수 계산 (score_answer)                     │
  │    - 문제 유형에 따라 점수 결정                │
  │      • MC/TF: 1.0 또는 0.0                     │
  │      • Short Answer: 0-100 (부분 점수)        │
  │    - 시간 페널티 적용 (선택)                   │
  │    - is_correct, score 업데이트               │
  └──────────────┬──────────────────────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────────────────────┐
  │ 4. 라운드 점수 계산 (calculate_round_score)    │
  │    - 모든 attempt_answers의 score 합산         │
  │    - total_score = SUM(scores) / count * 100   │
  │    - test_results에 최종 점수 저장            │
  └─────────────────────────────────────────────────┘

  ---
  💡 시간 페널티 예제

# 시간 제한: 20분 (1200000ms)

# 실제 소비: 25분 (1500000ms)

  base_score = 100.0 (모두 맞음)

  elapsed_ms = 1500000
  time_limit_ms = 1200000
  excess_ms = 1500000 - 1200000 = 300000

  penalty_ratio = 300000 / 1200000 = 0.25 (25%)
  penalty_points = 0.25 * 100 = 25점

  final_score = 100 - 25 = 75점

  ---
  🚀 당신의 질문에 답변

  Q1: "score 필드는 필요한가?"

  A: 네, 필수입니다! 특히:

- Short Answer: 부분 점수를 위해 필수 (0-100)
- 다중 문제 시나리오: 각 문제별 점수를 추적해야 분석 가능
- 약점 분석: 카테고리별 점수를 계산할 때 필요

  Q2: "왜 MC에서는 항상 1이 나오는가?"

  A: MC/TF는 부분 점수가 없기 때문:

- 정답: 1
- 오답: 0
- 중간값 없음

  MC를 10점, 20점 같이 다양하게 하려면 문제마다 다른 가중치(weight) 필드가 필요합니다.

  Q3: "N개 문제에서 최종 점수 계산 방식?"

  A: 평균값 (현재 구현):
  최종 점수 = SUM(all scores) / total_questions * 100

  ---
  📋 개선 제안 (선택사항)

  현재 구조에서 더 나은 점수 관리를 위해:

# 제안: 문제별 가중치 추가

  class Question(Base):
      ...
      weight: float = 1.0  # 기본 1.0, MC는 2.0, SA는 3.0 등
      max_points: float = 100.0

# 최종 점수 계산

  total_points = sum(attempt.score *question.weight)
  max_total = sum(question.max_points* question.weight)
  final_score = (total_points / max_total) * 100

  ---
  정리: score는 필수 필드이며, MC는 binary (0/1), Short Answer는 부분점수(0-100)를 저장합니다! 🎯
