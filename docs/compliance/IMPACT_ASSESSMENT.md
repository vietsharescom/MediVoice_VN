# IMPACT_ASSESSMENT.md | DS-VN-CL08-IA
# ISO/IEC 42001:2023 Clause 8.2 + Annex A.5.3
# Luật AI 134/2025 — Bắt buộc cho High-Risk AI
# v1.0 | 2026-06-03 | Approved: Andy Phan

**Phân loại:** HIGH RISK (medical AI, ảnh hưởng sức khỏe bệnh nhân)

---

## IMPACT AREAS

| ID | Rủi ro tác động | Mức độ | Kiểm soát | Residual |
|---|---|---|---|---|
| IA-VN-001 | **Privacy** — PHI bệnh nhân trong transcript | HIGH | NĐ13/2023 + L5 PII scan + Fernet + hash patient ref | LOW |
| IA-VN-002 | **Safety** — Tên thuốc/liều sai trong bệnh án | CRITICAL | L1b drug correct + L4 BS review + CEER tracking | MEDIUM (ACCEPTED) |
| IA-VN-003 | **Fairness** — ASR kém chính xác giọng miền Nam | MEDIUM | WER tracking + fine-tune từ pilot audio | LOW |
| IA-VN-004 | **Transparency** — BS không biết AI không chắc chắn | MEDIUM | Hiển thị confidence + transcript gốc | LOW |
| IA-VN-005 | **Human oversight** — BS approve không đọc kỹ | HIGH | L4 design: hiển thị đầy đủ draft, yêu cầu action rõ ràng | LOW |
| IA-VN-006 | **Data residency** — Data rời VN | CRITICAL | module_contracts: no foreign cloud | LOW |
| IA-VN-007 | **Legal liability** — MediVoice VN bị xếp SaMD | HIGH | Positioning "Documentation Assistant" (3 AI reviews confirmed NOT SaMD) | LOW |
| IA-VN-008 | **Non-discrimination** — BS vùng sâu, giọng địa phương | MEDIUM | Fine-tune đa giọng từ pilot audio | MEDIUM |

**OVERALL: HIGH RISK**
**Residual Risk Accepted by:** Andy Phan | 2026-06-03
**Review:** Annually hoặc khi có major change

---

*DS-VN-CL08-IA | IMPACT_ASSESSMENT v1.0 | 2026-06-03*
