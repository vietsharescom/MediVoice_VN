"""
MediVoice VN — Human Gate (L4)
ISO/IEC 42001:2023 Clause 5.3 | Luật KCB 2023 Điều 62 | Luật AI 134/2025 Điều 22

Nguyên tắc (từ CONSTITUTION.md):
"AI có thể thay con người ở EXECUTION + REVIEW layer
 nhưng KHÔNG thể thay con người ở ACCOUNTABILITY layer"

FROZEN: Layer này không thể bị bypass trong bất kỳ ngữ cảnh nào.
Xem: config/contracts/module_contracts_vn.json → L4_HUMAN_GATE.may_be_bypassed = false
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional
import uuid


@dataclass
class ApprovalDecision:
    """
    Immutable record của một quyết định phê duyệt.
    Luật AI 134/2025: phải có evidence BS đã review.
    """
    decision_id: str
    record_id: str            # ID bệnh án được phê duyệt
    approved: bool
    approver_cchn: str        # Chứng chỉ hành nghề của BS
    approver_name: str
    timestamp: str            # ISO 8601
    draft_presented: str      # Bản draft AI đã trình bày (JSON)
    notes: str                # Ghi chú của BS nếu có

    def to_dict(self) -> dict:
        import dataclasses
        return dataclasses.asdict(self)


class HumanGate:
    """
    L4 Human Gate — CCP-1 (Critical Control Point).

    KHÔNG BAO GIỜ bypass. Không có auto-approve trong production.
    Luật KCB 2023 Điều 62: BS chịu trách nhiệm về nội dung hồ sơ.

    Modes:
      production:  approval_callback phải được cung cấp
                   callback(record_id, draft) → (approved, cchn, name, notes)
      testing:     MockApproval.always_approve() hoặc MockApproval.always_reject()
    """

    def __init__(
        self,
        approval_callback: Optional[Callable] = None,
        approver_cchn: str = "UNKNOWN",
        approver_name: str = "UNKNOWN",
    ):
        """
        Args:
            approval_callback: Hàm gọi để lấy quyết định BS.
                Signature: callback(record_id, draft_json) -> (approved: bool, cchn: str, name: str, notes: str)
                None = không dùng được (chỉ cho testing qua MockApproval)
            approver_cchn: CCHN mặc định (override trong callback)
            approver_name: Tên BS mặc định
        """
        self._callback = approval_callback
        self._default_cchn = approver_cchn
        self._default_name = approver_name
        self._decisions: list[ApprovalDecision] = []

    def request_approval(
        self,
        record_id: str,
        draft_json: str,
        required_role: str = "bac_si",
    ) -> ApprovalDecision:
        """
        Yêu cầu BS phê duyệt bệnh án draft.

        Args:
            record_id:     ID bệnh án
            draft_json:    JSON string của bệnh án draft
            required_role: Vai trò cần thiết (mặc định: "bac_si")

        Returns:
            ApprovalDecision — nếu approved=False: pipeline bị HALT

        Raises:
            ValueError: Nếu không có approval_callback (misconfiguration)
        """
        if self._callback is None:
            raise ValueError(
                "HumanGate yêu cầu approval_callback trong production. "
                "Sử dụng MockApproval cho testing."
            )

        try:
            approved, cchn, name, notes = self._callback(record_id, draft_json)
        except Exception as e:
            # Nếu callback lỗi → mặc định reject (an toàn nhất)
            approved = False
            cchn = self._default_cchn
            name = self._default_name
            notes = f"[CALLBACK ERROR — defaulting to reject]: {str(e)}"

        decision = ApprovalDecision(
            decision_id=str(uuid.uuid4()),
            record_id=record_id,
            approved=approved,
            approver_cchn=cchn or self._default_cchn,
            approver_name=name or self._default_name,
            timestamp=datetime.utcnow().isoformat() + "Z",
            draft_presented=draft_json[:500],  # Lưu 500 chars đầu để audit
            notes=notes or "",
        )

        self._decisions.append(decision)
        return decision

    def get_decisions(self) -> list[ApprovalDecision]:
        return list(self._decisions)

    def approved_count(self) -> int:
        return sum(1 for d in self._decisions if d.approved)

    def rejected_count(self) -> int:
        return sum(1 for d in self._decisions if not d.approved)

    def audit_log(self) -> list[dict]:
        return [d.to_dict() for d in self._decisions]


class MockApproval:
    """
    Mock callbacks cho testing.
    KHÔNG dùng trong production.
    """

    @staticmethod
    def always_approve(cchn: str = "TEST-CCHN", name: str = "Test BS"):
        """Mock: luôn approve — dùng trong tests."""
        def callback(record_id: str, draft_json: str):
            return True, cchn, name, "Test auto-approve"
        return callback

    @staticmethod
    def always_reject(cchn: str = "TEST-CCHN", name: str = "Test BS"):
        """Mock: luôn reject — dùng trong tests."""
        def callback(record_id: str, draft_json: str):
            return False, cchn, name, "Test auto-reject"
        return callback

    @staticmethod
    def approve_after_review(
        modified_draft: str = "",
        cchn: str = "TEST-CCHN",
        name: str = "Test BS"
    ):
        """Mock: approve với draft đã sửa — simulates BS edits."""
        def callback(record_id: str, draft_json: str):
            return True, cchn, name, "Reviewed and approved with edits"
        return callback
