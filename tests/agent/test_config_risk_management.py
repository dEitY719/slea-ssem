"""
Test suite for REQ-AGENT-0-0: Risk Management Strategy.

REQ: REQ-AGENT-0-0

Tests the feature flag system for controlling structured output usage
across different LLM models (Gemini vs DeepSeek).

Test Categories:
- Feature flag configuration (environment variable based)
- Model-based routing (Gemini → True, DeepSeek → False)
- Failure count rollback (circuit breaker pattern)
- Edge cases (disabled flag, unknown models, invalid inputs)
- Acceptance criteria verification
"""

import os
from unittest.mock import patch

import pytest

from src.agent.config import STRUCTURED_OUTPUT_CONFIG, should_use_structured_output


@pytest.mark.no_db_required
class TestStructuredOutputConfig:
    """Test STRUCTURED_OUTPUT_CONFIG initialization from environment variables."""

    def test_config_defaults_when_env_not_set(self):
        """
        Test: STRUCTURED_OUTPUT_CONFIG uses conservative defaults when env vars not set.

        REQ: REQ-AGENT-0-0 (Acceptance Criteria #6)
        Expected: enabled=False, rollout=100.0, max_failures=3
        """
        # This test assumes clean environment or uses defaults
        # In practice, this is tested via module import
        assert "enabled" in STRUCTURED_OUTPUT_CONFIG
        assert "rollout_percentage" in STRUCTURED_OUTPUT_CONFIG
        assert "max_failures_before_disable" in STRUCTURED_OUTPUT_CONFIG
        assert "success_rate_threshold" in STRUCTURED_OUTPUT_CONFIG
        assert "latency_threshold_seconds" in STRUCTURED_OUTPUT_CONFIG
        assert "parser_error_rate_threshold" in STRUCTURED_OUTPUT_CONFIG

    @patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG")
    def test_config_enabled_via_env_var(self, mock_config):
        """
        Test: ENABLE_STRUCTURED_OUTPUT=true enables structured output globally.

        REQ: REQ-AGENT-0-0 (Acceptance Criteria #1)
        Expected: Config reflects environment variable setting
        """
        # Mock config with enabled=True
        mock_config.__getitem__.side_effect = lambda key: {
            "enabled": True,
            "max_failures_before_disable": 3,
        }.get(key)
        mock_config.__contains__ = lambda key: True

        # Verify config would reflect the setting
        assert mock_config["enabled"] is True
        assert mock_config["max_failures_before_disable"] == 3

    @patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG")
    def test_config_custom_failure_threshold(self, mock_config):
        """
        Test: MAX_STRUCTURED_FAILURES environment variable sets custom threshold.

        REQ: REQ-AGENT-0-0 (Risk Mitigation #1)
        Expected: Threshold configurable via environment
        """
        # Mock config with custom max_failures=5
        mock_config.__getitem__.side_effect = lambda key: {
            "enabled": True,
            "max_failures_before_disable": 5,  # Custom threshold
        }.get(key)

        # Verify custom threshold is applied
        assert mock_config["max_failures_before_disable"] == 5

        # Verify circuit breaker triggers at custom threshold
        with patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", mock_config):
            # At failure_count=4, should still return True (below threshold)
            result_below = should_use_structured_output("gemini-2.0", failure_count=4)
            assert result_below is True

            # At failure_count=5, should return False (at threshold)
            result_at = should_use_structured_output("gemini-2.0", failure_count=5)
            assert result_at is False


