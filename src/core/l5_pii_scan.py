# L5 — PII Scan
# Input: any text hoặc form_data dict | Output: list of PII types detected
# Detects: CCCD, BHYT, SĐT — NĐ13/2023 compliance
# FROZEN PIPELINE LAYER

from __future__ import annotations
import re

# CCCD mới: 12 chữ số (từ 2021)
_RE_CCCD = re.compile(r"\b0\d{11}\b")
# CMND cũ: 9 chữ số
_RE_CMND = re.compile(r"\b\d{9}\b")
# Số điện thoại VN: 0[3-9]xx xxx xxx
_RE_SDT = re.compile(r"\b0[3-9]\d{8}\b")
# BHYT: 2 chữ cái + 13 chữ số (VD: BN1234567890123)
_RE_BHYT = re.compile(r"\b[A-Z]{2}\d{13}\b")
# Email
_RE_EMAIL = re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b")


def scan_text(text: str) -> list[str]:
    """
    Quét text, trả về danh sách loại PII tìm thấy.
    VD: ["CCCD", "SDT"]
    """
    found = []
    if _RE_CCCD.search(text):
        found.append("CCCD")
    if _RE_CMND.search(text):
        found.append("CMND")
    if _RE_SDT.search(text):
        found.append("SDT")
    if _RE_BHYT.search(text):
        found.append("BHYT")
    if _RE_EMAIL.search(text):
        found.append("EMAIL")
    return found


def scan_form_data(form_data: dict) -> list[str]:
    """Quét toàn bộ form_data dict."""
    combined = _flatten_dict_to_text(form_data)
    return scan_text(combined)


def mask_pii(text: str) -> str:
    """Mask PII trong text trước khi log/display (không dùng cho DB storage)."""
    text = _RE_CCCD.sub("[CCCD-MASKED]", text)
    text = _RE_CMND.sub("[CMND-MASKED]", text)
    text = _RE_SDT.sub("[SDT-MASKED]", text)
    text = _RE_BHYT.sub("[BHYT-MASKED]", text)
    text = _RE_EMAIL.sub("[EMAIL-MASKED]", text)
    return text


def _flatten_dict_to_text(d: dict | list | str | None, sep: str = " ") -> str:
    if isinstance(d, dict):
        return sep.join(_flatten_dict_to_text(v, sep) for v in d.values())
    if isinstance(d, list):
        return sep.join(_flatten_dict_to_text(i, sep) for i in d)
    if d is None:
        return ""
    return str(d)
