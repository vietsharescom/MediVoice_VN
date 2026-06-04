# execution_proof.py -- ISO/IEC 42001:2023 Clause 9.1
import hashlib, json
from datetime import datetime
from typing import Any, Dict, List, Optional

class ExecutionProof:
    def __init__(self, run_id: str, input_payload: Any):
        self.run_id = run_id
        self.started_at = datetime.utcnow().isoformat()
        self.input_hash = hashlib.sha256(json.dumps(str(input_payload)).encode()).hexdigest()[:16]
        self.stage_records: List[Dict] = []
        self.status: str = "IN_PROGRESS"
        self.completed_at: Optional[str] = None

    def record_stage(self, stage: str, ok: bool, error: Optional[str] = None) -> None:
        self.stage_records.append({"stage": stage, "ok": ok, "error": error,
                                   "timestamp": datetime.utcnow().isoformat()})

    def finalize(self, ok: bool) -> None:
        self.status = "VALID" if ok else "INVALID"
        self.completed_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {"run_id": self.run_id, "status": self.status,
                "started_at": self.started_at, "completed_at": self.completed_at,
                "input_hash": self.input_hash, "stages": self.stage_records}
