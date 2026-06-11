# src/core/vtln.py
# FID-VN-013 §2.5 — VTLN (Vocal Tract Length Normalization) — RESEARCH (AC-013)
#
# KHÔNG được gọi từ pipeline L0->L10 (FROZEN) cho đến khi POC (scripts/vtln_poc.py)
# chứng minh >=3% relative WER reduction (AC-013). Hiện tại chỉ là module nghiên cứu
# độc lập — estimate_warp_factor() + apply_vtln_warp() là các pure function có thể
# test riêng, KHÔNG động tới audio pipeline thật.
#
# Risk: THẤP — output là 1 scalar (warp_factor), không phải biometric fingerprint
# (6/6 AI consensus, CONS-20260610-005.md).

from __future__ import annotations

import numpy as np

WARP_MIN = 0.8
WARP_MAX = 1.2
DEFAULT_BASELINE_F0 = 120.0  # Hz — tần số cơ bản trung tính (giữa nam/nữ trưởng thành)


def estimate_warp_factor(
    y: np.ndarray,
    sr: int = 16000,
    baseline_f0: float = DEFAULT_BASELINE_F0,
) -> float:
    """
    Ước lượng VTLN warp factor từ pitch (f0) trung vị của 1 đoạn audio mẫu.

    warp_factor = median_f0(BS) / baseline_f0, clip về [0.8, 1.2].
    Trả về 1.0 (no-op) nếu không phát hiện được pitch (vd audio im lặng/lỗi).
    """
    import librosa

    if y is None or len(y) == 0:
        return 1.0

    f0, voiced_flag, _ = librosa.pyin(
        y.astype(np.float32),
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        sr=sr,
    )
    voiced_f0 = f0[voiced_flag.astype(bool)] if voiced_flag is not None else f0
    voiced_f0 = voiced_f0[~np.isnan(voiced_f0)]
    if voiced_f0.size == 0:
        return 1.0

    median_f0 = float(np.median(voiced_f0))
    warp = median_f0 / baseline_f0
    return float(np.clip(warp, WARP_MIN, WARP_MAX))


def apply_vtln_warp(y: np.ndarray, sr: int, warp_factor: float) -> np.ndarray:
    """
    Áp frequency warp lên audio theo warp_factor (resample-based formant shift).

    warp_factor == 1.0 -> trả về y nguyên vẹn (AC-014: backward compat no-op).
    """
    if y is None or len(y) == 0 or abs(warp_factor - 1.0) < 1e-6:
        return y

    import librosa

    warp_factor = float(np.clip(warp_factor, WARP_MIN, WARP_MAX))

    # Resample lên/xuống theo warp_factor rồi resample lại về sr gốc — thay đổi
    # tỉ lệ formant/tần số mà giữ nguyên độ dài tổng thể (qua time_stretch bù lại).
    warped_sr = int(round(sr * warp_factor))
    y_resampled = librosa.resample(y.astype(np.float32), orig_sr=sr, target_sr=warped_sr)
    y_back = librosa.resample(y_resampled, orig_sr=warped_sr, target_sr=sr)

    # time_stretch để bù chiều dài lệch do resample 2 lần (giữ duration gốc)
    if len(y_back) > 0:
        rate = len(y_back) / len(y)
        y_out = librosa.effects.time_stretch(y_back, rate=rate)
    else:
        y_out = y_back

    # Khớp độ dài chính xác (pad/truncate) để tương thích L0 pipeline
    if len(y_out) < len(y):
        y_out = np.pad(y_out, (0, len(y) - len(y_out)))
    else:
        y_out = y_out[: len(y)]

    return y_out.astype(np.float32)
