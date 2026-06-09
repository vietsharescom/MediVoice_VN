# src/core/dialect_norm.py
# A3-DIALECT-NORM + A3b-ABBREV-EXPAND — FID-VN-010
# Map từ vùng miền → tiếng Việt chuẩn TRƯỚC khi vào NER.
# ⚠️ CRITICAL: "ốm" = bệnh (Trung) ≠ "ốm" = gầy (Nam) — đọc facility.region trước.

from __future__ import annotations
import re

# ---------------------------------------------------------------------------
# DIALECT_MAP — 200+ entries
# Thứ tự quan trọng: multi-word trước single-word trong apply
# ---------------------------------------------------------------------------

DIALECT_MAP: dict[str, dict[str, str]] = {

    # ── MIỀN TRUNG (Đà Nẵng, Huế, Quảng Nam, Quảng Ngãi) ──────────────────
    "central": {
        # Multi-word phrases (apply trước)
        "bây chừ": "bây giờ",
        "cấy chi": "cái gì",
        "răng ri": "như thế nào",
        "mô rứa": "ở đâu vậy",
        "rứa hỉ": "vậy nhỉ",
        "bao chừ": "bao giờ",
        "răng nữa": "còn sao nữa",
        "mô chừ": "đâu rồi",
        "đau bụng dưới": "đau vùng hạ vị",
        "bụng dạ": "bụng",
        "nước biển": "dịch truyền",  # clinical
        "chừa thuốc": "ngừng thuốc",
        "thuốc đau đầu": "thuốc giảm đau đầu",
        "mạnh giỏi": "khoẻ mạnh",
        "ít bữa": "vài ngày",
        "bữa ni": "hôm nay",
        "bữa qua": "hôm qua",
        "bữa kia": "ngày kia",
        "mấy bữa ni": "mấy ngày này",
        "tự dưng": "đột ngột",
        "lâu ni": "lâu nay",

        # Single-word — pronouns & demonstratives
        "tui": "tôi",
        "ni": "này",
        "nớ": "đó",
        "tê": "kia",
        "eng": "anh",
        "ả": "chị",
        "hắn": "anh ấy",
        "bọn hắn": "họ",

        # Question words
        "mô": "đâu",
        "răng": "sao",
        "rứa": "vậy",
        "hỉ": "nhỉ",
        "chi": "gì",
        "chừ": "giờ",

        # Verbs
        "mần": "làm",
        "ngó": "nhìn",
        "nói chuyện": "nói chuyện",
        "chừng": "khoảng",
        "ri": "thế này",
        "chứ": "chứ",
        "biết mô": "không biết",

        # Adjectives / adverbs
        "tra": "già",
        "mạnh": "khoẻ",

        # Nouns (body / daily)
        "nác": "nước",
        "đọi": "bát",
        "nác": "nước",

        # ⚠️ CRITICAL semantic trap
        "ốm": "bệnh",   # Trung: ốm = bệnh (sick) — KHÔNG phải gầy

        # Clinical symptom normalizations
        "tức ngực": "đau tức ngực",
        "đau bụng": "đau bụng",
        "nhức đầu": "đau đầu",
        "nhức mình": "đau người",
        "nóng người": "sốt",
        "lạnh run": "ớn lạnh",
        "mệt trong mình": "mệt mỏi",
        "chóng mặt": "chóng mặt",
        "buồn nôn": "buồn nôn",
        "ỉa chảy": "tiêu chảy",
        "đái dắt": "tiểu buốt",
        "tiểu buốt": "tiểu buốt",
        "nước tiểu vàng": "nước tiểu vàng đậm",
        "ho có đờm": "ho đờm",
        "khó thở": "khó thở",
        "đánh trống ngực": "hồi hộp",

        # Time expressions
        "bữa": "ngày",
        "tháng ni": "tháng này",
        "tuần ni": "tuần này",
        "hôm ni": "hôm nay",
        "tối ni": "tối nay",
        "sáng ni": "sáng nay",

        # Frequency / dosage
        "ngày đôi lần": "ngày 2 lần",
        "ngày ba lần": "ngày 3 lần",
        "sáng tối": "sáng và tối",
    },

    # ── MIỀN NAM (Sài Gòn, Cần Thơ, Kiên Giang, Long An) ──────────────────
    "southern": {
        # Multi-word phrases
        "bệnh nhân nói": "bệnh nhân cho biết",
        "hổng có": "không có",
        "hổng biết": "không biết",
        "hổng được": "không được",
        "hổng thấy": "không thấy",
        "thôi thì": "thì",
        "ít ít": "một chút",
        "vô đây": "vào đây",
        "hồi đó": "trước đây",
        "hồi nào": "khi nào",
        "hồi xưa": "trước đây",
        "lúc đó": "lúc đó",
        "mấy bữa nay": "mấy ngày nay",
        "hổng thấy đỡ": "không thấy giảm",
        "uống thuốc vô": "uống thuốc",
        "đau quá trời": "đau rất nhiều",
        "nặng quá trời": "nặng rất nhiều",

        # Negation
        "hổng": "không",
        "hỏng": "không",
        "hổng phải": "không phải",

        # Movement
        "dzô": "vào",
        "vô": "vào",
        "ra": "ra",

        # Pronouns
        "tui": "tôi",
        "ổng": "ông ấy",
        "bả": "bà ấy",
        "ảnh": "anh ấy",
        "chỉ": "chị ấy",
        "tụi nó": "họ",
        "tụi tôi": "chúng tôi",
        "mình": "tôi",

        # Particles / endings
        "hen": "nhé",
        "nghen": "nhé",
        "nha": "nhé",
        "nè": "này",
        "vậy đó": "vậy",
        "thôi": "rồi",
        "á": "à",
        # NOTE: "ha" (interjection "hả?") bị bỏ khỏi map — conflict với medical_abbrev "ha"="huyết áp"
        # medical_abbrev expand_abbreviations() sẽ xử lý "ha" trong context số (ví dụ "ha 120/80")

        # ⚠️ CRITICAL semantic trap
        "ốm": "gầy",        # Nam: ốm = gầy (thin) — KHÔNG phải bệnh

        # Clinical terms (Nam variants)
        "xỉu": "ngất",
        "ngất xỉu": "ngất xỉu",
        "quặn bụng": "đau quặn bụng",
        "sổ mũi": "chảy mũi",
        "sổ": "chảy",
        "chảy nước mắt": "chảy nước mắt",
        "nhức đầu": "đau đầu",
        "bịnh": "bệnh",
        "bịnh nhân": "bệnh nhân",
        "uống": "uống",
        "chích": "tiêm",
        "chích thuốc": "tiêm thuốc",
        "lên cơn": "cơn",
        "khỏe re": "khoẻ tốt",
        "mệt quá": "mệt nhiều",
        "ói mửa": "nôn mửa",
        "ói": "nôn",
        "chóng mặt": "chóng mặt",
        "bụng đau": "đau bụng",
        "tiêu lỏng": "tiêu chảy",
        "đi cầu": "đại tiện",
        "đi tiểu": "tiểu tiện",

        # Dosage / frequency
        "uống sáng chiều tối": "uống 3 lần/ngày",
        "sáng chiều": "ngày 2 lần",

        # Body parts (Nam colloquial)
        "cổ họng": "họng",
        "lồng ngực": "ngực",
    },

    # ── MIỀN BẮC (Hà Nội, Hải Phòng, Thanh Hoá) ───────────────────────────
    "northern": {
        # Bắc gần chuẩn nhất — chỉ map các từ địa phương nổi bật
        "tớ": "tôi",
        "mình": "tôi",
        "nhá": "nhé",
        "tẹo": "một chút",
        "đau bỏ mẹ": "đau rất nhiều",
        "đau vãi": "đau nhiều",
        "sắp chết": "rất tệ",  # hyperbole in Northern speech
        "đêm qua": "đêm qua",
        "hôm kia": "hôm kia",
        "bữa kia": "hôm kia",
        "chả": "chẳng",
        "chả biết": "không biết",
        "chả thấy": "không thấy",
        "chả sao": "không sao",
        "kinh": "rất",
        "đau kinh": "đau nhiều",
        "đau lắm": "đau nhiều",
        "khó ở": "khó chịu",
        "uể oải": "mệt mỏi",
        "ậm ọe": "buồn nôn",
        "buồn nôn": "buồn nôn",
        "oẹ": "nôn",
    },

    # ── MEDICAL ABBREVIATIONS (tất cả vùng) ────────────────────────────────
    # Expand SAU dialect normalization (A3b)
    "medical_abbrev": {
        # Vitals
        "ha": "huyết áp",
        "mch": "mạch",
        "nhiet do": "nhiệt độ",
        "nđ": "nhiệt độ",
        "spo2": "độ bão hoà oxy",
        "bmi": "chỉ số khối cơ thể",

        # Patient / workflow
        "bn": "bệnh nhân",
        "tk": "tái khám",
        "bv": "bệnh viện",
        "pk": "phòng khám",
        "bs": "bác sĩ",
        "dd": "dạ dày",
        "tn": "tai nạn",

        # Tests / imaging
        "xn": "xét nghiệm",
        "sa": "siêu âm",
        "xq": "x-quang",
        "ct": "chụp cắt lớp",
        "mri": "chụp cộng hưởng từ",
        "ecg": "điện tâm đồ",
        "ekg": "điện tâm đồ",

        # Diagnoses
        "đtđ": "đái tháo đường",
        "tha": "tăng huyết áp",
        "tmct": "nhồi máu cơ tim",
        "copd": "bệnh phổi tắc nghẽn mãn tính",
        "gerd": "trào ngược dạ dày thực quản",
        "uti": "nhiễm trùng đường tiểu",
        "hiv": "hiv",
        "tb": "lao phổi",
        "suy tim": "suy tim",
        "rltm": "rối loạn tiêu hoá",

        # Blood counts
        "hc": "hồng cầu",
        "bc": "bạch cầu",
        "tc": "tiểu cầu",
        "hgb": "huyết sắc tố",
        "hct": "hematocrit",
        "wbc": "bạch cầu",
        "rbc": "hồng cầu",

        # Lifestyle
        "htl": "hút thuốc lá",
        "bu": "béo phì",
        "tktw": "không thuốc lá không rượu",

        # Drug frequency (abbreviations in prescriptions)
        "tid": "3 lần mỗi ngày",
        "bid": "2 lần mỗi ngày",
        "qd": "1 lần mỗi ngày",
        "prn": "khi cần",
        "ac": "trước ăn",
        "pc": "sau ăn",
        "hs": "trước khi ngủ",
        "po": "uống",
        "iv": "tiêm tĩnh mạch",
        "im": "tiêm bắp",
    },
}

