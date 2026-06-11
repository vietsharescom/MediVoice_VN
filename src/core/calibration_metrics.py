# src/core/calibration_metrics.py
# FID-VN-014 — Voice Calibration Lab §2.2 (Standardized Reading Passage Test)
#
# Pure functions, KHÔNG động tới pipeline L0->L10 (FROZEN). Dùng để tính
# speaking_rate_class + pause_style từ audio mẫu BS đọc đoạn văn chuẩn.
# vtln_warp_factor đo qua vtln.estimate_warp_factor() (riêng, đã có).

from __future__ import annotations

import numpy as np

# FID-VN-018 §2 (CT-043) — đoạn văn chuẩn (~90 từ) cho Phần 2, theo vùng miền
# (double-check `profile.region` BS tự khai qua từ ngữ/phong cách giọng đọc).
# `central`/`southern` dùng marker từ `dialect_norm._CENTRAL_MARKERS` /
# `_SOUTHERN_MARKERS` để có thể double-check qua detect_region(transcript).
READING_PASSAGES_BY_REGION: dict[str, str] = {
    "northern": (
        "Hôm nay trời nắng đẹp, bệnh nhân đến phòng khám để kiểm tra sức khỏe định kỳ. "
        "Bác sĩ hỏi thăm về tiền sử bệnh tăng huyết áp và đái tháo đường của gia đình. "
        "Sau khi đo huyết áp và nhịp tim, bác sĩ ghi nhận chỉ số trong giới hạn bình thường. "
        "Bệnh nhân chia sẻ rằng gần đây hay bị đau đầu, mất ngủ và mệt mỏi vào buổi chiều. "
        "Bác sĩ khuyên nên giảm muối, tập thể dục đều đặn và tái khám sau hai tuần nữa."
    ),
    "central": (
        "Bữa ni trời nắng đẹp, bệnh nhân tới phòng khám để khám sức khỏe định kỳ. "
        "Bác sĩ hỏi mô răng rứa về tiền sử bệnh tăng huyết áp và đái tháo đường của gia đình. "
        "Sau khi đo huyết áp và nhịp tim, bác sĩ ghi nhận chỉ số ở mức bình thường. "
        "Bệnh nhân nói rứa tê, dạo ni hay bị đau đầu, mất ngủ và mệt mỏi vào buổi chiều. "
        "Bác sĩ khuyên mần giảm muối, tập thể dục đều đặn và tái khám sau hai tuần nớ."
    ),
    "southern": (
        "Bữa nay trời nắng đẹp, bệnh nhân tới phòng khám để khám sức khỏe định kỳ nha. "
        "Bác sĩ hỏi thăm về tiền sử bịnh tăng huyết áp và tiểu đường của gia đình. "
        "Sau khi đo huyết áp và nhịp tim, bác sĩ ghi nhận chỉ số ở mức bình thường nghen. "
        "Bệnh nhân nói hổng biết sao gần đây hay bị đau đầu, mất ngủ và mệt mỏi vào buổi chiều. "
        "Bác sĩ khuyên giảm muối, tập thể dục đều đặn và tái khám sau hai tuần nữa hen."
    ),
}

# Backward-compat alias — test cũ FID-VN-014 tham chiếu hằng số đơn này.
READING_PASSAGE_VI = READING_PASSAGES_BY_REGION["northern"]

# FID-VN-018 §2 — câu mẫu ngắn (~10-15s) cho Phần 1, theo vùng miền. `central`
# giữ nguyên câu hiện có (CT-038, đã hardcode trong index.html).
REGION_TEST_SENTENCES: dict[str, str] = {
    "northern": "Bác sĩ ơi, cháu bị đau đầu và mệt mỏi mấy hôm nay rồi ạ.",
    "central": "Bác sĩ ơi, mô răng rứa mà bệnh nhân ni đau hoài rứa hè?",
    "southern": "Bác sĩ ơi, con bị đau đầu hoài hổng biết sao nha.",
}


def get_passage_for_region(region: str | None) -> str:
    """FID-VN-018 §2 — đoạn văn Phần 2 theo vùng miền, fallback 'northern'."""
    return READING_PASSAGES_BY_REGION.get(region, READING_PASSAGES_BY_REGION["northern"])


def get_region_sentence(region: str | None) -> str:
    """FID-VN-018 §2 — câu mẫu Phần 1 theo vùng miền, fallback 'northern'."""
    return REGION_TEST_SENTENCES.get(region, REGION_TEST_SENTENCES["northern"])

