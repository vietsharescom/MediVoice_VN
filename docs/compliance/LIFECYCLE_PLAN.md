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
| **P0.1 Design** | Done 2026-06-03 | CLAUDE.md + BRS + VISION approved |
| **P0.2 Implement** | Done 2026-06-04 | 61/61 tests PASS, L0-L10 implemented |
| **P0.3 Benchmark** | Chờ audio | BENCH-001: WER<30%, CEER<5% |
| **P0.4 Pilot** | TBD | 5 BS pilot, NPS>7, approve_rate>85% |
| **P1.0 Fine-tune** | Sau pilot | PhoBERT trained, WER<20% |
| **P1.1 Launch** | Sau P1.0 | 5 paying users, legal review done |
| **P2.0 Conformity** | Trước 2027-09-01 | Luật AI 134/2025 conformity assessment |

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

*DS-VN-COM-012 | LIFECYCLE_PLAN v1.0 | ISO/IEC 42001:2023 Cl.8.3 | 2026-06-04*
