# SEMI_SYNTHETIC_DATA_PLAN.md
# Kế hoạch Dữ liệu Bán Tổng Hợp — MediVoice VN
# Thay thế chiến lược: 1 cơ sở/1 giọng → 4 giọng vùng miền trong 1 ngày
# v1.0 | 2026-06-09

> ⚠️ NOTE: Andy có báo cáo Grok từ chiều nay — gửi lại Claude để tích hợp nếu cần điều chỉnh tiêu chuẩn.

---

## VẤN ĐỀ GỐC RỄ

| Vấn đề | Hậu quả |
|---|---|
| 1 pilot Đà Nẵng | Chỉ có giọng Trung (một vùng) |
| Thu âm thật chậm | Mất 1–3 tháng mới đủ mẫu |
| Không kiểm soát nội dung | Ground truth không chuẩn, CEER không đo được |
| 1 bác sĩ | Pipeline overfit giọng đó, không generalize |

---

## GIẢI PHÁP — Semi-Synthetic (Human-Read Scripted)

```
4 người đọc × 5 kịch bản = 20 recordings có kiểm soát
→ 4 accent khác nhau với CÙNG ground truth
→ Calibrate CEER per entity per region
→ Tune parameters TRƯỚC khi vào pilot thật
→ Có thể hoàn thành trong 1 ngày làm việc
```

**Tại sao "semi-synthetic" chứ không phải TTS?**
TTS (gen_test_audio.py) = giọng máy → không test được accent thật.
Semi-synthetic = người thật đọc script soạn sẵn → có accent thật + kiểm soát nội dung.

---

## KIẾN TRÚC 3 GIAI ĐOẠN

```
GIAI ĐOẠN 1 — Calibration (1 ngày, LÀM NGAY)
  Input:  4 người đọc 5 kịch bản soạn sẵn = 20 recordings
  Output: CEER baseline per entity × per region
  Action: Tune drug aliases, number regex, ICD fuzzy threshold

GIAI ĐOẠN 2 — Validation (Pilot thật, 2–4 tuần)
  Input:  BS pilot nói tự nhiên (không theo script)
  Output: CEER thật trong clinical environment
  Action: Confirm calibration đúng, thu mẫu đa dạng

GIAI ĐOẠN 3 — Fine-tuning (Sau 50h+ audio thật)
  Input:  BENCH-002 data từ pilot
  Output: Fine-tuned PhoWhisper + NER
  Action: TRAIN-001 + TRAIN-002
```

---

## 4 DOCTOR PERSONAS

| ID | Tên gọi | Vùng | Tốc độ | Đặc trưng chính |
|---|---|---|---|---|
| HN | BS Bắc | Hà Nội | 130–150 âm/phút | Formal, học thuật, "ừ/thì/ờ", "kê đơn" |
| SG | BS Sài Gòn | TP.HCM | 170–190 âm/phút | Nhanh, "hông/hổng", "kê toa", bỏ bớt từ hư |
| CT | BS Cần Thơ | Tây Nam Bộ | 110–130 âm/phút | Chậm, "tui/dùng cơm/hổng", "cho thuốc" |
| CA | BS Canada | Việt kiều | 130–150 âm/phút | Code-switch EN/VI, "euh/so", clinical terms EN |

---

## 5 KỊCH BẢN CHUẨN (SAME GROUND TRUTH × 4 VERSIONS)

| ID | Bệnh | ICD-10-VN | Thời lượng | Entity focus |
|---|---|---|---|---|
| SC-01 | Viêm họng cấp | J02.9 | ~45s | 4 vitals + 2 thuốc + tai_kham |
| SC-02 | Viêm loét dạ dày | K25.9 | ~50s | 3 thuốc (stop 1) + tai_kham |
| SC-03 | Tăng huyết áp | I10 | ~55s | Điều chỉnh liều + thêm thuốc |
| SC-04 | ĐTĐ type 2 | E11.9 | ~65s | Multi-thuốc + biến chứng thần kinh |
| SC-05 | Gout cấp | M10.9 | ~50s | Liều phức tạp (Colchicine step-down) |

