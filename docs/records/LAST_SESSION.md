# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260613
## Thời gian: 2026-06-13
## Version: v0.11.19 → v0.11.24

---

> **Lưu ý phạm vi**: phiên này gộp 2 phần việc:
> (A) Phiên catch-up cho 4 versions (v0.11.20→v0.11.23) đã commit vào master ở
>     các phiên trước nhưng CHƯA TỪNG có LAST_SESSION/PROJECT_PROGRESS entry
>     (FID-VN-020/CT-011, CT-054, CT-055, CT-056).
> (B) Phiên hiện tại: FID-VN-021 (CT-060d, research note) + docs-sync session
>     close (PENDING_REQUESTS/BACKLOG/PROJECT_PROGRESS/CLAUDE.md/CHANGELOG).

---

## Trạng thái đầu → cuối
v0.11.19 | 973/973 tests → v0.11.24 | 984/984 tests (master) — 1009/1009 trên `experiment/fid-vn-021-phoneme`

## 1. Actions Completed

**Catch-up (v0.11.20→v0.11.23, đã commit trước, nay backfill docs):**
- FID-VN-020 (ORCH-001/CT-011) ✅ — `scripts/orchestrator.py::detect_confusion/
  create_consultation_request/close_session` + `tests/unit/test_orchestrator.py`
  (+11 tests). Commit `cde09f3`.
- CT-054 ✅ — fix GT/NOTE spacing bug (`data/eval/ref_voice_transcripts_review.txt`,
  3 clips) → regenerate `data/eval/bench_002b_results.json`. Drug Recall
  0.545→0.615, Drug Precision 0.857→1.0, Diag CEER cải thiện.
- CT-055 ✅ — fix remaining spacing bug across all 57 clips → Drug Recall
  0.556→0.615 (TP 6→8, FP 1→0), Precision→100%, Diag CEER ALL 71.4%→21.4%.
- CT-056 ✅ — fix patient-name "là"-prefix NER bug, gender dropdown
  case-mismatch, temp audio path %TEMP%→`data/tmp/` (ổ D).

**Phiên hiện tại (FID-VN-021, CT-060d):**
- Files tạo:
  - `src/core/vn_phoneme.py` — `decompose_syllable()`, `phoneme_key()`
    (onset-canon + coda-drop, dựa trên ViSpeechFormer / Syllabic-Structure
    Decoder research).
  - `tests/unit/test_vn_phoneme.py` — 25 tests.
  - `data/eval/bench_002b_results_fid021.json` — A/B benchmark output.
- Files sửa:
  - `src/core/l1b_drug_correct.py` — `_fuzzy_match()` rewrite: thêm phoneme-key
    2nd-pass scoring (`PHONEME_WEIGHT=0.9`), `_phoneme_alias_index()` cache.
    `alias_map` 1913 entries KHÔNG đổi (CT-042 frozen).
- Code generated: ~150 LOC (module + integration) + 25 tests (~120 LOC).
- Tests chạy: 1009/1009 PASS (experiment branch), 984/984 PASS (master).
- Benchmark: BENCH-002b A/B — byte-identical kết quả vs baseline
  (Drug Recall 0.615, Precision 1.0 unchanged).

**Docs-sync (phiên này, trên master):**
- `docs/records/PENDING_REQUESTS.md` — CT-011/CT-054/CT-055/CT-056/FID-VN-021
  → DONE với version + benchmark delta.
- `docs/records/BACKLOG.md` — FID-VN-021 section DRAFT → DONE (research note).
- `docs/records/PROJECT_PROGRESS.md` — header v0.11.24, METRICS table cập nhật
  benchmark mới (Drug Recall 61.5%/Precision 100%/Diag CEER 21.4%/Vitals CEER
  28.9%/WER 18.3%), "PHIÊN TIẾP THEO" table refresh (bỏ FID-VN-020 đã done),
  2 dòng LỊCH SỬ PHIÊN mới (catch-up + SES-20260613).
- `CLAUDE.md` — CURRENT STATE → v0.11.24, 984/984, pending/next-task refresh.
- `CHANGELOG.md` — entry mới `[v0.11.24]` mô tả docs-sync + research note.

## 2. Decisions

- **Owner Decisions (Andy)**:
  - APPROVE `fids/FID-VN-021.md` (Status: approve, "ĐÃ APPROVE") — cho phép
    implement phoneme-key re-scoring trên branch experiment.
