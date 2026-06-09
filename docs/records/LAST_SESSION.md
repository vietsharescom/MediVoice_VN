# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260609b
## Thời gian: 2026-06-09 (đêm tiếp theo)
## Version: v0.8.5 → v0.8.6

---

## Trạng thái đầu → cuối
v0.8.5 | 473 tests → v0.8.6 | 678/678 tests PASS

## Đã hoàn thành
- [A1-PROMPT-INJECT] `src/core/l1a_asr.py` — SPECIALTY_DRUG_CLASSES + get_drugs_by_specialty() + build_initial_prompt()
  - `transcribe()` / `transcribe_file()` / `transcribe_chunks()` nhận drug_db + specialty params
  - `tests/unit/test_l1a_prompt_inject.py` — 23 tests PASS | Total: 496/496
- [A2-VAD-CHUNK] `src/core/l0_normalize.py` — _merge_short_gaps() + vad_chunk_audio() (silero-vad==6.2.1)
  - Max chunk 20s, gap_ms 500ms, midpoint split nếu vượt, fallback fixed chunk_audio()
  - `tests/unit/test_l0_vad_chunk.py` — 18 tests PASS | Total: 514/514
- [A3-DIALECT-NORM] `src/core/dialect_norm.py` — 200+ entries (central/southern/northern/medical_abbrev)
  - detect_region() + normalize_dialect() + expand_abbreviations() + normalize_text()
  - `tests/unit/test_l1a_dialect_norm.py` — 49 tests PASS | Total: 563/563
- [L4-REDESIGN-001] `demo/app.py` — per-drug st.checkbox gate + _all_drugs_confirmed + disabled=not _all_drugs_confirmed
  - Flagged drugs hiện st.warning + confidence %; reset drug_confirm keys on new session/Từ chối/Khám BN tiếp theo
  - Evidence: Session 174116 Losartan→Atorvastatin safety failure

## Kết quả đo được
- Tests: 473/473 → 678/678 PASS (+205 tests trong phiên)
- A1: Prompt injection bias PhoWhisper decoder → drug vocabulary per specialty
- A2: VAD chunking tại silence tự nhiên → không cắt giữa "Kê Ciprofloxacin [pause] 500mg"
- A3: 200+ dialect entries — "mô→đâu", "tui→tôi", "ha→huyết áp" (medical abbrev)
- L4: Per-drug mandatory confirm → BS không thể batch approve mà không đọc từng thuốc

## Blocker / Phụ thuộc bên ngoài
- [PA-009] Andy chưa fill 54/57 GT clips → BENCH-002b CEER thật chưa đo được
- [PA-010] FID-VN-010 approve retroactive (Phase 0 đã implement xong)
- [PA-011] Andy chưa chốt Q1+Q3 → FID-VN-009 PhoBERT deferred

## Phiên tiếp theo — làm ngay theo thứ tự
1. [RAG-001-DRUG-VECTOR] `src/core/drug_rag.py` — Chroma + paraphrase-multilingual-MiniLM-L12-v2
2. [UI-SUGGEST-001] Drug chips + dialect badge (cần RAG-001 xong trước)
3. [PA-009] Andy fill GT clips song song với Claude implement RAG-001
