# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260610b
## Thời gian: 2026-06-10 (buổi sáng — tiếp nối SES-20260610)
## Version: v0.7.2 → v0.7.2 (training + analysis + doc — không có code mới phiên này)

---

## Trạng thái đầu → cuối
v0.7.2 | training epoch 3 đang chạy 67% → v0.7.2 | 409/409 PASS · TRAIN-002 DONE

## Đã hoàn thành
- [TRAIN-002] PhoBERT NER training 3 epochs HOÀN TẤT:
  - Epoch 1: F1=98.95% · Epoch 2: F1=98.73% · Epoch 3: F1=**99.44%** (BEST)
  - Best model: `models/ner_phobert/best/` (512.8MB model.safetensors)
  - Entities: MEDICATION · DOSE · FREQUENCY · SYMPTOM · VITAL · FOLLOWUP
  - Note: trained trên synthetic data — cần validate trên pilot audio thực trước production
- [BUG-K2] "một sáu lăm"=165 abbreviated SG tens — fix xác nhận 409/409 PASS
- [BUG-N] chan_doan from "tái khám [disease]" — fix xác nhận 409/409 PASS
- [ANALYSIS] overnight_run.bat evaluation:
  - VietMed audio FAILED: `trust_remote_code` deprecated + doof-ferb/VietMed gated (cần HF login)
  - VietMed-NER drugs (313) = OB/GYN context, không phù hợp mở rộng drug_db phòng mạch đa khoa
  - drug_db.json 118 drugs cần mở rộng theo TT07/2017 + pilot prescription review
- [ANALYSIS] Canadian medical voice benchmark (Dragon Medical One / Abridge / Suki):
  - Accuracy cao nhờ speaker adaptation + medical LM + LLM post-processing
  - Ambient AI Scribe trend: nghe suốt buổi → auto-gen note → BS chỉ ký
  - MediVoice moat: tiếng Việt + offline + VN compliance + price point
- [DRUG-DB-002] Phân tích gap + thêm BACKLOG: ~30 thuốc thiếu (Augmentin, Bisoprolol, SGLT-2...)
- [VIETMED-FIX-001] Thêm BACKLOG: fix download script (HF_TOKEN + trust_remote_code)

## Kết quả đo được
- Tests: 409/409 PASS
- TRAIN-002 PhoBERT: F1=99.44% (epoch 3 best, synthetic data) — target >0.70 ✅
- best/ model: `models/ner_phobert/best/model.safetensors` 512.8MB ✅

## Blocker / Phụ thuộc bên ngoài
- [BENCH-002b] Pilot Đà Nẵng chưa bắt đầu — cần audio BS thật
- [VIETMED-FIX-001] doof-ferb/VietMed gated — Andy cần HuggingFace login + request access
- [PA-007] Andy copy `docs/dev/CHATGPT_CORPUS_PROMPT.md` → ChatGPT/Grok → 41 scripts → BS review

## Phiên tiếp theo — làm ngay theo thứ tự
1. [DRUG-DB-002] Mở rộng drug_db.json 118 → ~150 thuốc (Augmentin · Bisoprolol · Tramadol · SGLT-2 · Folic acid · Vitamin D3 · Smecta...) — L1b correction sẽ chuẩn hơn ngay
2. [FID-VN-NER-ML] Viết FID hybrid PhoBERT vào `src/core/l1c_ner.py` — Andy approve trước khi implement
3. [BENCH-002b] Pilot Đà Nẵng — Andy install + BS dùng thật + record audio
4. [VIETMED-FIX-001] Fix `scripts/download_vietmed.py` — HF_TOKEN auth
