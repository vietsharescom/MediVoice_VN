# FID-VN-015 — Pronunciation Recognition Lab (Part 3 Redesign) + Scientific Basis cho Part 1/2
# MediVoice VN | Feature Intent Document
# Status: IMPLEMENTED ✅ — Approved by Andy "đồng ý" 2026-06-11, implemented same session
# Author: Claude | Created: 2026-06-11 | Approved: 2026-06-11
# Refs: FID-VN-014 (Voice Calibration Lab — Part 1/2/3 v1, đã DONE) · FID-VN-013 §2.4
#       (Drug Pronunciation Wizard, đã DONE) · CONS-20260610-005

---

| Field | Value |
|---|---|
| FID ID | FID-VN-015 |
| Layer | Frontend (PWA) + reference audio assets (static) — KHÔNG đổi pipeline L0→L10 |
| LOC estimate | ~300-380 LOC |
| Risk level | LOW-MEDIUM (TTS pre-gen offline, không gửi audio BS ra ngoài) |
| Created | 2026-06-11 |
| Approved by | Andy ("đồng ý" — Q1-Q5 theo đề xuất Claude) |
| Approved date | 2026-06-11 |

---

## 1. WHY

Andy đề xuất (2026-06-11) đổi tên "🎓 Luyện đọc thuốc" → **"Nhận dạng giọng nói —
tên thuốc & thuật ngữ chuyên ngành"** (đã đổi tên UI ngay, Tầng 3 — xem
`src/api/static/index.html`) và redesign luồng Part 3 thành:

1. Hiển thị tên thuốc/thuật ngữ (vd "Paracetamol") + **nút "🔊 Nghe mẫu"** — phát
   audio chuẩn cách đọc phiên âm tiếng Việt (vd "pa-ra-xê-ta-môn")
2. Nút "🎤 Đọc" — BS thu âm theo cách của mình
3. Hiển thị **transcript theo dòng thời gian** (những gì AI nghe được, vd
   "pa ra xê ta môn") + **waveform/đường cao độ (pitch)** phía trên
4. Nếu khớp với chuẩn → hiển thị **2 đồ hình (waveform/pitch) chuẩn vs thực tế**
   để BS thấy trực quan
5. BS có thể đọc lại nhiều lần; nếu chưa khớp nhưng BS muốn dừng → **"Tạm chấp
   nhận"** → AI vẫn lưu (giống AC-011 hiện có) + khuyến khích "đọc thêm vài lần
   để AI nhận dạng tốt hơn"

Đồng thời Part 1 (vùng miền) và Part 2 (bài đọc chuẩn) cần hiển thị **cơ sở khoa
học/kỹ thuật đang dùng**, và liệt kê các kỹ thuật khác để Andy biết/tham khảo
(không nhất thiết implement ngay).

---

## 2. RESEARCH — Cơ sở khoa học (web search 2026-06-11)

### 2.1 Phương ngữ VN — đặc điểm ngữ âm (Part 1)

| Vùng | Đặc điểm chính |
|---|---|
| Bắc (Hà Nội) | Coi là giọng "chuẩn"; phân biệt rõ phụ âm cuối c/t, n/ng, d/gi |
| Trung (Huế) | Không phân biệt dấu hỏi/ngã (phát âm nửa vời, gần dấu nặng); nói nhanh, ngữ điệu trầm bổng, "mô/răng/rứa/ni/tê/chi" |
| Nam | c/t → c, n/ng → ng, v → d (vd "vui vẻ" → "dui dẻ") |

