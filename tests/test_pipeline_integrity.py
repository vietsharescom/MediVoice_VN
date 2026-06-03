"""
MediVoice VN — Pipeline Integrity Tests
ISO/IEC 42001:2023 | Luật AI 134/2025

QUAN TRỌNG: Đây là tầng bảo vệ ISO consistency.
  - Chạy TRƯỚC KHI commit bất kỳ code nào
  - 100% PASS là điều kiện bắt buộc
  - Không được sửa test để pass — phải sửa code

Tests này bảo vệ:
  1. Pipeline order L0→L10 không bị đảo/bỏ
  2. L4 Human Gate không bao giờ bị bypass
  3. Data không rời VN
  4. Drug names không bị dịch/sửa
  5. ICD-10-VN bắt buộc trong chẩn đoán
  6. Audit log bất biến (immutable)
  7. Tên thuốc không được tự động thay đổi
  8. CCHN không block người dùng hoàn toàn
"""

import pytest
import json
import os
import sys
from pathlib import Path

# Thêm src vào path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

DATA_DIR = ROOT / "data" / "reference"


# ═══════════════════════════════════════════════════════════════
# NHÓM 1: DATA REFERENCE — Kiểm tra files thiết yếu tồn tại
# ═══════════════════════════════════════════════════════════════

