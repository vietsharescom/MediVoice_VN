# src/core/dvp_alias.py
# DVP Layer 3 — Personal Drug Alias promotion logic (FID-VN-012)
# Passive learning from L4 correction capture → alias candidates → BS confirm Human Gate
# Luật KCB 2023 Đ.62: BS confirm trước khi alias active — KHÔNG bypass

from __future__ import annotations
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Promotion thresholds (FID-VN-012 §2)
MIN_OCCURRENCES = 3
MIN_SESSIONS = 2


def check_and_promote(
    cchn: str,
    db_path: Path | None = None,
) -> list[dict]:
    """
    Kiểm tra aliases đủ điều kiện promote cho BS này.
    Trả về list alias candidates (pending confirm) nếu có.
    Caller (main.py) hiển thị notification cho BS.

    Returns: list of {alias_id, alias_text, inn, occurrence_count, session_count}
    """
    from .l7_storage import get_pending_aliases
    pending = get_pending_aliases(cchn, db_path)
    result = []
    for alias in pending:
        result.append({
            "alias_id":       alias.id,
            "alias_text":     alias.alias_text,
            "inn":            alias.inn,
            "occurrence_count": alias.occurrence_count,
            "session_count":  alias.session_count,
            "message": (
                f"Trợ lý học được: [{alias.alias_text}] = {alias.inn} "
                f"({alias.occurrence_count} lần / {alias.session_count} phiên). Xác nhận?"
            ),
        })
    return result


def apply_active_aliases(
    transcript: str,
    cchn: str,
    db_path: Path | None = None,
) -> tuple[str, list[str]]:
    """
    Áp dụng confirmed aliases của BS vào transcript trước khi L1b.
    Returns: (modified_transcript, list_of_substitutions_made)
    """
    from .l7_storage import get_active_aliases
    import re

    aliases = get_active_aliases(cchn, db_path)
    if not aliases:
        return transcript, []

    result = transcript
    subs: list[str] = []
    # Sort by alias length desc — longer first to avoid partial matches
    for alias in sorted(aliases, key=lambda a: len(a.alias_text), reverse=True):
        pattern = re.compile(
            rf'(?<!\w){re.escape(alias.alias_text)}(?!\w)', re.IGNORECASE
        )
        new_result, count = pattern.subn(alias.inn, result)
        if count > 0:
            subs.append(f"{alias.alias_text} → {alias.inn}")
            result = new_result
    return result, subs


def record_correction(
    cchn: str,
    ai_drug: str,
    bs_drug: str,
    session_id: str,
    transcript_fragment: str = "",
    db_path: Path | None = None,
) -> None:
    """
    Ghi nhận một L4 correction (AI đề xuất ai_drug → BS sửa thành bs_drug).
    Tìm alias_text trong transcript_fragment → ghi vào doctor_aliases.
    Nếu không tìm được fragment → skip (không ép data).
    """
    from .l7_storage import save_alias_occurrence
    import re

    # Tìm từ nào trong transcript dẫn đến ai_drug bị sửa thành bs_drug
    # Heuristic: tìm token gần nhất trước/sau ai_drug (phonetically)
    if transcript_fragment:
        # Dùng ai_drug làm anchor — tìm token ~phonetic trong transcript
        tokens = re.split(r'\s+', transcript_fragment.lower())
        # Nếu ai_drug có trong transcript → đó là alias candidate
        ai_lower = ai_drug.lower()
        for tok in tokens:
            if tok and tok != bs_drug.lower() and (
                ai_lower.startswith(tok[:3]) or tok.startswith(ai_lower[:3])
            ):
                save_alias_occurrence(cchn, tok, bs_drug, session_id, db_path)
                logger.debug("DVP alias recorded: %s → %s for BS %s", tok, bs_drug, cchn)
                return

    # Fallback: lưu ai_drug làm alias → bs_drug
    if ai_drug and bs_drug and ai_drug.lower() != bs_drug.lower():
        save_alias_occurrence(cchn, ai_drug.lower(), bs_drug, session_id, db_path)
        logger.debug("DVP alias fallback: %s → %s for BS %s", ai_drug, bs_drug, cchn)
