# CHANGELOG — MediVoice VN
# ISO/IEC 42001:2023 Clause 10.2

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