Sources: [VIEGEN — Phân biệt giọng vùng miền](https://viegen.vn/phan-biet-giong-vung-mien/),
[Hocvienphoenix — Đặc trưng phát âm giọng vùng miền](https://hocvienphoenix.com/2024/03/16/dat-trung-phat-am-cua-giong-vung-mien-trong-tieng-viet/),
[ilovemyvoice — Giọng nói Việt từ Bắc đến Nam](http://ilovemyvoice.vn/giong-noi-viet-tu-bac-vao-nam/)

### 2.2 Kỹ thuật nhận dạng vùng miền — list để tham khảo/lựa chọn

| # | Kỹ thuật | Độ chính xác / ghi chú | Trạng thái MediVoice |
|---|---|---|---|
| 1 | Lexical/từ điển (DIALECT_MAP, từ đặc trưng "mô/rứa", "dui dẻ"...) | Giải thích được, 0 chi phí audio | ✅ ĐANG DÙNG (`detect_region()`, FID-VN-014 §2.1) |
| 2 | MFCC + F0 (fundamental frequency) | MFCC alone ~58.6%, MFCC+F0 ~70.8% | Chưa dùng — cần model riêng |
| 3 | ANN/SVM/k-NN trên acoustic features | Tốt hơn Random Forest | Chưa dùng |
| 4 | Transfer learning từ ASR pretrained | Cải thiện ~46.7% so baseline | Chưa dùng |
| 5 | Dataset 63 tỉnh (>9000 samples) | Accuracy 71-83% | Chưa dùng — cần dataset lớn |

Sources: [Automatic Identification of Vietnamese Dialects (VJS)](https://vjs.ac.vn/index.php/jcc/article/view/7905),
[Vietnamese Regional Voice Dataset (SpringerLink)](https://link.springer.com/chapter/10.1007/978-981-96-4288-5_18),
[Transfer learning for low-resource accent recognition (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S0952197624000538)

**Đề xuất**: giữ #1 cho v1 (đã làm, rẻ, giải thích được). #2-5 → "Phase 1 Research
Track" — cần audio dataset lớn + model riêng, không phù hợp pilot hiện tại.

### 2.3 Kỹ thuật phân tích bài đọc chuẩn (Part 2)

- Đang dùng: speaking rate (từ/giây), pause detection (RMS-based silence),
  pitch median (`vtln.estimate_warp_factor()` qua `librosa.pyin`)
- Có thể thêm (Phase 1 Research): jitter/shimmer (ổn định pitch/amplitude — voice
  quality), prosodic features đầy đủ (duration/energy/pitch contour theo thời gian)

### 2.4 Phonation type (breathy/creaky) — bổ sung quan trọng (Andy 2026-06-11)

Theo Andrea Hoa Pham, *"The Key Phonetic Properties of Vietnamese Tone: A
Reassessment"* (giọng Bắc chuẩn, 8 thanh: ngang/huyền/sắc1/nặng1/hỏi/ngã/sắc2/
nặng2):

- **Phonation type** (breathy = giọng thở, creaky = giọng gằn, modal = bình
  thường) — chứ KHÔNG chỉ pitch (F0) — mới là tín hiệu chính người nghe dùng để
  phân biệt thanh điệu.
- Thanh **hỏi/ngã** đặc biệt bị "lệch" nếu chỉ nhìn pitch contour; cần thêm
  phonation feature mới giải thích đúng.
- Hệ quả cho voice profiling tiếng Việt: pitch-only (như `vtln.estimate_warp_factor`
  hiện tại) **không đủ** — cần thêm breathiness/creakiness index (đo qua
  jitter/shimmer + năng lượng dải cao + độ đều của glottal pulses) để:
  - nhận dạng vùng miền chính xác hơn (Bắc/Trung/Nam có pattern phonation khác
    nhau, đặc biệt liên quan tới việc Trung/Nam không phân biệt hỏi/ngã)
  - hiểu "style giọng" từng BS (thở nhiều / gằn nhiều / đều) → tinh chỉnh ASR
    decoding (beam search, smoothing) theo từng nhóm

**Đề xuất tích hợp vào FID-VN-015**:
- v1 (trong scope FID này): mở rộng `extract_f0_contour()` (đã đề xuất §3.2)
  thêm 2 chỉ số đơn giản, tính cùng lúc với f0 contour, KHÔNG cần model riêng:
  - `jitter` (biến thiên chu kỳ pitch frame-to-frame, %) — proxy cho creakiness
  - `shimmer` (biến thiên biên độ frame-to-frame, %) — proxy cho breathiness
  - Lưu 2 giá trị này vào `doctor_profiles` (cột mới `jitter_pct`,
    `shimmer_pct`, additive migration giống FID-VN-014) — hiển thị tham khảo,
    KHÔNG dùng để auto-adapt ASR (giữ nguyên tinh thần "visualization only" của
    FID-VN-013/014)
- Phase 1 Research Track: phân loại phonation type đầy đủ (breathy/creaky/modal
  classifier), dùng phonation pattern để cải thiện `detect_region()` (hiện tại
  thuần lexical), và điều chỉnh ASR decoding theo phonation profile — cần
  dataset + validation, không phù hợp pilot hiện tại.

Source: Pham, Andrea Hoa (2003), *"The Key Phonetic Properties of Vietnamese
Tone: A Reassessment"* — đề xuất Andy cung cấp link/PDF cụ thể nếu có để Claude
đọc sâu hơn khi implement jitter/shimmer.

### 2.5 CAPT (Computer-Assisted Pronunciation Training) — cho Part 3

- GOP (Goodness of Pronunciation): điểm dựa trên posterior probability của ASR
  acoustic model — cần access vào internals của PhoWhisper (phức tạp)
- DTW (Dynamic Time Warping): align pitch contour giữa audio mẫu và audio user
  để overlay 2 đường cong
- Feedback: scalar score + visual diff (waveform/spectrogram overlay)

Sources: [CAPT overview (EmergentMind)](https://www.emergentmind.com/topics/computer-assisted-pronunciation-training),
[End-to-End Mispronunciation Detection (arXiv)](https://arxiv.org/pdf/2103.03023),
[MuFFIN — Multifaceted Pronunciation Feedback (arXiv)](https://arxiv.org/pdf/2510.04956)

### 2.6 TTS reference cho phát âm thuốc — khảo sát thêm (Andy 2026-06-11)

Không tìm thấy nghiên cứu chuyên biệt "drug name pronunciation recognition"
cho tiếng Việt. 3 nguồn liên quan có thể tham khảo cho audio mẫu (Q1):

| Nguồn | Ghi chú |
|---|---|
| gTTS (Google TTS) | Đã dùng cho Queue TTS (FID hiện tại) — offline sau khi pre-gen, miễn phí, KHÔNG phân biệt vùng miền |
| Narakeet — Vietnamese Pronunciation Generator | AI TTS tiếng Việt, **có phân biệt giọng Bắc/Nam** — có thể dùng tạo "giọng mẫu" theo vùng miền BS đã chọn ở Part 1, nhưng là dịch vụ trả phí/cloud ngoài VN → cần kiểm tra compliance NĐ13/2023 (data residency) nếu audio xử lý qua cloud nước ngoài |
| HowToPronounce / SVFF AI Pronunciation | Từ điển phát âm đa ngôn ngữ, có module luyện phát âm (nghe-lặp-so sánh) — tham khảo UX pattern, không phải nguồn audio trực tiếp cho thuật ngữ y khoa VN |

**Khuyến nghị (giữ nguyên Q1 = gTTS)**: gTTS pre-gen offline vẫn là lựa chọn an
toàn nhất cho v1 (NĐ13/2023 — data tại VN, không phụ thuộc cloud ngoài). Ý
tưởng "giọng mẫu theo vùng miền" (Narakeet) ghi vào Phase 1 Research Track —
chỉ xem xét nếu có TTS engine VN nội địa (VNG/FPT/VNPT) hỗ trợ accent Bắc/Nam.

**Đề xuất v1 (thấp LOC, không cần GPU)**:
- Audio mẫu: gTTS (đã dùng cho Queue TTS — `docs/records/DESIGN_REPORT` Queue
  Management) đọc **phiên âm tiếng Việt** của thuật ngữ (vd "pa ra xê ta môn"
  cho Paracetamol) — pre-generate 1 lần, cache file `.mp3` trong
  `src/api/static/audio/pronunciation/`
- Transcript BS đọc: PhoWhisper transcribe bình thường (đã có, AC-010) → hiển
  thị trực tiếp text
- Pitch contour: mở rộng `vtln.estimate_warp_factor()` để trả thêm full f0
  contour (list, không chỉ median) cho cả audio mẫu (tính 1 lần, cache) và audio
  BS — vẽ 2 đường trên canvas, time-normalized (0-100%), KHÔNG cần DTW ở v1
- "Khớp" — Levenshtein ratio giữa transcript_clean và phiên âm chuẩn → ratio ≥
  ngưỡng (đề xuất 0.8) → badge "✅ Khớp"; ratio thấp hơn nhưng BS bấm "Tạm chấp
  nhận" → vẫn `add_confirmed_alias()` (giống AC-011) + toast khuyến khích đọc
  thêm

### 2.7 Phase 1 Research Track — danh mục tham khảo mở rộng (Andy 2026-06-11)

> ⚠️ Danh sách do Andy tổng hợp (qua AI khác), Claude **CHƯA verify từng link/
> tên công trình** — trước khi trích dẫn vào tài liệu compliance (SRS/RTM) cần
> WebSearch xác minh nguồn thật. Ghi lại đây để định hướng Phase 1, KHÔNG dùng
> làm căn cứ pháp lý/khoa học chính thức cho tới khi verify.

**A. Nhận dạng vùng miền (Dialect Recognition)**
| Nguồn | Kỹ thuật | Ghi chú |
|---|---|---|
| VLSP — Vietnamese Regional Accent Recognition Challenge | MFCC, i-vector, x-vector, CNN+LSTM, Transformer speaker embedding | Cuộc thi chính thức về nhận dạng Bắc/Trung/Nam — cần tìm dataset/benchmark cụ thể |
| VIVOS Corpus (FPT/AILab) | ASR training, có metadata vùng miền | MediVoice đã biết VIVOS (TECH DECISIONS) — kiểm tra license cho dialect labels |
| UIT-ViVoice (ĐH CNTT TP.HCM) | Dataset gán nhãn vùng miền + speaker verification | |
| VAIS — Vietnamese Accent Identification | Mel-spectrogram + CNN + attention classifier | |
| "Vietnamese Dialect Identification Using Deep Neural Networks" (ĐH Bách Khoa) | CNN + BiLSTM, accuracy ~92% | Số liệu cần verify |

**B. Thanh điệu tiếng Việt (Tone — nền tảng Voice Profiling)**
| Nguồn | Nội dung |
|---|---|
| Andrea Hoa Pham (2003) | Breathiness/creakiness > pitch cho 8 thanh — đã đưa vào §2.4 |
| Nguyễn & Edmondson — "Thanh điệu tiếng Việt hiện đại" | F0 + formant + spectrogram + glottal pulses, phân biệt hỏi/ngã/nặng |
| LIMSI-CNRS — "Acoustic Characteristics of Vietnamese Tones" | Đo bằng EGG (Electroglottography): creaky/breathy/modal voice |

**C. AI Tone Classification**
| Nguồn | Kỹ thuật | Ghi chú |
|---|---|---|
| "Vietnamese Tone Recognition Using CNN-LSTM" | Mel-spectrogram + CNN + LSTM, accuracy ~95% | Số liệu cần verify |
| "End-to-End Tone Recognition for Vietnamese Speech" | CTC + attention, tone embedding tự học | |
| "Tone Error Correction for Vietnamese ASR" | Post-processing sửa lỗi thanh điệu | Hữu ích cho L1b/L1c |

**D. Kết hợp Dialect + Tone modeling**
| Nguồn | Kết quả |
|---|---|
| "Vietnamese Dialect and Tone Modeling for ASR" | Tone embedding + accent embedding → giảm WER 10-15% | Số liệu cần verify |

**Định hướng Phase 1 (sau TRAIN-001, KHÔNG block pilot hiện tại)**:
1. Voice Calibration Module mở rộng — pitch + breathiness + creakiness + tone
   shape + accent → `DoctorVoiceProfile` (đã có khung từ FID-VN-014, mở rộng
   §2.4 jitter/shimmer là bước đầu)
2. Accent-aware ASR — accent embedding giảm lỗi vùng miền (cần fine-tune,
   nằm trong scope TRAIN-001 mở rộng)
3. Tone-aware ASR — tone embedding cho PhoWhisper, giảm lỗi hỏi/ngã/nặng
4. Drug Pronunciation Wizard — so khớp phoneme + alias theo vùng miền (mở rộng
   từ §2.5/§3 FID này)
5. UI tham khảo pattern "ello.ai" — avatar + waveform + pitch contour + tone
   curve + accent badge (MediVoice đã có avatar mirror + waveform từ
   FID-VN-014, tone curve là phần mới)

→ Việc cần làm trước khi mở Phase 1: Andy/Claude WebSearch verify từng nguồn ở
trên (link, năm xuất bản, license dataset), đánh giá license/compliance
(NĐ13/2023 nếu dataset/cloud ngoài VN), và xác nhận TRAIN-001 đã đạt baseline
WER mục tiêu trước (theo CONS-20260610-005 / PA-014).

---

## 3. WHAT — Implementation outline (v1)

### 3.1 Phiên âm chuẩn cho thuật ngữ (data)
- Cần bảng "INN → phiên âm tiếng Việt" (vd `Paracetamol → "pa ra xê ta môn"`,
  `Amlodipine → "am lô đi pin"`). Nguồn: heuristic transliteration rules
  (tiếng Anh/Pháp → cách đọc kiểu Việt) áp dụng cho `drug_db.json` (110 thuốc).
  Có thể tái dùng 1 phần `phonetic_variants` đã có trong drug_db (FID-VN-013).

### 3.2 Backend (additive)
- `scripts/gen_pronunciation_audio.py` — chạy 1 lần (offline), gTTS generate
  `.mp3` cho mỗi phiên âm chuẩn → `src/api/static/audio/pronunciation/<inn>.mp3`
- `src/core/vtln.py` — thêm `extract_f0_contour(y, sr) -> list[float]` (pure
  function, tách từ `estimate_warp_factor`, KHÔNG đổi hàm cũ)
- `src/core/calibration_metrics.py` (FID-VN-014, mở rộng) — thêm
  `compute_jitter_shimmer(y, sr) -> tuple[float, float]` (jitter %, shimmer %)
  — proxy cho creakiness/breathiness theo Pham (2003), §2.4. Pure function,
  dùng chung cho Part 2 (bài đọc chuẩn) lẫn Part 3 nếu cần.
- `src/core/l7_storage.py` — thêm 2 cột `doctor_profiles`: `jitter_pct REAL`,
  `shimmer_pct REAL` (additive migration, theo pattern FID-VN-014
  `update_calibration_results()` — mở rộng COALESCE)
- `src/models/doctor_profile.py` — thêm `jitter_pct: Optional[float] = None`,
  `shimmer_pct: Optional[float] = None`
- `src/api/main.py` — endpoint mới:
  - `GET /api/pronunciation-reference/{inn}` → trả `{audio_url, phonetic_text,
    f0_contour}` (f0_contour của audio mẫu, tính 1 lần lúc gen, cache JSON)
  - Mở rộng `POST /api/doctors/{cchn}/pronunciation-enroll` (đã có) → trả thêm
    `f0_contour` của audio BS + `match_ratio` (Levenshtein)
  - Mở rộng `POST /api/doctors/{cchn}/calibration/passage` (FID-VN-014) → tính
    thêm `jitter_pct`/`shimmer_pct`, lưu qua `update_calibration_results()`

### 3.3 Frontend (Wizard modal — FID-VN-013 §2.4, đổi tên đã xong)
- Thêm nút "🔊 Nghe mẫu" → play `audio_url` từ `/api/pronunciation-reference/{inn}`
- Sau khi BS đọc → hiển thị transcript + canvas 2 đường f0 contour (chuẩn vs BS,
  time-normalized)
- Badge "✅ Khớp" nếu `match_ratio ≥ 0.8`, ngược lại nút "Đọc lại" + "Tạm chấp
  nhận" (giữ luồng AC-011 hiện có)

### 3.4 Frontend — hiển thị jitter/shimmer (Lab Hiệu chỉnh, step 2)
- `#lab-passage-result` (FID-VN-014) hiển thị thêm 2 chỉ số tham khảo: "Độ rung
  giọng (jitter)" và "Độ thở (shimmer)" dạng % + nhãn mô tả ngắn (vd "Bình
  thường" / "Hơi gằn" / "Hơi thở nhiều") — KHÔNG auto-adapt, chỉ hiển thị, đúng
  tinh thần tooltip "chỉ visualization" (FID-VN-013/014)

---

## 4. DECISION NEEDED — Andy approve

- **Q1 (TTS reference)**: dùng gTTS pre-generate (cần internet 1 lần lúc build,
  sau đó offline — giống Queue TTS) hay ghi âm mẫu thật từ 1 giọng BS chuẩn?
  Khuyến nghị: gTTS pre-gen — scale dễ cho 110 thuốc, không cần thu âm thật.
- **Q2 (Pitch contour viz)**: v1 đơn giản — 2 đường line chart time-normalized,
  KHÔNG DTW — hay đầu tư DTW alignment ngay? Khuyến nghị: v1 đơn giản trước,
  DTW → Phase 1 nếu BS thấy hữu ích.
- **Q3 (Ngưỡng "khớp")**: Levenshtein ratio ≥ 0.8 coi là "Khớp ✅"? (có thể chỉnh
  sau khi pilot có dữ liệu thật)
- **Q4 (Phiên âm chuẩn 110 thuốc)**: Claude tự generate heuristic transliteration
  (rule-based Anh/Pháp → Việt) cho `drug_db.json`, Andy review sau — hay Andy
  muốn cung cấp danh sách phiên âm chuẩn riêng (vd từ 1 dược sĩ)?
- **Q5 (Jitter/shimmer — §2.4, theo Pham 2003)**: thêm `compute_jitter_shimmer()`
  vào v1 của FID này (hiển thị tham khảo trong Lab step 2, ~30 LOC) hay tách
  riêng thành FID-VN-016 sau? Khuyến nghị: gộp vào FID-VN-015 luôn — cùng
  pattern với `extract_f0_contour()` (cùng audio, cùng endpoint
  `calibration/passage`), tránh phải mở lại migration `doctor_profiles` lần
  nữa. Nếu Andy có link/PDF bài Pham (2003), gửi để Claude đọc kỹ trước khi
  code công thức jitter/shimmer cho đúng.

---

## 5. HARD CONSTRAINTS

- KHÔNG đổi pipeline L0→L10 — TTS reference + pitch contour chỉ là UI helper
- Audio BS vẫn purge ngay sau xử lý (như mọi luồng khác)
- Audio mẫu (gTTS) KHÔNG chứa giọng BS — không phải biometric data, lưu static
- TRAIN-001 (ưu tiên #1) không bị ảnh hưởng — toàn bộ FID này CPU/frontend +
  1 lần pre-gen offline

---

## 6. ESTIMATE

| Phần | LOC | Ghi chú |
|---|---|---|
| Phiên âm chuẩn 110 thuốc (data + heuristic gen script) | ~60 | `scripts/gen_pronunciation_audio.py` + data file |
| `extract_f0_contour()` (vtln.py, pure function) | ~25 | tách từ `estimate_warp_factor` |
| `compute_jitter_shimmer()` + 2 cột DB + model field (§2.4/Q5) | ~50 | `calibration_metrics.py` + `l7_storage.py` migration + `doctor_profile.py` |
| Backend endpoints (`pronunciation-reference`, mở rộng `pronunciation-enroll`, `calibration/passage`) | ~70 | `src/api/main.py` |
| Frontend: nút nghe mẫu + canvas pitch overlay + badge khớp + jitter/shimmer display | ~110 | `index.html` Wizard modal + Lab step 2 |
| Tests | ~60 | |
| **Total** | **~375** | |

---

*FID-VN-015 | DRAFT 2026-06-11 | Claude*
*Chờ Andy trả lời Q1-Q4 trước khi implement*
