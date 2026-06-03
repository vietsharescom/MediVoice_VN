# LATEST_SESSION.md -- MediVoice VN Claude Memory
# Project: MediVoice VN | Path: C:\Projects\MediVoice_VN | Owner: Andy Phan
# READ THIS FIRST every session.

## SESSION: MV-VN-SES-20260603-001

| Field | Value |
|---|---|
| Session ID | MV-VN-SES-20260603-001 |
| Date | 2026-06-03 |
| AI Model | claude-sonnet-4-6 |
| Version | v0.1.0 (documentation only — no code yet) |
| Owner | Andy Phan (Viet) — Maple Leaf Group |
| Tests | N/A — no code yet |
| Status | PROJECT_KICKOFF S1–S9 complete. Awaiting Andy S10 approval. |

---

## 1. PROJECT IDENTITY

- **Project**: MediVoice VN — Bác sĩ đọc → Bệnh án điện tử TT32/2023
- **Forked from**: MediVoice AI (Canada) v2.61.3
- **Stack**: Python 3.10, FastAPI, PhoWhisper-small (VN ASR), PhoBERT+CRF (NER), SQLite, Fernet
- **Market**: Vietnam — phòng khám tư nhân, trung tâm CĐHA
- **Pipeline**: L0→L1→L2→L3→L4→L5→L6[+PLUGIN]→L7→L8→L9→L10 (FROZEN)
- **Key difference from CA**: No MarianMT. Output = TT32/2023 VN format. ICD-10-VN.

---

## 2. CURRENT STATE

**Version:** v0.1.0 — Documentation phase
**Code:** Not started — awaiting PROJECT_KICKOFF S10 approval from Andy
**Tests:** N/A

### Documents created this session

| File | Status |
|---|---|
| CLAUDE.md | ✅ Done |
| docs/cl08_operation/PROJECT_KICKOFF.md | ✅ S1–S9 Done — **AWAITING S10** |
| docs/cl08_operation/BRS.md | ✅ Done |
| docs/cl05_leadership/VISION.md | ✅ Done |
| docs/records/LATEST_SESSION.md | ✅ This file |
| docs/records/TASK_BACKLOG.md | ✅ Done |
| CHANGELOG.md | ✅ Done |

---

## 3. KEY RESEARCH FINDINGS (2026-06-02)

### Market
- **37,000–40,000** phòng khám tư đang hoạt động tại VN
- **No competitor** cung cấp voice→bệnh án chuẩn TT32 tại VN
- VEM.AI: live tại BV E Hà Nội — cloud LLM (có thể vi phạm NĐ13/2023)
- Heidi Health: 12–18 tháng mới vào VN — window cơ hội còn đó

### Legal
- **NĐ13/2023**: Data PHẢI ở server trong VN — cloud nước ngoài = vi phạm
- **TT32/2023**: 29 mẫu bệnh án — output PHẢI theo chuẩn BYT
- **TT13/2025**: Deadline 31/12/2026 — phòng khám tư BẮT BUỘC có EMR
- **Luật AI 134/2025**: Grace period đến 01/09/2027 cho y tế
- **KHÔNG cần BYT approve** phần mềm trước khi bán — thị trường mở

### Workflow
- BS siêu âm đọc → thư ký gõ = **Use Case #1** (30–50 ca/ngày)
- 29 mẫu TT32 = **70% common core + 30% specialty plugins**
- Báo cáo CĐHA KHÔNG thuộc 29 mẫu — format riêng biệt
- Bệnh nhân không CCCD vẫn được khám — patient ID linh hoạt

### Architecture decisions
- **Option B selected**: Local only — no cloud, no MarianMT
- **Plugin system**: 1 core + 3 plugins Phase 1 = 85% thị trường
- **Phase 1 priority**: plugin_cdha → plugin_ngoai_tru → plugin_nha_khoa
- **ICD-10-VN** (QĐ5837) thay ICD-10-CA

---

## 4. OPEN ITEMS — WAITING-ANDY

| # | ID | Priority | Task |
|---|---|---|---|
| 1 | **KICKOFF-S10** | 🔴 BLOCKING | Andy ký Section 10 của PROJECT_KICKOFF → mở đường cho FID-VN-001 |
| 2 | **PILOT-CLINIC** | 🟡 | Andy arrange: 1 phòng khám CĐHA tư cho pilot |
| 3 | **LEGAL-REVIEW** | 🟡 | Confirm với luật sư: SOAP note AI có phải đăng ký thiết bị y tế không? |
| 4 | **GITHUB-VN** | 🟢 | Tạo repo riêng trên GitHub cho MediVoice_VN |

---

## 5. START NEXT SESSION

```powershell
cd C:\Projects\MediVoice_VN
# Baseline check (sau khi có code):
# python -m pytest tests/ -q
```

**Priority phiên tới — sau khi Andy ký S10:**
1. FID-VN-001: plugin_cdha.py — báo cáo CĐHA
2. FID-VN-002: plugin_ngoai_tru.py — Mẫu 15/BV1
3. Xóa L1b_translation (MarianMT) khỏi fork
4. Thay PII patterns → CCCD/CMND/BHYT

---

*MV-VN-SES-20260603-001 | MediVoice VN v0.1.0 | Documentation phase*
*Generated: 2026-06-03 | claude-sonnet-4-6*
