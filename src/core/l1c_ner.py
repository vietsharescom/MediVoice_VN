# L1c — Medical Named Entity Recognition (Rule-based, Phase 0)
# Input: corrected transcript | Output: structured entities dict
# Phase 0: regex + pattern matching. Phase 1: PhoBERT + CRF
# FROZEN PIPELINE LAYER

from __future__ import annotations
import re
from dataclasses import dataclass, field


@dataclass
class MedicalEntities:
    # Lý do khám / triệu chứng
    ly_do: str = ""
    trieu_chung: list[str] = field(default_factory=list)

    # Sinh hiệu
    nhiet_do: float | None = None
    huyet_ap_tam_thu: int | None = None
    huyet_ap_tam_truong: int | None = None
    mach: float | None = None
    nhip_tho: float | None = None
    can_nang: float | None = None
    spo2: float | None = None

    # Khám lâm sàng
    toan_than: str = ""
    cac_bo_phan: str = ""

    # Chẩn đoán
    chan_doan: str = ""

    # Đơn thuốc (mỗi item: {inn, ham_luong, lieu_dung, so_lan, so_ngay, duong_dung})
    don_thuoc: list[dict] = field(default_factory=list)

    # Tái khám
    tai_kham: str = ""

    # Xét nghiệm / CĐHA được đề cập
    chi_dinh: list[str] = field(default_factory=list)


# ─── Sinh hiệu patterns ────────────────────────────────────────────────────

_RE_NHIET_DO = re.compile(
    r"(?:sốt|nhiệt độ|temp(?:erature)?)\s*[:\s]?\s*(\d{2}(?:[.,]\d)?)\s*°?(?:c|celsius)?",
    re.IGNORECASE
)
_RE_HA_SYSTOLIC = re.compile(
    r"(?:huyết\s*áp|HA|BP)\s*[:\s]?\s*(\d{2,3})\s*/\s*(\d{2,3})",
    re.IGNORECASE
)
_RE_MACH = re.compile(
    r"(?:mạch|pulse|HR)\s*[:\s]?\s*(\d{2,3})\s*(?:lần/phút|bpm|nhịp)?",
    re.IGNORECASE
)
_RE_NHIP_THO = re.compile(
    r"(?:nhịp\s*thở|SpR|RR)\s*[:\s]?\s*(\d{1,2})\s*(?:lần/phút)?",
    re.IGNORECASE
)
_RE_CAN_NANG = re.compile(
    r"(?:cân\s*nặng|weight|CN)\s*[:\s]?\s*(\d{2,3}(?:[.,]\d)?)\s*(?:kg)?",
    re.IGNORECASE
)
_RE_SPO2 = re.compile(
    r"(?:SpO2|spo2|độ\s*bão\s*hòa)\s*[:\s]?\s*(\d{2,3})\s*%?",
    re.IGNORECASE
)

# ─── Đơn thuốc patterns ────────────────────────────────────────────────────

_RE_DOSE_NUMBER = re.compile(r"(\d+(?:[.,]\d+)?)\s*(mg|g|ml|mcg|iu|đv)?", re.IGNORECASE)
_RE_FREQUENCY = re.compile(
    r"(\d+)\s*(?:lần|viên|ống|gói)\s*(?:/|mỗi|x)?\s*(?:ngày|day)",
    re.IGNORECASE
)
_RE_DURATION = re.compile(
    r"(?:trong|uống|dùng)?\s*(\d+)\s*(?:ngày|day)",
    re.IGNORECASE
)
_RE_ROUTE = re.compile(
    r"\b(uống|tiêm|nhỏ\s*mắt|nhỏ\s*mũi|đặt|bôi|hít|truyền)\b",
    re.IGNORECASE
)

# ─── Tái khám patterns ──────────────────────────────────────────────────────

