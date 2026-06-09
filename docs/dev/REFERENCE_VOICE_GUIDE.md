# REFERENCE_VOICE_GUIDE.md
# Hướng dẫn thu Reference Voice từ Pilot BS
# MediVoice VN | v2.0 | 2026-06-12
# Cập nhật từ v1.0: clip dài hơn, nội dung đủ 5 entity types, distribution frame
# Dùng cho: CONS-002-SPRINT6 — F5-TTS voice cloning → TRAIN-001

---

## MỤC ĐÍCH

Reference voice là **3 đoạn ghi âm (~20s mỗi clip, tổng ~60s)** của chính BS.
Dùng cho 2 mục tiêu:

```
[A] Speaker Embedding cho F5-TTS:
    Reference voice (3 clips × 20s)
    → F5-TTS clone giọng BS
    → Synthetic corpus (1,100 clips, balanced distribution)
    → Fine-tune PhoWhisper
    → Drug CEER: 0.989 → target < 0.15

[B] Baseline ASR evaluation:
    Reference voice → PhoWhisper transcribe → WER thật của từng BS
    → Biết baseline trước fine-tune
```

**Pipeline đúng thứ tự (v2.0):**
```
CLINICAL FRAME (distribution: Drug 35% / Symptom 20% / Vital 15% / Diag 15% / FU 10% / Noise 5%)
    → Controlled Medical Text (script dưới đây)
    → Phonetic Normalizer ("120/80" → "một trăm hai mươi trên tám mươi")
    → F5-TTS (speaker = ref voice clone)
    → Synthetic Audio Dataset (1,100 clips)
    → PhoWhisper Fine-tune
    → NER + Drug CEER Eval
```

---

## YÊU CẦU KỸ THUẬT (v2.0)

| Yêu cầu | Chi tiết |
|---|---|
| Số clip | **3 clips** mỗi BS |
| Thời lượng | **~20 giây** mỗi clip — KHÔNG ngắn hơn 15s |
| Tổng / BS | **~60 giây** — F5-TTS cần ≥30s để embedding tốt |
| Phòng | Yên tĩnh — tắt quạt, đóng cửa, tắt điều hoà nếu ồn |
| Thiết bị | Điện thoại cầm cách miệng ~20cm, KHÔNG bật loa ngoài |
| Format | .m4a / .mp3 / .wav — Claude sẽ convert sang 16kHz mono WAV |
| Tốc độ | Tốc độ khám bình thường — KHÔNG đọc chậm từng chữ |
| Style | Đọc script, paraphrase tự nhiên OK — không cần đọc từng chữ |

---

## NỘI DUNG BS ĐỌC — 3 CLIPS

> **Tại sao cùng topic nhưng bệnh nhân khác nhau?**
> — Để đo drug WER trực tiếp giữa các giọng (cùng tên thuốc)
> — Nhưng context bệnh nhân khác → nghe tự nhiên, không phải robot
> — BS được phép paraphrase miễn là giữ đúng tên thuốc + số liệu

---

### Clip 1 — Tiếp nhận + Sinh hiệu (~20 giây)

> Đọc tự nhiên như đang khám thật. BS nên thêm tên bệnh nhân thật (giả) và nghề nghiệp.

**Script mẫu (paraphrase tự nhiên OK):**

> *"Bệnh nhân nam [30-60] tuổi, nghề [kế toán/giáo viên/nông dân], vào khám vì [đau họng / ho / sốt / đau đầu] được [2-5] ngày nay.*
> *Sinh hiệu: huyết áp một trăm [hai mươi / ba mươi] trên [bảy mươi / tám mươi], mạch [tám mươi / chín mươi] lần mỗi phút, nhiệt độ ba mươi [bảy / tám] phẩy [năm / tám] độ, nhịp thở [mười tám / hai mươi] lần mỗi phút.*
> *Bệnh nhân tỉnh táo, tiếp xúc tốt."*

**Entity types covered:** VITAL (BP, pulse, temp, RR) + SYMPTOM + INTAKE

