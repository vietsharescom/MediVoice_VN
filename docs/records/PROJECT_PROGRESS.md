# PROJECT_PROGRESS.md | DS-VN-REC-PROGRESS
# MediVoice VN — Bảng Theo Dõi Tiến Độ Toàn Dự Án
# Cập nhật: 2026-06-08 | v0.5.3
# Owner: Andy Phan — Maple Leaf Group

---

## LEGEND

| Ký hiệu | Ý nghĩa |
|---|---|
| 🟢 | **DONE** — Hoàn thành |
| 🔵 | **PARTIAL** — Đang làm / hoàn thành một phần |
| 🔴 | **BLOCKED** — Bị chặn, cần unblock trước |
| ⏳ | **PENDING** — Chưa bắt đầu |
| 🟡 | **WAITING** — Chờ điều kiện bên ngoài |

---

## BẢNG TIẾN ĐỘ TOÀN DỰ ÁN

| # | Lưu đồ | Chức năng | Status | Task ID | Phiên hoàn thành | Ghi chú |
|---|---|---|---|---|---|---|
| | **▼ START** | | | | | |
| | | | | | | |
| **P0** | **══════════════** | | | | | |
| **P0** | **PHASE 0 — MVP** | BS nói → Mẫu 15/BV-01 → PDF | 🔵 | — | — | 6/7 milestones done |
| **P0** | **══════════════** | | | | | |
| | | | | | | |
| P0.1 | ├─ 🟢 **Design** | VISION, BRS, PROJECT_KICKOFF S1-S9, 32 decisions locked | 🟢 | — | SES-20260603 | Andy ký S10 còn treo |
| P0.1a | │  ├─ VISION.md | Tầm nhìn, 3 gói, 9 modules, roadmap | 🟢 | — | SES-20260603 | |
| P0.1b | │  ├─ BRS.md | Business requirements, user stories, constraints | 🟢 | — | SES-20260603 | |
| P0.1c | │  ├─ PROJECT_KICKOFF | S1-S9: legal scan, tech scan, market, solution | 🟢 | — | SES-20260603 | S10 Andy ký sau |
| P0.1d | │  └─ DECISIONS.md | 47 ADRs — kiến trúc, pháp lý, kỹ thuật | 🟢 | — | SES-20260606 | Thêm 15 ADR mới |
| | │ | | | | | |
| P0.2 | ├─ 🟢 **Implement L0→L10** | AI Pipeline đầy đủ + FastAPI PWA | 🟢 | — | SES-20260608d | GAP-003 ✅ GAP-004 ✅ — 322/322 PASS |
| P0.2.L0 | │  ├─ L0 Normalize | 16kHz mono, VAD, hash, purge audio | 🟢 | — | SES-20260604 | NĐ13/2023 |
| P0.2.L1a | │  ├─ L1a PhoWhisper ASR | Nhận dạng giọng nói VN, offline, chunk 10s | 🟢 | — | SES-20260604 | WER 36-52% chưa fine-tune |
| P0.2.L1b | │  ├─ L1b Drug Correct | Sửa tên thuốc về INN, alias map 110+ thuốc | 🟢 | — | SES-20260604 | |
| P0.2.L1c | │  ├─ L1c NER VN | Rule-based: vitals, drugs, diagnosis, follow-up | 🟢 | FID-VN-005 | SES-20260607 | VN word-form numbers fixed |
| P0.2.L1d | │  ├─ L1d ICD-10-VN | Auto-lookup 15,026 mã (QĐ5837/BYT) | 🟢 | — | SES-20260604 | |
| P0.2.L2 | │  ├─ L2 Validate | Confidence scoring, weighted fields | 🟢 | — | SES-20260604 | |
| P0.2.L3 | │  ├─ L3 Route | lam_sang/cdha/nha_khoa + transcript fallback | 🟢 | — | SES-20260606 | Bug fix: transcript fallback |
| P0.2.L4 | │  ├─ L4 Human Gate | BS approve bắt buộc — không bypass | 🟢 | — | SES-20260604 | Luật KCB Đ.62 |
| P0.2.L5 | │  ├─ L5 PII Scan | CCCD/SĐT/BHYT/email — NĐ13/2023 | 🟢 | GAP-002 | SES-20260604 | 27 unit tests ✅ |
| P0.2.L6 | │  ├─ L6 Form Gen | NER → BenhAnNgoaiTru (Mẫu 15/BV-01) | 🟢 | FID-VN-004 | SES-20260607 | VN NER direct mapping |
| P0.2.L7 | │  ├─ L7 Storage | SQLite + WAL + Fernet encryption | 🟢 | — | SES-20260604 | |
| P0.2.L8 | │  ├─ L8 Recovery | Error handling, @with_recovery | 🟢 | GAP-003 ✅ | SES-20260608d | 20 tests PASS `tests/unit/test_l8_error_handler.py` |
| P0.2.L9a | │  ├─ L9a PDF | Mẫu 15/BV-01 ReportLab + disclaimer | 🟢 | GAP-004 ✅ | SES-20260608d | 15 tests PASS `tests/unit/test_l9a_pdf_export.py` |
| P0.2.L10 | │  └─ L10 Audit Log | SHA-256 hash chain, append-only, 10 năm | 🟢 | — | SES-20260604 | |
| | │ | | | | | |
| P0.2.API | │  ├─ FastAPI PWA | Doctor UI: record → review → approve → PDF | 🟢 | GAP-005 | SES-20260604 | 18 integration tests ✅ |
| P0.2.CA | │  └─ Canada Pipeline Port | L0→L9 Canada (MarianMT + SOAP) cho NER quality | 🟢 | — | SES-20260605 | Dùng nội bộ |
| | │ | | | | | |
| P0.3 | ├─ 🟢 **Benchmark BENCH-001** | PhoWhisper + Canada pipeline trên 22 audio | 🟢 | BENCH-001 | SES-20260605 | T-007 10/10, T-005 20/22 PASS |
| P0.3a | │  ├─ T-007 WER | eval_phowhisper.py — WER 36-52%, RTF 0.5x | 🟢 | — | SES-20260605 | |
| P0.3b | │  └─ T-005 Pipeline | Canada pipeline 20/22 PASS (91%) | 🟢 | — | SES-20260605 | 2 FAIL hợp lệ (silence) |
| | │ | | | | | |
| P0.4 | ├─ 🟢 **Design Review** | DESIGN_REPORT v1.1 + ISO audit system | 🟢 | — | SES-20260606 | Full system design confirmed |
| P0.4a | │  ├─ DESIGN_REPORT v1.1 | Master design 21 sections, 700+ dòng | 🟢 | — | SES-20260606 | docs/records/ |
| P0.4b | │  ├─ ISO Audit System | iso_audit.py + session counter + weekly trigger | 🟢 | — | SES-20260606 | |
| P0.4c | │  ├─ AI Memory System | 5-tier memory + CONFUSION_PATTERNS (25 patterns) | 🟢 | — | SES-20260606 | |
| P0.4d | │  ├─ Consultation Template | Multi-AI consultation workflow | 🟢 | — | SES-20260606 | |
| P0.4e | │  ├─ PENDING_REQUESTS | PA/CT/TP tracking system | 🟢 | — | SES-20260606 | |
| P0.4f | │  ├─ ISO Docs Mới | DPA, INCIDENT_PLAN, BS_ONBOARDING | 🟢 | — | SES-20260606 | |
| P0.4g | │  └─ Bug Fixes (4) | trieu_chung, patient_name, l3 transcript, qua_trinh | 🟢 | — | SES-20260606 | 210 tests PASS |
| | │ | | | | | |
| **P0.5** | **├─ 🟢 VN-ROUTER-001** | **L6 branch: NER → Mẫu 15/BV-01 trực tiếp** | **🟢** | **FID-VN-004** | SES-20260606 | **232 tests PASS** |
| P0.5a | │  ├─ FID-VN-004 | Feature Intent Document | 🟢 | CT-001 | SES-20260606 | fids/FID-VN-004.md DONE |
| P0.5b | │  ├─ l3_routing vn_route | detect_vn_route() trong Canada L3 | 🟢 | CT-002 | SES-20260606 | 14 tests PASS |
| P0.5c | │  ├─ l6_agent dispatch | lam_sang → benh_an / cdha → SOAP | 🟢 | CT-002 | SES-20260606 | AC-001 AC-002 PASS |
| P0.5d | │  └─ l6_mau15_generator | generate_mau15(): NER → form_data → generate_benh_an() | 🟢 | CT-002 | SES-20260606 | 22 new tests PASS |
| | │ | | | | | |
| **P0.5.1** | **├─ 🟢 VN-NER-002** | **VN word-form numbers → vital extraction fixed** | **🟢** | **FID-VN-005** | SES-20260607 | **272 tests PASS** |
| P0.5.1a | │  ├─ FID-VN-005 | Feature Intent Document — approved Andy | 🟢 | — | SES-20260607 | fids/FID-VN-005.md DONE |
| P0.5.1b | │  ├─ _normalize_vn_numbers() | PhoWhisper word-form → digits trước NER regex | 🟢 | FID-VN-005 | SES-20260607 | "tám mươi"→80 |
| P0.5.1c | │  ├─ generate_mau15_from_vn_ner() | MedicalEntities direct mapping (không qua Canada NER) | 🟢 | FID-VN-005 | SES-20260607 | Root cause fix |
| P0.5.1d | │  ├─ l6_agent lam_sang | original VI text → l1c_ner (không qua MarianMT) | 🟢 | FID-VN-005 | SES-20260607 | Canada path (cdha) giữ nguyên |
| P0.5.1e | │  └─ test_l1c_vn_numbers | 40 tests: _vn_to_int, normalize, TC-001/002/003 | 🟢 | FID-VN-005 | SES-20260607 | bench_ceer tc_001/002: vital=True ✅ |
| | │ | | | | | |
| **P0.5.2** | **├─ 🔵 BENCH-002 Baseline** | **Lâm sàng vùng miền: 10 files, Vitals✅ Diag✅ Drug🔴 Followup✅(0.1)** | **🔵** | **BENCH-002** | SES-20260608 | **Drug🔴 blocked TRAIN-001. Followup fixed CT-007.** |
| P0.5.2a | │  ├─ gen_test_audio.py | Tạo WAV từ JSON template (gTTS → 16kHz mono) | 🟢 | — | SES-20260608 | `tools/gen_test_audio.py` |
| P0.5.2b | │  ├─ bench_ceer --gt flag | Whitelist filtering, fix AUDIO_TOO_LONG | 🟢 | — | SES-20260608 | `tools/bench_ceer.py` |
| P0.5.2c | │  ├─ 10 vùng miền template | Hà Nội→Kiên Giang, ground truth đầy đủ | 🟢 | PA-006 | SES-20260608 | `data/audio/ground_truth_lam_sang_template.json` |
| P0.5.2d | │  ├─ CEER Drug baseline | Drug=0.9🔴 → DEFERRED | 🟡 | CT-006 | — | Blocked: TRAIN-001 cần 50-100h audio thật. Andy approved defer 2026-06-08 |
| P0.5.2e | │  ├─ CEER Followup baseline | Followup=0.7🔴 → **0.1✅** | 🟢 | CT-007 | SES-20260608 | _RE_TAI_KHAM captures extra context (kèm/nếu/xét nghiệm). binh_dinh=TRAIN-001 dep. |
| P0.5.2f | │  └─ Data tổ chức | dental/ folder tách riêng, xóa 22 duplicates | 🟢 | — | SES-20260608 | `data/audio/dental/` |
| | │ | | | | | |
| **P0.6** | **├─ 🟢 DEPLOY-001** | **Windows installer cho BS Đà Nẵng** | **🟢** | **CT-005** | SES-20260608 | install.bat + start.bat + check_env + setup_facility + facility_config |
| P0.6a | │  ├─ Python venv bundle | install.bat — check Python + create venv + pip install | 🟢 | CT-005 | SES-20260608 | `install.bat` |
| P0.6b | │  ├─ Model cache | check_env.py checks PhoWhisper cache (~150MB tự download) | 🟢 | CT-005 | SES-20260608 | `scripts/check_env.py` |
| P0.6c | │  └─ Setup wizard | setup_facility.py + facility_config.json template | 🟢 | CT-005 | SES-20260608 | `scripts/setup_facility.py` |
| | │ | | | | | |
| **P0.7** | **└─ 🟡 PILOT Đà Nẵng + SG** | **5 BS dùng thật + thu audio thực tế** | **🟡** | — | — | Chờ P0.6 done + PA-006 |
| P0.7a |    ├─ BS Onboarding | Andy trực tiếp cài + hướng dẫn | 🔵 | ONBOARD-001 | SES-20260606 | BS onboarding checklist ĐÃ KÝ |
| P0.7b |    ├─ DPA ký | Hợp đồng xử lý dữ liệu | 🟡 | PA-003 | — | Luật sư review xong → ký |
| P0.7c |    ├─ BENCH-002 thật | Record 30-50 audio thật → CEER thật | 🟡 | PA-006 | — | Chờ pilot deploy |
| P0.7d |    └─ LEGAL-001 | Luật sư VN review DPA + tư vấn | 🔵 | LEGAL-001 | SES-20260606 | Email đã gửi |
| | | | | | |
| | **▼** | | | | |
| | | | | | |
| **P1** | **══════════════** | | | | |
| **P1** | **PHASE 1 — Complete Product** | M1-M7 + Plugins + Staff Screen | ⏳ | — | Sau 5 paying users |
| **P1** | **══════════════** | | | | |
| | | | | | |
| P1.M1 | ├─ M1 Patient Mgmt | Hồ sơ BN đầy đủ, CCCD scan, QR thẻ | ⏳ | — | |
| P1.M2 | ├─ M2 Booking Engine | 7 states + buffer + waitlist + D-1/H-2/H-15p | ⏳ | — | |
| P1.M4 | ├─ M4 Email Auto-processor | 3 điều kiện + quarantine | ⏳ | — | |
| P1.M5 | ├─ M5 Referral 2 chiều | Deal %, commission tracking (no money) | ⏳ | — | Gói 3 |
| P1.M6 | ├─ M6 Zalo + Email | Text→Zalo, File→Email, Post-care CRM | ⏳ | — | |
| P1.M7 | ├─ M7 VN Cloud | VNG/FPT/VNPT sync | ⏳ | — | |
| P1.QMS | ├─ Queue Management | Số thứ tự + TTS loa | ⏳ | — | |
| P1.STAFF | ├─ Staff Screen (Mode B) | Tiếp nhận + admin gộp | ⏳ | — | STAFF-001 |
| P1.AFTERCARE | ├─ Post-care CRM | D+2/D+4/D+7 wellness check | ⏳ | — | |
| P1.WEBSITE | ├─ Website Widget | Booking embed + REST API | ⏳ | — | |
| P1.CDHA | ├─ Plugin CĐHA | Báo cáo siêu âm/X-quang (FID-VN-001) | ⏳ | — | |
| P1.NHA | ├─ Plugin Nha khoa | Mẫu 16/BV-01 (FID-VN-002) | ⏳ | — | |
| P1.TRAIN | ├─ TRAIN-001 | Fine-tune PhoWhisper 50-100h audio | ⏳ | — | Sau pilot |
| P1.LEGAL | └─ LEGAL-001 sign-off | Luật sư ký → launch thương mại | 🔵 | — | Email gửi rồi |
| | | | | | |
| | **▼** | | | | |
| | | | | | |
| **P2** | **══════════════** | | | | |
| **P2** | **PHASE 2 — TT13 Compliance** | Chữ ký số + FHIR + HL7 | ⏳ | — | Deadline 31/12/2026 |
| **P2** | **══════════════** | | | | |
| | | | | | |
| P2.SIGN | ├─ Chữ ký số BS | TT13/2025 — ký số bệnh án | ⏳ | — | |
| P2.HL7 | ├─ HL7 v2 Export | BravoSoft / FPT.eHospital | ⏳ | — | |
| P2.FHIR | ├─ FHIR R4 Export | Khi TT13/2025 thực sự enforce | ⏳ | — | |
| P2.M9 | ├─ M9 HIS Integration | API partners | ⏳ | — | Gói 3 |
| P2.AUDIT | └─ BYT Audit Export | L10 audit log export chuẩn | ⏳ | — | |
| | | | | | |
| | **▼** | | | | |
| | | | | | |
| **P3** | **══════════════** | | | | |
| **P3** | **PHASE 3 — Scale + Conformity** | 500+ phòng, Luật AI 134 | ⏳ | — | Trước 01/09/2027 |
| **P3** | **══════════════** | | | | |
| | | | | | |
| P3.CONF | ├─ Conformity Assessment | Luật AI 134/2025 — budget 80-200M VND | ⏳ | — | |
| P3.VNEID | ├─ VNeID API | Khi BYT publish | ⏳ | — | |
| P3.BHYT | ├─ BHYT Check | Real-time eligibility | ⏳ | — | |
| P3.PARTNER | ├─ FPT/Viettel Partnership | Plugin/add-on 400+ BV | ⏳ | — | Sau 100+ users |
| P3.IVR | └─ IVR Phone Booking | VoIP + SIP | ⏳ | — | |
| | | | | | |
| | **▼ END** | | | | |

