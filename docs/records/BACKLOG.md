# BACKLOG.md — MediVoice VN
# v0.4.1 — Updated 2026-06-06
# Single source of truth cho tasks.

---

## IMMEDIATE — TRƯỚC KHI LAUNCH

- [ ] **LEGAL-001** 🔴 Thuê luật sư VN (healthtech + data + AI) — trước khi launch
- [x] **BENCH-001** ✅ Benchmark PhoWhisper trên 22 audio — WER 36–52%, T-005 20/22 PASS (2026-06-05)
- [ ] **BENCH-002** 🟡 Đo CEER thật: audio pilot thực tế BS nói + ground truth labels
  - Baseline lâm sàng synthetic (2026-06-08): 10/10 files | Vitals=0.033✅ Diag=0.1✅ Drug=0.9🔴
  - Template lâm sàng: `data/audio/ground_truth_lam_sang_template.json` (10 vùng miền, gTTS done)
  - Template dental: `data/audio/dental/ground_truth_dental_template.json` (Andy điền khi có audio nha khoa thật)
  - Tạo WAV: `python tools/gen_test_audio.py --input <template.json>`
  - Chạy CEER: `python -X utf8 tools/bench_ceer.py --full --gt <template.json>`
  - Full CEER thật: Andy record audio BS nói → điền ground truth → chạy bench
- [x] **GAP-002** ✅ Unit tests PII scan — tests/unit/test_pii_scan.py 27 tests PASS (2026-06-06)
- [x] **GAP-003** ✅ Unit tests L8 error handler — `tests/unit/test_l8_error_handler.py` 20 tests PASS (2026-06-08) | P0.2.L8
- [x] **GAP-004** ✅ Unit tests L9a PDF export — `tests/unit/test_l9a_pdf_export.py` 15 tests PASS (2026-06-08) | P0.2.L9a
- [x] **GAP-005** ✅ API integration tests — tests/integration/test_api.py 18 tests PASS (2026-06-06)
- [x] **FID-VN-004** ✅ Feature Intent Document VN-ROUTER-001 — Andy approved 2026-06-06
- [x] **VN-ROUTER-001** ✅ L6 branch: lam_sang→Mẫu15/BV-01 | cdha→SOAP — 232 tests PASS (2026-06-06)
- [x] **VN-NER-002** ✅ [FID-VN-005] VN word-to-number + L6 lam_sang dùng VN NER — 272 tests PASS (2026-06-07)
  - _normalize_vn_numbers() — PhoWhisper word-form → digits
  - generate_mau15_from_vn_ner() — MedicalEntities direct mapping
  - bench_ceer tc_001/tc_002: vital=True, followup=True

- [x] **DPA-SIGN-001** ✅ Andy ký `docs/compliance/DPA_TEMPLATE.md` với BS pilot Đà Nẵng (2026-06-08)
- [ ] **ONBOARD-001** 🔴 Andy ký `docs/compliance/BS_ONBOARDING_CHECKLIST.md` với từng BS pilot
- [ ] **BENCH-002** 🟡 Record 30-50 audio consultations tại Đà Nẵng + ground truth labels → CEER thật
- [ ] **LEGAL-001** 🔴 Thuê luật sư VN review DPA + tư vấn pháp lý trước launch thương mại

---

## PHASE 0 — MVP ✅ PIPELINE DONE — Còn lại: FID + VN-Router + Deploy

**Mục tiêu:** BS nói → Mẫu 15/BV-01 → PDF → local save → BS approve
**Target user:** 5–10 BS phòng mạch tư Đà Nẵng + Sài Gòn
**Success:** 5 BS trả tiền

