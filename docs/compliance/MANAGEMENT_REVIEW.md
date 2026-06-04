# MANAGEMENT_REVIEW.md | DS-VN-COM-005
# ISO 9001:2015 Clause 9.3 — Management Review
# ISO/IEC 42001:2023 Clause 9.3 — Management Review
# MediVoice VN — Xem xét của Lãnh đạo
# v1.0 | 2026-06-04 | Owner: Andy Phan

---

## 1. TẦN SUẤT VÀ HÌNH THỨC

| Loại | Tần suất | Người thực hiện | Ghi chép |
|---|---|---|---|
| **Review định kỳ** | Hàng quý (Q) | Andy Phan | Cập nhật section này |
| **Review khẩn cấp** | Sau NC-CRITICAL | Andy Phan | Tạo record DS-VN-MR-YYYYMMDD |
| **Review milestone** | Trước mỗi phase launch | Andy Phan | Tạo record DS-VN-MR-YYYYMMDD |

---

## 2. NỘI DUNG XEM XÉT (Input)

Theo ISO 9001:2015 Cl.9.3.2, mỗi lần review phải xem xét:

| # | Hạng mục | Nguồn dữ liệu |
|---|---|---|
| 1 | Kết quả audit nội bộ | docs/archive/ (khi có audit) |
| 2 | Feedback khách hàng (BS) | /api/feedback log |
| 3 | KPI performance | docs/dev/KPI_METRICS.md + dữ liệu thực tế |
| 4 | Nonconformities + corrective actions | NONCONFORMING.md |
| 5 | Rủi ro và cơ hội | RISK_REGISTER.md |
| 6 | Thay đổi môi trường bên ngoài (luật, cạnh tranh) | Andy cập nhật thủ công |
| 7 | Hiệu quả các hành động từ review trước | Review trước |

---

## 3. OUTPUT XEM XÉT

Sau mỗi review phải quyết định về:
- Cơ hội cải tiến → thêm vào BACKLOG.md
- Thay đổi QMS/AIMS nếu cần → cập nhật CLAUDE.md
- Nhu cầu nguồn lực (thời gian, tiền) → ghi vào BACKLOG

---

## 4. LỊCH SỬ REVIEW

### Q1 2026 — Review Trước Pilot (dự kiến)
**Ngày:** 2026-07-01 (ước tính)
**Trạng thái:** ⏳ Chưa thực hiện — chờ pilot data

---

### REVIEW 0 — Pre-Launch Baseline (2026-06-04)
**Người review:** Andy Phan
**Phạm vi:** Kiểm tra trạng thái hệ thống trước pilot

| Hạng mục | Kết quả | Quyết định |
|---|---|---|
| Tests | 61/61 PASS | ✅ Tiếp tục |
| Pipeline L0→L10 | Implemented | ✅ Sẵn sàng pilot |
| ISO compliance gaps | 6 items → đã tạo đủ docs hôm nay | ✅ Đóng gap |
| BENCH-001 | Chờ audio | 🔴 Blocker trước pilot |
| Legal review | Chờ luật sư VN | 🔴 Blocker trước launch |
| KPI actuals | Chưa có data thực | ⏳ Sau pilot |

**Quyết định từ review này:**
1. Tạo 6 compliance docs còn thiếu → DONE hôm nay
2. BENCH-001 là blocker cứng trước khi mời BS pilot
3. LEGAL-001 là blocker trước khi charge tiền

---

## 5. TEMPLATE CHO REVIEW TIẾP THEO

```markdown
### Review Q{N} — {YYYY-MM-DD}
**Người review:** Andy Phan
**Dữ liệu kỳ:** {từ} → {đến}

| KPI | Target | Actual | Trend |
|---|---|---|---|
| CEER | < 5% | | |
| WER | < 30% | | |
| BS approve rate | > 85% | | |
| Paying users | ≥ 5 | | |

| Nonconformity | Đã đóng? |
|---|---|
| | |

**Quyết định:**
1. ...
```

---

*DS-VN-COM-005 | MANAGEMENT_REVIEW v1.0 | ISO 9001:2015 Cl.9.3 | 2026-06-04*
