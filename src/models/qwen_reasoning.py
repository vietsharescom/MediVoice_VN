# src/models/qwen_reasoning.py
# Qwen2.5-3B-Instruct local LLM — Assessment + Plan generation
# FID: MV-FID-019
# Version: v1.0

import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

QWEN_MODEL_ID = "Qwen/Qwen2.5-3B-Instruct"
QWEN_MAX_NEW_TOKENS = 512
QWEN_TEMPERATURE = 0.2   # low temp for clinical consistency

_SYSTEM_PROMPT = """Bạn là bác sĩ AI hỗ trợ soạn SOAP note lâm sàng tại Canada.

QUY TẮC BẮT BUỘC:
1. DDx: chỉ liệt kê 3-4 chẩn đoán LIÊN QUAN TRỰC TIẾP đến triệu chứng chính. KHÔNG thêm chẩn đoán không liên quan.
2. KHÔNG kết luận chẩn đoán cuối cùng — chỉ đưa ra phân biệt.
3. "Đang dùng thuốc" = thuốc bệnh nhân đang điều trị, KHÔNG phải nguyên nhân gây bệnh.
4. Plan: tối thiểu 4 bước thực tế, ngắn gọn, phù hợp guideline.
5. Ngôn ngữ: tiếng Việt y khoa ngắn gọn, chuẩn xác.
6. PHẢI dùng đúng format này (không thay đổi nhãn):

A — Assessment: [nhận định + DDx ngắn gọn]
P — Plan: [các bước xử trí]
⚠️ Cần bác sĩ xem xét và quyết định lâm sàng."""

_USER_TEMPLATE = """THÔNG TIN BỆNH NHÂN:
{patient_summary}

HƯỚNG DẪN LÂM SÀNG LIÊN QUAN:
{kb_context}

Viết Assessment và Plan theo đúng format trên:"""


def _build_patient_summary(entities: List) -> str:
    """Convert NEREntity list to Vietnamese patient summary string."""
    parts = []
    age = next((e.value for e in entities if e.type == "AGE"), None)
    gender = next((e.value for e in entities if e.type == "GENDER"), None)
    gender_vi = {"male": "nam", "female": "nữ"}.get(gender, "") if gender else ""

    if age and gender_vi:
        parts.append(f"Bệnh nhân {gender_vi} {age} tuổi.")
    elif age:
        parts.append(f"Bệnh nhân {age} tuổi.")

    symptoms = [e.value for e in entities if e.type == "SYMPTOM"]
    if symptoms:
        parts.append(f"Triệu chứng: {', '.join(symptoms)}.")

    vitals = [e for e in entities if e.type == "VITAL"]
    for v in vitals:
        name = (v.name or "").replace("_", " ")
        parts.append(f"{name.title()}: {v.value} {v.unit or ''}".strip() + ".")

    meds = [e for e in entities if e.type == "MEDICATION"]
    for m in meds:
        freq = f" {m.frequency}" if m.frequency else ""
        parts.append(f"Đang dùng: {m.value} {m.dose or ''}{freq}.")

    history = [e.value for e in entities if e.type == "HISTORY"]
    if history:
        parts.append(f"Tiền sử: {', '.join(history)}.")

    return " ".join(parts) if parts else "Không có thông tin."


