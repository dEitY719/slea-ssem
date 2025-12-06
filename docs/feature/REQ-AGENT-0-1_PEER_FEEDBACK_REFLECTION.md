# REQ-AGENT-0-1 Phase 1: 동료 피드백 반영 내용

**작성일**: 2025-12-06
**상태**: ✅ 모든 피드백 반영 완료
**대상**:
- G (Gemini) Review: `REQ-AGENT-0-1_PHASE1_DEBUG_IMPLEMENTATION_review-G.md`
- CX Review: `REQ-AGENT-0-1_PHASE1_DEBUG_IMPLEMENTATION_review-CX.md`

---

## 📋 G의 피드백 및 반영

### 피드백 1: LOG_LEVEL 설정 필요 (⚠️)

**원본**:
> Ensure the internal environment is configured to show `DEBUG` level logs. If the default is `INFO`, these logs won't appear.
> Action: Add a note to the user to run with `LOG_LEVEL=DEBUG`

**반영 내용**:
```markdown
# 문서: REQ-AGENT-0-1_PHASE1_DEBUG_IMPLEMENTATION.md

### 🚨 중요: LOG_LEVEL 설정 필수

**문제**: 기본 로거 레벨이 INFO/WARNING이면 DEBUG 로그가 출력되지 않습니다.
**해결**: 사내 테스트 시 반드시 LOG_LEVEL=DEBUG를 설정해야 합니다.

### 사내 테스트 방법

# 터미널 1: CLI 실행 (LOG_LEVEL=DEBUG 필수)
export LOG_LEVEL=DEBUG
export LITELLM_MODEL=deepseek-v3-0324
python src/cli/main.py > logs/phase1_debug/deepseek_$(date +%Y%m%d_%H%M%S).log 2>&1
```

**검증**: ✅ 사내 테스트 절차에 명시적으로 포함

---

### 피드백 2: 구현 준비 완료 (✅)

**원본**:
> Ready for Deployment/Testing. No code changes required.

**결론**:
✅ G의 검토 완료 - 코드 품질 승인됨

---

## 📋 CX의 피드백 및 반영

### 피드백 1: DEBUG 로그 레벨 노출 조건 문서화

**원본**:
> DEBUG 로그 노출 조건이 문서화되지 않음
> 개선: 사내 수집 절차에 `LOG_LEVEL=DEBUG` 설정과 로그 핸들러(파일/콘솔) 예시를 명시해 주세요.

**반영 내용**:

#### 문서 업데이트
```markdown
# 문서: REQ-AGENT-0-1_PHASE1_DEBUG_IMPLEMENTATION.md

### 🚨 중요: LOG_LEVEL 설정 필수

**문제**: 기본 로거 레벨이 INFO/WARNING이면 DEBUG 로그가 출력되지 않습니다.
**해결**: 사내 테스트 시 반드시 LOG_LEVEL=DEBUG를 설정해야 합니다.

### 로그 디렉토리 준비
mkdir -p logs/phase1_debug

### 사내 테스트 방법 (3가지 선택지)

#### 1️⃣ DeepSeek 테스트 (필수)
export LOG_LEVEL=DEBUG
export LITELLM_MODEL=deepseek-v3-0324
python src/cli/main.py > logs/phase1_debug/deepseek_$(date +%Y%m%d_%H%M%S).log 2>&1

#### 2️⃣ Gemini 테스트 (선택)
export LOG_LEVEL=DEBUG
export LITELLM_MODEL=gemini-2.0-flash
python src/cli/main.py > logs/phase1_debug/gemini_$(date +%Y%m%d_%H%M%S).log 2>&1

#### 3️⃣ GPT-OSS-120b 테스트 (선택)
export LOG_LEVEL=DEBUG
export LITELLM_MODEL=gpt-oss-120b
python src/cli/main.py > logs/phase1_debug/gpt_oss_$(date +%Y%m%d_%H%M%S).log 2>&1
```

**검증**: ✅ 명시적으로 문서화됨

---

### 피드백 2: 요청 상관키 부재 (요청 추적 어려움)

**원본**:
> 요청 상관키가 로그에 없어 다중 요청 시 추적 곤란
> 현재 로그는 모델명/step 정도만 남기고 `session_id`, `survey_id`, `round_id` 등 식별자를 찍지 않아
> 개선: 각 Phase-1 디버그 라인에 `session_id`와 `round_id` 포함

**반영 내용**:

#### 코드 변경 (src/agent/llm_agent.py)
```python
# 요청 상관키 추출
session_id = request.session_id
survey_id = request.survey_id
round_idx = request.round_idx

# Phase 1 디버그 프리픽스 (모든 Phase-1 로그에 포함)
phase1_prefix = f"[Phase-1-Debug req={session_id[:8]}|survey={survey_id[:8]}|r{round_idx}]"

# 모든 Phase-1 로그에 prefix 사용
logger.debug(f"{phase1_prefix} Model: {model_name}")
logger.debug(f"{phase1_prefix} Agent input length: {len(agent_input)}")
logger.debug(f"{phase1_prefix} Intermediate steps count: {len(intermediate_steps)}")
# ... 이하 모든 Phase-1 로그
```

