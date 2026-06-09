# BACKLOG.md — MediVoice VN
# v0.9.1 — Updated 2026-06-09
# Single source of truth cho tasks.

---

## IMMEDIATE — TRƯỚC KHI LAUNCH

- [x] **LEGAL-001** ✅ Luật sư VN review xong — trước khi launch
- [x] **BENCH-001** ✅ Benchmark PhoWhisper trên 22 audio — WER 36–52%, T-005 20/22 PASS (2026-06-05)
- [x] **BENCH-002a** ✅ Semi-synthetic CEER: 3 regions VI-only, 15 files (2026-06-07 · v2 re-run 2026-06-11)
  - ✅ Andy ghi âm 40 files: HN/SG/CT/CA × 5 SC × 2 takes (CA dropped từ benchmark)
  - ✅ CA/BS4 dropped: PhoWhisper không handle code-switch EN/VN (WER 101%)
  - WER VI-only: SG 25.8% | CT 30.4% | HN 34.6%
  - **v2 engine re-run (2026-06-11):**
  - CEER Overall: Drug=0.989🔴 | Diag=0.667🔴 | Vital=0.272⚠️ | Fup=0.400🔴
  - CEER by region: CT (Drug=0.9 Diag=0.4 Vital=0.15) | HN (Drug=0.9 Diag=0.6 Vital=0.5) | SG (Drug=1.167🔴 Diag=1.0 Vital=0.167)
  - ⚠️ SG Drug=1.167 > 1.0: FP drugs detected (engine hallucinate trên ASR garbled output)
  - ✅ `tools/bench_ceer_semi.py` — CEER tool cho groundtruth_all.json format
  - **Root cause: ASR bottleneck — PhoWhisper mangling drug names → L1b không tìm được**
  - **Kết luận: BENCH-002b (pilot thật) + TRAIN-001 bắt buộc trước GO**
- [x] **BENCH-002b** ✅ CEER thật trên 57 real-voice clips BS (HN/DN/SG) — 2026-06-09
  - `tools/bench_002b.py` + `data/eval/bench_002b_results.json`
  - **WER**: HN=29.3% · DN=16.3% · SG=16.3% · **Overall=18.4%** ← PhoWhisper tốt trên giọng thật
  - **Drug Recall**: 55.6% lower bound (GT NER miss phonetic-spelled drugs → actual thấp hơn)
  - **Drug Precision**: 83.3% (FP thấp ✅)
  - **Diag Accuracy**: 71.4% overall (DN/SG=83.3%✅ · HN=0%🔴 do WER cao)
  - **Vitals Accuracy**: 69.3% overall (DN/SG OK · HN thấp)
  - **Followup Accuracy**: 72.7% overall (SG=100%✅)
  - Missed drugs: Ciprofloxacin · Paracetamol · Vitamin B1 · Folic acid
  - Root cause drug miss: BS spell-out phonetic "MÉt PHỐT min" → L1b không nhận → cần TRAIN-001
  - ✅ PA-009 done: Andy điền đủ 57/57 GT clips

### FID-VN-010 PIPELINE REDESIGN — Phase 0 [IMMEDIATE, sau BENCH-002b pending]
> Evidence: BENCH-002b 2026-06-08 | FID: `fids/FID-VN-010.md` | Prerequisite: A1+A2+A3 trước khi bật bất kỳ ML layer mới

- [x] **A1-PROMPT-INJECT** ✅ Whisper prompt injection — bias PhoWhisper decoder về drug vocabulary (2026-06-09)
  - `src/core/l1a_asr.py` — `SPECIALTY_DRUG_CLASSES` + `get_drugs_by_specialty()` + `build_initial_prompt()`
  - `transcribe()` / `transcribe_file()` / `transcribe_chunks()` nhận `drug_db` + `specialty` params
  - `tests/unit/test_l1a_prompt_inject.py` — 23 tests PASS | Total: 496/496
  - Graceful fallback khi transformers version không support `initial_prompt`
- [x] **A2-VAD-CHUNK** ✅ VAD silence-aware chunking — thay fixed 10s chunk (2026-06-09)
  - `src/core/l0_normalize.py` — `_merge_short_gaps()` + `vad_chunk_audio()`
  - `silero-vad==6.2.1` thêm vào `requirements.txt` + `requirements-prod.txt`
  - Max chunk 20s, gap_ms 500ms, auto-split nếu vượt, fallback về `chunk_audio()` cũ
  - `tests/unit/test_l0_vad_chunk.py` — 18 tests PASS | Total: 514/514
- [x] **A3-DIALECT-NORM** ✅ Dialect normalization + abbreviation expansion (2026-06-09)
  - `src/core/dialect_norm.py` — DIALECT_MAP 200+ entries (central/southern/northern/medical_abbrev)
  - `detect_region()` + `normalize_dialect()` + `expand_abbreviations()` + `normalize_text()`
  - ⚠️ "ốm" handled correctly: bệnh (central) ≠ gầy (southern) — region-aware
  - Multi-word phrases matched trước single-word (sort by length desc)
  - `tests/unit/test_l1a_dialect_norm.py` — 49 tests PASS | Total: 563/563
