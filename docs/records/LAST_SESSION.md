# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260609
## Thời gian: 2026-06-09
## Version: v0.7.0 → v0.7.1

---

## Trạng thái đầu → cuối
v0.7.0 | 388 tests → v0.7.1 | 395 tests

## Đã hoàn thành

- [SYNTHETIC-NER-001] `scripts/generate_synthetic_ner.py` — 2100 BIO-tagged samples, 7 scenarios × 4 regions (HN/SG/CT/CA), 9 entity types. Output: `data/synthetic_ner/train.jsonl` (1680) + `val.jsonl` (210) + `test.jsonl` (210)
- [NER-BUGFIX-004] `src/core/l1c_ner.py` chan_doan regex major fix — xử lý ". filler Kê" pattern (2 lookahead alternatives), ICD codes inline ("viêm họng cấp J02.9"), "gout" trong fallback, "bị/mắc" trigger
- [SYNTHETIC-NER-001] `tests/unit/test_synthetic_ner_pipeline.py` — 7 tests, 210 test samples qua pipeline. Drug 97-100% · CD 63-80% · Vital 63-77% · TK 33-60%
- [DATASET-001] Download VietMed-NER (9K) + VietMed-Sum (106K) + VN Medical QA (9K) → `data/external/`
- [DATASET-002] `scripts/analyze_vietmed_ner.py` — entity mapping 18 types → 9 types, `data/reference/vietmed_drugs_raw.json` (313 drugs)
- [DRUG-DB] `data/reference/drug_db.json` v0.2.0 — 110 → 118 drugs (+8: Progesterone/Estradiol/Dydrogesterone/MefenamicAcid/Norfloxacin/Spironolactone/Carvedilol/Ceftriaxone)
- [DATA-PLAN] `docs/dev/SEMI_SYNTHETIC_DATA_PLAN.md` + `docs/dev/RECORDING_SCRIPTS_4BS.md` (20 scripts) + `data/audio/corpus/semi_synthetic/groundtruth_all.json`
- [DATA-CATALOG] `docs/dev/DATA_CATALOG.md` — 26 datasets, license/domain/download status

## Kết quả đo được
- Tests: 395/395 PASS (+7 từ `tests/unit/test_synthetic_ner_pipeline.py`)
- Pipeline hit rates on 210 synthetic samples: Drug 97-100% · chan_doan 63-80% · vital 63-77% · tai_kham 33-60%
- chan_doan regex: 10/10 test cases pass (". thật ra Kê", "bị gout cấp. Cho dùng", J02.9 inline)
- doof-ferb/VietMed_labeled = YouTube source (NOT real clinic), ViMedNER data chưa available

## Blocker / Phụ thuộc bên ngoài
- [PA-008] 4 người ghi âm (HN/SG/CT/CA) — Andy cần tìm người trước khi có BENCH-002a
- [PA-006] Dental ground truth labels — Andy chưa điền
- [PA-007] ChatGPT corpus — Andy chưa generate
- [DATASET-001] VietMed audio 2.5GB + ViMedCSS 4GB — cần disk/bandwidth riêng

## Phiên tiếp theo — làm ngay theo thứ tự
1. [PILOT] Install.bat thật tại phòng khám Đà Nẵng — nếu Andy sẵn sàng deploy
2. [BENCH-002a] Sau khi PA-008 xong (4 người ghi âm) → run `tools/bench_ceer.py` calibrate
3. [DATASET-001] Download phần còn lại: VietMed ASR 2.5GB + ViMedCSS 4GB (khi có disk)
4. [analyze_corrections.py] Chạy sau 10+ approvals tích lũy từ pilot
