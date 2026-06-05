# CHANGELOG — MediVoice VN
# ISO/IEC 42001:2023 Clause 10.2

## [v0.7.0] — 2026-06-08 — L4 Correction Capture — FID-VN-006 (366 tests total)

### Feature: L4 Correction Capture (TIER 2 Adaptive Learning)
- feat(l4_correction_capture): `src/core/l4_correction_capture.py` — diff AI vs BS form_data, log JSONL to `data/corrections/{clinic_id}/`
- feat(main): hook `capture()` into `approve_record()` — best-effort, non-blocking
- feat(analyze_corrections): `scripts/analyze_corrections.py` — CLI tool for drug alias suggestions (human review required)
- feat(gitignore): `data/corrections/` excluded — patient data must not be committed
- feat(fids): `fids/FID-VN-006.md` — Feature Intent Document approved by Andy

### Tests
- test(l4_correction_capture): `tests/unit/test_l4_correction_capture.py` — 14 tests, AC-001→AC-005 all PASS
- Stats: **366/366 tests PASS** (+14) | bandit 0 HIGH/MEDIUM

---

## [v0.6.3] — 2026-06-08 — Real-world NER+ICD fix A-03 (352 tests total)

### NER Fixes (A-03 Tăng huyết áp)
- fix(l1c_ner): `_RE_HA_SYSTOLIC` — allow up to 40 chars between "huyết áp" and digits (fixes "hôm nay là 170/100")
- fix(l1c_ner): `_RE_BP_WORDS` — add "tri" as alias for "trên" (PhoWhisper phonetic confusion)
- fix(l1c_ner): `ly_do` fallback — skip "nghề nghiệp X" prefix pattern
- fix(l1c_ner): `ly_do` — require symptom keyword in fallback capture (filters admin text)
- fix(l1c_ner): `tai_kham` — strip trailing admin instructions, only keep "hoặc/nếu/sớm hơn" clauses
- fix(l1c_ner): Iron (Ferrous) context guard — require anemia context (thiếu máu/ferritin etc.) to prevent false positive from Losartan phonetic explosion

### Stats: **352/352 tests PASS** (+5 from A-03 NER regression tests) | bandit 0 HIGH/MEDIUM

---

## [v0.6.2] — 2026-06-08 — Real-world NER+ICD fix A-01/A-02 (347 tests total)

### NER Fixes (A-01 Viêm họng cấp)
- fix(l1c_ner): `chan_doan` boundary overflow — stop capture at "điều trị/kê đơn/tái khám" keywords
- fix(l1c_ner): Temperature decimal without "phẩy" — "ba mươi bảy tám" → 37.8 (not 37.0)
- fix(l1c_ner): Patient self-medication filter — "bệnh nhân tự uống X" → excluded from don_thuoc
- fix(l1c_ner): Drug unit ml→mg correction for oral route (PhoWhisper: "miligam"→"ml")

### ICD-10 Fix (A-02 Viêm loét dạ dày)
- fix(l1d_icd_lookup): `auto_lookup()` progressive prefix matching — drop up to 3 trailing ASR noise words and retry search

### Tests
- test(ner_bugs): `tests/unit/test_l1c_ner_bugs.py` expanded to 30 tests
  - TestChanDoanBoundary (5), TestTemperatureDecimalWithoutPhay (6), TestPatientSelfMedicationFilter (5)
  - TestDrugUnitMlToMg (3), TestLyDoExtraction (4), TestNgungFilter (3), TestICD10AutoLookup (4)

### Docs
- docs: `docs/records/ADAPTIVE_LEARNING_ARCHITECTURE.md` — 3-tier adaptive learning design
  (TIER 1: PhoWhisper-medium upgrade, TIER 2: L4 Correction Capture, TIER 3: LoRA fine-tune)
- docs: `docs/dev/CHATGPT_CORPUS_PROMPT.md` v2.0 — 41-case corpus prompt (Groups A-H) for ChatGPT/Grok regeneration
- docs: `docs/dev/CLINICAL_TEST_CORPUS_VN.md` v2.0 — VN terminology corrections ("tình trạng" not "tổng trạng", "đau khi nuốt" not "đau tăng khi nuốt")

