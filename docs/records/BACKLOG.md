# BACKLOG.md — MediVoice VN
# v0.7.2 — Updated 2026-06-07
# Single source of truth cho tasks.

---

## IMMEDIATE — TRƯỚC KHI LAUNCH

- [x] **LEGAL-001** ✅ Luật sư VN review xong — trước khi launch
- [x] **BENCH-001** ✅ Benchmark PhoWhisper trên 22 audio — WER 36–52%, T-005 20/22 PASS (2026-06-05)
- [x] **BENCH-002a** ✅ Semi-synthetic CEER: 3 regions VI-only, 15 files (2026-06-07 · v2 re-run 2026-06-11)
  - ✅ Andy ghi âm 40 files: HN/SG/CT/CA × 5 SC × 2 takes (CA dropped từ benchmark)
  - ✅ CA/BS4 dropped: PhoWhisper không handle code-switch EN/VN (WER 101%)
  - WER VI-only: SG 25.8% | CT 30.4% | HN 34.6%
  - **v2 engine re-run (2026-06-11):**
  - CEER Overall: Drug=0.989🔴 | Diag=0.667🔴 | Vital=0.272⚠️ | Fup=0.400🔴
  - CEER by region: CT (Drug=0.9 Diag=0.4 Vital=0.15) | HN (Drug=0.9 Diag=0.6 Vital=0.5) | SG (Drug=1.167🔴 Diag=1.0 Vital=0.167)
  - ⚠️ SG Drug=1.167 > 1.0: FP drugs detected (engine hallucinate trên ASR garbled output)
  - ✅ `tools/bench_ceer_semi.py` — CEER tool cho groundtruth_all.json format
  - **Root cause: ASR bottleneck — PhoWhisper mangling drug names → L1b không tìm được**
  - **Kết luận: BENCH-002b (pilot thật) + TRAIN-001 bắt buộc trước GO**
- [ ] **BENCH-002b** 🟡 CEER thật: audio pilot BS Đà Nẵng + ground truth labels (sau BENCH-002a)
  - Baseline lâm sàng synthetic (2026-06-08): 10/10 files | Vitals=0.033✅ Diag=0.1✅ Drug=0.9🔴
  - Template lâm sàng: `data/audio/ground_truth_lam_sang_template.json`
  - Template dental: `data/audio/dental/ground_truth_dental_template.json`
  - ✅ 57 clips BS thật đã transcribed (2026-06-12): `data/eval/ref_voice_transcripts_review.txt` + `.json`
  - 12+ chuyên khoa: tim mạch, hô hấp, GI, tiết niệu, nội tiết, nhi, sản khoa, da liễu, ung thư...
  - Drug mishear patterns thật: Amoxicillin→amosicilin, Metformin→mek fốc binh, Amlodipine→ong lau đi pin
  - ⏳ **Chờ Andy**: điền GT vào `data/eval/ref_voice_transcripts_review.txt` (Clip2+Clip3 ưu tiên)
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
- [x] **ONBOARD-001** ✅ Andy ký `docs/compliance/BS_ONBOARDING_CHECKLIST.md` với BS pilot — DONE
- [ ] **BENCH-002b** 🟡 Pilot thật: record 30-50 audio tại Đà Nẵng → CEER thật (sau BENCH-002a)
- [x] **LEGAL-001** ✅ Luật sư VN review DPA + tư vấn pháp lý — DONE

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
- [x] **FID-VN-006** ✅ Feature Intent Document L4 Correction Capture — Andy approved 2026-06-08
- [x] **L4-CORRECTION-001** ✅ [FID-VN-006] L4 Correction Capture — implicit supervision (2026-06-08)
  - `src/core/l4_correction_capture.py` — diff AI→BS, log to data/corrections/ JSONL
  - `scripts/analyze_corrections.py` — CLI alias suggestion tool (human review req)
  - `tests/unit/test_l4_correction_capture.py` — 14 tests PASS | Total: 366/366
  - Hook vào `src/api/main.py` approve_record() — best-effort, không block flow
  - `data/corrections/` vào .gitignore — không commit patient data
- [x] **CHATGPT-CORPUS-001** ✅ `docs/dev/CLINICAL_TEST_CORPUS_VN.md` v2.0 — 1210 dòng, by_disease + by_accent + by_drug_hard (2026-06-08)
- [x] **DRUG-ALIAS-001** ✅ Mở rộng alias map drug_db.json v0.3.0 — PhoWhisper phonetic variants cho 6 drugs: Glimepiride/Colchicine/Etoricoxib/VitaminB/Metformin/Omeprazole (2026-06-10)
- [ ] **DRUG-DB-002** 🟡 Mở rộng drug_db.json 118 → ~150 thuốc — bổ sung nhóm thiếu cho phòng mạch tư VN
  - Ưu tiên: Augmentin (Amox/Clav) · Bisoprolol · Tramadol · Empagliflozin · Sitagliptin · Folic acid · Vitamin D3 · Smecta · Phosphalugel · Celecoxib · Dapagliflozin · Indapamide
  - VietMed-NER drugs (313 entries) = OB/GYN context, overlap thấp → KHÔNG dùng
  - Source: TT07/2017 (243 OTC hoạt chất) + TT28/2024 + pilot prescription review
