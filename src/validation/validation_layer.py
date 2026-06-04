# validation_layer.py — Composite Validation Layer VN
# Học từ MediVoice_AI v2.61.3 | Adapted cho thị trường VN
# ISO/IEC 42001:2023 Cl.6.1 + 8.5 + 9.1
# "Hệ miễn dịch" của AI Governance VN
# v1.0 | 2026-06-04

from __future__ import annotations
import time
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from .rule_engine import RuleEngine, ValidationReport
from .anomaly_detector import AnomalyDetector, AnomalyReport

logger = logging.getLogger(__name__)


@dataclass
class LayerResult:
    """Kết quả validation đầy đủ cho một stage."""
    stage: str
    phase: str                    # "pre" | "post"
    can_proceed: bool
    rule_report: ValidationReport | None = None
    anomaly_report: AnomalyReport | None = None
    escalate_to_human: bool = False
    escalation_reasons: list[str] = field(default_factory=list)
    total_time_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "stage": self.stage, "phase": self.phase,
            "can_proceed": self.can_proceed,
            "escalate_to_human": self.escalate_to_human,
            "escalation_reasons": self.escalation_reasons,
            "total_time_ms": round(self.total_time_ms, 2),
            "rule": self.rule_report.to_dict() if self.rule_report else None,
            "anomaly": self.anomaly_report.to_dict() if self.anomaly_report else None,
        }


class ValidationLayer:
    """
    Validation Layer VN — chạy ĐỘC LẬP song song với pipeline.

    PRE-execution:  RuleEngine (deterministic checks)
    POST-execution: RuleEngine (output check) + AnomalyDetector (drift)

    ESCALATION → BS khi:
    - CRITICAL rule violation
    - Critical anomaly (latency hoặc error rate)
    - CCP stage (L4_HUMAN_GATE, L6_FORM_GENERATOR)

    ISO/IEC 42001:2023 Cl.6.1 + 8.5 + 9.1
    """

    # Critical Control Points VN
    CCPS = {"L4_HUMAN_GATE", "L6_FORM_GENERATOR"}

    def __init__(
        self,
        rule_engine: RuleEngine | None = None,
        anomaly_detector: AnomalyDetector | None = None,
        escalation_callback: Callable | None = None,
    ):
        self.rule_engine = rule_engine or RuleEngine()
        self.anomaly_detector = anomaly_detector or AnomalyDetector()
        self.escalation_callback = escalation_callback
        self._results: list[LayerResult] = []

    def validate_pre(self, stage: str, fn: Any) -> LayerResult:
        """Pre-execution: chỉ RuleEngine."""
        t = time.perf_counter()
        result = LayerResult(stage=stage, phase="pre", can_proceed=True)
        reasons = []

        rule = self.rule_engine.validate(stage, None, phase="pre")
        result.rule_report = rule
        if not rule.passed:
            result.can_proceed = False
            for v in rule.blocking_violations:
                reasons.append(f"Rule [{v.rule_id}/{v.severity}]: {v.message}")

        result = self._check_escalation(result, stage, reasons)
        result.total_time_ms = (time.perf_counter() - t) * 1000
        self._results.append(result)
        return result

    def validate_post(self, stage: str, input_payload: Any,
                      output_payload: Any, execution_time_ms: float,
                      stage_ok: bool) -> LayerResult:
        """Post-execution: RuleEngine + AnomalyDetector."""
        t = time.perf_counter()
        result = LayerResult(stage=stage, phase="post", can_proceed=True)
        reasons = []

        # Rule check
        rule = self.rule_engine.validate(stage, output_payload, phase="post")
        result.rule_report = rule
        if rule.has_critical:
            reasons.append(f"CRITICAL rule violation: {[v.rule_id for v in rule.violations if v.severity=='CRITICAL']}")

        # Anomaly detection
        anomaly = self.anomaly_detector.detect(
            stage=stage,
            execution_time_ms=execution_time_ms,
            payload_size=len(str(output_payload)) if output_payload else 0,
            ok=stage_ok,
        )
        result.anomaly_report = anomaly
        if anomaly.severity == "CRITICAL":
            reasons.append(f"CRITICAL anomaly: {[a.metric for a in anomaly.anomalies]}")
        elif anomaly.severity == "HIGH":
            logger.warning(f"[{stage}] HIGH anomaly: {anomaly.to_dict()}")

        result = self._check_escalation(result, stage, reasons)
        result.total_time_ms = (time.perf_counter() - t) * 1000
        self._results.append(result)
        return result

    def _check_escalation(self, result: LayerResult, stage: str,
                           reasons: list[str]) -> LayerResult:
        if not reasons:
            return result

        result.escalation_reasons = reasons
        is_ccp = stage in self.CCPS
        should_escalate = is_ccp or any("CRITICAL" in r.upper() for r in reasons)

        if should_escalate:
            result.escalate_to_human = True
            logger.warning(f"[{stage}] ESCALATE → BS: {reasons}")
            if self.escalation_callback:
                approved = self.escalation_callback(stage, reasons)
                result.can_proceed = approved

        return result

    def get_run_summary(self) -> dict:
        total = len(self._results)
        failed = sum(1 for r in self._results if not r.can_proceed)
        escalated = sum(1 for r in self._results if r.escalate_to_human)
        return {
            "total_validations": total,
            "passed": total - failed,
            "failed": failed,
            "escalated_to_human": escalated,
            "results": [r.to_dict() for r in self._results],
        }

    def reset(self) -> None:
        self._results = []
