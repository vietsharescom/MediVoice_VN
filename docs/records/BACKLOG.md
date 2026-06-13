# BACKLOG.md — MediVoice VN
# v0.9.4 — Updated 2026-06-12
# Single source of truth cho tasks.

## CT-053 — Vietnamese Medical Phonetic Encoder (Phase 2, supersedes CT-052) [NEW 2026-06-12]
- [ ] Phát sinh từ FID-VN-019 v3 (CT-042 revision, CONS-20260612-001 ChatGPT+Grok
  review) — hướng kiến trúc dài hạn thay cho việc tiếp tục mở rộng
  `_phonological_variants()` (enumerate-based sẽ "nổ" theo cấp số nhân khi
  155→300→1000 thuốc)
- [ ] Đề xuất: Soundex/Metaphone/Double-Metaphone-style encoder cho tên thuốc
  tiếng Việt — encode alias → canonical code (vd "mét phọc min"/"mét phô min"/
  "mét pho min" đều → `MTFRMN`), match qua code thay vì enumerate biến thể
- [ ] Phạm vi gộp 3 nhóm hiện tượng (KHÔNG implement trong FID-VN-019):
  1. **Consonant cluster reduction/epenthesis** (cũ CT-052) — tiếng Việt không có
     cluster phụ âm → English cluster ("-stat-in", "pred-ni-sone") bị rụng 1 phụ
     âm hoặc chèn nguyên âm đệm (vd "statin"→"sờ ta tin", "steroid"→"xì tê rôi")
  2. **Vowel normalization** — biến đổi o/ô/ơ, i/inh, en/eng, an/ang (vd
     "metformin"→"mét pho min"/"mét phọc min"/"mét phô min")
  3. **Syllable insertion / stress relocation** — BS Việt thêm âm tiết đệm khi
     gặp cluster tiếng Anh (vd "clopidogrel"→"cờ lô pi đô gờ ren")
- [ ] KHÔNG implement cùng FID-VN-019 — cần audio thật (BENCH-002b hoặc pilot) để
  xác định pattern cụ thể trước khi thiết kế encoder
- [ ] Kết hợp tốt với Drug Pronunciation Wizard (FID-VN-013/014, Grok round 3
  CONS-20260612-001): BS đọc tên thuốc → ASR + rule-based variant → confirm alias
  → enrich `phonetic_variants` tự động (hybrid curation)
