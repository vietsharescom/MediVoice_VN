# FID-VN-014 — Voice Calibration Lab (3-Part Standardized Test) + AI Avatar Mirror
# MediVoice VN | Feature Intent Document
# Status: DRAFT — Chờ Andy approve
# Author: Claude | Created: 2026-06-11
# Refs: FID-VN-012 (DVP) · FID-VN-013 (Voice Calibration UX v2, đã DONE) · CT-024 (pilot consent exception precedent) · PA-014

---

| Field | Value |
|---|---|
| FID ID | FID-VN-014 |
| Layer | Frontend (PWA) + DoctorProfile (DB, additive) — KHÔNG đổi pipeline L0→L10 |
| LOC estimate | ~280 LOC (3-part test) + ~150-250 LOC (avatar, conditional theo provider) |
| Risk level | LOW (3-part test) / MEDIUM-HIGH (avatar — cloud API, ảnh khuôn mặt BS) |
| Created | 2026-06-11 |
| Approved by | — |
| Approved date | — |

---

## 1. WHY

Andy đề xuất (2026-06-11): biến màn "Cài đặt giọng nói" (FID-VN-013 §2.4 Drug
Pronunciation Wizard, hiện chỉ có 1 phần) thành một **"Voice Calibration Lab"** đầy đủ
3 phần, có visualization ấn tượng để BS thấy "AI assistant = phiên bản chính họ" —
tăng motivation calibrate (đúng insight đã ghi nhận: BS pilot VN dễ chấp nhận
calibration khi frame là "trợ lý cá nhân", kiểu Dragon Medical One).

3 phần test, mỗi phần có cơ sở khoa học/kỹ thuật riêng (xem FID-VN-013 §6 addendum
2026-06-11 cho phân tích kỹ thuật gốc):

1. **Vùng miền** — đọc 1 câu/đoạn ngắn → `detect_region()` (đã có,
   `src/core/dialect_norm.py:311`) → xác định Bắc/Trung(Huế)/Nam → áp
   `DIALECT_MAP` tương ứng (đã có, 200+ entries, kể cả "mô răng rứa" Huế/Trung,
   "n"↔"l" Bắc, "ơ"↔"a" Nam qua phonetic_variants trong drug_db).
2. **Bài đọc chuẩn (ngắt nghỉ / cao độ / tốc độ)** — đọc 1 đoạn văn bản cố định
   (chuẩn hoá, ~30-45s) → đo:
   - Speaking rate (từ/giây) → `speaking_rate_class` (chậm/vừa/nhanh)
   - Pause pattern (số lần + độ dài ngắt, dùng `detectPauses()` đã có trong
     `audio_quality.js`) → `pause_style`
   - Pitch median → `vtln_warp_factor` qua `estimate_warp_factor()` đã có
     (`src/core/vtln.py`) — **vẫn giữ gate AC-013 (≥3% relative WER), KHÔNG tự
     động bật VTLN nếu chưa có evidence**
3. **Thuật ngữ thuốc/chuyên môn vay mượn** — ✅ ĐÃ XONG, Drug Pronunciation Wizard
   (FID-VN-013 §2.4) — tái sử dụng nguyên trạng, chỉ cần đưa vào chung 1 luồng UI
   "Voice Calibration Lab" thay vì nút riêng trong DVP greeting.

**AI Avatar Mirror** (đề xuất thêm, Andy 2026-06-11): ảnh BS tự upload → tạo avatar
"mấp môi nói" theo audio thử giọng, hiển thị song song bên trái màn hình trong lúc làm
3 bài test trên (bên phải = phân tích giọng/kết quả).

---

## 2. WHAT

### 2.1 — Phần 1: Region Detection Test

