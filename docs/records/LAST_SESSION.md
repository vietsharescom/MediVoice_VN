# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260609j
## Thời gian: 2026-06-09 (đêm)
## Version: v0.11.2 → v0.11.3

---

## Trạng thái đầu → cuối
v0.11.2 | 817 tests → v0.11.3 | 817 tests (no new tests — bug fixes + UI + revert)

## 1. Actions Completed
- Files sửa:
  - `src/core/l1c_ner.py` — CT-018: thêm `_RE_BP_DIGITS` (bắt "120 trên cao 80"→120/80), `_RE_NHIET_DO`/`_RE_NHIET_DO_SPLIT` thêm `(?:là\s*)?` (bắt "nhiệt độ là 39 độ c"→39.0)
  - `src/api/static/index.html` — CT-015: card "🩺 Trợ lý AI của Bác sĩ" (DVP Layer 1 registration), `DVP.init()`/`DVP.save()`/`DVP.edit()`, lưu `mv_doctor_cchn` vào localStorage, gọi `POST /api/doctors` + `GET /api/doctors/{cchn}`
  - `src/api/main.py` + `src/core/l0_normalize.py` — A2-VAD: wire `vad_chunk_audio()` + `transcribe_chunks()` vào `/transcribe`, cache `_vad_model` module-level → **REVERTED ngay sau live test** (về lại `transcribe()` whole-file)
  - `docs/records/BACKLOG.md`, `docs/records/PENDING_REQUESTS.md` — cập nhật CT-015 ✅ DONE, A2-VAD-CHUNK note REVERT + CT-019 mới
- Commits: `0300b53` (PDF font + ho_hap, từ đầu phiên) · `91c4369` (CT-018 NER fix) · `270cea3` (A2 wire) · `271b82a` (A2 revert + CT-015 DVP UI)
- Tests chạy: `pytest tests/ -q` → **817/817 PASS** (xác nhận lại cuối phiên, không regression)
- Báo cáo phân tích (chat, không tạo file):
  - So sánh pipeline hiện tại vs BENCH-002b baseline — kết quả tệ do server CŨ chưa restart, sau restart vẫn còn lỗi → traced về A2-VAD regression
  - Giải thích CT-004/GAP-005 (18 API integration tests)
  - So sánh cấu trúc layer FID-VN-010 v2.0 vs live wiring — phát hiện A2 chưa wire (trước khi wire+revert)
  - Trả lời: model ASR KHÔNG đổi (PhoWhisper-medium, baseline gốc) — A1/A3 chỉ là pre/post-processing
  - Trả lời: WER target <20% ✅ ĐẠT (ALL=18.4%, nhưng HN=29.3% chưa đạt) | Drug CEER <0.10 🔴 CHƯA ĐẠT (proxy miss ≈44%)

## 2. Decisions
- **Owner Decisions (Andy):**
  - Test thực tế A2-VAD ngay sau khi wire → phát hiện regression nặng ("KHÔNG NHẬN DẠNG ĐƯỢC GÌ LUÔN") → ra lệnh revert ngay
  - Yêu cầu DVP registration UI triển khai ngay trong scope FID-VN-012 hiện có (không cần FID mới)
- **Technical Decisions (Claude):**
  - Revert A2-VAD wiring NGAY khi có bằng chứng live regression — không debug "tại chỗ" để tránh kéo dài downtime cho Andy
  - Giữ `_vad_model` cache (module-level lazy load) trong `l0_normalize.py` dù chưa wire — vô hại, tránh reload khi A2 được wire lại sau debug
  - Không tạo FID mới cho DVP UI — đã nằm trong scope FID-VN-012 §3 đã approve (PA-012)

## 3. Architecture Changes
- **A2-VAD-CHUNK**: KHÔNG còn wired vào `/transcribe` — pipeline hiện tại dùng `transcribe()` whole-file (giống trước phiên này). `vad_chunk_audio()` + `transcribe_chunks()` vẫn tồn tại với 18 tests PASS nhưng KHÔNG được gọi từ API.
- Không có thay đổi nào khác ảnh hưởng L0→L10.

## 4. Tasks Created
- `CT-019` 🔴 HIGH — A2 VAD-chunk regression: cần debug offline (so sánh per-chunk transcript vs whole-file transcript trên cùng audio) trước khi wire lại. KHÔNG tự ý wire lại nếu chưa A/B test rõ ràng.

## 5. Pending Items
- `CT-019` 🔴 — A2-VAD debug (mới, ưu tiên cao nhất phiên sau)
- `CT-016` ⏳ — Transcribe accuracy regression, cần Andy cung cấp audio file mới + ground truth
- `CT-017` ⏳ — GG Drive backup, chờ Andy cung cấp đường dẫn JSON service account key
- `CT-014` ⏳ — FID-VN-013 Voice Calibration, chờ Andy mô tả flow chi tiết
- `CT-011` — ORCH-001 FID đầy đủ (carry-over)
- `VIETMED-FIX-001` — carry-over (HF_TOKEN, ~5 LOC)

## 6. Risks / Confusions
- 🔴 **A2-VAD regression (CT-019)**: hypothesis là PhoWhisper hallucinate nặng trên chunk ngắn độc lập + `initial_prompt` (drug list) lặp lại mỗi chunk gây bias sai sang thuật ngữ y khoa không liên quan — CHƯA xác nhận bằng A/B test, cần làm trước khi động lại A2.
- 🔴 **Chất lượng ASR tổng thể (drug recall, hallucination)** = giới hạn của PhoWhisper-medium chưa fine-tune. WER overall đã đạt mục tiêu (<20%) nhưng Drug Recall (55.6%LB, target ≥70%) và Drug CEER (proxy ≈44% miss, target <10%) CHƯA đạt — không sửa được bằng patch nhỏ (regex/prompt), cần TRAIN-001 (fine-tune trên VietMed + audio pilot 50-100h). TRAIN-001 vẫn `[ ]` chưa bắt đầu, blocked bởi GPU/cloud VM + FID-VN-007.
- `data/drug_vectorstore/chroma.sqlite3` thay đổi (binary, runtime artifact từ chạy server/tests) — đã commit cùng phiên trước, tiếp tục commit theo cùng pattern.

---

## Phiên tiếp theo — thứ tự ưu tiên
1. [CT-019] 🔴 Debug A2-VAD-chunk regression — A/B test per-chunk vs whole-file transcript offline trước khi wire lại. KHÔNG bật lại cho đến khi có kết quả rõ ràng.
2. [TRAIN-001 prep] 🔴 Chất lượng ASR tổng thể (drug recall, hallucination) = giới hạn PhoWhisper hiện tại — cần audio pilot thật + GPU/cloud VM + FID-VN-007 approval, không sửa được bằng patch nhỏ.
3. [CT-011] ORCH-001 FID — viết FID cho phần Orchestrator còn lại, chờ Andy approve
4. [VIETMED-FIX-001] Fix `scripts/download_vietmed.py` — remove trust_remote_code + HF_TOKEN (~5 LOC)
5. [CT-016/CT-017/CT-014] Chờ Andy cung cấp audio+GT / GG Drive JSON key path / mô tả flow calibration
6. [PILOT-DN] Andy test demo app tại phòng khám Đà Nẵng — thu audio thật
