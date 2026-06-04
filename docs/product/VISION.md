# VISION.md | DS-VN-CL05-VIS | MediVoice VN Product Vision
# ISO/IEC 42001:2023 Clause 5 | v0.2.0 | 2026-06-03

---

## 1. TẦM NHÌN

> **"Bác sĩ nói — bệnh án tự viết. Phòng mạch tư hiện đại hoá trong 30 phút."**

MediVoice VN là **Documentation Assistant** đầu tiên tại Việt Nam dành riêng cho
phòng mạch tư nhân — tự động hoá ghi chép hồ sơ bệnh án từ giọng nói bác sĩ,
tuân thủ TT32/2023, chạy 100% offline, sẵn sàng cho TT13/2025.

**Không phải Medical Device. Không tự chẩn đoán.**
AI tạo nháp — Bác sĩ chịu trách nhiệm hoàn toàn.

---

## 2. SẢN PHẨM — 2 LAYER + 3 GÓI

### 2 Layers

```
LAYER 1: Patient Management (optional)
  Hồ sơ bệnh nhân, lịch hẹn online, thu chi, referral

LAYER 2: AI Voice Core (bắt buộc — core value)
  BS nói → PhoWhisper → điền Mẫu 15/BV1 → BS approve → PDF
```

### 3 Gói Dịch Vụ

| Gói | Tên | Giá | Modules | Target |
|---|---|---|---|---|
| **Gói 1** | AI Voice Only | 500k–1M/tháng | Core AI + PDF | BS cần ghi chép nhanh |
| **Gói 2** | Phòng Mạch | 2–3M/tháng | Gói 1 + M1+M2+M3+M4+M6+M7 | Phòng mạch tư có đăng ký |
| **Gói 3** | Phòng Khám | 4–8M/tháng | Tất cả + M5+M8+M9 | Phòng khám đa khoa, có HIS |

### 9 Modules

```
M1: Quản lý bệnh nhân    — hồ sơ, lịch sử, CCCD scan
M2: Đặt lịch hẹn         — BN book online, QR check-in
M3: Thu chi đơn giản     — voice log thu/chi, báo cáo ngày/tháng
M4: Kết quả bên thứ 3   — upload PDF/ảnh từ XN/CĐHA vào hồ sơ
M5: Referral partner     — chỉ định đối tác (KHÔNG ghi tiền)
M6: Zalo / Thông báo    — reminder tái khám, share đơn thuốc
M7: VN Cloud sync        — backup VNG/FPT/VNPT, multi-device
M8: Plugin chuyên khoa  — CĐHA, nha khoa, tai mũi họng...
M9: HIS integration      — HL7 v2, BravoSoft, FPT.eHospital
```

---

## 3. THỊ TRƯỜNG MỤC TIÊU

### Target Phase 0: Phòng Mạch Tư Lâm Sàng

```
Đặc điểm:
  Đăng ký BYT, 1–3 BS, 10–30 BN/ngày
  50% vẫn dùng sổ giấy hoặc Excel
  TT13/2025 deadline 31/12/2026 — đang lo lắng
  WTP: 1–3M VNĐ/tháng

Pain point chính:
  Ghi chép bằng tay chậm — mất 5–10 phút/BN
  Không có lịch sử BN → hỏi lại từ đầu mỗi lần
  Chưa comply TT13/2025 → nguy cơ bị phạt

MediVoice VN giải quyết:
  Ghi chép bằng giọng nói → 1–2 phút/BN
  Lịch sử BN tự động → load ngay khi BN đến
  TT13 compliance ready — không cần thêm tool
```

### Phân Khúc Thị Trường VN

