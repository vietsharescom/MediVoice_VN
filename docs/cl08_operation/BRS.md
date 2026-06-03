# BRS.md | DS-VN-CL08-BRS | Business Requirements Specification
# ISO/IEC/IEEE 29148:2018 | v1.0 | MediVoice VN
# Created: 2026-06-03 | Owner: Andy Phan — Maple Leaf Group

---

## BUSINESS CONTEXT

**Problem:**
Bác sĩ và nhân viên y tế tại phòng khám tư Việt Nam phải ghi chép hồ sơ bệnh án
thủ công — gõ tay hoặc đọc cho thư ký gõ. Không có sản phẩm AI nào tự động hóa
luồng "bác sĩ nói → bệnh án điện tử chuẩn TT32/2023" tại Việt Nam.

**Khác biệt cốt lõi với MediVoice CA:**
- VN không có bác sĩ gia đình — bệnh nhân tự đến chuyên khoa/bệnh viện
- Output: bệnh án TT32/2023 tiếng Việt (không phải SOAP tiếng Anh)
- ICD-10-VN bắt buộc trong phần Chẩn đoán (QĐ5837/BYT)
- Data residency bắt buộc tại VN (NĐ13/2023)
- Nhiều vai trò ghi vào 1 hồ sơ: điều dưỡng, BS lâm sàng, BS CĐHA, thư ký

**Value:**
MediVoice VN tự động sinh bệnh án điện tử chuẩn TT32/2023 từ giọng nói bác sĩ,
giúp phòng khám tư tuân thủ TT13/2025 (deadline 31/12/2026) và tiết kiệm 5–10
giờ/ngày cho mỗi bác sĩ.

---

## BUSINESS OBJECTIVES

| ID | Objective | Priority | Success Metric | Phase |
|---|---|---|---|---|
| BO-VN-001 | Giảm thời gian ghi chép bệnh án | Must Have | < 3 phút/ca thay vì 15–30 phút | 1 |
| BO-VN-002 | ASR tiếng Việt y tế | Must Have | WER < 20% trên medical speech VN | 1 |
| BO-VN-003 | Code-switching VI+EN | Must Have | Nhận diện đúng > 90% câu trộn VI+EN | 1 |
| BO-VN-004 | Output chuẩn TT32/2023 | Must Have | BS chấp nhận > 85% không sửa nhiều | 1 |
| BO-VN-005 | ICD-10-VN tự động | Must Have | Chẩn đoán có mã ICD-10-VN đúng > 90% | 1 |
| BO-VN-006 | Offline hoàn toàn | Must Have | Full flow không cần internet | 1 |
| BO-VN-007 | Báo cáo CĐHA tự động | Must Have | BS siêu âm tiết kiệm > 60% thời gian đọc kết quả | 1 |
| BO-VN-008 | Human approval gate | Must Have | 100% bệnh án phải có BS ký trước khi lưu | 1 |
| BO-VN-009 | NĐ13/2023 compliant | Must Have | 0 vi phạm data residency | 1 |
| BO-VN-010 | HL7 FHIR export | Should Have | Export chuẩn HL7 FHIR r4 | 1 (TT13/2025) |
| BO-VN-011 | Chữ ký số integration | Should Have | Tích hợp với VNPT-CA hoặc Viettel-CA | 1 |
| BO-VN-012 | Nha khoa plugin | Should Have | Mẫu 16/BV1 + sơ đồ răng FDI | 1 |
| BO-VN-013 | EHR integration | Nice to Have | Plugin FPT.eHospital / Viettel HIS | 2 |
| BO-VN-014 | Sản khoa plugin | Nice to Have | Mẫu 05/BV1 | 2 |
| BO-VN-015 | Luật AI 134 compliance | Must Have | Conformity assessment trước 01/09/2027 | 2 |

---

## USER STORIES

### Nhóm A: Bác sĩ CĐHA (Use Case #1 — Ưu tiên cao nhất)

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| US-VN-001 | BS siêu âm tại phòng khám tư | Đọc to kết quả siêu âm trong lúc nhìn hình | MediVoice tự sinh báo cáo có cấu trúc — không cần thư ký |
| US-VN-002 | BS X-quang | Đọc kết luận phim X-quang | Báo cáo hoàn chỉnh để ký số và lưu RIS/HIS |
| US-VN-003 | BS CĐHA | Review draft báo cáo trước khi ký | Đảm bảo chính xác — AI chỉ là draft |

### Nhóm B: Bác sĩ Lâm Sàng

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| US-VN-004 | BS lâm sàng | Đọc to kết luận sau khi có đủ kết quả XN + CĐHA | MediVoice tự điền Mẫu 15/BV1 hoàn chỉnh với ICD-10-VN |
| US-VN-005 | BS tại phòng mạch ngoài giờ | Ghi bệnh án nhanh cho bệnh nhân | Không cần nhân viên hỗ trợ, tiết kiệm thời gian |
| US-VN-006 | BS | Xem bệnh án draft và phê duyệt bằng 1 tap | Bệnh án lưu vào hệ thống với chữ ký số của tôi |

