# SRS.md | DS-VN-COM-007
# ISO/IEC/IEEE 29148:2018 — System Requirements Specification
# ISO/IEC 42001:2023 Clause 8.3 — AI System Lifecycle
# MediVoice VN — System Requirements (Vietnamese Market)
# v1.0 | 2026-06-04 | Owner: Andy Phan

---

## p0_ingestion — L0_NORMALIZE

| ID | Requirement | Priority |
|---|---|---|
| SRS-L0-001 | SHALL accept audio formats WAV, MP3, M4A, WEBM và normalize về 16kHz mono PCM | Must |
| SRS-L0-002 | SHALL reject audio ngắn hơn 1 giây hoặc > 95% silence (VAD) | Must |
| SRS-L0-003 | SHALL xóa audio khỏi memory sau khi transcription hoàn tất | Must |
| SRS-L0-004 | SHALL trả về numpy array float32 + temp WAV path | Must |
| SRS-L0-005 | SHALL chunk audio thành 10s với overlap 2s cho streaming ASR | Must |

---

## p1_processing — L1a_ASR

| ID | Requirement | Priority |
|---|---|---|
| SRS-L1a-001 | SHALL dùng PhoWhisper-small (vinai/PhoWhisper-small, BSD-3-Clause) cho tiếng Việt | Must |
| SRS-L1a-002 | SHALL hoạt động offline — không có network call trong khi transcribe | Must |
| SRS-L1a-003 | SHALL lazy-load model — chỉ load khi cần, graceful degradation nếu model unavailable | Must |
| SRS-L1a-004 | SHALL trả về chuỗi rỗng (không crash) nếu model không load được | Must |
| SRS-L1a-005 | SHALL hỗ trợ chunked transcription cho audio dài | Must |

## p1_processing — L1b_DRUG_CORRECT

| ID | Requirement | Priority |
|---|---|---|
| SRS-L1b-001 | SHALL chuẩn hóa tên thuốc về INN chuẩn từ drug_db.json (110+ thuốc) | Must |
| SRS-L1b-002 | SHALL NOT dịch tên INN sang tiếng Việt (an toàn bệnh nhân) | Must |
| SRS-L1b-003 | SHALL match n-gram (3-gram, 2-gram, 1-gram) với alias map | Must |
| SRS-L1b-004 | SHALL normalize diacritics khi so khớp (fuzzy match) | Must |

## p1_processing — L1c_NER

| ID | Requirement | Priority |
|---|---|---|
| SRS-L1c-001 | SHALL extract: nhiệt độ, huyết áp, mạch, nhịp thở, cân nặng, SpO2 từ transcript | Must |
| SRS-L1c-002 | SHALL extract: chẩn đoán, đơn thuốc, tái khám | Must |
| SRS-L1c-003 | Phase 0: rule-based regex. Phase 1: PhoBERT + CRF | Must |
| SRS-L1c-004 | SHALL trích xuất context đơn thuốc: hàm lượng, tần suất, số ngày, đường dùng | Must |

## p1_processing — L1d_ICD_LOOKUP

| ID | Requirement | Priority |
|---|---|---|
| SRS-L1d-001 | SHALL tra ICD-10-VN từ icd10vn.json (15,026 mã, QĐ5837/QĐ-BYT) | Must |
| SRS-L1d-002 | SHALL hỗ trợ tra theo mã chính xác và tìm kiếm substring | Must |
| SRS-L1d-003 | SHALL trả về display tiếng Việt kèm mã ICD | Must |

## p1_processing — L2_VALIDATE

| ID | Requirement | Priority |
|---|---|---|
| SRS-L2-001 | SHALL tính confidence score cho từng field (0.0–1.0) | Must |
| SRS-L2-002 | SHALL tính overall_confidence weighted: chan_doan(0.30), don_thuoc(0.25), ly_do(0.14)... | Must |
| SRS-L2-003 | SHALL flag overall_confidence < 0.3 trong ValidationLayer | Must |
| SRS-L2-004 | SHALL trả về form_data dict sẵn sàng merge vào ClinicalRecord | Must |

## p1_processing — L3_ROUTE

| ID | Requirement | Priority |
|---|---|---|
| SRS-L3-001 | SHALL classify route: lam_sang (default) / cdha / nha_khoa | Must |
| SRS-L3-002 | SHALL detect CDHA từ keywords: siêu âm, x-quang, CT, MRI | Must |
| SRS-L3-003 | SHALL detect nha_khoa từ keywords: răng, nha, nướu | Must |
| SRS-L3-004 | SHALL NOT execute routing — classification only | Must |

---

## p2_decision — L4_HUMAN_GATE

