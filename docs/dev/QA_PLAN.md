# QA_PLAN.md | DS-VN-DEV-003
# ISO 9001:2015 Clause 8 + ISO/IEC 12207:2017 Cl.7.2.4
# Học từ MediVoice_AI QA_PLAN v1.2
# MediVoice VN — Quality Assurance Plan
# v1.0 | 2026-06-04

---

## 1. QA GATES

| Gate | Điều kiện | Tool | Block gì |
|---|---|---|---|
| Pre-commit | Tất cả tests PASS | pytest | Commit |
| Pre-commit | Line coverage ≥ 80% | pytest-cov | Commit |
| Pre-commit | Không có HIGH/MEDIUM security issues | bandit | Commit |
| Pre-commit | Không có type errors trong src/ | mypy | Commit |
| Pre-FID-build | FID status = APPROVED | Manual | Build start |
| Pre-release | KPI-012=100%, CEER<5% | Manual review | Release |

---

## 2. QA ACTIVITIES

| Activity | Khi nào | Owner |
|---|---|---|
| Code review vs SRS requirements | Mỗi FID | Andy |
| ValidationLayer review (VN rules) | Mỗi FID mới | Andy |
| Test coverage review | Mỗi commit | pytest-cov (auto) |
| CHANGELOG audit | Mỗi commit | git hooks |
| Session state confirmation | Đầu mỗi phiên | Claude (bắt buộc) |
| Pipeline E2E test TC-001 | Trước mỗi release | Andy |
| Audit chain verify | Hàng tuần (thứ 2) | Andy |

---

## 3. STATIC ANALYSIS COMMANDS

```bash
# Security scan (phải clean trước khi commit)
bandit -r src/ -ll           # -ll = HIGH + MEDIUM only

# Type check (phải clean trước khi commit)
mypy src/ --ignore-missing-imports --python-version 3.10

# Coverage (phải ≥ 80%)
python -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=80
```

---

## 4. COVERAGE GATE

| Level | Mechanism | Block |
|---|---|---|
| Local (developer) | Chạy coverage command trước mỗi commit | Commit phải fail nếu <80% |
| CI/CD | GitHub Actions (quality-gate job) | PR merge bị block nếu <80% |

**Rule:** Không commit nào được chấp nhận với coverage < 80%.
**Responsibility:** Andy verify local; GitHub Actions enforce tự động.

---

## 5. VALIDATION LAYER INTEGRATION

Mỗi khi thay đổi L1a (ASR) hoặc L1c (NER):
1. Chạy `pytest tests/validation/ -v`
2. Chạy E2E test TC-001 với input chuẩn
3. Verify output: CEER, confidence, ICD accuracy
4. Ghi kết quả vào `docs/records/DS-VN-TST-YYYYMMDD-001.md`

---

*DS-VN-DEV-003 | QA_PLAN v1.0 | ISO 9001:2015 Cl.8 + ISO/IEC 12207:2017 | 2026-06-04*
