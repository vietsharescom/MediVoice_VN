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
    r"(?:tái\s*khám|hẹn\s*lại|follow.?up)\s*(?:sau|after)?\s*(\d+)\s*(ngày|tuần|tháng)"
    r"([^.!?\n]*)",
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

# ─── Vietnamese word-form number normalization (FID-VN-005) ───────────────────
# PhoWhisper outputs word-form numbers ("tám mươi", "một trăm ba mươi trên chín mươi")
# These must be converted to digits before regex NER patterns can match.

_VN_ONES: dict[str, int] = {
    "không": 0,
    "mốt": 1, "một": 1,
    "hai": 2,
    "ba": 3,
    "bốn": 4, "tư": 4,
    "năm": 5, "lăm": 5,
    "sáu": 6,
    "bảy": 7, "bẩy": 7,
    "tám": 8,
    "chín": 9,
}

# Building blocks (all non-capturing)
_W1  = r"(?:mốt|một|hai|ba|bốn|tư|lăm|năm|sáu|bảy|bẩy|tám|chín)"
_WO  = r"(?:không|mốt|một|hai|ba|bốn|tư|lăm|năm|sáu|bảy|bẩy|tám|chín)"
_WTG = r"(?:hai|ba|bốn|tư|năm|sáu|bảy|bẩy|tám|chín)\s+mươi(?:\s+" + _W1 + r")?"
_W10 = r"mười(?:\s+" + _W1 + r")?"
_WSH = r"(?:ba|bốn|tư|năm|sáu|bảy|bẩy|tám|chín)\s+(?:lăm|mốt)"   # "tám lăm"=85
_WH  = (r"(?:một|hai|ba|bốn|tư|năm|sáu|bảy|bẩy|tám|chín)\s+trăm"
        r"(?:\s+(?:" + _WTG + r"|" + _W10 + r"|" + _W1 + r"))?")
_WN  = r"(?:" + _WH + r"|" + _WTG + r"|" + _W10 + r"|" + _WSH + r")"

_RE_BP_WORDS  = re.compile(r"\b(" + _WN + r")\s+trên\s+(" + _WN + r")\b", re.I | re.U)
_RE_DEC_WORDS = re.compile(r"\b(" + _WN + r"|" + _WO + r")\s+phẩy\s+(" + _WO + r")\b", re.I | re.U)
_RE_RUOI      = re.compile(r"\b(" + _WN + r"|" + _WO + r")\s+(?:độ\s+)?rưỡi\b", re.I | re.U)
_RE_WINT      = re.compile(r"\b" + _WN + r"\b", re.I | re.U)
_WU           = r"\s*(?:viên|lần|ngày|tuần|tháng|kg|kilogram|g(?:ram)?|mg|miligam|ml|mililit|mcg|microgam|ống|gói|giọt)"
_RE_W1U       = re.compile(r"\b(" + _WO + r")(" + _WU + r")\b", re.I | re.U)


def _vn_tens_int(t: str) -> int | None:
    m = re.match(
        r"^(hai|ba|bốn|tư|năm|sáu|bảy|bẩy|tám|chín)"
        r"\s+mươi(?:\s+(mốt|một|hai|ba|bốn|tư|lăm|năm|sáu|bảy|bẩy|tám|chín))?$",
        t, re.UNICODE,
    )
    if m:
        return _VN_ONES[m.group(1)] * 10 + (_VN_ONES.get(m.group(2), 0) if m.group(2) else 0)
    m = re.match(
        r"^mười(?:\s+(mốt|một|hai|ba|bốn|tư|lăm|năm|sáu|bảy|bẩy|tám|chín))?$",
        t, re.UNICODE,
    )
    if m:
        return 10 + (_VN_ONES.get(m.group(1), 0) if m.group(1) else 0)
    # Shorthand: "tám lăm"→85, "ba mốt"→31
    m = re.match(r"^(ba|bốn|tư|năm|sáu|bảy|bẩy|tám|chín)\s+(lăm|mốt)$", t, re.UNICODE)
    if m:
        _sh = {"ba": 3, "bốn": 4, "tư": 4, "năm": 5, "sáu": 6, "bảy": 7, "bẩy": 7, "tám": 8, "chín": 9}
        return _sh[m.group(1)] * 10 + (5 if m.group(2) == "lăm" else 1)
    return _VN_ONES.get(t)


