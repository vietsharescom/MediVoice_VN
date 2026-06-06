# SYNTHETIC_AUDIO_REQUIREMENTS.md
# MediVoice VN — Yêu cầu TTS Synthetic Audio Dataset
# Giai đoạn 1: AI-generated audio (trước khi có pilot audio thật)
# v1.0 | 2026-06-09 | Owner: Andy Phan

---

## TRẢ LỜI 7 DÒNG CHO CHATGPT/GROK

```
1. Scope:             Full MedVoice (Option C)
                      Audio → ASR → Drug Correction → NER → Structured Chart
                      Output: Mẫu 15/BV-01 (TT32/2023 VN bệnh án ngoại trú)

2. Specialty:         General Practice (Nội khoa tổng quát) — Phase 0
                      Dentistry (Nha khoa) — Phase 1 (sau khi GP stable)

3. Number of drugs:   200 thuốc (từ drug_db.json hiện có 118 → expand lên 200)
                      70% Generic INN | 30% Brand name VN phổ biến
                      Ưu tiên: thuốc thông dụng phòng mạch tư (không phải ICU/bệnh viện)

4. Accent:            35% Nam — TP.HCM / Sài Gòn (tốc độ nhanh, kê toa, hông/hổng)
                      25% Trung — Đà Nẵng (pilot chính, giọng Quảng Nam/Đà Nẵng)
                      25% Bắc — Hà Nội (kê đơn, không/ừ/thì)
                      15% Tây Nam Bộ — Cần Thơ (chậm, tui/nha/dó)

5. Doctor-Patient:    Doctor 95% | Patient 5%
                      (MediVoice chỉ record giọng BS — patient voice không cần cho pipeline)
                      Patient 5% = doctor summarize lời BN: "bệnh nhân khai đau họng 3 ngày"

6. Number of audios:  1,000 audio clips tổng
                      Split: Train 700 / Val 150 / Test 150
                      Phân bổ: 200 clips × 5 bệnh + 200 clips general drug prescription

7. TTS engine:        PRIMARY:   Vbee TTS API (vbee.vn) — tốt nhất cho accent vùng miền VN
                      SECONDARY: FPT.AI TTS API — backup, nhiều giọng VN
                      TERTIARY:  XTTS v2 (Coqui, open source) — offline, fine-tune được
                      AVOID:     ElevenLabs (Vietnamese kém), gTTS (chỉ 1 giọng, không accent)
```

---

## CONTEXT MEDIVOICE VN — CHATGPT CẦN BIẾT

### Bối cảnh thực tế
- **Môi trường:** Phòng mạch tư nhân (1–3 BS), không phải bệnh viện
- **BS nói trong lúc khám** — không phải dictation sau khi khám xong
- **Ngắn gọn, có tạp âm tự nhiên:** quạt, tiếng xe, tiếng BN hỏi xen vào
- **Pilot hiện tại:** Đà Nẵng → accent Trung quan trọng nhất (25% dataset)

### Pipeline hiện có (để output schema khớp)
```python
Audio → L0 (normalize 16kHz mono)
      → L1a (PhoWhisper-medium ASR)
      → L1b (Drug correction — drug_db.json 118 thuốc)
      → L1c (Medical NER VN — rule-based regex)
      → L1d (ICD-10-VN lookup — QĐ5837, 15,026 mã)
      → L4  (Human Gate — BS approve)
      → L6  (Mẫu 15/BV-01 PDF)
```

### Output schema — PHẢI khớp với MedicalEntities (src/core/l1c_ner.py)
```json
{
  "audio_id": "SYN-GP-001-SG-001",
  "speaker_region": "SG",
  "speaker_role": "doctor",
  "duration_sec": 22,
  "noise_level": "clean|light|heavy",
  "transcript_clean": "...",
  "transcript_asr_sim": "...",
  "entities": {
    "nhiet_do": 37.8,
    "huyet_ap": "120/80",
    "mach": 80,
    "can_nang": 70,
    "chan_doan": "viêm họng cấp",
    "icd10": "J02.9",
    "don_thuoc": [
      {
        "inn": "Amoxicillin",
        "ham_luong": "500mg",
        "so_lan_ngay": "3 lần/ngày",
        "so_ngay": 5,
        "duong_dung": "uống"
      }
    ],
    "tai_kham": "5 ngày"
  },
  "ground_truth_mau15": {
    "chan_doan_chinh": "Viêm họng cấp J02.9",
    "don_thuoc": [...],
    "tai_kham": "Tái khám sau 5 ngày hoặc sớm hơn nếu sốt cao"
  }
}
```