### Stats: **347/347 tests PASS** (+25 new NER regression tests) | bandit 0 HIGH/MEDIUM

---

## [v0.6.1] — 2026-06-08 — GAP-003 + GAP-004: Unit tests L8 + L9a (322 tests total)

### Tests
- test(l8): `tests/unit/test_l8_error_handler.py` — 20 tests
  - TestPipelineErrorCode: enum values + str subclass
  - TestPipelineError: constructor, code/layer attrs, message format
  - TestWithRecovery: happy path, PipelineError re-raised, callable fallback, static fallback, no-fallback→PipelineError, logging, zero fallback, functools.wraps
  - TestSafeLog: happy path, exception swallowed→None, critical logged, functools.wraps, PipelineError swallowed
- test(l9a): `tests/unit/test_l9a_pdf_export.py` — 15 tests
  - TestExportPdfFileCreation: str path, file exists, BA_ prefix, record_id in name, correct dir, mkdir parents, .pdf ext, nonempty, valid %PDF header
  - TestRecordIdEdgeCases: empty→UNKNOWN, short id
  - TestDrugSection: no drugs, with drugs + tai_kham, multiple drugs
  - TestDefaultOutputDir: monkeypatch _EXPORTS_DIR

### Stats: **322/322 tests PASS** (+35 new) | bandit 0 HIGH/MEDIUM

---

## [v0.6.0] — 2026-06-08 — CT-005 DEPLOY-001: Windows venv installer cho BS Đà Nẵng

### Deploy
- feat(deploy): `install.bat` — 6-step Windows installer (Python check → venv → pip → data → config → pre-flight)
- feat(deploy): `start.bat` — daily launcher (auto-detect port → open browser → run app)
- feat(deploy): `scripts/check_env.py` — pre-flight checks: Python version, disk space, packages, model cache, reference data, port availability
- feat(deploy): `scripts/setup_facility.py` — interactive facility config wizard (tên PK, địa chỉ, BS, CCHN, port)
- feat(deploy): `config/facility_config.json` — facility config template (province_code, byt_registration_number, host, port)
- feat(deploy): `requirements-prod.txt` — production deps only (no pytest/dev tools)

### Tests
- test(deploy): `tests/unit/test_check_env.py` — 15 tests covering all check_env functions
  - TestCheckPython: version detection + MIN_PYTHON threshold
  - TestCheckDisk: disk usage mock (patch check_env.shutil.disk_usage as tuple)
  - TestCheckPackages: import mock
  - TestCheckReferenceData: tmp_path with REQUIRED_DATA override
  - TestCheckPort: real socket binding
  - TestCheckFacilityConfig: JSON valid/missing/malformed
  - TestRunAll: all-pass + one-fail

### Stats: **287/287 tests PASS** (+15 new) | bandit 0 HIGH/MEDIUM

---

## [v0.5.3] — 2026-06-08 — CT-007: Followup CEER 0.7→0.1 (tai_kham regex extended)

### NER Fix
- fix(l1c_ner): `_RE_TAI_KHAM` extended to capture optional trailing context after time unit
  - Adds group(3) `([^.!?\n]*)` — captures "kèm điện tâm đồ", "xét nghiệm axit uric", "nếu không đỡ" etc.
  - Removes "Sau" prefix from output (GT format: "2 tuần" not "Sau 2 tuần")
  - Output: `f"{N} {unit} {extra}".strip()` — includes all context up to sentence boundary
- data: `data/audio/ground_truth_lam_sang_template.json` — simplify aspirational GT entries
  - nghe_an tai_kham: "1 tháng + HbA1c" → "1 tháng" (transcript không đề cập HbA1c)
  - kien_giang tai_kham: "1 tháng + đường huyết + creatinin" → "1 tháng" (transcript không đề cập)
  - binh_dinh: "a xít u rích" (PhoWhisper) ≠ "axit uric" (GT) — documented as TRAIN-001 dependency

### Benchmark BENCH-002 — Followup CEER improved
- Followup CEER: **0.7🔴 → 0.1✅** (target <0.3)
  8/10 pass | 1 fail = binh_dinh (TRAIN-001 phonetic: "a xít u rích" ≠ "axit uric")