- [x] **L4-REDESIGN-001** ✅ Per-drug mandatory confirm UI — safety critical (2026-06-09)
  - `demo/app.py` — per-drug `st.checkbox` + `_all_drugs_confirmed` gate + `disabled=not _all_drugs_confirmed`
  - Flagged drugs (L1b drug_flags): hiện `st.warning` + confidence % thay vì static card
  - Reset drug_confirm keys khi new result / Từ chối / Khám BN tiếp theo
  - **PWA update (2026-06-09)**: `src/api/static/index.html` — `.drug-confirm-row` per-drug checkbox + `updateApproveButton()` disabled until all ✓ + L4 safety guard trong `approveRecord()`
  - 755/755 tests PASS | Evidence: Session 174116 Losartan→Atorvastatin safety failure
- [x] **RAG-001-DRUG-VECTOR** ✅ Drug Vector Store — Chroma + multilingual MiniLM (2026-06-09)
  - `src/core/drug_rag.py` — `build_drug_vectorstore()` + `query_drug_rag()` + `query_drug_rag_from_file()`
  - Build từ `data/reference/drug_db_v200.json` (146 INN, phonetic_variants)
  - Persist: `data/drug_vectorstore/` (gitignored)
  - `tests/unit/test_drug_rag.py` — 80 tests PASS | Total: 721/721
- [x] **RAG-001-FIX** ✅ Hybrid fuzzy+RAG query — fix phonetic recall (2026-06-09)
  - `src/core/drug_rag.py` — `_build_phonetic_index()` + `_fuzzy_phonetic_search()` + `hybrid_query_drug()` + `hybrid_query_drug_from_file()`
  - Score: 0.65 × RapidFuzz token_set_ratio + 0.35 × RAG cosine similarity
  - Fix RC-A (MiniLM not phonetic) và RC-C (missing phonetic variants)
  - `src/api/main.py` `/api/drug-candidates` endpoint → dùng `hybrid_query_drug()`
  - +31 new tests (TestBuildPhoneticIndex 9 + TestFuzzyPhoneticSearch 11 + TestHybridQueryDrug 13) | Total: 755/755
- [x] **UI-SUGGEST-001** ✅ Real-time suggestion UI — drug chips + dialect badge + terminology sidebar (2026-06-09)
  - `src/api/static/js/suggestions.js` — Suggestions module: onTranscriptReady + onSpecialtyChange + init
  - `src/api/main.py` — GET `/api/drug-candidates`, GET `/api/terms`, POST `/api/dialect-check`
  - `src/api/static/index.html` — drug chips panel + dialect badge + term sidebar + specialty selector
  - `tests/unit/test_api_suggestions.py` — 43 tests PASS | Total: 755/755
- [x] **BENCH-GT-001** ✅ Andy điền 57/57 GT clips `data/eval/ref_voice_transcripts_review.txt` — 2026-06-09
- [x] **FID-VN-011** ✅ L1b Layer 3b RAG fallback + model preload — 2026-06-09
  - `src/api/main.py` — startup singleton preload `_embed_model` + `_drug_collection`
  - `src/core/l1b_drug_correct.py` — `_rag_fallback_match()` + Layer 3b (score≥0.68 accept)
  - `tests/unit/test_l1b_rag_layer3.py` — 17 tests | Total: 772/772 PASS
- [x] **DRUG-DB-002** ✅ drug_db_v200.json 146 → 154 INNs — 2026-06-09
  - +8: Erythromycin · Aluminium phosphate · Betamethasone · Clindamycin · Lisinopril · Digoxin · Nystatin · Ketoconazole
  - 9 phonetic variants/drug (3 regions) | `scripts/add_drugs_002.py`
- [x] **TEST-E2E-001** ✅ End-to-end pipeline tests — 2026-06-09
  - `tests/integration/test_e2e_pipeline.py` — 22 tests PASS
  - Coverage: pipeline structure (6) · NER extraction (5) · L4 gate (4) · PDF (3) · PII (2) · routing (2)
  - Mock L1a ASR with `ground_truth_lam_sang_template.json`; all downstream layers run real
  - Total: 794/794 PASS
- [x] **DEMO-001** ✅ Streamlit Demo App v2.0 — Pilot data collection + Mẫu 15/BV-01 UI redesign (2026-06-09)
  - `demo/app.py` — 27+ commit history; ISO gap resolved: FID/design documented 2026-06-09
  - **Bug fixed**: `st.audio_input` re-processing on every Streamlit rerun → audio hash guard (`_audio_hash` + `hashlib.md5`)
  - **UI redesign** v2.0: Mẫu 15/BV-01 layout (I. Hành chính · II. Lý do · III. Sinh hiệu · IV. CĐ + ICD · V. Đơn thuốc L4 gate · Tái khám)
  - **L4 per-drug gate**: `st.checkbox` xác nhận từng thuốc — disabled PHÊ DUYỆT until all ✓
  - **Pilot data**: 9 WAV + 10 JSON sessions 2026-06-08 tại DN/SG — `data/drive-download-20260609T031416Z-3-001/`
  - Deploy: `https://medivoice-vn-demo.streamlit.app/` (Streamlit Cloud, auto-redeploy on push)
  - Localhost: `demo_start.bat` → `http://localhost:8501` + localtunnel global URL
  - Secrets (gitignored): `.streamlit/secrets.toml` — add manually in Streamlit Cloud dashboard
  - Design doc: `docs/records/DESIGN_REPORT_v1.1_20260606.md` §21 Demo App (added 2026-06-09)
