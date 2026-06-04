# FID-VN-004 — VN-ROUTER-001: L6 branch NER→Mẫu 15/BV-01
# Feature Intent Document | ISO_VN v1.0
# Status: DRAFT → **AWAITING APPROVAL** → APPROVED → DONE

| Field | Value |
|---|---|
| FID ID | FID-VN-004 |
| Layer | L6 (l6_agent.py) + L3 (l3_routing.py) |
| LOC estimate | ~130 LOC |
| Risk level | HIGH (thay đổi L6 — frozen layer — FID bắt buộc) |
| Created | 2026-06-06 |
| Approved by | *(chờ Andy Phan)* |
| Approved date | *(chờ)* |

---

## WHY (Tại sao cần feature này?)

Canada pipeline hiện sinh SOAP {S,O,A,P} cho MỌI route. Với `lam_sang`, SOAP là trung gian thừa — VN yêu cầu Mẫu 15/BV-01 trực tiếp từ NER entities.

**Hậu quả nếu không fix:** App không output được Mẫu 15/BV-01 → BS không dùng được → Phase 0 không thể pilot.

**Root cause:** PROJECT_KICKOFF §9d nói "Rewrite L6 for VN" nhưng phiên 2026-06-05 port Canada pipeline (có SOAP). VN-ROUTER-001 là bước fix đúng hướng thiết kế gốc.

**ADR:** DECISIONS.md — 2026-06-06 — "L6 branch tại NER entities, không qua SOAP cho lam_sang"

---

## WHAT (Feature làm gì?)

**Input:** L6_AGENT nhận payload với `vn_route` (từ L3) + NER entities đã extract

**Output:**
- `lam_sang` → `BenhAnNgoaiTru` object (Mẫu 15/BV-01, tiếng Việt)
- `cdha` / `nha_khoa` → giữ nguyên `soap_note` (Canada flow)

**Side effects:** Không thay đổi L0-L5, L7-L10. Không break Canada pipeline.

**Files thay đổi:**
```
src/pipeline/p1_processing/l3_routing.py    — thêm vn_route detection (~20 LOC)
src/pipeline/p2_decision/l6_agent.py         — thêm dispatch lam_sang/cdha (~25 LOC)
src/pipeline/p2_decision/l6_mau15_generator.py — file mới: generate_mau15() (~85 LOC)
  Tái sử dụng: src/core/l6_generate_form.generate_benh_an() (đã có sẵn)
  generate_mau15() chỉ làm: Canada NER entities → form_data format → gọi generate_benh_an()

Lưu ý: src/core/l6_generate_form.py đã được fix trước khi FID implement:
  - Bug: qua_trinh_benh_ly dùng nhầm ly_do → đã fix (dùng trieu_chung list)
  - Bug: patient_name từ transcribe request bị mất → đã fix (lưu vào form_data)
  - Bug: l3_route detect từ form_data only → đã fix (thêm transcript fallback)
```

**Mapping NER entities → Mẫu 15/BV-01:**
```
VITAL      → kham_benh.sinh_hieu (mach, nhiet_do, huyet_ap, nhip_tho, spo2, can_nang)
SYMPTOM    → ly_do.ly_do + hoi_benh.qua_trinh_benh_ly
HISTORY    → hoi_benh.tien_su_ban_than
MEDICATION → don_thuoc.danh_sach_thuoc (ThuocKe: ten_thuoc, ham_luong, so_lan_ngay, so_ngay)
ICD code   → kham_benh.ma_icd10 (từ L1d lookup)
diagnosis  → kham_benh.chan_doan_ban_dau + chan_doan_ra_vien
FOLLOWUP   → don_thuoc.tai_kham
```

---

## ACCEPTANCE CRITERIA (Khi nào gọi là DONE?)

- [ ] lam_sang route → output có `BenhAnNgoaiTru` object (không phải SOAP)
- [ ] cdha route → output vẫn có `soap_note {S,O,A,P}` như cũ
- [ ] lam_sang + "kê Amoxicillin 500mg" → `don_thuoc.danh_sach_thuoc` có 1 ThuocKe đúng
- [ ] lam_sang + "huyết áp 120/80" → `sinh_hieu.huyet_ap_tam_thu = 120`
- [ ] lam_sang + "sốt 38.5" → `sinh_hieu.nhiet_do = 38.5`
- [ ] lam_sang + chẩn đoán → `chan_doan_ban_dau` không rỗng
- [ ] 210/210 existing tests vẫn PASS (không regression)
- [ ] Tests 100% PASS
- [ ] CEER không tăng sau khi thêm feature
- [ ] CHANGELOG entry
- [ ] Không vi phạm frozen layers

---

## RISKS

| Risk ID | Mô tả | Kiểm soát |
|---|---|---|
| R-F001 | L6_AGENT thay đổi break Canada pipeline flow | Chỉ thêm dispatch, không sửa generate_soap() |
| R-F002 | NER entities thiếu → BenhAnNgoaiTru có fields rỗng | Graceful: rỗng vẫn OK, BS fill khi approve (L4) |
| R-F003 | vn_route không detect → default lam_sang sai cho cdha | Unit test cho detect_vn_route() với nhiều keywords |

---

## TESTS REQUIRED

- [ ] Unit test: `tests/unit/test_vn_router.py` — test generate_mau15() mapping
- [ ] Unit test: `tests/unit/test_vn_route_detect.py` — test detect_vn_route() keywords
- [ ] Integration test: lam_sang full flow → BenhAnNgoaiTru → PDF
- [ ] Pipeline integrity test vẫn PASS (165+ tests)

---

## COMMIT FORMAT

```
feat(L6): VN-ROUTER-001 — L6 branch NER→Mẫu15/BV-01 [FID-VN-004]
```

---

*FID-VN-004 | VN-ROUTER-001 | ISO_VN v1.0 | MediVoice VN | 2026-06-06*
