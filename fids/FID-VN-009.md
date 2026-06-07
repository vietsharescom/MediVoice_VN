# FID-VN-009 — Hybrid NER: PhoBERT + Rule-based (L1c upgrade)
# Feature Intent Document | ISO_VN v1.0
# Status: APPROVED — CONS-20260610-003 (3 AIs) 2026-06-10

| Field | Value |
|---|---|
| FID ID | FID-VN-009 |
| Layer | L1c |
| LOC estimate | ~200 LOC (new module) + ~40 LOC l1c_ner.py changes |
| Risk level | MEDIUM |
| Created | 2026-06-10 |
| Approved by | Andy Phan + CONS-20260610-003 (ChatGPT + Grok + Copilot) |
| Approved date | 2026-06-10 |

---

## WHY (Tại sao cần feature này?)

L1c hiện tại là **rule-based only** (regex/patterns, 446 LOC). Ưu điểm: nhanh, chính xác cho pattern cố định (sinh hiệu, chan_doan keyword). Nhược điểm: miss contextual symptoms, không bắt variant cú pháp mới.

TRAIN-002 đã produce **PhoBERT NER model** tại `models/ner_phobert/best/` (F1=99.44% synthetic):
- Entities: MEDICATION / SYMPTOM / VITAL / FOLLOWUP / DOSE / FREQUENCY / DURATION
- Trained on 10,000 synthetic VN outpatient sentences (BIO format)

**Vấn đề thực tế:**
- "bệnh nhân ho khạc đờm nhiều" → rule-based: `trieu_chung=[]` (không có keyword cố định)
- "theo dõi thêm" → rule-based: `tai_kham=""` (không bắt variant này)
- "mệt mỏi nhiều, ngủ kém" → rule-based: miss 2 symptoms

**PhoBERT SUPPLEMENT** → fill những gì rule-based miss, rule-based vẫn PRIMARY.

**Tại sao PhoBERT KHÔNG primary:**
1. Trained trên synthetic only → unknown real-world accuracy (validation cần BENCH-002b)
2. CPU latency ~200-400ms → acceptable nhưng cần cache
3. Rule-based vitals regex rất chính xác → không nên override

---

## WHAT (Feature làm gì?)

### Architecture: PARALLEL HYBRID + optional early-exit

```
transcript
    │
    ├─[ALWAYS]─ Rule-based NER (l1c_ner.py)
    │               → MedicalEntities_rule (fast, deterministic)
    │
    │ (if use_phobert=False → return here)
    │
    ├─[OPTIONAL EARLY-EXIT]─
    │   if _has_no_gap(entities_rule):    # trieu_chung + tai_kham + ly_do đều filled
    │       → return entities_rule (PhoBERT skipped, saves ~300ms)
    │
    ├─[IF use_phobert=True AND gap]─ PhoBERT NER (l1c_phobert.py — lazy load)
    │       → BIO predictions
    │       → Confidence filter (entity-type-specific thresholds)
    │       → VITAL entities → log to meta ONLY (không dùng để điền chart)
    │
    └─[MERGE]─ gap-filling strategy
        VITAL:      rule ONLY (PhoBERT VITAL → meta["phobert_vital_detected"])
        chan_doan:  rule wins nếu non-empty; PhoBERT fills empty
        don_thuoc:  L1b primary; PhoBERT SUPPLEMENT/VALIDATE:
                    - same INN → tăng confidence
                    - new INN + score≥0.85 → add với flagged_for_review=True
        trieu_chung: UNION (rule + PhoBERT, dedup by normalized text)
        tai_kham:   rule wins nếu non-empty; PhoBERT fills empty
        ly_do:      rule wins nếu non-empty; PhoBERT fills empty

MERGE STRATEGY DECISION (CONS-20260610-003):
  - 2/3 AIs (Grok + Copilot) → PARALLEL: medical accuracy over CPU
  - ChatGPT: CASCADE → addressed bằng optional early-exit
  - Copilot: VITAL log-to-meta (không skip silently) → research value
```

### Confidence Thresholds (entity-type-specific)

```python
# src/core/l1c_phobert.py
PHOBERT_CONFIDENCE_HIGH: float = 0.85   # MEDICATION, DOSE, FREQUENCY, DURATION
PHOBERT_CONFIDENCE_STD:  float = 0.75   # SYMPTOM, FOLLOWUP, LY_DO
PHOBERT_CONFIDENCE_MIN:  float = 0.60   # discard nếu dưới ngưỡng này

# Lý do phân tách: safety-critical entities cần ngưỡng cao hơn recall-priority entities
```