- All other CEER unchanged: Vitals=0.033✅, Diag=0.1✅, Drug=0.9🔴(TRAIN-001)

### Stats: 272/272 tests PASS | bandit 0 HIGH/MEDIUM

---

## [v0.5.2] — 2026-06-08 — BENCH-002 lam_sang baseline + tools + data organization

### Tools
- feat(tools): `tools/gen_test_audio.py` — tạo WAV từ JSON ground_truth template (gTTS → 16kHz mono)
  - `--input` chỉ file JSON, `--force` ghi đè, `--dry-run` preview
- fix(tools): `tools/bench_ceer.py` — thêm `--gt` flag + whitelist filtering
  - Khi dùng `--gt`, chỉ scan/transcribe files listed trong GT template (bỏ scan toàn folder)
  - Fix AUDIO_TOO_LONG: rút ngắn 3 transcript (Huế/Nghệ An/Kiên Giang) về < 28 giây

### Data
- data: `data/audio/ground_truth_lam_sang_template.json` — 10 ca lâm sàng × 10 vùng miền VN
  Hà Nội, Hải Phòng, Nghệ An, Huế, Quảng Nam, Bình Định, Phú Yên, Sài Gòn, Tiền Giang, Kiên Giang
  Mỗi ca: ground truth đầy đủ (drugs, chan_doan, vitals, tai_kham) + accent_risk notes
- data: `data/audio/dental/ground_truth_dental_template.json` — 10 ca nha khoa điền đầy đủ chan_doan
- data: dental audio → `data/audio/dental/` (24 WAV + 1 JSON tách khỏi lâm sàng)
- data: xóa 22 " - Copy.wav" duplicate files
- data: 10 `lam_sang_*.wav` generated (gTTS, 16kHz mono, 25-28s mỗi file)

### Benchmark BENCH-002 — Baseline lâm sàng vùng miền
- bench: 10/10 files processed (fix AUDIO_TOO_LONG cho Huế/Nghệ An/Kiên Giang)
  Vitals CEER:    0.033 ✅  (near-perfect — NER vitals hoạt động tốt)
  Diagnosis CEER: 0.1   ✅  (~90% chan_doan đúng)
  Drug CEER:      0.9   🔴  (cần TRAIN-001 — drug NER yếu trên gTTS audio)
  Follow-up CEER: 0.7   🔴  (cần TRAIN-001)
- Report: `data/audio/BENCH002_ceer_results.json`

### Stats: 272/272 tests PASS (không thay đổi — tooling/data only)

## [v0.5.1] — 2026-06-07 — VN-NER-002: VN word-to-number + L6 lam_sang dùng VN NER [FID-VN-005]

### Core fix (vital signs extraction from PhoWhisper output)
- feat(L1c): `_normalize_vn_numbers()` — VN word-form numbers → Arabic digits before NER regex
  - BP: "một trăm ba mươi trên chín mươi" → "130/90" ✅
  - Decimal: "ba mươi tám phẩy năm" → "38.5", "ba mươi tám rưỡi" → "38.5" ✅
  - Tens: "tám mươi" → "80", "bảy mươi lăm" → "75" ✅
  - Shorthand: "tám lăm" → "85" (spoken shorthand for 85) ✅
  - Units: "một tuần" → "1 tuần", "ba ngày" → "3 ngày", "năm miligam" → "5 miligam" ✅
- feat(L6): `generate_mau15_from_vn_ner()` — maps MedicalEntities (VN dataclass) directly
  replaces Canada NEREntity bridge for lam_sang route (FID-VN-004 interim)
- feat(L6): `l6_agent.py` lam_sang path now uses original VI text → l1c_ner → VN NER
  root cause fix: was using processed_text (MarianMT output) → Canada NER → 0% vital coverage
- test: `tests/unit/test_l1c_vn_numbers.py` — 40 tests: _vn_to_int, _normalize_vn_numbers,
  full transcript acceptance criteria (TC-001, TC-002, TC-003)
- bench: `bench_ceer.py --partial` tc_001: vital=True followup=True ✅
          `bench_ceer.py --partial` tc_002: vital=True followup=True ✅

