# CHANGELOG — MediVoice VN
# ISO/IEC 42001:2023 Clause 10.2

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