### Core Pipeline ✅ DONE 2026-06-04
- [x] **L0:** Audio normalize (16kHz mono, VAD) — librosa + soundfile
- [x] **L1a:** PhoWhisper streaming chunk 10s (lazy-load, graceful degradation)
- [x] **L1b:** Drug name correction engine — alias map, n-gram matching
- [x] **L1c:** Medical NER rule-based — regex sinh hiệu, chẩn đoán, đơn thuốc
- [x] **L1d:** ICD-10-VN auto-lookup — substring search 15,026 mã
- [x] **L2:** Schema validation + confidence scoring — weighted fields
- [x] **L3:** Route detection — lam_sang default, CDHA/nha_khoa keywords
- [x] **L4:** Human Gate — state machine PENDING_REVIEW→APPROVED/REJECTED
- [x] **L5:** PII scan — CCCD, SĐT, BHYT, email regex (NĐ13/2023)
- [x] **L6:** Generate Mẫu 15/BV-01 (TT32/2023)
- [x] **L7:** SQLite + WAL + Fernet encryption
- [x] **L8:** Error handling + recovery — @with_recovery, @safe_log
- [x] **L9a:** PDF export (Mẫu 15/BV-01 ReportLab, disclaimer bắt buộc)
- [x] **L10:** Immutable audit log (SHA-256 hash chain, append-only)

### Data Models ✅ DONE 2026-06-04
- [x] **DATA-001:** Patient schema (Pydantic v2, VNeID-ready)
- [x] **DATA-002:** Clinical record schema + RecordStatus enum
- [x] **DATA-003:** Audit log schema (hash chain, BYT-sync-ready)
- [x] **DATA-004:** Facility schema (byt_registration_number, province_code)

### App Shell ✅ DONE 2026-06-04 (FastAPI PWA)
- [x] **APP-001:** FastAPI app — /api/transcribe + approve + reject + pdf
- [x] **APP-002:** SQLite offline-first architecture
- [x] **APP-003:** CCHN input + disclaimer bắt buộc
- [x] **APP-004:** Doctor voice recording UI (MediaRecorder, hold to record)
- [x] **APP-005:** Draft review form (edit fields + approve/reject)
- [x] **APP-006:** PDF download Mẫu 15/BV-01

### Phase 0 Còn Lại
- [x] **BENCH-001** ✅ T-005 20/22 PASS | T-007 10/10 PASS | WER 29–52% | SOAP 20/20 (2026-06-05)
- [x] **FID-VN-004** ✅ Feature Intent Document cho VN-ROUTER-001 (2026-06-06)
- [x] **VN-ROUTER-001** ✅ L6 branch: NER entities → BenhAnNgoaiTru (2026-06-06)
- [x] **BENCH-002-BASELINE** ✅ Lâm sàng synthetic 10 vùng miền — Vitals 0.033, Diag 0.1 (2026-06-08)
  - `tools/gen_test_audio.py` — tạo WAV từ JSON template
  - `bench_ceer.py --gt` flag — whitelist filtering
  - `data/audio/dental/` — dental audio tách riêng
- [ ] **TEST-E2E-001** 🟡 End-to-end test full pipeline với audio thực tế (sau DEPLOY-001)
- [x] **DEPLOY-001** ✅ Windows venv installer cho BS Đà Nẵng (2026-06-08)
  - `install.bat` — one-click installer (Python check + venv + pip + config)
  - `start.bat` — daily launcher (auto-open browser)
  - `scripts/check_env.py` — pre-flight checks (Python, disk, packages, port)
  - `scripts/setup_facility.py` — interactive facility config wizard
  - `config/facility_config.json` — facility config template
  - `requirements-prod.txt` — production deps (no dev tools)
  - `tests/unit/test_check_env.py` — 15 tests PASS | Total: 287/287
- [x] **CONFIG-001** ✅ Facility config JSON (config/facility_config.json + setup_facility.py) (2026-06-08)
- [x] **VN-NER-003** ✅ Real-world NER bug fix A-01/A-02/A-03 — 11 bugs fixed (352 tests, 2026-06-08)
  - chan_doan boundary · temp decimal · self-med filter · ml→mg · ICD prefix strip
  - Iron context guard · BP intermediate text · BP "tri" alias · ly_do symptom filter · tai_kham admin strip
