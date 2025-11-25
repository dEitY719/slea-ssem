# Phase 2: Test Design - REQ-B-A2-Avail-2

## Test Case Design

**REQ ID**: REQ-B-A2-Avail-2
**Feature**: Nickname Validation with Unicode/Special Character Support
**Test File**: `/home/bwyoon/para/project/slea-ssem/tests/backend/test_nickname_validator.py`

---

## Test Cases Overview

| TC# | Name | Category | Input | Expected Outcome |
|-----|------|----------|-------|------------------|
| TC-1 | Valid nickname - single character | Happy Path | "a" | Valid (length=1) |
| TC-2 | Valid nickname - mixed chars | Happy Path | "john_doe" | Valid |
| TC-3 | Valid nickname - Korean | Happy Path | "김철수" | Valid |
| TC-4 | Valid nickname - Unicode emoji | Happy Path | "😊user" | Valid |
| TC-5 | Valid nickname - special chars | Happy Path | "alice@home" | Valid |
| TC-6 | Invalid - empty string | Input Validation | "" | Invalid, length error |
| TC-7 | Invalid - too long | Input Validation | "a"*31 | Invalid, length error |
| TC-8 | Invalid - forbidden word exact | Forbidden Words | "admin" | Invalid, forbidden word |
| TC-9 | Invalid - forbidden word prefix | Forbidden Words | "admin123" | Invalid, forbidden word |
| TC-10 | Invalid - system keyword | Forbidden Words | "system" | Invalid, forbidden word |
| TC-11 | Valid - 30 chars max | Edge Case | "a"*30 | Valid |
| TC-12 | Valid - all special chars | Edge Case | "@#$%^" | Valid |
| TC-13 | Valid - mixed Unicode | Edge Case | "user_😊_名" | Valid |
| TC-14 | Error helper method | Helper | various | Correct error messages |

---

## Test Case Definitions

### TC-1: Valid Single Character
```python
def test_valid_nickname_single_character() -> None:
    """Happy path: Single character nickname (length=1, new minimum)."""
    is_valid, error = NicknameValidator.validate("a")
    assert is_valid is True
    assert error is None
```

### TC-2: Valid Mixed Characters (English, Numbers, Underscore)
```python
def test_valid_nickname_mixed_chars() -> None:
    """Happy path: Valid nickname with letters, numbers, underscore."""
    is_valid, error = NicknameValidator.validate("john_doe_123")
    assert is_valid is True
    assert error is None

    is_valid, error = NicknameValidator.validate("alice_bob")
    assert is_valid is True
    assert error is None
```

### TC-3: Valid Korean Characters
```python
def test_valid_nickname_korean() -> None:
    """Happy path: Korean characters allowed (REQ-B-A2-Avail-2)."""
    is_valid, error = NicknameValidator.validate("김철수")
    assert is_valid is True
    assert error is None

    is_valid, error = NicknameValidator.validate("이영희")
    assert is_valid is True
    assert error is None
```

### TC-4: Valid Unicode Emoji
```python
def test_valid_nickname_unicode_emoji() -> None:
    """Happy path: Unicode emoji characters allowed (REQ-B-A2-Avail-2)."""
    is_valid, error = NicknameValidator.validate("😊user")
    assert is_valid is True
    assert error is None

    is_valid, error = NicknameValidator.validate("user🎉")
    assert is_valid is True
    assert error is None
```

### TC-5: Valid Special Characters
```python
def test_valid_nickname_special_chars() -> None:
    """Happy path: Special characters allowed (REQ-B-A2-Avail-2)."""
    is_valid, error = NicknameValidator.validate("alice@home")
    assert is_valid is True
    assert error is None

    is_valid, error = NicknameValidator.validate("user#2024")
    assert is_valid is True
    assert error is None

    is_valid, error = NicknameValidator.validate("john-doe")
    assert is_valid is True
    assert error is None
```

### TC-6: Invalid - Empty String
```python
def test_nickname_empty_string() -> None:
    """Input validation: Empty string rejected."""
    is_valid, error = NicknameValidator.validate("")
    assert is_valid is False
    assert "at least 1 character" in error
```

### TC-7: Invalid - Too Long (31+ chars)
```python
def test_nickname_too_long() -> None:
    """Input validation: Nickname > 30 chars."""
    is_valid, error = NicknameValidator.validate("a" * 31)
    assert is_valid is False
    assert "at most 30 characters" in error
```

