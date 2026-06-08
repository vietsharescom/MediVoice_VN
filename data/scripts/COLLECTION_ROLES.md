# Data Collection — Vai trò & Nhiệm vụ từng nhóm
# MediVoice VN Training Data v0.1

---

## Tổng quan hệ thống

```
NHÓM A — Andy (Lead)          : Tạo scripts, QC, upload, analysis
NHÓM B — Người nhà / Bạn bè  : Thu âm đa dạng giọng, đọc scripts
NHÓM C — Người Trung / Huế   : Thu âm giọng Trung đặc biệt
NHÓM D — Người Nam            : Thu âm giọng Nam
NHÓM E — Tình nguyện viên     : Annotation (gán nhãn text, không cần ghi âm)

Quy trình:
Script → Thu âm → Upload demo app → AI process → Review → Lưu JSON → Analysis
                                                    ↑
                                          Nhóm A/E annotation
```

---

## NHÓM A — Andy (Lead & QC)

**Làm gì:**
- Tạo và review scripts (templates bên dưới)
- Ghi âm Take 1 (chuẩn) + Take 2 (tự nhiên có ừm/dừng) cho TẤT CẢ scripts
- Upload lên demo app → xem kết quả → điền field_eval
- Download JSON từ Drive → phân tích accuracy
- QC audio từ nhóm khác trước khi dùng

**Lưu file tại:** `data/recordings/by_disease/` hoặc `by_drug_hard/`

**Đặt tên:** `{SCRIPT_ID}_{andy}_{YYYYMMDD}_T{take}.wav`

**Template script Andy tạo:** Xem mục "SCRIPT TEMPLATE" bên dưới

---

## NHÓM B — Người nhà / Bạn bè (Diverse Speakers)

**Yêu cầu:**
- Ít nhất 3 người, giọng khác nhau (tuổi, giới, accent)
- KHÔNG cần biết y tế — chỉ cần đọc như đang thuyết trình
- Lý tưởng: 1 người Bắc + 1 người Nam + 1 người Trung

**Làm gì:**
1. Nhận script từ Andy (file .txt)
2. Đọc phần "NỘI DUNG ĐỌC" — đọc tự nhiên, không robot
3. Lần 1: đọc chuẩn, rõ từng từ
4. Lần 2: đọc tự nhiên như đang nói chuyện (cho phép "ừm", dừng, sửa)
5. Lưu file WAV, gửi cho Andy qua Zalo/email

**Hướng dẫn ghi âm:**
- Dùng điện thoại: Voice Memo (iPhone) hoặc Samsung Voice Recorder
- Cầm phone cách miệng 20-30cm
- Phòng yên tĩnh (hoặc nếu muốn: phòng có tiếng quạt → ghi chú)
- KHÔNG cần mic chuyên nghiệp

**Template nhận script:**
```
Anh/chị ơi, mình nhờ anh/chị đọc đoạn này 2 lần nhé:
Lần 1: đọc rõ ràng, chậm rãi
Lần 2: đọc tự nhiên như đang nói chuyện

[paste nội dung từ file .txt]

Lưu file âm thanh rồi gửi lại cho mình nhé. Cảm ơn!
```

**Lưu file tại:** Gửi cho Andy → Andy lưu vào `data/recordings/`

---

## NHÓM C — Người Trung / Huế / Đà Nẵng

**Tại sao quan trọng:**
Đây là pilot chính (Đà Nẵng). Giọng Trung rất đặc biệt:
- "răng rứa hỉ mô chi" — từ địa phương
- Âm 'l/r' đặc trưng: Losartan → "Rô sa tang"
- Thanh điệu khác: hỏi/ngã phẳng hơn

**Làm gì:**
1. Đọc scripts như Nhóm B
2. THÊM: sau mỗi script, nói thêm 30 giây hội thoại bác sĩ-bệnh nhân bằng giọng Huế/Đà Nẵng thật

**Ví dụ hội thoại Trung cần thu:**
```
"Răng anh đau rứa? Đau mô? Huyết áp cao ni uống thuốc ni hỉ.
Losartan ni anh uống buổi tối. Tái khám chỗ ni rứa."
```

**Lưu file tại:** `data/recordings/by_accent/mien_trung/`
**Đặt tên:** `{SCRIPT_ID}_trung_{name}_{date}_T{take}.wav`

---

## NHÓM D — Người Nam / Sài Gòn

**Tại sao quan trọng:**
Pilot thứ 2 (Sài Gòn BS partner). Giọng Nam:
- Nói nhanh, nuốt âm cuối
- "huyết áp" → "huết ép"
- "nghen, nè, ha" cuối câu