---

## PHIÊN TIẾP THEO — LÀM GÌ?

### ⚡ NGAY BÂY GIỜ

| # | Task | Điều kiện | File |
|---|---|---|---|
| 1 | **PILOT Đà Nẵng** Cài install.bat, BS dùng thật | DEPLOY-001 DONE ✅ | Andy |
| 2 | **BENCH-002** Record 30-50 audio thật → CEER thật | Sau pilot | PA-001 |
| 3 | **TEST-E2E-001** End-to-end với audio thật | Sau pilot | CT |

### 🟡 SONG SONG (Andy làm)

| # | Task | Mô tả |
|---|---|---|
| PA-001 | Record audio Đà Nẵng | 30-50 consultations thật → `data/audio/pilot/` |
| PA-004 | `data/audio/ground_truth.json` | Điền labels → chạy `bench_ceer.py --full` |
| PA-002 | Chờ luật sư VN | Email đã gửi |
| PA-003 | Ký DPA | Sau luật sư review |

### 📋 SAU DEPLOY-001

| # | Task |
|---|---|
| CONFIG-001 | Facility config UI |
| CT-006 | Mở rộng drug_db.json (30 drug interactions) |
| TEST-E2E-001 | End-to-end test với audio thật + ground truth |
| PILOT Đà Nẵng | Install + BS dùng thật |

