# PROJECT_PROGRESS.md | DS-VN-REC-PROGRESS
# MediVoice VN — Bảng Theo Dõi Tiến Độ Toàn Dự Án
# Cập nhật: 2026-06-06 | v0.4.5
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

| # | Lưu đồ | Chức năng | Status | Phiên hoàn thành | Ghi chú |
|---|---|---|---|---|---|
| | **▼ START** | | | | |
| | | | | | |
| **P0** | **══════════════** | | | | |
| **P0** | **PHASE 0 — MVP** | BS nói → Mẫu 15/BV-01 → PDF | 🔵 | — | 5/7 milestones done |
| **P0** | **══════════════** | | | | |
| | | | | | |
| P0.1 | ├─ 🟢 **Design** | VISION, BRS, PROJECT_KICKOFF S1-S9, 32 decisions locked | 🟢 | SES-20260603 | Andy ký S10 còn treo |
| P0.1a | │  ├─ VISION.md | Tầm nhìn, 3 gói, 9 modules, roadmap | 🟢 | SES-20260603 | |
| P0.1b | │  ├─ BRS.md | Business requirements, user stories, constraints | 🟢 | SES-20260603 | |
| P0.1c | │  ├─ PROJECT_KICKOFF | S1-S9: legal scan, tech scan, market, solution | 🟢 | SES-20260603 | S10 Andy ký sau |
| P0.1d | │  └─ DECISIONS.md | 47 ADRs — kiến trúc, pháp lý, kỹ thuật | 🟢 | SES-20260606 | Thêm 15 ADR mới |
| | │ | | | | |
| P0.2 | ├─ 🟢 **Implement L0→L10** | AI Pipeline đầy đủ + FastAPI PWA | 🟢 | SES-20260604 | 165 tests PASS |
| P0.2.L0 | │  ├─ L0 Normalize | 16kHz mono, VAD, hash, purge audio | 🟢 | SES-20260604 | NĐ13/2023 |
| P0.2.L1a | │  ├─ L1a PhoWhisper ASR | Nhận dạng giọng nói VN, offline, chunk 10s | 🟢 | SES-20260604 | WER 36-52% chưa fine-tune |
| P0.2.L1b | │  ├─ L1b Drug Correct | Sửa tên thuốc về INN, alias map 110+ thuốc | 🟢 | SES-20260604 | |
| P0.2.L1c | │  ├─ L1c NER VN | Rule-based: vitals, drugs, diagnosis, follow-up | 🟢 | SES-20260604 | Phase 1: PhoBERT+CRF |
| P0.2.L1d | │  ├─ L1d ICD-10-VN | Auto-lookup 15,026 mã (QĐ5837/BYT) | 🟢 | SES-20260604 | |
| P0.2.L2 | │  ├─ L2 Validate | Confidence scoring, weighted fields | 🟢 | SES-20260604 | |
| P0.2.L3 | │  ├─ L3 Route | lam_sang/cdha/nha_khoa + transcript fallback | 🟢 | SES-20260606 | Bug fix: transcript fallback |
| P0.2.L4 | │  ├─ L4 Human Gate | BS approve bắt buộc — không bypass | 🟢 | SES-20260604 | Luật KCB Đ.62 |
| P0.2.L5 | │  ├─ L5 PII Scan | CCCD/SĐT/BHYT/email — NĐ13/2023 | 🟢 | SES-20260604 | Tests: 27 unit tests ✅ |
| P0.2.L6 | │  ├─ L6 Form Gen | NER → BenhAnNgoaiTru (Mẫu 15/BV-01) | 🟢 | SES-20260606 | Bug fix: trieu_chung, patient_name |
| P0.2.L7 | │  ├─ L7 Storage | SQLite + WAL + Fernet encryption | 🟢 | SES-20260604 | |
| P0.2.L8 | │  ├─ L8 Recovery | Error handling, @with_recovery | 🟢 | SES-20260604 | |
| P0.2.L9a | │  ├─ L9a PDF | Mẫu 15/BV-01 ReportLab + disclaimer | 🟢 | SES-20260604 | |
| P0.2.L10 | │  └─ L10 Audit Log | SHA-256 hash chain, append-only, 10 năm | 🟢 | SES-20260604 | |
| | │ | | | | |
| P0.2.API | │  ├─ FastAPI PWA | Doctor UI: record → review → approve → PDF | 🟢 | SES-20260604 | API tests: 18 tests ✅ |
| P0.2.CA | │  └─ Canada Pipeline Port | L0→L9 Canada (MarianMT + SOAP) cho NER quality | 🟢 | SES-20260605 | Dùng nội bộ, không nối API |
| | │ | | | | |
| P0.3 | ├─ 🟢 **Benchmark BENCH-001** | PhoWhisper + Canada pipeline trên 22 audio | 🟢 | SES-20260605 | T-007 10/10, T-005 20/22 PASS |
| P0.3a | │  ├─ T-007 WER | eval_phowhisper.py — WER 36-52%, RTF 0.5x | 🟢 | SES-20260605 | |
| P0.3b | │  └─ T-005 Pipeline | Canada pipeline 20/22 PASS (91%) | 🟢 | SES-20260605 | 2 FAIL hợp lệ (silence) |
| | │ | | | | |
| P0.4 | ├─ 🟢 **Design Review** | DESIGN_REPORT v1.1 + ISO audit system | 🟢 | SES-20260606 | Full system design confirmed |
| P0.4a | │  ├─ DESIGN_REPORT v1.1 | Master design 21 sections, 700+ dòng | 🟢 | SES-20260606 | docs/records/ |
| P0.4b | │  ├─ ISO Audit System | iso_audit.py + session counter + weekly trigger | 🟢 | SES-20260606 | |
| P0.4c | │  ├─ AI Memory System | 5-tier memory + CONFUSION_PATTERNS (25 patterns) | 🟢 | SES-20260606 | |
| P0.4d | │  ├─ Consultation Template | Multi-AI consultation workflow | 🟢 | SES-20260606 | |
| P0.4e | │  ├─ PENDING_REQUESTS | PA/CT/TP tracking system | 🟢 | SES-20260606 | |
| P0.4f | │  ├─ ISO Docs Mới | DPA, INCIDENT_PLAN, BS_ONBOARDING | 🟢 | SES-20260606 | |
| P0.4g | │  └─ Bug Fixes (4) | trieu_chung, patient_name, l3 transcript, qua_trinh | 🟢 | SES-20260606 | 210 tests PASS |
| | │ | | | | |
| **P0.5** | **├─ 🔴 VN-ROUTER-001** | **L6 branch: NER → Mẫu 15/BV-01 trực tiếp** | **🔴** | — | **BLOCKED: chờ Andy approve FID** |
| P0.5a | │  ├─ FID-VN-004 | Feature Intent Document — đã viết xong | 🟡 | SES-20260606 | fids/FID-VN-004.md — PA-005 |
| P0.5b | │  ├─ l3_routing vn_route | detect_vn_route() trong Canada L3 | ⏳ | — | Sau FID approve |
| P0.5c | │  ├─ l6_agent dispatch | if vn_route=="lam_sang" → branch | ⏳ | — | Sau FID approve |
| P0.5d | │  └─ l6_mau15_generator | generate_mau15(): NER entities → form_data → generate_benh_an() | ⏳ | — | Tái dùng l6_generate_form.py |
| | │ | | | | |
| **P0.6** | **├─ ⏳ DEPLOY-001** | **Windows installer cho BS Đà Nẵng** | **⏳** | — | Sau P0.5 |
| P0.6a | │  ├─ Python venv bundle | PyInstaller hoặc NSIS installer | ⏳ | — | |
| P0.6b | │  ├─ Model cache | PhoWhisper + ICD + drug_db pre-bundled | ⏳ | — | |
| P0.6c | │  └─ Setup wizard | Cấu hình CCHN, phòng khám, license | ⏳ | — | CONFIG-001 |
| | │ | | | | |
| **P0.7** | **└─ 🟡 PILOT Đà Nẵng + SG** | **5 BS dùng thật + thu audio thực tế** | **🟡** | — | Chờ P0.5+P0.6 + PA-001..003 |
| P0.7a |    ├─ BS Onboarding | Andy trực tiếp cài + hướng dẫn | 🔵 | SES-20260606 | BS onboarding checklist ĐÃ KÝ |
| P0.7b |    ├─ DPA ký | Hợp đồng xử lý dữ liệu | 🟡 | — | PA-003 — chờ luật sư review |
| P0.7c |    ├─ BENCH-002 | Record 30-50 audio thật → CEER measurement | 🟡 | — | PA-001 — chờ Andy record |
| P0.7d |    └─ LEGAL-001 | Luật sư VN review DPA + tư vấn | 🔵 | SES-20260606 | Email đã gửi — PA-002 |
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

