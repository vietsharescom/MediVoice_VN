# IMPROVEMENT_PROCESS.md | DS-VN-COM-013
# ISO 9001:2015 Clause 10.3 — Continual Improvement
# ISO/IEC 42001:2023 Clause 10 — Improvement
# MediVoice VN — Quy trình Cải tiến Liên tục
# v1.0 | 2026-06-06 | Owner: Andy Phan

---

## 1. MỤC ĐÍCH

Tài liệu này trả lời 4 câu hỏi cốt lõi:

1. **Quy định nằm ở đâu?** — Ai viết, Claude đọc ở file nào
2. **Cải tiến thì làm thế nào?** — Quy trình từ ý tưởng đến deployed
3. **Ghi chú ý tưởng thế nào?** — Không để mất bất kỳ improvement nào
4. **Bao lâu cập nhật?** — Cadence chuẩn cho từng loại thay đổi

---

## 2. QUY ĐỊNH Ở ĐÂU — MAP TÀI LIỆU

### Ai làm gì được quy định tại đâu?

| Quy định | Nằm tại | Ai đọc | Cơ chế thực thi |
|---|---|---|---|
| Session protocol (start/close) | `CLAUDE.md` → SESSION PROTOCOL | Claude (mọi phiên) | Claude tự đọc + thực hiện |
| Task tracking | `docs/records/BACKLOG.md` | Claude + Andy | Claude đọc khi mở phiên |
| Improvement ideas | `docs/records/BACKLOG.md` | Claude + Andy | Thêm ngay khi phát sinh |
| Architecture decisions | `docs/records/DECISIONS.md` | Claude + Andy | Thêm sau mỗi quyết định |
| Code quality gates | `.pre-commit-config.yaml` | Git hooks | Chạy tự động trước mỗi commit |
| ISO health check | `scripts/iso_audit.py` | Claude + Andy | Chạy mỗi phiên (Step D) |
| V&V criteria | `docs/compliance/VV_PLAN.md` | Andy + Audit | Review trước mỗi phase |
| Risk management | `docs/compliance/RISK_REGISTER.md` | Andy | Update khi có design/risk mới |
| System design full | `docs/records/DESIGN_REPORT_v1.1_*.md` | Claude (khi cần) | Đọc khi viết FID/implement |

### "Start" trigger — ghi ở đâu, chạy ở đâu?

```
QUY ĐỊNH: CLAUDE.md → Section "SESSION PROTOCOL → 1. MỞ PHIÊN"

KHÔNG PHẢI CODE thông thường — là instruction cho Claude (AI agent).
Claude đọc CLAUDE.md → thực thi như một protocol.

AUTO-ENFORCE qua:
  1. CLAUDE.md — Claude đọc bắt buộc trước mọi action
  2. scripts/iso_audit.py — script Python Andy/Claude chạy
  3. .pre-commit-config.yaml — gates khi commit code

KHÔNG CÓ: server-side enforcement, database trigger, cron job
VÌ: MediVoice VN Phase 0 = 1 developer + Claude, không cần overengineering
KHI NÀO CẦN: Phase 1+ multi-user thì thêm CI/CD pipeline (GitHub Actions)
```

---

## 3. QUY TRÌNH CẢI TIẾN — TỪ Ý TƯỞNG ĐẾN DEPLOYED

### 3.1 Phát hiện improvement (5 nguồn)

```
NGUỒN 1: Claude phát hiện trong phiên làm việc
  → Ghi vào BACKLOG.md ngay (đừng chờ)
  → Tag: 💡 IMPROVEMENT

NGUỒN 2: Andy có ý tưởng mới
  → Nói với Claude → Claude ghi vào BACKLOG.md
  → Andy xác nhận priority (🔴/🟡/🟢)

NGUỒN 3: BS pilot feedback (khi có pilot)
  → /api/feedback → lưu SQLite → Claude đọc weekly
  → FEEDBACK_PROCESS.md quy định xử lý

NGUỒN 4: ISO audit phát hiện gap
  → scripts/iso_audit.py báo cáo
  → Gap → BACKLOG.md ngay với priority
  → NONCONFORMING.md nếu là nonconformity

NGUỒN 5: Test fail / security issue
  → Pre-commit hook chặn commit
  → Fix immediately → retest → commit
  → NONCONFORMING.md nếu critical
```