| ID | Requirement | Priority |
|---|---|---|
| SRS-L4-001 | SHALL yêu cầu BS review và approve TRƯỚC KHI lưu — Luật KCB 2023 Điều 62 | Must |
| SRS-L4-002 | SHALL reject record nếu doctor_cchn rỗng | Must |
| SRS-L4-003 | SHALL NOT cho phép auto-approve hoặc bypass | Must |
| SRS-L4-004 | SHALL transition status: DRAFT → PENDING_REVIEW → APPROVED/REJECTED | Must |

## p2_decision — L5_PII_SCAN

| ID | Requirement | Priority |
|---|---|---|
| SRS-L5-001 | SHALL phát hiện CCCD (12 số), CMND (9 số), SĐT VN (0[3-9]xxxxxxxx) | Must |
| SRS-L5-002 | SHALL phát hiện số BHYT và email — NĐ13/2023 | Must |
| SRS-L5-003 | SHALL flag PII trong output (không block pipeline) | Must |
| SRS-L5-004 | SHALL cung cấp mask_pii() cho logging an toàn | Must |

## p2_decision — L6_FORM_GENERATOR

| ID | Requirement | Priority |
|---|---|---|
| SRS-L6-001 | SHALL điền Mẫu 15/BV-01 từ form_data (TT32/2023) | Must |
| SRS-L6-002 | SHALL NOT tự chẩn đoán — chỉ ghi lại lời BS nói | Must |
| SRS-L6-003 | SHALL ghi ICD-10-VN vào trường ma_icd10 | Must |
| SRS-L6-004 | SHALL hiển thị disclaimer: "AI tạo nháp — BS chịu trách nhiệm" | Must |

## p2_decision — L7_STORAGE

| ID | Requirement | Priority |
|---|---|---|
| SRS-L7-001 | SHALL lưu SQLite + WAL mode, Fernet encryption | Must |
| SRS-L7-002 | SHALL chỉ lưu record sau khi L4 APPROVED (assert_approved()) | Must |
| SRS-L7-003 | SHALL NOT gọi cloud nước ngoài — NĐ13/2023 | Must |
| SRS-L7-004 | SHALL support shared connection với L10 cho atomicity | Must |

---

## p3_output — L8_ERROR_HANDLER

| ID | Requirement | Priority |
|---|---|---|
| SRS-L8-001 | SHALL bắt exception tại mỗi layer, log, trả về fallback | Must |
| SRS-L8-002 | SHALL cung cấp @with_recovery và @safe_log decorators | Must |
| SRS-L8-003 | SHALL không crash pipeline khi L10 fail (safe_log) | Must |

## p3_output — L9a_PDF_EXPORT

| ID | Requirement | Priority |
|---|---|---|
| SRS-L9a-001 | SHALL xuất PDF Mẫu 15/BV-01 bằng ReportLab | Must |
| SRS-L9a-002 | SHALL hiển thị disclaimer bắt buộc trên mỗi PDF | Must |
| SRS-L9a-003 | SHALL ghi đầy đủ: hành chính, sinh hiệu, khám, chẩn đoán ICD, đơn thuốc | Must |

## p3_output — L10_AUDIT_LOG

| ID | Requirement | Priority |
|---|---|---|
| SRS-L10-001 | SHALL ghi mọi sự kiện: CREATED, APPROVED, REJECTED, EXPORTED, FEEDBACK | Must |
| SRS-L10-002 | SHALL immutable — không có hàm xóa/sửa | Must |
| SRS-L10-003 | SHALL SHA-256 hash chain — tamper detection | Must |
| SRS-L10-004 | SHALL verify_chain() kiểm tra toàn bộ chain | Must |
| SRS-L10-005 | Lưu trữ tối thiểu 10 năm (TT32/2023 + Luật AI 134/2025) | Must |

---

## REST_API

| ID | Requirement | Priority |
|---|---|---|
| SRS-API-001 | GET /api/health SHALL trả về status=ok và version | Must |
| SRS-API-002 | POST /api/transcribe SHALL chạy pipeline L0→L3+L5 và trả về draft record | Must |
| SRS-API-003 | POST /api/records/{id}/approve SHALL yêu cầu doctor_cchn hợp lệ | Must |
| SRS-API-004 | POST /api/records/{id}/reject SHALL ghi lý do vào L10 | Must |
| SRS-API-005 | GET /api/records/{id}/pdf SHALL xuất PDF chỉ sau khi APPROVED | Must |
| SRS-API-006 | POST /api/feedback SHALL lưu feedback BS vào SQLite | Must |

---

*DS-VN-COM-007 | SRS v1.0 | ISO/IEC/IEEE 29148:2018 | 2026-06-04*
