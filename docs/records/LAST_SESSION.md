# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260610c
## Thời gian: 2026-06-10 (buổi chiều — tiếp nối SES-20260610b)
## Version: v0.7.2 → v0.7.2 (consultation synthesis + BACKLOG update — không có code mới)

---

## Trạng thái đầu → cuối
v0.7.2 | 409/409 PASS · CONS-20260610-002 PENDING → v0.7.2 | 409/409 PASS · CONS-002 CLOSED

## Đã hoàn thành
- [CONS-20260610-002] Multi-AI consultation synthesis HOÀN TẤT:
  - 3 AI responses: ChatGPT (NO-GO core / CONDITIONAL-GO augment) · Grok (CONDITIONAL-GO + F5-TTS) · Copilot (CONDITIONAL-GO + text normalization)
  - Decision: CONDITIONAL-GO — phonetic_variants → TTS input, NOT INN gốc
  - File: `docs/records/consultations/CONS-20260610-002.md` — CLOSED
  - F5-TTS-Vietnamese (nguyenthienhy, hynt/ViVoice 1000h) = alternative candidate
  - Pilot gate: 20 clips → BS evaluate → quyết GO full 20K
- [CONS-20260610-001] Footer corrected — CLOSED status confirmed
- [BACKLOG] Thêm Sprint tasks:
  - CONS-002-IMPL: drug_db_v200 + phonetic_variants (Sprint 1)
  - CONS-002-SPRINT2: DrugCorrectionEngine v2 + Safety Rules (Sprint 2)
  - CONS-002-EVAL: Evaluation dataset 200-500 câu (Sprint 4)
  - CONS-002-SPRINT6: TTS pilot XTTS/F5-TTS (Sprint 6, CONDITIONAL-GO)

## Kết quả đo được
- Tests: 409/409 PASS (không thay đổi — không có code mới)
- CONS-001: CLOSED · CONS-002: CLOSED
- BACKLOG: 4 Sprint tasks thêm mới

## Blocker / Phụ thuộc bên ngoài
- [BENCH-002b] Pilot Đà Nẵng chưa bắt đầu — cần audio BS thật + reference voices
- [PA-007] Andy copy `docs/dev/CHATGPT_CORPUS_PROMPT.md` → ChatGPT/Grok → 41 scripts → BS review
- [CONS-002-SPRINT6] Cần reference voices BS thật (HN/HCM/DN/CT ~6-10s) trước TTS pilot

## Phiên tiếp theo — làm ngay theo thứ tự
1. [CONS-002-IMPL] Mở rộng `data/reference/drug_db.json` → `drug_db_v200.json` — 200 drugs + `phonetic_variants:{north,central,south}` theo 7 consensus rules từ CONS-001
2. [DRUG-DB-002] Bổ sung ~30 thuốc thiếu: Augmentin · Bisoprolol · Tramadol · SGLT-2 · Folic acid · Vitamin D3 · Smecta (có thể gộp vào CONS-002-IMPL)
3. [FID-VN-NER-ML] Viết FID hybrid PhoBERT vào `src/core/l1c_ner.py` — Andy approve trước khi implement
4. [BENCH-002b] Pilot Đà Nẵng — Andy install + BS dùng thật + record audio + thu reference voices