### ⚡ NGAY BÂY GIỜ (unblock pipeline)

| # | Task | Điều kiện | File |
|---|---|---|---|
| 1 | **Andy approve FID-VN-004** | — | `fids/FID-VN-004.md` |
| 2 | Implement VN-ROUTER-001 | Sau #1 | CT-002 |
| 3 | GAP-003 (error handler tests) + GAP-004 (PDF tests) | Cùng lúc | `tests/unit/` |

### 🟡 SONG SONG (Andy làm)

| # | Task | Mô tả |
|---|---|---|
| PA-001 | Record audio Đà Nẵng | 30-50 consultations thật → `data/audio/pilot/` |
| PA-002 | Chờ luật sư VN | Email đã gửi |
| PA-003 | Ký DPA | Sau luật sư review |

### 📋 SAU VN-ROUTER-001

| # | Task |
|---|---|
| DEPLOY-001 | Windows installer |
| CONFIG-001 | Facility config UI |
| DRUG-ALIAS-001 | Mở rộng drug_db.json |
| TEST-E2E-001 | End-to-end test với audio thật |

---

## METRICS HIỆN TẠI (2026-06-06)

| KPI | Target | Actual | Status |
|---|---|---|---|
| Tests PASS | 100% | 210/210 | 🟢 |
| bandit | 0 HIGH/MEDIUM | 0/0 | 🟢 |
| Coverage | ≥80% | 88% | 🟢 |
| WER | <30% | 36-52% | 🔴 cần fine-tune |
| CEER | <5% | ❓ chưa đo | 🟡 BENCH-002 |
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

---

*DS-VN-REC-PROGRESS | PROJECT_PROGRESS v1.0 | 2026-06-06*
*Cập nhật mỗi phiên đóng. Đọc cùng BACKLOG.md + PENDING_REQUESTS.md*
