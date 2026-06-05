# NAMING_CONVENTION.md | DS-VN-DEV-001
# ISO 9001:2015 Clause 7.5 + ISO/IEC 42001:2023 | v1.2
# MediVoice VN — Naming & Document Conventions
# Updated: 2026-06-08

---

## 0. NGUYÊN TẮC (ISO 9001:2015 Cl.7.5)

Mọi tài liệu phải **identifiable** — biết được:
- **Cái gì** (TYPE code)
- **Khi nào** (YYYYMMDD)
- **Phiên bản** (version hoặc số thứ tự)

Hai loại tài liệu:

| Loại | Đặc điểm | Ví dụ |
|---|---|---|
| **Living doc** | Cập nhật liên tục, tên cố định | `BACKLOG.md`, `CLAUDE.md` |
| **Record** | Snapshot tại thời điểm, không sửa sau khi tạo | `DS-VN-AUD-20260603-001.md` |

---

## 1. DOCUMENT NAMING

### Living Documents — tên cố định, ngày ở trong nội dung
```
CLAUDE.md               ← master context (root)
CHANGELOG.md            ← version history (root)
docs/records/BACKLOG.md         ← task tracker
docs/records/LAST_SESSION.md    ← phiên gần nhất (ghi đè mỗi phiên)
docs/records/DECISIONS.md       ← architecture decision records
docs/records/PROJECT_PROGRESS.md← tiến độ toàn dự án
```

### Records — có ngày + số thứ tự, KHÔNG sửa sau khi tạo
```
FORMAT: DS-VN-[TYPE]-[YYYYMMDD]-[NNN].md

Ví dụ:
  DS-VN-AUD-20260603-001.md   ← audit report
  DS-VN-EPR-20260603-001.md   ← external peer review
  DS-VN-FID-20260604-001.md   ← feature intent document
```

### Document Type Codes
| Code | Loại | Nơi lưu |
|---|---|---|
| AUD | Audit report | docs/archive/ |
| EPR | External peer review | docs/archive/ |
| RDY | Readiness / sign-off | docs/archive/ |
| FID | Feature Intent Document | fids/ |
| TST | Test report | docs/records/ |
| SES | Session record (archive) | docs/archive/sessions/ |

---

## 2. CODE FILE NAMING

### Python — pipeline layers (src/core/)
```
src/core/l{N}_{name}.py         l0_normalize.py
                                l1a_asr.py
                                l1b_drug_correct.py
                                l1c_ner.py
                                l1d_icd_lookup.py
                                l2_validate.py
                                l3_route.py
                                l4_human_gate.py
                                l5_pii_scan.py
                                l6_generate_form.py
                                l7_storage.py
                                l8_error_handler.py
                                l9a_pdf_export.py
                                l10_audit_log.py
```

Quy tắc `l{N}`:
- `l` = Layer (không phải Phase)
- Số = thứ tự trong pipeline (0 → 10)
- Chữ cái suffix (a/b/c) = sub-layer cùng bước

### Support files trong src/core/ (KHÔNG có layer number)
Các file này là infrastructure cho pipeline, không phải layer:
```
src/core/exceptions.py      ← Custom exception types (PipelineError, ValidationError...)
src/core/orchestrator.py    ← Gọi L0→L10 tuần tự — entry point VN pipeline
src/core/orchestrator_ca.py ← Canada AI pipeline (legacy port, NOT active VN)
src/core/stage_result.py    ← Data class cho kết quả mỗi stage
src/core/state_machine.py   ← State machine (dùng bởi L4 human gate)
```

### Python — modules khác
```
src/models/{name}.py            patient.py, clinical_record.py
src/api/{name}.py               main.py
src/audit/{name}.py             immutable_ledger.py, execution_proof.py
src/governance/{name}.py        accountability.py, human_gate.py
src/risk/{name}.py              risk_engine.py
src/adapters/{name}.py          llm_adapter.py
src/validation/{name}.py        validation_layer.py, rule_engine.py
tools/{name}.py                 bench_ceer.py, gen_test_audio.py
scripts/{name}.py               iso_audit.py, build_drug_db.py
```