- [x] **DEMO-002** ✅ Demo App v2.1 — Bug fixes + UX header redesign (2026-06-09 SES-20260609h)
  - **Header Block A/B/C**: Thông tin BS · DVP settings (chuyên khoa + vùng miền + ngôn ngữ) · BN pre-fill
  - **Bug: empty drug** — skip LLM-generated blank `ten` entries (`if not _name.strip(): continue`)
  - **Bug: `**Amoxicillin**`** — markdown bold → `<b>name</b>` HTML trong drug card div
  - **Bug: checkbox default False** → `value=True` (thuốc pre-confirmed, bỏ tick để từ chối)
  - **UX: nút Phê duyệt** — moved inside container right after drug section (không cần scroll)
  - Handler reads `note_giong/noise/bs/correction` từ `st.session_state.get(...)` (defined below)
  - Commit: `1d5dd96` | 817/817 tests PASS (no new tests — demo-only fixes)
- [x] **FID-VN-012** ✅ Doctor Voice Profile (DVP) Layer 1+2 — 2026-06-09
  - `src/models/doctor_profile.py` — DoctorProfile + DoctorAlias (12 specialties, 3 regions)
  - `src/core/l7_storage.py` — doctor_profiles + doctor_aliases tables + full CRUD
  - `src/core/l1a_asr.py` — SPECIALTY_DRUG_CLASSES 12 canonical + 6 legacy
  - `src/core/dvp_alias.py` — alias promotion logic (Layer 3 schema, pilot-gated)
  - `src/api/main.py` — pipeline injection (specialty→L1a, region→A3) + 4 DVP endpoints
  - `tests/unit/test_dvp.py` — 23 tests AC-001→AC-010 PASS | Total: 817/817
  - Predicted Drug Recall: 55.6% → 65-75% (Layer 1+2), 80-90% (Layer 3 mature)
- [~] **ORCH-001** 🔵 Orchestrator v1.0 — PROTOTYPE multi-AI chạy được (2026-06-09 SES-20260609i)
  - Source: `Andy/Improvements.md` → `docs/dev/SESSION_CAPTURE_RULES.md`
  - File: `scripts/orchestrator.py` (~250 LOC) — CLI: `start | consult | check | close`
  - **Done**: `start_session()` (load ISO audit + LAST_SESSION + BACKLOG + PENDING) ✅
  - **Done**: `multi_ai_consult()` + `_PROVIDERS` registry — Groq/OpenAI/xAI qua `_openai_compatible_call()` chung ✅
  - **Done**: `consult(topic, question)` — gọi tất cả providers, lưu JSON evidence vào `docs/records/consultations/` ✅
  - **Done**: `consistency_check(topic, question)` — query tất cả providers + Groq phân tích AGREEMENTS/CONFLICTS/RECOMMENDATION ✅
  - **Done**: `close_session()` — in checklist 6 bước (chưa tự động hóa, chỉ reminder)
  - **Provider status (2026-06-09)**:
    - Groq/LLaMA-3.3-70B ✅ hoạt động (free tier)
    - OpenAI/GPT-4o-mini ⚠️ key hợp lệ nhưng HTTP 429 — hết quota/chưa add billing (`platform.openai.com`)
    - xAI/Grok-2 ⚠️ key hợp lệ nhưng HTTP 403 — team chưa có credits (`console.x.ai`)
  - **Demo evidence**: `docs/records/consultations/ORCH-CONSULT-20260609-184913.json`, `*-184931.json`, `*-195003.json` (multi-provider, Groq output thật + OpenAI/xAI skip reasons)
  - **Chưa làm**: `detect_confusion()`, `create_consultation_request()` (CONSULTATION_TEMPLATE format), tự động hóa `close_session()` (chưa tự update docs)
  - Prerequisite for full v1.0: FID cần Andy approve (> 100 LOC tổng + new module + ghi đè LAST_SESSION tự động)
  - Priority: Phase 1 (sau pilot Đà Nẵng — khi cần scale multi-AI consultation)
