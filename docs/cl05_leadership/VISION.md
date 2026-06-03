# VISION.md | DS-VN-CL05-VIS | MediVoice VN Product Vision
# ISO/IEC 42001:2023 Clause 5 | v1.0 | 2026-06-03

---

## 1. TẦMNHÌN

> **"Mọi bác sĩ Việt Nam có thể nói và bệnh án tự viết — chuẩn pháp lý, không cần thư ký."**

MediVoice VN là công cụ AI đầu tiên tại Việt Nam tự động hóa việc ghi chép hồ sơ
bệnh án điện tử từ giọng nói bác sĩ, tuân thủ đầy đủ TT32/2023 và NĐ13/2023,
chạy 100% offline trên thiết bị của phòng khám.

---

## 2. THỊ TRƯỜNG MỤC TIÊU

### Đặc điểm hệ thống y tế VN

Việt Nam **không có bác sĩ gia đình** và **không có gatekeeping**:
- Bệnh nhân tự đến thẳng bệnh viện hoặc phòng khám chuyên khoa — không cần giới thiệu
- Bệnh viện Bạch Mai: 3,000–3,600 ngoại trú/ngày
- Phòng khám tư: ~37,000–40,000 đang hoạt động, ~1,000–2,000 trung tâm CĐHA tư

### Target users (theo thứ tự ưu tiên)

**Persona #1 — Bác sĩ CĐHA tư (siêu âm, X-quang, CT)**
- Làm 30–50 ca/ngày, mỗi ca đọc 200–300 chữ kết quả
- Hiện tại: thư ký gõ theo lời đọc, hoặc BS tự gõ
- Pain: 6,000–15,000 chữ/ngày + không chuẩn hóa
- MediVoice VN: BS đọc → báo cáo có cấu trúc trong < 5 giây → ký số

**Persona #2 — BS chuyên khoa mở phòng mạch ngoài giờ**
- BS bệnh viện công, sau giờ làm ở phòng khám riêng
- Ít nhân viên, áp lực thời gian
- Cần EMR trước 31/12/2026 (TT13/2025)
- MediVoice VN: ghi bệnh án + compliance cùng lúc

**Persona #3 — Chủ phòng khám đa khoa tư**
- Quản lý 2–10 BS, cần chuẩn hóa hồ sơ
- Deadline TT13/2025 đang đến gần
- MediVoice VN: compliance + tiết kiệm nhân sự thư ký

---

## 3. PHÂN TÍCH ĐỐI THỦ

| Đối thủ | Điểm yếu tạo lợi thế cho MediVoice VN |
|---|---|
| **VEM.AI** (BV E HN) | Cloud LLM → có thể vi phạm NĐ13/2023; không offline; không chuẩn TT32 |
| **Dr.AI** (Đài Loan) | $149/tháng (~3.7M VNĐ); EN output only; cloud; chưa deploy VN |
| **Heidi Health** (AU) | Chưa vào VN (12–18 tháng); tiếng Việt chưa được validate |
| **FPT/Viettel** | HIS infrastructure — không có AI scribe → **đối tác, không đối thủ** |
| **VinBrain/NVIDIA** | Imaging AI only — khác domain Phase 1 |

**Cửa sổ cơ hội: 12–18 tháng** trước khi Heidi Health pivot vào VN.

---

## 4. LUỒNG SẢN PHẨM

### VN-FLOW-A: Báo cáo CĐHA ← PRIORITY #1

```
BS siêu âm/X-quang nhìn hình ảnh
    ↓
Đọc to (tiếng Việt, hoặc VI+EN code-switching):
"Gan kích thước bình thường, nhu mô đồng nhất,
 không có khối u. Túi mật không sỏi..."
    ↓
[MediVoice VN — plugin_cdha.py]
    ↓
Báo cáo có cấu trúc:
┌────────────────────────────────────────┐
│ KỸ THUẬT:   Siêu âm ổ bụng tổng quát │
│ MÔ TẢ:      Gan: bình thường...       │
│             Túi mật: không sỏi...     │
│ KẾT LUẬN:  Không phát hiện bất thường │
│ BS ký số:   [chờ phê duyệt]          │
└────────────────────────────────────────┘
    ↓ BS review → Ký số → Lưu RIS/HIS
```

### VN-FLOW-B: Bệnh án Ngoại trú Mẫu 15/BV1 ← PRIORITY #2

```
BS lâm sàng sau khi có đủ kết quả XN + CĐHA
    ↓
Đọc to kết luận:
"Bệnh nhân nữ 45 tuổi, đau bụng vùng hạ sườn phải.
 Siêu âm không sỏi. XN bình thường.
 Chẩn đoán: Hội chứng ruột kích thích.
 Điều trị: Mebeverine 135mg ngày 3 lần..."
    ↓
[MediVoice VN — plugin_ngoai_tru.py]
    ↓
Mẫu 15/BV1:
┌────────────────────────────────────────┐
│ Lý do vào viện:  Đau bụng HSD phải   │
│ Bệnh sử:         3 ngày, tăng khi...  │
│ Tiền sử:         Không đặc biệt       │
│ Khám LS:         Bụng mềm, đau HSD P │
│ CLS:             SA ổ bụng: bt        │
│                  XN máu: trong GHBT   │
│ Chẩn đoán:      Hội chứng ruột kích   │
│                  ICD-10-VN: K58.9    │
│ Hướng điều trị: Mebeverine 135mg...   │
│ BS ký số:        [chờ phê duyệt]     │
└────────────────────────────────────────┘
    ↓ BS review → Ký số → Lưu EMR (HL7 FHIR)
```

