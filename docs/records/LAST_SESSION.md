# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260607
## Thời gian: 2026-06-07
## Version: v0.5.0 → v0.5.1

---

## Trạng thái đầu → cuối
v0.5.0 | 232 tests → v0.5.1 | 272 tests PASS | VN-NER-002 DONE + process fixes

---

## Đã hoàn thành

### A. FID-VN-005 — VN-NER-002: VN word-form numbers + L6 VN NER

**Root cause fix cho 0% vital extraction từ PhoWhisper:**
PhoWhisper output "tám mươi" / "một trăm ba mươi trên chín mươi" — regex NER dùng `\d{2,3}` → 0% extract.
L6 lam_sang cũ dùng Canada NER trên MarianMT-translated text → silent entity failure.

**A1. src/core/l1c_ner.py — thêm VN word-to-number normalizer**
- `_normalize_vn_numbers(text)`: 5 bước — BP (trên), decimal (phẩy), rưỡi (+độ), multi-word ints, single+unit
- `_vn_to_int()` + `_vn_tens_int()`: parse "tám lăm"→85, "ba mươi tám"→38, "một trăm ba mươi"→130
- `extract_entities()`: normalize transcript trước khi chạy regex NER
- `_extract_drug_context()`: normalize chỉ context window 20-word (không normalize toàn bộ — tránh position drift)

**A2. src/pipeline/p2_decision/l6_mau15_generator.py — thêm generate_mau15_from_vn_ner()**
- Map `MedicalEntities` (VN dataclass fields) trực tiếp → `form_data` → `generate_benh_an()`
- `generate_mau15()` cũ giữ nguyên (Canada path cho cdha/nha_khoa)
- `ly_do` fallback: lấy symptom đầu tiên nếu `ents.ly_do` rỗng

**A3. src/pipeline/p2_decision/l6_agent.py — lam_sang dùng VN NER**
- `vi_transcript = payload.get("original_text") or original or text`
- Gọi `l1b_drug_correct` + `l1c_ner.extract_entities()` trực tiếp
- Kết quả: TC-001 HA=130/90 ✅, TC-002 nhiet_do=38.5 ✅, TC-003 HA=135/85 ✅

**A4. tests/unit/test_l1c_vn_numbers.py — 40 tests mới**
- TestVnToInt (9 tests): digit forms, alternate, tens, tens+units, 10-19, hundreds, shorthand
- TestNormalizeVnNumbers (16 tests): BP, decimal, rưỡi, standalone, units, digits unchanged, empty
- TestExtractEntitiesVnNumbers (15 tests): FID acceptance criteria TC-001/002/003

**A5. fids/FID-VN-005.md — tất cả acceptance criteria [x]**
- Status: Approved 2026-06-07 | Implemented 2026-06-07 | 272/272 PASS · bandit 0 HIGH/MEDIUM

### B. Process fixes (Andy feedback)

**B1. CLAUDE.md — ĐÓNG PHIÊN 5→6 bước**
- Thêm BƯỚC 2: Update `docs/records/PROJECT_PROGRESS.md`
- Nguyên nhân: PROJECT_PROGRESS.md không có trong close protocol → bỏ sót milestone tracking

**B2. docs/compliance/IMPROVEMENT_PROCESS.md — v1.1→v1.2**
- Section 5 trigger table "Phiên CLOSE": thêm PROJECT_PROGRESS
- Section 6 post-close checklist: thêm bước 4 cho PROJECT_PROGRESS.md (renumber 5→6)

**B3. docs/records/PROJECT_PROGRESS.md — milestone update**
- P0.5.1 VN-NER-002: 5 sub-rows (a→e) với chi tiết implementation
- L1c + L6 rows: cập nhật FID-VN-005 DONE
- Metrics: 232→272 tests, vital extraction fixed
- Lịch sử phiên: SES-20260607 added

---

## Kết quả đo được
- Tests: 232 → **272/272 PASS** (+40 tests VN number normalization)
- bench_ceer --partial tc_001_noi_khoa.wav: vital=True, followup=True ✅
- bench_ceer --partial tc_002_ho_hap.wav: vital=True, followup=True ✅
- TC-001 pipeline: HA=130/90, mach=80.0, tai_kham="Sau 1 tuần"
- TC-002 pipeline: HA=120/80, nhiet_do=38.5, nhip_tho=22.0, tai_kham="Sau 3 ngày"
- TC-003 pipeline: HA=135/85, can_nang=72.0, mach=75.0, tai_kham="Sau 1 tháng"
- bandit: 0 HIGH/MEDIUM ✅
- Process gaps fixed: 2 (close protocol + improvement process)

---

## Blocker / Phụ thuộc bên ngoài
- [PA-006] Andy chưa điền `data/audio/ground_truth.json` → chưa đo CEER thật (nhắc #2)
- Drug detection 0% trên real audio — PhoWhisper transcribes drug names differently from gTTS
  Không phải regression — pre-existing limitation, cần PA-006 ground truth để đánh giá đúng

---

## Phiên tiếp theo — làm ngay theo thứ tự

1. **[CT-005] DEPLOY-001** 🟡 — Windows installer PyInstaller cho BS Đà Nẵng (ưu tiên cao nhất)
   - PyInstaller bundle: app + venv + models pre-cached
   - CONFIG-001: Facility config UI (tên phòng khám, CCHN, khoa)
2. **[GAP-003]** 🟡 — Unit tests `src/pipeline/p3_storage/l8_error_handler.py`
3. **[GAP-004]** 🟡 — Unit tests `src/pipeline/p3_storage/l9a_pdf_export.py`
4. **[CT-006]** 🟢 — Update `data/drug_db.json` — 30 drug interaction pairs
5. **[PA-006]** Andy điền ground truth → `python -X utf8 tools/bench_ceer.py --full`
