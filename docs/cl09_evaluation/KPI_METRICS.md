# KPI_METRICS.md | DS-VN-CL09-KPI
# ISO/IEC 42001:2023 Clause 9 | v1.0 | 2026-06-03
# MediVoice VN — Key Performance Indicators

---

## AI QUALITY METRICS

| KPI | Metric | Target | Trigger |
|---|---|---|---|
| KPI-001 | CEER (Clinical Entity Error Rate) | < 5% | > 10%: stop pilot |
| KPI-002 | WER (Word Error Rate) | < 30% | > 25% sustained 7d: retrain |
| KPI-003 | Latency (end-to-end) | < 5s perceived | > 8s: optimize chunk size |
| KPI-004 | BS approve rate (no major edits) | > 85% | < 70%: review form generation |

## BUSINESS METRICS

| KPI | Metric | Target |
|---|---|---|
| KPI-005 | Paying users end of Phase 0 | >= 5 BS |
| KPI-006 | DAU/MAU ratio | > 0.6 (BS dùng mỗi ngày) |
| KPI-007 | Onboarding time | < 30 phút |
| KPI-008 | Net Promoter Score (pilot BS) | > 7/10 |

## COMPLIANCE METRICS

| KPI | Metric | Target |
|---|---|---|
| KPI-009 | L4 bypass incidents | 0 |
| KPI-010 | Data residency violations | 0 |
| KPI-011 | Audit log chain integrity | 100% |
| KPI-012 | Tests passing | 100% before every commit |

---

*DS-VN-CL09-KPI | KPI_METRICS v1.0 | 2026-06-03*