---

## METRICS HIỆN TẠI (2026-06-08)

| KPI | Target | Actual | Status |
|---|---|---|---|
| Tests PASS | 100% | 322/322 | 🟢 |
| bandit | 0 HIGH/MEDIUM | 0/0 | 🟢 |
| Vital extraction (TC audio) | >0% | bench tc_001/tc_002: vital=True | 🟢 fixed FID-VN-005 |
| WER | <30% | 36-52% | 🔴 cần fine-tune |
| CEER Vitals | <5% | 0.033 (lam_sang gTTS baseline) | 🟢 near-perfect |
| CEER Diagnosis | <10% | 0.1 (lam_sang gTTS baseline) | 🟢 tốt |
| CEER Drug | <10% | 0.9 (lam_sang gTTS baseline) | 🔴 cần TRAIN-001 |
| CEER Followup | <10% | **0.1** (lam_sang gTTS baseline) | 🟢 CT-007 done |
| CEER thật | <5% | ❓ cần audio BS thật | 🟡 BENCH-002 PA-006 |
| BS approve rate | >85% | ❓ chưa pilot | ⏳ |
| NPS | >7/10 | ❓ chưa pilot | ⏳ |
| Paying users | ≥5 | 0 | ⏳ |

---

## LỊCH SỬ PHIÊN

