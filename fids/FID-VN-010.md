# FID-VN-010 — AI Pipeline Redesign: Multi-layer RAG + Dialect + Real-time UI
# MediVoice VN | Author: Andy Phan + Claude Sonnet 4.6 | 2026-06-09
# Status: DRAFT — Pending Andy APPROVE
# Evidence base: BENCH-002b + CONS-20260608-002 + CONS-20260610-003 (6 AI reviews)
# Tier: Tầng 1 (>100 LOC, architecture change) → FID required

---

## 1. WHY — Bằng chứng thực nghiệm buộc phải redesign

### 1.1 Kết quả đo được từ data thật (không phải synthetic)

| Metric | Synthetic (test set) | Real BS voice | Gap |
|---|---|---|---|
| Drug Recall (local pipeline) | 99.5% | **13–18%** | 5–7x |
| Drug Recall (Cloud LLM) | — | 78% | — |
| WER PhoWhisper | 36–52% (gTTS) | **47–89%** (real) | 1.5–2x |
| NER F1 | 99.44% | **unknown** | unknown |
| don_thuoc accuracy | high | 1/4 = 25% (N=1) | ~4x |

### 1.2 Root causes xác định (CONS-20260608-002, 6 AI reviews)

```
RC-1: Drug OOV Hallucination
  "Ciprofloxacin" → "karaoke tamon" (PhoWhisper, deterministic)
  L1b text-level fuzzy match không recover được hallucination hoàn toàn

RC-2: No Clinical Domain Bias ở ASR Decoder
  Whisper decode với general VN language model
  Zero drug-domain signal → drug tokens bị suppress

RC-3: Fixed chunk (10s) cắt giữa câu
  BS nói "Kê Ciprofloxacin [cắt] 500mg" → 2 chunks mất context

RC-4: Dialect & Abbreviation
  "mô rứa hỉ" | "ha 155/95" | "bn 45t tk 4 tuần"
  NER/LLM không hiểu → miss fields

RC-5: Cloud LLM mask điểm yếu local
  Cloud 78% vs local 13% → pilot BS hài lòng nhưng product thật không đạt

RC-6: L4 Human Gate UX failure
  BS approve sai thuốc (Losartan→Atorvastatin) mà chấm 5/5
  Batch approve không force per-drug confirm
```

### 1.3 Prerequisite từ Copilot (CONS-20260610-003)

> "Bật PhoBERT ngay = pipeline tệ hơn, không tốt hơn."
> A1 + A2 + A3 phải done TRƯỚC khi enable bất kỳ ML layer mới nào.

---

## 2. WHAT — Kiến trúc mới

### 2.1 Overview: 5-layer solution stack

```
┌─────────────────────────────────────────────────────────────────────┐
│                  MEDIVOICE AI PIPELINE v2.0                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LAYER 0: Audio Pre-processing                                      │
│    L0-a: Normalize 16kHz mono (existing)                           │
│    L0-b: VAD chunking → silence-aware segments [NEW — A2]          │
│    L0-c: SHA-256 hash + purge (existing)                           │
│                                                                     │
│  LAYER 1: ASR + Text Normalization                                  │
│    L1a-i:  PhoWhisper-medium + prompt injection [NEW — A1]         │
│             initial_prompt = drug list + dialect hints              │
│    L1a-ii: Dialect normalization [NEW — A3a]                       │
│             "mô rứa hỉ" → "đâu vậy nhỉ" (dict 200+ entries)       │
│    L1a-iii: Abbreviation expansion [NEW — A3b]                     │
│             "ha" → "huyết áp" | "bn" → "bệnh nhân"                │
│                                                                     │
│  LAYER 2: Drug + Entity RAG                                         │
│    L1b-i:  Drug Correction Engine v2 (existing, FuzzyMatch)        │
│    L1b-ii: Drug Vector RAG [NEW — RAG-001]                         │
│             Query: distorted drug token + diagnosis context         │
│             Store: drug_db_v200 (146 INN, phonetic, class)         │
│    L1c-i:  Rule-based NER (existing)                               │
│    L1c-ii: PhoBERT NER SHADOW [FID-VN-009, default OFF]           │
│                                                                     │
│  LAYER 3: LangChain Orchestration                                   │
│    Chain-A: Drug normalization (drug RAG + phonetic)               │
│    Chain-B: ICD-10 lookup (15K vector store)                       │
│    Chain-C: Dialect context (regional mapping)                      │
│    Chain-D: Form fill + validation                                  │
│    LLM:    Groq LLaMA-3.3-70B (Phase 0) → Qwen2.5-7B LoRA (Ph2)  │
│                                                                     │
│  LAYER 4: Human Gate (redesigned)                                   │
│    Per-drug mandatory confirm [NEW — L4-REDESIGN]                  │
│    Confidence display per field                                     │
│    Dialect badge + mapping shown to BS                              │
│                                                                     │
│  REAL-TIME UI LAYER (parallel with all layers):                     │
│    Drug suggestion chips (top 3 candidates + pronunciation)         │
│    Dialect badge ("Giọng Trung phát hiện: mô=đâu")                │
│    Specialty terminology sidebar                                     │
│    Transcript live display (streaming)                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Chi tiết từng component mới

---

#### A1 — Whisper Prompt Injection

**Mục tiêu:** Bias PhoWhisper decoder về drug vocabulary trước khi transcribe.

**Cơ chế:** Whisper autoregressive decoder: mỗi token predict dựa trên token trước. Inject drug list vào `initial_prompt` → drug tokens có probability cao hơn khi audio có âm tương tự.

```python
# src/core/l1a_asr.py — thêm vào transcribe()