- [x] **CONS-002-IMPL** ✅ Sprint 1: `data/reference/drug_db_v200.json` v2.0.0 — 146 drugs + phonetic_variants (2026-06-10)
  - Basis: CONS-20260610-001 + CONS-20260610-002 CLOSED, Approach C APPROVED
  - Top 50 drugs: manual × 3 vùng = ~300-500 entries thủ công (high accuracy)
  - 150 drugs còn lại: 7 consensus phoneme rules (R1-R7) auto-generate
  - Fields mới: `phonetic_variants`, `valid_doses_mg[]`, `dose_range{min,max}`, `drug_class`, `compatible_diagnoses`
  - Depend: drug_db_v200 là prerequisite của CONS-002-SPRINT2, CONS-002-SPRINT6
- [x] **CONS-002-SPRINT2** ✅ DrugCorrectionEngine v2 — 4-layer fuzzy + Ambiguity Gate + Safety (2026-06-10)
  - `src/core/l1b_drug_correct.py` v2 · `fids/FID-VN-008.md` APPROVED
  - 35 new tests → 444/444 PASS
  - Layer 1: Exact alias match (current behavior)
  - Layer 2: Fuzzy match RapidFuzz fuzz.token_sort_ratio() cutoff ~85%
  - Layer 3: Phonetic prefix + context (session_context: diagnosis, drug_class)
  - Layer 4: Safety Rule Engine — hard dose validation per drug, ambiguity → flag không auto-commit
  - Depend: CONS-002-IMPL (phonetic_variants trong drug_db_v200)
- [ ] **VIETMED-FIX-001** 🟢 Fix `scripts/download_vietmed.py` — bỏ `trust_remote_code`, thêm HF_TOKEN auth
  - Lỗi hiện tại: `trust_remote_code is not supported anymore` + 401 Unauthorized
  - Dataset `doof-ferb/VietMed` cần HuggingFace login để download (~2.5GB, 16h audio MIT)
  - Dùng cho: TRAIN-001 PhoWhisper fine-tune (Phase 1 — không block Phase 0)
- [x] **BUG-K2** ✅ "một sáu lăm"=165 abbreviated SG tens fixed (2026-06-10) — `_WABR` pattern + `_WCOLLQ` extended. +1 test `test_sg_bp_colloquial_165_abbreviated` → 409/409 PASS
- [x] **BUG-N** ✅ chan_doan rỗng cho follow-up visits (2026-06-10) — BS nói "tái khám tăng huyết áp" mà không có "chẩn đoán:" keyword. Fix: `_RE_TAI_KHAM_DIAGNOSIS` checked trước `_RE_CHAN_DOAN_FALLBACK`. +4 tests → 408/408 PASS
- [~] **DATASET-001** 🔵 PARTIAL — Download P1 public datasets (VietMed family — MIT/Apache-2.0)
  - ✅ Downloaded: VietMed-NER (9K NER, ~30MB) · VietMed-Sum (106K, ~43MB) · VN Medical QA (9K, ~5MB) → `data/external/`
  - ✅ `scripts/download_vietmed.py` sẵn sàng — chạy overnight qua `scripts/overnight_run.bat`
  - ⏳ VietMed (~2.5GB ASR audio) → `data/vietmed/` | ViMedCSS (4GB) — để sau
  - Script: `python -X utf8 scripts/download_datasets.py` | Catalog: `docs/dev/DATA_CATALOG.md`
- [~] **DATASET-002** 🔵 PARTIAL — Phân tích VietMed-NER → map 18 entity types → MediVoice 5 types
  - ✅ `scripts/analyze_vietmed_ner.py` — entity mapping, vocab extracted, staging file
  - ✅ `data/reference/vietmed_drugs_raw.json` — 313 unique DRUGCHEMICAL entities
  - ✅ `data/reference/vietmed_ner_vocabulary.json` — top terms extracted
  - ⏳ `scripts/train_ner.py` — fine-tune training pipeline (gated FID-VN-007)
