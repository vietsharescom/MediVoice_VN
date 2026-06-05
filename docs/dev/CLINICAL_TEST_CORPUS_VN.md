# CLINICAL_TEST_CORPUS_VN.md
# Bộ kịch bản kiểm thử ASR/NER y tế — MediVoice VN
# v1.0 | 2026-06-08 | Andy Phan (Maple Leaf Group)
#
# Tiêu chuẩn tham chiếu:
#   i2b2/n2c2 Medication Extraction (2009–2022)
#   CLEF eHealth Clinical NLP Task (2013–2018)
#   VLSP 2018 Vietnamese NER Benchmark
#   ITU-T P.800 Mean Opinion Score (MOS)
#   ICD-10-VN QĐ5837 (15,026 mã)
#   TT32/2023 Mẫu 15/BV-01
#   WHO AI in Health Guidelines (2021)
#   Luật KCB 2023 + NĐ13/2023

---

## I. TỔNG QUAN

### 1.1 Mục tiêu
Đánh giá hiệu suất pipeline MediVoice VN (ASR + NER + Form mapping) trên dữ liệu
y tế tiếng Việt thực tế, bao gồm:
- Độ chính xác trích xuất thực thể lâm sàng (CEER per entity)
- Độ bền vững qua giọng vùng miền (accent robustness)
- Độ bền vững qua điều kiện âm thanh khó (noise robustness)
- Độ bền vững qua phong cách ngôn ngữ y tế VN (terminology)

### 1.2 Cấu trúc corpus — 21 kịch bản

| Nhóm | Mô tả | Số kịch bản | Điều kiện chuẩn |
|---|---|---|---|
| A | Lâm sàng cơ bản | 5 | Yên tĩnh, chuẩn Hà Nội/Đà Nẵng |
| B | Giọng vùng miền | 4 | Yên tĩnh, accent biến thể |
| C | Ngôn ngữ khó | 5 | Yên tĩnh, thuật ngữ phức tạp |
| D | Điều kiện âm thanh | 4 | Nhiễu/tiếng động |
| E | Ca lâm sàng phức tạp | 3 | Hỗn hợp |
| **Tổng** | | **21** | ~210 câu, ~25–40 phút audio |

### 1.3 Thang điểm PASS/FAIL

| Thực thể | Metric | PASS | Ghi chú |
|---|---|---|---|
| Sinh hiệu (Vitals) | CEER | < 0.05 | Safety-critical |
| Chẩn đoán | CEER | < 0.10 | ICD lookup |
| Thuốc — tên | CEER | < 0.10 | Drug DB match |
| Thuốc — liều | CEER | < 0.05 | Dosage safety |
| Tái khám | CEER | < 0.30 | Less critical |
| WER tổng thể | WER | < 0.40 | ASR baseline |

> Nguồn: i2b2 2010 Medication Challenge (F1 ≥ 0.90 ngưỡng state-of-art)
> Điều chỉnh cho PhoWhisper Phase 0 (model nhỏ, chưa fine-tune)

---

## II. HƯỚNG DẪN THU ÂM

### 2.1 Thiết bị
```
KHUYẾN NGHỊ:
  Mic: USB condenser hoặc lapel clip-on
  Khoảng cách: 15–25 cm từ miệng đến mic
  Phòng: phòng khám thật hoặc phòng ít vang (phủ rèm)
  Software: Audacity (free) hoặc Voice Memos (iPhone)
  Format: WAV, 16kHz, mono, 16-bit (hoặc để nguyên, pipeline tự convert)

TRÁNH:
  Không đeo mic trên cravat (gây tiếng cọ)
  Không hướng thẳng vào quạt
  Không test trong phòng đá hoa (vang)
```

### 2.2 Quy ước đọc

| Ký hiệu | Ý nghĩa | Thực hiện |
|---|---|---|
| `[DỪNG 1s]` | Ngừng nói 1 giây | Đếm thầm 1–2 |
| `[DỪNG 2s]` | Ngừng nói 2 giây | Đếm thầm 1–2–3–4 |
| `[CHẬM]` | Đọc chậm hơn 30% | Kéo dài âm tiết cuối |
| `[NHANH]` | Đọc nhanh hơn 30% | Rút ngắn khoảng nghỉ |
| `[NHẤN]` | Nhấn mạnh từ này | Tăng volume nhẹ |
| `[ừm]` | Nói "ừm" thật | Ngập ngừng tự nhiên |
| `[SỬA]` | Tự sửa theo câu tiếp | Nói "à... sửa lại..." |
| `[HỌ]` | Điền họ tên giả bất kỳ | Không đọc tên thật BN |
| `*TEXT*` | Đọc nhưng sẽ bị lỗi ASR | Đọc bình thường |

### 2.3 Tốc độ nói chuẩn
- **Bình thường:** 130–150 âm tiết/phút (tiếng Việt)
- **Chậm:** < 110 âm tiết/phút
- **Nhanh:** > 180 âm tiết/phút (cuối ngày, mệt)
- **Chuẩn tham chiếu:** VLSP 2018 ~140 âm tiết/phút

---

## III. NHÓM A — LÂM SÀNG CƠ BẢN

> Điều kiện: Phòng yên tĩnh | SNR > 30dB | Tốc độ bình thường | Giọng chuẩn

---

### A-01 | Viêm họng cấp | J02.9 | Hà Nội | Yên tĩnh | ⭐ Dễ

**Thời lượng ước tính:** 45–60 giây

**KỊCH BẢN ĐỌC:**

```
Bệnh nhân nam, bốn mươi hai tuổi, nghề nghiệp kế toán. [DỪNG 1.5s]
Lý do vào khám: đau họng ba ngày nay, đau tăng khi nuốt. [DỪNG 1s]
Bệnh nhân tự uống Paracetamol nhưng không đỡ. [DỪNG 1.5s]

Khám: tổng trạng tỉnh táo, tiếp xúc tốt. [DỪNG 0.5s]
Huyết áp một trăm hai mươi trên tám mươi. [DỪNG 0.5s]
Mạch tám mươi lần mỗi phút. [DỪNG 0.5s]
Nhiệt độ ba mươi bảy phẩy tám độ. [DỪNG 0.5s]
Cân nặng bảy mươi ki lô. [DỪNG 1.5s]

Khám họng: niêm mạc đỏ, amidan hai bên sưng to, không có mủ.
Không có hạch cổ. [DỪNG 1.5s]

Chẩn đoán: [NHẤN] Viêm họng cấp. [DỪNG 1s]

Điều trị:
Amoxicillin năm trăm miligam, uống ba lần mỗi ngày, trong năm ngày. [DỪNG 0.5s]
Paracetamol năm trăm miligam, uống khi sốt trên ba mươi tám độ. [DỪNG 1s]

Tái khám sau năm ngày, hoặc sớm hơn nếu sốt cao không hạ.
```

**GROUND TRUTH:**
| Field | Giá trị |
|---|---|
| huyet_ap | 120/80 |
| mach | 80 |
| nhiet_do | 37.8 |
| can_nang | 70 |
| chan_doan | Viêm họng cấp |
| icd10 | J02.9 |
| thuoc[0] | Amoxicillin 500mg × 3/ngày × 5 ngày |
| thuoc[1] | Paracetamol 500mg khi sốt >38°C |
| tai_kham | Sau 5 ngày |

