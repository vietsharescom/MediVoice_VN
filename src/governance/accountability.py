# accountability.py
# Decision Accountability Tracker
# ISO/IEC 42001:2023 Clause 5.3 -- Roles, Responsibilities, Authorities
# Standard: Every decision logged with: WHO decided, HOW (AI or Human), WHY
# Version: v1.0
#
# KEY REQUIREMENT:
# ISO 42001 requires clear accountability for every AI system decision.
# This module answers: "Who is accountable for this decision?"

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class DecisionMaker(Enum):
    AI_AUTOMATIC    = "AI_AUTOMATIC"      # AI decided without human
    AI_ASSISTED     = "AI_ASSISTED"       # AI proposed, human confirmed
    HUMAN_OVERRIDE  = "HUMAN_OVERRIDE"    # Human overrode AI decision
    HUMAN_ONLY      = "HUMAN_ONLY"        # Human decided (AI was not involved)
    RULE_ENGINE     = "RULE_ENGINE"       # Deterministic rule (no AI)
    SYSTEM          = "SYSTEM"            # Framework-level decision


@dataclass
class DecisionRecord:
    """
    Immutable record of one decision in the pipeline.

    ISO/IEC 42001:2023 Clause 5.3:
    "The organization shall assign the responsibility and authority
    for ensuring that the AI management system conforms."
    """
    record_id: str
    stage: str
    decision: str               # What was decided ("allow", "reject", "route_to_X", etc.)
    decision_maker: DecisionMaker
    confidence: float           # 0.0 - 1.0 (1.0 for deterministic)
    timestamp: str
    human_identity: Optional[str] = None   # filled if human was involved
    ai_model: Optional[str] = None         # filled if AI was involved
    rationale: str = ""
    input_hash: str = ""        # hash of input that led to decision
    risk_score_at_decision: int = 0
    is_critical_control_point: bool = False
    overridable: bool = True    # some decisions cannot be overridden

    def is_human_accountable(self) -> bool:
        """Human is accountable ONLY if they actually participated in the decision."""
        return self.decision_maker in (
            DecisionMaker.AI_ASSISTED,
            DecisionMaker.HUMAN_OVERRIDE,
            DecisionMaker.HUMAN_ONLY,
        )

    def to_dict(self) -> Dict:
        return {
            "record_id": self.record_id,
            "stage": self.stage,
            "decision": self.decision,
            "decision_maker": self.decision_maker.value,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "human_identity": self.human_identity,
            "ai_model": self.ai_model,
            "rationale": self.rationale,
            "risk_score": self.risk_score_at_decision,
            "is_ccp": self.is_critical_control_point,
            "human_accountable": self.is_human_accountable(),
        }


