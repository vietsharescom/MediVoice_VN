# BACKLOG.md — MediVoice VN
# v0.3.0 — Updated 2026-06-04
# Single source of truth cho tasks.

---

## IMMEDIATE — TRƯỚC KHI LAUNCH

- [ ] **LEGAL-001** 🔴 Thuê luật sư VN (healthtech + data + AI) — trước khi launch
- [ ] **BENCH-001** 🟡 Benchmark PhoWhisper-small vs medium trên 10–20 audio thực tế từ Đà Nẵng
- [ ] **BENCH-002** 🟡 Đo CEER (Clinical Entity Error Rate): tên thuốc VN + liều + chẩn đoán

---

## PHASE 0 — MVP ✅ PIPELINE DONE — Còn lại: test thực tế + deploy

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

### App Shell ✅ DONE 2026-06-04 (FastAPI PWA thay Tauri)
- [x] **APP-001:** FastAPI app — /api/transcribe + approve + reject + pdf
- [x] **APP-002:** SQLite offline-first architecture
- [x] **APP-003:** CCHN input + disclaimer bắt buộc
- [x] **APP-004:** Doctor voice recording UI (MediaRecorder, hold to record)
- [x] **APP-005:** Draft review form (edit fields + approve/reject)
- [x] **APP-006:** PDF download Mẫu 15/BV-01

### Phase 0 Còn Lại
- [ ] **TEST-E2E-001** 🟡 End-to-end test với audio thực tế (cần BENCH-001 audio từ Đà Nẵng)
- [ ] **DEPLOY-001** 🟡 Package app để BS Đà Nẵng install (Windows + Python venv installer)
- [ ] **CONFIG-001** 🟢 Facility config UI (tên phòng khám, CCHN, khoa — file JSON)
- [ ] **DRUG-ALIAS-001** 🟢 Mở rộng alias map trong drug_db.json (thêm typo VN phổ biến)

---

## PHASE 1 — COMPLETE PRODUCT (3–6 tháng sau Phase 0)

### Modules
- [ ] **M1:** Patient management (hồ sơ, lịch sử, CCCD camera scan)
- [ ] **M2:** Appointment booking (BN book online, QR check-in)
- [ ] **M3:** Thu chi đơn giản (voice log thu tiền, ghi chi phí, báo cáo)
- [ ] **M4:** Kết quả bên thứ 3 (BS upload PDF/ảnh kết quả XN/CĐHA)
- [ ] **M6:** Zalo Share SDK + OA API reminder (non-medical content)
- [ ] **M7:** VN Cloud sync (VNG/FPT/VNPT)

### Architecture (học từ MediVoice_AI)
- [ ] **ARCH-001:** Cross-visit memory (SQLite last 5 visits per patient) — M1 prerequisite
- [ ] **ARCH-002:** AccountabilityTracker — AI vs Human decision log (Luật AI 134/2025)
- [ ] **ARCH-003:** RTM Engine live (rtm_engine.py) — replace static RTM.md
- [ ] **ARCH-004:** StateMachine formal — replace RecordStatus enum
- [ ] **ARCH-005:** MultiCritic + Simulator trong ValidationLayer (Phase 0 chỉ có Rule+Anomaly)

### Features — AI & Language
- [ ] **LANG-001:** MarianMT VI→EN option — output EN cho BS nước ngoài (BO-VN-003)
- [ ] **LANG-002:** Bilingual EN/VI output toggle — detect language, chọn template phù hợp
- [ ] **NER-PHOBERT-001:** Nâng L1c lên PhoBERT + CRF (thay rule-based) — sau TRAIN-001
- [ ] **KB-001:** FAISS KB y tế VN — ICD-10-VN terms, thuật ngữ siêu âm, tim mạch → hỗ trợ form mapping

### Features — CĐHA & Chuyên khoa (VN-FLOW-CDHA)
- [ ] **FID-VN-001:** Plugin CĐHA — báo cáo siêu âm (abdominal, thyroid, OB, vascular)
- [ ] **FID-VN-001b:** Plugin CĐHA — báo cáo X-quang, CT, MRI
- [ ] **FID-VN-001c:** Plugin CĐHA — báo cáo ECG/tim mạch
- [ ] **FID-VN-002:** Plugin Nha khoa — Mẫu 16/BV1 + sơ đồ răng
- [ ] **FID-VN-003:** Plugin Sản khoa — Mẫu 05/BV1

### Features — Workflow
- [ ] **STAFF-001:** Staff voice context (tiếp nhận BN — khác với doctor voice)
- [ ] **REPEAT-001:** Tái kê đơn cũ (copy đơn + điều chỉnh nhỏ)
- [ ] **DRUG-INTERACT-001:** Drug interaction check cơ bản
- [ ] **HL7-001:** HL7 v2 export (ADT/ORU)
- [ ] **SIGN-001:** Chữ ký số BS (TT13/2025)

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

- [ ] **FHIR-001:** FHIR R4 export (khi TT13/2025 thực sự enforce)
- [ ] **M5:** Referral partner management (chỉ track, không ghi tiền)
- [ ] **M8:** Plugin mở rộng (Tai mũi họng, Tim mạch, Sản khoa...)
- [ ] **M9:** HIS integration (BravoSoft, FPT.eHospital API)
- [ ] **CONFORM-001:** Conformity assessment (Luật AI 134/2025) — trước 01/09/2027
- [ ] **VNEID-001:** VNeID API integration (khi BYT có API)
- [ ] **BHYT-001:** BHYT eligibility check
- [ ] **BYT-SYNC-001:** BYT Central Registry sync

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
- [x] **CLAUDE.md** — thêm trigger words end/done/start/begin (2026-06-04)

---

## DEFERRED (Không làm cho đến khi có signal rõ ràng)

- [ ] Native mobile app (iOS/Android) — quá tốn, web responsive đủ
- [ ] Multi-tenant SaaS infrastructure — Phase 2+
- [ ] Luật AI 134 conformity assessment detail — sau khi có revenue
- [ ] FPT/Viettel partnership — sau khi có 100+ users
- [ ] VNeID health platform integration — chờ BYT API public

---

*Updated: 2026-06-04 | v0.3.0*
