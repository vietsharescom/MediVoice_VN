# AI_POLICY.md | DS-VN-CL05-001
# ISO/IEC 42001:2023 Clause 5.2 | ISO_VN v1.0 | v1.0
# MediVoice VN — AI Policy
# Owner: Andy Phan | Maple Leaf Group | 2026-06-03

---

## TUYÊN BỐ CHÍNH SÁCH

Maple Leaf Group cam kết triển khai AI có trách nhiệm, minh bạch, an toàn
trong MediVoice VN. AI được phân loại **High Risk** (y tế, ảnh hưởng sức khỏe).

> **MediVoice VN là "Documentation Assistant" — không phải thiết bị y tế (SaMD).**
> AI tạo bản nháp. Bác sĩ là tác giả và chịu trách nhiệm pháp lý hoàn toàn.

---

## 1. HUMAN AUTHORSHIP — BẤT KHẨU THUYẾT

- AI sinh bản nháp; bác sĩ là tác giả hồ sơ bệnh án
- Không bệnh án nào được lưu khi chưa có bác sĩ review và approve
- App yêu cầu hành động "Phê duyệt & Lưu" rõ ràng — không auto-save

---

## 2. MINH BẠCH TRONG MỌI OUTPUT

Mỗi bệnh án AI tạo phải hiển thị:
- Transcript gốc (lời BS nói)
- Entities được extract và nguồn
- Mã ICD-10-VN và confidence
- Tên thuốc từ drug database

---

## 3. TOÀN VẸN THUẬT NGỮ Y TẾ

- Tên thuốc, chẩn đoán KHÔNG BAO GIỜ được dịch hoặc tự diễn giải lại
- Sai chính tả ASR → flag để BS sửa, không tự sửa tùy tiện
- Tên thuốc thiếu liều lượng → flag cảnh báo

---

## 4. PRIVACY BY DESIGN — NĐ13/2023

- Audio xử lý local; không gửi ra ngoài
- Dữ liệu BN lưu tại VN (SQLite local hoặc VN Cloud)
- Patient ref lưu dưới dạng hash — không lưu raw ID
- Mã hóa Fernet at rest
- Lưu trữ 10 năm tối thiểu (TT32/2023)

---

## 5. TUÂN THỦ PHÁP LÝ VN

| Luật | Yêu cầu | Cách thực thi |
|---|---|---|
| NĐ13/2023 | Data tại VN | SQLite local + VN Cloud |
| TT32/2023 | Mẫu bệnh án chuẩn | Mẫu 15/BV-01 |
| Luật KCB 2023 Điều 62 | BS ký | L4 Human Gate |
| Luật KCB 2023 Điều 80 | Không hoa hồng | Referral tracking (không ghi tiền) |
| TT13/2025 | EMR + FHIR (31/12/2026) | Phase 2 roadmap |
| Luật AI 134/2025 | Human oversight + audit | L4 + L10 |

---

## 6. AI PROACTIVE INTELLIGENCE (P6)

AI phải chủ động:
- Nghiên cứu và đề xuất cải tiến kỹ thuật
- So sánh với sản phẩm cạnh tranh
- Scan công nghệ mới (ASR, NLP, datasets)
- Không cần đợi được hỏi

AI không được:
- Tự deploy/commit/push khi chưa có approval
- Thay đổi frozen layers mà không có FID

---

## 7. PHÂN LOẠI — KHÔNG PHẢI SaMD

Theo TT46/2017/TT-BYT:
- SaMD = phần mềm tham gia vào quyết định chẩn đoán/điều trị
- MediVoice VN = transcription + điền mẫu → **KHÔNG phải SaMD**
- Không cần đăng ký BYT như thiết bị y tế

---

## 8. INCIDENT PROCESS

1. Log ngay lập tức (L10)
2. Thông báo Andy trong 1 giờ
3. Root cause trong 48 giờ
4. Corrective action trong 7 ngày
5. Vi phạm NĐ13/2023: thông báo Bộ Công an

---

## 9. TRÁCH NHIỆM

| Vai trò | Trách nhiệm |
|---|---|
| Andy Phan (Owner) | AI policy, system integrity, legal compliance |
| BS sử dụng | Clinical authorship, patient consent, record accuracy |
| Maple Leaf Group | Data privacy, system maintenance, incident response |
| Bệnh nhân | Quyền xem và yêu cầu chỉnh sửa hồ sơ |

---

*DS-VN-CL05-001 | AI_POLICY v1.0 | ISO/IEC 42001:2023 Clause 5.2 | 2026-06-03*
