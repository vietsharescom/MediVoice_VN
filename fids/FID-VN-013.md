# FID-VN-013 — Voice Calibration UX + Drug Pronunciation Wizard + VTLN
# MediVoice VN | Feature Intent Document
# Status: DRAFT — Chờ Andy approve
# Author: Claude | Created: 2026-06-10 | Revised: 2026-06-10 (v2 — mở rộng scope)
# Consensus: 6-AI (Claude+Groq+Copilot+ChatGPT+AI#4+Grok-revised) — CONS-20260610-005, 85% confidence
# Refs: CONS-20260610-005.md · FID-VN-012.md (DVP) · CT-014 · PA-014 · PA-015

---

| Field | Value |
|---|---|
| FID ID | FID-VN-013 |
| Layer | Frontend (PWA) + L0 (audio preprocessing, additive) + DB (1 column thêm) |
| LOC estimate | ~430 LOC (~370 chắc chắn + ~60 VTLN điều kiện theo AC-013) |
| Risk level | LOW |
| Created | 2026-06-10 |
| Approved by | — |
| Approved date | — |

> **v2 (2026-06-10)**: Mở rộng theo yêu cầu Andy + review Grok — thêm
> **Drug Pronunciation Enrollment Wizard** (Section 2.4) và **VTLN** (Section 2.5).
> LoRA per-speaker (Option B "full personalization") vẫn defer → Phase 1 Research Track
> (Section 6) — KHÔNG đổi.

---

## 1. WHY — Vấn đề cần giải quyết

BS lần đầu dùng AI voice scribe không có phản hồi gì trong lúc nói — không biết AI có
"nghe" không, có nói quá nhỏ/quá xa mic không, có nói quá nhanh không, môi trường có ồn
không. Thiếu feedback này làm giảm trust và có thể gây lỗi thu âm (mic quá xa → audio
chất lượng kém → WER cao) mà BS không biết để sửa ngay tại chỗ.

5/5 AI (CONS-20260610-005) đồng thuận: giải quyết phần UX bằng **Option A —
visualization + behavioral hints**, KHÔNG phải Option B (per-speaker LoRA
personalization — defer sang "Phase 1 Research Track", xem Section 6).

### Bổ sung (Andy, 2026-06-10) — 2 vấn đề kỹ thuật cụ thể chưa được cover bởi Option A

1. **Phát âm thuốc tiếng Anh khác nhau giữa các BS**: 1 BS đọc "Amlodipine" theo kiểu
   tiếng Anh ("am lo di phin"), BS khác đọc kiểu Việt hoá ("âm lô phin") — ASR + L1b
   drug correction hiện tại có thể miss 1 trong 2 cách đọc → Drug Recall thấp
   (55.6% LB, BENCH-002b).
2. **Đặc trưng giọng nói (pitch/tần số) khác nhau giữa các BS** — Andy muốn hệ thống
   "nghe thử 1 câu" rồi tự điều chỉnh layer xử lý cho phù hợp với từng BS.

Sau khi Claude phân tích + Grok review (xem CONS-20260610-005.md addendum), 2 vấn đề
này tách thành **2 giải pháp risk thấp, KHÔNG phải LoRA**:

- Vấn đề (1) → **Drug Pronunciation Enrollment Wizard** (Section 2.4) — text-level
  alias dictionary, dùng lại schema `doctor_aliases` đã có từ FID-VN-012
- Vấn đề (2) → **VTLN (Vocal Tract Length Normalization)** (Section 2.5) — kỹ thuật
  signal processing cổ điển, output chỉ là 1 scalar/BS, KHÔNG cần train/LoRA/GPU

---

## 2. WHAT — Scope v1 (Option A, 5-AI consensus)

### 2.1 — Client-side, real-time trong lúc ghi âm (Web Audio API, KHÔNG đổi backend)