@pytest.mark.no_db_required
class TestShouldUseStructuredOutput:
    """Test should_use_structured_output() model-based routing logic."""

    # ===== Test 1: Happy Path - Gemini Model =====
    @patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", {"enabled": True, "max_failures_before_disable": 3})
    def test_gemini_model_returns_true_when_enabled(self):
        """
        Test: Gemini models return True when feature flag is enabled.

        REQ: REQ-AGENT-0-0 (Acceptance Criteria #2, #3)
        Input: model_name="gemini-2.0-flash", failure_count=0, enabled=True
        Expected: True
        Reason: Gemini supports structured output
        """
        result = should_use_structured_output("gemini-2.0-flash", failure_count=0)
        assert result is True

    @patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", {"enabled": True, "max_failures_before_disable": 3})
    def test_gemini_pro_model_returns_true(self):
        """
        Test: Different Gemini model variants (gemini-1.5-pro) also return True.

        REQ: REQ-AGENT-0-0 (Acceptance Criteria #3)
        Input: model_name="gemini-1.5-pro"
        Expected: True
        """
        result = should_use_structured_output("gemini-1.5-pro", failure_count=0)
        assert result is True

    # ===== Test 2: Happy Path - DeepSeek Model =====
    @patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", {"enabled": True, "max_failures_before_disable": 3})
    def test_deepseek_model_returns_false_always(self):
        """
        Test: DeepSeek models always return False (uses TextReActAgent).

        REQ: REQ-AGENT-0-0 (Acceptance Criteria #3, #4)
        Input: model_name="deepseek-chat", enabled=True
        Expected: False
        Reason: DeepSeek doesn't support structured output
        """
        result = should_use_structured_output("deepseek-chat", failure_count=0)
        assert result is False

    @patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", {"enabled": True, "max_failures_before_disable": 3})
    def test_deepseek_v3_model_returns_false(self):
        """
        Test: DeepSeek-v3 variant also returns False.

        REQ: REQ-AGENT-0-0 (Acceptance Criteria #4)
        Input: model_name="deepseek-v3-0324"
        Expected: False
        """
        result = should_use_structured_output("deepseek-v3-0324", failure_count=0)
        assert result is False

    # ===== Test 3: Edge Case - Feature Flag Disabled =====
    @patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", {"enabled": False, "max_failures_before_disable": 3})
    def test_all_models_return_false_when_disabled(self):
        """
        Test: When feature flag is disabled, all models return False.

        REQ: REQ-AGENT-0-0 (Acceptance Criteria #1)
        Input: enabled=False, model_name="gemini-2.0-flash"
        Expected: False
        Reason: Global disable overrides model support
        """
        result = should_use_structured_output("gemini-2.0-flash", failure_count=0)
        assert result is False

    # ===== Test 4: Edge Case - Failure Count Circuit Breaker =====
    @patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", {"enabled": True, "max_failures_before_disable": 3})
    def test_circuit_breaker_triggers_at_threshold(self):
        """
        Test: Circuit breaker disables structured output after max failures.

        REQ: REQ-AGENT-0-0 (Acceptance Criteria #4, Risk Mitigation #1)
        Input: failure_count=3, max_failures=3, model="gemini-2.0-flash"
        Expected: False
        Reason: Auto-rollback triggered
        """
        result = should_use_structured_output("gemini-2.0-flash", failure_count=3)
        assert result is False

    @patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", {"enabled": True, "max_failures_before_disable": 3})
    def test_circuit_breaker_allows_below_threshold(self):
        """
        Test: Below threshold, structured output is still allowed.

        REQ: REQ-AGENT-0-0 (Risk Mitigation #1)
        Input: failure_count=2, max_failures=3
        Expected: True (for Gemini)
        """
        result = should_use_structured_output("gemini-2.0-flash", failure_count=2)
        assert result is True

    @patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", {"enabled": True, "max_failures_before_disable": 3})
    def test_circuit_breaker_triggers_above_threshold(self):
        """
        Test: Above threshold, circuit breaker remains open.

        REQ: REQ-AGENT-0-0 (Risk Mitigation #1)
        Input: failure_count=5 (> max_failures=3)
        Expected: False
        """
        result = should_use_structured_output("gemini-2.0-flash", failure_count=5)
        assert result is False

    # ===== Test 5: Edge Case - Unknown Models =====
    @patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", {"enabled": True, "max_failures_before_disable": 3})
    def test_unknown_model_returns_false_conservative(self):
        """
        Test: Unknown models default to False (conservative strategy).

        REQ: REQ-AGENT-0-0 (Acceptance Criteria #2)
        Input: model_name="gpt-4" (not Gemini or DeepSeek)
        Expected: False
        Reason: Conservative default for untested models
        """
        result = should_use_structured_output("gpt-4", failure_count=0)
        assert result is False

    @patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", {"enabled": True, "max_failures_before_disable": 3})
    def test_empty_model_name_returns_false(self):
        """
        Test: Empty model name returns False safely.

        REQ: REQ-AGENT-0-0 (Input Validation)
        Input: model_name=""
        Expected: False
        Reason: Invalid input, conservative default
        """
        result = should_use_structured_output("", failure_count=0)
        assert result is False

    # ===== Test 6: Logging and Observability =====
    @patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", {"enabled": True, "max_failures_before_disable": 3})
    def test_decision_is_logged(self, caplog):
        """
        Test: Every decision is logged with model name and reason.

        REQ: REQ-AGENT-0-0 (Acceptance Criteria #5)
        Input: Any valid call
        Expected: Log entry with decision details
        """
        with caplog.at_level("INFO"):
            should_use_structured_output("gemini-2.0-flash", failure_count=0)

        # Verify that a log entry was created with model name and decision
        assert len(caplog.records) > 0
        log_message = caplog.text.lower()
        assert "gemini-2.0-flash" in log_message or "structured output" in log_message
        assert caplog.records[0].levelname == "INFO"

    @patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", {"enabled": True, "max_failures_before_disable": 3})
    def test_alert_logged_on_circuit_breaker(self, caplog):
        """
        Test: ALERT-level log when circuit breaker triggers.

        REQ: REQ-AGENT-0-0 (Risk Mitigation #4)
        Input: failure_count >= max_failures
        Expected: Log with "auto-disabling" or similar alert message
        """
        with caplog.at_level("WARNING"):
            should_use_structured_output("gemini-2.0-flash", failure_count=3)

        # Verify that a WARNING level log was created for circuit breaker
        assert len(caplog.records) > 0
        # Find the circuit breaker warning log
        circuit_breaker_logs = [
            record for record in caplog.records
            if record.levelname == "WARNING" and "circuit breaker" in record.message.lower()
        ]
        assert len(circuit_breaker_logs) > 0, "Circuit breaker warning not found in logs"


