# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260611
## Thời gian: 2026-06-11
## Version: v0.8.2 → v0.8.3

---

## Trạng thái đầu → cuối
v0.8.2 | 473 tests → v0.8.3 | 473 tests

## Đã hoàn thành

- [CE-103] 3 safety bug fixes DrugCorrectionEngine v2 — `src/core/l1b_drug_correct.py`
  - Fix 1: 2-syllable phonetic alias filter (ga ba → Gabapentin FP eliminated)
  - Fix 2: STRICT threshold 82→88 (soát→Iron silent FP eliminated)
  - Fix 3: Greedy window guard (ghi kê Paracetamol → Layer 1 exact match restored)
  - Trade-off: Drug Recall 99.5%→96.9%, Silent FP 0.0% maintained, Safety Catch 100%
  - 473/473 PASS (2 tests updated for 3-syllable phonetic variants)

- [BENCH-002a-v2] Re-run BENCH-002a với DrugCorrectionEngine v2 — `tools/bench_ceer_semi.py`
  - 15 files: HN/SG/CT × 5 SC × take1 (40 files tồn tại, CA dropped)
  - CEER Overall: Drug=0.989🔴 | Diag=0.667🔴 | Vital=0.272⚠️ | Fup=0.400🔴
  - By region: CT best (Drug=0.9 Vital=0.15) | SG worst (Drug=1.167 FP hallucination)
  - By scenario: SC-04 ĐTĐ worst (Drug=1.222) | SC-01 Viêm họng best (Drug=0.833)
  - Root cause xác nhận: ASR bottleneck — PhoWhisper mangling drug names trên real speech
  - Gap: CONS-002-EVAL clean text Recall=99.5% vs BENCH-002a speech CEER=0.989

## Kết quả đo được
- Tests: 473/473 PASS
- CE-103 Drug eval (clean text): Recall=96.9% Silent FP=0.0% Safety=100% ✅ GO
- BENCH-002a Drug CEER (ASR speech): 0.989 🔴 — ASR là bottleneck, không phải NER
- CT (Cần Thơ) tốt nhất: Drug=0.9 Vital=0.15 (nói chậm → transcript sạch hơn)
- SG (Sài Gòn) tệ nhất: Drug=1.167 (nhanh → ASR garble → FP drugs)

## Blocker / Phụ thuộc bên ngoài
- [BENCH-002b] Audio BS thật Đà Nẵng — pilot chưa deploy (HIGHEST PRIORITY)
- [PA-007] Andy paste ChatGPT corpus prompt → 41 scripts → BS review
- [VIETMED-FIX-001] HF_TOKEN auth cho download_vietmed.py — không block Phase 0
- [CONS-002-SPRINT6] CONDITIONAL-GO: cần reference voices từ pilot BS

## Phiên tiếp theo — làm ngay theo thứ tự
1. [BENCH-002b] Andy record 30-50 audio BS thật → ground truth labels → CEER thật
2. [PA-007] Andy paste `docs/dev/CHATGPT_CORPUS_PROMPT.md` → ChatGPT → 41 scripts
3. [DRUG-DB-002] Mở rộng drug_db.json → ~150 thuốc (Augmentin, Bisoprolol, Celecoxib...)
4. [CE-103-FU] Thêm Azithromycin phonetic alias "a zi thro my xin" vào drug_db_v200
5. [CONS-002-SPRINT6] TTS Pilot sau khi có reference voices
