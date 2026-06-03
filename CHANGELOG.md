# CHANGELOG — MediVoice VN
# ISO/IEC 42001:2023 Clause 10.2

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
