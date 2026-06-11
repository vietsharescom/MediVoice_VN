# FID-VN-016 — Pronunciation Lab: 2-dòng phiên âm (chuẩn thế giới + cá nhân hoá VN)
# MediVoice VN | Feature Intent Document
# Status: IMPLEMENTED ✅ — Approved by Andy "đồng ý" 2026-06-11
# Author: Claude | Created: 2026-06-11

| Field | Value |
|---|---|
| FID ID | FID-VN-016 |
| Layer | Ngoài L0-L10 (Pronunciation Recognition Lab — research/UI, không động pipeline FROZEN) |
| LOC estimate | ~140 LOC (backend ~60, frontend ~50, data ~30) |
| Risk level | LOW |
| Created | 2026-06-11 |
| Approved by | Andy ("đồng ý") |
| Approved date | 2026-06-11 |
| Refs | CT-039 (`docs/records/PENDING_REQUESTS.md`), FID-VN-015 §3.1-3.2 |

---

## WHY

CT-039 phát hiện: phiên âm "paraxi ta mol" hiện tại do Claude tự bịa (heuristic
`pronunciation_phonetic.py`), không có nguồn chính thống. Andy đề xuất hướng
mới — tách rõ 2 dòng hiển thị trong Wizard (Pronunciation Recognition Lab
Part 3):

- **Dòng 1 (trên)**: phiên âm CHUẨN chuyên ngành y dược thế giới — viết kiểu
  "dễ đọc" (vd "puh-RASS-uh-tuh-mol"), KHÔNG phải IPA academic. Nguồn: AMA/USP
  USAN Drug Name Pronunciation Guide (chuẩn quốc tế cho generic name).
- **Dòng 2 (dưới)**: phiên âm kiểu Việt — CÁ NHÂN HOÁ theo từng BS:
  - Ban đầu (chưa ghi âm/confirm lần nào): dùng heuristic Claude hiện có
    (vd "lô ra ta di nê" cho Loratadine) — fallback, không phải chuẩn.
  - Sau khi BS ghi âm + bấm "Xác nhận": dòng 2 đổi thành CHÍNH transcript ASR
    nghe được từ giọng đọc của BS đó (cách BS quen đọc) — ghi đè, chỉ giữ
    **1 bản mới nhất** (không tích luỹ nhiều version).
- **"Nghe mẫu" (audio)**: phát theo phiên âm chuẩn thế giới (dòng 1), không
  phải phiên âm Việt heuristic — dùng gTTS tiếng Anh đọc tên INN gốc.
- **Transcript lộn xộn (đọc lặp nhiều lần/nhiều biến thể)**: KHÔNG đề xuất
  confirm alias từ chuỗi dài lộn xộn — báo BS đọc lại, chỉ 1 lần, chọn cách
  đọc thoải mái nhất.

## WHAT

### 1. Data — `data/reference/drug_db.json`
- Thêm field optional `pronunciation_en` (string, kiểu USAN respelling, vd
  `"par-a-SEE-ta-mol"`) cho **pilot subset** — ưu tiên các thuốc xuất hiện
  trong `pronunciation-wordlist` của các specialty đang dùng pilot (noi_khoa,
  tim_mach, ...) — ước tính ~20-30 thuốc trước, KHÔNG làm hết 110 thuốc cùng
  lúc (tránh lặp lỗi "Claude bịa hàng loạt" — mỗi entry Claude tra cứu/đối
  chiếu kiến thức y khoa tổng quát, ghi `"pronunciation_en_source": "USAN-style"`
  để minh bạch nguồn). Thuốc chưa có `pronunciation_en` → ẩn dòng 1, chỉ hiện
  dòng 2 (Phase B mở rộng dần).

### 2. Backend
- `src/core/pronunciation_phonetic.py`:
  - `get_pronunciation_en(inn, drug_entry) -> str | None` — đọc field
    `pronunciation_en` từ drug_entry, trả `None` nếu chưa có.
  - `is_garbled_transcript(transcript: str, expected_inn: str) -> bool` —
    heuristic phát hiện transcript đọc lặp nhiều lần (vd cùng 1 cụm âm tiết
    lặp lại ≥2 lần, hoặc số từ > 3x số âm tiết kỳ vọng).
