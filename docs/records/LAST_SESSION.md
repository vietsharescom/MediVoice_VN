# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260608e
## Thời gian: 2026-06-08
## Version: v0.6.1 → v0.6.3

---

## Trạng thái đầu → cuối
v0.6.1 | 322 tests → v0.6.3 | 352 tests

## Đã hoàn thành

- [VN-NER-003] **Real-world NER+ICD bug fix — 11 bugs từ A-01/A-02/A-03 testing**

  A-01 (Viêm họng cấp):
  1. `chan_doan` boundary overflow → stop at "điều trị/kê đơn/tái khám"
  2. Temperature decimal without "phẩy" → "ba mươi bảy tám" = 37.8
  3. Patient self-medication filter → "bệnh nhân tự uống X" excluded from don_thuoc
  4. Drug unit ml→mg for oral route (PhoWhisper: "miligam"→"ml")

  A-02 (Viêm loét dạ dày):
  5. ICD-10 `auto_lookup()` progressive prefix matching — drop up to 3 trailing ASR noise words
  6. Iron (Ferrous) context guard — require anemia context to prevent Losartan phonetic false positive

  A-03 (Tăng huyết áp):
  7. `_RE_HA_SYSTOLIC` — allow up to 40 chars intermediate text ("hôm nay là 170/100")
  8. `_RE_BP_WORDS` — add "tri" as alias for "trên" (PhoWhisper phonetic confusion)
  9. `ly_do` fallback — skip "nghề nghiệp X" prefix
  10. `ly_do` — require symptom keyword (đau/sốt/ho/khó...) to accept fallback
  11. `tai_kham` — strip trailing admin text, only keep "hoặc/nếu/sớm hơn" clauses

- [CORPUS-001] **CLINICAL_TEST_CORPUS_VN.md v2.0** — VN terminology fixes
  - "tổng trạng tỉnh táo" → "tình trạng tỉnh táo"
  - "đau tăng khi nuốt" → "đau khi nuốt"

- [ADAPTIVE-001] **`docs/records/ADAPTIVE_LEARNING_ARCHITECTURE.md`** — Design document
  - 3-tier: TIER 1 PhoWhisper-medium upgrade · TIER 2 L4 Correction Capture · TIER 3 LoRA fine-tune
  - ASR failure log: Domperidone/Omeprazole/Losartan phonetic explosions documented
  - Data flywheel formula: Dùng → Sửa → Học → Dùng nhiều hơn

- [CHATGPT-CORPUS-001] **`docs/dev/CHATGPT_CORPUS_PROMPT.md` v2.0** — 41-case corpus prompt
  - Groups A-H: A (Tổng quát) B (Thuốc mạn tính) C (Nha khoa) D (CĐHA) E (Phụ sản) F (NER Stress/negation) G (Intent/temporal) H (Dental extended)
  - 3-file structure per case: script.txt / reference.txt / groundtruth.json
  - Extended brand→INN mapping, ICD-10-VN clarification

- [DOC] BACKLOG.md: VN-NER-003/CORPUS-001/ADAPTIVE-001 → ✅ | CHATGPT-CORPUS-001 → pending (PA-007)
- [DOC] CHANGELOG.md: v0.6.2 + v0.6.3 entries added
- [DOC] PENDING_REQUESTS.md: PA-007 added (ChatGPT corpus)
- [DOC] PROJECT_PROGRESS.md: SES-20260608e added, metrics 322→352

## Kết quả đo được
- Tests: **352/352 PASS** (+30 NER regression tests từ A-01/A-02/A-03)
- A-01 (Viêm họng cấp): chan_doan ✅ nhiệt_độ ✅ don_thuoc ✅ (Amoxicillin + Paracetamol)
- A-02 (Viêm loét dạ dày): ICD-10 auto_lookup ✅ huyết_áp ✅ don_thuoc deferred (TRAIN-001)
- A-03 (Tăng huyết áp): huyết_áp 170/100 ✅ ly_do '' ✅ (admin filtered) tai_kham '2 tuần' ✅
- Phonetic explosions confirmed TRAIN-001 dependency: Amlodipine, Losartan, Omeprazole, Domperidone

## Blocker / Phụ thuộc bên ngoài
- [TRAIN-001] Drug NER CEER 0.9🔴 — cần 50-100h audio BS thật (PA-006)
- [PA-006] Andy điền `data/audio/dental/ground_truth_dental_template.json` — dental ground truth
- [PA-007] Andy dùng `docs/dev/CHATGPT_CORPUS_PROMPT.md` v2.0 → ChatGPT → 41 scripts → BS review → gửi lại

## Phiên tiếp theo — làm ngay theo thứ tự
1. [PILOT Đà Nẵng] Andy chạy `install.bat` tại phòng khám thật — ghi nhận feedback
2. [BENCH-002] Record 30-50 audio consultations thật → ground truth → CEER thật
3. [PA-007] Andy: copy `docs/dev/CHATGPT_CORPUS_PROMPT.md` v2.0 → ChatGPT → 41 corpus scripts → BS review → gửi Claude
4. [TEST-A04] Test case A-04 (Đái tháo đường) hoặc A-05 (Đau thắt lưng) — tiếp tục real-world NER validation