| Hạng mục | Mô tả | Nguồn |
|---|---|---|
| Waveform realtime | Canvas vẽ waveform từ `AnalyserNode` trong lúc ghi | Mới (FE only) |
| Mic level indicator | Thanh VU-meter từ RMS amplitude | Mới (FE only) |
| Speaking speed indicator | Ước lượng tốc độ nói từ tần suất voice/silence transitions | Mới (FE only) |
| Pause detection (UI) | Đánh dấu khoảng lặng > 1.5s trên waveform | Mới (FE only) — KHÔNG liên quan A2-VAD backend (CT-019), đây là hiển thị client-side độc lập |
| Recording quality score | Heuristic: clipping (peaks > 0.95), low signal (RMS < ngưỡng), noise floor | Mới (FE only) |
| Behavioral hints | "Nói chậm hơn một chút" / "Micro quá xa" / "Môi trường có tiếng ồn" — hiển thị khi quality score thấp | Mới (FE only) |

### 2.2 — Dialect badge (đã có backend, chỉ cần hiển thị)

`/transcribe` đã trả về `dvp_region` + `dialect_subs` (`src/api/main.py:188-189`), và
`/api/dialect-check` đã trả về `detect_region()` (`src/api/main.py:692-713`). v1 chỉ cần
hiển thị badge "Vùng miền phát hiện: {region}" trong màn hình review (L4) — KHÔNG cần
thêm endpoint hay đổi pipeline.

### 2.3 — Tooltip / disclaimer (UX rule — AI #4)

Hiển thị 1 lần (dismissible) khi BS bật tính năng lần đầu:
> "Đây là hiển thị trực quan giúp BS theo dõi chất lượng ghi âm. AI **không** tự động
> thay đổi cách xử lý theo giọng nói của BS."

Lý do: tránh BS hiểu nhầm "AI đang tự học/adapt theo giọng tôi" (Option B chưa làm) —
nhất quán với Absolute Rule #8 (UI hiển thị "AI tạo nháp — BS chịu trách nhiệm").

> **Lưu ý**: Sau khi thêm Section 2.4 + 2.5, disclaimer này cần điều chỉnh — hệ thống
> CÓ điều chỉnh nhẹ (VTLN warp + drug alias) sau enrollment, nhưng KHÔNG phải "AI tự
> học liên tục trong mọi session" (đó vẫn là Option B/LoRA, chưa làm). Text đề xuất:
> "AI dùng 1 lần ghi âm mẫu để tinh chỉnh nhẹ (âm lượng/tần số) và học cách BS đọc tên
> thuốc — BS có thể làm lại hoặc bỏ qua bất cứ lúc nào trong Cài đặt."

---

### 2.4 — Drug Pronunciation Enrollment Wizard (MỚI — risk thấp, dùng schema có sẵn)

**Mục tiêu**: Giải quyết Drug Recall gap (55.6%LB → 70% target) bằng cách chủ động học
cách BS đọc tên thuốc tiếng Anh/INN, thay vì chờ passive learning từ L4 corrections
(FID-VN-012 Layer 3 — cần ≥3 corrections × ≥2 sessions, chậm).

**Flow**:
```
1. Trigger: lúc đăng ký DoctorProfile (FID-VN-012) hoặc "Cài đặt → Luyện đọc thuốc"
2. Lấy 15-20 thuốc phổ biến nhất theo primary_specialty (specialty_vocab packs,
   FID-VN-012 §2.2 — đã có data)
3. UI hiển thị từng thuốc (vd "Amlodipine") → BS bấm ghi âm, đọc tên thuốc 1 lần
4. PhoWhisper transcribe đoạn ghi (reuse /transcribe pipeline, KHÔNG qua L1c/L4 —
   chỉ cần raw transcript)
5. So sánh transcript với INN đã biết trước (ground truth = thuốc đang yêu cầu đọc):
   - Khớp → bỏ qua, không tạo alias thừa
   - Khác (vd transcript="âm lô phin", INN="Amlodipine") → propose alias
6. BS xem preview alias được đề xuất → Confirm / Sửa thủ công / Bỏ qua
   (Human Gate — tái dùng UI confirm từ FID-VN-012 §2.5 DoctorAlias)
7. Confirmed alias → INSERT vào doctor_aliases với confirmed_by_bs=1,
   session_count=1, occurrence_count=1 (KHÁC passive flow — bypass "≥3 corrections"
   promote rule vì ground truth đã biết chắc chắn lúc enrollment)
8. Audio enrollment → purge ngay sau transcribe (giống mọi audio khác, L0 purge_audio())
```

