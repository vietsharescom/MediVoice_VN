# FID-VN-007 — PhoWhisper Fine-tune Pipeline (TRAIN-001 prep)
# Feature Intent Document | ISO_VN v1.0
# Status: APPROVED (implicit — TRAIN-001 ưu tiên #1 per CT-028, Andy)

| Field | Value |
|---|---|
| FID ID | FID-VN-007 |
| Layer | Tooling (ngoài L0→L10 frozen pipeline) |
| LOC estimate | ~200 LOC |
| Risk level | LOW |
| Created | 2026-06-11 |
| Approved by | Andy Phan (implicit — TRAIN-001 = next task, CT-028) |
| Approved date | 2026-06-11 |

---

## WHY (Tại sao cần feature này?)

BENCH-002b (57 clip giọng BS thật): WER=18.4% (tốt) nhưng **Drug Recall chỉ 55.6% lower-bound**
và Diag CEER 71.4% — PhoWhisper-medium gốc không nhận đúng tên thuốc khi BS đọc phiên âm/spell-out
("MÉt PHỐT min" → Metformin). CT-028 (2026-06-10): Andy quyết định 100% local pipeline, KHÔNG hybrid
Groq, **TRAIN-001 (fine-tune PhoWhisper) là ưu tiên #1**. FID-VN-007 chuẩn bị pipeline fine-tune
(manifest builder + training script) TRƯỚC KHI có đủ 50-100h audio pilot + GPU/cloud, để khi data
sẵn sàng có thể chạy ngay.

## WHAT (Feature làm gì? Input/Output?)

**Input (hiện có, dùng cho smoke-test):**
- `data/eval/ref_voice_transcripts.json` — 57 clip giọng BS thật (HN/DN/SG), `transcript_gt`
  đã có sẵn, tổng ~17 phút audio tại `data/audio/reference_voices/{BS_hanoi,BS_danang,BS_saigon}/`

**Input (tương lai):**
- VietMed (16h, MIT, KHÔNG PII) — `scripts/download_vietmed.py` đã sửa xong (VIETMED-FIX-001, commit
  `3fd6990`) nhưng dataset **gated trên HuggingFace** → cần Andy: đăng nhập huggingface.co, accept
  license tại `huggingface.co/datasets/doof-ferb/VietMed`, tạo Read token, `set HF_TOKEN=hf_xxx` (PA-024)
