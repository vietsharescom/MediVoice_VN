# PENDING_REQUESTS.md | DS-VN-REC-PR
# MediVoice VN — Theo dõi Requests Chưa Xử Lý
# Auto-checked by scripts/iso_audit.py mỗi phiên (Step D)
# v1.0 | 2026-06-06

---

## CÁCH ĐỌC FILE NÀY

```
ANDY_ACTION  = Andy cần làm gì đó (record audio, review doc, cung cấp thông tin...)
CLAUDE_TODO  = Claude có task chưa hoàn thành từ phiên trước
THIRD_PARTY  = Cần copy/paste cho ChatGPT/Grok review (consultation pending)
SYSTEM       = Hệ thống yêu cầu review định kỳ

Status: PENDING → IN_PROGRESS → DONE | DISMISSED
```

Claude đọc file này MỖI PHIÊN — báo cáo PENDING items trước khi làm bất cứ điều gì.
Nếu Andy trả lời/làm xong → Claude cập nhật status → DONE.

---

## ANDY_ACTION — Andy cần làm

| ID | Mô tả | Priority | Status | Created | Nhắc #|
|---|---|---|---|---|---|
| PA-001 | **Record pilot audio** — audio pilot đã có tại `data/audio/`. Partial CEER chạy xong: 0/10 coverage. Cần ground truth để đo full CEER. | 🔴 HIGH | ✅ DONE | 2026-06-06 | 2 |
| PA-002 | **Luật sư VN** — đã phản hồi + review `docs/compliance/DPA_TEMPLATE.md`. | 🔴 HIGH | ✅ DONE | 2026-06-06 | 2 |
| PA-003 | **Ký `docs/compliance/DPA_TEMPLATE.md`** với BS pilot Đà Nẵng — đã ký. | 🔴 HIGH | ✅ DONE | 2026-06-06 | 2 |
| PA-004 | **BS Onboarding Checklist** — đã ký với BS pilot. | 🟡 MEDIUM | ✅ DONE | 2026-06-06 | 1 |
| PA-006 | **Ground truth labels (dental)** — Mở `data/audio/dental/ground_truth_dental_template.json`, điền chan_doan/drugs/vitals/tai_kham cho từng file audio nha khoa. Dental audio đã move sang `data/audio/dental/`. | 🟡 MEDIUM | ✅ DONE (Claude 2026-06-10) | 2026-06-08 | 4 |
| PA-009 | **BENCH-GT-001** — Điền GT cho 54/57 clips còn lại trong `data/eval/ref_voice_transcripts_review.txt` (Clip2+Clip3 ưu tiên). Cần để đo BENCH-002b CEER thật + PhoBERT GO criteria. | 🔴 HIGH | ✅ DONE (Andy 2026-06-09 — 57/57 filled) | 2026-06-09 | 1 |
| PA-012 | **FID-VN-012 APPROVE** — Review và approve `fids/FID-VN-012.md` (DVP — Doctor Voice Profile) sau khi Claude viết xong CT-010. 4-AI consensus 85% confidence: Option C phased, 12 specialties, alias Human Gate. | 🔴 HIGH | ✅ DONE (Andy 2026-06-09 — "TRIỂN KHAI NGAY") | 2026-06-09 |
| PA-010 | **FID-VN-010 APPROVE** — Review và approve `fids/FID-VN-010.md` (AI Pipeline Redesign v2.0). Đặc biệt: Q1 Phase 0 implement A1/A2/A3 ngay? Q2 L4-REDESIGN-001 safety priority? | 🔴 HIGH | ✅ DONE (Andy 2026-06-09 — approved ngầm, ra lệnh implement A1/A2/A3/L4) | 2026-06-09 | 1 |
| PA-011 | **CONS-20260610-003 Q1+Q3 Decision** — Chốt Q1 (PARALLEL+exit vs Shadow Mode) và Q3 (VALIDATE+SUPPLEMENT vs VALIDATE ONLY) cho FID-VN-009 PhoBERT implementation. | 🟡 MEDIUM | ✅ DONE (Andy 2026-06-09 — Q1=PARALLEL+early-exit · Q3=VALIDATE+SUPPLEMENT) | 2026-06-09 | 1 |
| PA-007 | **Corpus ChatGPT** — `docs/dev/CLINICAL_TEST_CORPUS_VN.md` v2.0 đã có 1210 dòng, scripts by_disease/by_accent/by_drug_hard đầy đủ | 🟡 MEDIUM | ✅ DONE (2026-06-08) | 2026-06-08 | 3 |
| PA-008 | **Semi-synthetic ghi âm** — ✅ 30 files VI-only (HN/SG/CT × 5 SC × 2 takes). CA bỏ (không thực tế VN). WER: SG 25.8% / CT 30.4% / HN 34.6%. Cần TRAIN-001 để xuống ≤20%. | 🔴 HIGH | ✅ DONE (2026-06-07) | 2026-06-09 | 2 |
| PA-005 | Approve FID-VN-004 | 🔴 HIGH | ✅ DONE | 2026-06-06 | 1 |
| PA-013 | **GROQ_API_KEY cho benchmark** — Để chạy CT-029 (benchmark Groq pipeline trên cùng 57 clip BENCH-002b để so sánh CEER head-to-head với local), Andy cần set biến môi trường `GROQ_API_KEY` (KHÔNG paste key vào chat) — vd `$env:GROQ_API_KEY="gsk_..."` trước khi Claude chạy `tools/bench_groq.py`. | 🔴 HIGH | ⏳ PENDING | 2026-06-10 | |

