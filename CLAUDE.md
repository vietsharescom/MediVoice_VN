# CLAUDE.md — MediVoice VN
# ISO/IEC 42001:2023 | ISO_VN v1.0 | v1.1
# Owner: Andy Phan (Viet) | Maple Leaf Group
# Path: C:\Projects\MediVoice_VN | Forked from: MediVoice AI (CA) v2.61.3

---

## IDENTITY

| Field | Value |
|---|---|
| Project | MediVoice VN — Bác sĩ đọc → Bệnh án TT32/2023 tự động |
| Market | Vietnam — phòng khám tư nhân, trung tâm CĐHA |
| Stack | Python 3.10, FastAPI, PhoWhisper-small, PhoBERT+CRF, SQLite, Fernet |
| Compliance | ISO_VN: NĐ13/2023 · TT32/2023 · TT13/2025 · Luật AI 134/2025 |
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
| Version | v0.1.0 |
| Status | Documentation phase — code chưa bắt đầu |
| Tests | N/A |
| Blocker | Andy ký PROJECT_KICKOFF Section 10 |
| Next task | FID-VN-001: plugin_cdha.py (sau khi S10 approved) |

**Key files:**
- [PROJECT_KICKOFF.md](docs/cl08_operation/PROJECT_KICKOFF.md) — S1–S9 done, **S10 chờ Andy ký**
- [BACKLOG.md](docs/records/BACKLOG.md) — task tracker
- [DECISIONS.md](docs/records/DECISIONS.md) — key decisions log
- [CHANGELOG.md](CHANGELOG.md) — version history

---

## PIPELINE (FROZEN)

```
L0 → L1 → L2 → L3 → L4 → L5 → L6[+PLUGIN] → L7 → L8 → L9 → L10
```

**Plugins Phase 1:**
1. `plugin_cdha.py` — báo cáo siêu âm/X-quang ← FID-VN-001
2. `plugin_ngoai_tru.py` — Mẫu 15/BV1 ← FID-VN-002
3. `plugin_nha_khoa.py` — Mẫu 16/BV1 ← FID-VN-003

---

## FEATURE WORKFLOW — 3 TẦNG

### Tầng 1: Lớn (> 100 LOC | API mới | thay đổi architecture)
```
1. Viết FID (1 trang: Why + What + Acceptance criteria)
2. Andy approve
3. Implement + tests (100% PASS)
4. CHANGELOG entry
5. External review CHỈ KHI safety/security risk
6. Commit: feat(VN-L{N}): description [FID-VN-NNN]
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
(Không cần FID, không cần BACKLOG entry)
```

---

## ABSOLUTE RULES

1. Pipeline L0→L10 FROZEN — thay đổi chỉ qua FID
2. 100% tests PASS trước mọi commit
3. BS phải approve — AI chỉ tạo draft (Luật KCB 2023)
4. Data on-premise — không cloud nước ngoài (NĐ13/2023)
5. Output theo mẫu TT32/2023 — không tự do format
6. ICD-10-VN trong phần Chẩn đoán (QĐ5837)
7. STAY IN PROJECT DIRECTORY — C:\Projects\MediVoice_VN

---

## LEGAL CONSTRAINTS (HARD — không thể bỏ)

| Luật | Yêu cầu | Kiến trúc |
|---|---|---|
| NĐ13/2023 | Data ở VN | On-premise / cloud VN |
| TT32/2023 | Mẫu bệnh án chuẩn | Plugin outputs TT32 format |
| Luật KCB 2023 | BS phải ký | Human gate L4 bắt buộc |
| TT13/2025 | Chữ ký số + HL7 FHIR | Deadline 31/12/2026 |
| Luật AI 134/2025 | Audit trail | L10 immutable log |

---

## EXTERNAL REVIEW — CHỈ KHI CẦN

**Cần review (ChatGPT + Grok):**
- L4 human gate, L5 PII handling, L10 audit — safety critical
- Encryption, data access control — security
- Major architecture change

**Không cần review:**
- Plugin output formatting
- ICD-10 mapping, vocab
- Config, test files, docs

---

## KEY DECISIONS (xem DECISIONS.md để đầy đủ)

| Decision | Rationale |
|---|---|
| Option B: Local only | NĐ13/2023 + AI consistency |
| Output: TT32/2023 (VI) | Pháp lý bắt buộc |
| Plugin system | 29 forms = 1 core + N plugins |
| Xóa MarianMT | Output VN — không cần dịch |
| FID threshold: 100 LOC | Lean > paperwork |
| Patient ID: flexible | VN law không bắt buộc CCCD |

---

## SESSION END

```
1. Update BACKLOG.md (move DOING → DONE, add new tasks)
2. Update CHANGELOG.md nếu có code thay đổi
3. Update CURRENT STATE section bên trên
4. Báo: "Done. Remaining: {task list}"
```

*(Không cần tạo file session report riêng)*

---

*MediVoice VN | ISO_VN v1.0 | Updated: 2026-06-03*
