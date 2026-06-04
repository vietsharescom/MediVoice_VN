# NAMING_CONVENTION.md | DS-VN-CL07-001
# ISO 9001:2015 Clause 7.5 + ISO/IEC 42001:2023 | v1.0
# MediVoice VN — Naming & Document Conventions

---

## 0. NGUYÊN TẮC ISO 9001:2015 CL.7.5

ISO yêu cầu mọi documented information phải **identifiable**:
- Biết được: cái gì (TYPE) + khi nào (YYYYMMDD) + thứ mấy (NNN)
- Phân biệt 2 loại:
  - **Living docs** (cập nhật liên tục) → tên file cố định, ngày ở trong nội dung
  - **Records** (snapshot thời điểm) → tên file PHẢI có ngày + số thứ tự

---

## 1. FORMAT ĐẶT TÊN

### Living Documents (không có ngày trong tên)
Cập nhật liên tục, luôn là "bản hiện tại":
```
BACKLOG.md          ← task tracker
DECISIONS.md        ← decision log
CHANGELOG.md        ← version history
CLAUDE.md           ← master context
```

### Records (có ngày + số thứ tự trong tên)
Snapshot tại thời điểm cụ thể, KHÔNG sửa sau khi tạo:
```
FORMAT: DS-VN-[TYPE]-[YYYYMMDD]-[NNN].md

DS-VN-SES-20260603-001.md   ← session report phiên 1 ngày 3/6
DS-VN-SES-20260603-002.md   ← session report phiên 2 cùng ngày
DS-VN-AUD-20260603-001.md   ← audit report
DS-VN-EPR-20260603-001.md   ← external peer review
DS-VN-RDY-20260603.md       ← readiness report (1 lần, không NNN)
DS-VN-FID-001_20260603.md   ← feature intent document
DS-VN-TST-001_20260603.md   ← test report
```

### Document Type Codes
| Code | Loại | Nơi lưu |
|---|---|---|
| SES | Session report | docs/records/sessions/ |
| AUD | Audit report (internal) | docs/records/ |
| EPR | External peer review | docs/records/ |
| RDY | Readiness / sign-off | docs/records/ |
| FID | Feature Intent Document | fids/ |
| TST | Test report | docs/records/ |
| CL05 | Leadership docs | docs/cl05_leadership/ |
| CL06 | Planning docs | docs/cl06_planning/ |
| BRS | Business Requirements | docs/cl08_operation/ |

---

## 2. CODE NAMING

### Python files
```
src/core/       l{N}_{name}.py      l0_normalize.py
src/audit/      {name}.py           immutable_ledger.py
src/governance/ {name}.py           human_gate.py
src/risk/       {name}.py           risk_engine.py
tests/          test_{scope}.py     test_pipeline_integrity.py
```

### Mandatory annotations
```python
# @req BRS-VN-BO-001  -- Tên yêu cầu
# @verifies BRS-VN-BO-001  -- Trong test files
```

---

## 3. GIT COMMIT FORMAT

```
{type}({scope}): {mô tả} [{FID nếu có}]

type:  feat | fix | docs | test | refactor | chore
scope: L0-L10 | audit | governance | risk | api | frontend | docs

Ví dụ:
  feat(L0): normalize audio to 16kHz mono [FID-VN-L0]
  fix(L1b): correct Amoxicillin spelling variants
  docs(cl06): update RISK_REGISTER with R-A08
  test(compliance): add audit ledger chain verification
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
...

## What
...

## Acceptance Criteria
- [ ] ...

## Tests Required
- [ ] ...
```

---

## 5. RISK ID FORMAT

`R-[PREFIX][NN]`
- P = Pháp lý
- A = AI/Kỹ thuật
- O = Vận hành

---

*DS-VN-CL07-001 | NAMING_CONVENTION v1.0 | 2026-06-03*