# Markers dùng để auto-detect region
_CENTRAL_MARKERS: frozenset[str] = frozenset({
    "mô", "răng", "rứa", "hỉ", "ni", "nớ", "tê", "nác", "đọi", "mần",
    "bây chừ", "cấy chi", "răng ri",
})
_SOUTHERN_MARKERS: frozenset[str] = frozenset({
    "hổng", "dzô", "ổng", "bả", "hen", "nghen", "nha", "nè",
    "ảnh", "chỉ", "bịnh", "ói", "chích",
})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_region(text: str) -> str:
    """
    Auto-detect dialect region từ nội dung text.
    Returns: "central" | "southern" | "northern" (fallback).
    """
    text_lower = text.lower()
    central_score = sum(1 for m in _CENTRAL_MARKERS if m in text_lower)
    southern_score = sum(1 for m in _SOUTHERN_MARKERS if m in text_lower)

    if central_score > southern_score:
        return "central"
    if southern_score > central_score:
        return "southern"
    return "northern"


def normalize_dialect(text: str, region: str = "auto") -> tuple[str, list[str]]:
    """
    Normalize dialect tokens về tiếng Việt chuẩn.
    region: "central" | "southern" | "northern" | "auto"
    Returns: (normalized_text, substitutions_made)
    substitutions_made dùng để hiển thị dialect badge trong UI.
    ⚠️ "ốm" được xử lý đúng theo region (bệnh vs gầy).
    """
    if region == "auto":
        region = detect_region(text)

    dialect_entries = DIALECT_MAP.get(region, {})

    result = text
    subs: list[str] = []

    # Sort by length descending — multi-word phrases trước
    sorted_entries = sorted(dialect_entries.items(), key=lambda x: len(x[0]), reverse=True)

    for src, dst in sorted_entries:
        if src == dst:
            continue
        pattern = re.compile(rf'(?<!\w){re.escape(src)}(?!\w)', re.IGNORECASE)
        new_result, count = pattern.subn(dst, result)
        if count > 0:
            subs.append(f"{src} → {dst}")
            result = new_result

    return result, subs


def expand_abbreviations(text: str) -> str:
    """
    Expand medical abbreviations (A3b) — áp dụng SAU normalize_dialect().
    Word-boundary match để không thay "ha" trong "hành", "thay", v.v.
    """
    abbrevs = DIALECT_MAP["medical_abbrev"]
    result = text

    # Sort by length descending — longer abbrevs first
    for abbr, expansion in sorted(abbrevs.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(rf'\b{re.escape(abbr)}\b', re.IGNORECASE)
        result = pattern.sub(expansion, result)

    return result


def normalize_text(text: str, region: str = "auto") -> tuple[str, list[str]]:
    """
    Full A3 pipeline: dialect normalization → abbreviation expansion.
    Returns: (fully_normalized_text, substitutions_made)
    Convenience wrapper gọi từ pipeline.
    """
    normalized, subs = normalize_dialect(text, region)
    expanded = expand_abbreviations(normalized)
    return expanded, subs
