# orchestrator.py — MediVoice VN Pipeline Execution Controller
# Học từ MediVoice_AI v2.61.3 | Adapted cho thị trường VN
# ISO/IEC 42001:2023 Clause 8.4 — AI System Lifecycle
# v1.0 | 2026-06-04

from __future__ import annotations
import time
import logging
from dataclasses import dataclass, field
from typing import Any

from ..models.clinical_record import ClinicalRecord, RecordStatus
from . import (
    l0_normalize, l1a_asr, l1b_drug_correct, l1c_ner,
    l1d_icd_lookup, l2_validate, l3_route,
    l4_human_gate, l5_pii_scan,
)
from ..core.l8_error_handler import PipelineError, PipelineErrorCode

logger = logging.getLogger(__name__)


@dataclass
class StageResult:
    """Kết quả thực thi một stage trong pipeline."""
    stage: str
    ok: bool
    duration_ms: float = 0.0
    output: Any = None
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "stage": self.stage,
            "ok": self.ok,
            "duration_ms": round(self.duration_ms, 1),
            "error": self.error,
        }


@dataclass
class PipelineResult:
    """Kết quả toàn bộ pipeline L0→L3+L5."""
    record: ClinicalRecord | None = None
    stages: list[StageResult] = field(default_factory=list)
    transcript: str = ""
    overall_ok: bool = False
    total_ms: float = 0.0
    validation_summary: dict = field(default_factory=dict)

    def stage_summary(self) -> list[dict]:
        return [s.to_dict() for s in self.stages]


