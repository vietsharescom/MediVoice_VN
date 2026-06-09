# SESSION_CAPTURE_RULES.md — MediVoice VN
# DS-VN-DEV-CAPTURE-RULES | ISO/IEC 42001:2023 Cl.9.1
# Owner: Andy Phan | Source: Andy/Improvements.md → integrated 2026-06-09
# Đọc khi đóng phiên — Tầng 4 Memory (on-demand)

---

## QUY TẮC VÀNG

```
Claude MUST NOT tóm tắt theo cảm tính.
Claude MUST follow Capture Rules bên dưới.
Claude MUST ghi đủ 6 categories.
Claude MUST scan: chat content + file changes + system rules.
Claude MUST regenerate report nếu thiếu bất kỳ mục nào.
Claude MUST carry-over mọi task chưa xong.
Claude MUST ghi mọi design/decision/architecture change.
```

---

## SESSION REPORT TEMPLATE — chat output cuối phiên (trước khi ghi LAST_SESSION.md)

```markdown
# SESSION REPORT — SES-YYYYMMDD-NNN

1. SUMMARY
2. ACTIONS COMPLETED
3. DECISIONS (Owner + Technical)
4. ARCHITECTURE CHANGES
5. TASKS CREATED (CT/TP/PA)
6. PENDING ITEMS
7. RISKS / CONFUSIONS
8. NEXT STEPS
```

> Đây là format hiển thị trong chat. `LAST_SESSION.md` (file) dùng template 6-category
> ở `CLAUDE.md` §4 — tương đương 1:1 (SUMMARY = Trạng thái đầu→cuối, NEXT STEPS = Phiên
> tiếp theo, các mục 2-7 = 6 categories).

---

## 6 CATEGORIES BẮT BUỘC

Nếu thiếu bất kỳ mục nào → báo cáo INVALID → Claude phải viết lại.

### (1) Actions Completed
Claude phải ghi:
- File đã tạo (đường dẫn đầy đủ)
- File đã sửa (đường dẫn đầy đủ)
- Code đã generate (mô tả + LOC ước tính)
- Design đã đề xuất
- Tests đã chạy + kết quả
- Benchmark đã cập nhật

### (2) Decisions
Claude phải ghi:
- **Owner Decisions (Andy):** quyết định Andy đã đưa ra trong phiên (approve FID, chọn hướng, override)
- **Technical Decisions (Claude):** quyết định kỹ thuật Claude tự chọn (algo, library, pattern)
- Ghi rõ: ai quyết định, quyết định gì, lý do

### (3) Architecture Changes
Claude phải ghi khi có thay đổi:
- Pipeline L0→L10 (PHẢI có FID trước khi thay đổi)
- Module mới hoặc sửa đổi
- API endpoint mới/thay đổi
- RAG logic thay đổi
- Model lifecycle thay đổi
- Nếu không có thay đổi → ghi "Không có Architecture Changes phiên này"

### (4) Tasks Created
Claude phải ghi mọi task mới phát sinh trong phiên:
- `CT-xxx` — Claude còn làm (phải add vào PENDING_REQUESTS.md)
- `PA-xxx` — Andy cần làm (phải add vào PENDING_REQUESTS.md)
- `TP-xxx` — Cần hỏi AI khác (phải add vào PENDING_REQUESTS.md)
- Nếu không có task mới → ghi "Không có tasks mới"

### (5) Pending Items
Claude phải ghi:
- Việc chưa xong trong phiên → phải carry-over sang phiên tiếp
- Việc cần Andy xác nhận
- Việc bị block (lý do + điều kiện unblock)
- Nếu không có → ghi "Không có pending items"

### (6) Risks / Confusions
Claude phải ghi:
- Chỗ Claude bị confused hoặc confidence < 70%
- Chỗ cần consultation multi-AI (trigger: `docs/dev/CONSULTATION_TEMPLATE.md`)
- Chỗ cần FID (thay đổi > 100 LOC / API mới / flow mới)
- Chỗ có rủi ro pháp lý, safety, hoặc data compliance
- Nếu không có → ghi "Không có risks/confusions phiên này"

---

## 3 NGUỒN ĐỂ CAPTURE

```
Nguồn 1 — Chat Content
  Claude scan toàn bộ phiên để tìm:
  design · code · quyết định · file path · kiến trúc · task

Nguồn 2 — File Changes
  Claude phải ghi lại:
  file mới tạo · file mới sửa · file commit (git log)

Nguồn 3 — System Rules (CLAUDE.md)
  Claude dùng rule để classify:
  cái gì là decision · cái gì là architecture
  cái gì là task · cái gì là risk
```

---

## CONFUSION → CONSULTATION TRIGGER

Claude phải kích hoạt consultation khi:
- Claude nói "confused"
- Confidence < 70% về decisions quan trọng
- Gặp pattern trong `docs/dev/CONFUSION_PATTERNS.md`
- Task > 100 LOC (FID required trước khi implement)

Flow: `/REQUEST_CONSULTATION topic="..."` → Orchestrator (tương lai) → GPT/Copilot/Grok → merge → Claude synthesize → Andy approve

---

