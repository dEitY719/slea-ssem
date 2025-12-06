# Phase 1 Debug Test Script 사용 가이드

**파일**: `scripts/run_phase1_test.sh`
**목적**: REQ-AGENT-0-1 Phase 1 디버그 로깅 테스트
**생성일**: 2025-12-06

---

## 🚀 빠른 시작

### 기본 사용법

```bash
./scripts/run_phase1_test.sh <MODEL_NAME>
```

### 예시

```bash
# Gemini 테스트 (사외 개발 환경)
./scripts/run_phase1_test.sh gemini-2.0-flash

# DeepSeek 테스트 (사내 문제 모델)
./scripts/run_phase1_test.sh deepseek-v3-0324

# GPT-OSS 테스트 (선택사항 - 비교 모델)
./scripts/run_phase1_test.sh gpt-oss-120b
```

---

## 📋 스크립트 기능

### 자동으로 처리되는 작업

1. **로그 디렉토리 생성**: `logs/phase1_debug/` 자동 생성
2. **환경 변수 설정**:
   - `LOG_LEVEL=DEBUG` (필수)
   - `LITELLM_MODEL=<모델명>` (사용자 지정)
3. **타임스탐프 추가**: `logs/phase1_debug/<MODEL>_YYYYMMDD_HHMMSS.log`
4. **로그 분석**: 자동으로 주요 결과 요약 표시
5. **검색 팁 제공**: 로그 분석 명령어 예시 제공

---

## 📝 테스트 절차

### Step 1: Gemini 테스트 (사외 PC)

```bash
./scripts/run_phase1_test.sh gemini-2.0-flash
```

스크립트 실행 후:
```
📌 CLI 실행 중... (LOG_LEVEL=DEBUG)

📝 다음 명령을 CLI에서 입력하세요:
   > auth login <username>
   > questions generate --domain AI --round 1
   > exit
```

**CLI에서 실행**:
```
> auth login bwyoon
✓ Login successful

> questions generate --domain AI --round 1
Generating 5 questions for domain: AI...
✓ Generated 5 questions

> exit
```

---

### Step 2: DeepSeek 테스트 (사내 PC)

```bash
./scripts/run_phase1_test.sh deepseek-v3-0324
```

동일한 절차로 테스트 실행

---

### Step 3: GPT-OSS-120b 테스트 (선택사항)

```bash
./scripts/run_phase1_test.sh gpt-oss-120b
```

---

## 📊 로그 분석

### 자동 요약 (스크립트 실행 후)

```
✅ 테스트 완료!

📌 로그 파일 정보
  경로: logs/phase1_debug/gemini_20251206_130000.log
  크기: 125432 bytes
  줄수: 842 lines

📌 Phase-1 디버그 로그 요약

  Phase-1 로그 라인 수: 45
  파싱 성공: 1
  파싱 실패: 0

✅ ✨ 파싱 성공!
  생성된 문항 개수: 5
```

### 수동 분석

#### Phase-1 로그만 추출
```bash
grep "\[Phase-1-Debug" logs/phase1_debug/gemini_20251206_*.log | head -20
```

#### 특정 요청 추적 (요청 ID로 필터링)
```bash
# 예: req=sess-abc 요청만 추출
grep "req=sess-abc" logs/phase1_debug/gemini_20251206_*.log
```

#### 에러 확인
```bash
grep -E "Parsing failed|Full exception|Error" logs/phase1_debug/gemini_20251206_*.log
```

#### Tool 호출 단계 추적
```bash
grep "Intermediate steps count" logs/phase1_debug/gemini_20251206_*.log
```

#### 전체 로그 보기 (less 사용)
```bash
cat logs/phase1_debug/gemini_20251206_130000.log | less
```

---

## 📁 로그 파일 구조

```
logs/phase1_debug/
├── gemini_20251206_130000.log         # Gemini 테스트
├── gemini_20251206_140000.log         # Gemini 재테스트
├── deepseek_v3_0324_20251206_150000.log  # DeepSeek 테스트
└── gpt_oss_120b_20251206_160000.log   # GPT-OSS 테스트
```

---

## 🔍 로그 분석 가이드

### 정상 작동 시 (Gemini)
```
[Phase-1-Debug req=sess-abc|survey=surv-001|r1] Model: gemini-2.0-flash
[Phase-1-Debug req=sess-abc|survey=surv-001|r1] Intermediate steps count: 5
[Phase-1-Debug req=sess-abc|survey=surv-001|r1] Parsing succeeded: 5 questions
✅ 파싱 성공!
```

### 에러 발생 시 (DeepSeek)
```
[Phase-1-Debug req=sess-def|survey=surv-002|r1] Model: deepseek-v3-0324
[Phase-1-Debug req=sess-def|survey=surv-002|r1] Intermediate steps count: 0
⚠️  Incomplete ReAct response detected
[Phase-1-Debug req=sess-def|survey=surv-002|r1] Parsing failed: JSONDecodeError
❌ 파싱 실패 - 로그 분석 필요
```

---

## 🎯 예상 결과

### Gemini (사외 - 정상 작동 예상)
- ✅ Parsing succeeded 1회
- ✅ 5 questions 생성
- ⏱️ 대략 30-60초

### DeepSeek (사내 - 에러 발생 가능)
- ❌ Parsing failed 가능
- ⚠️ Incomplete ReAct response 가능
- 🔍 근본 원인 파악 필요 (로그 분석)

### GPT-OSS-120b (선택사항 - 비교)
- ✅ 또는 ❌ (안정성 평가)
- 비교: Gemini vs DeepSeek vs GPT-OSS

---

## 🛠️ 문제 해결

### 권한 오류
```bash
# 해결:
chmod +x scripts/run_phase1_test.sh
```

### 로그 디렉토리 권한 문제
```bash
# 해결:
mkdir -p logs/phase1_debug
chmod 755 logs
chmod 755 logs/phase1_debug
```

### LOG_LEVEL=DEBUG 안 먹히는 경우
```bash
# 직접 확인:
export LOG_LEVEL=DEBUG
echo $LOG_LEVEL  # DEBUG 출력 확인

# 로그에 [Phase-1-Debug 보이는지 확인
grep "\[Phase-1-Debug" logs/phase1_debug/*.log
```

### 모델명 오타
```bash
# 올바른 모델명:
gemini-2.0-flash
deepseek-v3-0324
gpt-oss-120b

# 틀린 예:
deepseek (X) → deepseek-v3-0324 (O)
gpt-oss (X) → gpt-oss-120b (O)
```

---

## 📚 참고

- **로깅 구현**: `src/agent/llm_agent.py` (lines 582-710)
- **문서**: `docs/feature/REQ-AGENT-0-1_PHASE1_DEBUG_IMPLEMENTATION.md`
- **피드백 반영**: `docs/feature/REQ-AGENT-0-1_PEER_FEEDBACK_REFLECTION.md`
- **전체 계획**: `docs/feature/REQ-AGENT-0-1_ACTION_PLAN.md`

---

**상태**: ✅ Ready to use
**테스트 시간**: ~30초-2분 (모델별)
**필수 조건**: Python, .venv, LITELLM_MODEL 지원