- [ ] **TRAIN-001** ⏳ Fine-tune PhoWhisper trên 50-100h real clinical audio — cần audio thật từ pilot
- [x] **GAP-002** ✅ Unit tests PII scan — tests/unit/test_pii_scan.py 27 tests PASS (2026-06-06)
- [x] **GAP-003** ✅ Unit tests L8 error handler — `tests/unit/test_l8_error_handler.py` 20 tests PASS (2026-06-08) | P0.2.L8
- [x] **GAP-004** ✅ Unit tests L9a PDF export — `tests/unit/test_l9a_pdf_export.py` 15 tests PASS (2026-06-08) | P0.2.L9a
- [x] **GAP-005** ✅ API integration tests — tests/integration/test_api.py 18 tests PASS (2026-06-06)
- [x] **FID-VN-004** ✅ Feature Intent Document VN-ROUTER-001 — Andy approved 2026-06-06
- [x] **VN-ROUTER-001** ✅ L6 branch: lam_sang→Mẫu15/BV-01 | cdha→SOAP — 232 tests PASS (2026-06-06)
- [x] **VN-NER-002** ✅ [FID-VN-005] VN word-to-number + L6 lam_sang dùng VN NER — 272 tests PASS (2026-06-07)
  - _normalize_vn_numbers() — PhoWhisper word-form → digits
  - generate_mau15_from_vn_ner() — MedicalEntities direct mapping
  - bench_ceer tc_001/tc_002: vital=True, followup=True

- [x] **DPA-SIGN-001** ✅ Andy ký `docs/compliance/DPA_TEMPLATE.md` với BS pilot Đà Nẵng (2026-06-08)
- [x] **ONBOARD-001** ✅ Andy ký `docs/compliance/BS_ONBOARDING_CHECKLIST.md` với BS pilot — DONE
- [ ] **BENCH-002b** 🟡 Pilot thật: record 30-50 audio tại Đà Nẵng → CEER thật (sau BENCH-002a)
- [x] **LEGAL-001** ✅ Luật sư VN review DPA + tư vấn pháp lý — DONE

---

## PHASE 0 — MVP ✅ PIPELINE DONE — Còn lại: FID + VN-Router + Deploy

**Mục tiêu:** BS nói → Mẫu 15/BV-01 → PDF → local save → BS approve
**Target user:** 5–10 BS phòng mạch tư Đà Nẵng + Sài Gòn
**Success:** 5 BS trả tiền

### Core Pipeline ✅ DONE 2026-06-04
- [x] **L0:** Audio normalize (16kHz mono, VAD) — librosa + soundfile
- [x] **L1a:** PhoWhisper streaming chunk 10s (lazy-load, graceful degradation)
- [x] **L1b:** Drug name correction engine — alias map, n-gram matching
- [x] **L1c:** Medical NER rule-based — regex sinh hiệu, chẩn đoán, đơn thuốc
- [x] **L1d:** ICD-10-VN auto-lookup — substring search 15,026 mã
- [x] **L2:** Schema validation + confidence scoring — weighted fields
- [x] **L3:** Route detection — lam_sang default, CDHA/nha_khoa keywords
- [x] **L4:** Human Gate — state machine PENDING_REVIEW→APPROVED/REJECTED
- [x] **L5:** PII scan — CCCD, SĐT, BHYT, email regex (NĐ13/2023)
- [x] **L6:** Generate Mẫu 15/BV-01 (TT32/2023)
- [x] **L7:** SQLite + WAL + Fernet encryption
- [x] **L8:** Error handling + recovery — @with_recovery, @safe_log
- [x] **L9a:** PDF export (Mẫu 15/BV-01 ReportLab, disclaimer bắt buộc)
- [x] **L10:** Immutable audit log (SHA-256 hash chain, append-only)

### Data Models ✅ DONE 2026-06-04
- [x] **DATA-001:** Patient schema (Pydantic v2, VNeID-ready)
- [x] **DATA-002:** Clinical record schema + RecordStatus enum
- [x] **DATA-003:** Audit log schema (hash chain, BYT-sync-ready)
- [x] **DATA-004:** Facility schema (byt_registration_number, province_code)

### App Shell ✅ DONE 2026-06-04 (FastAPI PWA)
- [x] **APP-001:** FastAPI app — /api/transcribe + approve + reject + pdf
- [x] **APP-002:** SQLite offline-first architecture
- [x] **APP-003:** CCHN input + disclaimer bắt buộc
- [x] **APP-004:** Doctor voice recording UI (MediaRecorder, hold to record)
- [x] **APP-005:** Draft review form (edit fields + approve/reject)
- [x] **APP-006:** PDF download Mẫu 15/BV-01

### Phase 0 Còn Lại
- [x] **BENCH-001** ✅ T-005 20/22 PASS | T-007 10/10 PASS | WER 29–52% | SOAP 20/20 (2026-06-05)
- [x] **FID-VN-004** ✅ Feature Intent Document cho VN-ROUTER-001 (2026-06-06)
- [x] **VN-ROUTER-001** ✅ L6 branch: NER entities → BenhAnNgoaiTru (2026-06-06)
- [x] **BENCH-002-BASELINE** ✅ Lâm sàng synthetic 10 vùng miền — Vitals 0.033, Diag 0.1 (2026-06-08)
  - `tools/gen_test_audio.py` — tạo WAV từ JSON template
  - `bench_ceer.py --gt` flag — whitelist filtering
  - `data/audio/dental/` — dental audio tách riêng
