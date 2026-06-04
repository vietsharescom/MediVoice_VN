# FEEDBACK_PROCESS.md | DS-VN-COM-006
# ISO/IEC 42001:2023 Annex A.6.2 — Feedback Mechanisms
# MediVoice VN — Quy trình Thu thập Phản hồi BS → AI
# v1.0 | 2026-06-04 | Owner: Andy Phan

---

## 1. MỤC ĐÍCH

BS là người duy nhất biết output AI có đúng lâm sàng không.
Kênh phản hồi là cơ chế bắt buộc để:
- Phát hiện lỗi AI (drug error, NER sai, ICD sai)
- Cải thiện drug_db.json và NER patterns
- Phát hiện nonconformities (→ NONCONFORMING.md)
- Thu thập data cho TRAIN-001 (fine-tune Phase 1)

---

## 2. CÁC KÊNH PHẢN HỒI

### Kênh 1 — In-app feedback (chính)
**Endpoint:** `POST /api/feedback`
**Khi nào:** Sau mỗi lần BS approve hoặc reject record
**Nội dung:**

```json
{
  "record_id": "uuid",
  "doctor_cchn": "CCHN-xxx",
  "feedback_type": "drug_error | ner_error | icd_error | latency | other",
  "field_affected": "don_thuoc[0].inn | kham_benh.ma_icd10 | ...",
  "correct_value": "giá trị đúng theo BS",
  "severity": "critical | high | medium | low",
  "comment": "ghi chú thêm"
}
```

### Kênh 2 — Reject + reason (tự động)
Khi BS reject record ở L4, `rejection_reason` tự động ghi vào L10 audit log.
Đây là feedback ngầm về chất lượng output.

### Kênh 3 — Pilot observation (Andy trực tiếp)
Trong pilot Đà Nẵng, Andy quan sát trực tiếp và ghi chép.

---

## 3. QUY TRÌNH XỬ LÝ FEEDBACK

```
BS gửi feedback
    ↓
Lưu vào SQLite (bảng feedback)
    ↓
Claude đọc trong Management Review hàng quý
    ↓
Phân loại:
  drug_error → cập nhật drug_db.json (aliases)
  ner_error  → cải thiện regex trong l1c_ner.py
  icd_error  → review icd10vn.json mapping
  critical   → kích hoạt NONCONFORMING.md ngay
    ↓
Đóng feedback: ghi "resolved" + commit
```

---

## 4. SLA XỬ LÝ

| Mức độ | Thời gian phản hồi | Thời gian fix |
|---|---|---|
| critical | 24 giờ | 48 giờ |
| high | 3 ngày | 7 ngày |
| medium | 7 ngày | Sprint tiếp |
| low | Quarterly review | Khi có bandwidth |

---

## 5. METRICS

| KPI | Target |
|---|---|
| Feedback response rate | 100% critical + high |
| Critical drug errors resolved | < 48 giờ |
| Monthly unique feedbacks (pilot) | ≥ 5 per active BS |

---

*DS-VN-COM-006 | FEEDBACK_PROCESS v1.0 | ISO/IEC 42001:2023 Annex A.6.2 | 2026-06-04*
