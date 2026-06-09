# FID-VN-012 — Doctor Voice Profile (DVP)
# MediVoice VN | Feature Intent Document
# Status: DRAFT — Chờ Andy approve (PA-012)
# Author: Claude | Created: 2026-06-09
# Consensus: Andy + Claude + Grok + GPT + Copilot (4/4 on core — CONS-20260610-004)
# Refs: WIN2_REPORT_20260609.md · CONS-20260610-004.md · BENCH-002b Drug Recall=55.6%LB

---

## 1. WHY — Vấn đề cần giải quyết

### Evidence từ BENCH-002b (2026-06-09)

| Metric | Actual | Gap |
|---|---|---|
| Drug Recall (real BS voice) | 55.6% LB | ≥ 70% target |
| WER HN | 29.3% | ≤ 20% target |
| WER DN/SG | 16.3% ✅ | — |

**Root cause phân tích (4 AI đồng thuận):**

- **LEXICAL gap, không phải acoustic.** ASR transcript đúng nhưng drug name bị garble phonetic
- BS nói "mét phốt min" (Metformin) theo cách đọc của riêng họ → L1b miss
- Pipeline không biết BS này hay nói "xi klo phốt phơ rin" cho Ciprofloxacin
- **Một lần biết → mọi session sau đều chính xác** — đây là learnable pattern

### Problem statement

> Mỗi bác sĩ có cách phát âm thuốc, dialect, và vocabulary pattern riêng.
> Pipeline hiện tại xử lý mọi BS giống nhau → suboptimal với phonetic variations.
> DVP giải quyết bằng cách học từng BS một lần, áp dụng vĩnh viễn.

---

## 2. WHAT — Những thay đổi cần làm

### Architecture: 3 Layers (Option C Phased — 4/4 AI consensus)

```
DVP LAYER 1 — Doctor Metadata (registration, ≤ 2 phút)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MANDATORY (ảnh hưởng chất lượng ngay session 1):
  cchn:              Số chứng chỉ hành nghề (đã có)
  name:              Tên BS (đã có)
  region:            Bắc / Trung / Nam
  primary_specialty: 12 options (xem 2.2)

SELF-REPORTED (optional, cải thiện thêm):
  secondary_specialty: optional
  english_level:     Basic / Intermediate / Good
    → Basic: inject phonetic VN vào Whisper prompt
    → Good: inject INN English name vào Whisper prompt
  speaking_speed:    Chậm / Vừa / Nhanh
    → Điều chỉnh VAD gap_ms ban đầu

KHÔNG HỎI: pitch, volume, clarity → auto-detect từ calibration sau

DVP LAYER 2 — Specialty Vocabulary (auto-load, zero friction)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Primary 70% + Secondary 30% → merge drug list
  Inject vào A1 Whisper prompt_injection (src/core/l1a_asr.py)
  Link vào A3 dialect_norm (src/core/dialect_norm.py region-aware)
  → 0 friction, bắt đầu ngay session 1

DVP LAYER 3 — Personal Drug Alias (passive learning từ L4)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Source: data/corrections/{clinic_id}.jsonl (L4 Correction Capture — đã có)
  Promote rule:
    ≥ 3 corrections cùng alias (drug_ai → drug_bs)
    Phải từ ≥ 2 sessions KHÁC NHAU
    Recency-weighted (session gần đây weight cao hơn)
    Conflict check: alias → 2+ INN khác nhau → reject (ambiguous)
  Human Gate alias (bắt buộc):
    → Thông báo: "Trợ lý học được cách BS đọc [Metformin] là [mét phốt min]"
    → BS confirm YES / NO trước khi activate
    → Luật KCB 2023 Đ.62: BS chịu trách nhiệm mọi mapping
```

### 2.2 — 12 Specialties