- **Technical Decisions (Claude)**:
  - FID-VN-021: A/B benchmark byte-identical vs baseline → áp dụng precedent
    CT-028 ("nếu cả Recall và Precision không cải thiện, giữ làm research note
    trên experiment branch, KHÔNG merge vào master"). Branch
    `experiment/fid-vn-021-phoneme` giữ lại làm tài liệu tham khảo (cùng nhóm
    với `experiment/groq-degallucination`, `experiment/local-accuracy`).
  - Docs-sync: chọn backfill 4 versions chưa đóng phiên (v0.11.20-23) VÀO
    CÙNG session report này (1 dòng "catch-up" trong LỊCH SỬ PHIÊN) thay vì
    tạo 4 LAST_SESSION.md riêng — vì các version đó đã có CHANGELOG entries
    đầy đủ, chỉ thiếu cross-doc sync.
  - Yêu cầu của Andy về "Session Closure Report" theo khung Jira/Agile/Scrum/
    DevOps/AI-Coding-Agent/ISO 42001: áp dụng các category THỰC TẾ áp dụng
    được (xem mục 7-10 dưới) bằng dữ liệu thật từ BACKLOG.md/
    PENDING_REQUESTS.md (CT/PA/TP/FID-xxx — đây là hệ thống Kanban-equivalent
    của project này), KHÔNG fabricate Story Points/Velocity/Sprint Burndown vì
    project KHÔNG dùng các đơn vị đó.

## 3. Architecture Changes

- L1b (`src/core/l1b_drug_correct.py::_fuzzy_match`) — thêm phoneme-key 2nd-pass
  CHỈ TRÊN `experiment/fid-vn-021-phoneme`, KHÔNG ảnh hưởng master. Pipeline
  L0→L10 trên master KHÔNG đổi (Pipeline FROZEN — ABSOLUTE RULE #1 giữ nguyên).
- `scripts/orchestrator.py` (master, từ v0.11.20) — orchestrator v1.0 đã có
  `detect_confusion`/`create_consultation_request`/`close_session`, nhưng các
  hàm này CHƯA được gọi tự động trong session-close flow của Claude (vẫn làm
  thủ công theo CLAUDE.md §3 6-step). Cơ hội tích hợp cho phiên sau.

## 4. Tasks Created

- (không có CT/PA/TP mới phát sinh phiên này — FID-VN-021 đã đóng thành
  research note, không phát sinh follow-up task ngoài CT-053 đã có)

## 5. Pending Items

- [CT-053] Vietnamese Medical Phonetic Encoder (Phase 2) — chờ pilot audio,
  hướng dài hạn thay `_phonological_variants()` enumerate-based.
- [CT-027] Ciprofloxacin alias "si pô lo siêu âm si" — chờ audio mẫu mới.
- [CT-049] Andy re-test clip TMH lần 3.
- [PA-020/PA-021] Andy test UI FID-VN-017/018.
- [PA-015/PA-017/PA-018] Andy test UI FID-VN-013/014/015/016.
- [CT-019] 🔴 Debug A2 VAD-chunk regression — cần audio mẫu.
- [TRAIN-001] 🔴 Full fine-tune PhoWhisper (VietMed 9207 samples) — ưu tiên cao
  nhất theo CT-028, chờ GPU/quota tốt hơn hoặc pilot audio.
- [SY-001] Weekly ISO audit (`iso_audit.py --weekly`) — due Session 7, kiểm tra
  ở BƯỚC 6 session-close.

## 6. Risks / Confusions

- (không có chỗ confused/<70% confidence trong phiên này)
- Risk theo dõi: Drug Recall thật (61.5%) vẫn dưới target ≥70% — TRAIN-001 vẫn
  là CRITICAL GAP, chưa có giải pháp ngoài fine-tune (Groq hybrid đã REJECTED
  — CT-028).
- `experiment/*` branches (3 nhánh: groq-degallucination, local-accuracy,
  fid-vn-021-phoneme) tích lũy làm reference — không gây risk nhưng cần dọn
  định kỳ nếu quá nhiều (chưa đến ngưỡng).

---

## 7. Decisions Approved / Pending (Governance view)

| Decision | Status | Ref |
|---|---|---|
| FID-VN-021 (phoneme-key re-scoring) | ✅ Approved by Andy → implemented → research note (not merged) | `fids/FID-VN-021.md` |
| FID-VN-020 (Orchestrator automation) | ✅ Approved + implemented (v0.11.20, catch-up) | `fids/FID-VN-020.md` |
| CT-028 precedent (no Groq hybrid, fine-tune only) | ✅ Standing decision, re-applied to FID-VN-021 | BACKLOG.md |

## 8. New Requirements / Change Requests

- Andy requested session-close reports adopt an extended "Project Audit &
  Continuity Report" structure (Jira/Agile/Scrum/DevOps/AI-Coding-Agent/ISO
  42001-style). This LAST_SESSION.md is the first instance applying that
  structure using this project's real CT/PA/TP/FID-xxx tracking (sections
  7-10). No code/process change request beyond documentation format.

## 9. Risks / Issues / Technical Debt Register