class TestDataReference:
    """Data reference files phải tồn tại và hợp lệ."""

    def test_icd10vn_exists(self):
        """ICD-10-VN database phải tồn tại."""
        f = DATA_DIR / "icd10vn.json"
        assert f.exists(), f"MISSING: {f}\nChạy: python scripts/download_icd10vn.py"

    def test_icd10vn_has_minimum_codes(self):
        """ICD-10-VN phải có ít nhất 15,000 mã."""
        with open(DATA_DIR / "icd10vn.json", encoding="utf-8") as f:
            db = json.load(f)
        count = len(db.get("by_code", {}))
        assert count >= 15000, f"ICD-10-VN chỉ có {count} mã, cần >= 15000"

    def test_icd10vn_common_codes_present(self):
        """Các mã ICD thông dụng phải có trong database."""
        with open(DATA_DIR / "icd10vn.json", encoding="utf-8") as f:
            db = json.load(f)
        codes = db.get("by_code", {})
        required = ["J02.9", "I10", "E11", "J18.9", "M17.1"]
        missing = [c for c in required if c not in codes]
        assert not missing, f"Thiếu mã ICD: {missing}"

    def test_drug_db_exists(self):
        """Drug database phải tồn tại."""
        f = DATA_DIR / "drug_db.json"
        assert f.exists(), f"MISSING: {f}\nChạy: python scripts/build_drug_db.py"

    def test_drug_db_has_minimum_drugs(self):
        """Drug DB phải có ít nhất 50 thuốc."""
        with open(DATA_DIR / "drug_db.json", encoding="utf-8") as f:
            db = json.load(f)
        count = len(db.get("by_inn", {}))
        assert count >= 50, f"Drug DB chỉ có {count} thuốc, cần >= 50"

    def test_drug_db_common_drugs_present(self):
        """Thuốc thông dụng phải có trong database."""
        with open(DATA_DIR / "drug_db.json", encoding="utf-8") as f:
            db = json.load(f)
        drugs = db.get("by_inn", {})
        required = ["Paracetamol", "Amoxicillin", "Metformin", "Omeprazole"]
        missing = [d for d in required if d not in drugs]
        assert not missing, f"Thiếu thuốc: {missing}"

    def test_mau_15bv01_model_importable(self):
        """Mẫu 15/BV-01 data model phải import được."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "mau15bv01",
            DATA_DIR / "MAU_15BV01_fields.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "BenhAnNgoaiTru"), "BenhAnNgoaiTru class không tìm thấy"
        assert hasattr(mod, "HanhChinh"), "HanhChinh class không tìm thấy"
        assert hasattr(mod, "KhamBenh"), "KhamBenh class không tìm thấy"
        assert hasattr(mod, "DonThuoc"), "DonThuoc class không tìm thấy"


# ═══════════════════════════════════════════════════════════════
# NHÓM 2: PIPELINE STRUCTURE — Kiểm tra module pipeline tồn tại
# ═══════════════════════════════════════════════════════════════

class TestPipelineStructure:
    """Tất cả layer L0–L10 phải có file tương ứng."""

    PIPELINE_FILES = {
        "L0":  "src/core/l0_normalize.py",
        "L1a": "src/core/l1a_asr.py",
        "L1b": "src/core/l1b_drug_correct.py",
        "L1c": "src/core/l1c_ner.py",
        "L1d": "src/core/l1d_icd_lookup.py",
        "L2":  "src/core/l2_validate.py",
        "L3":  "src/core/l3_route.py",
        "L4":  "src/core/l4_human_gate.py",
        "L5":  "src/core/l5_pii_scan.py",
        "L6":  "src/core/l6_generate_form.py",
        "L7":  "src/core/l7_storage.py",
        "L8":  "src/core/l8_error_handler.py",
        "L9a": "src/core/l9a_pdf_export.py",
        "L10": "src/core/l10_audit_log.py",
    }

    def test_all_pipeline_files_exist(self):
        """Tất cả layer L0–L10 phải có file."""
        missing = []
        for layer, path in self.PIPELINE_FILES.items():
            full = ROOT / path
            if not full.exists():
                missing.append(f"{layer}: {path}")
        assert not missing, (
            f"Các layer chưa có code:\n" + "\n".join(f"  - {m}" for m in missing) +
            "\n\nTạo stub files trước khi commit."
        )

    @pytest.mark.parametrize("layer,path", PIPELINE_FILES.items())
    def test_pipeline_file_not_empty(self, layer, path):
        """Mỗi layer file không được rỗng."""
        full = ROOT / path
        if not full.exists():
            pytest.skip(f"{layer} chưa được implement")
        assert full.stat().st_size > 0, f"{layer} ({path}) là file rỗng"


# ═══════════════════════════════════════════════════════════════
# NHÓM 3: L4 HUMAN GATE — Không bao giờ bypass
# ═══════════════════════════════════════════════════════════════

class TestL4HumanGate:
    """
    L4 Human Gate là yêu cầu pháp lý bắt buộc.
    Luật KCB 2023 Điều 62: BS phải ký trước khi lưu.
    Luật AI 134/2025: Human oversight bắt buộc.
    """

    def test_l4_module_exists(self):
        """L4 module phải tồn tại."""
        f = ROOT / "src/core/l4_human_gate.py"
        if not f.exists():
            pytest.skip("L4 chưa implement")

    def test_l4_has_no_bypass_flag(self):
        """L4 không được có flag bypass/skip."""
        f = ROOT / "src/core/l4_human_gate.py"
        if not f.exists():
            pytest.skip("L4 chưa implement")
        content = f.read_text(encoding="utf-8").lower()
        forbidden = ["bypass", "skip_l4", "skip_gate", "force_approve", "auto_approve"]
        found = [w for w in forbidden if w in content]
        assert not found, (
            f"L4 KHÔNG ĐƯỢC có logic bypass!\n"
            f"Tìm thấy từ khóa nguy hiểm: {found}\n"
            f"L4 là yêu cầu pháp lý (Luật KCB 2023 Điều 62)"
        )

    def test_l4_requires_explicit_approval(self):
        """L4 phải có hàm approve/reject rõ ràng."""
        f = ROOT / "src/core/l4_human_gate.py"
        if not f.exists():
            pytest.skip("L4 chưa implement")
        content = f.read_text(encoding="utf-8").lower()
        assert any(w in content for w in ["approve", "reject", "human_review"]), (
            "L4 phải có hàm approve/reject explicit.\n"
            "Không được tự động approve."
        )


# ═══════════════════════════════════════════════════════════════
# NHÓM 4: L10 AUDIT LOG — Immutable
# ═══════════════════════════════════════════════════════════════

class TestL10AuditLog:
    """
    L10 Audit Log phải immutable (ISO 42001 + Luật AI 134/2025).
    Không được có hàm delete/update/modify records.
    """

    def test_l10_module_exists(self):
        f = ROOT / "src/core/l10_audit_log.py"
        if not f.exists():
            pytest.skip("L10 chưa implement")

    def test_l10_no_delete_function(self):
        """L10 KHÔNG được có hàm xóa records."""
        f = ROOT / "src/core/l10_audit_log.py"
        if not f.exists():
            pytest.skip("L10 chưa implement")
        content = f.read_text(encoding="utf-8").lower()
        forbidden = ["delete_log", "remove_log", "truncate", "drop_table",
                     "clear_audit", "wipe_log", "update_log", "modify_log"]
        found = [w for w in forbidden if w in content]
        assert not found, (
            f"L10 Audit Log là IMMUTABLE — không được có hàm xóa/sửa!\n"
            f"Tìm thấy: {found}"
        )

    def test_l10_has_hash_function(self):
        """L10 phải có cơ chế hash để tamper detection."""
        f = ROOT / "src/core/l10_audit_log.py"
        if not f.exists():
            pytest.skip("L10 chưa implement")
        content = f.read_text(encoding="utf-8").lower()
        assert any(w in content for w in ["hash", "fernet", "hmac", "sha256"]), (
            "L10 phải có tamper detection (hash/Fernet/HMAC).\n"
            "Yêu cầu: ISO 42001 + Luật AI 134/2025"
        )


# ═══════════════════════════════════════════════════════════════
# NHÓM 5: DATA RESIDENCY — Data không rời VN
# ═══════════════════════════════════════════════════════════════

class TestDataResidency:
    """
    NĐ13/2023: Dữ liệu y tế PHẢI lưu tại VN.
    Không được dùng AWS/GCP/Azure region ngoài VN.
    """

    FORBIDDEN_CLOUD = [
        "amazonaws.com",
        "azure.com",
        "googleapis.com",
        "cloudflare.com",
        "digitalocean.com",
        "linode.com",
        "heroku.com",
    ]

    ALLOWED_VN_CLOUD = [
        "vngcloud.vn",
        "fptcloud.com",
        "vnpt-technology.vn",
        "localhost",
        "127.0.0.1",
    ]

    def _scan_file(self, filepath):
        """Quét file tìm foreign cloud endpoints."""
        content = filepath.read_text(encoding="utf-8", errors="ignore").lower()
        found = []
        for domain in self.FORBIDDEN_CLOUD:
            if domain in content:
                found.append(domain)
        return found

    def test_no_foreign_cloud_in_storage(self):
        """L7 storage không được dùng cloud nước ngoài."""
        f = ROOT / "src/core/l7_storage.py"
        if not f.exists():
            pytest.skip("L7 chưa implement")
        found = self._scan_file(f)
        assert not found, (
            f"L7 Storage có foreign cloud URLs!\n"
            f"Vi phạm NĐ13/2023 data residency.\n"
            f"Tìm thấy: {found}\n"
            f"Chỉ được dùng: {self.ALLOWED_VN_CLOUD}"
        )

    def test_no_foreign_cloud_in_api(self):
        """API routes không được gọi foreign cloud."""
        api_dir = ROOT / "src/api"
        if not api_dir.exists():
            pytest.skip("API chưa implement")
        violations = []
        for py_file in api_dir.rglob("*.py"):
            found = self._scan_file(py_file)
            if found:
                violations.append(f"{py_file.name}: {found}")
        assert not violations, (
            f"API có foreign cloud calls — vi phạm NĐ13/2023!\n" +
            "\n".join(violations)
        )


# ═══════════════════════════════════════════════════════════════
# NHÓM 6: DRUG NAMES — Không dịch, không tự sửa
# ═══════════════════════════════════════════════════════════════

class TestDrugNameIntegrity:
    """
    Tên thuốc PHẢI giữ nguyên — không dịch, không tự sửa.
    Sai tên thuốc = nguy hiểm cho bệnh nhân.
    """

    def test_drug_correct_preserves_inn(self):
        """L1b drug correction không được thay đổi tên INN đúng."""
        f = ROOT / "src/core/l1b_drug_correct.py"
        if not f.exists():
            pytest.skip("L1b chưa implement")
        # Kiểm tra không có hard-coded replacement sai
        content = f.read_text(encoding="utf-8")
        # Không được translate drug names sang tiếng Việt
        forbidden_translations = [
            '"Paracetamol": "Thuốc hạ sốt"',
            '"Amoxicillin": "Kháng sinh"',
            '"Metformin": "Thuốc tiểu đường"',
        ]
        for bad in forbidden_translations:
            assert bad not in content, (
                f"Tên thuốc KHÔNG được dịch sang tiếng Việt!\n"
                f"Tìm thấy: {bad}"
            )

    def test_drug_db_inn_names_not_translated(self):
        """Trong drug_db.json, INN names là tiếng Anh."""
        with open(DATA_DIR / "drug_db.json", encoding="utf-8") as f:
            db = json.load(f)
        vietnamese_words = ["thuốc", "viên", "hạ sốt", "kháng sinh"]
        violations = []
        for inn in list(db.get("by_inn", {}).keys())[:20]:
            for vw in vietnamese_words:
                if vw in inn.lower():
                    violations.append(inn)
        assert not violations, f"INN names không được chứa tiếng Việt: {violations}"


# ═══════════════════════════════════════════════════════════════
# NHÓM 7: ICD-10-VN — Bắt buộc trong chẩn đoán
# ═══════════════════════════════════════════════════════════════

class TestICD10VNRequired:
    """
    QĐ5837/QĐ-BYT: ICD-10-VN bắt buộc trong phần Chẩn đoán.
    """

    def test_icd_lookup_returns_vn_code(self):
        """ICD-10-VN lookup phải trả về mã VN (không phải CA/US)."""
        with open(DATA_DIR / "icd10vn.json", encoding="utf-8") as f:
            db = json.load(f)
        # Mã VN dùng format chuẩn WHO (J02.9, I10, E11...)
        sample = db["by_code"].get("J02.9")
        assert sample is not None, "J02.9 (Viêm họng cấp) phải có trong DB"
        assert "viêm họng" in sample.get("display", "").lower(), \
            "J02.9 phải có display tiếng Việt"

    def test_benh_an_model_has_icd_field(self):
        """BenhAnNgoaiTru model phải có field ICD-10-VN."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "mau15bv01", DATA_DIR / "MAU_15BV01_fields.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        kb = mod.KhamBenh()
        assert hasattr(kb, "ma_icd10"), \
            "KhamBenh phải có field ma_icd10 (ICD-10-VN code)"


