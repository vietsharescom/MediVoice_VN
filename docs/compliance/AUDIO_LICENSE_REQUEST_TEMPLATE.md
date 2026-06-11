# AUDIO_LICENSE_REQUEST_TEMPLATE.md | DS-VN-COM-021
# Yêu cầu cấp phép sử dụng audio phát âm (pronunciation audio)
# ISO/IEC 42001:2023 Cl.8.1 — Operational planning (third-party content)
# v1.0 | 2026-06-11 | Owner: Andy Phan | Maple Leaf Group
# ⚠️ CHƯA gửi — chỉ là TEMPLATE, Andy điền + gửi qua kênh chính thức của bên cấp phép

---

## BỐI CẢNH

`scripts/gen_pronunciation_audio.py` hiện dùng **gTTS** (Google Text-to-Speech,
miễn phí, không vướng bản quyền) để sinh 149 file audio mẫu (`src/api/static/
audio/pronunciation/*.mp3`) cho 155 thuốc — BS nghe + tập đọc tên thuốc gốc
tiếng Anh trong "Lab Hiệu chỉnh Giọng nói" (Pronunciation Recognition Lab).

Andy muốn dùng audio phát âm chuẩn hơn từ **Merriam-Webster Medical Dictionary**
(vd https://www.merriam-webster.com/dictionary/cetirizine có file audio phát âm
chuẩn). Audio này thuộc sở hữu của **Merriam-Webster / Encyclopaedia Britannica,
Inc.** — KHÔNG được tải hàng loạt + đóng gói vào app khi chưa có giấy phép bằng
văn bản (vi phạm Terms of Use → rủi ro pháp lý cho sản phẩm thương mại).

→ 2 hướng xử lý:

1. **Gửi yêu cầu cấp phép** (template thư bên dưới) tới Merriam-Webster —
   nếu họ đồng ý (bằng văn bản/email), Claude sẽ viết script tải + tích hợp
   audio đó thay/bổ sung cho gTTS.
2. **Nguồn thay thế hợp pháp** (xem mục NGUỒN THAY THẾ bên dưới) — không cần
   chờ phản hồi, có thể dùng song song với gTTS hiện tại.

---

## NGUỒN THAY THẾ HỢP PHÁP (không cần xin phép)

| Nguồn | Giấy phép | Ghi chú |
|---|---|---|
| **gTTS** (đang dùng) | Miễn phí, không giới hạn thương mại (dùng Google Translate TTS API công khai) | Chất lượng "máy đọc", không phải giọng người bản xứ thật |
| **Wikimedia Commons / Wiktionary audio** | CC BY-SA hoặc Public Domain (audio do tình nguyện viên ghi âm) | Giọng người thật, nhưng KHÔNG phải mọi tên thuốc đều có; cần kiểm tra từng từ tại `commons.wikimedia.org` |
| **Forvo** (forvo.com) | Có API thương mại trả phí (Forvo API) — license rõ ràng cho dùng trong app | Giọng người bản xứ thật, nhiều biến thể accent; cần đăng ký + trả phí theo lượng request |
| **Microsoft Azure / AWS Polly Neural TTS** | Trả phí theo ký tự, license thương mại rõ ràng | Chất lượng tự nhiên hơn gTTS đáng kể, có giọng đọc y khoa |

**Khuyến nghị:** Phase 0 (pilot) tiếp tục dùng gTTS (đã hoạt động, miễn phí).
Nếu Andy muốn nâng cấp chất lượng audio cho bản chính thức, **Azure/AWS Polly
Neural TTS** là lựa chọn ít rủi ro pháp lý nhất (license thương mại rõ ràng,
trả phí theo dùng) — Claude có thể viết script tích hợp khi Andy quyết định.

---

## TEMPLATE THƯ XIN CẤP PHÉP — MERRIAM-WEBSTER

> Gửi qua: https://www.merriam-webster.com/contact-us (chọn mục "Permissions")
> hoặc email permissions ghi trên trang "About Us" của Merriam-Webster.
> Andy điền các chỗ `_______` rồi gửi. Nếu họ phản hồi (chấp thuận/từ chối/có
> điều kiện) → dán nội dung phản hồi vào `docs/records/PENDING_REQUESTS.md`
> để Claude xử lý bước tiếp theo.

```
Subject: Permission Request — Use of Pronunciation Audio Files in Medical
         Training Software (MediVoice VN)

To: Merriam-Webster / Encyclopaedia Britannica, Inc. — Permissions Department

Dear Sir/Madam,

I am writing on behalf of _______________ (company: Maple Leaf Group), the
developer of MediVoice VN, a clinical documentation assistant software used
by private medical clinics in Vietnam.

We are developing a "Pronunciation Recognition Lab" feature that helps
Vietnamese-speaking doctors practice pronouncing English/Latin medical drug
names (INN — International Nonproprietary Names) correctly, so that our
speech-recognition system can better understand their dictation.

We would like to request permission to download and embed the pronunciation
audio files (.mp3/.wav) from merriam-webster.com/dictionary/{term}#medical
Dictionary for approximately 150-200 medical/pharmaceutical terms (e.g.,
"cetirizine", "azithromycin", "paracetamol") into our software's static asset
library, for the following use:

- Use case: doctors play the audio to hear correct English pronunciation of
  drug names before practicing aloud (educational/training purpose only)
- Distribution: bundled within MediVoice VN software, installed locally at
  each clinic (NOT publicly redistributed, NOT resold separately)
- Attribution: we are happy to display "Pronunciation audio courtesy of
  Merriam-Webster" or any attribution text you require
- Commercial context: MediVoice VN is offered as a paid subscription service
  to clinics in Vietnam (please advise if a commercial license fee applies)

Could you please let us know:
1. Whether such use is permitted under your Terms of Use, and if so, under
   what conditions (attribution, fee, term, geographic scope)
2. If a commercial license is required, the process and cost to obtain one
3. Any technical access (bulk download / API) you can offer for this purpose

Thank you very much for your time and consideration. We look forward to your
response.

Sincerely,
_______________ (Tên người gửi)
_______________ (Chức vụ)
Maple Leaf Group — MediVoice VN
Email: vietshares.com@gmail.com
```

---

## SAU KHI GỬI

- [ ] Andy gửi thư trên qua kênh chính thức của Merriam-Webster
- [ ] Ghi vào `docs/records/PENDING_REQUESTS.md` (mục TP — chờ phản hồi bên thứ 3)
- [ ] Khi có phản hồi → dán nguyên văn vào `docs/records/PENDING_REQUESTS.md`,
      Claude sẽ đánh giá điều kiện cấp phép + viết script tích hợp nếu phù hợp
- [ ] Nếu KHÔNG nhận được phản hồi sau 2-4 tuần hoặc bị từ chối → dùng
      Azure/AWS Polly Neural TTS (xem bảng NGUỒN THAY THẾ) cho bản chính thức

---

*AUDIO_LICENSE_REQUEST_TEMPLATE.md | DS-VN-COM-021 | MediVoice VN*
