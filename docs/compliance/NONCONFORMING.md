# NONCONFORMING.md | DS-VN-COM-003
# ISO 9001:2015 Clause 8.7 — Control of Nonconforming Outputs
# ISO/IEC 42001:2023 Clause 10.2 — Nonconformity and Corrective Action
# MediVoice VN — Quy trình Xử lý Kết quả Không Đạt
# v1.0 | 2026-06-04 | Owner: Andy Phan

---

## 1. ĐỊNH NGHĨA — Nonconforming Output

Kết quả không đạt trong MediVoice VN là bất kỳ output nào vi phạm:

| Loại | Ví dụ cụ thể | Mức độ |
|---|---|---|
| **NC-SAFETY** | Tên thuốc/liều sai trong bản nháp | CRITICAL |
| **NC-PRIVACY** | PII bệnh nhân xuất hiện trong log/display không mã hóa | CRITICAL |
| **NC-LEGAL** | Record được lưu mà không có L4 BS approve | CRITICAL |
| **NC-ACCURACY** | CEER > 10% (lỗi entity lâm sàng) | HIGH |
| **NC-SYSTEM** | Tests fail trước khi commit | HIGH |
| **NC-DATA** | Audit log chain bị break (tamper detected) | HIGH |
| **NC-UI** | Disclaimer "AI tạo nháp" không hiển thị | MEDIUM |

---

## 2. QUY TRÌNH XỬ LÝ

### Bước 1 — Phát hiện
Các nguồn phát hiện:
- BS báo lỗi qua `/api/feedback` (→ xem FEEDBACK_PROCESS.md)
- Automated tests (pytest 100% trước mỗi commit)
- L10 Audit log chain verification
- Andy review định kỳ (Management Review)

### Bước 2 — Ngăn chặn ngay (Containment)

| Mức độ | Hành động ngay lập tức |
|---|---|
| CRITICAL | Stop deployment · Thông báo BS affected · Khóa record liên quan |
| HIGH | Log vào L10 · Flag trong BACKLOG · Không deploy thêm |
| MEDIUM | Log · Schedule fix trong sprint tiếp |

### Bước 3 — Phân tích nguyên nhân (Root Cause)
- CRITICAL: trong 48 giờ
- HIGH: trong 7 ngày
- MEDIUM: trong sprint tiếp

### Bước 4 — Corrective Action
- Viết fix + test coverage mới
- 100% tests PASS trước khi deploy lại
- Cập nhật RISK_REGISTER nếu rủi ro mới phát sinh

### Bước 5 — Xác nhận hiệu quả (Effectiveness check)
- Chạy lại scenario gây ra NC
- Xác nhận KPI liên quan cải thiện
- Ghi vào MANAGEMENT_REVIEW kỳ tiếp

---

## 3. LOG NONCONFORMITIES

| ID | Ngày | Loại | Mô tả | Trạng thái |
|---|---|---|---|---|
| *(chưa có — Phase 0 chưa pilot)* | | | | |

---

## 4. NGƯỠNG ESCALATION

Nếu trong 1 tháng có:
- ≥ 1 NC-CRITICAL → Andy review toàn bộ pipeline
- ≥ 3 NC-HIGH → Tạm dừng onboard BS mới
- CEER > 10% liên tục 7 ngày → Kích hoạt TRAIN-001

---

*DS-VN-COM-003 | NONCONFORMING v1.0 | ISO 9001:2015 Cl.8.7 | 2026-06-04*
