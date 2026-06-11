# tests/unit/test_audio_quality.py
# FID-VN-013 §2.1 — Recording quality score + behavioral hints (pure JS, run via Node)
# AC-004, AC-005

from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path

import pytest

JS_FILE = Path(__file__).resolve().parents[2] / "src" / "api" / "static" / "js" / "audio_quality.js"

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="node not available in PATH"
)


def _call(fn: str, **kwargs):
    script = (
        f"const AQ = require({json.dumps(str(JS_FILE))});"
        f"const args = {json.dumps(kwargs)};"
        f"console.log(JSON.stringify(AQ.{fn}(" +
        ",".join(f"args.{k}" for k in kwargs) +
        ")));"
    )
    result = subprocess.run(
        ["node", "-e", script], capture_output=True, text=True, check=True,
        encoding="utf-8",
    )
    return json.loads(result.stdout.strip())


# ── AC-004: computeQualityScore ─────────────────────────────────────────────

def test_ac004_silence_is_low_signal():
    """RMS ~0 → lowSignal=True, score giảm."""
    samples = [0.0] * 1000
    q = _call("computeQualityScore", samples=samples)
    assert q["lowSignal"] is True
    assert q["clipping"] is False
    assert q["score"] <= 60


def test_ac004_clipping_detected():
    """Nhiều sample >= 0.95 → clipping=True."""
    samples = [0.99] * 100 + [0.5] * 900
    q = _call("computeQualityScore", samples=samples)
    assert q["clipping"] is True
    assert q["score"] <= 60


def test_ac004_normal_signal_high_score():
    """RMS vừa phải, không clip → score cao, không có vấn đề."""
    import math
    samples = [0.3 * math.sin(i * 0.1) for i in range(1000)]
    q = _call("computeQualityScore", samples=samples)
    assert q["clipping"] is False
    assert q["lowSignal"] is False
    assert q["noiseFloor"] is False
    assert q["score"] == 100


def test_ac004_noise_floor_high_rms_no_clip():
    """RMS cao nhưng không clip (vd noise lấp đầy) → noiseFloor=True."""
    samples = [0.6] * 1000
    q = _call("computeQualityScore", samples=samples)
    assert q["clipping"] is False
    assert q["noiseFloor"] is True
    assert q["score"] < 100


def test_ac004_empty_samples():
    q = _call("computeQualityScore", samples=[])
    assert q["score"] == 0
    assert q["lowSignal"] is True


# ── AC-005: getBehavioralHint ───────────────────────────────────────────────

def test_ac005_hint_clipping_priority():
    quality = {"clipping": True, "lowSignal": True, "noiseFloor": True}
    hint = _call("getBehavioralHint", quality=quality)
    assert "to" in hint or "xa" in hint  # gợi ý nói nhỏ / để xa micro


def test_ac005_hint_low_signal():
    quality = {"clipping": False, "lowSignal": True, "noiseFloor": False}
    hint = _call("getBehavioralHint", quality=quality)
    assert "gần" in hint or "to hơn" in hint


def test_ac005_hint_noise_floor():
    quality = {"clipping": False, "lowSignal": False, "noiseFloor": True}
    hint = _call("getBehavioralHint", quality=quality)
    assert "ồn" in hint


def test_ac005_no_hint_when_quality_good():
    quality = {"clipping": False, "lowSignal": False, "noiseFloor": False}
    hint = _call("getBehavioralHint", quality=quality)
    assert hint is None


# ── AC-003: detectPauses ─────────────────────────────────────────────────────

def test_ac003_pause_over_threshold_detected():
    """20 frames * 100ms = 2s of silence (> 1.5s) → 1 pause detected."""
    rms_history = [0.3] * 5 + [0.0] * 20 + [0.3] * 5
    pauses = _call("detectPauses", rmsHistory=rms_history, frameDurationMs=100, pauseThresholdMs=1500)
    assert len(pauses) == 1
    assert pauses[0]["startFrame"] == 5
    assert pauses[0]["endFrame"] == 24


def test_ac003_short_pause_not_detected():
    """5 frames * 100ms = 500ms of silence (< 1.5s) → no pause."""
    rms_history = [0.3] * 5 + [0.0] * 5 + [0.3] * 5
    pauses = _call("detectPauses", rmsHistory=rms_history, frameDurationMs=100, pauseThresholdMs=1500)
    assert len(pauses) == 0
