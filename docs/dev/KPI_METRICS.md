# KPI_METRICS.md | DS-VN-DEV-002
# ISO/IEC 42001:2023 Clause 9.1 — Monitoring, Measurement, Analysis
# ISO 9001:2015 Clause 9.1 — Monitoring and Measurement
# MediVoice VN — Key Performance Indicators
# v1.1 | 2026-06-04

---

## 1. AI QUALITY METRICS

| KPI | Metric | Target | Ngưỡng dừng | Nguồn dữ liệu |
|---|---|---|---|---|
| KPI-001 | CEER (Clinical Entity Error Rate) | < 5% | > 10%: dừng pilot | BENCH-001 results |
| KPI-002 | WER (Word Error Rate) | < 30% | > 40%: retrain | BENCH-001 results |
| KPI-003 | Latency E2E | < 5s | > 8s: optimize | App timing log |
| KPI-004 | BS approve rate (không sửa nhiều) | > 85% | < 70%: review L6 | L10 audit log |

---

## 2. BUSINESS METRICS

| KPI | Metric | Target | Nguồn dữ liệu |
|---|---|---|---|
| KPI-005 | Paying users cuối Phase 0 | ≥ 5 BS | Manual tracking |
| KPI-006 | DAU/MAU ratio | > 0.6 | SQLite usage log |
| KPI-007 | Onboarding time | < 30 phút | Pilot observation |
| KPI-008 | NPS (pilot BS) | > 7/10 | /api/feedback |

---

## 3. COMPLIANCE METRICS

| KPI | Metric | Target | Nguồn dữ liệu |
|---|---|---|---|
| KPI-009 | L4 bypass incidents | 0 | L10 audit log |
| KPI-010 | Data residency violations | 0 | TestDataResidency |
| KPI-011 | Audit log chain integrity | 100% | verify_chain() weekly |
| KPI-012 | Tests passing trước commit | 100% | pytest CI |
| KPI-013 | Critical feedback resolved < 48h | 100% | feedback table |

---

## 4. QUY TRÌNH ĐO LƯỜNG (ISO 9001:2015 Cl.9.1.1)

### Cadence

| Loại | Tần suất | Người thực hiện |
|---|---|---|
| Tests (KPI-012) | Trước mỗi commit | Tự động (pre-commit) |
| Audit chain (KPI-011) | Hàng tuần (thứ 2) | Andy — chạy `verify_chain()` |
| App metrics (KPI-003, 006) | Sau mỗi tuần pilot | Andy — query SQLite |
| BENCH metrics (KPI-001, 002) | Sau BENCH-001 audio | Andy + BS Đà Nẵng |
| Business metrics (KPI-005, 007, 008) | Monthly | Andy |
| Quarterly review | Mỗi quý | Management Review |

### Phương pháp thu thập

```python
# KPI-004 approve rate — query L10
SELECT
  COUNT(*) FILTER (WHERE action='APPROVED') * 1.0 /
  COUNT(*) FILTER (WHERE action IN ('APPROVED','REJECTED')) AS approve_rate
FROM audit_log
WHERE timestamp > date('now', '-30 days');

# KPI-011 chain integrity
from src.core.l10_audit_log import verify_chain
conn = sqlite3.connect('medivoice.db')
ok, err = verify_chain(conn)
assert ok, f"CHAIN BROKEN: {err}"
```

---

## 5. ACTUALS (điền sau mỗi kỳ đo)

| Ngày | KPI | Actual | Target | Status |
|---|---|---|---|---|
| 2026-06-04 | KPI-012 | 61/61 = 100% | 100% | ✅ |
| *(chờ pilot)* | KPI-001 CEER | — | < 5% | ⏳ |
| *(chờ pilot)* | KPI-004 Approve rate | — | > 85% | ⏳ |

---

*DS-VN-DEV-002 | KPI_METRICS v1.1 | ISO/IEC 42001:2023 Cl.9.1 | 2026-06-04*
