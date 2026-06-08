"""
MediVoice VN — RAG Chain
Audio transcript → L1b drug correction → LangChain NER → L1d ICD lookup
"""
from __future__ import annotations
import sys
import logging
from pathlib import Path

# Repo root so we can import src.core.*
_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

logger = logging.getLogger(__name__)

# ── Optional src imports (graceful fallback if env is incomplete) ─────────────

try:
    from src.core.l1b_drug_correct import correct_drug_names_v2, DrugMatch
    _L1B_OK = True
except Exception as _e:
    logger.warning("L1b unavailable: %s — skipping drug pre-correction", _e)
    _L1B_OK = False

try:
    from src.core.l1d_icd_lookup import search_by_text as _icd_search
    _L1D_OK = True
except Exception as _e:
    logger.warning("L1d unavailable: %s — skipping ICD enhancement", _e)
    _L1D_OK = False

# ── ICD quick-reference (primary care top-30) ─────────────────────────────────
# Used in NER prompt so LLM has grounding. Supplement to L1d full database.

_ICD_QUICK = [
    ("Tăng huyết áp nguyên phát",                    "I10"),
    ("Tăng huyết áp kèm rối loạn lipid máu",         "I10, E78.5"),
    ("Đái tháo đường type 2",                         "E11.9"),
    ("Rối loạn lipid máu",                            "E78.5"),
    ("Viêm phổi cộng đồng",                          "J18.9"),
    ("Nhiễm siêu vi đường hô hấp trên",              "J06.9"),
    ("Viêm amidan cấp",                               "J03.9"),
    ("Viêm phế quản cấp",                             "J20.9"),
    ("Hen phế quản",                                  "J45.9"),
    ("Viêm dạ dày",                                   "K29.7"),
    ("Trào ngược dạ dày thực quản",                   "K21.0"),
    ("Thoát vị đĩa đệm cột sống thắt lưng",          "M51.1"),
    ("Đau thần kinh tọa",                             "M54.4"),
    ("Viêm khớp dạng thấp",                          "M06.9"),
    ("Gout cấp",                                      "M10.9"),
    ("Trầm cảm nhẹ",                                  "F32.0"),
    ("Rối loạn lo âu lan tỏa",                        "F41.1"),
    ("Mề đay cấp",                                    "L50.0"),
    ("Viêm da dị ứng",                                "L20.9"),
    ("Thiếu máu",                                     "D64.9"),
    ("Suy giáp",                                      "E03.9"),
    ("Cường giáp",                                    "E05.9"),
    ("Đau đầu căng thẳng",                            "G44.2"),
    ("Đau nửa đầu Migraine",                          "G43.9"),
    ("Nhiễm trùng tiểu",                              "N39.0"),
    ("Viêm khớp gối",                                 "M17.9"),
    ("Thoái hóa cột sống",                            "M47.9"),
    ("Viêm gan B mạn tính",                           "B18.1"),
    ("Sốt xuất huyết Dengue",                         "A97.0"),
    ("Viêm tai giữa cấp",                             "H66.0"),
]

_ICD_CONTEXT_STR = "Bảng ICD-10-VN hay gặp:\n" + "\n".join(
    f"  {diag} → {code}" for diag, code in _ICD_QUICK
)

# ── NER Prompt ────────────────────────────────────────────────────────────────

