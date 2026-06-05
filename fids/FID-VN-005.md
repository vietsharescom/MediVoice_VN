# FID-VN-005 — VN-NER-002: L1c word-to-number + L6 lam_sang dùng VN NER
# Feature Intent Document | ISO_VN v1.0
# Status: DRAFT → AWAITING APPROVAL

| Field | Value |
|---|---|
| FID ID | FID-VN-005 |
| Layer | L1c (l1c_ner.py) + L6 (l6_agent.py, l6_mau15_generator.py) |
| LOC estimate | ~140 LOC |
| Risk level | MEDIUM (L6 thay đổi — additive, không xoá Canada path) |
| Builds on | FID-VN-004 (VN-ROUTER-001 DONE) |
| Created | 2026-06-07 |
| Approved by | Andy Phan |
| Approved date | 2026-06-07 |
| Implemented | 2026-06-07 — 272/272 PASS · bandit 0 HIGH/MEDIUM |

---

## WHY (Tại sao cần feature này?)

**FID-VN-004** đã implement L6 branch `lam_sang → Mẫu 15/BV-01` nhưng dùng Canada NER
(`SOAPGenerator.extract_entities()`) làm bridge tạm thời. Canada NER nhận EN text
(sau MarianMT). VN pipeline không chạy MarianMT cho `lam_sang` → Canada NER nhận VI text
→ regex EN không match → entities rỗng.

**Root cause cụ thể:**
1. PhoWhisper output: `"huyết áp một trăm ba mươi trên chín mươi"`
2. `l1c_ner.py` regex: `(\d{2,3})/(\d{2,3})` — chỉ nhận số, không nhận chữ
3. `bench_ceer.py` test: 0% vital coverage trên mọi audio thực tế

**Design §15 (DESIGN_REPORT_v1.1_20260606.md):**
- `[L1c]` extract từ transcript **tiếng Việt**, Phase 0: rule-based regex
- `[L6] lam_sang`: NER entities → map trực tiếp → BenhAnNgoaiTru (không qua SOAP)

→ VN NER (`l1c_ner`) phải xử lý được VI word-form numbers từ PhoWhisper.
→ L6 `lam_sang` phải dùng `l1c_ner` output (`MedicalEntities`), không phải Canada NEREntity.

**Canada pipeline không thay đổi:**
`VI text → MarianMT (EN) → Canada NER → SOAP` — path này giữ nguyên cho `cdha`/`nha_khoa`.

---

## WHAT (Feature làm gì?)

### File 1: `src/core/l1c_ner.py` — Thêm `_normalize_vn_numbers()`

Preprocess transcript trước khi chạy regex:

```
"một trăm ba mươi trên chín mươi"    → "130/90"
"một trăm ba mươi lăm trên tám lăm"  → "135/85"
"tám mươi"                            → "80"
"bảy mươi lăm"                       → "75"
"bảy mươi hai"                        → "72"
"hai mươi hai"                        → "22"
"ba mươi tám phẩy năm"               → "38.5"
"ba mươi tám rưỡi"                   → "38.5"
"năm trăm"                            → "500"
"một tuần"                            → "1 tuần"
"ba ngày"                             → "3 ngày"
"hai viên"                            → "2 viên"
```

Logic:
1. Build `_vn_to_int(text)` — parse VI word sequence → integer (0–999)
2. BP pattern: `([num_words]) trên ([num_words])` → `"N/M"` (trước khi general pass)
3. General pass: tìm VI number sequences → thay bằng digits

### File 2: `src/pipeline/p2_decision/l6_mau15_generator.py` — Thêm `generate_mau15_from_vn_ner()`

New function nhận `MedicalEntities` (VN dataclass) thay vì Canada NEREntity list:

```python
def generate_mau15_from_vn_ner(ents: MedicalEntities, payload: dict) -> dict:
    """VN NER MedicalEntities → form_data → generate_benh_an() → BenhAnNgoaiTru dict."""
    form_data = {
        "ly_do":        ents.ly_do,
        "trieu_chung":  ents.trieu_chung,
        "sinh_hieu": {
            "huyet_ap_tam_thu":    ents.huyet_ap_tam_thu,
            "huyet_ap_tam_truong": ents.huyet_ap_tam_truong,
            "nhiet_do":  ents.nhiet_do,
            "mach":      ents.mach,
            "nhip_tho":  ents.nhip_tho,
            "can_nang":  ents.can_nang,
            "spo2":      ents.spo2,
        },
        "chan_doan":  ents.chan_doan,
        "don_thuoc":  ents.don_thuoc,      # [{inn, ham_luong, so_lan_ngay, so_ngay, duong_dung}]
        "tai_kham":  ents.tai_kham,
        "chi_dinh":  ents.chi_dinh,
        "tien_su":   "",
        "icd_code":  payload.get("icd_code", ""),
        "icd_display": payload.get("icd_display", ""),
    }
    # ... rồi gọi generate_benh_an() như generate_mau15() hiện tại
```

