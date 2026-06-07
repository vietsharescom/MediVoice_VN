# SYNTHETIC_AUDIO_REQUIREMENTS.md
# MediVoice VN — Data Generation Specification (TTS Synthetic Audio)
# Giai đoạn 1: AI-generated audio prototype trước khi có pilot audio thật
# v2.0 | 2026-06-09 | Owner: Andy Phan / Maple Leaf Group
# Reviewed by: ChatGPT (structural review) + Claude (MediVoice-specific)

---

## 1. TỔNG QUAN

| Field | Value |
|---|---|
| Mục tiêu | Tạo 1,100 TTS audio clips để test pipeline MediVoice trước khi có giọng BS thật |
| Scope | Full MedVoice: Audio → ASR → Drug Correction → NER → Structured Chart (Mẫu 15/BV-01) |
| Chuyên khoa | General Practice (Phase 0) · Dentistry (Phase 1, sau khi GP stable) |
| Output chính | WAV 16kHz mono + JSON metadata (1 cặp mỗi clip) + corpus_manifest.csv |
| Benchmark | CEER per entity × per region (chạy qua `tools/bench_ceer.py`) |

---

## 2. PIPELINE MEDIVOICE (để output schema khớp)

```
Audio → L0  (normalize 16kHz mono, VAD)
      → L1a (PhoWhisper-medium ASR — offline)
      → L1b (Drug correction — drug_db.json 200 thuốc)
      → L1c (Medical NER VN — rule-based regex)
      → L1d (ICD-10-VN lookup — QĐ5837, 15,026 mã)
      → L4  (Human Gate — BS approve bắt buộc)
      → L6  (Mẫu 15/BV-01 PDF)
```

**Bối cảnh ghi âm thực tế:**
- Phòng mạch tư nhân (1–3 BS), không phải bệnh viện
- BS nói trong lúc khám (không phải dictation sau khi khám)
- Có tạp âm tự nhiên: quạt, tiếng xe, tiếng BN xen vào
- Pilot hiện tại: Đà Nẵng → accent Trung là ưu tiên

---

## 3. TRẢ LỜI 7 DÒNG CHO CHATGPT/GROK

```
1. Scope:          Full MedVoice (Option C)
                   Audio → ASR → Drug Correction → NER → Mẫu 15/BV-01

2. Specialty:      General Practice (Phase 0)
                   Dentistry (Phase 1 — sau khi GP stable)

3. Number drugs:   200 thuốc
                   70% Generic INN | 30% Brand name VN phổ biến
                   118 thuốc đã có trong drug_db.json — thêm 82 thuốc nữa

4. Accent:         35% SG — TP.HCM (nhanh, kê toa, hông/hổng)
                   25% DN — Đà Nẵng (pilot chính, giọng Quảng Nam/Trung)
                   25% HN — Hà Nội (chuẩn, kê đơn, không/ừ/thì)
                   15% CT — Cần Thơ (chậm, tui/nha/dó)

5. Doctor-Patient: Doctor 95% | Patient 5%
                   (Patient 5% = doctor summarize lời BN: "bệnh nhân khai...")

6. Number audios:  1,100 clips tổng (1,000 main + 100 challenge set)
                   Split: Train 700 / Val 150 / Test 150 / Challenge 100

7. TTS engine:     PRIMARY:   Vbee TTS API (vbee.vn) — best accent vùng miền VN
                   SECONDARY: FPT.AI TTS API — backup, nhiều giọng
                   TERTIARY:  XTTS v2 (Coqui, open source) — offline
                   AVOID:     ElevenLabs (VN kém), gTTS (1 giọng, không accent)
```

---

## 4. PHÂN BỔ 1,000 MAIN CLIPS

### 4.1 Theo bệnh (5 bệnh × 200 clips)

