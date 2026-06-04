# CONFUSION_PATTERNS.md | DS-VN-DEV-003
# MediVoice VN — Patterns Claude Hay Nhầm
# Tầng 4 Memory: Đọc khi Claude báo confused hoặc có multiple options
# v1.0 | 2026-06-06 | Owner: Andy Phan

---

## MỤC ĐÍCH

File này ngăn Claude lặp lại các nhầm lẫn đã xảy ra.
Mỗi pattern = 1 câu hỏi đã được resolve + answer chuẩn + lý do.
Claude đọc file này khi: bắt đầu FID, khi confused, khi có multiple options.

---

## NHÓM A — AI PIPELINE ARCHITECTURE

### P-A01: L6 tạo SOAP hay Mẫu 15/BV-01 trực tiếp?
```
SAI: L6_SOAP_GENERATOR → SOAP → VN-ROUTER convert → Mẫu 15
ĐÚNG: L6 BRANCH tại NER entities:
  lam_sang  → NER entities → BenhAnNgoaiTru (Mẫu 15/BV-01 TRỰC TIẾP)
  cdha      → NER entities → generate_soap() → SOAP output
  nha_khoa  → NER entities → Mẫu 16/BV-01 [Phase 1]

LÝ DO: PROJECT_KICKOFF §9d "Rewrite L6 generator for VN"
       DECISIONS.md ADR 2026-06-06: "L6 branch tại NER entities"
       SOAP là format Canada, VN cần Mẫu 15 trực tiếp.
```

### P-A02: MarianMT — giữ hay xóa?
```
SAI TRƯỚC ĐÂY: "MarianMT không cần — output tiếng Việt" (PROJECT_KICKOFF §7)
ĐÚNG HIỆN TẠI: GIỮ MarianMT nhưng dùng nội bộ cho NER

LÝ DO: BENCH-001 CEER=0% khi không có MarianMT.
       NER hoạt động tốt hơn trên EN text (PhoBERT+CRF trained EN-heavy).
       MarianMT chỉ dùng cho NER quality — output BSmax vẫn là VI.
       ADR 2026-06-05: "MarianMT kích hoạt ngay"
```

### P-A03: Canada pipeline — sửa hay không sửa?
```
QUY TẮC: src/pipeline/ (Canada handlers) = KHÔNG SỬA
         Ngoại lệ DUY NHẤT: thêm vn_route hook vào L6_AGENT (VN-ROUTER-001)

LÝ DO: ADR 2026-06-05: "Canada pipeline = core pipeline VN, giữ nguyên"
       T-005 20/22 PASS xác nhận pipeline hoạt động
       Sửa sẽ phá vỡ test suite Canada

NGOẠI LỆ: L6_AGENT nhận vn_route từ payload → dispatch lam_sang/cdha
          Đây là VN routing hook, không phải sửa core logic
```

### P-A04: VN-ROUTER-001 đặt ở đâu trong pipeline?
```
SAI: Đặt sau L9_RESPONSE (convert SOAP → Mẫu 15)
ĐÚNG: Branch TRONG L6_AGENT — sau extract_entities(), trước generate_soap()

CỤ THỂ:
  L6_AGENT:
    entities = extract_entities(EN_text, vi_text)
    if vn_route == "lam_sang":
        return L6_GENERATE_MAU15(entities)    ← NEW (VN-ROUTER-001)
    else:
        return generate_soap(entities)         ← existing Canada flow

LÝ DO: DECISIONS.md ADR 2026-06-06 + Andy confirm trong phiên
```

### P-A05: VN route detection (lam_sang/cdha) — ở đâu?
```
LƯU Ý: Canada L3_ROUTING detect FLOW_A/B/C/D (KHÔNG phải lam_sang/cdha)
VN route cần detect RIÊNG từ VI original_text keywords

GIẢI PHÁP: Detect vn_route ở L3_ROUTING (thêm nhỏ) hoặc từ API caller
           src/core/l3_route.py có sẵn logic này (lam_sang/cdha/nha_khoa)
           Truyền vn_route qua payload từ L3 → L6

CÁC KEYWORDS:
  cdha:     siêu âm, x-quang, CT, MRI, chụp, điện tim, ECG
  nha_khoa: răng, nha, nướu, lợi
  default:  lam_sang
```

---

## NHÓM B — PRODUCT & LEGAL

### P-B01: Referral commission — ghi % không?
```
SAI: "KHÔNG ghi tiền, KHÔNG ghi phần trăm" (rule cũ)
ĐÚNG: % setup trong M5 partner CONFIG (tham chiếu nội bộ)
      KHÔNG ghi % vào từng giao dịch cụ thể

CỤ THỂ:
  Config partner: deal_rate = 5% (admin sets once)
  Per referral: partner, patient, date, status → KHÔNG có amount
  Dashboard: volume × deal% = tham chiếu (không phải invoice)
  Payment: outside system, by owner manually

LÝ DO: Luật KCB 2023 Điều 80 cấm hoa hồng PER TRANSACTION
       Deal % trong config = business agreement record (khác per-transaction)
       RISK_REGISTER R-P02 v1.1 đã cập nhật
```

