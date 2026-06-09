# tests/unit/test_l1a_prompt_inject.py
# A1-PROMPT-INJECT unit tests — FID-VN-010
# Chỉ test pure functions + mock pipeline (không load PhoWhisper thật)

import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from src.core.l1a_asr import (
    SPECIALTY_DRUG_CLASSES,
    build_initial_prompt,
    get_drugs_by_specialty,
    transcribe,
    transcribe_chunks,
)

# ---------------------------------------------------------------------------
# Minimal mock drug_db — không cần load file thật
# ---------------------------------------------------------------------------

MOCK_DB = {
    "by_inn": {
        "DrugStatin": {"inn": "DrugStatin", "drug_class": "statin", "compatible_diagnoses": []},
        "DrugACE": {"inn": "DrugACE", "drug_class": "ace_inhibitor", "compatible_diagnoses": []},
        "DrugARB": {"inn": "DrugARB", "drug_class": "arb", "compatible_diagnoses": []},
        "DrugPeni": {"inn": "DrugPeni", "drug_class": "penicillin", "compatible_diagnoses": []},
        "DrugCeph": {"inn": "DrugCeph", "drug_class": "cephalosporin_3g", "compatible_diagnoses": []},
        "DrugNSAID": {"inn": "DrugNSAID", "drug_class": "nsaid", "compatible_diagnoses": []},
        "DrugPPI": {"inn": "DrugPPI", "drug_class": "ppi", "compatible_diagnoses": []},
        "DrugCortico": {"inn": "DrugCortico", "drug_class": "corticosteroid", "compatible_diagnoses": []},
        "DrugBiguanide": {"inn": "DrugBiguanide", "drug_class": "biguanide", "compatible_diagnoses": []},
        "DrugAntiHist": {"inn": "DrugAntiHist", "drug_class": "antihistamine_2nd_gen", "compatible_diagnoses": []},
        "DrugMacrolide": {"inn": "DrugMacrolide", "drug_class": "macrolide", "compatible_diagnoses": []},
        "DrugOpioid": {"inn": "DrugOpioid", "drug_class": "opioid_weak", "compatible_diagnoses": []},
        "DrugUnknown": {"inn": "DrugUnknown", "drug_class": "unknown_class", "compatible_diagnoses": []},
    }
}


# ---------------------------------------------------------------------------
# get_drugs_by_specialty
# ---------------------------------------------------------------------------

class TestGetDrugsBySpecialty:
    def test_noi_khoa_returns_specialty_drugs(self):
        names = get_drugs_by_specialty(MOCK_DB, "noi_khoa", n=30)
        assert "DrugStatin" in names
        assert "DrugACE" in names
        assert "DrugARB" in names
        assert "DrugBiguanide" in names

    def test_nhi_khoa_returns_specialty_drugs(self):
        names = get_drugs_by_specialty(MOCK_DB, "nhi_khoa", n=30)
        assert "DrugPeni" in names
        assert "DrugCeph" in names
        assert "DrugMacrolide" in names
        assert "DrugAntiHist" in names

    def test_lam_sang_returns_all_drugs(self):
        names = get_drugs_by_specialty(MOCK_DB, "lam_sang", n=30)
        assert len(names) == len(MOCK_DB["by_inn"])

    def test_unknown_specialty_returns_all_drugs(self):
        # Specialty không có trong map → None → all drugs
        names = get_drugs_by_specialty(MOCK_DB, "specialty_not_exist", n=30)
        assert len(names) == len(MOCK_DB["by_inn"])

    def test_respects_n_limit(self):
        names = get_drugs_by_specialty(MOCK_DB, "lam_sang", n=3)
        assert len(names) == 3

    def test_n_larger_than_pool_returns_all(self):
        names = get_drugs_by_specialty(MOCK_DB, "lam_sang", n=1000)
        assert len(names) == len(MOCK_DB["by_inn"])

    def test_supplements_when_specialty_has_fewer_than_n(self):
        # ngoai_khoa chỉ có 6 drugs trong MOCK_DB — request n=10 → bổ sung
        names = get_drugs_by_specialty(MOCK_DB, "ngoai_khoa", n=10)
        assert len(names) == 10

    def test_specialty_drugs_come_first(self):
        # tim_mach drugs phải đứng trước supplement drugs
        names = get_drugs_by_specialty(MOCK_DB, "tim_mach", n=30)
        assert "DrugStatin" in names
        assert "DrugACE" in names

    def test_empty_drug_db(self):
        names = get_drugs_by_specialty({"by_inn": {}}, "noi_khoa")
        assert names == []

    def test_drug_missing_inn_field_excluded(self):
        db = {"by_inn": {"X": {"drug_class": "statin"}}}  # no 'inn' key
        names = get_drugs_by_specialty(db, "noi_khoa")
        assert names == []

    def test_no_duplicate_in_result(self):
        names = get_drugs_by_specialty(MOCK_DB, "noi_khoa", n=30)
        assert len(names) == len(set(names))


