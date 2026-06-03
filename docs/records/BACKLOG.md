# BACKLOG.md — MediVoice VN
# v0.2.0 — Updated after design finalization
# Single source of truth cho tasks.

---

## IMMEDIATE — TRƯỚC KHI CODE

- [ ] **LEGAL-001** 🔴 Thuê luật sư VN (healthtech + data + AI) — trước khi launch
- [ ] **BENCH-001** 🟡 Benchmark PhoWhisper-small vs medium trên 10–20 audio thực tế từ Đà Nẵng
- [ ] **BENCH-002** 🟡 Đo CEER (Clinical Entity Error Rate): tên thuốc VN + liều + chẩn đoán

---

## PHASE 0 — MVP (6–8 tuần) — Sau khi IMMEDIATE xong

**Mục tiêu:** BS nói → Mẫu 15/BV1 → PDF → local save → BS approve
**Target user:** 5–10 BS phòng mạch tư Đà Nẵng + Sài Gòn
**Success:** 5 BS trả tiền trong tháng 3

### Core Pipeline
- [ ] **L0:** Audio normalize (16kHz mono, VAD)
- [ ] **L1a:** PhoWhisper streaming chunk 10s (với overlap 2s)
- [ ] **L1b:** Drug name correction engine (sau khi DRUG-DB-001 xong)
- [ ] **L1c:** Medical NER — PhoBERT + CRF (tên thuốc, liều, chẩn đoán)
- [ ] **L1d:** ICD-10-VN auto-lookup
- [ ] **L2:** Schema validation + confidence scoring
- [ ] **L3:** Route detection (lâm sàng là default Phase 0)
- [ ] **L4:** Human Gate UI (BS review + chỉnh sửa + approve)
- [ ] **L5:** PII scan (CCCD, SĐT, BHYT)
- [ ] **L6:** Generate Mẫu 15/BV1 (TT32/2023)
- [ ] **L7:** SQLite + WAL + Fernet encryption
- [ ] **L8:** Error handling + recovery
- [ ] **L9a:** PDF export (đơn thuốc + bệnh án)
- [ ] **L10:** Immutable audit log (timestamp + BS_ID + hash)

### App Shell (Tauri)
- [ ] **APP-001:** Tauri project setup (Windows + macOS)
- [ ] **APP-002:** Offline-first architecture
- [ ] **APP-003:** CCHN/GPHN input khi đăng ký + disclaimer
- [ ] **APP-004:** Doctor voice recording UI (bấm giữ để nói)
- [ ] **APP-005:** Draft review UI (L4 — BS chỉnh sửa trước khi approve)
- [ ] **APP-006:** PDF preview + print + manual Zalo share

### Data Model (VNeID-ready từ đầu)
- [ ] **DATA-001:** Patient schema (vneid_number nullable, bhyt_code nullable, legacy_id)
- [ ] **DATA-002:** Clinical record schema (Mẫu 15/BV1 fields)
- [ ] **DATA-003:** Audit log schema (BYT-sync-ready)
- [ ] **DATA-004:** Facility schema (byt_registration_number, province_code)

---

## PHASE 1 — COMPLETE PRODUCT (3–6 tháng sau Phase 0)

### Modules
- [ ] **M1:** Patient management (hồ sơ, lịch sử, CCCD camera scan)
- [ ] **M2:** Appointment booking (BN book online, QR check-in)
- [ ] **M3:** Thu chi đơn giản (voice log thu tiền, ghi chi phí, báo cáo)
- [ ] **M4:** Kết quả bên thứ 3 (BS upload PDF/ảnh kết quả XN/CĐHA)
- [ ] **M6:** Zalo Share SDK + OA API reminder (non-medical content)
- [ ] **M7:** VN Cloud sync (VNG/FPT/VNPT)

### Features
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
- [ ] **FID-VN-002:** `plugin_ngoai_tru_full.py` — Mẫu 15/BV1 đầy đủ (upgrade từ Phase 0 basic)
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

---

## DEFERRED (Không làm cho đến khi có signal rõ ràng)

- [ ] Native mobile app (iOS/Android) — quá tốn, web responsive đủ
- [ ] Multi-tenant SaaS infrastructure — Phase 2+
- [ ] Luật AI 134 conformity assessment detail — sau khi có revenue
- [ ] FPT/Viettel partnership — sau khi có 100+ users
- [ ] VNeID health platform integration — chờ BYT API public

---

*Updated: 2026-06-03 | v0.2.0*