---

## CLAUDE_TODO — Claude có task chưa hoàn thành

| ID | Mô tả | Priority | Status | Created |
|---|---|---|---|---|
| CT-001 | Viết FID-VN-004 | 🔴 HIGH | ✅ DONE — fids/FID-VN-004.md | 2026-06-06 |
| CT-002 | Implement VN-ROUTER-001 | 🔴 HIGH | ✅ DONE — 232 tests PASS | 2026-06-06 |
| CT-003 | Viết tests GAP-002 (PII scan unit tests) | 🔴 HIGH | ✅ DONE | 2026-06-06 |
| CT-004 | Viết tests GAP-005 (API integration tests) | 🔴 HIGH | ✅ DONE | 2026-06-06 |
| CT-006 | **Drug CEER fix** — DEFERRED. Blocked by TRAIN-001 (cần audio thật). Andy approved defer 2026-06-08. \| P0.5.2d | 🟡 LOW | DEFERRED | 2026-06-08 |
| CT-008 | **GAP-003** Unit tests L8 error handler — `tests/unit/test_l8_error_handler.py` 20 tests | 🟡 MEDIUM | ✅ DONE (2026-06-08) | 2026-06-08 |
| CT-009 | **GAP-004** Unit tests L9a PDF export — `tests/unit/test_l9a_pdf_export.py` 15 tests | 🟡 MEDIUM | ✅ DONE (2026-06-08) | 2026-06-08 |
| CT-007 | **Followup CEER fix** — Cải thiện tai_kham regex `src/core/l1c_ner.py` → Followup CEER **0.7→0.1** ✅ \| P0.5.2e | 🟡 MEDIUM | ✅ DONE | 2026-06-08 |
| CT-005 | **DEPLOY-001** Windows installer (venv approach) — install.bat + start.bat + check_env + setup_facility \| P0.6 | 🟡 MEDIUM | ✅ DONE — 287/287 PASS | 2026-06-06 |
| CT-010 | **FID-VN-012** — Viết Doctor Voice Profile (DVP) FID: 3 layers (Metadata+SpecialtyVocab+PersonalAlias), 8 ACs, DoctorProfile SQLite schema, UX "Trợ lý AI của BS [Tên]". Đọc `docs/records/consultations/CONS-20260610-004.md` + WIN2 Phần 1. | 🔴 HIGH | ✅ DONE — fids/FID-VN-012.md (2026-06-09) | 2026-06-09 |
| CT-011 | **ORCH-001 FID** — Viết FID đầy đủ cho Orchestrator v1.0: `detect_confusion()`, `create_consultation_request()` (CONSULTATION_TEMPLATE format), tự động hóa `close_session()` (auto-update BACKLOG/PROJECT_PROGRESS/CHANGELOG/LAST_SESSION + iso_audit --increment-session + commit/push). Prototype hiện tại: `scripts/orchestrator.py` (start/consult/check chạy thật với Groq). | 🟡 MEDIUM | ⏳ PENDING | 2026-06-09 |
| CT-012 | **PDF font fix** — `src/core/l9a_pdf_export.py` dùng Helvetica (không hỗ trợ dấu VN) → ô vuông đen "■" trong Mẫu 15/BV1. Đã fix: bundle `assets/fonts/DejaVuSans*.ttf` + đăng ký font family. 817/817 PASS. | 🔴 HIGH | ✅ DONE (2026-06-09) | 2026-06-09 |
| CT-013 | **`ho_hap` specialty bug** — `SPECIALTY_DRUG_CLASSES` (`src/core/l1a_asr.py`) thiếu key `"ho_hap"` (dùng trong dropdown index.html) → fallback None → không ưu tiên thuốc hô hấp. Đã thêm mapping (beta2_agonist, corticosteroid, kháng sinh hô hấp...). | 🟡 MEDIUM | ✅ DONE (2026-06-09) | 2026-06-09 |
| CT-014 | **FID-VN-013 — Voice Calibration (DVP Layer 3)** — Andy mô tả chi tiết flow (2026-06-10): (1) Khi BS đăng ký/setup ban đầu (KHÔNG bắt buộc mỗi phiên — optional, BS có thể bỏ qua), AI "chẩn đoán tông giọng" của BS (tốc độ nói, ngắt nghỉ, vùng miền) để tự điều chỉnh lựa chọn ASR cho khớp giọng chuẩn hơn; (2) UX: visualization dạng "AI assistant" với sóng âm thanh (waveform) theo tông giọng BS — ấn tượng, giúp BS THẤY được AI đang "nghe" mình; (3) Auto-adapt: nếu BS nói nhanh/giọng vùng (vd "mô răng rứa" — miền Trung) → model bắt theo; nếu nói chậm/dừng lâu → model tự điều chỉnh theo kịp. Đây là phần MỞ RỘNG cho FID-VN-012 §6 (calibration hiện chỉ lưu region/specialty/english_level/speaking_speed dạng form, KHÔNG có voice sample/waveform UI — đúng như Andy nhận xét "frontend thiết kế phần BS nhập vào nhưng chưa có tác dụng gì" — thực ra CÓ tác dụng (inject vào ASR prompt + dialect_norm theo CT-015/FID-VN-012) nhưng KHÔNG có visual feedback cho BS thấy). Cần: FID mới (scope waveform UI, voice sample storage — lưu tạm hay không lưu theo Privacy by Design L0, auto-adapt logic). | 🔴 HIGH | ⏳ PENDING — viết FID-VN-013 dựa trên mô tả trên | 2026-06-10 |
| CT-015 | **DVP Layer 1 frontend UI** — Backend `/api/doctors` đã có (region/specialty/english_level/speaking_speed), nhưng `index.html` chưa có form đăng ký "Trợ lý AI của BS [Tên]". | 🟡 MEDIUM | ✅ DONE (2026-06-09) — card "🩺 Trợ lý AI của Bác sĩ" + DVP.save()/DVP.init() trong `src/api/static/index.html`, lưu localStorage + POST /api/doctors | 2026-06-09 |
| CT-019 | **🔴 A2 VAD-chunk regression** — Wire `vad_chunk_audio()`+`transcribe_chunks()` vào `/transcribe` → REVERTED ngay vì transcript "KHÔNG NHẬN DẠNG ĐƯỢC GÌ LUÔN" (test thực tế Andy). `scripts/debug_a2_vad_chunk.py` (CT-019 offline A/B) chạy trên 3 file pilot thật (12.2s/28.5s/92.6s): per-chunk = whole-file hoặc TỐT HƠN, `initial_prompt` KHÔNG ảnh hưởng (output giống hệt có/không prompt) — KHÔNG reproduce được lỗi "KHÔNG NHẬN DẠNG ĐƯỢC GÌ LUÔN" trên data hiện có. Hypothesis ban đầu (initial_prompt bias) BỊ LOẠI. Nghi ngờ mới: audio thực tế của Andy (ghi qua browser, có thể noisy/silence dài) → VAD over-segment thành nhiều chunk cực ngắn → hallucination tích luỹ — CẦN audio thật bị lỗi để test trực tiếp (liên quan CT-016). KHÔNG wire lại cho đến khi có audio đó. | 🔴 HIGH | ⏳ PENDING — chờ audio lỗi từ Andy (CT-016) | 2026-06-09 |
| CT-016 | **Transcribe accuracy regression (audio mới)** — **2026-06-10: Andy gửi ground truth đầy đủ (3 clip, BS Phan Đình Hiệp/Hà Nội + ca Ngô Thị Liên) + transcript thực tế từ live test**. So sánh phát hiện: (1) "ghi bệnh án bằng giọng nói"→"nghi vệ nán mặt giọng nói" (lỗi nặng câu giới thiệu); (2) "Mạch bảy mươi lăm lần một phút"→"mật bảy mươi lăm một phút" (mất "lần", "Mạch"→"mật"); (3) "Chẩn đoán theo dõi nhiễm khuẩn đường tiêu hóa"→"chẩn đoán theo thì..."; (4) tên thuốc Ciprofloxacin/Paracetamol/Oresol bị ASR garbling nặng ("si pô lo siêu âm si", "parasyte mode"). **Cần raw transcript (trước L1b) + audio file 3 clip để debug offline** — đối chiếu BENCH-002b (baseline: Drug Recall 55.6%, WER DN/SG 16.3%, WER HN 29.3%). | 🟡 MEDIUM | ⏳ PENDING — cần Andy gửi audio 3 clip (clip1/2/3) | 2026-06-09 |
| CT-020 | **NER miss: Mạch (pulse) khi ASR lỗi "Mạch"→"mật"** — `src/core/l1c_ner.py` `_RE_MACH` thiếu alias "mật". | 🟡 MEDIUM | ✅ DONE (2026-06-10) — thêm "mật" vào `_RE_MACH`, test `test_mat_alias_word_form`, 820/820 PASS | 2026-06-10 |
| CT-021 | **NER miss: Chẩn đoán khi ASR "theo dõi"→"theo thì" + "Kê"→"chê"** — `src/core/l1c_ner.py` `_RE_CHAN_DOAN` lookahead `_PRESCRIPTION_KW` cần "kê" nhưng ASR ra "chê", và "theo thì" chưa được skip như filler. | 🟡 MEDIUM | ✅ DONE (2026-06-10) — thêm `(?:theo\s*(?:dõi\|thì)\s+)?` filler + "chê" alias cho "kê" trong `_PRESCRIPTION_KW`, 2 tests mới, 820/820 PASS | 2026-06-10 |
| CT-022 | **🔴 SAFETY: L1b drug match — "Oresol" (bù nước) bị thay bằng "Xylometazoline" (thuốc nhỏ mũi)** — Đơn thuốc draft chỉ hiện "Xylometazoline" thay vì Ciprofloxacin + Paracetamol + Oresol. `Oresol` KHÔNG có trong `data/reference/drug_db_v200.json` (đã kiểm tra — `by_inn` không có key "Oresol"). Nghi: ASR garble "Oresol pha theo..." → fuzzy match Layer 2 (`_fuzzy_match`, cutoff 70%) khớp nhầm sang phonetic_variant "xylo me ta zo li ne" của Xylometazoline. | 🔴 HIGH | ✅ DONE (2026-06-10) — thêm "Oresol" (INN, brands ORS/Hydrite/Resomal, phonetic_variants "o re sol"/"ô rê sôn"/"o re son", drug_class `oral_rehydration_salt`) vào `data/reference/drug_db_v200.json` (155 drugs). Layer 1 exact-match giờ thắng trước Layer 2 fuzzy → "o re sol" KHÔNG còn nhầm sang Xylometazoline. Test `test_oresol_exact_not_xylometazoline` (`tests/unit/test_l1b_drug_correct_v2.py`), 821/821 PASS. ⚠️ `data/drug_vectorstore/` (RAG Layer 3b) chưa rebuild với Oresol — không block vì Layer 1 đã bắt trước, nhưng nên rebuild sau (CT-027). | 2026-06-10 |
| CT-023 | **🔴 UX/SAFETY: L4 per-drug confirm KHÔNG có nút "Xóa/Từ chối thuốc"** — `src/api/static/index.html` `renderDrugConfirmList()` mỗi dòng thuốc chỉ có checkbox "Xác nhận", và nút Lưu bị khoá đến khi 100% thuốc được tick (`updateApproveButton`). Nếu AI gợi ý SAI tên thuốc (vd CT-022: Xylometazoline), BS chỉ có 2 lựa chọn: (a) tick xác nhận thuốc SAI để được Lưu — nguy hiểm, hoặc (b) không tick được → kẹt, không Lưu được. Cần thêm nút "🗑️ Xóa" mỗi dòng để BS loại bỏ gợi ý sai trước khi Lưu (xóa khỏi `don_thuoc`, giảm `_drugTotal`), không tính vào yêu cầu xác nhận. | 🔴 HIGH | ⏳ PENDING | 2026-06-10 |
| CT-017 | **GG Drive backup tài liệu dev/ISO** — tiếp tục từ GCP service account key Andy gửi (project `valid-dragon-498814-b3`, SA `medivoice-uploader@...`). Cần Andy cung cấp đường dẫn file JSON key đã tải (KHÔNG paste JSON vào chat). Sau đó wire `gcp_service_account` vào `.streamlit/secrets.toml` + viết `scripts/backup_docs.py`. **SCOPE: chỉ tài liệu dev/ISO (non-PHI) — KHÔNG dùng cho audio pilot có giọng/PII bệnh nhân thật (xem CT-024).** | 🟡 MEDIUM | ⏳ PENDING — chờ JSON key file path | 2026-06-09 |
| CT-024 | **PILOT-PHASE EXCEPTION: audio pilot có PII → tạm lưu GG Drive (consent đã có)** — Andy xác nhận (2026-06-10) đã có consent từ BS + bệnh nhân + luật sư review riêng cho giai đoạn thử nghiệm → CHO PHÉP tạm lưu audio pilot (giọng+PII thật) lên GG Drive trong PHASE PILOT. Đã ghi ADR vào `docs/records/DECISIONS.md` (2026-06-10) + cập nhật `docs/compliance/RISK_REGISTER.md` R-P03 (exception, không đổi rule production). **Điều kiện**: (1) văn bản consent phải lưu tại `docs/compliance/` (DPA_TEMPLATE.md/BS_ONBOARDING_CHECKLIST.md — Andy cung cấp); (2) TRƯỚC launch chính thức phải di chuyển/xóa audio khỏi GG Drive → VN Cloud. Setup kỹ thuật tiếp tục theo CT-017 (cần JSON key path). | 🟡 MEDIUM | ✅ Quyết định ghi nhận (2026-06-10) — chờ CT-017 (JSON key) để wire kỹ thuật + chờ Andy upload văn bản consent | 2026-06-10 |
| CT-029 | **Benchmark harness Groq pipeline** — viết `tools/bench_groq.py` (clone từ `tools/bench_002b.py`), chạy `extract_clinical_data()`-style trên cùng 57 clip `data/eval/`, output CEER cùng format (Drug Recall/Precision, Diag, Vitals, Followup) để so sánh trực tiếp với local. Branch: `experiment/groq-degallucination`. | 🔴 HIGH | ⏳ PENDING — chờ PA-013 (GROQ_API_KEY) | 2026-06-10 |
| CT-028 | **PHƯƠNG ÁN 3 — Mix/Hybrid pipeline** — sau khi có số liệu CT-029 (Groq) + CT-027 (local cải thiện), quyết định kiến trúc lai (vd: ASR Groq whisper-large-v3 + extraction local deterministic l1b/l1c). Cần FID-VN-014 nếu approve. Branch dự kiến: `experiment/hybrid-pipeline` (tạo sau khi có số liệu). | 🟡 MEDIUM | ⏳ BLOCKED — chờ CT-029 + CT-027 | 2026-06-10 |
| CT-027 | **PHƯƠNG ÁN 5 — Tăng accuracy local pipeline** — cải thiện CEER local (hiện Drug Recall 55.6%, Diag 71.4%, Vitals 69.3% — BENCH-002b): (1) TRAIN-001 fine-tune PhoWhisper trên audio pilot; (2) mở rộng `drug_db_v200.json` alias/phonetic cho thuốc hay bị garble — ✅ Oresol DONE (CT-022); Ciprofloxacin: `phonetic_variants` hiện có ("xi pro phlo xa xin"...) nhưng KHÔNG khớp garble thực tế CT-016 "si pô lo siêu âm si" — **CHƯA THÊM** vì "siêu âm" = từ khóa lâm sàng phổ biến (siêu âm = ultrasound), thêm làm alias sẽ gây FALSE POSITIVE match mọi câu nhắc "siêu âm". Cần thêm audio/transcript mẫu khác để tìm pattern garble ổn định hơn trước khi sửa. CT-034 (Paracetamol "pha ra citamon") cùng dạng — PENDING; (3) tiếp tục NER alias fixes kiểu CT-018/020/021 — ✅ CT-030 (nhiệt độ "chấm"), CT-031 (chẩn đoán "che"), CT-032 (tái khám "tái kháng") DONE 2026-06-10; (4) rebuild `data/drug_vectorstore/` (RAG) với drug_db mới (155 drugs, chưa rebuild). Branch: `experiment/local-accuracy`. | 🟡 MEDIUM | 🔵 IN PROGRESS — (2) Oresol done, CT-034 pending; (3) CT-030/031/032 done; RAG-rebuild/TRAIN-001 còn pending | 2026-06-10 |
| CT-026 | **PHƯƠNG ÁN 4 — Giảm hallucination demo Groq** (`demo/app.py` `extract_clinical_data()`) — áp guardrail: (1) thêm quy tắc prompt "CHỈ liệt kê thuốc có tên xuất hiện trong TRANSCRIPT, KHÔNG thêm thuốc khác dù phổ biến — nếu không có thuốc nào → don_thuoc=[]"; (2) `temperature=0` (hiện 0.1); (3) thêm field `trich_dan` (verbatim quote) cho mỗi thuốc + post-process fuzzy-validate `trich_dan` có thật trong transcript, loại item không khớp; (4) cross-check với `l1b_drug_correct` local. Branch: `experiment/groq-degallucination`. Mục tiêu: rerun test W1-001 → don_thuoc chỉ còn 3 thuốc đúng (Amlodipine/Losartan/Atorvastatin), không còn 9 thuốc bịa. | 🔴 HIGH | ⏳ PENDING | 2026-06-10 |
| CT-025 | **🔴 CRITICAL SAFETY: Demo Groq (`medivoice-vn-demo.streamlit.app`) — LLM (llama-3.3-70b) BỊA RA 9 thuốc KHÔNG có trong transcript** — Andy chạy test script W1-001 (Tim mạch — 3 thuốc: Amlodipine 5mg, Losartan 50mg, Atorvastatin 20mg). ASR (Groq whisper-large-v3) garble nhưng vẫn nhận diện đúng 3 tên thuốc + đúng liều Losartan/Atorvastatin (Amlodipine bị đổi 5mg→50mg, app tự flag DOSE_OUT_OF_RANGE 100% — đúng cơ chế). Nhưng **Mục V. Đơn thuốc cuối cùng hiện "12/12 thuốc đã xác nhận"** gồm thêm Clopidogrel, Valsartan, Vitamin D3, Meloxicam, Sertraline, Enalapril, Paracetamol — **KHÔNG hề có trong audio/transcript/ground truth**. Đây là LLM hallucination — model tự "hoàn thiện" phác đồ tăng huyết áp+rối loạn lipid máu điển hình thay vì chỉ trích xuất từ lời BS nói. Vi phạm trực tiếp Absolute Rule #7 (AI KHÔNG tự ra chỉ định ngoài lời BS). Thêm: ASR có hallucination kiểu Whisper kinh điển — chèn câu "Hãy subscribe cho kênh La La School..." vào cuối transcript (không liên quan lâm sàng); BP 145/90 (ground truth) → ASR ra 115/90; Chẩn đoán bị cắt cụt "tăng huyết áp" (thiếu "độ 2 kèm rối loạn lipid máu" + thiếu mã E78). **KẾT LUẬN: Kiến trúc Groq cloud Whisper+LLM (`demo/app.py`) KHÔNG phù hợp làm backend production** — ngoài vi phạm NĐ13/2023 (audio ra khỏi VN, đã biết), rủi ro bịa đơn thuốc nghiêm trọng hơn nhiều so với pipeline local hiện tại (PhoWhisper+regex NER chỉ miss/nhầm tên thuốc đã nói, KHÔNG bịa thuốc mới — xem CT-022). Giữ nguyên TECH DECISIONS LOCKED (PhoWhisper-medium offline + PhoBERT/CRF deterministic). Demo Groq chỉ dùng tham khảo/so sánh, KHÔNG làm hướng đi production. | 🔴 CRITICAL | ⏳ PENDING — Andy review, cân nhắc thêm guardrail "chỉ trích xuất thuốc có trong transcript" nếu vẫn muốn dùng Groq cho mục đích khác (vd benchmark ASR riêng) | 2026-06-10 |
| CT-018 | **NER fix: Huyết áp digit-form + Nhiệt độ "là"** — `src/core/l1c_ner.py`: (1) thêm `_RE_BP_DIGITS` để bắt "120 trên cao 80"→120/80 (trước đây chỉ bắt word-form); (2) `_RE_NHIET_DO`/`_RE_NHIET_DO_SPLIT` thêm `(?:là\s*)?` để bắt "nhiệt độ là 39 độ c" (trước đây regex fail vì "là" không phải whitespace/colon). 817/817 PASS. | 🟡 MEDIUM | ✅ DONE (2026-06-09) | 2026-06-09 |
| CT-030 | **NER fix: Nhiệt độ decimal mất khi ASR "phẩy"→"chấm"** — Test thật Clip 1/2/3 (BS Phan Đình/Q.Tân Phú/BN Nguyễn Văn An, viêm họng cấp): "ba mươi bảy chấm chín độ c" (37.9°C ground truth) → `_RE_DEC_WORDS` (`src/core/l1c_ner.py`) chỉ nhận "phẩy" → `nhiet_do=37.0` (mất phần thập phân). | 🟡 MEDIUM | ✅ DONE (2026-06-10) — `_RE_DEC_WORDS` thêm `(?:phẩy\|chấm)`, test `test_temp_cham_alias_for_phay`, 822/822 PASS | 2026-06-10 |
| CT-031 | **NER fix: Chẩn đoán/ICD-10 trống khi ASR "Kê"→"che" (không dấu)** — Cùng test Clip 1/2/3: "...chẩn đoán viêm phẩm cấp che Amoxicillin..." → `_PRESCRIPTION_KW` chỉ nhận "kê"/"chê" (CT-021) không nhận "che" → `_RE_CHAN_DOAN` lookahead fail → `chan_doan`/`icd10`/`tai_kham` đều trống trên UI. | 🟡 MEDIUM | ✅ DONE (2026-06-10) — thêm "che" vào `_PRESCRIPTION_KW`, test `test_chan_doan_che_no_diacritic`, 823/823 PASS. Lưu ý: `chan_doan` capture ra "viêm phẩm cấp" (ASR garble "họng"→"phẩm") nên KHÔNG tự map ICD-10 J02.9 — chấp nhận được vì L4 yêu cầu BS sửa. | 2026-06-10 |
| CT-032 | **NER fix: Tái khám trống khi ASR "tái khám"→"tái kháng"** — Cùng test Clip 1/2/3: "...tái kháng sau năm ngày hoặc sớm hơn nếu kéo dài" → `_RE_TAI_KHAM`/`_RE_TAI_KHAM_DIAGNOSIS`/`_PRESCRIPTION_KW` chỉ nhận "kh[aá]m" (đuôi "-m"), không nhận "kháng" (đuôi "-ng") → `tai_kham` trống trên UI. | 🟡 MEDIUM | ✅ DONE (2026-06-10) — 3 regex đổi `kh[aá]m` → `kh[aá](?:m\|ng)`, 2 test mới (`TestBugO_TaiKhangAlias`), 825/825 PASS | 2026-06-10 |
| CT-033 | **🔴 SAFETY: L1b "Vitamin D3" hallucination từ garble exam-finding (KHÁC CT-022)** — Cùng test Clip 1/2/3: BS nói khám "amidan sưng nhẹ" (exam finding, KHÔNG phải chỉ định thuốc) → ASR garble thành chuỗi chứa literal "Vitamin D3 xương nhẹ" → L1b match ĐÚNG kỹ thuật (chuỗi đúng là "Vitamin D3") nhưng SAI ngữ nghĩa → đơn thuốc UI hiện "Vitamin D3" — thuốc BS KHÔNG hề kê. Khác CT-022 (đó là garble TÊN THUỐC thật bị fuzzy-match nhầm thuốc khác); đây là garble CÂU KHÁM bị nhận nhầm thành tên thuốc. Không có fix regex đơn giản (root cause ở ASR, không ở L1b matching logic) — **mitigation chính = CT-023 (nút "🗑️ Xóa" mỗi dòng thuốc)** để BS loại bỏ trước khi Lưu. | 🔴 HIGH | ⏳ PENDING — không tự sửa được bằng regex; ưu tiên CT-023 làm guardrail UI | 2026-06-10 |
| CT-034 | **Drug recall miss: "Paracetamol"→"pha ra citamon" không match** — Cùng test Clip 1/2/3: BS kê Paracetamol nhưng ASR garble "pha ra citamon" → L1b không match (Layer 1 exact + Layer 2 fuzzy đều miss) → đơn thuốc UI thiếu Paracetamol (chỉ còn Amoxicillin + "Vitamin D3" bịa — xem CT-033). Một phần CT-027 (drug_db alias expansion) — cần thêm "pha ra citamon"/biến thể tương tự vào `phonetic_variants` của Paracetamol trong `data/reference/drug_db_v200.json`, kiểm tra fuzzy cutoff không gây FP. | 🟡 MEDIUM | ⏳ PENDING — phần của CT-027 | 2026-06-10 |
| CT-035 | **PDF screenshot Andy gửi (13:36 giờ khám / record lúc 13:44:14) là từ SERVER CŨ** — server có CT-030/031/032 fix khởi động lúc 13:44:42 (PID 12736), tức **28 giây SAU** record được tạo → PDF đó KHÔNG phản ánh fix mới (giải thích vì sao nhiệt độ vẫn "37°C" thay vì 37.9, chẩn đoán/ICD-10 vẫn "---"). Cần Andy ghi âm lại 1 lần nữa trên server hiện tại (PID 12736+) để xác nhận 3 fix có hoạt động trên audio thật (không chỉ unit test). | 🟡 MEDIUM | ⏳ PENDING — chờ Andy re-test | 2026-06-10 |
| CT-036 | **Đường dẫn lưu trữ — trả lời câu hỏi Andy "đang lưu ở đâu"**: (1) **Voice/audio**: KHÔNG lưu — `l0_normalize.purge_audio()` xóa file WAV tạm sau khi xử lý (Privacy by Design, đúng pipeline L0 FROZEN). Audio pilot có PII chỉ lưu tạm GG Drive theo exception CT-024 (consent riêng), KHÔNG phải flow mặc định; (2) **Hồ sơ kết quả khám**: SQLite `medivoice.db` (root, bảng `clinical_records`, `form_data_enc` mã hoá Fernet) + PDF xuất tại `exports/BA_<record_id>_<timestamp>.pdf`; (3) **File chuẩn để so sánh đo lường (ground truth/benchmark)**: `data/eval/` — `bench_002b_results.json`, `drug_correction_eval.json`, `ref_voice_transcripts.json` + `ref_voice_transcripts_review.txt`. Phát hiện thêm: `data/medivoice.db` là file RỖNG (0 bytes, leftover) — KHÔNG dùng, có thể xóa khi dọn dẹp. | 🟢 LOW | ✅ TRẢ LỜI — không cần action thêm trừ khi Andy muốn dọn `data/medivoice.db` rỗng | 2026-06-10 |

