"""AuditEntry — immutable log entry (L10)."""
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class AuditEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    record_id: str
    actor_cchn: str
    action: str           # CREATED | APPROVED | REJECTED | EXPORTED | VIEWED
    detail: str = ""
    prev_hash: str = ""   # hash of previous entry (chain)
    entry_hash: str = ""  # SHA-256 of this entry content

    class Config:
        frozen = True     # immutable after creation
        json_encoders = {datetime: lambda v: v.isoformat()}
