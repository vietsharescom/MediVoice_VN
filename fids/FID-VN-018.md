# FID-VN-018 — DVP setup: chuyên khoa trước + bài test Lab theo vùng miền (double-check)
# MediVoice VN | Feature Intent Document
# Status: IMPLEMENTED — v0.11.9
# Author: Claude | Created: 2026-06-11

| Field | Value |
|---|---|
| FID ID | FID-VN-018 |
| Layer | Ngoài L0-L10 (DVP registration + Calibration Lab — UI/research, không động pipeline FROZEN) |
| LOC estimate | ~160 LOC (backend ~70, frontend ~70, data/passages ~20) |
| Risk level | MEDIUM (đụng UI flow Calibration Lab — tương tự FID-VN-014/015) |
| Created | 2026-06-11 |
| Approved by | Andy |
| Approved date | 2026-06-11 |
| Refs | CT-043 (`docs/records/BACKLOG.md`), CT-038 (`fids/FID-VN-014.md` v2 region-manual fix) |

---

## WHY

Andy feedback session 2026-06-11, ý #3 (`docs/records/BACKLOG.md` CT-043):

> "ngay từ đầu phải setup thông tin bác sĩ chuyên ngành gì trước thì mới vào
> setup giọng ngôn ngữ để narrow down xuống. hơn nữa cũng double check 1 lần
> nữa về ngôn ngữ. ví dụ personality ghi là giọng trung thì khi vào test check
> đúng giọng trung. và trong giọng trung thì sẽ bài test sẽ viết theo phong
> cách giọng của người trung, tương tự người bắc thì tông giọng văn hoá test
> cũng bắc"

2 ý cụ thể:

1. **Chuyên khoa TRƯỚC, voice setup SAU** — hiện `dvp-form` (đăng ký DVP) có
   field "Vùng miền" (`dvp-region`) đặt TRƯỚC "Chuyên khoa chính"
   (`dvp-primary-specialty`) trong layout (`src/api/static/index.html:359-371`).
   Andy muốn đảo thứ tự + giải thích rõ: chọn chuyên khoa trước để các bài
   test sau (Calibration Lab Phần 3 — wordlist thuốc theo specialty, đã có)
   phù hợp ngay từ đầu.

2. **Double-check vùng miền qua nội dung bài test** — hiện
   `READING_PASSAGE_VI` (Phần 2, `src/core/calibration_metrics.py:15`) và câu
   mẫu Phần 1 (`lab-region-sentence`, hardcode trong HTML — câu giọng Trung
   "Bác sĩ ơi, mô răng rứa...") là **CỐ ĐỊNH 1 bộ cho TẤT CẢ BS**, không phụ
   thuộc `profile.region` đã khai khi đăng ký. Andy muốn: nếu BS khai
   `region="central"`, bài đọc Phần 1+2 phải dùng từ ngữ/phong cách giọng
   Trung (tương tự cho Bắc/Nam) — vừa cho BS đọc tự nhiên hơn (từ ngữ quen
   thuộc), vừa **double-check** `profile.region` tự khai có khớp với
   `detect_region(transcript)` từ giọng đọc thật hay không (liên quan CT-038
   — region-manual override đã có sẵn để BS tự sửa nếu auto-detect sai).

## WHAT

### 1. Frontend — reorder DVP form (CT-043 ý 1)

`src/api/static/index.html` (`#dvp-form`, dòng ~348-389):

- Đổi thứ tự field: **Chuyên khoa chính/phụ** lên TRƯỚC, **Vùng miền** +
  English level + Speaking speed xuống SAU.
- Thêm 1 dòng hint nhỏ phía trên: "Chọn chuyên khoa trước — các bài luyện
  giọng/đọc thuốc bên dưới sẽ tự điều chỉnh theo chuyên khoa của bạn."
- KHÔNG đổi field names/IDs/`DVP.save()` payload — chỉ đổi thứ tự hiển thị
  (HTML reorder + hint text, ~10-15 LOC).

### 2. Data — passages theo vùng miền (CT-043 ý 2)

`src/core/calibration_metrics.py`:

- Đổi `READING_PASSAGE_VI` (hằng số đơn) thành
  `READING_PASSAGES_BY_REGION: dict[str, str]` với 3 key `northern` /
  `central` / `southern` — nội dung tương đương (~90 từ, ngữ cảnh khám bệnh),
  nhưng dùng từ vựng đặc trưng vùng miền (tái sử dụng `_CENTRAL_MARKERS`/
  `_SOUTHERN_MARKERS` từ `src/core/dialect_norm.py` làm "checklist" để đảm
  bảo passage central/southern thực sự chứa marker tương ứng — phục vụ double
  -check ở bước 3).
  - `northern`: giữ nguyên `READING_PASSAGE_VI` hiện tại (chuẩn, trung tính
    Bắc).
  - `central`: thay 1 số từ bằng "mô/răng/rứa/ni/hè/tê/nớ/mần/mô rứa..."
  - `southern`: thay bằng "hổng/dzô/ổng/bả/hen/nghen/nha/nè/bịnh/ói..."
  - Giữ `READING_PASSAGE_VI = READING_PASSAGES_BY_REGION["northern"]` (alias,
    backward-compat cho test cũ).