---

## THIRD_PARTY — Cần hỏi AI khác

| ID | Mô tả | Priority | Status | Created |
|---|---|---|---|---|
| TP-002 | **CONS-20260610-004** — Doctor Voice Profile (DVP) architecture. 3/3 responses received (ChatGPT ✅ + Grok ✅ + Copilot ✅). 4-AI synthesis hoàn thành. Andy trả lời O1-O4 xong (2026-06-09). FID-VN-012.md DONE. File: `docs/records/consultations/CONS-20260610-004.md` | 🟡 MEDIUM | ✅ DONE | 2026-06-09 |

---

## SYSTEM — Review định kỳ

| ID | Mô tả | Tần suất | Next due | Status |
|---|---|---|---|---|
| SY-001 | Weekly ISO audit (iso_audit.py --weekly) | Session 7 | Session 7 | SCHEDULED |
| SY-002 | Monthly MANAGEMENT_REVIEW entry | Monthly | 2026-07-06 | SCHEDULED |
| SY-003 | BENCH-002 review sau khi có audio | Post-pilot | TBD | WAITING |

---

## LỊCH SỬ ĐÃ XỬ LÝ (gần đây)

| ID | Mô tả | Resolved | By |
|---|---|---|---|
| CT-003 | tests/unit/test_pii_scan.py — 27 tests PASS | 2026-06-06 | Claude |
| CT-004 | tests/integration/test_api.py — 18 tests PASS | 2026-06-06 | Claude |
| CT-001 | `fids/FID-VN-004.md` viết xong | 2026-06-06 | Claude |
| PA-004 | `docs/compliance/BS_ONBOARDING_CHECKLIST.md` ký với BS pilot | 2026-06-06 | Andy ✅ |
| PA-001 | Audio pilot record xong → `data/audio/pilot/` | 2026-06-08 | Andy ✅ |
| PA-002 | Luật sư VN phản hồi + review `docs/compliance/DPA_TEMPLATE.md` xong | 2026-06-08 | Andy ✅ |
| PA-003 | `docs/compliance/DPA_TEMPLATE.md` đã ký với BS pilot Đà Nẵng | 2026-06-08 | Andy ✅ |

---

## QUY TẮC CẬP NHẬT

```
CLAUDE làm khi mở phiên:
  1. Đọc file này
  2. Báo cáo tất cả PENDING items TRƯỚC khi làm việc khác
  3. "Andy có X items cần làm: PA-001, PA-002..."
  4. "Claude có Y items chưa xong: CT-001, CT-002..."

CLAUDE làm trong phiên:
  → Khi nhận yêu cầu mới từ Andy → thêm vào PA-xxx ngay
  → Khi Claude có task chưa xong (ví dụ list 5 items làm 3) → thêm CT-xxx
  → Khi cần third-party review → thêm TP-xxx

CLAUDE làm khi đóng phiên:
  → Update status các items đã xử lý → DONE
  → Tăng số nhắc cho items vẫn PENDING (Nhắc #)
  → Flag nếu item PENDING > 3 phiên → escalate
```

---

*DS-VN-REC-PR | PENDING_REQUESTS v1.0 | 2026-06-06*
