"""
Tests for ValidationLayer VN.
@verifies SRS-L2-003, SRS-L1b-002, SRS-L4-003
"""
import pytest
from src.validation.rule_engine import RuleEngine, Violation
from src.validation.anomaly_detector import AnomalyDetector
from src.validation.validation_layer import ValidationLayer, LayerResult


class TestRuleEngine:
    def test_pre_rules_pass_for_normal_stage(self):
        engine = RuleEngine()
        report = engine.validate("L2_VALIDATE", None, phase="pre")
        assert report.passed is True
        assert len(report.violations) == 0

    def test_post_rules_flag_translated_drug_names(self):
        engine = RuleEngine()
        # L1b output with translated drug name — CRITICAL violation
        bad_output = "thuốc hạ sốt 500mg 2 viên"
        report = engine.validate("L1b_DRUG_CORRECT", bad_output, phase="post")
        assert not report.passed
        critical = [v for v in report.violations if v.severity == "CRITICAL"]
        assert len(critical) > 0

    def test_post_rules_pass_for_correct_inn(self):
        engine = RuleEngine()
        good_output = "Paracetamol 500mg 2 viên"
        report = engine.validate("L1b_DRUG_CORRECT", good_output, phase="post")
        assert report.passed is True

    def test_post_rules_flag_low_confidence(self):
        engine = RuleEngine()
        low_conf = ({}, {}, 0.1)  # tuple from l2_validate
        report = engine.validate("L2_VALIDATE", low_conf, phase="post")
        medium = [v for v in report.violations if v.severity == "MEDIUM"]
        assert len(medium) > 0

    def test_has_critical_property(self):
        engine = RuleEngine()
        report = engine.validate("L1b_DRUG_CORRECT", "thuốc hạ sốt", phase="post")
        assert report.has_critical is True

    def test_blocking_violations_filter(self):
        engine = RuleEngine()
        report = engine.validate("L1b_DRUG_CORRECT", "thuốc hạ sốt", phase="post")
        blocking = report.blocking_violations
        assert all(v.severity in ("CRITICAL", "HIGH") for v in blocking)


class TestAnomalyDetector:
    def test_normal_latency_no_anomaly(self):
        detector = AnomalyDetector()
        report = detector.detect("L3_ROUTE", execution_time_ms=20.0, ok=True)
        assert report.severity == "INFO"
        assert len(report.anomalies) == 0

    def test_high_latency_triggers_anomaly(self):
        detector = AnomalyDetector()
        report = detector.detect("L3_ROUTE", execution_time_ms=200.0, ok=True)
        assert report.severity in ("MEDIUM", "HIGH")
        assert len(report.anomalies) > 0

    def test_critical_latency(self):
        detector = AnomalyDetector()
        report = detector.detect("L3_ROUTE", execution_time_ms=500.0, ok=True)
        assert report.severity in ("HIGH", "CRITICAL")

    def test_error_rate_tracking(self):
        detector = AnomalyDetector()
        # Simulate 6 consecutive failures
        for _ in range(6):
            detector.detect("L2_VALIDATE", execution_time_ms=50.0, ok=False)
        report = detector.detect("L2_VALIDATE", execution_time_ms=50.0, ok=False)
        assert report.severity in ("HIGH", "CRITICAL")

    def test_to_dict_format(self):
        detector = AnomalyDetector()
        report = detector.detect("L0_NORMALIZE", 100.0)
        d = report.to_dict()
        assert "stage" in d
        assert "severity" in d
        assert "anomalies" in d


class TestValidationLayer:
    def test_validate_pre_returns_layer_result(self):
        vl = ValidationLayer()
        result = vl.validate_pre("L2_VALIDATE", lambda: None)
        assert isinstance(result, LayerResult)
        assert result.stage == "L2_VALIDATE"
        assert result.phase == "pre"

    def test_validate_pre_can_proceed_for_normal(self):
        vl = ValidationLayer()
        result = vl.validate_pre("L3_ROUTE", lambda: None)
        assert result.can_proceed is True

    def test_validate_post_returns_layer_result(self):
        vl = ValidationLayer()
        result = vl.validate_post("L3_ROUTE", None, "lam_sang", 10.0, True)
        assert isinstance(result, LayerResult)
        assert result.phase == "post"

    def test_validate_post_normal_output_passes(self):
        vl = ValidationLayer()
        result = vl.validate_post("L3_ROUTE", None, "lam_sang", 10.0, True)
        assert result.can_proceed is True
        assert result.escalate_to_human is False

    def test_escalation_for_critical_drug_violation(self):
        escalated = []

        def callback(stage, reasons):
            escalated.append((stage, reasons))
            return True  # approved

        vl = ValidationLayer(escalation_callback=callback)
        vl.validate_post("L1b_DRUG_CORRECT", None, "thuốc hạ sốt", 10.0, True)
        assert len(escalated) > 0

    def test_get_run_summary(self):
        vl = ValidationLayer()
        vl.validate_pre("L0_NORMALIZE", lambda: None)
        vl.validate_post("L0_NORMALIZE", None, "OK", 100.0, True)
        summary = vl.get_run_summary()
        assert "total_validations" in summary
        assert summary["total_validations"] == 2

    def test_reset_clears_results(self):
        vl = ValidationLayer()
        vl.validate_pre("L0_NORMALIZE", lambda: None)
        vl.reset()
        summary = vl.get_run_summary()
        assert summary["total_validations"] == 0

    def test_layer_result_to_dict(self):
        vl = ValidationLayer()
        result = vl.validate_pre("L2_VALIDATE", lambda: None)
        d = result.to_dict()
        assert "stage" in d
        assert "phase" in d
        assert "can_proceed" in d