---

## TIÊU CHUẨN CHẤT LƯỢNG KỊCH BẢN

### TC-1: Tính đại diện lâm sàng
- [ ] Bệnh nằm trong top 20 phổ biến phòng mạch tư VN
- [ ] Liều thuốc theo phác đồ VN hiện hành (không phải US/EU protocol)
- [ ] ICD-10-VN (QĐ5837) — không phải ICD-10-CM Mỹ
- [ ] Thuật ngữ: cách BS VN thực nói (không phải văn viết sách giáo khoa)
- [ ] Số phải viết bằng chữ: "một trăm hai mươi" không phải "120"

### TC-2: Tính đại diện giọng vùng miền
- [ ] Tốc độ đúng theo bảng (HN/CT/SG/CA)
- [ ] Có ≥ 2 regional markers tự nhiên per script
- [ ] Không đọc ký hiệu [DỪNG] [NHANH] [CHẬM] thành tiếng — thực hiện thật
- [ ] Pauses tự nhiên, không đọc liên tục như robot

### TC-3: Tính đa dạng ngôn ngữ (thiết kế sẵn trong scripts)
- [ ] HN dùng "kê đơn" | SG/CT dùng "kê toa" hoặc "cho thuốc" | CA dùng "prescription"
- [ ] Có tên INN chuẩn (Amoxicillin, Metformin...) — không dùng brand name trong A-E scripts
- [ ] Có viết tắt y tế VN khi tự nhiên: ĐTĐ, THA, HA, BN, HbA1c, BP, SpO2

### TC-4: Tính tự nhiên (naturalness)
- [ ] Có fillers phù hợp vùng (ừ/thì Bắc | hả/nha Nam SG | ờ/dó TNBộ | euh/so Canada)
- [ ] Có ≥ 1 self-correction hoặc ngập ngừng trong bộ 5 scripts của mỗi BS
- [ ] Câu không quá chính xác như đọc văn bản — cho phép lược bỏ từ hư tự nhiên

### TC-5: Chất lượng ghi âm
- [ ] WAV 16kHz mono 16-bit (hoặc để nguyên, pipeline L0 tự convert)
- [ ] SNR > 25dB — phòng yên tĩnh, không quạt/điều hòa chạy
- [ ] Mic cách miệng 15–25 cm
- [ ] Ít nhất 2 takes, chọn take tốt hơn
- [ ] File name chuẩn: `SC01_HN_take1.wav`, `SC03_SG_take2.wav`...

### TC-6: Ground truth (Accuracy)
- [ ] Tất cả entries trong `groundtruth_all.json` đã được xác nhận lâm sàng trước khi thu âm
- [ ] Liều thuốc trong ground truth khớp chính xác với script
- [ ] Nếu script có regional variant (vd: "tiểu đường" thay "đái tháo đường") → ground truth vẫn là tên chuẩn

---

## BẢNG REGIONAL LINGUISTIC MARKERS — Tiêu chuẩn

| Đặc điểm | Hà Nội | TP.HCM | Cần Thơ | Canada (Việt kiều) |
|---|---|---|---|---|
| **Tốc độ** | 130–150 | 170–190 | 110–130 | 130–150 |
| **Filler chính** | ừ, thì, ờ, à | hả, nha, đó, vậy | ờ, nha, dó | euh, so, basically |
| **"Không"** | không | hông / hổng | hổng | không |
| **"Bệnh nhân"** | bệnh nhân | bệnh nhân | bệnh nhân | bệnh nhân / patient |
| **"Kê đơn"** | kê đơn | kê toa | cho thuốc / điều trị | prescription |
| **"Ăn"** | ăn | ăn | dùng cơm (cho bữa ăn) | ăn |
| **"Uống thuốc"** | uống thuốc | uống thuốc | uống thuốc | uống thuốc / take medication |
| **Y thuật ngữ** | Việt chuẩn | Việt chuẩn | Việt chuẩn | VN + EN (ECG/BP/HbA1c) |
| **Ngưng thuốc** | ngưng / dừng | ngưng / bỏ | ngưng | stop / ngưng |