### PhoBERT Inference (l1c_phobert.py)

```python
# Lazy load — không load 512MB trừ khi USE_PHOBERT_NER=True
@lru_cache(maxsize=1)
def _load_phobert_pipeline():
    from transformers import pipeline
    return pipeline(
        "token-classification",
        model="models/ner_phobert/best",
        aggregation_strategy="simple",
        device=-1,  # CPU always (Phase 0 offline)
    )

def predict_entities(transcript: str) -> list[dict]:
    """Returns HF pipeline output: [{entity_group, score, word, start, end}]"""
    pipe = _load_phobert_pipeline()
    return pipe(transcript)
```

### BIO → MedicalEntities mapping

```
PhoBERT entity_group → MedicalEntities field:
  MEDICATION  → don_thuoc[].inn (SUPPLEMENT: if L1b missed + score ≥ 0.85 + flagged)
  DOSE        → don_thuoc[].ham_luong (last MEDICATION's dose, score ≥ 0.85)
  FREQUENCY   → don_thuoc[].lieu_dung (score ≥ 0.85)
  DURATION    → don_thuoc[].so_ngay (score ≥ 0.85)
  SYMPTOM     → trieu_chung (APPEND, score ≥ 0.75 — recall priority)
  VITAL       → meta["phobert_vital_detected"] ONLY — KHÔNG điền MedicalEntities
  FOLLOWUP    → tai_kham (fill if empty, score ≥ 0.75)

NOTE: VITAL → log to meta for research (cải thiện regex sau), không bao giờ override rule.
NOTE: MEDICATION với score 0.60-0.85 → discard (too risky for medical context)
```

### Public API (l1c_ner.py — unchanged signature)

```python
# UNCHANGED — no API break:
def extract_entities(transcript: str) -> MedicalEntities:
    """Rule-based only (default, USE_PHOBERT_NER=False)."""

# NEW — hybrid:
def extract_entities_hybrid(
    transcript: str,
    use_phobert: bool = False,   # must explicitly opt-in
) -> tuple[MedicalEntities, dict]:
    """
    Returns (entities, meta) where meta = {
        "rule_fields_filled": [...],
        "phobert_fields_added": [...],
        "phobert_confidence_avg": float,
        "phobert_used": bool,
        "phobert_vital_detected": [...],  # Copilot: log for research, không dùng chart
        "early_exit": bool,               # True nếu PhoBERT skipped vì rule đã đủ
    }
    """

def _has_coverage_gap(entities: MedicalEntities) -> bool:
    """True if any contextual field is empty → trigger PhoBERT."""
    return not entities.trieu_chung or not entities.tai_kham or not entities.ly_do
```

### Config flag

```python
# src/core/l1c_phobert.py
import os
USE_PHOBERT_NER = os.getenv("MEDIVOICE_PHOBERT_NER", "false").lower() == "true"
MODEL_PATH = Path("models/ner_phobert/best")
```

---

## ACCEPTANCE CRITERIA

- [ ] `extract_entities()` cũ không thay đổi — 444/444 PASS
- [ ] PhoBERT KHÔNG load khi `use_phobert=False` (default) — không thêm latency
- [ ] PhoBERT load thành công khi `use_phobert=True` (model tồn tại)
- [ ] "bệnh nhân ho khạc đờm" → `trieu_chung` có "ho" hoặc "ho khạc đờm" (rule or PhoBERT)
- [ ] "theo dõi thêm" → `tai_kham` non-empty khi PhoBERT enabled
- [ ] MERGE: rule-based vitals không bị PhoBERT override (huyết áp 130/80 vẫn đúng)
- [ ] MERGE: PhoBERT VITAL → meta["phobert_vital_detected"], không điền MedicalEntities
- [ ] MERGE: don_thuoc không bị duplicate INN (Metformin chỉ xuất hiện 1 lần)
- [ ] Confidence: MEDICATION score=0.70 bị discard (below PHOBERT_CONFIDENCE_HIGH=0.85)
- [ ] Confidence: SYMPTOM score=0.78 được accept (above PHOBERT_CONFIDENCE_STD=0.75)
- [ ] Early-exit: khi trieu_chung + tai_kham + ly_do đều filled → meta["early_exit"]=True
- [ ] Conditional FOLLOWUP "nếu không đỡ" → không auto-fill tai_kham
- [ ] ModelNotFound: nếu model missing → graceful fallback về rule-based, no crash
- [ ] Unit tests: `tests/unit/test_l1c_phobert_hybrid.py` ≥ 18 test cases
- [ ] Không vi phạm: L4 Human Gate vẫn là gating point cuối
- [ ] CHANGELOG entry

