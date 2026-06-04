# rule_engine.py — Deterministic Medical VN Rules
# Học từ MediVoice_AI | Adapted cho thị trường VN
# ISO/IEC 42001:2023 Cl.8.5 | Luật KCB 2023 | TT32/2023
# v1.0 | 2026-06-04

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Violation:
    severity: str   # CRITICAL | HIGH | MEDIUM | LOW
    rule_id: str
    message: str


@dataclass
class ValidationReport:
    stage: str
    phase: str
    passed: bool
    violations: list[Violation] = field(default_factory=list)

    @property
    def blocking_violations(self) -> list[Violation]:
        return [v for v in self.violations if v.severity in ("CRITICAL", "HIGH")]

    @property
    def has_critical(self) -> bool:
        return any(v.severity == "CRITICAL" for v in self.violations)

    def to_dict(self) -> dict:
        return {
            "stage": self.stage, "phase": self.phase, "passed": self.passed,
            "violations": [{"id": v.rule_id, "sev": v.severity, "msg": v.message}
                           for v in self.violations],
        }


class RuleEngine:
    """
    Deterministic rule enforcement cho pipeline VN.
    Rules không thể bị thuyết phục — luôn chạy.
    """

    def validate(self, stage: str, payload: Any, phase: str = "pre") -> ValidationReport:
        violations = []

        if phase == "pre":
            violations.extend(self._pre_rules(stage, payload))
        else:
            violations.extend(self._post_rules(stage, payload))

        passed = not any(v.severity in ("CRITICAL", "HIGH") for v in violations)
        return ValidationReport(stage=stage, phase=phase, passed=passed, violations=violations)

    def _pre_rules(self, stage: str, payload: Any) -> list[Violation]:
        v = []
        if stage == "L4_HUMAN_GATE" and payload is None:
            v.append(Violation("CRITICAL", "R-L4-001", "L4 không được nhận payload None"))
        if stage == "L7_STORAGE" and payload is None:
            v.append(Violation("CRITICAL", "R-L7-001", "Không lưu record None vào DB"))
        return v

    def _post_rules(self, stage: str, payload: Any) -> list[Violation]:
        v = []
        if stage == "L1b_DRUG_CORRECT" and isinstance(payload, str):
            # Tên thuốc không được bị dịch sang tiếng Việt
            vi_drug_names = ["thuốc hạ sốt", "kháng sinh", "thuốc tiểu đường"]
            if any(name in payload.lower() for name in vi_drug_names):
                v.append(Violation("CRITICAL", "R-L1b-001",
                                   "Tên INN bị dịch sang tiếng Việt — vi phạm drug integrity"))
        if stage == "L5_PII_SCAN" and isinstance(payload, list):
            if "CCCD" in payload or "SĐT" in payload:
                v.append(Violation("HIGH", "R-L5-001",
                                   f"PII phát hiện: {payload} — cần mask trước khi log"))
        if stage == "L2_VALIDATE" and isinstance(payload, tuple) and len(payload) == 3:
            _, _, conf = payload
            if isinstance(conf, float) and conf < 0.3:
                v.append(Violation("MEDIUM", "R-L2-001",
                                   f"Confidence thấp ({conf:.2f}) — khuyên BS kiểm tra kỹ"))
        return v
