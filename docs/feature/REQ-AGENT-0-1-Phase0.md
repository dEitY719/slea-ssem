● Phase 1️⃣: SPECIFICATION - REQ-AGENT-0-1 with_structured_output 도입

  요구사항 분석

  REQ-AGENT-0-1: with_structured_output 도입

  - 목표: 수동 JSON 파싱 제거, LangChain with_structured_output으로 모델 간 차이 추상화
  - Priority: P0
  - Dependencies: REQ-AGENT-0-0 (완료됨 ✅)

  ---
  현재 상황 (이전)

  # 현재: 복잡한 3단계 파싱 프로세스
  1. Agent 실행 → ReAct Final Answer 텍스트 반환
  2. AgentOutputConverter.parse_final_answer_json() → JSON 추출
  3. parse_json_robust() → 5가지 cleanup 전략으로 JSON 정제
  4. 여전히 실패 가능성 높음

  문제점:
  - _parse_agent_output_generate (line 888): 999줄에 걸친 복잡한 파싱 로직
  - parse_json_robust (line 48): 5가지 정제 전략으로도 불안정
  - AgentOutputConverter: JSON 문자열 → dict 변환의 다양한 엣지 케이스 처리
  - 타입 안전성 부재: 문자열 파싱이므로 런타임 에러 가능

  ---
  개선 후 (with_structured_output)

  # 개선: LangChain의 with_structured_output 사용
  if should_use_structured_output(self.llm.model_name):
      # Gemini: with_structured_output 사용
      structured_llm = self.llm.with_structured_output(GenerateQuestionsResponse)
      response = await structured_llm.ainvoke(prompts)  # 직접 Pydantic 객체 반환
  else:
      # DeepSeek: TextReActAgent (기존 경로)
      response = await self.text_react_agent.ainvoke(...)

  장점:
  - ✅ LangChain이 모델별 차이 내부 처리 (JSON mode, function calling 자동 선택)
  - ✅ 복잡한 파싱 로직 제거 가능 (parse_json_robust, AgentOutputConverter.parse_final_answer_json 불필요)
  - ✅ 타입 안전성 보장 (Pydantic 스키마로 검증)
  - ✅ 오류 감소: 타입 미스매치 자동 감지

  ---
  구현 범위

  | 파일                              | 작업                                  | 상세                                                           |
  |---------------------------------|-------------------------------------|--------------------------------------------------------------|
  | src/agent/llm_agent.py:549      | generate_questions 수정               | should_use_structured_output() 적용, with_structured_output 호출 |
  | src/agent/llm_agent.py:888-1100 | _parse_agent_output_generate 제거/단순화 | 구조화된 응답 직접 사용 가능                                             |
  | src/agent/llm_agent.py:48-115   | parse_json_robust 제거                | 더 이상 필요 없음                                                   |
  | src/agent/config.py             | should_use_structured_output() 호출   | 기존 정의된 함수 활용                                                 |

  ---
  Acceptance Criteria

  - should_use_structured_output(llm.model_name)로 Gemini만 structured output 적용
  - parse_json_robust 함수 제거 (사용처 확인 후 안전하게 제거)
  - _parse_agent_output_generate 함수 제거 또는 단순화 (이전 파싱 로직 불필요)
  - AgentOutputConverter.parse_final_answer_json 호출 제거
  - 타입 안전성 보장: GenerateQuestionsResponse Pydantic 객체로 직접 반환
  - 테스트 통과: pytest tests/agent/ -v (모든 기존 테스트 pass)
  - Gemini (structured output) 및 DeepSeek (TextReAct fallback) 경로 모두 검증

  ---
  우려사항 & 완화 전략

  | 우려사항                                      | 완화 전략                                            |
  |-------------------------------------------|--------------------------------------------------|
  | DeepSeek에서 with_structured_output 호출 시 에러 | should_use_structured_output() guard로 Gemini만 실행 |
  | 기존 ReAct 텍스트 파싱 코드 의존성 파악 어려움             | Grep으로 모든 호출처 확인 후 제거                            |
  | 프로덕션 배포 시 장애 위험                           | Phase 2 테스트 설계로 모든 엣지 케이스 검증                     |

  ---
  질문: 구현 방향 승인

  Phase 1 내용이 적절한가요? 다음 내용으로 진행해도 될까요?

  1. Phase 2 (Test Design): 4-5개 테스트 케이스 설계 (Gemini structured output, DeepSeek fallback, 타입 검증 등)
  2. Phase 3 (Implementation): 코드 작성 및 테스트 통과
  3. Phase 4 (Summary): 진행 파일 생성 및 commit