**Làm gì:**
1. Đọc scripts như Nhóm B
2. THÊM: nói tự nhiên kiểu Nam sau mỗi script 20 giây

**Ví dụ hội thoại Nam cần thu:**
```
"Anh uống Losartan buổi tối nè. Amlodipine buổi sáng nghen.
Tái khám 4 tuần sau ha. Có gì không ổn thì ghé lại nè."
```

**Lưu file tại:** `data/recordings/by_accent/mien_nam/`
**Đặt tên:** `{SCRIPT_ID}_nam_{name}_{date}_T{take}.wav`

---

## NHÓM E — Annotation (Tình nguyện viên, không cần ghi âm)

**Yêu cầu:**
- Biết tiếng Việt, hiểu cơ bản về y tế là lợi thế
- Có thể là sinh viên y, y tá, người thân BS
- Làm online, mỗi session 30-60 phút

**Làm gì:**
1. Đọc transcript (text) từ Drive
2. Dán nhãn entities theo hướng dẫn:
   - `[DRUG]Amlodipine[/DRUG]`
   - `[DOSE]5mg[/DOSE]`
   - `[VITAL_BP]145/90[/VITAL_BP]`
   - `[DIAGNOSIS]Tăng huyết áp độ 2[/DIAGNOSIS]`
   - `[ICD]I10[/ICD]`
   - `[FOLLOW_UP]4 tuần[/FOLLOW_UP]`
3. Đánh dấu từ không rõ: `[UNCLEAR]...text...[/UNCLEAR]`
4. Ghi chú nếu phát hiện lỗi y tế

**Tool:** Google Docs với Track Changes hoặc tool label đơn giản
**Volume target:** 10 transcripts/người/ngày = ~2 giờ

---

## SCRIPT TEMPLATE — Andy dùng để tạo script mới

```
SCRIPT ID: {CHUYÊN_KHOA}-{NNN}
CHUYÊN KHOA: [Tên chuyên khoa]
TIÊU ĐỀ: [Mô tả ngắn ca bệnh]
ĐỘ KHÓ: ⭐ đến ⭐⭐⭐⭐⭐
THỜI GIAN ĐỌC ƯỚC TÍNH: {N}–{M} giây

GHI CHÚ BS (hướng dẫn người đọc):
- Tên thuốc khó: [tên thuốc] — nói 2 lần, chậm rãi
- Từ chuyên môn: [từ] — nhấn mạnh, dừng sau
- Sinh hiệu: đọc theo thứ tự: HA → mạch → nhiệt độ → cân nặng

GROUND TRUTH:
  chan_doan: [chẩn đoán chuẩn]
  icd: [mã ICD-10-VN]
  sinh_hieu: {huyet_ap: "X/Y", mach: N, nhiet_do: N.N, can_nang: N}
  thuoc: [Tên 1 liều 1] / [Tên 2 liều 2] / ...
  tai_kham: [thời gian]

THÔNG TIN BỆNH NHÂN MẪU:
  Tên: [tên giả]
  Tuổi: [tuổi], Giới: [Nam/Nữ]
  Tiền sử: [tiền sử liên quan]

═══════════════════════════════════════════════
NỘI DUNG ĐỌC (đọc tự nhiên theo phong cách BS):
═══════════════════════════════════════════════

[Nội dung — bao gồm:
1. Giới thiệu bệnh nhân
2. Lý do đến khám / triệu chứng
3. Sinh hiệu (HA - mạch - nhiệt độ - cân)
4. Chẩn đoán (NHẤN MẠNH, nói 2 lần nếu từ khó)
5. Đơn thuốc (mỗi thuốc: tên x2 + liều)
6. Tái khám
7. Dặn dò thêm (tùy chọn)]
```

---

## MANIFEST.csv — Index tất cả files

```csv
file_path,script_id,speaker_id,accent,gender,age_group,environment,take_type,date,duration_sec,quality_flag
recordings/by_disease/tang_huyet_ap/HA-001_andy_20260608_T1.wav,HA-001,andy,canada_en,M,40s,quiet,scripted,2026-06-08,47,OK
recordings/by_disease/tang_huyet_ap/HA-001_andy_20260608_T2.wav,HA-001,andy,canada_en,M,40s,quiet,natural,2026-06-08,53,OK
```

**Các trường quan trọng:**
- `accent`: canada_en / mien_bac / mien_trung_hue / mien_trung_danang / mien_nam_sg / mien_nam_delta
- `take_type`: scripted (đọc chuẩn) / natural (có disfluency) / drill (luyện thuốc)
- `environment`: quiet / fan_noise / multi_person / outdoor / clinic_ambient
- `quality_flag`: OK / REDO (âm thanh kém) / PARTIAL (thiếu nội dung)
