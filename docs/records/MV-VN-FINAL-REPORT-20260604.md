# MV-VN-FINAL-REPORT-20260604
# MediVoice VN — Báo cáo Tổng hợp Phiên 2026-06-04
# ISO/IEC 42001:2023 Cl.9.3 — Management Review Record
# Owner: Andy Phan | Maple Leaf Group

---

## 1. TRẠNG THÁI TỔNG QUAN

| Field | Giá trị |
|---|---|
| Version | **v0.3.0** |
| Tests | **165/165 PASS** |
| Coverage | **88%** (gate: ≥80%) |
| Security | **0 HIGH/MEDIUM** (bandit) |
| Commits phiên này | 9 commits |
| Audio files sẵn sàng | **22 WAV files** (data/Voices/) |

---

## 2. ĐÃ XÂY DỰNG — PHÂN LOẠI NGUỒN GỐC

### A. COPY TRỰC TIẾP TỪ MediVoice_AI (Canada)

| Component | File VN | Ghi chú |
|---|---|---|
| Orchestrator pattern | `src/core/orchestrator.py` | Adapted — VN pipeline flow |
| ValidationLayer | `src/validation/validation_layer.py` | Adapted — VN medical rules |
| RuleEngine | `src/validation/rule_engine.py` | Adapted — drug, PII, confidence rules |
| AnomalyDetector | `src/validation/anomaly_detector.py` | Direct copy + VN latency thresholds |
| Pipeline staging p0-p3 | `src/pipeline/p0-p3/__init__.py` | Wrapper pattern từ CA |
| QA gates pre-commit | `.pre-commit-config.yaml` | 3 gates: tests+bandit+coverage |
| GitHub Actions CI | `.github/workflows/ci.yml` | Adapted từ CA ci.yml |
| ISO framework structure | `docs/compliance/` (17 files) | Adapted cho ISO_VN |
| SRS format | `docs/compliance/SRS.md` | VN-specific requirements |
| RTM format | `docs/compliance/RTM.md` | VN SRS→code→test |
| V4 AI review script | `scripts/ai_model_review.py` | Concept từ CA QA_PLAN |
| Audit hash chain | `src/core/l10_audit_log.py` | Identical pattern |
| 4-layer control model | `docs/compliance/SOFTWARE_ARCHITECTURE.md` | Adapted diagram |

### B. VIẾT MỚI HOÀN TOÀN (không có ở Canada)

| Component | File | Lý do VN-specific |
|---|---|---|
| L1b Drug correction | `src/core/l1b_drug_correct.py` | drug_db.json VN (TT07/2017) |
| L1c Medical NER | `src/core/l1c_ner.py` | VN medical patterns, tiếng Việt |
| L1d ICD-10-VN lookup | `src/core/l1d_icd_lookup.py` | ICD-10-VN (QĐ5837) — không phải ICD-10-CA |
| L4 Human Gate VN | `src/core/l4_human_gate.py` | Luật KCB 2023 Điều 62 |
| L5 PII scan VN | `src/core/l5_pii_scan.py` | CCCD/SĐT/BHYT (NĐ13/2023) |
| L6 Mẫu 15/BV-01 | `src/core/l6_generate_form.py` | TT32/2023 — Canada dùng SOAP |
| L9a PDF Mẫu 15/BV-01 | `src/core/l9a_pdf_export.py` | ReportLab VN form |
| Pydantic models | `src/models/` (4 files) | VN patient model (CCCD, BHYT, VNeID) |
| FastAPI PWA | `src/api/main.py` + `static/index.html` | Mobile-first cho BS VN |
| /api/feedback | `src/api/main.py` | ISO 42001 A.6.2 — Canada không có |
| Data: drug_db.json | `data/reference/drug_db.json` | 110 thuốc VN (TT07+TT28) |
| Data: icd10vn.json | `data/reference/icd10vn.json` | 15,026 mã ICD-10-VN |
| Data: Mẫu 15/BV-01 | `data/reference/MAU_15BV01_fields.py` | TT32/2023 fields |
| Compliance VN | `docs/compliance/` (GLOSSARY, SCOPE, REFERENCED_STANDARDS...) | VN law specific |
| Audio test files | `data/Voices/` (22 WAV) | Real audio cho BENCH-001 |

### C. CHỈNH SỬA TỪ CANADA (adapt)

