# runtime_hook.py -- ISO/IEC 42001:2023 Clause 9.2
from dataclasses import dataclass
from typing import List, Optional
from ..core.stage_result import StageResult
from ..core.exceptions import AuditViolationError

@dataclass
class AuditEvent:
    stage: str
    ok: bool
    violation: bool = False
    violation_reason: Optional[str] = None

class RuntimeAuditHook:
    def __init__(self, strict: bool = False):
        self.strict = strict
        self._events: List[AuditEvent] = []

    def on_stage_complete(self, stage_name: str, result: StageResult) -> None:
        violation = not result.ok
        event = AuditEvent(stage=stage_name, ok=result.ok, violation=violation,
                           violation_reason=result.error if violation else None)
        self._events.append(event)
        if violation and self.strict:
            raise AuditViolationError(f"Audit violation at {stage_name}: {result.error}")

    def has_violation(self) -> bool: return any(e.violation for e in self._events)
    def get_audit_events(self) -> List[AuditEvent]: return list(self._events)
    def summary(self) -> str:
        if self.has_violation():
            return f"VIOLATIONS_DETECTED: {[e.stage for e in self._events if e.violation]}"
        return "CLEAN"
    def reset(self) -> None: self._events = []