| ID | Tên | Lưu ý |
|---|---|---|
| noi_khoa | Nội khoa | Default — broad vocabulary |
| tim_mach | Tim mạch | ACEI, ARB, beta-blocker, statin |
| chan_thuong_chinh_hinh | Chấn thương chỉnh hình | NSAID, opioid, bone drugs |
| tai_mui_hong | Tai Mũi Họng | Vocab khác hoàn toàn noi_khoa |
| san_phu_khoa | Sản phụ khoa | Oxytocin, hormones, contraceptives |
| nhi | Nhi | Liều theo kg — logic khác adults |
| cdha | Chẩn đoán hình ảnh | Contrast agents, imaging terms |
| ngoai | Ngoại | Surgical terms, anesthesia |
| da_lieu | Da liễu | Topical drugs, antihistamines |
| mat | Mắt | Eye drops, ophthalmologic vocab |
| noi_tiet | Nội tiết | Insulin, thyroid, diabetes |
| than_tiet_nieu | Thận tiết niệu | Diuretics, nephrology terms |

### 2.3 — Calibration (Triggered, KHÔNG force)

```
Trigger: sau 3–5 sessions, detect drug X miss liên tục
Prompt: "Trợ lý AI của BS [Tên] thấy [Metformin] bị nghe nhầm 3 lần.
        Muốn tăng độ chính xác không? (5 phút, BS có thể bỏ qua)"
UI: "Trợ lý AI của BS [Tên]" — KHÔNG gọi "Voice Calibration Setup"
Kết quả: record 5–10 câu mẫu → cải thiện phonetic index cho BS này
```

### 2.4 — UX Rules (4/4 AI consensus + Andy insight)

| KHÔNG dùng | PHẢI dùng |
|---|---|
| "Voice Calibration Setup" | "Trợ lý AI của BS [Tên]" |
| "Cấu hình giọng nói" | "Cá nhân hóa trợ lý" |
| "Training model" | "Muốn trợ lý học cách BS đọc [Metformin]?" |
| "Accuracy threshold" | "Tăng độ chính xác — 5 phút, tùy BS" |

**Dragon Medical One model:** BS biết app cần học giọng → tự nguyện train khi frame là "AI trợ lý chuyên biệt của riêng họ".

### 2.5 — Data Schema

```sql
-- Bảng mới: DoctorProfile
CREATE TABLE doctor_profiles (
    cchn            TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    region          TEXT NOT NULL,          -- Bắc/Trung/Nam
    primary_specialty TEXT NOT NULL,        -- 12 options
    secondary_specialty TEXT,
    english_level   TEXT DEFAULT 'Basic',   -- Basic/Intermediate/Good
    speaking_speed  TEXT DEFAULT 'Vừa',     -- Chậm/Vừa/Nhanh
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

-- Bảng mới: DoctorAlias (Layer 3)
CREATE TABLE doctor_aliases (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cchn            TEXT NOT NULL REFERENCES doctor_profiles(cchn),
    alias_text      TEXT NOT NULL,          -- "mét phốt min"
    inn             TEXT NOT NULL,          -- "Metformin"
    session_count   INTEGER DEFAULT 0,      -- số sessions đã confirm
    occurrence_count INTEGER DEFAULT 0,     -- tổng lần xuất hiện
    confirmed_by_bs INTEGER DEFAULT 0,      -- 0=pending, 1=confirmed, -1=rejected
    created_at      TEXT NOT NULL,
    last_seen       TEXT NOT NULL,
    UNIQUE(cchn, alias_text)
);
```

### 2.6 — Integration với pipeline hiện tại

```
A1 src/core/l1a_asr.py:
  get_drugs_by_specialty(specialty) — ĐÃ CÓ
  build_initial_prompt(drug_db, specialty) — ĐÃ CÓ
  → Cần: load DoctorProfile.primary_specialty + pass vào transcribe()
  → Hiện tại: hardcode specialty='noi_khoa' → thay bằng doctor's specialty

A3 src/core/dialect_norm.py:
  normalize_text(text, region) — ĐÃ CÓ
  → Cần: load DoctorProfile.region + pass thay 'north' default

L1b src/core/l1b_drug_correct.py:
  _load_drug_db() — ĐÃ CÓ
  → Cần: inject doctor_aliases vào drug lookup (thêm vào alias map)

src/api/main.py:
  → Cần: load_doctor_profile(doctor_cchn) tại transcribe() start
  → Pass profile vào l1a, l1b, dialect_norm
```

