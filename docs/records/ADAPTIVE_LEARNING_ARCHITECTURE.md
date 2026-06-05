# ADAPTIVE_LEARNING_ARCHITECTURE.md
# Kiến trúc học thích nghi — Giọng vùng miền + Drug names
# Ghi từ phiên 2026-06-08 | MediVoice VN
# Trạng thái: THIẾT KẾ — cần FID trước khi implement

---

## Vấn đề gốc

PhoWhisper-small bị phonetic explosion với drug names + giọng vùng miền:

| BS nói | PhoWhisper output | Đúng phải là |
|---|---|---|
| Domperidone | don erdogan lén buồn | Domperidone |
| Omeprazole 20mg | om mê brazil hai mươi | Omeprazole 20mg |
| tá tràng | tát rạn / đa trạng | tá tràng |
| mạch 80 | mặc tám mươi / mật tám | mạch 80 |

Alias mapping không đủ vì mỗi lần ASR noise khác nhau.
→ Giải pháp duy nhất dài hạn: fine-tuning + correction capture.

---

## Nguyên lý cốt lõi: Implicit Supervision

```
BS edit AI draft → đó LÀ nhãn (label) — không cần annotation riêng

AI output:  "Paracetamol 38mg"   ← sai
BS sửa:     "Paracetamol 500mg"  ← đúng
                    ↓
         Pair (sai, đúng) = 1 training example
         Thu thập đủ → học
```

Tên kỹ thuật: Continual Learning with Implicit Human Feedback
Gần với RLHF nhưng dùng direct correction thay vì reward model.
Tương tự: Google Keyboard, SwiftKey học từng người dùng không share data.

---

## Giải pháp 3 tầng cho giọng vùng miền + English proficiency

### TIER 1 — Ngay bây giờ (Phase 0, 0 đồng)

```
Upgrade PhoWhisper-small → PhoWhisper-medium
→ Coverage accent tốt hơn ~30%
→ Drug names nhận dạng tốt hơn đáng kể
→ Offline, cùng license BSD-3
→ Effort: ~2 giờ swap
```

### TIER 2 — Sau pilot (Phase 1, cần PA-006)

```
L4 Correction Capture:
  AI draft → BS sửa field → ghi pair → training_queue.jsonl

Correction Logger (không cần ML):
  {session_id, field, ai_value, bs_value, audio_hash, timestamp}
  → data/corrections/{clinic_id}/corrections.jsonl

Rule Updater (Frequency counting):
  Cùng pattern bị sửa > 5 lần → update regex rule
  VD: "38" bị bỏ 10 lần trong context nhiệt → fix: require medical unit

Alias Expander (Voting):
  (wrong_text, bs_typed_inn) → votes++
  votes > threshold → add normalized form vào alias_map
  VD: "don erdogan" × 5 lần → "Domperidone" → add alias
```

### TIER 3 — TRAIN-001 (cần 50-100h audio từ PA-006)

```
Thuật toán: LoRA (Low-Rank Adaptation)

Nguyên lý:
  PhoWhisper: 244M params → đóng băng hoàn toàn
  LoRA adapter: A × B matrix, rank=4~16
  → Chỉ train ~0.1% params của model
  → Nhanh, rẻ, không quên tiếng Việt chung (catastrophic forgetting avoided)

Kết quả per-clinic:
  Base model:           tiếng Việt chung tốt
  + clinic_danang.lora: giọng Đà Nẵng + drug names phòng khám cụ thể
  + clinic_saigon.lora: giọng Nam + drug names phòng khám cụ thể

Library: HuggingFace PEFT (đã có trong ecosystem Python)
```

---

## Data Flywheel

```
Phiên 1:   AI sai 40% → BS sửa 40 fields → 40 correction pairs
Phiên 50:  AI sai 25% → 25 pairs
Tháng 3:   500 pairs → trigger LoRA fine-tune
Phiên 100: AI sai 15% → BS hài lòng → dùng nhiều hơn

Vòng lặp: Dùng → Sửa → Học → Ít sửa → Dùng nhiều hơn
```

---

## Implementation roadmap

| Task | Phase | Effort | Blocker |
|---|---|---|---|
| Upgrade PhoWhisper-medium | Phase 0 | 2h | Không |
| Correction Logger (L4) | Phase 0 pilot | 1 FID | Không |
| Rule Updater | Phase 1 | 1 FID | 100 corrections |
| Alias Expander | Phase 1 | 1 FID | 500 corrections |
| LoRA Fine-tuner | TRAIN-001 | 1 sprint | PA-006 audio |
| Per-clinic adapters | Phase 2 | 1 sprint | TRAIN-001 done |

---

## Tham chiếu

- BACKLOG: TRAIN-001
- PENDING_REQUESTS: PA-006 (BENCH-002 audio Đà Nẵng)
- Nguồn: LoRA paper (Hu et al. 2021), HuggingFace PEFT library
- Ghi lại: 2026-06-08