- Tương tự, thêm `REGION_TEST_SENTENCES: dict[str, str]` cho Phần 1 (câu
  ngắn ~10-15s) — 3 biến thể Bắc/Trung/Nam (câu hiện tại "Bác sĩ ơi, mô răng
  rứa..." giữ làm `central`).
- Hàm helper `get_passage_for_region(region: str) -> str` và
  `get_region_sentence(region: str) -> str` — fallback `"northern"` nếu
  region không hợp lệ/`None`.

### 3. Backend — API trả passage/sentence theo profile.region

`src/api/main.py`:

- `GET /api/calibration/passage-text?cchn=...` — load `profile.region`
  (mặc định `"northern"` nếu chưa có), trả `get_passage_for_region(region)`
  thay vì hằng số cố định. `cchn` optional — nếu thiếu/profile not found,
  fallback `"northern"` (giữ tương thích test cũ
  `test_pronunciation_reference_fallback_when_no_cache`-style).
- **Endpoint mới** `GET /api/calibration/region-sentence?cchn=...` — trả
  `get_region_sentence(profile.region)` cho Phần 1 (hiện đang hardcode trong
  HTML).
- `calibration_region()` (Phần 1, đã có) — sau `detect_region(transcript)`,
  thêm field response `region_match: bool` = `(detected_region ==
  profile.region)`. Nếu `False` → message gợi ý BS xem lại lựa chọn vùng
  miền (UI Phần 1 đã có dropdown sửa tay từ CT-038, tái sử dụng — không thêm
  UI mới).

### 4. Frontend — Calibration Lab Step 1/2 load theo region

`src/api/static/index.html`:

- `lab-region-sentence` — load động qua `GET
  /api/calibration/region-sentence?cchn=...` khi mở Lab (thay vì hardcode).
- `lab-passage-text` — `GET /api/calibration/passage-text?cchn=...` (đã có
  sẵn lời gọi, chỉ thêm `?cchn=`).
- Sau Phần 1, nếu response có `region_match: false` → hiện thêm dòng:
  "⚠️ Giọng đọc có vẻ khác với vùng miền đã khai (X). Vui lòng chọn lại nếu
  cần:" phía trên dropdown sửa tay (CT-038, đã có).

## ACCEPTANCE CRITERIA

- [x] Tests 100% PASS
- [x] `dvp-form` hiển thị Chuyên khoa chính/phụ TRƯỚC Vùng miền (kiểm tra DOM
      order trong `index.html`)
- [x] `get_passage_for_region("central")` chứa ít nhất 1 marker trong
      `_CENTRAL_MARKERS`; tương tự `southern`/`_SOUTHERN_MARKERS`
- [x] `READING_PASSAGE_VI` (alias) vẫn === `READING_PASSAGES_BY_REGION["northern"]`
      — test cũ FID-VN-014 không vỡ
- [x] `GET /api/calibration/passage-text?cchn=X` trả passage theo
      `profile.region`; thiếu `cchn` → fallback northern
- [x] `GET /api/calibration/region-sentence?cchn=X` trả sentence theo
      `profile.region`
- [x] `calibration_region()` trả thêm `region_match: bool`
- [x] CHANGELOG entry + FID status → IMPLEMENTED

## RISKS

| Risk ID | Mô tả | Kiểm soát |
|---|---|---|
| R-018-1 | Passage central/southern do Claude viết — có thể không tự nhiên/đúng văn phong thật của vùng miền đó (Claude không phải người bản xứ Trung/Nam) | Andy (hoặc BS pilot SG — vùng Nam) review nội dung passage trước khi dùng thật; ghi rõ "draft, cần BS bản địa review" trong code comment |
| R-018-2 | `region_match: false` có thể gây hoang mang nếu `detect_region()` vẫn còn bug như CT-038 (lexical, dễ sai với giọng Huế) | Message chỉ là "gợi ý xem lại", không tự động ghi đè `profile.region`; BS toàn quyền giữ lựa chọn cũ qua dropdown CT-038 |
| R-018-3 | Đổi `READING_PASSAGE_VI` thành dict có thể vỡ test cũ tham chiếu trực tiếp hằng số | Giữ alias `READING_PASSAGE_VI = READING_PASSAGES_BY_REGION["northern"]`, chạy lại toàn bộ `tests/unit/test_calibration_lab.py` |

## TESTS REQUIRED

- [x] `tests/unit/test_calibration_lab.py` — `get_passage_for_region`,
      `get_region_sentence`, alias `READING_PASSAGE_VI`, marker checks
- [x] `tests/unit/test_dvp_wizard.py` hoặc test_calibration_lab — endpoint
      `passage-text?cchn=`, `region-sentence?cchn=`, `region_match` field
- [x] DOM order test (hoặc smoke test) cho `dvp-form` reorder

## COMMIT FORMAT

```
feat(research): FID-VN-018 — DVP chuyên khoa trước + Lab passages theo vùng miền
```

---

*FID-VN-018 | ISO_VN v1.0 | MediVoice VN*
