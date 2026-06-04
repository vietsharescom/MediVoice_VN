# SOFTWARE_ARCHITECTURE.md | DS-VN-COM-009
# ISO/IEC 12207:2017 Architecture Definition
# ISO/IEC 42001:2023 Clause 8.4 — AI System Lifecycle
# Học từ MediVoice_AI v2.61.3 | Adapted cho VN
# v1.0 | 2026-06-04

---

## 1. TỔNG QUAN HỆ THỐNG

MediVoice VN implement kiến trúc 4-layer governed AI pipeline.
Mọi AI execution là pipeline-bound, validated, auditable, và human-controlled.

> Nguyên tắc: AI viết nháp nhanh — BS không thể review hết.
> Giải pháp: ValidationLayer pre-screens mọi thứ. BS chỉ tham gia tại Critical Control Points.

---

## 2. MÔ HÌNH 4-LAYER CONTROL

```
┌────────────────────────────────────────────────────────────────┐
│ LAYER 1 — AI GENERATION (ISO 42001 Cl.8)                       │
│ Pipeline: L0 → L1a → L1b → L1c → L1d → L2 → L3               │
│           → L4 → L5 → L6 → L7 → L8 → L9a → L10               │
│ AI executes ONLY at L1a (ASR) + L1c (NER) — bounded           │
└────────────────────────────────────────────────────────────────┘
         ↓ output → feeds into ↓
┌────────────────────────────────────────────────────────────────┐
│ LAYER 2 — AI VALIDATION (ISO 42001 Cl.6.1 + 8.5 + 9.1)        │
│ ValidationLayer (chạy SONG SONG với pipeline):                  │
│  ① RuleEngine     — deterministic, không bị thuyết phục       │
│  ② AnomalyDetector — statistical drift detection               │
└────────────────────────────────────────────────────────────────┘
         ↓ escalates critical issues ↓
┌────────────────────────────────────────────────────────────────┐
│ LAYER 3 — GOVERNANCE / RISK (ISO 42001 Cl.6.1 + 8.2)           │
│  RiskEngine        — dynamic scoring (src/risk/)               │
│  ImmutableLedger   — hash-chain audit log (L10)                │
└────────────────────────────────────────────────────────────────┘
         ↓ CCPs escalated to ↓
┌────────────────────────────────────────────────────────────────┐
│ LAYER 4 — HUMAN + EXTERNAL AUDIT (ISO 42001 Cl.5.3 + 9.2)     │
│  HumanGate    — BS approve tại L4 (Luật KCB 2023 Đ.62)       │
│  Feedback API — /api/feedback (ISO 42001 A.6.2)                │
│  AuditChain   — verify_chain() hàng tuần                       │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. PIPELINE FLOW (FROZEN)

```
INPUT (audio)
  → L0_NORMALIZE    [p0_ingestion]   16kHz mono PCM, chunking 10s
  → L1a_ASR         [p1_processing]  PhoWhisper-small VI ★
  → L1b_DRUG        [p1_processing]  Drug INN correction
  → L1c_NER         [p1_processing]  Medical NER (regex Phase 0)
  → L1d_ICD         [p1_processing]  ICD-10-VN lookup (15,026 mã)
  → L2_VALIDATE     [p1_processing]  Schema + confidence scoring
  → L3_ROUTE        [p1_processing]  lam_sang / cdha / nha_khoa
  → L4_HUMAN_GATE   [p2_decision]    ★ CCP: BS approve (Luật KCB Đ.62)
  → L5_PII_SCAN     [p2_decision]    CCCD/SĐT/BHYT detection
  → L6_FORM_GEN     [p2_decision]    ★ CCP: Mẫu 15/BV-01 generation
  → L7_STORAGE      [p2_decision]    SQLite + WAL + Fernet
  → L8_ERROR        [p3_output]      Error handling + recovery
  → L9a_PDF         [p3_output]      PDF export
  → L10_AUDIT       [p3_output]      Immutable hash-chain log
  → OUTPUT (FastAPI PWA)

