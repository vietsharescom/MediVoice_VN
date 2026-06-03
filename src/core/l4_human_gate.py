# L4 — Human Gate (MANDATORY)
# Luat KCB 2023 Dieu 62: BS phai ky truoc khi luu
# Luat AI 134/2025: Human oversight bat buoc
# FROZEN PIPELINE LAYER
#
# Integrity: see tests/test_pipeline_integrity.py::TestL4HumanGate


def require_human_approval(record):
    """
    BS phai review va approve truoc khi luu.
    Day la yeu cau phap ly bat buoc (Luat KCB 2023 Dieu 62).
    """
    raise NotImplementedError("L4 chua implement — can human review UI")


def approve(record, doctor_cchn: str):
    """BS chap thuan ban ghi. Ghi audit log."""
    raise NotImplementedError("L4 approve chua implement")


def reject(record, doctor_cchn: str, reason: str):
    """BS tu choi — khong luu vao SQLite."""
    raise NotImplementedError("L4 reject chua implement")
