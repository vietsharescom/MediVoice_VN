# CORRECTIVE_ACTION.md | DS-VN-CL10-CA
# ISO/IEC 42001:2023 Clause 10.2
# v1.0 | 2026-06-03

---

## QUY TRÌNH XỬ LÝ NONCONFORMITY

```
Phát hiện vấn đề (test fail / incident / audit finding)
    ↓
Tạo CA-VN-NNN trong file này
    ↓
Root cause analysis trong 48h
    ↓
Corrective action + code fix
    ↓
pytest → 100% PASS verification
    ↓
Close CA với ngày và evidence
```

## FORMAT CA ENTRY

```
| CA-VN-NNN | YYYY-MM-DD | Mô tả ngắn | Root cause | Action | Status | Verify |
```

## LOG

| CA ID | Ngày | Vấn đề | Root Cause | Action | Status | Verify |
|---|---|---|---|---|---|---|
| (Trống — chưa có nonconformity) | | | | | | |

---

## MỨC ĐỘ NONCONFORMITY

| Mức | Định nghĩa | SLA |
|---|---|---|
| CRITICAL | Vi phạm pháp lý, patient safety | 24h |
| MAJOR | Vi phạm ISO control, test fail | 48h |
| MINOR | Documentation gap, style | 7 ngày |
| OBS | Observation, improvement | Next sprint |

---

*DS-VN-CL10-CA | CORRECTIVE_ACTION v1.0 | 2026-06-03*
