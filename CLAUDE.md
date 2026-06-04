# CLAUDE.md — MediVoice VN
# ISO/IEC 42001:2023 | ISO_VN v1.0 | v0.4.1
# Owner: Andy Phan (Viet) | Maple Leaf Group
# GitHub: https://github.com/vietsharescom/MediVoice_VN
# DESIGN REF: docs/records/DESIGN_REPORT_v1.1_20260606.md (nguồn thiết kế đầy đủ nhất)

---

## ⚡ QUY TẮC SỐ 0 — BẮT BUỘC TUYỆT ĐỐI

> **CLAUDE PHẢI ĐỌC TOÀN BỘ FILE NÀY TRƯỚC KHI LÀM BẤT CỨ ĐIỀU GÌ.**
> Không trả lời, không code, không đề xuất — cho đến khi đọc xong.
> File này là nguồn sự thật duy nhất (single source of truth) cho dự án.

---

## IDENTITY

| Field | Value |
|---|---|
| Project | MediVoice VN — Phần mềm quản lý phòng khám tư + AI Voice |
| Positioning | **"Documentation Assistant"** — AI nghe BS nói, mapping vào đúng form, BS review + ký |
| Market | Phòng mạch tư nhân lâm sàng có đăng ký BYT — VN |
| Stack | Python 3.10, FastAPI, PhoWhisper-small, PhoBERT+CRF, SQLite, Fernet, PWA |
| Compliance | NĐ13/2023 · TT32/2023 · TT13/2025 · Luật KCB 2023 · Luật AI 134/2025 |
| Pilot | Phòng khám Đà Nẵng (Andy) + Phòng mạch Sài Gòn (BS partner) |
| GitHub | https://github.com/vietsharescom/MediVoice_VN |

---

## ⚡ SESSION PROTOCOL — ĐỌC KỸ, LUÔN TUÂN THỦ

### 1. MỞ PHIÊN

**Trigger:** `bắt đầu` · `start` · `begin` · `mở phiên` · hoặc tin nhắn đầu tiên bất kỳ

**Làm 3 việc SONG SONG:**
```
A. Read docs/records/BACKLOG.md        → lấy Next task từ IMMEDIATE
B. Read docs/records/LAST_SESSION.md  → lấy toàn bộ nội dung phiên trước
C. Run: pytest tests/ -q              → lấy N tests PASS
```

**Nếu phiên có thiết kế / viết FID / implement module mới:**
```
D. Read docs/records/DESIGN_REPORT_v1.1_20260606.md
   → đọc section liên quan đến task (không cần đọc toàn bộ 700 dòng)
   → DESIGN_REPORT là nguồn chi tiết nhất cho product/UX/flow decisions
```

**Báo cáo theo thứ tự — KHÔNG bỏ bước nào:**

```
BƯỚC 1 — Dòng trạng thái:
  v{X} | {N} tests PASS | Ready.

BƯỚC 2 — Hiển thị toàn bộ LAST_SESSION.md:
  (copy nguyên nội dung file ra — không tóm tắt, không bỏ)

BƯỚC 3 — Dừng lại, chờ lệnh:
  "Phiên trước kết thúc ở đây. Chờ lệnh Andy."
```

> KHÔNG tự ý bắt đầu làm gì. Chỉ báo cáo xong rồi CHỜ.

---

### 2. TRONG PHIÊN

**Khi Andy nói:** `tiếp tục` · `continue` · `làm đi` · `next`

```
Logic ưu tiên:
1. Next task trong IMMEDIATE làm được ngay? → LÀM LUÔN
2. Next task cần Andy cung cấp gì?
   → Nói 1 câu: "BENCH-001 cần audio — bắt đầu DEPLOY-001 trong lúc chờ."
   → Rồi BẮT ĐẦU ngay, không chờ xác nhận
3. Không biết làm gì? → Chọn task đầu tiên trong BACKLOG Phase 0
```

**TUYỆT ĐỐI KHÔNG dùng AskUserQuestion khi Andy nói tiếp tục.**

---

### 3. ĐÓNG PHIÊN

**Trigger:** `đóng phiên` · `kết thúc` · `end` · `done` · `had end` · `close` · `finish`

**Làm 5 bước, tự động, không hỏi:**

