# FID-VN-021 — L1b Phoneme-Key Re-scoring cho Drug Matching (CT-060d)
# Feature Intent Document | ISO_VN v1.0
# Status:approve

| Field | Value |
|---|---|
| FID ID | FID-VN-021 |
| Layer | L1b (drug name correction) |
| LOC estimate | ~120-150 LOC (`src/core/vn_phoneme.py` mới + wiring `_fuzzy_match`) + ~80 LOC tests |
| Risk level | MEDIUM — touches FROZEN L1b fuzzy-match scoring (ABSOLUTE RULE #1) |
| Created | 2026-06-13 |
| Approved by | (chờ Andy) |
| Approved date | — |

---

## WHY (Tại sao cần feature này?)

Phát sinh từ research session 2026-06-13 (CT-060, `docs/records/BACKLOG.md`): đọc
`Andy/ViSpeechFormer 2602.10003v1.pdf` + `Andy/2605.27874v1.pdf` ("Syllabic-Structure
Decoder for ASR in Vietnamese", UIT/VNU-HCM 5/2026) — cả hai cùng kết luận: decode/
so khớp ở **mức phoneme (initial/rhyme/tone)** thay vì chữ viết cho **OOV accuracy
~2x** so với baseline character/word-level (27.27% vs ~3-14% trên ViVOS/LSVSC).

Đây đánh trực tiếp vào vấn đề lớn nhất hiện tại: **Drug Recall chỉ 55.6%** (BENCH-002b,
57 clip thật) — tên thuốc tiếng Anh là OOV với PhoWhisper, ASR garble theo nhiều cách
khác nhau (b/p, tone, vowel...). FID-VN-019 (CT-042) đã enumerate 4 nhóm biến thể
text-level (1913 alias). FID-VN-019 v3 explicitly nói enumerate sẽ "nổ theo cấp số
nhân" — CT-053 (Vietnamese Medical Phonetic Encoder) đề xuất hướng encoder tổng quát
nhưng yêu cầu audio pilot để thiết kế đầy đủ.

FID này làm một bước **NHỎ HƠN, AN TOÀN HƠN CT-053**: không thay alias_map (vẫn giữ
1913 alias hiện có), chỉ thêm **1 tầng re-scoring phụ** trong `_fuzzy_match()` — so
khớp theo "phoneme key" (onset+rhyme, bỏ tone) bên cạnh RapidFuzz text score hiện có.
Tone trong tiếng Việt là phần ASR/dialect garble nhiều nhất (CT-038, vùng miền) →
bỏ tone khi so khớp giúp bắt thêm các trường hợp lệch dấu mà text-distance bỏ sót,
mà KHÔNG cần audio mới, KHÔNG cần GPU, test được ngay với data offline hiện có
(BENCH-002b 57 clip).

CT-060c (dialect detection rule-based) và CT-060e (F0/formant acoustic dialect ID,
`Andy/dangqa1951,+7905_Hung_Loan.pdf`) bị DEFER khỏi FID này — cả hai cần audio thật
để validate (CT-038 root cause vẫn chưa confirm), giữ nguyên trong CT-053/Phase 2.

---

## WHAT (Feature làm gì? Input/Output?)

### 1. Module mới `src/core/vn_phoneme.py`

```python
def decompose_syllable(syllable: str) -> tuple[str, str, str]:
    """Tách 1 âm tiết VN (đã normalize, có dấu) -> (onset, rhyme_no_tone, tone)."""

def phoneme_key(text: str) -> str:
    """Chuỗi text -> 'phoneme skeleton': mỗi âm tiết = onset+rhyme (bỏ tone),
    nối bằng dấu cách. Dùng để so khớp bỏ qua sự khác biệt thanh điệu."""
```

- Quy tắc tách âm tiết: cấu trúc âm tiết VN = (phụ âm đầu)(âm đệm)(âm chính)(âm
  cuối) + thanh điệu (FID-VN-019 đã có rule onset/coda tương tự — module này tổng
  quát hóa thành decompose đầy đủ, dùng bảng map ký tự có dấu -> (nguyên âm gốc,
  thanh điệu) — vd "ó"->("o","sắc"), "ò"->("o","huyền"), v.v. cho 12 nguyên âm x
  5 dấu = ~60 entries, viết tay từ bảng chữ cái VN, không cần đọc thêm paper).
- Input: 1 string (token hoặc cụm từ alias, đã qua `_normalize()` HOẶC giữ dấu —
  quyết định trong implementation: cần giữ dấu để detect tone, decompose dùng bản
  CÓ dấu, output `phoneme_key` đã bỏ tone + bỏ dấu).
- Output: string, dùng làm key phụ để so khớp (không phải alias_map mới).

### 2. Wiring vào `src/core/l1b_drug_correct.py::_fuzzy_match()`

- Hiện tại: `fuzz.token_sort_ratio(token, alias)` → 1 score.
- Thêm: `fuzz.ratio(phoneme_key(token), phoneme_key(alias))` → score phụ.
- Combine: `final_score = max(text_score, phoneme_score * PHONEME_WEIGHT)` với
  `PHONEME_WEIGHT` (vd 0.9) để phoneme-match không lấn át text-match chính xác,
  chỉ "cứu" các trường hợp text-score thấp (dưới threshold hiện tại) nhưng
  phoneme-skeleton khớp cao.
- Threshold match (`MATCH_THRESHOLD` hiện có trong l1b) GIỮ NGUYÊN — chỉ thay
  cách tính score đầu vào.

### Side effects
- Không đổi `alias_map` (1913 entries, CT-042) — không đổi `_build_alias_map()`.
- Không đổi schema `MedicalEntities`/`DrugMatch`.
- Có thể đổi KẾT QUẢ match cho 1 số token biên (score quanh threshold) —
  RỦI RO chính của FID này, kiểm soát bằng A/B benchmark (xem RISKS).

---

## ACCEPTANCE CRITERIA (Khi nào gọi là DONE?)

- [ ] Tests 100% PASS (984/984 + tests mới cho `vn_phoneme.py`)
- [ ] A/B benchmark trên branch `experiment/*` (giống CT-054 precedent):
      `tools/bench_002b.py` so sánh trước/sau trên 57 clip BENCH-002b
      - Drug Recall: không giảm, mục tiêu tăng từ 55.6%
      - Drug Precision: không giảm dưới 70% (hiện 71.4%)
- [ ] Chỉ merge vào `master` nếu Recall tăng HOẶC giữ nguyên VÀ Precision không
      giảm >2pp. Nếu cả 2 không cải thiện → giữ làm "research note", không merge
      (giống quyết định CT-028 với Groq hybrid).
- [ ] CHANGELOG entry
- [ ] Không vi phạm frozen layers (L0-L10 schema không đổi, chỉ scoring nội bộ L1b)

## RISKS

| Risk ID | Mô tả | Kiểm soát |
|---|---|---|
| R-PHON-10 | Phoneme-key quá "lỏng" (bỏ tone) → tăng false positive (vd "kha" ~ "khá" ~ "khà" đều cùng key, có thể match nhầm thuốc khác âm tiết gần) | `PHONEME_WEIGHT < 1.0` để phoneme-score không vượt text-score thật; A/B benchmark trước khi merge; giữ `_PHON_BLACKLIST` hiện có |
| R-PHON-11 | `decompose_syllable()` sai với các âm tiết có "qu", "gi", "ngh" (đa kí tự đầu) | Viết test cases riêng cho các onset phức (qu/gi/ngh/nh/ng/tr/ch/kh/ph/th) trước khi tích hợp |
| R-PHON-12 | Performance: thêm 1 lần tính `fuzz.ratio` cho mỗi candidate trong alias_map (1913 entries) | Benchmark thời gian transcribe trước/sau; nếu chậm đáng kể, cache `phoneme_key` cho alias_map (tính 1 lần, không phải mỗi request) |

## TESTS REQUIRED

- [ ] `tests/unit/test_vn_phoneme.py` — decompose_syllable cho ~20 âm tiết mẫu
      (đơn giản + onset phức + đủ 6 thanh điệu), phoneme_key cho cụm nhiều âm tiết
- [ ] `tests/unit/test_l1b_drug_correct_v2.py` — thêm case: token lệch tone khớp
      đúng INN qua phoneme re-scoring (vd alias có dấu sắc, ASR ra không dấu/dấu khác)
- [ ] Pipeline integrity test vẫn PASS (`tests/integration/`)
- [ ] A/B benchmark output lưu `data/eval/bench_002b_results_fid021.json` (không
      overwrite baseline — theo precedent CT-054)

## COMMIT FORMAT

```
feat(L1b): phoneme-key re-scoring cho drug matching [FID-VN-021]
```

---

*FID-VN-021 | ISO_VN v1.0 | MediVoice VN | 2026-06-13*
*Nguồn: CT-060/060d (docs/records/BACKLOG.md) — Andy/ViSpeechFormer 2602.10003v1.pdf,
Andy/2605.27874v1.pdf*
