# L1a — PhoWhisper ASR Streaming + A1 Prompt Injection
# Input: WAV 16kHz mono | Output: raw transcript (chunked 10s)
# Model: vinai/PhoWhisper-medium (BSD-3-Clause, commercial OK)
# FROZEN PIPELINE LAYER | A1-PROMPT-INJECT: FID-VN-010

from __future__ import annotations
import logging
import numpy as np

logger = logging.getLogger(__name__)

MODEL_ID = "vinai/PhoWhisper-medium"
_pipeline = None   # lazy-loaded

# A1-PROMPT-INJECT: Specialty → drug_class list mapping.
# None = all drugs (general clinical — no specialty filter).
# FID-VN-012 canonical IDs (12 specialties) + legacy aliases for backward compat.
SPECIALTY_DRUG_CLASSES: dict[str, list[str] | None] = {
    # ── FID-VN-012 canonical (12 specialties) ────────────────────────────────
    "noi_khoa": [
        "statin", "ace_inhibitor", "arb", "beta_blocker", "calcium_channel_blocker",
        "thiazide_like_diuretic", "loop_diuretic", "biguanide", "sulfonylurea",
        "dpp4_inhibitor", "sglt2_inhibitor", "analgesic_antipyretic", "ppi",
        "antihistamine_2nd_gen", "corticosteroid",
    ],
    "tim_mach": [
        "statin", "ace_inhibitor", "arb", "beta_blocker", "calcium_channel_blocker",
        "thiazide_like_diuretic", "loop_diuretic", "antiplatelet", "anticoagulant",
        "supplement_cardiac", "cardiac_glycoside",
    ],
    "chan_thuong_chinh_hinh": [
        "nsaid", "opioid_weak", "analgesic_antipyretic", "corticosteroid",
        "uric_acid_lowering", "gout_acute", "calcium_channel_blocker",
    ],
    "tai_mui_hong": [
        "antihistamine_2nd_gen", "corticosteroid", "macrolide", "quinolone",
        "analgesic_antipyretic", "penicillin", "cephalosporin_3g",
    ],
    "san_phu_khoa": [
        "analgesic_antipyretic", "penicillin", "cephalosporin_3g",
        "corticosteroid", "nitroimidazole", "macrolide",
    ],
    "nhi": [
        "analgesic_antipyretic", "antihistamine_2nd_gen", "penicillin",
        "cephalosporin_3g", "macrolide", "corticosteroid", "beta2_agonist",
    ],
    "cdha": None,  # contrast agents / all drugs — no specialty filter
    "ngoai": [
        "analgesic_antipyretic", "nsaid", "penicillin", "cephalosporin_3g",
        "opioid_weak", "ppi", "nitroimidazole", "penicillin_beta_lactamase_inhibitor",
    ],
    "da_lieu": [
        "antihistamine_2nd_gen", "corticosteroid", "azole_antifungal",
        "polyene_antifungal", "lincosamide",
    ],
    "mat": [
        "antihistamine_2nd_gen", "corticosteroid", "quinolone",
        "azole_antifungal", "analgesic_antipyretic",
    ],
    "noi_tiet": [
        "biguanide", "sulfonylurea", "dpp4_inhibitor", "sglt2_inhibitor",
        "alpha_glucosidase_inhibitor", "thiazolidinedione", "corticosteroid",
        "statin",
    ],
    "than_tiet_nieu": [
        "loop_diuretic", "thiazide_like_diuretic", "ace_inhibitor", "arb",
        "quinolone", "penicillin_beta_lactamase_inhibitor",
    ],
    # ── Legacy aliases (backward compat — same drug classes as canonical) ─────
    "nhi_khoa":    [
        "analgesic_antipyretic", "antihistamine_2nd_gen", "penicillin",
        "cephalosporin_3g", "macrolide", "corticosteroid", "beta2_agonist",
    ],
    "ngoai_khoa":  [
        "analgesic_antipyretic", "nsaid", "penicillin", "cephalosporin_3g",
        "opioid_weak", "ppi", "nitroimidazole", "penicillin_beta_lactamase_inhibitor",
    ],
    "san_khoa":    [
        "analgesic_antipyretic", "penicillin", "cephalosporin_3g",
        "corticosteroid", "nitroimidazole", "macrolide",
    ],
    "tieu_hoa":    ["ppi", "antacid", "prokinetic", "nitroimidazole", "penicillin"],
    "than_kinh":   [
        "analgesic_antipyretic", "anticonvulsant_neuropathic", "antioxidant_neuropathic",
        "ssri", "benzodiazepine", "sedative_hypnotic",
    ],
    "co_xuong_khop": ["nsaid", "corticosteroid", "uric_acid_lowering", "gout_acute"],
    "ho_hap": [
        "beta2_agonist", "corticosteroid", "antihistamine_2nd_gen",
        "macrolide", "quinolone", "penicillin", "cephalosporin_3g",
        "analgesic_antipyretic",
    ],
    "lam_sang": None,  # all drugs
}


