# NAMING_CONVENTION.md | DS-VN-DEV-001
# ISO 9001:2015 Clause 7.5 + ISO/IEC 42001:2023 | v1.1
# MediVoice VN — Naming & Document Conventions
# Updated: 2026-06-04

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

---

## 2. CODE FILE NAMING

### Python — pipeline layers
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

### Python — modules khác
```
src/models/{name}.py            patient.py, clinical_record.py
src/api/{name}.py               main.py
src/audit/{name}.py             immutable_ledger.py
tests/test_{scope}.py           test_pipeline_integrity.py
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
  fix(L1b): correct Amoxicillin spelling variants
  docs(dev): update NAMING_CONVENTION paths after restructure
  chore(session-end): close session 2026-06-04
```

---

## 4. FID FORMAT

File: `fids/FID-VN-{NNN}.md`

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

## 6. CẤU TRÚC THƯ MỤC CHUẨN

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
│   ├── compliance/
│   │   ├── AI_POLICY.md
│   │   ├── RISK_REGISTER.md
│   │   └── IMPACT_ASSESSMENT.md
│   ├── dev/
│   │   ├── NAMING_CONVENTION.md  ← file này
│   │   └── KPI_METRICS.md
│   ├── records/
│   │   ├── BACKLOG.md
│   │   ├── DECISIONS.md
│   │   └── LAST_SESSION.md
│   └── archive/            ← files cũ/done
├── src/
│   ├── core/               ← pipeline L0–L10
│   ├── models/             ← Pydantic data models
│   ├── api/                ← FastAPI + static PWA
│   ├── audit/
│   ├── governance/
│   └── risk/
├── tests/
├── fids/                   ← Feature Intent Documents
└── data/reference/         ← ICD-10-VN, drug_db, MAU_15BV01
```

---

*DS-VN-DEV-001 | NAMING_CONVENTION v1.1 | Updated: 2026-06-04*
hc