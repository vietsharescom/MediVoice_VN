# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260611c
## Thời gian: 2026-06-11
## Version: v0.11.13 → v0.11.14

---

## Trạng thái đầu → cuối
v0.11.13 | 939 tests → v0.11.14 | 948 tests

## 1. Actions Completed
- Files sửa:
  - `src/core/l1c_ner.py` — thêm `MedicalEntities.tuoi`/`gioi_tinh`, regex `_RE_PATIENT_NAME_AGE`/`_RE_GIOI_TINH_TUOI`/`_RE_TUOI`/`_NAME_STOP_KW`, wire vào `extract_entities()` (patient name fallback + tuổi/giới tính + ly_do dedup)
  - `src/core/l1b_drug_correct.py` — `_build_alias_map()`: nới filter phonetic_variants 2-từ cho phép nếu normalized ≥9 ký tự (cho "parasyte mode")
  - `data/reference/drug_db_v200.json` — Paracetamol `phonetic_variants` đã có "parasyte mode" (3 vùng miền, từ phiên trước)
  - `src/core/l2_validate.py` — `form_data` thêm `tuoi`, `gioi_tinh`
  - `src/core/l6_generate_form.py` — import `GioiTinh`, wire `form_data.tuoi`/`gioi_tinh` → `record.hanh_chinh`
  - `src/api/static/index.html` — thêm input Tuổi + select Giới tính trong `#card-setup`, autofill từ `displayDraft()`, đọc lại trong `buildEditedFormData()`
  - `tests/unit/test_l1c_ner_bugs.py` — +8 tests (TestBugN_ChanDoanThuocUongLa, TestBugO_TuoiGioiTinhVaTenBenhNhan)
  - `tests/unit/test_l1b_drug_correct_v2.py` — +1 test (`test_paracetamol_parasyte_mode_variant`)
  - `docs/records/PENDING_REQUESTS.md` — CT-049 row DONE, PA-023 cập nhật
  - `CHANGELOG.md` — entry v0.11.14
  - `CLAUDE.md` — CURRENT STATE → v0.11.14
  - `docs/records/BACKLOG.md` — section CT-049 [DONE]
- Code generated: ~120 LOC (regex + wiring + UI inputs)
- Tests chạy: 948/948 PASS (+9 mới), bandit 0 HIGH / 9 MEDIUM (pre-existing) / 2 LOW
- Commit code: `2d3f4ae` — 12 files, +226/-15

## 2. Decisions
- Owner Decisions (Andy): re-test pilot vòng 2 phát hiện 3 vấn đề mới (CT-049) → ưu tiên fix ngay trước TRAIN-001
- Technical Decisions (Claude):
  - Dùng câu mở đầu chuẩn "<nam/nữ> <N> tuổi, <Họ Tên>, <triệu chứng>..." làm fallback pattern cho `ho_ten`/`tuoi`/`gioi_tinh` khi không có cue rõ ràng ("tên là", "bệnh nhân tên")
  - Mở filter alias 2-từ trong `_build_alias_map()` chỉ khi normalized ≥9 ký tự — verify 58 alias 2-từ hiện có đều ≤8 ký tự, chỉ "parasyte mode" (13 ký tự) lọt qua → tránh false positive

## 3. Architecture Changes
- L1c NER: thêm 2 field mới (`tuoi: int|None`, `gioi_tinh: str`) vào `MedicalEntities` — không phá pipeline L0→L10, chỉ extend (Tầng 2 pattern, theo precedent CT-038/043/048)
- L2→L6: `form_data` → `HanhChinh.tuoi`/`gioi_tinh` → PDF Mẫu 15/BV1
- UI: thêm 2 input mới trong card setup (Tuổi, Giới tính), BS review/sửa trước khi confirm (L4 Human Gate giữ nguyên)

## 4. Tasks Created
- (không có task mới — CT-049 đã DONE trong phiên)

## 5. Pending Items
- [CT-049] Andy re-test clip TMH lần 3 — confirm chẩn đoán/đơn thuốc/tuổi-tên đúng trên PDF
- [PA-020/PA-021] Andy test UI FID-VN-017/018 (audio mẫu giờ đã có)
- [PA-015/PA-017/PA-018] Andy test UI FID-VN-013/014/015/016
- [CT-019] 🔴 A2 VAD-chunk regression — cần audio mẫu để debug
- [TRAIN-001] PhoWhisper fine-tune — vẫn ưu tiên cao nhất per CT-028, song song với CT-049 re-test

## 6. Risks / Confusions
- (không có — cả 3 fix CT-049 đều straightforward, verified end-to-end với transcript pilot thật)

## Phiên tiếp theo — thứ tự ưu tiên
1. TRAIN-001 — PhoWhisper fine-tune (ưu tiên cao nhất per CT-028)
2. CT-049 — chờ Andy re-test clip TMH lần 3, fix tiếp nếu còn vấn đề
3. CT-019 — debug A2-VAD nếu Andy cung cấp audio mẫu
