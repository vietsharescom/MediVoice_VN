# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260610
## Thời gian: 2026-06-10
## Version: v0.11.3 → v0.11.4

---

## Trạng thái đầu → cuối
v0.11.3 | 817 tests → v0.11.4 | 826 tests (+9, từ branch `experiment/local-accuracy`)

## 1. Actions Completed
- Files sửa:
  - `src/core/l1c_ner.py` — CT-030/031/032: NER fix từ Real Clip 1-3 (Mạch/pulse khi ASR "mật"+mất "lần", Chẩn đoán/ICD-10 khi ASR "theo dõi"→"theo thì")
  - `src/core/l1b_drug_correct.py` + RAG vectorstore — CT-034: alias "pha ra citamon" → Paracetamol, rebuild `data/drug_vectorstore/`
  - `src/api/static/index.html` — CT-023: nút "🗑️ Xóa" mỗi dòng thuốc trong L4 confirm list (`renderDrugConfirmList`, `_currentDrugs`/`_drugConfirmed`, `removeDrug(idx)`, `_renderDrugRows()`); `buildEditedFormData()` dùng `_currentDrugs` (sau khi BS xóa) làm `don_thuoc` cuối — mitigates CT-022 (Oresol→Xylometazoline) + CT-033 (hallucinated Vitamin D3)
  - `.gitignore` (master) — thêm `Andy/private_notes.md`; xóa `Andy/Note_Andy.md` + `Andy/Improvements.md` (đã consolidate vào `private_notes.md`, gitignored)
  - `docs/records/PENDING_REQUESTS.md`, `docs/records/BACKLOG.md`, `docs/records/PROJECT_PROGRESS.md`, `CHANGELOG.md`, `CLAUDE.md` — cập nhật CT-023/026/028/029/030-034 status
- Git ops:
  - Merge `experiment/local-accuracy` (CT-022/030/031/032/034) → `master` (fast-forward)
  - Re-deleted `Andy/Note_Andy.md`/`Andy/Improvements.md` (tái xuất hiện sau fast-forward)
  - Merge `origin/master` (`970f24c` "Added Dev Container Folder") vào local `master`
  - Commits: `bac583d` (docs CT-026/029/028/PA-013 + cleanup) · `2c3186a` (CT-023 UI) · `079afcc` (merge origin)
- Tests chạy: `pytest tests/ -q` → **826/826 PASS** (xác nhận sau merge, không regression)
- Báo cáo phân tích (chat, không tạo file):
  - Kết luận thử nghiệm CT-026/CT-029 (Groq whisper-large-v3 + llama-3.3-70b vs local pipeline trên 57 clip thật)

## 2. Decisions
- **Owner Decisions (Andy):**
  - **CT-028 (FINAL)**: GIỮ 100% local pipeline (PhoWhisper + PhoBERT/CRF), KHÔNG làm hybrid ASR Groq. Lý do: local thắng WER (18.4% vs 32.6%), Drug Precision (83.3% vs 57.1%), Diag CEER (0.286 vs 0.429); Groq chỉ thắng Drug Recall (88.9% vs 55.6%) nhưng hallucination chưa fix triệt để (vi phạm Absolute Rule #7).
  - Branch `experiment/groq-degallucination` (CT-026+CT-029) GIỮ LẠI làm reference, **KHÔNG merge vào master** — mở lại khi cần so sánh Groq vs local hoặc đánh giá hybrid tương lai.
  - Ưu tiên kế tiếp: **TRAIN-001** (fine-tune PhoWhisper).
  - Frontend cần redesign theo yêu cầu → đã làm CT-023 (nút Xóa thuốc L4).
- **Technical Decisions (Claude):**
  - Dùng node-based DOM-stub test để verify logic CT-023 (delete/confirm/buildEditedFormData) thay vì browser test đầy đủ (UI page load verified qua curl/uvicorn).
  - Re-delete `Andy/Note_Andy.md`/`Andy/Improvements.md` sau fast-forward merge (file cũ tái xuất hiện từ branch `experiment/local-accuracy`).
  - Revert binary churn `data/drug_vectorstore/chroma.sqlite3` không liên quan trước khi commit (giữ lại rebuild thật từ CT-034).

## 3. Architecture Changes
- KHÔNG có thay đổi pipeline L0→L10. CT-023 là UI-only (L4 Human Gate UX enhancement, KHÔNG bypass per-drug confirm — chỉ cho phép loại bỏ gợi ý sai trước khi confirm).
- `experiment/groq-degallucination` chính thức là permanent reference branch — KHÔNG nằm trong roadmap merge.

## 4. Tasks Created
- (không có task mới — CT-023/026/028/029/030-034 đều đã đóng trong phiên này)

## 5. Pending Items
- `CT-019` 🔴 — A2-VAD debug offline (carry-over, cần audio thật bị lỗi từ CT-016)
- `CT-016` ⏳ — chờ Andy cung cấp audio file mới + ground truth
- `CT-017` ⏳ — GG Drive backup, chờ Andy cung cấp đường dẫn JSON service account key
- `CT-014` ⏳ — FID-VN-013 Voice Calibration, chờ Andy mô tả flow chi tiết
- `PA-013` — Andy revoke `medivoice-bench` Groq API key trên console.groq.com (KHÔNG đụng `medivoice-demo`)
- `VIETMED-FIX-001` — carry-over (HF_TOKEN, ~5 LOC)
- `CT-011` — ORCH-001 FID đầy đủ (carry-over)

## 6. Risks / Confusions
- 🔴 **Drug Recall thực tế (55.6%LB)** vẫn chưa đạt target ≥70% — quyết định CT-028 xác nhận chỉ TRAIN-001 (fine-tune) giải quyết được, không phải patch nhỏ. Đây là ưu tiên cao nhất phiên sau.
- CT-023 đã verify logic qua Node DOM-stub, CHƯA test trực tiếp trên trình duyệt với flow ghi âm thật — nên test khi có dịp trước pilot.

---

## Phiên tiếp theo — thứ tự ưu tiên
1. [TRAIN-001] 🔴 Fine-tune PhoWhisper trên 50-100h audio thật — ưu tiên cao nhất per CT-028, blocked bởi GPU/cloud VM + FID-VN-007 + audio pilot.
2. [CT-019] 🔴 Debug A2-VAD-chunk regression nếu có audio lỗi mới từ CT-016.
3. [PA-013] Andy revoke Groq key `medivoice-bench`.
4. [CT-016/CT-017/CT-014] Chờ Andy cung cấp audio+GT / GG Drive JSON key path / mô tả flow calibration.
5. [VIETMED-FIX-001] Fix `scripts/download_vietmed.py` — remove trust_remote_code + HF_TOKEN (~5 LOC).
6. [PILOT-DN] Andy test demo app tại phòng khám Đà Nẵng — thu audio thật, kiểm tra CT-023 trên trình duyệt thật.
