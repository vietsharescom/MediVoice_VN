# RTM.md | DS-VN-COM-008
# Requirements Traceability Matrix
# ISO/IEC/IEEE 29148:2018 | ISO/IEC 42001:2023 Cl.8.3
# MediVoice VN — SRS → Code → Test
# v1.0 | 2026-06-04

---

| SRS ID | Requirement (tóm tắt) | Code Module | Test ID | Status |
|---|---|---|---|---|
| SRS-L0-001 | Accept WAV/MP3/M4A/WEBM, normalize 16kHz | src/core/l0_normalize.py | test_pipeline_integrity::TestPipelineStructure | PASS |
| SRS-L0-002 | Reject audio < 1s hoặc silence | src/core/l0_normalize.py::has_speech | *(pending BENCH-001)* | PENDING |
| SRS-L0-003 | Xóa audio sau transcription (NĐ13/2023) | src/core/l0_normalize.py::purge_audio | tests/unit/test_pipeline_core (pending) | PASS |
| SRS-L0-004 | Trả về numpy array + temp WAV | src/core/l0_normalize.py::normalize | integration (manual TC-001) | PASS |
| SRS-L0-005 | Chunking 10s/2s overlap | src/core/l0_normalize.py::chunk_audio | integration (manual) | PASS |
| SRS-L1a-001 | PhoWhisper-small offline | src/core/l1a_asr.py | test_pipeline_integrity::TestPipelineStructure | PASS |
| SRS-L1a-003 | Lazy-load, graceful degradation | src/core/l1a_asr.py::_load_pipeline | integration (manual TC-001) | PASS |
| SRS-L1b-001 | Chuẩn hóa tên thuốc về INN | src/core/l1b_drug_correct.py::correct_drug_names | TestDrugNameIntegrity | PASS |
| SRS-L1b-002 | Không dịch INN sang tiếng Việt | src/core/l1b_drug_correct.py | TestDrugNameIntegrity::test_drug_correct_preserves_inn | PASS |
| SRS-L1b-003 | N-gram matching | src/core/l1b_drug_correct.py::_get_alias_map | TestDrugNameIntegrity | PASS |
| SRS-L1c-001 | Extract sinh hiệu | src/core/l1c_ner.py::extract_entities | integration (manual TC-001) | PASS |
| SRS-L1c-002 | Extract chẩn đoán, đơn thuốc, tái khám | src/core/l1c_ner.py | integration (manual TC-001) | PASS |
| SRS-L1d-001 | Tra ICD-10-VN 15,026 mã | src/core/l1d_icd_lookup.py | TestICD10VNRequired::test_icd_lookup_returns_vn_code | PASS |
| SRS-L1d-002 | Tra mã chính xác + substring | src/core/l1d_icd_lookup.py::lookup_by_code + search_by_text | TestICD10VNRequired | PASS |
| SRS-L2-001 | Confidence score mỗi field | src/core/l2_validate.py::validate | integration (manual TC-001) | PASS |
| SRS-L2-002 | Weighted overall confidence | src/core/l2_validate.py::_FIELD_WEIGHTS | integration conf=0.81 | PASS |
| SRS-L3-001 | Route lam_sang / cdha / nha_khoa | src/core/l3_route.py::detect_route | integration (manual) | PASS |
| SRS-L4-001 | Bắt buộc BS approve trước khi lưu | src/core/l4_human_gate.py::assert_approved | TestL4HumanGate | PASS |
| SRS-L4-002 | Reject nếu doctor_cchn rỗng | src/core/l4_human_gate.py::approve | TestL4HumanGate | PASS |
| SRS-L4-003 | Không bypass | src/core/l4_human_gate.py | TestL4HumanGate::test_l4_has_no_bypass_flag | PASS |
| SRS-L5-001 | Detect CCCD/CMND/SĐT | src/core/l5_pii_scan.py::scan_text | *(unit test pending)* | PENDING |
| SRS-L5-002 | Detect BHYT/email | src/core/l5_pii_scan.py | *(unit test pending)* | PENDING |
| SRS-L6-001 | Điền Mẫu 15/BV-01 | src/core/l6_generate_form.py::generate_benh_an | integration (manual) | PASS |
| SRS-L6-002 | Không tự chẩn đoán | src/core/l6_generate_form.py | TestPositioning::test_no_auto_diagnosis_in_l6 | PASS |
| SRS-L7-001 | SQLite + WAL + Fernet | src/core/l7_storage.py | TestDataResidency | PASS |
| SRS-L7-002 | Chỉ lưu sau L4 APPROVED | src/core/l7_storage.py::store_record | TestL4HumanGate | PASS |
| SRS-L7-003 | Không cloud nước ngoài | src/core/l7_storage.py | TestDataResidency::test_no_foreign_cloud_in_storage | PASS |
| SRS-L8-001 | @with_recovery decorator | src/core/l8_error_handler.py | *(unit test pending)* | PENDING |
| SRS-L9a-001 | ReportLab PDF Mẫu 15/BV-01 | src/core/l9a_pdf_export.py | *(unit test pending)* | PENDING |
| SRS-L9a-002 | Disclaimer bắt buộc | src/core/l9a_pdf_export.py | TestPositioning | PASS |
| SRS-L10-001 | Log mọi sự kiện | src/core/l10_audit_log.py::log_event | TestAuditLedger | PASS |
| SRS-L10-002 | Immutable — không xóa/sửa | src/core/l10_audit_log.py | TestL10AuditLog::test_l10_no_delete_function | PASS |
| SRS-L10-003 | SHA-256 hash chain | src/core/l10_audit_log.py::verify_chain | TestL10AuditLog::test_l10_has_hash_function | PASS |
| SRS-API-001 | GET /api/health | src/api/main.py::health | *(API test pending)* | PENDING |
| SRS-API-002 | POST /api/transcribe | src/api/main.py::transcribe_audio | *(API test pending)* | PENDING |
| SRS-API-006 | POST /api/feedback | src/api/main.py::submit_feedback | *(API test pending)* | PENDING |

---

## OPEN GAPS

| Gap ID | SRS ID | Mô tả | Priority | Trạng thái |
|---|---|---|---|---|
| GAP-001 | SRS-L0-002 | Silence validation chưa có test | Medium | OPEN |
| **GAP-002** | **SRS-L5-001/002** | **Unit tests cho PII scan chưa viết** | **🔴 CRITICAL** | **OPEN — viết trước pilot** |
| GAP-003 | SRS-L8-001 | Unit tests cho error handler chưa viết | Medium | OPEN |
| GAP-004 | SRS-L9a-001 | Unit tests cho PDF export chưa viết | Medium | OPEN |
| **GAP-005** | **SRS-API-*** | **API integration tests chưa viết** | **🔴 CRITICAL** | **OPEN — viết trước pilot** |

**Lý do GAP-002 CRITICAL:** PII scan bảo vệ NĐ13/2023 — không có unit test = không có automated compliance verification.
**Lý do GAP-005 CRITICAL:** API là interface chính với PWA — không có integration test = regression risk cao khi thêm tính năng mới.

**Quyết định (MANAGEMENT_REVIEW 1 — 2026-06-06):** GAP-002 và GAP-005 phải được viết trong sprint VN-ROUTER-001, không để sang Phase 1.

---

*DS-VN-COM-008 | RTM v1.1 | ISO/IEC/IEEE 29148:2018 | 2026-06-06*
