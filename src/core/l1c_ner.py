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
    r"(?:sốt|nhiệt độ|temp(?:erature)?)\s*(?:là\s*)?[:\s]?\s*"
    r"(\d{2}(?:[.,]\d)?)"
    r"(?:\s+(?:độ\s*)?(\d|một|hai|ba|bốn|năm|sáu|bảy|bẩy|tám|chín))?"  # digit OR VN word; allow "độ" separator
    r"\s*°?(?:c|celsius|độ)?",
    re.IGNORECASE
)
# Fallback: "sốt ba 7.8" after DEC_WORDS normalize "bảy phẩy tám"→"7.8" but "ba" stays as word.
# Also handles: "sốt 3 7.8", "sốt 3 7 phẩy 8" (all digit-by-digit temp readings).
# tens group: VN word (ba/bốn/...) OR already-digit; rest: decimal number already normalized.
_RE_NHIET_DO_SPLIT = re.compile(
    r"(?:sốt|nhiệt độ|temp(?:erature)?)\s*(?:là\s*)?[:\s]?\s*"
    r"(ba|bốn|tư|năm|sáu|bảy|bẩy|tám|chín|\d)\s+"
    r"(\d+(?:[.,]\d)?)",
    re.IGNORECASE
)
_RE_HA_SYSTOLIC = re.compile(
    r"(?:huyết\s*á(?:p)?|HA|BP)\b[^/\d]{0,40}?(\d{2,3})\s*/\s*(\d{2,3})",  # "huyết á" (no p) accepted
    re.IGNORECASE
)
_RE_MACH = re.compile(
    r"(?:mạch|mặc|mặt|mật|pulse|HR)\s*[:\s]?\s*(\d{2,3})\s*(?:lần/phút|bpm|nhịp)?",  # "mặc"/"mặt"/"mật" = PhoWhisper for "mạch"
    re.IGNORECASE
)
_RE_NHIP_THO = re.compile(
    r"(?:nhịp\s*thở|SpR|RR)\s*[:\s]?\s*(\d{1,2})\s*(?:lần/phút)?",
    re.IGNORECASE
)
_RE_CAN_NANG = re.compile(
    r"(?:cân\s*nặng|weight|CN|(?<!\S)nặng)\s*[:\s]?\s*(\d{2,3}(?:[.,]\d)?)\s*(?:k[gý]|kilogram)?",
    re.IGNORECASE
)
_RE_SPO2 = re.compile(
    r"(?:SpO2|spo2|độ\s*bão\s*hòa)\s*[:\s]?\s*(\d{2,3})\s*%?",
    re.IGNORECASE
)

# ─── Đơn thuốc patterns ────────────────────────────────────────────────────

_RE_DOSE_NUMBER = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(mg|g|ml|mcg|iu|đv|kg|milygam|miligam|mililit)",
    re.IGNORECASE,
)
# PhoWhisper hay gộp số và đơn vị: "trămmilygam", "mươimilygam" → cần tách trước normalize
_RE_UNIT_GLUE = re.compile(
    r"(trăm|mười|mươi|một|hai|ba|bốn|năm|sáu|bảy|tám|chín|nghìn|ngàn)"
    r"(milygam|miligam|mg|ml|mcg)",
    re.IGNORECASE,
)
_RE_FREQUENCY = re.compile(
    # Allow "một/1" between "lần" and "ngày": "3 lần một ngày", "3 lần/ngày", "3 lần mỗi ngày"
    r"(\d+)\s*(?:lần|viên|ống|gói)\s*(?:/|mỗi|x|\d+|một)?\s*(?:ngày|day)",
    re.IGNORECASE,
)
# Strong: "trong/uống/dùng N ngày/tuần/tháng" — preferred, unambiguous duration signal
_RE_DURATION_STRONG = re.compile(
    r"(?:trong|uống|dùng)\s*(\d+)\s*(ngày|tuần|tháng)",
    re.IGNORECASE,
)
# Weak fallback: bare "N ngày/tuần" — may match frequency context, only used if strong fails
_RE_DURATION_WEAK = re.compile(
    r"\b(\d+)\s*(ngày|tuần|tháng)\b",
    re.IGNORECASE,
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
    r"(?:t[aá]i\s*kh[aá](?:m|ng)|hẹn\s*lại|follow.?up)\s*(?:sau|after)?\s*(\d+)\s*(ngày|tuần|tháng)"
    r"([^.!?\n]*)",
    re.IGNORECASE
)

