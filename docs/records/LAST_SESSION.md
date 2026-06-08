# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260612
## Thời gian: 2026-06-12
## Version: v0.8.3 → v0.8.4

---

## Trạng thái đầu → cuối
v0.8.3 | 473 tests → v0.8.4 | 473 tests

## Đã hoàn thành

- [AUDIO-MAP-001] Giải thích toàn diện quan hệ 3 doc types và audio folders:
  - `docs/dev/SEMI_SYNTHETIC_DATA_PLAN.md` → `data/audio/corpus/semi_synthetic/` (40 WAV / 35.1 min, calibration only)
  - `docs/dev/SYNTHETIC_AUDIO_REQUIREMENTS.md` → `data/synthetic_audio/` (60 WAV hiện có, target 1,100 clips TRAIN-001)
  - `docs/dev/REFERENCE_VOICE_GUIDE.md` → `data/audio/reference_voices/` (57 WAV / 17.2 min, BENCH-002b + TRAIN-001 + F5-TTS)
  - `data/audio/dental/` → Phase 1 riêng biệt, không đụng Phase 0
  - Bảng tổng hợp: Benchmark vs Training vs Voice Clone cho từng audio type

- [TRANSCRIBE-001] 57 real BS clips transcribed hoàn toàn (`tools/transcribe_ref_voices.py` background task):
  - Output: `data/eval/ref_voice_transcripts_review.txt` + `data/eval/ref_voice_transcripts.json`
  - HN: 9 clips | DN: 24 clips | SG: 24 clips — tổng 26.8 phút
  - RTF: 1.1–1.9x (PhoWhisper-medium CPU)
  - 12+ chuyên khoa phát hiện: tim mạch, hô hấp, GI, tiết niệu, nội tiết, nhi, sản khoa, da liễu, ung thư, dị ứng, thần kinh

- [BUG-EVAL-001] Fix NER bug `tools/eval_ref_voices.py` line 102:
  - Trước: `corrected, _ = correct_drug_names(hyp_text)` → RuntimeError "too many values to unpack"
  - Sau: `corrected = correct_drug_names(hyp_text)` — function trả về str không phải tuple

- [DRUG-MISHEAR-DOC] Documented 10 drug mishear patterns từ audio thật BS:
  - Amoxicillin → amosicilin / amosilin / camosilin
  - Metformin → mek fốc binh (worst — F→P, T→K)
  - Amlodipine → ong lau đi pin (worst — hoàn toàn mangle)
  - Paracetamol → parasyte môn
  - Loratadine → lông nata din
  - Prednisolone → brad ni sô lô
  - Ketoconazole → kê tô cô ra giôn
  - Tamsulosin → tam su lô xin (khá OK)
  - Aspirin → khá OK
  - Training data vàng cho TRAIN-001

- [PII-CONFIRM] Andy xác nhận: tên bệnh nhân trong audio là tên thật nhưng có consent đầy đủ — OK theo NĐ13/2023

## Kết quả đo được
- Tests: 473/473 PASS (không thay đổi — chỉ fix tool, không đổi production code)
- Transcription: 57/57 clips thành công, 0 ERROR
- Drug mishear patterns: 10 drugs documented từ audio thật
- Clinical diversity: 12+ chuyên khoa trong 57 clips (phong phú hơn semi-synthetic 5 diseases)

## Blocker / Phụ thuộc bên ngoài
- [BENCH-002b] ⏳ **Andy cần điền GT**: mở `data/eval/ref_voice_transcripts_review.txt`, nghe lại Clip2+Clip3 cho mỗi BS, ghi `GT:` — OK nếu đúng, transcript đúng nếu sai
- [PA-007] Andy paste `docs/dev/CHATGPT_CORPUS_PROMPT.md` → ChatGPT → 41 corpus scripts
- [VBEE_TOKEN] Andy cần lấy VBEE_TOKEN + VBEE_APP_ID để generate 1,100 synthetic clips
- [VIETMED-FIX-001] HF_TOKEN cho `scripts/download_vietmed.py` — không block Phase 0

## Phiên tiếp theo — làm ngay theo thứ tự
1. [BENCH-002b] Andy gửi `data/eval/ref_voice_transcripts_review.txt` đã fill GT → Claude chạy BENCH-002b CEER thật (drug/vital/symptom per BS) — HIGHEST PRIORITY
2. [PA-007] Andy paste ChatGPT corpus prompt → 41 clinical scripts → update CLINICAL_TEST_CORPUS_VN.md
3. [DRUG-DB-002] Mở rộng drug_db.json 118 → ~150 thuốc (Augmentin, Bisoprolol, Celecoxib...)
4. [CE-103-FU] Thêm Azithromycin "a zi thro my xin" phonetic alias vào drug_db_v200
5. [CONS-002-SPRINT6] TTS Pilot sau khi có VBEE_TOKEN
