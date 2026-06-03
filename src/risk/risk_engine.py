"""
MediVoice VN — Risk Engine
ISO 31000:2018 (Risk Management) | NIST AI RMF 1.0
Luật AI 134/2025 — High-Risk AI system risk management

Adapted from MediVoice AI (Canada) src/risk/risk_engine.py
VN changes:
  - Vietnamese stage names
  - VN medical domain risk weights
  - Removed PIPEDA-specific risks, added NĐ13/2023
  - Luật AI 134/2025 conformity tracking

NIST AI RMF Phases: GOVERN → MAP → MEASURE → MANAGE
Risk scale: LOW (0-3) | MEDIUM (3-6) | HIGH (6-9) | CRITICAL (9+)
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StageRisk:
    """Trạng thái rủi ro của một pipeline stage."""
    stage: str
    base_risk: float        # Rủi ro cơ bản (0-10)
    failure_multiplier: float  # Hệ số khi stage fail (1.0 = no change)
    current_risk: float = 0.0
    failed: bool = False
    risk_reason: str = ""

    def compute(self) -> float:
        """Tính rủi ro thực tế."""
        if self.failed:
            self.current_risk = min(self.base_risk * self.failure_multiplier, 10.0)
        else:
            self.current_risk = 0.0
        return self.current_risk

    @property
    def severity(self) -> str:
        r = self.current_risk
        if r < 3:   return "LOW"
        if r < 6:   return "MEDIUM"
        if r < 9:   return "HIGH"
        return "CRITICAL"


@dataclass
class RiskSummary:
    """Tổng hợp rủi ro toàn pipeline."""
    total_risk: float
    severity: str
    blocking_stages: list[str]
    stage_risks: dict[str, float]
    compliant: bool
    notes: list[str]


# ── VN Medical Domain Risk Weights ────────────────────────────────────────────
# Căn cứ: Luật AI 134/2025 (high-risk AI) + IMPACT_ASSESSMENT.md
VN_STAGE_RISKS = {
    # Rủi ro cao: sai tên thuốc/liều → hại bệnh nhân
    "L1b_DRUG_CORRECT":    StageRisk("L1b_DRUG_CORRECT",    base_risk=8.0, failure_multiplier=2.0),
    # Rủi ro cao: sai chẩn đoán ICD
    "L1d_ICD_LOOKUP":      StageRisk("L1d_ICD_LOOKUP",      base_risk=6.0, failure_multiplier=1.5),
    # Rủi ro CRITICAL: bypass L4 = vi phạm pháp lý
    "L4_HUMAN_GATE":       StageRisk("L4_HUMAN_GATE",       base_risk=9.5, failure_multiplier=3.0),
    # Rủi ro cao: PII lọt ra ngoài
    "L5_PII_SCAN":         StageRisk("L5_PII_SCAN",         base_risk=7.0, failure_multiplier=2.5),
    # Rủi ro cao: audit log bị compromise
    "L10_AUDIT_LOG":       StageRisk("L10_AUDIT_LOG",       base_risk=8.0, failure_multiplier=2.0),
    # Rủi ro thấp: normalize audio
    "L0_NORMALIZE":        StageRisk("L0_NORMALIZE",         base_risk=2.0, failure_multiplier=1.0),
    # Rủi ro trung bình: ASR
    "L1a_ASR":             StageRisk("L1a_ASR",              base_risk=4.0, failure_multiplier=1.5),
    # Rủi ro trung bình: NER
    "L1c_NER":             StageRisk("L1c_NER",              base_risk=5.0, failure_multiplier=1.5),
    # Rủi ro thấp: validate
    "L2_VALIDATE":         StageRisk("L2_VALIDATE",          base_risk=3.0, failure_multiplier=1.2),
    # Rủi ro thấp: route
    "L3_ROUTE":            StageRisk("L3_ROUTE",             base_risk=2.0, failure_multiplier=1.0),
    # Rủi ro trung bình: generate form
    "L6_GENERATE_FORM":    StageRisk("L6_GENERATE_FORM",     base_risk=5.0, failure_multiplier=1.5),
    # Rủi ro trung bình: storage
    "L7_STORAGE":          StageRisk("L7_STORAGE",           base_risk=6.0, failure_multiplier=2.0),
    # Rủi ro thấp: error handling
    "L8_ERROR_HANDLER":    StageRisk("L8_ERROR_HANDLER",     base_risk=2.0, failure_multiplier=1.0),
    # Rủi ro thấp: PDF export
    "L9a_PDF_EXPORT":      StageRisk("L9a_PDF_EXPORT",       base_risk=1.0, failure_multiplier=1.0),
}

# Blocking threshold — nếu stage risk > này → halt pipeline
BLOCKING_THRESHOLD = 7.0


class RiskEngine:
    """
    Medical AI Risk Engine cho MediVoice VN.
    ISO 31000:2018 + NIST AI RMF 1.0

    Stages: GOVERN (config) → MAP (identify) → MEASURE (score) → MANAGE (control)
    """

    def __init__(self, stage_risks: Optional[dict] = None):
        """
        Args:
            stage_risks: Custom risk weights (default: VN_STAGE_RISKS)
        """
        import copy
        self._stage_risks = copy.deepcopy(stage_risks or VN_STAGE_RISKS)
        self._run_log: list[dict] = []

    def mark_failed(self, stage: str, reason: str = "") -> float:
        """
        Đánh dấu stage đã fail và tính risk.

        Returns:
            Risk score cho stage này
        """
        if stage in self._stage_risks:
            sr = self._stage_risks[stage]
            sr.failed = True
            sr.risk_reason = reason
            risk = sr.compute()
            self._run_log.append({
                "stage": stage,
                "failed": True,
                "risk": risk,
                "severity": sr.severity,
                "reason": reason,
            })
            return risk
        return 0.0

    def mark_passed(self, stage: str) -> None:
        """Đánh dấu stage PASS (risk = 0)."""
        if stage in self._stage_risks:
            self._stage_risks[stage].failed = False
            self._stage_risks[stage].current_risk = 0.0

    def has_blocking_risk(self) -> bool:
        """Có stage nào có risk vượt blocking threshold không?"""
        return any(
            sr.current_risk >= BLOCKING_THRESHOLD
            for sr in self._stage_risks.values()
        )

    def blocking_stages(self) -> list[str]:
        """Danh sách stages đang block pipeline."""
        return [
            name for name, sr in self._stage_risks.items()
            if sr.current_risk >= BLOCKING_THRESHOLD
        ]

    def total_risk(self) -> float:
        """Tổng risk của toàn pipeline (0-10)."""
        risks = [sr.current_risk for sr in self._stage_risks.values()]
        return min(sum(risks) / max(len(risks), 1), 10.0)

    def summary(self) -> RiskSummary:
        """Tổng hợp risk toàn pipeline."""
        total = self.total_risk()
        blocking = self.blocking_stages()
        stage_risks = {
            name: sr.current_risk
            for name, sr in self._stage_risks.items()
        }

        notes = []
        if "L4_HUMAN_GATE" in blocking:
            notes.append("[CRITICAL] L4 Human Gate failed — Luật KCB 2023 Điều 62 violation risk")
        if "L10_AUDIT_LOG" in blocking:
            notes.append("[CRITICAL] L10 Audit Log failed — Luật AI 134/2025 Điều 24 violation risk")
        if "L5_PII_SCAN" in blocking:
            notes.append("[HIGH] PII Scan failed — NĐ13/2023 data protection risk")
        if "L1b_DRUG_CORRECT" in blocking:
            notes.append("[HIGH] Drug correction failed — Patient safety risk (CEER)")

        severity = "LOW"
        if total >= 9: severity = "CRITICAL"
        elif total >= 6: severity = "HIGH"
        elif total >= 3: severity = "MEDIUM"

        return RiskSummary(
            total_risk=round(total, 2),
            severity=severity,
            blocking_stages=blocking,
            stage_risks=stage_risks,
            compliant=len(blocking) == 0,
            notes=notes,
        )

    def reset(self) -> None:
        """Reset risk state giữa các lần chạy."""
        import copy
        self._stage_risks = copy.deepcopy(VN_STAGE_RISKS)
        self._run_log.clear()

    def run_log(self) -> list[dict]:
        """Log các stage đã fail trong run này."""
        return list(self._run_log)


if __name__ == "__main__":
    engine = RiskEngine()
    engine.mark_failed("L1b_DRUG_CORRECT", "Paracetamol nhầm thành Piracetam")
    summary = engine.summary()
    print(f"Total risk: {summary.total_risk} ({summary.severity})")
    print(f"Blocking: {summary.blocking_stages}")
    print(f"Compliant: {summary.compliant}")
    for note in summary.notes:
        print(f"  {note}")
