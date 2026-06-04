"""Facility model — cơ sở y tế đăng ký."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
import uuid


class Facility(BaseModel):
    facility_id: str = f"FAC-{str(uuid.uuid4())[:8].upper()}"
    ten_co_so: str
    byt_registration_number: str     # Số GPHN/CCHN cơ sở
    province_code: str               # 48=Đà Nẵng, 79=HCM...
    dia_chi: str = ""
    so_dien_thoai: str = ""
    so_y_te: str = ""                # Tên Sở Y tế quản lý