### 3.2 Phân loại và routing

```
Ý tưởng nhận được → Phân loại:

CRITICAL (fix ngay, không chờ):
  Test fail, security issue, data breach
  → Fix → retest → commit → NONCONFORMING.md

HIGH (trong sprint hiện tại):
  RTM gap CRITICAL, pipeline bug, legal blocker
  → BACKLOG IMMEDIATE với 🔴

MEDIUM (sprint tới):
  New feature, UX improvement, ISO gap non-critical
  → BACKLOG Phase 0/1 với 🟡

LOW (future):
  Nice-to-have, optimization, phase 2+ features
  → BACKLOG Deferred với 🟢

DECISION (kiến trúc):
  → DECISIONS.md + FID nếu Tầng 1 (>100 LOC)
```

### 3.3 Implement + verify

```
TẦNG 1 (lớn):
  FID → Andy approve → code → 100% tests → RTM update
  → CHANGELOG → DECISIONS nếu có ADR mới
  → DESIGN_REPORT update nếu design thay đổi lớn

TẦNG 2 (vừa):
  BACKLOG task → code → tests → CHANGELOG

TẦNG 3 (nhỏ):
  code → tests → commit

SAU MỌI IMPL:
  Run scripts/iso_audit.py → confirm no new gaps
```

---

## 4. GHI CHÚ Ý TƯỞNG — KHÔNG ĐỂ MẤT

### Quy tắc ZERO-LOSS cho improvement ideas

```
KHI CÓ Ý TƯỞNG (dù nhỏ):
  1. Claude ghi vào BACKLOG.md NGAY trong phiên
  2. Tag đúng section: IMMEDIATE / Phase 0 / Phase 1 / Deferred
  3. Priority: 🔴 / 🟡 / 🟢
  4. Nếu là decision → DECISIONS.md cùng lúc
  5. Nếu là design change → note trong LAST_SESSION.md

KHÔNG để:
  ❌ "Nhớ làm sau" mà không ghi
  ❌ Chỉ nói trong chat mà không ghi vào file
  ❌ Ghi vào note cá nhân thay vì BACKLOG

VÌ SAO: git history lưu mọi thứ — BACKLOG là source of truth
```

### Format ghi vào BACKLOG

```markdown
- [ ] **[TAG]-NNN** 🔴/🟡/🟢 Mô tả ngắn — lý do cần làm
      💡 Nguồn: Claude phát hiện / Andy / BS feedback / Audit
```

---

## 5. CADENCE — BAO LÂU CẬP NHẬT

### Trigger-based (event-driven) — ưu tiên hơn time-based

| Trigger | Files cập nhật | Ai làm | Bắt buộc? |
|---|---|---|---|
| Mọi phiên START | BACKLOG, LAST_SESSION đọc | Claude | ✅ Bắt buộc |
| Mọi phiên START | `iso_audit.py` chạy | Claude | ✅ Bắt buộc |
| Có ý tưởng mới | BACKLOG.md | Claude ngay | ✅ Bắt buộc |
| FID implement xong | RTM, CHANGELOG, DECISIONS | Claude | ✅ Bắt buộc |
| Design thay đổi lớn | DESIGN_REPORT mới, CLAUDE.md, DECISIONS | Claude + Andy | ✅ Bắt buộc |
| Test fail | Fix ngay, NONCONFORMING.md | Claude | ✅ Bắt buộc |
| Phiên CLOSE | BACKLOG, **PROJECT_PROGRESS**, CHANGELOG, LAST_SESSION, CLAUDE.md CURRENT STATE | Claude | ✅ Bắt buộc |

### Time-based (định kỳ)