| Type | Item | Severity | Status |
|---|---|---|---|
| Risk | Drug Recall real (61.5%) < target (70%) | 🔴 High | Open — TRAIN-001 |
| Risk | HN-region WER (29.2%) vs DN/SG (16.3%) | 🟡 Medium | Open — accent gap |
| Tech Debt | 4 versions (v0.11.20-23) shipped without session-close docs sync | 🟢 Resolved this session | Closed |
| Tech Debt | `experiment/*` branches accumulating (3 active) | 🟢 Low | Monitor |
| Issue | CT-019 A2 VAD-chunk regression (hallucination) | 🔴 High | Open — needs audio |

## 10. Task Governance Table (BACKLOG.md / PENDING_REQUESTS.md = Kanban-equivalent)

> Project này KHÔNG dùng Jira/Story Points/Sprint Velocity. Bảng dưới map
> trực tiếp ID thật từ `docs/records/BACKLOG.md` + `docs/records/PENDING_REQUESTS.md`.

| ID | Mô tả | Owner | Status | Version | Note |
|---|---|---|---|---|---|
| FID-VN-020/CT-011 | Orchestrator v1.0 automation | Claude | ✅ DONE | v0.11.20 | Catch-up backfill |
| CT-054 | Fix GT spacing bug (3 clips) + regen baseline | Claude | ✅ DONE | v0.11.21 | Catch-up backfill |
| CT-055 | Fix GT spacing bug (all 57 clips) | Claude | ✅ DONE | v0.11.22 | Catch-up backfill |
| CT-056 | Fix patient-name/gender UI bugs + temp path | Claude | ✅ DONE | v0.11.23 | Catch-up backfill |
| FID-VN-021/CT-060d | L1b phoneme-key re-scoring | Claude | ✅ DONE (research note) | — (not merged) | byte-identical A/B → CT-028 precedent |
| CT-053 | Vietnamese Medical Phonetic Encoder Phase 2 | Claude | ⏳ PENDING | — | chờ pilot audio |
| CT-027 | Ciprofloxacin alias audio | Andy+Claude | ⏳ PENDING | — | chờ audio mẫu |
| CT-019 | A2 VAD-chunk regression debug | Claude | 🔴 PENDING | — | cần audio |
| TRAIN-001 | Full fine-tune PhoWhisper | Andy+Claude | 🔴 PENDING (top priority) | — | GPU/pilot audio |

## 11. Interrupted Task Register

- (không có task bị interrupt giữa phiên — FID-VN-021 hoàn thành trọn vẹn
  trước khi chuyển sang docs-sync)

## 12. Open Discussion Register

- Câu hỏi mở (chưa cần trả lời ngay): liệu `scripts/orchestrator.py::close_session`
  (FID-VN-020, đã implement v0.11.20) có nên được tích hợp vào quy trình BƯỚC
  1-6 của CLAUDE.md §3 để tự động hóa một phần docs-sync này trong tương lai —
  để phiên sau xem xét, KHÔNG quyết định trong phiên này.

## 13. AI-Assisted Development Governance Note

- Toàn bộ code/docs trong phiên này được tạo bởi Claude Code (model
  `claude-sonnet-4-6`) dưới sự giám sát của Andy Phan (chủ dự án), theo
  CLAUDE.md ABSOLUTE RULE #2 (100% tests PASS trước commit) và FID-approval
  workflow (Tầng 1, >100 LOC qua FID + Andy approve). FID-VN-021 là ví dụ:
  Claude đề xuất → viết FID → Andy approve ("ĐÃ APPROVE") → Claude implement
  trên branch riêng → A/B benchmark → Claude quyết định research-note theo
  precedent đã có (CT-028), Andy không cần can thiệp thêm cho quyết định
  kỹ thuật cấp này.

## 14. DevOps & Compliance Snapshot

- bandit src/: 0 HIGH / 9 MEDIUM (pre-existing, không đổi) / 2 LOW.
- pytest: 984/984 PASS (master).
- Pipeline L0→L10: FROZEN, không đổi (ABSOLUTE RULE #1).
- Data residency: không đổi (VN-only, SQLite local).
- L4 Human Gate: không đổi (per-drug confirm gate, FID L4-REDESIGN-001).

---

## Phiên tiếp theo — thứ tự ưu tiên
1. **TRAIN-001** 🔴 — Full fine-tune PhoWhisper (VietMed 9207 samples, nhiều
   epoch) khi có GPU/quota tốt hơn (Kaggle 30h/tuần) hoặc pilot audio.
2. **CT-049** — Andy re-test clip TMH lần 3 (server local `http://localhost:8000`).
3. **CT-019** 🔴 — Debug A2 VAD-chunk regression nếu có audio mẫu.
4. **CT-027** — Ciprofloxacin alias nếu Andy có audio mẫu mới.
5. **PA-020/PA-021, PA-015/PA-017/PA-018** — Andy test UI các FID-VN-013→018.