_RE_TAI_KHAM = re.compile(
    r"(?:tái\s*khám|hẹn\s*lại|follow.?up)\s*(?:sau|after)?\s*(\d+)\s*(ngày|tuần|tháng)",
    re.IGNORECASE
)

# ─── Chẩn đoán patterns ─────────────────────────────────────────────────────

_RE_CHAN_DOAN = re.compile(
    r"(?:chẩn\s*đoán|diagnos\w*)[:\s]+([^.,;,\n]+?)(?=\s*(?:kê|cho\s*uống|cho\s*dùng|đơn\s*thuốc|tái\s*khám|$))",
    re.IGNORECASE
)

# ─── Chi định patterns ──────────────────────────────────────────────────────

_RE_CHI_DINH = re.compile(
    r"(?:chỉ\s*định|xét\s*nghiệm|siêu\s*âm|x.?quang|CT|MRI|ECG|điện\s*tim)[:\s]*([^.,;]*)",
    re.IGNORECASE
)


def extract_entities(transcript: str, drug_candidates: list[dict] | None = None) -> MedicalEntities:
    """
    Trích xuất các entity y tế từ transcript đã qua L1b.
    drug_candidates: output từ l1b.extract_drug_candidates()
    """
    ent = MedicalEntities()

    # Sinh hiệu
    m = _RE_NHIET_DO.search(transcript)
    if m:
        ent.nhiet_do = float(m.group(1).replace(",", "."))

    m = _RE_HA_SYSTOLIC.search(transcript)
    if m:
        ent.huyet_ap_tam_thu = int(m.group(1))
        ent.huyet_ap_tam_truong = int(m.group(2))

    m = _RE_MACH.search(transcript)
    if m:
        ent.mach = float(m.group(1))

    m = _RE_NHIP_THO.search(transcript)
    if m:
        ent.nhip_tho = float(m.group(1))

    m = _RE_CAN_NANG.search(transcript)
    if m:
        ent.can_nang = float(m.group(1).replace(",", "."))

    m = _RE_SPO2.search(transcript)
    if m:
        ent.spo2 = float(m.group(1))

    # Chẩn đoán
    m = _RE_CHAN_DOAN.search(transcript)
    if m:
        ent.chan_doan = m.group(1).strip()

    # Tái khám
    m = _RE_TAI_KHAM.search(transcript)
    if m:
        ent.tai_kham = f"Sau {m.group(1)} {m.group(2)}"

    # Chi định
    for m in _RE_CHI_DINH.finditer(transcript):
        val = m.group(0).strip()
        if val:
            ent.chi_dinh.append(val)

    # Đơn thuốc — dùng drug_candidates từ L1b
    if drug_candidates:
        for dc in drug_candidates:
            drug_entry = _extract_drug_context(transcript, dc)
            ent.don_thuoc.append(drug_entry)

    return ent


def _extract_drug_context(transcript: str, drug_candidate: dict) -> dict:
    """Lấy liều lượng, tần suất, số ngày cho một tên thuốc."""
    inn = drug_candidate["inn"]
    pos = drug_candidate.get("word_position", 0)

    # Lấy context 20 words sau tên thuốc
    words = transcript.split()
    context = " ".join(words[pos: pos + 20])

    ham_luong = ""
    m = _RE_DOSE_NUMBER.search(context)
    if m:
        ham_luong = m.group(0).strip()

    so_lan_ngay = ""
    m = _RE_FREQUENCY.search(context)
    if m:
        so_lan_ngay = m.group(0).strip()

    so_ngay = 0
    m = _RE_DURATION.search(context)
    if m:
        try:
            so_ngay = int(m.group(1))
        except ValueError:
            pass

    duong_dung = "uống"
    m = _RE_ROUTE.search(context)
    if m:
        duong_dung = m.group(1).lower().strip()

    return {
        "inn": inn,
        "ham_luong": ham_luong,
        "so_lan_ngay": so_lan_ngay,
        "so_ngay": so_ngay,
        "duong_dung": duong_dung,
    }