---

## 5. KIẾN TRÚC PIPELINE

```
Audio input (m4a/wav/mp3)
    ↓
[L0] Validate + normalize 16kHz mono
    ↓
[L1] PhoWhisper-small (VN ASR)
     → Fine-tuned trên VietMed (WER 51.8%→29.6%)
     → Handle code-switching VI+EN (ViMedCSS)
    ↓
[L2] Schema + confidence validation
    ↓
[L3] Routing → detect mode (CĐHA / ngoại trú / nha khoa / ...)
    ↓
[L4] Human gate — ALWAYS (Luật KCB 2023)
    ↓
[L5] PII scan — CCCD/CMND/BHYT/SĐT (NĐ13/2023)
    ↓
[L6] CORE GENERATOR + SPECIALTY PLUGIN
     ├── plugin_cdha.py       ← VN-FLOW-A
     ├── plugin_ngoai_tru.py  ← VN-FLOW-B (Mẫu 15/BV1)
     ├── plugin_nha_khoa.py   ← VN-FLOW-C (Mẫu 16/BV1)
     └── [Phase 2: san, nhi, nhan_khoa...]
     → Output: Bệnh án TT32/2023 + ICD-10-VN
    ↓
[L7] Memory — SQLite, Fernet, 10 năm (TT32/2023)
    ↓
[L8] Recovery — error handling
    ↓
[L9] Response — HL7 FHIR export (TT13/2025)
    ↓
[L10] Audit log — immutable (ISO 42001 + Luật AI 134)
```

**Không có L1b (MarianMT)** — không cần dịch VI→EN.

---

## 6. PLUGIN SYSTEM — 29 FORM TEMPLATES

TT32/2023 quy định 29 mẫu bệnh án nhưng tất cả chia sẻ 70% cấu trúc giống nhau.

```
COMMON CORE (70-80%):
  Hành chính | Lý do vào viện | Bệnh sử | Tiền sử |
  Khám LS | Cận LS | Chẩn đoán ICD-10-VN | Hướng điều trị

SPECIALTY PLUGINS (20-30%):
  CĐHA:     Kỹ thuật / Mô tả / Kết luận [không thuộc 29 mẫu BV1]
  Ngoại trú: Standard Mẫu 15/BV1
  Nha khoa:  Mẫu 16/BV1 + sơ đồ răng FDI
  Sản khoa:  Mẫu 05/BV1 + tiền sử sản, tuổi thai, Apgar [Phase 2]
  Nhi:       Mẫu 02/BV1 + cha mẹ, tiêm chủng, phát triển [Phase 2]
  Nhãn khoa: Mẫu 21-26/BV1 (6 sub-forms) [Phase 2]

Phase 1: 3 plugins → covers 85% thị trường private clinic VN
```

---

## 7. ROADMAP

```
PHASE 1 (NOW — Dec 2026):
  ├── VN-FLOW-A: plugin_cdha (siêu âm/X-quang)       ← FID-VN-001
  ├── VN-FLOW-B: plugin_ngoai_tru (Mẫu 15/BV1)       ← FID-VN-002
  ├── VN-FLOW-C: plugin_nha_khoa (Mẫu 16/BV1)        ← FID-VN-003
  ├── ICD-10-VN database (QĐ5837)
  ├── HL7 FHIR export (TT13/2025 compliance)
  ├── Digital signature support
  └── Pilot: 3–5 phòng khám CĐHA + đa khoa tư

PHASE 2 (2027):
  ├── Luật AI 134 conformity assessment
  ├── FPT.eHospital plugin integration
  ├── plugin_san_khoa (Mẫu 05/BV1)
  ├── plugin_nhi (Mẫu 02/BV1)
  └── VietMed fine-tuning v2 (improved WER)

PHASE 3 (2027-2028):
  ├── National health platform (VNeID) integration
  ├── Multi-user (điều dưỡng + BS + thư ký roles)
  └── Viettel HIS integration
```

---

## 8. KEY DECISIONS (KHÔNG RE-DEBATE)

| Decision | Rationale |
|---|---|
| **Option B: Local only** | NĐ13/2023 blocks cloud. ISO consistency requires frozen models. |
| **Output: TT32/2023, không SOAP** | Pháp lý VN bắt buộc |
| **Xóa MarianMT** | Output VN — không cần dịch |
| **Plugin system** | 1 core + N plugins — không phải 29 app riêng |
| **On-premise deployment** | NĐ13/2023 data residency |
| **Patient ID linh hoạt** | VN law: bệnh nhân không có CCCD vẫn được khám |
| **Human approval gate** | Luật KCB 2023: BS phải ký — AI chỉ là draft |
| **ICD-10-VN** | QĐ5837 bắt buộc — không ICD-10-CA |
| **CĐHA là use case #1** | Khối lượng cao nhất, ROI rõ nhất, quyết định mua nhanh nhất |
| **Target clinic tư** | Không đấu thầu, quyết định trong 1–4 tuần |

---

*DS-VN-CL05-VIS | MediVoice VN VISION v1.0 | 2026-06-03*
*Owner: Andy Phan — Maple Leaf Group*