# ─── Chẩn đoán patterns ─────────────────────────────────────────────────────

_PRESCRIPTION_KW = (
    r"(?:điều\s*trị|(?:kê|chê|che)\s*(?:đơn|thuốc|toa|là)?|đơn\s*thuốc|toa\s*thuốc|"  # "chê"/"che" = PhoWhisper for "kê"
    r"t[aá]i\s*kh[aá](?:m|ng)|hẹn|follow|cho\s*(?:\w+/?\w*\s*)?(?:uống|dùng))"  # "kháng" = PhoWhisper for "khám"
)
_RE_CHAN_DOAN = re.compile(
    r"(?:chẩn\s*đoán|diagnos\w*)[:\s]+"
    r"(?:(?:theo\s*(?:dõi|thì)|thì)\s+)?"               # "theo dõi"/"theo thì"/bare "thì" (PhoWhisper) filler — skip
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

# "tái khám [disease]" — follow-up visit where diagnosis is stated implicitly.
# e.g. "tái khám tăng huyết áp", "tái khám bệnh đái tháo đường".
# Stops at digits, "đo", sentence breaks — avoids capturing BP measurement text.
_RE_TAI_KHAM_DIAGNOSIS = re.compile(
    r"t[aá]i\s*kh[aá](?:m|ng)\s+(?:bệnh\s+)?"
    r"((?:viêm|tăng|đái|gout|suy|nhồi|thiếu|đau|gãy|loét|rối\s*loạn|hội\s*chứng)"
    r"(?:\s+(?!(?:đo|lần|lúc|bên|bị|kê|\d)\b)\w+){0,3})",
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
# Abbreviated tens (SG shorthand): "sáu lăm"=65, "chín lăm"=95 — "mươi" implied.
# Same as _WSH but used in WCOLLQ context (so named separately for clarity).
_WABR = r"(?:ba|bốn|tư|năm|sáu|bảy|bẩy|tám|chín)\s+(?:lăm|mốt)"
# Colloquial hundreds (spoken in SG/Nam): "một hai mươi"=120, "một sáu lăm"=165
# "một" + standard tens OR abbreviated tens (without "trăm").
_WCOLLQ = r"(?:một)\s+(?:" + _WTG + r"|" + _W10 + r"|" + _WABR + r")"
_WN  = r"(?:" + _WH + r"|" + _WCOLLQ + r"|" + _WTG + r"|" + _W10 + r"|" + _WSH + r")"

_RE_BP_WORDS  = re.compile(r"\b(" + _WN + r")\s+(?:trên|tri)\s+(" + _WN + r")\b", re.I | re.U)
# Digit-form BP with spoken "trên" connector + filler word: "120 trên cao 80" / "120 trên thấp 80" → "120/80"
_RE_BP_DIGITS = re.compile(r"\b(\d{2,3})\s+(?:trên|tri)\s+(?:cao|thấp)?\s*(\d{2,3})\b", re.I | re.U)
_RE_DEC_WORDS = re.compile(r"\b(" + _WN + r"|" + _WO + r")\s+(?:phẩy|chấm)\s+(" + _WO + r")\b", re.I | re.U)  # "chấm" = PhoWhisper alt for "phẩy" (decimal point)
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
    # Standard hundreds: "một trăm hai mươi" = 120
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
    # Colloquial hundreds (SG/Nam): "một hai mươi"=120, "một sáu lăm"=165
    # "một" + tens (without "trăm") — common in casual BP readings
    m = re.match(r"^(một)\s+(.+)$", t, re.UNICODE)
    if m:
        sub = _vn_tens_int(m.group(2))
        if sub is not None:
            return 100 + sub
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

    def _bp_digits(m: re.Match) -> str:
        return f"{m.group(1)}/{m.group(2)}"

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
    r = _RE_BP_DIGITS.sub(_bp_digits, r)
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
    else:
        # Digit-split fallback: "sốt ba 7.8" (DEC_WORDS converted "bảy phẩy tám"→"7.8"
        # but single-word "ba" stays unconverted). Handles SG colloquial digit-by-digit temp.
        m2 = _RE_NHIET_DO_SPLIT.search(t)
        if m2:
            tens_raw = m2.group(1).strip()
            tens = int(tens_raw) if tens_raw.isdigit() else _VN_ONES.get(tens_raw.lower(), 0)
            rest = float(m2.group(2).replace(",", "."))
            ent.nhiet_do = tens * 10 + rest

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

    # Chẩn đoán — try explicit keyword first, then tái-khám hint, then general fallback
    m = _RE_CHAN_DOAN.search(t)
    if m:
        ent.chan_doan = m.group(1).strip()
    else:
        # Check "tái khám [disease]" before general fallback — avoids matching drug phrases
        m = _RE_TAI_KHAM_DIAGNOSIS.search(t)
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
    # Split concatenated VN number+unit before normalize ("trămmilygam" → "trăm milygam")
    context_raw = _RE_UNIT_GLUE.sub(r"\1 \2", context_raw)
    context = _normalize_vn_numbers(context_raw)

    ham_luong = ""
    m = _RE_DOSE_NUMBER.search(context)
    if m and m.group(2):  # require explicit medical unit
        ham_luong = m.group(0).strip()
        # Normalize unit variants to standard abbreviations
        ham_luong = (ham_luong
                     .replace("milygam", "mg").replace("miligam", "mg")
                     .replace("mililit", "ml"))

    so_lan_ngay = ""
    m = _RE_FREQUENCY.search(context)
    if m:
        so_lan_ngay = m.group(0).strip()

    so_ngay = 0
    m = _RE_DURATION_STRONG.search(context)
    if m:
        try:
            val = int(m.group(1))
            unit = m.group(2).lower()
            so_ngay = val * (7 if "tuần" in unit else 30 if "tháng" in unit else 1)
        except (ValueError, IndexError):
            pass
    else:
        # Take max across all weak matches to avoid "1 ngày" from frequency context
        # (e.g., "3 lần 1 ngày trong 4 tuần" → max(1, 28) = 28)
        for m2 in _RE_DURATION_WEAK.finditer(context):
            try:
                val = int(m2.group(1))
                unit = m2.group(2).lower()
                candidate = val * (7 if "tuần" in unit else 30 if "tháng" in unit else 1)
                if candidate > so_ngay:
                    so_ngay = candidate
            except (ValueError, IndexError):
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


# ─── Hybrid NER (FID-VN-009) ──────────────────────────────────────────────────

def _get_filled_fields(entities: MedicalEntities) -> list[str]:
    """List non-empty MedicalEntities fields for meta reporting."""
    filled = []
    if entities.ly_do:
        filled.append("ly_do")
    if entities.trieu_chung:
        filled.append("trieu_chung")
    if entities.nhiet_do is not None:
        filled.append("nhiet_do")
    if entities.huyet_ap_tam_thu is not None:
        filled.append("huyet_ap")
    if entities.mach is not None:
        filled.append("mach")
    if entities.chan_doan:
        filled.append("chan_doan")
    if entities.don_thuoc:
        filled.append("don_thuoc")
    if entities.tai_kham:
        filled.append("tai_kham")
    return filled


def extract_entities_hybrid(
    transcript: str,
    drug_candidates: list[dict] | None = None,
    use_phobert: bool = False,
) -> tuple[MedicalEntities, dict]:
    """
    Hybrid NER: rule-based PRIMARY + PhoBERT SUPPLEMENT (opt-in).

    Architecture: PARALLEL + optional early-exit (FID-VN-009, CONS-20260610-003).
    Returns (entities, meta).

    meta keys:
        rule_fields_filled: list[str]
        phobert_fields_added: list[str]
        phobert_confidence_avg: float
        phobert_used: bool
        phobert_vital_detected: list[str]   — log only, not written to entities
        early_exit: bool                    — True if PhoBERT skipped (no gap)
    """
    # Lazy import to avoid circular dependency at module level
    from src.core.l1c_phobert import (
        bio_to_updates,
        has_coverage_gap,
        normalize_symptom,
        predict_entities,
        PHOBERT_CONFIDENCE_MIN,
    )

    # Step 1: Rule-based (always runs)
    entities = extract_entities(transcript, drug_candidates)

    meta: dict = {
        "rule_fields_filled": _get_filled_fields(entities),
        "phobert_fields_added": [],
        "phobert_confidence_avg": 0.0,
        "phobert_used": False,
        "phobert_vital_detected": [],
        "early_exit": False,
    }

    if not use_phobert:
        return entities, meta

    # Step 2: Optional early-exit when rule-based already covers contextual fields
    if not has_coverage_gap(entities):
        meta["early_exit"] = True
        return entities, meta

    # Step 3: PhoBERT inference (lazy load, graceful fallback)
    try:
        predictions = predict_entities(transcript)
    except FileNotFoundError:
        return entities, meta

    updates, vital_detected = bio_to_updates(predictions, transcript)
    meta["phobert_vital_detected"] = vital_detected

    all_scores = [
        p.get("score", 0.0)
        for p in predictions
        if p.get("score", 0.0) >= PHOBERT_CONFIDENCE_MIN
    ]
    meta["phobert_confidence_avg"] = (
        sum(all_scores) / len(all_scores) if all_scores else 0.0
    )
    meta["phobert_used"] = True

    added_fields: list[str] = []

    # Merge trieu_chung — UNION with normalized dedup (R-009-08)
    existing_norm = {normalize_symptom(s) for s in entities.trieu_chung}
    for symptom in updates["trieu_chung_add"]:
        norm = normalize_symptom(symptom)
        if norm not in existing_norm:
            entities.trieu_chung.append(symptom)
            existing_norm.add(norm)
            if "trieu_chung" not in added_fields:
                added_fields.append("trieu_chung")

    # Merge tai_kham — PhoBERT fills only when rule-based left it empty
    if not entities.tai_kham and updates["tai_kham_fill"]:
        entities.tai_kham = updates["tai_kham_fill"]
        added_fields.append("tai_kham")

    # Merge don_thuoc — SUPPLEMENT with strict INN dedup (R-009-10)
    existing_inns = {d.get("inn", "").lower() for d in entities.don_thuoc}
    for drug in updates["don_thuoc_supplement"]:
        inn_key = drug.get("inn", "").lower()
        if inn_key not in existing_inns:
            entities.don_thuoc.append({
                "inn": drug["inn"],
                "ham_luong": drug.get("ham_luong", ""),
                "so_lan_ngay": drug.get("so_lan_ngay", ""),
                "so_ngay": drug.get("so_ngay", 0),
                "duong_dung": drug.get("duong_dung", "uống"),
                "flagged_for_review": True,
                "flag_source": "phobert_supplement",
            })
            existing_inns.add(inn_key)
            if "don_thuoc" not in added_fields:
                added_fields.append("don_thuoc")

    meta["phobert_fields_added"] = added_fields
    return entities, meta