- [x] **CORPUS-001** ✅ CLINICAL_TEST_CORPUS_VN.md v2.0 — terminology fixes ("tình trạng", "đau khi nuốt") (2026-06-08)
- [x] **ADAPTIVE-001** ✅ `docs/records/ADAPTIVE_LEARNING_ARCHITECTURE.md` — 3-tier learning design (2026-06-08)
- [ ] **CHATGPT-CORPUS-001** 🟡 Andy sử dụng `docs/dev/CHATGPT_CORPUS_PROMPT.md` v2.0 → ChatGPT/Grok → 41 corpus scripts → BS review → gửi lại Claude update CLINICAL_TEST_CORPUS_VN.md (PA-007)
- [ ] **DRUG-ALIAS-001** 🟢 Mở rộng alias map trong drug_db.json (thêm typo VN phổ biến)

---

## PHASE 1 — COMPLETE PRODUCT (3–6 tháng sau Phase 0)

### Modules
- [ ] **M1:** Patient management đầy đủ (hồ sơ, lịch sử, CCCD scan, QR thẻ BN)
- [ ] **M2:** Booking engine (7 states + buffer + waitlist + D-1/H-2/H-15p reminder)
- [ ] **M3:** Thu chi đầy đủ (voice log, báo cáo, xuất Excel)
- [ ] **M4:** Email auto-processor (3 điều kiện + quarantine) + kết quả XN
- [ ] **M5:** Referral 2 chiều + deal % + commission dashboard (Gói 3)
- [ ] **M6:** Zalo OA (text non-medical) + Email routing (file y tế) + Post-care CRM
- [ ] **M7:** VN Cloud sync (VNG/FPT/VNPT)

### Architecture
- [ ] **QUEUE-001:** Queue Management System + TTS loa đọc tên
- [ ] **SCREEN-001:** Staff Screen riêng (Mode B) — tiếp nhận + thu ngân gộp
- [ ] **DOCTOR-001:** Doctor Pre-visit Briefing (tóm tắt BN trước ca)
- [ ] **STAFF-GATE-001:** Staff Confirm Gate (checklist đóng ca BN)
- [ ] **PARTNER-001:** Partner comm channel (Email CHÍNH THỨC + Zalo optional)
- [ ] **WEBSITE-001:** Website widget embed + REST API booking (Gói 2+)
- [ ] **BOOKING-001:** Booking engine chuẩn (7 states + reminder flow)
- [ ] **AFTERCARE-001:** Post-care CRM D+2/D+4/D+5/D+7
- [ ] **STAFF-001:** Staff voice context (tiếp nhận BN — khác với doctor voice)

### Plugins
- [ ] **FID-VN-001:** Plugin CĐHA — báo cáo siêu âm (abdominal, thyroid, OB, vascular)
- [ ] **FID-VN-001b:** Plugin CĐHA — X-quang, CT, MRI
- [ ] **FID-VN-002:** Plugin Nha khoa — Mẫu 16/BV1 + sơ đồ răng
- [ ] **FID-VN-003:** Plugin Sản khoa — Mẫu 05/BV1

### Features
- [ ] **REPEAT-001:** Tái kê đơn cũ (copy đơn + điều chỉnh nhỏ)
- [ ] **DRUG-INTERACT-001:** Drug interaction check cơ bản
- [ ] **EMAIL-PROC-001:** Email auto-processor inbound (M4)
- [ ] **REFERRAL-RETEST-001:** Referral retest flow (kết quả lần 1 không đạt)
- [ ] **ACCOUNT-API-001:** Kế toán export API (MISA/Fast CSV + REST)

### Training
- [ ] **TRAIN-001:** Fine-tune PhoWhisper trên 50–100h audio thực tế từ pilot
- [ ] **TRAIN-002:** Fine-tune NER trên VN medical entities từ pilot data

---

## PHASE 1B — PLUGINS CHUYÊN KHOA

- [ ] **FID-VN-001:** `plugin_cdha.py` — báo cáo siêu âm/X-quang
- [ ] **FID-VN-002:** `plugin_ngoai_tru_full.py` — Mẫu 15/BV1 đầy đủ (upgrade Phase 0 basic)
- [ ] **FID-VN-003:** `plugin_nha_khoa.py` — Mẫu 16/BV1

---

## PHASE 2 — KHI CÓ REVENUE (2027+)

