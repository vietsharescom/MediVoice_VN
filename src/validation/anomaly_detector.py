# anomaly_detector.py — Statistical Drift Detection
# Học từ MediVoice_AI | Adapted cho VN
# ISO/IEC 42001:2023 Cl.9.1 — Performance monitoring
# v1.0 | 2026-06-04

from __future__ import annotations
from dataclasses import dataclass, field
from collections import deque
import statistics


@dataclass
class Anomaly:
    metric: str
    expected: float
    actual: float
    severity: str  # CRITICAL | HIGH | MEDIUM


@dataclass
class AnomalyReport:
    stage: str
    severity: str  # CRITICAL | HIGH | MEDIUM | INFO
    anomalies: list[Anomaly] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "stage": self.stage, "severity": self.severity,
            "anomalies": [{"metric": a.metric, "expected": a.expected,
                           "actual": a.actual, "sev": a.severity}
                          for a in self.anomalies],
        }


class AnomalyDetector:
    """
    Phát hiện drift thống kê trong pipeline.
    Theo dõi latency và tỷ lệ lỗi theo thời gian.
    """

    # Ngưỡng latency (ms) theo stage
    LATENCY_THRESHOLDS = {
        "L0_NORMALIZE": 3000,
        "L1a_ASR": 10000,
        "L1b_DRUG_CORRECT": 500,
        "L1c_NER": 500,
        "L1d_ICD_LOOKUP": 200,
        "L2_VALIDATE": 100,
        "L3_ROUTE": 50,
        "L5_PII_SCAN": 100,
        "DEFAULT": 5000,
    }

    def __init__(self, window: int = 20):
        self._history: dict[str, deque] = {}
        self._window = window

    def detect(self, stage: str, execution_time_ms: float,
               payload_size: int = 0, risk_score: float = 0,
               ok: bool = True) -> AnomalyReport:
        anomalies = []

        # Latency check
        threshold = self.LATENCY_THRESHOLDS.get(stage, self.LATENCY_THRESHOLDS["DEFAULT"])
        if execution_time_ms > threshold * 2:
            anomalies.append(Anomaly("latency", threshold, execution_time_ms, "HIGH"))
        elif execution_time_ms > threshold:
            anomalies.append(Anomaly("latency", threshold, execution_time_ms, "MEDIUM"))

        # Rolling error rate
        key = f"{stage}_ok"
        if key not in self._history:
            self._history[key] = deque(maxlen=self._window)
        self._history[key].append(1.0 if ok else 0.0)

        if len(self._history[key]) >= 5:
            error_rate = 1.0 - statistics.mean(self._history[key])
            if error_rate > 0.5:
                anomalies.append(Anomaly("error_rate", 0.1, error_rate, "CRITICAL"))
            elif error_rate > 0.2:
                anomalies.append(Anomaly("error_rate", 0.1, error_rate, "HIGH"))

        severity = "INFO"
        if anomalies:
            max_sev = max(["INFO","MEDIUM","HIGH","CRITICAL"].index(a.severity)
                          for a in anomalies)
            severity = ["INFO","MEDIUM","HIGH","CRITICAL"][max_sev]

        return AnomalyReport(stage=stage, severity=severity, anomalies=anomalies)
