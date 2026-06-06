# DATA_CATALOG.md — MediVoice VN
# Danh mục datasets công khai dùng để fine-tune ASR/NER
# Cập nhật: 2026-06-09 | v1.1 (verified từ papers + HuggingFace)

---

## TỔNG QUAN

MediVoice VN cần 4 loại data:

| Loại | Hiện trạng | Gap | Giải pháp |
|---|---|---|---|
| **ASR — VN Medical Speech** | PhoWhisper-medium (general VN) | Chưa fine-tune medical | VietMed + ViMedCSS |
| **NER — Medical Entities** | PhoBERT+CRF (pre-trained) | Chưa fine-tune medical | VietMed-NER + ViMQ |
| **Drug DB** | 110 thuốc (drug_db.json) | Quá mỏng | Drugbank.vn + VietMed-NER DRUGCHEMICAL |
| **ICD-10-VN** | QD5837 list (15,026 mã) | Không có training data | Mine từ VietMed metadata |

---

## NHÓM A — CÓ THỂ DOWNLOAD NGAY

### MultiMed Family (Khai Le-Duc, University of Toronto)

> Cùng tác giả, cùng repo: https://github.com/leduckhai/MultiMed
> Contact: duckhai.le@mail.utoronto.ca

---

#### VietMed ⭐ — ASR
- **HuggingFace:** `leduckhai/VietMed`
- **GitHub:** https://github.com/leduckhai/MultiMed/tree/master/VietMed
- **Paper:** LREC-COLING 2024
- **License:** MIT (code) + CC-BY-4.0 (data) ✅ commercial OK
- **Size:**
  - 16h labeled medical speech (trên HF)
  - 1,000h unlabeled medical speech (Google Drive)
  - 1,200h unlabeled general-domain speech (Google Drive)
  - Tổng: ~2,216h — world's largest public medical ASR dataset
- **Nội dung:** Hội thoại BS-BN-host. Đủ accent Bắc/Nam/Trung. Bao phủ toàn bộ ICD-10 groups.
- **Pipeline MediVoice:** L1a — fine-tune PhoWhisper-medium
- **Models đi kèm:** w2v2-Viet, XLSR-53-Viet (pre-trained), fine-tuned medical ASR
- **Download P1 (16h labeled):**
  ```python
  from datasets import load_dataset
  ds = load_dataset("leduckhai/VietMed")
  ds.save_to_disk("data/external/VietMed")
  ```
- **Download full (2,216h):** Email duckhai.le@mail.utoronto.ca xin Google Drive link

---

#### VietMed-NER ⭐⭐ — NER (quan trọng nhất)
- **HuggingFace:** `leduckhai/VietMed-NER`
- **GitHub:** https://github.com/leduckhai/MultiMed/tree/master/VietMed-NER
- **Paper:** NAACL 2025 — arxiv.org/abs/2406.13337
- **License:** CC-BY-4.0 ✅ commercial OK
- **Size:** 9,270 samples | 21,735 total entities | ~50 MB
- **Splits:** Train 4,620 / Val 1,150 / Test 3,500
  - Test set lớn có chủ ý để "statistically significant evaluation"
- **Format:** BIO tagging (Begin-Inside-Outside) trên Parquet
- **Modalities:** Text + Audio (từ VietMed corpus)
- **Annotation:** 2 annotator độc lập (1 có medical background) + 2 QA reviewer + iterative refinement

**18 Entity Types + MediVoice mapping:**

