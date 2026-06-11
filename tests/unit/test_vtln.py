# tests/unit/test_vtln.py
# FID-VN-013 §2.5 — VTLN research module (AC-013, AC-014)
# KHÔNG test pipeline integration — module độc lập, chưa wire vào L0.

from __future__ import annotations

import numpy as np
import pytest

from src.core.vtln import (
    estimate_warp_factor, apply_vtln_warp, extract_f0_contour, WARP_MIN, WARP_MAX,
)


# ── AC-014: warp_factor=1.0 -> no-op (backward compat) ─────────────────────

def test_ac014_warp_factor_one_is_noop():
    y = np.random.RandomState(0).uniform(-0.5, 0.5, 16000).astype(np.float32)
    out = apply_vtln_warp(y, sr=16000, warp_factor=1.0)
    assert np.array_equal(out, y)


def test_ac014_empty_audio_is_noop():
    y = np.array([], dtype=np.float32)
    out = apply_vtln_warp(y, sr=16000, warp_factor=1.1)
    assert len(out) == 0


# ── estimate_warp_factor ─────────────────────────────────────────────────────

def test_estimate_warp_factor_silence_returns_one():
    """Audio im lặng (không pitch) -> warp_factor=1.0 (no-op)."""
    y = np.zeros(16000, dtype=np.float32)
    warp = estimate_warp_factor(y, sr=16000)
    assert warp == 1.0


def test_estimate_warp_factor_within_clip_range():
    """Tone với f0 cao hơn baseline -> warp_factor trong [WARP_MIN, WARP_MAX]."""
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # 200 Hz tone (cao hơn baseline 120 Hz)
    y = 0.5 * np.sin(2 * np.pi * 200 * t).astype(np.float32)
    warp = estimate_warp_factor(y, sr=sr, baseline_f0=120.0)
    assert WARP_MIN <= warp <= WARP_MAX
    assert warp > 1.0  # f0 cao hơn baseline -> warp > 1


# ── apply_vtln_warp output shape ─────────────────────────────────────────────

def test_apply_vtln_warp_preserves_length():
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    y = 0.3 * np.sin(2 * np.pi * 150 * t).astype(np.float32)
    out = apply_vtln_warp(y, sr=sr, warp_factor=1.1)
    assert len(out) == len(y)
    assert out.dtype == np.float32


def test_apply_vtln_warp_clips_extreme_factor():
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    y = 0.3 * np.sin(2 * np.pi * 150 * t).astype(np.float32)
    out_extreme = apply_vtln_warp(y, sr=sr, warp_factor=5.0)
    out_clipped = apply_vtln_warp(y, sr=sr, warp_factor=WARP_MAX)
    assert len(out_extreme) == len(out_clipped) == len(y)


# ── extract_f0_contour (FID-VN-015 §2.5) ────────────────────────────────────

def test_extract_f0_contour_empty_audio_returns_empty_list():
    assert extract_f0_contour(np.array([]), sr=16000) == []
    assert extract_f0_contour(None, sr=16000) == []


def test_extract_f0_contour_silence_returns_empty_list():
    """Audio im lặng (không có pitch voiced) -> []."""
    y = np.zeros(16000, dtype=np.float32)
    assert extract_f0_contour(y, sr=16000) == []


def test_extract_f0_contour_tone_returns_n_points():
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    y = 0.5 * np.sin(2 * np.pi * 150 * t).astype(np.float32)
    contour = extract_f0_contour(y, sr=sr, n_points=20)
    assert len(contour) == 20
    assert all(isinstance(v, float) for v in contour)
    assert all(v > 0 for v in contour)