| Bệnh | ICD-10-VN | N | Lý do |
|---|---|---|---|
| Viêm họng cấp | J02.9 | 200 | Phổ biến nhất phòng mạch tư |
| Viêm loét dạ dày | K25.9 | 200 | Multi-drug prescription phức tạp |
| Tăng huyết áp | I10 | 200 | Điều chỉnh liều, safety-critical |
| Đái tháo đường type 2 | E11.9 | 200 | Nhiều thuốc + biến chứng |
| Gout cấp | M10.9 | 200 | Colchicine step-down dosing phức tạp |

### 4.2 Intent Distribution (THÊM MỚI)

| Intent | % | N | Ví dụ |
|---|---|---|---|
| diagnosis_plus_prescription | 35% | 350 | "Chẩn đoán viêm họng cấp. Kê Amoxicillin..." |
| prescription_only | 20% | 200 | "Kê Paracetamol năm trăm mg ngày hai lần." |
| diagnosis_only | 20% | 200 | "Chẩn đoán tăng huyết áp." |
| medication_adjustment | 10% | 100 | "Tăng amlodipine từ năm lên mười miligam." |
| followup_instruction | 10% | 100 | "Tái khám sau hai tuần, xét nghiệm HbA1c." |
| vital_signs_only | 5% | 50 | "Huyết áp một trăm bảy mươi trên một trăm." |

### 4.3 Drug Complexity Level (THÊM MỚI)

| Level | Số thuốc | % | N | Ghi chú |
|---|---|---|---|---|
| Easy | 1 thuốc | 40% | 400 | "Paracetamol năm trăm mg." |
| Medium | 2–3 thuốc | 45% | 450 | Prescription thông thường |
| Hard | 4–6 thuốc | 15% | 150 | Nơi Drug Correction dễ lỗi nhất |

### 4.4 Doctor Speaking Style (THÊM MỚI)

| Style | % | N | Ví dụ |
|---|---|---|---|
| concise | 40% | 400 | "Viêm họng. Amoxi năm trăm. Ba lần. Năm ngày." |
| normal | 40% | 400 | "Bệnh nhân viêm họng cấp, kê Amoxicillin năm trăm mg uống ba lần mỗi ngày trong năm ngày." |
| fast_dictation | 20% | 200 | "Viêm họng kê amoxi năm trăm TID năm ngày tái khám năm ngày." |

> **fast_dictation** là dạng khó nhất cho PhoWhisper — cần đủ sample để test.

### 4.5 Theo độ dài audio

| Loại | Duration | % | N |
|---|---|---|---|
| Ngắn | 5–15s | 70% | 700 |
| Trung bình | 15–45s | 25% | 250 |
| Dài | 45–120s | 5% | 50 |

### 4.6 Theo accent

| Region | % | N | TTS voice gợi ý |
|---|---|---|---|
| SG — Sài Gòn | 35% | 350 | Vbee "Nam nữ" / FPT "Linhsan" |
| DN — Đà Nẵng | 25% | 250 | Vbee "Trung" — ưu tiên vì pilot |
| HN — Hà Nội | 25% | 250 | Vbee "Bắc" / FPT "Minhquang" |
| CT — Tây Nam Bộ | 15% | 150 | Vbee "Nam — chậm" |

### 4.7 Theo noise level

| Noise | % | N | Mô tả |
|---|---|---|---|
| Clean | 50% | 500 | Phòng yên tĩnh |
| Light | 30% | 300 | Tiếng quạt, air-con xa, tiếng giấy |
| Heavy | 20% | 200 | Tiếng xe, BN hỏi xen vào, điện thoại |

---

## 5. CHALLENGE SET — 100 CLIPS (THÊM MỚI)

Bộ test riêng đo CEER tại điểm khó nhất. Không dùng trong training.

| Challenge | N | Mô tả | Ví dụ |
|---|---|---|---|
| Drug name confusion | 30 | Tên thuốc giống nhau | Amoxicillin vs Amlodipine vs Azithromycin |
| Number confusion | 25 | Số nghe dễ nhầm | "mười lăm" vs "năm mươi" / "hai lăm" vs "năm mươi hai" |
| Dose confusion | 20 | Liều dễ lẫn | 250mg vs 500mg vs 750mg |
| Followup confusion | 15 | Thời gian tái khám | 3 ngày vs 5 ngày vs 7 ngày vs 14 ngày |
| Fast speech extreme | 10 | Tốc độ tối đa | BS Sài Gòn kê 4 thuốc liên tục không nghỉ |