**Fallback**: nếu BS đọc không rõ / ASR lỗi nhiều lần → nút "Bỏ qua thuốc này, để hệ
thống học dần qua L4 corrections" (quay về passive flow FID-VN-012 Layer 3).

**Risk**: THẤP — `doctor_aliases` chỉ là text mapping (alias_text → INN), KHÔNG phải
model weights/voice fingerprint → KHÔNG coi là biometric data theo NĐ13/2023 (đồng
thuận Grok + 4/5 AI trước đó cho LoRA, ngược lại với text alias).

#### 2.4.1 — Kiến trúc alias: `global_aliases` + `doctor_overrides` (bổ sung — ChatGPT review)

**Vấn đề**: nếu mỗi BS có alias dictionary riêng hoàn toàn trong `doctor_aliases`, khi
scale lên 50-100 BS sẽ có 50-100 dictionary gần giống nhau (vd "am lo đi pin" / "âm lô
đi phin" / "am lô đip pin" đều → Amlodipine) — khó maintain, alias tốt của BS A không
giúp ích BS B.

**Giải pháp 2 tầng**:
```
Drug Dictionary (drug_db.json — đã có)
        ↓
Global Alias Layer (alias phổ biến, học từ NHIỀU BS — bảng mới: drug_aliases_global)
        ↓
Doctor Override Layer (doctor_aliases — đã có, FID-VN-012 — chỉ case đặc biệt/hiếm)
        ↓
L1b drug correction lookup
```

Lookup order tại L1b: `doctor_aliases` (theo `cchn`) → `drug_aliases_global` →
`drug_db.json` base.

**Promote rule global**: 1 alias xuất hiện ở `doctor_aliases` của ≥3 BS KHÁC NHAU
(không cần cùng clinic) → promote lên `drug_aliases_global` (admin/Andy review trước
khi promote — KHÔNG tự động, vì ảnh hưởng toàn hệ thống).

**Schema mới (additive, không đổi `doctor_aliases`)**:
```sql
CREATE TABLE IF NOT EXISTS drug_aliases_global (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    alias_text  TEXT NOT NULL UNIQUE,
    inn         TEXT NOT NULL,
    source_count INTEGER DEFAULT 1,   -- số BS distinct đã có alias này
    promoted_by TEXT,                  -- "andy" hoặc "auto" (luôn "andy" cho v1)
    created_at  TEXT NOT NULL
);
```

**v1 scope**: implement `doctor_aliases` (per-BS, từ wizard 2.4) trước — đây là phần
"chắc chắn" trong estimate (~170 LOC). `drug_aliases_global` + promote rule là
**optional/Phase 1.5** (không block v1, vì cần ≥3 BS pilot dùng wizard trước mới có dữ
liệu để promote — hiện pilot chỉ có 1-2 BS).

**Risk**: THẤP — vẫn là text mapping, chỉ thêm 1 bảng global (không có `cchn`/PII) +
human review trước khi promote.

---

### 2.5 — VTLN (Vocal Tract Length Normalization) — MỚI, signal processing only

**Mục tiêu**: "Tinh chỉnh layer xử lý theo đặc trưng tần số giọng từng BS" — đúng ý
Andy, nhưng bằng kỹ thuật signal processing cổ điển (không train/LoRA).

**Cơ chế**:
```
1. Trong cùng phiên enrollment (Section 2.4) hoặc 1 câu mẫu riêng (~10-15s):
   phân tích pitch/formant frequency của BS (librosa.pyin hoặc praat-parselmouth)
2. Tính 1 hệ số "warp factor" (~0.8-1.2, scalar) — so với baseline trung tính
3. Lưu vào doctor_profiles.vtln_warp_factor (cột mới, REAL DEFAULT 1.0)
4. Tại L0 normalize (src/core/l0_normalize.py), TRƯỚC khi đưa vào PhoWhisper:
   áp frequency warping lên audio theo warp_factor (librosa.effects hoặc
   torchaudio.functional — warp tần số theo trục mel/Hz)
5. Nếu doctor_profile=None hoặc warp_factor=1.0 → audio không đổi (backward compat,
   giống AC-005 của FID-VN-012)
```

**Cần research/POC trước khi implement chính thức** (đánh dấu RESEARCH trong
Acceptance Criteria):
- Test compatibility: warping 16kHz mono audio có làm hỏng input format PhoWhisper
  không? (PhoWhisper expect 16kHz mel spectrogram chuẩn — warp factor lệch nhiều có
  thể phản tác dụng)
- Test trên 2-3 audio pilot có sẵn (`data/audio/`) — đo WER trước/sau warp, threshold:
  CHỈ enable nếu WER giảm ≥3% relative, nếu không → để `vtln_warp_factor=1.0` mặc định
  (no-op) và ghi nhận "không đủ evidence", không rollout

**Risk**: THẤP — output là 1-2 số thực (scalar), không encode đặc trưng giọng dạng có
thể dùng để nhận dạng/xác thực danh tính → 6/6 AI (bao gồm Grok review) đồng ý KHÔNG
coi là biometric data theo NĐ13/2023.

### Input / Output / Side effects

```
Input:  MediaStream từ navigator.mediaDevices.getUserMedia() (đã có, dùng lại)
Output: - Canvas waveform + VU meter + speed/quality indicators (UI only)
        - Behavioral hint text (UI only, không lưu)
        - Dialect badge (đọc field có sẵn từ /transcribe response)
Side effects: KHÔNG — không lưu thêm dữ liệu, không đổi audio pipeline, không train
              gì, không thêm bảng DB mới
```

---

## 3. HARD CONSTRAINTS

- Section 2.1-2.3 (waveform/UX): KHÔNG đổi pipeline L0→L10 (FROZEN) — client-side
  rendering + đọc field response đã tồn tại
- Section 2.4 (Drug Wizard): chỉ thêm dữ liệu vào `doctor_aliases` (schema có sẵn từ
  FID-VN-012, không tạo bảng mới) — KHÔNG lưu raw audio enrollment (purge ngay sau
  transcribe, giống mọi audio khác)
- Section 2.5 (VTLN): thêm 1 cột `vtln_warp_factor` vào `doctor_profiles` (additive
  migration, default=1.0=no-op) — áp dụng tại L0 normalize TRƯỚC PhoWhisper, KHÔNG đổi
  cấu trúc pipeline L0→L10 (vẫn 1 input → 1 output ở L0, chỉ thêm 1 transform có thể
  tắt qua warp_factor=1.0)
- KHÔNG liên quan CT-019 (A2-VAD backend regression) — pause detection (2.1) là
  client-side waveform analysis cho mục đích hiển thị, độc lập với
  `vad_chunk_audio()` (`src/core/l0_normalize.py:78`)
- TRAIN-001 (ưu tiên #1, CT-028) không bị ảnh hưởng — VTLN/Drug Wizard chạy trên CPU,
  0 GPU resource, KHÔNG train/fine-tune model nào
- L4 Human Gate không đổi — alias từ Drug Wizard vẫn cần BS confirm (Section 2.4 step 6)

---

## 4. ACCEPTANCE CRITERIA

| ID | Criteria | Test |
|---|---|---|
| AC-001 | Waveform canvas vẽ realtime trong lúc `mediaRecorder.state === 'recording'` | manual browser test |
| AC-002 | Mic level indicator phản ánh đúng RMS amplitude (im lặng → gần 0, nói to → cao) | manual browser test |
| AC-003 | Pause > 1.5s hiển thị marker trên waveform | manual browser test |
| AC-004 | Recording quality score tính đúng 3 tiêu chí: clipping / low signal / noise floor | unit test (JS, pure function — tách riêng module testable) |
| AC-005 | Behavioral hint hiển thị đúng theo quality score (vd score thấp do low signal → "Micro quá xa") | unit test |
| AC-006 | Dialect badge hiển thị `dvp_region` từ `/transcribe` response trong màn L4 review | manual browser test |
| AC-007 | Tooltip disclaimer hiển thị lần đầu, dismissible, lưu trạng thái dismiss trong `localStorage` | manual browser test |
| AC-008 | KHÔNG có network call mới ngoài enrollment wizard (2.4), KHÔNG có dữ liệu waveform/mic level (2.1) nào được gửi/lưu | code review |
| AC-009 | 100% existing tests PASS (no regression) | `pytest tests/ -q` |
| AC-010 | Drug Wizard: transcript khác INN ground truth → propose alias đúng `(alias_text, inn)`; transcript khớp → KHÔNG tạo alias | unit test |
| AC-011 | Drug Wizard: alias confirmed qua wizard → `confirmed_by_bs=1, session_count=1` ngay (khác passive flow cần ≥3×≥2sessions) | unit test |
| AC-012 | Drug Wizard: audio enrollment bị purge ngay sau transcribe (gọi `purge_audio()`) | unit test |
| AC-013 (RESEARCH) | VTLN POC: đo WER trước/sau warp trên ≥2 audio pilot — chỉ tiếp tục implement L0 integration nếu WER giảm ≥3% relative | research report (không phải code) |
| AC-014 | `doctor_profiles.vtln_warp_factor` default=1.0 → L0 normalize output KHÔNG đổi so với hiện tại (backward compat) | unit test |

---

## 5. ESTIMATE

| Phần | LOC | Ghi chú |
|---|---|---|
| Waveform canvas + AnalyserNode wiring | ~70 | `src/api/static/index.html` `<script>` |
| Mic level / speed / pause / quality score (pure JS functions) | ~80 | tách thành module riêng để unit test được (`src/api/static/js/audio_quality.js`) |
| Behavioral hints + tooltip disclaimer | ~30 | `src/api/static/index.html` |
| Dialect badge (đọc field có sẵn) | ~15 | `src/api/static/index.html` |
| Tests (AC-004, AC-005) | ~25 | `tests/unit/test_audio_quality.py` (hoặc JS test runner nếu có) |
| Drug Pronunciation Wizard UI (đọc thuốc, ghi âm, preview alias, confirm) | ~80 | `src/api/static/index.html` |
| Drug Wizard backend endpoint (`POST /api/doctors/{cchn}/pronunciation-enroll`) | ~50 | `src/api/main.py` — reuse transcribe + alias insert logic FID-VN-012 |
| Tests (AC-010, AC-011, AC-012) | ~40 | `tests/unit/test_dvp_wizard.py` |
| VTLN POC script (research, không merge vào pipeline nếu fail AC-013) | ~30 | `scripts/vtln_poc.py` — chạy offline, đo WER |
| VTLN L0 integration (CHỈ NẾU AC-013 pass) | ~20 | `src/core/l0_normalize.py` + migration cột `vtln_warp_factor` |
| Test (AC-014) | ~10 | `tests/unit/test_l0_normalize.py` |
| **Tổng** | **~430 LOC** | (~370 LOC chắc chắn + ~60 LOC VTLN L0 integration điều kiện theo AC-013) |

---

## 6. KHÔNG làm trong FID này — Option B "Phase 1 Research Track"

> Lưu ý: Drug Pronunciation Wizard (2.4) và VTLN (2.5) **KHÔNG phải** Option B —
> đây là 2 giải pháp risk thấp mới được thêm vào v2 (xem Section 1). Chỉ
> **per-speaker LoRA adapter** (model fine-tuning thật sự) mới defer dưới đây.

Per-speaker LoRA adapter (per CONS-20260610-005, 5/5 AI đồng thuận defer, Grok review
v2 xác nhận lại):

**Gating conditions để mở lại Option B (TẤT CẢ phải đạt):**
1. TRAIN-001 hoàn tất (PhoWhisper fine-tuned trên 50-100h audio thật)
2. Có baseline WER đo theo từng BS (per-doctor)
3. Chứng minh được speaker variance là nguồn lỗi LỚN (không phải base model issue)
4. ≥50-100h audio thật đã thu thập

**Khi mở lại, cần thêm trước khi implement:**
- Ý kiến luật sư VN: LoRA adapter weights có phải "dữ liệu sinh trắc học" theo
  NĐ13/2023 + Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 không (4/5 AI giả định CÓ)
- Nếu CÓ → consent riêng (không gộp consent chung) + DPIA + cơ chế BS xoá adapter
- Đo PWA offline init-time impact khi load adapter theo `doctor_id`
- DoctorProfile schema (`doctor_profiles` table, FID-VN-012) đã có `cchn` PRIMARY KEY
  → có thể mở rộng thêm field `lora_adapter_path` khi cần, KHÔNG cần làm gì bây giờ

**OWNER QUESTION (PA-014, không gấp — trả lời trước khi TRAIN-001 xong):**
> "Sau khi TRAIN-001 giảm WER xuống mức chấp nhận được cho ĐA SỐ bác sĩ, Andy có còn
> muốn đầu tư personalization theo từng BS (Option B) hay giữ triết lý universal
> model?"

---

## 7. DECISION NEEDED — Andy approve

**Q1 (owner question, theo Grok review)**: Anh muốn Phase 0 pilot ưu tiên gì cho
Voice Calibration?
- (a) Chỉ UI waveform + dialect + VAD (Section 2.1-2.3, Option A gốc, ~195 LOC)
- (b) (a) + Drug Pronunciation Wizard (Section 2.4, +~170 LOC) — **đề xuất: chọn cái
  này**, risk thấp, win nhanh cho Drug Recall
- (c) (b) + VTLN (Section 2.5, +~60 LOC, có gate AC-013 — chỉ implement L0 integration
  nếu POC cho thấy WER giảm ≥3%)
- (d) Full personalization (LoRA) ngay — KHÔNG khuyến nghị (xem Section 6, defer)

**Khuyến nghị Claude**: (c) — cả 3 phần đều risk thấp/offline/không vướng TRAIN-001,
VTLN có gate nghiên cứu trước (AC-013) nên không tốn effort nếu không hiệu quả.

**Q2**: Vị trí UI cho waveform/indicators (2.1) — ngay trên record button (Doctor
Screen) hay tab riêng "Chất lượng ghi âm"? (đề xuất: ngay trên record button)

**Q3**: Drug Pronunciation Wizard (2.4) — chạy lúc đăng ký DoctorProfile (bắt buộc 1
lần) hay optional trong "Cài đặt" (BS có thể bỏ qua/làm sau)? (đề xuất: optional, theo
nguyên tắc "KHÔNG force" của FID-VN-012 §2.3)

---

*FID-VN-013 | IMPLEMENTED v2 2026-06-10 | Claude*
*Consensus: CONS-20260610-005.md (8-AI, 85% confidence — Grok + ChatGPT + AI#5 reviewed v2 scope)*
*Option B (LoRA) deferred → Phase 1 Research Track (gating conditions Section 6)*

## STATUS (2026-06-10) — Implemented, chờ Andy review (PA-015)

- Q1: (c) full 3-layer — DONE
- Q2: waveform/mic level đặt trong card "Ghi âm", ngay dưới nút record — DONE
- Q3: Drug Pronunciation Wizard = optional, nút "🎓 Luyện đọc thuốc" trong DVP
  greeting card (Cài đặt) — DONE
- Q4 (`global_aliases`+`doctor_overrides`, §2.4.1): KHÔNG implement — Phase 1.5

| Section | Trạng thái | Files |
|---|---|---|
| 2.1-2.3 Visualization | ✅ DONE | `src/api/static/index.html`, `src/api/static/js/audio_quality.js` |
| 2.4 Drug Pronunciation Wizard | ✅ DONE | `src/core/l7_storage.py` (`add_confirmed_alias`), `src/api/main.py` (3 endpoints), `src/api/static/index.html` (wizard modal) |
| 2.5 VTLN | ⏳ RESEARCH module xong, AC-013 POC CHƯA chạy (cần audio + ground truth transcript — CT-035) | `src/core/vtln.py`, `scripts/vtln_poc.py` |

Tests: `tests/unit/test_dvp_wizard.py` (9), `tests/unit/test_audio_quality.py` (11),
`tests/unit/test_vtln.py` (6) — tổng 852/852 PASS, bandit 0 HIGH/0 MEDIUM.