---

## 3. SCOPE

- DVP Layer 1+2: implement trong FID này
- DVP Layer 3 (alias promote): implement sau pilot có ≥5 sessions
- Calibration wizard: Phase 1 (sau pilot)
- Multiple BS per facility: bao gồm trong schema (1 facility nhiều BS)
- Không thay đổi L4 Human Gate logic
- Không thay đổi pipeline L0→L10 frozen states

---

## 4. ACCEPTANCE CRITERIA

| ID | Criteria | Test |
|---|---|---|
| AC-001 | DoctorProfile table tạo đúng schema (cchn PK, region, primary_specialty) | unit test |
| AC-002 | load_doctor_profile(cchn) trả về DoctorProfile hoặc None | unit test |
| AC-003 | transcribe() nhận doctor_profile → pass specialty vào A1 prompt injection | unit test (mock) |
| AC-004 | transcribe() nhận doctor_profile → pass region vào A3 dialect_norm | unit test (mock) |
| AC-005 | Khi profile=None → pipeline hoạt động như cũ (backward compat) | unit test |
| AC-006 | 12 specialties có vocabulary pack (tối thiểu 20 drugs/specialty) | unit test |
| AC-007 | DoctorAlias promote rule: ≥3 corrections + ≥2 sessions → pending | unit test |
| AC-008 | Human Gate alias: BS phải confirm YES/NO trước khi alias active | integration test |
| AC-009 | Registration form: region + primary_specialty bắt buộc | API test |
| AC-010 | 100% existing tests PASS (no regression) | pytest -q |

---

## 5. ESTIMATE

| Phần | LOC | Ghi chú |
|---|---|---|
| DoctorProfile model + DB migration | ~60 | models/ + l7_storage |
| 12 specialty vocab packs | ~150 | data/specialty_vocab/ JSON files |
| load_doctor_profile() + pipeline injection | ~80 | main.py + l1a_asr.py + dialect_norm.py |
| DoctorAlias promote logic | ~100 | new module: src/core/dvp_alias.py |
| Registration API endpoint | ~60 | POST /api/doctors |
| Tests (AC-001 → AC-010) | ~100 | tests/unit/test_dvp.py |
| **Tổng** | **~550 LOC** | Tầng 1 — cần FID ✅ |

**Build order:** L1 (2–3 ngày) → L2 (1–2 ngày) → L3 (1 tuần sau pilot data)

---

## 6. KHÔNG làm trong FID này

- Calibration wizard UI (âm thanh record) → Phase 1
- Tự động detect region từ audio → Phase 1
- Multiple profiles per BS (role variants) → Phase 2
- Analytics dashboard alias usage → Phase 1

---

## 7. PERFORMANCE PREDICTION (4-AI consensus)

| Giai đoạn | Drug Recall | WER HN | Timeline |
|---|---|---|---|
| Hiện tại v0.10.1 | ~55–65% | 29.3% | — |
| Sau DVP L1+2 (Session 1) | ~65–75% | ~26% | Ngay session đầu |
| Sau DVP L3 mature | ~80–90% | ~26% | Session 10+ |
| Sau TRAIN-001 + DVP | ~90%+ | <20% | Phase 1 |

---

## 8. DECISION NEEDED — Andy approve

**Q1**: Approve implement DVP Layer 1+2 ngay?
- **Yes** → Claude implement, ~550 LOC, 10 ACs
- **No / Later** → defer

**Q2**: 12 specialties có đủ không? Cần thêm specialty nào cho pilot Đà Nẵng?

**Q3**: DoctorAlias Human Gate — form text nào BS sẽ thấy khi confirm?
- Option A: "Trợ lý học được: [mét phốt min] = Metformin. Xác nhận?"
- Option B: "Phát âm mới được học: [mét phốt min] → Metformin (3 lần). Đồng ý không?"

---

*FID-VN-012 | DRAFT 2026-06-09 | Claude*
*Consensus: WIN2_REPORT_20260609.md + CONS-20260610-004.md*
*Evidence: BENCH-002b 55.6% Drug Recall LB · BENCH-002a Drug=0.967 synthetic*
