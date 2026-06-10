# PROJECT_PROGRESS.md | DS-VN-REC-PROGRESS
# MediVoice VN — Bảng Theo Dõi Tiến Độ Toàn Dự Án
# Cập nhật: 2026-06-10 | v0.11.4
# Owner: Andy Phan — Maple Leaf Group

---

## LEGEND

| Ký hiệu | Ý nghĩa |
|---|---|
| 🟢 | **DONE** — Hoàn thành |
| 🔵 | **PARTIAL** — Đang làm / hoàn thành một phần |
| 🔴 | **BLOCKED** — Bị chặn, cần unblock trước |
| ⏳ | **PENDING** — Chưa bắt đầu |
| 🟡 | **WAITING** — Chờ điều kiện bên ngoài |

---

## BẢNG TIẾN ĐỘ TOÀN DỰ ÁN

| # | Lưu đồ | Chức năng | Status | Task ID | Phiên hoàn thành | Ghi chú |
|---|---|---|---|---|---|---|
| | **▼ START** | | | | | |
| | | | | | | |
| **P0** | **══════════════** | | | | | |
| **P0** | **PHASE 0 — MVP** | BS nói → Mẫu 15/BV-01 → PDF | 🔵 | — | — | Demo app local OK · LangChain RAG deployed · L1b FP fix |
| **P0** | **══════════════** | | | | | |
| | | | | | | |
| P0.1 | ├─ 🟢 **Design** | VISION, BRS, PROJECT_KICKOFF S1-S9, 32 decisions locked | 🟢 | — | SES-20260603 | Andy ký S10 còn treo |
| P0.1a | │  ├─ VISION.md | Tầm nhìn, 3 gói, 9 modules, roadmap | 🟢 | — | SES-20260603 | |
| P0.1b | │  ├─ BRS.md | Business requirements, user stories, constraints | 🟢 | — | SES-20260603 | |
| P0.1c | │  ├─ PROJECT_KICKOFF | S1-S9: legal scan, tech scan, market, solution | 🟢 | — | SES-20260603 | S10 Andy ký sau |
| P0.1d | │  └─ DECISIONS.md | 47 ADRs — kiến trúc, pháp lý, kỹ thuật | 🟢 | — | SES-20260606 | Thêm 15 ADR mới |
| | │ | | | | | |
| P0.2 | ├─ 🟢 **Implement L0→L10** | AI Pipeline đầy đủ + FastAPI PWA | 🟢 | — | SES-20260608d | GAP-003 ✅ GAP-004 ✅ — 322/322 PASS |
| P0.2.L0 | │  ├─ L0 Normalize | 16kHz mono, VAD, hash, purge audio | 🟢 | — | SES-20260604 | NĐ13/2023 |
| P0.2.L1a | │  ├─ L1a PhoWhisper ASR | Nhận dạng giọng nói VN, offline, chunk 10s | 🟢 | — | SES-20260608e | **Upgraded medium** — better accent/drug coverage. WER 36-52% chưa fine-tune |
| P0.2.L1b | │  ├─ L1b Drug Correct | Sửa tên thuốc về INN, alias map 110+ thuốc | 🟢 | — | SES-20260604 | |
| P0.2.L1c | │  ├─ L1c NER VN | Rule-based: vitals, drugs, diagnosis, follow-up | 🟢 | FID-VN-005 | SES-20260608e | 11 bugs fixed A-01/A-02/A-03 — real-world testing |
| P0.2.L1d | │  ├─ L1d ICD-10-VN | Auto-lookup 15,026 mã (QĐ5837/BYT) | 🟢 | — | SES-20260604 | |
| P0.2.L2 | │  ├─ L2 Validate | Confidence scoring, weighted fields | 🟢 | — | SES-20260604 | |
| P0.2.L3 | │  ├─ L3 Route | lam_sang/cdha/nha_khoa + transcript fallback | 🟢 | — | SES-20260606 | Bug fix: transcript fallback |
| P0.2.L4 | │  ├─ L4 Human Gate | BS approve bắt buộc — per-drug mandatory confirm | 🟢 | L4-REDESIGN-001 | SES-20260609b | Luật KCB Đ.62 · ✅ L4-REDESIGN-001 DONE — per-drug st.checkbox gate, disabled until all confirmed |
| P0.2.L5 | │  ├─ L5 PII Scan | CCCD/SĐT/BHYT/email — NĐ13/2023 | 🟢 | GAP-002 | SES-20260604 | 27 unit tests ✅ |
| P0.2.L6 | │  ├─ L6 Form Gen | NER → BenhAnNgoaiTru (Mẫu 15/BV-01) | 🟢 | FID-VN-004 | SES-20260607 | VN NER direct mapping |
| P0.2.L7 | │  ├─ L7 Storage | SQLite + WAL + Fernet encryption | 🟢 | — | SES-20260604 | |
| P0.2.L8 | │  ├─ L8 Recovery | Error handling, @with_recovery | 🟢 | GAP-003 ✅ | SES-20260608d | 20 tests PASS `tests/unit/test_l8_error_handler.py` |
| P0.2.L9a | │  ├─ L9a PDF | Mẫu 15/BV-01 ReportLab + disclaimer | 🟢 | GAP-004 ✅ | SES-20260608d | 15 tests PASS `tests/unit/test_l9a_pdf_export.py` |
| P0.2.L10 | │  └─ L10 Audit Log | SHA-256 hash chain, append-only, 10 năm | 🟢 | — | SES-20260604 | |
| | │ | | | | | |
| P0.2.API | │  ├─ FastAPI PWA | Doctor UI: record → review → approve → PDF | 🟢 | GAP-005 | SES-20260604 | 18 integration tests ✅ |
| P0.2.CA | │  └─ Canada Pipeline Port | L0→L9 Canada (MarianMT + SOAP) cho NER quality | 🟢 | — | SES-20260605 | Dùng nội bộ |
| | │ | | | | | |
| P0.3 | ├─ 🟢 **Benchmark BENCH-001** | PhoWhisper + Canada pipeline trên 22 audio | 🟢 | BENCH-001 | SES-20260605 | T-007 10/10, T-005 20/22 PASS |
| P0.3a | │  ├─ T-007 WER | eval_phowhisper.py — WER 36-52%, RTF 0.5x | 🟢 | — | SES-20260605 | |
| P0.3b | │  └─ T-005 Pipeline | Canada pipeline 20/22 PASS (91%) | 🟢 | — | SES-20260605 | 2 FAIL hợp lệ (silence) |
| | │ | | | | | |
| P0.4 | ├─ 🟢 **Design Review** | DESIGN_REPORT v1.1 + ISO audit system | 🟢 | — | SES-20260606 | Full system design confirmed |
| P0.4a | │  ├─ DESIGN_REPORT v1.1 | Master design 21 sections, 700+ dòng | 🟢 | — | SES-20260606 | docs/records/ |
| P0.4b | │  ├─ ISO Audit System | iso_audit.py + session counter + weekly trigger | 🟢 | — | SES-20260606 | |
| P0.4c | │  ├─ AI Memory System | 5-tier memory + CONFUSION_PATTERNS (25 patterns) | 🟢 | — | SES-20260606 | |
| P0.4d | │  ├─ Consultation Template | Multi-AI consultation workflow | 🟢 | — | SES-20260606 | |
| P0.4e | │  ├─ PENDING_REQUESTS | PA/CT/TP tracking system | 🟢 | — | SES-20260606 | |
| P0.4f | │  ├─ ISO Docs Mới | DPA, INCIDENT_PLAN, BS_ONBOARDING | 🟢 | — | SES-20260606 | |
| P0.4g | │  └─ Bug Fixes (4) | trieu_chung, patient_name, l3 transcript, qua_trinh | 🟢 | — | SES-20260606 | 210 tests PASS |
| | │ | | | | | |
| **P0.5** | **├─ 🟢 VN-ROUTER-001** | **L6 branch: NER → Mẫu 15/BV-01 trực tiếp** | **🟢** | **FID-VN-004** | SES-20260606 | **232 tests PASS** |
| P0.5a | │  ├─ FID-VN-004 | Feature Intent Document | 🟢 | CT-001 | SES-20260606 | fids/FID-VN-004.md DONE |
| P0.5b | │  ├─ l3_routing vn_route | detect_vn_route() trong Canada L3 | 🟢 | CT-002 | SES-20260606 | 14 tests PASS |
| P0.5c | │  ├─ l6_agent dispatch | lam_sang → benh_an / cdha → SOAP | 🟢 | CT-002 | SES-20260606 | AC-001 AC-002 PASS |
| P0.5d | │  └─ l6_mau15_generator | generate_mau15(): NER → form_data → generate_benh_an() | 🟢 | CT-002 | SES-20260606 | 22 new tests PASS |
| | │ | | | | | |
| **P0.5.1** | **├─ 🟢 VN-NER-002** | **VN word-form numbers → vital extraction fixed** | **🟢** | **FID-VN-005** | SES-20260607 | **272 tests PASS** |
| P0.5.1a | │  ├─ FID-VN-005 | Feature Intent Document — approved Andy | 🟢 | — | SES-20260607 | fids/FID-VN-005.md DONE |
| P0.5.1b | │  ├─ _normalize_vn_numbers() | PhoWhisper word-form → digits trước NER regex | 🟢 | FID-VN-005 | SES-20260607 | "tám mươi"→80 |
| P0.5.1c | │  ├─ generate_mau15_from_vn_ner() | MedicalEntities direct mapping (không qua Canada NER) | 🟢 | FID-VN-005 | SES-20260607 | Root cause fix |
| P0.5.1d | │  ├─ l6_agent lam_sang | original VI text → l1c_ner (không qua MarianMT) | 🟢 | FID-VN-005 | SES-20260607 | Canada path (cdha) giữ nguyên |
| P0.5.1e | │  └─ test_l1c_vn_numbers | 40 tests: _vn_to_int, normalize, TC-001/002/003 | 🟢 | FID-VN-005 | SES-20260607 | bench_ceer tc_001/002: vital=True ✅ |
| | │ | | | | | |
| **P0.5.2** | **├─ 🔵 BENCH-002 Baseline** | **Lâm sàng vùng miền: 10 files, Vitals✅ Diag✅ Drug🔴(v1) Followup✅(0.1)** | **🔵** | **BENCH-002** | SES-20260608 | **Drug🔴 = v1 engine 2026-06-08. Engine v2 → CONS-002-EVAL 99.5%✅. Re-run benchmark để confirm pipeline.** |
| P0.5.2a | │  ├─ gen_test_audio.py | Tạo WAV từ JSON template (gTTS → 16kHz mono) | 🟢 | — | SES-20260608 | `tools/gen_test_audio.py` |
| P0.5.2b | │  ├─ bench_ceer --gt flag | Whitelist filtering, fix AUDIO_TOO_LONG | 🟢 | — | SES-20260608 | `tools/bench_ceer.py` |
| P0.5.2c | │  ├─ 10 vùng miền template | Hà Nội→Kiên Giang, ground truth đầy đủ | 🟢 | PA-006 | SES-20260608 | `data/audio/ground_truth_lam_sang_template.json` |
| P0.5.2d | │  ├─ CEER Drug baseline | Drug=0.9🔴 → DEFERRED | 🟡 | CT-006 | — | Blocked: TRAIN-001 cần 50-100h audio thật. Andy approved defer 2026-06-08 |
| P0.5.2e | │  ├─ CEER Followup baseline | Followup=0.7🔴 → **0.1✅** | 🟢 | CT-007 | SES-20260608 | _RE_TAI_KHAM captures extra context (kèm/nếu/xét nghiệm). binh_dinh=TRAIN-001 dep. |
| P0.5.2f | │  └─ Data tổ chức | dental/ folder tách riêng, xóa 22 duplicates | 🟢 | — | SES-20260608 | `data/audio/dental/` |
| | │ | | | | | |
| **P0.6** | **├─ 🟢 DEPLOY-001** | **Windows installer cho BS Đà Nẵng** | **🟢** | **CT-005** | SES-20260608 | install.bat + start.bat + check_env + setup_facility + facility_config |
| P0.6a | │  ├─ Python venv bundle | install.bat — check Python + create venv + pip install | 🟢 | CT-005 | SES-20260608 | `install.bat` |
| P0.6b | │  ├─ Model cache | check_env.py checks PhoWhisper cache (~150MB tự download) | 🟢 | CT-005 | SES-20260608 | `scripts/check_env.py` |
| P0.6c | │  └─ Setup wizard | setup_facility.py + facility_config.json template | 🟢 | CT-005 | SES-20260608 | `scripts/setup_facility.py` |
| | │ | | | | | |
| **P0.6.1** | **├─ 🟢 L4 Correction Capture** | **Implicit supervision — BS edits = training labels** | **🟢** | **FID-VN-006** | SES-20260608f | 14 tests PASS — hook approve_record(), analyze_corrections.py |
| P0.6.1a | │  ├─ l4_correction_capture.py | diff AI→BS form_data, log JSONL per-clinic | 🟢 | FID-VN-006 | SES-20260608f | `src/core/l4_correction_capture.py` |
| P0.6.1b | │  ├─ analyze_corrections.py | CLI tool: alias suggestions, drug miss freq table | 🟢 | FID-VN-006 | SES-20260608f | `scripts/analyze_corrections.py` |
| P0.6.1c | │  └─ test_l4_correction_capture.py | AC-001→AC-005, 14 tests PASS | 🟢 | FID-VN-006 | SES-20260608f | `tests/unit/test_l4_correction_capture.py` |
| | │ | | | | | |
| **P0.6.2** | **├─ 🟢 Synthetic NER + Data** | **10K BIO samples · 17 scenarios · chan_doan fix · drug_db 118 · pipeline test** | **🟢** | SYNTHETIC-NER-001 | SES-20260607 | 395/395 PASS |
| P0.6.2a | │  ├─ generate_synthetic_ner.py | 17 scenarios × 4 regions — BIO format, 10K samples | 🟢 | — | SES-20260607 | `scripts/generate_synthetic_ner.py` |
| P0.6.2b | │  ├─ test_synthetic_ner_pipeline.py | 7 tests — drug 97-100% · CD 63-80% · vital 63-77% | 🟢 | — | SES-20260607 | `tests/unit/test_synthetic_ner_pipeline.py` |
| P0.6.2c | │  ├─ chan_doan regex fix | ". filler Kê" pattern · ICD code · "gout" fallback · "bị" trigger | 🟢 | NER-BUGFIX-004 | SES-20260607 | `src/core/l1c_ner.py` |
| P0.6.2d | │  ├─ drug_db.json v0.3.0 | 118 drugs + PhoWhisper aliases (Glimepiride/Colchicine/Etoricoxib/Metformin/Omeprazole/VitB) | 🟢 | DRUG-ALIAS-001 | SES-20260610 | `data/reference/drug_db.json` |
| P0.6.2e | │  ├─ VietMed family (partial) | VietMed-NER 9K · Sum 106K · QA 9K — `data/external/` | 🔵 | DATASET-001 | SES-20260607 | VietMed audio 2.5GB + ViMedCSS 4GB còn lại |
| P0.6.2f | │  └─ DATA_CATALOG.md | 26 datasets, license/domain/download status | 🟢 | — | SES-20260607 | `docs/dev/DATA_CATALOG.md` |
| | │ | | | | | |
| **P0.6.3** | **├─ 🟢 BENCH-002a + TRAIN-002 Overnight** | **Semi-synthetic CEER · 10K NER · PhoBERT F1=99.44% · 409 PASS** | **🟢** | BENCH-002a+TRAIN-002 | SES-20260610 | TRAIN-002 ✅ done |
| P0.6.3a | │  ├─ BENCH-002a CEER | 15 files HN/SG/CT — Drug=0.967✅ Diag=0.667⚠️ Vital=0.333🔴 | 🟢 | — | SES-20260607 | `tools/bench_ceer_semi.py` |
| P0.6.3b | │  ├─ ner_semantic_test.py | HYP transcript test — BS1 7/7=100% · BS2 6/7=86% (post-fix) | 🟢 | — | SES-20260610 | `tools/ner_semantic_test.py` |
| P0.6.3c | │  ├─ wer_clinical_test.py | WER test trên clinical WAV — semi_synthetic + real | 🟢 | — | SES-20260610 | `tools/wer_clinical_test.py` |
| P0.6.3d | │  ├─ TRAIN-002 ✅ DONE | PhoBERT NER 3 epochs: E1=98.95% · E2=98.73% · E3=**99.44%** best | 🟢 | TRAIN-002 | SES-20260610 | `models/ner_phobert/best/` (512MB) |
| P0.6.3e | │  ├─ NER Bug K/L/M/K2 fixes | SG colloquial BP · nhiet_do digit-split · nặng+ký · abbreviated tens · +10 tests | 🟢 | BUG-K2 | SES-20260610 | `src/core/l1c_ner.py` — 409/409 PASS |
| P0.6.3f | │  ├─ NER Bug N fix | chan_doan from "tái khám [disease]" follow-up pattern · +4 tests | 🟢 | BUG-N | SES-20260610 | `src/core/l1c_ner.py` — 409/409 PASS |
| P0.6.3g | │  └─ VietMed audio download ❌ | `trust_remote_code` deprecated · doof-ferb/VietMed gated (cần HF login) | 🔵 | VIETMED-FIX-001 | SES-20260610 | Fix `scripts/download_vietmed.py` + HF_TOKEN |
| | │ | | | | | |
| **P0.6.4** | **├─ 🟢 FID-VN-009 Hybrid NER** | **PARALLEL rule+PhoBERT · optional early-exit · 29 tests · 473 PASS** | **🟢** | **FID-VN-009** | SES-20260610 | **CONS-20260610-003 CLOSED APPROVE_WITH_CHANGES** |
| P0.6.4a | │  ├─ l1c_phobert.py | PhoBERT NER lazy load · lru_cache · confidence thresholds 0.85/0.75/0.60 | 🟢 | FID-VN-009 | SES-20260610 | `src/core/l1c_phobert.py` |
| P0.6.4b | │  ├─ extract_entities_hybrid() | PARALLEL: rule-based luôn chạy · PhoBERT supplement gaps | 🟢 | FID-VN-009 | SES-20260610 | `src/core/l1c_ner.py` |
| P0.6.4c | │  ├─ VITAL meta-only | VITAL → meta["phobert_vital_detected"] · không viết vào MedicalEntities | 🟢 | FID-VN-009 | SES-20260610 | R-009-12: conditional FOLLOWUP guard |
| P0.6.4d | │  └─ test_l1c_phobert_hybrid.py | 29 tests — backward compat · early-exit · dedup · fallback · meta | 🟢 | FID-VN-009 | SES-20260610 | `tests/unit/test_l1c_phobert_hybrid.py` |
| | │ | | | | | |
| **P0.6.5** | **├─ 🟢 CONS-002-EVAL Drug Eval** | **204 cases · GO: Recall=99.5% FP=0.0% Safety=92.1% Phonetic=98.7%** | **🟢** | **CONS-002-EVAL** | SES-20260610 | **✅ GO — DrugCorrectionEngine v2 production-ready** |
| P0.6.5a | │  ├─ generate_drug_eval_dataset.py | 204 cases: clean=90 noisy=76 dangerous=38 · seed + templates | 🟢 | CONS-002-EVAL | SES-20260610 | `scripts/generate_drug_eval_dataset.py` |
| P0.6.5b | │  ├─ eval_drug_correction.py | 4 metrics: Drug Recall / Silent FP / Safety Catch / Phonetic Recall | 🟢 | CONS-002-EVAL | SES-20260610 | `scripts/eval_drug_correction.py` |
| P0.6.5c | │  ├─ drug_correction_eval.json | 204 ground-truth cases v1.0.0 | 🟢 | CONS-002-EVAL | SES-20260610 | `data/eval/drug_correction_eval.json` |
| P0.6.5d | │  └─ Known issues | "a zi thro my xin" FN · "metro" AMBIGUOUS miss (3/38) | 🔵 | — | — | Log để cải tiến sau pilot |
| | │ | | | | | |
| **P0.6.6** | **├─ 🟢 Real Voice Testing + Consultation** | **9 sessions Drive · L4 safety finding · 6 AI reviews · CONS-002 complete** | **🟢** | CONS-20260608-002 | SES-20260609 | BENCH-002b partial: Drug Recall local=13-18% vs Cloud=78% |
| P0.6.6a | │  ├─ Drive session analysis | 9 JSON+WAV sessions 2026-06-08 afternoon · 5 scripted + 4 real voice | 🟢 | — | SES-20260609 | `data/drive-download-20260609T031416Z-3-001/` |
| P0.6.6b | │  ├─ CONS-20260608-002 rewrite | Full consultation: 8 data sections + 4 root causes + Options A-G + prioritized roadmap | 🟢 | — | SES-20260609 | `docs/records/consultations/CONS-20260608-002.md` (644 dòng) |
| P0.6.6c | │  ├─ CONS-20260610-003 update | 6 AI reviews: ChatGPT + Grok + Copilot independent reviews saved | 🟢 | — | SES-20260609 | `docs/records/consultations/CONS-20260610-003.md` (852 dòng) |
| P0.6.6d | │  └─ FID-VN-010 DRAFT | AI Pipeline Redesign v2.0 — A1+A2+A3+RAG+UI+L4-redesign | 🔵 | FID-VN-010 | SES-20260609 | `fids/FID-VN-010.md` · Phase 0 A1✅A2✅A3✅L4✅ · RAG-001+UI-SUGGEST-001 còn lại |
| | │ | | | | | |
| | │ | | | | | |
| **P0.6.7** | **├─ 🟢 FID-VN-010 Phase 0** | **A1+A2+A3+L4+RAG+UI+Hybrid — 755 tests** | **🟢** | **FID-VN-010** | SES-20260609c | A1✅ A2✅ A3✅ L4✅ RAG-001✅ RAG-FIX✅ UI-SUGGEST-001✅ |
| P0.6.7a | │  ├─ A1-PROMPT-INJECT | PhoWhisper initial_prompt drug list per specialty | 🟢 | A1 | SES-20260609b | `src/core/l1a_asr.py` · 23 tests |
| P0.6.7b | │  ├─ A2-VAD-CHUNK | silero-vad chunking tại silence tự nhiên, max 20s | 🟢 | A2 | SES-20260609b | `src/core/l0_normalize.py` · 18 tests |
| P0.6.7c | │  ├─ A3-DIALECT-NORM | 200+ entries Trung/Nam/abbrev, region-aware | 🟢 | A3 | SES-20260609b | `src/core/dialect_norm.py` · 49 tests |
| P0.6.7d | │  ├─ L4-REDESIGN-001 | Per-drug mandatory confirm — demo/app.py + PWA index.html | 🟢 | L4 | SES-20260609c | `src/api/static/index.html` — `.drug-confirm-row` + `updateApproveButton()` · disabled until all ✓ |
| P0.6.7e | │  ├─ RAG-001-DRUG-VECTOR | Chroma + MiniLM drug vector store — 80 tests | 🟢 | RAG-001 | SES-20260609c | `src/core/drug_rag.py` · 80 tests |
| P0.6.7f | │  ├─ RAG-001-FIX Hybrid | Hybrid 0.65×fuzzy + 0.35×RAG — fix RC-A/RC-C | 🟢 | RAG-FIX | SES-20260609c | `_build_phonetic_index` + `hybrid_query_drug` · +31 tests |
| P0.6.7g | │  └─ UI-SUGGEST-001 | Drug chips + dialect badge + terminology sidebar — 43 tests | 🟢 | UI-001 | SES-20260609c | `src/api/static/js/suggestions.js` · `src/api/main.py` 3 endpoints |
| | │ | | | | | |
| **P0.6.8** | **├─ 🟢 BENCH-002b Real Voice** | **57 clips BS thật HN/DN/SG · WER=18.4% · Drug=55.6%LB** | **🟢** | **BENCH-002b** | SES-20260609d | WER✅ · Drug🔴LB · Diag⚠️ · findings → TRAIN-001 next |
| P0.6.8a | │  ├─ tools/bench_002b.py | Parse GT TXT → WER (jiwer) + CEER per clip, aggregate by region | 🟢 | BENCH-002b | SES-20260609d | `tools/bench_002b.py` |
| P0.6.8b | │  ├─ WER by region | HN=29.3%⚠️ · DN=16.3%✅ · SG=16.3%✅ · ALL=18.4%✅ | 🟢 | BENCH-002b | SES-20260609d | PhoWhisper untuned good on real BS voice |
| P0.6.8c | │  ├─ Drug Recall (lower bound) | TP=5 FN=4 FP=1 · Recall=55.6%LB · Precision=83.3% | 🔴 | BENCH-002b | SES-20260609d | GT phonetic spell → undercount · actual recall lower · TRAIN-001 required |
| P0.6.8d | │  ├─ Missed drugs | Ciprofloxacin · Paracetamol · Vitamin B1 · Folic acid | 🔴 | BENCH-002b | SES-20260609d | Add phonetic_variants to drug_db.json |
| P0.6.8e | │  └─ bench_002b_results.json | Full per-clip results: wer, gt_drugs, pred_drugs, ceer | 🟢 | BENCH-002b | SES-20260609d | `data/eval/bench_002b_results.json` |
| | │ | | | | | |
| **P0.6.9** | **├─ 🟢 FID-VN-011 + DRUG-DB-002 + TEST-E2E-001** | **L1b RAG Layer 3b + preload · 154 INNs · 22 E2E tests** | **🟢** | **FID-VN-011** | SES-20260609e/f | v0.10.0→v0.10.1 · 772→794 tests |
| P0.6.9a | │  ├─ FID-VN-011 RAG Layer 3b | `src/core/l1b_drug_correct.py` — `_rag_fallback_match()` + Layer 3b (score≥0.68) | 🟢 | FID-VN-011 | SES-20260609e | `tests/unit/test_l1b_rag_layer3.py` 17 tests |
| P0.6.9b | │  ├─ Model preload singleton | `src/api/main.py` — `_embed_model`+`_drug_collection` preload at startup | 🟢 | FID-VN-011 | SES-20260609e | Eliminate 3-5s cold start per API call |
| P0.6.9c | │  ├─ DRUG-DB-002 | `data/reference/drug_db_v200.json` 146→154 INNs · 9 phonetic variants/drug | 🟢 | DRUG-DB-002 | SES-20260609e | +Erythromycin/AlPO4/Betamethasone/Clindamycin/Lisinopril/Digoxin/Nystatin/Ketoconazole |
| P0.6.9d | │  └─ TEST-E2E-001 | `tests/integration/test_e2e_pipeline.py` 22 tests · pipeline L1b→L10 real | 🟢 | TEST-E2E-001 | SES-20260609f | Structure/NER/L4Gate/PDF/PII/Routing · 794/794 PASS |
| | │ | | | | | |
| **P0.6.10** | **├─ 🟢 FID-VN-012 DVP Layer 1+2** | **Doctor Voice Profile — 12 specialties · 4 endpoints · 23 tests · 817 PASS** | **🟢** | **FID-VN-012** | SES-20260609g | v0.10.1→v0.11.0 · Drug Recall 55.6%→65-75% predicted |
| | │ | | | | | |
| **P0.6.11** | **├─ 🟢 DEMO-002 Demo App v2.1** | **Header Block A/B/C · drug card fixes · button visibility** | **🟢** | **DEMO-002** | SES-20260609h | v0.11.0→v0.11.1 · UX fixes cho pilot |
| P0.6.11a | │  ├─ Header Block A/B/C | BS info (ten/coso/cchn) · DVP (chuyen_khoa/vung_mien/lang) · BN pre-fill | 🟢 | DEMO-002 | SES-20260609h | commit `19334a0` |
| P0.6.11b | │  ├─ Drug card HTML bold | `<b>name</b>` thay vì `**name**` trong div — markdown không render trong HTML | 🟢 | DEMO-002 | SES-20260609h | commit `1d5dd96` |
| P0.6.11c | │  ├─ Skip empty drug entries | `if not _name.strip(): continue` — LLM blank entries | 🟢 | DEMO-002 | SES-20260609h | commit `1d5dd96` |
| P0.6.11d | │  ├─ Checkbox default True | `value=True` — thuốc pre-confirmed, BS bỏ tick để từ chối | 🟢 | DEMO-002 | SES-20260609h | commit `1d5dd96` |
| P0.6.11e | │  └─ Button visibility | Phê duyệt & Lưu moved inside container right after drug section | 🟢 | DEMO-002 | SES-20260609h | commit `1d5dd96` |
| P0.6.10a | │  ├─ DoctorProfile model | `src/models/doctor_profile.py` — 12 specialties, 3 regions, DoctorAlias schema | 🟢 | FID-VN-012 | SES-20260609g | VALID_SPECIALTIES + SPECIALTY_DISPLAY |
| P0.6.10b | │  ├─ l7_storage DVP CRUD | doctor_profiles + doctor_aliases tables · save/load/alias full CRUD | 🟢 | FID-VN-012 | SES-20260609g | Migration-safe CREATE TABLE IF NOT EXISTS |
| P0.6.10c | │  ├─ SPECIALTY_DRUG_CLASSES 12 | `src/core/l1a_asr.py` — 12 canonical + 6 legacy aliases | 🟢 | FID-VN-012 | SES-20260609g | cdha=None · mat/noi_tiet/than_tiet_nieu new |
| P0.6.10d | │  ├─ dvp_alias.py Layer 3 | check_and_promote · apply_active_aliases · record_correction (pilot-gated) | 🟢 | FID-VN-012 | SES-20260609g | `src/core/dvp_alias.py` |
| P0.6.10e | │  ├─ Pipeline injection | main.py: specialty→L1a A1 + region→A3 dialect + dvp_specialty/dvp_region in response | 🟢 | FID-VN-012 | SES-20260609g | 4 new endpoints: POST /api/doctors + GET + aliases pending + confirm |
| P0.6.10f | │  └─ test_dvp.py | 23 tests AC-001→AC-010 · DB schema · CRUD · pipeline · alias Human Gate | 🟢 | FID-VN-012 | SES-20260609g | 817/817 PASS · 0 regressions |
| | │ | | | | | |
| **P0.6.12** | **├─ 🔵 ORCH-001 Orchestrator v1.0 PROTOTYPE** | **CLI: start/consult/check/close — gọi Groq API thật** | **🔵** | **ORCH-001** | SES-20260609i | `scripts/orchestrator.py` (~190 LOC) — chưa qua FID đầy đủ |
| P0.6.12a | │  ├─ start_session() | Load iso_audit + LAST_SESSION + BACKLOG + PENDING_REQUESTS | 🟢 | ORCH-001 | SES-20260609i | Chạy thật, output verified |
| P0.6.12b | │  ├─ consult(topic, question) | Groq API (`requests`, llama-3.3-70b-versatile) → JSON evidence | 🟢 | ORCH-001 | SES-20260609i | `docs/records/consultations/ORCH-CONSULT-20260609-184913.json` |
| P0.6.12c | │  ├─ consistency_check() | 2x Groq (temp 0.1/0.7) + AGREEMENTS/CONFLICTS/RECOMMENDATION | 🟢 | ORCH-001 | SES-20260609i | `docs/records/consultations/ORCH-CONSULT-20260609-184931.json` |
| P0.6.12d | │  └─ close_session() | In checklist 6 bước (chưa tự động update docs) | 🟡 | ORCH-001 | SES-20260609i | Chưa làm: detect_confusion(), create_consultation_request() |
| | │ | | | | | |
| **P0.6.13** | **├─ 🟡 CT-018+CT-015 NER fix + DVP UI · A2-VAD REVERTED** | **Digit BP/nhiệt độ "là" fix · DVP registration card · A2 wire→revert** | **🟡** | **CT-018/015/019** | SES-20260609j | v0.11.2→v0.11.3 · 817/817 PASS |
| P0.6.13a | │  ├─ CT-018 NER fix | `_RE_BP_DIGITS` "120 trên cao 80"→120/80 · `_RE_NHIET_DO` chấp nhận "là" | 🟢 | CT-018 | SES-20260609j | `src/core/l1c_ner.py` commit `91c4369` |
| P0.6.13b | │  ├─ CT-015 DVP Layer 1 UI | Card "🩺 Trợ lý AI của Bác sĩ" — register/edit, localStorage `mv_doctor_cchn` | 🟢 | CT-015 | SES-20260609j | `src/api/static/index.html` commit `271b82a` |
| P0.6.13c | │  └─ A2-VAD wire→REVERT | Wired vào `/transcribe` → live test "KHÔNG NHẬN DẠNG ĐƯỢC GÌ LUÔN" → revert ngay | 🔴 | CT-019 | SES-20260609j | commits `270cea3`→`271b82a` · cần debug offline (per-chunk vs whole-file) |
| | │ | | | | | |
| **P0.6.14** | **├─ 🟢 CT-030/031/032/034 + CT-023 L4 UI + CT-028 decision** | **Real Clip 1-3 NER/drug fixes · L4 nút Xóa thuốc · Groq hybrid REJECTED** | **🟢** | **CT-023/028/029/030-034** | SES-20260610 | v0.11.3→v0.11.4 · 826/826 PASS |
| P0.6.14a | │  ├─ CT-030/031 NER fix | Mạch (pulse) "mật"+mất "lần" · Chẩn đoán/ICD-10 "theo dõi"→"theo thì" | 🟢 | CT-030/031 | SES-20260610 | `src/core/l1c_ner.py` commit `8d5f983` |
| P0.6.14b | │  ├─ CT-032 NER fix | Fix bổ sung từ Real Clip 1-3 test | 🟢 | CT-032 | SES-20260610 | `src/core/l1c_ner.py` commit `8d5f983` |
| P0.6.14c | │  ├─ CT-034 Drug DB | "pha ra citamon"→Paracetamol alias + RAG vectorstore rebuild | 🟢 | CT-034 | SES-20260610 | `src/core/l1b_drug_correct.py` commit `aa9bea1` |
| P0.6.14d | │  ├─ CT-029 Groq benchmark | 57 real clips: WER 18.4% local vs 32.6% Groq · Drug Precision 83.3% vs 57.1% · Diag CEER 0.286 vs 0.429 · Groq Drug Recall 88.9% vs 55.6% (nhưng hallucination chưa fix) | 🟢 | CT-029 | SES-20260610 | branch `experiment/groq-degallucination` (CT-026+CT-029, KHÔNG merge) |
| P0.6.14e | │  ├─ CT-028 quyết định | Andy: GIỮ 100% local pipeline, KHÔNG hybrid Groq. Ưu tiên TRAIN-001. `experiment/groq-degallucination` giữ làm reference, mở lại khi cần so sánh | 🟢 | CT-028 | SES-20260610 | `docs/records/PENDING_REQUESTS.md` |
| P0.6.14f | │  └─ CT-023 L4 nút Xóa thuốc | Per-drug "🗑️ Xóa" trong L4 confirm list — `_currentDrugs`/`_drugConfirmed`, `buildEditedFormData()` dùng list sau khi xóa → mitigates CT-022/CT-033 | 🟢 | CT-023 | SES-20260610 | `src/api/static/index.html` commit `2c3186a` |
| | │ | | | | | |
| **P0.7** | **└─ 🟡 PILOT Đà Nẵng + SG** | **5 BS dùng thật + thu audio thực tế** | **🟡** | — | — | Chờ P0.6 done + PA-006 |
| P0.7a |    ├─ BS Onboarding | Andy trực tiếp cài + hướng dẫn | 🔵 | ONBOARD-001 | SES-20260606 | BS onboarding checklist ĐÃ KÝ |
| P0.7b |    ├─ DPA ký | Hợp đồng xử lý dữ liệu | 🟡 | PA-003 | — | Luật sư review xong → ký |
| P0.7c |    ├─ BENCH-002 thật | Record 30-50 audio thật → CEER thật | 🟡 | PA-006 | — | Chờ pilot deploy |
| P0.7d |    └─ LEGAL-001 | Luật sư VN review DPA + tư vấn | 🔵 | LEGAL-001 | SES-20260606 | Email đã gửi |
| | | | | | |
| | **▼** | | | | |
| | | | | | |
| **P1** | **══════════════** | | | | |
| **P1** | **PHASE 1 — Complete Product** | M1-M7 + Plugins + Staff Screen | ⏳ | — | Sau 5 paying users |
| **P1** | **══════════════** | | | | |
| | | | | | |
| P1.M1 | ├─ M1 Patient Mgmt | Hồ sơ BN đầy đủ, CCCD scan, QR thẻ | ⏳ | — | |
| P1.M2 | ├─ M2 Booking Engine | 7 states + buffer + waitlist + D-1/H-2/H-15p | ⏳ | — | |
| P1.M4 | ├─ M4 Email Auto-processor | 3 điều kiện + quarantine | ⏳ | — | |
| P1.M5 | ├─ M5 Referral 2 chiều | Deal %, commission tracking (no money) | ⏳ | — | Gói 3 |
| P1.M6 | ├─ M6 Zalo + Email | Text→Zalo, File→Email, Post-care CRM | ⏳ | — | |
| P1.M7 | ├─ M7 VN Cloud | VNG/FPT/VNPT sync | ⏳ | — | |
| P1.QMS | ├─ Queue Management | Số thứ tự + TTS loa | ⏳ | — | |
| P1.STAFF | ├─ Staff Screen (Mode B) | Tiếp nhận + admin gộp | ⏳ | — | STAFF-001 |
| P1.AFTERCARE | ├─ Post-care CRM | D+2/D+4/D+7 wellness check | ⏳ | — | |
| P1.WEBSITE | ├─ Website Widget | Booking embed + REST API | ⏳ | — | |
| P1.CDHA | ├─ Plugin CĐHA | Báo cáo siêu âm/X-quang (FID-VN-001) | ⏳ | — | |
| P1.NHA | ├─ Plugin Nha khoa | Mẫu 16/BV-01 (FID-VN-002) | ⏳ | — | |
| P1.TRAIN | ├─ TRAIN-001 | Fine-tune PhoWhisper 50-100h audio | ⏳ | — | Sau pilot |
| P1.LEGAL | └─ LEGAL-001 sign-off | Luật sư ký → launch thương mại | 🔵 | — | Email gửi rồi |
| | | | | | |
| | **▼** | | | | |
| | | | | | |
| **P2** | **══════════════** | | | | |
| **P2** | **PHASE 2 — TT13 Compliance** | Chữ ký số + FHIR + HL7 | ⏳ | — | Deadline 31/12/2026 |
| **P2** | **══════════════** | | | | |
| | | | | | |
| P2.SIGN | ├─ Chữ ký số BS | TT13/2025 — ký số bệnh án | ⏳ | — | |
| P2.HL7 | ├─ HL7 v2 Export | BravoSoft / FPT.eHospital | ⏳ | — | |
| P2.FHIR | ├─ FHIR R4 Export | Khi TT13/2025 thực sự enforce | ⏳ | — | |
| P2.M9 | ├─ M9 HIS Integration | API partners | ⏳ | — | Gói 3 |
| P2.AUDIT | └─ BYT Audit Export | L10 audit log export chuẩn | ⏳ | — | |
| | | | | | |
| | **▼** | | | | |
| | | | | | |
| **P3** | **══════════════** | | | | |
| **P3** | **PHASE 3 — Scale + Conformity** | 500+ phòng, Luật AI 134 | ⏳ | — | Trước 01/09/2027 |
| **P3** | **══════════════** | | | | |
| | | | | | |
| P3.CONF | ├─ Conformity Assessment | Luật AI 134/2025 — budget 80-200M VND | ⏳ | — | |
| P3.VNEID | ├─ VNeID API | Khi BYT publish | ⏳ | — | |
| P3.BHYT | ├─ BHYT Check | Real-time eligibility | ⏳ | — | |
| P3.PARTNER | ├─ FPT/Viettel Partnership | Plugin/add-on 400+ BV | ⏳ | — | Sau 100+ users |
| P3.IVR | └─ IVR Phone Booking | VoIP + SIP | ⏳ | — | |
| | | | | | |
| | **▼ END** | | | | |