- [ ] **TEST-E2E-001** 🟡 End-to-end test full pipeline với audio thực tế (sau DEPLOY-001)
- [x] **DEPLOY-001** ✅ Windows venv installer cho BS Đà Nẵng (2026-06-08)
  - `install.bat` — one-click installer (Python check + venv + pip + config)
  - `start.bat` — daily launcher (auto-open browser)
  - `scripts/check_env.py` — pre-flight checks (Python, disk, packages, port)
  - `scripts/setup_facility.py` — interactive facility config wizard
  - `config/facility_config.json` — facility config template
  - `requirements-prod.txt` — production deps (no dev tools)
  - `tests/unit/test_check_env.py` — 15 tests PASS | Total: 287/287
- [x] **CONFIG-001** ✅ Facility config JSON (config/facility_config.json + setup_facility.py) (2026-06-08)
- [x] **VN-NER-003** ✅ Real-world NER bug fix A-01/A-02/A-03 — 11 bugs fixed (352 tests, 2026-06-08)
  - chan_doan boundary · temp decimal · self-med filter · ml→mg · ICD prefix strip
  - Iron context guard · BP intermediate text · BP "tri" alias · ly_do symptom filter · tai_kham admin strip
- [x] **CORPUS-001** ✅ CLINICAL_TEST_CORPUS_VN.md v2.0 — terminology fixes ("tình trạng", "đau khi nuốt") (2026-06-08)
- [x] **ADAPTIVE-001** ✅ `docs/records/ADAPTIVE_LEARNING_ARCHITECTURE.md` — 3-tier learning design (2026-06-08)
- [x] **FID-VN-006** ✅ Feature Intent Document L4 Correction Capture — Andy approved 2026-06-08
- [x] **L4-CORRECTION-001** ✅ [FID-VN-006] L4 Correction Capture — implicit supervision (2026-06-08)
  - `src/core/l4_correction_capture.py` — diff AI→BS, log to data/corrections/ JSONL
  - `scripts/analyze_corrections.py` — CLI alias suggestion tool (human review req)
  - `tests/unit/test_l4_correction_capture.py` — 14 tests PASS | Total: 366/366
  - Hook vào `src/api/main.py` approve_record() — best-effort, không block flow
  - `data/corrections/` vào .gitignore — không commit patient data
- [x] **CHATGPT-CORPUS-001** ✅ `docs/dev/CLINICAL_TEST_CORPUS_VN.md` v2.0 — 1210 dòng, by_disease + by_accent + by_drug_hard (2026-06-08)
- [x] **DRUG-ALIAS-001** ✅ Mở rộng alias map drug_db.json v0.3.0 — PhoWhisper phonetic variants cho 6 drugs: Glimepiride/Colchicine/Etoricoxib/VitaminB/Metformin/Omeprazole (2026-06-10)
- [ ] **DRUG-DB-002** 🟡 Mở rộng drug_db.json 118 → ~150 thuốc — bổ sung nhóm thiếu cho phòng mạch tư VN
  - Ưu tiên: Augmentin (Amox/Clav) · Bisoprolol · Tramadol · Empagliflozin · Sitagliptin · Folic acid · Vitamin D3 · Smecta · Phosphalugel · Celecoxib · Dapagliflozin · Indapamide
  - VietMed-NER drugs (313 entries) = OB/GYN context, overlap thấp → KHÔNG dùng
  - Source: TT07/2017 (243 OTC hoạt chất) + TT28/2024 + pilot prescription review
- [x] **CONS-002-IMPL** ✅ Sprint 1: `data/reference/drug_db_v200.json` v2.0.0 — 146 drugs + phonetic_variants (2026-06-10)
  - Basis: CONS-20260610-001 + CONS-20260610-002 CLOSED, Approach C APPROVED
  - Top 50 drugs: manual × 3 vùng = ~300-500 entries thủ công (high accuracy)
  - 150 drugs còn lại: 7 consensus phoneme rules (R1-R7) auto-generate
  - Fields mới: `phonetic_variants`, `valid_doses_mg[]`, `dose_range{min,max}`, `drug_class`, `compatible_diagnoses`
  - Depend: drug_db_v200 là prerequisite của CONS-002-SPRINT2, CONS-002-SPRINT6
- [x] **CONS-002-SPRINT2** ✅ DrugCorrectionEngine v2 — 4-layer fuzzy + Ambiguity Gate + Safety (2026-06-10)
  - `src/core/l1b_drug_correct.py` v2 · `fids/FID-VN-008.md` APPROVED
  - 35 new tests → 444/444 PASS
  - Layer 1: Exact alias match (current behavior)
  - Layer 2: Fuzzy match RapidFuzz fuzz.token_sort_ratio() cutoff ~85%
  - Layer 3: Phonetic prefix + context (session_context: diagnosis, drug_class)
  - Layer 4: Safety Rule Engine — hard dose validation per drug, ambiguity → flag không auto-commit
  - Depend: CONS-002-IMPL (phonetic_variants trong drug_db_v200)
