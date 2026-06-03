# CLAUDE.md — MediVoice VN
# ISO/IEC 42001:2023 | ISO_VN v1.0 | v0.2.0
# Owner: Andy Phan (Viet) | Maple Leaf Group
# GitHub: https://github.com/vietsharescom/MediVoice_VN

---

## IDENTITY

| Field | Value |
|---|---|
| Project | MediVoice VN — Phần mềm quản lý phòng khám tư + AI Voice |
| Positioning | **"Documentation Assistant"** — AI tạo nháp, BS chịu trách nhiệm |
| Market | Phòng mạch tư nhân lâm sàng có đăng ký BYT — VN |
| Stack | Python 3.10, FastAPI, PhoWhisper-small, PhoBERT+CRF, SQLite, Fernet, Tauri |
| Compliance | NĐ13/2023 · TT32/2023 · TT13/2025 · Luật KCB 2023 · Luật AI 134/2025 |
| Pilot | Phòng khám Đà Nẵng (Andy) + Phòng mạch Sài Gòn (BS partner) |
| GitHub | https://github.com/vietsharescom/MediVoice_VN |

---

## SESSION START — ĐỌC CÁI NÀY TRƯỚC

```
1. Đọc: Section CURRENT STATE bên dưới
2. Đọc: BACKLOG.md (xem TODO + DOING)
3. Chạy: python -m pytest tests/ -q  (sau khi có code)
4. Báo cáo 1 dòng: "v{X} | {N} tests | Next: {task} | Ready."
```

---

## CURRENT STATE

| Field | Value |
|---|---|
| Version | v0.2.0 |
| Status | **Design finalized — sẵn sàng code Phase 0** |
| Tests | N/A (chưa có code) |
| Blocker | Drug database strategy (cần giải quyết trước code) |
| Next task | BENCH-001: Benchmark PhoWhisper trên audio thực tế |

**Key files:**
- [BACKLOG.md](docs/records/BACKLOG.md) — task tracker
- [DECISIONS.md](docs/records/DECISIONS.md) — all locked decisions
- [VISION.md](docs/cl05_leadership/VISION.md) — product vision v0.2
- [BRS.md](docs/cl08_operation/BRS.md) — business requirements v0.2
- [CHANGELOG.md](CHANGELOG.md) — version history

---

## SẢN PHẨM — 2 LAYER + 3 GÓI

### 2 Layers
```
LAYER 1: Patient Management
  Hồ sơ bệnh nhân, lịch hẹn, thu chi, referral, storage

LAYER 2: AI Voice Core
  BS/nhân viên nói → PhoWhisper → điền form → BS approve → PDF
```

### 9 Modules (bật/tắt theo gói)
```
M1: Quản lý bệnh nhân    (hồ sơ, lịch sử, CCCD scan)
M2: Đặt lịch hẹn         (BN tự book online, QR check-in)
M3: Thu chi đơn giản     (voice log thu tiền, ghi chi phí)
M4: Kết quả bên thứ 3   (upload PDF/ảnh → gắn hồ sơ BN)
M5: Referral partner     (chỉ định đối tác, KHÔNG ghi tiền)
M6: Zalo / Thông báo    (reminder tái khám, share PDF đơn thuốc)
M7: VN Cloud sync        (VNG/FPT/VNPT Cloud, multi-device)
M8: Plugin chuyên khoa  (CĐHA, nha khoa, tai mũi họng...)
M9: HIS integration      (HL7 v2 export, BravoSoft, FPT)
```

### 3 Gói dịch vụ
```
GÓI 1 — AI Voice Only         ~500k–1M/tháng
  Core AI + Mẫu 15/BV1 + PDF + SQLite local offline

GÓI 2 — Phòng Mạch            ~2–3M/tháng
  Gói 1 + M1 + M2 + M3 + M4 + M6 + M7
  TT13/2025 compliant ready

GÓI 3 — Phòng Khám Đầy Đủ    ~4–8M/tháng
  Tất cả modules + M5 + M8 + M9
```

---

## PIPELINE (FROZEN)

```
Audio → [L0]  Normalize 16kHz mono
      → [L1a] PhoWhisper chunk streaming (10s overlap)
      → [L1b] Drug name correction (VN drug database)
      → [L1c] Medical NER (PhoBERT + CRF)
      → [L1d] ICD-10-VN auto-lookup (QĐ5837)
      → [L2]  Schema + confidence validation
      → [L3]  Route: lâm sàng / CĐHA plugin / nha khoa...
      → [L4]  Human Gate — BS review + approve (KHÔNG BYPASS)
      → [L5]  PII scan (NĐ13/2023)
      → [L6]  Generate Mẫu 15/BV1 + plugin nếu có
      → [L7]  SQLite + Fernet lưu trữ
      → [L8]  Error handling + recovery
      → [L9a] PDF export            ← Phase 0
      → [L9b] HL7 v2 export         ← Phase 1
      → [L9c] FHIR R4 export        ← Phase 2
      → [L10] Immutable audit log (10+ năm, tamper-proof)
```

### 2 Voice Contexts
```
STAFF VOICE (tiếp nhận BN):
  Hỏi: "Tên gì? Ở đâu? Bệnh gì?"
  → AI điền form tiếp nhận (tên, tuổi, lý do đến)
  → Phase 1 feature (sau khi core stable)

DOCTOR VOICE (trong phòng khám):
  Nói: triệu chứng, khám, chẩn đoán, thuốc, chỉ định
  → AI điền Mẫu 15/BV1 + đơn thuốc
  → Phase 0 core feature
```

---

## FORM PRIORITY

