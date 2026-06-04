# INCIDENT_RESPONSE_PLAN.md | DS-VN-COM-015
# ISO/IEC 42001:2023 Cl.8.5 — Response to AI System Incidents
# NĐ13/2023 Điều 23 — Thông báo vi phạm dữ liệu 72h
# Luật AI 134/2025 — Incident reporting cho high-risk AI
# v1.0 | 2026-06-06 | Owner: Andy Phan

---

## 1. LOẠI SỰ CỐ VÀ MỨC ĐỘ

| Loại | Ví dụ | Mức độ | Response time |
|---|---|---|---|
| **AI-01** | AI output tên thuốc sai, BS approve → BN dùng thuốc sai | CRITICAL | Ngay lập tức |
| **AI-02** | AI nhầm liều lượng (5mg↔50mg), BS không catch | CRITICAL | Ngay lập tức |
| **DATA-01** | Dữ liệu bệnh nhân bị truy cập trái phép | CRITICAL | <1 giờ |
| **DATA-02** | SQLite file bị copy ra ngoài/bị đánh cắp | CRITICAL | <1 giờ |
| **AI-03** | L4 Human Gate bị bypass (bệnh án lưu không có BS approve) | HIGH | <4 giờ |
| **AI-04** | L10 audit log bị modify/xóa | HIGH | <4 giờ |
| **AI-05** | PII scan không hoạt động (CCCD lưu raw) | HIGH | <4 giờ |
| **SYS-01** | App crash liên tục trong lúc BS đang khám | MEDIUM | <24 giờ |
| **SYS-02** | PDF export không ra file | MEDIUM | <24 giờ |
| **DATA-03** | Backup cloud fail (dữ liệu chỉ còn local) | LOW | <72 giờ |

---

## 2. SƠ ĐỒ PHẢN HỒI

```
SỰ CỐ XẢY RA
     │
     ▼
AI hoặc Andy phát hiện → Ghi vào NONCONFORMING.md NGAY
     │
     ├── CRITICAL/HIGH → Andy nhận thông báo trong 1 giờ
     │       │
     │       ├── Dữ liệu? → Data breach protocol (Mục 3)
     │       └── AI error? → AI incident protocol (Mục 4)
     │
     └── MEDIUM/LOW → Claude log + Andy review cuối ngày
```

---

## 3. DATA BREACH PROTOCOL (NĐ13/2023)

**Khi dữ liệu bệnh nhân bị rò rỉ/truy cập trái phép:**

```
BƯỚC 1 — Ngay lập tức (0-1 giờ):
  □ Xác nhận: dữ liệu nào bị ảnh hưởng? Bao nhiêu bệnh nhân?
  □ Cô lập: tắt server nếu cần, ngừng sync cloud
  □ Preserve evidence: không xóa log

BƯỚC 2 — Thông báo Bên A (1-24 giờ):
  □ Gọi điện BS/chủ phòng khám ngay
  □ Email xác nhận: loại dữ liệu, số lượng BN ảnh hưởng
  □ Hành động đã làm để ngăn chặn

BƯỚC 3 — Báo cáo cơ quan (≤ 72 giờ):
  □ Bộ Công an — Cục An ninh mạng và phòng chống tội phạm công nghệ cao
     Website: https://www.bocongan.gov.vn
     Hotline: 113 (cấp cứu) hoặc theo hướng dẫn NĐ13/2023
  □ Nội dung báo cáo:
     - Loại vi phạm
     - Thời điểm phát hiện
     - Số lượng chủ thể dữ liệu bị ảnh hưởng
     - Biện pháp khắc phục đã thực hiện
     - Biện pháp phòng ngừa tiếp theo

BƯỚC 4 — Khắc phục (7-30 ngày):
  □ Root cause analysis
  □ Patch/fix
  □ Update RISK_REGISTER
  □ Thông báo các bệnh nhân bị ảnh hưởng (theo hướng dẫn luật sư)
```

---

## 4. AI INCIDENT PROTOCOL

**Khi AI output sai gây nguy hiểm cho bệnh nhân:**

```
BƯỚC 1 — Ngay lập tức:
  □ BS thông báo ngay cho Andy (SĐT Andy Phan: _______________)
  □ BS ghi rejection reason trong app + ghi tay đơn đúng
  □ Andy log vào NONCONFORMING.md

BƯỚC 2 — Trong 48 giờ:
  □ Reproduce: chạy lại cùng audio → xem AI output
  □ Root cause: ASR sai hay NER sai hay drug_db thiếu?
  □ Immediate fix nếu có thể (drug alias, regex)
  □ Thông báo BS pilot về loại lỗi + cách phòng tránh

BƯỚC 3 — Trong 7 ngày:
  □ Patch + test (phải pass 210+ tests)
  □ Update drug_db.json hoặc NER patterns
  □ Update CONFUSION_PATTERNS.md nếu là pattern mới
  □ Ghi vào NONCONFORMING.md → RESOLVED

BƯỚC 4 — Báo cáo (theo Luật AI 134/2025):
  □ Ghi vào incident log (L10 audit)
  □ Nếu injury → báo cáo theo quy định Luật AI 134
  □ Tham khảo LEGAL-001 (luật sư) về nghĩa vụ báo cáo
```

---

## 5. LIÊN HỆ KHẨN CẤP

| Người | Vai trò | Liên hệ |
|---|---|---|
| Andy Phan | Owner, Data Controller | vietshares.com@gmail.com |
| BS Đà Nẵng Pilot | Clinical contact | *(cập nhật khi có pilot)* |
| Luật sư VN | LEGAL-001 | *(cập nhật sau LEGAL-001)* |
| Cục An ninh mạng | Data breach reporting | Theo NĐ13/2023 |

---

## 6. TRAINING CHO BS PILOT

BS pilot cần biết (15 phút onboarding):

```
1. "Khi nào nhấn REJECT?"
   → Khi AI điền sai BẤT KỲ thông tin nào (tên thuốc, liều, chẩn đoán)
   → Không cần toàn bộ sai — 1 field sai = REJECT

2. "Báo lỗi thế nào?"
   → Nhấn [Từ chối] → điền lý do (ví dụ: "sai tên thuốc Amoxicillin→Ampicillin")
   → App tự ghi vào feedback log

3. "Nếu dữ liệu BN người khác xuất hiện?"
   → DỪNG ngay, gọi Andy: vietshares.com@gmail.com
   → Không tiếp tục dùng app cho đến khi Andy xác nhận

4. "Nếu app crash giữa lúc khám?"
   → Ghi tay bình thường → báo Andy sau buổi khám
   → Dữ liệu đã approve trước đó vẫn được lưu
```

---

*DS-VN-COM-015 | INCIDENT_RESPONSE_PLAN v1.0 | ISO 42001:2023 Cl.8.5 | 2026-06-06*
