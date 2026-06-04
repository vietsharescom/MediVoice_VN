# VV_PLAN.md | DS-VN-COM-004
# ISO/IEC 42001:2023 Clause 8.6 — AI System Verification & Validation
# MediVoice VN — Kế hoạch Kiểm tra và Xác nhận
# v1.0 | 2026-06-04 | Owner: Andy Phan

---

## 1. MỤC ĐÍCH

Xác nhận rằng:
- **Verification:** Hệ thống được xây dựng đúng theo thiết kế (build it right)
- **Validation:** Hệ thống đúng với nhu cầu thực tế của BS (build the right thing)

---

## 2. VERIFICATION — Kiểm tra kỹ thuật

### V1 — Unit & Integration Tests (tự động)
| Test | File | Tiêu chí pass |
|---|---|---|
| Pipeline integrity | `tests/test_pipeline_integrity.py` | 100% PASS |
| L4 Human Gate không bypass | `TestL4HumanGate` | PASS |
| L10 Audit log immutable | `TestL10AuditLog` | PASS |
| Data residency | `TestDataResidency` | PASS |
| Drug names không bị dịch | `TestDrugNameIntegrity` | PASS |
| ICD-10-VN format | `TestICD10VNRequired` | PASS |

**Cadence:** Chạy trước mỗi commit (pre-commit hook)

### V2 — Pipeline End-to-End Test (thủ công)
**Input chuẩn (test case TC-001):**
```
"Bệnh nhân đau đầu sốt 38.5 huyết áp 120/80
 chẩn đoán viêm họng cấp kê Amoxicillin 500mg
 2 viên 3 lần ngày 5 ngày tái khám sau 5 ngày"
```

**Output kỳ vọng:**
| Field | Giá trị mong đợi | Tolerance |
|---|---|---|
| nhiet_do | 38.5 | ±0.1 |
| huyet_ap | 120/80 | exact |
| chan_doan | viêm họng cấp | exact |
| icd_code | J02 hoặc J02.9 | exact |
| drug[0].inn | Amoxicillin | exact |
| drug[0].ham_luong | 500mg | exact |
| tai_kham | Sau 5 ngày | exact |
| confidence | ≥ 0.7 | min |

**Cadence:** Trước mỗi release + sau mỗi thay đổi L1b/L1c/L1d

### V3 — Security Verification
- [ ] Fernet key không hardcode trong source
- [ ] SQLite file nằm trong thư mục local (không remote URL)
- [ ] No foreign cloud endpoints trong src/
- **Tool:** `TestNoHardcodedSecrets` + `TestDataResidency`

---

## 3. AI MODEL CODE REVIEW — Quy trình Review Độc lập L1a/L1c

> **ISO/IEC 42001:2023 Cl.8.6:** Kết quả V&V phải được review bởi người không tham gia phát triển.
> Với 1 founder, "độc lập" = Claude `/code-review` + so sánh output trước/sau + BS pilot xác nhận.

### Khi nào trigger?

**Bắt buộc chạy V4 khi:**
- Thay đổi `src/core/l1a_asr.py` (ASR model, chunking, confidence)
- Thay đổi `src/core/l1c_ner.py` (NER patterns, regex, entity extraction)
- Thay đổi `data/reference/drug_db.json` (drug aliases, INN names)
- Nâng L1c từ rule-based → PhoBERT+CRF (Phase 1)

### V4 — AI Model Code Review (3 bước bắt buộc)

**Bước 1 — Regression Snapshot (tự động)**

Chạy script `scripts/ai_model_review.py` TRƯỚC khi thay đổi:
```bash
python scripts/ai_model_review.py --save-baseline
# Lưu: docs/records/AI_REVIEW_BASELINE.json
```

Sau khi thay đổi, chạy lại để so sánh:
```bash
python scripts/ai_model_review.py --compare-baseline
# Output: diff report với PASS/FAIL mỗi test case
```