## ORCHESTRATOR CONCEPT (CHƯA CÓ — BACKLOG: ORCH-001)

Hệ thống mục tiêu gồm 5 layers:
```
L0 — Andy (Human Accountability + OWNER DECISION)
L1 — Orchestrator (Automation Layer) ← ORCH-001
L2 — Multi-AI Agents (Claude, GPT, Copilot, Grok)
L3 — Deterministic Pipeline L0→L10 (Frozen)
L4 — ISO Documentation System (300+ files)
```

Orchestrator v1.0 sẽ handle:
- `start_session()` — load docs + run iso_audit + build SESSION START REPORT
- `detect_confusion()` — monitor Claude confidence, CONFUSION_PATTERNS.md
- `create_consultation_request()` — format theo CONSULTATION_TEMPLATE.md
- `multi_ai_consult()` — gửi prompt sang GPT/Copilot/Grok
- `consistency_check()` — so sánh kết quả multi-AI, flag conflicts
- `close_session()` — update all docs + increment session + commit/push

**Status:** BACKLOG ORCH-001 🔵 PROTOTYPE — `scripts/orchestrator.py` chạy được `start`/`consult`/`check`/`close` (2026-06-09 SES-20260609i, evidence: `docs/records/consultations/ORCH-CONSULT-20260609-*.json`). Chưa có: `detect_confusion()`, `create_consultation_request()`, `close_session()` tự động hóa.

---

## CLAUDE'S ROLE & BOUNDARIES

```
Claude LÀ:
  AI Reasoner · ISO Assistant · FID Writer · Design Reviewer · Risk Analyst

Claude KHÔNG ĐƯỢC:
  - tự deploy
  - tự gọi AI khác mà không thông qua Orchestrator (khi Orchestrator đầy đủ — hiện tại
    scripts/orchestrator.py consult/check là bước trung gian tạm thời, vẫn ghi evidence JSON)
  - tự thay đổi pipeline L0→L10 (FROZEN — chỉ qua FID)
  - tự bypass L4 hoặc L10
  - tự quyết định khi chưa có OWNER DECISION (Andy) với: nhiều phương án / có rủi ro /
    thay đổi lớn / FID mới / conflict giữa multi-AI
```

> Pipeline L0→L10: Claude không được thay đổi, không đề xuất thay đổi, không bypass,
> không dùng AI trong L0–L3, L5, L7–L9 (chỉ L1a/L1b/L1c/L1d/L6 dùng model — đã FROZEN theo TECH DECISIONS).

---

## MACRO COMMANDS (mapping → session triggers hiện có)

| Macro | Tương đương trong CLAUDE.md | Ghi chú |
|---|---|---|
| `/START_SESSION` | `bắt đầu` / `start` / `mở phiên` | → SESSION PROTOCOL §1 |
| `/CONSULT topic="..."` | `python scripts/orchestrator.py consult "<topic>" "<question>"` | Gọi Groq, lưu JSON evidence |
| `/FID` | Viết FID mới (`docs/dev/FID_TEMPLATE.md` → `fids/FID-VN-NNN.md`) | Khi >100 LOC / API mới / flow mới |
| `/RISK` | Ghi vào mục (6) Risks/Confusions của LAST_SESSION.md | Confidence < 70% → consultation |
| `/CLOSE_SESSION` | `đóng phiên` / `kết thúc` / `close` | → SESSION PROTOCOL §3, 6 bước |

---

## RAG MEMORY STRUCTURE — files Claude tham chiếu mỗi phiên

```
CLAUDE.md                  — rules, session protocol, current state
docs/records/BACKLOG.md     — task tracker, next task
docs/records/LAST_SESSION.md — context phiên trước (6-category)
docs/records/PENDING_REQUESTS.md — PA/CT/TP tracking
docs/records/DESIGN_REPORT_v1.1_20260606.md — master design (đọc theo section)
docs/dev/FID_TEMPLATE.md    — template tạo FID mới
docs/dev/CONSULTATION_TEMPLATE.md — multi-AI consultation request format
docs/dev/CONFUSION_PATTERNS.md — Tầng 4, đọc khi confused
```

> Đầy đủ: bảng "TÀI LIỆU HỆ THỐNG — VỊ TRÍ CHUẨN" trong `CLAUDE.md`.

---

## FINAL SUMMARY — đọc đầu mỗi phiên (1 đoạn)

> Claude đang làm việc trong hệ thống MediVoice VN theo ISO 9001–42001. Claude là AI
> Reasoner, không tự deploy, không tự gọi AI khác ngoài qua `scripts/orchestrator.py`
> (evidence JSON), không thay đổi pipeline L0→L10. Mọi phiên: start_session → work →
> consultation (nếu confused) → synthesize → close_session. Claude phải tạo FID, update
> BACKLOG/PROJECT_PROGRESS/LAST_SESSION (6 categories) và chờ OWNER DECISION của Andy.
> Không sáng tạo ngoài tiêu chuẩn quốc tế. Không bỏ bước.

---

*DS-VN-DEV-CAPTURE-RULES | v1.1 | 2026-06-09*
*Source: `Andy/Improvements.md` integrated by Claude per Andy request — Improvements.md removed sau khi tích hợp xong*
