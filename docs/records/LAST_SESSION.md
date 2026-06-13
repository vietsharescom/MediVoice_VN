# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260612c
## Thời gian: 2026-06-12 (đóng phiên)
## Version: v0.11.18 → v0.11.19

---

## Trạng thái đầu → cuối
v0.11.18 | 958/958 PASS → v0.11.19 | 973/973 PASS

## 1. Actions Completed
- Files sửa:
  - `src/core/l1b_drug_correct.py` — thêm `_phonological_variants()` +
    `_phon_syllable_onset_variants()` + `_add_phon_alias()` + constants
    (`_ASPIRATION_MAP`, `_CODA_DROP_SET`, `_PHON_BLACKLIST`,
    `_PHON_MIN_VARIANT_LEN`), wired vào `_build_alias_map()`
  - `tests/unit/test_l1b_phonological.py` (mới) — 13 tests
  - `tests/unit/test_l1b_drug_correct_v2.py` — +2 tests e2e
    (`test_metronidazole_consonant_swap_garble`, `test_theophylline_th_garble`)
  - `fids/FID-VN-019.md` — Approved by Andy (CONS-20260612-001), tất cả
    acceptance criteria + tests checked off với kết quả thật
  - `fids/FID-VN-020.md` — Status: APPROVED (Andy "APPROVE FID 20 TIẾP TỤC", 2026-06-12)
  - `CHANGELOG.md` — entry v0.11.19 (FID-VN-019)
  - `docs/records/BACKLOG.md` — CT-042 → DONE (kết quả đầy đủ), thêm CT-053
    (Phonetic Encoder Phase 2) + entry CT-011/FID-VN-020 (approved, chưa implement)
  - `docs/records/PENDING_REQUESTS.md` — CT-011 → APPROVED, implementation để
    phiên sau
  - `CLAUDE.md` — CURRENT STATE → v0.11.19
  - `docs/records/PROJECT_PROGRESS.md` — SES-20260612c row, header v0.11.19
  - `data/eval/bench_002b_phon_results.json` (mới) — A/B benchmark output
- Code generated: ~140 LOC (`_phonological_variants` + helpers) + ~95 LOC tests
- Tests chạy: 973/973 PASS, bandit src/ 0 HIGH (9 MEDIUM/2 LOW pre-existing, không đổi)
- Design/Benchmark: A/B benchmark (`tools/bench_002b.py --save-json`, branch
  `experiment/fid-vn-019-phonological`) → Drug Recall 0.556, Drug Precision 0.714
  (cả hai KHÔNG ĐỔI so với baseline/master HEAD — verified)

## 2. Decisions
- Owner Decisions (Andy):
  - "ĐÃ XONG FID 19 CHUYỂN SANG 20 ĐƯỢC CHƯA" → confirm merge FID-19, hỏi tiếp FID-20
  - "APPROVE FID 20 TIẾP TỤC" — approve `fids/FID-VN-020.md` (Orchestrator
    automation), implementation để phiên sau
- Technical Decisions (Claude):
  - Merge `experiment/fid-vn-019-phonological` → `master` fast-forward (commit
    `13aff3a`) sau khi A/B benchmark PASS (Drug Recall/Precision không đổi)
  - Precision 0.714 (vs committed baseline `bench_002b_results.json` 0.833) là
    PRE-EXISTING trên master HEAD, KHÔNG do FID-VN-019 — verified bằng cách chạy
    master HEAD's `l1b_drug_correct.py` trên cùng eval data → cũng ra 0.714/FP=2.
    Ghi nhận CT-054 (regenerate baseline + debug Oresol NER FP), không block merge
  - `data/drug_vectorstore/chroma.sqlite3` tiếp tục để uncommitted (file lock
    Windows, leftover từ phiên trước + A/B run này) — CT-054

## 3. Architecture Changes
- Không thay đổi flow/pipeline L0→L10 — `_phonological_variants()` chỉ MỞ RỘNG
  alias_map (data layer của L1b), không đổi match logic/order (Layer 1 exact vẫn
  thắng trước Layer 2 fuzzy / Layer 3 RAG)

## 4. Tasks Created
- **CT-053** [NEW 2026-06-12] — Vietnamese Medical Phonetic Encoder (Phase 2,
  supersedes CT-052) — chờ pilot audio trước khi viết FID riêng
- **CT-054** [NEW 2026-06-12] — regenerate `data/eval/bench_002b_results.json`
  baseline (stale: 0.833/FP=1 vs master HEAD 0.714/FP=2) + debug Oresol NER FP
  trên `REF_HN_P1_Clip3.wav`
- **CT-011/FID-VN-020** [APPROVED 2026-06-12] — Orchestrator v1.0 automation
  (`detect_confusion`/`create_consultation_request`/`close_session`),
  implementation để phiên sau

## 5. Pending Items
- **FID-VN-020** (CT-011) — APPROVED, implementation chưa bắt đầu (~180-220 LOC +
  tests, risk LOW dev-tooling only)
- **CT-054** 🟡 — regenerate bench baseline + debug Oresol NER FP
- **CT-053** — Phonetic Encoder Phase 2, chờ pilot audio
- **CT-027** — Ciprofloxacin "si pô lo siêu âm si" alias — cần thêm audio mẫu khác
- **CT-049** — Andy re-test clip TMH lần 3
- **PA-020/PA-021/PA-015/PA-017/PA-018** — Andy test UI (FID-VN-013..018)
- **CT-019** 🔴 — A2 VAD-chunk regression debug (cần audio mẫu)
- **TRAIN-001** — full fine-tune (9207 samples VietMed, nhiều epoch) khi có
  GPU/quota tốt hơn (Kaggle 30h/tuần) hoặc pilot audio

## 6. Risks / Confusions
- Không có chỗ confidence <70%
- `data/drug_vectorstore/chroma.sqlite3` vẫn modified/uncommitted (CT-054) — không
  commit phiên này, cần investigate file lock trước khi resolve

## Phiên tiếp theo — thứ tự ưu tiên
1. **FID-VN-020** (CT-011) — implement Orchestrator automation (đã approve)
2. **TRAIN-001** — full fine-tune khi có Kaggle/GPU mạnh hơn hoặc pilot audio
   (theo `docs/dev/COLAB_KAGGLE_TRAINING.md`)
3. **CT-054** — regenerate bench baseline + debug Oresol NER FP
4. **CT-049** — Andy re-test clip TMH lần 3
5. **CT-019** debug A2-VAD (nếu có audio mẫu) · các PA UI test khác (PA-015/017/018/020/021)
6. **CT-027** — Ciprofloxacin alias khi có audio mẫu mới