def build_initial_prompt(drug_db: dict, specialty: str = "noi_khoa") -> str:
    """Build domain-priming prompt cho Whisper decoder."""
    # Top 30 drugs by specialty (từ compatible_diagnoses)
    top_drugs = get_drugs_by_specialty(drug_db, specialty, n=30)
    drug_str = ", ".join(top_drugs)

    # Dialect hint theo region detect (Phase 1 — tạm để trống)
    dialect_hint = ""

    return (
        f"Bác sĩ Việt Nam kê đơn thuốc y tế: {drug_str}. "
        f"Chẩn đoán, sinh hiệu, tái khám. {dialect_hint}"
    )

# Trong transcribe():
result = model.transcribe(
    audio,
    language="vi",
    initial_prompt=build_initial_prompt(drug_db, specialty),
    condition_on_previous_text=True,
)
```

**Expected improvement:** 10–25% drug recall cho drugs có phonetic overlap (literature: ~15% relative WER reduction).
**Limitation:** Không cứu được hallucination hoàn toàn ("karaoke tamon").
**Effort:** 4h | **Risk:** Thấp | **Rollback:** Xóa initial_prompt parameter.

---

#### A2 — VAD Silence-Aware Chunking

**Mục tiêu:** Thay fixed 10s chunk bằng chunk theo điểm im lặng tự nhiên → không cắt giữa câu.

**Vấn đề hiện tại:**
```
BS: "Kê Ciprofloxacin [chunk cut] 500mg uống 2 lần"
Chunk 1: "Kê Ciprofloxacin" — OK
Chunk 2: "500mg uống 2 lần" — mất context drug → NER assign sai
```

**Giải pháp:**
```python
# src/core/l0_normalize.py — thêm vad_chunk()

from silero_vad import load_silero_vad, get_speech_timestamps

def vad_chunk_audio(audio_path: str, max_chunk_s: float = 20.0) -> list[dict]:
    """
    Chunk audio theo điểm im lặng tự nhiên (VAD).
    Mỗi chunk = 1 utterance hoàn chỉnh của BS.
    Max 20s để Whisper không bị truncate.
    """
    model = load_silero_vad()
    timestamps = get_speech_timestamps(audio, model, sampling_rate=16000)

    chunks = []
    for ts in merge_short_gaps(timestamps, gap_ms=500):
        chunk = {
            "start": ts["start"] / 16000,
            "end": ts["end"] / 16000,
            "audio": audio[ts["start"]:ts["end"]],
        }
        # Split nếu > max_chunk_s
        if (chunk["end"] - chunk["start"]) > max_chunk_s:
            chunks.extend(split_at_midpoint_silence(chunk))
        else:
            chunks.append(chunk)
    return chunks