---

## 6. METADATA SCHEMA (UPDATED — đủ fields)

```json
{
  "audio_id": "j029_SG_medium_clean_0042",
  "filepath": "train/j029_SG_medium_clean_0042.wav",
  "split": "train",

  "speaker_region": "SG",
  "speaker_role": "doctor",
  "tts_engine": "vbee",
  "tts_voice": "linhsan_female",

  "disease": "viem_hong_cap",
  "icd10": "J02.9",
  "duration_sec": 22.4,
  "noise_level": "clean",

  "intent": "diagnosis_plus_prescription",
  "drug_complexity": "medium",
  "speaking_style": "normal",
  "n_drugs": 2,
  "has_vital": true,
  "has_followup": true,

  "transcripts": {
    "clean":    "Chẩn đoán viêm họng cấp. Kê Amoxicillin năm trăm miligam uống ba lần mỗi ngày trong năm ngày.",
    "regional": "Chẩn đoán viêm họng cấp. Kê toa Amoxi năm trăm uống ba lần ngày năm ngày nha.",
    "asr_sim":  "chẩn đoán viêm họng cấp kê toa amo xi lan năm trăm uống ba lần ngày năm ngày"
  },

  "ground_truth": {
    "ly_do_kham": "đau họng",
    "dau_hieu_sinh_ton": {
      "nhiet_do": 37.8,
      "huyet_ap": "120/80",
      "mach": 80,
      "can_nang": 70
    },
    "chan_doan": "Viêm họng cấp",
    "icd10": "J02.9",
    "don_thuoc": [
      {
        "inn": "Amoxicillin",
        "ham_luong": "500mg",
        "duong_dung": "uống",
        "so_lan_ngay": "3 lần/ngày",
        "so_ngay": 5
      }
    ],
    "tai_kham": "5 ngày",
    "xu_tri": "Kháng sinh viêm họng"
  },

  "ground_truth_mau15": {
    "chan_doan_chinh": "Viêm họng cấp J02.9",
    "don_thuoc_full": "Amoxicillin 500mg × 3 lần/ngày × 5 ngày",
    "tai_kham": "Tái khám sau 5 ngày hoặc sớm hơn nếu sốt cao"
  }
}
```

> **3 levels transcript** cho phép benchmark ASR / Drug Correction / NER riêng biệt.

---

## 7. STRUCTURED CHART COVERAGE (THÊM MỚI)

Ít nhất **20% corpus (200 clips)** có đủ các trường Mẫu 15/BV-01:

```json
{
  "ly_do_kham":        "đau họng 3 ngày, sốt",
  "benh_su":           "Bệnh nhân nam 35 tuổi, khởi phát cách đây 3 ngày...",
  "dau_hieu_sinh_ton": {"nhiet_do": 37.8, "huyet_ap": "120/80", "mach": 80, "can_nang": 70},
  "kham_lam_sang":     "Họng đỏ, amidan sưng hai bên độ 1",
  "chan_doan":         "Viêm họng cấp J02.9",
  "xu_tri":            "Kháng sinh + hạ sốt",
  "don_thuoc":         [...],
  "tai_kham":          "5 ngày"
}
```

| Coverage level | % | N | Fields bắt buộc |
|---|---|---|---|
| Minimal | 80% | 800 | chan_doan + don_thuoc + tai_kham |
| Full Mẫu 15 | 20% | 200 | Tất cả 8 fields trên |

---

## 8. LINGUISTIC PATTERNS BẮT BUỘC

