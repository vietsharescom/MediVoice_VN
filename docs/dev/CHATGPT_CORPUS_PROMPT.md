# CHATGPT_CORPUS_PROMPT.md — v2.0
# Prompt tạo CLINICAL_TEST_CORPUS_VN — 46 test cases
# Synthesis từ: Claude + ChatGPT analysis + Grok corpus
# Cách dùng: Copy phần "=== BẮT ĐẦU PROMPT ===" → dán vào ChatGPT/Grok/Gemini

---

## LỊCH SỬ PHIÊN BẢN

| Version | Ngày | Thay đổi |
|---|---|---|
| v1.0 | 2026-06-08 | Claude tạo — 21 cases |
| v2.0 | 2026-06-08 | +ChatGPT: 3-file structure, Group F/G/H | +Grok: fix thuật ngữ VN | = 46 cases |

## LỖI THUẬT NGỮ CLAUDE ĐÃ MẮC — CẦN TRÁNH

| Sai (Claude v1) | Đúng | Lý do |
|---|---|---|
| `tổng trạng tỉnh táo` | `tình trạng tỉnh táo` hoặc bỏ prefix | "tổng" sai |
| `đau tăng khi nuốt` | `nuốt khó` hoặc `đau khi nuốt` | "tăng" thừa |
| Chỉ test `kê đơn` | Test cả `toa thuốc` (phổ biến miền Nam) | Bias từ |
| ICD-10 không rõ nguồn | ICD-10-VN (Bộ Y tế QĐ5837) — KHÔNG phải ICD-10-CM Mỹ | |

## CẤU TRÚC FILE — ChatGPT suggestion (đúng)

Mỗi test case cần 3 files riêng:
```
TC-A01/
├── script.txt        ← BS đọc cái này (kịch bản)
├── reference.txt     ← Expected transcript (không ký hiệu, text thuần)
└── groundtruth.json  ← Field values để đo WER + CEER
```

---

=== BẮT ĐẦU PROMPT v2.0 — COPY TỪ ĐÂY ===

# Yêu cầu tạo bộ kiểm thử ASR y tế tiếng Việt — 46 test cases

## Bối cảnh

Phần mềm MediVoice VN: AI nghe bác sĩ đọc bệnh án → tự động điền Mẫu 15/BV-01 (TT32/2023).
Cần 46 kịch bản đọc để kiểm thử toàn bộ pipeline: Audio → ASR → NER → Structured Chart.

Bác sĩ sẽ review trước khi dùng. Mọi thuật ngữ phải đúng thực tế lâm sàng VN.

---

## QUY TẮC NGÔN NGỮ — BẮT BUỘC

### Thuật ngữ đúng thực tế:
- `tình trạng tỉnh táo, tiếp xúc tốt` — KHÔNG "tổng trạng tỉnh táo"
- `nuốt khó` hoặc `đau khi nuốt` — KHÔNG "đau tăng khi nuốt"
- Tên thuốc: tiếng Anh theo cách BS VN phát âm, không Việt hóa
- Cho phép cả `kê đơn:` VÀ `toa thuốc:` — test cả hai variant
- ICD-10-VN (Bộ Y tế QĐ5837) — KHÔNG ICD-10-CM Mỹ

### Số viết bằng chữ (bắt buộc):
- `120/80` → `một trăm hai mươi trên tám mươi`
- `500mg` → `năm trăm miligam`
- `3 lần/ngày` → `ba lần mỗi ngày`
- `0.5mg` → `không phẩy năm miligam`
- `mg/kg` → `miligam mỗi kilogram cân nặng`

### Giọng vùng miền (tự nhiên):
- Nghệ An: `bữa ni`, `mô`, `hỉ`, không đơn thuần đọc script chuẩn
- Huế: `hỉ`, `mô`, `bệnh nhơn`, giọng trầm
- Nam Bộ: `hông`, `hổng có`, `tui`, tốc độ nhanh 170-190 âm tiết/phút
- Tây Nam Bộ: `dùng cơm`, `tui`, chậm 110-130 âm tiết/phút

---

## CẤU TRÚC 46 TEST CASES

