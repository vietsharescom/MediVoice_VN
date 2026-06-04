# L3 — Route Detection
# Input: validated form_data | Output: route string
# Phase 0: lam_sang là default. Plugin routes kích hoạt nếu có keyword.
# FROZEN PIPELINE LAYER

from __future__ import annotations

ROUTE_LAM_SANG = "lam_sang"
ROUTE_CDHA = "cdha"
ROUTE_NHA_KHOA = "nha_khoa"

# Keywords kích hoạt plugin routes
_CDHA_KEYWORDS = [
    "siêu âm", "x-quang", "xquang", "ct scan", "mri", "chụp",
    "cđha", "chẩn đoán hình ảnh", "điện tim", "ecg"
]
_NHA_KHOA_KEYWORDS = [
    "răng", "nha", "nhổ răng", "trám", "chụp răng", "nướu", "lợi"
]


def detect_route(form_data: dict) -> str:
    """
    Xác định route từ form_data.
    Phase 0: chỉ lam_sang và plugin stubs (CDHA, nha khoa).
    """
    # Lấy text để phân tích
    text = " ".join([
        str(form_data.get("chan_doan", "")),
        str(form_data.get("ly_do", "")),
        " ".join(str(c) for c in form_data.get("chi_dinh", [])),
    ]).lower()

    for kw in _NHA_KHOA_KEYWORDS:
        if kw in text:
            return ROUTE_NHA_KHOA

    for kw in _CDHA_KEYWORDS:
        if kw in text:
            return ROUTE_CDHA

    return ROUTE_LAM_SANG