---

## PHÂN BỔ 1,000 AUDIO CLIPS

### Theo bệnh (5 bệnh × 200 clips = 1,000)

| Bệnh | ICD-10-VN | N clips | Lý do |
|---|---|---|---|
| Viêm họng cấp | J02.9 | 200 | Phổ biến nhất phòng mạch tư |
| Viêm loét dạ dày | K25.9 | 200 | Multi-drug prescription phức tạp |
| Tăng huyết áp | I10 | 200 | Điều chỉnh liều quan trọng |
| Đái tháo đường type 2 | E11.9 | 200 | Nhiều thuốc + biến chứng |
| Gout cấp | M10.9 | 200 | Colchicine dosing scheme phức tạp |

### Theo độ dài (per ChatGPT recommendation)

| Loại | Duration | N clips | Ví dụ |
|---|---|---|---|
| Ngắn | 5–15s | 700 (70%) | "Kê Paracetamol năm trăm mg ngày hai lần" |
| Trung bình | 15–45s | 250 (25%) | Prescription + vitals + tai_kham |
| Dài | 45–120s | 50 (5%) | Full consultation: symptoms + exam + prescription |

### Theo accent (1,000 clips)

| Region | % | N clips | TTS voice gợi ý |
|---|---|---|---|
| SG — Sài Gòn | 35% | 350 | Vbee "Nam nữ" / FPT "Linhsan" |
| DN — Đà Nẵng/Trung | 25% | 250 | Vbee "Trung" — **ưu tiên vì pilot** |
| HN — Hà Nội | 25% | 250 | Vbee "Bắc" / FPT "Minhquang" |
| CT — Tây Nam Bộ | 15% | 150 | Vbee "Nam — chậm" |

### Theo noise level

| Noise | % | N clips | Mô tả |
|---|---|---|---|
| Clean | 50% | 500 | Phòng yên tĩnh, không nhiễu |
| Light | 30% | 300 | Tiếng quạt, air-con xa, tiếng giấy |
| Heavy | 20% | 200 | Tiếng xe, BN hỏi xen vào, điện thoại |

---

## DANH SÁCH 200 THUỐC — PHÂN NHÓM

### Hiện có trong drug_db.json (118 thuốc) — ĐÃ VERIFIED
*(Danh sách đầy đủ trong `data/reference/drug_db.json`)*

Nhóm chính: Kháng sinh · Hạ nhiệt/giảm đau · Tim mạch · Tiêu hóa · Nội tiết · Thần kinh · Hô hấp · Vitamin · Xương khớp · Hormone sinh sản

### Cần thêm 82 thuốc để đạt 200 — Ưu tiên nhóm:
```
Kháng sinh: Ciprofloxacin, Azithromycin, Clarithromycin, Doxycycline, Cephalexin,
            Cetirizine, Levofloxacin, Trimethoprim, Nitrofurantoin, Vancomycin (IV)

Tim mạch:   Bisoprolol, Ramipril, Valsartan, Furosemide, Hydrochlorothiazide,
            Digoxin, Warfarin, Clopidogrel, Rosuvastatin, Pravastatin

Tiêu hóa:  Pantoprazole, Esomeprazole, Lansoprazole, Sucralfate, Bismuth,
            Loperamide, Ondansetron, Metoclopramide, Lactulose, Simethicone

Nội tiết:  Levothyroxine, Pioglitazone, Empagliflozin, Dapagliflozin, Insulin NPH,
            Glipizide, Repaglinide, Vildagliptin, Acarbose, Saxagliptin

Thần kinh: Gabapentin, Duloxetine, Amitriptyline, Alprazolam, Clonazepam,
            Melatonin, Topiramate, Valproic Acid, Levetiracetam, Zolpidem

Hô hấp:   Salbutamol, Budesonide, Montelukast, Fluticasone, Tiotropium,
            Acetylcysteine, Ambroxol, Bromhexine, Erdosteine, Guaifenesin

Khác:      Ferrous Sulfate, Folic Acid, Vitamin D3 2000IU, Calcium, Zinc,
            Omega-3, Glucosamine (1500mg), Chondroitin, Collagen, Biotin
```