```
BƯỚC 1 — Update BACKLOG.md
  docs/records/BACKLOG.md
  DOING → DONE cho tasks hoàn thành
  Thêm tasks mới nếu phát sinh

BƯỚC 2 — Update CHANGELOG.md
  Thêm entry nếu có code thay đổi
  Format: ## [vX.Y.Z] — YYYY-MM-DD — mô tả ngắn

BƯỚC 3 — Update CURRENT STATE
  Section bên dưới trong file này
  Cập nhật: Version, Status, Tests, Blocker, Next task

BƯỚC 4 — Ghi đè LAST_SESSION.md
  File: docs/records/LAST_SESSION.md
  Dùng template bên dưới — đủ 5 mục, không bỏ qua
  1 file duy nhất, git history tự lưu các phiên cũ

BƯỚC 5 — Commit & Push
  git add -A
  git commit -m "chore(session-end): close session YYYY-MM-DD"
  git push
```

---

### 4. TEMPLATE LAST_SESSION.md

```markdown
# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-YYYYMMDD
## Thời gian: YYYY-MM-DD (giờ đóng phiên nếu biết)
## Version: v{trước} → v{sau}

---

## Trạng thái đầu → cuối
v{trước} | {N} tests → v{sau} | {N} tests

## Đã hoàn thành
- [TASK-ID] mô tả kết quả cụ thể, đo được
- [TASK-ID] ...

## Kết quả đo được
- Tests: N/N PASS
- Pipeline: input mẫu → output mẫu (nếu có)

## Blocker / Phụ thuộc bên ngoài
- [TASK-ID] lý do bị block

## Phiên tiếp theo — làm ngay theo thứ tự
1. [TASK-ID] mô tả (ưu tiên cao nhất)
2. [TASK-ID] ...
3. [TASK-ID] ...
```

---

### 5. TÀI LIỆU HỆ THỐNG — VỊ TRÍ CHUẨN

| File | Vị trí | Ai đọc | Mục đích |
|---|---|---|---|
| `CLAUDE.md` | `/` | **Claude** | Rules, context, session protocol |
| `CHANGELOG.md` | `/` | Andy | Lịch sử code theo version |
| `BACKLOG.md` | `docs/records/` | Claude + Andy | Task tracker — nguồn Next task |
| `LAST_SESSION.md` | `docs/records/` | Claude + Andy | Phiên gần nhất — resume context |
| `DECISIONS.md` | `docs/records/` | Claude + Andy | Architecture decisions (ADR) |
| `VISION.md` | `docs/product/` | Andy | Product direction |
| `BRS.md` | `docs/product/` | Andy | Business requirements |
| `AI_POLICY.md` | `docs/compliance/` | Audit | ISO 42001 Cl.5.2 — chính sách AI |
| `SCOPE.md` | `docs/compliance/` | Audit | ISO 9001+42001 Cl.4.3 — phạm vi |
| `RISK_REGISTER.md` | `docs/compliance/` | Andy | ISO 42001 Cl.6.1 — rủi ro |
| `IMPACT_ASSESSMENT.md` | `docs/compliance/` | Audit | ISO 42001 Cl.8.2 — tác động AI |
| `COMPETENCE.md` | `docs/compliance/` | Andy | ISO 9001 Cl.7.2 — năng lực |
| `NONCONFORMING.md` | `docs/compliance/` | Andy | ISO 9001 Cl.8.7 — lỗi/NC |
| `VV_PLAN.md` | `docs/compliance/` | Andy | ISO 42001 Cl.8.6 — V&V |
| `MANAGEMENT_REVIEW.md` | `docs/compliance/` | Andy | ISO 9001 Cl.9.3 — review định kỳ |
| `FEEDBACK_PROCESS.md` | `docs/compliance/` | Andy | ISO 42001 A.6.2 — feedback BS |
| `NAMING_CONVENTION.md` | `docs/dev/` | Claude | ISO 9001 Cl.7.5 — đặt tên |
| `KPI_METRICS.md` | `docs/dev/` | Andy | ISO 42001 Cl.9.1 — đo lường |
| `DESIGN_REPORT_v1.1_20260606.md` | `docs/records/` | Claude + Andy | **Master design — đọc khi FID/implement module** |

> `docs/archive/` — files cũ/done, không đọc trong workflow thường ngày.
> `DESIGN_REPORT` — đọc theo section khi cần, không cần đọc toàn bộ mỗi phiên.

---

## CURRENT STATE

| Field | Value |
|---|---|
| Version | v0.4.1 |
| Status | **Design Review hoàn tất 2026-06-06 — DESIGN_REPORT v1.1 đã tạo — FID-VN-004 cần viết** |
| Tests | **165/165 PASS** · bandit 0 HIGH/MEDIUM · Coverage 88% |
| Audio | **22 WAV files** tại `data/audio/` + `data/kb/` Clinical KB active |
| Next task | **FID-VN-004** (L6 branch design) → VN-ROUTER-001 (NER→Mẫu15) → DEPLOY-001 |
| Design | Xem chi tiết: `docs/records/DESIGN_REPORT_v1.1_20260606.md` |

