# FID-VN-004 — VN-ROUTER-001
# Feature Intent Document
# Status: DRAFT — Chờ Andy approve
# Author: Claude Sonnet 4.6 | 2026-06-06
# Ref: DECISIONS.md ADR 2026-06-06 | DESIGN_REPORT_v1.1 Section 3 + 7

---

## APPROVE / REJECT

```
[ ] APPROVED — proceed to implement
[ ] REJECTED — reason: _______________
[ ] CONDITIONAL — change: _______________

Signed: Andy Phan | Date: ___/___/______
```

> Andy đọc xong → sửa dòng trên → gõ "đồng ý" hoặc "approve" trong chat.
> Claude sẽ bắt đầu implement ngay sau khi nhận approve.

---

## 1. WHY — Tại sao cần

**Vấn đề hiện tại:**
Canada pipeline (đang dùng) luôn sinh ra SOAP output {S, O, A, P} cho MỌI route.
Với route `lam_sang`, SOAP là format trung gian không cần thiết — VN cần Mẫu 15/BV-01 trực tiếp.

```
HIỆN TẠI (sai):
  BS nói → NER entities → generate_soap() → SOAP text
    → VN-ROUTER convert SOAP ngược lại → BenhAnNgoaiTru → PDF

ĐÚNG (thiết kế gốc PROJECT_KICKOFF §9d):
  BS nói → NER entities → BRANCH:
    lam_sang → BenhAnNgoaiTru trực tiếp → PDF
    cdha     → generate_soap() → SOAP (đúng dùng cho CĐHA)
```

**Hậu quả nếu không fix:** Pipeline Phase 0 không output được Mẫu 15/BV-01 — app không dùng được cho BS lâm sàng.

**ADR reference:** DECISIONS.md — "L6 branch tại NER entities (KHÔNG qua SOAP cho lam_sang)" — 2026-06-06

---

## 2. WHAT — Làm gì cụ thể

### Scope
- **File chính cần sửa:** `src/pipeline/p2_decision/l6_agent.py`
- **File mới cần tạo:** `src/pipeline/p3_output/l9_vn_router.py` (L6 generator cho lam_sang)
- **File cần bổ sung nhỏ:** `src/pipeline/p1_processing/l3_routing.py` (detect vn_route)
- **LOC estimate:** ~120-150 LOC (tầng 1 — FID bắt buộc)

### Thay đổi thiết kế

**Bước 1 — L3_ROUTING thêm vn_route detection:**
```python
# Thêm vào l3_routing.py — detect từ original_text VI keywords
def detect_vn_route(original_text: str) -> str:
    text = original_text.lower()
    cdha_kw  = ["siêu âm","x-quang","xquang","ct scan","mri","chụp","cđha","điện tim","ecg"]
    nha_kw   = ["răng","nha","nướu","lợi","nhổ răng","trám"]
    for kw in nha_kw:
        if kw in text: return "nha_khoa"
    for kw in cdha_kw:
        if kw in text: return "cdha"
    return "lam_sang"  # default
```

**Bước 2 — L6_AGENT thêm dispatch:**
```python
# Trong l6_agent.py handle() — sau extract_entities():
vn_route = payload.get("vn_route", "lam_sang")

if vn_route == "lam_sang":
    # NEW PATH: NER → BenhAnNgoaiTru trực tiếp
    from src.pipeline.p3_output.l9_vn_router import generate_mau15
    benh_an = generate_mau15(entities, payload)
    return {
        "ok": True, "stage": "L6_AGENT",
        "data": {**payload, "benh_an": benh_an, "vn_route": "lam_sang"}
    }
else:
    # EXISTING PATH: generate_soap() cho cdha/nha_khoa
    soap = _generator.generate_soap(entities, text)
    ...
```

**Bước 3 — l9_vn_router.py (file mới — logic chính):**
```python
def generate_mau15(entities, payload) -> BenhAnNgoaiTru:
    """NER entities → BenhAnNgoaiTru fields mapping"""

    # Mapping từ NER entities → Mẫu 15/BV-01 fields:
    VITAL     → kham_benh.sinh_hieu (mach, nhiet_do, huyet_ap, nhip_tho, spo2, can_nang)
    SYMPTOM   → ly_do.ly_do + hoi_benh.qua_trinh_benh_ly
    HISTORY   → hoi_benh.tien_su_ban_than
    MEDICATION→ don_thuoc.danh_sach_thuoc (ThuocKe per drug)
    ICD code  → kham_benh.ma_icd10 (từ L1d)
    FOLLOWUP  → don_thuoc.tai_kham
    # diagnosis text → kham_benh.chan_doan_ban_dau + chan_doan_ra_vien
```

---

## 3. ACCEPTANCE CRITERIA

Test phải PASS trước khi commit:

```
[ ] AC-001: lam_sang route → output có BenhAnNgoaiTru object (không phải SOAP)
[ ] AC-002: cdha route → output vẫn có soap_note {S,O,A,P} như cũ
[ ] AC-003: lam_sang + kê 2 thuốc → don_thuoc.danh_sach_thuoc có đúng 2 ThuocKe
[ ] AC-004: lam_sang + "huyết áp 120/80" → sinh_hieu.huyet_ap_tam_thu = 120
[ ] AC-005: lam_sang + "sốt 38.5" → sinh_hieu.nhiet_do = 38.5
[ ] AC-006: lam_sang + chẩn đoán → kham_benh.chan_doan_ban_dau không rỗng
[ ] AC-007: 210/210 existing tests vẫn PASS (không regression)
[ ] AC-008: iso_audit.py không có new 🔴 issues sau implement
```

---

## 4. CONSTRAINTS

```
KHÔNG sửa:     Canada pipeline core logic (L0→L5, L7→L10)
KHÔNG sửa:     generate_soap() trong l6_soap_generator.py
GIỮ NGUYÊN:    MarianMT (vẫn cần cho NER quality)
OUTPUT TIẾNG:  Mẫu 15/BV-01 = tiếng Việt (không phải tiếng Anh)
TEST:          100% PASS trước commit (ABSOLUTE RULE #2)
```

---

## 5. EFFORT ESTIMATE

```
l3_routing.py bổ sung detect_vn_route():   0.5 ngày
l9_vn_router.py (file mới, core mapping):   1.5 ngày
l6_agent.py dispatch:                       0.5 ngày
Tests AC-001..AC-008:                       1.0 ngày
─────────────────────────────────────────────────────
Total:                                      3.5 ngày
```

---

*FID-VN-004 | VN-ROUTER-001 | v1.0 DRAFT | 2026-06-06*
*Lưu tại: docs/dev/fids/FID-VN-004.md*