---

## GROUND TRUTH CHUẨN — 5 KỊCH BẢN

*(Dùng chung cho tất cả 4 doctors — thay đổi audio_file path theo region)*

| Script | Vitals | Chan doan (chuẩn) | ICD | Thuoc | Tai kham |
|---|---|---|---|---|---|
| SC-01 | HA 120/80, M 80, T 37.8, CN 70 | Viêm họng cấp | J02.9 | Amoxicillin 500mg×3/ngày×5ngày; Paracetamol 500mg khi sốt >38°C | 5 ngày |
| SC-02 | HA 110/70, M 75 | Viêm loét dạ dày tá tràng | K25.9 | Omeprazole 20mg×1/ngày trước ăn 30'×4 tuần; Domperidone 10mg×3/ngày trước ăn; STOP Ibuprofen | 4 tuần |
| SC-03 | HA 170/100 (lần 1), 165/95 (lần 2) | Tăng huyết áp | I10 | Amlodipine 10mg×1/ngày (tăng từ 5mg); Losartan 50mg×1/ngày sáng (thêm mới) | 2 tuần |
| SC-04 | HA 130/85, M 82, CN 78 | Đái tháo đường type 2; Biến chứng thần kinh ngoại biên nhẹ | E11.9 | Metformin 500mg×2/ngày sau ăn; Glimepiride 2mg×1/ngày sáng trước ăn; Vitamin B1B6B12×1/ngày | 1 tháng |
| SC-05 | HA 130/80, M 85 | Gout cấp ngón chân cái phải | M10.9 | Colchicine 0.5mg: 2 viên ngay → 1viên/giờ max 6 viên/24h; Etoricoxib 60mg×1/ngày sau ăn×5ngày | 1 tuần |

---

## KẾ HOẠCH THU ÂM 1 NGÀY

### Chuẩn bị (30 phút trước khi bắt đầu)
- [ ] In `docs/dev/RECORDING_SCRIPTS_4BS.md` — 1 bản riêng mỗi BS (chỉ in section của họ)
- [ ] Test mic + Audacity/Voice Memo trên máy từng người
- [ ] Mỗi người đọc thử SC-01 1 lần — không record — để quen với ký hiệu
- [ ] Kiểm tra SNR: record 5 giây im lặng, kiểm tra noise floor < -40dBFS

### Thu âm (~3–4 giờ, 4 người song song nếu có đủ mic)
```
Mỗi người:
  5 scripts × 2 takes = 10 files
  Thời gian: ~30–40 phút ghi + 10 phút kiểm tra

Tổng: 4 × 10 = 40 files
Naming: SC01_HN_take1.wav | SC01_SG_take2.wav | SC03_CT_take1.wav ...
```

### Sau thu âm (30 phút)
- [ ] Nghe lại take 1 và 2, đánh dấu take tốt hơn
- [ ] Note MOS score tự đánh giá (1–5) cho mỗi file
- [ ] Upload vào `data/audio/corpus/semi_synthetic/`
- [ ] Điền `metadata.json` (region, take, MOS, ghi chú)

---

## CALIBRATION WORKFLOW

### Step 1 — Chạy pipeline trên 20 recordings chính (take tốt nhất)

```bash
python -X utf8 tools/bench_ceer.py --full --gt data/audio/corpus/semi_synthetic/groundtruth_all.json
```

### Step 2 — Phân tích CEER per entity × per region

