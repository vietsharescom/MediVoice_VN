# FID-VN-020 — Orchestrator v1.0 Automation (ORCH-001, CT-011)
# Feature Intent Document | ISO_VN v1.0
# Status: APPROVED

| Field | Value |
|---|---|
| FID ID | FID-VN-020 |
| Layer | Tooling — `scripts/orchestrator.py` (KHÔNG thuộc L0-L10 pipeline, KHÔNG FROZEN) |
| LOC estimate | ~180-220 LOC (3 new functions + tests) |
| Risk level | LOW — dev-tooling only, không chạm pipeline/runtime API |
| Created | 2026-06-12 |
| Approved by | Andy |
| Approved date | 2026-06-12 |

---

## WHY (Tại sao cần feature này?)

`scripts/orchestrator.py` (355 LOC, prototype 2026-06-09) hiện có:
- `start_session()` — đọc CLAUDE.md/BACKLOG/LAST_SESSION (Tầng 1 memory)
- `consult()` / `consistency_check()` — multi-AI Groq/OpenAI/xAI/OpenRouter, lưu
  `docs/records/consultations/ORCH-CONSULT-*.json`
- `close_session()` — **CHỈ IN RA CHECKLIST** (6 bước), KHÔNG tự thực hiện

CLAUDE.md mục "CONTINUOUS IMPROVEMENT" yêu cầu mỗi phiên:
1. Khi confused/multiple-options/<70% confident → generate consultation request
   theo `docs/dev/CONSULTATION_TEMPLATE.md` → `docs/records/consultations/CONS-YYYYMMDD-NNN.md`
2. Khi đóng phiên → cập nhật 5 file (BACKLOG/PROJECT_PROGRESS/CHANGELOG/LAST_SESSION/
   CLAUDE.md CURRENT STATE) + `iso_audit.py --increment-session` + commit/push

Hiện tại Claude (tôi) làm 2 việc này **thủ công mỗi phiên** (đúng nhưng tốn nhiều
tool calls/tokens — vd phiên SES-20260612b vừa rồi: 6 file edits riêng lẻ). ORCH-001
tự động hoá phần "máy móc" (đọc template, ghi file đúng format, chạy iso_audit, git),
Claude vẫn quyết định NỘI DUNG (text mô tả, decisions, risks) — automation chỉ giảm
boilerplate, không thay phán đoán.

## WHAT (Feature làm gì? Input/Output?)