---

## PHIÊN TIẾP THEO — LÀM GÌ?

### ⚡ NGAY BÂY GIỜ — v0.11.4 · TRAIN-001 ưu tiên cao nhất (per CT-028)

| # | Task | Ai | Điều kiện |
|---|---|---|---|
| 1 | **TRAIN-001 🔴** — Fine-tune PhoWhisper trên 50-100h audio thật | Andy + Claude | 🔴 Drug Recall 55.6%LB / Diag CEER chưa đạt — quyết định CT-028 (2026-06-10): KHÔNG hybrid Groq, chỉ fine-tune giải quyết được |
| 2 | **CT-019 🔴** — Debug A2 VAD-chunk regression: A/B test per-chunk vs whole-file transcript offline (script riêng, KHÔNG wire vào `/transcribe` cho đến khi rõ nguyên nhân hallucination) | Claude | Cần audio mẫu (data/audio/) |
| 3 | **ORCH-001 FID** — Viết FID cho Orchestrator v1.0 đầy đủ (`detect_confusion`, `create_consultation_request`, tự động `close_session`) | Claude | Andy approve scope trước khi +100 LOC |
| 4 | **VIETMED-FIX-001** — Fix `scripts/download_vietmed.py` remove `trust_remote_code` + HF_TOKEN (~5 LOC) | Claude | Làm được ngay |
| 5 | **CT-016/CT-017/CT-014** — chờ Andy cung cấp audio+GT / GG Drive JSON key path / mô tả flow calibration | Andy | Chờ Andy |
| 6 | **Pilot Đà Nẵng** — Cài install.bat thật tại phòng khám → thu audio → TRAIN-001 | Andy | Code sẵn sàng · DVP needs real doctor CCHN |
| 7 | **PA-013** — Revoke `medivoice-bench` Groq API key trên console.groq.com (KHÔNG đụng `medivoice-demo`) | Andy | Key đã expose trong chat phiên CT-029 |

