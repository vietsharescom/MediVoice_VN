# CLAUDE.md -- MediVoice VN AI Execution Context
# ISO/IEC 42001:2023 | ISO_VN v1.0 | v1.0 ACTIVE
# Forked from: MediVoice AI (Canada) v2.61.3
# Created: 2026-06-03 | Owner: Andy Phan (Viet) | Maple Leaf Group

## IDENTITY
Project: MediVoice VN — Bác sĩ đọc → Bệnh án điện tử tự động (thị trường Việt Nam)
Code: DS-VN | Owner: Andy Phan (Viet) | Maple Leaf Group
Path: C:\Projects\MediVoice_VN | GitHub: TBD
Stack: Python 3.10, FastAPI, PhoWhisper-small, PhoBERT+CRF, SQLite, Fernet
Market: Vietnam — phòng khám tư nhân, trung tâm CĐHA, bác sĩ chuyên khoa
Compliance: ISO_VN (NĐ13/2023 + TT32/2023 + TT13/2025 + Luật AI 134/2025)

## KHÁC BIỆT CỐT LÕI VỚI MEDIVOICE CA
- Output: Bệnh án TT32/2023 (tiếng Việt) — KHÔNG phải SOAP tiếng Anh
- ICD codes: ICD-10-VN (QĐ5837/BYT) — KHÔNG phải ICD-10-CA
- PII: CCCD/CMND/BHYT/SĐT — KHÔNG phải OHIP/SIN
- Translation: KHÔNG có MarianMT — output tiếng Việt trực tiếp
- Templates: Core + Specialty Plugins (CĐHA, Ngoại trú, Nha khoa...)
- Deployment: On-premise bắt buộc (NĐ13/2023 data residency)
- Patient ID: Họ tên + ngày sinh (CCCD optional, không bắt buộc SHA-256)

## PIPELINE (FROZEN)
L0 → L1 → L2 → L3 → L4 → L5 → L6[+PLUGIN] → L7 → L8 → L9 → L10
Source of truth: config/pipeline/graph_registry_vn.json
Plugin system: src/pipeline/p2_decision/plugins/ (CĐHA, ngoai_tru, nha_khoa,...)

## STRUCTURE
src/core/                Engine (DO NOT MODIFY)
src/audit/               Audit (DO NOT MODIFY)
src/pipeline/p0-p3/      Stage handlers (build via FID)
src/pipeline/p2_decision/plugins/  Specialty output plugins
config/                  Graph, schemas, contracts, ICD-10-VN
tests/unit/              Unit tests
tests/integration/       End-to-end tests
tests/compliance/        ISO + Luật AI 134 compliance tests
docs/cl04_context/       ISO 42001 Clause 4
docs/cl05_leadership/    ISO 42001 Clause 5
docs/cl06_planning/      ISO 42001 Clause 6
docs/cl07_support/       ISO 42001 Clause 7
docs/cl08_operation/     ISO 42001 Clause 8
docs/cl09_evaluation/    ISO 42001 Clause 9
docs/cl10_improvement/   ISO 42001 Clause 10
docs/features/           FID documents
docs/records/            Session logs + reports

## SESSION START -- ALWAYS DO THIS FIRST
1. Read: docs/records/LATEST_SESSION.md
2. Read: docs/records/TASK_BACKLOG.md (report WAITING-ANDY items)
3. Run:  python -m pytest tests/ -q (verify baseline)
4. Confirm current state matches LATEST_SESSION.md Section 4
5. REPORT (mandatory before doing anything):
   "State: v{X} | Tests: {N}/{N} PASS | Open tasks: {N} | Next: {task} | Ready."

## SESSION END -- ALWAYS DO THIS LAST
1. Read TASK_BACKLOG.md — list remaining ACTIVE tasks to Andy
2. Update TASK_BACKLOG.md — mark completed DONE, add new tasks
3. Update docs/records/LATEST_SESSION.md — version, test count, open items
4. Report: "Session closed. Remaining open: {task list}"

## ABSOLUTE RULES
1. ALL execution through Orchestrator only
2. Pipeline order L0→L10 FROZEN — plugins via FID only
3. Every feature needs APPROVED FID (major >50 LOC; minor <20 LOC = direct commit + test)
4. 100% tests PASS before any commit
5. Every change needs CHANGELOG entry
6. ONLY L6_AGENT + plugins call external logic
7. STAY IN PROJECT DIRECTORY — NEVER read/write outside C:\Projects\MediVoice_VN
8. AI ADVISORY (P6): Propose A/B/C options. Never single solution. Flag risks BEFORE code.
9. TECH SCAN (P8): Before architecture change, scan HuggingFace + arXiv + MOH circulars.

## LEGAL CONSTRAINTS (HARD RULES)
- NĐ13/2023: Dữ liệu bệnh nhân PHẢI ở server trong VN. Cloud nước ngoài = vi phạm.
- TT32/2023: Output PHẢI theo mẫu bệnh án BYT — không được tự do format.
- TT13/2025: Phải hỗ trợ chữ ký số + audit trail + HL7 FHIR (deadline 31/12/2026).
- Luật AI 134/2025: AI y tế = rủi ro cao. Conformity assessment trước 01/09/2027.
- Luật KCB 2023: AI chỉ tạo draft — bác sĩ BẮT BUỘC phải phê duyệt trước khi lưu.

## FEATURE WORKFLOW
1. FID in docs/features/ -- Status = APPROVED (Andy ký)
2. Implement in src/pipeline/ + @req SRS-VN-L{N}-NNN header
3. Tests with @verifies SRS-VN-L{N}-NNN
4. python -m pytest tests/ -v (100% PASS)
5. Update CHANGELOG.md
6. Commit: feat(VN-L{N}): description [FID-VN-NNN]

## SPECIALTY PLUGINS (Phase 1)
Priority order:
1. plugin_cdha.py     — Báo cáo siêu âm/X-quang/CT (USE CASE #1)
2. plugin_ngoai_tru.py — Mẫu 15/BV1 ngoại trú chung
3. plugin_nha_khoa.py  — Mẫu 16/BV1 nha khoa ngoại trú
Phase 2: san_khoa (05/BV1), nhi (02/BV1), nhan_khoa (21-26/BV1)

## AI ADVISORY PROTOCOL (P6 + P7)
At any task start, Claude scans for and reports:
  [RISK-CRITICAL] pháp lý/an toàn → resolve trước khi code
  [RISK-HIGH]     kiến trúc impact → Andy quyết định
  [RISK-MEDIUM]   chất lượng → flag + proceed unless Andy objects
  [RISK-LOW]      minor → log only

## KEY DATASETS (cần tích hợp)
- VietMed (arXiv 2404.05659): 16h labeled + 1000h unlabeled VN medical speech
- ViMedCSS (arXiv 2602.12911): VN medical code-switching (VI+EN)
- ICD-10-VN: QĐ5837/QĐ-BYT (bắt buộc trong phần Chẩn đoán)

## KEY DECISIONS (DO NOT RE-DEBATE)
- Option B: Local only — không cloud, không MarianMT
- Output: TT32/2023 format — không SOAP
- Plugin system: 1 core + N specialties — không phải 29 app riêng
- Target Phase 1: phòng khám CĐHA tư + phòng khám đa khoa tư
- Go-to-market: plugin/add-on, không cạnh tranh FPT/Viettel
- Patient ID: flexible (không bắt buộc CCCD) — khác CA
