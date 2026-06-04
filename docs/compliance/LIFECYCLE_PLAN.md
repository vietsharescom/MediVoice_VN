# LIFECYCLE_PLAN.md | DS-VN-COM-012
# ISO/IEC 42001:2023 Clause 8.3 — AI System Lifecycle
# MediVoice VN — Kế hoạch Vòng đời Hệ thống
# v1.0 | 2026-06-04

---

## 1. VÒNG ĐỜI AI SYSTEM

```
PHASE 0 (hiện tại):  Design → Implement → Test → Pilot (Đà Nẵng)
PHASE 1:             Fine-tune → Validate → Launch thương mại
PHASE 2:             Scale → Conformity Assessment → Certification
```

---

## 2. CÁC GIAI ĐOẠN

| Giai đoạn | Mốc | Tiêu chí exit |
|---|---|---|
| **P0.1 Design** | ✅ Done 2026-06-03 | CLAUDE.md + BRS + VISION approved |
| **P0.2 Implement** | ✅ Done 2026-06-04 | 165/165 tests PASS, L0-L10 implemented |
| **P0.3 Benchmark** | ✅ Done 2026-06-05 | BENCH-001: T-005 20/22 PASS, T-007 10/10 |
| **P0.4 Design Review** | ✅ Done 2026-06-06 | DESIGN_REPORT_v1.1, ISO audit, 6 gaps closed |
| **P0.5 VN-Router + Deploy** | 🔴 Current | FID-VN-004 → VN-ROUTER-001 → DEPLOY-001 |
| **P0.6 Pilot** | TBD | 5 BS pilot Đà Nẵng + SG, audio thu thập |
| **P0.7 CEER Validation** | Sau pilot | BENCH-002: CEER<5%, approve_rate>85% |
| **P1.0 Complete Product** | 3–6 tháng sau P0 | M2/M4/M5/M6/M7 + plugins, 5 paying users |
| **P1.1 Legal Review** | Trước charge tiền | LEGAL-001: luật sư VN sign-off |
| **P2.0 TT13 Compliance** | Trước 31/12/2026 | Chữ ký số + HL7/FHIR |
| **P2.1 Conformity** | Trước 01/09/2027 | Luật AI 134/2025 conformity assessment |

---

## 3. CHANGE CONTROL

Mọi thay đổi pipeline L0→L10 phải:
1. Có FID (Feature Intent Document) với status = APPROVED
2. 100% tests PASS sau thay đổi
3. RTM.md cập nhật
4. CHANGELOG.md entry

---

## 4. END-OF-LIFE

- Dữ liệu bệnh nhân lưu tối thiểu 10 năm (TT32/2023)
- Audit log lưu tối thiểu 10 năm (Luật AI 134/2025)
- Khi ngừng hoạt động: thông báo BS trước 90 ngày, export dữ liệu cho BS

---

*DS-VN-COM-012 | LIFECYCLE_PLAN v1.1 | ISO/IEC 42001:2023 Cl.8.3 | 2026-06-06*
