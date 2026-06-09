# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260609c
## Thời gian: 2026-06-09 (tiếp nối SES-20260609b)
## Version: v0.8.6 → v0.9.0

---

## Trạng thái đầu → cuối
v0.8.6 | 678 tests → v0.9.0 | 755/755 tests PASS

## Đã hoàn thành
- [RAG-001-DRUG-VECTOR] `src/core/drug_rag.py` — ChromaDB + paraphrase-multilingual-MiniLM-L12-v2
  - build_drug_vectorstore() + load_drug_vectorstore() + query_drug_rag() + query_drug_rag_from_file()
  - Document: INN + phonetic_variants (3 regions) + brands + keywords + drug_class + diagnoses
  - `tests/unit/test_drug_rag.py` — 80 tests PASS
- [RAG-001-FIX] Hybrid fuzzy 65% + RAG 35% — fix RC-A (MiniLM not phonetic) + RC-C (missing variants)
  - _build_phonetic_index() + _fuzzy_phonetic_search() + hybrid_query_drug() + hybrid_query_drug_from_file()
  - "mek foc binh"→Metformin✅ "ong lau di pin"→Amlodipine✅ (vs RAG-only: ❌)
  - /api/drug-candidates endpoint cập nhật dùng hybrid_query_drug() → source="hybrid"
  - +31 tests: TestBuildPhoneticIndex(9) + TestFuzzyPhoneticSearch(11) + TestHybridQueryDrug(13)
- [UI-SUGGEST-001] `src/api/static/js/suggestions.js` — Suggestions IIFE module
  - onTranscriptReady() parallel drug candidates + dialect check
  - onSpecialtyChange() reload term sidebar với cache
  - Renders: drug chips, dialect badge, term sidebar
  - `tests/unit/test_api_suggestions.py` — 43 tests PASS
- [UI-SUGGEST-001 API] `src/api/main.py` — 3 endpoints
  - GET /api/drug-candidates (hybrid fallback fuzzy), GET /api/terms (8 chuyên khoa), POST /api/dialect-check
  - _SPECIALTY_TERMS: 8 specialties × 10-20 terms ICD coded
- [UI-SUGGEST-001 HTML] `src/api/static/index.html` — drug chips + dialect badge + term sidebar
  - specialty selector + suggest-drug-panel + suggest-dialect-badge + suggest-term-sidebar
- [L4-REDESIGN-001 PWA] `src/api/static/index.html` — per-drug confirm UI (Luật KCB 2023 Đ.62)
  - .drug-confirm-row (unconfirmed=amber, confirmed=green) + .drug-confirm-progress
  - renderDrugConfirmList() + onDrugConfirmChange() + updateApproveButton()
  - #btn-approve disabled cho đến khi tất cả thuốc được xác nhận
  - L4 safety guard trong approveRecord(): block nếu chưa confirm đủ

## Kết quả đo được
- Tests: 678/678 → 755/755 PASS (+77 tests trong phiên)
- RAG-001: ChromaDB vectorstore build/query với paraphrase-multilingual-MiniLM-L12-v2
- RAG-001-FIX: hybrid score = 0.65×fuzzy + 0.35×rag → fix phonetic recall
- UI-SUGGEST-001: 3 endpoints + JS module + HTML integration hoàn chỉnh
- L4-PWA: per-drug checkbox PWA, BS không thể bypass mà không tick từng thuốc
- bandit: 0 HIGH / 0 MEDIUM từ code mới (9 medium pre-existing HuggingFace download)

## Blocker / Phụ thuộc bên ngoài
- [PA-009] Andy chưa fill 54/57 GT clips → BENCH-002b CEER thật chưa đo được
- [PA-010] FID-VN-010 approve retroactive (Phase 0 đã implement xong)
- [PA-011] Andy chưa chốt Q1+Q3 → FID-VN-009 PhoBERT deferred
- [VIETMED-FIX-001] HF_TOKEN cần để download VietMed audio

## Phiên tiếp theo — làm ngay theo thứ tự
1. [BENCH-GT-001] Andy fill GT clips `data/eval/ref_voice_transcripts_review.txt` (Clip2+Clip3 ưu tiên)
2. [BENCH-002b] Đo CEER thật sau khi có GT — Drug Recall, Diag, Vital real pilot audio
3. [TRAIN-001] Fine-tune PhoWhisper trên 50-100h audio pilot thật — cần BENCH-002b trước