★ = Critical Control Point (CCP) — cần BS involvement
```

---

## 4. COMPONENT STRUCTURE

```
src/
├── core/              Pipeline layers L0–L10 (implementation)
│   ├── l0_normalize.py
│   ├── l1a_asr.py    l1b_drug_correct.py    l1c_ner.py    l1d_icd_lookup.py
│   ├── l2_validate.py    l3_route.py
│   ├── l4_human_gate.py    l5_pii_scan.py    l6_generate_form.py
│   ├── l7_storage.py    l8_error_handler.py    l9a_pdf_export.py
│   ├── l10_audit_log.py
│   └── orchestrator.py        ← NEW: Central execution controller
├── pipeline/          Stage grouping (wrapper around core/)
│   ├── p0_ingestion/    l0
│   ├── p1_processing/   l1a, l1b, l1c, l1d, l2, l3
│   ├── p2_decision/     l4, l5, l6, l7
│   └── p3_output/       l8, l9a, l10
├── validation/        Validation Layer (NEW — học từ MediVoice_AI)
│   ├── rule_engine.py       Deterministic VN medical rules
│   ├── anomaly_detector.py  Statistical drift detection
│   └── validation_layer.py  Composite layer
├── models/            Pydantic data models
│   ├── patient.py    clinical_record.py    facility.py    audit_entry.py
├── api/               FastAPI + PWA
│   ├── main.py
│   └── static/index.html
├── audit/             ImmutableLedger (existing)
├── governance/        HumanGate (existing)
└── risk/              RiskEngine (existing)

docs/
├── compliance/        9 docs ISO 9001+42001
├── product/           VISION.md, BRS.md
├── dev/               NAMING_CONVENTION.md, KPI_METRICS.md
└── records/           BACKLOG.md, DECISIONS.md, LAST_SESSION.md
```

---

## 5. CRITICAL CONTROL POINTS (VN)

| Stage | CCP Type | Luật | Hành động | BS Required |
|---|---|---|---|---|
| L4_HUMAN_GATE | Authorization gate | KCB 2023 Đ.62 | halt | YES — bắt buộc pháp lý |
| L6_FORM_GEN | AI output gate | AI 134/2025 | review | YES — human oversight |

---

## 6. DATA FLOW VN

```
Audio (mic/upload)
  ↓ L0: 16kHz mono
  ↓ L1a: transcript VI
  ↓ L1b: drug names corrected
  ↓ L1c: {nhiet_do, huyet_ap, chan_doan, don_thuoc, ...}
  ↓ L1d: {icd_code: "J02", icd_display: "Viêm họng cấp"}
  ↓ L2: form_data + confidence=0.81
  ↓ L3: route="lam_sang"
  ↓ [BS reviews draft in PWA]
  ↓ L4: approve(doctor_cchn="CCHN-012345")
  ↓ L5: pii_detected=[]
  ↓ L6: BenhAnNgoaiTru (Mẫu 15/BV-01)
  ↓ L7: SQLite encrypted record
  ↓ L9a: PDF → BS tải về / share Zalo
  ↓ L10: audit_log entry với SHA-256 hash
```

---

## 7. KHÁC BIỆT SO VỚI MediVoice_AI (Canada)

| Aspect | MediVoice_AI (CA) | MediVoice_VN |
|---|---|---|
| Core pipeline | Canada pipeline L0→L9 | **Canada pipeline GIỮ NGUYÊN** (2026-06-05) |
| Output lâm sàng | SOAP note (EN) | SOAP → VN router → **Mẫu 15/BV-01 (VI)** |
| Output CĐHA | SOAP note (EN) | **SOAP giữ nguyên** (S/O/A/P phù hợp imaging) |
| Privacy law | PIPEDA | NĐ13/2023 |
| Patient ID | SHA-256(OHIP) | CCCD nullable, VNeID-ready |
| ASR | PhoWhisper-small + Whisper-small | **PhoWhisper-small** (Whisper optional) |
| Translation | MarianMT VI→EN (output) | **MarianMT VI→EN (NER nội bộ)** — output vẫn VI |
| NER | l6_soap_generator (regex + PhoBERT) | **l6_soap_generator từ Canada** (2026-06-05) |
| KB | FAISS Clinical KB | **FAISS KB từ Canada** active (2026-06-05) |
| Qwen DDx | Qwen reasoner | Template DDx fallback (Qwen Phase 2) |
| Deploy | HF Spaces + Docker | Local + VN Cloud |
| Compliance | PIPEDA + ISO_CA | NĐ13 + TT32 + Luật KCB + Luật AI 134 |

---

*DS-VN-COM-009 | SOFTWARE_ARCHITECTURE v1.0 | ISO/IEC 12207:2017 | 2026-06-04*