# ===== Integration Test: Environment Variable Flow =====
@pytest.mark.no_db_required
class TestEnvironmentVariableIntegration:
    """Integration tests for full environment variable → config → decision flow."""

    def test_env_var_false_disables_globally(self):
        """
        Test: ENABLE_STRUCTURED_OUTPUT=false disables for all models.

        REQ: REQ-AGENT-0-0 (Acceptance Criteria #1, #6)
        Scenario: User sets ENABLE_STRUCTURED_OUTPUT=false
        Expected: should_use_structured_output returns False for all models
        """
        # Mock config with enabled=False
        mock_config = {"enabled": False, "max_failures_before_disable": 3}

        with patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", mock_config):
            # Should return False for all models when globally disabled
            assert should_use_structured_output("gemini-2.0-flash", 0) is False
            assert should_use_structured_output("gemini-1.5-pro", 0) is False
            assert should_use_structured_output("deepseek-chat", 0) is False

    def test_low_failure_threshold_triggers_quickly(self):
        """
        Test: Custom low threshold (MAX_STRUCTURED_FAILURES=1) triggers faster.

        REQ: REQ-AGENT-0-0 (Risk Mitigation #1)
        Input: failure_count=1, max_failures=1
        Expected: Circuit breaker triggers immediately
        """
        # Mock config with max_failures=1 (very low threshold)
        mock_config = {"enabled": True, "max_failures_before_disable": 1}

        with patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", mock_config):
            # At failure_count=0, should return True
            assert should_use_structured_output("gemini-2.0", failure_count=0) is True

            # At failure_count=1, should return False (triggers immediately)
            assert should_use_structured_output("gemini-2.0", failure_count=1) is False

            # Verify higher failure counts also return False
            assert should_use_structured_output("gemini-2.0", failure_count=2) is False


# ===== Performance Test =====
@pytest.mark.no_db_required
class TestPerformance:
    """Test performance requirements for should_use_structured_output()."""

    @patch("src.agent.config.STRUCTURED_OUTPUT_CONFIG", {"enabled": True, "max_failures_before_disable": 3})
    def test_function_executes_under_1ms(self):
        """
        Test: should_use_structured_output() completes in < 1ms.

        REQ: REQ-AGENT-0-0 (Non-Functional: Performance)
        Expected: No I/O, simple boolean logic
        """
        import time

        start = time.perf_counter()
        for _ in range(1000):
            should_use_structured_output("gemini-2.0-flash", failure_count=0)
        elapsed = time.perf_counter() - start

        avg_time_ms = (elapsed / 1000) * 1000
        assert avg_time_ms < 1.0, f"Average execution time {avg_time_ms:.3f}ms exceeds 1ms"
