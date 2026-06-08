# RAG + LangChain Integration Plan — MediVoice VN
# Version: 0.1.0 — 2026-06-08
# Status: DESIGN — Implement sau khi pilot data collected

---

## Tổng quan: Tại sao cần RAG?

Hệ thống hiện tại:
```
Audio → Whisper → transcript → LLM prompt (NER) → form
```

Vấn đề:
- LLM "đoán" tên thuốc từ context → sai nếu thuốc lạ
- LLM "đoán" ICD → không chắc chắn
- Không có knowledge base để look up → hallucination

Hệ thống với RAG:
```
Audio → Whisper → transcript
                        ↓
              [RAG Retrieval Layer]
               ├─ Drug DB search  → top-3 drug matches
               ├─ ICD DB search   → top-3 ICD suggestions
               └─ Medical vocab   → term normalization
                        ↓
              LLM (NER) + retrieved context → structured form
```

---

## 3 RAG Indexes cần xây

### Index 1: Drug RAG

```python
# Embed tất cả drug names + variants → vector store
# Query: ASR output substring → find closest drug

Document per drug:
  content: "Amlodipine. Phát âm: am-lô-đi-pin. Variants: amlo, am lo, amlodiphine..."
  metadata: {inn: "Amlodipine", category: "Calcium antagonist", dose_forms: [...]}

Query flow:
  ASR says "am lo di phi 5 milligram"
  → embed "am lo di phi"
  → cosine similarity → top match: Amlodipine (0.94)
  → inject into NER prompt: "Likely drug: Amlodipine 5mg"
```

### Index 2: ICD-10-VN RAG

```python
# QĐ5837 — 15,026 codes đã có
# Embed mã + mô tả → semantic search từ chẩn đoán BS

Document per ICD:
  content: "I10 — Tăng huyết áp nguyên phát / Essential hypertension"
  metadata: {code: "I10", chapter: "Circulatory", parent: "I10-I15"}

Query flow:
  BS nói "tăng huyết áp độ 2"
  → semantic search → top match: I10 (0.91), I11.9 (0.82)
  → suggest: "ICD gợi ý: I10, I11.9 — BS xác nhận"
```

### Index 3: Medical Vocabulary RAG

```python
# medical_vocab_by_specialty.json → embed terms + context
# Dùng để: detect specialty, boost relevant terms, normalize

Query flow:
  BS nói "thoát vị đĩa đệm cột sống thắt lưng"
  → vocab search → match: M51.1, specialty: orthopedics
  → NER prompt: [specialty_context = orthopedics]
  → NER boost: Etoricoxib, Pregabalin likely drugs
```

---

## Implementation Plan — 3 phases

### Phase 0 (Hiện tại — KHÔNG dùng RAG)
```
Current: Pure LLM NER với prompt engineering
Lý do: Groq free tier, đơn giản, đủ cho demo
Khi nào upgrade: Khi drug error rate > 10% sau 50 real recordings
```

### Phase 1 (Sau pilot — 2-3 tháng)
```
Tool: LlamaIndex hoặc LangChain + FAISS local vector store
Drug RAG: embed drug_pronunciation_vi.json → FAISS index
Integrate vào L1b (Drug correction layer)

Code sketch:
  from llama_index import VectorStoreIndex, Document
  
  drug_docs = [Document(text=f"{d['inn']} {' '.join(d['asr_variants'])}",
               metadata={"inn": d["inn"]}) for d in drug_db]
  drug_index = VectorStoreIndex.from_documents(drug_docs)
  
  def correct_drug_rag(asr_text):
      results = drug_index.query(asr_text, similarity_top_k=3)
      return results[0].metadata["inn"] if results[0].score > 0.8 else asr_text
```

### Phase 2 (Production — 6+ tháng)
```
Full RAG pipeline:
  - Drug + ICD + Medical Vocab all indexed
  - Streaming: ASR chunk → immediate RAG lookup → context injected to LLM
  - LangChain chain: ASR | DrugRAG | NERChain | ValidationChain | FormFill
  - Local inference: replace Groq with local LLM (Qwen-7B or Llama-3.1-8B)
  - Knowledge base auto-update: new drugs from pilot → re-embed overnight
```

---

## LangChain vs LlamaIndex — Chọn cái nào?

| Tiêu chí | LangChain | LlamaIndex |
|---|---|---|
| RAG document indexing | ✅ OK | ✅✅ Tốt hơn |
| LLM chain (multi-step) | ✅✅ Tốt hơn | ✅ OK |
| Community + docs | ✅✅ Lớn hơn | ✅ Tốt |
| VN-specific support | Như nhau | Như nhau |
| Complexity | Cao hơn | Vừa phải |

**Khuyến nghị: LlamaIndex cho RAG indexing + LangChain cho orchestration chain**

Thực tế Phase 1: Chỉ cần FAISS + simple similarity — không cần cả framework.

---

## Self-improving (Sức mạnh cộng đồng)

```
Flywheel:
  BS dùng app → correction data → training examples
                                        ↓
              [Weekly batch]
              1. Extract (transcript, correction) pairs
              2. Add to NER training set
              3. Fine-tune PhoBERT+CRF
              4. A/B test: new model vs old model
              5. Deploy if new model wins
              ↑_____________________________________↓

Metrics to track:
  - Drug name accuracy (by drug)
  - Tái khám extraction rate
  - ICD suggestion acceptance rate
  - Field_eval scores over time

Community model (tương lai):
  - Federated: mỗi phòng khám có model local
  - Aggregate: anonymous corrections → improve central model
  - KHÔNG share PII — chỉ share (anonymized_transcript, correction) pairs
```

---

## Ưu tiên triển khai

```
TUẦN 1-2:  Build vocabulary files (đã làm)
            Thu âm DRUG-DRILL-001 → measure baseline
THÁNG 1:   NER fine-tune trên ChatGPT corpus (PA-007)
THÁNG 2:   FAISS Drug RAG (Phase 1) → integrate vào L1b
THÁNG 3:   ICD RAG → suggest ICD từ chẩn đoán
THÁNG 4+:  LangChain chain → full RAG pipeline
```
