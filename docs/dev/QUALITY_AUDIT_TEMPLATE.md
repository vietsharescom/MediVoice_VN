# QUALITY_AUDIT_TEMPLATE.md | DS-VN-DEV-005
# ISO/IEC 25010:2023 — Software Quality Model
# ISO/IEC 42001:2023 Cl.9.1 — Monitoring, Measurement, Analysis
# MediVoice VN — Product Quality Audit Template
# v1.0 | 2026-06-06 | Owner: Andy Phan

---

## MỤC ĐÍCH

Template đánh giá chất lượng sản phẩm theo chuẩn ISO/IEC 25010.
KHÁC với ISO framework audit (document consistency).
Đây là đánh giá "dây chuyền sản xuất" — product đang ra đúng spec không?

---

## CADENCE (dựa trên ISO/IEC 25010 + thực tế startup)

| Loại | Tần suất | Tool | Ai chạy |
|---|---|---|---|
| Code quality (auto) | Mỗi commit | pytest + bandit + coverage | Git pre-commit hook |
| AI model quality | Sau mỗi thay đổi L1a/L1c | scripts/ai_model_review.py | Claude |
| Full product audit | Trước mỗi phase launch | Template này | Claude + Andy |
| Pilot quality review | Hàng tuần trong pilot | KPI_METRICS + template | Andy |
| Post-release audit | 1 tháng sau launch | Full template | Andy + Claude |

---

## QUALITY AUDIT — FULL TEMPLATE

```
QUALITY AUDIT — MediVoice VN
Audit ID: QA-AUDIT-YYYYMMDD
Auditor: [Claude / Andy / Cả hai]
Phase: [Phase 0 pilot / Phase 1 launch / etc.]
Date: YYYY-MM-DD
Ref: docs/dev/QUALITY_AUDIT_TEMPLATE.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 1 — AI ACCURACY (Core — AI specific, ISO 42001 Cl.9.1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KPI-001 CEER (Clinical Entity Error Rate):
  Measured: ___% | Target: < 5% | Status: PASS/FAIL/PENDING
  Source: BENCH-002 (pilot audio) / scripts/ai_model_review.py
  Breakdown:
    Drug name errors: ___% | Target: < 2%
    Dose errors:      ___% | Target: < 1%
    Diagnosis errors: ___% | Target: < 5%
    ICD code errors:  ___% | Target: < 5%
  
KPI-002 WER (Word Error Rate):
  Measured: ___% | Target: < 30% | Status: PASS/FAIL/PENDING
  Source: BENCH-001 (22 audio files) — current: 36-52%
  Note: WER 36-52% đang trên threshold → cần fine-tune TRAIN-001

KPI-003 Latency E2E:
  Measured: ___s | Target: < 5s | Status: PASS/FAIL
  Source: App timing log
  Breakdown:
    L0 normalize:  ___ms
    L1a ASR:       ___ms (bottleneck expected)
    L1b-L1d:       ___ms
    L6 form gen:   ___ms
    L9a PDF:       ___ms

AI Transparency (ISO 42001 A.6.3):
  □ Confidence score displayed to BS:      YES/NO
  □ Transcript gốc displayed to BS:        YES/NO
  □ ICD source displayed:                  YES/NO
  □ Disclaimer "AI tạo nháp" present:      YES/NO

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 2 — RELIABILITY (ISO/IEC 25010 Cl.4.5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KPI-012 Test coverage:
  Tests passing: ___/___ | Target: 100% | Status: PASS/FAIL
  Coverage: ___% | Target: ≥ 80% | Status: PASS/FAIL
  Source: pytest + coverage report

  Critical test suites:
  □ TestL4HumanGate (bypass protection):   PASS/FAIL
  □ TestL10AuditLog (immutable log):        PASS/FAIL
  □ TestDataResidency (no foreign cloud):   PASS/FAIL
  □ TestDrugNameIntegrity (INN preserve):   PASS/FAIL
  □ TestICD10VNRequired (ICD format):       PASS/FAIL
  □ TestPositioning (not SaMD):             PASS/FAIL

Error recovery:
  □ L8 @with_recovery: graceful degradation tested: YES/NO
  □ Pipeline continues when ASR unavailable: YES/NO

Open RTM CRITICAL gaps:
  GAP-002 (PII unit tests):     OPEN/CLOSED
  GAP-005 (API integration):    OPEN/CLOSED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 3 — SECURITY (ISO/IEC 25010 Cl.4.6 + NĐ13/2023)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

bandit scan:
  HIGH severity: ___ | Target: 0 | Status: PASS/FAIL
  MEDIUM severity: ___ | Target: 0 | Status: PASS/FAIL
  Source: bandit src/ -r

Data residency:
  □ No foreign cloud endpoints in src/: PASS/FAIL (TestDataResidency)
  □ SQLite only in local path: PASS/FAIL
  □ No hardcoded secrets: PASS/FAIL (TestNoHardcodedSecrets)

Privacy:
  □ Audio purged after transcription (L0): PASS/FAIL
  □ PII scan active (L5): PASS/FAIL
  □ Fernet encryption at rest (L7): PASS/FAIL
  □ Patient ref as hash (not raw CCCD in logs): PASS/FAIL

L4 Human Gate integrity:
  □ No bypass flag in codebase: PASS/FAIL
  □ L4 bypass incidents since last audit: ___  [Target: 0]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 4 — UX QUALITY (khi có pilot data)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KPI-004 BS Approve Rate:
  Measured: ___% | Target: > 85% | Status: PASS/FAIL/PENDING
  Source: L10 audit log
  
  Top 3 rejection reasons (from L10):
  1. ___________________
  2. ___________________
  3. ___________________
  → Action: [what to improve in pipeline]

KPI-003 Time per Record:
  Measured: ___ min | Target: < 3 min | Status: PASS/FAIL/PENDING
  Source: Pilot observation / L10 timestamps

KPI-008 BS NPS:
  Measured: ___/10 | Target: > 7 | Status: PASS/FAIL/PENDING
  Source: /api/feedback + pilot interview

KPI-007 Onboarding Time:
  Measured: ___ min | Target: < 30 min | Status: PASS/FAIL/PENDING
  Source: Pilot observation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 5 — DESIGN ADHERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BACKLOG status:
  □ All IMMEDIATE 🔴 items done: YES/NO
    Pending: [list if any]
  □ No overdue FID implementation: YES/NO

RTM coverage:
  Open gaps: ___ total | CRITICAL: ___
  Newly resolved this sprint: [list]

DESIGN_REPORT adherence:
  Feature implemented this sprint: [feature name]
  □ Matches DESIGN_REPORT spec: YES/NO/PARTIAL
  □ Matches FID acceptance criteria: YES/NO/PARTIAL
  □ Tests cover the feature: YES/NO/PARTIAL

  Deviations from design (if any):
  [List any intentional deviations + reason + ADR if needed]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECTION 6 — COMPLIANCE CHECK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

L10 audit log integrity:
  □ verify_chain() result: PASS/FAIL
  □ No tampered entries: PASS/FAIL
  □ Audit log has entries since last audit: YES/NO

Legal compliance:
  □ Mẫu 15/BV-01 format correct (TT32/2023): YES/NO
  □ ICD-10-VN in diagnosis field: YES/NO
  □ Disclaimer on all PDF output: YES/NO
  □ BS CCHN collected at registration: YES/NO
  □ No referral financial amounts recorded: YES/NO

Data retention:
  □ SQLite schema supports 10+ year retention: YES/NO

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUDIT SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Overall: PASS / CONDITIONAL PASS / FAIL

Critical issues (must fix immediately):
  1. [issue + action + owner + deadline]

High priority (fix before next phase):
  1. [issue + action]

Improvements for backlog:
  1. [improvement + priority]

Next audit: [YYYY-MM-DD or "before [milestone]"]
Sign-off: Andy Phan | [Date]
```