- [ ] Nguồn: [The Adaptation of French Consonant Clusters in Vietnamese Phonology:
  An OT Account](https://www.sejongjul.org/archive/view_article?pid=jul-18-1-69),
  [CTU Journal — Common mistakes in pronouncing English consonant
  clusters](https://ctujs.ctu.edu.vn/index.php/ctujs/article/view/448)
- Priority: 🟡 MEDIUM — chờ thêm pilot audio trước khi viết FID riêng

## CT-011 / FID-VN-020 — Orchestrator v1.0 Automation [DONE 2026-06-12]
- [x] `fids/FID-VN-020.md` — Status: APPROVED by Andy ("APPROVE FID 20 TIẾP TỤC", 2026-06-12)
  → implemented + acceptance criteria checked off với kết quả thật
- [x] 3 hàm mới trong `scripts/orchestrator.py`:
  1. `detect_confusion(note) -> dict` — heuristic match trigger T1-T5
     (`docs/dev/CONSULTATION_TEMPLATE.md`) qua `_CONFUSION_TRIGGERS`, chỉ gợi ý
     KHÔNG block workflow
  2. `create_consultation_request(topic, question, options, hard_constraints,
     analysis) -> Path` — sinh `docs/records/consultations/CONS-YYYYMMDD-NNN.md`
     đúng format `CONSULTATION_TEMPLATE.md`, NNN tự tăng theo ngày
     (`_next_consultation_number` quét file thực tế, tránh trùng đa máy — R-ORCH-03)
  3. `close_session(updates, push=False) -> dict` — 4 hàm `_patch_backlog`/
     `_patch_project_progress`/`_patch_changelog`/`_patch_claude_md` patch 5 file
     session-end tại marker xác định + `_write_last_session` + chạy
     `iso_audit.py --increment-session` (subprocess) + `git add -A && git commit`
     (push CHỈ khi `push=True`, default False — R-ORCH-02)
  - Hàm `close_session()` cũ (checklist printer) đổi tên → `print_close_checklist()`,
    CLI `close` subcommand cập nhật theo
- [x] Tests: `tests/unit/test_orchestrator.py` (mới, 11 tests) — detect_confusion
  trigger keywords T1/T5/no-trigger, consultation numbering+format,
  `_patch_*` helpers (tmp_path), close_session push=False/True default
- [x] KHÔNG đổi `start_session()`/`consult()`/`consistency_check()` hiện có
- [x] 973/973 existing PASS + 11 mới = 984/984 PASS, bandit 0 HIGH (9 MEDIUM
  pre-existing không đổi, LOW 2→13 — subprocess B404/B603/B607 mới từ
  `close_session()`, không phải HIGH/MEDIUM), CHANGELOG entry v0.11.20
- Priority: 🟡 MEDIUM — Risk LOW (dev-tooling only) — DONE

## CT-051 — L1b drug match window 1-4 → 1-6 words [DONE 2026-06-12]
- [x] `src/core/l1b_drug_correct.py::_match_window()` window (4,3,2,1) → (6,5,4,3,2,1)
- [x] Unlock 187 phonetic_variants 5-6 từ trong `drug_db_v200.json` (Azithromycin,
  Ciprofloxacin "xi pro phlo xa xin", Atorvastatin, Rosuvastatin, Clarithromycin...)
  trước đây KHÔNG THỂ MATCH (window cũ tối đa 4 từ)
- [x] Exact-match only → không tăng false-positive risk
- [x] 2 tests mới (`test_phonetic_5word_azithromycin`, `test_phonetic_5word_ciprofloxacin`)
  — 958/958 PASS
- Phần CT-027(5). Chưa fix riêng Ciprofloxacin "si pô lo siêu âm si" (CT-016, spelling khác,
  cần thêm data trước khi thêm alias)

## CT-050 — Dev-machine bootstrap + test infra hardening [DONE 2026-06-12]
- [x] `tests/conftest.py` gọi `init_db()` trực tiếp (FastAPI `startup` event không chạy
  khi `TestClient(app)` không dùng `with` → DB schema thiếu trên máy mới)
- [x] Tạo lại fixture local `data/audio/ground_truth_lam_sang_template.json` (gitignored)
- [x] `tests/unit/test_build_asr_manifest.py` — `@pytest.mark.skipif` khi
  `data/audio/reference_voices/` (pilot audio gitignored) không có local — tránh false 🔴
- 954/956 PASS + 2 skipped (skip = pilot-audio-absent, không phải lỗi code), bandit 0 HIGH
- Không thay đổi pipeline/feature — env-only, máy dev mới

## CT-049 — Pilot test fix round 3 [DONE 2026-06-11]
- [x] Chẩn đoán nuốt đơn thuốc ("thuốc uống là <thuốc>") → `_PRESCRIPTION_KW` (`src/core/l1c_ner.py`) thêm `thuốc\s+(?:uống|tiêm|bôi|nhỏ|dán|xịt|là)\b`
- [x] Thiếu Paracetamol (ASR "parasyte mode") → `phonetic_variants` + nới filter 2-từ ≥9 ký tự (`src/core/l1b_drug_correct.py::_build_alias_map()`)
- [x] Tuổi/giới tính/tên BN chưa trích xuất từ "<nam/nữ> <N> tuổi, <Tên>..." → `MedicalEntities.tuoi`/`gioi_tinh` + `_RE_GIOI_TINH_TUOI`/`_RE_TUOI`/`_RE_PATIENT_NAME_AGE` (`src/core/l1c_ner.py`) → `form_data` → `HanhChinh.tuoi`/`gioi_tinh` (PDF) + UI input Tuổi/Giới tính
- 948/948 PASS, bandit 0 HIGH/9 MEDIUM (pre-existing) — chi tiết `docs/records/PENDING_REQUESTS.md` CT-049

## CT-048 — Pilot test fix round 2 (PA-023 items #1-3) [DONE 2026-06-11]
- [x] Lý do khám trống → `_RE_LY_DO_FALLBACK2` + `_RE_SYMPTOM_KW` (`src/core/l1c_ner.py`)
- [x] Tên BN không tự điền → `MedicalEntities.ho_ten` + `_RE_PATIENT_NAME` (cue rõ ràng) → `form_data.ho_va_ten` → autofill `#patient-name`
- [x] Gợi ý thuốc RAG sai (Salbutamol/Amlodipine) → chỉ gọi `/api/drug-candidates` khi `don_thuoc` rỗng (`src/api/static/index.html` + `js/suggestions.js::dismissDrugChips()`)
- 939/939 PASS, bandit 0 HIGH/9 MEDIUM (pre-existing) — chi tiết `docs/records/PENDING_REQUESTS.md` PA-023

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

### FID-VN-013 v2 — Voice Calibration UX + Drug Pronunciation Wizard + VTLN [DONE, chờ Andy review]
> FID: `fids/FID-VN-013.md` | Consensus: `docs/records/consultations/CONS-20260610-005.md` (8-AI, 85%)

- [x] **2.1-2.3 Visualization** ✅ Waveform/mic-level/pause-detection/quality-score/behavioral-hint/dialect-badge/calib-tooltip — client-side only, AC-008 (no audio stored/sent)
  - `src/api/static/js/audio_quality.js` — `computeRMS`, `qualityFromStats`, `computeQualityScore`, `getBehavioralHint`, `detectPauses` (UMD, Node-tested)
  - `src/api/static/index.html` — `#audio-viz` waveform canvas + mic-level bar trong card "Ghi âm", `#region-badge` (AC-006), `#calib-tooltip` (AC-007, dismiss → localStorage)
  - `tests/unit/test_audio_quality.py` — 11 tests PASS
- [x] **2.4 Drug Pronunciation Enrollment Wizard** ✅ Active enrollment (bypass passive ≥3×≥2 promote rule)
  - `src/core/l7_storage.py` — `add_confirmed_alias()` insert trực tiếp confirmed_by_bs=1
  - `src/api/main.py` — 3 endpoints: `GET /api/doctors/{cchn}/pronunciation-wordlist`, `POST .../pronunciation-enroll`, `POST .../pronunciation-confirm`
  - `src/api/static/index.html` — nút "🎓 Luyện đọc thuốc" trong DVP greeting card + `Wizard` modal
  - `tests/unit/test_dvp_wizard.py` — 9 tests PASS (AC-010/011/012, purge_audio verified)
  - 2.4.1 `global_aliases`/`doctor_overrides` — KHÔNG implement (Phase 1.5 per ChatGPT proposal)
- [x] **2.5 VTLN research module** ✅ AC-013 gate research (chưa wire vào L0)
  - `src/core/vtln.py` — `estimate_warp_factor()` (librosa.pyin) + `apply_vtln_warp()` (resample-based, no-op tại warp=1.0, AC-014)
  - `scripts/vtln_poc.py` — CLI POC, đo WER trước/sau VTLN, gate ≥3% relative reduction
  - `tests/unit/test_vtln.py` — 6 tests PASS
  - **CT-037** ⏳ POC chưa chạy — cần audio pilot + ground-truth transcript text đầy đủ (xem PENDING_REQUESTS.md)
- 852/852 tests PASS, bandit 0 HIGH/0 MEDIUM
- **PA-015** ⏳ Andy test UI (ghi âm + wizard) trên trình duyệt thật, confirm OK

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
  - `_vad_model` cached module-level (tránh reload silero-vad mỗi request)
  - 🔴 ĐÃ THỬ wire vào `/transcribe` (2026-06-09 đêm) → REVERTED ngay — Andy test thực tế: transcript "KHÔNG NHẬN DẠNG ĐƯỢC GÌ LUÔN" (regression nặng, per-chunk PhoWhisper hallucination). Cần debug riêng (CT-019) trước khi wire lại — KHÔNG tự ý wire lại nếu chưa có A/B test.
  - **CT-019 offline A/B (2026-06-10)**: `scripts/debug_a2_vad_chunk.py` chạy trên 3 file pilot thật (12.2s/28.5s/92.6s) — per-chunk transcript = whole-file hoặc TỐT HƠN, KHÔNG hallucination, `initial_prompt` (drug_db) KHÔNG ảnh hưởng (output giống hệt có/không). KHÔNG reproduce được lỗi của Andy → cần audio thật bị lỗi (CT-016) để test trực tiếp trước khi wire lại.
  - **CT-016 ground truth nhận được (2026-06-10)**: Andy gửi script gốc 3 clip (BS Phan Đình Hiệp/Hà Nội, ca Ngô Thị Liên đau bụng/sốt/tiêu hoá) + transcript thực tế từ live test → phát sinh 3 task mới:
    - `CT-020` 🟡 NER miss Mạch (pulse) khi ASR "Mạch"→"mật" + mất "lần"
    - `CT-021` 🟡 NER miss Chẩn đoán + ICD-10 khi ASR "theo dõi"→"theo thì"
    - `CT-022` 🔴 SAFETY: L1b fuzzy match nhầm "Oresol" (bù nước, KHÔNG có trong drug_db) → "Xylometazoline" (thuốc nhỏ mũi) trong đơn thuốc draft
    - Cả 3 cần raw transcript (trước L1b) hoặc audio 3 clip từ Andy để xác nhận root cause trước khi fix.
  - **CT-025 🔴 CRITICAL (2026-06-10)**: Test demo Groq cloud (`medivoice-vn-demo.streamlit.app`, `demo/app.py` — whisper-large-v3 + llama-3.3-70b) với script W1-001 (3 thuốc) → LLM tự BỊA THÊM 9 thuốc không có trong audio (Clopidogrel, Valsartan, Vitamin D3, Meloxicam, Sertraline, Enalapril, Paracetamol...), hiện "12/12 thuốc đã xác nhận". Vi phạm Absolute Rule #7. Kết luận: KHÔNG dùng kiến trúc Groq LLM-extraction cho production — giữ TECH DECISIONS LOCKED (PhoWhisper + PhoBERT/CRF deterministic NER, không hallucinate thuốc mới).
  - **CT-022 ✅ DONE (2026-06-10)**: thêm "Oresol" vào `data/reference/drug_db_v200.json` (155 drugs) — Layer 1 exact match thắng trước fuzzy → hết nhầm Xylometazoline. Branch `experiment/local-accuracy`.
  - **Test thật Clip 1/2/3 (2026-06-10, BS Phan Đình/Q.Tân Phú HCM, BN Nguyễn Văn An, viêm họng cấp)** → phát sinh 5 task mới, branch `experiment/local-accuracy`:
    - `CT-030` ✅ DONE — Nhiệt độ decimal mất khi ASR "phẩy"→"chấm" (37.9°C → đọc thành 37.0). Fix `_RE_DEC_WORDS`.
    - `CT-031` ✅ DONE — Chẩn đoán/ICD-10/Tái khám trống khi ASR "Kê"→"che" (không dấu). Fix `_PRESCRIPTION_KW`.
    - `CT-032` ✅ DONE — Tái khám trống khi ASR "tái khám"→"tái kháng". Fix `_RE_TAI_KHAM`/`_RE_TAI_KHAM_DIAGNOSIS`/`_PRESCRIPTION_KW` (`kh[aá]m`→`kh[aá](?:m|ng)`).
    - `CT-033` ✅ Mitigated — SAFETY: "Vitamin D3" hallucinated vào đơn thuốc từ ASR garble câu khám "amidan sưng nhẹ" → literal "Vitamin D3 xương nhẹ" → L1b match đúng kỹ thuật nhưng sai ngữ nghĩa. Không sửa được bằng regex — mitigation = CT-023 (nút Xóa).
    - `CT-034` ✅ DONE — Drug recall miss "Paracetamol"→"pha ra citamon" — thêm phonetic_variants 3-từ vào drug_db_v200.json.
    - 826/826 tests PASS. RAG vectorstore (`data/drug_vectorstore/`) rebuilt với 155 thuốc (Oresol + Paracetamol alias mới).
  - **CT-023 ✅ DONE (2026-06-10)**: `src/api/static/index.html` `renderDrugConfirmList()` — thêm nút "🗑️ Xóa" mỗi dòng thuốc (`removeDrug(idx)`), state `_currentDrugs`/`_drugConfirmed`. Xóa thuốc → `_drugTotal` giảm, không tính vào yêu cầu xác nhận; xóa hết (`_drugTotal===0`) → nút Lưu tự mở khóa. `buildEditedFormData()` dùng `_currentDrugs` làm `don_thuoc` cuối — thuốc bị xóa KHÔNG vào hồ sơ/PDF. 826/826 PASS.
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
  - **Done**: `multi_ai_consult()` + `_PROVIDERS` registry — Groq/OpenAI/xAI/OpenRouter qua `_openai_compatible_call()` chung ✅
  - **Done**: `consult(topic, question)` — gọi tất cả providers, lưu JSON evidence vào `docs/records/consultations/` ✅
  - **Done**: `consistency_check(topic, question)` — query tất cả providers + Groq phân tích AGREEMENTS/CONFLICTS/RECOMMENDATION ✅
  - **Done**: `close_session()` — in checklist 6 bước (chưa tự động hóa, chỉ reminder)
  - **Provider status (2026-06-09)**:
    - Groq/LLaMA-3.3-70B ✅ hoạt động (free tier) — model thật trả lời bằng tiếng Việt
    - OpenAI/GPT-4o-mini ⚠️ key hợp lệ nhưng HTTP 429 — hết quota/chưa add billing (`platform.openai.com`)
    - xAI/Grok-3 ⚠️ key hợp lệ, model name đúng (grok-3) nhưng HTTP 403 — team chưa có credits (`console.x.ai`)
    - OpenRouter/LLaMA-3.3-70B-free ⚠️ key hợp lệ nhưng HTTP 429 — model `:free` đang bị rate-limit upstream (thử lại sau hoặc thêm key riêng)
  - **Demo evidence**: `docs/records/consultations/ORCH-CONSULT-20260609-184913.json`, `*-184931.json`, `*-195003.json`, `*-195413.json`, `*-200335.json` (multi-provider, Groq output thật + OpenAI/xAI/OpenRouter skip reasons)
  - **Chưa làm**: `detect_confusion()`, `create_consultation_request()` (CONSULTATION_TEMPLATE format), tự động hóa `close_session()` (chưa tự update docs)
  - Prerequisite for full v1.0: FID cần Andy approve (> 100 LOC tổng + new module + ghi đè LAST_SESSION tự động)
  - Priority: Phase 1 (sau pilot Đà Nẵng — khi cần scale multi-AI consultation)
- [ ] **TRAIN-001** ⏳ Fine-tune PhoWhisper trên 50-100h real clinical audio — cần audio thật từ pilot
  - [x] **FID-VN-007** ✅ Prep pipeline (2026-06-11): `scripts/build_asr_manifest.py` +
    `scripts/train_asr_phowhisper.py --smoke-test` (verified OK trên CPU, 57-clip/17min manifest).
    952/952 PASS. Full run BLOCKED: HF_TOKEN (VietMed gated) + 50-100h pilot audio + GPU/cloud VM.
  - [x] **FID-VN-007 v2** ✅ Colab/Kaggle GPU direction (2026-06-11, Andy: "đã có consent, làm đi"):
    `build_vietmed_manifest()` + `build_pilot_manifest()` (`scripts/build_asr_manifest.py`),
    `--fp16` flag (`scripts/train_asr_phowhisper.py`), setup guide
    `docs/dev/COLAB_KAGGLE_TRAINING.md`. ADR `docs/records/DECISIONS.md` 2026-06-11
    (Pilot Phase Exception #2 — audio PII tạm upload Colab/Kaggle, xóa ngay sau run).
    956/956 PASS, bandit unchanged. Full run vẫn chờ PA-024 (HF_TOKEN) + pilot audio recording.
  - [x] **FID-VN-007 v3** ✅ VIETMED-FIX-001 v2 (2026-06-12): dataset ID đúng `leduckhai/VietMed`
    (không gated, PA-024 đóng) + audio decode fix. VietMed 16h sẵn sàng train ngay (local hoặc
    Colab/Kaggle). TRAIN-001 full run chỉ còn chặn bởi 50-100h pilot audio.

### FID-VN-017/018 IMPLEMENTED — Phonetic guidance + DVP flow reorder [2026-06-11]
> Andy feedback session 2026-06-11 (sau FID-VN-016 test) — 4 ý lớn. CT-040/041 →
> FID-VN-017 (v0.11.8), CT-043 → FID-VN-018 (v0.11.9), cả 2 IMPLEMENTED. CT-042
> (L1b phonological correction, CHẠM FROZEN) tách riêng FID-VN-019 sau (cần
> audio pilot A/B test). CT-044 (verify MW) còn lại, không block.

- [x] **CT-040** ✅ Mở rộng `pronunciation_en` (Merriam-Webster-style, xem CONS-20260611-001) ra 9 thuốc tim_mach còn thiếu — top-20 wordlist `noi_khoa`+`tim_mach` đều có `pronunciation_en`. (Phase 2 của CT-039) → `fids/FID-VN-017.md` IMPLEMENTED v0.11.8 (2026-06-11)
- [x] **CT-041** ✅ "stress hint" (viết hoa âm tiết trọng âm trong `vn_phonetic_default` qua `apply_stress_hint()`) + tip ngắn về phụ âm bật hơi p/t/k trong Wizard Part 3. User vẫn tự đọc theo cách của mình (confirm cá nhân hoá FID-VN-016), default chỉ là gợi ý. → `fids/FID-VN-017.md` IMPLEMENTED v0.11.8 (2026-06-11)
- [ ] **CT-044** 🟢 LOW — **Verify `pronunciation_en` với Merriam-Webster thật** (`docs/records/consultations/CONS-20260611-001.md`): WebFetch `merriam-webster.com` bị chặn (403) trong môi trường Claude Code, nên 25 entries (FID-VN-016) + 9 entries (FID-VN-017) hiện ghi theo kiến thức chung của Claude (format khớp MW ở 2 ví dụ Andy kiểm tra: paracetamol, cetirizine), CHƯA verify từng entry. Khi Andy rảnh: paste respelling MW (`merriam-webster.com/dictionary/{ten-thuoc}#medicalDictionary`) cho từng thuốc → Claude đối chiếu/sửa `pronunciation_en` + cập nhật `pronunciation_en_source` thành "verified vs MW YYYY-MM-DD". Không block FID-VN-017.
- [x] **CT-042** ✅ DONE — `fids/FID-VN-019.md` v3 APPROVED by Andy (2026-06-12) +
  IMPLEMENTED: `_phonological_variants()` + `_add_phon_alias()` trong
  `src/core/l1b_drug_correct.py`, wired vào `_build_alias_map()` cho
  brands/name_variants/phonetic_variants (4 rule groups: aspiration b/p-d/t-g/k/c,
  coda drop {l,z,v,d,đ} multi-syllable only, th→t/d, r/l/n split-by-region +
  blacklist 43 từ). alias_map 1028→1913 keys (+885), 21 phonological collisions
  skipped (ambiguity guard). +15 tests (973/973 PASS), bandit 0 HIGH.
  **A/B benchmark** (branch `experiment/fid-vn-019-phonological`,
  `tools/bench_002b.py --save-json` → `data/eval/bench_002b_phon_results.json`):
  Drug Recall 0.556 (KHÔNG ĐỔI so với baseline 55.6% — PASS); Drug Precision 0.714
  — **KHÔNG ĐỔI so với master HIỆN TẠI** (verified: chạy lại bench trên master HEAD
  l1b_drug_correct.py + cùng eval data → cũng ra 0.714, FP=2) → FID này KHÔNG thêm
  FP mới (PASS). LƯU Ý: `data/eval/bench_002b_results.json` (committed baseline,
  precision 0.833/FP=1) ĐÃ STALE — master hiện tại đã là 0.714/FP=2 (Oresol FP trên
  REF_HN_P1_Clip3, không liên quan FID-VN-019, có sẵn trước session này) → xem
  **CT-054** (mới, regenerate baseline + investigate Oresol FP).
- [x] **CT-054** ✅ DONE 2026-06-12 — `data/eval/bench_002b_results.json` regenerated.
  Root cause của Oresol FP trên `REF_HN_P1_Clip3.wav`: **KHÔNG phải bug L1b/L1c** —
  `data/eval/ref_voice_transcripts_review.txt` dòng NOTE thiếu space sau dấu `.`
  (`"...năm ngày.Paracetamol năm trăm..."`, `"...ba mươi tám độ.Oresol pha..."`)
  → `extract_drug_candidates()` (L1b) không match được "Paracetamol"/"Oresol" vì
  bị dính liền với từ trước → GT NER undercount → "Oresol" do pred pipeline trích
  đúng (NOTE thật có Oresol) bị tính sai thành FP. Fix: thêm space sau `.` trong
  NOTE của `REF_HN_P1_Clip3.wav` (3 dấu câu) + `REF_HN_P1_Clip2.wav` (4 dấu câu,
  cùng lỗi, ảnh hưởng vitals CEER) + GT của `REF_DN_P4_Clip2.wav` (Vitamin C FP
  tương tự). Regenerate: TP=5→6, FN=4→5, FP=2→1, **Drug Recall 0.556→0.545, Drug
  Precision 0.714→0.857**. HN drug CEER 1.000→0.334. 984/984 tests PASS (không
  liên quan src/, chỉ data/eval). KHÔNG đổi pipeline L0-L10.
- [x] **CT-055** ✅ DONE 2026-06-12 — Fix toàn bộ lỗi **thiếu space sau dấu `.`**
  trong GT/NOTE của `data/eval/ref_voice_transcripts_review.txt` (52 dòng, pattern
  `[a-zà-ỹ0-9]\.[A-ZÀ-Ỹ]` tự động + 6 case đặc biệt sửa tay: "độ C.Khám"/"độ
  C.Mạch"/"P S A.Nếu"/"TÁM.Bệnh"/"nói.tôi"/"độ.nhớ" — không đụng số thập phân
  vì file không có số thập phân thật trong GT/NOTE, chỉ duration "(15.3s)" ở dòng
  FILE). Regenerate `bench_002b_results.json`:
  - Drug: TP 6→8, FN 5→5, **FP 1→0**, Recall 0.545→**0.615**, Precision
    0.857→**1.0**
  - Drug CEER ALL 0.519→**0.367**, DN drug CEER 0.500→0.200 (✅)
  - WER ALL 0.184→0.183 (không đổi đáng kể — chỉ ảnh hưởng entity extraction,
    không ảnh hưởng ASR text)
  - 984/984 tests PASS (data/eval only, không đụng src/ — pipeline L0-L10 KHÔNG đổi)
  - Còn lại: HN drug CEER 0.334 (Paracetamol/Ciprofloxacin GT NER vẫn miss do BS
    đánh vần phonetic "Pa ra ce ta mol"/"Ci pro flo vac cin" — known issue, xem
    CT-053 Phonetic Encoder Phase 2)
- [x] **CT-056** ✅ DONE 2026-06-12 — Fix 2 lỗi UI phát hiện qua test thực tế
  (Andy, case "Phạm Minh Tuấn"):
  1. **Tên BN dính chữ "Là"**: `_RE_PATIENT_NAME_AGE` (`src/core/l1c_ner.py`)
     bắt cả filler "là" giữa "...tuổi" và tên ("18 tuổi **là** Phạm Minh Tuấn"
     → `ho_ten="Là Phạm Minh Tuấn"`). Fix: thêm `(?:là\s+)?` optional sau
     `\d{1,3}\s*tuổi[,\s]+`.
  2. **Giới tính không tự chọn**: `fd.gioi_tinh` ("nam"/"Nam") không khớp
     `<option value="Nam">` (case-sensitive) → dropdown trống. Fix: JS
     (`src/api/static/index.html`) chuẩn hoá lowercase trước khi map
     `'nam'→'Nam'`/`'nữ'→'Nữ'`.
  3. **Temp audio path**: chuyển từ `%TEMP%` (ổ C) → `data/tmp/` (ổ D) —
     thêm `_TMP_DIR` trong `src/core/l0_normalize.py` + `src/api/main.py`
     (4 chỗ `NamedTemporaryFile`), `mkdir(parents=True, exist_ok=True)`.
  984/984 tests PASS. KHÔNG đụng pipeline L0-L10 logic (chỉ regex NER +
  JS mapping + path storage).
- [ ] **CT-057** 🟡 — **Lưu audio + transcript mỗi lần test qua UI vào
  `data/recordings/` (ổ D)** để Andy đánh giá lại sau (quyết định
  2026-06-12: áp dụng cho MỌI lần gọi `/api/transcribe`, không cần flag
  riêng). Implement: trước `purge_audio()` trong `src/api/main.py`
  (`transcribe_audio`), copy `wav_path` → `data/recordings/{ts}_{record_id}.wav`
  + ghi `data/recordings/{ts}_{record_id}.json` (transcript_raw/corrected,
  form_data, confidence, route, dvp_specialty/region, dialect_subs).
  ⚠️ Cân nhắc: vẫn giữ `purge_audio()` cho file tạm gốc (Privacy by Design
  L0 KHÔNG đổi) — chỉ lưu THÊM 1 bản copy có chủ đích vào `data/recordings/`
  cho mục đích đánh giá nội bộ (Andy, không phải lưu trữ BN production).
- [ ] **CT-058** 🟢 — **Dev tool `scripts/gdrive_fetch.py`**: Andy làm việc
  từ xa (nước ngoài), audio test để trên Google Drive (cá nhân, không phải
  dữ liệu BN) → script tải file từ link GG Drive về `data/recordings/`
  (hoặc `data/eval/`) trên ổ D để test pipeline. KHÔNG liên quan production/
  patient data, KHÔNG vi phạm ABSOLUTE RULE #4 (NĐ13/2023) — chỉ là tool dev
  cá nhân.
- [ ] **CT-059** 🟡 — **NER schema gap: "chỉ dẫn điều trị tại chỗ"** (nhỏ
  tai/nhỏ mắt/bôi/súc miệng...) phát hiện qua test "Nhỏ tai dung dịch sát
  khuẩn hai lần mỗi ngày" — câu này KHÔNG match `_RE_CHI_DINH` (chỉ bắt
  CĐHA/xét nghiệm: siêu âm/x-quang/CT/MRI/ECG) và KHÔNG phải tên thuốc
  trong `drug_db` → rơi ra ngoài hoàn toàn (không vào đơn thuốc, không vào
  chỉ định), KỂ CẢ KHI ASR đúng 100%. Cần FID (Tầng 1 — entity mới ảnh hưởng
  schema NER + mapping Mẫu 15/BV1).
- [ ] **NOTE 2026-06-12** — Test case "Phạm Minh Tuấn" (TMH, 18 tuổi) cũng
  phát hiện 2 case ASR hallucination MỚI (không sửa bằng regex, cần
  audio/model tuning — TRAIN-001):
  1. "Paracetamol năm trăm miligam khi đau tai hoặc sốt" → ASR ra
     "Paracetamol **and Tramadol** khi đau hoặc sốt" (chèn tên thuốc tiếng
     Anh không có trong audio). Safety net CT-023/CT-033 (xác nhận từng
     thuốc + nút xóa) đã hoạt động đúng — Tramadol hiện "chưa xác nhận".
  2. "Nhỏ tai dung dịch sát khuẩn hai lần mỗi ngày" → ASR ra "nhỏ tay và
     chiêm ngưỡng nước khác **Iron (Ferrous)** khuẩn hai lần mỗi ngày"
     (garble + hallucination tiếng Anh). → liên quan CT-059 + CT-053 +
     TRAIN-001.
- [x] **CT-043** ✅ **DVP setup flow reorder**: `dvp-form` reorder (Chuyên khoa chính/phụ TRƯỚC Vùng miền + hint), `READING_PASSAGES_BY_REGION`/`REGION_TEST_SENTENCES` (3 biến thể Bắc/Trung/Nam), `GET /api/calibration/passage-text?cchn=`/`region-sentence?cchn=` region-aware, `calibration_region()` trả `region_match: bool` (double-check `profile.region` declared vs `detect_region(transcript)`) + cảnh báo UI khi mismatch. → `fids/FID-VN-018.md` IMPLEMENTED v0.11.9 (2026-06-11)
- [x] **CT-045** ✅ **Lab Hiệu chỉnh Giọng nói — hiển thị thông tin BS (personality) trước test** (Andy feedback PA-021, follow-up FID-VN-018): `calib-lab-modal` thêm khối `#lab-doctor-info` (tên/chuyên khoa/vùng miền + nút "Sửa thông tin") NGAY ĐẦU modal, TRƯỚC `lab-grid`; `CalibLab.open()` gọi `_loadDoctorInfo()` trước `goStep(1)`; `CalibLab.editProfile()` đóng Lab → mở `DVP.edit()`. → v0.11.10 (2026-06-11), 4 tests mới `tests/unit/test_dvp_wizard.py`
- [x] **CT-046** ✅ **Pre-gen audio mẫu phát âm (gTTS) + ưu tiên `phonetic_variants.north`** (Andy yêu cầu "tải audio thuốc cho vào thư viện" + feedback Azithromycin "a dith rô my xin" không đọc được): chạy `scripts/gen_pronunciation_audio.py` sinh 149 mp3 + `_cache.json` (155 INN) tại `src/api/static/audio/pronunciation/`; fix `UnicodeEncodeError` (stdout utf-8 trên Windows); `get_reference_phonetic()` ưu tiên `phonetic_variants.north[0]` trước heuristic transliteration (tránh cụm phụ âm Anh không tồn tại trong tiếng Việt, vd "dith"). → v0.11.11 (2026-06-11), 3 tests mới
  - LƯU Ý: KHÔNG dùng audio Merriam-Webster (bản quyền + WebFetch 403, xem `docs/records/consultations/CONS-20260611-001.md`) — gTTS là nguồn hợp pháp duy nhất hiện tại
- [x] **CT-047** ✅ **Fix nhanh từ pilot test thật (TMH clip Andy 2026-06-11)**: (1) "Chẩn đoán: thì viêm tai giữa cấp" — `_RE_CHAN_DOAN` (`src/core/l1c_ner.py`) chỉ skip filler "theo dõi"/"theo thì", KHÔNG skip "thì" đứng một mình → thêm alternative `(?:(?:theo\s*(?:dõi|thì)|thì)\s+)?`. (2) "Thiếu Amoxicillin trong đơn thuốc" — transcript ASR ra "a mốt xi lin" (biến thể "mốt" chưa có trong `phonetic_variants`/`brands` của Amoxicillin) → thêm brand variant "a mốt xi lin" vào `data/reference/drug_db_v200.json`. → 935/935 tests PASS (+2 mới: `test_chan_doan_bare_thi_filler`, `test_phonetic_amot_xi_lin_variant`)
  - **CHƯA FIX (cần thêm việc, không phải 1-line)**:
    - **"Lý do khám" trống** — script gốc Andy đọc "Bệnh nhân nam **mười tám tuổi**, Phạm Minh Tuấn, vào khám vì..." nhưng ASR transcript KHÔNG có "tuổi" ở đâu cả (PhoWhisper bỏ sót cụm tuổi hoàn toàn, ghép lẫn vào "...nếu mà nặng quáạm minh tuấn vào khám..."). `_RE_LY_DO_FALLBACK` (`src/core/l1c_ner.py:121`) bắt buộc pattern `\d+\s*tuổi` làm anchor → không match khi ASR không transcribe được tuổi. Đây là vấn đề ASR (TRAIN-001), không phải regex; cần thêm 1 fallback pattern KHÔNG phụ thuộc "tuổi" (vd anchor trên tên riêng + "vào khám (vì\|bị)") nhưng rủi ro false-positive cao hơn — cần FID nhỏ hoặc Andy review trước khi thêm.
    - **"Tên bệnh nhân" không tự điền** — hiện `form_data["ho_va_ten"]` chỉ được set nếu FE gửi `patient_name` (field nhập tay, `src/api/main.py:147-148`); KHÔNG có NER entity nào extract tên BN từ transcript dù transcript có "Phạm Minh Tuấn"/"anh Tuấn". Cần entity mới (PERSON_NAME) trong `l1c_ner.py` — Tầng 1 (FID, đụng schema NER).
    - **Gợi ý thuốc sai (Salbutamol 78%, Amlodipine 77%)** — `💊 Gợi ý thuốc` (RAG-based, FID-VN-011 layer 3b) gợi ý thuốc KHÔNG xuất hiện trong transcript. Cần xem lại embedding/threshold của RAG suggestion (`_collection.query`/`_embed_model` trong `src/core/l1b_drug_correct.py` layer 3b) — có thể threshold quá thấp hoặc query dùng sai đoạn transcript.
  - Log đầy đủ trong `docs/records/PENDING_REQUESTS.md` PA-023 (Andy review độ ưu tiên)
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
- [x] **VIETMED-FIX-001** ✅ Fix `scripts/download_vietmed.py` — bỏ `trust_remote_code`, thêm HF_TOKEN auth (commit `3fd6990`, đã verify code OK 2026-06-11)
- [x] **VIETMED-FIX-001 v2** ✅ (2026-06-12) — root cause thật: dataset ID SAI `doof-ferb/VietMed`
  (404, không tồn tại) từ đầu. Đúng là **`leduckhai/VietMed`** — 16h labeled, MIT, **KHÔNG gated**,
  KHÔNG cần HF_TOKEN (PA-024 đóng, không cần nữa). Splits: train(2773)/dev(2912)/test(3437)/cv(85).
  Cũng fix audio decode: `Audio(decode=False)` + soundfile/librosa resample (torchcodec
  incompatible với torch version trong venv). Verify: download thật split `cv` (85 samples, 17MB)
  + smoke-test `train_asr_phowhisper.py` chạy OK với audio thật. `data/vietmed/` + manifest
  generated files → `.gitignore`. 956/956 PASS.
  - Dùng cho: TRAIN-001 PhoWhisper fine-tune (FID-VN-007) — chỉ còn chặn bởi 50-100h pilot audio
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
- [ ] **TRAIN-001:** Fine-tune PhoWhisper trên VietMed (16h labeled MIT, leduckhai/VietMed) + pilot audio (50–100h)
  - Datasets: `data/vietmed/` (leduckhai/VietMed, KHÔNG gated — verify 2026-06-12) + pilot audio
  - Target: WER 35–40% → <20% | Drug CEER 0.90 → <0.10
  - GPU: **Colab/Kaggle free-tier** (quyết định 2026-06-11, thay VNG/FPT cho giai đoạn pilot) —
    setup guide `docs/dev/COLAB_KAGGLE_TRAINING.md` | **FID-VN-007 ✅ DONE (v1+v2+v3, 2026-06-11/12)**
    — pipeline + Colab/Kaggle manifests/fp16 + VietMed fix (dataset ID đúng, không gated, audio
    decode fix) sẵn sàng. **VietMed 16h có thể train ngay** (local hoặc Colab/Kaggle, không PII).
    Full run (đủ 50-100h) vẫn chờ pilot audio.
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