- [x] **SYNTHETIC-NER-001** ✅ Tạo 10,000 samples BIO-tagged VN outpatient NER (2026-06-07)
  - `scripts/generate_synthetic_ner.py` — 17 scenarios × 4 regions (expanded từ 7)
  - `data/synthetic_ner/` — train 7994 / val 1003 / test 1003 (JSONL, BIO format)
  - `tests/unit/test_synthetic_ner_pipeline.py` — 7 tests pipeline benchmark (395/395 PASS)
  - Hit rates: Drug 97-100% · Diagnosis 63-80% · Vital 63-77% · Tái khám 33-60%
  - 10 scenarios mới: viem_phe_quan · viem_xoang · di_ung_mui · viem_da_ruot · nhiem_trung_tiet_nieu
    thieu_mau · mat_ngu · tang_mo_mau · viem_ket_mac · viem_amidan
- [x] **NER-BUGFIX-004** ✅ chan_doan regex major fix (2026-06-09)
  - Fix: lookahead xử lý ". filler Kê" pattern, ICD codes, "bị/mắc" prefix, "gout" fallback
  - File: `src/core/l1c_ner.py` — _RE_CHAN_DOAN + _RE_CHAN_DOAN_FALLBACK
  - Verified: 10/10 test cases pass, 92/92 existing tests không bị break

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
- [ ] **TRAIN-001:** Fine-tune PhoWhisper trên VietMed (16h labeled MIT) + pilot audio (50–100h)
  - Datasets: `data/external/VietMed` + `data/external/ViMedCSS` + pilot audio
  - Target: WER 35–40% → <20% | Drug CEER 0.90 → <0.10
  - Cần: GPU/cloud VM (VNG/FPT) | FID-VN-007 trước khi implement
- [x] **TRAIN-002** ✅ Fine-tune PhoBERT+CRF NER trên synthetic 10K — HOÀN TẤT (2026-06-10)
  - Epoch 1: F1=**98.95%** P=98.98% R=98.91% | Epoch 2: F1=**98.73%** | Epoch 3: F1=**99.44%** ← BEST
  - Best model: `models/ner_phobert/best/` (512.8MB, checkpoint-3000) ✅
  - Entities: MEDICATION · DOSE · FREQUENCY · SYMPTOM · VITAL · FOLLOWUP
  - Datasets: `data/synthetic_ner/` (7994 train / 1003 val / 1003 test)
  - **Note:** Trained trên synthetic data — cần validate trên pilot audio thực trước khi dùng production
- [x] **FID-VN-009-IMPL** ✅ Hybrid NER [FID-VN-009] — DONE 2026-06-10
  - `src/core/l1c_phobert.py` — lazy load, confidence thresholds, bio_to_updates(), has_coverage_gap()
  - `src/core/l1c_ner.py` — extract_entities_hybrid() + _get_filled_fields() + _has_coverage_gap
  - `tests/unit/test_l1c_phobert_hybrid.py` — 29 tests → 473/473 PASS
  - PARALLEL + optional early-exit: trieu_chung+tai_kham+ly_do filled → skip PhoBERT
  - VITAL → meta["phobert_vital_detected"] only; MEDICATION ≥0.85; SYMPTOM ≥0.75
  - Default OFF (MEDIVOICE_PHOBERT_NER=false) — bật sau BENCH-002b GO criteria
- [x] **CONS-002-EVAL** ✅ Sprint 4: Evaluation dataset + eval script DrugCorrectionEngine v2 (2026-06-10)
  - `scripts/generate_drug_eval_dataset.py` → `data/eval/drug_correction_eval.json` (204 cases)
  - `scripts/eval_drug_correction.py` — 4 metrics: Drug Recall / Silent FP / Safety Catch / Phonetic
  - Categories: clean=90 / noisy=76 / dangerous=38
  - Results: Drug Recall=**99.5%** ✅ | Silent FP=**0.0%** ✅ | Safety=**92.1%** ✅ | Phonetic=**98.7%** ✅
  - **→ ✅ GO — all criteria met** (thresholds: ≥88% / ≤10% / ≥80% / ≥85%)
  - Known issues: "a zi thro my xin" Azithromycin FN · "metro"/"me tro" AMBIGUOUS miss (3 cases)
  - Distinction: silent FP (unflagged, dangerous) vs warned FP (LOW_CONFIDENCE, BS reviews → rejects)
- [ ] **CONS-002-SPRINT6** 🟢 Sprint 6: TTS Pilot — XTTS-v2 / F5-TTS Vietnamese drug corpus (CONDITIONAL-GO)
  - Prerequisite: CONS-002-IMPL done (phonetic_variants) + reference voices thu được từ pilot BS
  - Step 1: Generate 20 clips (5 câu × 4 voices) → BS evaluate → quyết GO/NO-GO full
  - Step 2 (nếu GO): 5000 câu × 4 voices = 20K clips overnight + noise augment
  - Test cả XTTS-v2 (thivux/XTTS-v2-vietnamse) và F5-TTS (nguyenthienhy/F5-TTS-Vietnamese)
  - Bridge CONS-001→002: dùng phonetic_variants làm TTS input text (KHÔNG dùng INN gốc)

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