---

## QUICK CHECKLIST (dùng sau mỗi FID — 5 phút)

```
POST-FID QUICK CHECK — [FID name] — [Date]

Code quality:
  □ pytest 100% PASS
  □ bandit 0 HIGH/MEDIUM
  □ Coverage ≥ 80%

Docs updated:
  □ CHANGELOG entry added
  □ RTM: new requirements mapped
  □ DECISIONS.md: ADR if needed
  □ BACKLOG: task marked done

Design adherence:
  □ FID acceptance criteria met
  □ DESIGN_REPORT section matches implementation
  □ iso_audit.py: no new 🔴 issues

Status: PASS / FAIL
```

---

## AI MODEL SPECIFIC AUDIT (sau thay đổi L1a/L1c)

Theo VV_PLAN.md V4 process:

```
STEP 1: Regression baseline
  python scripts/ai_model_review.py --save-baseline
  
STEP 2: Make changes to L1a or L1c

STEP 3: Compare
  python scripts/ai_model_review.py --compare-baseline

PASS criteria:
  □ All 5 test cases: same output (5/5 PASS)
  □ No drug name lost
  □ Confidence delta ≤ 0.10
  □ No ICD regression

STEP 4: /code-review high on the diff

STEP 5: Record in docs/records/AI_REVIEW_YYYYMMDD.md
```

---

*DS-VN-DEV-005 | QUALITY_AUDIT_TEMPLATE v1.0 | ISO/IEC 25010:2023 | 2026-06-06*