_NER_TEMPLATE = """\
Bạn là AI phân tích bệnh án y tế tiếng Việt. \
Xử lý lời nói tự nhiên của bác sĩ trong phòng khám.

QUY TẮC:
1. BỎ QUA: chào hỏi xã giao, câu chuyện phiếm, tiếng ừ/à/hmm
2. Thông tin BN: trích xuất tên/tuổi/giới nếu BS đề cập
3. Sinh hiệu: để 0 hoặc "" nếu không được đề cập
4. Tên thuốc: đã được AI chuẩn hóa trước — dùng đúng tên trong transcript
5. ICD-10: tham khảo bảng dưới. Chỉ điền khi chắc chắn.
6. "ngay" để "" nếu BS nói "khi cần" hoặc không nói số ngày
7. Chỉ trả về JSON — không giải thích thêm

{icd_context}

{drug_context}

TRANSCRIPT (đã qua drug correction):
{transcript}

JSON:
{{
  "benh_nhan": {{"ten": "", "tuoi": 0, "gioi": "Nam/Nữ/Không rõ", "nam_sinh": ""}},
  "ly_do": "",
  "chan_doan": "",
  "icd": "",
  "sinh_hieu": {{"nhiet_do": 0, "huyet_ap": "", "mach": 0, "can_nang": 0}},
  "don_thuoc": [{{"ten": "", "ham_luong": "", "lieu": "", "ngay": ""}}],
  "tai_kham": ""
}}"""

# ── Chain builder ─────────────────────────────────────────────────────────────

def build_chain(api_key: str):
    """Build and return the LangChain NER chain. Cached per api_key call."""
    llm = ChatGroq(
        api_key=api_key,
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        max_tokens=1000,
    )
    prompt = ChatPromptTemplate.from_template(_NER_TEMPLATE)
    parser = JsonOutputParser()
    return prompt | llm.with_retry(stop_after_attempt=2) | parser


# ── Context builders ──────────────────────────────────────────────────────────

def _drug_context(matches: list) -> str:
    """Human-readable drug match summary for NER prompt."""
    if not matches:
        return ""
    confirmed = [m for m in matches if not m.flagged_for_review]
    flagged   = [m for m in matches if m.flagged_for_review]
    parts = []
    if confirmed:
        parts.append("THUỐC ĐÃ XÁC NHẬN: " + ", ".join(m.inn for m in confirmed))
    for m in flagged:
        parts.append(f"⚠️ CẦN BS XÁC NHẬN: '{m.original_text}' → {m.inn}? ({m.flag_reason})")
    return "\n".join(parts)


# ── Public API ────────────────────────────────────────────────────────────────

def extract_clinical_rag(
    transcript: str,
    api_key: str,
) -> tuple[dict, str, list]:
    """
    Full RAG pipeline:
      transcript → [L1b] drug correction → [LangChain] NER → [L1d] ICD enhance
    Returns: (clinical_data, error_msg, drug_matches)
    """
    if not transcript or not api_key:
        return {}, "Thiếu transcript hoặc API key", []

    # ── L1b: Drug correction ──────────────────────────────────────────────────
    drug_matches: list = []
    corrected = transcript
    if _L1B_OK:
        try:
            corrected, drug_matches = correct_drug_names_v2(transcript)
            logger.info("L1b: %d drug matches, corrected len %d→%d",
                        len(drug_matches), len(transcript), len(corrected))
        except Exception as e:
            logger.warning("L1b correction failed: %s", e)
            corrected = transcript

    # ── LangChain NER chain ───────────────────────────────────────────────────
    try:
        chain = build_chain(api_key)
        result: dict = chain.invoke({
            "transcript":   corrected,
            "icd_context":  _ICD_CONTEXT_STR,
            "drug_context": _drug_context(drug_matches),
        })
    except Exception as e:
        return {}, f"NER chain lỗi: {e}", drug_matches

    # ── L1d: ICD enhancement (nếu NER bỏ trống) ──────────────────────────────
    if _L1D_OK and not result.get("icd"):
        chan_doan = result.get("chan_doan", "")
        if chan_doan:
            try:
                hits = _icd_search(chan_doan, max_results=1)
                if hits and hits[0]["score"] >= 0.5:
                    result["icd"] = hits[0]["code"]
                    logger.info("L1d enhanced ICD: %s → %s", chan_doan, result["icd"])
            except Exception as e:
                logger.warning("L1d ICD lookup failed: %s", e)

    return result, "", drug_matches
