# FID-VN-008 — DrugCorrectionEngine v2 (L1b upgrade)
# Feature Intent Document | ISO_VN v1.0
# Status: APPROVED — 2026-06-10 (Andy + ChatGPT + Copilot reviews incorporated)

| Field | Value |
|---|---|
| FID ID | FID-VN-008 |
| Layer | L1b |
| LOC estimate | ~200 LOC |
| Risk level | MEDIUM |
| Created | 2026-06-10 |
| Approved by | Andy Phan |
| Approved date | 2026-06-10 |

---

## WHY (Tại sao cần feature này?)

L1b hiện tại chỉ dùng **exact alias match** sau normalize — tức là phải có tên thuốc trong `brands[]` của `drug_db.json` mới nhận ra được. Ví dụ:

- BS nói "am lô đi pin" → MATCH ✅ (đã có trong brands)
- BS nói "am lô đi" → MISS ❌ (không có trong brands → PhoWhisper output này bị bỏ qua)
- BS nói "amlordipine" → MISS ❌ (typo không có exact match)

CONS-20260610-001 + CONS-20260610-002 (CLOSED) đã xác định:
1. `drug_db_v200.json` bây giờ có `phonetic_variants:{north, central, south}` cho 40+ drugs
2. RapidFuzz có thể handle fuzzy/phonetic match nhanh (Rust-based, ~3M matches/s)
3. Cần **Safety Rule Engine** — hard dose validation để tránh kê nhầm liều

Upgrade L1b từ 1 layer (exact) → 4 layers, dùng `drug_db_v200.json` làm nguồn.

---

## WHAT (Feature làm gì? Input/Output?)

**Input:** transcript thô từ L1a PhoWhisper (string)
**Output:** transcript đã chuẩn hóa drug names về INN (string)  
**Side effects:** `DrugMatch` objects với `confidence`, `match_layer`, `flagged_for_review`

### 4-Layer Matching Architecture (v2 — ChatGPT review incorporated)

```
NGUYÊN TẮC: Eliminate unsafe candidates FIRST, then choose best safe candidate
(không phải "find best match" — đây là medical system)

─────────────────────────────────────────────────────────────
PRE-FILTER (mới, chạy TRƯỚC Layer 2/3 khi có session_context)
─────────────────────────────────────────────────────────────
  Input: session_context["diagnosis"] + session_context["drug_class_context"]
  Logic: build alias_map_filtered chỉ gồm drugs có:
           compatible_diagnoses overlap diagnosis
           OR drug_class match drug_class_context
  Nếu không có session_context → dùng full alias_map (fallback safe)
  Impact: giảm ~70% search space → giảm false positive
  [Đề xuất ChatGPT: "medical constrained search space"]

─────────────────────────────────────────────────────────────
Layer 1 — Exact alias match (current behavior, giữ nguyên)
─────────────────────────────────────────────────────────────
  Dùng: alias_map từ brands[] + phonetic_variants[] của drug_db_v200.json
  Normalize: lowercase + strip diacritics
  Window: 1–4 words sliding
  → HIT: return INN, confidence=1.0, no flag

─────────────────────────────────────────────────────────────
Layer 2 — Fuzzy match (RapidFuzz) với Ambiguity Gate
─────────────────────────────────────────────────────────────
  Áp dụng chỉ khi Layer 1 MISS
  Search space: alias_map_filtered (từ PRE-FILTER) hoặc full
  Dùng: rapidfuzz.process.extract(limit=2)  ← top 2, không chỉ top 1
       scorer=rapidfuzz.fuzz.token_sort_ratio
       cutoff=82

  AMBIGUITY GATE (mới — ChatGPT R-008-01 fix):
    nếu top1_score - top2_score < 8:
      → FLAG_AMBIGUOUS, confidence=(top1/100)*0.7, flagged=True
      → KHÔNG auto-commit (BS phải chọn)

  Nếu không ambiguous:
    score ≥ 82: return INN, confidence=score/100, flagged=False
    70 ≤ score < 82: return INN, confidence=score/100, flagged=True, reason="LOW_CONFIDENCE"
    score < 70: MISS → Layer 3

─────────────────────────────────────────────────────────────
Layer 3 — Context-aware prefix match
─────────────────────────────────────────────────────────────
  Áp dụng chỉ khi Layer 2 MISS
  Search: trong alias_map_filtered, tìm INN/alias starts_with normalized token
  Yêu cầu: ít nhất 1 unique candidate (nếu 2+ ambiguous → FLAG_AMBIGUOUS)
  → HIT: return INN, confidence=0.6, flagged=True, reason="LOW_CONFIDENCE"

─────────────────────────────────────────────────────────────
Layer 4 — Safety Engine (chạy SAU L1/2/3 khi có match)
─────────────────────────────────────────────────────────────
  KHÔNG override match, KHÔNG auto-correct
  Chỉ thêm flag + severity lên DrugMatch hiện tại

  Safety checks (theo thứ tự severity):

  a. DOSE_OUT_OF_RANGE (severity=HIGH):
     IF dose_detected AND drug có dose_range (min>0):
       IF dose_detected < dose_range.min OR > dose_range.max:
         → flag=True, reason="DOSE_OUT_OF_RANGE", severity="HIGH"

  b. CLASS_MISMATCH (severity=MEDIUM):
     IF session_context có diagnosis AND drug có compatible_diagnoses:
       IF không overlap:
         → flag=True, reason="CLASS_MISMATCH", severity="MEDIUM"

  c. AMBIGUOUS (severity=HIGH):
     IF từ Layer 2 Ambiguity Gate → severity="HIGH"

  Severity → L4 Human Gate priority:
    HIGH   → BS phải review TRƯỚC khi approve record
    MEDIUM → hiển thị warning, BS có thể accept without extra click
    LOW    → log only

  [ChatGPT: severity scoring prevents L4 Human Gate overload]
```

