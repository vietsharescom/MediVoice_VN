# state_machine.py -- ISO/IEC 42001:2023 Clause 9.1
from typing import List, Dict, Any, Optional
from .stage_result import StageResult

class StateMachine:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []
        self._current_stage: Optional[str] = None

    def record(self, stage: str, result: StageResult) -> None:
        self._history.append({"stage": stage, "ok": result.ok, "error": result.error, "metadata": result.metadata})
        self._current_stage = stage

    def get_history(self): return list(self._history)
    def get_current_stage(self): return self._current_stage
    def all_passed(self): return all(e["ok"] for e in self._history)

    def snapshot(self):
        return {"current_stage": self._current_stage, "total_stages": len(self._history),
                "all_passed": self.all_passed(), "history": self.get_history()}