| Phân khúc | Số lượng ước tính | WTP | Priority |
|---|---|---|---|
| Phòng mạch tư lâm sàng (đăng ký) | ~15,000–20,000 | 1–3M/tháng | **Phase 0** |
| Phòng khám đa khoa tư | ~5,000–8,000 | 3–8M/tháng | Phase 1 |
| Trung tâm CĐHA tư | ~1,000–2,000 | 3–8M/tháng | Phase 1 plugin |
| BS công + phòng mạch tư đăng ký | ~10,000–15,000 | 500k–2M/tháng | Phase 1 |

### Personas Chính

**Persona #1 — BS lâm sàng phòng mạch tư (TARGET PHASE 0)**
- Mở phòng mạch sau giờ công, đã đăng ký BYT
- 15–30 BN/ngày, không có hoặc có 1 trợ lý
- Đang dùng sổ giấy hoặc BravoSoft cũ
- Cần: TT13 compliance + ghi chép nhanh
- Quyết định mua: 1–2 tuần, tự quyết

**Persona #2 — BS CĐHA tư (CĐHA plugin Phase 1)**
- 30–50 ca siêu âm/X-quang mỗi ngày
- Tự gõ báo cáo hoặc có thư ký gõ = 3+ giờ/ngày
- Pain rõ: voice → structured report
- WTP cao, quyết định nhanh nếu demo tốt

**Persona #3 — Chủ phòng khám đa khoa (Phase 1–2)**
- 5–20 BS, cần chuẩn hoá hồ sơ toàn phòng
- Deadline TT13/2025 đang gần
- Cần: multi-user + HIS integration + compliance

---

## 4. QUYTRÌNH BỆNH NHÂN ĐẦY ĐỦ

```
[TRƯỚC KHI ĐẾN] — Gói 2+
  BN book lịch qua Zalo/web → phòng mạch nhận lịch
  Không cần gọi điện, không cần chờ lâu

[ĐẾN PHÒNG MẠCH]
  BN mới: nhập tay / voice / scan CCCD → tạo hồ sơ
  BN cũ: scan QR → load hồ sơ + lịch sử tự động

[TRONG PHÒNG KHÁM — CORE VALUE]
  BS nói vào mic trong lúc khám:
  "Đau khớp gối phải 2 tuần, sưng nhẹ...
   Chẩn đoán thoái hoá khớp. Kê Meloxicam 7.5mg...
   Chỉ định X-quang. Tái khám 2 tuần."
       ↓ AI điền Mẫu 15/BV1 theo thời gian thực
  BS đọc lại → chỉnh sửa → PHÊ DUYỆT (L4)

[SAU KHÁM]
  Đơn thuốc PDF → Zalo/in cho BN
  Giấy chỉ định → in / gửi đối tác
  Lịch tái khám tự động → Zalo reminder D-1
  Revenue log: "Thu 200k BN Lan" → app ghi

[KẾT QUẢ VỀ] — Gói 2+
  Không integrate: BS/BN upload PDF/ảnh kết quả
  Có integrate (Gói 3): thông báo tự động khi có kết quả
```

---

## 5. KIẾN TRÚC PIPELINE

```
Audio input (mic streaming)
    ↓
[L0]  Validate + normalize 16kHz mono
    ↓
[L1a] PhoWhisper-small chunk streaming (10s + 2s overlap)
[L1b] Drug name correction (VN drug database)
[L1c] Medical NER — PhoBERT + CRF
[L1d] ICD-10-VN auto-lookup (QĐ5837)
    ↓
[L2]  Schema + confidence validation
    ↓
[L3]  Route → lâm sàng (default) / plugin chuyên khoa
    ↓
[L4]  Human Gate — BS review + chỉnh sửa + APPROVE (BẮTBUỘC)
    ↓
[L5]  PII scan — CCCD/BHYT/SĐT (NĐ13/2023)
    ↓
[L6]  Generate Mẫu 15/BV1 + plugin nếu có
    ↓
[L7]  SQLite + Fernet lưu trữ (local)
    ↓
[L8]  Recovery — error handling
    ↓
[L9a] PDF export         ← Phase 0
[L9b] HL7 v2 export      ← Phase 1
[L9c] FHIR R4 export     ← Phase 2
    ↓
[L10] Immutable audit log (ISO 42001 + Luật AI 134)
```