| Tần suất | Hành động | File | Ai làm |
|---|---|---|---|
| Mỗi tháng | MANAGEMENT_REVIEW entry | MANAGEMENT_REVIEW.md | Andy |
| Mỗi quý | Full ISO audit (như phiên này) | Tất cả ISO docs | Claude + Andy |
| Trước mỗi phase launch | V&V full | VV_PLAN.md + tests + BENCH | Andy + Claude |
| Khi có pilot feedback | Update drug_db, NER patterns | drug_db.json, l1c_ner.py | Claude |
| Khi luật thay đổi | Update RISK_REGISTER, LEGAL CONSTRAINTS | RISK_REGISTER, CLAUDE.md | Andy + Claude |

### Ngưỡng "desync không chấp nhận được"

```
🔴 PHẢI FIX NGAY:
  - Tests fail
  - DECISIONS.md có ADR mà CLAUDE.md chưa cập nhật
  - RISK_REGISTER thiếu risk HIGH/CRITICAL đã biết

🟡 FIX TRONG TUẦN:
  - RTM có CRITICAL gap chưa ghi
  - CHANGELOG không có entry cho code change
  - SCOPE không phản ánh feature đã implement

🟢 FIX TRONG THÁNG:
  - Version numbers lỗi thời
  - MANAGEMENT_REVIEW chưa có entry monthly
  - Docs minor inconsistency
```

---

## 6. AUTO-AUDIT — CLAUDE TỰ ĐÁNH GIÁ ISO

### scripts/iso_audit.py — Chạy mỗi phiên

```
Claude chạy: python scripts/iso_audit.py

Script kiểm tra:
  ① Test count (phải ≥ 165, hoặc số hiện tại)
  ② RTM CRITICAL gaps còn mở
  ③ BACKLOG IMMEDIATE items 🔴 chưa done
  ④ LAST_SESSION date (cảnh báo nếu > 7 ngày không có phiên)

Output: ✅ OK / ⚠️ Warning / 🔴 Issue

Khi có issue → Claude flag ngay trong báo cáo đầu phiên
```

### Tự động check code quality

```
PRE-COMMIT HOOKS (.pre-commit-config.yaml):
  ✅ pytest tests/ -q         → 100% tests PASS
  ✅ bandit src/              → 0 HIGH/MEDIUM
  ✅ coverage ≥ 80%

MANUAL (Claude chạy khi được yêu cầu hoặc sau FID):
  python scripts/iso_audit.py
  python scripts/ai_model_review.py --compare-baseline (sau thay đổi L1a/L1c)
  /code-review high (trước merge FID lớn)
```

### Quality check sau mỗi layer/feature

```
SAU MỖI L* IMPLEMENTATION:
  1. pytest tests/ → phải PASS
  2. Grep RTM.md → SRS-L*-xxx mapped?
  3. grep CHANGELOG → entry có không?
  4. DECISIONS.md → cần ADR mới không?

SAU MỖI PHIÊN CLOSE:
  1. git status → không còn unstaged changes
  2. LAST_SESSION.md → đủ 5 mục
  3. BACKLOG.md → tasks done đánh ✅
  4. PROJECT_PROGRESS.md → milestones/metrics/session history cập nhật
  5. CHANGELOG → version entry có không?
  6. Push thành công
```

---

## 7. PHÁT HIỆN VÀ SỬA NGAY — ZERO-TOLERANCE LIST

```
Những lỗi sau phát hiện → SỬA NGAY, không chờ:

CRITICAL (block commit + fix immediate):
  ❌ Test fail → fix + retest → commit
  ❌ bandit HIGH/MEDIUM → fix → commit
  ❌ L4 Human Gate bypass bất kỳ → revert + fix
  ❌ Data lưu ngoài VN → revert + fix

HIGH (fix trong phiên hiện tại):
  ❌ BACKLOG có 🔴 chưa ghi rõ nguyên nhân
  ❌ RTM CRITICAL gap không có plan
  ❌ DECISIONS.md thiếu ADR cho quyết định >100 LOC
  ❌ CLAUDE.md CURRENT STATE sai version

MEDIUM (fix trong phiên tiếp theo):
  ❌ CHANGELOG thiếu entry
  ❌ ISO doc version cũ > 2 tháng
  ❌ SCOPE thiếu feature đã implemented
```

---

## 8. LIÊN KẾT QUY TRÌNH