### Canada Pipeline (src/pipeline/) — LEGACY PORT
```
src/pipeline/p{N}_{phase}/l{N}_{name}.py

QUAN TRỌNG: src/pipeline/ là port Canada AI pipeline (Phase 0 nghiên cứu).
KHÔNG ACTIVE trong VN build. VN pipeline = src/core/orchestrator.py.
Layer numbers (l1, l2...) trong src/pipeline/ là Canada numbering — KHÔNG xung đột
với src/core/ vì hai codebase tách biệt hoàn toàn.
```

### Annotations bắt buộc trong code
```python
# @req BRS-VN-BO-001       ← file implement requirement này
# @verifies BRS-VN-BO-001  ← trong test files
```

---

## 3. GIT COMMIT FORMAT

```
{type}({scope}): {mô tả ngắn} [{FID nếu có}]

type:   feat | fix | docs | test | refactor | chore
scope:  L0–L10 | models | api | frontend | docs | compliance

Ví dụ:
  feat(L0): normalize audio to 16kHz mono [FID-VN-L0]
  fix(L1c): extend tai_kham regex to capture context [CT-007]
  docs(dev): update NAMING_CONVENTION v1.2
  chore(session-end): close session 2026-06-08
```

---

## 4. FID FORMAT

File: `fids/FID-VN-{NNN}.md`

Template: `docs/dev/FID_TEMPLATE.md`

```markdown
# FID-VN-NNN — Tên feature
Status: DRAFT | APPROVED | DONE
Layer: L{N}
LOC estimate: {N}

## Why
## What
## Acceptance Criteria
- [ ] ...
## Tests Required
- [ ] ...
```

---

## 5. RISK ID FORMAT

```
R-[PREFIX][NN]
  P = Pháp lý (Legal)
  A = AI / Kỹ thuật
  O = Vận hành (Operational)

Ví dụ: R-P01, R-A03, R-O02
```

---

## 6. TASK ID SYSTEM

Mọi task trong BACKLOG.md / PENDING_REQUESTS.md / PROJECT_PROGRESS.md đều có ID.

### FORMAT: {PREFIX}-{NNN}
`NNN` = 3 chữ số, đánh số tuần tự trong từng prefix (001, 002, ...)

### Prefix — Session Management
| Prefix | Ý nghĩa | File |
|---|---|---|
| `CT-` | Claude Todo — task Claude chưa hoàn thành | PENDING_REQUESTS.md |
| `PA-` | Andy Action — việc Andy cần làm | PENDING_REQUESTS.md |
| `TP-` | Third Party — cần hỏi AI khác (ChatGPT/Grok) | PENDING_REQUESTS.md |
| `SY-` | System — review định kỳ tự động | PENDING_REQUESTS.md |

### Prefix — Test & Quality
| Prefix | Ý nghĩa | File |
|---|---|---|
| `GAP-` | Test Gap — unit/integration tests còn thiếu | BACKLOG.md |
| `BENCH-` | Benchmark task | BACKLOG.md |
| `TRAIN-` | Model training (PhoWhisper/NER fine-tune) | BACKLOG.md |

### Prefix — Delivery
| Prefix | Ý nghĩa | File |
|---|---|---|
| `DEPLOY-` | Deployment / packaging task | BACKLOG.md |
| `CONFIG-` | Configuration / setup task | BACKLOG.md |
| `TEST-E2E-` | End-to-end test | BACKLOG.md |

### Prefix — Compliance & Legal
| Prefix | Ý nghĩa | File |
|---|---|---|
| `LEGAL-` | Legal / luật sư / compliance task | BACKLOG.md |
| `ONBOARD-` | BS onboarding task | BACKLOG.md |
| `DPA-` | Data Processing Agreement task | BACKLOG.md |

### Prefix — Feature (BACKLOG Phase 1+)
Các feature task trong Phase 1+ dùng tên mô tả ngắn + số thứ tự:
```
{FEATURE_NAME}-{NNN}

Ví dụ:
  DRUG-ALIAS-001    ← mở rộng alias map thuốc
  DRUG-INTERACT-001 ← drug interaction check
  QUEUE-001         ← queue management system
  BOOKING-001       ← booking engine
  SCREEN-001        ← staff screen
  HL7-001           ← HL7 v2 export
  FHIR-001          ← FHIR R4 export
  TRAIN-001         ← fine-tune PhoWhisper
  TRAIN-002         ← fine-tune NER
```