# ---------------------------------------------------------------------------
# build_initial_prompt
# ---------------------------------------------------------------------------

class TestBuildInitialPrompt:
    def test_returns_string(self):
        result = build_initial_prompt(MOCK_DB, "noi_khoa")
        assert isinstance(result, str)

    def test_contains_drug_names(self):
        result = build_initial_prompt(MOCK_DB, "noi_khoa")
        assert "DrugStatin" in result or "DrugACE" in result

    def test_contains_required_prefix(self):
        result = build_initial_prompt(MOCK_DB, "noi_khoa")
        assert result.startswith("Bác sĩ Việt Nam kê đơn thuốc y tế:")

    def test_contains_required_suffix_keywords(self):
        result = build_initial_prompt(MOCK_DB, "noi_khoa")
        assert "Chẩn đoán" in result
        assert "sinh hiệu" in result
        assert "tái khám" in result

    def test_different_specialties_produce_different_prompts(self):
        p1 = build_initial_prompt(MOCK_DB, "nhi_khoa")
        p2 = build_initial_prompt(MOCK_DB, "tim_mach")
        assert p1 != p2

    def test_lam_sang_prompt_includes_many_drugs(self):
        result = build_initial_prompt(MOCK_DB, "lam_sang")
        # lam_sang = tất cả drugs, nhiều tên hơn specialty hẹp
        drug_section = result.split(":")[1].split(".")[0]
        drug_count = len(drug_section.split(","))
        assert drug_count > 0


# ---------------------------------------------------------------------------
# transcribe — mock pipeline (không load PhoWhisper thật)
# ---------------------------------------------------------------------------

class TestTranscribeWithPromptInjection:
    def _make_audio(self):
        return np.zeros(16000, dtype=np.float32)

    def test_transcribe_without_drug_db_no_prompt(self):
        mock_pipe = MagicMock(return_value={"text": "xin chào"})
        with patch("src.core.l1a_asr._pipeline", mock_pipe):
            result = transcribe(self._make_audio())
        assert result == "xin chào"
        # Không có drug_db → pipe gọi không có initial_prompt
        call_kwargs = mock_pipe.call_args[1] if mock_pipe.call_args else {}
        assert "initial_prompt" not in call_kwargs

    def test_transcribe_with_drug_db_passes_initial_prompt(self):
        mock_pipe = MagicMock(return_value={"text": "Amoxicillin 500mg"})
        with patch("src.core.l1a_asr._pipeline", mock_pipe):
            result = transcribe(self._make_audio(), drug_db=MOCK_DB, specialty="nhi_khoa")
        assert result == "Amoxicillin 500mg"
        call_kwargs = mock_pipe.call_args[1]
        assert "initial_prompt" in call_kwargs
        assert "DrugPeni" in call_kwargs["initial_prompt"]

    def test_transcribe_fallback_when_initial_prompt_not_supported(self):
        # Simulate transformers version không support initial_prompt
        call_count = {"n": 0}

        def side_effect(audio_input, **kwargs):
            call_count["n"] += 1
            if "initial_prompt" in kwargs:
                raise TypeError("unexpected keyword argument 'initial_prompt'")
            return {"text": "fallback result"}

        mock_pipe = MagicMock(side_effect=side_effect)
        with patch("src.core.l1a_asr._pipeline", mock_pipe):
            result = transcribe(self._make_audio(), drug_db=MOCK_DB)
        assert result == "fallback result"
        assert call_count["n"] == 2  # lần 1 raise, lần 2 fallback

    def test_transcribe_returns_empty_when_pipeline_none(self):
        with patch("src.core.l1a_asr._pipeline", None):
            with patch("src.core.l1a_asr._load_pipeline", return_value=None):
                result = transcribe(self._make_audio(), drug_db=MOCK_DB)
        assert result == ""

    def test_transcribe_chunks_passes_drug_db(self):
        mock_pipe = MagicMock(return_value={"text": "thuốc"})
        chunks = [self._make_audio(), self._make_audio()]
        with patch("src.core.l1a_asr._pipeline", mock_pipe):
            result = transcribe_chunks(chunks, drug_db=MOCK_DB, specialty="noi_khoa")
        assert result == "thuốc thuốc"
        # Mỗi chunk đều có initial_prompt
        for call in mock_pipe.call_args_list:
            assert "initial_prompt" in call[1]

    def test_transcribe_strips_whitespace(self):
        mock_pipe = MagicMock(return_value={"text": "  xin chào bác sĩ  "})
        with patch("src.core.l1a_asr._pipeline", mock_pipe):
            result = transcribe(self._make_audio(), drug_db=MOCK_DB)
        assert result == "xin chào bác sĩ"
