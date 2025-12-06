# Phase 1 Debug Test - 실행 가이드

## ⚡ 빠른 요약

**시간 낭비 없이 2개 터미널로 깔끔하게 해결:**

1. **터미널 1** (로그 수집):
   ```bash
   ./scripts/run_phase1_test.sh deepseek-v3-0324
   # 화면에 표시되는 grep 명령 복사 실행
   ```

2. **터미널 2** (CLI 실행):
   ```bash
   ./tools/dev.sh cli
   > auth login <username>
   > questions generate --domain AI --round 1
   > exit
   ```

3. **터미널 1**에서 `[Phase-1-Debug]` 로그 관찰 및 기록

---

## 📋 단계별 실행

### Step 1: 환경 변수 설정 (터미널 1)

```bash
./scripts/run_phase1_test.sh deepseek-v3-0324
```

출력:
```
===============================================================================
  REQ-AGENT-0-1 Phase 1: Production Error Debugging
===============================================================================

✅ 환경 설정 완료
  - LOG_LEVEL: DEBUG
  - LITELLM_MODEL: deepseek-v3-0324

이제 2개의 터미널을 사용해주세요:

  [터미널 1 - 이 창] 로그 수집용:
    tail -f ~/.local/share/slea-ssem/logs/*.log 2>/dev/null | grep '\[Phase-1-Debug'

  [터미널 2 - 새 창] CLI 실행용:
    ./tools/dev.sh cli

    그 후 CLI 프롬프트에서:
    > auth login <username>
    > questions generate --domain AI --round 1
    > exit
```

### Step 2: 로그 수집 (터미널 1)

표시된 명령을 복사하여 **같은 터미널**에서 실행:

```bash
tail -f ~/.local/share/slea-ssem/logs/*.log 2>/dev/null | grep '\[Phase-1-Debug'
```

이제 CLI 로그를 실시간으로 모니터링합니다.

### Step 3: CLI 실행 (터미널 2 - 새 창)

```bash
./tools/dev.sh cli
```

CLI 프롬프트가 나타나면:

```
> auth login bwyoon
✓ Login successful

> questions generate --domain AI --round 1
Generating questions for domain: AI...

> exit
```

### Step 4: 결과 확인 (터미널 1)

[Phase-1-Debug] 로그가 실시간으로 표시됩니다:

```
[Phase-1-Debug req=sess-abc|survey=surv-001|r1] Model: deepseek-v3-0324
[Phase-1-Debug req=sess-abc|survey=surv-001|r1] Agent input length: 1234
[Phase-1-Debug req=sess-abc|survey=surv-001|r1] Intermediate steps count: 5
[Phase-1-Debug req=sess-abc|survey=surv-001|r1] Parsing succeeded: 5 questions
```

또는 에러 시:

```
[Phase-1-Debug req=sess-def|survey=surv-002|r1] Model: deepseek-v3-0324
[Phase-1-Debug req=sess-def|survey=surv-002|r1] Intermediate steps count: 2
⚠️  Incomplete ReAct response detected
[Phase-1-Debug req=sess-def|survey=surv-002|r1] Parsing failed: JSONDecodeError
```

---

## 🎯 3가지 모델 비교

각 모델에서 동일한 절차 반복:

```bash
# Gemini (외부 개발용 - 참조)
./scripts/run_phase1_test.sh gemini-2.0-flash

# DeepSeek (사내 - 문제 모델)
./scripts/run_phase1_test.sh deepseek-v3-0324

# GPT-OSS (선택사항 - 비교)
./scripts/run_phase1_test.sh gpt-oss-120b
```

---

## 🔍 로그 해석

### 정상 작동 (Gemini)
```
✅ Model: gemini-2.0-flash
✅ Intermediate steps count: 5
✅ Parsing succeeded: 5 questions
```

### 문제 있음 (DeepSeek)
```
⚠️  Model: deepseek-v3-0324
⚠️  Intermediate steps count: 0 (또는 불완전)
❌ Parsing failed: JSONDecodeError
```

### 확인할 핵심 지표
1. **Intermediate steps count**: Tool 호출 횟수 (정상: 5+)
2. **Parsing succeeded/failed**: 최종 결과 (succeeded = 성공)
3. **에러 타입**: JSONDecodeError, KeyError, etc.

---

## 💾 로그 저장 (선택사항)

실시간 출력을 파일로 저장하려면:

```bash
tail -f ~/.local/share/slea-ssem/logs/*.log 2>/dev/null | grep '\[Phase-1-Debug' | tee phase1_deepseek.log
```

---

## 🛠️ 문제 해결

### Q: 로그가 안 보여요
A: LOG_LEVEL이 정확히 설정되었는지 확인
```bash
echo $LOG_LEVEL  # DEBUG여야 함
```

### Q: tail -f가 안 먹혀요
A: 로그 디렉토리 경로 확인
```bash
ls ~/.local/share/slea-ssem/logs/
```

### Q: CLI 프롬프트가 안 나와요
A: `./tools/dev.sh cli`로 직접 실행 (이 스크립트 아님)

---

## 📊 기대 결과

| 모델 | 상태 | 예상 시간 |
|------|------|----------|
| Gemini | ✅ 정상 | ~30초 |
| DeepSeek | ❓ 테스트 필요 | ~30초 |
| GPT-OSS | ❓ 선택사항 | ~30초 |

---

**핵심**: 2개 터미널 분리로 깔끔하고 명확한 테스트 가능 ✨