- Pilot audio 50-100h từ phòng khám Đà Nẵng/Sài Gòn — chưa ghi âm (Pilot chưa launch). Khi có,
  upload lên Colab/Kaggle để train CẦN tuân `docs/records/DECISIONS.md` 2026-06-11 (Pilot Phase
  Exception #2 — consent đã có, xóa audio ngay sau training run).
- GPU: **Colab/Kaggle free-tier GPU** (T4/P100, Andy đã có account) — quyết định 2026-06-11,
  thay cho VNG/FPT cloud VM ở giai đoạn pilot. Xem `docs/dev/COLAB_KAGGLE_TRAINING.md`.

**Output (FID này, mở rộng 2026-06-11):**
- `scripts/build_asr_manifest.py`:
  - `build_manifest()` — đọc `ref_voice_transcripts.json` + resolve đường dẫn audio theo `bs` code
    (HN→BS_hanoi, DN→BS_danang, SG→BS_saigon) → `data/asr_manifest/ref_voice_manifest.jsonl`
    (57 dòng `{"audio": <path>, "text": <transcript_gt>}`)
  - `build_vietmed_manifest()` — đọc `data/vietmed/{split}/metadata.jsonl` + `audio/` →
    `data/asr_manifest/vietmed_{split}_manifest.jsonl` (trả `[]` nếu chưa download)
  - `build_pilot_manifest(pilot_dir)` — quét `*.wav` + transcript `.txt`/`.json` liền kề →
    `data/asr_manifest/pilot_manifest.jsonl` (trả `[]` nếu dir trống)
  - CLI flags `--vietmed --pilot <dir> --combined` → `combined_manifest.jsonl`
- `scripts/train_asr_phowhisper.py` — fine-tune `vinai/PhoWhisper-medium` qua
  `Seq2SeqTrainer` + `WhisperProcessor`. Flag `--smoke-test`: chạy 1 training step trên 2 sample
  đầu (CPU OK) để xác nhận data collator + forward/backward hoạt động đúng — KHÔNG dùng để
  fine-tune thật (17 phút data quá nhỏ, sẽ overfit). Flag mới `--fp16`: mixed-precision cho GPU
  (Colab/Kaggle T4/P100).
- `docs/dev/COLAB_KAGGLE_TRAINING.md` — hướng dẫn setup từng bước (clone, HF_TOKEN secret,
  download VietMed, build manifest, smoke-test, full run, cleanup PII)
- `models/asr_phowhisper/` — output dir, đã có trong `.gitignore` (`/models/`)

**Side effects:** KHÔNG đụng pipeline L1a (`src/core/l1a_asr.py`) — model fine-tune chỉ swap vào
production qua FID riêng SAU KHI đạt GO criteria (WER <20%, Drug CEER <0.10) trên full dataset.

## ACCEPTANCE CRITERIA (Khi nào gọi là DONE?)

- [x] `build_manifest()` đọc 57 clip từ `ref_voice_transcripts.json`, resolve đúng đường dẫn audio
- [x] `scripts/train_asr_phowhisper.py --smoke-test` chạy 1 step trên CPU không lỗi
- [x] `build_vietmed_manifest()` + `build_pilot_manifest()` — trả `[]` an toàn khi data chưa có,
  parse đúng khi có (transcript field tolerant: text/transcription/sentence/transcript)
- [x] `--fp16` flag cho `train_asr_phowhisper.py` (GPU Colab/Kaggle)
- [x] `docs/dev/COLAB_KAGGLE_TRAINING.md` — setup guide + compliance note (Pilot Exception #2)
- [x] Unit test `tests/unit/test_build_asr_manifest.py` — 100% PASS
- [x] CHANGELOG entry
- [x] Pipeline L0→L10 không đổi
- [ ] **OUT OF SCOPE (CT mới)**: full fine-tune run thật — chờ (1) HF_TOKEN cho VietMed (PA-024),
  (2) 50-100h pilot audio. Khi đủ → chạy `train_asr_phowhisper.py --fp16` trên Colab/Kaggle,
  GO/NO-GO theo WER<20%/Drug CEER<0.10.

## RISKS

| Risk ID | Mô tả | Kiểm soát |
|---|---|---|
| R-007-1 | Fine-tune trên 17 phút data sẽ overfit/làm hỏng model | `--smoke-test` CHỈ validate pipeline (1 step, không save checkpoint dùng production); full run chờ ≥50h |
| R-007-2 | Pilot audio có PII upload Colab/Kaggle (ngoài VN) | Pilot Phase Exception #2 (`docs/records/DECISIONS.md` 2026-06-11) — consent đã có, xóa audio ngay sau run, chỉ giữ checkpoint |
| R-007-3 | Checkpoint PhoWhisper fine-tune (~3GB) không được commit | `/models/` đã trong `.gitignore` |
| R-007-4 | VietMed dataset gated (401) | Cần Andy tạo HF_TOKEN — PA-024 |

## TESTS REQUIRED

- [x] Unit test: `tests/unit/test_build_asr_manifest.py`
- [ ] Integration test: không cần (tooling ngoài pipeline)
- [x] Pipeline integrity test vẫn PASS (948/948 không đổi)

## COMMIT FORMAT

```
feat(train): TRAIN-001 prep — PhoWhisper fine-tune pipeline scaffold [FID-VN-007]
```

---

*FID-VN-007 | ISO_VN v1.0 | MediVoice VN | 2026-06-11*
