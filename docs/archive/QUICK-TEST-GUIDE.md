# Quick Test Guide - Answer Schema Fix Verification

**Purpose**: Verify that the critical answer_schema mismatch fix works end-to-end.

**Duration**: ~2 minutes

---

## Test Scenario 1: Verify Adaptive Question Generation (New Schema Format)

```bash
# Start interactive CLI
./tools/dev.sh cli

# Login
> auth login [your-username]

# Generate adaptive questions (uses MOCK_QUESTIONS with legacy format)
> questions generate adaptive --count 3

# Expected Output:
# ✓ 3 questions generated
# ✓ Each question has:
#   - question_id
#   - stem (question text)
#   - choices (answer options)
#   - answer_schema with STANDARD format:
#     * "type": "exact_match" or "keyword_match"
#     * "correct_answer": "B" (NOT "correct_key")
#     * "keywords": null or [list]
```

**Success Criteria**:

- ✅ answer_schema contains "type" field
- ✅ answer_schema contains "correct_answer" field (NOT "correct_key")
- ✅ No Pydantic validation errors
- ✅ No "KeyError: correct_answer" errors

---

## Test Scenario 2: Verify Scoring Works (Not 0 Points)

```bash
# In same CLI session, take the test
> questions solve

# Answer each question:
# 1. First question: Choose option B (or appropriate answer)
# 2. Second question: Answer with T or F
# 3. Third question: Enter short answer

# After answering all questions, quit
# Expected output: Answers auto-saved

# Now score the answers
> questions score

# Expected Output:
# ✓ Score results shown
# ✓ Score is NOT 0 (should be 0-100 based on correctness)
# ✓ Each question has a score breakdown
```

**Success Criteria**:

- ✅ Scoring completes without errors
- ✅ Score is NOT all 0 points
- ✅ Scores reflect correct vs incorrect answers
- ✅ No "type should be string" validation errors

---

## Test Scenario 3: Verify Standard Generation Still Works

```bash
# Generate standard questions (uses Agent/Tool 5)
> questions generate --count 3

# Expected Output:
# ✓ 3 questions generated
# ✓ Same answer_schema structure as adaptive:
#   * "type": "exact_match"
#   * "correct_answer": "string"
#   * "keywords": null
```

**Success Criteria**:

- ✅ Standard and adaptive questions have IDENTICAL answer_schema format
- ✅ Both can be scored using same service
- ✅ No format differences between modes

---

## Test Scenario 4: Database Format Verification (Optional)

If you have database access:

```sql
-- Check generated questions
SELECT id, stem, answer_schema
FROM questions
ORDER BY created_at DESC
LIMIT 5;

-- Expected answer_schema format for ALL rows:
-- {"type": "exact_match", "keywords": null, "correct_answer": "..."}
--
-- NOT:
-- {"correct_key": "B", "explanation": "..."}
```

---

## Expected Data Format Changes

### Before Fix (Broken)

```json
{
  "answer_schema": {
    "correct_key": "B",
    "explanation": "The LLM explanation..."
  }
}
```

### After Fix (Correct)

```json
{
  "answer_schema": {
    "type": "exact_match",
    "keywords": null,
    "correct_answer": "B"
  }
}
```

---

## Troubleshooting

### Issue 1: "Pydantic validation error for type"

**Cause**: answer_schema still has old format
**Solution**: Verify code is at commit 99303af or later

```bash
git log --oneline -1  # Should show "fix: Normalize answer_schema..."
```

### Issue 2: "Scoring returns 0 points for all questions"

**Cause**: answer_schema "correct_answer" field not found
**Solution**: Check database contains normalized schema

```sql
SELECT answer_schema FROM questions LIMIT 1;
-- Should contain "correct_answer" field
```

### Issue 3: "questions generate adaptive hangs"

**Cause**: MOCK_QUESTIONS normalization not working
**Solution**: Restart CLI and try again

```bash
./tools/dev.sh cli
auth login ...
questions generate adaptive --count 1
```

---

## Success Checklist

After running all tests, verify:

- [ ] Test 1: Adaptive generates with standard answer_schema format
- [ ] Test 2: Scoring returns non-zero scores
- [ ] Test 3: Standard generation uses same format as adaptive
- [ ] Test 4 (optional): Database shows standard schema format
- [ ] No validation errors in any test
- [ ] Both generation paths produce identical schema

**Result**: ✅ ALL TESTS PASS = Fix is working!

---

## Related Documentation

- **Full Fix Details**: `docs/FIX-VERIFICATION-SUMMARY.md`
- **Root Cause Analysis**: `docs/ANSWER-SCHEMA-MISMATCH-ANALYSIS.md`
- **Code Locations**:
  - Service normalization: `src/backend/services/question_gen_service.py:250-315`
  - Agent normalization: `src/agent/llm_agent.py:120-167`
  - Applied in adaptive: `src/backend/services/question_gen_service.py:706-709`

---

**Last Updated**: 2025-11-18
**Status**: Ready for testing
