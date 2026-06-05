# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260608c
## Thời gian: 2026-06-08
## Version: v0.5.3 → v0.6.0

---

## Trạng thái đầu → cuối
v0.5.3 | 272 tests → v0.6.0 | 287 tests

## Đã hoàn thành

- [CT-005/DEPLOY-001] **Windows venv installer** — install.bat + start.bat + check_env + setup_facility + facility_config + requirements-prod.txt (287/287 PASS). P0.6 → 🟢
  - `install.bat` — 6-step: Python check → venv → pip → data check → config wizard → pre-flight
  - `start.bat` — daily launcher, auto-detect port, auto-open browser
  - `scripts/check_env.py` — pre-flight: Python version, disk (5GB min), packages, model cache, reference data, port
  - `scripts/setup_facility.py` — interactive wizard: tên PK, địa chỉ, BS, CCHN, port → `config/facility_config.json`
  - `requirements-prod.txt` — production deps only (no pytest/dev tools)
  - `tests/unit/test_check_env.py` — 15 tests, all mock patterns documented (patch check_env.shutil.disk_usage, CONFIG_PATH, REQUIRED_DATA)
- [CONFIG-001] `config/facility_config.json` template với defaults (province_code, byt_registration_number, host, port)
- [DOC] `docs/records/PROJECT_PROGRESS.md` updated: P0.6 🟢, METRICS 272→287, LỊCH SỬ PHIÊN SES-20260608c, NGAY BÂY GIỜ updated to GAP-003/GAP-004/PILOT
- [DOC] `docs/records/BACKLOG.md` updated: DEPLOY-001 ✅, CONFIG-001 ✅
- [DOC] `docs/records/PENDING_REQUESTS.md` CT-005 → ✅ DONE
- [DOC] `CLAUDE.md` CURRENT STATE: v0.5.3→v0.6.0, 272→287 tests, Next task = GAP-003/GAP-004/PILOT
- [DOC] `CHANGELOG.md` v0.6.0 entry added

## Kết quả đo được
- Tests: **287/287 PASS** (+15 test_check_env)
- DEPLOY-001: install.bat + start.bat fully functional
- check_env.py: 7 checks, exit 0/1 pattern
- setup_facility.py: interactive wizard → config/facility_config.json

## Blocker / Phụ thuộc bên ngoài
- [CT-006] Drug CEER 0.9🔴 — deferred, cần TRAIN-001 (50-100h audio BS thật)
- [GAP-003] `tests/unit/test_l8_error_handler.py` — impl done, unit tests chưa có
- [GAP-004] `tests/unit/test_l9a_pdf_export.py` — impl done, unit tests chưa có
- [PA-006] Andy điền `data/audio/dental/ground_truth_dental_template.json`

## Phiên tiếp theo — làm ngay theo thứ tự
1. [GAP-003] `tests/unit/test_l8_error_handler.py` — unit tests `src/core/l8_error_handler.py` | P0.2.L8
2. [GAP-004] `tests/unit/test_l9a_pdf_export.py` — unit tests `src/core/l9a_pdf_export.py` | P0.2.L9a
3. [PILOT Đà Nẵng] Andy chạy `install.bat` tại phòng khám Đà Nẵng — cài đặt thật + ghi nhận feedback
4. [BENCH-002] Sau pilot: record 30-50 audio consultations → ground truth → CEER thật
