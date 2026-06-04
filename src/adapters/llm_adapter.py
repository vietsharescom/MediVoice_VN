# llm_adapter.py -- ISO/IEC 42001:2023 Annex A.4
# Replace with your LLM provider. Only L6_AGENT calls this.

from typing import Optional

class LLMAdapter:
    def __init__(self, model: str = "[MODEL_NAME]", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key

    def complete(self, prompt: str, system: Optional[str] = None) -> str:
        raise NotImplementedError("Implement with your LLM provider.")

    def embed(self, text: str) -> list:
        raise NotImplementedError("Implement with your embedding provider.")
