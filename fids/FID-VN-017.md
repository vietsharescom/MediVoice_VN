# FID-VN-017 — Pronunciation Lab: mở rộng pronunciation_en (tim_mạch) + gợi ý trọng âm/phát âm EN
# MediVoice VN | Feature Intent Document
# Status: IMPLEMENTED — v0.11.8
# Author: Claude | Created: 2026-06-11

| Field | Value |
|---|---|
| FID ID | FID-VN-017 |
| Layer | Ngoài L0-L10 (Pronunciation Recognition Lab — research/UI, không động pipeline FROZEN) |
| LOC estimate | ~110 LOC (data ~15, backend ~60, frontend ~35) |
| Risk level | LOW |
| Created | 2026-06-11 |
| Approved by | Andy |
| Approved date | 2026-06-11 |
| Refs | CT-040, CT-041 (`docs/records/BACKLOG.md`), FID-VN-016 (`fids/FID-VN-016.md`) |

---

## WHY

Sau khi test FID-VN-016, Andy phản hồi 4 ý (log tại `docs/records/BACKLOG.md`
CT-040..043). FID này xử lý 2 ý không đụng pipeline FROZEN:

- **CT-040**: `pronunciation_en` (dòng 1 — chuẩn USAN-style) hiện chỉ có cho
  25 thuốc pilot `noi_khoa`. Andy nhấn mạnh đây là "mẫu định vị" quan trọng
  cho user — cần mở rộng dần sang specialty pilot tiếp theo (`tim_mach`)
  trước khi làm hết 155 thuốc.
- **CT-041**: dòng 2 (`vn_phonetic_default`, heuristic VN) hiện là respelling
  tự do, không định hướng người đọc về phát âm tiếng Anh chuẩn. Andy muốn
  dòng 2 **gợi ý trọng âm** (stress) — đặc điểm khác biệt lớn nhất giữa tiếng
  Việt (đơn âm tiết, không trọng âm) và tiếng Anh (trọng âm quyết định nghe
  đúng/sai) — và có **ghi chú ngắn về phát âm phụ âm bật hơi p/t/k** (Andy
  thực nghiệm: đổi "b"→"p" bật hơi khi đọc tên thuốc tăng độ nhận dạng cá
  nhân từ ~20% lên ~50%).

  **Cập nhật (CONS-20260611-001, `docs/records/consultations/CONS-20260611-001.md`)**:
  CT-039 kết luận "không có từ điển" chỉ đúng cho chiều Anh→Việt; **chiều
  tiếng Anh CÓ nguồn miễn phí, công khai — Merriam-Webster (Medical)
  Dictionary** (vd "paracetamol" → `ˌpar-ə-ˈsēt-ə-ˌmȯl`, "cetirizine" →
  `se-ˈtir-ə-ˌzēn`). Đối chiếu 2 ví dụ Andy cung cấp, format
  `pronunciation_en` hiện tại (CAPS = trọng âm chính, hyphen tách âm tiết) đã
  KHỚP vị trí trọng âm với MW — chỉ cần đổi `pronunciation_en_source` để cite
  rõ nguồn này thay vì "USAN-style (manual, chưa verify)". WebFetch
  `merriam-webster.com` bị chặn (403) trong môi trường này → 9 entries mới
  (CT-040) Claude điền theo kiến thức chung (format khớp MW), đánh dấu
  "chưa verify trực tiếp" — Andy paste MW respelling khi rảnh để Claude đối
  chiếu/sửa (CT-044, follow-up).

  CT-042 (chuẩn hoá ngữ âm cho L1b drug-matching — b≈p, d≈t, g≈k, final-l)
  **KHÔNG nằm trong FID này** — đụng pipeline FROZEN, cần FID riêng
  (FID-VN-018) + A/B test trên audio pilot thật.

## WHAT

### 1. Data — `data/reference/drug_db_v200.json` (CT-040)

Thêm field `pronunciation_en` + `pronunciation_en_source` cho 9 thuốc còn
thiếu trong top-20 wordlist `tim_mach`
(`get_drugs_by_specialty(db, "tim_mach", n=20)`):

```
Warfarin, Clopidogrel, Telmisartan, Olmesartan, Irbesartan,
Nifedipine, Lercanidipine, Metoprolol, Indapamide
```

`pronunciation_en_source` mới (thay "USAN-style (manual, chưa verify)"):
```
"Merriam-Webster-style (manual, dựa kiến thức chung — CHƯA verify trực tiếp
với merriam-webster.com do WebFetch bị chặn 403, xem CONS-20260611-001).
CAPS = trọng âm chính (tương đương dấu ˈ của MW)."
```

Sau FID này: top-20 wordlist của cả `noi_khoa` và `tim_mach` đều có
`pronunciation_en`. Phase 3 (specialty khác, hoặc phần còn lại của 155
thuốc) + CT-044 (verify lại 25+9 entries với MW thật khi Andy có thời gian
paste) để follow-up sau.

### 2. Backend — gợi ý trọng âm (CT-041a)

`src/core/pronunciation_phonetic.py`:

