# LEGAL_BRIEF_001.md | DS-VN-COM-020
# Tóm tắt Pháp lý Gửi Luật sư — MediVoice VN
# LEGAL-001 — Healthtech + Dữ liệu + AI
# v1.0 | 2026-06-09 | Soạn bởi: Andy Phan / Maple Leaf Group

---

## THƯ YÊU CẦU TƯ VẤN PHÁP LÝ

**Kính gửi:** Luật sư / Văn phòng Luật _______________________________

**Từ:** Andy Phan (Viet) — Maple Leaf Group
**Email:** vietshares.com@gmail.com
**Ngày:** ___/___/______

---

## 1. GIỚI THIỆU DỰ ÁN

**Tên sản phẩm:** MediVoice VN
**Loại:** Phần mềm hỗ trợ ghi chép y tế có AI ("Documentation Assistant")
**Giai đoạn:** Pilot — 2–3 phòng mạch tư nhân tại Đà Nẵng và TP.HCM
**Mô hình vận hành:**

> Bác sĩ nói trong lúc khám → AI nhận dạng giọng nói (offline, không internet) →
> Hệ thống điền vào mẫu bệnh án nháp → **Bác sĩ đọc, sửa và phê duyệt** →
> Xuất PDF Mẫu 15/BV-01 (TT32/2023) → Lưu tại máy tính phòng khám.

**Điểm quan trọng:**
- AI KHÔNG tự ra chẩn đoán — chỉ ghi lại lời bác sĩ
- Dữ liệu lưu 100% tại máy tính phòng khám (on-premise), không lên cloud nước ngoài
- Bác sĩ ký/phê duyệt mọi bệnh án trước khi lưu (Luật KCB 2023 Điều 62)
- Không phải SaMD (Software as Medical Device) theo định nghĩa TT46/2017

---

## 2. PHẠM VI TƯ VẤN CẦN THIẾT

### 2.1 — Ưu tiên CAO (cần trước khi ký hợp đồng pilot thương mại)

**A. Review Hợp đồng Xử lý Dữ liệu (DPA)**
- File: `docs/compliance/DPA_TEMPLATE.md`
- Căn cứ pháp lý: NĐ13/2023/NĐ-CP Điều 38 — bắt buộc ký trước khi phòng khám dùng app
- Cần luật sư xác nhận: nội dung đủ điều kiện pháp lý, điều khoản xử lý dữ liệu sức khỏe đúng

**B. Tư vấn phân loại sản phẩm — Có phải SaMD không?**
- TT46/2017/TT-BYT: Nếu là thiết bị y tế phần mềm → cần đăng ký BYT (chi phí/thời gian cao)
- Lập luận hiện tại: MediVoice VN = "documentation tool", không phân tích ảnh/sinh hiệu → KHÔNG phải SaMD
- Cần luật sư xác nhận hoặc tư vấn risk nếu BYT có diễn giải khác

**C. Tư vấn Hoa hồng / Referral (Luật KCB 2023 Điều 80)**
- App có tính năng tracking giới thiệu (không lưu tiền/%) — cần xác nhận không vi phạm Điều 80
- Phạm vi: M5 Referral module — ghi nhận "từ đối tác nào" nhưng không xử lý thanh toán hoa hồng

### 2.2 — Ưu tiên TRUNG BÌNH (cần trong 3 tháng)

**D. Cấu trúc pháp lý Maple Leaf Group**
- Hiện tại: cá nhân Andy Phan vận hành
- Cần tư vấn: nên thành lập công ty (TNHH/CP) trước khi ký hợp đồng thương mại?
- Rủi ro cá nhân vs. rủi ro pháp nhân

**E. Điều khoản miễn trừ trách nhiệm trong hợp đồng BS**
- Nếu bác sĩ phê duyệt thông tin sai → ai chịu trách nhiệm?
- Cần câu ngôn ngữ pháp lý mạnh trong hợp đồng sử dụng

**F. Tuân thủ Luật AI 134/2025/QH15**
- Hiệu lực từ 01/07/2025 — conformity assessment deadline 09/2027
- Cần tư vấn: MediVoice VN thuộc nhóm rủi ro nào (cao/trung bình/thấp)?
- Audit trail requirements (đã có L10 hash chain — cần xác nhận đủ chưa)

### 2.3 — Thông tin để biết (không cần tư vấn ngay)

- TT32/2023/TT-BYT: Mẫu bệnh án đã implement đúng (Mẫu 15/BV-01)
- TT13/2025/TT-BYT: Chữ ký số + EMR — deadline 31/12/2026, đang plan Phase 2
- NĐ13/2023: Dữ liệu on-premise, không cloud nước ngoài — đã đảm bảo