**TIÊU CHÍ PASS:** Vitals 4/4 | Thuốc 2/2 tên + liều | Chẩn đoán đúng | Tái khám đúng

---

### A-02 | Viêm loét dạ dày | K25.9 | Đà Nẵng | Yên tĩnh | ⭐ Dễ

**Thời lượng ước tính:** 50–65 giây

**KỊCH BẢN ĐỌC:**

```
Bệnh nhân nữ, ba mươi lăm tuổi. [DỪNG 1s]
Đau thượng vị hai tuần, đau âm ỉ, tăng khi đói, giảm sau ăn. [DỪNG 0.5s]
Ợ chua, đầy bụng. Không nôn ra máu, không đi phân đen. [DỪNG 1.5s]
Tiền sử: uống Ibuprofen nhiều lần trong tháng trước do đau khớp. [DỪNG 1s]

Huyết áp một trăm mười trên bảy mươi. [DỪNG 0.5s]
Mạch bảy mươi lăm. [DỪNG 1.5s]

Khám bụng: mềm, ấn đau vùng thượng vị, không có phản ứng thành bụng. [DỪNG 1.5s]

Chẩn đoán: [NHẤN] Viêm loét dạ dày tá tràng. [DỪNG 1s]

Điều trị:
Omeprazole hai mươi miligam, uống một lần mỗi ngày trước ăn sáng ba mươi phút,
trong bốn tuần. [DỪNG 0.5s]
Domperidone mười miligam, uống ba lần mỗi ngày trước bữa ăn. [DỪNG 1s]
Ngưng Ibuprofen hoàn toàn. [DỪNG 1s]

Hẹn tái khám sau bốn tuần.
```

