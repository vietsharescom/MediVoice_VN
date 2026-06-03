# TASK_BACKLOG.md — MediVoice VN Persistent Task Tracker
# Claude reads this at EVERY session start (after LATEST_SESSION.md).
# Updated: 2026-06-03

## WAITING-ANDY (cần quyết định)

| ID | Task | Priority | Added |
|---|---|---|---|
| **KICKOFF-S10** | Ký Section 10 của PROJECT_KICKOFF.md → mở đường cho FID | 🔴 BLOCKING | 2026-06-03 |
| PILOT-CLINIC | Arrange 1 phòng khám CĐHA tư cho pilot test | 🟡 | 2026-06-03 |
| LEGAL-REVIEW | Confirm với luật sư: AI scribe có phải đăng ký thiết bị y tế? | 🟡 | 2026-06-03 |
| VIETMED-LICENCE | Verify VietMed dataset commercial use licence | 🟡 | 2026-06-03 |
| GITHUB-VN | Tạo repo GitHub riêng cho MediVoice_VN | 🟢 | 2026-06-03 |

## READY — Sau khi KICKOFF-S10 approved

| ID | Task | FID | Notes |
|---|---|---|---|
| FID-VN-001 | plugin_cdha.py — báo cáo siêu âm/X-quang/CT | Cần viết FID | Use case #1 |
| FID-VN-002 | plugin_ngoai_tru.py — Mẫu 15/BV1 ngoại trú chung | Cần viết FID | Use case #2 |
| FID-VN-003 | plugin_nha_khoa.py — Mẫu 16/BV1 nha khoa | Cần viết FID | Use case #3 |
| INFRA-001 | Fork MediVoice CA v2.61.3 → xóa MarianMT (L1b) | < 20 LOC | Direct commit |
| INFRA-002 | Thay PII patterns: OHIP/SIN → CCCD/CMND/BHYT | < 20 LOC | Direct commit |
| INFRA-003 | Build ICD-10-VN database (QĐ5837/BYT) | FID needed | ~50 LOC |
| INFRA-004 | HL7 FHIR export basic (TT13/2025) | FID needed | ~80 LOC |
| TRAIN-001 | Fine-tune PhoWhisper trên VietMed 16h labeled | Kaggle | 1 session |
| TRAIN-002 | Handle ViMedCSS code-switching | FID needed | ~30 LOC |

## DEFERRED (Phase 2+)

| ID | Task | Condition |
|---|---|---|
| FID-VN-004 | plugin_san_khoa.py — Mẫu 05/BV1 | Phase 2 |
| FID-VN-005 | plugin_nhi.py — Mẫu 02/BV1 | Phase 2 |
| FID-VN-006 | plugin_nhan_khoa.py — Mẫu 21-26/BV1 | Phase 2 |
| LEGAL-001 | Luật AI 134 conformity assessment | Trước 01/09/2027 |
| INTEG-001 | FPT.eHospital API integration | Phase 2 |
| INTEG-002 | Viettel HIS API integration | Phase 2 |
| INTEG-003 | VNeID health platform integration | Phase 3 |
| TRAIN-003 | KB tiếng Việt — hướng dẫn lâm sàng MOH | Phase 2 |

## COMPLETED

| ID | Task | Date | Notes |
|---|---|---|---|
| RESEARCH-001 | Market research VN (~15h) | 2026-06-02 | Full competitive analysis |
| DOC-001 | CLAUDE.md VN | 2026-06-03 | ✅ |
| DOC-002 | PROJECT_KICKOFF S1–S9 | 2026-06-03 | ✅ Awaiting S10 |
| DOC-003 | BRS.md | 2026-06-03 | ✅ |
| DOC-004 | VISION.md | 2026-06-03 | ✅ |
| DOC-005 | LATEST_SESSION + TASK_BACKLOG | 2026-06-03 | ✅ |

---
*TASK_BACKLOG.md | MediVoice VN | Updated: 2026-06-03*