---

### Clip 2 — Chẩn đoán + Kê đơn (~20 giây)

> Đây là clip quan trọng nhất cho drug CEER. Đọc rõ tên thuốc + liều.

**Script mẫu — BS PHẢI đọc đúng các tên thuốc này:**

> *"Chẩn đoán: [viêm họng cấp / viêm phế quản / viêm dạ dày / tăng huyết áp độ một].*
> *Kê đơn: Amoxicillin năm trăm miligam, uống ba lần một ngày trong bảy ngày.*
> *Paracetamol năm trăm miligam, uống khi sốt trên ba mươi tám độ, cách nhau ít nhất bốn giờ.*
> *Omeprazole hai mươi miligam, uống một lần mỗi sáng trước ăn."*

**Entity types covered:** DIAGNOSIS + MEDICATION × 3 + DOSE + FREQUENCY + DURATION

> **Lưu ý cho BS:** Paracetamol / Amoxicillin / Omeprazole — đây là 3 tên thuốc quan trọng nhất cần nhận dạng. Đọc rõ, không đọc tắt.

---

### Clip 3 — Điều trị thêm + Referral + Tái khám (~20 giây)

> Clip này đo NER entity types mở rộng: referral, lab, imaging.

**Script mẫu:**

> *"Cho bệnh nhân làm xét nghiệm công thức máu và CRP.*
> *Nếu CRP trên năm mươi thì chuyển chụp X-quang ngực thẳng.*
> *Siêu âm bụng tổng quát nếu đau bụng không cải thiện sau ba ngày.*
> *Tái khám sau bảy ngày, hoặc sớm hơn nếu sốt không hạ, khó thở, hoặc đau tăng.*
> *Hẹn lại: thứ [Hai / Ba / Tư] tuần sau."*

**Entity types covered:** REFERRAL (lab: CBC, CRP) + REFERRAL (imaging: X-ray, US) + FOLLOWUP + CONDITION (conditional)

---

## PHÂN PHỐI SYNTHETIC DATA (1,100 clips)

Script trên được dùng để tạo synthetic corpus với distribution cân bằng:

| Category | % | Clips | Script coverage |
|---|---|---|---|
| Drug prescription | 35% | 385 | Clip 2 core + variation |
| Symptoms / Chief complaint | 20% | 220 | Clip 1 variation |
| Vital signs | 15% | 165 | Clip 1 core |
| Diagnosis | 15% | 165 | Clip 2 opener |
| Follow-up / Referral | 10% | 110 | Clip 3 |
| ASR noise simulation | 5% | 55 | Inject errors |
| **Total** | **100%** | **1,100** | |

---

## NỘI DUNG MỖI BS — GIỐNG HAY KHÁC?

| Element | Quyết định | Lý do |
|---|---|---|
| Tên thuốc (Amoxicillin, Paracetamol, Omeprazole) | **GIỐNG** tất cả BS | Cần so WER drug trực tiếp giữa các giọng |
| Liều / tần suất | **GIỐNG** | Core CEER measurement |
| Tên bệnh nhân | **KHÁC** (BS tự chọn) | Nghe tự nhiên hơn |
| Chẩn đoán | **KHÁC** (chọn trong danh sách) | Đa dạng hơn |
| Referral | **KHÁC** (xét nghiệm khác nhau) | Phong phú hơn |

**Lựa chọn chẩn đoán cho mỗi BS (chọn 1):**
- HN: viêm họng cấp + viêm phế quản
- DN: nhiễm siêu vi đường hô hấp trên + tăng huyết áp độ một
- SG: viêm dạ dày cấp + tiểu đường type 2

---

## PHONETIC NORMALIZATION — LỖI LỚN NHẤT CỦA ASR Y TẾ

PhoWhisper cần nghe **dạng nói** (không phải dạng số):

