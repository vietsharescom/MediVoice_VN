"""
Tests for pipeline p0/p1/p2/p3 stage structure.
@verifies SRS-L0-001, SRS-L1a-001, SRS-L4-001
"""
import pytest


class TestPipelineStaging:
    """p0/p1/p2/p3 stage imports phải hoạt động."""

    def test_p0_ingestion_imports(self):
        from src.pipeline.p0_ingestion import normalize, chunk_audio, has_speech
        assert callable(normalize)
        assert callable(chunk_audio)
        assert callable(has_speech)

    def test_p1_processing_imports(self):
        from src.pipeline.p1_processing import (
            transcribe, correct_drug_names, extract_entities,
            auto_lookup, validate, detect_route
        )
        assert callable(transcribe)
        assert callable(correct_drug_names)
        assert callable(extract_entities)
        assert callable(auto_lookup)
        assert callable(validate)
        assert callable(detect_route)

    def test_p2_decision_imports(self):
        from src.pipeline.p2_decision import (
            require_human_approval, approve, reject,
            assert_approved, scan_form_data, generate_benh_an,
            init_db, store_record
        )
        assert callable(require_human_approval)
        assert callable(approve)
        assert callable(reject)
        assert callable(generate_benh_an)

    def test_p3_output_imports(self):
        from src.pipeline.p3_output import (
            export_pdf, log_event, verify_chain, with_recovery, safe_log
        )
        assert callable(export_pdf)
        assert callable(log_event)
        assert callable(verify_chain)
        assert callable(with_recovery)
        assert callable(safe_log)

    def test_orchestrator_import(self):
        from src.core.orchestrator import Orchestrator, PipelineResult, StageResult
        assert Orchestrator is not None
        assert PipelineResult is not None
        assert StageResult is not None

    def test_orchestrator_initialization(self):
        from src.core.orchestrator import Orchestrator
        from src.validation.validation_layer import ValidationLayer
        vl = ValidationLayer()
        orch = Orchestrator(validation_layer=vl)
        assert orch.validation_layer is vl

    def test_orchestrator_without_validation_layer(self):
        from src.core.orchestrator import Orchestrator
        orch = Orchestrator()
        assert orch.validation_layer is None

    def test_stage_result_to_dict(self):
        from src.core.orchestrator import StageResult
        sr = StageResult(stage="L0", ok=True, duration_ms=50.0)
        d = sr.to_dict()
        assert d["stage"] == "L0"
        assert d["ok"] is True
        assert "duration_ms" in d
