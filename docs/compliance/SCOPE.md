# SCOPE.md | DS-VN-COM-001
# ISO 9001:2015 Clause 4.3 + ISO/IEC 42001:2023 Clause 4.3
# MediVoice VN — Phạm vi Hệ thống Quản lý Chất lượng + AI
# v1.1 | 2026-06-06 | Owner: Andy Phan | Maple Leaf Group
# Updated: Design Review — DESIGN_REPORT_v1.1_20260606.md

---

## 1. PHẠM VI QMS (ISO 9001:2015 Cl.4.3)

**Tổ chức:** Maple Leaf Group — đơn vị phát triển MediVoice VN

**Phạm vi áp dụng:**
> Thiết kế, phát triển, triển khai và hỗ trợ phần mềm MediVoice VN —
> hệ thống AI hỗ trợ ghi chép hồ sơ bệnh án ngoại trú cho phòng mạch tư nhân tại Việt Nam.

**Địa lý:** Việt Nam (server + data tại VN theo NĐ13/2023)

**Loại trừ (Exclusions):**
| Clause | Lý do loại trừ |
|---|---|
| ISO 9001 Cl.7.1.5 — Calibration | Không có thiết bị đo lường vật lý |
| ISO 9001 Cl.8.3 — Design of products | Áp dụng riêng qua FID + FEATURE WORKFLOW |
| ISO 9001 Cl.8.4 — External providers | Phase 0: không có nhà cung cấp bên ngoài có hợp đồng |

---

## 2. PHẠM VI AIMS (ISO/IEC 42001:2023 Cl.4.3)

**Hệ thống AI trong phạm vi:**

| Hệ thống | Mô tả | Phân loại rủi ro |
|---|---|---|
| PhoWhisper ASR (L1a) | Chuyển giọng nói BS → văn bản | HIGH |
| Medical NER (L1c) | Trích xuất thực thể y tế từ transcript | HIGH |
| ICD-10-VN Lookup (L1d) | Tra mã bệnh tự động | MEDIUM |
| Form Generator (L6) | Điền Mẫu 15/BV-01 từ NER output | HIGH |

**Ngoài phạm vi AIMS:**
- L7 Storage, L8 Error handler, L9a PDF, L10 Audit log — không phải AI components
- L4 Human Gate — là control mechanism, không phải AI

**Mục đích sử dụng được phép (Intended Use):**
- Hỗ trợ BS ghi chép hồ sơ bệnh án ngoại trú
- Tạo bản nháp để BS review và phê duyệt
- Không được dùng để chẩn đoán, kê đơn độc lập

**Mục đích sử dụng KHÔNG được phép (Prohibited Use):**
- Thay thế phán đoán lâm sàng của BS
- Lưu bệnh án mà không có BS approve
- Dùng bởi cơ sở không có GPHN/CCHN hợp lệ

---

## 3. RANH GIỚI HỆ THỐNG (System Boundary)

```
IN SCOPE — PHASE 0 (hiện tại):
  ├── Audio capture + normalize (L0)
  ├── AI pipeline L1a → L6 (ASR, NER, ICD, form generation)
  ├── Human Gate L4 (BS approve bắt buộc)
  ├── Staff Confirm Gate (admin side)
  ├── Storage L7 (local SQLite + Fernet)
  ├── Audit log L10 (immutable hash chain)
  ├── FastAPI PWA (web interface — Doctor + Staff screens)
  ├── Queue Management System (số thứ tự + TTS loa)
  ├── Email SMTP (gửi PDF, kết quả XN)
  ├── M1 Patient Management (cơ bản)
  └── M3 Thu chi đơn giản

IN SCOPE — PHASE 1 (sắp tới):
  ├── M2 Booking engine (7 states + buffer + waitlist)
  ├── M4 Email auto-processor (kết quả XN từ bên ngoài)
  ├── M5 Referral partner 2 chiều
  ├── M6 Zalo OA + Email routing
  ├── M7 VN Cloud sync
  └── Integration Gateway (Zalo/Email/SMS adapters)

IN SCOPE — PHASE 2:
  ├── M8 Plugin chuyên khoa (CĐHA, Nha khoa)
  ├── M9 HIS integration (HL7 v2 / FHIR R4)
  └── Chữ ký số (TT13/2025)

OUT OF SCOPE (vĩnh viễn):
  ├── Hạ tầng thiết bị phòng khám (máy tính, mic, loa — do cơ sở KCB)
  ├── Cloud nước ngoài (AWS/GCP/Azure)
  ├── Quyết định lâm sàng của BS
  └── Xử lý thanh toán commission (ngoài hệ thống)
```

---

## 4. LIÊN KẾT VỚI CÁC TÀI LIỆU KHÁC

| Tài liệu | Mô tả |
|---|---|
| [AI_POLICY.md](AI_POLICY.md) | Chính sách AI — ISO 42001 Cl.5.2 |
| [RISK_REGISTER.md](RISK_REGISTER.md) | Rủi ro trong phạm vi này |
| [IMPACT_ASSESSMENT.md](IMPACT_ASSESSMENT.md) | Đánh giá tác động AI |
| [BRS.md](../product/BRS.md) | Yêu cầu nghiệp vụ chi tiết |

---

*DS-VN-COM-001 | SCOPE v1.1 | ISO 9001:2015 Cl.4.3 + ISO/IEC 42001:2023 Cl.4.3 | 2026-06-06*
