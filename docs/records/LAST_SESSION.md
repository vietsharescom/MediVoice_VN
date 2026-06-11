# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260610c
## Thời gian: 2026-06-10 (đêm)
## Version: v0.11.4 → v0.11.5

---

## Trạng thái đầu → cuối
v0.11.4 | 826 tests → v0.11.5 | 852 tests

## 1. Actions Completed
- Files tạo:
  - `fids/FID-VN-013.md` (FID v2 — Voice Calibration UX + Drug Pronunciation Wizard + VTLN)
  - `src/api/static/js/audio_quality.js` (UMD: computeRMS/qualityFromStats/computeQualityScore/getBehavioralHint/detectPauses)
  - `src/core/vtln.py` (estimate_warp_factor + apply_vtln_warp — research, KHÔNG wire L0)
  - `scripts/vtln_poc.py` (CLI POC — AC-013 WER gate ≥3% relative)
  - `tests/unit/test_audio_quality.py` (11 tests), `tests/unit/test_dvp_wizard.py` (9 tests), `tests/unit/test_vtln.py` (6 tests)
  - `docs/records/consultations/CONS-20260610-005.md` (8-AI consensus, 85% — FID-VN-013 v2 scope)
- Files sửa:
  - `src/core/l7_storage.py` — thêm `add_confirmed_alias()` (active enrollment, bypass passive ≥3×≥2 promote rule)
  - `src/api/main.py` — 3 endpoints mới: `GET/POST /api/doctors/{cchn}/pronunciation-wordlist|enroll|confirm`
  - `src/api/static/index.html` — §2.1-2.3 visualization (audio-viz waveform/mic-level/behavioral-hint, region-badge, calib-tooltip), §2.4 Drug Pronunciation Wizard modal + nút "🎓 Luyện đọc thuốc" trong DVP greeting
  - `docs/records/BACKLOG.md` (v0.9.1→v0.9.2) — section FID-VN-013 v2 DONE
  - `docs/records/PENDING_REQUESTS.md` — PA-015 (Andy test UI), CT-037 (VTLN POC run, đổi từ CT-035 do trùng ID với entry có sẵn)
  - `docs/records/PROJECT_PROGRESS.md` (v1.9→v1.10) — P0.6.15 FID-VN-013 v2, metrics 852/852, LỊCH SỬ PHIÊN
  - `CHANGELOG.md` — entry `[v0.11.5]`
  - `CLAUDE.md` — CURRENT STATE → v0.11.5
- Code generated: ~3 endpoints + 1 storage fn + 1 research module + 1 CLI + 1 JS module + ~13 UI edits (index.html) ≈ 700 LOC + 26 tests
- Tests chạy: 852/852 PASS (toàn bộ suite, 26.98s)
- Design/Benchmark cập nhật: `fids/FID-VN-013.md` đánh dấu IMPLEMENTED v2

## 2. Decisions
- Owner Decisions (Andy): "vậy triển khai" — implement full 3-layer scope (Option c): §2.1-2.3 Visualization + §2.4 Drug Pronunciation Wizard + §2.5 VTLN research (LoRA per-speaker vẫn deferred Phase 1, theo PA-014)
- Technical Decisions (Claude):
  - §2.4.1 (`global_aliases`/`doctor_overrides`) — KHÔNG implement, đúng kế hoạch Phase 1.5 (per ChatGPT proposal trong CONS-20260610-005)
  - §2.5 VTLN — chỉ build research module + POC CLI, KHÔNG wire vào L0/transcribe cho đến khi AC-013 (≥3% relative WER reduction) được chứng minh — tránh vi phạm "Pipeline L0→L10 FROZEN"
  - JS testing: dùng Node subprocess từ pytest (UMD module) thay vì thêm jest/package.json — không có JS test runner sẵn trong repo
  - Sửa duplicate ID: entry VTLN POC ban đầu đặt CT-035 nhưng trùng với CT-035 có sẵn (PDF screenshot/server cũ) từ commit `860f284` → đổi thành CT-037

## 3. Architecture Changes
- KHÔNG có thay đổi pipeline L0→L10 (FROZEN giữ nguyên). Tất cả thay đổi additive:
  - L7 storage: thêm `add_confirmed_alias()` (dùng schema `doctor_aliases` có sẵn từ FID-VN-012)
  - API: 3 endpoint mới (không sửa endpoint cũ)
  - Frontend: thêm UI components (waveform canvas, wizard modal, badges) — client-side only, không gọi API mới cho visualization (AC-008)
  - `src/core/vtln.py` — module độc lập, KHÔNG import từ pipeline modules, KHÔNG có call site nào trong `src/core/l0_normalize.py` hay `main.py`

## 4. Tasks Created
- PA-015: Andy test UI FID-VN-013 v2 (waveform/mic-level/calib-tooltip/region-badge + Drug Pronunciation Wizard) trên trình duyệt thật tại `http://localhost:8000`, confirm OK — 🟡 MEDIUM
- CT-037: Chạy `scripts/vtln_poc.py` (AC-013 WER gate) — cần audio pilot thật + ground-truth transcript text đầy đủ (corpus hiện tại chỉ có structured fields). KHÔNG block TRAIN-001 — 🟢 LOW

## 5. Pending Items
- [PA-015] Andy chưa test UI thật (server local đang chạy tại `http://localhost:8000`, đã verify FileResponse trả đúng HTML/JS mới — vấn đề trước đó là browser cache, đã hướng dẫn hard-refresh)
- [CT-037] VTLN POC chưa chạy — cần audio + ground truth transcript
- Carry-over từ phiên trước (chưa đổi): CT-019 (🔴 A2 VAD-chunk regression), CT-016/CT-017/CT-014, CT-035/CT-036 (PDF screenshot server cũ / storage path — đã trả lời, chờ Andy re-test), VIETMED-FIX-001, TRAIN-001 (ưu tiên #1 theo CT-028)

## 6. Risks / Confusions
- Duplicate task ID CT-035 phát hiện giữa session này (VTLN POC, mới thêm) và session trước (PDF screenshot/storage path, đã commit `860f284`) — đã sửa thành CT-037, nhưng cảnh báo: PENDING_REQUESTS.md cần kiểm tra ID trùng trước khi thêm entry mới (ID cao nhất hiện tại = CT-037)
- §2.5 VTLN: risk THẤP theo 6/6 AI consensus (warp_factor là scalar, không phải biometric fingerprint) nhưng CHƯA có bằng chứng thực nghiệm (AC-013 POC chưa chạy) — giữ nguyên `vtln_warp_factor=1.0` no-op cho đến khi có data

## Phiên tiếp theo — thứ tự ưu tiên
1. [PA-015] Andy test UI FID-VN-013 v2 trên trình duyệt thật (server đã sẵn sàng `http://localhost:8000`) — đăng ký DVP trước để thấy nút "🎓 Luyện đọc thuốc"
2. [TRAIN-001] Fine-tune PhoWhisper trên 50-100h audio thật (ưu tiên #1 per CT-028) — chờ audio pilot
3. [CT-019] Debug A2 VAD-chunk regression offline nếu có audio lỗi từ Andy