SILENCE_RMS = 0.01
DEFAULT_FRAME_MS = 100
DEFAULT_PAUSE_THRESHOLD_MS = 1500


def detect_pauses_from_audio(
    y: np.ndarray,
    sr: int = 16000,
    frame_ms: int = DEFAULT_FRAME_MS,
    pause_threshold_ms: int = DEFAULT_PAUSE_THRESHOLD_MS,
) -> list[float]:
    """
    Phát hiện các đoạn ngắt (im lặng liên tục >= pause_threshold_ms) trong audio.
    Tương đương detectPauses() trong audio_quality.js nhưng nhận audio array
    thẳng thay vì rmsHistory đã tính sẵn.

    Returns: list các pause duration (giây).
    """
    if y is None or len(y) == 0:
        return []

    frame_len = max(1, int(sr * frame_ms / 1000))
    n_frames = int(np.ceil(len(y) / frame_len))
    min_frames = max(1, int(np.ceil(pause_threshold_ms / frame_ms)))

    pauses: list[float] = []
    silent_run = 0

    for i in range(n_frames):
        frame = y[i * frame_len: (i + 1) * frame_len]
        rms = float(np.sqrt(np.mean(frame.astype(np.float64) ** 2))) if len(frame) else 0.0
        if rms < SILENCE_RMS:
            silent_run += 1
        else:
            if silent_run >= min_frames:
                pauses.append(silent_run * frame_ms / 1000.0)
            silent_run = 0

    if silent_run >= min_frames:
        pauses.append(silent_run * frame_ms / 1000.0)

    return pauses


def classify_speaking_rate(word_count: int, duration_sec: float) -> str:
    """
    Phân loại tốc độ nói từ số từ / thời lượng audio (giây).
    Ngưỡng: <2.0 từ/giây = Chậm | 2.0-3.5 = Vừa | >3.5 = Nhanh.
    """
    if duration_sec <= 0 or word_count <= 0:
        return "Vừa"

    words_per_sec = word_count / duration_sec
    if words_per_sec < 2.0:
        return "Chậm"
    if words_per_sec > 3.5:
        return "Nhanh"
    return "Vừa"


def classify_pause_style(pauses: list[float]) -> str:
    """
    Phân loại kiểu ngắt nghỉ từ danh sách pause durations.
    0-1 lần ngắt = It_ngat | 2-4 = Vua_phai | >=5 = Nhieu_ngat.
    """
    n = len(pauses)
    if n <= 1:
        return "It_ngat"
    if n <= 4:
        return "Vua_phai"
    return "Nhieu_ngat"


def compute_jitter_shimmer(y: np.ndarray, sr: int = 16000) -> tuple[float, float]:
    """
    FID-VN-015 §2.4 — Jitter/shimmer như proxy cho creakiness/breathiness
    (Pham 2003: phonation type quan trọng hơn pitch-only cho thanh điệu VN).

    jitter_pct  = biến thiên trung bình chu kỳ pitch frame-to-frame (%)
    shimmer_pct = biến thiên trung bình biên độ (RMS) frame-to-frame (%)

    Hiển thị tham khảo (Lab step 2) — KHÔNG dùng để auto-adapt ASR.
    Trả về (0.0, 0.0) nếu audio rỗng hoặc không đủ dữ liệu voiced.
    """
    import librosa

    if y is None or len(y) == 0:
        return 0.0, 0.0

    y32 = y.astype(np.float32)

    f0, voiced_flag, _ = librosa.pyin(
        y32,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        sr=sr,
    )
    jitter_pct = 0.0
    if f0 is not None and f0.size > 0:
        voiced = voiced_flag.astype(bool) if voiced_flag is not None else ~np.isnan(f0)
        voiced_f0 = f0[voiced]
        voiced_f0 = voiced_f0[~np.isnan(voiced_f0)]
        if voiced_f0.size >= 2:
            periods = 1.0 / voiced_f0
            mean_period = float(np.mean(periods))
            if mean_period > 0:
                jitter_pct = float(np.mean(np.abs(np.diff(periods))) / mean_period * 100.0)

    shimmer_pct = 0.0
    rms = librosa.feature.rms(y=y32)[0]
    rms = rms[rms > 0]
    if rms.size >= 2:
        mean_rms = float(np.mean(rms))
        if mean_rms > 0:
            shimmer_pct = float(np.mean(np.abs(np.diff(rms))) / mean_rms * 100.0)

    return round(jitter_pct, 2), round(shimmer_pct, 2)
