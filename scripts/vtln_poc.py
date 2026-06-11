#!/usr/bin/env python
# scripts/vtln_poc.py
# FID-VN-013 §2.5 — VTLN POC (AC-013, RESEARCH — chưa wire vào L0/pipeline)
#
# Mục tiêu: đo WER trước/sau khi áp VTLN warp lên audio pilot, để quyết định
# có implement chính thức (L0 integration) hay không.
#
# Gate: CHỈ enable VTLN tại L0 nếu WER giảm >=3% relative. Nếu không đủ bằng
# chứng -> giữ vtln_warp_factor=1.0 mặc định (no-op), KHÔNG rollout.
#
# YÊU CẦU: PhoWhisper-medium model load được (CPU/GPU) + audio pilot có
# ground-truth transcript đầy đủ (data/audio/corpus/.../groundtruth_all.json
# hiện chỉ có structured fields, CHƯA có full transcript text -> cần Andy bổ
# sung transcript text trước khi WER có thể tính chính xác).
#
# Usage:
#   python -X utf8 scripts/vtln_poc.py --audio path/to/file.wav [--baseline-f0 120]
#   python -X utf8 scripts/vtln_poc.py --audio path/to/file.wav --reference "câu nói tham chiếu"

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import soundfile as sf

from src.core.vtln import estimate_warp_factor, apply_vtln_warp


def _word_error_rate(ref: str, hyp: str) -> float:
    """Levenshtein-based WER trên token level."""
    ref_tokens = ref.lower().split()
    hyp_tokens = hyp.lower().split()
    if not ref_tokens:
        return 0.0 if not hyp_tokens else 1.0

    n, m = len(ref_tokens), len(hyp_tokens)
    dp = np.zeros((n + 1, m + 1), dtype=int)
    dp[:, 0] = np.arange(n + 1)
    dp[0, :] = np.arange(m + 1)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref_tokens[i - 1] == hyp_tokens[j - 1] else 1
            dp[i, j] = min(dp[i - 1, j] + 1, dp[i, j - 1] + 1, dp[i - 1, j - 1] + cost)
    return dp[n, m] / n


def main() -> None:
    parser = argparse.ArgumentParser(description="VTLN POC — FID-VN-013 §2.5 / AC-013")
    parser.add_argument("--audio", required=True, help="Đường dẫn file .wav 16kHz mono")
    parser.add_argument("--baseline-f0", type=float, default=120.0)
    parser.add_argument("--reference", default=None, help="Transcript tham chiếu (ground truth) để tính WER")
    parser.add_argument("--out-warped", default=None, help="Lưu audio sau warp để nghe thử (debug)")
    args = parser.parse_args()

    audio_path = Path(args.audio)
    y, sr = sf.read(str(audio_path), dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)

    warp_factor = estimate_warp_factor(y, sr=sr, baseline_f0=args.baseline_f0)
    print(f"File: {audio_path}")
    print(f"Sample rate: {sr} Hz, duration: {len(y)/sr:.2f}s")
    print(f"Estimated VTLN warp_factor: {warp_factor:.4f}")

    y_warped = apply_vtln_warp(y, sr=sr, warp_factor=warp_factor)

    if args.out_warped:
        sf.write(args.out_warped, y_warped, sr)
        print(f"Warped audio written to: {args.out_warped}")

    if args.reference:
        from src.core import l1a_asr
        from src.core.l1b_drug_correct import _load_drug_db

        drug_db = _load_drug_db()
        transcript_orig = l1a_asr.transcribe(y, sample_rate=sr, drug_db=drug_db)
        transcript_warped = l1a_asr.transcribe(y_warped, sample_rate=sr, drug_db=drug_db)

        wer_orig = _word_error_rate(args.reference, transcript_orig)
        wer_warped = _word_error_rate(args.reference, transcript_warped)
        rel_change = (wer_orig - wer_warped) / wer_orig if wer_orig > 0 else 0.0

        print(f"\nTranscript (original): {transcript_orig}")
        print(f"Transcript (VTLN warped): {transcript_warped}")
        print(f"WER original: {wer_orig:.3f}")
        print(f"WER warped:   {wer_warped:.3f}")
        print(f"Relative WER change: {rel_change*100:.1f}%")

        if rel_change >= 0.03:
            print("\n[RESULT] >=3% relative WER reduction -> AC-013 PASS, đủ điều kiện L0 integration")
        else:
            print("\n[RESULT] <3% relative WER reduction -> AC-013 chưa đạt, giữ vtln_warp_factor=1.0 (no-op)")
    else:
        print("\n(Không có --reference -> chỉ in warp_factor, chưa tính WER. "
              "Cần ground-truth transcript text để chạy AC-013 gate đầy đủ.)")


if __name__ == "__main__":
    main()
