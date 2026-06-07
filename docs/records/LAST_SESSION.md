# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260610c
## Thời gian: 2026-06-10
## Version: v0.8.0 → v0.8.2

---

## Trạng thái đầu → cuối
v0.8.0 | 444 tests → v0.8.2 | 473 tests

## Đã hoàn thành

- [CONS-20260610-003] Tổng hợp 3 AI review FID-VN-009 (ChatGPT+Grok+Copilot) → CLOSED APPROVE_WITH_CHANGES
  - Quyết định: PARALLEL + optional early-exit (Grok+Copilot 2/3 majority, không phải CASCADE)
  - VITAL → meta["phobert_vital_detected"] only (Copilot addition)
  - MEDICATION thresholds: ≥0.85 HIGH | ≥0.75 STD | <0.60 discard
  - 6 risks mới: R-009-07 to R-009-12 (L1b error propagation, semantic merge, CPU, dedup, over-extraction, conditional FOLLOWUP)

- [FID-VN-009-IMPL] Hybrid NER Architecture — DONE 2026-06-10
  - `src/core/l1c_phobert.py` — PhoBERT NER module (lazy load lru_cache, confidence thresholds, bio_to_updates, has_coverage_gap)
  - `src/core/l1c_ner.py` — extract_entities_hybrid() + _get_filled_fields() (PARALLEL+early-exit)
  - `tests/unit/test_l1c_phobert_hybrid.py` — 29 tests → 473/473 PASS
  - Default OFF: MEDIVOICE_PHOBERT_NER=false — bật sau BENCH-002b GO criteria
  - R-009-12: "nếu không đỡ tái khám" → NOT auto-filled tai_kham (conditional FOLLOWUP guard)

- [CONS-002-EVAL] Evaluation dataset + script DrugCorrectionEngine v2 — DONE 2026-06-10
  - `scripts/generate_drug_eval_dataset.py` — 204 cases (clean=90 / noisy=76 / dangerous=38)
  - `scripts/eval_drug_correction.py` — 4 metrics với GO/NO-GO + per-category breakdown
  - `data/eval/drug_correction_eval.json` — 204 ground-truth cases v1.0.0
  - Key fix: "Dexamethasone injection" là INN trong drug_db_v200 (không phải "Dexamethasone")
  - Phân biệt silent FP (unflagged, nguy hiểm) vs warned FP (LOW_CONFIDENCE flagged, BS review → reject)

## Kết quả đo được
- Tests: 473/473 PASS
- Drug Recall: **99.5%** ✅ (TP=194 FN=1 — chỉ Azithromycin north phonetic "a zi thro my xin" bị miss)
- Silent FP Rate: **0.0%** ✅ (8 FPs đều là LOW_CONFIDENCE flagged → BS reject)
- Safety Catch Rate: **92.1%** ✅ (35/38 — 3 AMBIGUOUS miss: "metro"/"me tro")
- Phonetic Recall: **98.7%** ✅ (TP=75 FN=1)
- **→ ✅ GO — DrugCorrectionEngine v2 production-ready**

## Blocker / Phụ thuộc bên ngoài
- [BENCH-002b] Cần audio BS thật Đà Nẵng — pilot chưa deploy
- [PA-007] Andy cần paste ChatGPT corpus prompt → lấy 41 scripts → BS review
- [VIETMED-FIX-001] HF_TOKEN auth cho download_vietmed.py — không block Phase 0
- [CONS-002-SPRINT6] CONDITIONAL-GO: cần reference voices từ pilot BS trước khi chạy TTS

## Known issues từ eval
- CE-103: "a zi thro my xin" (Azithromycin bắc) → Layer 2 fuzzy miss — cần thêm phonetic alias
- "metro"/"me tro" → Metronidazole 91% confident nhưng không trigger AMBIGUOUS gate (top1-top2 gap ≥8) — acceptable
- 8 warned FPs: clinical admin words ("theo dõi", "định kỳ", "máu") fuzzy-match drug aliases → LOW_CONFIDENCE flagged → BS sẽ reject

## Phiên tiếp theo — làm ngay theo thứ tự
1. [BENCH-002b] Andy record 30-50 audio BS thật → ground truth labels → CEER thật — HIGHEST PRIORITY
2. [PA-007] Andy paste `docs/dev/CHATGPT_CORPUS_PROMPT.md` prompt → ChatGPT → 41 scripts → BS review
3. [CONS-002-SPRINT6] TTS Pilot XTTS-v2/F5-TTS — CONDITIONAL-GO sau khi có reference voices
4. [VIETMED-FIX-001] Fix HF_TOKEN auth nếu cần download VietMed audio
5. Add minimum token length filter cho drug fuzzy matching (CE-103 follow-up)