### 🟡 BENCHMARK TIẾP THEO

| # | Task |
|---|---|
| BENCH-003 | Re-run sau FID-VN-011 + drug_db 154 INNs → đo Drug Recall improvement vs 55.6%LB |
| BENCH-PILOT | Record 50-100h audio thật → CEER thật → GO criteria cho TRAIN-001 |

---

## METRICS HIỆN TẠI (2026-06-10 · v0.11.4)

| KPI | Target | Actual | Status |
|---|---|---|---|
| Tests PASS | 100% | **826/826** | 🟢 |
| **Drug Recall Groq vs local (CT-029)** | ≥70% | Groq=88.9% (hallucination chưa fix) vs local=55.6%LB | 🔴 TRAIN-001 required (Groq REJECTED — CT-028) |
| **Diag CEER Groq vs local (CT-029)** | <30% | local=0.286 vs Groq=0.429 | 🟢 local thắng |
| bandit | 0 HIGH/MEDIUM | 0/0 | 🟢 |
| Vital extraction (TC audio) | >0% | bench tc_001/tc_002: vital=True | 🟢 fixed FID-VN-005 |
| WER semi-synthetic | <30% | SG 25.8% · CT 30.4% · HN 34.6% | 🟡 cần fine-tune |
| **WER real BS voice (BENCH-002b)** | **<20%** | **ALL=18.4%✅ · DN/SG=16.3%✅ · HN=29.3%⚠️** | **🟢 OK (untuned)** |
| NER BS1 (Bắc chuẩn, WER=8%) | >80% | **7/7 = 100%** | 🟢 |
| NER BS2 (Nam nhanh, WER=19%) | >80% | **6/7 = 86%** (post-fix BUG-K/L/M) | 🟢 |
| CEER Drug (semi-synthetic) | <10% | 0.967 (Drug 97%) | ✅ |
| CEER Diag (semi-synthetic) | <10% | 0.667 | ⚠️ cần pilot thật |
| **Drug Recall real (BENCH-002b LB)** | **≥70%** | **55.6% LB** (GT phonetic miss → actual lower) | **🔴 TRAIN-001 required** |
| **Diag CEER real (BENCH-002b)** | **<30%** | ALL=71.4% · DN/SG=83.3%✅ · HN=0%🔴 | 🟡 HN blocked by WER |
| **Vitals CEER real (BENCH-002b)** | **<30%** | 69.3% ALL | 🟡 |
| TRAIN-002 PhoBERT NER | F1 > 0.70 | **F1=99.44%** (epoch 3, synthetic data) | ✅ |
| **Drug Recall (CONS-002-EVAL, synthetic)** | **≥88%** | **99.5%** | **✅ GO (synthetic)** |
| **Silent FP Rate (CONS-002-EVAL)** | **≤10%** | **0.0%** | **✅ GO** |
| **Safety Catch (CONS-002-EVAL)** | **≥80%** | **92.1%** | **✅ GO** |
| **Phonetic Recall (CONS-002-EVAL)** | **≥85%** | **98.7%** | **✅ GO** |
| **Drug Recall real BS voice (local pipeline)** | **≥70%** | **55.6%LB** (BENCH-002b) | **🔴 CRITICAL GAP** |
| **L4 Human Gate safety** | 0 drug substitution | Per-drug confirm gate ✅ DONE | 🟢 L4-REDESIGN-001 SES-20260609b |
| BS approve rate | >85% | ❓ chưa pilot | ⏳ |
| NPS | >7/10 | ❓ chưa pilot | ⏳ |
| Paying users | ≥5 | 0 | ⏳ |

