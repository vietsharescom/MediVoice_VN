# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260605
## Thời gian: 2026-06-05
## Version: v0.3.0 → v0.4.0

---

## Trạng thái đầu → cuối
v0.3.0 | 165 tests → v0.4.0 | 165 tests PASS | T-005 20/22 PASS (91%)

---

## Đã hoàn thành

### BENCH-001 — Hoàn tất
- T-007: eval_phowhisper.py — 10/10 PASS | WER 36–52% | RTF ~0.5x
- Partial CEER: 0% → phát hiện drug_db aliases rỗng + NER patterns quá cứng
- Nguyên nhân CEER=0%: Canada dùng MarianMT nội bộ cho NER → VN đã xóa nhầm

### Canada Pipeline Port (toàn bộ, không sửa)
- src/pipeline/p0–p3: l0_input, l1_semantic, l1b_translation (MarianMT), l2_enforcer, l3_routing, l4_authority, l5_policy, l6_agent, l6_soap_generator, l7_memory, l8_recovery, l9_response, l10_observability
- src/models/: phobert_ner, clinical_kb, qwen_reasoning, _phobert_crf
- src/adapters/: llm_adapter
- data/kb/: chunks.json + faiss_index.bin + guidelines.json (Clinical KB từ Canada)
- tools/: eval_phowhisper.py, run_test_audio.py, record_test_audio.py (Canada, không sửa)

### T-005 — Canada Pipeline trên VN audio
- 20/22 PASS (91%) | 20/20 VI detected | 20/20 SOAP S/O/A/P complete
- 2 FAIL hợp lệ: test_dental_01 (silence >95%), test_dental_02 (too short 1s)
- MarianMT active: translation VI→EN cho NER
- SOAP-S extraction: age + chief complaint detected cho nhiều files

### Architecture Decisions (ADR mới)
- Canada pipeline = core pipeline VN (không rewrite)
- MarianMT kích hoạt ngay (sửa quyết định sai 2026-06-04)
- SOAP = output chuẩn cho CĐHA branch
- FAISS KB kích hoạt

### ISO Docs Updated
- DECISIONS.md: 4 ADR mới
- SOFTWARE_ARCHITECTURE.md: bảng so sánh CA/VN cập nhật
- BACKLOG.md: BENCH-001 → DONE, thêm VN-ROUTER-001
- CHANGELOG.md: v0.4.0 entry

---

## Kết quả đo được
- Tests: 165/165 PASS (không thay đổi)
- T-007: 10/10 PASS | WER avg 46% | RTF 0.5x
- T-005: 20/22 PASS (91%) | SOAP 20/20
- WER range: 0.29–0.52 (proxy, chưa fine-tune)
- CEER: partial 0% (test audio) → cần pilot audio thực tế

---

## Blocker / Phụ thuộc bên ngoài
- VN-ROUTER-001: cần implement trước khi output Mẫu 15/BV-01 hoạt động
- BENCH-002 (CEER thật): cần pilot audio BS nói thật + ground truth
- TRAIN-001: cần 50–100h audio từ pilot Đà Nẵng
- LEGAL-001: luật sư VN — trước launch thương mại
- Qwen reasoner: template DDx fallback OK cho Phase 0, Qwen = Phase 2

---

## Phiên tiếp theo — làm ngay theo thứ tự
1. **VN-ROUTER-001** — l9_vn_router.py: SOAP→Mẫu 15/BV-01 (lam_sang) | SOAP giữ (cdha)
2. **DEPLOY-001** — Windows installer cho BS Đà Nẵng (Python venv + models cached)
3. **CONFIG-001** — Facility config UI (tên phòng khám, CCHN, khoa)
4. **DRUG-ALIAS-001** — Thêm aliases drug_db.json (ammosiline→Amoxicillin etc.)