---

## LINGUISTIC PATTERNS BẮT BUỘC TRONG SCRIPT

### Số phải nói bằng tiếng Việt (PhoWhisper output)
```
✅ "năm trăm miligam" — không phải "500mg"
✅ "ba lần một ngày" — không phải "3 lần/ngày"
✅ "một trăm hai mươi trên tám mươi" — không phải "120/80"
✅ "ba mươi bảy phẩy tám độ" — không phải "37.8°C"
✅ "bảy ngày" — không phải "1 tuần"
```

### Regional markers bắt buộc (≥2 per script)
```
HN:  kê đơn · không · ừ · thì · tái khám · bệnh nhân
SG:  kê toa · hông/hổng · hả · nha · bệnh nhân
CT:  cho thuốc · hổng · tui · nha · dó · ờ
DN:  kê thuốc · không · ừ (giọng nặng) · mô/răng (ít dùng trong Y)
CA:  prescription · euh · so · basically · follow up · patient
```

### ASR noise simulation (không cần TTS làm — pipeline test sẽ inject)
```
Drug mishear examples (đã biết từ pilot):
  Amoxicillin → "amo xi lan" / "ammos xi lin"
  Paracetamol → "para xi ta mol" / "para xê ta"
  Omeprazole  → "ô mê pra zol"
  Metformin   → "mê phô min"
  Amlodipine  → "am lô đi pin"
```

---

## TIÊU CHUẨN KỸ THUẬT AUDIO

```
Format:     WAV, 16kHz, mono, 16-bit PCM
            (khớp với L0 pipeline — không cần convert)

Naming:     {disease}_{region}_{length}_{noise}_{idx:04d}.wav
            vd: j029_SG_short_clean_0001.wav
                i10_DN_medium_light_0042.wav

Metadata:   Mỗi audio kèm 1 file JSON cùng tên
            vd: j029_SG_short_clean_0001.json

SNR target: Clean ≥ 35dB | Light 20–35dB | Heavy 10–20dB

Duration:   Short 5–15s | Medium 15–45s | Long 45–120s
```

---

## TRAIN/VAL/TEST SPLIT

```
Total: 1,000 clips

Train: 700 (70%)  — dùng để fine-tune PhoWhisper + NER
Val:   150 (15%)  — monitor training
Test:  150 (15%)  — benchmark cuối (không dùng trong training)

Stratified by: disease × region × noise_level
→ Mỗi tổ hợp phải có ≥ 3 clips trong test set
```

---

## DELIVERABLES YÊU CẦU

```
data/synthetic_audio/
  ├── train/
  │   ├── *.wav        (700 files)
  │   └── *.json       (700 metadata files)
  ├── val/
  │   ├── *.wav        (150 files)
  │   └── *.json       (150 files)
  ├── test/
  │   ├── *.wav        (150 files)
  │   └── *.json       (150 files)
  ├── corpus_manifest.csv   (tất cả 1000 clips, metadata dạng bảng)
  └── README.md             (mô tả dataset, license, usage)

corpus_manifest.csv columns:
  audio_id, filepath, region, disease, icd10, duration, noise_level,
  n_drugs, has_vital, has_followup, tts_engine, tts_voice, split
```

---

## PIPELINE TEST SAU KHI CÓ AUDIO

```bash
# Chạy benchmark trên test set (150 clips)
python -X utf8 tools/bench_ceer.py \
  --full \
  --gt data/synthetic_audio/test/ \
  --output results/synthetic_audio_ceer.json

# Mục tiêu CEER:
#   Drug name:  < 0.15  (TTS phát âm rõ hơn người thật)
#   Drug dose:  < 0.05
#   Vitals:     < 0.05
#   Chan_doan:  < 0.10
#   Tai_kham:   < 0.30
```

---

*SYNTHETIC_AUDIO_REQUIREMENTS v1.0 | MediVoice VN | 2026-06-09*
*Dùng file này paste vào ChatGPT/Grok để generate corpus + audio plan*
*Kết hợp với: `docs/dev/SEMI_SYNTHETIC_DATA_PLAN.md` (human recording — giai đoạn 2)*
