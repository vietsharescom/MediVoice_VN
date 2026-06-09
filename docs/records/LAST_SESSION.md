# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260609
## Thời gian: 2026-06-09 (đêm)
## Version: v0.8.5 → v0.8.5 (docs only, no code change)

---

## Trạng thái đầu → cuối
v0.8.5 | 473 tests → v0.8.5 | 473 tests (không thay đổi code)

## Đã hoàn thành
- [FID-VN-010] `fids/FID-VN-010.md` — AI Pipeline Redesign v2.0 DRAFT (706 dòng)
  - A1: Whisper prompt injection (initial_prompt drug list theo specialty) — 4h effort
  - A2: VAD silence-aware chunking (silero-vad, max 20s, thay fixed 10s) — 1 ngày
  - A3: Dialect normalization 200+ entries (Trung/Nam) + abbreviation expansion — 2 ngày
  - RAG-001: Drug vector store Chroma + multilingual MiniLM — 3 ngày
  - UI-001: Drug suggestion chips + dialect badge + terminology sidebar — 5 ngày
  - L4-REDESIGN: Per-drug mandatory confirm (safety fix Session 174116) — 3 ngày
- [DESIGN-UPDATE] `docs/records/DESIGN_REPORT_v1.1_20260606.md` Section 15 → v2.0
  - Pipeline v2.0 với VAD/prompt injection/dialect/RAG layers
  - Benchmark table: Drug Recall local=13-18% vs Cloud=78%
  - Roadmap 4 phases documented
- [BACKLOG] FID-VN-010 Phase 0 tasks thêm vào IMMEDIATE: A1/A2/A3/L4-REDESIGN/RAG-001/UI-SUGGEST/BENCH-GT
- [PENDING] PA-009 (fill GT 54 clips) + PA-010 (FID approve) + PA-011 (CONS Q1+Q3)
- [PROGRESS] `docs/records/PROJECT_PROGRESS.md` v1.5: P0.6.6 block mới + L4 safety finding + METRICS Drug Recall real
- [COMMITS] 10334f4 (FID-VN-010) · 7200054 (PROJECT_PROGRESS) · aec1fda (notes+refs+push)

## Kết quả đo được
- Tests: 473/473 PASS (không thay đổi)
- FID-VN-010: DRAFT hoàn chỉnh, đủ để Andy review và approve
- Benchmark evidence: Drug Recall local pipeline = 13–18% (BENCH-002b real) vs 78% (Cloud LLM)
- Root causes: RC-1 Drug OOV hallucination · RC-2 No clinical domain bias · RC-3 Fixed chunk · RC-4 Dialect

## Blocker / Phụ thuộc bên ngoài
- [PA-010] Andy chưa approve FID-VN-010 → Claude chưa implement A1/A2/A3
- [PA-009] Andy chưa fill 54/57 GT clips → BENCH-002b CEER thật chưa đo được
- [PA-011] Andy chưa chốt Q1+Q3 → FID-VN-009 PhoBERT chưa implement

## Phiên tiếp theo — làm ngay theo thứ tự
1. [PA-010] Andy approve `fids/FID-VN-010.md` → Claude implement A1-PROMPT-INJECT (4h, zero risk)
2. [A2-VAD-CHUNK] `src/core/l0_normalize.py` — silero-vad chunking (1 ngày)
3. [A3-DIALECT-NORM] `src/core/dialect_norm.py` — dict 200 entries + abbrev (2 ngày)
4. [L4-REDESIGN-001] Per-drug confirm UI — safety critical (3 ngày)
5. [PA-009] Andy fill GT clips song song với Claude implement
