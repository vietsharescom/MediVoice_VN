# BACKLOG.md — MediVoice VN
# Single source of truth cho tasks. Đọc sau CLAUDE.md.
# Format: simple kanban. Không cần status field phức tạp.

---

## WAITING-ANDY

- [ ] **KICKOFF-S10** 🔴 Ký Section 10 của PROJECT_KICKOFF.md → unlock FID-VN-001
- [ ] **PILOT-CLINIC** 🟡 Arrange phòng khám CĐHA tư cho pilot
- [ ] **GITHUB-VN** 🟢 Tạo repo GitHub cho MediVoice_VN
- [ ] **VIETMED-LICENCE** 🟡 Verify commercial use licence cho VietMed dataset

---

## TODO (sau khi S10 approved)

- [ ] FID-VN-001: `plugin_cdha.py` — báo cáo siêu âm/X-quang/CT
- [ ] FID-VN-002: `plugin_ngoai_tru.py` — Mẫu 15/BV1 ngoại trú chung
- [ ] FID-VN-003: `plugin_nha_khoa.py` — Mẫu 16/BV1 nha khoa
- [ ] INFRA: Fork CA v2.61.3 → xóa MarianMT (L1b) + thay PII patterns
- [ ] INFRA: Build ICD-10-VN database (QĐ5837/BYT)
- [ ] INFRA: HL7 FHIR export basic (TT13/2025, deadline 31/12/2026)
- [ ] TRAIN: Fine-tune PhoWhisper trên VietMed 16h labeled (Kaggle)
- [ ] TRAIN: Handle ViMedCSS code-switching VI+EN

---

## DOING

*(trống — chờ S10)*

---

## DONE

- [x] Research thị trường VN (~15h, 2026-06-02)
- [x] CLAUDE.md v1.1
- [x] PROJECT_KICKOFF S1–S9
- [x] BRS.md, VISION.md
- [x] BACKLOG.md, DECISIONS.md, CHANGELOG.md
- [x] Git init + first commit

---

## DEFERRED (Phase 2+)

- [ ] plugin_san_khoa (Mẫu 05/BV1)
- [ ] plugin_nhi (Mẫu 02/BV1)
- [ ] FPT.eHospital integration
- [ ] Luật AI 134 conformity assessment (deadline 01/09/2027)
- [ ] VNeID health platform integration

---
*Updated: 2026-06-03*
