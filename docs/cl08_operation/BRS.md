# BRS.md | DS-VN-CL08-BRS | Business Requirements Specification
# ISO/IEC/IEEE 29148:2018 | v0.2.0 | MediVoice VN
# Updated: 2026-06-03 | Owner: MLG

---

## BUSINESS CONTEXT

**Problem:**
Bác sĩ và nhân viên y tế tại phòng mạch tư nhân Việt Nam phải ghi chép hồ sơ
bệnh án thủ công — gõ tay hoặc viết vào sổ giấy. Không có sản phẩm nào tự động
hoá luồng "bác sĩ nói → bệnh án điện tử chuẩn TT32/2023" cho phòng mạch nhỏ.

**Khác biệt cốt lõi với MediVoice CA:**
- VN không có bác sĩ gia đình — bệnh nhân tự đến chuyên khoa
- Output: Mẫu 15/BV1 tiếng Việt (không phải SOAP tiếng Anh)
- ICD-10-VN bắt buộc (QĐ5837/BYT)
- Data residency bắt buộc tại VN (NĐ13/2023)
- Phòng mạch tư nhỏ: 1–3 BS, ít hoặc không có nhân viên

**Value:**
MediVoice VN giúp phòng mạch tư tiết kiệm 5–10 giờ ghi chép/ngày,
tuân thủ TT13/2025 (deadline 31/12/2026) và xây dựng hồ sơ bệnh nhân
số hoá từ hôm nay — trước khi BYT bắt buộc.

---

## BUSINESS OBJECTIVES

| ID | Objective | Priority | Success Metric | Phase |
|---|---|---|---|---|
| BO-VN-001 | Giảm thời gian ghi chép | Must Have | < 2 phút/ca thay vì 5–10 phút | 0 |
| BO-VN-002 | ASR tiếng Việt y tế | Must Have | CEER < 5% cho tên thuốc + liều + chẩn đoán | 0 |
| BO-VN-003 | Code-switching VI+EN | Must Have | Nhận diện đúng > 90% tên thuốc EN trong câu VN | 0 |
| BO-VN-004 | Output chuẩn Mẫu 15/BV1 | Must Have | BS chấp nhận > 85% không sửa nhiều | 0 |
| BO-VN-005 | ICD-10-VN tự động | Must Have | Chẩn đoán có mã ICD-10-VN đúng > 90% | 0 |
| BO-VN-006 | Offline hoàn toàn | Must Have | Full flow không cần internet | 0 |
| BO-VN-007 | Human approval gate | Must Have | 100% hồ sơ phải có BS approve trước khi lưu | 0 |
| BO-VN-008 | NĐ13/2023 compliant | Must Have | 0 vi phạm data residency | 0 |
| BO-VN-009 | Quản lý bệnh nhân | Should Have | Lịch sử BN, CCCD scan, tái khám | 1 |
| BO-VN-010 | Appointment booking | Should Have | BN book online, QR check-in | 1 |
| BO-VN-011 | Thu chi đơn giản | Should Have | Voice log thu/chi, báo cáo cuối ngày | 1 |
| BO-VN-012 | Zalo notification | Should Have | Reminder tái khám, share đơn thuốc | 1 |
| BO-VN-013 | HL7 v2 export | Should Have | Integrate với HIS có sẵn | 1 |
| BO-VN-014 | Plugin CĐHA | Should Have | BS siêu âm tiết kiệm > 60% thời gian | 1 |
| BO-VN-015 | TT13/2025 compliance | Must Have | Chữ ký số + FHIR R4, deadline 31/12/2026 | 2 |
| BO-VN-016 | Luật AI 134 | Must Have | Conformity assessment trước 01/09/2027 | 2 |

---

## USER STORIES

