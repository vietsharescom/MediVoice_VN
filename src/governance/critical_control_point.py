# critical_control_point.py
# Critical Control Points -- ISO/IEC 42001:2023 Clause 8.2
# Standard: Formal identification of pipeline points requiring human authority
# Version: v1.0
#
# Definition (ISO 8.2):
# A Critical Control Point is a stage where:
# - Risk to safety, accountability, or compliance is highest
# - Failure cannot be automatically recovered
# - Human decision authority is REQUIRED
# - AI cannot self-authorize

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CriticalControlPoint:
    """
    Formal definition of a Critical Control Point.

    ISO/IEC 42001:2023 Clause 8.2 -- AI System Impact Assessment
    ISO/IEC 42001:2023 Clause 5.3 -- Roles, Responsibilities, Authorities
    """
    stage: str
    description: str
    risk_threshold: int         # risk score that triggers human review
    action_on_breach: str       # "halt" | "escalate" | "log"
    requires_human_approval: bool
    human_role: str             # who must approve
    iso_clause: str             # ISO clause this CCP maps to
    rationale: str              # why this is a CCP
    monitoring_metrics: List[str] = field(default_factory=list)

    def is_breached(self, risk_score: int) -> bool:
        return risk_score >= self.risk_threshold

    def to_dict(self) -> Dict:
        return {
            "stage": self.stage,
            "description": self.description,
            "risk_threshold": self.risk_threshold,
            "action_on_breach": self.action_on_breach,
            "requires_human_approval": self.requires_human_approval,
            "human_role": self.human_role,
            "iso_clause": self.iso_clause,
            "rationale": self.rationale,
            "monitoring_metrics": self.monitoring_metrics,
        }


class CCPRegistry:
    """
    Registry of all Critical Control Points in the pipeline.

    Source of truth for which stages require human authority.
    Cannot be modified at runtime -- defined at system design time.

    ISO/IEC 42001:2023 Clause 8.2 -- AI System Impact Assessment
    ISO/IEC 42001:2023 Clause 5.3 -- Accountability
    """

    # ----------------------------------------------------------------
    # Critical Control Points -- defined by Architecture Authority
    # Changes require: system owner approval + CHANGELOG entry
    # ----------------------------------------------------------------

    _REGISTRY: Dict[str, CriticalControlPoint] = {

        "L4_DECISION_AUTHORITY": CriticalControlPoint(
            stage="L4_DECISION_AUTHORITY",
            description="Authorization gate -- decides if AI execution is allowed",
            risk_threshold=5,
            action_on_breach="halt",
            requires_human_approval=True,
            human_role="System Owner or delegated AI Operations Lead",
            iso_clause="ISO 42001 Cl.5.3 + Cl.8.2",
            rationale=(
                "This stage makes the final allow/reject decision for AI execution. "
                "An incorrect allow could grant AI unauthorized access. "
                "An incorrect reject could block legitimate operations. "
                "Human accountability required per ISO 42001 Clause 5.3."
            ),
            monitoring_metrics=["rejection_rate", "override_rate", "risk_score"]
        ),

        "L6_AGENT": CriticalControlPoint(
            stage="L6_AGENT",
            description="AI execution stage -- only stage that calls LLM/tools",
            risk_threshold=4,
            action_on_breach="halt",
            requires_human_approval=True,
            human_role="AI Operations Lead",
            iso_clause="ISO 42001 Cl.8.5 + Annex A.9.3",
            rationale=(
                "L6_AGENT is the ONLY stage with LLM/tool access. "
                "Scope violations here have direct external impact. "
                "Must verify L4=allow AND L5=pass before execution. "
                "Human accountability required for AI-generated actions."
            ),
            monitoring_metrics=[
                "tool_calls_per_run", "token_usage", "execution_time_ms",
                "policy_compliance_rate"
            ]
        ),

        "L8_RECOVERY": CriticalControlPoint(
            stage="L8_RECOVERY",
            description="Recovery stage -- handles failures, applies fallback",
            risk_threshold=7,
            action_on_breach="escalate",
            requires_human_approval=False,  # auto-recovery unless escalated
            human_role="Operations Lead",
            iso_clause="ISO 42001 Cl.10.2",
            rationale=(
                "Recovery failures mean unhandled exceptions propagate to users. "
                "High risk score triggers escalation. "
                "Automated recovery preferred but human escalation on threshold breach."
            ),
            monitoring_metrics=["recovery_success_rate", "escalation_rate"]
        ),
    }

    @classmethod
    def get(cls, stage: str) -> Optional[CriticalControlPoint]:
        """Return CCP for stage, or None if not a CCP."""
        return cls._REGISTRY.get(stage)

    @classmethod
    def is_ccp(cls, stage: str) -> bool:
        return stage in cls._REGISTRY

    @classmethod
    def all(cls) -> List[CriticalControlPoint]:
        return list(cls._REGISTRY.values())

    @classmethod
    def requires_human(cls, stage: str) -> bool:
        ccp = cls.get(stage)
        return ccp is not None and ccp.requires_human_approval

    @classmethod
    def check_breach(cls, stage: str, risk_score: int) -> Optional[str]:
        """
        Check if risk_score breaches CCP threshold.
        Returns action string if breached, None if not.
        """
        ccp = cls.get(stage)
        if ccp and ccp.is_breached(risk_score):
            return ccp.action_on_breach
        return None

    @classmethod
    def summary(cls) -> List[Dict]:
        return [ccp.to_dict() for ccp in cls._REGISTRY.values()]
