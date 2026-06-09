# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260609g
## Thời gian: 2026-06-09
## Version: v0.10.1 → v0.11.0

---

## Trạng thái đầu → cuối
v0.10.1 | 794 tests → v0.11.0 | 817 tests

## Đã hoàn thành
- [FID-VN-012] Doctor Voice Profile Layer 1+2 — IMPLEMENTED (PA-012 Andy approved "TRIỂN KHAI NGAY")
  - `src/models/doctor_profile.py` — DoctorProfile + DoctorAlias · VALID_SPECIALTIES (12) · VALID_REGIONS
  - `src/core/l7_storage.py` — doctor_profiles + doctor_aliases tables (migration-safe) + full CRUD
  - `src/core/l1a_asr.py` — SPECIALTY_DRUG_CLASSES 12 canonical FID-VN-012 + 6 legacy aliases
  - `src/core/dvp_alias.py` — Layer 3 alias promotion logic (pilot-gated schema)
  - `src/api/main.py` — pipeline injection: specialty→L1a A1, region→A3 dialect norm
    + POST /api/doctors · GET /api/doctors/{cchn}
    + GET /api/doctors/{cchn}/aliases/pending · POST /api/doctors/{cchn}/aliases/{id}/confirm
  - `tests/unit/test_dvp.py` — 23 tests AC-001→AC-010 PASS
- Commits: `e6d9dc1` (FID-VN-012 DRAFT + WIN2 docs) · `a3b733a` (DVP L1+2 implementation)

## Kết quả đo được
- Tests: 817/817 PASS (794→817, +23 DVP, 0 regressions)
- Pipeline injection: dvp_specialty + dvp_region trả về trong /api/transcribe response
- DB: doctor_profiles + doctor_aliases tables live trong medivoice.db
- AC-001→AC-010 đủ 100%

## Blocker / Phụ thuộc bên ngoài
- [TRAIN-001] Cần audio thật từ pilot — BS phải cài install.bat tại phòng khám thật
- [DVP-L3] Layer 3 alias passive learning — cần ≥5 sessions pilot data để test promote

## Phiên tiếp theo — làm ngay theo thứ tự
1. [VIETMED-FIX-001] Fix `scripts/download_vietmed.py` — remove trust_remote_code + HF_TOKEN (~5 LOC, làm ngay)
2. [DESIGN-REVIEW] Cập nhật `docs/records/DESIGN_REPORT_v1.1_20260606.md` §15 thêm DVP section
3. [PILOT] Andy cài install.bat tại phòng khám Đà Nẵng → thu audio → TRAIN-001
4. [DVP-L3] Sau pilot: implement alias passive learning (promote từ corrections)