- `src/core/l7_storage.py`:
  - `get_latest_confirmed_alias(cchn, inn, db_path=None) -> str | None` —
    lấy `alias_text` mới nhất (theo `created_at`) đã confirm cho 1 INN.
  - `add_confirmed_alias()` — giữ nguyên (vẫn insert mới mỗi lần confirm,
    phục vụ audit/RTM); chỉ THAY ĐỔI cách hiển thị (lấy bản mới nhất).
- `src/api/main.py`:
  - `GET /api/pronunciation-reference/{inn}`: response thêm
    `pronunciation_en` (None nếu chưa có data), `vn_phonetic_user` (kết quả
    `get_latest_confirmed_alias`, None nếu chưa confirm lần nào),
    `vn_phonetic_default` (heuristic hiện có). `audio_url` đổi sang gen từ
    gTTS **tiếng Anh** đọc INN gốc (không phải phiên âm Việt).
  - `pronunciation-enroll`: thêm check `is_garbled_transcript()` — nếu True,
    trả `retry_needed: true` + message "Trợ lý nghe không rõ, vui lòng đọc
    lại 1 lần duy nhất theo cách thoải mái nhất", KHÔNG đề xuất alias.
- `scripts/gen_pronunciation_audio.py`: đổi gTTS sang `lang='en'`, input text
  = INN gốc (vd "Paracetamol") thay vì phiên âm Việt.

### 3. Frontend (Wizard modal)
- Hiển thị 2 dòng: dòng 1 = `pronunciation_en` (ẩn nếu None), dòng 2 =
  `vn_phonetic_user ?? vn_phonetic_default`.
- Sau khi confirm alias thành công → reload `_loadReference()` để dòng 2 cập
  nhật ngay theo bản mới nhất.
- Nếu `retry_needed=true` → hiện message yêu cầu đọc lại, ẩn nút confirm.

## ACCEPTANCE CRITERIA

- [x] Tests 100% PASS (unit mới cho `get_pronunciation_en`,
      `is_garbled_transcript`, `get_latest_confirmed_alias`, endpoint mở rộng)
      — 901/901 PASS
- [x] `pronunciation-reference` trả đủ 4 field: `pronunciation_en`,
      `vn_phonetic_default`, `vn_phonetic_user`, `audio_url`
- [x] Audio "Nghe mẫu" phát tiếng Anh chuẩn (gTTS lang='en'), không phải VN
      heuristic
- [x] Transcript lộn xộn (đọc lặp ≥2 lần) → `retry_needed=true`, không đề
      xuất alias
- [x] Sau confirm → dòng 2 hiển thị bản mới nhất của BS, không tích luỹ
- [x] CHANGELOG entry + FID status → IMPLEMENTED

## RISKS

| Risk ID | Mô tả | Kiểm soát |
|---|---|---|
| R-016-1 | `pronunciation_en` cho pilot subset vẫn do Claude tra cứu kiến thức tổng quát (không phải scrape trực tiếp AMA USAN) — có thể sai lệch nhỏ | Ghi rõ `pronunciation_en_source: "USAN-style (manual, chưa verify từng entry)"`, Andy/BS review khi dùng thực tế, sửa dần |
| R-016-2 | gTTS tiếng Anh đọc INN có thể phát âm khác US/UK hoặc sai với từ y khoa hiếm | Vẫn ghi rõ "tham khảo" trên UI, không phải nguồn duy nhất |
| R-016-3 | `is_garbled_transcript()` heuristic có thể false-positive với tên thuốc đa âm tiết tự nhiên dài | Threshold rộng (>3x âm tiết kỳ vọng), test với các tên dài thật (Loratadine, Cetirizine...) |

## TESTS REQUIRED

- [x] `tests/unit/test_pronunciation_phonetic.py` — `get_pronunciation_en`,
      `is_garbled_transcript`
- [x] `tests/unit/test_dvp_wizard.py` — endpoint mở rộng + retry_needed +
      `vn_phonetic_user` sau confirm + `get_latest_confirmed_alias`

## COMMIT FORMAT

```
feat(research): FID-VN-016 — 2-dòng phiên âm chuẩn thế giới + cá nhân hoá VN
```

---

*FID-VN-016 | ISO_VN v1.0 | MediVoice VN*
