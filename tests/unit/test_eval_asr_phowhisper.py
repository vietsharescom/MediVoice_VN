# tests/unit/test_eval_asr_phowhisper.py
# TRAIN-001: WER aggregation helpers for scripts/eval_asr_phowhisper.py

from scripts.eval_asr_phowhisper import _norm, aggregate, compute_wer


class TestNorm:
    def test_lowercases_and_collapses_whitespace(self):
        assert _norm("  Bệnh  Nhân   Đau  ") == "bệnh nhân đau"


class TestComputeWer:
    def test_identical_text_zero_wer(self):
        assert compute_wer("benh nhan dau dau", "benh nhan dau dau") == 0.0

    def test_empty_ref_returns_none(self):
        assert compute_wer("", "benh nhan") is None

    def test_one_word_diff_nonzero(self):
        wer = compute_wer("benh nhan dau dau", "benh nhan dau bung")
        assert wer is not None and wer > 0


class TestAggregate:
    def test_mean_over_samples(self):
        samples = [{"wer": 0.1}, {"wer": 0.3}, {"wer": 0.2}]
        assert aggregate(samples) == 0.2

    def test_skips_none_wer(self):
        samples = [{"wer": 0.2}, {"wer": None}, {"wer": 0.4}]
        assert aggregate(samples) == 0.3

    def test_empty_returns_none(self):
        assert aggregate([]) is None