### Nhóm A: BS Lâm Sàng Phòng Mạch Tư (Target Phase 0)

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| US-VN-001 | BS lâm sàng phòng mạch tư | Nói vào mic trong lúc khám | MediVoice tự điền Mẫu 15/BV1 — không gõ máy |
| US-VN-002 | BS phòng mạch | Xem lại và chỉnh sửa draft trước khi ký | Đảm bảo chính xác — AI chỉ là nháp |
| US-VN-003 | BS phòng mạch | In đơn thuốc PDF gửi qua Zalo | Bệnh nhân nhận đơn ngay không cần tờ giấy |
| US-VN-004 | BS phòng mạch | Tái kê đơn cũ cho bệnh mãn tính | Không phải viết lại toàn bộ từ đầu |
| US-VN-005 | BS phòng mạch | Nói "Thu 200k bệnh nhân Lan" | App ghi doanh thu không cần dừng tay |

### Nhóm B: Nhân Viên / Trợ Lý (Phase 1)

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| US-VN-006 | Trợ lý phòng mạch | Nói hỏi bệnh nhân rồi app tự điền | Không gõ tay form tiếp nhận |
| US-VN-007 | Trợ lý | Quét CCCD bệnh nhân bằng camera | Thông tin tự điền, không nhập tay |
| US-VN-008 | Trợ lý | Xem danh sách bệnh nhân hôm nay | Biết ai đang chờ, ai đã khám xong |

### Nhóm C: Bệnh Nhân (Phase 1 — Gói 2)

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| US-VN-009 | Bệnh nhân | Book lịch khám online qua Zalo | Không phải gọi điện, không chờ ngoài cửa |
| US-VN-010 | Bệnh nhân | Nhận nhắc tái khám qua Zalo | Không quên lịch hẹn |
| US-VN-011 | Bệnh nhân | Check-in bằng QR khi đến | Không phải điền form lại từ đầu |

### Nhóm D: Chủ Phòng Khám (Phase 1–2)

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| US-VN-012 | Chủ phòng khám | Xem doanh thu ngày/tháng | Biết phòng khám đang làm ăn thế nào |
| US-VN-013 | Chủ phòng khám | Có EMR sẵn sàng TT13/2025 | Phòng khám không bị phạt sau 31/12/2026 |
| US-VN-014 | Chủ phòng khám | Audit trail đầy đủ | Sẵn sàng cho thanh tra BYT |

---

## CONSTRAINTS

| Type | Constraint |
|---|---|
| **Pháp lý — Data** | NĐ13/2023: Data BN PHẢI lưu tại VN — không cloud nước ngoài |
| **Pháp lý — Format** | TT32/2023: Output PHẢI theo Mẫu 15/BV1 — không tự do format |
| **Pháp lý — EMR** | TT13/2025: Chữ ký số + FHIR (deadline 31/12/2026) |
| **Pháp lý — AI** | Luật AI 134/2025: Human oversight bắt buộc — L4 không bypass |
| **Pháp lý — Hành nghề** | Luật KCB 2023 Đ.14: Chỉ phục vụ cơ sở KCB đăng ký BYT |
| **Pháp lý — Hoa hồng** | Luật KCB 2023 Đ.80: Referral KHÔNG ghi tiền/phần trăm |
| **Pháp lý — NOT SaMD** | TT46/2017: Chỉ transcription — không chẩn đoán — không đăng ký BYT |
| **Kỹ thuật** | 100% offline — không cloud dependency cho core features |
| **Kỹ thuật** | Latency: < 5 giây perceived (streaming chunk 10s) |
| **Kỹ thuật** | CEER < 5% cho tên thuốc, liều lượng, chẩn đoán |
| **Y tế** | Tên thuốc giữ nguyên tiếng Anh — không dịch, không sửa |
| **Y tế** | ICD-10-VN bắt buộc trong Chẩn đoán (QĐ5837) |
| **Ngân sách** | Phase 0 bootstrapped — $0 cloud API cost |
| **Pháp lý — AI Budget** | Conformity assessment 80–200M VND trước 01/09/2027 |

---

## LUỒNG / FLOWS

