# L8 — Error Handling + Recovery
# FROZEN PIPELINE LAYER

from __future__ import annotations
import logging
import functools
from enum import Enum
from typing import Callable, Any

logger = logging.getLogger(__name__)


class PipelineErrorCode(str, Enum):
    ASR_FAILED = "ASR_FAILED"
    NER_FAILED = "NER_FAILED"
    ICD_NOT_FOUND = "ICD_NOT_FOUND"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    STORAGE_FAILED = "STORAGE_FAILED"
    PDF_FAILED = "PDF_FAILED"
    AUDIT_FAILED = "AUDIT_FAILED"
    L4_NOT_APPROVED = "L4_NOT_APPROVED"


class PipelineError(Exception):
    def __init__(self, code: PipelineErrorCode, message: str, layer: str = ""):
        self.code = code
        self.layer = layer
        super().__init__(f"[{layer}] {code}: {message}")


def with_recovery(layer: str, fallback=None):
    """
    Decorator: bắt exception tại một layer, log, và trả về fallback.
    Pipeline không crash — lỗi tại layer nào thì layer đó trả rỗng/None.
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return fn(*args, **kwargs)
            except PipelineError:
                raise  # PipelineError đã có context đầy đủ
            except Exception as e:
                logger.error(f"[{layer}] Unexpected error: {e}", exc_info=True)
                if fallback is not None:
                    return fallback() if callable(fallback) else fallback
                raise PipelineError(
                    PipelineErrorCode.VALIDATION_FAILED,
                    str(e),
                    layer=layer
                )
        return wrapper
    return decorator


def safe_log(fn: Callable) -> Callable:
    """Decorator: bắt lỗi audit log — không được crash pipeline chính."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            logger.critical(f"AUDIT LOG FAILED: {e}", exc_info=True)
    return wrapper
