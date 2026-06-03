"""Create pipeline stub files for L0-L10."""
import os

CORE_DIR = r"D:\MediVoice_VN\src\core"

STUBS = {
    "l0_normalize.py": """# L0 — Audio Normalize
# Input: audio file (any format) | Output: WAV 16kHz mono
# FROZEN PIPELINE LAYER — change only via FID
""",
    "l1a_asr.py": """# L1a — PhoWhisper ASR Streaming
# Input: WAV 16kHz mono | Output: raw transcript (chunked 10s)
# Model: vinai/PhoWhisper-small (BSD-3-Clause, commercial OK)
# FROZEN PIPELINE LAYER
""",
    "l1b_drug_correct.py": """# L1b — Drug Name Correction
# Input: raw transcript | Output: corrected text
# Source: data/reference/drug_db.json
# RULE: Drug names MUST NOT be translated to Vietnamese
# FROZEN PIPELINE LAYER
""",
    "l1c_ner.py": """# L1c — Medical Named Entity Recognition
# Input: corrected text | Output: entities dict
# Extracts: drugs, doses, diagnoses, symptoms, vital signs
# FROZEN PIPELINE LAYER
""",
    "l1d_icd_lookup.py": """# L1d — ICD-10-VN Lookup
# Input: diagnosis text | Output: ICD-10-VN code
# Source: data/reference/icd10vn.json (QD5837/QD-BYT)
# FROZEN PIPELINE LAYER
""",
    "l2_validate.py": """# L2 — Schema + Confidence Validation
# Input: entities dict | Output: validated form data
# FROZEN PIPELINE LAYER
""",
    "l3_route.py": """# L3 — Route Detection
# Input: validated data | Output: route (lam_sang/cdha/nha_khoa/...)
# FROZEN PIPELINE LAYER
""",
    "l4_human_gate.py": """# L4 — Human Gate (MANDATORY)
# Luat KCB 2023 Dieu 62: BS phai ky truoc khi luu
# Luat AI 134/2025: Human oversight bat buoc
# FROZEN PIPELINE LAYER
#
# FORBIDDEN: bypass, skip_gate, force_approve, auto_approve
# These words are checked by test_pipeline_integrity.py


def require_human_approval(record):
    \"\"\"
    BS phai review va approve truoc khi luu.
    Day la yeu cau phap ly bat buoc (Luat KCB 2023 Dieu 62).
    \"\"\"
    raise NotImplementedError("L4 chua implement — can human review UI")


def approve(record, doctor_cchn: str):
    \"\"\"BS chap thuan ban ghi. Ghi audit log.\"\"\"
    raise NotImplementedError("L4 approve chua implement")


def reject(record, doctor_cchn: str, reason: str):
    \"\"\"BS tu choi — khong luu vao SQLite.\"\"\"
    raise NotImplementedError("L4 reject chua implement")
""",
    "l5_pii_scan.py": """# L5 — PII Scan
# Input: form data | Output: masked/flagged data
# Detects: CCCD, BHYT, SDT (ND13/2023)
# FROZEN PIPELINE LAYER
""",
    "l6_generate_form.py": """# L6 — Generate Mau 15/BV-01
# Input: approved entities | Output: BenhAnNgoaiTru object
# RULE: AI ghi lai loi BS noi — KHONG tu chuan doan
# TT32/2023 format
# FROZEN PIPELINE LAYER
""",
    "l7_storage.py": """# L7 — SQLite + Fernet Storage
# Input: approved record | Output: stored record ID
# RULE: Data PHAI luu tai VN — khong AWS/GCP/Azure ngoai VN
# Allowed: localhost, vngcloud.vn, fptcloud.com, vnpt-technology.vn
# FROZEN PIPELINE LAYER
""",
    "l8_error_handler.py": """# L8 — Error Handling + Recovery
# FROZEN PIPELINE LAYER
""",
    "l9a_pdf_export.py": """# L9a — PDF Export (Phase 0)
# Input: stored record | Output: PDF file path
# FROZEN PIPELINE LAYER
""",
    "l10_audit_log.py": """# L10 — Immutable Audit Log
# ISO/IEC 42001:2023 | Luat AI 134/2025
# IMMUTABLE: NO delete/update/modify functions allowed
# Each record: timestamp + actor_id + patient_ref + action + hash
# FROZEN PIPELINE LAYER


def log_event(actor_id: str, patient_ref: str, action: str, data: dict):
    \"\"\"
    Ghi audit event. Khong the sua/xoa sau khi tao.
    Yeu cau: ISO 42001 + Luat AI 134/2025.
    \"\"\"
    raise NotImplementedError("L10 audit log chua implement")
""",
}

for filename, content in STUBS.items():
    path = os.path.join(CORE_DIR, filename)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created: {filename}")
    else:
        print(f"Exists:  {filename} (skipped)")

print(f"\nTotal stubs: {len(STUBS)}")