class AccountabilityTracker:
    """
    Tracks accountability for every decision in the pipeline.

    For each decision, records:
    - WHO decided (AI, Human, Rule Engine, System)
    - WHAT was decided
    - WHY (rationale + risk context)
    - WHEN (timestamp)
    - Confidence level

    Enables:
    - Audit trail: "who made this decision?"
    - Compliance: "was human involved at CCPs?"
    - Non-repudiation: "this decision was made by X at Y"
    - Escalation tracking: "how many times was human called?"

    ISO/IEC 42001:2023 Clause 5.3
    """

    def __init__(self):
        self._records: List[DecisionRecord] = []
        self._counter = 0

    def _new_id(self) -> str:
        self._counter += 1
        return f"ACC-{self._counter:04d}"

    def record_ai_decision(
        self,
        stage: str,
        decision: str,
        ai_model: str = "AI",
        confidence: float = 0.8,
        rationale: str = "",
        risk_score: int = 0,
        is_ccp: bool = False,
    ) -> DecisionRecord:
        """Record an AI-made decision."""
        record = DecisionRecord(
            record_id=self._new_id(),
            stage=stage,
            decision=decision,
            decision_maker=DecisionMaker.AI_AUTOMATIC,
            confidence=confidence,
            timestamp=datetime.now(timezone.utc).isoformat(),
            ai_model=ai_model,
            rationale=rationale,
            risk_score_at_decision=risk_score,
            is_critical_control_point=is_ccp,
        )
        self._records.append(record)
        return record

    def record_human_decision(
        self,
        stage: str,
        decision: str,
        human_identity: str,
        rationale: str = "",
        risk_score: int = 0,
        is_ccp: bool = False,
        overriding_ai: bool = False,
    ) -> DecisionRecord:
        """Record a human-made decision."""
        maker = (
            DecisionMaker.HUMAN_OVERRIDE if overriding_ai
            else DecisionMaker.HUMAN_ONLY
        )
        record = DecisionRecord(
            record_id=self._new_id(),
            stage=stage,
            decision=decision,
            decision_maker=maker,
            confidence=1.0,      # human decisions have full confidence
            timestamp=datetime.now(timezone.utc).isoformat(),
            human_identity=human_identity,
            rationale=rationale,
            risk_score_at_decision=risk_score,
            is_critical_control_point=is_ccp,
        )
        self._records.append(record)
        return record

    def record_ai_assisted_decision(
        self,
        stage: str,
        decision: str,
        ai_model: str,
        human_identity: str,
        ai_confidence: float = 0.8,
        rationale: str = "",
        risk_score: int = 0,
        is_ccp: bool = False,
    ) -> DecisionRecord:
        """Record: AI proposed, Human confirmed."""
        record = DecisionRecord(
            record_id=self._new_id(),
            stage=stage,
            decision=decision,
            decision_maker=DecisionMaker.AI_ASSISTED,
            confidence=ai_confidence,
            timestamp=datetime.now(timezone.utc).isoformat(),
            ai_model=ai_model,
            human_identity=human_identity,
            rationale=rationale,
            risk_score_at_decision=risk_score,
            is_critical_control_point=is_ccp,
        )
        self._records.append(record)
        return record

    def record_rule_decision(
        self,
        stage: str,
        decision: str,
        rule_id: str,
        is_ccp: bool = False,
    ) -> DecisionRecord:
        """Record a deterministic rule-based decision."""
        record = DecisionRecord(
            record_id=self._new_id(),
            stage=stage,
            decision=decision,
            decision_maker=DecisionMaker.RULE_ENGINE,
            confidence=1.0,
            timestamp=datetime.now(timezone.utc).isoformat(),
            rationale=f"Rule {rule_id}",
            is_critical_control_point=is_ccp,
            overridable=False,   # rule decisions cannot be overridden
        )
        self._records.append(record)
        return record

    def get_all(self) -> List[DecisionRecord]:
        return list(self._records)

    def get_by_stage(self, stage: str) -> List[DecisionRecord]:
        return [r for r in self._records if r.stage == stage]

    def get_ai_decisions(self) -> List[DecisionRecord]:
        return [r for r in self._records
                if r.decision_maker == DecisionMaker.AI_AUTOMATIC]

    def get_human_decisions(self) -> List[DecisionRecord]:
        return [r for r in self._records
                if r.decision_maker in (
                    DecisionMaker.HUMAN_ONLY,
                    DecisionMaker.HUMAN_OVERRIDE,
                    DecisionMaker.AI_ASSISTED,
                )]

    def get_ccp_decisions(self) -> List[DecisionRecord]:
        return [r for r in self._records if r.is_critical_control_point]

    def compliance_check(self) -> Dict:
        """
        Check if all CCP decisions had human involvement.
        ISO 42001 Clause 5.3 compliance.
        """
        ccp_records = self.get_ccp_decisions()
        missing_human = [
            r for r in ccp_records
            if not r.is_human_accountable()
        ]
        return {
            "total_decisions": len(self._records),
            "ai_decisions": len(self.get_ai_decisions()),
            "human_decisions": len(self.get_human_decisions()),
            "ccp_decisions": len(ccp_records),
            "ccp_missing_human": len(missing_human),
            "compliant": len(missing_human) == 0,
            "missing_human_accountability": [r.record_id for r in missing_human],
        }

    def audit_report(self) -> List[Dict]:
        return [r.to_dict() for r in self._records]

    def reset(self) -> None:
        self._records = []
        self._counter = 0
