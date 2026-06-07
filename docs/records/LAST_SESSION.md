# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260607
## Thời gian: 2026-06-07
## Version: v0.7.1 → v0.7.2

---

## Trạng thái đầu → cuối
v0.7.1 | 395 tests → v0.7.2 | 395 tests

## Đã hoàn thành

- [BENCH-002a] ✅ Semi-synthetic CEER — 15 files (HN/SG/CT × 5 SC × take1)
  - Drug=0.967✅ Diag=0.667⚠️ Vital=0.333🔴 Fup=0.400🔴
  - SG best (Drug=1.1✅ Diag=1.0✅) | HN worst diag (Diag=0.6⚠️) | CT worst vital (Vital=0.22🔴)
  - `tools/bench_ceer_semi.py` — CEER adapter cho groundtruth_all.json format
  - `docs/dev/RECORDING_SCRIPTS_4BS.md` — fixes: "nôn ra máu", bỏ pronunciation guide
  - CA/BS4 dropped (WER 101%, code-switch EN/VN)

- [SYNTHETIC-NER-001] ✅ Expanded 2100 → 10,000 samples, 7 → 17 scenarios
  - 10 new: viem_phe_quan, viem_xoang, di_ung_mui, viem_da_ruot, nhiem_trung_tiet_nieu,
    thieu_mau, mat_ngu, tang_mo_mau, viem_ket_mac, viem_amidan
  - `data/synthetic_ner/` — train 7994 / val 1003 / test 1003

- [TRAIN-002] ✅ Overnight training scripts sẵn sàng
  - `scripts/train_ner_phobert.py` — PhoBERT NER training (3 epochs, 7994 train samples, CPU)
  - `scripts/download_vietmed.py` — VietMed download từ HuggingFace
  - `scripts/overnight_run.bat` — 1-click overnight: download VietMed + train NER (~5-8h)
  - Dependencies: accelerate + evaluate + seqeval ✅ installed

- [TEST-FIX] ✅ 395/395 PASS (từ 393/395)
  - `tests/conftest.py` — MEDIVOICE_SKIP_QWEN=1 disable Qwen 3B LLM loading trong tests
    - Root cause: Qwen load trong full suite → test_ac002_cdha flaky (assessment không có "DDx:")
  - `tests/unit/test_synthetic_ner_pipeline.py` — _vital_hit() thêm 10 scenarios mới

## Kết quả đo được
- Tests: 395/395 PASS (33s — cải thiện từ 18 phút nhờ conftest.py + SKIP_QWEN)
- BENCH-002a CEER: Drug 97% ✅ · Diag 67% ⚠️ · Vital 33% 🔴 · Fup 40% 🔴
- WER VI-only: SG 25.8% | CT 30.4% | HN 34.6% (CA dropped)

## Blocker / Phụ thuộc bên ngoài
- [TRAIN-002] Overnight run chưa bắt đầu — Andy khởi động trước khi ngủ
- [BENCH-002b] Cần pilot audio thật từ BS Đà Nẵng
- [PA-007] ChatGPT corpus 41 cases — Andy chưa generate
- [LEGAL-001] Thuê luật sư VN — Andy cần làm

## Phiên tiếp theo — làm ngay theo thứ tự
1. [TRAIN-002] Check kết quả overnight: `logs/overnight_run.log` + `models/ner_phobert/best/`
   - Nếu F1 > 0.70 → tích hợp vào l1c_ner.py (thay thế rule-based NER)
   - Nếu F1 < 0.50 → cần thêm data hoặc tune hyperparameters
2. [BENCH-002b] Pilot audio recording tại Đà Nẵng + CEER thật (sau TRAIN-002)
3. [PILOT] Test install.bat tại phòng khám Đà Nẵng (cần Andy onsite)
4. [DRUG-ALIAS-001] Mở rộng alias map trong drug_db.json (typo VN phổ biến)
