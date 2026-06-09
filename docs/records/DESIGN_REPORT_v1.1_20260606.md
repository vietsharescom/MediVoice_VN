# MEDIVOICE VN — BÁO CÁO THIẾT KẾ HỆ THỐNG
# Design Report | DS-VN-REC-20260606-001
# Version: v1.1 | Ngày: 2026-06-06
# Owner: Andy Phan — Maple Leaf Group
# Trạng thái: FINAL — Đã review và xác nhận
# ISO/IEC 42001:2023 | ISO 9001:2015 | TT32/2023 | NĐ13/2023

---

## MỤC LỤC

1. [Tóm tắt điều hành](#1-tóm-tắt-điều-hành)
2. [Tầm nhìn & Định vị sản phẩm](#2-tầm-nhìn--định-vị-sản-phẩm)
3. [Thị trường & Đối tượng khách hàng](#3-thị-trường--đối-tượng-khách-hàng)
4. [Sản phẩm: 3 Gói × 9 Modules](#4-sản-phẩm-3-gói--9-modules)
5. [Người dùng & Vai trò](#5-người-dùng--vai-trò)
6. [Màn hình & Chế độ vận hành](#6-màn-hình--chế-độ-vận-hành)
7. [Hành trình bệnh nhân — 7 giai đoạn](#7-hành-trình-bệnh-nhân--7-giai-đoạn)
8. [Hệ thống quản lý hàng chờ (Queue)](#8-hệ-thống-quản-lý-hàng-chờ-queue)
9. [Hệ thống book lịch & nhắc hẹn (M2)](#9-hệ-thống-book-lịch--nhắc-hẹn-m2)
10. [Hệ thống đối tác & Referral (M5)](#10-hệ-thống-đối-tác--referral-m5)
11. [Chăm sóc sau khám — After-care CRM (M6)](#11-chăm-sóc-sau-khám--after-care-crm-m6)
12. [Quản lý bệnh nhân (M1)](#12-quản-lý-bệnh-nhân-m1)
13. [Thu chi & Báo cáo (M3)](#13-thu-chi--báo-cáo-m3)
14. [Kết quả bên thứ 3 (M4)](#14-kết-quả-bên-thứ-3-m4)
15. [AI Pipeline kỹ thuật (L0→L10)](#15-ai-pipeline-kỹ-thuật-l0l10)
16. [Tích hợp kênh liên lạc (M6)](#16-tích-hợp-kênh-liên-lạc-m6)
17. [Dữ liệu, lưu trữ & Tuân thủ pháp luật](#17-dữ-liệu-lưu-trữ--tuân-thủ-pháp-luật)
18. [Kiến trúc tích hợp & Thiết bị](#18-kiến-trúc-tích-hợp--thiết-bị)
19. [Lộ trình triển khai — 4 Phase](#19-lộ-trình-triển-khai--4-phase)
20. [So sánh tính năng theo gói](#20-so-sánh-tính-năng-theo-gói)
21. [Phụ lục: Thuật ngữ & Pháp lý](#21-phụ-lục-thuật-ngữ--pháp-lý)

---

## 1. TÓM TẮT ĐIỀU HÀNH

### Dành cho ai: Tất cả — Ban lãnh đạo, Kinh doanh, Kỹ thuật, Đối tác

**MediVoice VN là gì?**

MediVoice VN là phần mềm trợ lý ghi chép hồ sơ bệnh án bằng giọng nói, dành riêng cho phòng mạch tư nhân Việt Nam. Bác sĩ nói chuyện bình thường trong khi khám — hệ thống tự động điền vào biểu mẫu bệnh án chuẩn theo quy định Bộ Y tế (Mẫu 15/BV-01, TT32/2023). Bác sĩ đọc lại, chỉnh sửa nếu cần, rồi phê duyệt — toàn bộ quy trình từ 1-2 phút thay vì 5-10 phút ghi tay.

**Vấn đề giải quyết:**
- Bác sĩ mất 5–10 giờ/ngày chỉ để ghi chép hồ sơ
- Không có sản phẩm nào tại VN tự động hoá "bác sĩ nói → bệnh án điện tử chuẩn TT32"
- Deadline TT13/2025: 37,000+ phòng khám tư phải có EMR trước 31/12/2026

**Giá trị cốt lõi:**
- Tiết kiệm 3–8 giờ ghi chép/ngày
- 100% tuân thủ TT32/2023, NĐ13/2023, TT13/2025
- Chạy hoàn toàn offline — không phụ thuộc internet
- Dữ liệu lưu tại VN — đúng luật

**Không phải:** Hệ thống chẩn đoán. AI chỉ ghi lại những gì bác sĩ nói — bác sĩ chịu trách nhiệm hoàn toàn.

**Thị trường Phase 0:** 15,000–20,000 phòng mạch tư lâm sàng đã đăng ký BYT
**Pilot:** Phòng khám Đà Nẵng (Andy) + Phòng mạch Sài Gòn (BS partner)
**Mục tiêu Phase 0:** 5 bác sĩ trả tiền

---

## 2. TẦM NHÌN & ĐỊNH VỊ SẢN PHẨM

### Dành cho ai: Tất cả

```
TẦM NHÌN:
"Bác sĩ nói — bệnh án tự viết.
 Phòng mạch tư hiện đại hoá trong 30 phút."

ĐỊNH VỊ: Documentation Assistant
  AI nghe bác sĩ nói → map vào đúng form đúng field
  → Bác sĩ review + phê duyệt (bắt buộc theo luật)
  → Xuất PDF bệnh án chuẩn

TUYÊN BỐ QUAN TRỌNG:
  - KHÔNG phải công cụ chẩn đoán
  - KHÔNG phải Thiết bị Y tế (SaMD)
  - AI chỉ tạo bản nháp — Bác sĩ chịu trách nhiệm hoàn toàn
  - Mọi bệnh án đều phải có chữ ký bác sĩ (Luật KCB 2023 Điều 62)
```

### So sánh với đối thủ

| Đối thủ | Điểm yếu → Lợi thế MediVoice VN |
|---|---|
| BravoSoft | Không có AI voice, UI cũ, không TT32 mới |
| VEM.AI | Cloud nước ngoài → vi phạm NĐ13/2023 |
| Dr.AI (Đài Loan) | $149/tháng, tiếng Anh, không offline |
| Heidi Health (Úc) | Chưa vào VN, không TT32 |
| OneClinic | Không có AI voice |

**Không ai đang làm AI voice-to-EMR cho phòng mạch tư VN.**
Cửa sổ cơ hội: 12–18 tháng.

---

## 3. THỊ TRƯỜNG & ĐỐI TƯỢNG KHÁCH HÀNG

### Dành cho ai: Kinh doanh, Ban lãnh đạo

### Phân khúc thị trường

| Phân khúc | Số lượng | WTP | Phase |
|---|---|---|---|
| Phòng mạch tư lâm sàng (đăng ký BYT) | 15,000–20,000 | 1–3M/tháng | **Phase 0** |
| Phòng khám đa khoa tư | 5,000–8,000 | 3–8M/tháng | Phase 1 |
| Trung tâm CĐHA tư | 1,000–2,000 | 3–8M/tháng | Phase 1 plugin |
| BS công + phòng mạch tư ngoài giờ | 10,000–15,000 | 500k–2M/tháng | Phase 1 |

### 3 Persona chính

**Persona 1 — BS lâm sàng phòng mạch tư (TARGET PHASE 0)**
- Mở phòng mạch sau giờ công, 15–30 bệnh nhân/ngày
- Đang dùng sổ giấy hoặc BravoSoft cũ
- Lo lắng deadline TT13/2025 (31/12/2026)
- Quyết định mua nhanh (1–2 tuần), tự quyết định
- Ưu tiên: tiết kiệm thời gian + compliance

**Persona 2 — BS CĐHA tư (Plugin Phase 1)**
- 30–50 ca siêu âm/X-quang mỗi ngày
- Tự gõ báo cáo hoặc đọc cho thư ký = 3+ giờ/ngày
- WTP cao, quyết định nhanh nếu demo thuyết phục
- Ưu tiên: tốc độ + chính xác báo cáo CĐHA

**Persona 3 — Chủ phòng khám đa khoa (Phase 1–2)**
- 5–20 bác sĩ, cần chuẩn hoá hồ sơ toàn phòng
- TT13/2025 deadline đang gần — áp lực cao
- Cần: multi-user + compliance + HIS integration

---

## 4. SẢN PHẨM: 3 GÓI × 9 MODULES

### Dành cho ai: Kinh doanh, Khách hàng

### 3 Gói dịch vụ

```
┌─────────────────────────────────────────────────────────────────────┐
│ GÓI 1 — AI VOICE ONLY                          ~500k–1M VNĐ/tháng │
│                                                                     │
│ Dành cho: BS mở phòng mạch ngoài giờ, làm một mình                │
│                                                                     │
│ Bao gồm:                                                           │
│  ✅ AI Pipeline: giọng nói → Mẫu 15/BV-01                        │
│  ✅ PDF đơn thuốc + bệnh án                                        │
│  ✅ Hồ sơ bệnh nhân cơ bản (M1)                                   │
│  ✅ Ghi thu chi đơn giản bằng giọng nói (M3)                      │
│  ✅ Queue display + TTS loa gọi tên                                │
│  ✅ Chạy 100% offline, không cần internet                          │
│  ✅ Dữ liệu SQLite local, mã hoá Fernet                           │
│                                                                     │
│ Không bao gồm: đặt lịch online, Zalo, cloud sync                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ GÓI 2 — PHÒNG MẠCH                             ~2–3M VNĐ/tháng   │
│                                                                     │
│ Dành cho: Phòng mạch 1–3 BS + trợ lý, TT13 deadline              │
│                                                                     │
│ Bao gồm tất cả Gói 1, cộng thêm:                                  │
│  ✅ M1 đầy đủ: lịch sử khám, CCCD scan, QR thẻ BN                │
│  ✅ M2: Đặt lịch online + reminder tự động                        │
│  ✅ M4: Upload kết quả XN/CĐHA từ bên ngoài                      │
│  ✅ M6: Zalo OA nhắc lịch + email kết quả                        │
│  ✅ M7: Sync VN Cloud (VNG/FPT/VNPT) — backup + multi-device     │
│  ✅ Màn hình trợ lý riêng (Staff Screen)                          │
│  ✅ Widget đặt lịch cho website phòng khám                        │
│  ✅ Báo cáo doanh thu xuất Excel                                   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ GÓI 3 — PHÒNG KHÁM ĐẦY ĐỦ                      ~4–8M VNĐ/tháng  │
│                                                                     │
│ Dành cho: Phòng khám đa khoa, có nhiều BS, cần HIS                │
│                                                                     │
│ Bao gồm tất cả Gói 2, cộng thêm:                                  │
│  ✅ M5: Referral partner 2 chiều + commission tracking             │
│  ✅ M8: Plugin chuyên khoa (CĐHA, Nha khoa, TMH...)               │
│  ✅ M9: HIS integration (HL7 v2, BravoSoft, FPT.eHospital)       │
│  ✅ REST API Gateway cho kế toán, website                          │
│  ✅ Multi-role: Doctor / Staff / Cashier riêng                    │
│  ✅ Báo cáo đầy đủ + audit export cho BYT                         │
└─────────────────────────────────────────────────────────────────────┘
```

### 9 Modules chi tiết

| # | Module | Mô tả ngắn | Gói |
|---|---|---|---|
| M1 | Quản lý bệnh nhân | Hồ sơ, lịch sử, QR, CCCD scan | 1,2,3 |
| M2 | Đặt lịch hẹn | Book Zalo/web, state machine, reminder | 2,3 |
| M3 | Thu chi đơn giản | Voice log thu/chi, bán thuốc, báo cáo | 1,2,3 |
| M4 | Kết quả bên thứ 3 | Upload/email PDF kết quả XN, CĐHA | 2,3 |
| M5 | Referral partner | 2 chiều, deal %, không ghi tiền | 3 |
| M6 | Zalo/Thông báo | Text non-medical, email cho file y tế | 2,3 |
| M7 | VN Cloud sync | VNG/FPT/VNPT, offline-first, backup | 2,3 |
| M8 | Plugin chuyên khoa | CĐHA, Nha khoa, TMH, Sản khoa | 3 |
| M9 | HIS integration | HL7 v2, BravoSoft, FPT.eHospital | 3 |

---

## 5. NGƯỜI DÙNG & VAI TRÒ

### Dành cho ai: Kinh doanh, Kỹ thuật

### 5 Nhóm người dùng trong hệ thống

**A1 — Bệnh nhân**
- Book lịch qua Zalo/website (Gói 2+)
- Nhận nhắc hẹn, xác nhận lịch
- Gửi kết quả XN qua email (khi có mã giới thiệu)
- Nhận đơn thuốc PDF
- Theo dõi vị trí hàng chờ qua Zalo

**A2 — Trợ lý / Thu ngân (Staff)**
- Tiếp nhận bệnh nhân, tạo/load hồ sơ
- Quản lý hàng chờ, gọi loa
- Thu tiền, phát thuốc, xác nhận đóng ca bệnh nhân
- Lên lịch tái khám
- Ghi doanh thu (M3)

> Ghi chú: Phòng nhỏ = Staff làm luôn thu ngân.
> Phòng lớn = có thu ngân riêng nhưng vẫn dùng cùng 1 app, khác role login.

**A3 — Bác sĩ**
- Khám bệnh, nói vào mic
- Review draft bệnh án do AI tạo
- Phê duyệt hoặc từ chối (bắt buộc theo luật)
- Chỉ định XN/CĐHA/chuyên khoa (referral out)
- Xem hồ sơ bệnh nhân, lịch sử khám

**A4 — Đối tác ngoài** (Lab, X-quang, Nhà thuốc, BS khác)
- Nhận thông báo giới thiệu bệnh nhân (email/Zalo optional)
- Xác nhận tiếp nhận + hoàn tất qua email/Zalo keyword
- Không cần đăng nhập hệ thống
- Không thấy thông tin tài chính/commission trong message

**A5 — Chủ phòng khám / Admin**
- Cấu hình hệ thống (tên phòng, khoa, CCHN BS)
- Setup đối tác referral (M5)
- Xem báo cáo doanh thu, thống kê
- Quản lý tài khoản nhân viên
- Export audit log cho BYT

### Phân quyền

| Quyền | BS | Staff | Admin |
|---|---|---|---|
| Phê duyệt bệnh án | ✅ (bắt buộc) | ❌ | ❌ |
| Tạo referral out | ✅ | ❌ | ❌ |
| Thu tiền | ✅ (Mode A) | ✅ | ❌ |
| Tiếp nhận BN | ✅ (Mode A) | ✅ | ❌ |
| Xem báo cáo đầy đủ | ❌ | ❌ | ✅ |
| Setup hệ thống | ❌ | ❌ | ✅ |
| Xem lịch sử BN | ✅ | ✅ (cơ bản) | ✅ |

---

## 6. MÀN HÌNH & CHẾ ĐỘ VẬN HÀNH

### Dành cho ai: Kỹ thuật, Kinh doanh, Khách hàng

### 4 Màn hình trong hệ thống

```
┌──────────────────────────────────────────────────────────────────┐
│ S1 — MÀN HÌNH PHÒNG CHỜ (TV/Tablet treo tường)                 │
│                                                                  │
│ Hiển thị:                                                        │
│  - Số đang được khám                                            │
│  - Số tiếp theo (chuẩn bị)                                      │
│  - Danh sách đang chờ                                           │
│  - Số đã xong                                                   │
│  - Số vắng mặt (đỏ)                                            │
│                                                                  │
│ Âm thanh: Loa TTS đọc tên bằng giọng Việt chuẩn               │
│  "Kính mời chuẩn bị: số 5, bệnh nhân Trần Thị B"             │
│  "Mời số 5, Trần Thị B, vào phòng khám"                      │
│                                                                  │
│ Setup: Mở browser trên TV → http://192.168.1.x/queue-display  │
│        Tự động refresh 5 giây                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ S2 — STAFF SCREEN (Tablet/PC tại quầy lễ tân)                  │
│                                                                  │
│ Tabs:                                                           │
│  [TIẾP NHẬN]: Thêm BN, load hồ sơ, ghi nguồn giới thiệu      │
│  [HÀNG CHỜ]:  Queue list, [Gọi tiếp theo], trạng thái BN      │
│  [THU TIỀN]:  Checklist đóng ca BN, thu tiền, phát thuốc      │
│  [LỊCH HẸN]:  Calendar, quản lý booking                        │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ S3 — DOCTOR SCREEN (Tablet/PC trên bàn BS)                     │
│                                                                  │
│ Tabs:                                                           │
│  [HÔM NAY]:   Danh sách BN + tóm tắt hồ sơ sơ bộ             │
│  [KHÁM]:      Recording UI, draft review, approve/reject        │
│  [CHỈ ĐỊNH]:  Referral out (XN/CĐHA/chuyên khoa)             │
│  [HỒ SƠ]:    Tra cứu lịch sử BN bất kỳ                        │
│                                                                  │
│ Mode A (không trợ lý): thêm tabs [TIẾP NHẬN] + [THU TIỀN]    │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│ S4 — ZALO BN (Điện thoại bệnh nhân)                            │
│                                                                  │
│ Nhận:                                                           │
│  - Xác nhận đặt lịch + mã booking                             │
│  - Nhắc hẹn D-1, H-2, H-0:15                                  │
│  - Vị trí hàng chờ ("Đang chờ số 5, ~15 phút")               │
│  - Hỏi thăm sức khoẻ sau khám (D+2, D+4)                     │
│  - Hướng dẫn gửi kết quả qua email                            │
│                                                                  │
│ Gửi được (BN → phòng khám):                                    │
│  - Đặt/huỷ/dời lịch                                           │
│  - Phản hồi sức khoẻ (😊/😐/😰)                               │
│  - Text thông báo có kết quả XN                               │
│                                                                  │
│ Không gửi được qua Zalo: File y tế (gửi qua email)            │
└──────────────────────────────────────────────────────────────────┘
```

### 3 Chế độ vận hành

**Mode A — BS làm một mình (Gói 1, không trợ lý)**
- 1 màn hình Doctor Screen với đủ 4 tabs
- BS tự tiếp nhận BN → khám → chỉ định → thu tiền
- Loa TTS optional (BS tự ra mời BN vào)

**Mode B — BS + Trợ lý (Gói 2)**
- Staff Screen: tiếp nhận + thu ngân gộp chung
- Doctor Screen: khám + chỉ định
- Hai màn hình sync realtime qua mạng LAN nội bộ

**Mode C — BS + Trợ lý + Thu ngân riêng (Gói 3)**
- Staff Screen 1: chỉ tiếp nhận
- Staff Screen 2: chỉ thu tiền/admin
- Doctor Screen: khám + chỉ định
- Cùng 1 app, login role khác nhau

---

## 7. HÀNH TRÌNH BỆNH NHÂN — 7 GIAI ĐOẠN

### Dành cho ai: Tất cả — Đây là luồng trung tâm của hệ thống

---

### GIAI ĐOẠN 0 — NGUỒN BỆNH NHÂN (4 nguồn vào)

```
NGUỒN 1: Walk-in trực tiếp
  Bệnh nhân đến quầy không có hẹn
  → Staff/BS đăng ký ngay → vào hàng chờ

NGUỒN 2: Đặt lịch qua Zalo OA [Gói 2+]
  BN nhắn Zalo phòng khám → chọn ngày giờ
  → M2 tạo appointment → Zalo confirm + mã đặt lịch
  → Ngày hẹn: BN đến check-in QR → vào queue

NGUỒN 3: Referral IN từ đối tác [M5, Gói 3]
  Nhà thuốc, phòng khám khác, BS khác giới thiệu BN
  → Staff ghi nguồn tại tiếp nhận
  → M5 track: đối tác + BN + ngày
  → Vào hàng chờ bình thường

NGUỒN 4: Tái khám có hẹn
  BN đã có lịch hẹn tái khám từ lần trước
  → Zalo nhắc D-1 và sáng ngày hẹn
  → BN đến → scan QR → check-in → hàng chờ
  → Hồ sơ + lịch sử load tự động

NGUỒN 5: Từ Website phòng khám [Gói 2+]
  BN thấy trang web phòng khám → đặt lịch qua widget
  → M2 tạo appointment → cùng luồng như Nguồn 2
```

---

### GIAI ĐOẠN 1 — TIẾP NHẬN & ĐĂNG KÝ

```
STAFF SCREEN — Tab [TIẾP NHẬN]

BN CŨ (có QR thẻ bệnh nhân):
  Scan QR → M1 load toàn bộ hồ sơ:
    Thông tin cá nhân, BHYT, dị ứng thuốc ⚠️
    Bệnh mãn tính, lịch sử 5 lần khám gần nhất
    Kết quả XN/CĐHA đã có
    Referral history
  Staff cập nhật: lý do đến hôm nay
  → Thêm vào hàng chờ → số thứ tự

BN MỚI:
  Staff nói vào mic (Mode B) hoặc BS nói (Mode A):
    "Bệnh nhân Trần Thị B, 30 tuổi, nữ,
     địa chỉ Đà Nẵng, đau bụng,
     từ Nhà thuốc Bình Minh giới thiệu"
  → M1 tạo hồ sơ mới (họ tên, DOB, giới tính, địa chỉ...)
  → M5 ghi referral_in nếu có nguồn giới thiệu
  → Scan CCCD [Gói 2+]: camera auto-fill thông tin
  → Ký consent data (lần đầu)
  → Vào hàng chờ → số thứ tự
  → In QR thẻ bệnh nhân (cho lần sau)

THÔNG TIN BẮTBUỘC (TT32/2023):
  Họ tên đầy đủ, ngày sinh, giới tính
  Địa chỉ đầy đủ (thôn, xã, huyện, tỉnh)
  Đối tượng: BHYT / Thu phí / Miễn / Khác

THÔNG TIN KHUYẾN KHÍCH:
  CCCD/CMND, số thẻ BHYT + hạn, nghề nghiệp
  SĐT, email, người thân liên hệ
  Dị ứng thuốc, bệnh mãn tính
```

---

### GIAI ĐOẠN 2 — CHỜ KHÁM (DOCTOR PRE-VISIT BRIEFING)

```
DOCTOR SCREEN — Tab [HÔM NAY]
(BS mở trước khi bắt đầu ca)

Hiển thị tóm tắt từng BN trong queue hôm nay:

┌────────────────────────────────────────────────────────┐
│ CA SÁNG — 12/06/2026              BS Nguyễn Văn B     │
│ 8 bệnh nhân │ 3 có lịch hẹn │ 5 walk-in              │
├────────────────────────────────────────────────────────┤
│ SỐ 1 — Nguyễn Văn A, 45t, Nam          [9:00 HẸN]    │
│   Lần 4 │ Tăng HA (tiền sử) │ "Kiểm tra HA định kỳ" │
│   ⚠️ Dị ứng: Penicillin                              │
│   📋 Lần trước: HA 150/95 — tăng liều Amlodipine     │
│   🔔 Kết quả XN từ 10/06 chưa đọc — cần xem         │
│                                                        │
│ SỐ 2 — Trần Thị B, 30t, Nữ              [Walk-in]    │
│   Lần đầu │ "Đau bụng"                               │
│                                                        │
│ ... (các BN tiếp theo)                                │
│                                                        │
│ ⚠️ CẢNH BÁO: 2 BN có dị ứng Penicillin hôm nay     │
└────────────────────────────────────────────────────────┘

BS click BN → pop-up tóm tắt nhanh + ô ghi chú trước khám
→ [GỌI BN VÀO →] → Loa TTS đọc tên

TRÊN HÀNG CHỜ (S1):
  BN được gọi → số nhấp nháy trên TV
  Loa đọc: "Kính mời chuẩn bị: số 5, Trần Thị B"
  30 giây sau: "Mời số 5 vào phòng khám"

TRÊN ZALO BN [Gói 2+]:
  "Chuẩn bị! Bạn là số tiếp theo. Vui lòng vào gần cửa."
```

---

### GIAI ĐOẠN 3 — KHÁM LÂM SÀNG (AI PIPELINE)

```
DOCTOR SCREEN — Tab [KHÁM]

BS chọn BN từ queue → hồ sơ load tự động
Cảnh báo hiện ngay: dị ứng thuốc ⚠️, bệnh mãn tính
BS nhấn [MIC] → nói tự nhiên trong khi khám

─── VÍ DỤ BÁC SĨ NÓI ───────────────────────────────────
"Bệnh nhân Trần Thị B, 30 tuổi, đau bụng vùng thượng vị
 3 ngày nay, ăn vào đau hơn, không sốt.
 Huyết áp 120/80, mạch 78, không sốt.
 Khám bụng: ấn đau vùng thượng vị, không phản ứng thành bụng.
 Chẩn đoán: Viêm dạ dày cấp.
 Kê Omeprazole 20mg 1 viên 2 lần ngày 7 ngày,
 Bismuth 120mg 2 viên 3 lần ngày 7 ngày.
 Kiêng đồ cay, chua, rượu bia.
 Tái khám sau 1 tuần nếu không đỡ."
─────────────────────────────────────────────────────────

AI XỬ LÝ (L0→L10) → DRAFT TỰ ĐỘNG:
┌────────────────────────────────────────────────────────┐
│ MẪU 15/BV-01 — NHÁP AI                               │
│ ─────────────────────────────────────────────────────  │
│ II. LÝ DO VÀO VIỆN:                                  │
│ Đau bụng vùng thượng vị 3 ngày, ăn vào đau hơn      │
│                                                        │
│ III. HỎI BỆNH:                                       │
│ Quá trình bệnh lý: Đau thượng vị 3 ngày, ăn vào đau │
│ Tiền sử: ...                                          │
│                                                        │
│ IV. KHÁM BỆNH:                                       │
│ Sinh hiệu: HA 120/80 | Mạch 78 lần/ph | Nhiệt 37°C  │
│ Toàn thân: Bình thường                               │
│ Các bộ phận: Ấn đau vùng thượng vị                  │
│ Chẩn đoán: Viêm dạ dày cấp                          │
│ ICD-10-VN: K29.1 (tự tra)                            │
│                                                        │
│ ĐƠN THUỐC:                                           │
│ 1. Omeprazole 20mg — 1v × 2 lần/ngày × 7 ngày       │
│ 2. Bismuth 120mg — 2v × 3 lần/ngày × 7 ngày         │
│                                                        │
│ Tái khám: Sau 1 tuần nếu không đỡ                    │
│                                                        │
│ Confidence: 89% | [Xem transcript gốc]               │
│ ─────────────────────────────────────────────────────  │
│ [CHỈNH SỬA] [TỪ CHỐI] [PHÊ DUYỆT & LƯU ✅]         │
│                                                        │
│ ⚠️ AI tạo nháp — Bác sĩ chịu trách nhiệm hoàn toàn  │
└────────────────────────────────────────────────────────┘

BS review → chỉnh sửa nếu cần → [PHÊ DUYỆT & LƯU]
→ L7: SQLite lưu (encrypted)
→ L10: Audit log ghi "APPROVED by CCHN-xxx at timestamp"
→ L9a: PDF tạo tự động
→ Queue: IN_EXAM → nhánh tiếp theo
```

---

### GIAI ĐOẠN 4 — PHÂN NHÁNH SAU KHÁM

```
Sau khi BS phê duyệt → 3 nhánh, có thể kết hợp:

NHÁNH A — Kết thúc tại phòng khám (không cần XN thêm)
  PDF đơn thuốc → Staff Screen
  → Đi tới GIAI ĐOẠN 5A (thanh toán)

NHÁNH B — BS chỉ định XN/CĐHA/Chuyên khoa (Referral Out)
  BS nói vào [Tab CHỈ ĐỊNH]:
    "Chỉ định X-quang ngực thẳng tại Phòng X-quang ABC"
    "Xét nghiệm máu: CBC, đường huyết tại Lab XYZ"
    "Chuyển BS tim mạch Hùng tại Bệnh viện C"

  System tạo Giấy chỉ định PDF:
    Tên BN + yêu cầu + cơ sở nhận + BS ký
  System gửi thông báo:
    → BN (Zalo text): "Chỉ định tại [Tên cơ sở], mã REF-xxx"
    → Đối tác (Email — CHÍNH THỨC):
       "BN [Tên], dịch vụ [X], mã REF-001234.
        Reply 'OK REF-001234' khi tiếp nhận.
        Reply 'DONE REF-001234' khi hoàn tất."
    → Đối tác (Zalo cá nhân — TÙY CHỌN nếu setup)
  M5: ghi referral_out
  Queue BN: → PENDING_RESULTS
  Staff in giấy chỉ định + hướng dẫn BN tự đi
  → Đi tới GIAI ĐOẠN 4B

NHÁNH C — Bán thuốc tại phòng khám (BS có tủ thuốc)
  Staff đối chiếu đơn thuốc ↔ tồn kho phòng
  Phát thuốc từ tủ → ghi vào M3
  Kết hợp với Nhánh A hoặc B
```

---

### GIAI ĐOẠN 4B — REFERRAL: KẾT QUẢ TỪ BÊN NGOÀI VỀ

```
ĐƯỜNG ĐI CỦA BỆNH NHÂN SAU KHI ĐƯỢC CHỈ ĐỊNH:

Bước 1: Đối tác nhận và xác nhận
  Đối tác reply email/Zalo: "OK REF-001234"
  → System: M5 status = ACKNOWLEDGED
  → Staff notified: "Lab XYZ đã xác nhận tiếp nhận BN B"

Bước 2: BN đến đối tác làm XN/CĐHA
  BN tự liên lạc và đến cơ sở được chỉ định

Trường hợp cần XÉT NGHIỆM LẠI (kết quả lần 1 không đạt):
  Đối tác reply: "REDO REF-001234"
  → M5 status = RETEST_REQUIRED
  → Zalo BN: "Cần xét nghiệm lại, liên hệ [Tên cơ sở]"
  → Tạo REF-001234-R2 nếu cần chỉ định lại
  Commission chỉ tính khi COMPLETED lần cuối cùng

Bước 3: Đối tác hoàn tất
  Reply: "DONE REF-001234"
  → M5 status = COMPLETED, commission event ghi nhận

Bước 4: BN liên hệ phòng khám để tái khám
  BN nhắn Zalo (TEXT ONLY — không file):
    "Em có kết quả X-quang rồi ạ, muốn đặt tái khám"

  System auto-reply Zalo:
    "Gửi file kết quả về email:
     ketqua@phongkham-nguyen.vn
     Tiêu đề: KQ [Tên] [Ngày sinh] (ví dụ: KQ Tran Thi B 01011996)"

Bước 5: BN gửi file kết quả qua EMAIL
  From: bn@gmail.com
  To: ketqua@phongkham-nguyen.vn
  Subject: KQ Tran Thi B 01011996
  Attachment: xquang.pdf

  EMAIL AUTO-PROCESSOR (chỉ khi có điều kiện):
  ① BN đã có hồ sơ M1 (đã đăng ký)
  ② Có referral ACTIVE (REF-001234 đang chờ kết quả)
  ③ BN đã ký consent data processing
  → Tự động: parse → match patient → M4 upload → notify BS
  → Thiếu 1 trong 3: QUARANTINE → Staff xem xét thủ công

Bước 6: Đặt lịch tái khám
  Zalo hỏi: "Kết quả đã nhận. Chọn lịch tái khám:"
  [18/06 14h] [19/06 9h] [20/06 10h] [Ngày khác]
  → Booking flow (Giai đoạn 6)
```

---

### GIAI ĐOẠN 5A — THANH TOÁN & ĐÓNG CA BỆNH NHÂN

```
STAFF SCREEN — Tab [THU TIỀN]

Checklist bắt buộc trước khi đóng ca bệnh nhân:

┌──────────────────────────────────────────────────────┐
│ BN: Trần Thị B — Số 5                               │
│                                                      │
│ ☑ Thu tiền khám:     150.000đ                       │
│ ☑ Thu tiền thuốc:    200.000đ (phát tại phòng khám) │
│   hoặc: BN mua ngoài — Không áp dụng               │
│ ☑ Đã phát thuốc:     Omeprazole + Bismuth           │
│ ☑ Giấy chỉ định:     Đã in + đã đưa BN             │
│   (nếu có nhánh B)                                  │
│ ☑ Lịch tái khám:     19/06/2026 9h                 │
│   hoặc: Không tái khám — Không áp dụng             │
│                                                      │
│ [ XÁC NHẬN HOÀN TẤT ✅ ]                            │
└──────────────────────────────────────────────────────┘

Sau khi xác nhận:
→ M3: ghi doanh thu tự động
→ L10: audit "ADMIN_CONFIRMED" + staff_id + timestamp
→ M2: tạo lịch hẹn tái khám nếu có

ZALO BN [Gói 2+]:
  "✅ Cảm ơn đã đến khám! Nhớ uống thuốc đầy đủ nhé 😊"
  (text generic — không gửi tên thuốc/chẩn đoán qua Zalo OA)

EMAIL BN (nếu có địa chỉ email):
  Đính kèm: [Đơn thuốc.pdf] + [Mẫu 15/BV-01.pdf]
  (file y tế → email, không phải Zalo)

BN ra về.
```

---

### GIAI ĐOẠN 6 — BOOK LỊCH TÁI KHÁM

```
HỆ THỐNG BOOKING — Tiêu chuẩn industry

VÒNG ĐỜI LỊCH HẸN (Appointment States):

SUGGESTED → BN chọn slot → PENDING
  → BN confirm (2h) → CONFIRMED
  → Ngày hẹn: check-in → COMPLETED
  → Hoặc: CANCELLED / LATE_CANCEL / NO_SHOW / RESCHEDULED

TRIGGER TẠO LỊCH:
  A. BS nói "tái khám sau 1 tuần"
     → System tính ngày → query lịch BS → gợi ý 3 slot
  B. BN nhắn "muốn đặt lịch"
     → System show available slots
  C. Kết quả XN về → auto-suggest tái khám

REMINDER CHUẨN (Tiêu chuẩn Canada):
  Lịch hẹn: 12/06/2026 lúc 10:00

  D-1 lúc 9h (11/06):
    "Nhắc: Tái khám ngày mai 12/06 lúc 10:00
     Phòng khám BS Nguyễn — 45 Trần Phú, Đà Nẵng
     [Xác nhận đến ✅] [Huỷ ❌] [Dời lịch 🔄]"

  H-2 lúc 8:00 (12/06):
    "Còn 2 tiếng! Lịch 10:00 hôm nay.
     Nhớ mang kết quả XN nếu có."
     [Xác nhận đến ✅] [Huỷ ❌]

  H-0:15 lúc 9:45 (12/06):
    "Còn 15 phút! Vui lòng đến làm thủ tục trước 10:00."

BUFFER & WAITLIST (bảo vệ bác sĩ):
  H-1 (9:00) — BN chưa xác nhận → UNCONFIRMED
    → Staff alert: "BN X chưa xác nhận lịch 10h"
    → Check waitlist: ai muốn sớm hơn?
    → Offer slot cho waitlist ngay

  Huỷ < 2h → EMERGENCY_AVAILABLE
    → Offer ngay cho waitlist qua Zalo/SMS

  Buffer sau mỗi 4 ca: 15 phút
    → Hấp thụ ca kéo dài, BN tiếp không bị trễ

CANCELLATION FLOW:
  > 24h: CANCELLED → slot released → offer reschedule
         "Đã huỷ. Đặt lịch mới: [3 slot gợi ý]"
  < 24h: LATE_CANCEL → slot released + staff notified
         "Huỷ trễ. Lần sau vui lòng báo trước 24h."
  No-show: sau 30 phút → NO_SHOW
         Zalo: "Có lịch hẹn hôm nay chưa đến..."
         [Đặt lịch mới] [Không cần]
  Dời lịch: BN click [Dời lịch] → slot mới → PENDING
```

---

### GIAI ĐOẠN 7 — CHĂM SÓC SAU KHÁM (After-care CRM)

```
TỰ ĐỘNG DỰA TRÊN ĐƠN THUỐC + LỊCH TÁI KHÁM

Ví dụ: thuốc 7 ngày, tái khám 1 tuần

D+2 (ngày 14/06 8h):
  "Chào [Tên]! Thuốc uống đều chưa? Cảm thấy thế nào? 😊"

D+5 (ngày 17/06 8h) — sắp hết thuốc:
  "Còn ~2 ngày thuốc. Bạn cảm thấy thế nào?"
  [😊 Tốt hơn nhiều]
  [😐 Còn hơi khó chịu]
  [😰 Không cải thiện / Nặng hơn]

  → 😊 Tốt hơn:
     "Vui vì bạn khoẻ hơn! 🌟 Nhớ uống hết thuốc.
      Lịch tái khám: [Date Time]."

  → 😐 Còn khó chịu:
     "Muốn tái khám sớm hơn?
      [Đặt lịch sớm] [Giữ lịch [Date]]"

  → 😰 Nặng hơn:
     ⚠️ ALERT STAFF NGAY
     "Vui lòng liên hệ phòng khám. [Gọi] [Đặt lịch khẩn]"

D+7 (ngày 19/06): Reminder tái khám → Giai đoạn 6 tiếp quản

BỆNH NHÂN KHÔNG CÓ TÁI KHÁM (bệnh nhẹ):
  D+3: "Hy vọng bạn đã khoẻ 😊"
  D+30: "Lâu rồi chưa gặp. Phòng khám luôn sẵn sàng."
        (1 tin duy nhất)

BỆNH MÃN TÍNH (tiểu đường, cao HA — gắn tag M1):
  D+30: "Kiểm tra sức khoẻ định kỳ tháng này chưa?"
  D+90: "Nhắc: kiểm tra 3 tháng. [Đặt lịch]"

RULES ANTI-SPAM:
  Max 3 tin/tuần per BN
  Giờ gửi: 7h–20h (không gửi đêm)
  BN nhắn "DỪNG" → unsubscribe ngay
  Nội dung: generic wellness, không tên bệnh/thuốc (Zalo policy)
```

---

## 8. HỆ THỐNG QUẢN LÝ HÀNG CHỜ (QUEUE)

### Dành cho ai: Kỹ thuật, Kinh doanh

```
QUEUE STATES:
  BOOKED    ← Zalo đặt lịch trước
  WAITING   ← Walk-in hoặc đã check-in
  CALLED    ← Gọi chuẩn bị, loa đọc tên
  IN_EXAM   ← Đang trong phòng với BS
  DONE_CASHIER     ← Ra thanh toán
  PENDING_RESULTS  ← Chờ kết quả XN bên ngoài
  REFERRED_OUT     ← Đã được gửi đi chuyên khoa
  NO_SHOW          ← Được gọi 2 lần không vào
  DONE             ← Đã hoàn tất tất cả, ra về

MÀN HÌNH PHÒNG CHỜ (S1):
┌──────────────────────────────────────────────────────┐
│          PHÒNG KHÁM BS NGUYỄN                        │
│                                                      │
│  ĐANG KHÁM        CHUẨN BỊ                          │
│  ┌──────────┐     ┌──────────────────┐              │
│  │  SỐ  4  │     │     SỐ  5        │              │
│  │ Ng.Văn A│     │  Trần Thị B     │ ← nhấp nháy  │
│  └──────────┘     └──────────────────┘              │
│                                                      │
│  ĐANG CHỜ:                                          │
│  6-Lê C   7-Phạm D   8-Hoàng E   9-Ngô F           │
│                                                      │
│  ĐÃ XONG: ✅1  ✅2  ✅3                              │
│  VẮNG MẶT: ❌2-Bùi G (được gọi 2 lần)              │
└──────────────────────────────────────────────────────┘

LOA TTS — Script tự động:
  CALLED:  "Kính mời chuẩn bị: số 5, bệnh nhân Trần Thị B"
  IN_EXAM: "Mời số 5, bệnh nhân Trần Thị B, vào phòng khám"
  REMIND2: "Nhắc lần 2: số 2, bệnh nhân Bùi Văn G"
  ABSENT:  "Số 2 vắng mặt — xin mời số 3 tiếp theo"

  Engine: VinAI TTS offline / gTTS
  Đọc đúng dấu tiếng Việt (giọng chuẩn miền Nam/Bắc)
  Phát qua loa USB hoặc loa Bluetooth

STAFF SCREEN — Queue Table:
┌──┬────────────┬────────┬──────┬────────────────────┐
│# │ Tên BN     │ Trạng  │ Chờ  │ Actions            │
│  │            │ thái   │(ph)  │                    │
├──┼────────────┼────────┼──────┼────────────────────┤
│4 │ Ng.Văn A   │🟢KHÁM  │  --  │ [Hồ sơ]           │
│5 │ Trần Thị B │🟡CHUẨN │   0  │ [Mời vào] [Vắng]  │
│6 │ Lê Văn C   │⬜CHỜ   │  12  │ [Xem] [Gọi]       │
│7 │ Phạm Thị D │📅HẸN   │ 9:30 │ [Xem]             │
│2 │ Bùi Văn G  │🔴VẮNG  │  45  │ [Nhắc] [Xoá]      │
└──┴────────────┴────────┴──────┴────────────────────┘
│ [GỌI SỐ TIẾP THEO 🔊]                               │
│ Đã khám: 3  │  Đang chờ: 5  │  Tổng hôm nay: 8   │
```

---

## 9. HỆ THỐNG BOOK LỊCH & NHẮC HẸN (M2)

### Dành cho ai: Kinh doanh, Kỹ thuật

*(Chi tiết đã mô tả trong Giai đoạn 6 — xem thêm)*

### Calendar View (Staff Screen)

```
┌──────┬──────┬──────┬──────┬──────┬──────┐
│ T.2  │ T.3  │ T.4  │ T.5  │ T.6  │ T.7  │
│ 17   │ 18   │ 19   │ 20   │ 21   │ 22   │
├──────┼──────┼──────┼──────┼──────┼──────┤
│ 9h✅ │ 9h✅ │ 9h🔵 │ 9h⬜ │ 9h✅ │NGHỈ  │
│ 9:30⬜│9:30⬜│10:30 │10h⬜ │10h✅ │      │
│ 10h✅│ 10h⬜│ 11h⬜│ 11h⬜│ 11h✅│      │
└──────┴──────┴──────┴──────┴──────┴──────┘
✅ Confirmed  🔵 Pending  ⬜ Trống  ❌ Cancelled

WAITLIST: BN muốn slot sớm hơn
  → Khi có slot cancel → offer ngay qua Zalo
  → "Có chỗ trống 10h hôm nay. Nhận không? [Có ✅] [Không ❌]"
```

### Tích hợp Website & Zalo

```
WEBSITE WIDGET [Gói 2+]:
  BS thêm vào website:
  <script src="https://book.medivoice.vn/widget.js"
          data-clinic="pk-nguyen-danang">
  </script>
  Widget hiện form đặt lịch → submit → M2 nhận

REST API BOOKING [Gói 3]:
  POST /api/v1/booking
  → Clinic's developer tự build UI trên website
  → MediVoice xử lý backend booking
```

---

## 10. HỆ THỐNG ĐỐI TÁC & REFERRAL (M5)

### Dành cho ai: Kinh doanh, Kỹ thuật

### Hai chiều Referral

```
CHIỀU 1 — REFERRAL OUT (Tôi gửi BN đi đối tác)
  Ví dụ: BS chỉ định X-quang tại Phòng X-quang ABC

  Quy trình:
  1. BS nói [Tab CHỈ ĐỊNH] → System tạo REF-001234
  2. Email → Phòng X-quang ABC (chính thức, bảo mật)
     Zalo cá nhân đối tác (optional, nếu họ muốn)
  3. Đối tác reply: "OK REF-001234" → ACKNOWLEDGED
  4. BN đi XN → Đối tác làm xong
  5. Đối tác reply: "DONE REF-001234" → COMPLETED
  6. Commission event ghi nhận (không ghi tiền)

  Trường hợp RETEST (lần 1 không đạt):
  Đối tác reply: "REDO REF-001234"
  → System tạo REF-001234-R2
  → BN làm lại → DONE R2 → commission tính lần cuối

CHIỀU 2 — REFERRAL IN (Đối tác gửi BN đến tôi)
  Staff ghi tại INTAKE: "từ Nhà thuốc Bình Minh"
  → M5: referral_in, partner, patient, date
  Báo cáo: "Tháng 6: 12 BN từ Nhà thuốc Bình Minh"
```

### Commission Tracking — Đúng Luật

```
ĐƯỢC LÀM:
  ✅ Ghi nhận: đối tác + BN + ngày + sự kiện
  ✅ Setup % deal khi cấu hình đối tác (tham chiếu)
  ✅ Báo cáo volume: bao nhiêu BN trao đổi
  ✅ Tính toán tham chiếu: volume × deal %
  ✅ Đối tác xem dashboard của họ (số BN, sự kiện)

KHÔNG ĐƯỢC LÀM (Luật KCB 2023 Điều 80):
  ❌ Ghi số tiền commission cụ thể trong giao dịch
  ❌ Xử lý thanh toán commission trong app
  ❌ Tự động chuyển tiền

THANH TOÁN THỰC TẾ:
  Hai bên tự thực hiện ngoài hệ thống
  App chỉ cung cấp: volume data để tham chiếu

KÊNH LIÊN LẠC VỚI ĐỐI TÁC:
  Email: CHÍNH THỨC — tất cả thông tin nhạy cảm
  Zalo: TÙY CHỌN — chỉ khi đối tác muốn, chỉ text
  Thông tin commission: KHÔNG qua Zalo (bí mật)
```

### Dashboard M5

```
REFERRAL REPORT — Tháng 6/2026
┌────────────────────────────────────────────────────────┐
│ ĐÃ GỬI (Out): Tôi gửi BN đi                          │
├──────────────┬──────┬───────┬────────────────────────  │
│ Đối tác      │ Gửi  │ Xong  │ Deal (tham chiếu)       │
├──────────────┼──────┼───────┼──────────────────────── │
│ PX X-quang  │   8  │   7   │ 5% / ca                  │
│ Lab XYZ     │   5  │   5   │ 3% / ca                  │
│ BS Tim mạch │   2  │   1   │ Không deal               │
├────────────────────────────────────────────────────────│
│ ĐÃ NHẬN (In): Đối tác gửi BN đến tôi                 │
├──────────────┬──────┬───────┬──────────────────────── │
│ Nguồn        │ Nhận │ Tái   │ Deal (tham chiếu)       │
├──────────────┼──────┼───────┼──────────────────────── │
│ NT Bình Minh │  12  │   4   │ 10% / ca                │
│ PK Sơn       │   6  │   2   │ 8% / ca                 │
│ Walk-in      │  45  │  18   │ —                       │
└────────────────────────────────────────────────────────┘
⚠️ Số tiền thực tế: do hai bên thoả thuận ngoài hệ thống
```

---

## 11. CHĂM SÓC SAU KHÁM — AFTER-CARE CRM (M6)

### Dành cho ai: Kinh doanh, Kỹ thuật

*(Chi tiết đã mô tả trong Giai đoạn 7 — xem thêm)*

### Quy tắc nội dung Zalo

```
ĐƯỢC GỬI QUA ZALO OA:
  ✅ Nhắc lịch hẹn (ngày, giờ, địa chỉ)
  ✅ Xác nhận đặt lịch
  ✅ Hỏi thăm sức khoẻ chung (không tên bệnh/thuốc)
  ✅ Thông báo có kết quả → hướng dẫn gửi email

KHÔNG GỬI QUA ZALO OA (vi phạm chính sách Zalo):
  ❌ Tên bệnh, chẩn đoán
  ❌ Tên thuốc, liều lượng
  ❌ File đính kèm y tế
  ❌ Thông tin kết quả XN/CĐHA chi tiết

GỬI QUA EMAIL (không hạn chế):
  ✅ PDF đơn thuốc
  ✅ PDF bệnh án Mẫu 15/BV-01
  ✅ File kết quả XN/CĐHA
  ✅ Thông tin y tế chi tiết
```

### Kênh liên lạc theo giai đoạn

| Sự kiện | Zalo | Email | SMS |
|---|---|---|---|
| Xác nhận booking | ✅ | ✅ | Ph.2 |
| Nhắc D-1, H-2, H-0:15 | ✅ | ❌ | Ph.2 |
| PDF đơn thuốc | ❌ | ✅ | ❌ |
| PDF bệnh án | ❌ | ✅ | ❌ |
| Hỏi thăm D+2, D+4 | ✅ | ❌ | ❌ |
| Kết quả XN hướng dẫn | ✅ (text) | ✅ (file) | ❌ |
| Referral confirm | Email/Zalo CP | Email | ❌ |

---

## 12. QUẢN LÝ BỆNH NHÂN (M1)

### Dành cho ai: Kinh doanh, Kỹ thuật

```
HỒ SƠ BỆNH NHÂN — Chuẩn TT32/2023 Phần I Hành chính

BẮT BUỘC:
  Họ và tên đầy đủ
  Ngày/tháng/năm sinh + Tuổi (tự tính)
  Giới tính
  Địa chỉ: số nhà, thôn/phố, xã/phường, huyện, tỉnh/thành
  Đối tượng: BHYT / Thu phí / Miễn / Khác
  Giờ đến khám (tự động timestamp)

KHÔNG BẮT BUỘC (khuyến khích):
  CCCD/CMND 12 số
  BHYT: số thẻ + hạn dùng
  Nghề nghiệp, Dân tộc
  Nơi làm việc
  Người thân liên hệ + SĐT khẩn cấp
  Nguồn đến: Y tế giới thiệu / Tự đến
  Chẩn đoán nơi giới thiệu (nếu có)
  Email (digital communication)
  SĐT Zalo (nhắc lịch)

CLINICAL (AI điền từ voice):
  Dị ứng thuốc ⚠️ (CẢNH BÁO khi BS kê đơn)
  Bệnh mãn tính (tự load vào tiền sử mỗi lần khám)
  Thuốc đang dùng

LỊCH SỬ KHÁM:
  5 lần khám gần nhất hiển thị ngay
  Đơn thuốc cũ → suggest tái kê
  Kết quả XN/CĐHA đã upload (M4)
  Referral history (M5)

TAGS:
  [Bệnh mãn tính] [Lần đầu] [BHYT] [VIP] [Dị ứng đặc biệt]

QR CODE:
  Mỗi BN = 1 QR duy nhất
  In ra thẻ bệnh nhân → scan cho lần sau
  Scan = load toàn bộ hồ sơ ngay lập tức

CONSENT (ký khi tạo hồ sơ lần đầu):
  ① Thu thập thông tin cho mục đích khám chữa bệnh
  ② Lưu hồ sơ điện tử tại phòng khám (TT32/2023)
  ③ Nhận nhắc lịch qua Zalo (non-medical text)
  ④ Nhận thông tin hẹn qua email (nếu cung cấp)
  ⑤ Kết quả XN khi có mã giới thiệu hợp lệ
  BN rút consent: unsubscribe + flag "no_digital_contact"
```

---

## 13. THU CHI & BÁO CÁO (M3)

### Dành cho ai: Kinh doanh, Kỹ thuật

```
THU CHI ĐƠN GIẢN (Voice):
  Staff/BS nói vào mic:
    "Thu 200k bệnh nhân Trần Thị B"
    "Bán Amoxicillin 1 hộp 50k"
    "Chi mua thuốc 2 triệu"
    "Thu phí khám 150k"

  Auto parse → lưu SQLite:
    type: THU/CHI
    amount, description, patient_id (nếu có)
    timestamp, staff_id

BÁO CÁO:
  Ngày: tổng thu / tổng chi / lợi nhuận gộp
  Tuần: biểu đồ doanh thu
  Tháng: so sánh tháng trước
  Top dịch vụ theo doanh thu

XUẤT DỮ LIỆU:
  Excel/CSV: [Gói 2+] — import thủ công vào MISA/Fast
  REST API: [Gói 3] — kế toán phần mềm kéo tự động

GHI CHÚ:
  M3 = thu chi đơn giản, không phải kế toán đầy đủ
  Phần kế toán chính thức: chủ phòng khám tự dùng MISA/Fast
```

---

## 14. KẾT QUẢ BÊN THỨ 3 (M4)

### Dành cho ai: Kỹ thuật

```
UPLOAD THỦ CÔNG [Gói 2+]:
  Staff/BS scan hoặc chụp ảnh kết quả giấy
  → Upload → gắn vào hồ sơ BN M1
  → Doctor Screen: badge thông báo "Có kết quả mới"

EMAIL AUTO-PROCESSOR [Gói 2+, Phase 1]:
  BN gửi email với file kết quả
  Điều kiện tự động xử lý (CẢ 3 phải đủ):
    ① BN đã đăng ký trong M1
    ② Có referral ACTIVE (REF-xxx đang chờ)
    ③ BN đã ký consent
  → Parse subject → match patient → upload M4
  → Nếu thiếu: QUARANTINE → Staff xem xét thủ công

TÍCH HỢP AUTO [Gói 3, Phase 2]:
  M9 HIS API kéo kết quả từ Lab/CĐHA tự động
  → M4 nhận → gắn vào hồ sơ BN
  → Thông báo BS ngay
```

---

## 15. AI PIPELINE KỸ THUẬT (L0→L10)

### Dành cho ai: Kỹ thuật
### Version: v2.1 — Cập nhật 2026-06-09 | FID-VN-010 + FID-VN-011 | BENCH-002b evidence

> **v2.0 RATIONALE:** BENCH-002b evidence (2026-06-08): Drug Recall local pipeline = 13–18% vs Cloud LLM = 78%.
> Root causes: Drug OOV hallucination + No clinical domain bias ở ASR + Fixed chunk cắt giữa câu + Dialect gap.
> FID: `fids/FID-VN-010.md` | Consultation: `docs/records/consultations/CONS-20260608-002.md`
>
> **v2.1 UPDATE (2026-06-09):** FID-VN-011 implement xong — Layer 3b RAG thay vì "Layer 5"; thresholds calibrated từ
> BENCH-002b; drug_db_v200 nâng lên 154 INN; model preload singleton; PhoBERT chạy PARALLEL thay shadow mode.
> FID: `fids/FID-VN-011.md` | Tests: 794/794 PASS

```
INPUT: Giọng nói bác sĩ (WAV/MP3/M4A/WEBM)

[L0] NORMALIZE (v2 — VAD-aware)
  a. Chuẩn hoá về 16kHz mono PCM
  b. VAD silence-aware chunking [v2 NEW — silero-vad]
       → chunk theo điểm im lặng tự nhiên (thay fixed 10s)
       → max chunk = 20s để Whisper không truncate
       → giữ drug+dose trong cùng 1 chunk
  c. Hash SHA-256 để đảm bảo bất biến
  d. XÓA audio gốc sau khi xử lý (Privacy by Design — NĐ13/2023)

[L1a] ASR — NHẬN DẠNG GIỌNG NÓI (v2 — domain-primed)
  Model: PhoWhisper-medium (vinai/PhoWhisper-medium, BSD-3-Clause)
         [upgraded từ PhoWhisper-small theo BENCH-001/002 evidence]
  Chạy: 100% offline, không network call
  Chunking: VAD silence-aware (L0b) — không cắt giữa câu [v2]
  [v2 NEW] Prompt Injection — initial_prompt với drug list:
    → Inject top 30 drugs theo specialty vào Whisper decoder
    → Bias acoustic model về medical vocabulary
    → Expected: +10–25% drug recall cho drugs có phonetic overlap
  Output: transcript tiếng Việt thô

[POST-ASR TEXT NORMALIZATION] [v2 NEW]
  a. Dialect normalization — src/core/dialect_norm.py:
       Miền Trung: mô→đâu | rứa→vậy | hỉ→nhỉ | răng→sao | ni→này
       Miền Nam: hổng→không | dzô→vào | tui→tôi
       ⚠️ Region-aware: "ốm" = bệnh (Trung) ≠ gầy (Nam)
       Nguồn region: facility.region config khi BS đăng ký
  b. Abbreviation expansion — cùng file:
       ha→huyết áp | bn→bệnh nhân | tk→tái khám
       xn→xét nghiệm | sa→siêu âm | xq→x-quang
       đtđ→đái tháo đường | tha→tăng huyết áp

[L1b] DRUG CORRECTION (v2.1 — multi-layer, FID-VN-011)
  Layer 1: Exact alias match — drug_db_v200.json keywords + brand names (fast)
  Layer 2: Fuzzy match RapidFuzz token_sort_ratio (cutoff 70%) — n-gram windows (3,2,1)
  Layer 3: Phonetic prefix + diagnosis context (_context_prefix_match)
  Layer 3b [FID-VN-011 — v2.1 NEW]: Drug Vector RAG fallback
    → Trigger: token ≥6 chars AND Layer 1+2+3 đều miss
    → Hybrid query: 0.65 × RapidFuzz phonetic + 0.35 × RAG cosine similarity
         (hybrid_query_drug() trong src/core/drug_rag.py)
    → Store: drug_db_v200 (154 INN, phonetic_variants 3 vùng miền, drug_class)
    → Recover: "zxqvjkw" + "tăng huyết áp" context → Amlodipine
    → Thresholds (calibrated từ BENCH-002b):
         score ≥ 0.68 → auto-accept, flag LOW_CONFIDENCE (BS confirm qua L4)
         score 0.55–0.68 → flag only, không sửa transcript
         score < 0.55 → bỏ qua
    → Nếu RAG deps không install → skip silently (backward compat)
  Layer 4: Safety Rule Engine — hard dose validation, ambiguity → flag (mọi layer)
  DB: drug_db_v200.json — 154 INN (DRUG-DB-002: +8 2026-06-09), phonetic_variants 3 regions
  Model preload [FID-VN-011]: src/api/main.py startup():
    → _embed_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    → _drug_collection = load_drug_vectorstore()
    → Load 1 lần lúc startup — inject vào correct_drug_names_v2(rag_collection, embed_model)
    → Tránh cold start 3-5s mỗi API call

[L1c] NER — NHẬN DẠNG THỰC THỂ Y TẾ
  Extract từ transcript tiếng Việt đã normalize:
    VITAL: huyết áp, mạch, nhiệt độ, nhịp thở, cân nặng, SpO2
    SYMPTOM: triệu chứng, lý do khám
    MEDICATION: thuốc + liều + tần suất + số ngày + đường dùng
    HISTORY: tiền sử bệnh, dị ứng
    FOLLOWUP: lịch tái khám
  Phase 0: rule-based regex (nhanh, reliable) — CURRENT (production)
  [FID-VN-009 — DONE 2026-06-09] PhoBERT PARALLEL mode — ON (supplement only):
    → PARALLEL: rule-based luôn chạy; PhoBERT bổ sung gaps (không replace)
    → early-exit: nếu rule-based confidence cao → bỏ qua PhoBERT call
    → PhoBERT F1=99.44% (TRAIN-002, 3 epochs, 10K synthetic BIO samples)
    → Chỉ ghi vào meta["phobert_*"] — KHÔNG viết trực tiếp vào MedicalEntities vital
    → Dedup: PhoBERT result trùng rule-based → bỏ qua; khác → supplement
    → Model: vinai/phobert-base-v2 + CRF head, lazy-load, lru_cache
    → src/core/l1c_phobert.py + extract_entities_hybrid() trong l1c_ner.py

[L1d] ICD-10-VN LOOKUP
  Tra mã tự động từ text chẩn đoán (đã dialect-normalized)
  Database: 15,026 mã (icd10vn.json — QĐ5837/QĐ-BYT)
  [v2] ICD-10 Vector RAG — LangChain (Phase 0.5):
    → Semantic lookup thay substring search
    → Handle synonyms: "đái tháo đường" = "tiểu đường" = T90
  Output: mã ICD-10-VN + tên tiếng Việt

[L2] VALIDATE (v2 — confidence per field)
  Tính confidence score cho từng field (0.0–1.0)
  Overall confidence = weighted score
  [v2] Per-field confidence hiển thị ở L4 UI:
    don_thuoc[i]: 0.61 ⚠️ → BS phải confirm bằng tap
  Flag low confidence < 0.3 → cảnh báo BS + block approve

[L3] ROUTE
  Phân loại từ keywords trong transcript:
    lam_sang (default) → Mẫu 15/BV-01
    cdha (siêu âm, x-quang, CT, MRI) → báo cáo CĐHA [M8]
    nha_khoa (răng, nha, nướu) → Mẫu 16/BV-01 [M8]
  LangChain orchestration (Phase 0.5): 4 chains parallel:
    Chain-A: Drug normalization | Chain-B: ICD-10 lookup
    Chain-C: Dialect context | Chain-D: Form fill + validation
    LLM: Groq LLaMA-3.3-70B (Phase 0) → Qwen2.5-7B LoRA local (Phase 2)

[L4] HUMAN GATE (v2 — per-drug mandatory confirm)
  Status → PENDING_REVIEW
  [v2 SAFETY REDESIGN — FID-VN-010]:
    KHÔNG batch approve toàn form
    Mỗi thuốc: BS phải tap [✓ Xác nhận: Amlodipine 5mg/sáng]
    Thuốc flagged (confidence < 0.80): [⚠️ AI chưa chắc — xác nhận?]
    Chỉ khi tất cả drugs confirmed → unlock [Approve & Sign]
    Hiển thị confidence bar cho từng field
  KHÔNG bypass, KHÔNG auto-save (Luật KCB 2023 Điều 62)
  Evidence: Session 174116 — Losartan→Atorvastatin, BS chấm 5/5 không phát hiện

  [L4 CORRECTION CAPTURE — FID-VN-006, v2]:
    Ghi diff AI→BS corrections vào data/corrections/{clinic_id}.jsonl:
      {session_id, drug_ai, drug_bs, confidence_before, timestamp, specialty}
    Chạy tự động mỗi approve — không làm chậm flow
    Source chính cho DVP Layer 3 (personal alias — FID-VN-012):
      ≥3 corrections cùng alias trong ≥2 sessions → promote candidate
      Human Gate: BS confirm YES/NO trước khi alias activate
    Tool phân tích: scripts/analyze_corrections.py

[L5] PII SCAN
  Quét thông tin nhạy cảm trong transcript:
    CCCD 12 số, CMND 9 số
    Số điện thoại (0[3-9]xxxxxxxx)
    Số thẻ BHYT | Email
  Flag nếu phát hiện → BS được thông báo

[L6] BRANCH — TẠO FORM
  lam_sang:
    NER entities → map trực tiếp → BenhAnNgoaiTru:
      VITAL → kham_benh.sinh_hieu.*
      SYMPTOM → ly_do.ly_do + hoi_benh.qua_trinh_benh_ly
      HISTORY → hoi_benh.tien_su_ban_than
      MEDICATION → don_thuoc.danh_sach_thuoc (ThuocKe)
      ICD → kham_benh.ma_icd10
      FOLLOWUP → don_thuoc.tai_kham
    (Không qua SOAP — trực tiếp từ NER entities)
  cdha / nha_khoa → plugin riêng [Phase 1, M8]

[L7] STORAGE
  SQLite + WAL (Write-Ahead Logging) — hiệu suất cao
  Fernet encryption at rest — dữ liệu mã hoá
  Local on-premise — tuân thủ NĐ13/2023
  Schema: ClinicalRecord, Patient, Facility, AuditEntry

[L8] ERROR RECOVERY
  @with_recovery decorator cho mọi stage
  Graceful degradation — pipeline không crash toàn bộ
  Log lỗi → L10

[L9a] PDF EXPORT
  ReportLab → Mẫu 15/BV-01 (TT32/2023)
  Bắt buộc: "AI tạo nháp — Bác sĩ chịu trách nhiệm hoàn toàn"
  Xuất ra thư mục exports/
  BS ký số [Phase 2, TT13/2025]

[L10] IMMUTABLE AUDIT LOG
  SHA-256 hash chain — mỗi entry link đến entry trước
  Append-only — không thể sửa/xoá
  Lưu trữ 10+ năm (TT32/2023)
  Nội dung: stage, actor, timestamp, action, hash
  [v2] Ghi thêm: dialect_substitutions, drug_rag_candidates, confidence_scores
  verify_chain() — kiểm tra tính toàn vẹn hàng tuần

[MODEL LIFECYCLE — FID-VN-011]
  Embedding model + ChromaDB collection preloaded tại app startup (1 lần):
    _embed_model:      SentenceTransformer singleton (paraphrase-multilingual-MiniLM-L12-v2)
    _drug_collection:  ChromaDB collection singleton (data/drug_vectorstore/)
  Startup flow (src/api/main.py):
    → startup() gọi load_drug_vectorstore() + SentenceTransformer()
    → ~3–5 giây lúc khởi động (chấp nhận được)
    → Inject vào pipeline: correct_drug_names_v2(rag_collection=_drug_col, embed_model=_emb)
  Per-request latency: +0ms (model đã load sẵn)
  Fallback: nếu sentence-transformers / chromadb chưa install
    → warning log, skip RAG, L1b hoạt động Layer 1+2+3 như v1 (backward compat)

OUTPUT: BenhAnNgoaiTru + PDF Mẫu 15/BV-01 + Audit entry

REAL-TIME UI LAYER (parallel với tất cả layers):
  Drug suggestion chips — top 3 candidates + pronunciation VN
  Dialect badge — "Giọng Trung: mô→đâu, rứa→vậy" (dismissible)
  Specialty terminology sidebar — thuật ngữ hay dùng theo chuyên khoa
  Transcript live display — streaming từng utterance
```

### Performance benchmarks (BENCH-002b real BS voice, 2026-06-09)

| Metric | v1.0 local | **v2.1 actual (2026-06-09)** | Target v2.x | Cloud LLM (ref) |
|---|---|---|---|---|
| WER (ALL) | 47–89% | **18.4%** ✅ | ≤ 20% | — |
| WER HN | 47–89% | **29.3%** ⚠️ | ≤ 20% (sau TRAIN-001) | — |
| WER DN/SG | 47–89% | **16.3%** ✅ | ≤ 20% | — |
| Drug Recall (real LB) | 13–18% | **55.6% LB** 🔴 | ≥ 70% (TRAIN-001) | 78% |
| Drug Precision | — | **83.3%** ✅ | ≥ 90% | — |
| Drug Recall (synthetic CONS-002-EVAL) | — | **99.5%** ✅ | ≥ 88% | — |
| Safety Catch (CONS-002-EVAL) | — | **92.1%** ✅ | ≥ 80% | — |
| PhoBERT NER F1 (TRAIN-002 synthetic) | — | **99.44%** ✅ | ≥ 0.85 real | — |
| Tests PASS | 0 | **794/794** ✅ | 100% | — |

> ⚠️ Drug Recall 55.6%LB: BS spell tên thuốc theo phonetic ("mét phốt min") → GT NER miss → actual recall thấp hơn.
> Root cause: PhoWhisper garble phonetic drug names → Layer 3b RAG giúp một phần → TRAIN-001 để giải quyết triệt để.

### Roadmap phases (FID-VN-010 + FID-VN-011 — trạng thái 2026-06-09)

```
Phase 0  ✅ DONE (2026-06-09) — A1+A2+A3+L4-REDESIGN (FID-VN-010)
  src/core/l1a_asr.py  — prompt injection
  src/core/l0_normalize.py  — VAD silence-aware chunking
  src/core/dialect_norm.py  — 200+ entries, region-aware
  src/api/static/index.html  — per-drug mandatory confirm UI

Phase 0.5 ✅ DONE (2026-06-09) — RAG-001+UI-001+FID-VN-011
  src/core/drug_rag.py  — Chroma + MiniLM + hybrid_query_drug()
  src/core/l1b_drug_correct.py  — Layer 3b fallback (FID-VN-011)
  src/api/main.py  — model preload singleton
  src/api/static/js/suggestions.js  — drug chips + dialect badge + terminology sidebar
  data/reference/drug_db_v200.json  — 154 INN
  tests/integration/test_e2e_pipeline.py  — 22 E2E tests

Phase 1  (3–6 tháng)  — TRAIN-001 + PhoBERT production + pilot audio
  PhoWhisper fine-tune trên 50-100h real BS audio (sau pilot Đà Nẵng)
  PhoBERT NER validation trên real audio (hiện: synthetic F1=99.44%)
  ICD-10 Vector RAG (semantic lookup thay substring)

Phase 2  (9–12 tháng) — LoRA PhoWhisper + TT13/2025 compliance
  Qwen2.5-7B LoRA local (thay Groq)
  Chữ ký số BS (TT13/2025 deadline 31/12/2026)
  HL7 v2 + FHIR R4 export
```

---

## 16. TÍCH HỢP KÊNH LIÊN LẠC (M6)

### Dành cho ai: Kỹ thuật

```
ABSTRACTION LAYER — Communication Channel:
  interface CommunicationChannel:
    .send_text(recipient, message)
    .send_file(recipient, file)  ← chỉ Email adapter
    .receive(channel, sender, content) ← inbound

ADAPTERS:
  ZaloAdapter    → Zalo OA SDK (non-medical text)
  EmailAdapter   → SMTP gửi + IMAP nhận auto-process
  SMSAdapter     → Viettel/VNPT gateway [Phase 2]
  PartnerAdapter → Email/Zalo cho đối tác
  TTSAdapter     → gTTS / VinAI TTS → OS audio output

INBOUND EMAIL PROCESSOR:
  Monitor inbox: ketqua@phongkham.vn
  Parse subject → extract tên + ngày sinh
  Match patient trong M1
  Kiểm tra điều kiện (3 điều kiện)
  Upload file → M4
  Notify Staff + Doctor Screen

INBOUND ZALO PARSER:
  Nhận reply từ BN → booking confirm/cancel/reschedule
  Nhận reply từ đối tác → "OK REF-xxx" / "DONE REF-xxx"
  Parse → update M2/M5 accordingly
```

---

## 17. DỮ LIỆU, LƯU TRỮ & TUÂN THỦ PHÁP LUẬT

### Dành cho ai: Kỹ thuật, Pháp lý, Audit

### Dữ liệu lưu ở đâu

```
LAYER 1 — LOCAL (bắt buộc, mọi gói):
  SQLite + WAL + Fernet encryption
  Máy tính phòng khám (on-premise)
  Trách nhiệm lưu trữ: Cơ sở KCB
  Thời gian: 10 năm tối thiểu (TT32/2023)
  Phòng bệnh nhân tử vong: 30 năm

LAYER 2 — VN CLOUD (Gói 2+, optional):
  VNG Cloud / FPT Cloud / VNPT Cloud (VN region only)
  Sync encrypted data — không sync raw audio
  Mục đích: backup + multi-device

TUYỆT ĐỐI KHÔNG:
  ❌ AWS / GCP / Azure (region ngoài VN)
  ❌ Lưu raw audio sau transcription
  ❌ PII raw trong log (chỉ hash)
  ❌ Dữ liệu y tế qua Zalo OA file
```

### Pháp lý áp dụng

| Luật | Yêu cầu | Cách thực thi |
|---|---|---|
| NĐ13/2023 | Data tại VN, consent, mục đích cụ thể | SQLite local + VN Cloud + consent form |
| TT32/2023 | Mẫu bệnh án chuẩn, lưu 10 năm | Mẫu 15/BV-01, SQLite 10 năm |
| Luật KCB Đ.62 | BS ký bệnh án | L4 Human Gate không bypass |
| Luật KCB Đ.80 | Không hoa hồng | M5 chỉ track volume, không ghi tiền |
| TT13/2025 | EMR + chữ ký số + FHIR | Phase 2 roadmap (deadline 31/12/2026) |
| Luật AI 134/2025 | Human oversight + audit | L4 + L10 + conformity 09/2027 |

### Xử lý dữ liệu không được yêu cầu

```
Ví dụ: BN tự gửi ảnh siêu âm mà phòng khám không yêu cầu

LỚP BẢO VỆ 1 — ZALO:
  Zalo OA không cho phép file y tế → block tự nhiên

LỚP BẢO VỆ 2 — EMAIL AUTO-PROCESSOR (có điều kiện):
  CHỈ xử lý auto khi đủ 3 điều kiện:
    ① BN đã đăng ký M1
    ② Có referral ACTIVE
    ③ BN đã ký consent data
  Thiếu → QUARANTINE → Staff quyết định thủ công

LỚP BẢO VỆ 3 — HƯỚNG DẪN BN:
  "Kết quả XN: mang bản giấy ĐẾN PHÒNG KHÁM
   hoặc gửi email CHỈ KHI phòng khám cung cấp mã REF"
  Không có mã REF → không trigger auto-process

LỚP BẢO VỆ 4 — POLICY PHÒNG KHÁM:
  Phòng khám có thể cấu hình: "KHÔNG nhận file email"
  → Toàn bộ email đính kèm → quarantine
  Trách nhiệm email server: cơ sở KCB (không phải MediVoice)
```

---

## 18. KIẾN TRÚC TÍCH HỢP & THIẾT BỊ

### Dành cho ai: Kỹ thuật, IT triển khai

### Thiết bị vật lý — Plug & Play

```
AUDIO INPUT:
  ✅ USB mic cắm vào máy tính (ưu tiên, ổn định nhất)
  ✅ Bluetooth wireless mic (BS di chuyển trong phòng)
  ✅ Điện thoại BS (MediaRecorder API qua browser PWA)
  ✅ Mic tích hợp laptop/tablet
  Config: nhận từ default audio device của OS

AUDIO OUTPUT — TTS LOA:
  ✅ Loa USB cắm máy tính
  ✅ Loa Bluetooth
  ✅ Loa rời jack 3.5mm
  ✅ Loa tích hợp máy tính
  System: TTS tạo WAV → OS audio output API

MÀN HÌNH PHÒNG CHỜ:
  ✅ TV qua HDMI từ máy tính phụ
  ✅ TV qua mạng LAN nội bộ (browser → URL local)
  ✅ Tablet gắn tường (browser PWA full-screen)
  Setup: browser → http://192.168.1.x/queue-display
         Auto-refresh 5 giây, không cài app thêm

MÁY IN:
  ✅ Máy in USB → giấy chỉ định, đơn thuốc PDF
  ✅ Máy in label → QR thẻ bệnh nhân
  OS print API → không cần driver đặc biệt
```

### Plugin Adapter Pattern

```
CORE SYSTEM
    │
    ├── Integration Gateway
    │         │
    ├── ZaloAdapter      → Zalo OA SDK
    ├── EmailAdapter     → SMTP + IMAP
    ├── SMSAdapter       → Viettel/VNPT SMS [Ph.2]
    ├── WebsiteAdapter   → REST API + Widget Embed
    ├── TTSAdapter       → gTTS / VinAI TTS offline
    ├── PrintAdapter     → OS print API
    ├── AccountingAdapter→ MISA/Fast API + CSV Export
    ├── HL7Adapter       → HL7 v2 [Ph.2]
    ├── FHIRAdapter      → FHIR R4 [Ph.2]
    └── PartnerAdapter   → Email + Zalo keyword parser

Thêm adapter mới: tạo file adapter_xxx.py + register
Không sửa core system.
```

### Bảng tích hợp theo Phase

| Kết nối | Ph.0 | Ph.1 | Ph.2 | Ph.3 |
|---|---|---|---|---|
| USB/BT mic | ✅ | ✅ | ✅ | ✅ |
| Màn hình phòng chờ (LAN) | ✅ | ✅ | ✅ | ✅ |
| Loa TTS | ✅ | ✅ | ✅ | ✅ |
| Máy in USB | ✅ | ✅ | ✅ | ✅ |
| Email SMTP/IMAP | ✅ | ✅ | ✅ | ✅ |
| Zalo OA | ❌ | ✅ | ✅ | ✅ |
| SMS Gateway | ❌ | ✅ | ✅ | ✅ |
| Website Widget + API | ❌ | ✅ | ✅ | ✅ |
| Kế toán API (MISA...) | ❌ | ✅ | ✅ | ✅ |
| HL7 v2 HIS | ❌ | ❌ | ✅ | ✅ |
| FHIR R4 | ❌ | ❌ | ✅ | ✅ |
| IVR Phone | ❌ | ❌ | ❌ | ✅ |
| WhatsApp / Facebook | ❌ | ❌ | ❌ | ✅ |
| VoIP Call Recording | ❌ | ❌ | ❌ | ✅ |
| VNeID API | ❌ | ❌ | ❌ | ✅ |
| BHYT eGov | ❌ | ❌ | ❌ | ✅ |

---

## 19. LỘ TRÌNH TRIỂN KHAI — 4 PHASE

### Dành cho ai: Ban lãnh đạo, Kinh doanh, Kỹ thuật

```
PHASE 0 — MVP ✅ KỸ THUẬT HOÀN THÀNH (2026-06-09 · v0.10.1)
  Mục tiêu: 5 BS trả tiền
  Pilot: Đà Nẵng (Andy) + Sài Gòn (BS partner)

  Kỹ thuật đã hoàn thành (794/794 tests PASS):
  ✅ AI Pipeline L0→L10 (794 tests PASS — E2E tested)
  ✅ Mẫu 15/BV-01 (lam_sang route) — VN-ROUTER-001 + VN-NER-002 DONE
  ✅ M1 cơ bản, M3 thu chi, PDF
  ✅ Queue management + TTS
  ✅ Mode A (BS làm một mình)
  ✅ VN-ROUTER-001: NER→Mẫu 15/BV-01 direct — DONE (FID-VN-004)
  ✅ BENCH-002b: WER=18.4%ALL / 16.3%DN+SG / 29.3%HN — DONE 2026-06-09
  ✅ DEPLOY-001: install.bat + start.bat + check_env — DONE
  ✅ Phase 0 AI enhancements: A1 Prompt Injection + A2 VAD + A3 Dialect — DONE
  ✅ Phase 0.5 RAG: drug_rag.py hybrid + UI-SUGGEST-001 + FID-VN-011 — DONE

  Phase 0.6 — DVP Layer 1+2 ✅ DONE (FID-VN-012 v0.11.0 · 2026-06-09):
  ✅ DVP Layer 1: DoctorProfile (region + specialty metadata) — src/models/doctor_profile.py
  ✅ DVP Layer 2: 12 specialty vocab packs (link vào A1+A3) — SPECIALTY_DRUG_CLASSES l1a_asr.py
  ✅ DB: doctor_profiles + doctor_aliases tables — l7_storage.py CRUD
  ✅ Pipeline: specialty→L1a A1 + region→A3 dialect norm per doctor
  ✅ API: POST /api/doctors · GET · aliases/pending · aliases/confirm
  ✅ Layer 3 schema: dvp_alias.py (promote logic) — pilot-gated
  ⏳ DVP Layer 3: Personal alias passive learning — cần ≥5 sessions pilot data

  KPIs Phase 0 (đo sau pilot):
    WER actual: 18.4% ✅ (target <30%) | Drug Recall: 55.6%LB 🔴 (target ≥70%)
    BS approve rate > 85% | NPS > 7/10 | 5 BS paying users

─────────────────────────────────────────────────────

PHASE 1 — Complete Product (3–9 tháng sau Phase 0)
  Mục tiêu: 50–200 phòng mạch

  Modules mới:
  M2: Booking engine đầy đủ + reminder chuẩn
  M4: Email auto-processor + kết quả XN
  M5: Referral 2 chiều (Gói 3)
  M6: Zalo OA + email routing đúng luật
  M7: VN Cloud sync (VNG/FPT/VNPT)
  M8: Plugin CĐHA (FID-VN-001) + Nha khoa (FID-VN-002)

  Tính năng mới:
  Staff Screen (Mode B) — màn hình trợ lý riêng
  Website widget + REST API booking
  Post-care CRM D+2/D+4/D+7
  Partner commission tracking (M5 đầy đủ)
  Báo cáo xuất Excel + kế toán API

─────────────────────────────────────────────────────

PHASE 2 — Compliance & Scale (2027)
  Mục tiêu: TT13/2025 compliance, 500+ phòng

  Kỹ thuật:
  Chữ ký số bác sĩ (TT13/2025 deadline 31/12/2026)
  HL7 v2 export (HIS integration)
  FHIR R4 export (BYT mandate)
  M9: BravoSoft, FPT.eHospital API
  Audit export chuẩn cho BYT thanh tra

  Pháp lý:
  Luật AI 134/2025 conformity assessment
  Budget: 80–200M VND (trước 01/09/2027)

─────────────────────────────────────────────────────

PHASE 3 — Platform (2027–2028)
  VNeID API integration (khi BYT publish)
  BHYT eligibility check real-time
  IVR phone booking
  WhatsApp/Facebook channel
  FPT/Viettel partnership (plugin/add-on)
  BYT Central Registry sync
```

---

## 20. SO SÁNH TÍNH NĂNG THEO GÓI

### Dành cho ai: Kinh doanh, Khách hàng

| Tính năng | Gói 1 | Gói 2 | Gói 3 |
|---|---|---|---|
| **Giá** | 500k–1M/tháng | 2–3M/tháng | 4–8M/tháng |
| **AI Voice → Mẫu 15/BV-01** | ✅ | ✅ | ✅ |
| **PDF đơn thuốc + bệnh án** | ✅ | ✅ | ✅ |
| **Hồ sơ bệnh nhân cơ bản** | ✅ | ✅ | ✅ |
| **Thu chi đơn giản (voice)** | ✅ | ✅ | ✅ |
| **Queue + TTS loa** | ✅ | ✅ | ✅ |
| **Doctor Pre-visit Briefing** | ✅ | ✅ | ✅ |
| **Giấy chỉ định XN/CĐHA** | ✅ | ✅ | ✅ |
| **Chạy offline 100%** | ✅ | ✅ | ✅ |
| **Hồ sơ BN đầy đủ + QR** | ❌ | ✅ | ✅ |
| **CCCD scan auto-fill** | ❌ | ✅ | ✅ |
| **Đặt lịch online (M2)** | ❌ | ✅ | ✅ |
| **Reminder D-1, H-2, H-15p** | ❌ | ✅ | ✅ |
| **Buffer + Waitlist** | ❌ | ✅ | ✅ |
| **Upload kết quả XN (M4)** | ❌ | ✅ | ✅ |
| **Email auto kết quả** | ❌ | ✅ | ✅ |
| **Zalo OA nhắc lịch** | ❌ | ✅ | ✅ |
| **After-care CRM D+2/D+4** | ❌ | ✅ | ✅ |
| **VN Cloud sync (M7)** | ❌ | ✅ | ✅ |
| **Website widget booking** | ❌ | ✅ | ✅ |
| **Staff Screen riêng** | ❌ | ✅ | ✅ |
| **Báo cáo + xuất Excel** | ❌ | ✅ | ✅ |
| **Referral 2 chiều (M5)** | ❌ | ❌ | ✅ |
| **Commission tracking** | ❌ | ❌ | ✅ |
| **Plugin CĐHA (M8)** | ❌ | ❌ | ✅ |
| **Plugin Nha khoa (M8)** | ❌ | ❌ | ✅ |
| **HIS integration (M9)** | ❌ | ❌ | ✅ |
| **Kế toán API** | ❌ | ❌ | ✅ |
| **Multi-role (Doctor/Staff/Cashier)** | ❌ | ❌ | ✅ |
| **Audit export BYT** | ❌ | ❌ | ✅ |

---

## 21. PHỤ LỤC: THUẬT NGỮ & PHÁP LÝ

### Dành cho ai: Tất cả

### Thuật ngữ kỹ thuật

| Thuật ngữ | Giải thích |
|---|---|
| AI Pipeline L0→L10 | Chuỗi 11 bước xử lý từ audio đến bệnh án |
| PhoWhisper | Model nhận dạng giọng nói tiếng Việt (VinAI, offline) |
| NER | Named Entity Recognition — nhận dạng thực thể y tế |
| ICD-10-VN | Mã phân loại bệnh quốc tế phiên bản Việt Nam |
| Mẫu 15/BV-01 | Biểu mẫu bệnh án ngoại trú chuẩn (TT32/2023) |
| Fernet | Thuật toán mã hoá dữ liệu tại chỗ |
| SQLite WAL | Cơ sở dữ liệu local với Write-Ahead Logging |
| L4 Human Gate | Cổng bắt buộc BS phê duyệt trước khi lưu |
| L10 Audit Log | Nhật ký kiểm tra bất biến (SHA-256 hash chain) |
| TTS | Text-to-Speech — đọc text thành giọng nói |
| Queue | Hàng chờ bệnh nhân với số thứ tự |
| Referral | Giới thiệu bệnh nhân đến/từ cơ sở khác |
| PWA | Progressive Web App — chạy trên browser, offline được |
| Mode A/B/C | Chế độ vận hành không/có/nhiều trợ lý |

### Viết tắt pháp lý

| Viết tắt | Đầy đủ |
|---|---|
| NĐ13/2023 | Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân |
| TT32/2023 | Thông tư 32/2023/TT-BYT về biểu mẫu bệnh án |
| TT13/2025 | Thông tư 13/2025/TT-BYT về hồ sơ bệnh án điện tử |
| Luật AI 134 | Luật Công nghệ AI 134/2025/QH15 |
| Luật KCB 2023 | Luật Khám bệnh, chữa bệnh 15/2023/QH15 |
| CCHN | Chứng chỉ hành nghề khám chữa bệnh |
| GPHN | Giấy phép hành nghề |
| BHYT | Bảo hiểm y tế |
| SaMD | Software as Medical Device — Phần mềm thiết bị y tế |
| EMR | Electronic Medical Record — Hồ sơ bệnh án điện tử |
| HIS | Hospital Information System — Hệ thống thông tin bệnh viện |
| FHIR | Fast Healthcare Interoperability Resources — chuẩn trao đổi dữ liệu y tế |
| HL7 v2 | Health Level 7 version 2 — chuẩn tích hợp HIS tại VN |
| CĐHA | Chẩn đoán hình ảnh (X-quang, siêu âm, CT, MRI) |

### Điểm tuân thủ quan trọng nhất

```
1. KHÔNG bypass L4 Human Gate — BS PHẢI phê duyệt mọi bệnh án
2. Data LUÔN ở VN — không cloud nước ngoài
3. KHÔNG ghi tiền commission — chỉ track volume
4. KHÔNG gửi file y tế qua Zalo OA
5. Audio RAW xoá ngay sau khi transcribe
6. Disclaimer BẮT BUỘC trên mọi output:
   "AI tạo nháp — Bác sĩ chịu trách nhiệm hoàn toàn"
7. Conformity assessment Luật AI 134 trước 01/09/2027
```

---

## 21. DEMO APP — STREAMLIT PILOT DATA COLLECTION

### Dành cho ai: Kỹ thuật, Kinh doanh

### Mục đích

```
Demo App KHÔNG phải sản phẩm cuối.
Mục tiêu: thu audio BS thật tại phòng khám VN → training data cho TRAIN-001.

1. BS nói về ca khám → Groq Whisper transcribe → LLM Groq NER → Mẫu 15/BV-01 draft
2. BS review từng field + xác nhận từng thuốc (L4 gate)
3. Lưu: Google Drive (audio WAV + session JSON) hoặc local_saves/
4. Đánh giá độ chính xác AI (1-5 per field) → dataset quality labels

Pilot data 2026-06-08: 9 WAV + 10 JSON tại DN/SG
  → data/drive-download-20260609T031416Z-3-001/
```

### Kiến trúc

```
demo/app.py          ← Streamlit UI chính (Mẫu 15/BV-01 layout)
demo/rag_chain.py    ← RAG pipeline: Groq Whisper + L1b + ICD lookup
demo/requirements.txt← deps Streamlit Cloud
demo/local_saves/    ← fallback lưu local nếu Google Drive chưa cấu hình

Import chain:
  demo/app.py → demo/rag_chain.py → src.core.l1b_drug_correct (RAG)
  Fallback: nếu src import lỗi → gọi Groq LLM trực tiếp qua requests

Secrets (gitignored .streamlit/secrets.toml):
  groq_api_key      = "gsk_..."
  drive_folder_id   = "1YlFmNcusVgRwA4ObwtBJej19ZcyzrzqL"
  gcp_service_account = { ... }  ← chỉ cần khi upload Google Drive
```

### UI Layout — Mẫu 15/BV-01

```
HEADER: 🎙️ MediVoice VN | Badge DEMO v2.0
DISCLAIMER: ⚠️ AI tạo nháp — BS chịu trách nhiệm hoàn toàn

SIDEBAR: Test Mode (script selection — DVP calibration)

─── THÔNG TIN PHIÊN KHÁM ─────────────────────────
  Tên BS ★ | Cơ sở ★ | CCHN ★ | Chuyên khoa | Ngày
  Tên BN demo (tên giả — KHÔNG nhập thật)

─── GHI ÂM ────────────────────────────────────────
  [Script chuẩn / Tự nhiên] — radio
  st.audio_input → WAV → hash guard → Groq ASR → NER

─── TRANSCRIPT BOX ────────────────────────────────
  Transcript gốc (màu xanh lá)
  Confidence bar
  Drug flags ⚠️ nếu có

─── MẪU 15/BV-01 DRAFT ──────────────────────────
  I.  Thông tin BN: tên / tuổi / giới / năm sinh / SĐT / CCCD
  II. Lý do khám / Triệu chứng chính
  III. Sinh hiệu: HA | Mạch | Nhiệt độ | Cân nặng
  IV. Chẩn đoán ★ + ICD-10-VN ★ + Tái khám
  V.  Đơn thuốc — L4 Human Gate:
      💊 Thuốc 1 — hàm lượng · liều · ngày  [✓ checkbox]
      ⚠️ Thuốc 2 (flagged) — nghe: X · Y% [✓ checkbox]
      ← disabled PHÊ DUYỆT until ALL checkboxes ✓

─── ĐÁNH GIÁ TRANSCRIPT ───────────────────────────
  Slider 1-5 per field: transcript, tên, tuổi, ngày, sinh hiệu, CĐ, thuốc, tái khám

─── NOTES ─────────────────────────────────────────
  Giọng vùng miền | Môi trường | Đặc điểm BS | Ghi chú sửa lỗi

─── ACTIONS ───────────────────────────────────────
  [✅ Phê duyệt & Lưu]   [❌ Từ chối]
  → Drive: audio WAV + session JSON
  → Fallback: demo/local_saves/
  → Download buttons: JSON + WAV
```

### Triển khai

```
LOCAL:
  demo_start.bat → streamlit run demo/app.py --server.port 8501
  + localtunnel: npx --yes localtunnel --port 8501 → global URL tạm thời
  Lần đầu visit global URL → nhập IP máy tính (194.34.105.20) làm password

STREAMLIT CLOUD:
  URL: https://medivoice-vn-demo.streamlit.app/
  Branch: master | Main file: demo/app.py
  Auto-redeploy: mỗi push lên GitHub
  Secrets: thêm thủ công trong dashboard (không commit vào git)
    groq_api_key = "gsk_..."
    drive_folder_id = "1Yl..."
    [gcp_service_account] = { ... }
  Sleep: 7 ngày không dùng → ngủ → push commit để wake

ISO GAP (đã khắc phục 2026-06-09):
  Lý do gap: demo/app.py được build qua 27+ commits (nhiều phiên) không có FID
  Fix: BACKLOG DEMO-001 + §21 DESIGN_REPORT (file này)
```

### Giới hạn DEMO

```
NOT production:
  - Groq API: cloud (data ngoài VN) — chỉ dùng cho demo/training
  - Production sẽ dùng PhoWhisper offline (NĐ13/2023 compliant)
  - Database: Google Drive + local_saves (không SQLite+Fernet)
  - Không có L10 audit log, không có L7 encrypted storage

Data handling:
  - BS dùng tên giả cho BN → không vi phạm NĐ13/2023
  - Audio/JSON upload Google Drive → chỉ training data, không bệnh án thật
  - BS đã ký BS_ONBOARDING_CHECKLIST + DPA trước khi dùng demo
```

---

## CHANGELOG BÁO CÁO THIẾT KẾ

| Version | Ngày | Thay đổi |
|---|---|---|
| v1.0 | 2026-06-03 | Bản thiết kế gốc (VISION + BRS + PROJECT_KICKOFF) |
| v1.1 | 2026-06-06 | **Major update từ session design review:**<br>• Thêm Queue Management System + TTS loa<br>• Thêm 2 chế độ vận hành (Mode A/B/C)<br>• Thêm Doctor Pre-visit Briefing<br>• Thêm Post-care CRM (D+2/D+4/D+7)<br>• Thêm Referral 2 chiều + Retest flow<br>• Thêm Staff Confirm Gate<br>• Cập nhật kênh liên lạc (Zalo/Email phân tách)<br>• Thêm Email auto-processor + điều kiện 3 lớp<br>• Thêm Booking engine chuẩn (7 states + buffer)<br>• Thêm Integration Gateway + adapter pattern<br>• Cập nhật M5 commission tracking đúng luật<br>• Thêm Website widget + REST API booking<br>• Thêm kế toán API gateway<br>• Làm rõ data compliance 3 lớp bảo vệ |
| v2.0 | 2026-06-09 | **§15 AI Pipeline rewrite — FID-VN-010 + BENCH-002b:**<br>• L0: VAD silence-aware chunking (silero-vad)<br>• L1a: Prompt Injection (initial_prompt drug list per specialty)<br>• Post-ASR: Dialect normalization (200+ entries, region-aware)<br>• L1b: "Layer 5 RAG" concept draft (thresholds chưa calibrated)<br>• L4: Per-drug mandatory confirm safety redesign<br>• Performance benchmarks từ BENCH-002b evidence |
| v2.1 | 2026-06-09 | **§15 sync với code thật — FID-VN-011 + DRUG-DB-002 + FID-VN-009:**<br>• L1b: Layer 5 → **Layer 3b** (tên đúng với code)<br>• L1b: Threshold 0.80 → **0.68 accept / 0.55 flag** (calibrated)<br>• L1b: Hybrid query **0.65×fuzzy + 0.35×RAG** (logic thật)<br>• L1b: Model preload singleton (_embed_model + _drug_collection startup)<br>• L1b: drug_db_v200 **154 INN** (DRUG-DB-002 +8 drugs)<br>• L1c: PhoBERT **PARALLEL + early-exit** (thay shadow mode)<br>• Benchmarks: cập nhật v2.1 actual từ BENCH-002b real voice<br>• Roadmap: Phase 0 ✅ + Phase 0.5 ✅ đánh dấu DONE với file paths |
| v2.2 | 2026-06-09 | **§15+§19 DVP Layer 1+2 DONE — FID-VN-012 v0.11.0:**<br>• Roadmap: Phase 0.6 DVP L1+2 ✅ DONE (⏳→✅)<br>• DVP: DoctorProfile model · doctor_profiles+doctor_aliases tables<br>• DVP: SPECIALTY_DRUG_CLASSES 12 canonical (cdha/mat/noi_tiet/than_tiet_nieu mới)<br>• DVP: Pipeline injection specialty→L1a + region→A3 per doctor<br>• DVP Layer 3: dvp_alias.py schema (pilot-gated, ⏳ cần ≥5 sessions)<br>• VIETMED-FIX-001: download_vietmed.py trust_remote_code → HF_TOKEN |
| v2.3 | 2026-06-09 | **§21 Demo App — ISO gap fix DEMO-001:**<br>• Thêm §21 Demo App (Streamlit pilot collection — 27+ commits chưa có FID)<br>• demo/app.py v2.0: audio hash guard (fix form không hiện) + Mẫu 15/BV-01 UI redesign<br>• UI: I.Hành chính → II.Lý do → III.Sinh hiệu → IV.CĐ+ICD → V.Đơn thuốc L4 gate<br>• BACKLOG DEMO-001 entry added |

---

*DS-VN-REC-20260606-001 | Design Report v2.1*
*Prepared by: Claude Sonnet 4.6 | Owner: Andy Phan — Maple Leaf Group*
*Created: 2026-06-06 | Last updated: 2026-06-09 | Status: LIVING DOCUMENT*
*ISO/IEC 42001:2023 | ISO 9001:2015 | TT32/2023 | NĐ13/2023*