| Dạng viết | ❌ Không đọc | ✅ Đọc |
|---|---|---|
| 120/80 mmHg | "một hai không / tám không" | "một trăm hai mươi trên tám mươi" |
| 37.8°C | "ba bảy chấm tám" | "ba mươi bảy phẩy tám độ" |
| 500mg | "năm trăm m g" | "năm trăm miligam" |
| 3×/ngày | "ba lần" (đủ) | "ba lần một ngày" |
| 7 ngày | "bảy ngày" | "trong bảy ngày" |
| CRP >50 | "C R P lớn hơn năm mươi" | "CRP trên năm mươi" |

---

## CÁCH GHI ÂM

### Android
```
1. Mở "Máy ghi âm" — chọn chất lượng CAO
2. Bấm REC → đọc câu → bấm STOP (mỗi clip = 1 file riêng)
3. Kiểm tra thời lượng ≥ 15 giây
4. Nghe lại — nếu có tiếng ồn to hoặc đọc vấp → ghi lại
5. Đặt tên: REF_DN_Clip1.m4a / REF_DN_Clip2.m4a / REF_DN_Clip3.m4a
```

### iPhone
```
1. App "Ghi âm" (Voice Memos — icon đỏ)
2. Bấm nút tròn đỏ → đọc → STOP
3. Nhấn giữ → "Chia sẻ" → gửi Andy
```

---

## CHECKLIST TRƯỚC KHI GHI

- [ ] Tắt quạt / điều hoà nếu ồn
- [ ] Điện thoại im lặng hoàn toàn
- [ ] Đọc script 1 lần thầm trước
- [ ] Clip mỗi đoạn ≥ 15 giây khi nghe lại
- [ ] Không nói quá chậm / quá nhanh
- [ ] Tên thuốc đọc rõ: Amoxicillin / Paracetamol / Omeprazole

---

## GỬI FILE

Gửi cho **Andy** qua Zalo cá nhân hoặc email vietshares.com@gmail.com

Đặt tên rõ ràng:
```
REF_HN_Clip1.m4a    ← BS Hà Nội, clip sinh hiệu
REF_HN_Clip2.m4a    ← BS Hà Nội, clip kê đơn
REF_HN_Clip3.m4a    ← BS Hà Nội, clip referral+tái khám
REF_DN_Clip1.m4a    ← BS Đà Nẵng ...
REF_SG_Clip1.m4a    ← BS Sài Gòn ...
```

---

## SAU KHI NHẬN FILE (Andy → Claude)

```
1. Andy: bỏ file vào data/audio/reference_voices/BS_hanoi/ | BS_danang/ | BS_saigon/
2. Claude: convert → 16kHz mono WAV
3. Claude: chạy eval_ref_voices.py → WER baseline thật + NER check
4. Claude: generate 1,100 clips via Vbee API (balanced distribution)
5. Claude: TRAIN-001 fine-tune PhoWhisper
6. Claude: BENCH-002b — CEER thật trước và sau fine-tune
```

---

## LƯU Ý BẢO MẬT

- Clip chỉ chứa câu mẫu hoặc tên bệnh nhân giả — KHÔNG dùng bệnh nhân thật
- Dùng nội bộ train AI — không chia sẻ bên ngoài
- BS có quyền yêu cầu xoá reference voice bất kỳ lúc nào

---

## TIMELINE (CẬP NHẬT v2.0)

| Bước | Ai | Thời gian |
|---|---|---|
| BS ghi 3 clips × 20s | Pilot BS | 15 phút |
| Gửi về Andy | BS → Andy | Ngay |
| Convert + WER baseline | Claude | 10 phút |
| Generate 1,100 clips (Vbee API) | Claude | 2–4 giờ |
| Fine-tune PhoWhisper (TRAIN-001) | Claude | 4–8 giờ |
| BENCH-002b re-test | Claude | 1 giờ |

---

*REFERENCE_VOICE_GUIDE v2.0 | MediVoice VN | 2026-06-12*
*ChatGPT review integrated: distribution frame, phonetic normalization, clip duration*
*Kết hợp: `docs/dev/SYNTHETIC_AUDIO_REQUIREMENTS.md` + `docs/records/consultations/CONS-20260610-002.md`*