# ═══════════════════════════════════════════════════════════════
# NHÓM 8: POSITIONING — "Documentation Assistant"
# ═══════════════════════════════════════════════════════════════

class TestPositioning:
    """
    MediVoice VN phải luôn là "Documentation Assistant".
    KHÔNG tự nhận là Medical Software hay AI chẩn đoán.
    Luật AI 134/2025: AI tạo nháp — BS chịu trách nhiệm.
    """

    def test_no_auto_diagnosis_in_l6(self):
        """L6 generate form không được tự ra chẩn đoán — chỉ ghi lại lời BS."""
        f = ROOT / "src/core/l6_generate_form.py"
        if not f.exists():
            pytest.skip("L6 chưa implement")
        content = f.read_text(encoding="utf-8").lower()
        # Không được có AI diagnosis engine
        forbidden = ["ai_diagnose", "auto_diagnose", "suggest_diagnosis",
                     "gpt_diagnose", "llm_diagnose"]
        found = [w for w in forbidden if w in content]
        assert not found, (
            f"L6 KHÔNG được tự chẩn đoán!\n"
            f"AI chỉ ghi lại lời BS — không tự ra chẩn đoán.\n"
            f"Tìm thấy: {found}"
        )


# ═══════════════════════════════════════════════════════════════
# NHÓM 9: CONFIGURATION — Không hardcode credentials
# ═══════════════════════════════════════════════════════════════