### Nhóm C: Phòng Khám / Hành Chính

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| US-VN-007 | Chủ phòng khám | Có giải pháp EMR tuân thủ TT13/2025 | Phòng khám không bị phạt sau deadline 31/12/2026 |
| US-VN-008 | Lễ tân phòng khám | Đăng ký bệnh nhân nhanh kể cả không có CCCD | Mọi bệnh nhân đều được tiếp nhận theo luật |
| US-VN-009 | Chủ phòng khám | Có audit trail đầy đủ cho mọi bệnh án | Sẵn sàng cho thanh tra BYT bất kỳ lúc nào |

---

## CONSTRAINTS

| Type | Constraint |
|---|---|
| **Pháp lý VN — Data** | NĐ13/2023: Dữ liệu bệnh nhân PHẢI lưu tại VN — không cloud nước ngoài |
| **Pháp lý VN — Format** | TT32/2023: Output PHẢI theo mẫu bệnh án BYT — không tự do format |
| **Pháp lý VN — EMR** | TT13/2025: Hỗ trợ chữ ký số + audit trail + HL7 FHIR (deadline 31/12/2026) |
| **Pháp lý VN — AI** | Luật AI 134/2025: Human oversight bắt buộc — BS phải approve trước khi lưu |
| **Pháp lý VN — Hành nghề** | Luật KCB 2023: AI chỉ tạo draft — BS có CCHN ký = chủ thể pháp lý |
| **Kỹ thuật** | 100% offline — không cloud dependency |
| **Kỹ thuật** | Latency: < 5 giây sau khi BS đọc xong |
| **Kỹ thuật** | Không có MarianMT — output tiếng Việt trực tiếp |
| **Y tế** | Tên thuốc giữ nguyên — không dịch, không sửa |
| **Y tế** | ICD-10-VN bắt buộc trong phần Chẩn đoán (không phải ICD-10-CA) |
| **Ngân sách** | Phase 1 bootstrapped — $0 cloud API cost |

---

## LUỒNG / FLOWS

| Flow | Tên | MVP Phase | Mô tả |
|---|---|---|---|
| **VN-FLOW-A** | **Báo cáo CĐHA** | **1 — NGAY** | BS siêu âm/X-quang đọc to → báo cáo CĐHA có cấu trúc → BS ký |
| **VN-FLOW-B** | **Bệnh án Ngoại trú** | **1 — NGAY** | BS lâm sàng đọc kết luận → Mẫu 15/BV1 + ICD-10-VN → BS ký |
| VN-FLOW-C | Bệnh án Nha khoa | 1 | BS nha đọc → Mẫu 16/BV1 + sơ đồ răng → BS ký |
| VN-FLOW-D | Bệnh án Sản khoa | 2 | BS sản đọc → Mẫu 05/BV1 + tiền sử sản → BS ký |
| VN-FLOW-E | Bệnh án Nhi | 2 | BS nhi đọc → Mẫu 02/BV1 + cha mẹ/phát triển → BS ký |

---

## OUTPUT FORMAT — PHẦN CHUNG TẤT CẢ FLOWS

```
┌─────────────────────────────────────────────────┐
│  PHẦN I: HÀNH CHÍNH (common to all)            │
│  • Họ tên, ngày sinh, giới tính, dân tộc       │
│  • Địa chỉ, SĐT                                │
│  • CCCD / BHYT (optional — không bắt buộc)     │
│  • Tên cơ sở y tế, khoa, bác sĩ               │
│                                                 │
│  PHẦN II: CHUYÊN MÔN (by flow/plugin)         │
│  [VN-FLOW-A — CĐHA]                            │
│  • Kỹ thuật: [loại chụp, protocol]            │
│  • Mô tả: [findings chi tiết từng cơ quan]    │
│  • Kết luận: [chẩn đoán hình ảnh]             │
│  • Khuyến nghị: [nếu cần]                     │
│  • Bác sĩ CĐHA ký: ___                        │
│                                                 │
│  [VN-FLOW-B — Ngoại trú Mẫu 15/BV1]          │
│  • Lý do vào viện: [triệu chứng]              │
│  • Bệnh sử: [diễn biến theo thời gian]        │
│  • Tiền sử: [bản thân + gia đình + dị ứng]   │
│  • Khám lâm sàng: [sinh hiệu + khám cơ quan] │
│  • Cận lâm sàng: [kết quả XN + CĐHA]         │
│  • Chẩn đoán: [bệnh chính] — ICD-10-VN: [mã] │
│  • Hướng điều trị: [thuốc + liều + tái khám] │
│  • Bác sĩ lâm sàng ký: ___                   │
└─────────────────────────────────────────────────┘
```

---

## QUALITY ATTRIBUTES

| Attribute | Requirement |
|---|---|
| Accuracy | WER < 20% VN medical speech; BS approve > 85% không sửa nhiều |
| Latency | < 5 giây sau khi BS đọc xong |
| Availability | 99.5% uptime local; không phụ thuộc cloud |
| Security | Fernet encryption at rest; TLS in transit; no data leaves device |
| Compliance | TT32/2023 format; ICD-10-VN; NĐ13/2023; Luật AI 134/2025 |
| Auditability | Full immutable audit log — mọi thay đổi có timestamp + user ID |
| Usability | BS không cần training đặc biệt — đọc to như bình thường |

---

*DS-VN-CL08-BRS | MediVoice VN v1.0 | ISO/IEC/IEEE 29148:2018 | 2026-06-03*
