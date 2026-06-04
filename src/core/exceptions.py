# exceptions.py -- ISO/IEC 42001:2023 Clause 8.5

class PipelineError(Exception):
    """Base exception for all pipeline errors."""

class StageViolationError(PipelineError):
    """Raised when a stage violates its contract."""

class GuardViolationError(PipelineError):
    """Raised when PipelineGuard blocks execution."""

class AuditViolationError(PipelineError):
    """Raised when RuntimeAuditHook detects a violation (strict mode)."""

class SchemaViolationError(PipelineError):
    """Raised when payload does not match required schema."""

class GraphViolationError(PipelineError):
    """Raised when graph execution order is violated."""

class AuthorityViolationError(PipelineError):
    """Raised when a stage exceeds its defined authority."""
