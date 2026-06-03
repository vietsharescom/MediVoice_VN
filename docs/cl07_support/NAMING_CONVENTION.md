# NAMING_CONVENTION.md | DS-VN-CL07-001
# ISO 9001:2015 Clause 7.5 + ISO/IEC 42001:2023 | v1.0
# MediVoice VN — Naming & Document Conventions

---

## 1. DOCUMENT ID FORMAT

```
[PROJECT_CODE]-[TYPE]-[NNN]_[YYYYMMDD]

PROJECT_CODE: DS-VN (MediVoice VN)
TYPE:         CL04, CL05, BRS, FID, SES, AUD, TST...
NNN:          3 digits từ 001
YYYYMMDD:     Ngày tạo hoặc sửa lần cuối
```

### Document Types
| Type | File | Ví dụ |
|---|---|---|
| DS-VN-CL05-001 | AI_POLICY.md | AI Policy |
| DS-VN-CL05-002 | CONSTITUTION.md | Governance principles |
| DS-VN-CL06-001 | RISK_REGISTER.md | Risk register |
| DS-VN-CL08-BRS | BRS.md | Business requirements |
| DS-VN-FID-NNN | fids/FID-VN-NNN.md | Feature Intent Document |
| DS-VN-SES-YYYYMMDD | docs/records/SES-*.md | Session log |

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
