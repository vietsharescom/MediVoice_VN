# docs/records/consultations/
# Multi-AI Consultation Records — MediVoice VN
# Template: docs/dev/CONSULTATION_TEMPLATE.md

Thư mục này lưu tất cả consultation requests và synthesis results.

## Naming Convention
  CONS-YYYYMMDD-NNN.md
  Example: CONS-20260606-001.md

## Workflow
  1. Claude generates CONS-YYYYMMDD-NNN.md
  2. Andy copies REQUEST section → pastes to ChatGPT/Grok
  3. Andy pastes responses back to Claude
  4. Claude completes SYNTHESIS section in the same file
  5. Decision recorded in DECISIONS.md if it's an ADR

## Index
(Claude updates this list when new consultations are added)

| File | Topic | Date | Status | Decision |
|---|---|---|---|---|
| [CONS-20260611-001.md](CONS-20260611-001.md) | Từ điển phiên âm Anh→Việt cho tên thuốc (CT-039/040/041) | 2026-06-11 | RESOLVED | Merriam-Webster (Medical) Dictionary là nguồn — cite trong `pronunciation_en_source` |