### Root cause fixed (FID-VN-005 §WHY)
PhoWhisper outputs word-form numbers ("tám mươi") — l1c_ner regex required `\d{2,3}` digits.
l6_agent lam_sang was using `processed_text` (MarianMT, mixed EN/VI) + Canada NER → silent fail.
Fix: normalize VN numbers first, then use original VI text + VN NER directly.

### Stats: 232 → 272 tests (+40 new)

## [v0.5.0] — 2026-06-06 — VN-ROUTER-001 DONE [FID-VN-004]

### Core feature (Phase 0 complete)
- feat(L6): VN-ROUTER-001 — L6 branch NER→Mẫu15/BV-01 [FID-VN-004]
  lam_sang route: NER entities → Mẫu 15/BV-01 directly (no SOAP)
  cdha/nha_khoa: preserved Canada SOAP path
- feat(L3): detect_vn_route() in l3_routing.py — lam_sang/cdha/nha_khoa from VI text
- feat(L6): l6_mau15_generator.py — generate_mau15() reusing l6_generate_form
- test: tests/unit/test_vn_router.py — 22 tests (AC-001..006 + 14 route detection tests)

### Stats: 210 → 232 tests (+22 new)

## [v0.4.5] — 2026-06-06 — PENDING_REQUESTS system + GAP-002/005 closed + ISO compliance docs

### Tests (165 → 210 PASS)
- feat(test): tests/unit/test_pii_scan.py — 27 tests, GAP-002 CLOSED
  Covers: CCCD/CMND/SDT/BHYT/EMAIL detection, mask_pii, scan_form_data edge cases
- feat(test): tests/integration/test_api.py — 18 tests, GAP-005 CLOSED
  Covers: health endpoint, transcribe, approve/reject, PDF, feedback, L4 protection

### PENDING_REQUESTS tracking system
- feat(process): docs/records/PENDING_REQUESTS.md — tracks Andy actions + Claude todos
  iso_audit.py now shows pending items at session start with full detail
- feat(ci): iso_audit.py — check_pending_requests() added to doc sync check
- docs: CLAUDE.md — Step C added (read PENDING_REQUESTS), BƯỚC 2 added to report

### ISO Compliance docs (3 new)
- feat(docs): DPA_TEMPLATE.md (DS-VN-COM-014) — NĐ13/2023 data processing agreement
- feat(docs): INCIDENT_RESPONSE_PLAN.md (DS-VN-COM-015) — ISO 42001 Cl.8.5 + 72h breach
- feat(docs): BS_ONBOARDING_CHECKLIST.md (DS-VN-COM-016) — ISO 9001 Cl.7.2 training record

### Other
- docs: RTM.md — GAP-002 + GAP-005 marked CLOSED
- docs: BACKLOG.md — DPA-SIGN-001, ONBOARD-001, BENCH-002 added to IMMEDIATE

## [v0.4.4] — 2026-06-06 — Automated ISO audit cadence + RAG memory timing

### Process automation
- feat(ci): docs/records/audit_schedule.json — session counter (auto-managed)
- feat(ci): scripts/iso_audit.py v2.0 — full rewrite with:
    --weekly: ISO 9001:2015 Cl.9.1.1 + 42001:2023 Cl.9.1 + Cl.6.1.2 specific checks
    --quality: ISO/IEC 25010 product quality checks
    --increment-session: session close counter → triggers weekly at session 7
    session 7 popup: automatic banner + weekly audit reminder
- docs: CLAUDE.md — close protocol: python iso_audit.py --increment-session added
- docs: CLAUDE.md — 5-tier memory with timing estimates (Tier 1: ~30-45s, 16% context)
- docs: QUALITY_AUDIT_TEMPLATE.md — explicit ISO clause mapping per section

## [v0.4.3] — 2026-06-06 — AI Memory + Multi-AI Consultation System