---

## SẢN PHẨM — 2 LAYER + 3 GÓI

### 2 Layers
```
LAYER 1: Patient Management
  Hồ sơ bệnh nhân, lịch hẹn, thu chi, referral, storage
  + Queue Management (số thứ tự + TTS loa)
  + 3 operating modes: A (BS alone) | B (BS + Staff) | C (BS + Staff + Cashier)
  + 4 screens: Phòng chờ TV | Staff Screen | Doctor Screen | Zalo BN

LAYER 2: AI Voice Core
  BS nói → PhoWhisper → NER VN → L6 branch → Mẫu 15/BV1 → BS approve → PDF
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
Audio → [L0]  Normalize 16kHz mono, VAD, hash, purge (Privacy by Design)
      → [L1a] PhoWhisper chunk streaming (10s overlap) — offline
      → [L1b] Drug name correction (VN drug database, INN chuẩn)
      → [L1c] Medical NER VN (VITAL/SYMPTOM/MEDICATION/HISTORY/FOLLOWUP)
      → [L1d] ICD-10-VN auto-lookup (QĐ5837 — 15,026 mã)
      → [L2]  Schema + confidence validation (weighted score)
      → [L3]  Route: lam_sang(default) / cdha / nha_khoa
               + session context: clinical / intake / admin
      → [L4]  Human Gate — BS review + approve (KHÔNG BYPASS — Luật KCB Đ.62)
      → [L5]  PII scan (CCCD/SĐT/BHYT — NĐ13/2023)
      → [L6]  BRANCH tại NER entities (KHÔNG qua SOAP cho lam_sang):
               lam_sang  → NER→BenhAnNgoaiTru (Mẫu 15/BV1 trực tiếp)
               cdha      → SOAP → báo cáo CĐHA [Phase 1, M8]
               nha_khoa  → Mẫu 16/BV1 [Phase 1, M8]
      → [L7]  SQLite + WAL + Fernet lưu trữ (local, encrypted)
      → [L8]  Error handling + recovery
      → [L9a] PDF export Mẫu 15/BV1    ← Phase 0
      → [L9b] HL7 v2 export             ← Phase 1
      → [L9c] FHIR R4 export            ← Phase 2
      → [L10] Immutable audit log (SHA-256 hash chain, 10+ năm)

STAFF CONFIRM GATE (sau L10 — admin side):
  Staff xác nhận: đã thu tiền + đã phát thuốc + đã lên lịch
  → M3 ghi doanh thu + L10 audit "ADMIN_CONFIRMED"
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
3. L4 Human Gate — BS phải approve mọi record (Luật KCB 2023 Đ.62)
4. Data lưu tại VN — không AWS/GCP/Azure region ngoài VN
5. Output theo mẫu TT32/2023
6. ICD-10-VN bắt buộc trong Chẩn đoán (QĐ5837)
7. Positioning = "Documentation Assistant": AI nghe BS nói → mapping vào đúng form field → BS approve
   — AI KHÔNG tự ra chẩn đoán nếu BS chưa nói
   — AI PHẢI hiểu thuật ngữ chuyên khoa để map đúng (không phải "no reasoning")
   — Output VI (default) hoặc EN option (BS nước ngoài, CĐHA bilingual)
8. UI luôn hiển thị: "AI tạo nháp — Bác sĩ chịu trách nhiệm hoàn toàn"
9. CCHN/GPHN thu thập khi đăng ký — platform không chịu TN nếu user khai sai
10. Referral/commission: KHÔNG ghi tiền trong giao dịch cụ thể
    — M5 CÓ THỂ setup deal % khi cấu hình đối tác (tham chiếu nội bộ, không public)
    — Thanh toán thực ngoài hệ thống — app không xử lý tiền commission
11. Kênh liên lạc: Zalo OA = text non-medical ONLY | Email = file y tế + nội dung nhạy cảm
    — KHÔNG gửi file y tế qua Zalo OA (vi phạm Zalo policy)
    — Partner comm bí mật (commission) → Email, KHÔNG qua Zalo
12. Email auto-processor: CHỈ xử lý khi đủ 3 điều kiện:
    ① BN đã đăng ký M1 ② Có referral ACTIVE ③ BN đã ký consent
    — Thiếu 1 trong 3 → QUARANTINE → Staff xem xét thủ công
13. Booking Engine: 7 states (SUGGESTED→PENDING→CONFIRMED→COMPLETED/CANCELLED/NO_SHOW/RESCHEDULED)
    + Buffer sau mỗi 4 ca + Waitlist cho slot cancel
    + Reminder: D-1 (9h) → H-2 → H-0:15 (chuẩn Canada)

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
| Frontend | **PWA** (FastAPI + HTML/JS) | Mobile-first — BS dùng phone |
| Mobile | Web responsive Phase 0 | Không build native app |
| Database | SQLite + WAL + Fernet | Simple, offline, encrypted |
| Cloud | VN only: VNG/FPT/VNPT | NĐ13/2023 compliant |
| Export Ph0 | PDF | Universal, no integration needed |
| Export Ph1 | HL7 v2 | Real standard in VN (not FHIR yet) |
| Export Ph2 | FHIR R4 | When TT13/2025 enforced |
| Zalo Ph0 | Manual share | No API risk |
| Zalo Ph1 | OA text non-medical (reminder, booking) | Zalo policy: NO medical file via OA |
| Email Ph1 | SMTP gửi + IMAP nhận auto-process | File y tế, kết quả XN, bệnh án PDF |
| Partner comm | Email PRIMARY (bí mật/formal) + Zalo optional | Commission info bí mật → không qua Zalo |
| Queue | Số thứ tự + TTS loa (gTTS/VinAI offline) | Thay thế số giấy + loa thủ công |
| Drug DB | drug_db.json (110 thuốc) | Phase 0 curated, expand từ pilot |

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

---

## DESIGN DECISIONS (2026-06-06) — ĐỌC KHI IMPLEMENT

> Chi tiết đầy đủ: `docs/records/DESIGN_REPORT_v1.1_20260606.md`
> Đây là tóm tắt compact — Claude đọc khi làm việc liên quan.

```
PATIENT JOURNEY — 7 giai đoạn:
  0. Nguồn BN: Walk-in | Zalo OA | Referral IN | Tái khám | Website widget
  1. Tiếp nhận: QR scan (cũ) | voice/gõ (mới) → M1 → Queue → số thứ tự
  2. Chờ: Doctor Pre-visit Briefing (tóm tắt hồ sơ + cảnh báo dị ứng)
  3. Khám: AI Pipeline L0→L10 → draft → BS approve → PDF
  4. Phân nhánh:
     A. Kết thúc tại PK → Staff Confirm Gate → M3 → Zalo text + Email PDF
     B. Referral OUT → email/Zalo đối tác → RETEST nếu cần → kết quả email về → booking
     C. Bán thuốc tại phòng → gộp với A
  5. Booking: 7 states + D-1/H-2/H-15p + buffer + waitlist
  6. After-care CRM: D+2/D+4/D+5/D+7 với response branching
  7. Tái khám: QR scan → lặp lại vòng

