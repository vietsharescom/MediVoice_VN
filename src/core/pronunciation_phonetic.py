# src/core/pronunciation_phonetic.py
# FID-VN-015 §3.1/Q4 — Phiên âm tiếng Việt cho tên thuốc (Pronunciation
# Recognition Lab — Part 3)
#
# Pure functions, KHÔNG động tới pipeline L0->L10 (FROZEN). Sinh "phiên âm
# tiếng Việt" tham khảo cho audio mẫu (gTTS) + so khớp transcript BS đọc.
#
# Heuristic transliteration v1 (Claude generate, Andy review sau — FID-VN-015
# Q4). Nếu drug_db đã có 1 brand variant kiểu "para xê ta môn" (lowercase,
# nhiều âm tiết cách nhau bằng dấu cách, khác INN gốc) thì ưu tiên dùng variant
# đó (đã được con người ghi nhận, đáng tin hơn heuristic).

from __future__ import annotations

import re

_VOWELS = set("aeiouyăâêôơư")

# Thay thế nhiều ký tự (áp dụng trước, theo thứ tự) — ánh xạ cách đọc tiếng
# Anh/Pháp phổ biến trong tên thuốc sang chữ viết kiểu tiếng Việt.
_MULTI_SUBS = [
    (re.compile(r"c([eiy])"), r"x\1"),   # "ce/ci/cy" -> "xe/xi/xy" (âm /s/)
    (re.compile(r"ph"), "ph"),           # giữ nguyên (đã giống cách đọc VN)
    (re.compile(r"qu"), "qu"),           # giữ nguyên
    (re.compile(r"th"), "th"),           # giữ nguyên
    (re.compile(r"ch"), "ch"),           # giữ nguyên
    (re.compile(r"sh"), "s"),
    (re.compile(r"^f"), "ph"),           # "f" đầu từ -> "ph"
    (re.compile(r"f"), "ph"),
]

# Thay thế từng ký tự đơn (sau khi đã xử lý multi-char ở trên)
_SINGLE_SUBS = {
    "e": "ê",
    "o": "ô",
    "j": "gi",
    "z": "d",
    "w": "v",
}

# Phụ âm cuối tiếng Việt không có "l" — chuyển thành "n"
_FINAL_CONSONANT_SUBS = {"l": "n"}


def _apply_substitutions(name: str) -> str:
    s = name.lower()
    for pattern, repl in _MULTI_SUBS:
        s = pattern.sub(repl, s)
    s = "".join(_SINGLE_SUBS.get(ch, ch) for ch in s)
    if s and s[-1] in _FINAL_CONSONANT_SUBS:
        s = s[:-1] + _FINAL_CONSONANT_SUBS[s[-1]]
    return s


def _syllabify(s: str) -> list[str]:
    """
    Tách chuỗi đã transliterate thành các "âm tiết" kiểu VN: mỗi âm tiết gồm
    (phụ âm đầu tùy chọn) + (nguyên âm) + (phụ âm cuối tùy chọn, chỉ khi
    không còn nguyên âm nào theo sau cần phụ âm đầu).
    """
    n = len(s)
    syllables: list[str] = []
    current = ""
    i = 0
    while i < n:
        c = s[i]
        current += c
        if c in _VOWELS:
            j = i + 1
            while j < n and s[j] in _VOWELS:
                current += s[j]
                j += 1
            cons_start = j
            while j < n and s[j] not in _VOWELS:
                j += 1
            cons = s[cons_start:j]
            if j < n:
                # Còn nguyên âm theo sau -> phụ âm cuối cùng làm âm đầu âm
                # tiết tiếp theo, các phụ âm còn lại (nếu có) làm âm cuối.
                if len(cons) >= 2:
                    current += cons[:-1]
                syllables.append(current)
                current = cons[-1] if cons else ""
                i = j
                continue
            else:
                current += cons
                syllables.append(current)
                current = ""
                i = j
                continue
        i += 1
    if current:
        syllables.append(current)
    return syllables


def transliterate_to_vn_phonetic(name: str) -> str:
    """
    Sinh phiên âm tiếng Việt heuristic cho 1 tên thuốc/thuật ngữ (vd
    "Paracetamol" -> "pa ra xê ta môn"). Chỉ giữ chữ cái a-z, bỏ khoảng trắng/
    dấu/ký tự khác. Trả về "" nếu input rỗng/không có chữ cái.
    """
    cleaned = re.sub(r"[^a-zA-Z]", "", name)
    if not cleaned:
        return ""
    transformed = _apply_substitutions(cleaned)
    syllables = _syllabify(transformed)
    return " ".join(syllables)