### P-B02: Zalo file đính kèm?
```
QUY TẮC CỨNG:
  Zalo OA = TEXT ONLY (non-medical content)
  File y tế (kết quả XN, bệnh án PDF, đơn thuốc) → EMAIL only

LÝ DO: Zalo policy: cấm gửi thông tin y tế nhạy cảm qua OA
       NĐ13/2023: dữ liệu y tế = dữ liệu nhạy cảm → cần bảo vệ đặc biệt

ĐƯỢC GỬI QUA ZALO: "Nhắc tái khám 10/7 lúc 9h" / "Xác nhận lịch" / wellness text
KHÔNG QUA ZALO: PDF đơn thuốc, kết quả XN, tên bệnh, tên thuốc cụ thể
```

### P-B03: Partner communication — kênh nào?
```
EMAIL = CHÍNH THỨC (default cho tất cả partner comm)
  - Referral notification + acknowledgment
  - Commission deal documentation
  - Sensitive/formal communication

ZALO = TÙY CHỌN (chỉ nếu partner muốn, chỉ text không nhạy cảm)
  - Quick "OK REF-001234" confirmation (chỉ text)
  - NON-sensitive operational updates

Commission info = BÍ MẬT → Email only, KHÔNG qua Zalo bất kỳ hình thức nào
```

### P-B04: LEGAL-001 chặn cái gì?
```
LEGAL-001 CHẶN: Commercial launch (charge tiền thật)
KHÔNG CHẶN: Technical pilot (BS dùng thử, không trả tiền)

TIẾP TỤC ĐƯỢC:
  - Build + test + VN-ROUTER-001
  - Deploy DEPLOY-001 cho BS Đà Nẵng (pilot miễn phí)
  - Thu feedback, BENCH-002

PHẢI CÓ LEGAL-001 TRƯỚC:
  - Ký hợp đồng với phòng khám
  - Charge tiền subscription
  - Launch marketing
```

### P-B05: NOT SaMD — ý nghĩa thực tế?
```
NOT SaMD = MediVoice VN không phải thiết bị y tế
→ Không cần đăng ký BYT như thiết bị y tế (TT46/2017)
→ AI_POLICY.md §7 + IMPACT_ASSESSMENT.md confirmed

ĐIỀU KIỆN ĐỂ GIỮ NOT SaMD:
  ✅ AI chỉ transcribe + điền form (không tự chẩn đoán)
  ✅ BS phải approve MỌI record (L4 Human Gate)
  ✅ Output labeled "AI tạo nháp — BS chịu TN"
  ❌ NẾU AI tự ra chẩn đoán → trở thành SaMD → cần đăng ký BYT
```

---

## NHÓM C — SESSION & DOCUMENT MANAGEMENT

### P-C01: Start trigger — làm gì đúng?
```
ĐÚNG (4 bước song song):
  A. Read BACKLOG.md (IMMEDIATE tasks)
  B. Read LAST_SESSION.md (previous context)
  C. Run pytest tests/ -q (test count)
  D. Run python scripts/iso_audit.py (ISO health)

Sau đó:
  1. Báo: v{X} | {N} tests | ISO: OK/⚠️/🔴
  2. Hiện toàn bộ LAST_SESSION.md (không tóm tắt)
  3. Dừng chờ lệnh Andy

KHÔNG làm gì thêm khi chưa có lệnh từ Andy.
```

### P-C02: Đóng phiên — làm gì đúng?
```
5 bước bắt buộc:
  1. BACKLOG.md: DOING→DONE, thêm tasks mới phát sinh
  2. CHANGELOG.md: entry nếu có code change
  3. CLAUDE.md CURRENT STATE: update version + status + next task
  4. LAST_SESSION.md: ghi đè theo template đủ 5 mục
  5. git add -A + commit + push

KHÔNG QUÊN: Nếu DECISIONS.md có ADR mới phiên này → ghi vào DECISIONS.md trước bước 5
```

### P-C03: DESIGN_REPORT — đọc khi nào?
```
KHÔNG đọc mỗi phiên (quá dài, 700 dòng)
ĐỌC KHI: Viết FID / Implement module mới / Design decision needed

File: docs/records/DESIGN_REPORT_v1.1_20260606.md
Đọc section liên quan đến task, không toàn bộ
```

### P-C04: CONSTITUTION.md còn dùng không?
```
KHÔNG — CONSTITUTION.md đã được ARCHIVE (docs/archive/)
Superseded bởi: CLAUDE.md (rules) + AI_POLICY.md (AI principles)
Không đọc, không update CONSTITUTION.md trong workflow
```

### P-C05: Archive files — update không?
```
KHÔNG UPDATE bất kỳ file nào trong docs/archive/
Archive = historical snapshots, git history tự preserve
Các session records cũ (DS-VN-SES-*) cũng không update
```