Existing `generate_mau15(entities, payload)` — giữ nguyên (cho cdha/nha_khoa nếu cần).

### File 3: `src/pipeline/p2_decision/l6_agent.py` — Update lam_sang path

```python
# Hiện tại (Canada NER — interim từ FID-VN-004):
entities = _generator.extract_entities(text, vi_text=vi_text)
...
if vn_route == "lam_sang":
    benh_an_dict = generate_mau15(entities, payload)

# Sau fix (VN NER — đúng design §15):
if vn_route == "lam_sang":
    from src.core import l1c_ner
    vi_transcript = payload.get("original_text") or text
    vn_ents = l1c_ner.extract_entities(vi_transcript, drug_cands)
    from src.pipeline.p2_decision.l6_mau15_generator import generate_mau15_from_vn_ner
    benh_an_dict = generate_mau15_from_vn_ner(vn_ents, payload)
```

`drug_cands` đã có trong payload từ L1b (hoặc re-extract từ `l1b_drug_correct`).

---

## ACCEPTANCE CRITERIA

- [x] `"huyết áp một trăm ba mươi trên chín mươi"` → `sinh_hieu.huyet_ap_tam_thu = 130`
- [x] `"mạch tám mươi"` → `sinh_hieu.mach = 80.0`
- [x] `"sốt ba mươi tám phẩy năm"` → `sinh_hieu.nhiet_do = 38.5`
- [x] `"sốt ba mươi tám rưỡi"` → `sinh_hieu.nhiet_do = 38.5`
- [x] `"tái khám sau một tuần"` → `tai_kham = "Sau 1 tuần"`
- [x] `"tái khám sau ba ngày"` → `tai_kham = "Sau 3 ngày"`
- [x] `"kê amoxicillin năm trăm miligam ngày hai viên"` → `don_thuoc[0].inn = "Amoxicillin"`
- [x] `bench_ceer.py --partial` trên `tc_001_noi_khoa.wav`: `vital=True`, `followup=True`
- [x] `bench_ceer.py --partial` trên `tc_002_ho_hap.wav`: `vital=True`, `followup=True`
- [x] Canada path (`cdha` route) không thay đổi — `soap_note` vẫn output đúng
- [x] 272/272 tests PASS (232 existing + 40 new VN number tests)
- [x] CHANGELOG entry

---

## RISKS

| Risk ID | Mô tả | Kiểm soát |
|---|---|---|
| R-F001 | Word normalization thay số trong tên thuốc ("năm" → "5") | Chạy normalization TRƯỚC L1b drug correction, chỉ normalize trong context của vital/unit patterns |
| R-F002 | `_vn_to_int()` parse sai khi text không phải số | Return None → không replace, text giữ nguyên |
| R-F003 | lam_sang path dùng VN NER miss entities mà Canada NER bắt được | Acceptable Phase 0 — VN NER sẽ improve (Phase 1: PhoBERT+CRF) |
| R-F004 | drug_cands không có trong payload khi l6_agent gọi l1c_ner | Re-extract từ `l1b_drug_correct.extract_drug_candidates(vi_transcript)` |

---

## TESTS REQUIRED

- [ ] `tests/unit/test_l1c_vn_numbers.py` — unit tests cho `_normalize_vn_numbers()` và `_vn_to_int()`
- [ ] `tests/unit/test_l6_vn_ner_mapping.py` — test `generate_mau15_from_vn_ner()` mapping
- [ ] Regression: 232/232 existing tests PASS
- [ ] CEER: `bench_ceer.py --partial` → coverage tăng (drug ≥ 2/3, vital ≥ 2/3, followup ≥ 1/3)

---

## COMMIT FORMAT

```
feat(L1c+L6): VN-NER-002 — VN word-to-number + L6 lam_sang dùng VN NER [FID-VN-005]
```

---

*FID-VN-005 | VN-NER-002 | ISO_VN v1.0 | MediVoice VN | 2026-06-07*