def get_pronunciation_en(inn: str, drug_entry: dict | None = None) -> str | None:
    """
    FID-VN-016 §1 — phiên âm chuẩn y dược thế giới (kiểu USAN respelling, vd
    "par-a-SEE-ta-mol"), dòng 1 hiển thị Wizard. Lấy từ field `pronunciation_en`
    trong drug_db (pilot subset, có nguồn AMA/USP USAN — xem CT-039).
    Trả None nếu thuốc chưa có data (Phase B sẽ bổ sung dần).
    """
    if drug_entry:
        value = drug_entry.get("pronunciation_en")
        if value:
            return value
    return None


def is_garbled_transcript(transcript: str, expected_inn: str) -> bool:
    """
    FID-VN-016 §1 — phát hiện transcript đọc lặp nhiều lần/nhiều biến thể
    trong 1 lần ghi âm (vd BS đọc thử 4-5 lần liên tiếp). Heuristic: số từ
    trong transcript vượt quá 3 lần số âm tiết kỳ vọng của INN.
    Trả True -> Wizard yêu cầu đọc lại 1 lần duy nhất, KHÔNG đề xuất alias.
    """
    words = transcript.strip().split()
    if not words:
        return False

    expected_syllables = max(1, len(transliterate_to_vn_phonetic(expected_inn).split()))
    return len(words) > 3 * expected_syllables


def apply_stress_hint(vn_phonetic: str, pronunciation_en: str | None) -> str:
    """
    FID-VN-017 §2 — gợi ý trọng âm: ánh xạ vị trí âm tiết viết HOA trong
    `pronunciation_en` (vd "par-a-SEE-ta-mol") sang âm tiết tương ứng trong
    `vn_phonetic` (vd "pa ra xê ta môn" -> "pa ra XÊ ta môn"), theo tỉ lệ vị
    trí (idx_en/total_en ~ idx_vn/total_vn). Heuristic, không chính xác tuyệt
    đối — chỉ là gợi ý "đọc nhấn vào đây".

    Trả nguyên `vn_phonetic` nếu `pronunciation_en` rỗng/None hoặc không tìm
    thấy âm tiết viết HOA.
    """
    if not pronunciation_en:
        return vn_phonetic

    en_segments = pronunciation_en.split("-")
    total_en = len(en_segments)
    idx_en = next(
        (i for i, seg in enumerate(en_segments) if any(c.isupper() for c in seg)),
        None,
    )
    if idx_en is None or total_en == 0:
        return vn_phonetic

    vn_syllables = vn_phonetic.split()
    total_vn = len(vn_syllables)
    if total_vn == 0:
        return vn_phonetic

    idx_vn = round((idx_en / total_en) * total_vn)
    idx_vn = max(0, min(total_vn - 1, idx_vn))

    vn_syllables[idx_vn] = vn_syllables[idx_vn].upper()
    return " ".join(vn_syllables)


def get_reference_phonetic(
    inn: str,
    drug_entry: dict | None = None,
    pronunciation_en: str | None = None,
) -> str:
    """
    Lấy phiên âm chuẩn cho 1 INN, theo thứ tự ưu tiên:
      1. Brand variant đã có trong drug_db (kiểu "para xê ta môn", lowercase,
         nhiều âm tiết cách nhau bằng dấu cách).
      2. `phonetic_variants.north[0]` trong drug_db (đã được con người ghi
         nhận theo giọng đọc thực tế — tránh các cụm phụ âm tiếng Anh không
         tồn tại trong tiếng Việt mà heuristic transliteration tạo ra, vd
         "Azithromycin" -> "a dith rô my xin" KHÔNG đọc được, trong khi
         `phonetic_variants.north` đã có sẵn "a zi thro my xin").
      3. Heuristic transliteration trên từ đầu tiên của INN (vd "Aspirin
         (Acetylsalicylic acid)" -> "Aspirin") — chỉ dùng khi drug_db chưa có
         dữ liệu nào ở trên.

    FID-VN-017 §2 — nếu `pronunciation_en` được truyền vào, áp
    `apply_stress_hint()` lên kết quả trước khi trả về (gợi ý trọng âm).
    """
    if drug_entry:
        for brand in drug_entry.get("brands", []):
            if (
                " " in brand
                and brand == brand.lower()
                and brand != inn.lower()
                and re.fullmatch(r"[a-zàáảãạăâêôơưđ\s]+", brand)
            ):
                return apply_stress_hint(brand, pronunciation_en)

        north_variants = drug_entry.get("phonetic_variants", {}).get("north")
        if north_variants:
            return apply_stress_hint(north_variants[0], pronunciation_en)

    first_word = re.split(r"[\s(]", inn.strip())[0]
    return apply_stress_hint(transliterate_to_vn_phonetic(first_word), pronunciation_en)
