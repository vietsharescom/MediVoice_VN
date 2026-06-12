import os

# Disable Qwen LLM loading during tests — use template DDx fallback instead.
# Prevents 3B model from loading (slow, non-deterministic) in unit/integration tests.
# MEDIVOICE_SKIP_QWEN is checked in src/models/qwen_reasoning.py QwenReasoner.load()
os.environ.setdefault("MEDIVOICE_SKIP_QWEN", "1")

# Ensure SQLite schema exists before API integration tests run.
# TestClient(app) without a `with` block never fires FastAPI's startup
# event (which normally calls init_db()), so tables may be missing.
from src.core.l7_storage import init_db  # noqa: E402

init_db()