| Flow | Tên | Phase | Mô tả |
|---|---|---|---|
| **VN-FLOW-MAIN** | **Lâm sàng ngoại trú** | **0 — NGAY** | BS nói → Mẫu 15/BV1 + đơn thuốc → BS ký |
| VN-FLOW-CDHA | Báo cáo CĐHA | 1 | BS siêu âm/X-quang đọc → báo cáo có cấu trúc → BS ký |
| VN-FLOW-NHA | Bệnh án Nha khoa | 1 | BS nha đọc → Mẫu 16/BV1 + sơ đồ răng → BS ký |
| VN-FLOW-TMH | Tai mũi họng | 2 | Plugin chuyên khoa |
| VN-FLOW-SAN | Sản khoa | 2 | Mẫu 05/BV1 |

---

## OUTPUT FORMAT — MẪU 15/BV1 (CORE)

```
┌─────────────────────────────────────────────────────────────┐
│  PHẦN I: HÀNH CHÍNH                                        │
│  Họ tên BN | Ngày sinh | Giới tính | Dân tộc              │
│  Địa chỉ | SĐT                                             │
│  CCCD (optional) | BHYT (optional)                         │
│  Tên phòng mạch | BS điều trị | Ngày khám                 │
│                                                             │
│  PHẦN II: LÂM SÀNG                                         │
│  Lý do đến khám: [từ giọng nói]                            │
│  Bệnh sử: [từ giọng nói]                                   │
│  Tiền sử: [dị ứng thuốc + bệnh nền]                       │
│  Khám lâm sàng: [sinh hiệu + khám cơ quan]                │
│  Cận lâm sàng: [kết quả XN + CĐHA nếu có]                 │
│  Chẩn đoán: [bệnh chính] — ICD-10-VN: [mã auto]          │
│  Hướng điều trị:                                           │
│    1. [Tên thuốc] [liều] × [số lần]/ngày × [số ngày]      │
│    2. ...                                                   │
│  Tái khám: [ngày]                                          │
│  Bác sĩ ký: ___ [timestamp audit]                         │
└─────────────────────────────────────────────────────────────┘
```

---

## PATIENT DATA MODEL (VNeID-Ready)

```python
patient = {
    "id": str,                    # local UUID
    "name": str,                  # họ tên đầy đủ
    "dob": date,                  # ngày sinh
    "gender": str,                # nam/nữ/khác
    "phone": str,                 # SĐT
    "address": str,               # địa chỉ
    "vneid_number": str | None,   # CCCD 12 số (nullable)
    "bhyt_code": str | None,      # mã BHYT (nullable)
    "bhyt_expiry": date | None,   # hết hạn BHYT
    "legacy_id": str | None,      # ID cũ / hộ chiếu
    "id_verified": bool,          # đã verify VNeID?
    "drug_allergy": list[str],    # dị ứng thuốc
    "chronic_conditions": list[str],  # bệnh mãn tính
    "created_at": datetime,
    "facility_id": str            # phòng mạch nào
}

facility = {
    "id": str,
    "name": str,
    "byt_registration_number": str,   # số giấy phép KCB
    "doctor_cchn": str,               # CCHN bác sĩ
    "tax_code": str | None,
    "province_code": str,             # mã tỉnh/thành
    "specialty": list[str],
    "tier": str                       # phong_mach / phong_kham / cdha
}
```

---

## QUALITY ATTRIBUTES

| Attribute | Requirement |
|---|---|
| Accuracy (CEER) | < 5% error trên tên thuốc, liều lượng, chẩn đoán |
| Latency | < 5 giây perceived (streaming chunk 10s) |
| Availability | 100% offline — không phụ thuộc cloud |
| Security | Fernet encryption at rest; data không rời VN |
| Compliance | Mẫu 15/BV1 TT32/2023; ICD-10-VN; NĐ13/2023 |
| Auditability | L10 immutable audit log — timestamp + BS_ID + hash |
| Usability | Setup < 30 phút; không cần training đặc biệt |
| Storage | Hỗ trợ lưu trữ 10+ năm (TT32/2023) |

---

*DS-VN-CL08-BRS | MediVoice VN v0.2.0 | ISO/IEC/IEEE 29148:2018 | 2026-06-03*