**Tiêu chí PASS:**
| Metric | Threshold | Xử lý nếu fail |
|---|---|---|
| Tất cả 5 test cases giữ nguyên output | 5/5 PASS | Block merge |
| Không có drug name nào bị mất | 100% | Block merge |
| Confidence không giảm > 0.1 | Δ ≤ 0.10 | Review + Andy approve |
| Không có ICD code sai | 0 regressions | Block merge |

**Bước 2 — Independent Review (Claude /code-review)**

Chạy `/code-review` trên diff của L1a hoặc L1c:
```
/code-review high
```
- CRITICAL hoặc HIGH findings → fix trước khi merge
- Ghi kết quả vào commit message: `[V4-REVIEW: PASS/findings]`

**Bước 3 — Clinical Validation (BS pilot)**

Khi có BS pilot: gửi 5 câu mẫu trước/sau thay đổi, hỏi BS:
> "Output nào chính xác hơn về thuốc, chẩn đoán, liều lượng?"

Kết quả ghi vào `docs/records/DS-VN-TST-YYYYMMDD-V4.md`.

### Output bắt buộc

Mỗi lần thay đổi L1a/L1c phải có:
- [ ] `docs/records/AI_REVIEW_YYYYMMDD.md` — kết quả V4
- [ ] Commit message có `[V4-REVIEW: PASS]`
- [ ] RTM.md cập nhật nếu có SRS thay đổi

---

## 4. VALIDATION — Xác nhận với người dùng thực

### Val-1 — Benchmark BENCH-001 (cần audio từ Đà Nẵng)
**Mục tiêu:** Đo CEER thực tế trước khi pilot

| Metric | Mục tiêu | Ngưỡng dừng pilot |
|---|---|---|
| CEER (tên thuốc) | < 5% | > 10% |
| WER (Word Error Rate) | < 30% | > 40% |
| Latency E2E | < 5s | > 8s |

**Phương pháp:**
1. Andy ghi 20–30 câu mẫu thực tế tại phòng khám Đà Nẵng
2. Chạy pipeline, so sánh output với transcript do BS viết tay
3. Ghi kết quả vào `docs/records/DS-VN-TST-{date}-001.md`

### Val-2 — Usability Test với BS pilot (Phase 0)
**Tiêu chí acceptance:**
- BS hoàn thành 1 bệnh án trong < 3 phút (so với ghi tay 5–10 phút)
- BS approve ≥ 85% bản nháp không cần sửa nhiều (KPI-004)
- BS NPS ≥ 7/10 sau 1 tuần dùng thật

**Phương pháp:**
- Quan sát trực tiếp 5 buổi khám tại Đà Nẵng
- Thu feedback qua `/api/feedback`
- Phỏng vấn ngắn sau mỗi tuần

### Val-3 — Compliance Validation (Luật AI 134/2025)
- L4 Human Gate: BS luôn approve trước khi lưu → verify qua audit log
- L10 chain integrity: chạy `verify_chain()` hàng tuần
- PII scan: kiểm tra không có CCCD/SĐT raw trong log

---

## 5. V&V RECORDS

Kết quả V&V lưu tại:
- Test reports: `docs/records/DS-VN-TST-YYYYMMDD-NNN.md`
- Benchmark results: `docs/records/BENCH-001-results.md` (sau khi có audio)
- AI model review: `docs/records/AI_REVIEW_YYYYMMDD.md`

---

## 6. TRẠNG THÁI HIỆN TẠI

| Hạng mục | Trạng thái |
|---|---|
| V1 Automated tests | ✅ 165/165 PASS |
| V2 Pipeline E2E | ✅ Đã test TC-001 (conf=0.81) |
| V3 Security | ✅ bandit: 0 HIGH/MEDIUM |
| **V4 AI Model Review** | ✅ Quy trình documented + script sẵn sàng |
| Val-1 BENCH-001 | ⏳ Chờ audio Đà Nẵng |
| Val-2 Usability | ⏳ Chờ pilot |
| Val-3 Compliance | ⏳ Chờ pilot |

---

*DS-VN-COM-004 | VV_PLAN v1.1 | ISO/IEC 42001:2023 Cl.8.6 | 2026-06-04*