---

## RISKS

| Risk ID | Mô tả | Kiểm soát |
|---|---|---|
| R-009-01 | PhoBERT real-world F1 thấp hơn synthetic (99.44%) | Default OFF; pilot BENCH-002b validate trước khi bật production |
| R-009-02 | CPU latency 200-500ms/request | Lazy load + lru_cache; early-exit khi rule đủ; log timing |
| R-009-03 | MEDICATION trùng với L1b output | Don_thuoc dedup by normalized INN; flagged_for_review nếu PhoBERT-only |
| R-009-04 | VITAL từ PhoBERT conflict với rule-based | PhoBERT VITAL → meta only, không bao giờ điền MedicalEntities |
| R-009-05 | transformers import nặng (startup) | Lazy import chỉ trong _load_phobert_pipeline() |
| R-009-06 | model safetensors 512MB → slow load lần đầu | Log "PhoBERT loading..." + lru_cache sau lần đầu |
| R-009-07 | L1b error propagation → PhoBERT thấy INN sai | L1b output là ground truth; PhoBERT chỉ bổ sung, không override L1b INN |
| R-009-08 | Merge semantic ambiguity — "ho" vs "ho khan" | Normalize text trước dedup; longest span wins nếu overlap |
| R-009-09 | CPU bottleneck nếu latency > 600ms | Quantize 8-bit (BitsAndBytes) nếu cần; measure thực tế trên i5-12400F |
| R-009-10 | MEDICATION dedup strict — L1b + PhoBERT overlap | Normalize INN (lowercase strip) trước union; L1b entry giữ, PhoBERT skip |
| R-009-11 | Symptom over-extraction — PhoBERT tag quá nhiều | Filter: score ≥ 0.75; optionally filter by diagnosis context từ L1d |
| R-009-12 | FOLLOWUP misinterpretation — conditional vs definite | Flag conditional phrases ("nếu không đỡ") trong meta; không auto-fill tai_kham |

---

## TESTS REQUIRED

- [ ] `tests/unit/test_l1c_phobert_hybrid.py` (≥ 18 tests):
  - PhoBERT lazy load: không load khi use_phobert=False
  - PhoBERT load: thành công khi model exists + use_phobert=True
  - MERGE vitals: rule-based wins; PhoBERT VITAL → meta["phobert_vital_detected"]
  - MERGE trieu_chung: UNION (no duplicate, normalized dedup)
  - MERGE don_thuoc: L1b primary; PhoBERT supplement flagged_for_review
  - ModelNotFound: fallback to rule-based
  - extract_entities() cũ PASS (backward compat)
  - Hybrid output has meta dict with required keys (incl. phobert_vital_detected, early_exit)
  - phobert_confidence_avg in [0.0, 1.0]
  - Confidence filter: MEDICATION score=0.70 → discard (below 0.85)
  - Confidence filter: SYMPTOM score=0.78 → accept (above 0.75)
  - Early-exit: trieu_chung + tai_kham + ly_do all filled → meta["early_exit"]=True
  - Conditional FOLLOWUP: "nếu không đỡ thì tái khám" → tai_kham not auto-filled

---

## NOTES

**Phase 0:** `USE_PHOBERT_NER=False` (default) — validate trên pilot audio trước khi bật

**GO CRITERIA để enable production (BENCH-002b, ≥50 transcripts thực):**
  - trieu_chung recall ≥ +20% vs rule-only baseline
  - F1 (SYMPTOM + FOLLOWUP + MEDICATION) ≥ 0.85 trên real pilot audio
  - False positive rate ≤ 8%
  - BS satisfaction ≥ 80% ("đúng và hữu ích, không thêm thuốc sai")
  - Latency increase < 600ms vs rule-only
  - Critical errors (medication add mà BS không nói) = 0

**Phase 1:** Enable khi đạt GO CRITERIA trên (tất cả 6 điều kiện)
**Phase 2:** Fine-tune PhoBERT trên real clinical transcripts (sau BENCH-002b) → F1 thực tăng

---

## COMMIT FORMAT

```
feat(L1c): hybrid PhoBERT+rule NER — lazy load, parallel merge [FID-VN-009]
```

---

*FID-VN-009 | L1c Hybrid NER | APPROVED 2026-06-10 | CONS-20260610-003*