- [ ] **VIETMED-FIX-001** 🟢 Fix `scripts/download_vietmed.py` — bỏ `trust_remote_code`, thêm HF_TOKEN auth
  - Lỗi hiện tại: `trust_remote_code is not supported anymore` + 401 Unauthorized
  - Dataset `doof-ferb/VietMed` cần HuggingFace login để download (~2.5GB, 16h audio MIT)
  - Dùng cho: TRAIN-001 PhoWhisper fine-tune (Phase 1 — không block Phase 0)
- [x] **BUG-K2** ✅ "một sáu lăm"=165 abbreviated SG tens fixed (2026-06-10) — `_WABR` pattern + `_WCOLLQ` extended. +1 test `test_sg_bp_colloquial_165_abbreviated` → 409/409 PASS
- [x] **BUG-N** ✅ chan_doan rỗng cho follow-up visits (2026-06-10) — BS nói "tái khám tăng huyết áp" mà không có "chẩn đoán:" keyword. Fix: `_RE_TAI_KHAM_DIAGNOSIS` checked trước `_RE_CHAN_DOAN_FALLBACK`. +4 tests → 408/408 PASS
- [~] **DATASET-001** 🔵 PARTIAL — Download P1 public datasets (VietMed family — MIT/Apache-2.0)
  - ✅ Downloaded: VietMed-NER (9K NER, ~30MB) · VietMed-Sum (106K, ~43MB) · VN Medical QA (9K, ~5MB) → `data/external/`
  - ✅ `scripts/download_vietmed.py` sẵn sàng — chạy overnight qua `scripts/overnight_run.bat`
  - ⏳ VietMed (~2.5GB ASR audio) → `data/vietmed/` | ViMedCSS (4GB) — để sau
  - Script: `python -X utf8 scripts/download_datasets.py` | Catalog: `docs/dev/DATA_CATALOG.md`
- [~] **DATASET-002** 🔵 PARTIAL — Phân tích VietMed-NER → map 18 entity types → MediVoice 5 types
  - ✅ `scripts/analyze_vietmed_ner.py` — entity mapping, vocab extracted, staging file
  - ✅ `data/reference/vietmed_drugs_raw.json` — 313 unique DRUGCHEMICAL entities
  - ✅ `data/reference/vietmed_ner_vocabulary.json` — top terms extracted
  - ⏳ `scripts/train_ner.py` — fine-tune training pipeline (gated FID-VN-007)
- [x] **SYNTHETIC-NER-001** ✅ Tạo 10,000 samples BIO-tagged VN outpatient NER (2026-06-07)
  - `scripts/generate_synthetic_ner.py` — 17 scenarios × 4 regions (expanded từ 7)
  - `data/synthetic_ner/` — train 7994 / val 1003 / test 1003 (JSONL, BIO format)
  - `tests/unit/test_synthetic_ner_pipeline.py` — 7 tests pipeline benchmark (395/395 PASS)
  - Hit rates: Drug 97-100% · Diagnosis 63-80% · Vital 63-77% · Tái khám 33-60%
  - 10 scenarios mới: viem_phe_quan · viem_xoang · di_ung_mui · viem_da_ruot · nhiem_trung_tiet_nieu
    thieu_mau · mat_ngu · tang_mo_mau · viem_ket_mac · viem_amidan
- [x] **NER-BUGFIX-004** ✅ chan_doan regex major fix (2026-06-09)
  - Fix: lookahead xử lý ". filler Kê" pattern, ICD codes, "bị/mắc" prefix, "gout" fallback
  - File: `src/core/l1c_ner.py` — _RE_CHAN_DOAN + _RE_CHAN_DOAN_FALLBACK
  - Verified: 10/10 test cases pass, 92/92 existing tests không bị break

---

## PHASE 1 — COMPLETE PRODUCT (3–6 tháng sau Phase 0)

### Modules
- [ ] **M1:** Patient management đầy đủ (hồ sơ, lịch sử, CCCD scan, QR thẻ BN)
- [ ] **M2:** Booking engine (7 states + buffer + waitlist + D-1/H-2/H-15p reminder)
- [ ] **M3:** Thu chi đầy đủ (voice log, báo cáo, xuất Excel)
- [ ] **M4:** Email auto-processor (3 điều kiện + quarantine) + kết quả XN
- [ ] **M5:** Referral 2 chiều + deal % + commission dashboard (Gói 3)
- [ ] **M6:** Zalo OA (text non-medical) + Email routing (file y tế) + Post-care CRM
- [ ] **M7:** VN Cloud sync (VNG/FPT/VNPT)