- Thêm `apply_stress_hint(vn_phonetic: str, pronunciation_en: str | None) -> str`:
  - Nếu `pronunciation_en` là `None`/rỗng → trả nguyên `vn_phonetic` (không đổi).
  - Tách `pronunciation_en` theo `-`, tìm segment có chữ HOA (vd `"SEE"` trong
    `"par-a-SEE-ta-mol"`) → `idx_en` (0-based), `total_en` = số segment.
  - Tách `vn_phonetic` theo khoảng trắng → `total_vn` âm tiết.
  - `idx_vn = round((idx_en / total_en) * total_vn)`, clamp `[0, total_vn-1]`.
  - Viết HOA âm tiết tại `idx_vn` trong `vn_phonetic`, trả chuỗi mới.
  - Heuristic tỉ lệ vị trí — không chính xác tuyệt đối, nhưng đủ để gợi ý
    "đọc nhấn vào đây" cho BS (chấp nhận sai số nhỏ, BS tự điều chỉnh qua
    confirm cá nhân hoá FID-VN-016 nếu cảm thấy không đúng).

- `get_reference_phonetic()` — khi có `pronunciation_en` (truyền thêm param
  `pronunciation_en: str | None = None`), áp `apply_stress_hint()` lên kết
  quả trước khi trả về.

`src/api/main.py`:

- `GET /api/pronunciation-reference/{inn}` — `vn_phonetic_default` áp
  `apply_stress_hint()` khi `pronunciation_en` có sẵn (chỉ default, KHÔNG áp
  lên `vn_phonetic_user` — bản BS tự đọc giữ nguyên, không can thiệp).

### 3. Frontend — ghi chú phát âm bật hơi (CT-041b)

`src/api/static/index.html` — Wizard Part 3:

- Thêm 1 dòng tip tĩnh (hiển thị 1 lần/thuốc, nhỏ, màu xám) khi
  `pronunciation_en` có sẵn VÀ INN có chứa âm tiết bắt đầu bằng "p"/"t"/"k"
  (không phải "ph"/"th"/"ch"/"kh"):
  > 💡 Tiếng Anh: chữ in hoa = trọng âm (đọc nhấn). "p/t/k" đọc bật hơi mạnh
  > hơn tiếng Việt (gần giống "ph/th/kh").
- Logic phát hiện: regex đơn giản trên `pronunciation_en` — nếu match
  `\b[ptk][^h]` ở đầu 1 segment → hiện tip. Không cần xử lý phức tạp/data
  mới — chỉ là 1 câu giải thích chung, hiện 1 lần.

## ACCEPTANCE CRITERIA

- [x] Tests 100% PASS (unit mới cho `apply_stress_hint`, data check 9 thuốc
      tim_mach có `pronunciation_en`)
- [x] `get_drugs_by_specialty(db, "tim_mach", n=20)` — tất cả 20 thuốc có
      `pronunciation_en` không None
- [x] `vn_phonetic_default` trả về có 1 âm tiết viết HOA (stress hint) khi
      `pronunciation_en` có sẵn; không đổi khi không có
- [x] `vn_phonetic_user` (sau confirm) KHÔNG bị áp stress hint — giữ nguyên
      transcript BS đọc
- [x] Tip "bật hơi/trọng âm" hiện đúng điều kiện (có pronunciation_en + chứa
      p/t/k đầu âm tiết không phải ph/th/kh)
- [x] CHANGELOG entry + FID status → IMPLEMENTED

## RISKS

| Risk ID | Mô tả | Kiểm soát |
|---|---|---|
| R-017-1 | `apply_stress_hint` heuristic tỉ lệ vị trí có thể nhấn sai âm tiết với tên thuốc rất ngắn (2 âm tiết) hoặc rất dài (≥6 âm tiết) | Test với cả 2 trường hợp (vd Metformin 3 âm tiết, Empagliflozin 5 âm tiết); BS tự điều chỉnh qua confirm cá nhân hoá nếu thấy lệch |
| R-017-2 | 9 `pronunciation_en` mới cho tim_mach vẫn do Claude tra cứu kiến thức tổng quát (không scrape AMA USAN trực tiếp) | Ghi `pronunciation_en_source` minh bạch như FID-VN-016, BS review khi dùng thực tế |
| R-017-3 | Tip phát âm bật hơi quá đơn giản, có thể chưa đúng 100% ngữ âm học (vd 1 số thuốc không có âm p/t/k đầu nhưng vẫn cần lưu ý) | Tip ghi rõ là gợi ý chung ("Tiếng Anh:..."), không tuyên bố là quy tắc tuyệt đối; CT-042 (FID-VN-018) sẽ nghiên cứu sâu hơn cho L1b matching |

## TESTS REQUIRED

- [x] `tests/unit/test_pronunciation_phonetic.py` — `apply_stress_hint`
      (có/không `pronunciation_en`, vị trí stress đúng cho vài ví dụ)
- [x] `tests/unit/test_dvp_wizard.py` — `pronunciation-reference` trả
      `vn_phonetic_default` có stress hint khi có `pronunciation_en`,
      `vn_phonetic_user` không bị ảnh hưởng
- [x] Data test — 9 thuốc tim_mach mới có `pronunciation_en` non-empty

## COMMIT FORMAT

```
feat(research): FID-VN-017 — mở rộng pronunciation_en (tim_mach) + gợi ý trọng âm/bật hơi
```

---

*FID-VN-017 | ISO_VN v1.0 | MediVoice VN*