### NHÓM A — Lâm sàng cơ bản (5 cases, giọng chuẩn, phòng yên tĩnh)

| ID | Bệnh | ICD-10-VN | Thuốc key |
|---|---|---|---|
| A-01 | Viêm họng cấp | J02.9 | Amoxicillin + Paracetamol |
| A-02 | Viêm loét dạ dày-tá tràng | K25.9 | Omeprazole + Domperidone, ngưng Ibuprofen |
| A-03 | Tăng huyết áp | I10 | Amlodipine tăng liều + Losartan thêm |
| A-04 | Đái tháo đường type 2 | E11.9 | Metformin + Glimepiride + Vitamin B |
| A-05 | Đau thắt lưng cấp | M54.5 | Ibuprofen + Thiocolchicoside |

Cấu trúc mỗi script nhóm A (đầy đủ, không outline):
```
[Hành chính: giới tính, tuổi, nghề nghiệp] [DỪNG 1s]
[Lý do khám — cách BS ghi nhận lời BN] [DỪNG 1s]
[Tiền sử nếu có] [DỪNG 1s]
[Sinh hiệu: HA, mạch, nhiệt độ, cân nặng — số viết bằng chữ] [DỪNG 1.5s]
[Khám lâm sàng ngắn gọn] [DỪNG 1.5s]
[Chẩn đoán: NHẤN tên bệnh] [DỪNG 1s]
[Điều trị: tên thuốc INN + liều + cách dùng + thời gian] [DỪNG 1s]
[Tái khám sau ...] [DỪNG 1s]
```

### NHÓM B — Giọng vùng miền (4 cases, nội dung tương tự A, đổi giọng)

| ID | Bệnh | Giọng | Đặc điểm bắt buộc |
|---|---|---|---|
| B-01 | Viêm họng cấp | Nghệ An | "bữa ni", "mô", "hỉ", "không đỡ mô" |
| B-02 | Viêm loét dạ dày | Huế | "hỉ", "mô", "bệnh nhơn", giọng trầm |
| B-03 | Tăng huyết áp | Nam Bộ [NHANH] | "hông", "hổng", tốc độ 170-190 âm/phút |
| B-04 | Đái tháo đường | Tây Nam Bộ [CHẬM] | "tui", "dùng", 110-130 âm/phút |

### NHÓM C — Ngôn ngữ khó (5 cases)

| ID | Test gì | Bệnh | ICD-10-VN |
|---|---|---|---|
| C-01 | Thuật ngữ ECG/EF/stent + 5 thuốc | Bệnh mạch vành | I25.1 |
| C-02 | Brand → INN: Ventolin/Flixotide/Singulair | Hen phế quản | J45.9 |
| C-03 | Viết tắt: ĐTĐ/THA/TBMN/HA/BV | Migraine | G43.9 |
| C-04 | Tự sửa [SỬA] + ngập ngừng [ừm] | Viêm da cơ địa | L20.9 |
| C-05 | Liều mg/kg nhi khoa | Viêm tai giữa cấp (nhi) | H66.9 |

### NHÓM D — Điều kiện âm thanh khó (4 cases)

| ID | Điều kiện | Bệnh |
|---|---|---|
| D-01 | Tiếng quạt/điều hòa nền SNR ~20dB | Viêm phế quản cấp |
| D-02 | Gió rít qua mic SNR ~12dB | Nhiễm khuẩn tiết niệu |
| D-03 | BS nói nhanh >180 âm/phút, cuối ca | Gout cấp |
| D-04 | Phòng vang RT60 ~0.8s, mic xa 60cm | Cường giáp |

### NHÓM E — Ca phức tạp (3 cases)

| ID | Mục tiêu | Bệnh |
|---|---|---|
| E-01 | Đa bệnh lý: 4 bệnh + 6 thuốc + self-correction | Cao tuổi đa bệnh |
| E-02 | Ca cấp, BS nói nhanh khẩn, nhiều số | Nhịp nhanh kịch phát |
| E-03 | So sánh lần trước vs hiện tại (SpO2 cũ ≠ mới) | COPD sau đợt cấp |

### NHÓM F — NER Stress Tests (10 cases) ← MỚI