### Data source upgrade

```python
# Trước: drug_db.json (exact only)
# Sau:   drug_db_v200.json (phonetic_variants + dose_range + drug_class)
# Backward compat: fallback to drug_db.json nếu v200 không tồn tại
```

### Config (Copilot: make cutoff configurable)

```python
DRUG_FUZZY_CUTOFF_STRICT = 82   # auto-accept nếu confidence ≥ 0.85 sau safety check
DRUG_FUZZY_CUTOFF_FLAG   = 70   # flag nếu 70 ≤ score < 82
# → tune theo pilot data thực tế, không hardcode trong logic
```

### session_context schema (Copilot: define precisely)

```python
# session_context được truyền từ L3 Router / L1c NER context
session_context = {
    "diagnosis": "tăng huyết áp",        # VN text từ NER
    "diagnosis_icd10": "I10",             # ICD-10-VN code (nếu có)
    "drug_class_context": ["CCB", "ARB"], # drug classes phù hợp với diagnosis
    "visit_stage": "prescription",         # intake | prescription | followup
    "current_drugs_this_session": [],      # INN drugs đã kê trong session này
    "allergy_flags": [],                   # INN drugs bị dị ứng (từ M1 patient record)
    "intent": "drug_prescription",         # dùng để weight context match
}
# Nếu session_context=None → disable PRE-FILTER + Layer 3 → chỉ L1+L2+L4 Safety
```

### New exported API

```python
# Giữ nguyên backward compat:
correct_drug_names(transcript: str) -> str          # unchanged signature
extract_drug_candidates(transcript: str) -> list[dict]  # unchanged signature

# Thêm mới:
correct_drug_names_v2(
    transcript: str,
    session_context: dict | None = None,
) -> tuple[str, list[DrugMatch]]
```

`DrugMatch` dataclass:
```python
@dataclass
class DrugMatch:
    inn: str
    original_text: str
    word_position: int
    confidence: float          # 0.0 – 1.0
    match_layer: int           # 1, 2, 3
    flagged_for_review: bool   # True nếu cần BS kiểm tra
    flag_reason: str           # "" | "LOW_CONFIDENCE" | "DOSE_OUT_OF_RANGE" | "CLASS_MISMATCH" | "AMBIGUOUS"
    severity: str              # "" | "LOW" | "MEDIUM" | "HIGH"
    fuzzy_score: float         # raw RapidFuzz score (0-100), 0.0 nếu L1 exact
    # Audit log: log toàn bộ fields này sau mỗi session (Copilot)
```

---

## ACCEPTANCE CRITERIA (Khi nào gọi là DONE?)

**Backward compat:**
- [ ] `correct_drug_names()` API cũ vẫn hoạt động — 409/409 PASS không giảm

**Layer 1 — Exact:**
- [ ] "am lô đi pin" → Amlodipine, confidence=1.0 ✅ (exact phonetic từ drug_db_v200)
- [ ] "a mốc xi lin" → Amoxicillin, confidence=1.0 ✅

