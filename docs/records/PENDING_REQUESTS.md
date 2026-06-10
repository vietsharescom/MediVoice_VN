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
| CT-014 | **FID-VN-013 — Voice Calibration (DVP Layer 3)** — Andy muốn ghi mẫu giọng/calibration **TRƯỚC MỖI PHIÊN KHÁM** (không chỉ đăng ký 1 lần). Khác với FID-VN-012 §6 (calibration triggered sau 3-5 sessions, Phase 1). Cần FID mới: scope, UX flow, có bắt buộc mỗi phiên hay optional, ảnh hưởng thời gian xử lý. | 🔴 HIGH | ⏳ PENDING — chờ Andy mô tả chi tiết flow mong muốn | 2026-06-09 |
| CT-015 | **DVP Layer 1 frontend UI** — Backend `/api/doctors` đã có (region/specialty/english_level/speaking_speed), nhưng `index.html` chưa có form đăng ký "Trợ lý AI của BS [Tên]". | 🟡 MEDIUM | ⏳ PENDING | 2026-06-09 |
| CT-016 | **Transcribe accuracy regression (audio mới)** — Andy ghi audio mới, transcript có lỗi nặng ("monroeleague", "viêm gan đại tràng" sai). Không có audio cũ để so sánh trực tiếp — cần Andy lưu lại audio file mới này (đã ở `data/audio/`?) + ground truth để đối chiếu BENCH-002b (baseline: Drug Recall 55.6%, WER DN/SG 16.3%, WER HN 29.3%). Thời gian xử lý >1 phút cũng cần đo lại (có thể do model load lần đầu — bình thường trên CPU). | 🟡 MEDIUM | ⏳ PENDING — cần audio file + ground truth | 2026-06-09 |
| CT-017 | **GG Drive backup tài liệu dev/ISO** — tiếp tục từ GCP service account key Andy gửi (project `valid-dragon-498814-b3`). Cần Andy cung cấp đường dẫn file JSON key đã tải (KHÔNG paste JSON vào chat). Sau đó wire `gcp_service_account` vào `.streamlit/secrets.toml` + viết `scripts/backup_docs.py`. | 🟡 MEDIUM | ⏳ PENDING — chờ JSON key file path | 2026-06-09 |
| CT-018 | **NER fix: Huyết áp digit-form + Nhiệt độ "là"** — `src/core/l1c_ner.py`: (1) thêm `_RE_BP_DIGITS` để bắt "120 trên cao 80"→120/80 (trước đây chỉ bắt word-form); (2) `_RE_NHIET_DO`/`_RE_NHIET_DO_SPLIT` thêm `(?:là\s*)?` để bắt "nhiệt độ là 39 độ c" (trước đây regex fail vì "là" không phải whitespace/colon). 817/817 PASS. | 🟡 MEDIUM | ✅ DONE (2026-06-09) | 2026-06-09 |

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
