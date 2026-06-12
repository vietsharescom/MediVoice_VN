# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260612b
## Thời gian: 2026-06-12 (đóng phiên)
## Version: v0.11.17 → v0.11.18

---

## Trạng thái đầu → cuối
v0.11.17 | 956/956 PASS (954/956+2skip trên máy thiếu pilot audio) → v0.11.18 | 958/958 PASS

## 1. Actions Completed
- Files sửa:
  - `docs/dev/COLAB_KAGGLE_TRAINING.md` — bước 3 đổi "Set HF_TOKEN (PA-024)" →
    "(Optional) Set HF_TOKEN — chỉ tăng rate limit, `leduckhai/VietMed` KHÔNG gated"
  - `src/core/l1b_drug_correct.py` — `_match_window()` window (4,3,2,1) → (6,5,4,3,2,1)
  - `tests/unit/test_l1b_drug_correct_v2.py` — +2 tests
    (`test_phonetic_5word_azithromycin`, `test_phonetic_5word_ciprofloxacin`)
  - `CHANGELOG.md` — entry v0.11.18 (CT-051)
  - `docs/records/PENDING_REQUESTS.md` — CT-027 phần (5) DONE
  - `docs/records/BACKLOG.md` — CT-051 [DONE]
  - `CLAUDE.md` — CURRENT STATE → v0.11.18
  - `docs/records/PROJECT_PROGRESS.md` — metrics 958/958, PHIÊN TIẾP THEO, lịch sử phiên
- Colab session (Andy): chạy `download_vietmed.py --split cv` (85 samples) +
  `train_asr_phowhisper.py --batch 2 --epochs 1` → smoke run thành công (loss 2.613,
  train_runtime 84.5s, `956 passed` local test suite trên Colab). KHÔNG download
  checkpoint (3GB, ~2h) — chỉ là proof-of-pipeline trên 85 samples/1 epoch, gần như =
  base model, không có giá trị fine-tune thật.
- Code generated: ~10 LOC (window fix + comment) + ~15 LOC tests
- Tests chạy: 958/958 PASS, bandit src/ 0 HIGH (9 MEDIUM/2 LOW pre-existing, không đổi)
- Design/Benchmark cập nhật: không

## 2. Decisions
- Owner Decisions (Andy):
  - "cả hai" — tiếp tục Colab training VÀ làm rõ phonetic dictionary (CT-027), cả 2
    song song trong phiên
  - Hủy download checkpoint Colab (3GB/~2h) — đồng ý đây chỉ là proof-of-pipeline,
    để full fine-tune cho phiên sau (Kaggle/GPU mạnh hơn hoặc pilot audio)
- Technical Decisions (Claude):
  - Phát hiện `_match_window` chỉ thử window 1-4 từ trong khi `drug_db_v200.json`
    có 187 `phonetic_variants` 5-6 từ → fix mở rộng window lên 6, exact-match nên
    không tăng false-positive risk — fix ngay (Tầng 3, <20 LOC, không cần FID vì
    không đổi flow/logic L1b, chỉ mở rộng phạm vi exact-match đã có)
  - KHÔNG thêm alias Ciprofloxacin "si pô lo siêu âm si" (CT-016) — giữ nguyên
    quyết định CT-027 cũ (cần data thêm, tránh FP "siêu âm")

## 3. Architecture Changes
- Không thay đổi flow/pipeline L0→L10 — chỉ mở rộng phạm vi window exact-match
  trong L1b (Layer 1), không phải logic mới

## 4. Tasks Created
- **CT-051** [DONE 2026-06-12] — L1b drug match window 1-4 → 1-6 từ (xem
  `docs/records/BACKLOG.md`)

## 5. Pending Items
- **CT-042** 🔴 BACKLOG IMMEDIATE — L1b phonological correction (p↔b/t↔d/k↔g) — cần
  FID trước khi sửa code (touches FROZEN L1b pipeline). iso_audit.py flag 🔴.
- **CT-027** — Ciprofloxacin "si pô lo siêu âm si" alias — cần thêm audio mẫu khác
- **CT-049** — Andy re-test clip TMH lần 3
- **PA-020/PA-021/PA-015/PA-017/PA-018** — Andy test UI (FID-VN-013..018)
- **CT-019** 🔴 — A2 VAD-chunk regression debug (cần audio mẫu)
- **TRAIN-001** — full fine-tune (9207 samples VietMed, nhiều epoch) khi có GPU/quota
  tốt hơn (Kaggle 30h/tuần) hoặc pilot audio

## 6. Risks / Confusions
- Không có chỗ confidence <70%
- Lưu ý: repo live-synced giữa nhiều máy — `git fetch` trước khi kết luận trạng thái

## Phiên tiếp theo — thứ tự ưu tiên
1. **CT-042** 🔴 — viết FID cho L1b phonological correction trước (BACKLOG IMMEDIATE,
   iso_audit.py đang flag 🔴)
2. **CT-049** — Andy re-test clip TMH lần 3
3. **TRAIN-001** — full fine-tune khi có Kaggle/GPU mạnh hơn hoặc pilot audio
   (theo `docs/dev/COLAB_KAGGLE_TRAINING.md`)
4. **CT-019** debug A2-VAD (nếu có audio mẫu) · các PA UI test khác (PA-015/017/018/020/021)
5. **CT-027** — Ciprofloxacin alias khi có audio mẫu mới