### Process & Templates (no code change to pipeline)
- feat(memory): docs/dev/CONFUSION_PATTERNS.md — 25 patterns Claude hay nhầm, Tầng 4 memory
- feat(ci): docs/dev/CONSULTATION_TEMPLATE.md — multi-AI consultation workflow + synthesis template
- feat(ci): docs/dev/QUALITY_AUDIT_TEMPLATE.md — ISO/IEC 25010 product quality audit template
- feat(ci): docs/records/consultations/ folder — lưu consultation history
- feat(ci): scripts/iso_audit.py --quality flag — product quality audit tách riêng khỏi doc sync
- docs: CLAUDE.md — 5-tier memory architecture + consultation trigger rules
- docs: IMPROVEMENT_PROCESS.md v1.1 — consultation workflow + ISO audit cadence chuẩn

## [v0.4.2] — 2026-06-06 — ISO Continuous Improvement System

### Process (no code change to pipeline)
- feat(ci): scripts/iso_audit.py — auto ISO health check, runs every session Step D
  Checks: tests, RTM CRITICAL gaps, BACKLOG IMMEDIATE, last session, doc consistency, NCs, DESIGN_REPORT
- feat(docs): IMPROVEMENT_PROCESS.md (DS-VN-COM-013) — quy trình cải tiến liên tục ISO 9001 Cl.10.3
  Covers: where rules live, how to record ideas, update cadence, auto-audit setup, zero-tolerance list
- feat(docs): CLAUDE.md — add Step D (iso_audit.py) to SESSION PROTOCOL
  Add CONTINUOUS IMPROVEMENT compact summary section
  Add IMPROVEMENT_PROCESS.md to document table

## [v0.4.1] — 2026-06-06 — Master Design Review + DESIGN_REPORT v1.1

### Design (no code change)
- docs: DESIGN_REPORT_v1.1_20260606.md — Master design document 21 sections, 700+ dòng
  Bao gồm: Queue QMS, Mode A/B/C, 4 screens, Doctor Pre-visit Briefing, Staff Confirm Gate,
  Referral 2 chiều + Retest, M5 Commission 2 chiều, Post-care CRM D+2/D+4/D+7,
  Booking Engine 7 states + buffer + waitlist, Email auto-processor 3 điều kiện,
  Data compliance 3 lớp, Integration Gateway adapter pattern, 17+ kết nối thiết bị

### Docs updated (consistency với DESIGN_REPORT)
- docs: CLAUDE.md v0.4.1 — pipeline L6 branch đúng, design decisions compact, DESIGN_REPORT ref
- docs: DECISIONS.md v0.3.0 — 15 ADR mới từ design review session 2026-06-06
- docs: BACKLOG.md v0.4.1 — FID-VN-004 thêm vào IMMEDIATE, DESIGN-001 done
- docs: LAST_SESSION.md — session 2026-06-06 ghi nhận

### Architecture decisions (no code change)
- decision: L6 branch tại NER entities, không qua SOAP cho lam_sang
- decision: Queue Management System + TTS loa
- decision: 3 operating modes (A/B/C) + 4 screens
- decision: Email = file y tế | Zalo = text non-medical (bắt buộc)
- decision: Partner comm = Email primary (bí mật), Zalo optional

## [v0.4.0] — 2026-06-05 — Canada pipeline port + BENCH-001 complete

### Pipeline (Canada port — không sửa)
- feat(pipeline): copy Canada handlers L0→L9 vào src/pipeline/ (l1_semantic, l2_enforcer, l3_routing, l4_authority, l5_policy, l6_agent, l6_soap_generator, l7_memory, l8_recovery, l9_response, l10_observability)
- feat(pipeline): l1b_translation.py (MarianMT VI→EN) — kích hoạt nội bộ cho NER
- feat(models): phobert_ner.py, clinical_kb.py, qwen_reasoning.py, _phobert_crf.py từ Canada
- feat(models): llm_adapter.py, state_machine.py, stage_result.py, exceptions.py từ Canada
- feat(data): data/kb/ — chunks.json + faiss_index.bin + guidelines.json (Clinical KB)
- feat(data): data/audio/ — 22 WAV test files (path chuẩn theo Canada)

### Tools
- feat(tools): tools/eval_phowhisper.py — T-007 benchmark (Canada, không sửa)
- feat(tools): tools/run_test_audio.py — T-005 pipeline test (Canada, không sửa)
- feat(tools): tools/record_test_audio.py — interactive recording
- feat(tools): tools/partial_ceer.py — partial CEER measurement