### P-C06: CURRENT STATE trong CLAUDE.md — update khi nào?
```
Update tại ĐÓNG PHIÊN (bước 3 protocol)
Update: Version, Status, Tests, Blocker, Next task

Khi nào tăng version:
  Patch (0.4.x): bug fix, doc update, config
  Minor (0.x.0): new feature / FID complete
  Major (x.0.0): phase launch (Phase 0 → Phase 1)
```

---

## NHÓM D — TECHNICAL DECISIONS

### P-D01: Pipeline "FROZEN" nghĩa là gì?
```
FROZEN = Không thay đổi logic core mà không có FID approved

FROZEN CHẶT (không thể thay đổi):
  L4 Human Gate bypass → NEVER
  L10 immutable log delete → NEVER
  Data ngoài VN → NEVER

FROZEN VỚI FID (có thể thay đổi nếu có FID):
  L0→L10 logic, pipeline order, stage behavior

KHÔNG FROZEN (thay đổi tự do):
  src/api/ (API routes, UI)
  src/core/ wrappers không ảnh hưởng pipeline logic
  tests/, scripts/, docs/
  drug_db.json, config files
```

### P-D02: FID threshold — khi nào cần?
```
CẦN FID (Tầng 1):
  > 100 LOC thực sự (không counting tests/docs)
  OR API endpoint mới
  OR thay đổi pipeline stage behavior
  OR thêm/sửa module M1-M9

KHÔNG CẦN FID (Tầng 2/3):
  20-100 LOC improvement / bug fix
  < 20 LOC = direct commit
  Test writing (dù > 100 LOC)
  Doc updates

VN-ROUTER-001: CẦN FID (thay đổi L6 architecture, > 100 LOC)
```

### P-D03: GAP-002 + GAP-005 — ưu tiên thế nào?
```
GAP-002 (PII unit tests): CRITICAL — viết trước pilot
GAP-005 (API integration tests): CRITICAL — viết trước pilot

LÝ DO: PII scan bảo vệ NĐ13/2023 — không có test = không có automated compliance verification
       API là interface chính — không có integration test = regression risk cao

PLAN: Viết song song với VN-ROUTER-001 trong cùng sprint
```

### P-D04: 2 orchestrators — dùng cái nào?
```
src/core/orchestrator.py    = VN orchestrator (L0→L5, basic)
src/core/orchestrator_ca.py = Canada orchestrator (full L0→L10)

DÙNG: Canada orchestrator (orchestrator_ca.py) cho main pipeline
       VN orchestrator đang dùng cho VN-specific modules (L6 form gen)
       
VN-ROUTER-001 sẽ bridge: Canada pipeline output → VN form generator
```

### P-D05: Email auto-processor — khi nào kích hoạt?
```
3 ĐIỀU KIỆN BẮT BUỘC (thiếu 1 → QUARANTINE):
  ① BN đã đăng ký trong M1 (record exists)
  ② Có referral ACTIVE (REF-xxx chưa COMPLETED)
  ③ BN đã ký consent data processing

QUARANTINE = email moved to review folder, staff notified, NOT auto-processed
LÝ DO: NĐ13/2023 không cho xử lý dữ liệu y tế không được consent
```

---

## NHÓM E — QUALITY & TESTING

### P-E01: BENCH-001 done — còn cần BENCH-002 không?
```
BENCH-001 (DONE): PhoWhisper benchmark trên 22 audio sample
  → WER 36-52%, T-005 20/22 PASS, T-007 10/10 PASS
  → Xác nhận pipeline hoạt động

BENCH-002 (CẦN): CEER thực tế từ audio BS nói thật tại Đà Nẵng
  → Ground truth labels do BS viết tay
  → Đo: drug names accuracy, dose accuracy, diagnosis accuracy
  → PHẢI < 5% để launch

BENCH-001 ≠ BENCH-002. Cả hai đều cần.
```

### P-E02: 165 tests — coverage thực tế thế nào?
```
Có: 165 tests PASS, coverage 88%
Thiếu (CRITICAL):
  GAP-002: SRS-L5-001/002 — PII scan unit tests (chưa có)
  GAP-005: SRS-API-* — API integration tests (chưa có)

Chấp nhận thiếu (Medium):
  GAP-001: Silence validation
  GAP-003: Error handler unit tests
  GAP-004: PDF export unit tests
```

---

## CẬP NHẬT FILE NÀY

Thêm pattern mới khi:
  - Claude bị confused lần thứ 2 về cùng 1 vấn đề
  - Andy sửa hướng Claude đi sai
  - Multi-AI consultation resolve một ambiguity

Format: P-[GROUP][NN]: [Câu hỏi ngắn]
```
SAI/SAI TRƯỚC ĐÂY: [wrong assumption]
ĐÚNG: [correct answer + how]
LÝ DO: [file reference + rule number]
```

---

*DS-VN-DEV-003 | CONFUSION_PATTERNS v1.0 | 2026-06-06*
*Tầng 4 Memory — Đọc khi bắt đầu FID hoặc Claude confused*
