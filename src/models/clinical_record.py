"""ClinicalRecord — wrapper cho BenhAnNgoaiTru với pipeline state."""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field
import uuid


class RecordStatus(str, Enum):
    DRAFT = "draft"            # ASR xong, chờ NER/validate
    PENDING_REVIEW = "pending_review"   # Qua L2-L3, chờ BS review (L4)
    APPROVED = "approved"      # BS approved → L7 lưu
    REJECTED = "rejected"      # BS rejected → không lưu
    STORED = "stored"          # Đã lưu SQLite (L7 done)
    EXPORTED = "exported"      # PDF đã export (L9a done)


class ClinicalRecord(BaseModel):
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    facility_id: str
    patient_id: Optional[str] = None
    doctor_cchn: str

    status: RecordStatus = RecordStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.now)
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None    # doctor CCHN
    rejected_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejection_reason: Optional[str] = None

    # Raw pipeline data
    audio_path: Optional[str] = None
    transcript_raw: Optional[str] = None    # L1a output
    transcript_corrected: Optional[str] = None  # L1b output

    # NER output (L1c)
    ner_entities: dict[str, Any] = Field(default_factory=dict)

    # ICD lookup (L1d)
    icd_code: Optional[str] = None
    icd_display: Optional[str] = None

    # Validated form (L2 output)
    form_data: dict[str, Any] = Field(default_factory=dict)
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    overall_confidence: float = 0.0

    # Route (L3)
    route: str = "lam_sang"      # lam_sang | cdha | nha_khoa

    # PII flags (L5)
    pii_detected: list[str] = Field(default_factory=list)

    # Audit (L10)
    audit_hash: Optional[str] = None
    byt_sync_status: str = "pending"

    # PDF path (L9a)
    pdf_path: Optional[str] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