```
Input:  BS đọc 1 câu mẫu ngắn (~10-15s) chứa từ khóa đặc trưng vùng miền
        (vd câu có "rứa"/"mô" cho Trung, hoặc câu trung tính để so sánh)
Output: - region detected (central/northern/southern) qua detect_region()
        - badge hiển thị: "Phát hiện giọng: Miền Trung — sẽ áp dụng từ điển
          phương ngữ Trung (vd 'mô răng rứa' → chuẩn hoá tự động)"
        - lưu vào doctor_profiles.region (cột đã có, FID-VN-012)
Side effects: KHÔNG lưu audio (purge ngay sau transcribe, giống mọi luồng khác)
```

### 2.2 — Phần 2: Standardized Reading Passage Test

```
Input:  BS đọc 1 đoạn văn bản cố định hiển thị trên màn hình (~80-120 từ,
        soạn sẵn — câu chuyện trung tính, đa dạng âm tiết tiếng Việt, tương tự
        triết lý "Rainbow Passage" dùng trong speech pathology nhưng bằng
        tiếng Việt + có lồng vài thuật ngữ y khoa phổ biến)
Xử lý:  - PhoWhisper transcribe (reuse /transcribe, không qua L1c/L4)
        - audio_quality.js: detectPauses(), computeRMS() → pause_style,
          speaking_rate (so từ transcript / thời lượng audio)
        - vtln.py: estimate_warp_factor() → lưu vtln_warp_factor (KHÔNG áp
          dụng vào pipeline — vẫn no-op cho đến AC-013 pass)
Output: - Card kết quả: "Tốc độ nói: Vừa | Ngắt nghỉ: 3 lần, TB 0.8s |
          Tần số giọng: Trung bình (warp=1.02, chưa áp dụng — nghiên cứu)"
        - Lưu speaking_rate_class + pause_style vào doctor_profiles
          (2 cột mới, additive migration, default NULL)
Side effects: audio purge ngay sau xử lý
```

### 2.3 — Phần 3: Drug/Term Pronunciation Wizard

✅ Đã xong (FID-VN-013 §2.4) — chỉ cần đưa vào chung flow "Voice Calibration Lab"
(UI re-organize, KHÔNG đổi logic backend).

### 2.4 — AI Avatar Mirror (CONDITIONAL — xem Section 3 Decision)

```
Input:  Ảnh chân dung BS (upload, lưu local/base64 trong browser hoặc
        doctor_profiles — KHÔNG gửi cloud nếu chọn Option A)
Output: Avatar "mấp môi" theo audio realtime trong lúc làm 3 bài test trên
```

**2 lựa chọn kỹ thuật** (xem Section 3 — Andy đã cho phép bypass Rule #4 lúc pilot
nếu cần, nhưng vẫn cần chọn hướng cụ thể vì ảnh hưởng LOC/provider/chi phí):