**Mục tiêu:** ASR đúng nhưng NER dễ sai. Test negation + attribution.

| ID | Input | NER phải ra |
|---|---|---|
| F-01 | "Bệnh nhân dị ứng Penicillin" | `{allergy: "Penicillin"}` |
| F-02 | "Không dị ứng thuốc" | `{allergy: null}` — KHÔNG extract gì |
| F-03 | "Cha bị tăng huyết áp, bệnh nhân không bị" | `{family_history: "THA", condition: null}` |
| F-04 | "Không sốt, không ho, không khó thở" | `{fever: null, cough: null, dyspnea: null}` |
| F-05 | "Đã hết đau đầu sau uống thuốc" | `{headache: "resolved"}` — không phải active symptom |
| F-06 | "Tiền sử từng bị viêm phổi năm ngoái" | `{history: "viêm phổi"}` — không phải current |
| F-07 | "Em đau họng, không đau tai" | `{throat_pain: true, ear_pain: false}` |
| F-08 | "Ngưng Metformin vì suy thận, thay Glipizide" | `{stopped: "Metformin", added: "Glipizide"}` |
| F-09 | "Chưa có biến chứng thần kinh" | `{complication_neuro: null}` |
| F-10 | "Bệnh nhân phủ nhận uống rượu" | `{alcohol: false}` — không extract "rượu" vào tiền sử |

**Lưu ý:** Mỗi F-case CHỈ cần:
- 1-3 câu ngắn (không cần full script)
- Ground truth JSON rõ field nào có giá trị, field nào null

### NHÓM G — Intent & Context (5 cases) ← MỚI

**Mục tiêu:** Phân biệt temporal context: current / historical / family / resolved

| ID | Input | Intent |
|---|---|---|
| G-01 | "Tôi đau họng" | CURRENT symptom |
| G-02 | "Bệnh nhân hết đau họng" | RESOLVED — không active |
| G-03 | "Tiền sử từng đau họng" | HISTORY — không current |
| G-04 | "Đau họng nếu uống lạnh" | CONDITIONAL — không active hiện tại |
| G-05 | "Mẹ bệnh nhân hay bị đau họng" | FAMILY — không phải bệnh nhân |

### NHÓM H — Nha khoa (5 cases) ← MỚI — Phase 1 target của MediVoice

| ID | Ca | ICD-10-VN |
|---|---|---|
| H-01 | Khám răng định kỳ, không có bệnh | Z01.2 |
| H-02 | Viêm tủy răng không hồi phục (răng 46) | K04.0 |
| H-03 | Nhổ răng khôn 48 biến chứng | K01.1 |
| H-04 | Cạo vôi và đánh bóng, hướng dẫn vệ sinh | Z29.8 |
| H-05 | Phục hình mão sứ zirconia (răng 21) | K08.3 |

**Thuật ngữ nha khoa cần dùng đúng:**
- Tên răng theo số: "răng bốn mươi sáu", "răng hai mươi mốt"
- "điều trị tủy" không phải "chữa ống tủy"
- "nhổ răng" không phải "rút răng"
- Vật liệu: "zirconia", "composite", "amalgam" — đọc theo cách BS VN thực nói

---

## BRAND → INN MAPPING (mở rộng từ v1.0)

| Tên thương mại (BS hay dùng) | INN chuẩn |
|---|---|
| Ventolin | Salbutamol |
| Flixotide 200mcg | Fluticasone propionate |
| Singulair 10mg | Montelukast |
| Glucophage 500mg | Metformin |
| Coversyl 5mg | Perindopril |
| Diamicron MR 30mg | Gliclazide |
| Augmentin 625mg | Amoxicillin/Clavulanate |
| Zocor 20mg | Simvastatin |
| Lipitor 20mg | Atorvastatin |
| Norvasc 5mg | Amlodipine |
| Cozaar 50mg | Losartan |
| Celebrex 200mg | Celecoxib |

---

## KÝ HIỆU (giữ từ v1.0)

