# L4 — Human Gate (MANDATORY)
# Luật KCB 2023 Điều 62: BS phải ký trước khi lưu
# Luật AI 134/2025: Human oversight bắt buộc
# FROZEN PIPELINE LAYER — Bắt buộc qua human review

from __future__ import annotations
from datetime import datetime
from ..models.clinical_record import ClinicalRecord, RecordStatus


class HumanGateError(Exception):
    """Raised khi cố lưu record mà chưa qua L4."""
    pass


def require_human_approval(record: ClinicalRecord) -> ClinicalRecord:
    """
    Chuyển record sang trạng thái PENDING_REVIEW để BS review.
    BS phải approve hoặc reject trước khi L7 lưu.
    Luật KCB 2023 Điều 62 — bắt buộc human review.
    """
    record = record.model_copy(update={"status": RecordStatus.PENDING_REVIEW})
    return record


def approve(record: ClinicalRecord, doctor_cchn: str) -> ClinicalRecord:
    """BS chấp thuận bản ghi. Status → APPROVED."""
    if record.status not in (RecordStatus.PENDING_REVIEW, RecordStatus.DRAFT):
        raise HumanGateError(
            f"Không thể approve record ở trạng thái {record.status}"
        )
    if not doctor_cchn or not doctor_cchn.strip():
        raise HumanGateError("CCHN bác sĩ không được để trống khi approve")

    return record.model_copy(update={
        "status": RecordStatus.APPROVED,
        "approved_at": datetime.now(),
        "approved_by": doctor_cchn.strip(),
    })


def reject(record: ClinicalRecord, doctor_cchn: str, reason: str) -> ClinicalRecord:
    """BS từ chối — không lưu vào SQLite."""
    if record.status not in (RecordStatus.PENDING_REVIEW, RecordStatus.DRAFT):
        raise HumanGateError(
            f"Không thể reject record ở trạng thái {record.status}"
        )
    if not doctor_cchn or not doctor_cchn.strip():
        raise HumanGateError("CCHN bác sĩ không được để trống khi reject")

    return record.model_copy(update={
        "status": RecordStatus.REJECTED,
        "rejected_at": datetime.now(),
        "rejected_by": doctor_cchn.strip(),
        "rejection_reason": reason,
    })


def assert_approved(record: ClinicalRecord) -> None:
    """Guard: gọi trước L7 để đảm bảo record đã qua L4."""
    if record.status != RecordStatus.APPROVED:
        raise HumanGateError(
            f"Record {record.record_id} chưa được BS approve. "
            f"Status hiện tại: {record.status}. "
            "L7 không lưu record chưa qua L4 (Luật KCB 2023 Điều 62)."
        )
