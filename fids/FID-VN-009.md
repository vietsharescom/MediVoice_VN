# FID-VN-009 — Hybrid NER: PhoBERT + Rule-based (L1c upgrade)
# Feature Intent Document | ISO_VN v1.0
# Status: DRAFT

| Field | Value |
|---|---|
| FID ID | FID-VN-009 |
| Layer | L1c |
| LOC estimate | ~180 LOC (new module) + ~30 LOC l1c_ner.py changes |
| Risk level | MEDIUM |
| Created | 2026-06-10 |
| Approved by | Andy Phan |
| Approved date | — |

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

### Architecture: PARALLEL HYBRID

```
transcript
    │
    ├── Rule-based NER (l1c_ner.py, hiện tại)
    │       → MedicalEntities_rule (fast, precise for vitals/chan_doan)
    │
    ├── PhoBERT NER (l1c_phobert.py, mới — lazy load)
    │       → BIO tags → MedicalEntities_phobert
    │       (chỉ chạy nếu USE_PHOBERT_NER=True ENV hoặc config)
    │
    └── MERGE (merge_entities)
            → MedicalEntities_final

MERGE STRATEGY (field-by-field):
  Vitals (nhiet_do, huyet_ap, mach, nhip_tho, can_nang, spo2):
    → rule-based ALWAYS wins (regex rất precise)

  chan_doan:
    → rule-based wins nếu non-empty
    → PhoBERT fills nếu rule-based empty

  don_thuoc:
    → UNION, deduplicate by INN (L1b đã normalize INN trước)

  trieu_chung:
    → UNION cả hai (PhoBERT thường rộng hơn rule-based)

  tai_kham:
    → rule-based wins nếu non-empty; PhoBERT fills empty

  ly_do:
    → rule-based wins nếu non-empty; PhoBERT fills empty
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
  MEDICATION  → don_thuoc[].inn (if L1b missed it)
  DOSE        → don_thuoc[].ham_luong (last MEDICATION's dose)
  FREQUENCY   → don_thuoc[].lieu_dung
  DURATION    → don_thuoc[].so_ngay
  SYMPTOM     → trieu_chung (APPEND — không override rule-based)
  VITAL       → SKIP (rule-based regex handles this better)
  FOLLOWUP    → tai_kham (fill if rule-based empty)
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
    }
    """
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
- [ ] MERGE: don_thuoc không bị duplicate INN (Metformin chỉ xuất hiện 1 lần)
- [ ] ModelNotFound: nếu model missing → graceful fallback về rule-based, no crash
- [ ] Unit tests: `tests/unit/test_l1c_phobert_hybrid.py` ≥ 15 test cases
- [ ] Không vi phạm: L4 Human Gate vẫn là gating point cuối
- [ ] CHANGELOG entry

---

## RISKS

| Risk ID | Mô tả | Kiểm soát |
|---|---|---|
| R-009-01 | PhoBERT real-world F1 thấp hơn synthetic (99.44%) | Default OFF; pilot BENCH-002b validate trước khi bật production |
| R-009-02 | CPU latency 200-500ms/request | Lazy load + lru_cache; chỉ bật khi cần; log timing |
| R-009-03 | MEDICATION trùng với L1b output | Don_thuoc dedup by INN; L1b INN chuẩn hóa trước L1c |
| R-009-04 | VITAL từ PhoBERT conflict với rule-based | Luôn skip PhoBERT VITAL entity → rule-based wins |
| R-009-05 | transformers import nặng (startup) | Lazy import chỉ trong _load_phobert_pipeline() |
| R-009-06 | model safetensors 512MB → slow load lần đầu | Log "PhoBERT loading..." + lru_cache sau lần đầu |

---

## TESTS REQUIRED

- [ ] `tests/unit/test_l1c_phobert_hybrid.py` (≥ 15 tests):
  - PhoBERT lazy load: không load khi use_phobert=False
  - PhoBERT load: thành công khi model exists + use_phobert=True
  - MERGE vitals: rule-based wins
  - MERGE trieu_chung: UNION (no duplicate)
  - MERGE don_thuoc: dedup by INN
  - ModelNotFound: fallback to rule-based
  - extract_entities() cũ PASS (backward compat)
  - Hybrid output has meta dict with required keys
  - phobert_confidence_avg in [0.0, 1.0]

---

## NOTES

**Phase 0:** `USE_PHOBERT_NER=False` (default) — validate trên pilot audio trước khi bật
**Phase 1:** Enable khi BENCH-002b xác nhận real-world F1 ≥ 70% trên clinical audio
**FID-VN-007** (TRAIN-001) sẽ fine-tune PhoWhisper → sau đó retrain PhoBERT với real data
→ Lúc đó F1 thực sẽ cao hơn synthetic training

---

## COMMIT FORMAT

```
feat(L1c): hybrid PhoBERT+rule NER — lazy load, parallel merge [FID-VN-009]
```

---

*FID-VN-009 | L1c Hybrid NER | DRAFT 2026-06-10*
