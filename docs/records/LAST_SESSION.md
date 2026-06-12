# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260611e
## Thời gian: 2026-06-11 (đóng phiên)
## Version: v0.11.14 → v0.11.16

---

## Trạng thái đầu → cuối
v0.11.14 | 948/948 tests → v0.11.16 | 956/956 tests

## 1. Actions Completed
- Files tạo:
  - `docs/dev/COLAB_KAGGLE_TRAINING.md` — Colab/Kaggle GPU setup guide (clone → HF_TOKEN secret
    → download VietMed → build manifest → smoke-test → full run → cleanup PII)
- Files sửa:
  - `scripts/build_asr_manifest.py` — thêm `build_vietmed_manifest()` (đọc
    `data/vietmed/{split}/metadata.jsonl`, tolerant transcript field
    text/transcription/sentence/transcript, trả `[]` nếu chưa download) +
    `build_pilot_manifest(pilot_dir)` (quét `*.wav` + `.txt`/`.json` transcript liền kề,
    trả `[]` nếu rỗng) + CLI `--vietmed --pilot <dir> --combined`
  - `scripts/train_asr_phowhisper.py` — thêm `--fp16` (mixed-precision cho GPU Colab/Kaggle T4/P100)
  - `tests/unit/test_build_asr_manifest.py` — +8 tests mới (`TestBuildVietmedManifest`,
    `TestBuildPilotManifest`)
  - `fids/FID-VN-007.md` — v2: cập nhật theo hướng Colab/Kaggle, ACCEPTANCE CRITERIA mới,
    R-007-2 đổi thành rủi ro pilot-audio-PII-trên-Colab/Kaggle
  - `docs/records/DECISIONS.md` — thêm ADR 2026-06-11 **Pilot Phase Exception #2**
  - `docs/compliance/RISK_REGISTER.md` — R-P03 cập nhật thêm Exception #2
  - `docs/records/BACKLOG.md`, `docs/records/PENDING_REQUESTS.md` (PA-025 mới), `CHANGELOG.md`,
    `CLAUDE.md` (CURRENT STATE → v0.11.16), `docs/records/PROJECT_PROGRESS.md`
- Code generated: ~340 LOC (manifest builders + tests + docs + ADR)
- Tests chạy: 956/956 PASS (+8 từ 948), bandit src/ 0 HIGH/9 MEDIUM/2 LOW (pre-existing, không đổi)
- Design/Benchmark cập nhật: không

## 2. Decisions
- Owner Decisions (Andy):
  - "tôi đã có consent nên không lo. làm đi" (2026-06-11) — chấp thuận dùng Colab/Kaggle GPU
    (thay VNG/FPT cho giai đoạn pilot) cho TRAIN-001, bao gồm cả pilot audio thật có PII,
    với consent BS+BN+luật sư đã có sẵn (cùng phạm vi CT-024 2026-06-10)
- Technical Decisions (Claude):
  - Theo precedent CT-024 (PILOT PHASE EXCEPTION format trong DECISIONS.md), ghi ADR mới
    "Pilot Phase Exception #2" — TẠM THỜI, chỉ training run, xóa audio khỏi Colab/Kaggle
    ngay sau khi train xong, chỉ giữ checkpoint model (không chứa PII)
  - VietMed (MIT, public, không PII) không bị ảnh hưởng bởi exception này — luôn được phép

## 3. Architecture Changes
- Không thay đổi pipeline L0→L10 (tooling ngoài pipeline, FID-VN-007 v2)

## 4. Tasks Created
- (không có CT/TP mới — PA-025 đã DONE ngay trong phiên, ghi vào PENDING_REQUESTS để track)

## 5. Pending Items
- **PA-024** — Andy tạo HF_TOKEN cho VietMed (login huggingface.co + accept license
  `doof-ferb/VietMed` + Read token + `set HF_TOKEN=hf_xxx`)
- **TRAIN-001** — vẫn BLOCKED: chờ PA-024 + 50-100h pilot audio (chưa ghi âm,
  `data/audio/pilot/` trống). Khi đủ → chạy theo `docs/dev/COLAB_KAGGLE_TRAINING.md`
- **CT-049** — Andy re-test clip TMH lần 3
- **PA-020/PA-021/PA-015/PA-017/PA-018** — Andy test UI (FID-VN-013/014/015/016/017/018)
- **CT-019** 🔴 — A2 VAD-chunk regression debug (cần audio mẫu)

## 6. Risks / Confusions
- R-007-2 (FID-VN-007): pilot audio có PII upload Colab/Kaggle (ngoài VN, NĐ13/2023) —
  kiểm soát bằng Pilot Phase Exception #2 (`docs/records/DECISIONS.md` 2026-06-11),
  TẠM THỜI, phải xóa ngay sau training run, production phải chuyển VN Cloud trước launch
- Không có chỗ confidence <70%

## Phiên tiếp theo — thứ tự ưu tiên
1. **PA-024** — Andy tạo HF_TOKEN cho VietMed (5-10 phút)
2. **CT-049** — Andy re-test clip TMH lần 3
3. **TRAIN-001** — khi có PA-024 + pilot audio → chạy trên Colab/Kaggle theo
   `docs/dev/COLAB_KAGGLE_TRAINING.md`
4. **CT-019** debug A2-VAD (nếu có audio mẫu) · các PA UI test khác (PA-015/017/018/020/021)