### Prefix — Implemented Features
```
VN-{AREA}-{NNN}     ← VN feature đã implement (trong BACKLOG DONE)
  VN-NER-002        ← VN word-form numbers + NER fix (FID-VN-005)
  VN-ROUTER-001     ← L6 branch lam_sang/cdha (FID-VN-004)

FID-VN-{NNN}        ← Feature Intent Document (xem Section 4)
  FID-VN-004        ← VN Router (DONE)
  FID-VN-005        ← VN NER word-form (DONE)
```

### Module IDs (Phase 1+)
```
M{N}   ← Module N (M1–M9) — xem CLAUDE.md SẢN PHẨM section
  M1 = Patient Management
  M2 = Booking Engine
  M3 = Thu chi
  M4 = Kết quả bên thứ 3
  M5 = Referral partner
  M6 = Zalo / Thông báo
  M7 = VN Cloud sync
  M8 = Plugin chuyên khoa
  M9 = HIS integration
```

---

## 7. PROGRESS TRACKING IDs (PROJECT_PROGRESS.md)

### FORMAT
```
P{PHASE}.{SECTION}[.{SUBSECTION}][{LETTER}]

PHASE:       0 | 1 | 2 | 3  ← Phase của dự án
SECTION:     1–9             ← Milestone chính trong phase
SUBSECTION:  1–9             ← Sub-milestone (optional)
LETTER:      a–z             ← Sub-item trong subsection (optional)
```

### Ví dụ
```
P0.1        Phase 0, Milestone 1: Design
P0.2        Phase 0, Milestone 2: Core Pipeline
P0.2.L0     Phase 0, Milestone 2, Sub-item L0 (layer 0)
P0.5.2      Phase 0, Milestone 5, Sub-milestone 2 (BENCH-002 baseline)
P0.5.2e     Phase 0, Milestone 5, Sub-milestone 2, item e
P1.M1       Phase 1, Module M1
P3.CONF     Phase 3, Conformity Assessment
```

### Phase mappings
```
P0 = Phase 0 MVP (BS nói → Mẫu 15/BV-01 → PDF)
P1 = Phase 1 Complete Product (M1–M7)
P2 = Phase 2 When Revenue (HL7, FHIR, HIS)
P3 = Phase 3 Scale + Conformity (Luật AI 134)
```

---

## 8. CẤU TRÚC THƯ MỤC CHUẨN

