# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260612
## Thời gian: 2026-06-12 (đóng phiên)
## Version: v0.11.16 → v0.11.17

---

## Trạng thái đầu → cuối
v0.11.16 | (chưa chạy được trên máy này — env thiếu) → v0.11.17 | 954/956 PASS + 2 skipped

## 1. Actions Completed
- Files sửa:
  - `tests/conftest.py` — gọi `init_db()` trực tiếp (FastAPI `startup` event không chạy khi
    `TestClient(app)` không dùng `with` → SQLite schema `doctor_profiles` v.v. không được tạo
    trên máy mới, gây 500 ở các test integration)
  - `tests/unit/test_build_asr_manifest.py` — thêm `@pytest.mark.skipif` cho
    `test_manifest_has_57_entries`/`test_audio_paths_exist` khi `data/audio/reference_voices/`
    (pilot audio, gitignored, NĐ13/2023 local-only) không tồn tại trên máy — tránh false 🔴
  - `docs/records/BACKLOG.md`, `CHANGELOG.md`, `CLAUDE.md` (CURRENT STATE → v0.11.17),
    `docs/records/PROJECT_PROGRESS.md`
- Files tạo (local, gitignored — không commit):
  - `data/audio/ground_truth_lam_sang_template.json` — tạo lại 7 entries (ha_noi/hai_phong/
    binh_dinh/nghe_an/hue/quang_nam/kien_giang) dựa trên pattern NER đã verify trong
    `tests/unit/test_l1c_vn_numbers.py`/`test_l1c_ner_bugs.py` + drug INNs có trong
    `data/reference/drug_db_v200.json`
- Chore (local venv, không commit):
  - `pip install silero-vad==6.2.1` (đã có trong requirements.txt, thiếu trong venv máy mới)
- Code generated: ~25 LOC (conftest fix + skipif markers)
- Tests chạy: 954/956 PASS + 2 skipped (skip = pilot-audio-absent, không phải lỗi code),
  bandit src/ 0 HIGH/9 MEDIUM/2 LOW (pre-existing, không đổi)
- Design/Benchmark cập nhật: không

## 2. Decisions
- Owner Decisions (Andy): không có trong phiên này
- Technical Decisions (Claude):
  - Đây là phiên dev-machine bootstrap (máy mới/sync khác) — KHÔNG phải feature work.
    Repo là live-synced drive, một máy khác (desktop) đã đẩy session SES-20260611e
    (v0.11.16, 956/956) trong lúc phiên này đang chạy — đã xác nhận qua `git fetch` +
    `git log` (HEAD=`de8b8ff`)
  - `test_manifest_has_57_entries`/`test_audio_paths_exist` (FID-VN-007) phụ thuộc
    `data/audio/reference_voices/` (pilot audio thật, gitignored theo NĐ13/2023) — KHÔNG
    fabricate audio để pass test; thay vào đó `skipif` khi absent, giữ assertion đầy đủ
    trên máy có pilot audio (CI/máy có data)

## 3. Architecture Changes
- Không thay đổi pipeline L0→L10 (env/test-infra only)

## 4. Tasks Created
- **CT-050** [DONE 2026-06-12] — Dev-machine bootstrap + test infra hardening
  (xem `docs/records/BACKLOG.md`)

## 5. Pending Items
- **CT-042** 🔴 BACKLOG IMMEDIATE — L1b phonological correction (p↔b/t↔d/k↔g) — cần FID
  trước khi sửa code (touches FROZEN L1b pipeline). iso_audit.py flag 🔴, chưa xử lý.
- **PA-024** — Andy tạo HF_TOKEN cho VietMed
- **CT-049** — Andy re-test clip TMH lần 3
- **PA-020/PA-021/PA-015/PA-017/PA-018** — Andy test UI (FID-VN-013..018)
- **CT-019** 🔴 — A2 VAD-chunk regression debug (cần audio mẫu)
- **TRAIN-001** — vẫn BLOCKED: chờ PA-024 + 50-100h pilot audio

## 6. Risks / Confusions
- Repo là live-synced working directory dùng chung giữa nhiều máy/session — HEAD có thể
  tự đổi giữa phiên (đã xảy ra 2 lần trong phiên trước, 7bbc49a→2066256→de8b8ff). Lưu ý
  khi `git status`/`git log` không khớp kỳ vọng: chạy `git fetch` trước khi kết luận.
- Không có chỗ confidence <70%

## Phiên tiếp theo — thứ tự ưu tiên
1. **CT-042** 🔴 — viết FID cho L1b phonological correction trước (BACKLOG IMMEDIATE,
   iso_audit.py đang flag 🔴)
2. **PA-024** — Andy tạo HF_TOKEN cho VietMed (5-10 phút)
3. **CT-049** — Andy re-test clip TMH lần 3
4. **TRAIN-001** — khi có PA-024 + pilot audio → chạy trên Colab/Kaggle theo
   `docs/dev/COLAB_KAGGLE_TRAINING.md`
5. **CT-019** debug A2-VAD (nếu có audio mẫu) · các PA UI test khác (PA-015/017/018/020/021)