### Architecture
- [ ] **QUEUE-001:** Queue Management System + TTS loa đọc tên
- [ ] **SCREEN-001:** Staff Screen riêng (Mode B) — tiếp nhận + thu ngân gộp
- [ ] **DOCTOR-001:** Doctor Pre-visit Briefing (tóm tắt BN trước ca)
- [ ] **STAFF-GATE-001:** Staff Confirm Gate (checklist đóng ca BN)
- [ ] **PARTNER-001:** Partner comm channel (Email CHÍNH THỨC + Zalo optional)
- [ ] **WEBSITE-001:** Website widget embed + REST API booking (Gói 2+)
- [ ] **BOOKING-001:** Booking engine chuẩn (7 states + reminder flow)
- [ ] **AFTERCARE-001:** Post-care CRM D+2/D+4/D+5/D+7
- [ ] **STAFF-001:** Staff voice context (tiếp nhận BN — khác với doctor voice)

### Plugins
- [ ] **FID-VN-001:** Plugin CĐHA — báo cáo siêu âm (abdominal, thyroid, OB, vascular)
- [ ] **FID-VN-001b:** Plugin CĐHA — X-quang, CT, MRI
- [ ] **FID-VN-002:** Plugin Nha khoa — Mẫu 16/BV1 + sơ đồ răng
- [ ] **FID-VN-003:** Plugin Sản khoa — Mẫu 05/BV1

### Features
- [ ] **REPEAT-001:** Tái kê đơn cũ (copy đơn + điều chỉnh nhỏ)
- [ ] **DRUG-INTERACT-001:** Drug interaction check cơ bản
- [ ] **EMAIL-PROC-001:** Email auto-processor inbound (M4)
- [ ] **REFERRAL-RETEST-001:** Referral retest flow (kết quả lần 1 không đạt)
- [ ] **ACCOUNT-API-001:** Kế toán export API (MISA/Fast CSV + REST)

### Training
- [ ] **TRAIN-001:** Fine-tune PhoWhisper trên VietMed (16h labeled MIT) + pilot audio (50–100h)
  - Datasets: `data/external/VietMed` + `data/external/ViMedCSS` + pilot audio
  - Target: WER 35–40% → <20% | Drug CEER 0.90 → <0.10
  - Cần: GPU/cloud VM (VNG/FPT) | FID-VN-007 trước khi implement
- [x] **TRAIN-002** ✅ Fine-tune PhoBERT+CRF NER trên synthetic 10K — HOÀN TẤT (2026-06-10)
  - Epoch 1: F1=**98.95%** P=98.98% R=98.91% | Epoch 2: F1=**98.73%** | Epoch 3: F1=**99.44%** ← BEST
  - Best model: `models/ner_phobert/best/` (512.8MB, checkpoint-3000) ✅
  - Entities: MEDICATION · DOSE · FREQUENCY · SYMPTOM · VITAL · FOLLOWUP
  - Datasets: `data/synthetic_ner/` (7994 train / 1003 val / 1003 test)
  - **Note:** Trained trên synthetic data — cần validate trên pilot audio thực trước khi dùng production
- [x] **FID-VN-009-IMPL** ✅ Hybrid NER [FID-VN-009] — DONE 2026-06-10
  - `src/core/l1c_phobert.py` — lazy load, confidence thresholds, bio_to_updates(), has_coverage_gap()
  - `src/core/l1c_ner.py` — extract_entities_hybrid() + _get_filled_fields() + _has_coverage_gap
  - `tests/unit/test_l1c_phobert_hybrid.py` — 29 tests → 473/473 PASS
  - PARALLEL + optional early-exit: trieu_chung+tai_kham+ly_do filled → skip PhoBERT
  - VITAL → meta["phobert_vital_detected"] only; MEDICATION ≥0.85; SYMPTOM ≥0.75
  - Default OFF (MEDIVOICE_PHOBERT_NER=false) — bật sau BENCH-002b GO criteria
- [x] **CONS-002-EVAL** ✅ Sprint 4: Evaluation dataset + eval script DrugCorrectionEngine v2 (2026-06-10)
  - `scripts/generate_drug_eval_dataset.py` → `data/eval/drug_correction_eval.json` (204 cases)
  - `scripts/eval_drug_correction.py` — 4 metrics: Drug Recall / Silent FP / Safety Catch / Phonetic
  - Categories: clean=90 / noisy=76 / dangerous=38
  - Results: Drug Recall=**99.5%** ✅ | Silent FP=**0.0%** ✅ | Safety=**92.1%** ✅ | Phonetic=**98.7%** ✅
  - **→ ✅ GO — all criteria met** (thresholds: ≥88% / ≤10% / ≥80% / ≥85%)
  - Known issues: "a zi thro my xin" Azithromycin FN · "metro"/"me tro" AMBIGUOUS miss (3 cases)
  - Distinction: silent FP (unflagged, dangerous) vs warned FP (LOW_CONFIDENCE, BS reviews → rejects)
- [ ] **CONS-002-SPRINT6** 🟢 Sprint 6: TTS Pilot — XTTS-v2 / F5-TTS Vietnamese drug corpus (CONDITIONAL-GO)
  - Prerequisite: CONS-002-IMPL done (phonetic_variants) + reference voices thu được từ pilot BS
  - Step 1: Generate 20 clips (5 câu × 4 voices) → BS evaluate → quyết GO/NO-GO full
  - Step 2 (nếu GO): 5000 câu × 4 voices = 20K clips overnight + noise augment
  - Test cả XTTS-v2 (thivux/XTTS-v2-vietnamse) và F5-TTS (nguyenthienhy/F5-TTS-Vietnamese)
  - Bridge CONS-001→002: dùng phonetic_variants làm TTS input text (KHÔNG dùng INN gốc)

