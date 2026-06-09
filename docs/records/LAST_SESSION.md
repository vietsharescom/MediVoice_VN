# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260609d
## Thời gian: 2026-06-09
## Version: v0.9.0 → v0.9.1

---

## Trạng thái đầu → cuối
v0.9.0 | 755 tests PASS → v0.9.1 | 755 tests PASS (no new code tests)

## Đã hoàn thành
- [PA-009 DONE] Andy điền đủ 57/57 GT clips `data/eval/ref_voice_transcripts_review.txt`
- [BENCH-GT-001 DONE] 57/57 GT transcripts verified filled
- [BENCH-002b] `tools/bench_002b.py` — WER + CEER trên 57 real-voice clips BS thật (HN/DN/SG)
  - Parse review TXT → merge GT → compute WER (jiwer) + CEER (drug/diag/vitals/followup)
  - `data/eval/bench_002b_results.json` — full per-clip results saved
  - `data/eval/ref_voice_transcripts.json` — updated với GT + wer values

## Kết quả đo được BENCH-002b
| Metric | HN | DN | SG | ALL |
|--------|----|----|-----|-----|
| WER | 29.3%⚠️ | 16.3%✅ | 16.3%✅ | **18.4%**✅ |
| Drug CEER | 0.500⚠️ | 0.500⚠️ | 0.667🔴 | 0.556🔴 |
| Diag CEER | 1.000🔴 | 0.167✅ | 0.167✅ | 0.286⚠️ |
| Vitals CEER | 0.556🔴 | 0.208⚠️ | 0.312⚠️ | 0.307⚠️ |
| Followup CEER | 1.000🔴 | 0.333⚠️ | 0.000✅ | 0.273⚠️ |

Drug: TP=5, FN=4, FP=1 → Recall=55.6%LB, Precision=83.3%
Missed: Ciprofloxacin · Paracetamol · Vitamin B1 · Folic acid
⚠️ GT drug count understated: BS spell-out phonetic ("MÉt PHỐT min") → L1b miss → actual recall thấp hơn

## Phân tích findings
- WER 18.4% overall: PhoWhisper hoạt động tốt trên giọng BS thật (không cần fine-tune để deploy)
- HN WER 29.3% vs DN/SG 16.3%: Giọng Bắc harder cho PhoWhisper (không surprise)
- Drug recall 55.6% lower bound: BOTTLENECK chính — BS nói tên thuốc theo phonetic ("mét phốt min")
- Diag HN=0%: Hệ quả trực tiếp của WER cao — transcript quá noisy để NER extract
- RAG-001 hybrid đã implement → sẽ cải thiện drug recall cho real-voice queries
- TRAIN-001 vẫn required: PhoWhisper cần fine-tune để học pronunciation "Ciprofloxacin", "Tamsulosin"

## Blocker / Phụ thuộc bên ngoài
- [TRAIN-001] Fine-tune PhoWhisper cần 50-100h audio thật → cần thêm pilot sessions
- [PA-011 DONE] PhoBERT Q1/Q3 đã chốt (xem PENDING_REQUESTS)
- [VIETMED-FIX-001] HF_TOKEN cần để download VietMed audio 2.5GB

## Phiên tiếp theo — làm ngay theo thứ tự
1. [FID-VN-011] Write FID cho L1b RAG integration + model preload lifecycle (Andy hỏi cuối phiên)
2. [TRAIN-001] Chuẩn bị training pipeline PhoWhisper fine-tune — cần 50-100h audio
3. [drug_db expand] Thêm phonetic_variants cho missed drugs: Ciprofloxacin · Tamsulosin · Diazepam · Omeprazole