**Layer 2 — Fuzzy:**
- [ ] "amlodiphin" → Amlodipine, score≥82, flagged=False ✅
- [ ] "am lô đi" → Amlodipine ✅ (fuzzy partial)
- [ ] "méphomin" → Metformin ✅ (fuzzy normalized)

**Ambiguity Gate (ChatGPT R-008-01 critical):**
- [ ] "met" alone → FLAG_AMBIGUOUS (Metformin vs Metoprolol vs Metronidazole) ✅
- [ ] "metronidazole" vs "metoprolol" → top2 gap check → flagged nếu gap < 8 ✅

**Safety — DOSE_OUT_OF_RANGE:**
- [ ] "Metformin 10mg" → matched Metformin, severity="HIGH", reason="DOSE_OUT_OF_RANGE" ✅
- [ ] "Amlodipine 50mg" → matched Amlodipine, severity="HIGH", reason="DOSE_OUT_OF_RANGE" ✅
- [ ] "Metformin 500mg" → matched Metformin, flagged=False ✅ (dose in range)

**Context (Layer 3):**
- [ ] context={diagnosis_icd10:"I10"} + "met" → Metoprolol preferred over Metformin ✅ (CCB/ARB context)
- [ ] context={drug_class_context:["antibiotic"]} + "amox" → Amoxicillin ✅

**Disfluency (Andy):**
- [ ] "ừm am lô đi pin" → Amlodipine ✅ (noise words filtered before window)

**Fallback + Audit:**
- [ ] drug_db_v200.json missing → load drug_db.json, no crash ✅
- [ ] Mỗi DrugMatch phải có đủ fields để audit log (original_text, score, layer, flag_reason, severity)

**Metrics (Andy):**
- [ ] Precision ≥ 92% trên `tools/ner_semantic_test.py` drug subset
- [ ] Recall ≥ 88% trên drug subset

**Tests:**
- [ ] `tests/unit/test_l1b_drug_correct_v2.py` ≥ 25 test cases
- [ ] CHANGELOG entry

---

## RISKS

| Risk ID | Mô tả | Kiểm soát |
|---|---|---|
| R-008-01 | False positive: fuzzy match sai drug (metronidazole vs metoprolol) | Ambiguity Gate: top1-top2 < 8 → FLAG_AMBIGUOUS; PRE-FILTER giảm search space |
| R-008-02 | Performance: ~500 alias keys × nhiều words | Cache alias_map_filtered theo session; RapidFuzz ~3M/s → OK |
| R-008-03 | Backward compat: API cũ bị break | correct_drug_names() giữ nguyên 100%, v2 là API song song |
| R-008-04 | Safety false alarm | dose_range={0,0} → skip safety; chỉ flag 40 manual drugs có dose_range đầy đủ |
| R-008-05 | L3 context match "quá tự tin" (Copilot) | confidence=0.6 + flagged=True bắt buộc cho L3; không auto-commit L3 |
| R-008-06 | Fuzzy scorer chưa tối ưu cho VN phonetics (Andy) | Phase 0: token_sort_ratio; Phase 1: thử WRatio hoặc custom phoneme distance |
| R-008-07 | Allergy/age-weight dosing chưa có (Andy) | Phase 0 SKIP, ghi note. Phase 1: allergy từ M1 patient record, nhi khoa riêng |

---

## TESTS REQUIRED

- [ ] `tests/unit/test_l1b_drug_correct_v2.py` (≥ 25 tests):
  - Layer 1: exact phonetic variants từ drug_db_v200 (north/central/south)
  - Layer 2: typos + abbreviations + VN phonetic mismatches
  - Layer 2: Ambiguity Gate — "metronidazole" vs "metoprolol" không auto-commit
  - Layer 2: low confidence (70-82) → flagged=True
  - Layer 3: context-aware — "met" + ICD-10 I10 → Metoprolol preferred
  - Layer 4 safety: dose out of range → severity="HIGH"
  - Layer 4 safety: dose in range → no flag
  - Disfluency: "ừm am lô đi" → Amlodipine (ignore filler words)
  - Backward compat: correct_drug_names() vẫn pass existing 409 tests
  - Fallback: db_v200 missing → load db v0.3.0, no crash
  - Config: DRUG_FUZZY_CUTOFF_STRICT=75 → more matches (param test)

---

## COMMIT FORMAT

```
feat(L1b): DrugCorrectionEngine v2 — 4-layer fuzzy + safety [FID-VN-008]
```

---

*FID-VN-008 | L1b DrugCorrectionEngine v2 | DRAFT 2026-06-10*
