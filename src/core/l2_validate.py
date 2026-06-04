# L2 — Schema + Confidence Validation
# Input: NER entities (L1c) | Output: validated form_data + confidence_scores
# FROZEN PIPELINE LAYER

from __future__ import annotations
from .l1c_ner import MedicalEntities


# Trọng số cho từng field khi tính overall confidence
_FIELD_WEIGHTS = {
    "chan_doan": 0.30,
    "don_thuoc": 0.25,
    "nhiet_do": 0.08,
    "huyet_ap": 0.08,
    "mach": 0.05,
    "tai_kham": 0.10,
    "ly_do": 0.14,
}


def _score_field(value) -> float:
    """0.0 = empty/missing, 1.0 = present."""
    if value is None:
        return 0.0
    if isinstance(value, str):
        return 1.0 if value.strip() else 0.0
    if isinstance(value, list):
        return 1.0 if len(value) > 0 else 0.0
    if isinstance(value, (int, float)):
        return 1.0
    return 0.0


def validate(entities: MedicalEntities) -> tuple[dict, dict[str, float], float]:
    """
    Validate entities từ L1c và tính confidence scores.
    Returns: (form_data, confidence_scores, overall_confidence)
    """
    scores: dict[str, float] = {}

    scores["ly_do"] = _score_field(entities.ly_do)
    scores["chan_doan"] = _score_field(entities.chan_doan)
    scores["don_thuoc"] = _score_field(entities.don_thuoc)
    scores["nhiet_do"] = _score_field(entities.nhiet_do)
    scores["huyet_ap"] = _score_field(entities.huyet_ap_tam_thu)
    scores["mach"] = _score_field(entities.mach)
    scores["tai_kham"] = _score_field(entities.tai_kham)

    overall = sum(
        _FIELD_WEIGHTS.get(k, 0.05) * v for k, v in scores.items()
    )

    # form_data là dict đã sẵn để merge vào ClinicalRecord
    form_data: dict = {
        "ly_do": entities.ly_do,
        "trieu_chung": entities.trieu_chung,
        "sinh_hieu": {
            "nhiet_do": entities.nhiet_do,
            "huyet_ap_tam_thu": entities.huyet_ap_tam_thu,
            "huyet_ap_tam_truong": entities.huyet_ap_tam_truong,
            "mach": entities.mach,
            "nhip_tho": entities.nhip_tho,
            "can_nang": entities.can_nang,
            "spo2": entities.spo2,
        },
        "toan_than": entities.toan_than,
        "cac_bo_phan": entities.cac_bo_phan,
        "chan_doan": entities.chan_doan,
        "don_thuoc": entities.don_thuoc,
        "tai_kham": entities.tai_kham,
        "chi_dinh": entities.chi_dinh,
    }

    return form_data, scores, round(overall, 3)
