# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260613c
## Thời gian: 2026-06-13
## Version: v0.11.27 → v0.11.28

---

## Trạng thái đầu → cuối
v0.11.27 | 1001 tests → v0.11.28 | 1001 tests

## 1. Actions Completed
- Files tạo/di chuyển: `data/eval/train001_eval_baseline.json`, `data/eval/train001_eval_results.json`
  (di chuyển từ `tests/train/kaggle/` sai vị trí — `tests/` chỉ dành cho pytest code)
- Files sửa: `docs/records/BACKLOG.md` (TRAIN-001 first run result + CT-062 mới),
  `docs/records/PROJECT_PROGRESS.md` (P1.TRAIN row, metrics v0.11.28, session history),
  `CHANGELOG.md` (entry v0.11.28), `CLAUDE.md` (CURRENT STATE)
- Model checkpoint: `models/asr_phowhisper/` (local, gitignored) — checkpoint-1151 từ Kaggle
  (model.safetensors + config.json + generation_config.json + preprocessor_config.json +
  processor_config.json + tokenizer.json + tokenizer_config.json)
- Tests chạy: 1001/1001 PASS (không đổi — không có thay đổi code/pipeline session này)
- Benchmark: TRAIN-001 first Kaggle GPU run — 1 epoch, `combined_manifest.jsonl`, eval n=30
  (`vietmed_manifest.jsonl` slice): WER baseline (vinai/PhoWhisper-medium) 0.2968 →
  fine-tuned (checkpoint-1151) 0.1517 (-49% relative)

## 2. Decisions
- Owner Decisions (Andy): không có quyết định kiến trúc mới — chỉ ghi nhận kết quả benchmark
- Technical Decisions (Claude): KHÔNG sửa `src/core/l1a_asr.py` MODEL_ID dù kết quả n=30 khả
  quan — theo FID-VN-007 §Side effects, swap production model cần FID riêng SAU KHI đạt GO
  trên full dataset (WER<0.20 + Drug CEER<0.10) + eval `ref_voice_manifest.jsonl` (57 clip BS
  thật, chưa test). `data/eval/train001_eval_*.json` đặt vào `data/eval/` (không phải `tests/`)
  theo convention các eval khác (`bench_002b_results.json` v.v.)

## 3. Architecture Changes
- (không có — pipeline L0→L10 không đổi)

## 4. Tasks Created
- CT-062: 🟡 Full eval cho `models/asr_phowhisper/` (checkpoint-1151) — (1) full
  `vietmed_manifest.jsonl` 9207 samples (không `--limit`), (2) `ref_voice_manifest.jsonl`
  (57 clip BS thật, cần upload lên Kaggle theo Pilot Exception #2), (3) Drug CEER. Nếu đạt
  GO → viết FID swap MODEL_ID. (Claude còn làm)

## 5. Pending Items
- [CT-062] full eval trước khi swap production model
- [BS pilot install] Máy BS (`C:\Users\Projects\MediVoice_VN`) đang cài Python 3.11 song
  song với 3.13 hiện có (torch==2.3.0 không có wheel cho Python 3.13) — chờ Andy xác nhận
  `py -3.11 -m venv venv` + `.\install.bat` chạy xong bước [3/6]

## 6. Risks / Confusions
- (không có — session chủ yếu docs sync + hỗ trợ cài đặt, không có thay đổi code rủi ro)

## Phiên tiếp theo — thứ tự ưu tiên
1. [BS pilot install] Xác nhận `install.bat` chạy xong trên máy BS (Python 3.11 venv) — nếu
   xong, hướng dẫn `start.bat` + ghi âm thật đầu tiên
2. [CT-062] Full eval model fine-tune (vietmed full + ref_voice + Drug CEER) — quyết định
   GO/NO-GO cho FID swap production ASR model
3. [CT-049] Andy re-test clip TMH lần 3
4. Các PA UI test khác (PA-015/PA-017/PA-018/PA-020/PA-021)
