"""
Tests for src/core/l8_error_handler.py
@verifies GAP-003 | P0.2.L8
"""
from __future__ import annotations
import sys
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from core.l8_error_handler import (
    PipelineError,
    PipelineErrorCode,
    with_recovery,
    safe_log,
)


# ── PipelineErrorCode ─────────────────────────────────────────────

class TestPipelineErrorCode:
    def test_all_expected_codes_exist(self):
        codes = {e.value for e in PipelineErrorCode}
        expected = {
            "ASR_FAILED", "NER_FAILED", "ICD_NOT_FOUND", "VALIDATION_FAILED",
            "STORAGE_FAILED", "PDF_FAILED", "AUDIT_FAILED", "L4_NOT_APPROVED",
        }
        assert expected.issubset(codes)

    def test_code_is_str(self):
        assert isinstance(PipelineErrorCode.ASR_FAILED, str)
        assert PipelineErrorCode.ASR_FAILED == "ASR_FAILED"


# ── PipelineError ─────────────────────────────────────────────────

class TestPipelineError:
    def test_attributes_set(self):
        err = PipelineError(PipelineErrorCode.NER_FAILED, "bad NER", layer="L1c")
        assert err.code == PipelineErrorCode.NER_FAILED
        assert err.layer == "L1c"

    def test_message_includes_code_and_layer(self):
        err = PipelineError(PipelineErrorCode.PDF_FAILED, "no reportlab", layer="L9a")
        msg = str(err)
        assert "L9a" in msg
        assert "PDF_FAILED" in msg

    def test_is_exception(self):
        err = PipelineError(PipelineErrorCode.AUDIT_FAILED, "hash mismatch")
        assert isinstance(err, Exception)

    def test_empty_layer_allowed(self):
        err = PipelineError(PipelineErrorCode.ASR_FAILED, "timeout")
        assert err.layer == ""


# ── with_recovery ─────────────────────────────────────────────────

class TestWithRecovery:
    def test_happy_path_returns_value(self):
        @with_recovery("L1a")
        def fn():
            return 42

        assert fn() == 42

    def test_happy_path_passes_args(self):
        @with_recovery("L2")
        def add(a, b):
            return a + b

        assert add(3, 4) == 7

    def test_pipeline_error_is_reraised(self):
        @with_recovery("L5", fallback="safe")
        def fn():
            raise PipelineError(PipelineErrorCode.STORAGE_FAILED, "disk full", layer="L7")

        with pytest.raises(PipelineError) as exc_info:
            fn()
        assert exc_info.value.code == PipelineErrorCode.STORAGE_FAILED

    def test_generic_exception_with_callable_fallback(self):
        @with_recovery("L1b", fallback=list)
        def fn():
            raise ValueError("oops")

        result = fn()
        assert result == []

    def test_generic_exception_with_static_fallback(self):
        @with_recovery("L1c", fallback="")
        def fn():
            raise RuntimeError("fail")

        assert fn() == ""

    def test_generic_exception_with_none_fallback_raises_pipeline_error(self):
        @with_recovery("L3")
        def fn():
            raise KeyError("missing key")

        with pytest.raises(PipelineError) as exc_info:
            fn()
        assert exc_info.value.code == PipelineErrorCode.VALIDATION_FAILED
        assert exc_info.value.layer == "L3"

    def test_generic_exception_logged(self, caplog):
        @with_recovery("L2", fallback=None)
        def fn():
            raise TypeError("type mismatch")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(PipelineError):
                fn()
        assert any("L2" in r.message for r in caplog.records)

    def test_fallback_zero_is_returned(self):
        @with_recovery("L0", fallback=0)
        def fn():
            raise Exception("boom")

        assert fn() == 0

    def test_preserves_function_name(self):
        @with_recovery("L4")
        def my_special_function():
            return True

        assert my_special_function.__name__ == "my_special_function"


# ── safe_log ──────────────────────────────────────────────────────

class TestSafeLog:
    def test_happy_path_returns_value(self):
        @safe_log
        def log_it(x):
            return x * 2

        assert log_it(5) == 10

    def test_exception_is_swallowed(self):
        @safe_log
        def fn():
            raise RuntimeError("audit DB down")

        result = fn()
        assert result is None

    def test_exception_logged_as_critical(self, caplog):
        @safe_log
        def fn():
            raise OSError("disk full")

        with caplog.at_level(logging.CRITICAL):
            fn()
        assert any("AUDIT LOG FAILED" in r.message for r in caplog.records)

    def test_preserves_function_name(self):
        @safe_log
        def audit_write():
            pass

        assert audit_write.__name__ == "audit_write"

    def test_does_not_reraise_pipeline_error(self):
        @safe_log
        def fn():
            raise PipelineError(PipelineErrorCode.AUDIT_FAILED, "chain broken")

        result = fn()
        assert result is None
