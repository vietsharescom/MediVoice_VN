import os

# Disable Qwen LLM loading during tests — use template DDx fallback instead.
# Prevents 3B model from loading (slow, non-deterministic) in unit/integration tests.
# MEDIVOICE_SKIP_QWEN is checked in src/models/qwen_reasoning.py QwenReasoner.load()
os.environ.setdefault("MEDIVOICE_SKIP_QWEN", "1")
