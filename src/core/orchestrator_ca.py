# orchestrator.py
# Central Pipeline Execution Controller
# ISO/IEC 42001:2023 Clause 8.4 -- AI System Lifecycle
# Version: v1.2 -- Full Governance Integration
#
# Integration layers:
# - audit_hook      : RuntimeAuditHook (per-stage event firing)
# - ledger          : ImmutableLedger (hash-chain log)
# - risk_engine     : RiskEngine (dynamic risk scoring)
# - validation_layer: ValidationLayer (pre+post validation)
# - human_gate      : HumanGate (CCP approval)
# - accountability  : AccountabilityTracker (who decided what)

import importlib
import uuid
from typing import Any, Dict, Optional

from .pipeline_guard import PipelineGuard
from .graph_resolver import GraphResolver
from .state_machine import StateMachine
from .stage_result import StageResult
from .exceptions import PipelineError


class Orchestrator:
    """
    Central pipeline execution controller.
    Enforces: L0 -> L1 -> L2 -> L3 -> L4 -> L5 -> L6 -> L7 -> L8 -> L9 -> L10

    All integrations are optional -- backwards compatible.
    Each integration adds a governance layer without changing core flow.

    Execution flow per stage:
    1. PipelineGuard validates order
    2. ValidationLayer.validate_pre() -- rules + simulation
    3. HumanGate (if CCP and escalation needed)
    4. Execute stage handler
    5. RuntimeAuditHook fires
    6. ImmutableLedger appends entry
    7. RiskEngine evaluates + propagates
    8. ValidationLayer.validate_post() -- critics + anomaly
    9. AccountabilityTracker records decision
    10. StateMachine records result
    """

    def __init__(
        self,
        guard: PipelineGuard,
        resolver: GraphResolver,
        audit_hook=None,
        ledger=None,
        risk_engine=None,
        validation_layer=None,
        human_gate=None,
        accountability=None,
    ):
        self.guard = guard
        self.resolver = resolver
        self.audit_hook = audit_hook
        self.ledger = ledger
        self.risk_engine = risk_engine
        self.validation_layer = validation_layer
        self.human_gate = human_gate
        self.accountability = accountability
        self.state = StateMachine()

    def run(self, payload: Any) -> Dict[str, Any]:
        """Execute full pipeline. Returns execution summary."""
        run_id = str(uuid.uuid4())[:8]
        self.guard.reset()
        self.state = StateMachine()

        if self.ledger:
            self.ledger.start_run(run_id)
        if self.risk_engine:
            self.risk_engine.reset()
        if self.validation_layer:
            self.validation_layer.reset()
        if self.accountability:
            self.accountability.reset()

        stages = self.resolver.get_stages()
        handlers = self.resolver.get_handlers()
        current_payload = payload
        stop_reason = None

        for stage_name in stages:
            self.guard.validate_entry(stage_name)
            handler_path = handlers.get(stage_name)

            # ① PRE-VALIDATION (Rule Engine + Simulator)
            if self.validation_layer:
                pre_result = self.validation_layer.validate_pre(
                    stage_name, handler_path, current_payload
                )
                if not pre_result.can_proceed:
                    stop_reason = f"Pre-validation failed at {stage_name}"
                    # Record as system decision
                    if self.accountability:
                        self.accountability.record_rule_decision(
                            stage=stage_name,
                            decision="halt_pre_validation",
                            rule_id="VALIDATION_LAYER_PRE",
                        )
                    break

                # ② HUMAN GATE (if escalation requested)
                if pre_result.escalate_to_human and self.human_gate:
                    approval = self.human_gate.request_approval(
                        stage=stage_name,
                        reasons=pre_result.escalation_reasons,
                        context=current_payload,
                    )
                    if self.accountability:
                        self.accountability.record_human_decision(
                            stage=stage_name,
                            decision="approve" if approval.approved else "reject",
                            human_identity=approval.approver,
                            rationale="; ".join(pre_result.escalation_reasons),
                            is_ccp=True,
                        )
                    if not approval.approved:
                        stop_reason = f"Human rejected at CCP {stage_name}"
                        break

            # ③ EXECUTE STAGE
            import time
            exec_start = time.perf_counter()
            result = self._execute_stage(stage_name, handler_path, current_payload)
            exec_time_ms = (time.perf_counter() - exec_start) * 1000

            self.guard.record_execution(stage_name)
            self.state.record(stage_name, result)

            # ④ AUDIT HOOK
            if self.audit_hook:
                self.audit_hook.on_stage_complete(stage_name, result)

            # ⑤ IMMUTABLE LEDGER
            if self.ledger:
                self.ledger.append(stage_name, result)

            # ⑥ RISK ENGINE
            if self.risk_engine:
                risk_record = self.risk_engine.evaluate_stage(stage_name, result)
                if risk_record.get("blocked"):
                    stop_reason = f"Risk blocked at {stage_name}"
                    break

            # ⑦ POST-VALIDATION (Critics + Anomaly Detector)
            if self.validation_layer:
                post_result = self.validation_layer.validate_post(
                    stage=stage_name,
                    input_payload=current_payload,
                    output_payload=result.data,
                    execution_time_ms=exec_time_ms,
                    stage_ok=result.ok,
                )

            # ⑧ ACCOUNTABILITY
            if self.accountability:
                self.accountability.record_ai_decision(
                    stage=stage_name,
                    decision="ok" if result.ok else "error",
                    rationale=result.error or "stage completed",
                    risk_score=self.risk_engine._stage_risks.get(
                        stage_name, type('', (), {'current_risk': 0})()
                    ).current_risk if self.risk_engine else 0,
                )

            if not result.ok:
                break
            if result.data is not None:
                current_payload = result.data

        if self.ledger:
            self.ledger.finalize()

        return self._build_summary(run_id, stop_reason)

    def _execute_stage(self, stage_name: str, handler_path: str,
                       payload: Any) -> StageResult:
        try:
            module = importlib.import_module(handler_path)
            result = module.handle(payload)
            if isinstance(result, dict):
                return StageResult(
                    stage=stage_name,
                    ok=result.get("ok", True),
                    data=result.get("data"),
                    error=result.get("error"),
                    metadata=result.get("metadata", {}),
                )
            return StageResult(stage=stage_name, ok=True, data=result)
        except Exception as e:
            return StageResult(stage=stage_name, ok=False, error=str(e))

    def _build_summary(self, run_id: str,
                       stop_reason: Optional[str] = None) -> Dict[str, Any]:
        summary = self.state.snapshot()
        summary["run_id"] = run_id
        if stop_reason:
            summary["stop_reason"] = stop_reason

        if self.ledger:
            summary["ledger"] = {
                "head_hash": self.ledger.head_hash(),
                "chain_valid": self.ledger.verify_chain(),
                "total_entries": self.ledger.total_entries(),
                "tampered": self.ledger.is_tampered(),
            }

        if self.risk_engine:
            summary["risk"] = self.risk_engine.summary().to_dict()

        if self.validation_layer:
            summary["validation"] = self.validation_layer.get_run_summary()

        if self.human_gate:
            summary["human_gate"] = self.human_gate.summary()

        if self.accountability:
            summary["accountability"] = self.accountability.compliance_check()

        return summary

    def snapshot(self) -> Dict[str, Any]:
        return self.state.snapshot()