| Ký hiệu | Ý nghĩa |
|---|---|
| `[DỪNG 1s]` | Ngừng nói 1 giây |
| `[DỪNG 1.5s]` | Ngừng nói 1.5 giây |
| `[DỪNG 2s]` | Ngừng nói 2 giây |
| `[CHẬM]` | Đọc chậm hơn 30% |
| `[NHANH]` | Đọc nhanh hơn 30% |
| `[NHẤN]` | Nhấn mạnh từ này |
| `[ừm]` | Nói "ừm" thật, ngập ngừng |
| `[SỬA]` | Tự sửa — nói "à, sửa lại..." |

---

## FORMAT OUTPUT — 3 FILES PER CASE (ChatGPT suggestion)

**File 1: TC-A01/script.txt** (BS đọc to cái này)
```
Bệnh nhân nam, hai mươi tám tuổi, nhân viên văn phòng. [DỪNG 1s]
Lý do khám: nuốt khó, sốt nhẹ về chiều đã ba ngày nay. [DỪNG 1s]
...
```

**File 2: TC-A01/reference.txt** (expected ASR output — không có ký hiệu)
```
Bệnh nhân nam hai mươi tám tuổi nhân viên văn phòng
Lý do khám nuốt khó sốt nhẹ về chiều đã ba ngày nay
...
```

**File 3: TC-A01/groundtruth.json**
```json
{
  "id": "TC-A01",
  "icd10_vn": "J02.9",
  "sinh_hieu": {
    "huyet_ap": "120/80",
    "mach": 80,
    "nhiet_do": 37.8,
    "can_nang": 68
  },
  "chan_doan": "Viêm họng cấp",
  "thuoc": [
    {"inn": "Amoxicillin", "lieu": "500mg", "tan_suat": "3 lần/ngày", "thoi_gian": "7 ngày"},
    {"inn": "Paracetamol", "lieu": "500mg", "chi_dinh": "khi đau hoặc sốt"}
  ],
  "tai_kham": "5 ngày"
}
```

---

## TỔNG KẾT SCOPE

| Nhóm | Số cases | Mục tiêu test |
|---|---|---|
| A — Cơ bản | 5 | ASR + NER baseline |
| B — Vùng miền | 4 | Accent robustness |
| C — Ngôn ngữ khó | 5 | Mixed lang, brand, abbreviation, disfluency |
| D — Âm thanh khó | 4 | Noise robustness |
| E — Phức tạp | 3 | Multi-disease, emergency, temporal |
| F — NER Stress | 10 | Negation + attribution |
| G — Intent | 5 | Temporal context: current/history/family |
| H — Nha khoa | 5 | Domain-specific Phase 1 |
| **TỔNG** | **41** | Full pipeline A→ASR→NER→Chart |

*(46 trong thiết kế ban đầu, sau review giảm G từ 10→5 vì overlap với F)*

---

## CHECKLIST BÁC SĨ REVIEW

Sau khi AI viết xong, bác sĩ kiểm tra:
- [ ] Thuật ngữ đúng cách BS VN nói thật (không phải sách giáo khoa)?
- [ ] Liều thuốc đúng phác đồ VN hiện hành?
- [ ] Sinh hiệu hợp lý lâm sàng?
- [ ] Giọng vùng miền nghe tự nhiên (cần BS từng vùng xác nhận)?
- [ ] ICD-10-VN code đúng (theo QĐ5837)?
- [ ] Kịch bản nha khoa đúng quy trình phòng khám nha?

=== KẾT THÚC PROMPT v2.0 ===

---

## WORKFLOW SAU KHI NHẬN CORPUS

```
1. AI viết 41 scripts + 3 files mỗi case
2. BS Đà Nẵng review: A, B, C, D
3. BS Sài Gòn review: B (giọng Nam), H (nha khoa)
4. Andy tổng hợp sửa
5. Claude:
   a. Thay thế CLINICAL_TEST_CORPUS_VN.md
   b. Generate groundtruth.json đầy đủ
   c. Chạy BENCH-001 với corpus mới
```

## FILES CẦN CẬP NHẬT

```
Thay thế: docs/dev/CLINICAL_TEST_CORPUS_VN.md
Tạo mới:  data/audio/corpus/TC-*/groundtruth.json (41 files)
Tham chiếu: docs/records/ADAPTIVE_LEARNING_ARCHITECTURE.md
```
