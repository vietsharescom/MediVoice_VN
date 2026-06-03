# AUDIT_PROGRAMME.md | DS-VN-CL09-AUD
# ISO/IEC 42001:2023 Clause 9.2 | Luật AI 134/2025 Điều 24
# v1.0 | 2026-06-03

---

## LỊCH AUDIT

| Audit | Phạm vi | Tần suất | Phương pháp | Chủ trách nhiệm |
|---|---|---|---|---|
| AUD-VN-001 | Pipeline integrity tests | Mỗi commit (tự động) | pytest pre-commit hook | CI |
| AUD-VN-002 | FID compliance | Mỗi sprint | Manual review | Andy Phan |
| AUD-VN-003 | Module contracts compliance | Quarterly | Code review | Andy Phan |
| AUD-VN-004 | ISO 42001 clause coverage | Annually | Document review | Andy Phan |
| AUD-VN-005 | Luật AI 134 conformity | Trước 01/09/2027 | External assessment | Bộ KH&CN |

## TIÊU CHÍ PASS

- AUD-VN-001: 100% tests PASS (xem KPI_METRICS.md KPI-012)
- AUD-VN-002: Mọi feature > 100 LOC đều có FID APPROVED
- AUD-VN-003: Không có layer vi phạm module_contracts_vn.json
- AUD-VN-004: Tất cả 10 clauses có ít nhất 1 document

## EXTERNAL PEER REVIEW (EPR)

Trigger: Major architecture changes, Phase transitions, safety-critical modules
Format: DS-VN-EPR-NNN-{REQUEST|RESPONSE}-[reviewer]-YYYYMMDD.md
Reviewers: ChatGPT + Grok + Copilot (3-source cross-validation)

---

*DS-VN-CL09-AUD | AUDIT_PROGRAMME v1.0 | 2026-06-03*