```
/
├── CLAUDE.md               ← AI context, session protocol
├── CHANGELOG.md            ← version history
├── app.py                  ← entry point
├── requirements.txt
├── docs/
│   ├── product/
│   │   ├── VISION.md
│   │   └── BRS.md
│   ├── compliance/         ← ISO docs, legal, audit
│   │   ├── AI_POLICY.md
│   │   ├── SCOPE.md
│   │   ├── RISK_REGISTER.md
│   │   ├── IMPACT_ASSESSMENT.md
│   │   ├── COMPETENCE.md
│   │   ├── NONCONFORMING.md
│   │   ├── VV_PLAN.md
│   │   ├── MANAGEMENT_REVIEW.md
│   │   ├── FEEDBACK_PROCESS.md
│   │   ├── IMPROVEMENT_PROCESS.md
│   │   ├── SRS.md
│   │   ├── RTM.md
│   │   ├── DPA_TEMPLATE.md
│   │   └── BS_ONBOARDING_CHECKLIST.md
│   ├── dev/                ← developer reference
│   │   ├── NAMING_CONVENTION.md    ← file này
│   │   ├── KPI_METRICS.md
│   │   ├── CONFUSION_PATTERNS.md
│   │   ├── CONSULTATION_TEMPLATE.md
│   │   ├── QUALITY_AUDIT_TEMPLATE.md
│   │   └── FID_TEMPLATE.md         ← template cho FID mới
│   ├── records/
│   │   ├── BACKLOG.md
│   │   ├── DECISIONS.md
│   │   ├── LAST_SESSION.md
│   │   ├── PENDING_REQUESTS.md
│   │   ├── PROJECT_PROGRESS.md
│   │   └── DESIGN_REPORT_v1.1_20260606.md
│   └── archive/            ← files cũ/done (snapshots không sửa)
│       └── sessions/       ← session archives DS-VN-SES-YYYYMMDD-NNN.md
├── src/
│   ├── core/               ← VN pipeline L0–L10 (ACTIVE)
│   ├── pipeline/           ← Canada AI pipeline (LEGACY PORT — không active VN)
│   ├── models/             ← Pydantic data models
│   ├── api/                ← FastAPI + static PWA
│   ├── audit/              ← Audit ledger + runtime hooks
│   ├── governance/         ← Accountability, human gate logic
│   ├── risk/               ← Risk engine
│   ├── adapters/           ← External system adapters (LLM, etc.)
│   └── validation/         ← Validation layer + rule engine
├── tests/
│   ├── unit/               ← Unit tests: test_{scope}.py
│   ├── integration/        ← Integration tests: test_{scope}.py
│   ├── compliance/         ← Compliance tests: test_{scope}.py
│   ├── governance/         ← Governance tests: test_{scope}.py
│   └── validation/         ← Validation tests: test_{scope}.py
├── fids/                   ← Feature Intent Documents: FID-VN-{NNN}.md
├── tools/                  ← Dev utilities (bench, eval, audio gen)
│   ├── bench_ceer.py
│   ├── gen_test_audio.py
│   └── eval_phowhisper.py
├── scripts/                ← Maintenance scripts (ISO audit, DB build)
│   ├── iso_audit.py
│   └── build_drug_db.py
├── config/                 ← Runtime config JSON
├── exports/                ← Generated output files (temp, gitignored)
└── data/
    ├── reference/          ← Immutable reference data (ICD-10-VN, drug_db, MAU_15)
    ├── audio/              ← Test audio files + benchmark data
    │   ├── lam_sang_*.wav  ← Lâm sàng synthetic (10 vùng miền)
    │   ├── tc_*.wav        ← Test case audio
    │   ├── dental/         ← Dental audio samples
    │   ├── test_scripts/   ← Transcript scripts
    │   ├── ground_truth_*.json ← Ground truth labels
    │   └── BENCH*_*.json   ← Benchmark result files
    └── kb/                 ← Knowledge base (FAISS index, guidelines)
```

---

## 9. QUY TẮC THỰC HÀNH

```
LUÔN:
  ✅ Dùng đường dẫn đầy đủ khi reference tài liệu
     Đúng: docs/compliance/DPA_TEMPLATE.md
     Sai:  DPA_TEMPLATE.md

  ✅ Task ID phải thuộc một prefix đã định nghĩa (Section 6)
  ✅ Progress ID dùng format P{PHASE}.{SECTION} (Section 7)
  ✅ Commit message kèm Task ID nếu có (Section 3)

KHÔNG:
  ❌ Tạo prefix mới mà không cập nhật Section 6 file này
  ❌ Đặt file vào folder ngoài cấu trúc Section 8 mà không ghi chú
  ❌ Dùng tên file có dấu cách (dùng _ hoặc - thay thế)
  ❌ Layer number trùng lắp giữa src/core/ và src/pipeline/
     (src/pipeline/ dùng Canada numbering — tách biệt hoàn toàn)
```

---

## CHANGELOG

| Version | Ngày | Thay đổi |
|---|---|---|
| v1.2 | 2026-06-08 | Thêm Section 6 (Task ID System), 7 (Progress IDs), 8 (Folder Structure đầy đủ). Thêm Canada pipeline note, support files trong src/core/. Cập nhật Section 2 tools/scripts. |
| v1.1 | 2026-06-04 | Thêm FID format, Risk ID. |
| v1.0 | 2026-06-03 | Initial version. |

---

*DS-VN-DEV-001 | NAMING_CONVENTION v1.2 | Updated: 2026-06-08*