### Số phải nói bằng tiếng Việt (PhoWhisper output format)
```
✅ "năm trăm miligam"              — không phải "500mg"
✅ "ba lần một ngày"               — không phải "3 lần/ngày"
✅ "một trăm hai mươi trên tám mươi" — không phải "120/80"
✅ "ba mươi bảy phẩy tám độ"       — không phải "37.8°C"
✅ "bảy ngày"                      — không phải "1 tuần"
```

### Regional markers bắt buộc (≥ 2 per script)
```
HN:  kê đơn · không · ừ · thì · tái khám
SG:  kê toa · hông/hổng · hả · nha · vậy
CT:  cho thuốc · hổng · tui · nha · dó · ờ
DN:  kê thuốc · không · ừ (giọng nặng) · bệnh nhân
CA:  prescription · euh · so · follow up · patient
```

### Drug ASR mishear patterns đã biết từ pilot
```
Amoxicillin → "amo xi lan" / "ammos xi lin" / "ami xi lin"
Paracetamol → "para xi ta mol" / "para xê ta"
Omeprazole  → "ô mê pra zol" / "ô me pra"
Metformin   → "mê phô min" / "met pho min"
Amlodipine  → "am lô đi pin" / "am lô đi"
Losartan    → "lô xar tan" / "lô sa tan"
```

---

## 9. DANH SÁCH 200 THUỐC

### Đã có trong drug_db.json (118 thuốc) — verified
*(Xem đầy đủ tại `data/reference/drug_db.json` v0.2.0)*

### Cần thêm 82 thuốc — theo nhóm ưu tiên

```
Kháng sinh (+10):
  Ciprofloxacin, Azithromycin, Clarithromycin, Doxycycline, Cephalexin,
  Levofloxacin, Trimethoprim, Nitrofurantoin, Clindamycin, Ampicillin

Tim mạch (+10):
  Bisoprolol, Ramipril, Valsartan, Furosemide, Hydrochlorothiazide,
  Digoxin, Warfarin, Clopidogrel, Rosuvastatin, Pravastatin

Tiêu hóa (+10):
  Pantoprazole, Esomeprazole, Lansoprazole, Sucralfate, Bismuth subsalicylate,
  Loperamide, Ondansetron, Metoclopramide, Lactulose, Simethicone

Nội tiết (+12):
  Levothyroxine, Pioglitazone, Empagliflozin, Dapagliflozin, Insulin NPH,
  Glipizide, Repaglinide, Vildagliptin, Acarbose, Saxagliptin,
  Insulin Glargine, Exenatide

Thần kinh (+10):
  Gabapentin, Duloxetine, Amitriptyline, Alprazolam, Clonazepam,
  Melatonin, Topiramate, Valproic Acid, Levetiracetam, Zolpidem

Hô hấp (+10):
  Salbutamol, Budesonide, Montelukast, Fluticasone, Tiotropium,
  Acetylcysteine, Ambroxol, Bromhexine, Erdosteine, Guaifenesin

Vitamin & Hỗ trợ (+10):
  Ferrous Sulfate, Folic Acid, Vitamin D3 2000IU, Calcium carbonate, Zinc,
  Omega-3, Glucosamine 1500mg, Chondroitin, Collagen peptide, Biotin

Da liễu & Khác (+10):
  Hydrocortisone cream, Betamethasone, Clotrimazole, Miconazole,
  Permethrin, Acyclovir, Valacyclovir, Isotretinoin, Doxycycline (derm),
  Erythromycin topical
```

---

## 10. TIÊU CHUẨN KỸ THUẬT AUDIO

```
Format:     WAV, 16kHz, mono, 16-bit PCM
            (khớp L0 pipeline — không cần convert)

Naming:     {icd_short}_{region}_{style}_{noise}_{idx:04d}.wav
            j029  = J02.9 viêm họng
            i10   = I10 tăng huyết áp
            k259  = K25.9 viêm dạ dày
            e119  = E11.9 đái tháo đường
            m109  = M10.9 gout
            chal  = challenge set

            Ví dụ: j029_SG_normal_clean_0001.wav
                   i10_DN_fast_light_0042.wav
                   chal_HN_drug_0015.wav

SNR:        Clean ≥ 35dB | Light 20–35dB | Heavy 10–20dB

Duration:   Short 5–15s | Medium 15–45s | Long 45–120s
```