```
Cải tiến liên tục ←→ tất cả documents:

PHÁT HIỆN:   iso_audit.py + tests + feedback
     ↓
GHI NHẬN:    BACKLOG.md + NONCONFORMING.md
     ↓
PHÂN TÍCH:   DECISIONS.md + RISK_REGISTER.md
     ↓
IMPLEMENT:   FID → code → tests → CHANGELOG
     ↓
VERIFY:      pytest + bandit + iso_audit.py
     ↓
DOCUMENT:    RTM + DECISIONS + CLAUDE.md
     ↓
REVIEW:      MANAGEMENT_REVIEW (monthly/quarterly)
     ↓
REPEAT ←─────────────────────────────────────
```

---

---

## 9. MULTI-AI CONSULTATION WORKFLOW

### Khi nào trigger?
```
Claude tự generate consultation (CONS-YYYYMMDD-NNN.md) khi:
  T1: ≥ 2 valid options, < 70% confident về decision quan trọng
  T2: Domain knowledge ngoài scope (luật VN chi tiết, medical standard)
  T3: Architecture choice ảnh hưởng Phase 1+ (irreversible)
  T4: Andy yêu cầu "hỏi AI khác"
```

### Workflow 5 bước
```
STEP 1: Claude detects confusion/ambiguity
  → Đọc CONFUSION_PATTERNS.md — vấn đề đã có answer chưa?
  → Nếu có: dùng answer đó, không generate consultation
  → Nếu chưa: tiếp tục step 2

STEP 2: Claude generates CONS-YYYYMMDD-NNN.md
  → Template: docs/dev/CONSULTATION_TEMPLATE.md
  → Điền: context, options A/B, constraints, current lean (X%)
  → Lưu vào: docs/records/consultations/

STEP 3: Andy copy REQUEST section → paste sang ChatGPT/Grok
  → Có thể hỏi nhiều AI khác nhau
  → Copy response về

STEP 4: Andy paste responses vào chat với Claude
  → Claude so sánh responses + own analysis
  → Claude điền SYNTHESIS section vào cùng file CONS-xxx.md

STEP 5: Claude presents decision
  → Consolidated confidence %
  → Nếu OWNER DECISION NEEDED: pro/con rõ ràng + specific question for Andy
  → Nếu không: Claude proceeds + ghi ADR vào DECISIONS.md
```

### Template location
```
Template:  docs/dev/CONSULTATION_TEMPLATE.md
Records:   docs/records/consultations/CONS-YYYYMMDD-NNN.md
Index:     docs/records/consultations/README.md
```

### ISO Audit Cadence (chuẩn ISO 9001:2015 Cl.9.2)
```
HÀNG NGÀY (auto, không cần người):
  pre-commit: pytest + bandit + coverage

MỖI PHIÊN (Claude, Step D):
  scripts/iso_audit.py         ← document sync check (fast)

SAU MỖI FID (Claude manual):
  scripts/iso_audit.py         ← verify no new gaps
  docs/dev/QUALITY_AUDIT_TEMPLATE.md (Post-FID Quick Check)

HÀNG THÁNG (Andy, 30 phút):
  MANAGEMENT_REVIEW.md entry
  RISK_REGISTER review

MỖI QUÝ (Claude + Andy, 2-4 giờ):
  Full document sync (ISO framework audit)
  scripts/iso_audit.py --all
  docs/dev/QUALITY_AUDIT_TEMPLATE.md (full template)

TRƯỚC PHASE LAUNCH (Claude + Andy + BS feedback):
  VV_PLAN.md full V&V
  docs/dev/QUALITY_AUDIT_TEMPLATE.md (full)
  Pilot metrics review

HÀNG NĂM (khi có revenue):
  Full ISO 9001+42001 audit
  External consultant nếu cần conformity
```

---

*DS-VN-COM-013 | IMPROVEMENT_PROCESS v1.2*
*ISO 9001:2015 Cl.10.3 | ISO/IEC 42001:2023 Cl.10 | 2026-06-07*
*Change: thêm PROJECT_PROGRESS.md vào Phiên CLOSE checklist (2026-06-07)*
*Ref: DESIGN_REPORT_v1.1_20260606.md | CLAUDE.md SESSION PROTOCOL*