| Entity VietMed-NER | Count | Map → MediVoice L1c | Priority |
|---|---|---|---|
| DISEASESYMPTOM | 4,716 | SYMPTOM + DIAGNOSIS | ⭐⭐ cao nhất |
| TREATMENT | ~2,000est | MEDICATION + FOLLOWUP | ⭐⭐ |
| DRUGCHEMICAL | ? | MEDICATION | ⭐⭐ |
| DATETIME | ? | FOLLOWUP (tái khám) | ⭐⭐ |
| UNITCALIBRATOR | ? | VITAL (38.5°C, 120/80) | ⭐⭐ |
| ORGAN | ? | SYMPTOM context | ⭐ |
| DIAGNOSTICS | ? | DIAGNOSIS | ⭐ |
| SURGERY | ? | HISTORY | ⭐ |
| AGE | ? | Patient intake | ⭐ |
| GENDER | ? | Patient intake | ⭐ |
| PERSONALCARE | ? | MEDICATION (OTC) | 🟡 |
| FOODDRINK | ? | FOLLOWUP advice | 🟡 |
| PREVENTIVEMED | ? | FOLLOWUP | 🟡 |
| MEDDEVICETECHNIQUE | ? | Thiết bị y tế | 🟢 |
| OCCUPATION | ? | Patient context | 🟢 |
| LOCATION | ? | Not needed | — |
| ORGANIZATION | ? | Not needed | — |
| TRANSPORTATION | 35 | Not needed | — |

- **Download:**
  ```python
  from datasets import load_dataset
  ds = load_dataset("leduckhai/VietMed-NER")
  ds.save_to_disk("data/external/VietMed-NER")
  ```
  Hoặc: `python -X utf8 scripts/download_datasets.py --id VietMed-NER`

---

#### VietMed-Sum — Summarization
- **HuggingFace:** `leduckhai/VietMed-Sum`
- **GitHub:** https://github.com/leduckhai/MultiMed/tree/master/VietMed-Sum
- **Paper:** Interspeech 2024
- **License:** MIT ✅
- **Size:** 106,252 rows | ~43 MB
- **Nội dung:** Hội thoại BS-BN + local summary + global summary. Tim mạch, hô hấp, da liễu, thần kinh, GI, miễn dịch.
- **Pipeline MediVoice:** L1c + L6 — summaries ≈ structured Mẫu 15 output
- **Use for MediVoice:**
  - Mine clinical entity vocabulary → expand NER training
  - Conversation → structured summary patterns → training cho L6 mapping
- **Download:**
  ```python
  from datasets import load_dataset
  ds = load_dataset("leduckhai/VietMed-Sum")
  ds.save_to_disk("data/external/VietMed-Sum")
  ```

---

#### MultiMed — Multilingual Medical ASR
- **GitHub:** https://github.com/leduckhai/MultiMed/tree/master/MultiMed
- **Paper:** ACL 2025
- **Languages:** Vietnamese, English, German, French, Mandarin Chinese
- **Note:** World's largest medical ASR dataset (by multiple metrics)
- **Use for MediVoice:** Không dùng trực tiếp. Có thể xem cross-lingual transfer methodology.

---

### ViMedCSS ⭐ — Code-Switching ASR
- **HuggingFace:** `tensorxt/ViMedCSS`
- **Paper:** arxiv.org/abs/2602.12911
- **License:** CC-BY-4.0 ✅ commercial OK
- **Size:** 34h, 16,576 utterances | ~4 GB
- **Language:** Vietnamese + English code-switching
- **Nội dung:** Lecture y tế YouTube. 5 chuyên khoa incl. nội tiết. Mỗi utterance: 1–4 English medical terms trong câu Việt.
- **Pipeline MediVoice:** L1a + L1b — hardest failure mode: "Amoxicillin" → "ammos lim"
- **Download:**
  ```python
  from datasets import load_dataset
  ds = load_dataset("tensorxt/ViMedCSS")
  ds.save_to_disk("data/external/ViMedCSS")
  ```

---

