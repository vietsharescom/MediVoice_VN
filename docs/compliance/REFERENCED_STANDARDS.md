# REFERENCED_STANDARDS.md | DS-VN-COM-014
# ISO/IEC 42001:2023 Clause 2 — Normative References
# MediVoice VN — Tiêu chuẩn Tham chiếu
# v1.0 | 2026-06-04

---

## Tiêu chuẩn Quốc tế (ISO/IEC)

| Tiêu chuẩn | Tên | Áp dụng cho |
|---|---|---|
| ISO/IEC 42001:2023 | AI Management Systems | Toàn bộ AIMS framework |
| ISO 9001:2015 | Quality Management Systems | QMS baseline |
| ISO 31000:2018 | Risk Management | RISK_REGISTER, RiskEngine |
| ISO/IEC 12207:2017 | Software Lifecycle | SOFTWARE_ARCHITECTURE, QA_PLAN |
| ISO/IEC/IEEE 29148:2018 | Requirements Engineering | SRS.md, RTM.md |
| ISO/IEC/IEEE 29119-3:2021 | Software Testing | TEST_PLAN.md |

## Pháp luật Việt Nam (Bắt buộc)

| Văn bản | Tên | Áp dụng cho |
|---|---|---|
| Nghị định 13/2023/NĐ-CP | Bảo vệ dữ liệu cá nhân | L5 PII, L7 storage, audio purge |
| Thông tư 32/2023/TT-BYT | Hồ sơ bệnh án điện tử | Mẫu 15/BV-01, L6, L9a |
| Thông tư 13/2025/TT-BYT | CNTT trong KCB (EMR/FHIR) | Phase 2 roadmap |
| Luật KCB 2023 (15/2023/QH15) | Khám chữa bệnh | L4 Human Gate, CCHN |
| Luật AI 134/2025 | Trí tuệ nhân tạo | L4+L10, conformity 2027 |
| Quyết định 5837/QĐ-BYT | ICD-10-VN | L1d, icd10vn.json |
| Thông tư 07/2017/TT-BYT | Kê đơn thuốc | drug_db.json, L1b |
| Thông tư 28/2024/TT-BYT | Danh mục thuốc | drug_db.json |
| Thông tư 46/2017/TT-BYT | Trang thiết bị y tế (SaMD) | NOT SaMD — Documentation Assistant |

## Tài liệu Kỹ thuật Tham chiếu

| Tài liệu | Nguồn | Dùng cho |
|---|---|---|
| ICD-10-VN (15,026 mã) | HL7 Vietnam / QĐ4469/QĐ-BYT | data/reference/icd10vn.json |
| VietMed dataset (MIT) | Kaggle | Training data L1a Phase 1 |
| PhoWhisper-small (BSD-3-Clause) | VinAI / HuggingFace | L1a ASR |
| PhoBERT (MIT) | VinAI / HuggingFace | L1c NER Phase 1 |

---

*DS-VN-COM-014 | REFERENCED_STANDARDS v1.0 | ISO/IEC 42001:2023 Cl.2 | 2026-06-04*
