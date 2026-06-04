"""Patient data model — NĐ13/2023 PII-aware."""
from __future__ import annotations
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class Patient(BaseModel):
    patient_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ho_va_ten: str
    sinh_ngay: Optional[date] = None
    gioi_tinh: Optional[str] = None          # "Nam" | "Nữ"
    dan_toc: str = ""
    nghe_nghiep: str = ""

    # Địa chỉ
    dia_chi_so_nha: str = ""
    dia_chi_xa_phuong: str = ""
    dia_chi_huyen: str = ""
    dia_chi_tinh: str = ""

    # PII — encrypted at L7
    so_dien_thoai: Optional[str] = None      # L5 PII
    cccd_so: Optional[str] = None            # L5 PII — VNeID-ready
    bhyt_so_the: Optional[str] = None
    bhyt_han_ngay: Optional[date] = None

    # Legacy
    legacy_id: Optional[str] = None          # Mã cũ của phòng khám

    class Config:
        json_encoders = {date: str}