```
CORE (Phase 0):
  Mẫu 15/BV1 — Bệnh án ngoại trú lâm sàng
  Dùng bởi 95% BS lâm sàng tư nhân

PLUGINS (Phase 1+):
  CĐHA        — báo cáo siêu âm/X-quang   (FID-VN-001)
  Nha khoa    — Mẫu 16/BV1               (FID-VN-003)
  Tai mũi họng, Tim mạch...              (Phase 2)

LƯU Ý QUAN TRỌNG:
  CĐHA và chuyên khoa dùng form riêng của ngành
  KHÔNG dùng Mẫu 15/BV1
  Chỉ là OPTION/PLUGIN — không phải Phase 0 target
```

---

## FEATURE WORKFLOW — 3 TẦNG

### Tầng 1: Lớn (> 100 LOC | API mới | thay đổi architecture)
```
1. Viết FID (1 trang: Why + What + Acceptance criteria)
2. Andy approve
3. Implement + tests (100% PASS)
4. CHANGELOG entry
5. Commit: feat(VN-L{N}): description [FID-VN-NNN]
```

### Tầng 2: Vừa (20–100 LOC)
```
1. Task trong BACKLOG.md
2. Implement + tests (100% PASS)
3. CHANGELOG entry
4. Commit: feat/fix: description
```

### Tầng 3: Nhỏ (< 20 LOC | bug fix | config)
```
1. Implement + tests
2. Commit với message rõ ràng
```

---

## ABSOLUTE RULES

1. Pipeline L0→L10 FROZEN — thay đổi chỉ qua FID
2. 100% tests PASS trước mọi commit
3. L4 Human Gate KHÔNG BYPASS — BS phải approve mọi record
4. Data lưu tại VN — không AWS/GCP/Azure region ngoài VN
5. Output theo mẫu TT32/2023
6. ICD-10-VN bắt buộc trong Chẩn đoán (QĐ5837)
7. Positioning = "Documentation Assistant" trong mọi UI/docs/marketing
8. UI luôn hiển thị: "AI tạo nháp — Bác sĩ chịu trách nhiệm hoàn toàn"
9. CCHN/GPHN thu thập khi đăng ký — platform không chịu TN nếu user khai sai
10. Referral/commission: KHÔNG ghi tiền, KHÔNG ghi phần trăm

---

## LEGAL CONSTRAINTS (HARD)

| Luật | Yêu cầu | Giải pháp |
|---|---|---|
| NĐ13/2023 | Data tại VN | SQLite local + VN Cloud (VNG/FPT/VNPT) |
| TT32/2023 | Mẫu bệnh án chuẩn | Mẫu 15/BV1 core, TT32 plugins |
| Luật KCB 2023 Đ.14 | BS hành nghề tại cơ sở đăng ký | Chỉ phục vụ cơ sở có đăng ký |
| Luật KCB 2023 Đ.62 | BS ký bệnh án | L4 không bypass |
| Luật KCB 2023 Đ.80 | Không hoa hồng | Referral tracking only, no financials |
| TT13/2025 | EMR + chữ ký số + FHIR | Deadline 31/12/2026 |
| Luật AI 134/2025 | Audit + human oversight | L4 + L10, conformity trước 09/2027 |
| TT46/2017 | SaMD nếu chẩn đoán | NOT SaMD — chỉ transcription/form fill |

---

## TECH DECISIONS (LOCKED)

| Component | Decision | Lý do |
|---|---|---|
| ASR | PhoWhisper-small (BSD-3-Clause) | Only VN medical ASR, offline |
| Training data | VietMed dataset (MIT) | Commercial OK |
| NLP/NER | PhoBERT + CRF (MIT) | Best VN NER |
| Desktop | **Tauri** (Rust) | 10MB vs Electron 150MB |
| Mobile | Web responsive (Phase 1) | Không build native app |
| Database | SQLite + WAL + Fernet | Simple, offline, encrypted |
| Cloud | VN only: VNG/FPT/VNPT | NĐ13/2023 compliant |
| Export Ph0 | PDF | Universal, no integration needed |
| Export Ph1 | HL7 v2 | Real standard in VN (not FHIR yet) |
| Export Ph2 | FHIR R4 | When TT13/2025 enforced |
| Zalo Ph0 | Manual share | No API risk |
| Zalo Ph1 | Share SDK + OA (non-medical only) | Zalo bans medical content via OA |
| Drug DB | TBD — blocker | Must resolve before L1b |

---

## PILOT PLAN

```
Pilot 1: Phòng khám Đà Nẵng (Andy trực tiếp)
  Mục tiêu: cài đặt + quan sát + thu audio thực tế

Pilot 2: Phòng mạch Sài Gòn (BS partner)
  Mục tiêu: test cold onboarding không có Andy tại chỗ

KPIs Pilot:
  □ Thu 50–100h audio y tế thực tế
  □ Đo CEER: tên thuốc, liều lượng, chẩn đoán
  □ Xác nhận: BS dùng app thật, không bỏ giữa chừng
  □ Xác nhận: WTP — trả tiền hay không
```

---

## EXTERNAL REVIEW — CHỈ KHI CẦN

**Đã review (ChatGPT + Grok + Copilot — 2026-06-03):**
- Kết luận: Khả thi về kỹ thuật và pháp lý
- Xem: [THIRD_PARTY_REVIEW_REQUEST.md](docs/records/THIRD_PARTY_REVIEW_REQUEST.md)

**Cần review thêm:**
- Luật sư VN (healthtech + data + AI) — trước khi bán
- Drug database licensing — trước khi build L1b

---

## SESSION END

```
1. Update BACKLOG.md (move DOING → DONE, add new tasks)
2. Update CHANGELOG.md nếu có code thay đổi
3. Update CURRENT STATE section bên trên
4. Báo: "Done. Remaining: {task list}"
```

---

*MediVoice VN | ISO_VN v1.0 | v0.2.0 | Updated: 2026-06-03*