| Phiên | Ngày | Version | Highlights |
|---|---|---|---|
| SES-20260602 | 2026-06-02 | — | ~15h research thị trường VN |
| SES-20260603 | 2026-06-03 | v0.1→v0.2 | Design + ISO framework + 32 decisions |
| SES-20260604 | 2026-06-04 | v0.2→v0.3 | L0→L10 implement + FastAPI PWA (165 tests) |
| SES-20260605 | 2026-06-05 | v0.3→v0.4 | Canada pipeline port + BENCH-001 (T-005 20/22) |
| SES-20260606 | 2026-06-06 | v0.4→v0.4.5 | Design review + ISO audit + 4 bugs fixed (210 tests) |
| SES-20260606b | 2026-06-06 | v0.4.5→v0.5.0 | VN-ROUTER-001 DONE — L6 branch FID-VN-004 (232 tests) |
| SES-20260607 | 2026-06-07 | v0.5.0→v0.5.1 | VN-NER-002 DONE — FID-VN-005 word-form numbers (272 tests) |
| SES-20260608 | 2026-06-08 | v0.5.1→v0.5.2 | BENCH-002 baseline lâm sàng 10 vùng miền + tools + data organization |
| SES-20260608b | 2026-06-08 | v0.5.2→v0.5.3 | CT-007 DONE — Followup CEER 0.7→0.1 (tai_kham regex extended) + Naming Convention v1.2 |
| SES-20260608c | 2026-06-08 | v0.5.3→v0.6.0 | CT-005 DEPLOY-001 DONE — install.bat + start.bat + check_env + setup_facility (287 tests) |
| SES-20260608d | 2026-06-08 | v0.6.0→v0.6.1 | GAP-003 ✅ GAP-004 ✅ — 35 unit tests L8+L9a (322 tests total) |

---

*DS-VN-REC-PROGRESS | PROJECT_PROGRESS v1.3 | 2026-06-08*
*Cập nhật mỗi phiên đóng. Đọc cùng BACKLOG.md + PENDING_REQUESTS.md*
