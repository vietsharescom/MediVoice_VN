# TEST_PLAN.md | DS-VN-DEV-004
# ISO/IEC/IEEE 29119-3:2021 — Test Plan
# Học từ MediVoice_AI TEST_PLAN v1.1
# MediVoice VN — Test Plan
# v1.0 | 2026-06-04

---

## 1. SCOPE

Tất cả pipeline stages L0-L10, validation layer, audit system, API.

---

## 2. TEST TYPES

| Type | Location | Tool | Trigger |
|---|---|---|---|
| Unit | tests/unit/ | pytest | Pre-commit |
| Integration | tests/integration/ | pytest | Pre-commit |
| Compliance | tests/compliance/ | pytest | Pre-commit |
| Validation | tests/validation/ | pytest | Pre-commit |
| Coverage | all | pytest-cov | Pre-commit |
| API | tests/api/ | pytest + httpx | Pre-commit |

---

## 3. TEST NAMING CONVENTION

```python
# File: tests/{scope}/test_{layer}_{what}.py
# @verifies SRS-L{N}-{NNN}  -- description
def test_function():
    ...
```

---

## 4. COVERAGE REQUIREMENT

```
Ngưỡng: ≥ 80% line coverage (KPI-012)
Command:
  python -m pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80
Scope: src/ (loại trừ __init__.py và stubs)
Standard: ISO/IEC 12207:2017 Cl.7.2.4
```

---

## 5. ENTRY/EXIT CRITERIA

**Entry:** FID status = APPROVED
**Exit:** 100% tests PASS + coverage ≥ 80% + CHANGELOG updated + RTM updated

---

## 6. TRẠNG THÁI HIỆN TẠI

| Test suite | Files | Tests | Status |
|---|---|---|---|
| Pipeline integrity | tests/test_pipeline_integrity.py | 61 | ✅ 61/61 PASS |
| Compliance | tests/compliance/ | - | ✅ (included above) |
| Governance | tests/governance/ | - | ✅ (included above) |
| Unit (pending) | tests/unit/ | - | ⏳ Cần viết |
| Integration (pending) | tests/integration/ | - | ⏳ Cần viết |
| Validation layer | tests/validation/ | - | ⏳ Cần viết |
| API | tests/api/ | - | ⏳ Cần viết |

---

## 7. OPEN ITEMS (từ RTM GAPs)

| Gap | Test cần viết | Priority |
|---|---|---|
| GAP-002 | tests/unit/test_l5_pii_scan.py | High |
| GAP-003 | tests/unit/test_l8_error_handler.py | Medium |
| GAP-004 | tests/unit/test_l9a_pdf_export.py | Medium |
| GAP-005 | tests/api/test_api_endpoints.py | High |
| NEW | tests/validation/test_validation_layer.py | High |

---

*DS-VN-DEV-004 | TEST_PLAN v1.0 | ISO/IEC/IEEE 29119-3:2021 | 2026-06-04*