- **Option A (local, AC #1)**: Canvas/CSS — ảnh tĩnh + overlay hình miệng
  đơn giản (ellipse) co giãn theo RMS amplitude realtime. 0 cloud, 0 chi phí,
  ảnh không rời máy BS (trừ khi BS chủ động lưu vào profile).
- **Option B (cloud lip-sync thật)**: gọi API ngoài (D-ID/HeyGen-style) —
  cần (1) chọn provider cụ thể + API key, (2) consent riêng (giống CT-024
  precedent — pilot exception cho Rule #4, ghi ADR vào `docs/records/DECISIONS.md`
  + cập nhật `docs/compliance/RISK_REGISTER.md`), (3) chi phí/request,
  (4) latency — không realtime được, avatar sẽ là video render sau khi ghi xong
  (không phải "mấp môi khi đang nói").

---

## 3. DECISION NEEDED — Andy approve

**Q1**: 3-part test (Section 2.1-2.3) — risk THẤP, tái dùng module có sẵn
(`detect_region`, `audio_quality.js`, `vtln.py`, Drug Wizard). Đề xuất: APPROVE,
implement trước.

**Q2 (Avatar)**: Andy nói "có consent bypass Rule #4 lúc thử nghiệm" — xác nhận:
- Chọn **Option B (cloud lip-sync)**? Nếu có, cần Andy:
  (a) chọn provider cụ thể (D-ID / HeyGen / khác — Claude không tự chọn vì khác
      nhau về giá, ToS, khả năng tích hợp),
  (b) xác nhận theo đúng quy trình CT-024: ghi ADR vào `docs/records/DECISIONS.md`
      + `docs/compliance/RISK_REGISTER.md` (pilot-only exception, ảnh BS gửi ra
      provider ngoài VN),
  (c) văn bản consent riêng cho việc dùng ảnh khuôn mặt BS (khác consent DPA hiện
      tại — DPA hiện chưa cover biometric/facial data)
- Hay Option A (local canvas) trước cho v1 — nâng cấp Option B sau khi có
  provider quyết định + giấy tờ consent? (Khuyến nghị Claude — Option A không
  block gì, có thể ship ngay cùng 3-part test; Option B làm riêng FID khi giấy tờ
  sẵn sàng)

**Q3**: Vị trí UI — "Voice Calibration Lab" là 1 màn riêng (wizard 3 bước) hay
mở rộng trong "Cài đặt → 🎓 Luyện đọc thuốc" hiện có?

---

## 4. HARD CONSTRAINTS

- KHÔNG đổi pipeline L0→L10 (additive: 2 cột DB mới `speaking_rate_class`,
  `pause_style` trong `doctor_profiles`, default NULL/no-op)
- VTLN vẫn giữ nguyên gate AC-013 (FID-VN-013) — `vtln_warp_factor` đo nhưng
  KHÔNG áp dụng cho đến khi có evidence
- Avatar Option B (nếu chọn): PHẢI có ADR + consent riêng trước khi code (theo
  precedent CT-024) — KHÔNG implement trước khi giấy tờ sẵn sàng
- L4 Human Gate không đổi
- TRAIN-001 (ưu tiên #1) không bị ảnh hưởng — toàn bộ FID này là CPU/frontend

---

## 5. ACCEPTANCE CRITERIA

| ID | Criteria | Test |
|---|---|---|
| AC-001 | Region test: đọc câu mẫu central → `detect_region()` trả "central" → badge hiển thị đúng | unit test (đã có detect_region, viết test cho UI flow) |
| AC-002 | Reading passage test: tính đúng speaking_rate_class từ word_count/duration | unit test |
| AC-003 | Reading passage test: pause_style tính từ `detectPauses()` (đã có) | unit test |
| AC-004 | vtln_warp_factor đo được, lưu DB, KHÔNG áp dụng vào L0 (vẫn no-op) | unit test |
| AC-005 | doctor_profiles 2 cột mới default NULL → audio pipeline output không đổi | unit test (backward compat) |
| AC-006 | Audio enrollment 3 phần purge ngay sau xử lý | unit test |
| AC-007 (avatar, conditional) | Theo Option đã chọn — TBD sau Q2 | TBD |
| AC-008 | 100% existing tests PASS | `pytest tests/ -q` |

---

## 6. ESTIMATE

| Phần | LOC | Ghi chú |
|---|---|---|
| Region test UI + wiring | ~50 | reuse `detect_region`, `/api/dialect-check` |
| Reading passage UI + scoring | ~120 | đoạn văn mẫu + speaking_rate/pause/pitch display |
| Backend: 2 cột DB mới + endpoint lưu kết quả | ~60 | `src/core/l7_storage.py`, `src/api/main.py` |
| Re-organize Drug Wizard vào chung flow | ~50 | UI only, logic giữ nguyên |
| Tests | ~50 | |
| **Subtotal (3-part test)** | **~280-330 LOC** | |
| Avatar Option A (canvas/CSS) | +~80 | nếu chọn |
| Avatar Option B (cloud lip-sync) | +~150-250 + ADR/consent | nếu chọn, riêng FID |

---

*FID-VN-014 | DRAFT 2026-06-11 | Claude*
*Chờ Andy trả lời Q1-Q3 trước khi implement*