---

## 6. PLUGIN SYSTEM — CHUYÊN KHOA LÀ OPTION

```
CORE (tất cả):
  Mẫu 15/BV1 — lâm sàng ngoại trú

PLUGINS (bật theo nhu cầu):
  CĐHA:       Báo cáo siêu âm/X-quang (FID-VN-001)
              Structured: Kỹ thuật / Mô tả / Kết luận
  Nha khoa:   Mẫu 16/BV1 + sơ đồ răng FDI (FID-VN-003)
  Phase 2:    Tai mũi họng, Tim mạch, Sản khoa, Nhi...

LƯU Ý: Mỗi chuyên khoa có form riêng —
        KHÔNG dùng Mẫu 15/BV1 cho CĐHA hay TMH
```

---

## 7. PHÂN TÍCH CẠNH TRANH

| Đối thủ | Điểm yếu → Lợi thế MediVoice VN |
|---|---|
| **BravoSoft** | Không có AI, không có voice, UI cũ, không FHIR |
| **VEM.AI** | Cloud only (vi phạm NĐ13), chỉ BV công, chưa thương mại |
| **Dr.AI (Taiwan)** | $149/tháng, tiếng Anh, cloud, không TT32 |
| **Heidi Health (AU)** | Chưa vào VN, không offline, không TT32 |
| **FPT/Viettel HIS** | Không có AI scribe → đối tác, không đối thủ |
| **OneClinic** | Cloud-based, modern UI nhưng không có AI voice |

**Không ai đang làm AI voice-to-EMR cho phòng mạch tư VN.**
Cửa sổ cơ hội: 12–18 tháng trước khi đối thủ pivot vào.

---

## 8. ROADMAP

```
PHASE 0 (2–3 tháng) — VALIDATE & REVENUE:
  Core AI Voice + Mẫu 15/BV1 + PDF + SQLite
  Pilot: Đà Nẵng (Andy) + Sài Gòn (BS partner)
  Mục tiêu: 5 BS trả tiền

PHASE 1 (3–9 tháng) — COMPLETE PRODUCT:
  Modules M1–M7 + Staff voice + HL7 v2
  Plugin CĐHA (FID-VN-001) + Nha khoa (FID-VN-003)
  Scale: 50–200 phòng mạch

PHASE 2 (2027) — KHI BYT SIẾT:
  FHIR R4 + Chữ ký số + BYT compliance
  Luật AI 134 conformity assessment
  Upsell từ Gói 1 → Gói 2/3

PHASE 3 (2027–2028) — NỀN TẢNG:
  VNeID real-time auth
  BHYT eligibility check
  BYT Central Registry sync
  FPT/Viettel partnership (M9)
```

---

## 9. KEY DECISIONS (KHÔNG RE-DEBATE)

| Decision | Rationale |
|---|---|
| Offline-first | NĐ13/2023 + AI consistency + phòng mạch VN internet yếu |
| Mẫu 15/BV1 là CORE | 95% BS lâm sàng tư dùng — không phải CĐHA |
| CĐHA là Plugin | Form chuyên ngành riêng, Phase 1 revenue cao |
| NOT SaMD | Chỉ transcription, không chẩn đoán (TT46/2017) |
| Tauri (không Electron) | 10MB vs 150MB — máy VN cũ |
| HL7 v2 trước FHIR | FHIR chưa production tại VN (2026) |
| Referral: không ghi tiền | Luật KCB 2023 Điều 80 |
| Target clinic tư | BV công = đấu thầu 6–18 tháng |
| Pilot Đà Nẵng + SG | Andy có phòng khám + BS partner sẵn |

---

*DS-VN-CL05-VIS | MediVoice VN VISION v0.2.0 | 2026-06-03*
*Owner: Andy Phan — Maple Leaf Group*