---

## 11. TRAIN / VAL / TEST SPLIT

```
Main set:      1,000 clips
Challenge set:   100 clips (test only — không train)
─────────────────────────────
Total:         1,100 clips

Main split (stratified by disease × region × noise):
  Train:   700 (70%) — fine-tune PhoWhisper + NER
  Val:     150 (15%) — monitor training
  Test:    150 (15%) — final benchmark

Challenge: 100 (test only)

Constraint: Mỗi tổ hợp (disease × region × noise_level) phải có ≥ 3 clips trong test.
```

---

## 12. DELIVERABLES

```
data/synthetic_audio/
  ├── train/                      # 700 clips
  │   ├── *.wav
  │   └── *.json
  ├── val/                        # 150 clips
  │   ├── *.wav
  │   └── *.json
  ├── test/                       # 150 clips
  │   ├── *.wav
  │   └── *.json
  ├── challenge/                  # 100 clips (test only)
  │   ├── *.wav
  │   └── *.json
  ├── corpus_manifest.csv         # tất cả 1100 clips, metadata dạng bảng
  └── README.md                   # mô tả dataset, license, usage

corpus_manifest.csv columns:
  audio_id, filepath, split, region, disease, icd10, duration_sec,
  noise_level, intent, drug_complexity, speaking_style, n_drugs,
  has_vital, has_followup, full_mau15, tts_engine, tts_voice,
  transcript_clean, transcript_regional, transcript_asr_sim
```

---

## 13. BENCHMARK KHI CÓ AUDIO

```bash
# Test trên 150 main test clips
python -X utf8 tools/bench_ceer.py \
  --full \
  --gt data/synthetic_audio/test/ \
  --output results/synthetic_ceer_main.json

# Test trên 100 challenge clips
python -X utf8 tools/bench_ceer.py \
  --full \
  --gt data/synthetic_audio/challenge/ \
  --output results/synthetic_ceer_challenge.json
```

**Target CEER (TTS phát âm rõ hơn người thật):**

| Entity | Target | Ghi chú |
|---|---|---|
| Drug name | < 0.15 | TTS không có ASR error nhưng drug_db coverage hạn chế |
| Drug dose | < 0.05 | Safety-critical |
| Vitals | < 0.05 | Safety-critical |
| Chan_doan | < 0.10 | ICD lookup + regex |
| Tai_kham | < 0.30 | Ít critical hơn |

---

## 14. ĐÁNH GIÁ HOÀN THIỆN (ChatGPT review)

| Thành phần | Trước v2.0 | Sau v2.0 |
|---|---|---|
| Clinical scope | 9/10 | 9/10 |
| Drug coverage | 8.5/10 | 9/10 |
| Accent coverage | 9/10 | 9/10 |
| Intent distribution | ❌ thiếu | ✅ 6 intents |
| Drug complexity | ❌ thiếu | ✅ 3 levels |
| ASR challenge set | 7/10 | ✅ 100 clips riêng |
| Structured chart | 7/10 | ✅ 20% full Mẫu 15 |
| Speaking style | ❌ thiếu | ✅ 3 styles |
| Transcript levels | ❌ thiếu | ✅ clean/regional/asr_sim |
| **Tổng** | **~8.5/10** | **~9.5/10** |

---

*SYNTHETIC_AUDIO_REQUIREMENTS v2.0 | MediVoice VN | 2026-06-09*
*Paste file này vào ChatGPT/Grok để generate corpus schema + audio generation plan*
*Kết hợp: `docs/dev/SEMI_SYNTHETIC_DATA_PLAN.md` (giai đoạn 2 — giọng người thật)*
*Drug list nguồn: `data/reference/drug_db.json` v0.2.0 (118 thuốc hiện có)*
