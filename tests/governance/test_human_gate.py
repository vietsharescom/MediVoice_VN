"""
Governance Tests — Human Gate L4
ISO/IEC 42001:2023 Clause 5.3 | Luật KCB 2023 Điều 62

Verify:
  1. Gate requires explicit callback (no silent auto-approve)
  2. Approval recorded with CCHN
  3. Rejection halts pipeline
  4. Callback error defaults to reject (safe failure)
  5. Decisions are auditable
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

from governance.human_gate import HumanGate, MockApproval, ApprovalDecision


class TestHumanGateRequired:
    """Human Gate phải được cấu hình đúng."""

    def test_no_callback_raises_error(self):
        """Không có callback → ValueError (không thể dùng trong production)."""
        gate = HumanGate()  # No callback
        with pytest.raises(ValueError, match="approval_callback"):
            gate.request_approval("REC-001", '{"test": true}')

    def test_approve_with_callback(self):
        """Approve callback hoạt động đúng."""
        gate = HumanGate(
            approval_callback=MockApproval.always_approve("CCHN-123", "BS Nguyễn")
        )
        decision = gate.request_approval("REC-001", '{"patient": "test"}')
        assert decision.approved is True
        assert decision.approver_cchn == "CCHN-123"
        assert decision.approver_name == "BS Nguyễn"
        assert decision.record_id == "REC-001"

    def test_reject_with_callback(self):
        """Reject callback hoạt động đúng."""
        gate = HumanGate(
            approval_callback=MockApproval.always_reject("CCHN-123", "BS Nguyễn")
        )
        decision = gate.request_approval("REC-001", '{"patient": "test"}')
        assert decision.approved is False
        assert decision.record_id == "REC-001"


class TestSafeFailure:
    """Khi có lỗi → mặc định reject (an toàn nhất)."""

    def test_callback_exception_defaults_to_reject(self):
        """Nếu callback throw exception → phải reject (không approve)."""
        def bad_callback(record_id, draft):
            raise RuntimeError("Connection lost")

        gate = HumanGate(approval_callback=bad_callback)
        decision = gate.request_approval("REC-001", '{}')

        # Phải reject khi callback lỗi — không được auto-approve
        assert decision.approved is False
        assert "CALLBACK ERROR" in decision.notes


class TestDecisionAudit:
    """Mọi quyết định phải được ghi lại để audit."""

    def test_decisions_are_recorded(self):
        """Tất cả decisions phải có trong audit log."""
        gate = HumanGate(
            approval_callback=MockApproval.always_approve("CCHN-001", "BS A")
        )
        gate.request_approval("REC-001", '{}')
        gate.request_approval("REC-002", '{}')

        decisions = gate.get_decisions()
        assert len(decisions) == 2

    def test_decision_has_timestamp(self):
        """Mỗi decision phải có timestamp ISO 8601."""
        gate = HumanGate(
            approval_callback=MockApproval.always_approve("CCHN-001", "BS A")
        )
        decision = gate.request_approval("REC-001", '{}')
        assert decision.timestamp.endswith("Z")
        assert "T" in decision.timestamp  # ISO format

    def test_decision_has_decision_id(self):
        """Mỗi decision phải có unique ID để trace."""
        gate = HumanGate(
            approval_callback=MockApproval.always_approve("CCHN-001", "BS A")
        )
        d1 = gate.request_approval("REC-001", '{}')
        d2 = gate.request_approval("REC-002", '{}')
        assert d1.decision_id != d2.decision_id

    def test_audit_log_exportable(self):
        """audit_log() phải return list of dicts."""
        gate = HumanGate(
            approval_callback=MockApproval.always_approve("CCHN-001", "BS A")
        )
        gate.request_approval("REC-001", '{}')
        log = gate.audit_log()
        assert isinstance(log, list)
        assert len(log) == 1
        assert "decision_id" in log[0]
        assert "approver_cchn" in log[0]

    def test_count_methods(self):
        """approved_count + rejected_count phải chính xác."""
        gate = HumanGate(
            approval_callback=MockApproval.always_approve("CCHN-001", "BS A")
        )
        gate.request_approval("REC-001", '{}')
        gate.request_approval("REC-002", '{}')

        gate2 = HumanGate(
            approval_callback=MockApproval.always_reject("CCHN-001", "BS A")
        )
        gate2.request_approval("REC-003", '{}')

        assert gate.approved_count() == 2
        assert gate.rejected_count() == 0
        assert gate2.approved_count() == 0
        assert gate2.rejected_count() == 1


class TestConstitutionCompliance:
    """Kiểm tra CONSTITUTION.md P1 — Human Accountability."""

    def test_approver_cchn_required(self):
        """Approver CCHN phải được ghi vào decision."""
        gate = HumanGate(
            approval_callback=MockApproval.always_approve("CCHN-REAL", "BS Trần")
        )
        decision = gate.request_approval("REC-001", '{}')
        assert decision.approver_cchn == "CCHN-REAL"
        assert decision.approver_cchn != ""
        assert decision.approver_cchn != "UNKNOWN"

    def test_draft_presented_is_stored(self):
        """Draft đã trình bày cho BS phải được lưu vào decision."""
        gate = HumanGate(
            approval_callback=MockApproval.always_approve("CCHN-001", "BS A")
        )
        test_draft = '{"patient": "Nguyen Van A", "diagnosis": "J02.9"}'
        decision = gate.request_approval("REC-001", test_draft)
        assert len(decision.draft_presented) > 0