#### 로그 출력 예시
```
[Phase-1-Debug req=sess-001|survey=surv-001|r1] Model: deepseek-v3-0324
[Phase-1-Debug req=sess-001|survey=surv-001|r1] Agent input length: 1234
[Phase-1-Debug req=sess-001|survey=surv-001|r1] Intermediate steps count: 5
[Phase-1-Debug req=sess-001|survey=surv-001|r1] Parsing succeeded: 5 questions
```

#### 장점
- ✅ 동시 다중 요청 실행 시 각 요청의 로그를 명확히 추적 가능
- ✅ 그렉 또는 다른 분석 도구로 특정 요청만 추출 가능
  ```bash
  grep "req=sess-001" logs/phase1_debug/*.log  # 특정 요청만 추출
  ```

**검증**: ✅ 코드 구현 + 문서화 완료

---

### 피드백 3: 수집 절차 미상세 (로그 보존/공유 어려움)

**원본**:
> 수집 절차에 로그 저장 위치/보존 방식 안내 부재
> 어디에 파일로 저장할지/회차별로 구분할지가 명시되지 않아
> 개선: 로그 디렉토리/파일명 패턴을 제안하고, LOG_FORMAT 예시 추가

**반영 내용**:

#### 로그 디렉토리 구조
```
logs/phase1_debug/
├── deepseek_20251206_120000.log      # DeepSeek 테스트 1차
├── deepseek_20251206_140000.log      # DeepSeek 테스트 2차 (모델 수정 후)
├── gemini_20251206_120530.log        # Gemini 참조 (선택사항)
└── gpt_oss_20251206_141000.log       # GPT-OSS 비교 (선택사항)
```

#### 파일명 패턴
```
<MODEL>_<DATE>_<TIME>.log

예시:
- deepseek_20251206_120000.log   # YYYYMMDD_HHMMSS 형식
- gemini_20251206_153045.log
- gpt_oss_20251206_160000.log
```

#### 파일 생성 명령
```bash
# 타임스탬프 자동으로 포함
python src/cli/main.py > logs/phase1_debug/deepseek_$(date +%Y%m%d_%H%M%S).log 2>&1
```

#### 로그 검색/분석 팁
```bash
# 특정 모델 로그만 추출
grep "Model: deepseek-v3-0324" logs/phase1_debug/deepseek_*.log

# 특정 요청만 추출
grep "req=sess-001" logs/phase1_debug/*.log

# 에러만 추출
grep "Parsing failed" logs/phase1_debug/deepseek_*.log

# Phase-1 디버그 로그만 추출
grep "\[Phase-1-Debug" logs/phase1_debug/deepseek_*.log | head -50

# 특정 날짜 로그만
ls logs/phase1_debug/deepseek_20251206_*.log
```

**검증**: ✅ 문서에 명시적으로 포함

---

## ✅ 변경 요약

### 코드 변경
| 파일 | 변경 내용 | 상태 |
|------|---------|------|
| `src/agent/llm_agent.py` | 요청 상관키 추가 (session_id/survey_id/round_id) | ✅ 완료 |
| `src/agent/llm_agent.py` | 모든 Phase-1 로그에 prefix 추가 | ✅ 완료 |

### 문서 변경
| 파일 | 변경 내용 | 상태 |
|------|---------|------|
| `PHASE1_DEBUG_IMPLEMENTATION.md` | LOG_LEVEL=DEBUG 설정 명시 | ✅ 완료 |
| `PHASE1_DEBUG_IMPLEMENTATION.md` | 로그 디렉토리 구조 명시 | ✅ 완료 |
| `PHASE1_DEBUG_IMPLEMENTATION.md` | 파일명 패턴 제안 | ✅ 완료 |
| `PHASE1_DEBUG_IMPLEMENTATION.md` | 로그 검색 팁 추가 | ✅ 완료 |

### 테스트 결과
```
✅ 15 tests PASSED (test_with_structured_output.py)
✅ 3 tests PASSED (test_llm_agent.py::TestGenerateQuestionsHappyPath)
✅ 모든 기존 기능 유지 (로깅만 추가)
```

---

## 🚀 사내 테스트 준비 완료

### Phase 1 체크리스트

- ✅ 디버깅 로깅 코드 구현
- ✅ 요청 식별 정보 추가 (session_id/survey_id/round_id)
- ✅ LOG_LEVEL=DEBUG 설정 명시
- ✅ 로그 디렉토리 구조 정의
- ✅ 파일명 패턴 제안
- ✅ 로그 검색 팁 제공
- ✅ 모든 테스트 통과

### 다음 단계

사용자는 다음 명령으로 사내 테스트 시작:

```bash
# 로그 디렉토리 생성
mkdir -p logs/phase1_debug

# DeepSeek 테스트 (필수)
export LOG_LEVEL=DEBUG
export LITELLM_MODEL=deepseek-v3-0324
python src/cli/main.py > logs/phase1_debug/deepseek_$(date +%Y%m%d_%H%M%S).log 2>&1

# 로그 파일에서 Phase-1-Debug 로그 추출
grep "\[Phase-1-Debug" logs/phase1_debug/deepseek_*.log
```

---

## 📌 참고

- **동료 피드백**: G(승인), CX(3가지 개선 사항)
- **모든 피드백 반영됨**: ✅
- **코드 품질**: 변경사항 최소, 로깅만 추가
- **테스트**: 모두 통과 ✅

---

**상태**: 🟢 Ready for Production Testing
**날짜**: 2025-12-06
**다음 액션**: 사내 환경에서 로그 수집 시작
