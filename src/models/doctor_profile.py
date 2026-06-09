# src/models/doctor_profile.py
# DVP — Doctor Voice Profile model (FID-VN-012)

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

VALID_SPECIALTIES: frozenset[str] = frozenset({
    "noi_khoa", "tim_mach", "chan_thuong_chinh_hinh", "tai_mui_hong",
    "san_phu_khoa", "nhi", "cdha", "ngoai", "da_lieu", "mat",
    "noi_tiet", "than_tiet_nieu",
})

VALID_REGIONS: frozenset[str] = frozenset({"northern", "central", "southern"})

VALID_ENGLISH_LEVELS: frozenset[str] = frozenset({"Basic", "Intermediate", "Good"})

VALID_SPEAKING_SPEEDS: frozenset[str] = frozenset({"Chậm", "Vừa", "Nhanh"})

SPECIALTY_DISPLAY: dict[str, str] = {
    "noi_khoa":              "Nội khoa",
    "tim_mach":              "Tim mạch",
    "chan_thuong_chinh_hinh":"Chấn thương chỉnh hình",
    "tai_mui_hong":          "Tai Mũi Họng",
    "san_phu_khoa":          "Sản phụ khoa",
    "nhi":                   "Nhi khoa",
    "cdha":                  "Chẩn đoán hình ảnh",
    "ngoai":                 "Ngoại khoa",
    "da_lieu":               "Da liễu",
    "mat":                   "Nhãn khoa",
    "noi_tiet":              "Nội tiết",
    "than_tiet_nieu":        "Thận tiết niệu",
}


@dataclass
class DoctorProfile:
    cchn: str
    name: str
    region: str                          # northern | central | southern
    primary_specialty: str              # VALID_SPECIALTIES
    secondary_specialty: Optional[str] = None
    english_level: str = "Basic"        # Basic | Intermediate | Good
    speaking_speed: str = "Vừa"        # Chậm | Vừa | Nhanh
    created_at: str = ""
    updated_at: str = ""


@dataclass
class DoctorAlias:
    id: Optional[int]
    cchn: str
    alias_text: str                 # "mét phốt min"
    inn: str                        # "Metformin"
    session_count: int = 0
    occurrence_count: int = 0
    confirmed_by_bs: int = 0        # 0=pending | 1=confirmed | -1=rejected
    created_at: str = ""
    last_seen: str = ""