def _vn_to_int(text: str) -> int | None:
    """Parse Vietnamese word-form integer (0–999) → int. Returns None on failure."""
    t = re.sub(r"\s+", " ", text.lower().strip())
    m = re.match(
        r"^(một|hai|ba|bốn|tư|năm|sáu|bảy|bẩy|tám|chín)\s+trăm(?:\s+(.+))?$",
        t, re.UNICODE,
    )
    if m:
        h = _VN_ONES[m.group(1)] * 100
        rest = (m.group(2) or "").strip()
        if not rest:
            return h
        sub = _vn_tens_int(rest)
        return h + sub if sub is not None else None
    return _vn_tens_int(t)


def _normalize_vn_numbers(text: str) -> str:
    """
    Convert Vietnamese word-form numbers → Arabic digits.
    Called at start of extract_entities() so all NER regex can match digit format.
    Order: BP first (avoid "trên" ambiguity), then decimal, rưỡi, integers, units.
    """
    def _bp(m: re.Match) -> str:
        a, b = _vn_to_int(m.group(1)), _vn_to_int(m.group(2))
        return f"{a}/{b}" if (a is not None and b is not None) else m.group(0)

    def _dec(m: re.Match) -> str:
        a = _vn_to_int(m.group(1))
        b = _VN_ONES.get(m.group(2).lower().strip())
        return f"{a}.{b}" if (a is not None and b is not None) else m.group(0)

    def _ruoi(m: re.Match) -> str:
        a = _vn_to_int(m.group(1))
        return f"{a}.5" if a is not None else m.group(0)

    def _wint(m: re.Match) -> str:
        v = _vn_to_int(m.group(0))
        return str(v) if v is not None else m.group(0)

    def _unit(m: re.Match) -> str:
        v = _VN_ONES.get(m.group(1).lower().strip())
        return f"{v}{m.group(2)}" if v is not None else m.group(0)

    r = _RE_BP_WORDS.sub(_bp, text)
    r = _RE_DEC_WORDS.sub(_dec, r)
    r = _RE_RUOI.sub(_ruoi, r)
    r = _RE_WINT.sub(_wint, r)
    r = _RE_W1U.sub(_unit, r)
    return r


def extract_entities(transcript: str, drug_candidates: list[dict] | None = None) -> MedicalEntities:
    """
    Trích xuất các entity y tế từ transcript đã qua L1b.
    drug_candidates: output từ l1b.extract_drug_candidates()
    """
    ent = MedicalEntities()

    # Pre-process: convert VN word-form numbers → digits for regex matching
    t = _normalize_vn_numbers(transcript)

    # Sinh hiệu
    m = _RE_NHIET_DO.search(t)
    if m:
        ent.nhiet_do = float(m.group(1).replace(",", "."))

    m = _RE_HA_SYSTOLIC.search(t)
    if m:
        ent.huyet_ap_tam_thu = int(m.group(1))
        ent.huyet_ap_tam_truong = int(m.group(2))

    m = _RE_MACH.search(t)
    if m:
        ent.mach = float(m.group(1))

    m = _RE_NHIP_THO.search(t)
    if m:
        ent.nhip_tho = float(m.group(1))

    m = _RE_CAN_NANG.search(t)
    if m:
        ent.can_nang = float(m.group(1).replace(",", "."))

    m = _RE_SPO2.search(t)
    if m:
        ent.spo2 = float(m.group(1))

    # Chẩn đoán
    m = _RE_CHAN_DOAN.search(t)
    if m:
        ent.chan_doan = m.group(1).strip()

    # Tái khám
    m = _RE_TAI_KHAM.search(t)
    if m:
        base = f"{m.group(1)} {m.group(2)}"
        extra = m.group(3).strip() if m.group(3) else ""
        ent.tai_kham = f"{base} {extra}".strip() if extra else base

    # Chi định
    for m in _RE_CHI_DINH.finditer(t):
        val = m.group(0).strip()
        if val:
            ent.chi_dinh.append(val)

    # Đơn thuốc — word positions from L1b are based on original transcript;
    # normalize only the extracted context window to avoid position shifts.
    if drug_candidates:
        for dc in drug_candidates:
            drug_entry = _extract_drug_context(transcript, dc)
            ent.don_thuoc.append(drug_entry)

    return ent


def _extract_drug_context(transcript: str, drug_candidate: dict) -> dict:
    """Lấy liều lượng, tần suất, số ngày cho một tên thuốc."""
    inn = drug_candidate["inn"]
    pos = drug_candidate.get("word_position", 0)

    # Original word positions preserved; normalize only the context window
    words = transcript.split()
    context_raw = " ".join(words[pos: pos + 20])
    context = _normalize_vn_numbers(context_raw)

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
