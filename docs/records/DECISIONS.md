# DECISIONS.md — MediVoice VN
# Architecture Decision Records (ADR) — lightweight
# Thay thế 20+ ISO docs bằng 1 file có cấu trúc.
# Format: Date | Decision | Why | Impact

---

## Architecture

| Date | Decision | Why | Impact |
|---|---|---|---|
| 2026-06-03 | **Option B: Local only** (no cloud) | NĐ13/2023 data residency + AI consistency for ISO | On-premise deployment bắt buộc |
| 2026-06-03 | **Xóa MarianMT** hoàn toàn | Output VN — không cần dịch VI→EN | Simplifies L1 pipeline significantly |
| 2026-06-03 | **Plugin system** (core + specialty) | 29 mẫu TT32 = 70% common + 30% specialty | L6 refactor: core generator + plugins/ folder |
| 2026-06-03 | **Báo cáo CĐHA là Use Case #1** | 30–50 ca/ngày × 200 chữ = điểm đau cao nhất | FID-VN-001 là ưu tiên tuyệt đối |

## Output & Compliance

| Date | Decision | Why | Impact |
|---|---|---|---|
| 2026-06-03 | **Output: TT32/2023 VN format** (không phải SOAP) | Pháp lý VN bắt buộc | Rewrite L6 generator |
| 2026-06-03 | **ICD-10-VN** (QĐ5837) thay ICD-10-CA | Chẩn đoán bắt buộc có mã VN | Build ICD-10-VN DB |
| 2026-06-03 | **Patient ID flexible** (không bắt buộc CCCD) | Luật KCB 2023: bệnh nhân không CCCD vẫn được khám | Khác CA — không SHA-256 bắt buộc |
| 2026-06-03 | **Human gate luôn bắt buộc** | Luật KCB 2023 Điều 62: BS phải ký | L4 không thể bypass |

## Process

| Date | Decision | Why | Impact |
|---|---|---|---|
| 2026-06-03 | **FID threshold: 100 LOC** (CA là 50 LOC) | CA quá rigid, làm chậm development | Tầng 2 (20–100 LOC) không cần FID |
| 2026-06-03 | **External review: chỉ safety/security** | CA review mọi module = quá chậm | Tiết kiệm 2–3 ngày per feature |
| 2026-06-03 | **4 files tracking thay vì 9 loại báo cáo** | CA over-documented — 126 files cho 1 dev | CLAUDE.md + BACKLOG + DECISIONS + CHANGELOG |

## Market

| Date | Decision | Why | Impact |
|---|---|---|---|
| 2026-06-03 | **Target: clinic tư trước BV công** | BV công = đấu thầu 6-18 tháng; clinic tư = 1-4 tuần | Go-to-market trực tiếp với BS |
| 2026-06-03 | **Không cạnh tranh FPT/Viettel** | Họ có 600+ BV — tích hợp là win-win | Plugin/add-on approach |
| 2026-06-03 | **Giá VNĐ, không USD** | $149/tháng (Dr.AI) quá cao cho VN | 500k–3M VNĐ/tháng |

---

## Template thêm decision mới

```
| YYYY-MM-DD | **Tên decision** | Lý do ngắn | Tác động |
```

*DECISIONS.md | MediVoice VN | Updated: 2026-06-03*