class Orchestrator:
    """
    Central pipeline execution controller — MediVoice VN.

    Thực thi pipeline: L0 → L1a → L1b → L1c → L1d → L2 → L3 → L5
    L4 (Human Gate) và L6-L10 được gọi từ API sau khi BS review.

    Mỗi stage:
    1. ValidationLayer.validate_pre() — kiểm tra trước
    2. Execute stage
    3. RuntimeAuditHook ghi log
    4. ValidationLayer.validate_post() — kiểm tra sau
    5. StageResult ghi nhận

    ISO/IEC 42001:2023 Cl.8.4 + Cl.9.1
    """

    # Critical Control Points — có thể cần escalate lên BS
    CCPS = {"L4_HUMAN_GATE", "L6_FORM_GENERATOR"}

    def __init__(self, validation_layer=None):
        self.validation_layer = validation_layer
        self._stages: list[StageResult] = []

    def run_transcription_pipeline(
        self,
        audio_path: str,
        facility_id: str,
        doctor_cchn: str,
    ) -> PipelineResult:
        """
        Chạy pipeline L0→L3+L5 từ audio file.
        Trả về ClinicalRecord ở trạng thái PENDING_REVIEW.
        L4 (approve/reject) do BS thực hiện qua UI.
        """
        result = PipelineResult()
        t_start = time.perf_counter()
        self._stages = []

        try:
            # ── p0: Ingestion ─────────────────────────────────────────
            audio, wav_path = self._run_stage("L0_NORMALIZE", lambda: l0_normalize.normalize(audio_path))
            if not self._last_ok:
                return self._fail(result, "L0 failed")

            # ── p1: Processing ────────────────────────────────────────
            transcript_raw = self._run_stage("L1a_ASR", lambda: l1a_asr.transcribe(audio))
            if not self._last_ok:
                transcript_raw = ""  # graceful — continue với empty transcript

            transcript_corrected = self._run_stage(
                "L1b_DRUG_CORRECT",
                lambda: l1b_drug_correct.correct_drug_names(transcript_raw)
            )
            drug_candidates = self._run_stage(
                "L1b_DRUG_EXTRACT",
                lambda: l1b_drug_correct.extract_drug_candidates(transcript_corrected or "")
            )
            entities = self._run_stage(
                "L1c_NER",
                lambda: l1c_ner.extract_entities(transcript_corrected or "", drug_candidates or [])
            )
            icd_code, icd_display = self._run_stage(
                "L1d_ICD_LOOKUP",
                lambda: l1d_icd_lookup.auto_lookup(entities.chan_doan if entities else "")
            ) or ("", "")

            form_data, conf_scores, overall_conf = self._run_stage(
                "L2_VALIDATE",
                lambda: l2_validate.validate(entities)
            ) or ({}, {}, 0.0)

            if form_data:
                form_data["icd_code"] = icd_code
                form_data["icd_display"] = icd_display

            route = self._run_stage(
                "L3_ROUTE",
                lambda: l3_route.detect_route(form_data or {})
            ) or "lam_sang"

            # ── p2: PII scan (trước khi tạo record) ───────────────────
            pii_detected = self._run_stage(
                "L5_PII_SCAN",
                lambda: l5_pii_scan.scan_form_data(form_data or {})
            ) or []

            # ── Tạo ClinicalRecord ────────────────────────────────────
            record = ClinicalRecord(
                facility_id=facility_id,
                doctor_cchn=doctor_cchn,
                audio_path=wav_path,
                transcript_raw=transcript_raw or "",
                transcript_corrected=transcript_corrected or "",
                ner_entities={
                    "chan_doan": entities.chan_doan if entities else "",
                    "don_thuoc": entities.don_thuoc if entities else [],
                    "nhiet_do": entities.nhiet_do if entities else None,
                    "huyet_ap": [
                        entities.huyet_ap_tam_thu if entities else None,
                        entities.huyet_ap_tam_truong if entities else None,
                    ],
                    "mach": entities.mach if entities else None,
                    "tai_kham": entities.tai_kham if entities else "",
                },
                icd_code=icd_code or "",
                icd_display=icd_display or "",
                form_data=form_data or {},
                confidence_scores=conf_scores or {},
                overall_confidence=overall_conf or 0.0,
                route=route,
                pii_detected=pii_detected,
            )

            # L4: chuyển sang PENDING_REVIEW — BS sẽ review qua UI
            record = l4_human_gate.require_human_approval(record)

            # ValidationLayer summary nếu có
            if self.validation_layer:
                result.validation_summary = self.validation_layer.get_run_summary()

            result.record = record
            result.transcript = transcript_corrected or transcript_raw or ""
            result.overall_ok = True
            result.stages = self._stages
            result.total_ms = (time.perf_counter() - t_start) * 1000

            logger.info(
                f"Pipeline OK | route={route} | conf={overall_conf:.2f} "
                f"| icd={icd_code} | {len(self._stages)} stages "
                f"| {result.total_ms:.0f}ms"
            )
            return result

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            result.stages = self._stages
            result.total_ms = (time.perf_counter() - t_start) * 1000
            return result

    # ── Helpers ──────────────────────────────────────────────────────────

    _last_ok: bool = True

    def _run_stage(self, name: str, fn) -> Any:
        """Chạy một stage, ghi StageResult, trả về output."""
        t = time.perf_counter()
        try:
            # Pre-validation
            if self.validation_layer:
                pre = self.validation_layer.validate_pre(name, fn)
                if not pre.can_proceed:
                    self._stages.append(StageResult(
                        stage=name, ok=False,
                        duration_ms=(time.perf_counter()-t)*1000,
                        error=f"Pre-validation failed: {pre.escalation_reasons}"
                    ))
                    self._last_ok = False
                    return None

            output = fn()
            duration = (time.perf_counter() - t) * 1000

            # Post-validation
            if self.validation_layer:
                self.validation_layer.validate_post(name, None, output, duration, True)

            self._stages.append(StageResult(stage=name, ok=True, duration_ms=duration, output=output))
            self._last_ok = True
            return output

        except Exception as e:
            duration = (time.perf_counter() - t) * 1000
            self._stages.append(StageResult(stage=name, ok=False, duration_ms=duration, error=str(e)))
            logger.warning(f"Stage {name} error: {e}")
            self._last_ok = False
            return None

    def _fail(self, result: PipelineResult, reason: str) -> PipelineResult:
        result.stages = self._stages
        logger.error(f"Pipeline aborted: {reason}")
        return result
