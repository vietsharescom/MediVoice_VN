# FID-VN-011 — L1b Layer 3 RAG + Model Preload Lifecycle
# MediVoice VN | Feature Intent Document
# Status: DRAFT — Chờ Andy approve
# Author: Claude | Created: 2026-06-09
# Refs: BENCH-002b Drug Recall=55.6%LB · drug_rag.py hybrid · main.py startup

---

## 1. WHY — Vấn đề cần giải quyết

### Vấn đề 1: Drug recall thấp trong pipeline thật

BENCH-002b (2026-06-09) đo trên 57 real-voice clips:
- **Drug Recall = 55.6% (lower bound)**
- TP=5, FN=4 — pipeline miss các thuốc mà BS nói theo phonetic

Root cause đã xác định:
- L1b alias map + RapidFuzz hoạt động ở **word level** trong transcript
- Khi PhoWhisper output garbled (WER HN=29.3%), tên thuốc bị cắt xén → alias miss
- Hybrid RAG đã có (`drug_rag.py` — 0.65×fuzzy + 0.35×RAG) nhưng **chưa wired vào L1b pipeline**

### Vấn đề 2: Cold start per API call

Hiện tại `hybrid_query_drug()` tại `/api/drug-candidates`:
```python
# main.py line 529 — load EVERY CALL
model = _ST("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
```
→ 3-5 giây load SentenceTransformer mỗi lần BS click drug suggestion
→ Không thể dùng trong L1b pipeline (sẽ tăng transcription latency ~5s/clip)

---

## 2. WHAT — Thay đổi cụ thể

### A. Model Preload tại Startup

**File**: `src/api/main.py`

```python
# _embed_model singleton — set at startup, used by all endpoints
_embed_model: "SentenceTransformer | None" = None
_drug_collection: "chromadb.Collection | None" = None

@app.on_event("startup")
async def startup():
    global _embed_model, _drug_collection
    init_db()
    # Preload embedding model + vectorstore nếu deps available
    try:
        from .core.drug_rag import load_drug_vectorstore, _DEPS_AVAILABLE
        if _DEPS_AVAILABLE:
            from sentence_transformers import SentenceTransformer
            _embed_model = SentenceTransformer(
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
            _drug_collection = load_drug_vectorstore()
            logger.info("RAG model preloaded — %.0fMB", ...)
    except Exception as e:
        logger.warning("RAG preload skip: %s", e)
```

`/api/drug-candidates` endpoint dùng `_embed_model` + `_drug_collection` thay vì load per-call.

### B. L1b Layer 3 — RAG Fallback

**File**: `src/core/l1b_drug_correct.py`

Layer 3 hiện tại (context validation) được mở rộng: khi fuzzy score thấp (`< DRUG_FUZZY_CUTOFF_FLAG = 70%`), thử hybrid RAG query.

```
Layer 1: Exact match (alias_map)           → auto-accept ≥88%
Layer 2: Fuzzy match (RapidFuzz)           → auto-accept ≥88%, flag 70-88%
Layer 3: Hybrid RAG fallback               → NEW — khi Layer 1+2 miss
          (0.65×fuzzy_phonetic + 0.35×RAG)
          → auto-accept nếu score ≥ 0.68
          → flag nếu 0.55 ≤ score < 0.68
          → skip nếu score < 0.55
Layer 4: Safety validation                 → giữ nguyên
```

**Inject model** vào L1b qua dependency injection (không hardcode):
```python
def correct_drug_names(
    transcript: str,
    session_context: dict | None = None,
    *,
    rag_collection=None,           # NEW
    embed_model=None,              # NEW — None = skip RAG
) -> list[DrugMatch]:
```

Caller (main.py pipeline) truyền `_drug_collection` + `_embed_model` khi available.

### C. Threshold Calibration

| Score | Action | Rationale |
|---|---|---|
| ≥ 0.68 | AUTO-ACCEPT | Phonetic match rõ ràng (e.g. "mek foc binh" → Metformin ~0.87) |
| 0.55 – 0.68 | FLAG LOW_CONFIDENCE | BS review nhưng suggestion hiện sẵn |
| < 0.55 | SKIP | Quá uncertain — không suggest |

> Threshold 0.68 dựa trên: hybrid demo "xi pro phlo" → Ciprofloxacin score ~0.71 ✅,
> "am lo" → Amlodipine ~0.47 (2-syllable prefix, quá ngắn) ❌.
> Sẽ re-calibrate sau pilot data.

---

## 3. SCOPE — KHÔNG thay đổi

- Pipeline L0→L10 frozen — chỉ thêm injection point tại L1b Layer 3
- L4 Human Gate KHÔNG bypass — drug flagged vẫn cần BS confirm
- Nếu `_embed_model = None` (deps not installed), L1b hoạt động như cũ — full backward compat
- `drug_rag.py` không thay đổi — chỉ wire vào L1b
- Tất cả existing L1b tests phải tiếp tục PASS

---

## 4. ACCEPTANCE CRITERIA

| ID | Criteria | Test |
|---|---|---|
| AC-001 | `startup()` load SentenceTransformer + Chroma một lần — `_embed_model is not None` sau startup | `test_startup_preload.py` |
| AC-002 | `/api/drug-candidates` dùng preloaded model (không gọi `SentenceTransformer()` trong handler) | mock test |
| AC-003 | `correct_drug_names()` nhận `rag_collection` + `embed_model` params — backward compat khi `None` | unit test |
| AC-004 | Layer 3 RAG fallback: "xi pro phlo xa" → Ciprofloxacin, score ≥ 0.68 | unit test |
| AC-005 | Layer 3 RAG fallback: "mek foc binh" (Metformin south phonetic) → match ≥ 0.68 | unit test |
| AC-006 | Khi `embed_model=None`, L1b Layer 3 skip silently — không raise exception | unit test |
| AC-007 | Latency `/api/transcribe` không tăng > 500ms khi RAG available (model đã preloaded) | benchmark |
| AC-008 | 100% existing tests PASS (no regression) | pytest -q |

---

## 5. ESTIMATE

| Phần | LOC | Ghi chú |
|---|---|---|
| `main.py` preload + inject | ~30 | `startup()` + truyền params vào pipeline |
| `l1b_drug_correct.py` Layer 3 | ~50 | Thêm RAG fallback branch + params |
| `tests/unit/test_l1b_rag_layer3.py` | ~60 | 8 acceptance criteria tests |
| Tổng | **~140 LOC** | → Tầng 1 (>100 LOC) — cần FID ✅ |

---

## 6. KHÔNG làm trong FID này

- Fine-tune PhoWhisper → FID-VN-012 (TRAIN-001)
- Standalone L1b RAG (không qua startup) → sau pilot
- Threshold auto-calibration từ pilot data → Phase 1
- RAG trong dialect_norm.py → không cần

---

## 7. DECISION NEEDED — Andy approve

**Q1**: Approve implement A (model preload) + B (L1b Layer 3 RAG fallback)?
- **Yes** → Claude implement ngay phiên này, ~140 LOC, test first
- **No / Later** → defer đến sau TRAIN-001

**Q2**: Threshold 0.68 có phù hợp? (Pilot data sẽ fine-tune sau)
- Có thể điều chỉnh: lower (0.60) = nhiều suggestions hơn nhưng nhiều FP; higher (0.75) = conservative hơn

---

*FID-VN-011 | DRAFT 2026-06-09 | Claude*
*Evidence: BENCH-002b `data/eval/bench_002b_results.json` · drug_rag.py hybrid*
