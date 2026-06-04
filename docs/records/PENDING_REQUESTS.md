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
| PA-001 | **Record 30-50 audio consultations tại phòng khám Đà Nẵng** (BENCH-002). Thiết bị: điện thoại đặt gần BS. BS viết ground truth sau mỗi ca (drug name, dose, diagnosis). Kết quả xác định CEER thật trước pilot. | 🔴 HIGH | PENDING | 2026-06-06 | 1 |
| PA-002 | **Tìm luật sư VN** (LEGAL-001) chuyên về healthtech + data + AI. Cần review DPA template trước khi ký với phòng khám. Budget: 10-20M VND. | 🔴 HIGH | PENDING | 2026-06-06 | 1 |
| PA-003 | **Review và ký DPA template** với BS pilot Đà Nẵng trước ngày đầu tiên họ dùng app (docs/compliance/DPA_TEMPLATE.md). | 🔴 HIGH | PENDING | 2026-06-06 | 1 |
| PA-004 | **Review và ký BS Onboarding Checklist** với mỗi BS pilot (docs/compliance/BS_ONBOARDING_CHECKLIST.md). | 🟡 MEDIUM | PENDING | 2026-06-06 | 1 |
| PA-005 | **Approve FID-VN-004** khi Claude viết xong (VN-ROUTER-001 L6 branch design). Cần Andy approve trước khi implement. | 🔴 HIGH | PENDING | 2026-06-06 | 1 |

---

## CLAUDE_TODO — Claude có task chưa hoàn thành

| ID | Mô tả | Priority | Status | Created |
|---|---|---|---|---|
| CT-001 | Viết FID-VN-004 (Feature Intent Document cho VN-ROUTER-001) | 🔴 HIGH | PENDING | 2026-06-06 |
| CT-002 | Implement VN-ROUTER-001 sau khi FID-VN-004 được Andy approve | 🔴 HIGH | PENDING | 2026-06-06 |
| CT-003 | Viết tests GAP-002 (PII scan unit tests) | 🔴 HIGH | ✅ DONE | 2026-06-06 |
| CT-004 | Viết tests GAP-005 (API integration tests) | 🔴 HIGH | ✅ DONE | 2026-06-06 |
| CT-005 | Build DEPLOY-001 (Windows installer) sau VN-ROUTER-001 | 🟡 MEDIUM | PENDING | 2026-06-06 |
| CT-006 | Update drug_db.json với 30 cặp drug interactions (DRUG-INTERACT-001 minimal) | 🟢 LOW | PENDING | 2026-06-06 |

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