### Vietnamese Medical QA — Vocabulary
- **HuggingFace:** `hungnm/vietnamese-medical-qa`
- **License:** Apache-2.0 ✅ commercial OK
- **Size:** 9,335 pairs | ~5 MB
- **Nguồn:** edoctor.vn + vinmec.com
- **Chuyên khoa:** Nha, TMH, da, tim, thần kinh, GI, tiết niệu, nội tiết, hô hấp, truyền nhiễm
- **Pipeline MediVoice:** L1c vocabulary, L1b drug names — mine drug/disease terms theo chuyên khoa
- **Download:**
  ```python
  from datasets import load_dataset
  ds = load_dataset("hungnm/vietnamese-medical-qa")
  ds.save_to_disk("data/external/Vietnamese-Medical-QA")
  ```

---

### VLSP2020-VinAI-100h — General ASR
- **HuggingFace:** `doof-ferb/vlsp2020_vinai_100h`
- **License:** CC-BY-4.0 ✅
- **Size:** 100h, 56K samples | 11.6 GB
- **Nội dung:** 20h read + **80h spontaneous speech** — gần nhất với giọng khám tự nhiên
- **Pipeline MediVoice:** L1a base acoustic model
- **Download:**
  ```python
  from datasets import load_dataset
  ds = load_dataset("doof-ferb/vlsp2020_vinai_100h")
  ds.save_to_disk("data/external/VLSP2020-VinAI")
  ```

---

### ViMQ — Medication NER
- **GitHub:** https://github.com/tadeephuy/ViMQ
- **License:** Chưa rõ — **verify commercial use với tác giả trước production**
- **Size:** 9,000 câu hỏi BN | ~20 MB
- **Entity types:** SYMPTOM&DISEASE, MEDICAL_PROCEDURE, **MEDICINE**
- **Nguồn:** Vinmec hospital patient question website
- **Download:**
  ```bash
  git clone --depth 1 https://github.com/tadeephuy/ViMQ.git data/external/ViMQ
  ```

---

### BUD500 — Large-Scale General VI ASR
- **HuggingFace:** `linhtran92/viet_bud500`
- **License:** Apache-2.0 *(verify NC clause trước production)*
- **Size:** 500h | **~100 GB — KHÔNG full download. Dùng streaming.**
- **Download (streaming only):**
  ```python
  from datasets import load_dataset
  ds = load_dataset("linhtran92/viet_bud500", streaming=True)
  for sample in ds["train"].take(1000):
      print(sample["sentence"])
  ```

---

## NHÓM B — CÓ PAPER NHƯNG DATA CHƯA PUBLIC

### ViMedNER (EAI INIS 2024)
- **Paper:** https://publications.eai.eu/index.php/inis/article/view/5221
- **License:** CC-BY-3.0
- **Entity types:** Disease names, symptoms, causes, diagnostics, treatments (5 types — ít hơn VietMed-NER)
- **Nguồn:** 4 websites y tế VN — collected from web text (không phải spoken)
- **Models tested:** PhoBERT, XLM-R, ViDeBERTa, ViPubMedDeBERTa, ViHealthBERT → XLM-R tốt nhất
- **Status: ❌ KHÔNG CÓ DOWNLOAD** — "Download data is not yet available"
- **Action:** Email tác giả (Pham Van Duong et al.) xin dataset khi available
- **Khi available:** Kết hợp với VietMed-NER → coverage tốt hơn cho text-based NER

### PhoNER_COVID19 (VinAI)
- **GitHub:** https://github.com/VinAIResearch/PhoNER_COVID19
- **License:** Research only, NO commercial, NO redistribute
- **Status:** Available nhưng không dùng production được
- **Dùng cho:** Pre-train NER backbone, SYMPTOM&DISEASE entity

---

## NHÓM C — LƯU CHO DỰ ÁN TƯƠNG LAI

### MultiMed (ACL 2025) — Khi cần multilingual
- **Languages:** VI + EN + DE + FR + ZH
- **Use case:** Khi MediVoice expand sang bác sĩ nước ngoài tại VN (BS Hàn, Nhật...)
- **URL:** github.com/leduckhai/MultiMed