```

**Library:** `silero-vad` (PyTorch, ~1MB, CPU fast, MIT license).
**Expected improvement:** WER giảm 5–15% do không cắt giữa câu. Drug + dose continuity tốt hơn.
**Effort:** 1 ngày | **Risk:** Thấp.

---

#### A3a — Dialect Normalization Dictionary

**Mục tiêu:** Map từ vùng miền về tiếng Việt chuẩn TRƯỚC khi vào NER.

```python
# src/core/dialect_norm.py — file mới

DIALECT_MAP = {
    # Miền Trung (Đà Nẵng, Huế, Quảng Nam)
    "central": {
        "mô": "đâu", "răng": "sao", "rứa": "vậy", "hỉ": "nhỉ",
        "ni": "này", "nớ": "đó", "tê": "kia", "chừng": "khoảng",
        "ngó": "nhìn", "tui": "tôi", "bây chừ": "bây giờ",
        "tra": "già", "nác": "nước", "đọi": "bát", "mần": "làm",
        "răng ri": "như thế nào", "cấy chi": "cái gì",
        "ốm": "bệnh",  # CRITICAL: miền Trung "ốm" = bệnh, không phải "gầy"
        "đau bụng dưới": "đau vùng hạ vị",  # clinical normalization
    },
    # Miền Nam (Sài Gòn, Cần Thơ, Kiên Giang)
    "southern": {
        "hổng": "không", "dzô": "vào", "tui": "tôi",
        "ổng": "ông ấy", "bả": "bà ấy", "nó": "bệnh nhân",
        "thôi": "rồi", "hen": "nhé", "nè": "này",
        "ốm": "gầy",  # CRITICAL: miền Nam "ốm" = gầy, không phải bệnh
        "mệt mỏi": "mệt mỏi",  # same
    },
    # Shared medical abbreviations (tất cả vùng)
    "medical_abbrev": {
        "ha": "huyết áp", "bn": "bệnh nhân", "tk": "tái khám",
        "xn": "xét nghiệm", "sa": "siêu âm", "xq": "x-quang",
        "đtđ": "đái tháo đường", "tha": "tăng huyết áp",
        "tmct": "nhồi máu cơ tim", "suy tim": "suy tim",
        "hc": "hồng cầu", "bc": "bạch cầu", "tc": "tiểu cầu",
        "bmi": "chỉ số khối cơ thể", "htl": "hút thuốc lá",
        "rltm": "rối loạn tiêu hoá",
    },
}

def normalize_dialect(text: str, region: str = "auto") -> tuple[str, list[str]]:
    """
    Normalize dialect → standard VN.
    Returns: (normalized_text, list_of_substitutions_made)
    Substitutions dùng để hiển thị trong UI (dialect badge).
    """
    ...
```

**⚠️ Critical semantic trap:** "ốm" = bệnh (miền Trung) ≠ "ốm" = gầy (miền Nam). Cần detect region trước khi normalize.

**Region detection:** Từ `facility.region` field khi BS đăng ký cơ sở → set mặc định. Có thể override theo session.

**Effort:** 2 ngày (dict 200 entries + unit tests) | **Risk:** Thấp.

---

#### A3b — Abbreviation Expansion

```python
# Tích hợp vào dialect_norm.py

def expand_abbreviations(text: str) -> str:
    """Medical abbreviation expansion — áp dụng SAU dialect normalization."""
    abbrevs = DIALECT_MAP["medical_abbrev"]
    # Regex word-boundary match (không replace "ha" trong "hai", "than")
    for abbr, expansion in abbrevs.items():
        text = re.sub(rf'\b{re.escape(abbr)}\b', expansion, text, flags=re.IGNORECASE)
    return text
```

**Effort:** 4h (tích hợp vào A3a) | **Risk:** Thấp.

---

#### RAG-001 — Drug Vector Store (LangChain + Chroma)

**Mục tiêu:** Thay thế/bổ sung RapidFuzz text-level matching bằng semantic + phonetic vector search.

**Cơ chế:** Mỗi drug trong drug_db_v200 = 1 document với đầy đủ context. Query = distorted drug token + chan_doan context → retrieve INN đúng.

```python
# src/core/drug_rag.py — file mới

from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