---

## 3. TÀI LIỆU ĐỂ LUẬT SƯ REVIEW

| File | Nội dung | Ưu tiên |
|---|---|---|
| `docs/compliance/DPA_TEMPLATE.md` | Hợp đồng xử lý dữ liệu BN | 🔴 CAO |
| `docs/compliance/AI_POLICY.md` | Chính sách AI — ISO 42001 Cl.5.2 | 🔴 CAO |
| `docs/compliance/BS_ONBOARDING_CHECKLIST.md` | Checklist onboarding + cam kết BS | 🟡 TRUNG BÌNH |
| `docs/compliance/SCOPE.md` | Phạm vi hệ thống — ISO 9001/42001 | 🟡 TRUNG BÌNH |
| `docs/compliance/RISK_REGISTER.md` | Đăng ký rủi ro pháp lý/kỹ thuật | 🟡 TRUNG BÌNH |
| `docs/compliance/IMPACT_ASSESSMENT.md` | Đánh giá tác động AI | 🟡 TRUNG BÌNH |

---

## 4. CÂU HỎI CỤ THỂ CẦN TRẢ LỜI

1. **DPA có đủ pháp lý để ký với BS pilot không?** Cần bổ sung gì?
2. **MediVoice VN có phải đăng ký là Thiết bị Y tế Phần mềm (TT46/2017) không?**
3. **Điều 80 Luật KCB 2023 (cấm hoa hồng):** Referral tracking có vi phạm không?
4. **Khi BS approve thông tin sai:** Trách nhiệm pháp lý phân chia thế nào giữa BS và Maple Leaf Group?
5. **Luật AI 134/2025:** Nhóm rủi ro nào? Cần làm gì để đáp ứng deadline 09/2027?

---

## 5. PHẠM VI VÀ PHÍ TƯ VẤN

| Hạng mục | Ước tính thời gian |
|---|---|
| Review DPA + tư vấn chỉnh sửa | 2–4 giờ |
| Tư vấn phân loại SaMD (TT46/2017) | 2–3 giờ |
| Tư vấn Luật KCB Điều 80 (referral) | 1–2 giờ |
| Tư vấn cấu trúc pháp lý Maple Leaf | 1–2 giờ |
| Ý kiến pháp lý bằng văn bản (Legal Opinion) | 3–5 giờ |
| **Tổng ước tính** | **9–16 giờ** |

**Phí tư vấn:** _______________________________ VND/giờ
**Tổng phí dự kiến:** _______________________________
**Phương thức thanh toán:** _______________________________
**Thời hạn hoàn thành:** _______________________________

---

## 6. THÔNG TIN BỔ SUNG VỀ KỸ THUẬT

*(Để luật sư hiểu bối cảnh — không cần đọc kỹ)*

| Yếu tố kỹ thuật | Chi tiết |
|---|---|
| AI model | PhoWhisper-medium (Đại học VinAI) — chạy offline |
| Lưu trữ | SQLite + mã hóa Fernet (AES-128) — tại máy phòng khám |
| Audio | Xóa ngay sau khi chuyển văn bản (Privacy by Design) |
| Audit log | Hash chain SHA-256, append-only — không sửa được |
| Network | Không cần internet cho tính năng cốt lõi |
| Cloud | Không bắt buộc. Nếu bật: chỉ VNG/FPT/VNPT |
| Human oversight | Bác sĩ PHẢI phê duyệt mọi bệnh án (không thể bỏ qua) |

---

## 7. THỎA THUẬN THAM GIA TƯ VẤN

*(Ký để xác nhận nhận brief và đồng ý phạm vi)*

**Luật sư / Văn phòng Luật:**

Họ tên luật sư: _______________________________
Số thẻ luật sư: _______________________________
Văn phòng: _______________________________
Địa chỉ: _______________________________
Email: _______________________________
SĐT: _______________________________

Tôi xác nhận đã nhận tài liệu này và đồng ý tư vấn theo phạm vi tại Mục 2 và Mục 5.

Chữ ký: _______________________________ Ngày: ___/___/______

---

**Maple Leaf Group — Bên yêu cầu tư vấn:**

Andy Phan (Viet)
Email: vietshares.com@gmail.com
Chữ ký: _______________________________ Ngày: ___/___/______

---

*DS-VN-COM-020 | LEGAL_BRIEF_001 v1.0 | Healthtech + Data + AI | 2026-06-09*
*Tài liệu này KHÔNG phải ý kiến pháp lý. Chỉ là brief nội bộ gửi luật sư.*