---

## LỊCH SỬ PHIÊN

| Phiên | Ngày | Version | Highlights |
|---|---|---|---|
| SES-20260602 | 2026-06-02 | — | ~15h research thị trường VN |
| SES-20260603 | 2026-06-03 | v0.1→v0.2 | Design + ISO framework + 32 decisions |
| SES-20260604 | 2026-06-04 | v0.2→v0.3 | L0→L10 implement + FastAPI PWA (165 tests) |
| SES-20260605 | 2026-06-05 | v0.3→v0.4 | Canada pipeline port + BENCH-001 (T-005 20/22) |
| SES-20260606 | 2026-06-06 | v0.4→v0.4.5 | Design review + ISO audit + 4 bugs fixed (210 tests) |
| SES-20260606b | 2026-06-06 | v0.4.5→v0.5.0 | VN-ROUTER-001 DONE — L6 branch FID-VN-004 (232 tests) |
| SES-20260607 | 2026-06-07 | v0.5.0→v0.5.1 | VN-NER-002 DONE — FID-VN-005 word-form numbers (272 tests) |
| SES-20260608 | 2026-06-08 | v0.5.1→v0.5.2 | BENCH-002 baseline lâm sàng 10 vùng miền + tools + data organization |
| SES-20260608b | 2026-06-08 | v0.5.2→v0.5.3 | CT-007 DONE — Followup CEER 0.7→0.1 (tai_kham regex extended) + Naming Convention v1.2 |
| SES-20260608c | 2026-06-08 | v0.5.3→v0.6.0 | CT-005 DEPLOY-001 DONE — install.bat + start.bat + check_env + setup_facility (287 tests) |
| SES-20260608d | 2026-06-08 | v0.6.0→v0.6.1 | GAP-003 ✅ GAP-004 ✅ — 35 unit tests L8+L9a (322 tests total) |
| SES-20260608e | 2026-06-08 | v0.6.1→v0.6.3 | Real-world test A-01/A-02/A-03 — 11 NER+ICD bugs fixed — 352 tests — Adaptive Learning arch doc |
| SES-20260608f | 2026-06-08 | v0.6.3→v0.7.0 | FID-VN-006 L4 Correction Capture — 14 new tests — 366 tests total |
| SES-20260607 | 2026-06-07 | v0.7.0→v0.7.1 | Synthetic NER 10K · 17 scenarios · chan_doan fix · VietMed download (395 tests) |
| SES-20260607b | 2026-06-07 | v0.7.1→v0.7.2 | BENCH-002a · CEER semi-synthetic (15 files) · overnight scripts · conftest SKIP_QWEN fix |
| SES-20260610 | 2026-06-10 | v0.7.2 | TRAIN-002 overnight started · ner_semantic_test · wer_clinical_test tools committed |
| SES-20260610b | 2026-06-10 | v0.7.2 | TRAIN-002 ✅ DONE F1=99.44% · BUG-K2+BUG-N fix · 409/409 · Drug corpus analysis · Canadian MedVoice benchmark |
| SES-20260609 | 2026-06-09 | v0.8.5 | Real voice testing 9 sessions Drive · CONS-20260608-002 rewrite (644 dòng) · CONS-20260610-003 6 AI reviews · FID-VN-010 DRAFT (AI Pipeline Redesign v2.0) · DESIGN_REPORT §15 → v2.0 |
| SES-20260609b | 2026-06-09 | v0.8.5→v0.8.6 | FID-VN-010 Phase 0: A1✅ A2✅ A3✅ L4-REDESIGN✅ · 473→678 tests (+205) |
| SES-20260609c | 2026-06-09 | v0.8.6→v0.9.0 | RAG-001-FIX Hybrid ✅ · UI-SUGGEST-001 ✅ · L4-PWA ✅ · 678→755 tests (+77) |
| SES-20260609d | 2026-06-09 | v0.9.0→v0.9.1 | BENCH-002b ✅ — 57 clips real BS voice WER=18.4% Drug=55.6%LB · tools/bench_002b.py |
| SES-20260609e | 2026-06-09 | v0.9.1→v0.10.0 | FID-VN-011 ✅ L1b Layer 3b RAG + preload · DRUG-DB-002 ✅ 154 INNs · 772 tests |
| SES-20260609f | 2026-06-09 | v0.10.0→v0.10.1 | TEST-E2E-001 ✅ 22 E2E integration tests · pipeline L1b→L10 real · 794/794 PASS |
| SES-20260609g | 2026-06-09 | v0.10.1→v0.11.0 | FID-VN-012 ✅ DVP Layer 1+2 · 12 specialties · 4 endpoints · 23 tests · 817/817 PASS |
| SES-20260609h | 2026-06-09 | v0.11.0→v0.11.1 | DEMO-002 ✅ Demo App v2.1 · Header Block A/B/C · drug card HTML bold · checkbox True · button visibility fix |
| SES-20260609i | 2026-06-09 | v0.11.1 | ORCH-001 PROTOTYPE ✅ — `scripts/orchestrator.py` start/consult/check/close · Groq API real test (consult + consistency check) · SESSION_CAPTURE_RULES integrated (commit `c9e1392`) · 6-category LAST_SESSION template demo |
| SES-20260609j | 2026-06-09 | v0.11.2→v0.11.3 | CT-018 ✅ NER fix (BP digits + nhiệt độ "là") · CT-015 ✅ DVP Layer 1 registration UI · A2-VAD wired vào `/transcribe` rồi REVERTED ngay (CT-019 🔴 — live test "KHÔNG NHẬN DẠNG ĐƯỢC GÌ LUÔN") · 817/817 PASS |
| SES-20260610 | 2026-06-10 | v0.11.3→v0.11.4 | CT-030/031/032 ✅ NER fix Real Clip 1-3 · CT-034 ✅ drug alias "pha ra citamon" + RAG rebuild · merge `experiment/local-accuracy`→master · CT-029 ✅ Groq benchmark 57 clips (local thắng WER/Drug Precision/Diag CEER) · CT-028 ✅ quyết định: 100% local, KHÔNG hybrid Groq, ưu tiên TRAIN-001 · `experiment/groq-degallucination` giữ làm reference (KHÔNG merge) · CT-023 ✅ L4 nút "🗑️ Xóa thuốc" · 826/826 PASS |

---

*DS-VN-REC-PROGRESS | PROJECT_PROGRESS v1.9 | 2026-06-10*
*Cập nhật mỗi phiên đóng. Đọc cùng BACKLOG.md + PENDING_REQUESTS.md*