def get_drugs_by_specialty(drug_db: dict, specialty: str = "noi_khoa", n: int = 30) -> list[str]:
    """
    Lấy top-n INN drug names cho specialty từ drug_db_v200.
    Nếu specialty không có trong map hoặc specialty="lam_sang" → tất cả drugs.
    Nếu specialty có ít hơn n drugs → bổ sung từ pool còn lại.
    """
    by_inn = drug_db.get("by_inn", {})
    target_classes = SPECIALTY_DRUG_CLASSES.get(specialty)  # None nếu không có hoặc "lam_sang"

    if target_classes is None:
        candidates = [d for d in by_inn.values() if d.get("inn", "")]
    else:
        candidates = [
            d for d in by_inn.values()
            if d.get("drug_class", "") in target_classes and d.get("inn", "")
        ]

    names = [d["inn"] for d in candidates]

    # Bổ sung từ pool còn lại nếu chưa đủ n
    if len(names) < n and target_classes is not None:
        all_names = [d.get("inn", "") for d in by_inn.values() if d.get("inn", "")]
        supplement = [name for name in all_names if name not in names]
        names = names + supplement

    return names[:n]


def build_initial_prompt(drug_db: dict, specialty: str = "noi_khoa") -> str:
    """
    Build domain-priming prompt cho PhoWhisper decoder (A1-PROMPT-INJECT).
    Inject top 30 drugs theo specialty → bias decoder về drug vocabulary.
    Expected improvement: +10–25% drug recall (FID-VN-010 §A1).
    """
    top_drugs = get_drugs_by_specialty(drug_db, specialty, n=30)
    drug_str = ", ".join(top_drugs)
    return (
        f"Bác sĩ Việt Nam kê đơn thuốc y tế: {drug_str}. "
        "Chẩn đoán, sinh hiệu, tái khám."
    )


def _load_pipeline():
    """Lazy load PhoWhisper — chỉ load khi cần, tốn ~3GB RAM."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    try:
        from transformers import pipeline as hf_pipeline
        import torch

        device = 0 if torch.cuda.is_available() else -1
        _pipeline = hf_pipeline(
            "automatic-speech-recognition",
            model=MODEL_ID,
            device=device,
            chunk_length_s=10,
            stride_length_s=2,
        )
        logger.info(f"PhoWhisper loaded: {MODEL_ID} (device={device})")
    except Exception as e:
        logger.warning(f"PhoWhisper không load được: {e}. ASR sẽ trả về rỗng.")
        _pipeline = None

    return _pipeline


def transcribe(
    audio: np.ndarray,
    sample_rate: int = 16000,
    drug_db: dict | None = None,
    specialty: str = "noi_khoa",
) -> str:
    """
    Chuyển audio numpy array → transcript tiếng Việt.
    drug_db: nếu cung cấp, inject drug vocab prompt vào Whisper decoder (A1).
    Nếu model chưa load được, trả về chuỗi rỗng (không crash pipeline).
    """
    pipe = _load_pipeline()
    if pipe is None:
        return ""

    audio_input = {"array": audio.astype(np.float32), "sampling_rate": sample_rate}

    try:
        if drug_db is not None:
            prompt = build_initial_prompt(drug_db, specialty)
            try:
                result = pipe(audio_input, initial_prompt=prompt)
            except TypeError:
                # transformers version không support initial_prompt — fallback không prompt
                logger.debug("initial_prompt not supported by pipeline version, falling back")
                result = pipe(audio_input)
        else:
            result = pipe(audio_input)
        return result.get("text", "").strip()
    except Exception as e:
        logger.error(f"ASR error: {e}")
        return ""


def transcribe_file(
    wav_path: str,
    drug_db: dict | None = None,
    specialty: str = "noi_khoa",
) -> str:
    """Transcribe từ file WAV path."""
    import soundfile as sf
    audio, sr = sf.read(wav_path, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return transcribe(audio, sr, drug_db=drug_db, specialty=specialty)


def transcribe_chunks(
    chunks: list[np.ndarray],
    sample_rate: int = 16000,
    drug_db: dict | None = None,
    specialty: str = "noi_khoa",
) -> str:
    """
    Transcribe danh sách chunks, ghép kết quả.
    Dùng cho streaming mode với L0.chunk_audio.
    """
    texts = [
        transcribe(c, sample_rate, drug_db=drug_db, specialty=specialty)
        for c in chunks if len(c) > 0
    ]
    return " ".join(t for t in texts if t)