---

## PHASE 1B — PLUGINS CHUYÊN KHOA

- [ ] **FID-VN-001:** `plugin_cdha.py` — báo cáo siêu âm/X-quang
- [ ] **FID-VN-002:** `plugin_ngoai_tru_full.py` — Mẫu 15/BV1 đầy đủ (upgrade Phase 0 basic)
- [ ] **FID-VN-003:** `plugin_nha_khoa.py` — Mẫu 16/BV1

---

## PHASE 2 — KHI CÓ REVENUE (2027+)

- [ ] **TT13-001:** Chữ ký số bác sĩ (TT13/2025 deadline 31/12/2026)
- [ ] **HL7-001:** HL7 v2 export (ADT/ORU)
- [ ] **FHIR-001:** FHIR R4 export (khi TT13/2025 thực sự enforce)
- [ ] **M9:** HIS integration (BravoSoft, FPT.eHospital API)
- [ ] **AUDIT-EXPORT-001:** Audit log export chuẩn cho BYT thanh tra
- [ ] **CONFORM-001:** Conformity assessment (Luật AI 134/2025) — trước 01/09/2027
- [ ] **M5:** Referral partner management đầy đủ (Gói 3)
- [ ] **M8:** Plugin mở rộng (Tai mũi họng, Tim mạch, Sản khoa...)
- [ ] **VNEID-001:** VNeID API integration (khi BYT có API)
- [ ] **BHYT-001:** BHYT eligibility check
- [ ] **BYT-SYNC-001:** BYT Central Registry sync

---

## DESIGN DOCS (Phiên 2026-06-06)
- [x] **DESIGN-001** ✅ Master Design Report v1.1 (2026-06-06) — docs/records/DESIGN_REPORT_v1.1_20260606.md
  Bao gồm: Queue QMS, Mode A/B/C, 4 màn hình, Doctor Briefing, Staff Gate,
  Referral 2 chiều + Retest, M5 Commission, Post-care CRM, Booking Engine chuẩn,
  Email auto-processor, Data compliance 3 lớp, Integration Gateway, 17+ kết nối

---

## DONE

- [x] Research thị trường VN (~15h, 2026-06-02)
- [x] CLAUDE.md v0.2.0 — 2 layers, 3 gói, 9 modules, mobile-first
- [x] VISION.md v0.2.0, BRS.md v0.2.0
- [x] BACKLOG.md, DECISIONS.md v0.2.0 (32 decisions locked)
- [x] Third-party review: ChatGPT + Grok + Copilot (A+B+C+D) — 2026-06-03
- [x] Design finalization (2 layers + 3 gói + 9 modules + mobile-first)
- [x] Data reference: ICD-10-VN (15,026) + TT23 (9,124) + drug_db (110) + Mẫu 15/BV-01
- [x] Enforcement: 61 tests + pre-commit hooks + pipeline stubs L0–L10
- [x] ISO_VN framework: CONSTITUTION + governance code + risk engine
- [x] DRUG-DB-001: drug_db.json 110 thuốc (TT07/2017 + TT28/2024) ✅
- [x] ICD-001: icd10vn.json 15,026 mã (HL7 Vietnam) ✅
- [x] PROJECT_KICKOFF S1–S9 done (S10 Andy ký sau)
- [x] Git init + 6 commits + pushed to GitHub
- [x] **Phase 0 pipeline L0→L10** — toàn bộ implement (2026-06-04)
- [x] **Data models** — Patient, ClinicalRecord, Facility, AuditEntry (Pydantic v2) (2026-06-04)
- [x] **FastAPI PWA** — voice recording + draft review + approve/reject + PDF (2026-06-04)
- [x] **CHANGELOG v0.3.0** — 16 feat entries (2026-06-04)
- [x] **Canada pipeline port** — L0→L9, MarianMT, FAISS KB (2026-06-05)
- [x] **BENCH-001** — T-005 20/22 PASS, T-007 10/10 PASS (2026-06-05)
- [x] **DESIGN_REPORT v1.1** — Master design document 21 sections (2026-06-06)

---

## DEFERRED (Không làm cho đến khi có signal rõ ràng)

- [ ] Native mobile app (iOS/Android) — quá tốn, web responsive đủ
- [ ] Multi-tenant SaaS infrastructure — Phase 2+
- [ ] Luật AI 134 conformity assessment detail — sau khi có revenue
- [ ] FPT/Viettel partnership — sau khi có 100+ users
- [ ] VNeID health platform integration — chờ BYT API public
- [ ] IVR Phone booking — Phase 3
- [ ] WhatsApp/Facebook channel — Phase 3

---

*Updated: 2026-06-08 | v0.6.3*
