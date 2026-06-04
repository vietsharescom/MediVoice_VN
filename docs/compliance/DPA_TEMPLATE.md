# DPA_TEMPLATE.md | DS-VN-COM-014
# Data Processing Agreement — Hợp đồng Xử lý Dữ liệu
# NĐ13/2023 Điều 38 — Bắt buộc ký trước khi phòng khám dùng app
# v1.0 | 2026-06-06 | Owner: Andy Phan | Maple Leaf Group
# ⚠️ CẦN LEGAL-001 (luật sư VN) review trước khi ký chính thức

---

## HỢP ĐỒNG XỬ LÝ DỮ LIỆU CÁ NHÂN
### (Theo Nghị định 13/2023/NĐ-CP về Bảo vệ Dữ liệu Cá nhân)

**Ký ngày:** ___/___/______

**Giữa:**

**BÊN A — Bên Kiểm soát Dữ liệu (Data Controller):**
Tên cơ sở KCB: _______________________________
Địa chỉ: _______________________________
Mã GPHN/đăng ký BYT: _______________________________
Đại diện: BS _______________________________  CCHN số: _______________
SĐT: _______________  Email: _______________

**BÊN B — Bên Xử lý Dữ liệu (Data Processor):**
Công ty: Maple Leaf Group
Đại diện: Andy Phan (Viet)
Sản phẩm: MediVoice VN
Địa chỉ: _______________________________
Email: vietshares.com@gmail.com

---

## ĐIỀU 1 — PHẠM VI XỬ LÝ

1.1 Bên B xử lý dữ liệu cá nhân của bệnh nhân Bên A CHỈ cho mục đích:
    - Nhận dạng giọng nói bác sĩ → tạo bản nháp bệnh án
    - Hỗ trợ ghi chép hồ sơ bệnh án theo TT32/2023
    - KHÔNG dùng cho mục đích khác, KHÔNG chia sẻ bên thứ 3

1.2 Dữ liệu được xử lý bao gồm:
    - Họ tên, ngày sinh, giới tính bệnh nhân
    - Địa chỉ, số điện thoại (nếu Bên A cung cấp)
    - CCCD/CMND, số thẻ BHYT (tùy chọn)
    - Âm thanh giọng nói bác sĩ (XÓA NGAY sau khi xử lý)
    - Nội dung bệnh án (chẩn đoán, đơn thuốc, sinh hiệu)

---

## ĐIỀU 2 — BIỆN PHÁP BẢO MẬT

2.1 Bên B cam kết:
    - Mã hoá dữ liệu tại chỗ bằng Fernet (AES-128-CBC)
    - Lưu trữ 100% tại máy tính của Bên A (on-premise)
    - KHÔNG upload dữ liệu lên cloud nước ngoài (tuân thủ NĐ13/2023)
    - Cloud backup (nếu bật): chỉ sử dụng VNG/FPT/VNPT (VN region)
    - Âm thanh giọng nói: xóa khỏi bộ nhớ ngay sau khi chuyển văn bản
    - Không có nhân viên Maple Leaf truy cập dữ liệu bệnh nhân của Bên A

2.2 Bên A chịu trách nhiệm:
    - Bảo mật mật khẩu đăng nhập vào MediVoice VN
    - Bảo mật máy tính/thiết bị cài đặt phần mềm
    - Không để người không có thẩm quyền truy cập hệ thống

---

## ĐIỀU 3 — THỜI HẠN LƯU TRỮ

3.1 Hồ sơ bệnh án điện tử: lưu tối thiểu **10 năm** (TT32/2023 Điều 59)
3.2 Trường hợp bệnh nhân tử vong: lưu tối thiểu **30 năm**
3.3 Khi chấm dứt hợp đồng: Bên A nhận toàn bộ dữ liệu trước khi xóa

---

## ĐIỀU 4 — QUYỀN CỦA CHỦ THỂ DỮ LIỆU (BỆNH NHÂN)

Bên A có trách nhiệm thực hiện các quyền của bệnh nhân:
- Quyền truy cập: bệnh nhân được xem hồ sơ của mình
- Quyền chỉnh sửa: thông qua bác sĩ điều trị
- Quyền xóa: theo quy định TT32/2023 (giới hạn bởi thời hạn lưu bắt buộc)
- Quyền phản đối xử lý: bệnh nhân có thể từ chối dùng AI

---

## ĐIỀU 5 — VI PHẠM DỮ LIỆU

5.1 Bên B thông báo Bên A **trong 24 giờ** nếu phát hiện vi phạm
5.2 Bên A thông báo Bộ Công an (Cục An ninh mạng) **trong 72 giờ** (NĐ13/2023 Điều 23)
5.3 Kênh thông báo vi phạm: vietshares.com@gmail.com

---

## ĐIỀU 6 — PHỤ TRÁCH DỮ LIỆU (DPO)

Bên B không bắt buộc có DPO (tổ chức nhỏ, Phase 0).
Đầu mối liên hệ bảo vệ dữ liệu: Andy Phan — vietshares.com@gmail.com

---

## ĐIỀU 7 — THỜI HẠN VÀ CHẤM DỨT

7.1 Hiệu lực: từ ngày ký đến khi chấm dứt sử dụng MediVoice VN
7.2 Khi chấm dứt:
    - Bên B xuất toàn bộ dữ liệu cho Bên A (format SQLite hoặc CSV)
    - Bên A nhận xác nhận xóa dữ liệu khỏi server Bên B (nếu có cloud)
    - Thông báo trước **30 ngày**

---

## CHỮ KÝ

**Bên A — Cơ sở KCB:**                    **Bên B — Maple Leaf Group:**

Họ tên: ___________________               Andy Phan (Viet)
Chức vụ: ___________________              Đại diện Maple Leaf Group
Ngày: ___/___/______                       Ngày: ___/___/______
Chữ ký: ___________________               Chữ ký: ___________________

---

⚠️ **LƯU Ý PHÁP LÝ:**
Template này chưa được luật sư VN review (LEGAL-001 pending).
Sử dụng nội bộ / pilot ký nháp. Cần review trước khi ký thương mại chính thức.

*DS-VN-COM-014 | DPA_TEMPLATE v1.0 | NĐ13/2023 Điều 38 | 2026-06-06*