### Benchmark Results (BENCH-001)
- T-007: 10/10 PASS | WER 36–52% | RTF ~0.5x (3s/file)
- T-005: 20/22 PASS (91%) | 20/20 VI detected | 20/20 SOAP S/O/A/P
- Partial CEER: 0% → revealed drug_db aliases missing + NER patterns rigid
- CEER fixed via Canada pipeline (MarianMT + l6_soap_generator)

### ISO Docs
- docs: DECISIONS.md — 4 ADR mới (Canada pipeline, MarianMT, SOAP/CĐHA, FAISS KB)
- docs: SOFTWARE_ARCHITECTURE.md — update bảng so sánh CA/VN

### Deps
- feat(deps): torch==2.3.0+cpu, transformers==4.41.2, faiss-cpu, sentencepiece, sacremoses, sentence-transformers, numpy==1.26.4

## [v0.3.1] — 2026-06-04 — Architecture upgrade + QA hardening + Design corrections

### Architecture (port từ MediVoice_AI Canada)
- feat(arch): src/pipeline/p0-p3 staging — pipeline grouped by function
- feat(arch): src/core/orchestrator.py — central execution controller
- feat(arch): src/validation/ — ValidationLayer VN (RuleEngine + AnomalyDetector)
- feat(arch): 4-layer control model documented in SOFTWARE_ARCHITECTURE.md

### ISO Docs (new)
- docs: SRS.md (35 requirements SRS-L{N}-NNN)
- docs: RTM.md (33 rows traced SRS→code→test)
- docs: SOFTWARE_ARCHITECTURE.md (4-layer diagram)
- docs: GLOSSARY.md, REFERENCED_STANDARDS.md, SoA, LIFECYCLE_PLAN, COMMUNICATION_PLAN
- docs: QA_PLAN.md v1.1 (V4 AI model review), TEST_PLAN.md

### QA
- feat(qa): .github/workflows/ci.yml (GitHub Actions)
- feat(qa): .pre-commit-config.yaml 3 gates (tests+bandit+coverage)
- feat(qa): scripts/ai_model_review.py (V4 — 5/5 PASS baseline)
- feat(qa): .coveragerc, 88% coverage

### Tests (new — 165 total from 61)
- test: tests/unit/test_models.py, test_pipeline_core.py, test_pipeline_staging.py
- test: tests/unit/test_l6_l7_orchestrator.py
- test: tests/validation/test_validation_layer.py

### Fixes
- fix(l0): purge_audio() — NĐ13/2023 data minimization (SRS-L0-003)
- fix(design): correct 4 wrong assumptions (Documentation Assistant, MarianMT, CĐHA, KB)
- fix(pipeline): 4 code issues (unused imports, sys.path, L7+L10 atomicity)

## [v0.3.0] — 2026-06-04 — Phase 0 pipeline implementation (L0→L10 + FastAPI PWA)

### Core Pipeline (new — all FROZEN layers now implemented)
- feat(L0): Audio normalize — librosa 16kHz mono + chunk_audio 10s/2s overlap + VAD
- feat(L1a): PhoWhisper ASR — lazy-load vinai/PhoWhisper-small, graceful degradation if unavailable
- feat(L1b): Drug name correction — alias map từ drug_db.json, n-gram matching, 110+ thuốc
- feat(L1c): Medical NER (rule-based) — regex patterns cho sinh hiệu, chẩn đoán, đơn thuốc, tái khám
- feat(L1d): ICD-10-VN lookup — substring search trên 15,026 mã, auto_lookup từ diagnosis text
- feat(L2): Schema validation + confidence scoring — weighted scores theo field importance
- feat(L3): Route detection — lam_sang default, CDHA/nha_khoa keyword triggers
- feat(L4): Human gate — state machine DRAFT→PENDING_REVIEW→APPROVED/REJECTED, Luật KCB 2023 Điều 62
- feat(L5): PII scan — regex CCCD (12 digits), CMND (9 digits), SĐT (0[3-9]xx), BHYT, email
- feat(L6): Form generation — transcript → BenhAnNgoaiTru (Mẫu 15/BV-01)
- feat(L7): SQLite + WAL + Fernet — encrypted form_data, init_db, store/load/update
- feat(L8): Error handler — PipelineError hierarchy, @with_recovery decorator, @safe_log
- feat(L9a): PDF export — ReportLab, Mẫu 15/BV-01 format, disclaimer bắt buộc
- feat(L10): Immutable audit log — SHA-256 hash chain, append-only, verify_chain, get_record_history