class QwenReasoner:
    """
    Qwen2.5-3B-Instruct local inference for SOAP Assessment + Plan.

    Usage:
        qwen = QwenReasoner()
        qwen.load()
        result = qwen.generate(entities, kb_chunks)
        # result = {"assessment": "...", "plan": "...", "source": "qwen"}
    """

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._loaded = False
        self._load_attempted = False

    def load(self) -> bool:
        """Lazy-load Qwen2.5-3B-Instruct. Returns True on success."""
        if self._loaded or self._load_attempted:
            return self._loaded
        self._load_attempted = True
        if os.environ.get("MEDIVOICE_SKIP_QWEN"):
            logger.info("MEDIVOICE_SKIP_QWEN set — skipping Qwen load, using template DDx")
            return False
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch

            logger.info("Loading %s (this may take a while on first run)...", QWEN_MODEL_ID)
            self._tokenizer = AutoTokenizer.from_pretrained(
                QWEN_MODEL_ID, trust_remote_code=True
            )
            self._model = AutoModelForCausalLM.from_pretrained(
                QWEN_MODEL_ID,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else "cpu",
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )
            self._model.eval()
            self._loaded = True
            logger.info("QwenReasoner loaded: %s", QWEN_MODEL_ID)
            return True
        except ImportError:
            logger.warning("transformers not available for Qwen — falling back to template DDx")
            return False
        except Exception as exc:
            logger.error("QwenReasoner load failed: %s — falling back to template DDx", exc)
            return False

    def generate(self, entities: List, kb_chunks: List[str]) -> Dict[str, str]:
        """
        Generate Assessment + Plan from entities and KB context.
        Returns dict with keys: assessment, plan, source.
        Falls back to {"assessment": "", "plan": "", "source": "fallback"} on failure.
        """
        if not self._loaded:
            return {"assessment": "", "plan": "", "source": "fallback"}
        try:
            patient_summary = _build_patient_summary(entities)
            kb_context = "\n\n".join(kb_chunks) if kb_chunks else "Không có hướng dẫn cụ thể."

            user_content = _USER_TEMPLATE.format(
                patient_summary=patient_summary,
                kb_context=kb_context[:2000],   # cap to avoid token overflow
            )

            messages = [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": user_content},
            ]

            import torch
            text = self._tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = self._tokenizer(text, return_tensors="pt").to(self._model.device)

            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=QWEN_MAX_NEW_TOKENS,
                    temperature=QWEN_TEMPERATURE,
                    do_sample=True,
                    pad_token_id=self._tokenizer.eos_token_id,
                )

            generated = self._tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True,
            ).strip()

            assessment, plan = self._parse_output(generated)
            return {"assessment": assessment, "plan": plan, "source": "qwen"}

        except Exception as exc:
            logger.error("QwenReasoner.generate failed: %s", exc)
            return {"assessment": "", "plan": "", "source": "fallback"}

    def _parse_output(self, raw: str) -> tuple:
        """Split Qwen output into (assessment, plan). Handles A—/P—/B— variants."""
        assessment, plan = "", ""
        lines = raw.split("\n")
        current = None
        buf = []

        _A_MARKERS = ("A —", "A—", "A -", "**A")
        # B — is Qwen's alternate for Plan section
        _P_MARKERS = ("P —", "P—", "P -", "**P", "B —", "B—", "B -", "**B")

        for line in lines:
            l = line.strip()
            l_lower = l.lower()

            is_assessment = (
                any(l.startswith(m) for m in _A_MARKERS) or
                l_lower.startswith("assessment") or
                l_lower.startswith("a. nhận định") or
                l_lower.startswith("nhận định lâm sàng")
            )
            is_plan = (
                any(l.startswith(m) for m in _P_MARKERS) or
                l_lower.startswith("plan") or
                l_lower.startswith("p. kế hoạch") or
                l_lower.startswith("kế hoạch xử trí")
            )

            if is_assessment:
                if current == "plan":
                    plan = "\n".join(buf).strip()
                current = "assessment"
                rest = l.split(":", 1)[-1].strip() if ":" in l else ""
                buf = [rest] if rest else []
            elif is_plan:
                if current == "assessment":
                    assessment = "\n".join(buf).strip()
                current = "plan"
                rest = l.split(":", 1)[-1].strip() if ":" in l else ""
                buf = [rest] if rest else []
            elif current and l:
                buf.append(l)

        if current == "assessment":
            assessment = "\n".join(buf).strip()
        elif current == "plan":
            plan = "\n".join(buf).strip()

        # Fallback: if still no plan, look for numbered list after assessment
        if assessment and not plan and raw:
            import re
            plan_match = re.search(
                r'(?:kế hoạch|plan|xử trí)[:\s]*\n?((?:\d+[.)].+\n?)+)',
                raw, re.IGNORECASE | re.UNICODE
            )
            if plan_match:
                plan = plan_match.group(1).strip()

        disclaimer = "⚠️ Cần bác sĩ xem xét và quyết định lâm sàng."
        if assessment and disclaimer not in assessment and disclaimer not in plan:
            plan = (plan + "\n" + disclaimer).strip() if plan else disclaimer

        return assessment, plan


# Module-level singleton
_qwen_instance: Optional[QwenReasoner] = None


def get_qwen_reasoner() -> QwenReasoner:
    """Return singleton QwenReasoner, loading model on first call."""
    global _qwen_instance
    if _qwen_instance is None:
        _qwen_instance = QwenReasoner()
        _qwen_instance.load()
    return _qwen_instance
