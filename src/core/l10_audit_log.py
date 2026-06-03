# L10 — Immutable Audit Log
# ISO/IEC 42001:2023 | Luat AI 134/2025
# IMMUTABLE: NO delete/update/modify functions allowed
# Each record: timestamp + actor_id + patient_ref + action + hash
# FROZEN PIPELINE LAYER


def log_event(actor_id: str, patient_ref: str, action: str, data: dict):
    """
    Ghi audit event. Khong the sua/xoa sau khi tao.
    Yeu cau: ISO 42001 + Luat AI 134/2025.
    """
    raise NotImplementedError("L10 audit log chua implement")
