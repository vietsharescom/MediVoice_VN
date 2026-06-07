# REFERENCE_VOICE_GUIDE.md
# Hướng dẫn thu Reference Voice từ Pilot BS
# MediVoice VN | v1.0 | 2026-06-11
# Dùng cho: CONS-002-SPRINT6 — F5-TTS voice cloning
# Prerequisite cho: Fine-tune PhoWhisper giọng BS thật

---

## MỤC ĐÍCH

Reference voice là **3 đoạn ghi âm ngắn (~10–15s)** của chính BS.
F5-TTS dùng những clip này để **clone giọng BS** → generate 1,100 câu y tế
giọng BS thật → fine-tune PhoWhisper nhận dạng giọng đó chính xác hơn.

```
Reference voice (BS ghi 3 clip) 
  → F5-TTS clone giọng 
  → 1,100 clips y tế giọng BS thật 
  → Fine-tune PhoWhisper 
  → Drug CEER: 0.989 → target < 0.15
```

---

## YÊU CẦU KỸ THUẬT

| Yêu cầu | Chi tiết |
|---|---|
| Số clip | **3 clips** mỗi BS (chọn clip sạch nhất) |
| Thời lượng | **10–15 giây** mỗi clip |
| Phòng | Yên tĩnh — tắt quạt, đóng cửa, tắt điều hoà nếu ồn |
| Thiết bị | Điện thoại, cầm cách miệng ~20cm, KHÔNG bật loa ngoài |
| Tư thế | Ngồi thẳng, micro hướng về phía BS |
| Format | .m4a / .mp3 / .wav đều OK — Claude sẽ convert |

---

## NỘI DUNG BS ĐỌC

> Đọc **tự nhiên**, tốc độ bình thường như đang khám thật.
> KHÔNG đọc chậm rõ từng chữ kiểu đọc sách.
> KHÔNG đọc ký hiệu ngoặc vuông — chỉ thay tên thật vào.

---

### Clip 1 — Giới thiệu (~10 giây)

> *"Tôi là bác sĩ [họ tên đầy đủ], công tác tại [tên phòng khám].
> Tôi đang tham gia dự án MediVoice — phần mềm hỗ trợ ghi bệnh án bằng giọng nói."*

---

### Clip 2 — Khám lâm sàng (~12 giây)

> *"Bệnh nhân vào khám với triệu chứng đau họng ba ngày nay, sốt nhẹ, không có ho.
> Huyết áp một trăm hai mươi trên tám mươi, mạch tám mươi,
> nhiệt độ ba mươi bảy phẩy tám độ."*

---

### Clip 3 — Kê đơn (~15 giây)

> *"Kê Amoxicillin năm trăm miligam, uống ba lần một ngày trong năm ngày.
> Paracetamol năm trăm miligam uống khi sốt trên ba mươi tám độ.
> Tái khám sau năm ngày, hoặc sớm hơn nếu sốt cao không hạ."*

---

## CÁCH GHI ÂM

### Android

```
1. Mở "Máy ghi âm" hoặc "Voice Recorder" (có sẵn trên máy)
2. Chọn chất lượng CAO (nếu có tuỳ chọn)
3. Bấm REC → đọc câu → bấm STOP
   (mỗi câu = 1 file riêng, không ghi liền 3 câu)
4. Nghe lại — nếu có tiếng ồn to → ghi lại
5. Đặt tên: clip1_[tên BS].m4a / clip2_[tên BS].m4a / clip3_[tên BS].m4a
```

### iPhone

```
1. Mở app "Ghi âm" (Voice Memos — icon màu đỏ)
2. Bấm nút tròn đỏ → đọc câu → bấm STOP
3. Nhấn giữ file → "Chia sẻ" → gửi về Andy
```

---

## CHECKLIST TRƯỚC KHI GHI

- [ ] Tắt quạt hoặc ra chỗ yên tĩnh hơn
- [ ] Điện thoại ở chế độ im lặng (không rung, không chuông)
- [ ] Đọc qua câu 1 lần thầm trước khi bấm REC
- [ ] Không nói quá chậm / quá nhanh — tốc độ khám bình thường
- [ ] Nghe lại clip trước khi gửi

---

## GỬI FILE VỀ ĐÂU

Gửi cho **Andy** qua:
- **Zalo cá nhân** (không qua Zalo OA)
- **Email cá nhân** Andy: vietshares.com@gmail.com

Đặt tên file rõ ràng:
```
REF_DN_clip1.m4a    ← BS Đà Nẵng, clip 1
REF_DN_clip2.m4a
REF_DN_clip3.m4a
REF_SG_clip1.m4a    ← BS Sài Gòn, clip 1
REF_SG_clip2.m4a
REF_SG_clip3.m4a
```

---

## SAU KHI NHẬN FILE (Andy → Claude)

```
Andy:  Bỏ file vào data/audio/reference_voices/BS_danang/ và BS_saigon/
Claude: Convert → 16kHz mono WAV
        → Test F5-TTS voice cloning (CONS-002-SPRINT6)
        → Generate 1,100 synthetic clips giọng BS thật
        → Fine-tune PhoWhisper
```

---

## LƯU Ý BẢO MẬT

- Clip chỉ chứa **câu mẫu trung lập** — không có tên bệnh nhân, không có thông tin y tế thật
- Dùng nội bộ để train AI — không chia sẻ bên ngoài
- Andy giữ file gốc, Claude chỉ xử lý bản đã convert
- BS có quyền yêu cầu xoá reference voice bất kỳ lúc nào

---

## TIMELINE

| Bước | Ai làm | Thời gian ước tính |
|---|---|---|
| BS ghi 3 clips | Pilot BS | 10 phút |
| Gửi về Andy | BS → Andy | Ngay sau khi ghi |
| Convert + test F5-TTS | Claude | 30 phút |
| Generate 1,100 clips | Claude (overnight) | 4–8 giờ (CPU) |
| Fine-tune PhoWhisper | Claude + TRAIN-001 | 2–4 giờ |
| BENCH-002b re-test | Claude | 1 giờ |

---

*REFERENCE_VOICE_GUIDE v1.0 | MediVoice VN | 2026-06-11*
*Kết hợp: `docs/dev/SYNTHETIC_AUDIO_REQUIREMENTS.md` (spec 1,100 clips)*
*Prerequisite: `docs/records/consultations/CONS-20260610-002.md` (F5-TTS decision)*