- [ ] **TT13-001:** Chữ ký số bác sĩ (TT13/2025 deadline 31/12/2026)
- [ ] **HL7-001:** HL7 v2 export (ADT/ORU)
- [ ] **FHIR-001:** FHIR R4 export (khi TT13/2025 thực sự enforce)
- [ ] **M9:** HIS integration (BravoSoft, FPT.eHospital API)
- [ ] **AUDIT-EXPORT-001:** Audit log export chuẩn cho BYT thanh tra
- [ ] **CONFORM-001:** Conformity assessment (Luật AI 134/2025) — trước 01/09/2027
- [ ] **M5:** Referral partner management đầy đủ (Gói 3)
- [ ] **M8:** Plugin mở rộng (Tai mũi họng, Tim mạch, Sản khoa...)
- [ ] **VNEID-001:** VNeID API integration (khi BYT có API)
- [ ] **BHYT-001:** BHYT eligibility check
- [ ] **BYT-SYNC-001:** BYT Central Registry sync

---

## DESIGN DOCS (Phiên 2026-06-06)
- [x] **DESIGN-001** ✅ Master Design Report v1.1 (2026-06-06) — docs/records/DESIGN_REPORT_v1.1_20260606.md
  Bao gồm: Queue QMS, Mode A/B/C, 4 màn hình, Doctor Briefing, Staff Gate,
  Referral 2 chiều + Retest, M5 Commission, Post-care CRM, Booking Engine chuẩn,
  Email auto-processor, Data compliance 3 lớp, Integration Gateway, 17+ kết nối

---

## DONE

- [x] Research thị trường VN (~15h, 2026-06-02)
- [x] CLAUDE.md v0.2.0 — 2 layers, 3 gói, 9 modules, mobile-first
- [x] VISION.md v0.2.0, BRS.md v0.2.0
- [x] BACKLOG.md, DECISIONS.md v0.2.0 (32 decisions locked)
- [x] Third-party review: ChatGPT + Grok + Copilot (A+B+C+D) — 2026-06-03
- [x] Design finalization (2 layers + 3 gói + 9 modules + mobile-first)
- [x] Data reference: ICD-10-VN (15,026) + TT23 (9,124) + drug_db (110) + Mẫu 15/BV-01
- [x] Enforcement: 61 tests + pre-commit hooks + pipeline stubs L0–L10
- [x] ISO_VN framework: CONSTITUTION + governance code + risk engine
- [x] DRUG-DB-001: drug_db.json 110 thuốc (TT07/2017 + TT28/2024) ✅
- [x] ICD-001: icd10vn.json 15,026 mã (HL7 Vietnam) ✅
- [x] PROJECT_KICKOFF S1–S9 done (S10 Andy ký sau)
- [x] Git init + 6 commits + pushed to GitHub
- [x] **Phase 0 pipeline L0→L10** — toàn bộ implement (2026-06-04)
- [x] **Data models** — Patient, ClinicalRecord, Facility, AuditEntry (Pydantic v2) (2026-06-04)
- [x] **FastAPI PWA** — voice recording + draft review + approve/reject + PDF (2026-06-04)
- [x] **CHANGELOG v0.3.0** — 16 feat entries (2026-06-04)
- [x] **Canada pipeline port** — L0→L9, MarianMT, FAISS KB (2026-06-05)
- [x] **BENCH-001** — T-005 20/22 PASS, T-007 10/10 PASS (2026-06-05)
- [x] **DESIGN_REPORT v1.1** — Master design document 21 sections (2026-06-06)

---

## DEFERRED (Không làm cho đến khi có signal rõ ràng)

- [ ] Native mobile app (iOS/Android) — quá tốn, web responsive đủ
- [ ] Multi-tenant SaaS infrastructure — Phase 2+
- [ ] Luật AI 134 conformity assessment detail — sau khi có revenue
- [ ] FPT/Viettel partnership — sau khi có 100+ users
- [ ] VNeID health platform integration — chờ BYT API public
- [ ] IVR Phone booking — Phase 3
- [ ] WhatsApp/Facebook channel — Phase 3

---

*Updated: 2026-06-08 | v0.6.3*