| Entity | HN | SG | CT | CA | Target | Action nếu fail |
|---|---|---|---|---|---|---|
| huyet_ap | ? | ? | ? | ? | < 0.05 | Tune BP regex (l1c_ner.py) |
| mach | ? | ? | ? | ? | < 0.05 | Tune mach regex |
| chan_doan | ? | ? | ? | ? | < 0.10 | Tune ICD fuzzy threshold |
| drug_name | ? | ? | ? | ? | < 0.10 | Expand drug_db.json aliases |
| drug_dose | ? | ? | ? | ? | < 0.05 | Tune _normalize_vn_numbers() |
| tai_kham | ? | ? | ? | ? | < 0.30 | Tune tai_kham regex |

### Step 3 — Tune theo entity fail

| Entity fail | File | Hành động cụ thể |
|---|---|---|
| Drug name (phát âm vùng) | `data/reference/drug_db.json` | Thêm phonetic aliases (vd: "ami-xi-lin" → Amoxicillin) |
| Number parsing | `src/core/l1c_ner.py` → `_normalize_vn_numbers()` | Thêm patterns: "tám lăm" → 85, "chín lăm" → 95 |
| ICD lookup | `src/core/l1d_icd.py` | Tune fuzzy threshold, thêm alias "tiểu đường"→"đái tháo đường" |
| BP regex (variant) | `src/core/l1c_ner.py` | Thêm "một hai mươi" pattern (HCM drop prefix) |
| Self-correction | `src/core/l1c_ner.py` | Verify [SỬA] handling, lấy giá trị CUỐI |

### Step 4 — Sau mỗi fix: chạy tests + bench
```bash
pytest tests/ -q  # Phải 100% PASS trước khi commit
python -X utf8 tools/bench_ceer.py --full --gt data/audio/corpus/semi_synthetic/groundtruth_all.json
```

### Step 5 — Declare calibrated khi đạt target tất cả regions

| Entity | Target | Ghi chú |
|---|---|---|
| Vitals (HA, mạch) | CEER < 0.05 | Safety-critical |
| Drug doses | CEER < 0.05 | Safety-critical |
| Drug names | CEER < 0.10 | |
| Chan doan | CEER < 0.10 | |
| Tai kham | CEER < 0.30 | Less critical |

---

## QUAN HỆ VỚI BACKLOG HIỆN TẠI

| BACKLOG task | Liên quan | Thay đổi |
|---|---|---|
| BENCH-002 | Semi-synthetic là Phase 1 của BENCH-002 | Chia thành BENCH-002a (semi-synthetic) + BENCH-002b (pilot thật) |
| DRUG-ALIAS-001 | Step 3 calibration sẽ generate alias list | Vẫn cần Andy approve trước khi merge |
| VN-NER-003 (DONE) | Bug fix đã làm — calibration sẽ confirm | |
| analyze_corrections.py | Vẫn dùng sau 10+ approvals pilot thật | Không thay thế bằng semi-synthetic |

---

## FILES CẦN TẠO/CẬP NHẬT

```
Tạo mới:
  docs/dev/SEMI_SYNTHETIC_DATA_PLAN.md      ← file này
  docs/dev/RECORDING_SCRIPTS_4BS.md         ← kịch bản in cho 4 BS
  data/audio/corpus/semi_synthetic/          ← folder audio (Andy tạo khi thu âm)
  data/audio/corpus/semi_synthetic/groundtruth_all.json  ← ground truth 20 cases

Cập nhật:
  docs/records/BACKLOG.md                   ← thêm BENCH-002a/2b
  docs/records/PENDING_REQUESTS.md          ← PA mới cho Andy
```

---

*SEMI_SYNTHETIC_DATA_PLAN v1.0 | MediVoice VN | 2026-06-09*
*Kịch bản: `docs/dev/RECORDING_SCRIPTS_4BS.md`*
*Ground truth: `data/audio/corpus/semi_synthetic/groundtruth_all.json`*
