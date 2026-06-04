# STATEMENT_OF_APPLICABILITY.md | DS-VN-COM-011
# ISO/IEC 42001:2023 Clause 6.1.3 — Statement of Applicability
# MediVoice VN — Tuyên bố Áp dụng
# v1.0 | 2026-06-04

---

## Annex A Controls — Áp dụng hay Không áp dụng

| Control | Tên | Áp dụng | Lý do / Ghi chú |
|---|---|---|---|
| A.2.2 | AI Policy implementation | ✅ | AI_POLICY.md |
| A.2.5 | Roles and responsibilities | ✅ | COMPETENCE.md |
| A.2.6 | Resource management | ⚠️ Partial | 1 founder — informal |
| A.3.2 | AI risk assessment | ✅ | RISK_REGISTER.md |
| A.3.3 | AI risk treatment | ⚠️ Partial | Trong RISK_REGISTER.md |
| A.4.1 | Data quality | ⚠️ Partial | drug_db.json + icd10vn.json curated |
| A.4.2 | Data governance | ✅ | AI_POLICY.md Cl.4 + L5 PII |
| A.4.3 | Data provenance | ⚠️ Partial | Drug/ICD sources documented |
| A.5.1 | AI system design | ✅ | SOFTWARE_ARCHITECTURE.md |
| A.5.2 | AI system requirements | ✅ | SRS.md + RTM.md |
| A.5.3 | AI system impact assessment | ✅ | IMPACT_ASSESSMENT.md |
| A.5.4 | AI system supply chain | ❌ | No 3rd party AI supplier (Phase 0) |
| A.6.1 | Human oversight | ✅ | L4 Human Gate (bắt buộc pháp lý) |
| A.6.2 | Feedback mechanisms | ✅ | /api/feedback + FEEDBACK_PROCESS.md |
| A.6.3 | Trustworthy AI principles | ✅ | CONSTITUTION.md (archived) → AI_POLICY.md |
| A.7.1 | AI system documentation | ✅ | Toàn bộ docs/compliance/ |
| A.7.2 | AI system logging | ✅ | L10 audit log (immutable hash chain) |
| A.7.3 | AI system testing | ✅ | VV_PLAN.md + 165 tests PASS (v0.4.1) |
| A.8.1 | Incident reporting | ✅ | AI_POLICY.md Cl.8 |
| A.8.2 | Corrective action | ✅ | NONCONFORMING.md |
| A.8.3 | Continual improvement | ✅ | MANAGEMENT_REVIEW.md |
| A.8.4 | Audit trail | ✅ | L10 + verify_chain() |

---

*DS-VN-COM-011 | SoA v1.1 | ISO/IEC 42001:2023 Cl.6.1.3 | 2026-06-06*
