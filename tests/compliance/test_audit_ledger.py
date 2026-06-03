"""
Compliance Tests — Immutable Audit Ledger
ISO/IEC 42001:2023 Clause 9 | Luật AI 134/2025 Điều 24

Verify:
  1. Records cannot be deleted
  2. Records cannot be modified
  3. Hash chain is intact after writes
  4. Tamper detection works
  5. Patient ref is hashed (not raw)
"""

import pytest
import tempfile
import os
import sys
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

from audit.immutable_ledger import ImmutableLedger


@pytest.fixture
def ledger(tmp_path):
    db = str(tmp_path / "test_audit.db")
    return ImmutableLedger(db)


class TestImmutability:
    """Ledger phải IMMUTABLE — không có hàm delete/update."""

    def test_no_delete_method(self):
        """ImmutableLedger không được có phương thức xóa records."""
        forbidden = ["delete", "remove", "truncate", "drop", "clear", "wipe", "purge"]
        methods = [m for m in dir(ImmutableLedger) if not m.startswith("_")]
        violations = [m for m in methods if any(f in m.lower() for f in forbidden)]
        assert not violations, (
            f"ImmutableLedger KHÔNG được có phương thức xóa!\n"
            f"Tìm thấy: {violations}\n"
            f"Luật AI 134/2025: audit log phải immutable"
        )

    def test_no_update_method(self):
        """ImmutableLedger không được có phương thức sửa records."""
        forbidden = ["update", "modify", "edit", "patch", "set_record", "overwrite"]
        methods = [m for m in dir(ImmutableLedger) if not m.startswith("_")]
        violations = [m for m in methods if any(f in m.lower() for f in forbidden)]
        assert not violations, (
            f"ImmutableLedger KHÔNG được có phương thức sửa!\n"
            f"Tìm thấy: {violations}"
        )

    def test_source_code_no_delete(self):
        """Source code không được có SQL DELETE/UPDATE trong ledger."""
        ledger_file = ROOT / "src/audit/immutable_ledger.py"
        if not ledger_file.exists():
            pytest.skip("immutable_ledger.py chưa tồn tại")
        content = ledger_file.read_text(encoding="utf-8").upper()
        forbidden_sql = ["DELETE FROM", "UPDATE audit_log SET", "DROP TABLE", "TRUNCATE"]
        found = [s for s in forbidden_sql if s in content]
        assert not found, (
            f"immutable_ledger.py có SQL không an toàn!\n"
            f"Tìm thấy: {found}"
        )


class TestHashChain:
    """Hash chain phải hoạt động chính xác."""

    def test_first_record_uses_genesis(self, ledger):
        """Record đầu tiên phải có prev_hash = 'GENESIS'."""
        record = ledger.log(
            actor_id="BS-001", actor_role="bac_si",
            patient_ref="hash_of_patient_1",
            action="draft_created", layer="L6",
            record_id="REC-001"
        )
        assert record.prev_hash == "GENESIS"

    def test_second_record_links_to_first(self, ledger):
        """Record thứ hai phải có prev_hash = hash của record thứ nhất."""
        first = ledger.log(
            actor_id="BS-001", actor_role="bac_si",
            patient_ref="hash_p1", action="draft_created",
            layer="L6", record_id="REC-001"
        )
        second = ledger.log(
            actor_id="BS-001", actor_role="bac_si",
            patient_ref="hash_p1", action="approved",
            layer="L4", record_id="REC-001"
        )
        assert second.prev_hash == first.record_hash

    def test_chain_verification_passes_clean(self, ledger):
        """Chain verification phải PASS khi không có tamper."""
        for i in range(5):
            ledger.log(
                actor_id="BS-001", actor_role="bac_si",
                patient_ref=f"patient_{i}", action="draft_created",
                layer="L6", record_id=f"REC-{i:03d}"
            )
        valid, errors = ledger.verify_chain()
        assert valid, f"Chain verification thất bại: {errors}"
        assert errors == []

    def test_tamper_detection(self, ledger):
        """Sửa record trong DB phải bị phát hiện."""
        ledger.log(
            actor_id="BS-001", actor_role="bac_si",
            patient_ref="patient_1", action="approved",
            layer="L4", record_id="REC-001"
        )

        # Tamper: sửa trực tiếp vào DB (bypass ledger)
        with sqlite3.connect(ledger.db_path) as conn:
            conn.execute(
                "UPDATE audit_log SET action = 'TAMPERED' WHERE record_id = 'REC-001'"
            )
            conn.commit()

        # Verify phải phát hiện tamper
        valid, errors = ledger.verify_chain()
        assert not valid, "Hash chain phải phát hiện tamper!"
        assert len(errors) > 0


class TestPatientPrivacy:
    """Patient ref phải là hash, không phải raw ID."""

    def test_patient_ref_stored_as_provided(self, ledger):
        """Ledger lưu patient_ref như được truyền vào — caller phải hash trước."""
        record = ledger.log(
            actor_id="BS-001", actor_role="bac_si",
            patient_ref="hashed_cccd_value",  # Caller đã hash
            action="draft_created", layer="L6", record_id="REC-001"
        )
        assert record.patient_ref == "hashed_cccd_value"

    def test_raw_cccd_not_in_source(self):
        """Source code không được lưu raw CCCD vào audit log."""
        l4_file = ROOT / "src/core/l4_human_gate.py"
        if not l4_file.exists():
            pytest.skip("L4 chưa implement")
        content = l4_file.read_text(encoding="utf-8").lower()
        # Không được có pattern lưu raw CCCD
        suspicious = ["cccd_raw", "raw_cccd", "patient_cccd =", "cccd_number ="]
        found = [p for p in suspicious if p in content]
        assert not found, f"L4 không được lưu raw CCCD: {found}"


class TestAuditRetrieval:
    """Truy vấn audit log phải hoạt động."""

    def test_get_records_for_patient(self, ledger):
        """Phải lấy được records theo patient_ref."""
        ledger.log("BS", "bac_si", "patient_A", "draft_created", "L6", "REC-1")
        ledger.log("BS", "bac_si", "patient_B", "draft_created", "L6", "REC-2")
        ledger.log("BS", "bac_si", "patient_A", "approved", "L4", "REC-1")

        records = ledger.get_records_for_patient("patient_A")
        assert len(records) == 2
        actions = {r["action"] for r in records}
        assert "draft_created" in actions
        assert "approved" in actions

    def test_count_increments(self, ledger):
        """Count phải tăng sau mỗi log."""
        assert ledger.count() == 0
        ledger.log("BS", "bac_si", "p1", "draft_created", "L6", "R1")
        assert ledger.count() == 1
        ledger.log("BS", "bac_si", "p1", "approved", "L4", "R1")
        assert ledger.count() == 2