### Data Models (new)
- feat(models): Patient, ClinicalRecord (RecordStatus enum), Facility, AuditEntry — Pydantic v2

### API + PWA (new)
- feat(api): FastAPI app — POST /api/transcribe, GET/POST /api/records/{id}/approve|reject|pdf
- feat(pwa): Mobile-first HTML/JS UI — voice recording (MediaRecorder), draft review form, approve/reject, PDF download

### Infra
- feat: app.py entry point — uvicorn runner

## [v0.2.0] — 2026-06-03 — Design finalized, data reference complete

### Documentation (5 files updated)
- refactor: CLAUDE.md v0.2.0 — 2-layer product, 3 gói, 9 modules, mobile-first, tech stack locked
- refactor: VISION.md v0.2.0 — product vision updated, competitive analysis, roadmap 3 phases
- refactor: BRS.md v0.2.0 — business requirements, Mẫu 15/BV-01 spec, VNeID-ready data model
- refactor: DECISIONS.md v0.2.0 — 32 decisions locked (product + legal + technical + market)
- refactor: BACKLOG.md v0.2.0 — IMMEDIATE / Phase 0 / Phase 1 / Phase 2 structure

### External Review
- docs: THIRD_PARTY_REVIEW_REQUEST.md — 35 câu hỏi cho 3 reviewers
- review: ChatGPT, Grok, Copilot (legal + technical + market) — 2026-06-03
- docs: INDEPENDENT REVIEW — CLAUDE.md — independent Claude analysis

### Data Reference (new)
- data: TT23_procedure_codes.xlsx — Phụ lục TT23, 9,124 kỹ thuật, 30 chuyên khoa, hiệu lực 01/07/2026
- data: tt23_procedures.json — parsed full database (5.7MB)
- data: tt23_cdha.json — 1,161 kỹ thuật CĐHA (siêu âm: 211, X-quang: 206, CT: 267, MRI: 253)
- data: icd10vn_raw.json — FHIR gốc từ HL7 Vietnam (7.5MB)
- data: icd10vn.json — 15,026 mã ICD-10-VN parsed, nguồn QĐ4469/QĐ-BYT (9.3MB)
- data: drug_db.json — 110 thuốc thông dụng VN, 492 keywords (TT07/2017 + TT28/2024)
- data: MAU_15BV01_fields.py — Python dataclass đầy đủ Mẫu 15/BV-01
- data: MS15BV-01_benh_an_ngoai_tru_chung.pdf.pdf — form gốc từ BS partner

### Scripts (new)
- scripts/tt23_to_json.py — convert TT23 Excel → JSON
- scripts/download_icd10vn.py — download ICD-10-VN từ HL7 Vietnam
- scripts/build_drug_db.py — build drug database từ TT07/2017 + TT28/2024
- scripts/md_to_docx.py — convert markdown → Word

### Key Decisions (v0.2.0)
- Product = 2 layers (Patient Mgmt + AI Voice) + 3 gói + 9 modules
- Phase 0 core = Mẫu 15/BV-01 lâm sàng (không phải CĐHA)
- Architecture = FastAPI backend + PWA frontend (mobile-first, không phải Tauri)
- CĐHA = Plugin Phase 1 (không phải Phase 0)
- NOT SaMD = không đăng ký BYT thiết bị y tế
- Pilot = Đà Nẵng (Andy) + Sài Gòn (BS partner)

## [v0.1.1] — 2026-06-03 — refactor: lean documentation system
- refactor: replace 9-type report system with 4-file tracking
- refactor: CLAUDE.md v1.1
- feat: BACKLOG.md, DECISIONS.md

## [v0.1.0] — 2026-06-03 — docs: project kickoff
- docs: CLAUDE.md v1.0, PROJECT_KICKOFF.md (S1-S9), BRS.md, VISION.md
- infra: git repository initialized

*MediVoice VN | Updated: 2026-06-03*
