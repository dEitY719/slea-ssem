# Phase 1: Specification - REQ-B-A2-Avail-2

## Overview

**REQ ID**: REQ-B-A2-Avail-2
**Title**: Nickname Validation (닉네임 유효성 검사)
**Priority**: Medium (M)
**Status**: Specification Phase

---

## Requirement Summary

Implement nickname validation that supports:
- **Length**: 1-30 characters (previously was 3-30)
- **Character support**: Korean/English/Numbers/Unicode/Special characters (previously: alphanumeric + underscore only)
- **Forbidden words filter**: Reject reserved/prohibited nicknames

**Source**: `docs/feature_requirement_mvp1.md` line 722

---

## Intent

Update the `NicknameValidator` class to enforce flexible, inclusive nickname rules while maintaining security through forbidden word filtering.

---

## Location

**File**: `/home/bwyoon/para/project/slea-ssem/src/backend/validators/nickname.py`

**Usage**:
- Used by `ProfileService` in `/home/bwyoon/para/project/slea-ssem/src/backend/services/profile_service.py`
- Tests in `/home/bwyoon/para/project/slea-ssem/tests/backend/test_nickname_validator.py`

---

## Signature

```python
class NicknameValidator:
    MIN_LENGTH = 1        # CHANGED: was 3
    MAX_LENGTH = 30       # CHANGED: was 20 (now same as requirement)

    @classmethod
    def validate(cls, nickname: str) -> tuple[bool, str | None]:
        """
        Validate nickname format and content.

        Args:
            nickname: Nickname to validate

        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, error_message) if invalid
        """

    @classmethod
    def get_validation_error(cls, nickname: str) -> str | None:
        """Get validation error message for nickname."""
```

---

## Behavior

### 1. Length Validation
- **Valid**: 1-30 characters (inclusive)
- **Invalid**: < 1 char or > 30 chars
- **Error messages**:
  - "Nickname must be at least 1 character long."
  - "Nickname must be at most 30 characters long."

### 2. Character Support
- **Allow ALL**: Unicode characters, special characters, Korean, English, numbers
  - Examples: "김철수", "John_Doe", "alice@home", "user#2024", "😊user", etc.
- **Remove**: Regex check for `^[a-zA-Z0-9_]+$` (currently too restrictive)
- **Note**: No character restrictions beyond length + forbidden words

### 3. Forbidden Words Filter
- **List**: admin, administrator, system, root, moderator, mod, staff, support, bot, service, account, user, test, temp, guest, anonymous
- **Behavior**:
  - Exact match (case-insensitive): "admin" → REJECT
  - Prefix match: "admin123" → REJECT
  - But allow if forbidden word is substring but not prefix: "my_admin" → might REJECT (need to decide)
  - Current implementation rejects if forbidden word is at start

### 4. Error Messages
- Clear, specific error message for each validation failure
- Include reason (length, forbidden word, etc.)

---

## Dependencies

**Required**:
- Python standard library: `re` (for any regex if needed)
- No external dependencies

**Related**:
- `ProfileService` calls `NicknameValidator.validate()` to check nicknames
- Database: `users.nickname` field (UNIQUE constraint)

---

## Acceptance Criteria

- [ ] MIN_LENGTH changed from 3 to 1
- [ ] MAX_LENGTH verified as 30
- [ ] Regex pattern removed or updated to allow all Unicode/special characters
- [ ] All validation tests pass
- [ ] Forbidden words filter maintains current behavior
- [ ] Error messages are clear and specific
- [ ] No breaking changes to `validate()` and `get_validation_error()` method signatures
- [ ] Backward compatible with existing ProfileService usage

---

## Non-Functional Requirements

- **Performance**: Validation should complete in < 1ms (negligible)
- **Type Safety**: Strict type hints throughout
- **Code Quality**: Pass ruff, black, mypy, pylint checks

---

## Changes Summary

### Current Implementation Issues
1. **MIN_LENGTH = 3** → Should be **1**
2. **Regex `^[a-zA-Z0-9_]+$`** → Too restrictive, should allow all characters
3. **MAX_LENGTH = 20** → Requirement says 30 (verify if already correct)

### Required Changes
```python
# CHANGE 1: Update MIN_LENGTH
MIN_LENGTH = 1  # was 3

# CHANGE 2: Remove restrictive regex or replace with length-only validation
# OLD: if not re.match(r"^[a-zA-Z0-9_]+$", nickname):
# NEW: Remove this check (allow all characters)

# Keep forbidden words check as-is
```

---

## Notes

- Recent commit (b3c1611) updated requirements to be more inclusive
- Unicode support is a deliberate design choice for international users
- Special character support enables creative nicknames
- Forbidden words filter prevents system/admin keyword abuse

---

## Ready for Phase 2?

**Specification Status**: COMPLETE

Key changes needed:
1. Update MIN_LENGTH from 3 to 1
2. Remove or relax regex to allow all Unicode characters
3. Keep forbidden words filtering logic
4. Update tests to verify new behavior

Proceed to Phase 2 (Test Design)? **[YES/NO needed from user]**