def build_drug_vectorstore(drug_db: dict) -> Chroma:
    """
    Build một lần, persist vào data/drug_vectorstore/
    Rebuild khi drug_db update.
    """
    docs = []
    for inn, d in drug_db["by_inn"].items():
        north = " ".join(d.get("phonetic_variants", {}).get("north", []))
        south = " ".join(d.get("phonetic_variants", {}).get("south", []))
        aliases = " ".join(d.get("name_variants", []))
        drug_class = d.get("drug_class", "")
        diagnoses = " ".join(d.get("compatible_diagnoses", []))
        dose_range = str(d.get("dose_range", ""))

        doc_text = (
            f"Tên thuốc INN: {inn}\n"
            f"Cách đọc miền Bắc: {north}\n"
            f"Cách đọc miền Nam: {south}\n"
            f"Tên biến thể: {aliases}\n"
            f"Nhóm thuốc: {drug_class}\n"
            f"Dùng cho: {diagnoses}\n"
            f"Liều thông thường: {dose_range}"
        )
        docs.append(doc_text)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        # Multilingual, 120MB, CPU fast, support VN
    )
    return Chroma.from_texts(docs, embeddings, persist_directory="data/drug_vectorstore")


def query_drug_rag(
    distorted_token: str,
    chan_doan_context: str,
    vectorstore: Chroma,
    k: int = 3,
) -> list[dict]:
    """
    Query drug RAG với distorted ASR token + diagnosis context.
    Ví dụ: query("glibizi", "đái tháo đường") → Glipizide (sulfonylurea)
    """
    query = f"{distorted_token} {chan_doan_context}"
    results = vectorstore.similarity_search_with_score(query, k=k)
    return [
        {"inn": r[0].page_content.split("\n")[0].replace("Tên thuốc INN: ", ""),
         "score": r[1]}
        for r in results
    ]
```

**Embedding model:** `paraphrase-multilingual-MiniLM-L12-v2` (120MB, CPU, multilingual VN support, MIT).

**Expected improvement:** Recover drugs như "glibizi" → Glipizide khi có diagnosis context. Complement L1b FuzzyMatch.

**Effort:** 3 ngày | **Risk:** Medium (cần validate không hallucinate).

---

#### UI-001 — Real-time Suggestion Layer

**Mục tiêu:** BS thấy gợi ý ngay khi nói, giảm cognitive load, tăng accuracy.

**3 loại gợi ý:**

```
┌──────────────────────────────────────────────────────────┐
│ 🎙️ Đang nghe...                    [Dừng] [Xóa]        │
│                                                           │
│ Transcript: "...kê thuốc Amlo..."                        │
│                                                           │
│ 💊 Gợi ý thuốc (tap để chọn):                           │
│  [Amlodipine 5mg | am-lo-đi-pin ▼]                      │
│  [Amoxicillin 500mg | a-mốc-xi-xi-lin]                  │
│  [Ambroxol 30mg | am-brốc-xôn]                          │
│                                                           │
│ 🗺️ Giọng Trung phát hiện:                               │
│  mô→đâu | rứa→vậy | hỉ→nhỉ          [Tắt]              │
│                                                           │
│ 📋 Thuật ngữ hay dùng (Nội khoa):                       │
│  [thoát vị đĩa đệm] [nhồi máu cơ tim]                  │
│  [rối loạn lipid máu] [đái tháo đường type 2]           │
└──────────────────────────────────────────────────────────┘
```

**Implementation:**
```javascript
// demo/static/js/suggestions.js — file mới

// Drug suggestion: trigger sau mỗi utterance (VAD segment end)
async function onUtteranceComplete(partialTranscript) {
    const candidates = await api.getDrugCandidates(partialTranscript);
    renderDrugChips(candidates);  // [{inn, pronunciation, score}]
}

// Dialect badge: trigger khi backend phát hiện dialect substitution
function onDialectDetected(substitutions) {
    // substitutions = [{"from": "mô", "to": "đâu"}, ...]
    renderDialectBadge(substitutions);
}

// Terminology sidebar: load theo specialty khi session start
async function loadTerminologySidebar(specialty) {
    const terms = await api.getTermsBySpecialty(specialty);
    renderTermSidebar(terms);  // [{term_vn, icd_code, pronunciation}]
}
```

**Backend API endpoints mới:**
```python
# demo/app.py — thêm 3 endpoints