### GigaSpeech2-VI (6,039h) — Khi cần acoustic pre-training lớn
- **HuggingFace:** `speechcolab/gigaspeech2`
- **Vấn đề:** License chưa rõ (auto-transcribed từ YouTube)
- **Use case:** Khi fine-tune PhoWhisper cần thêm acoustic diversity

### VietSuperSpeech (2026) — Conversational VN Speech
- **Paper:** arxiv.org/abs/2603.01894
- **Size:** 267h, 52K pairs. Casual conversational YouTube.
- **Status:** Very new (Feb 2026) — check HF availability
- **Use case:** Gần với phong cách nói của BS nhất sau VietMed

### MIMIC-III (English) + n2c2 2018 — Methodology reference
- **Dùng cho:** Drug NER schema design (n2c2 có 9 drug entity subtypes: name, dosage, frequency, route, form, ADE, reason, duration, strength)
- **Không dùng trực tiếp** vì English-only và DUA required

---

## NGUỒN DRUG DATABASE (Quan trọng cho drug CEER 0.90→<0.10)

### Drugbank.vn (BYT) — ưu tiên nhất
- **URL:** https://drugbank.vn
- **Nội dung:** 10,000+ thuốc đăng ký VN, tên thương mại, nhà sản xuất
- **Vấn đề:** Không có API/bulk download public
- **Action 1:** Liên hệ Cục Quản lý Dược (DAV) — xin data sharing agreement
- **Action 2:** Web scrape (verify ToS trước — legally ambiguous)
- **Tại sao critical:** Drug CEER 0.90 🔴 vì drug_db.json chỉ có 110 thuốc

### DrugBank Open Data (CC-0 public domain)
- **URL:** https://go.drugbank.com/data_packages
- **Nội dung:** 14,000+ INN drug names + synonyms — tên quốc tế áp dụng toàn cầu
- **Status:** Download tạm dừng — check periodically
- **Use:** Map INN names → Vietnamese brand/generic names → mở rộng drug_db.json

### Vietnamese Healthcare (HF)
- **HuggingFace:** `urnus11/Vietnamese-Healthcare`
- **Size:** 466 MB (vinmec.com articles incl. drug articles)
- **License:** Chưa rõ — verify trước dùng
- **Use:** Mine drug name vocabulary từ vinmec drug articles → expand aliases

---

## BẢNG TÓMMẮT — STATUS

| Dataset | Size | License | Download | Dùng ngay? | Dự án tương lai |
|---|---|---|---|---|---|
| VietMed (ASR) | 16h/2,216h | CC-BY-4.0 | ✅ HF | ✅ P1 | Multilingual expand |
| VietMed-NER | 9K samples | CC-BY-4.0 | ✅ HF | ✅ P1 | Spoken NER evolution |
| VietMed-Sum | 106K rows | MIT | ✅ HF | ✅ P1 | Summarization module |
| MultiMed | 5 languages | CC-BY-4.0 | ✅ GH | 🟡 P3 | Bilingual BS |
| ViMedCSS | 34h | CC-BY-4.0 | ✅ HF | ✅ P1 | Drug code-switch |
| VN Medical QA | 9.3K | Apache-2.0 | ✅ HF | ✅ P1 | Specialty expand |
| VLSP2020 | 100h | CC-BY-4.0 | ✅ HF | ✅ P2 | ASR base |
| BUD500 | 500h | Apache-2.0* | 🔶 Stream | 🟡 P2 | Acoustic model |
| ViMQ | 9K | Unclear | ✅ GH | 🟡 P2 verify | Drug NER |
| ViMedNER | 8K+ | CC-BY-3.0 | ❌ Not yet | 🔮 Future | Text NER |
| PhoNER_COVID19 | 35K entities | Research only | ✅ GH | ❌ No commercial | Backbone only |
| GigaSpeech2-VI | 6,039h | Unclear | ✅ HF | 🟡 P3 | Acoustic pre-train |
| VietSuperSpeech | 267h | TBD | 🔮 Check | 🔮 Future | Conversational |
| Drugbank.vn | 10K+ drugs | Gov/scrape | ❌ Manual | 🔮 Contact DAV | Drug DB expand |
| DrugBank Open | 14K INN | CC-0 | 🔶 Intermittent | 🔮 Check | INN names |
| MIMIC-III | 2M notes | DUA | ✅ PhysioNet | ❌ EN only | Schema reference |
| n2c2 2018 | 500 notes | DUA | ✅ PhysioNet | ❌ EN only | Drug NER schema |

