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

- [x] `detect_confusion()` — unit test với câu chứa/không chứa trigger keywords T1-T5
  → `test_detect_confusion_trigger_keywords` (T1), `test_detect_confusion_t5_low_confidence`
  (T5), `test_detect_confusion_no_trigger`
- [x] `create_consultation_request()` — sinh file đúng format `CONSULTATION_TEMPLATE.md`,
  số thứ tự NNN tự tăng đúng trong cùng ngày (test với 2 lần gọi liên tiếp)
  → `test_create_consultation_request_format_and_numbering` (`-001.md`/`-002.md`,
  verify QUESTION/OPTIONS/HARD CONSTRAINTS/ANALYSIS sections)
- [x] `close_session(updates, push=False)`:
  - Patch đúng 5 file tại marker xác định (test bằng tmp_path, KHÔNG sửa file thật)
    → `_patch_backlog`/`_patch_project_progress`/`_patch_changelog`/`_patch_claude_md`
    mỗi hàm có unit test riêng trên `tmp_path` (TestPatchHelpers)
  - Gọi `iso_audit.py --increment-session` qua subprocess (mock trong test)
    → mocked via `patch("scripts.orchestrator.subprocess.run")` trong
    `TestCloseSessionPushDefault`
  - `git commit` — mocked trong unit tests (không commit vào repo thật từ test suite)
  - `push=False` default — verified: `test_close_session_push_false_by_default`
    (assert không có call chứa `"push"`) +
    `test_close_session_push_true_calls_git_push` (push=True → git push gọi)
- [x] 973/973 tests hiện có PASS + 11 tests mới = **984/984 PASS**, bandit 0 HIGH
  (9 MEDIUM pre-existing không đổi, LOW 2→13 — subprocess B404/B603/B607 mới từ
  `close_session()`, không phải HIGH/MEDIUM)
- [x] CHANGELOG entry — v0.11.20
- [x] **KHÔNG thay đổi** `start_session()`/`consult()`/`consistency_check()` hiện có
  (chỉ thêm 3 hàm mới + helper `_patch_*`/`_next_consultation_number`/
  `_write_last_session`; hàm cũ `close_session()` (checklist) đổi tên thành
  `print_close_checklist()`, CLI `close` subcommand cập nhật tương ứng)

## RISKS

| Risk ID | Mô tả | Kiểm soát |
|---|---|---|
| R-ORCH-01 | `close_session()` patch sai marker → hỏng format BACKLOG/PROJECT_PROGRESS/CHANGELOG/CLAUDE.md (file quan trọng nhất của dự án) | Patch bằng string-anchor cụ thể (vd insert sau dòng `# BACKLOG.md ...`), test trên copy tmp_path trước; Claude LUÔN review diff trước khi để `close_session` ghi file thật (giữ thói quen hiện tại: Edit tool review-able) |
| R-ORCH-02 | `git push` tự động khi chưa có sự đồng ý Andy | `push=False` default; CLAUDE.md session protocol vẫn yêu cầu Claude báo cáo trước khi push — không đổi |
| R-ORCH-03 | `create_consultation_request()` sinh file trùng NNN nếu chạy 2 process song song (multi-machine live-sync, đã từng xảy ra — xem LAST_SESSION SES-20260612) | Đọc danh sách file hiện có trong `docs/records/consultations/` trước khi tính NNN tiếp theo (không dùng counter riêng) |

## TESTS REQUIRED

- [x] `tests/unit/test_orchestrator.py` (mới, 11 tests):
  - `test_detect_confusion_trigger_keywords`, `test_detect_confusion_t5_low_confidence`,
    `test_detect_confusion_no_trigger`
  - `test_create_consultation_request_format_and_numbering`
  - `test_patch_backlog_replaces_existing_heading`, `test_patch_backlog_inserts_new_heading`,
    `test_patch_project_progress_appends_row`, `test_patch_changelog_inserts_before_first_entry`,
    `test_patch_claude_md_updates_current_state` (thay cho
    `test_close_session_patches_files_tmp_path` — patch logic test theo từng hàm
    `_patch_*` riêng, dễ debug hơn 1 test lớn)
  - `test_close_session_push_false_by_default`, `test_close_session_push_true_calls_git_push`
- [x] 973/973 existing PASS + 11 mới = 984/984 PASS

## COMMIT FORMAT

```
feat(tooling): orchestrator detect_confusion + create_consultation_request + close_session automation [FID-VN-020]
```

---

*FID Template | ISO_VN v1.0 | MediVoice VN*
*File: fids/FID-VN-020.md*