GET  /api/drug-candidates?q={token}&diagnosis={text}&n=3
GET  /api/terms?specialty={noi_khoa|co_xuong_khop|...}&n=20
POST /api/dialect-check  body: {"text": "...", "region": "central"}
```

**Effort:** 5 ngày | **Risk:** Medium (UI real-time streaming).

---

#### L4-REDESIGN — Per-Drug Mandatory Confirm

**Vấn đề:** Session 174116 — Losartan→Atorvastatin, BS chấm 5/5 không phát hiện.

**Redesign:**
```
Hiện tại:
  [Form đầy đủ] → [Nút "Approve All"] → done

Mới:
  [Form đầy đủ]
  → Mỗi drug: [✓ Xác nhận: Amlodipine 5mg/sáng] [✗ Sai]
  → Mỗi drug flagged_for_review: [⚠️ AI chưa chắc: Atorvastatin — xác nhận?]
  → Chỉ khi tất cả drugs confirmed → mới unlock [Approve & Sign]

Confidence display:
  chan_doan: 0.92 ████████░░ (tự tin)
  don_thuoc[0]: 0.88 ████████░░ Amlodipine ✓
  don_thuoc[1]: 0.61 ██████░░░░ "Atorvastatin" ⚠️ (phải confirm)
  tai_kham: 0.45 ████░░░░░░ (AI không chắc — điền tay)
