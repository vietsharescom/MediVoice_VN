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
    r"(?:sốt|nhiệt độ|temp(?:erature)?)\s*[:\s]?\s*"
    r"(\d{2}(?:[.,]\d)?)"
    r"(?:\s+(?:độ\s*)?(\d|một|hai|ba|bốn|năm|sáu|bảy|bẩy|tám|chín))?"  # digit OR VN word; allow "độ" separator
    r"\s*°?(?:c|celsius|độ)?",
    re.IGNORECASE
)
_RE_HA_SYSTOLIC = re.compile(
    r"(?:huyết\s*á(?:p)?|HA|BP)\b[^/\d]{0,40}?(\d{2,3})\s*/\s*(\d{2,3})",  # "huyết á" (no p) accepted
    re.IGNORECASE
)
_RE_MACH = re.compile(
    r"(?:mạch|mặc|mặt|pulse|HR)\s*[:\s]?\s*(\d{2,3})\s*(?:lần/phút|bpm|nhịp)?",  # "mặc"/"mặt" = PhoWhisper for "mạch"
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

_RE_DOSE_NUMBER = re.compile(r"(\d+(?:[.,]\d+)?)\s*(mg|g|ml|mcg|iu|đv|kg)?", re.IGNORECASE)
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

# ─── Lý do khám patterns ─────────────────────────────────────────────────────

_RE_LY_DO = re.compile(
    r"(?:lý\s*do\s*(?:vào\s*)?(?:khám|cán|kham)|chief\s*complaint)[:\s]+"
    r"([^.!?\n]{3,}?)(?=\s*(?:bệnh\s*nhân|tiền\s*sử|huyết\s*áp|nhiệt\s*độ|mạch|$))",
    re.IGNORECASE,
)
_RE_LY_DO_FALLBACK = re.compile(
    r"\b\d+\s*tuổi[\s,.]+"
    r"(?:(?:nghề\s*nghiệp|nhân\s*viên)\s+[^,;.]{1,30}[,;.]?\s*)?"  # skip "nghề nghiệp X" / "nhân viên X"
    r"([^.!?\n]{5,}?)(?=\s*(?:tiền\s*sử|huyết\s*á|nhiệt\s*độ|mạch\s+\d|mặc\s+\d|mặt\s+\d|$))",  # "huyết á" without p
    re.IGNORECASE,
)

# ─── Tái khám patterns ──────────────────────────────────────────────────────

_RE_TAI_KHAM = re.compile(
    r"(?:tái\s*khám|hẹn\s*lại|follow.?up)\s*(?:sau|after)?\s*(\d+)\s*(ngày|tuần|tháng)"
    r"([^.!?\n]*)",
    re.IGNORECASE
)

# ─── Chẩn đoán patterns ─────────────────────────────────────────────────────

_PRESCRIPTION_KW = (
    r"(?:điều\s*trị|kê\s*(?:đơn|thuốc|toa)?|đơn\s*thuốc|toa\s*thuốc|"
    r"tái\s*khám|hẹn|follow|cho\s*(?:\w+/?\w*\s*)?(?:uống|dùng))"
)
_RE_CHAN_DOAN = re.compile(
    r"(?:chẩn\s*đoán|diagnos\w*)[:\s]+"
    r"([^.,;!?\n]+?(?:\s+[A-Z]\d+(?:\.\d+)?)?)"        # VN diagnosis + optional ICD code
    # Two lookahead alternatives:
    #  A) inline keyword (no sentence break): "viêm họng cấp điều trị"
    #  B) after sentence punct + optional 1 filler word: "gout cấp. thôi Kê"
    r"(?=\s*(?:" + _PRESCRIPTION_KW + r"|$)"
    r"|\s*[.,;!?]\s*(?:\w+\s+){0,2}" + _PRESCRIPTION_KW + r")",
    re.IGNORECASE
)
# Fallback: PhoWhisper sometimes drops "chẩn đoán" keyword entirely.
# Detect disease name (viêm/tăng/đái/gout...) directly before "kê đơn/điều trị".
# Also catches "bị <disease>" pattern.
_RE_CHAN_DOAN_FALLBACK = re.compile(
    r"(?:bị\s+|mắc\s+|có\s+)?"
    r"((?:viêm|tăng|đái|gout|suy|nhồi|thiếu|đau|gãy|loét|rối\s*loạn|hội\s*chứng)"
    r"(?:\s+\w+){1,5}?)"
    r"(?=\s*[.,;!?]?\s*(?:\w+\s+){0,2}" + _PRESCRIPTION_KW + r")",
    re.IGNORECASE
)

# ─── Patient self-medication context (exclude from prescription) ────────────
# Matches "bệnh nhân tự uống X" → drug X is patient history, NOT prescription

_RE_PATIENT_MED = re.compile(
    r"(?:bệnh\s*nh[aâ]n|người\s*bệnh|bn|b[aâ]́ch\s*nh[aâ]n)\s+"
    r"(?:tự\s+)?(?:đã\s+|đang\s+)?(?:uống|dùng|sử\s*dụng)\s*$",
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

_RE_BP_WORDS  = re.compile(r"\b(" + _WN + r")\s+(?:trên|tri)\s+(" + _WN + r")\b", re.I | re.U)
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
        val = m.group(1).replace(",", ".")
        # PhoWhisper often drops "phẩy" or uses "độ" separator:
        # "37 tám" / "37 độ tám" → 37.8 | "37 độ 8" → 37.8
        if "." not in val and m.group(2):
            dec_str = m.group(2).lower().strip()
            dec = int(dec_str) if dec_str.isdigit() else _VN_ONES.get(dec_str, 0)
            val = f"{val}.{dec}"
        ent.nhiet_do = float(val)

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

    # Lý do khám — explicit prefix first, fallback to text after age mention
    m = _RE_LY_DO.search(t)
    if m:
        ent.ly_do = m.group(1).strip()
    else:
        m = _RE_LY_DO_FALLBACK.search(t)
        if m:
            captured = m.group(1).strip()[:80]
            # Only accept fallback if it contains at least one symptom keyword
            # (avoids extracting occupation/admin text like "nghề nghiệp lái xe tái khám")
            _symptom_kw = re.compile(
                r"\b(đau|sốt|ho\b|khó|mệt|chóng|buồn|nôn|tiểu|khát|ngứa|phù|tê|sưng|rát|chảy|nuốt|ợ)\b",
                re.IGNORECASE,
            )
            if _symptom_kw.search(captured):
                ent.ly_do = captured

    # Chẩn đoán — try explicit keyword first, then fallback (PhoWhisper may drop "chẩn đoán")
    m = _RE_CHAN_DOAN.search(t)
    if m:
        ent.chan_doan = m.group(1).strip()
    else:
        m = _RE_CHAN_DOAN_FALLBACK.search(t)
        if m:
            ent.chan_doan = m.group(1).strip()

    # Tái khám
    m = _RE_TAI_KHAM.search(t)
    if m:
        base = f"{m.group(1)} {m.group(2)}"
        extra = m.group(3).strip() if m.group(3) else ""
        # Only keep short qualifiers starting with "hoặc"/"nếu" — strip carry/admin instructions
        if extra and re.match(r"^(hoặc|nếu|sớm\s*hơn)", extra, re.IGNORECASE):
            extra = extra[:40]
        else:
            extra = ""
        ent.tai_kham = f"{base} {extra}".strip() if extra else base

    # Chi định
    for m in _RE_CHI_DINH.finditer(t):
        val = m.group(0).strip()
        if val:
            ent.chi_dinh.append(val)

    # Đơn thuốc — word positions from L1b are based on original transcript;
    # normalize only the extracted context window to avoid position shifts.
    # Drugs requiring explicit clinical context to avoid false positives
    _CONTEXT_REQUIRED = {
        "Iron (Ferrous)": re.compile(
            r"\b(thiếu\s*máu|thiếu\s*sắt|anemia|hemoglobin|huyết\s*sắc\s*tố|ferritin)\b",
            re.IGNORECASE,
        ),
    }

    if drug_candidates:
        words_orig = transcript.split()
        for dc in drug_candidates:
            pos = dc.get("word_position", 0)
            inn = dc.get("inn", "")
            # Filter: patient self-medication context → not a prescription
            pre = " ".join(words_orig[max(0, pos - 5): pos])
            if _RE_PATIENT_MED.search(pre):
                continue
            # Filter: discontinuation instruction ("ngưng X") → not a new prescription
            if re.search(r"\bng[ưừ]ng\b", pre, re.IGNORECASE):
                continue
            # Filter: drugs requiring anemia/iron context — avoid phonetic false positives
            if inn in _CONTEXT_REQUIRED and not _CONTEXT_REQUIRED[inn].search(transcript):
                continue
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
    if m and m.group(2):  # require explicit medical unit (mg, g, ml, mcg, iu, đv)
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

    # PhoWhisper commonly mishears "miligam/mg" as "ml" for oral tablets
    if duong_dung == "uống" and ham_luong.endswith("ml"):
        ham_luong = ham_luong[:-2] + "mg"

    # Southern VN accent: "miligam" → "ký" (kg). Safe to correct for oral route
    # because valid mg/kg pediatric dosing is captured as "X mg trên kg", not "X kg"
    if duong_dung == "uống" and ham_luong.endswith("kg"):
        ham_luong = ham_luong[:-2] + "mg"

    return {
        "inn": inn,
        "ham_luong": ham_luong,
        "so_lan_ngay": so_lan_ngay,
        "so_ngay": so_ngay,
        "duong_dung": duong_dung,
    }