### 1. `detect_confusion(note: str) -> dict`
**Input**: 1 đoạn text Claude tự viết mô tả tình huống hiện tại (vd "2 cách implement X,
cả 2 đều hợp lý, chưa rõ option nào đúng cho VN").
**Output**: `{"should_consult": bool, "matched_triggers": ["T1","T5",...], "reason": str}`
— heuristic match các từ khóa trigger T1-T5 từ `docs/dev/CONSULTATION_TEMPLATE.md`
(vd "≥2 option"/"chưa rõ"/"<70%"/"hỏi thêm AI khác"/"so sánh"). Đây là **gợi ý**, Claude
vẫn tự quyết định có gọi `create_consultation_request()` hay không — KHÔNG tự động
chặn workflow.

### 2. `create_consultation_request(topic, question, options, hard_constraints, analysis) -> Path`
**Input**: dict đã điền theo cấu trúc `CONSULTATION_TEMPLATE.md` (QUESTION, OPTIONS
EVALUATED A/B[/C], HARD CONSTRAINTS, CLAUDE'S CURRENT ANALYSIS — Claude soạn nội dung,
hàm chỉ format + ghi file).
**Output**: ghi `docs/records/consultations/CONS-YYYYMMDD-NNN.md` (NNN tự tăng theo
ngày), trả về `Path`. Tùy chọn: nếu `--auto-send` + có API key, gọi `multi_ai_consult()`
hiện có và append responses vào cùng file.

### 3. `close_session(updates: dict, push: bool = False) -> dict`
**Input**: dict các đoạn text Claude đã soạn cho từng file:
```python
{
  "backlog_entries": [...],       # list of (task_id, status, description) → BACKLOG.md
  "progress_row": "...",          # 1 dòng markdown → PROJECT_PROGRESS.md LỊCH SỬ PHIÊN
  "changelog_entry": "...",       # block markdown → CHANGELOG.md (sau dòng "# CHANGELOG")
  "current_state": {...},         # dict Version/Status/Tests/Pending/Next task → CLAUDE.md CURRENT STATE table
  "last_session_md": "...",       # nội dung đầy đủ LAST_SESSION.md (Claude soạn theo 6-category template)
}
```
**Output**:
- Ghi/patch 5 file trên (string insert tại marker đã biết — KHÔNG parse/regenerate
  toàn file, tránh phá format)
- Chạy `python scripts/iso_audit.py --increment-session` (subprocess, capture output)
- `git add -A && git commit -m "chore(session-end): ..."` — message do Claude cung cấp
- `git push` **CHỈ KHI `push=True`** (default `False` — Claude vẫn phải xác nhận với
  Andy trước khi push, theo nguyên tắc "Executing actions with care")
- Trả về `{"committed": bool, "commit_hash": str, "pushed": bool, "iso_audit_output": str}`

**Side effects**: ghi file + git commit/push (nếu `push=True`) — đây là thay đổi shared
state, do đó `push=True` mặc định FALSE, Claude phải tự gọi `git push` riêng (như hiện
tại) hoặc truyền `push=True` SAU KHI đã thông báo Andy.

## ACCEPTANCE CRITERIA (Khi nào gọi là DONE?)

- [ ] `detect_confusion()` — unit test với câu chứa/không chứa trigger keywords T1-T5
- [ ] `create_consultation_request()` — sinh file đúng format `CONSULTATION_TEMPLATE.md`,
  số thứ tự NNN tự tăng đúng trong cùng ngày (test với 2 lần gọi liên tiếp)
- [ ] `close_session(updates, push=False)`:
  - Patch đúng 5 file tại marker xác định (test bằng tmp_path copy của 5 file thật,
    KHÔNG sửa file thật trong test)
  - Gọi `iso_audit.py --increment-session` qua subprocess (mock trong test, integration
    test riêng KHÔNG mock chạy thật trên branch — không trên CI)
  - `git commit` thật chỉ test trên tmp git repo riêng (KHÔNG commit vào repo thật từ
    test suite)
  - `push=False` default — verified bằng test rằng `git push` KHÔNG được gọi nếu
    `push` không truyền
- [ ] 958/958 tests hiện có PASS + N tests mới, bandit 0 HIGH
- [ ] CHANGELOG entry
- [ ] **KHÔNG thay đổi** `start_session()`/`consult()`/`consistency_check()` hiện có
  (chỉ thêm function mới + CLI subcommands)

## RISKS

| Risk ID | Mô tả | Kiểm soát |
|---|---|---|
| R-ORCH-01 | `close_session()` patch sai marker → hỏng format BACKLOG/PROJECT_PROGRESS/CHANGELOG/CLAUDE.md (file quan trọng nhất của dự án) | Patch bằng string-anchor cụ thể (vd insert sau dòng `# BACKLOG.md ...`), test trên copy tmp_path trước; Claude LUÔN review diff trước khi để `close_session` ghi file thật (giữ thói quen hiện tại: Edit tool review-able) |
| R-ORCH-02 | `git push` tự động khi chưa có sự đồng ý Andy | `push=False` default; CLAUDE.md session protocol vẫn yêu cầu Claude báo cáo trước khi push — không đổi |
| R-ORCH-03 | `create_consultation_request()` sinh file trùng NNN nếu chạy 2 process song song (multi-machine live-sync, đã từng xảy ra — xem LAST_SESSION SES-20260612) | Đọc danh sách file hiện có trong `docs/records/consultations/` trước khi tính NNN tiếp theo (không dùng counter riêng) |

## TESTS REQUIRED

- [ ] `tests/unit/test_orchestrator.py` (mới):
  - `test_detect_confusion_trigger_keywords`
  - `test_create_consultation_request_format_and_numbering`
  - `test_close_session_patches_files_tmp_path` (dùng `tmp_path` fixture, copy 5 file
    mẫu nhỏ, verify patch đúng vị trí)
  - `test_close_session_push_false_by_default` (mock `subprocess.run`, assert không
    có call chứa `"push"`)
- [ ] 958/958 existing PASS không đổi

## COMMIT FORMAT

```
feat(tooling): orchestrator detect_confusion + create_consultation_request + close_session automation [FID-VN-020]
```

---

*FID Template | ISO_VN v1.0 | MediVoice VN*
*File: fids/FID-VN-020.md*