```

**Effort:** 3 ngày | **Risk:** Thấp | **Impact:** SAFETY CRITICAL.

---

## 3. HOW — Kế hoạch triển khai

### Phase 0 — NGAY (Tuần 1–2, không cần data mới)

| Task | File | Effort | Priority |
|---|---|---|---|
| A1: Prompt injection | `src/core/l1a_asr.py` | 4h | 🔴 CRITICAL |
| A2: VAD chunking | `src/core/l0_normalize.py` | 1 ngày | 🔴 CRITICAL |
| A3a: Dialect dict (200 entries) | `src/core/dialect_norm.py` | 2 ngày | 🔴 HIGH |
| A3b: Abbreviation expansion | `src/core/dialect_norm.py` | 4h | 🔴 HIGH |
| L4-REDESIGN: Per-drug confirm | `demo/app.py` + `demo/static/` | 3 ngày | 🔴 SAFETY |

**Tổng Phase 0:** ~1.5 tuần | Không cần GPU, không cần data mới, không cần training.

### Phase 0.5 — Tuần 3–4 (sau khi A1/A2/A3 done)

| Task | File | Effort | Priority |
|---|---|---|---|
| RAG-001: Drug vector store | `src/core/drug_rag.py` | 3 ngày | 🟡 HIGH |
| UI-001: Drug suggestion chips | `demo/static/js/suggestions.js` | 3 ngày | 🟡 HIGH |
| UI-002: Dialect badge | `demo/static/js/suggestions.js` | 1 ngày | 🟡 MEDIUM |
| UI-003: Terminology sidebar | `demo/static/js/suggestions.js` | 2 ngày | 🟡 MEDIUM |
| BENCH-GT-001: Fill GT 57 clips | (Andy) | Andy's time | 🔴 CRITICAL |

### Phase 1 — Tháng 2–3 (sau khi có BENCH-002b real data)

| Task | Effort | Prerequisite |
|---|---|---|
| PhoBERT production (FID-VN-009) | 1 tuần | BENCH-002b GO criteria |
| Phoneme-level drug matching | 2 tuần | Drug pronunciation corpus |
| LangChain 4 chains (Drug/ICD/Dialect/Form) | 2 tuần | RAG-001 done |
| ICD-10 vector store (15K codes) | 1 tuần | LangChain setup |

### Phase 2 — Tháng 6–12 (LoRA + Local LLM)

| Task | Effort | Prerequisite |
|---|---|---|
| LoRA PhoWhisper (regional medical) | 3 tuần train | 50h labeled audio |
| Qwen2.5-7B LoRA local (replace Groq) | 2 tuần | Medical VN instruction data |
| Dialect audio collection (Đà Nẵng/SG/CT) | 2-3 tháng | Pilot BS agreement |
| Continual learning loop (L4 corrections → retrain) | 1 tuần setup | Production data |

---

## 4. ACCEPTANCE CRITERIA

### Phase 0 GO (sau 2 tuần):

| Metric | Threshold | Đo bằng |
|---|---|---|
| A1 Drug Recall improvement | ≥ +10% vs baseline | BENCH002 gTTS 10 files |
| A2 WER improvement | ≥ -5% vs fixed chunk | BENCH-002b 3 GT clips |
| A3 Abbreviation expand rate | ≥ 95% common abbrevs | Unit test 50 cases |
| L4 Per-drug confirm | BS phải confirm từng drug | UI integration test |
| All tests pass | 473/473 | pytest -q |

### Phase 0.5 GO (sau 4 tuần):

| Metric | Threshold |
|---|---|
| Drug RAG recall | ≥ 50% cho drugs ngoài top-30 common |
| Drug suggestion accuracy | ≥ 70% (top-1 correct) |
| BENCH-002b GT filled | ≥ 50/57 clips |
| BENCH-002b real CEER Drug | measured (benchmark established) |

### Phase 1 GO (PhoBERT):

| Metric | Threshold |
|---|---|
| trieu_chung recall | ≥ +20% vs rule-only |
| F1 real pilot audio | ≥ 0.85 trên ≥50 transcripts |
| BS correction rate drop | ≥ -10% |
| Critical errors | = 0 |

---

## 5. RISKS

| ID | Risk | Severity | Mitigation |
|---|---|---|---|
| R-010-01 | Prompt injection over-bias (wrong drug suggested) | HIGH | Threshold: only inject when confidence > 0.7; limit to 30 drugs |
| R-010-02 | VAD too aggressive (split mid-drug name) | MEDIUM | Tune gap_ms threshold; test trên 57 clips |
| R-010-03 | Dialect normalization semantic error ("ốm" ambiguous) | HIGH | Region-aware mapping; default to no-op if region unknown |
| R-010-04 | Drug RAG hallucinate (wrong drug from context) | HIGH | Score threshold ≥ 0.80; always flagged_for_review |
| R-010-05 | UI latency > 1s (suggestion too slow) | MEDIUM | Async API; cache top-30 drugs per specialty |
| R-010-06 | L4 redesign alert fatigue (BS clicks through) | MEDIUM | Max 5 items confirm; group by category |
| R-010-07 | PhoBERT enabled too early (before BENCH GO) | HIGH | Environment flag default=False; document prerequisite |

---

## 6. KHÔNG THAY ĐỔI (FROZEN)

- Pipeline L0→L10 tổng thể — chỉ thêm layers, không xóa
- L4 Human Gate — không bypass (Luật KCB 2023 Đ.62)
- Data residency VN — không gửi audio ra ngoài
- SQLite + Fernet storage
- PDF Mẫu 15/BV-01 output format

---

## 7. TECHNICAL STACK MỚI

| Component | Library | Size | License |
|---|---|---|---|
| VAD | silero-vad | ~1MB model | MIT |
| Drug Vector Store | chromadb + sentence-transformers | ~120MB | Apache 2.0 |
| Embedding | paraphrase-multilingual-MiniLM-L12-v2 | ~120MB | Apache 2.0 |
| Dialect dict | JSON file (custom) | ~50KB | Internal |

---

## 8. FILE STRUCTURE MỚI

```
src/core/
  l0_normalize.py    ← thêm vad_chunk_audio()
  l1a_asr.py         ← thêm build_initial_prompt()
  dialect_norm.py    ← file mới: normalize_dialect(), expand_abbreviations()
  drug_rag.py        ← file mới: build_drug_vectorstore(), query_drug_rag()

demo/
  app.py             ← thêm 3 API endpoints
  static/js/
    suggestions.js   ← file mới: drug chips, dialect badge, terminology

data/
  drug_vectorstore/  ← Chroma persistent store (gitignored)
  dialect/
    central_dict.json
    southern_dict.json
    medical_abbrev.json
```

---

*FID-VN-010 | AI Pipeline Redesign v2.0 | MediVoice VN | 2026-06-09*
*Status: DRAFT — Andy approve trước khi implement*
*Evidence: CONS-20260608-002 + CONS-20260610-003 (6 AI perspectives)*