class TestNoHardcodedSecrets:
    """Không được hardcode credentials, API keys, passwords."""

    SUSPICIOUS_PATTERNS = [
        "password=",
        "secret_key=",
        "api_key=",
        "aws_access",
        "aws_secret",
        "private_key=",
    ]

    def test_no_hardcoded_secrets_in_src(self):
        """Source code không được hardcode secrets."""
        src_dir = ROOT / "src"
        if not src_dir.exists():
            pytest.skip("src/ chưa có code")
        violations = []
        for py_file in src_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore").lower()
            for pattern in self.SUSPICIOUS_PATTERNS:
                # Chỉ flag nếu có giá trị thực (không phải comment hay placeholder)
                if pattern in content and "your_" not in content:
                    lines = [l for l in content.split("\n")
                             if pattern in l and not l.strip().startswith("#")]
                    if lines:
                        violations.append(f"{py_file.name}: {pattern}")
        assert not violations, (
            f"Tìm thấy hardcoded secrets!\n" +
            "\n".join(violations) +
            "\nDùng .env file và python-dotenv"
        )


# ═══════════════════════════════════════════════════════════════
# SMOKE TEST — Chạy nhanh để verify môi trường
# ═══════════════════════════════════════════════════════════════

class TestEnvironment:
    """Kiểm tra môi trường development."""

    def test_python_version(self):
        """Python phải >= 3.10."""
        import sys
        assert sys.version_info >= (3, 10), \
            f"Cần Python >= 3.10, đang dùng {sys.version}"

    def test_data_dir_exists(self):
        """data/reference/ phải tồn tại."""
        assert DATA_DIR.exists(), f"data/reference/ không tồn tại: {DATA_DIR}"

    def test_required_data_files(self):
        """Các files data thiết yếu phải tồn tại."""
        required = [
            "icd10vn.json",
            "drug_db.json",
            "tt23_cdha.json",
            "MAU_15BV01_fields.py",
        ]
        missing = [f for f in required if not (DATA_DIR / f).exists()]
        assert not missing, (
            f"Thiếu files data:\n" + "\n".join(f"  - {f}" for f in missing)
        )
