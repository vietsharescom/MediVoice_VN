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
| PA-007 | **Corpus ChatGPT** — Copy toàn bộ nội dung `docs/dev/CHATGPT_CORPUS_PROMPT.md` → paste vào ChatGPT/Grok → nhận 41 scripts → BS đọc và xác nhận → gửi lại Claude để update `docs/dev/CLINICAL_TEST_CORPUS_VN.md` v3.0 | 🟡 MEDIUM | PENDING | 2026-06-08 | 2 |
| PA-008 | **Semi-synthetic ghi âm** — Tìm 4 người: 1 HN + 1 SG + 1 CT + 1 Canada. In `docs/dev/RECORDING_SCRIPTS_4BS.md` (4 sections riêng). Mỗi người ghi 5 scripts × 2 takes. Upload vào `data/audio/corpus/semi_synthetic/`. Xem kế hoạch: `docs/dev/SEMI_SYNTHETIC_DATA_PLAN.md` | 🔴 HIGH | PENDING | 2026-06-09 | 2 |
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

---

## THIRD_PARTY — Cần hỏi AI khác

| ID | Mô tả | Priority | Status | Created |
|---|---|---|---|---|
| TP-001 | Không có consultation pending | - | - | - |

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
