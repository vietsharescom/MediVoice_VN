# stage_result.py -- ISO/IEC 42001:2023 Clause 8.5
from dataclasses import dataclass, field
from typing import Any, Optional, Dict

@dataclass
class StageResult:
    stage: str
    ok: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return {"stage": self.stage, "ok": self.ok, "data": self.data,
                "error": self.error, "metadata": self.metadata}