SCREENS: Phòng chờ TV | Staff Screen | Doctor Screen | Zalo BN (S4)
MODES:   A = BS alone (1 screen, 4 tabs) | B = BS + Staff | C = BS + Staff + Cashier
QUEUE:   Số thứ tự + TTS loa VN (gTTS offline) + Zalo notify vị trí chờ

REFERRAL (M5):
  OUT: BS chỉ định → email/Zalo đối tác → OK/DONE/REDO reply → commission event
  IN:  Staff ghi "từ [đối tác]" tại INTAKE → M5 track
  Deal: % setup per partner (tham chiếu) — thanh toán ngoài hệ thống

M1 PATIENT: QR code + consent form + dị ứng ⚠️ + lịch sử 5 lần + tags
M2 BOOKING: 7 states + buffer + waitlist + D-1/H-2/H-15p (chuẩn Canada)
M3 THU CHI: voice log → SQLite → báo cáo → Excel export / kế toán API
M4 KẾT QUẢ: email auto (3 điều kiện) + staff upload thủ công
M5 REFERRAL: 2 chiều + deal % + dashboard volume (not money)
M6 ZALO/EMAIL: text→Zalo | file y tế→Email | partner sensitive→Email only
M7 CLOUD: VNG/FPT/VNPT only | M8 PLUGIN: CĐHA/Nha/TMH | M9 HIS: HL7/FHIR

INTEGRATION GATEWAY: Plugin adapter pattern
  Adapters: Zalo | Email | SMS | TTS | Print | Website Widget | REST API
  Thiết bị: USB mic | BT mic | TV LAN (browser) | Loa USB/BT | Máy in USB
```

---

*MediVoice VN | ISO_VN v1.0 | v0.4.1 | Updated: 2026-06-06*
*Design ref: docs/records/DESIGN_REPORT_v1.1_20260606.md*