Legend: ✅ Sẵn sàng | 🔶 Cần điều kiện | 🔮 Tương lai | ❌ Không áp dụng

---

## WORKFLOW SỬ DỤNG

```
BƯỚC 1 — Download P1 (~6.6 GB):
  python -X utf8 scripts/download_datasets.py --list
  python -X utf8 scripts/download_datasets.py

BƯỚC 2 — Phân tích entity mapping VietMed-NER → MediVoice (DATASET-002):
  # Xem 18 entity types + counts → quyết định mapping strategy
  from datasets import load_from_disk
  ds = load_from_disk("data/external/VietMed-NER")
  # DISEASESYMPTOM(4,716) → SYMPTOM+DIAGNOSIS
  # DRUGCHEMICAL → MEDICATION
  # UNITCALIBRATOR → VITAL
  # DATETIME → FOLLOWUP

BƯỚC 3 — Fine-tune PhoBERT+CRF (TRAIN-002) — cần FID-VN-007:
  # Training script: scripts/train_ner.py (chưa có)
  # Target: Drug CEER 0.90 → <0.10

BƯỚC 4 — Fine-tune PhoWhisper (TRAIN-001) — cần GPU:
  # Training script: scripts/train_asr.py (chưa có)
  # Target: WER 35-40% → <20%

BƯỚC 5 — Benchmark:
  python -X utf8 tools/bench_ceer.py --full --gt data/audio/corpus/semi_synthetic/groundtruth_all.json
```

---

## STORAGE ESTIMATE

```
data/external/
  VietMed/                ~2.5 GB    P1 — 16h labeled portion
  VietMed-NER/            ~50 MB     P1 — NER gold labels
  ViMedCSS/               ~4.0 GB    P1 — code-switching ASR
  VietMed-Sum/            ~50 MB     P1 — summarization
  Vietnamese-Medical-QA/  ~10 MB     P1 — QA vocab
  ─────────────────────────────────────────────────────
  P1 Total:               ~6.6 GB

  VLSP2020-VinAI/         ~11.6 GB   P2 — spontaneous speech
  ViMQ/                   ~20 MB     P2 — medication NER
  ─────────────────────────────────────────────────────
  P1+P2 Total:            ~18.3 GB

  BUD500/ (streaming)     ~0 MB local   100 GB nếu full — KHÔNG LÀM
```

---

## TÀI LIỆU THAM KHẢO

| Paper | Venue | arXiv | Dùng cho |
|---|---|---|---|
| VietMed | LREC-COLING 2024 | - | ASR baseline |
| VietMed-NER | NAACL 2025 | 2406.13337 | NER primary |
| VietMed-Sum | Interspeech 2024 | - | Summarization |
| MultiMed | ACL 2025 | - | Multilingual methodology |
| ViMedCSS | - | 2602.12911 | Code-switching ASR |
| ViMedNER | EAI INIS 2024 | - | Text NER (future) |
| VietSuperSpeech | - | 2603.01894 | Conversational (future) |

---

*MediVoice VN | DATA_CATALOG v1.1 | 2026-06-09*
*Script download: `scripts/download_datasets.py` | Storage: `data/external/`*
*Xác minh: papers + HuggingFace + GitHub (2026-06-09)*