| Component | Canada | VN adaptation |
|---|---|---|
| L0 normalize | Audio purge ✅ | Thêm `purge_audio()` SRS-L0-003 |
| L1a ASR | Whisper (EN) + PhoWhisper (VI) | PhoWhisper-small only (VI) |
| L2 Validate | WER gate + drug check | Confidence scoring + VN fields |
| L3 Route | FLOW_A/B/C/D | lam_sang/cdha/nha_khoa/EN-option |
| L7 Storage | SQLite 7yr PIPEDA | SQLite 10yr TT32/2023 + Fernet |
| AI_POLICY | PIPEDA focus | NĐ13/2023 + Luật AI 134/2025 |

---

## 3. KIẾN TRÚC HIỆN TẠI

```
src/
├── core/          L0-L10 pipeline (14 layers) + Orchestrator
├── pipeline/      p0/p1/p2/p3 staging (wrappers)
├── validation/    ValidationLayer: RuleEngine + AnomalyDetector
├── models/        Patient, ClinicalRecord, Facility, AuditEntry
├── api/           FastAPI + PWA (mobile-first)
├── audit/         ImmutableLedger (existing)
├── governance/    HumanGate (existing)
└── risk/          RiskEngine (existing)

docs/
├── compliance/    17 files (full ISO 9001+42001)
├── product/       VISION.md, BRS.md
├── dev/           QA_PLAN, TEST_PLAN, KPI_METRICS, NAMING_CONVENTION
└── records/       BACKLOG, DECISIONS, LAST_SESSION, AI_REVIEW_BASELINE
```

---

## 4. QA STATUS

| Gate | Tool | Result |
|---|---|---|
| Tests | pytest | ✅ 165/165 PASS |
| Coverage | pytest-cov | ✅ 88% (≥80%) |
| Security | bandit | ✅ 0 HIGH/MEDIUM |
| V4 AI review | scripts/ai_model_review.py | ✅ 5/5 PASS (baseline saved) |
| CI/CD | GitHub Actions | ✅ Configured |

---

## 5. SO SÁNH VỚI CANADA (MediVoice_AI v2.61.3)

| Dimension | Canada | Vietnam |
|---|---|---|
| Pipeline | L0-L10 hoàn chỉnh | ✅ L0-L10 hoàn chỉnh |
| Architecture | 4-layer control | ✅ 4-layer control (adapted) |
| Tests | 643 (nhưng 25 fail) | ✅ **165/165 PASS** |
| Coverage | ~80%+ | ✅ **88%** |
| Output | SOAP (EN) | Mẫu 15/BV-01 (VI) |
| NER model | PhoBERT+CRF trained | Rule-based (Phase 0) |
| Deploy | HF Spaces live | Local (Phase 0) |
| Voices | MediVoice + Dental | ✅ **22 WAV + 10 VN** |

---

## 6. AUDIO FILES — BENCH-001 SẴN SÀNG

```
data/Voices/
  test_viet_01-10.wav    ← 10 Vietnamese audio files ← BENCH-001 NGAY
  test_medivoice_01-10.wav  ← 10 MediVoice AI audio (từ Canada)
  test_dental_01-02.wav  ← 2 dental audio
```

**BENCH-001 có thể chạy ngay** — không cần chờ Đà Nẵng nữa cho initial benchmark.
Sau pilot Đà Nẵng sẽ bổ sung audio thực tế của BS VN.

---

## 7. PHẦN CHƯA LÀM (Phase 1)

| Priority | Item | Loại |
|---|---|---|
| 🔴 | BENCH-001: Chạy PhoWhisper trên test_viet_*.wav | Có thể làm NGAY |
| 🔴 | DEPLOY-001: Package installer Windows | Cần trước pilot |
| 🟡 | VN-FLOW-CDHA: CĐHA forms (siêu âm, X-quang...) | Phase 1 |
| 🟡 | PhoBERT+CRF VN trained | Phase 1 sau pilot |
| 🟡 | Patient management M1 | Phase 1 |
| 🟡 | MarianMT EN option | Phase 1 |
| 🟡 | FAISS KB y tế VN | Phase 1 |
| 🟢 | Appointment booking M2 | Phase 1 |
| 🟢 | Revenue tracking M3 | Phase 1 |

---

## 8. DECISIONS SỬA TRONG PHIÊN NÀY

1. **"Documentation Assistant"** = transcription + form MAPPING (không phải "no reasoning")
2. **MarianMT** = option Phase 1 (không phải exclude)
3. **CĐHA forms** = specialized per modality (không phải single plugin)
4. **Audio purge** = bắt buộc sau transcription (SRS-L0-003, NĐ13/2023)

---

*MV-VN-FINAL-REPORT-20260604 | v0.3.0 | 165/165 PASS | 2026-06-04*
