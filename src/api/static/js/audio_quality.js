// src/api/static/js/audio_quality.js
// FID-VN-013 §2.1 — Recording quality score + behavioral hints (client-side, pure functions)
// AC-004: clipping / low signal / noise floor heuristics
// AC-005: behavioral hint mapping
// AC-008: KHÔNG gửi/lưu dữ liệu này — chỉ hiển thị tạm thời trong UI

(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.AudioQuality = factory();
  }
}(typeof self !== 'undefined' ? self : this, function () {

  const CLIP_THRESHOLD = 0.95;
  const CLIP_RATIO_THRESHOLD = 0.001;   // >0.1% samples clipped
  const LOW_SIGNAL_RMS = 0.02;
  const NOISE_FLOOR_RMS = 0.5;
  const SILENCE_RMS = 0.01;

  function computeRMS(samples) {
    if (!samples || samples.length === 0) return 0;
    let sum = 0;
    for (let i = 0; i < samples.length; i++) sum += samples[i] * samples[i];
    return Math.sqrt(sum / samples.length);
  }

  // Tính score/flags từ rms + clipRatio đã tổng hợp (dùng cho streaming — tránh
  // phải giữ toàn bộ buffer audio trong bộ nhớ, AC-008: không lưu audio).
  function qualityFromStats(rms, clipRatio) {
    const clipping = (clipRatio || 0) > CLIP_RATIO_THRESHOLD;
    const lowSignal = rms < LOW_SIGNAL_RMS;
    const noiseFloor = !lowSignal && rms > NOISE_FLOOR_RMS;

    let score = 100;
    if (clipping) score -= 40;
    if (lowSignal) score -= 40;
    if (noiseFloor) score -= 20;
    score = Math.max(0, Math.min(100, score));

    return { score, rms, clipping, lowSignal, noiseFloor };
  }

  // AC-004: tính quality score 0-100 từ 3 tiêu chí: clipping / low signal / noise floor
  function computeQualityScore(samples) {
    if (!samples || samples.length === 0) {
      return { score: 0, rms: 0, clipping: false, lowSignal: true, noiseFloor: false };
    }

    const rms = computeRMS(samples);

    let clipCount = 0;
    for (let i = 0; i < samples.length; i++) {
      if (Math.abs(samples[i]) >= CLIP_THRESHOLD) clipCount++;
    }
    return qualityFromStats(rms, clipCount / samples.length);
  }

  // AC-005: behavioral hint — ưu tiên clipping > low signal > noise floor
  function getBehavioralHint(quality) {
    if (!quality) return null;
    if (quality.clipping) {
      return 'Âm thanh quá to (clipping) — Bác sĩ thử nói nhỏ hơn hoặc để micro xa hơn một chút.';
    }
    if (quality.lowSignal) {
      return 'Micro quá xa hoặc giọng nói quá nhỏ — Bác sĩ thử nói to hơn hoặc đưa micro lại gần.';
    }
    if (quality.noiseFloor) {
      return 'Môi trường xung quanh có tiếng ồn — nếu có thể, Bác sĩ tìm nơi yên tĩnh hơn.';
    }
    return null;
  }

  // AC-003: pause > 1.5s detection trên chuỗi RMS theo frame (UI-only, không liên quan A2-VAD)
  function detectPauses(rmsHistory, frameDurationMs, pauseThresholdMs) {
    frameDurationMs = frameDurationMs || 100;
    pauseThresholdMs = pauseThresholdMs || 1500;
    const minFrames = Math.ceil(pauseThresholdMs / frameDurationMs);

    const pauses = [];
    let silentStart = null;
    const history = rmsHistory || [];

    for (let i = 0; i < history.length; i++) {
      if (history[i] < SILENCE_RMS) {
        if (silentStart === null) silentStart = i;
      } else {
        if (silentStart !== null) {
          if (i - silentStart >= minFrames) {
            pauses.push({ startFrame: silentStart, endFrame: i - 1 });
          }
          silentStart = null;
        }
      }
    }
    if (silentStart !== null && history.length - silentStart >= minFrames) {
      pauses.push({ startFrame: silentStart, endFrame: history.length - 1 });
    }
    return pauses;
  }

  return {
    computeRMS,
    computeQualityScore,
    qualityFromStats,
    getBehavioralHint,
    detectPauses,
    CLIP_THRESHOLD,
    LOW_SIGNAL_RMS,
    NOISE_FLOOR_RMS,
    SILENCE_RMS,
  };
}));