### TC-8: Invalid - Forbidden Word Exact Match
```python
def test_nickname_forbidden_word_exact() -> None:
    """REQ-B-A2-Avail-2 & REQ-B-A2-Avail-4: Forbidden words rejected (exact match)."""
    is_valid, error = NicknameValidator.validate("admin")
    assert is_valid is False
    assert "prohibited word" in error

    is_valid, error = NicknameValidator.validate("system")
    assert is_valid is False
    assert "prohibited word" in error

    is_valid, error = NicknameValidator.validate("root")
    assert is_valid is False
    assert "prohibited word" in error
```

### TC-9: Invalid - Forbidden Word Prefix
```python
def test_nickname_forbidden_word_prefix() -> None:
    """REQ-B-A2-Avail-4: Forbidden words rejected (prefix match)."""
    is_valid, error = NicknameValidator.validate("admin123")
    assert is_valid is False
    assert "prohibited word" in error

    is_valid, error = NicknameValidator.validate("system_user")
    assert is_valid is False
    assert "prohibited word" in error
```

### TC-10: Invalid - System Keyword with Unicode
```python
def test_nickname_forbidden_word_with_unicode() -> None:
    """REQ-B-A2-Avail-4: Forbidden words rejected even with Unicode suffix."""
    is_valid, error = NicknameValidator.validate("admin_😊")
    assert is_valid is False
    assert "prohibited word" in error
```

### TC-11: Valid - Maximum Length (30 chars)
```python
def test_valid_nickname_max_length() -> None:
    """Edge case: Valid at maximum length (30 chars)."""
    is_valid, error = NicknameValidator.validate("a" * 30)
    assert is_valid is True
    assert error is None
```

### TC-12: Valid - All Special Characters
```python
def test_valid_nickname_all_special_chars() -> None:
    """Edge case: Special-character-only nickname."""
    is_valid, error = NicknameValidator.validate("@#$%")
    assert is_valid is True
    assert error is None
```

### TC-13: Valid - Mixed Unicode
```python
def test_valid_nickname_mixed_unicode() -> None:
    """Edge case: Mixed Unicode characters (Korean, emoji, English)."""
    is_valid, error = NicknameValidator.validate("user_😊_名前")
    assert is_valid is True
    assert error is None
```

### TC-14: Error Helper Method
```python
def test_get_validation_error_message() -> None:
    """REQ-B-A2-Avail-4: Get error message helper works correctly."""
    # Invalid: too short
    error_msg = NicknameValidator.get_validation_error("")
    assert error_msg is not None
    assert "at least 1 character" in error_msg

    # Invalid: forbidden word
    error_msg = NicknameValidator.get_validation_error("admin")
    assert error_msg is not None
    assert "prohibited word" in error_msg

    # Valid
    error_msg = NicknameValidator.get_validation_error("john_doe")
    assert error_msg is None
```

---

## Backward Compatibility Tests

```python
def test_backward_compatibility_existing_valid_nicknames() -> None:
    """Verify existing valid nicknames still work (backward compatibility)."""
    # These were valid before and should still be valid
    is_valid, error = NicknameValidator.validate("john_doe")
    assert is_valid is True

    is_valid, error = NicknameValidator.validate("alice123")
    assert is_valid is True
```

---

## Test Summary

- **Total Test Cases**: 14 main + backward compatibility checks
- **Categories**:
  - Happy Path (Valid): 5 cases (single char, mixed, Korean, emoji, special)
  - Input Validation: 2 cases (empty, too long)
  - Forbidden Words: 3 cases (exact, prefix, Unicode)
  - Edge Cases: 3 cases (max length, all special, mixed Unicode)
  - Helper Methods: 1 case (error message)
  - Backward Compatibility: 1 case

- **Coverage**:
  - Length validation: MIN=1, MAX=30
  - Character types: ASCII, Unicode, Korean, emoji, special chars
  - Forbidden words: exact match, prefix match, with Unicode
  - Error messages: all validation paths

---

## Test File Location

**File**: `/home/bwyoon/para/project/slea-ssem/tests/backend/test_nickname_validator.py`

**Command to Run Tests**:
```bash
pytest tests/backend/test_nickname_validator.py -v
```

---

## Ready for Phase 3?

**Test Design Status**: COMPLETE

All test cases defined and ready for implementation. Tests will verify:
1. New minimum length (1 character)
2. New maximum length (30 characters)
3. Unicode and special character support
4. Forbidden words filtering
5. Error messages clarity

Proceed to Phase 3 (Implementation)? **[YES needed from user]**