**GROUND TRUTH:**
| Field | Giá trị |
|---|---|
| huyet_ap | 110/70 |
| mach | 75 |
| chan_doan | Viêm loét dạ dày tá tràng |
| icd10 | K25.9 |
| tien_su | Dùng Ibuprofen dài ngày |
| thuoc[0] | Omeprazole 20mg × 1/ngày (trước ăn 30') × 4 tuần |
| thuoc[1] | Domperidone 10mg × 3/ngày trước ăn |
| tai_kham | Sau 4 tuần |

---

### A-03 | Tăng huyết áp | I10 | TP.HCM | Yên tĩnh | ⭐⭐ Trung bình

**Thời lượng ước tính:** 55–70 giây

**KỊCH BẢN ĐỌC:**

```
Bệnh nhân nam, sáu mươi tuổi, nghề nghiệp lái xe. [DỪNG 1s]
Tái khám tăng huyết áp định kỳ. [DỪNG 1s]

Đo huyết áp hôm nay lần một: [NHẤN] một trăm bảy mươi trên một trăm. [DỪNG 0.5s]
Đo lại lần hai sau năm phút: [NHẤN] một trăm sáu mươi lăm trên chín mươi lăm. [DỪNG 1s]
Bệnh nhân khai đã uống thuốc đều, không bỏ liều. [DỪNG 0.5s]
Không đau đầu, không chóng mặt, không khó thở. [DỪNG 1.5s]

Đang dùng Amlodipine năm miligam một viên mỗi ngày. [DỪNG 1s]

Đánh giá: huyết áp chưa kiểm soát. [DỪNG 0.5s]

Điều chỉnh điều trị:
Tăng Amlodipine lên mười miligam mỗi ngày. [DỪNG 0.5s]
Thêm Losartan năm mươi miligam, uống một lần mỗi ngày buổi sáng. [DỪNG 1s]

Theo dõi huyết áp tại nhà sáng tối, ghi vào sổ. [DỪNG 0.5s]
Hạn chế muối, giảm cân nếu thừa cân. [DỪNG 1s]

Tái khám sau hai tuần, mang sổ huyết áp theo.
```

**GROUND TRUTH:**
| Field | Giá trị |
|---|---|
| huyet_ap | 170/100 (lần 1) / 165/95 (lần 2) → dùng 170/100 |
| chan_doan | Tăng huyết áp |
| icd10 | I10 |
| thuoc[0] | Amlodipine 10mg × 1/ngày |
| thuoc[1] | Losartan 50mg × 1/ngày (buổi sáng) |
| tai_kham | Sau 2 tuần |

---

### A-04 | Đái tháo đường type 2 | E11.9 | Cần Thơ | Yên tĩnh | ⭐⭐ Trung bình

**Thời lượng ước tính:** 60–75 giây

**KỊCH BẢN ĐỌC:**

```
Bệnh nhân nữ, năm mươi lăm tuổi, nội trợ, có tiền sử đái tháo đường type hai
tám năm nay. [DỪNG 1.5s]

Tái khám định kỳ. [DỪNG 0.5s]
Đường huyết đói sáng nay: chín phẩy ba mi lí mol trên lít. [DỪNG 0.5s]
HbA1c tháng trước: tám phẩy hai phần trăm. [DỪNG 1.5s]

Bệnh nhân khai ăn uống khó kiểm soát, hay ăn cơm nhiều. [DỪNG 0.5s]
Uống Metformin đều, không bỏ. [DỪNG 1.5s]

Huyết áp một trăm ba mươi trên tám lăm. [DỪNG 0.5s]
Mạch tám mươi hai. [DỪNG 0.5s]
Cân nặng bảy mươi tám ki lô. [DỪNG 1.5s]

Khám: không có phù nề, mạch mu bàn chân bình thường.
Cảm giác hai bàn chân giảm nhẹ. [DỪNG 1.5s]

Chẩn đoán: [NHẤN] Đái tháo đường type hai chưa kiểm soát tốt.
Biến chứng thần kinh ngoại biên nhẹ. [DỪNG 1s]

Điều trị:
Giữ Metformin năm trăm miligam, uống hai lần mỗi ngày sau ăn. [DỪNG 0.5s]
Thêm Glimepiride hai miligam, uống một lần trước ăn sáng. [DỪNG 0.5s]
Vitamin B1 B6 B12, uống một viên mỗi ngày. [DỪNG 1s]

Hẹn xét nghiệm lại HbA1c sau ba tháng. [DỪNG 0.5s]
Tái khám sau một tháng.
```

**GROUND TRUTH:**
| Field | Giá trị |
|---|---|
| huyet_ap | 130/85 |
| mach | 82 |
| can_nang | 78 |
| duong_huyet | 9.3 mmol/L |
| HbA1c | 8.2% |
| chan_doan | Đái tháo đường type 2 chưa kiểm soát; Biến chứng thần kinh ngoại biên |
| icd10 | E11.9 |
| thuoc[0] | Metformin 500mg × 2/ngày sau ăn |
| thuoc[1] | Glimepiride 2mg × 1/ngày trước ăn sáng |
| thuoc[2] | Vitamin B1B6B12 × 1/ngày |
| tai_kham | Sau 1 tháng |

---

### A-05 | Đau lưng cấp | M54.5 | Hà Nội | Yên tĩnh | ⭐ Dễ

**Thời lượng ước tính:** 40–55 giây

**KỊCH BẢN ĐỌC:**

```
Bệnh nhân nam, ba mươi tám tuổi, nhân viên văn phòng. [DỪNG 1s]
Đau lưng dưới ba ngày nay, đau tăng khi cúi người, giảm khi nằm. [DỪNG 0.5s]
Không lan xuống chân, không tê bì. [DỪNG 1.5s]
Tiền sử: ngồi máy tính nhiều giờ mỗi ngày. [DỪNG 1s]

Huyết áp một trăm hai mươi lăm trên tám mươi. [DỪNG 0.5s]
Mạch bảy mươi tám. [DỪNG 1.5s]

Khám: cột sống không vẹo, ấn đau cơ cạnh sống thắt lưng hai bên.
Test Lasègue âm tính. [DỪNG 1.5s]

Chẩn đoán: [NHẤN] Đau thắt lưng cấp do co cơ. [DỪNG 1s]

Điều trị:
Ibuprofen bốn trăm miligam, uống ba lần mỗi ngày sau ăn, trong năm ngày. [DỪNG 0.5s]
Thiocolchicoside tám miligam, uống hai lần mỗi ngày, trong năm ngày. [DỪNG 0.5s]
Chườm nóng vùng lưng hai mươi phút mỗi lần. [DỪNG 1s]

Tái khám sau một tuần nếu không đỡ.
```

**GROUND TRUTH:**
| Field | Giá trị |
|---|---|
| huyet_ap | 125/80 |
| mach | 78 |
| chan_doan | Đau thắt lưng cấp do co cơ |
| icd10 | M54.5 |
| thuoc[0] | Ibuprofen 400mg × 3/ngày sau ăn × 5 ngày |
| thuoc[1] | Thiocolchicoside 8mg × 2/ngày × 5 ngày |
| tai_kham | Sau 1 tuần |

---

## IV. NHÓM B — GIỌNG VÙNG MIỀN

> Nội dung lâm sàng giống nhóm A, đọc bằng giọng địa phương tự nhiên.
> Đánh giá: CEER phải ≤ 1.5× ngưỡng nhóm A (chấp nhận giảm độ chính xác nhẹ do accent)

---

### B-01 | Viêm họng cấp | J02.9 | GIỌNG NGHỆ AN | ⭐⭐⭐ Khó

**Đặc điểm phát âm Nghệ An cần thể hiện:**
- Thanh hỏi/ngã phát âm nặng hơn, gần nhau
- "không" → "khôông" (kéo dài)
- "một" → "một" (dấu nặng rõ hơn)
- Tốc độ chậm hơn, nhấn âm cuối mạnh
- "bao nhiêu" → "bao nhiêu răng"

**KỊCH BẢN ĐỌC — Giọng Nghệ An:**

```
Bệnh nhân nam, bốn mươi hai tuổi. [DỪNG 1.5s]
Đau họng ba bữa ni rồi, đau nhiều khi nuốt. [DỪNG 1s]
Tự uống thuốc hạ sốt mà không thấy đỡ mô. [DỪNG 1.5s]

Huyết áp một trăm hai mươi trên tám mươi. [DỪNG 0.5s]
Mạch tám mươi. [DỪNG 0.5s]
Nhiệt độ ba mươi bảy phẩy tám. [DỪNG 0.5s]
Cân nặng bảy mươi ký. [DỪNG 1.5s]

Họng đỏ, amidan sưng, không có mủ. [DỪNG 1.5s]

Chẩn đoán: viêm họng cấp. [DỪNG 1s]

Kê toa:
Amoxicillin năm trăm miligam, uống ba lần một ngày, trong năm ngày. [DỪNG 0.5s]
Paracetamol năm trăm, uống khi sốt. [DỪNG 1s]

Tái khám sau năm ngày hỉ.
```

**Ngưỡng PASS nhóm B:** CEER Vitals < 0.08 | Thuốc < 0.15 | Chẩn đoán đúng

---

### B-02 | Viêm loét dạ dày | K25.9 | GIỌNG HUẾ | ⭐⭐⭐ Khó

**Đặc điểm phát âm Huế cần thể hiện:**
- Thanh điệu độc đáo, âm vực thấp
- "không" → "khôông" kéo dài và trầm
- "bệnh nhân" → "bệnh nhơn"
- "ăn" → "ăn" (âm a ngắn hơn)
- Câu hỏi có "hỉ", "mô", "chi"

**KỊCH BẢN ĐỌC — Giọng Huế:**

```
Bệnh nhân nữ, ba mươi lăm tuổi. [DỪNG 1s]
Đau bụng trên hai tuần nay, đau khi đói, ăn vô thì đỡ hơn. [DỪNG 0.5s]
Ợ chua, khó chịu bụng. [DỪNG 1.5s]
Trước có uống thuốc giảm đau Ibuprofen nhiều. [DỪNG 1s]

Huyết áp một trăm mười trên bảy mươi. [DỪNG 0.5s]
Mạch bảy mươi lăm. [DỪNG 1.5s]

Bụng mềm, đau vùng thượng vị khi ấn. [DỪNG 1.5s]

Chẩn đoán: viêm loét dạ dày tá tràng. [DỪNG 1s]

Kê thuốc:
Omeprazole hai mươi miligam, uống sáng trước ăn ba mươi phút, bốn tuần. [DỪNG 0.5s]
Domperidone mười miligam, ba lần mỗi ngày trước ăn. [DỪNG 1s]

Hẹn tái khám sau bốn tuần hỉ.
```

---

### B-03 | Tăng huyết áp | I10 | GIỌNG TP.HCM NHANH | ⭐⭐⭐ Khó

**Đặc điểm phát âm Nam — tốc độ nhanh:**
- Tốc độ 170–190 âm tiết/phút [NHANH toàn bộ]
- Thanh hỏi/ngã gần nhau
- "của" → ngắn gọn
- Bỏ bớt từ hư: "uống một viên" thay "uống một viên mỗi ngày"
- "không" → "hông", "không có" → "hổng có"

**KỊCH BẢN ĐỌC — [NHANH] Giọng Nam:**

```
[NHANH] Bệnh nhân nam, sáu mươi tuổi, lái xe. [DỪNG 1s]
[NHANH] Tái khám huyết áp. Đo lần một: một bảy mươi trên một trăm. [DỪNG 0.5s]
[NHANH] Đo lại: một sáu lăm trên chín lăm. [DỪNG 1s]
[NHANH] Bệnh nhân uống thuốc đều, hông có bỏ. [DỪNG 0.5s]
[NHANH] Hổng đau đầu, hổng chóng mặt. [DỪNG 1.5s]

[NHANH] Đang dùng Amlodipine năm miligam một viên mỗi ngày. [DỪNG 1s]

[NHANH] Huyết áp chưa kiểm soát. [DỪNG 0.5s]
[NHANH] Tăng lên Amlodipine mười miligam. [DỪNG 0.5s]
[NHANH] Thêm Losartan năm mươi miligam, uống sáng. [DỪNG 1s]

[NHANH] Tái khám hai tuần.
```

---

### B-04 | Đái tháo đường | E11.9 | GIỌNG TÂY NAM BỘ | ⭐⭐⭐ Khó

**Đặc điểm Tây Nam Bộ:**
- Tốc độ chậm hơn, 110–130 âm tiết/phút [CHẬM]
- "tôi" → "tui", "bệnh nhân" → "bệnh nhân" (giữ nguyên nhưng âm a khác)
- "không" → "hông" hoặc "hổng"
- Từ địa phương: "ăn cơm" → "dùng cơm", "uống thuốc" → "uống thuốc" (giữ)

**KỊCH BẢN ĐỌC — [CHẬM] Giọng Tây Nam Bộ:**

```
[CHẬM] Bệnh nhân nữ, năm mươi lăm tuổi, có bệnh tiểu đường từ tám năm nay. [DỪNG 2s]
[CHẬM] Tái khám định kỳ. [DỪNG 1s]
[CHẬM] Đường huyết đói sáng nay chín phẩy ba. [DỪNG 0.5s]
[CHẬM] HbA1c tháng rồi tám phẩy hai phần trăm. [DỪNG 1.5s]

[CHẬM] Huyết áp một trăm ba mươi trên tám mươi lăm. [DỪNG 0.5s]
[CHẬM] Mạch tám mươi hai. Cân nặng bảy mươi tám ký. [DỪNG 2s]

[CHẬM] Chẩn đoán: tiểu đường loại hai chưa kiểm soát tốt, biến chứng thần kinh nhẹ. [DỪNG 1.5s]

[CHẬM] Giữ Metformin năm trăm, hai lần mỗi ngày sau ăn. [DỪNG 0.5s]
[CHẬM] Thêm Glimepiride hai miligam, một lần buổi sáng trước ăn. [DỪNG 0.5s]
[CHẬM] Vitamin B tổng hợp, một viên mỗi ngày. [DỪNG 1.5s]

[CHẬM] Hẹn lại một tháng.
```

---

## V. NHÓM C — NGÔN NGỮ KHÓ

---

### C-01 | Thuật ngữ pha tiếng Anh/Pháp | Tim mạch | I25.1 | ⭐⭐⭐ Khó

**Mục tiêu:** Test khả năng nhận diện mixed-language medical terms

**KỊCH BẢN ĐỌC:**

```
Bệnh nhân nam, năm mươi tám tuổi. [DỪNG 1s]
Tiền sử: nhồi máu cơ tim cũ, đã đặt stent động mạch vành hai năm trước. [DỪNG 1.5s]
Vào khám kiểm tra định kỳ. [DỪNG 1s]

Làm ECG hôm nay: nhịp xoang đều, không có ST thay đổi. [DỪNG 1s]
Siêu âm tim tháng trước: EF năm mươi lăm phần trăm, không hở van. [DỪNG 1.5s]

Huyết áp một trăm ba mươi trên tám mươi lăm. [DỪNG 0.5s]
Mạch sáu mươi lăm. SpO2 chín mươi tám phần trăm. [DỪNG 1.5s]

LDL cholesterol kết quả tuần rồi: hai phẩy một mi mol trên lít — đạt mục tiêu. [DỪNG 1.5s]

Chẩn đoán: Bệnh động mạch vành mãn. Sau can thiệp stent. [DỪNG 1s]

Tiếp tục phác đồ:
Aspirin một trăm miligam, uống một lần mỗi ngày sau ăn. [DỪNG 0.5s]
Clopidogrel bảy mươi lăm miligam, uống một lần mỗi ngày. [DỪNG 0.5s]
Atorvastatin bốn mươi miligam, uống tối. [DỪNG 0.5s]
Bisoprolol hai phẩy năm miligam, uống sáng. [DỪNG 0.5s]
Ramipril năm miligam, uống sáng. [DỪNG 1s]

Hẹn tái khám sau ba tháng, làm lại xét nghiệm lipid.
```

**GROUND TRUTH:**
| Field | Giá trị |
|---|---|
| huyet_ap | 130/85 |
| mach | 65 |
| spo2 | 98 |
| chan_doan | Bệnh động mạch vành mãn; Sau can thiệp stent |
| icd10 | I25.1 |
| thuoc[0] | Aspirin 100mg × 1/ngày sau ăn |
| thuoc[1] | Clopidogrel 75mg × 1/ngày |
| thuoc[2] | Atorvastatin 40mg × 1/ngày (tối) |
| thuoc[3] | Bisoprolol 2.5mg × 1/ngày (sáng) |
| thuoc[4] | Ramipril 5mg × 1/ngày (sáng) |
| tai_kham | Sau 3 tháng |

**CHÚ Ý ĐÁNH GIÁ:**
- "ECG", "EF", "stent", "LDL", "SpO2" → phải nhận diện đúng
- Số dạng "55%" → "năm mươi lăm phần trăm" → phải convert đúng
- 5 thuốc cùng lúc → test khả năng xử lý đa thuốc

---

### C-02 | Tên thuốc thương mại | Hô hấp | J45.9 | ⭐⭐ Trung bình

**Mục tiêu:** BS dùng tên thương mại thay INN — pipeline phải map sang INN chuẩn

**KỊCH BẢN ĐỌC:**

```
Bệnh nhân nữ, hai mươi tám tuổi, có tiền sử hen phế quản từ nhỏ. [DỪNG 1.5s]
Hôm nay khó thở nhẹ khi gắng sức, không cơn khó thở lúc nghỉ. [DỪNG 1s]

Huyết áp một trăm mười trên bảy mươi. [DỪNG 0.5s]
Mạch tám mươi. [DỪNG 0.5s]
Nhịp thở mười tám lần mỗi phút. [DỪNG 0.5s]
SpO2 chín mươi sáu phần trăm. [DỪNG 1.5s]

Nghe phổi: có rít nhẹ hai phổi. [DỪNG 1.5s]

Chẩn đoán: Hen phế quản kiểm soát một phần. [DỪNG 1s]

Điều trị:
Tiếp tục xịt Ventolin khi khó thở, tối đa bốn lần mỗi ngày. [DỪNG 0.5s]
Thêm Flixotide năm mươi microgam, xịt hai lần mỗi ngày — sáng và tối.
Súc miệng sau khi xịt. [DỪNG 0.5s]
Uống Singulair mười miligam, mỗi tối trước ngủ. [DỪNG 1s]

Hướng dẫn cách xịt đúng kỹ thuật. [DỪNG 1s]
Tái khám sau một tháng hoặc khi có cơn khó thở nặng.
```

**GROUND TRUTH (sau khi map tên thương mại):**
| Field | Giá trị |
|---|---|
| huyet_ap | 110/70 |
| mach | 80 |
| nhip_tho | 18 |
| spo2 | 96 |
| chan_doan | Hen phế quản kiểm soát một phần |
| icd10 | J45.9 |
| thuoc[0] | Salbutamol (Ventolin) — xịt khi cần × tối đa 4 lần/ngày |
| thuoc[1] | Fluticasone propionate (Flixotide) 50mcg × 2 lần/ngày |
| thuoc[2] | Montelukast (Singulair) 10mg × 1/ngày (tối) |
| tai_kham | Sau 1 tháng |

**CHÚ Ý:** "Ventolin" → Salbutamol | "Flixotide" → Fluticasone | "Singulair" → Montelukast

---

### C-03 | Từ viết tắt y tế VN | Thần kinh | G43.9 | ⭐⭐ Trung bình

**Mục tiêu:** Nhận diện từ viết tắt phổ biến trong y tế VN

**KỊCH BẢN ĐỌC:**

```
Bệnh nhân nữ, bốn mươi lăm tuổi, tiền sử ĐTĐ và THA. [DỪNG 1.5s]
Vào khám đau đầu dữ dội, khởi phát đột ngột hai giờ trước. [DỪNG 1s]
Kèm buồn nôn, sợ ánh sáng. Không có yếu liệt chi, không nói khó. [DỪNG 1.5s]

HA: một trăm sáu mươi trên một trăm. [DỪNG 0.5s]
Mạch: chín mươi. [DỪNG 0.5s]
Nhiệt độ: ba mươi bảy độ. [DỪNG 1.5s]

Khám thần kinh: không dấu thần kinh khu trú, Kernig âm tính. [DỪNG 1.5s]

Loại trừ TBMN cấp. [DỪNG 0.5s]
Chẩn đoán: Migraine có aura, cơn cấp. [DỪNG 1s]

Điều trị cấp cứu tại phòng khám:
Sumatriptan năm mươi miligam, uống ngay một viên. [DỪNG 0.5s]
Metoclopramide mười miligam tiêm bắp. [DỪNG 1s]

Nếu không đỡ sau một giờ hoặc có dấu hiệu bất thường: chuyển cấp cứu BV ngay. [DỪNG 1s]

Hẹn tái khám sau một tuần. Nếu cơn đau nhiều hơn ba lần mỗi tháng sẽ xem xét
điều trị phòng ngừa Propranolol.
```

**GROUND TRUTH:**
| Field | Giá trị |
|---|---|
| huyet_ap | 160/100 |
| mach | 90 |
| nhiet_do | 37.0 |
| tien_su | Đái tháo đường, Tăng huyết áp |
| chan_doan | Migraine có aura cơn cấp |
| icd10 | G43.9 |
| thuoc[0] | Sumatriptan 50mg × 1 viên ngay |
| thuoc[1] | Metoclopramide 10mg tiêm bắp |
| tai_kham | Sau 1 tuần |

**CHÚ Ý:** "ĐTĐ" → Đái tháo đường | "THA" → Tăng huyết áp | "TBMN" → Tai biến mạch máu não | "BV" → Bệnh viện | "HA" → Huyết áp

---

### C-04 | Tự sửa và do dự | Da liễu | L20.9 | ⭐⭐⭐ Khó

**Mục tiêu:** Xử lý self-correction, filler words, disfluency tự nhiên

**KỊCH BẢN ĐỌC:**

```
Bệnh nhân [ừm] nam, [DỪNG 0.5s] à, nữ, hai mươi mốt tuổi. [DỪNG 1s]
Ngứa và nổi mẩn đỏ ở tay, [ừm], hai tay, [DỪNG 0.5s] chân và bụng, ba tuần nay. [DỪNG 1s]
Ngứa nhiều về đêm. [DỪNG 1.5s]

Huyết áp, [DỪNG 0.5s] à... một trăm... một trăm mười trên bảy mươi. [DỪNG 0.5s]
Mạch bảy mươi. Nhiệt độ bình thường, ba mươi sáu phẩy chín. [DỪNG 1.5s]

Khám da: [ừm] mẩn đỏ dạng chàm, bề mặt khô, có vết gãi ở khuỷu tay
và khoeo chân. [DỪNG 1.5s]

Chẩn đoán: [DỪNG 0.5s] [SỬA] à sửa lại — Viêm da cơ địa, [NHẤN] không phải
mề đay nhé. [DỪNG 1s]

Điều trị:
Kem Hydrocortisone một phần trăm, thoa vùng da tổn thương hai lần mỗi ngày. [DỪNG 0.5s]
Loratadine mười miligam, [ừm], uống một lần mỗi ngày, tối trước ngủ. [DỪNG 0.5s]
Kem dưỡng ẩm Cetaphil, thoa toàn thân sau tắm. [DỪNG 1s]

Không dùng xà phòng thơm, không mặc đồ len. [DỪNG 1s]

Tái khám sau hai tuần.
```

**GROUND TRUTH (sau khi lọc disfluency):**
| Field | Giá trị |
|---|---|
| huyet_ap | 110/70 |
| mach | 70 |
| nhiet_do | 36.9 |
| chan_doan | Viêm da cơ địa |
| icd10 | L20.9 |
| thuoc[0] | Hydrocortisone 1% cream × 2 lần/ngày (tại chỗ) |
| thuoc[1] | Loratadine 10mg × 1/ngày (tối) |
| thuoc[2] | Cetaphil moisturizer (dưỡng ẩm) |
| tai_kham | Sau 2 tuần |

**CHÚ Ý:** "à, nữ" → giới tính NỮ (self-correction) | "[SỬA]" → chẩn đoán CUỐI là Viêm da cơ địa

---

### C-05 | Số dạng chữ phức tạp | Tiết niệu | N39.0 | ⭐⭐ Trung bình

**Mục tiêu:** Chuyển đổi số chữ → số: "hai lần rưỡi" → 2.5, "một phần tư" → 0.25

**KỊCH BẢN ĐỌC:**

```
Bệnh nhân nữ, sáu mươi ba tuổi. [DỪNG 1s]
Tiểu buốt, tiểu rắt hai ngày nay. Tiểu mười lần ban ngày, ba lần ban đêm. [DỪNG 1s]
Không sốt, không đau hông lưng. [DỪNG 1.5s]

Xét nghiệm nước tiểu: bạch cầu hai cộng, nitrite dương tính. [DỪNG 1.5s]

Huyết áp một trăm ba mươi trên tám mươi. [DỪNG 0.5s]
Mạch bảy mươi sáu. [DỪNG 0.5s]
Nhiệt độ ba mươi bảy phẩy hai. [DỪNG 1.5s]

Chẩn đoán: Nhiễm khuẩn đường tiết niệu dưới, không biến chứng. [DỪNG 1s]

Điều trị:
Trimethoprim — Sulfamethoxazole, viên tám trăm — một trăm sáu mươi miligam,
uống [NHẤN] hai lần mỗi ngày, trong [NHẤN] ba ngày. [DỪNG 0.5s]
Phenazopyridine hai trăm miligam, uống ba lần mỗi ngày sau ăn, trong hai ngày —
chỉ để giảm đau rát, không phải kháng sinh nhé. [DỪNG 1s]
Uống nhiều nước, tối thiểu một phẩy năm đến hai lít mỗi ngày. [DỪNG 1s]

Tái khám sau ba ngày nếu không đỡ.
```

**GROUND TRUTH:**
| Field | Giá trị |
|---|---|
| huyet_ap | 130/80 |
| mach | 76 |
| nhiet_do | 37.2 |
| chan_doan | Nhiễm khuẩn đường tiết niệu dưới |
| icd10 | N39.0 |
| thuoc[0] | TMP-SMX 800/160mg × 2 lần/ngày × 3 ngày |
| thuoc[1] | Phenazopyridine 200mg × 3 lần/ngày sau ăn × 2 ngày |
| huong_dan | Uống ≥ 1.5–2 lít nước/ngày |
| tai_kham | Sau 3 ngày |

---

## VI. NHÓM D — ĐIỀU KIỆN ÂM THANH KHÓ

> Ghi âm trong điều kiện có nhiễu. Đánh giá độ bền vững của ASR.

---

### D-01 | Tiếng quạt / điều hòa | Viêm phế quản | J20.9 | ⭐⭐ Trung bình

**Điều kiện thu âm:**
- Mở quạt điện hoặc điều hòa để trong phòng
- SNR ước tính: 18–22 dB
- Bật từ trước khi bắt đầu ghi âm, KHÔNG tắt trong khi đọc

**KỊCH BẢN ĐỌC (tốc độ bình thường, nhưng nói rõ hơn):**

```
Bệnh nhân nam, ba mươi tuổi. [DỪNG 1.5s]
Ho khan một tuần, tăng về đêm, không sốt. [DỪNG 1s]
Chảy nước mũi trong, hắt hơi. Không khó thở. [DỪNG 1.5s]

Huyết áp một trăm hai mươi trên bảy lăm. [DỪNG 0.5s]
Mạch tám mươi. [DỪNG 0.5s]
Nhiệt độ ba mươi sáu phẩy tám. [DỪNG 1.5s]

Nghe phổi: thông khí đều, không có ran. [DỪNG 1.5s]

Chẩn đoán: Viêm phế quản cấp do virus. [DỪNG 1s]

Điều trị:
Dextromethorphan mười lăm miligam, uống ba lần mỗi ngày khi ho. [DỪNG 0.5s]
Cetirizine mười miligam, uống một lần mỗi ngày trước ngủ. [DỪNG 0.5s]
Uống nhiều nước, nghỉ ngơi. [DỪNG 1s]
Không cần kháng sinh. [DỪNG 1s]

Tái khám sau một tuần nếu ho không cải thiện hoặc có sốt.
```

**NGƯỠNG PASS nhóm D:** CEER ≤ 2× ngưỡng nhóm A (chấp nhận tăng lỗi do nhiễu)

---

### D-02 | Tiếng gió rít (USB mic) | Tai mũi họng | H66.9 | ⭐⭐⭐ Khó

**Điều kiện thu âm:**
- Mic USB đặt gần cửa sổ hoặc gần quạt để gió thổi qua
- SNR ước tính: 10–15 dB — rất khó cho ASR
- Mục tiêu: đo WER tăng bao nhiêu % so với clean

**KỊCH BẢN ĐỌC:**

```
Bệnh nhân nam, tám tuổi, do bố mẹ đưa đến. [DỪNG 1.5s]
Đau tai phải ba ngày, chảy dịch tai. Không sốt. [DỪNG 1s]
Bé quấy khóc, ăn kém. [DỪNG 1.5s]

Nhiệt độ ba mươi bảy phẩy năm. [DỪNG 0.5s]
Mạch một trăm. [DỪNG 1.5s]

Khám tai phải: màng nhĩ đỏ, phồng, có dịch phía sau.
Tai trái bình thường. [DỪNG 1.5s]

Chẩn đoán: Viêm tai giữa cấp có mủ, tai phải. [DỪNG 1s]

Điều trị:
Amoxicillin bốn mươi miligam trên kilogram mỗi ngày, chia hai lần,
trong mười ngày — trẻ hai mươi lăm kilogram vậy là năm trăm miligam hai lần mỗi ngày. [DỪNG 0.5s]
Paracetamol mười lăm miligam trên kilogram mỗi bốn đến sáu giờ khi đau
hoặc sốt trên ba mươi tám độ. [DỪNG 1s]

Tái khám sau mười ngày kiểm tra tai.
```

**CHÚ Ý ĐÁNH GIÁ:**
- Kịch bản này có tính liều theo cân nặng (mg/kg) → test khả năng xử lý liều nhi khoa
- WER dự kiến tăng 15–25% so với clean do gió rít

---

### D-03 | Nói nhanh — bác sĩ cuối ca | Xương khớp | M10.9 | ⭐⭐⭐ Khó

**Điều kiện:** [NHANH] toàn bộ — > 180 âm tiết/phút
**Bối cảnh:** BS cuối ca, bệnh nhân thứ 40 trong ngày

**KỊCH BẢN ĐỌC [NHANH toàn bộ]:**

```
[NHANH] Bệnh nhân nam, bảy mươi tuổi. [DỪNG 0.5s]
[NHANH] Đau ngón chân cái phải đột ngột đêm qua, sưng đỏ nóng. [DỪNG 0.5s]
[NHANH] Có uống bia hôm qua, khoảng mười lon. [DỪNG 0.5s]
[NHANH] Tiền sử gout ba năm nay, không uống thuốc đều. [DỪNG 1s]

[NHANH] HA một ba mươi trên tám mươi. Mạch tám lăm. [DỪNG 0.5s]
[NHANH] Axit uric máu tuần trước: tám phẩy ba mi mol. [DỪNG 1s]

[NHANH] Khám: ngón chân cái phải sưng to, đỏ, đau khi chạm. [DỪNG 1s]

[NHANH] Chẩn đoán: Gout cấp, ngón chân cái phải. [DỪNG 0.5s]

[NHANH] Điều trị:
Colchicine không phẩy năm miligam, uống hai viên ngay, sau đó một viên
mỗi giờ cho đến khi đỡ đau hoặc tối đa sáu viên trong hai mươi bốn giờ. [DỪNG 0.5s]
[NHANH] Etoricoxib sáu mươi miligam, uống một lần mỗi ngày sau ăn, năm ngày. [DỪNG 0.5s]
[NHANH] Tuyệt đối không uống bia rượu. Uống nhiều nước. [DỪNG 0.5s]

[NHANH] Tái khám một tuần, xem xét thuốc hạ axit uric dài hạn.
```

**GROUND TRUTH:**
| Field | Giá trị |
|---|---|
| huyet_ap | 130/80 |
| mach | 85 |
| chan_doan | Gout cấp ngón chân cái phải |
| icd10 | M10.9 |
| thuoc[0] | Colchicine 0.5mg — 2 viên ngay, sau đó 1 viên/giờ max 6 viên/24h |
| thuoc[1] | Etoricoxib 60mg × 1/ngày sau ăn × 5 ngày |
| tai_kham | Sau 1 tuần |

---

### D-04 | Phòng có vang (reverberation) | Nội tiết | E05.9 | ⭐⭐⭐ Khó

**Điều kiện thu âm:**
- Phòng nền gạch hoa không có rèm, không đồ nội thất hấp âm
- RT60 ước tính: 0.6–1.0 giây
- Mic cách xa người nói: 50–80 cm

**KỊCH BẢN ĐỌC (Nói chậm và rõ hơn bình thường):**

```
[CHẬM] Bệnh nhân nữ, ba mươi hai tuổi, có bướu giáp đa nhân. [DỪNG 2s]
[CHẬM] Hồi hộp, tay run, sụt cân năm kilogram trong hai tháng. [DỪNG 1s]
[CHẬM] Mắt hơi lồi, ngủ kém. [DỪNG 2s]

[CHẬM] TSH: không phẩy không hai mIU trên lít — thấp. [DỪNG 0.5s]
[CHẬM] FT4: ba mươi hai picomol trên lít — cao. [DỪNG 2s]

[CHẬM] Huyết áp một trăm bốn mươi trên chín mươi. [DỪNG 0.5s]
[CHẬM] Mạch một trăm lẻ năm. Nhịp thở hai mươi hai. [DỪNG 2s]

[CHẬM] Chẩn đoán: Cường giáp, nhiều khả năng bệnh Basedow. [DỪNG 1.5s]

[CHẬM] Bắt đầu điều trị:
[CHẬM] Methimazole hai mươi miligam, uống hai lần mỗi ngày — tổng bốn mươi miligam mỗi ngày. [DỪNG 0.5s]
[CHẬM] Propranolol bốn mươi miligam, uống hai lần mỗi ngày. [DỪNG 1.5s]

[CHẬM] Cần làm thêm xét nghiệm kháng thể TRAb và siêu âm tuyến giáp. [DỪNG 1.5s]

[CHẬM] Tái khám sau bốn tuần kiểm tra chức năng tuyến giáp.
```

---

## VII. NHÓM E — CA LÂM SÀNG PHỨC TẠP

---

### E-01 | Đa bệnh lý cao tuổi | Hỗn hợp | ⭐⭐⭐⭐ Rất khó

**Mục tiêu:** Test khả năng xử lý nhiều bệnh + nhiều thuốc cùng lúc

**KỊCH BẢN ĐỌC:**

```
Bệnh nhân nam, bảy mươi lăm tuổi, về hưu. [DỪNG 1.5s]
Tiền sử: tăng huyết áp mười lăm năm, đái tháo đường type hai mười năm,
suy thận mãn độ ba, rung nhĩ không do bệnh van tim. [DỪNG 2s]

Tái khám định kỳ, không có triệu chứng mới. [DỪNG 1s]

Huyết áp lần một: một trăm bốn mươi lăm trên chín mươi. [DỪNG 0.5s]
Lần hai: một trăm bốn mươi trên tám mươi lăm. [DỪNG 0.5s]
Mạch bảy mươi, không đều. [DỪNG 0.5s]
Cân nặng bảy mươi hai kilogram. [DỪNG 1.5s]

Xét nghiệm tuần trước:
Đường huyết đói: tám phẩy một. HbA1c: bảy phẩy sáu. [DỪNG 0.5s]
Creatinine: một trăm tám mươi micromol — GFR ước tính ba mươi lăm. [DỪNG 0.5s]
Kali: bốn phẩy hai. Natri: một trăm ba mươi tám. [DỪNG 1.5s]

Siêu âm tim tháng trước: EF bốn mươi lăm phần trăm. [DỪNG 1.5s]

Chẩn đoán chính:
Một — Tăng huyết áp, kiểm soát chưa đạt mục tiêu. [DỪNG 0.5s]
Hai — Đái tháo đường type hai, kiểm soát trung bình. [DỪNG 0.5s]
Ba — Suy thận mãn độ ba. [DỪNG 0.5s]
Bốn — Rung nhĩ mãn. [DỪNG 1.5s]

Duy trì phác đồ hiện tại:
Amlodipine mười miligam, một lần mỗi ngày sáng. [DỪNG 0.5s]
Losartan năm mươi miligam, một lần mỗi ngày sáng. [DỪNG 0.5s]
Furosemide hai mươi miligam, một lần mỗi ngày sáng khi nặng hơn ba kilogram. [DỪNG 0.5s]
Metformin năm trăm miligam, hai lần mỗi ngày sau ăn —
[SỬA] à sửa lại — bệnh nhân GFR ba mươi lăm, ngưng Metformin, thay bằng
Glipizide năm miligam hai lần mỗi ngày trước ăn. [DỪNG 0.5s]
Apixaban hai phẩy năm miligam, hai lần mỗi ngày — do rung nhĩ và suy thận. [DỪNG 0.5s]
Atorvastatin hai mươi miligam, uống tối. [DỪNG 1.5s]

Hẹn tái khám sau một tháng, mang kết quả xét nghiệm.
```

**GROUND TRUTH:**
| Field | Giá trị |
|---|---|
| huyet_ap | 145/90 (lần 1) / 140/85 (lần 2) |
| mach | 70 (không đều) |
| can_nang | 72 |
| chan_doan | THA; ĐTĐ type 2; Suy thận mãn độ 3; Rung nhĩ mãn |
| thuoc[0] | Amlodipine 10mg × 1/ngày (sáng) |
| thuoc[1] | Losartan 50mg × 1/ngày (sáng) |
| thuoc[2] | Furosemide 20mg × 1/ngày (khi nặng > 3kg) |
| thuoc[3] | Glipizide 5mg × 2/ngày trước ăn (THAY Metformin) |
| thuoc[4] | Apixaban 2.5mg × 2/ngày |
| thuoc[5] | Atorvastatin 20mg × 1/ngày (tối) |
| tai_kham | Sau 1 tháng |

**CHÚ Ý:** Self-correction Metformin → Glipizide phải được xử lý đúng (giá trị CUỐI là Glipizide)

---

### E-02 | Ca cấp cứu nhẹ — nhịp tim nhanh | Tim mạch | I47.1 | ⭐⭐⭐⭐ Rất khó

**Mục tiêu:** BS nói nhanh, căng thẳng. Nhiều chỉ số sinh hiệu, quyết định nhanh.

**KỊCH BẢN ĐỌC [NHANH, giọng khẩn]:**

```
[NHANH] Bệnh nhân nữ, bốn mươi tuổi, vào cấp cứu vì hồi hộp đột ngột
mười lăm phút trước, choáng váng. [DỪNG 1s]
[NHANH] Không đau ngực, không khó thở, không ngất. [DỪNG 1s]

[NHANH] ECG ngay: nhịp nhanh kịch phát trên thất, tần số một bảy mươi lăm. [DỪNG 1s]
[NHANH] Huyết áp một trăm mười trên bảy mươi — còn ổn định. [DỪNG 0.5s]
[NHANH] SpO2 chín mươi chín. Không suy tim cấp. [DỪNG 1.5s]

[NHANH] Thực hiện nghiệm pháp Valsalva: chưa chuyển nhịp. [DỪNG 1s]

[NHANH] Điều trị:
[NHANH] Adenosine sáu miligam tiêm tĩnh mạch nhanh, sẵn sàng tiêm lần hai
mười hai miligam nếu không đáp ứng. [DỪNG 1.5s]

[NHANH] Theo dõi monitor liên tục. Đặt đường truyền tĩnh mạch. [DỪNG 1s]

[NHANH] Chẩn đoán: Nhịp nhanh kịch phát trên thất. [DỪNG 1s]

[NHANH] Nếu không đáp ứng sau hai liều Adenosine — hội chẩn tim mạch can thiệp.
[NHANH] Nếu chuyển nhịp — quan sát hai giờ, cho về nếu ổn,
[NHANH] kê Verapamil tám mươi miligam hai lần mỗi ngày, hẹn tim mạch một tuần.
```

---

### E-03 | Tái khám — so sánh với lần trước | Phổi | J44.1 | ⭐⭐⭐ Khó

**Mục tiêu:** BS so sánh diễn tiến. NER phải phân biệt giá trị hiện tại vs trước đây.

**KỊCH BẢN ĐỌC:**

```
Bệnh nhân nam, sáu mươi lăm tuổi, COPD giai đoạn hai, tái khám sau
đợt cấp cách đây một tháng. [DỪNG 1.5s]

Lần trước: khó thở độ ba, SpO2 tám mươi chín, phải nhập viện bốn ngày. [DỪNG 1s]
Hôm nay: khó thở cải thiện nhiều, độ một đến hai, lên cầu thang được ba tầng. [DỪNG 1.5s]

Đo SpO2 hôm nay: chín mươi lăm phần trăm khi nghỉ. [DỪNG 0.5s]
Huyết áp một trăm ba mươi trên tám mươi. [DỪNG 0.5s]
Mạch tám mươi. Nhịp thở hai mươi. [DỪNG 1.5s]

Đang dùng:
Tiotropium mười tám microgam, hít một lần mỗi ngày sáng — đều. [DỪNG 0.5s]
Salmeterol năm mươi microgam kết hợp Fluticasone năm trăm microgam — hít hai lần mỗi ngày. [DỪNG 1.5s]

Đánh giá: đợt cấp lui, phổi cải thiện tốt. [DỪNG 1s]

Chẩn đoán: COPD giai đoạn hai, sau đợt cấp, đang cải thiện. [DỪNG 1s]

Tiếp tục phác đồ hiện tại. [DỪNG 0.5s]
Thêm Carbocisteine năm trăm miligam, uống ba lần mỗi ngày trong một tháng
để long đờm. [DỪNG 1s]
Chương trình phục hồi chức năng hô hấp nếu có điều kiện. [DỪNG 1s]

Tái khám sau ba tháng hoặc khi có đợt cấp mới.
```

**GROUND TRUTH:**
| Field | Giá trị |
|---|---|
| spo2 | 95 (hiện tại) — KHÔNG dùng 89 (lần trước) |
| huyet_ap | 130/80 |
| mach | 80 |
| nhip_tho | 20 |
| chan_doan | COPD giai đoạn 2 sau đợt cấp |
| icd10 | J44.1 |
| thuoc[0] | Tiotropium 18mcg × 1/ngày (sáng) |
| thuoc[1] | Salmeterol 50mcg + Fluticasone 500mcg × 2/ngày |
| thuoc[2] | Carbocisteine 500mg × 3/ngày × 1 tháng |
| tai_kham | Sau 3 tháng |

**CHÚ Ý:** SpO2 89% là lần TRƯỚC — NER phải lấy SpO2 HIỆN TẠI là 95%

---

## VIII. KHUNG ĐÁNH GIÁ

### 8.1 Chạy đánh giá

```bash
# Tạo audio từ script (text-to-speech để test pipeline trước khi có audio thật)
python tools/gen_test_audio.py --input data/audio/test_corpus_ground_truth.json

# Chạy CEER trên corpus
python tools/bench_ceer.py --full --gt data/audio/test_corpus_ground_truth.json

# Report chi tiết
python tools/bench_ceer.py --report --output results/corpus_eval_YYYYMMDD.json
```

### 8.2 Ma trận đánh giá

| Kịch bản | Vitals | Thuốc | Chẩn đoán | Tái khám | WER | PASS? |
|---|---|---|---|---|---|---|
| A-01 | ? | ? | ? | ? | ? | ? |
| A-02 | ? | ? | ? | ? | ? | ? |
| ... | | | | | | |
| **TB nhóm A** | | | | | | |
| **TB nhóm B** | | | | | | |
| **TB nhóm C** | | | | | | |
| **TB nhóm D** | | | | | | |
| **TB nhóm E** | | | | | | |
| **TỔNG** | | | | | | |

### 8.3 Ngưỡng PASS theo nhóm

| Nhóm | Vitals CEER | Thuốc CEER | Chẩn đoán CEER | Tái khám CEER |
|---|---|---|---|---|
| A (cơ bản) | < 0.05 | < 0.10 | < 0.10 | < 0.30 |
| B (giọng) | < 0.08 | < 0.15 | < 0.10 | < 0.40 |
| C (thuật ngữ) | < 0.08 | < 0.15 | < 0.15 | < 0.40 |
| D (nhiễu) | < 0.10 | < 0.20 | < 0.20 | < 0.50 |
| E (phức tạp) | < 0.08 | < 0.15 | < 0.15 | < 0.40 |

### 8.4 Điểm chất lượng âm thanh (ITU-T P.800 MOS)

Sau khi ghi âm, tự đánh giá:

| MOS | Mô tả |
|---|---|
| 5 — Excellent | Hoàn toàn trong, không có nhiễu |
| 4 — Good | Có nhiễu nhẹ, nghe rõ ràng |
| 3 — Fair | Nhiễu trung bình, vẫn nghe được |
| 2 — Poor | Nhiều nhiễu, khó nghe |
| 1 — Bad | Không thể nghe rõ |

**Yêu cầu:** Nhóm A cần MOS ≥ 4 | Nhóm D chủ ý MOS 2–3 để test robustness

### 8.5 Định nghĩa CEER cho corpus này

```
CEER per field = 1 - (số tokens khớp ≥ 60%) / (số tokens ground truth)

Khớp = token_match(predicted, reference, threshold=0.6)
  → Fuzzy match để xử lý biến thể chính tả nhỏ

Thuốc: tên + liều phải khớp CÙNG entry
  → "Amoxicillin 500mg" ≠ "Amoxicillin 250mg" (sai liều = FAIL)
  → "Amoxicillin 500mg" = "amoxicillin 500 mg" (whitespace/case = PASS)
```

---

## IX. CHECKLIST GHI ÂM

### Trước khi ghi
- [ ] Chọn phòng ít vang (có rèm, đồ đạc)
- [ ] Kiểm tra mic: ghi thử 10 giây, nghe lại
- [ ] Đặt mic đúng khoảng cách (15–25 cm)
- [ ] Đọc qua kịch bản một lần trước khi ghi
- [ ] Ghi tên file: `TC-A01_clean_HN_take1.wav`

### Trong khi ghi
- [ ] Đọc đúng ký hiệu pause (không bỏ qua)
- [ ] Giữ tốc độ phù hợp nhóm (A: bình thường, D03: nhanh)
- [ ] Không ho, không tiếng ồn đột ngột giữa câu
- [ ] Nếu đọc sai câu quan trọng → dừng, ghi lại từ đầu
- [ ] Ghi ít nhất 2 takes cho mỗi kịch bản

### Sau khi ghi
- [ ] Nghe lại take tốt nhất
- [ ] Điền ground truth vào `test_corpus_ground_truth.json`
- [ ] Note MOS score (1–5) cho file đó
- [ ] Upload vào `data/audio/corpus/TC-XXX/`

### Cấu trúc folder
```
data/audio/corpus/
├── TC-A01/
│   ├── TC-A01_clean_HN_take1.wav  (dùng)
│   ├── TC-A01_clean_HN_take2.wav  (backup)
│   └── metadata.json
├── TC-A02/
│   └── ...
└── test_corpus_ground_truth.json  (ground truth tổng hợp)
```

---

## X. GROUND TRUTH JSON FORMAT

```json
{
  "corpus_version": "1.0",
  "created": "2026-06-08",
  "test_cases": [
    {
      "id": "TC-A01",
      "nhom": "A",
      "benh": "Viêm họng cấp",
      "icd10": "J02.9",
      "giong": "Hà Nội",
      "dieu_kien": "clean",
      "do_kho": "easy",
      "audio_file": "corpus/TC-A01/TC-A01_clean_HN_take1.wav",
      "mos": 4.5,
      "ground_truth": {
        "sinh_hieu": {
          "huyet_ap": "120/80",
          "mach": 80,
          "nhiet_do": 37.8,
          "can_nang": 70
        },
        "chan_doan": "Viêm họng cấp",
        "thuoc": [
          {"ten": "Amoxicillin", "lieu": "500mg", "duong": "uống", "tan_suat": "3 lần/ngày", "thoi_gian": "5 ngày"},
          {"ten": "Paracetamol", "lieu": "500mg", "duong": "uống", "chi_dinh": "khi sốt >38°C"}
        ],
        "tai_kham": "5 ngày"
      }
    }
  ]
}
```

---

*CLINICAL_TEST_CORPUS_VN v1.0 | 2026-06-08 | MediVoice VN*
*Tham chiếu: i2b2/n2c2 | VLSP 2018 | ITU-T P.800 | ICD-10-VN QĐ5837 | TT32/2023*
