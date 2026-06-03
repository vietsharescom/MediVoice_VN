# PROJECT_KICKOFF.md | DS-VN-CL08-PKF | ISO/IEC 42001:2023 §4 + §8.1
# Project: MediVoice VN | v1.0
# Claude fills S1–S9 | Andy signs S10 | No FID, no code until S10 signed
# Created: 2026-06-03 | Based on: Research session 2026-06-02 (~15h)

---

## WHY THIS FORM EXISTS

Bài học từ MediVoice CA: yêu cầu pháp lý VN (NĐ13/2023, TT21/2019, Luật AI 134/2025)
phát hiện muộn gây rework kiến trúc. Form này ngăn điều đó tái diễn.

---

## SECTION 1: PROBLEM STATEMENT

| Field | Value |
|---|---|
| Problem | Bác sĩ và nhân viên y tế tại phòng khám tư Việt Nam phải ghi chép hồ sơ bệnh án thủ công — gõ tay hoặc đọc cho thư ký gõ. Không có sản phẩm thương mại nào tại VN tự động hóa luồng "bác sĩ nói → bệnh án điện tử chuẩn TT32/2023" |
| Who has this problem | ~60,000 bác sĩ tại VN; đặc biệt: BS siêu âm (30–50 ca/ngày), BS chuyên khoa mở phòng mạch ngoài giờ, chủ phòng khám đa khoa tư cần EMR trước 31/12/2026 |
| Quantified pain | BS siêu âm: 30–50 ca/ngày × 200–300 chữ/ca = **6,000–15,000 chữ/ngày** phải đọc/gõ. BS lâm sàng: 15–30 phút/bệnh nhân × 20–40 BN/ngày = **5–10 giờ/ngày** chỉ để ghi chép |
| What happens if not solved | Bác sĩ tiếp tục dùng thư ký (chi phí cao, không chuẩn hóa); phòng khám tư không đáp ứng deadline EMR TT13/2025 (31/12/2026); VEM.AI và Heidi Health chiếm thị phần |
| Why now | (1) TT13/2025: 37,000+ phòng khám tư bắt buộc có EMR trước 31/12/2026 — demand khổng lồ đang mở. (2) Không có đối thủ thương mại nào cung cấp giải pháp này tại VN. (3) Luật AI 134/2025 có grace period đến 01/09/2027. (4) Window trước Heidi Health: 12–18 tháng. |

**Owner brief:**
```
Tạo phiên bản MediVoice AI cho thị trường Việt Nam.
Fork từ MediVoice CA v2.61.3.
Target: phòng khám tư nhân — CĐHA, đa khoa, chuyên khoa.
Output: bệnh án TT32/2023 tiếng Việt, không phải SOAP tiếng Anh.
Architecture: local-only (NĐ13/2023 data residency).
```

---

## SECTION 2: TARGET MARKET

| Field | Value |
|---|---|
| Country / Region | Việt Nam — TP.HCM, Hà Nội, Đà Nẵng (Phase 1) |
| Language(s) | Tiếng Việt primary + code-switching VI+EN (phổ biến trong y khoa) |
| User type | (1) BS CĐHA tư — siêu âm, X-quang. (2) BS chuyên khoa phòng mạch ngoài giờ. (3) Chủ phòng khám đa khoa tư |
| Deployment target | **On-premise** tại phòng khám (bắt buộc — NĐ13/2023) |
| Internet requirement | Optional — fully offline-capable |
| Scale (launch) | Pilot: 3–5 phòng khám / trung tâm CĐHA (10–30 bác sĩ) |
| Scale (12 months) | 200–500 bác sĩ qua direct sales + đối tác |

**Market size:**
- ~37,000–40,000 phòng khám tư đang hoạt động
- ~1,000–2,000 trung tâm CĐHA tư
- ~140,000 tổng số bác sĩ VN
- Addressable market Phase 1: **10,000–20,000 phòng khám**

**Go-to-market:**
- Phase 1: Direct sales — phòng khám CĐHA tư (use case rõ nhất, ROI nhanh nhất)
- Phase 2: Plugin/add-on tích hợp FPT.eHospital (400+ BV) hoặc Viettel HIS (200+ BV)
- Không cạnh tranh với FPT/Viettel — tích hợp như AI scribe module

**Competitor landscape:**
| Đối thủ | Mức đe dọa | Điểm yếu của họ |
|---|---|---|
| VEM.AI (BV E HN) | 🔴 Cao | Cloud LLM → vi phạm NĐ13/2023, không offline |
| Dr.AI (Đài Loan, $149/tháng) | 🟡 Trung bình | EN output, cloud, chưa deploy VN |
| Heidi Health (AU) | 🟡 12–18 tháng | Chưa vào VN, tiếng Việt chưa confirmed |
| VinBrain/NVIDIA | 🟡 Dài hạn | Imaging AI only, chưa có SOAP/bệnh án |

---

## SECTION 3: LEGAL & REGULATORY SCAN

### 3a. Data Privacy

| Regulation | Applicable? | Key Obligations | Impact on Architecture |
|---|---|---|---|
| **NĐ13/2023/NĐ-CP** | ✅ YES | Explicit consent; **data MUST stay in VN**; 72h breach notification; DPA bắt buộc với vendor | **Server on-premise tại phòng khám. Cloud nước ngoài = vi phạm.** |
| **Luật An ninh mạng 2018** | ✅ YES | Data residency VN bắt buộc | Không cloud nước ngoài |
| **Luật Dữ liệu 60/2024** | ✅ YES | Dữ liệu y tế = dữ liệu quan trọng; quy định lưu trữ đặc biệt | On-premise hoặc cloud VN |
| Canada PIPEDA | ❌ N/A | — | — |
| EU GDPR | ❌ N/A | — | — |

### 3b. Domain-specific regulation

| Domain | Regulation | Impact |
|---|---|---|
| Hồ sơ bệnh án | **TT32/2023/TT-BYT** — 29 mẫu bệnh án chuẩn | Output PHẢI theo đúng mẫu TT32; không được tự do format |
| EMR bắt buộc | **TT13/2025/TT-BYT** (hiệu lực 21/7/2025) | Deadline 31/12/2026; phải hỗ trợ chữ ký số + audit trail + HL7 FHIR |
| Mã bệnh | **QĐ5837/QĐ-BYT** — ICD-10-VN | Chẩn đoán PHẢI có mã ICD-10-VN (không phải ICD-10-CA) |
| Hành nghề | **Luật KCB 15/2023** | AI chỉ tạo draft — BS có CCHN phải phê duyệt trước khi lưu |
| Lưu trữ | TT21/2019 + TT32/2023 | 10 năm thông thường, 20 năm tử vong |

### 3c. AI-specific regulation

| Regulation | Applicable? | Notes |
|---|---|---|
| **Luật AI 134/2025/QH15** (hiệu lực 01/03/2026) | ✅ YES | AI y tế = **rủi ro cao**. Phải có conformity assessment. **Grace period đến 01/09/2027** |
| Nghị định hướng dẫn Luật AI | Monitor | Danh sách hệ thống rủi ro cao đang soạn thảo |

**Obligations Luật AI 134 trước 01/09/2027:**
1. Conformity Assessment — đánh giá sự phù hợp với cơ quan được chỉ định
2. Đăng ký trên Cổng thông tin AI quốc gia
3. Human oversight bắt buộc — AI không ra quyết định cuối cùng
4. Incident reporting — báo cáo sự cố qua cổng một cửa
5. Risk management documentation

**Phạt vi phạm:** Lên đến **2 tỷ VNĐ** (~$75,800 USD)

### 3d. Regulatory verdict

- **Blocking trước launch:** Không có — grace period đến 01/09/2027 cho đủ thời gian
- **Phải làm ngay:**
  - Output theo mẫu TT32/2023 (bắt buộc từ 01/03/2024)
  - Hỗ trợ chữ ký số + audit trail + HL7 FHIR (deadline 31/12/2026)
  - ICD-10-VN trong phần Chẩn đoán
  - Data Processing Agreement (DPA) với từng phòng khám
- **Chuẩn bị (trước 01/09/2027):** Conformity assessment Luật AI 134
- **ISO framework:** ISO_VN (NĐ13/2023 + Bộ Y Tế + Luật ATTT + Luật AI 134)

---

## SECTION 4: INPUT DATA ASSESSMENT

| Field | Value |
|---|---|
| Base code | MediVoice AI CA v2.61.3 (643/643 PASS) — proven pipeline |
| Dataset 1 | **VietMed** (arXiv 2404.05659, LREC-COLING 2024) — 16h labeled + 1,000h unlabeled VN medical speech. WER 51.8%→29.6% khi fine-tune |
| Dataset 2 | **ViMedCSS** (arXiv 2602.12911, 2025) — VN medical code-switching (VI+EN mixed, phổ biến trong y khoa VN) |
| Dataset 3 | **PhoWhisper training data** — 844h Vietnamese speech (VinAI, Apache 2.0) |
| Dataset 4 | **ICD-10-VN** — QĐ5837/QĐ-BYT (database mã bệnh VN, cần build) |
| Contains PII? | VietMed: de-identified. Clinical data: YES → NĐ13/2023 applies |
| Licence | VietMed: research (verify commercial); PhoWhisper: Apache 2.0 ✅ |
| Known biases | VietMed covers all regional accents ✅; may underrepresent Southern Vietnam clinical terms |
| Critical gap vs CA | MarianMT VI→EN **KHÔNG CẦN** — output tiếng Việt. Remove completely. |

---

## SECTION 5: USE CASE CLASSIFICATION

### Use Case #1 — BS CĐHA (Siêu âm, X-quang, CT) ← PRIORITY

| Field | Value |
|---|---|
| User | Bác sĩ siêu âm, bác sĩ X-quang tại phòng khám CĐHA tư |
| Action | BS nhìn hình ảnh → đọc to → MediVoice VN nghe → sinh báo cáo CĐHA có cấu trúc → BS ký |
| Volume | 30–50 ca/ngày × 200–300 chữ/ca |
| Latency | < 5 giây sau khi BS đọc xong |
| Format output | Báo cáo CĐHA: Kỹ thuật / Mô tả / Kết luận / Khuyến nghị |
| Ký | BS CĐHA bắt buộc ký (KTV không được ký theo pháp luật) |
| Criticality | HIGH |

### Use Case #2 — BS Lâm Sàng Kết Luận

| Field | Value |
|---|---|
| User | BS lâm sàng tại phòng khám đa khoa / chuyên khoa tư |
| Action | BS đọc to kết luận sau khi có đủ kết quả XN + CĐHA → MediVoice sinh bệnh án TT32 |
| Format output | Mẫu 15/BV1 (ngoại trú chung): Lý do vào viện / Bệnh sử / Tiền sử / Khám LS / CLS / Chẩn đoán ICD-10-VN / Hướng điều trị |
| Ký | BS lâm sàng bắt buộc ký số (TT13/2025) |
| Criticality | HIGH |

### Use Case #3 — Phòng Khám Nha Khoa

| Field | Value |
|---|---|
| User | BS răng hàm mặt tại phòng khám nha tư |
| Action | BS đọc tình trạng bệnh nhân → sinh Mẫu 16/BV1 |
| Format output | Mẫu 16/BV1: + sơ đồ răng FDI, tình trạng nha chu, kế hoạch điều trị nha |
| Criticality | MEDIUM |

**Chung cho tất cả use cases:**
- Human-in-loop: ALWAYS — BS phải phê duyệt trước khi lưu (Luật KCB 2023)
- Failure mode: Must fail loudly — không được silent error
- Auditability: Full trace — L10 audit log (ISO 42001 + Luật AI 134)
- Offline: 100% — không internet dependency

---

## SECTION 6: ISO FRAMEWORK SELECTION

| Framework | Select | Rationale |
|---|---|---|
| ISO_EU_CA | ☐ | Không applicable — không phải thị trường EU/Canada |
| **ISO_VN** | ✅ | VN domestic market: NĐ13/2023 + TT32/2023 + TT13/2025 + Luật AI 134/2025 |
| ISO_CA | ☐ | Canada version only |

**Selected: ISO_VN**
**Rationale:** NĐ13/2023 data residency → on-premise bắt buộc. TT32/2023 → format bệnh án bắt buộc. Luật AI 134/2025 → high-risk AI, conformity assessment trước 09/2027. Local frozen models = ISO auditable = consistent AI (lý do Andy xây ISO framework).

---

## SECTION 7: 5M RESOURCE PLANNING

### Man (People)
| Role | Resource | Thời gian ước tính |
|---|---|---|
| Owner / Decision maker | Andy Phan | 2–3h/tuần review |
| AI Developer | Claude (primary) | Per sprint |
| Domain expert | BS VN (cần cho test cases CĐHA + lâm sàng) | 5–10h validation |
| Legal advisor | Luật sư y tế VN (Luật AI 134 conformity) | 1 consultation |
| External AI reviewers | ChatGPT + Grok per module (theo MV process) | Per CR |

### Machine (Infrastructure)
| Resource | Spec | Status |
|---|---|---|
| Dev machine | Windows 11, C:\Projects\MediVoice_VN | ✅ Ready |
| GPU training (VietMed) | Kaggle T4 free tier (30h/week) | Available |
| GPU inference | CPU-only (PhoWhisper-small chạy được) | ✅ |
| Deployment | On-premise clinic server hoặc Docker local | Docker ready ✅ |
| Network | Offline-capable | ✅ Required |

### Method (Process)
| Item | Value |
|---|---|
| Methodology | Single-developer agile (Andy + Claude) |
| FID | > 50 LOC = APPROVED FID; < 20 LOC = direct commit + test |
| Test coverage | 100% PASS trước mọi commit |
| Review | ChatGPT + Grok per module |
| Plugin system | 1 FID per specialty plugin |

### Money (Budget)
| Item | Estimate | Notes |
|---|---|---|
| AI model API | $0 | Local only — Option B |
| Cloud compute | $0 Phase 1 | Kaggle free |
| VietMed licence | $0 (research) | Verify commercial use |
| Legal consultation | TBD | Luật AI 134 compliance roadmap |
| **Total Phase 1** | **~$0 operational** | Bootstrapped |

### Material (Data & Tools)
| Item | Value |
|---|---|
| ASR | PhoWhisper-small → fine-tune VietMed |
| NER | PhoBERT+CRF (val_f1=0.8163, từ CA) |
| Translation | ❌ REMOVED — không cần MarianMT |
| Forms | 29 mẫu TT32/2023 → implement as plugins |
| ICD codes | ICD-10-VN (QĐ5837) database |
| Framework | FastAPI, SQLite, Fernet, PyTorch, HuggingFace |

---

## SECTION 8: SOLUTION OPTIONS — A / B / C

### Option A — Cloud LLM (GPT-4o, Claude API)
| Field | Value |
|---|---|
| Data leaves VN? | YES — dữ liệu bệnh nhân gửi ra nước ngoài |
| Legal VN | ❌ **BLOCKED** — vi phạm NĐ13/2023 + Luật An ninh mạng 2018 |
| Verdict | **REJECTED — bất hợp pháp cho thị trường VN** |

### Option B — Local open-source models ✅ SELECTED
| Field | Value |
|---|---|
| Technology | PhoWhisper-small (ASR) + PhoBERT+CRF (NER) + rule-based bệnh án generator |
| Cost | $0/tháng vận hành |
| Data leaves VN? | NO — 100% local |
| Legal VN | ✅ NĐ13/2023 compliant |
| Consistency | ✅ Frozen weights = same input → same output = ISO auditable |
| Offline | ✅ 100% |
| Verdict | **SELECTED — duy nhất hợp pháp + ISO auditable** |

### Option C — Hybrid (local + cloud escalation)
| Field | Value |
|---|---|
| Data leaves VN? | Complex cases: YES |
| Legal VN | ❌ Cloud escalation vi phạm NĐ13/2023 |
| Verdict | **REJECTED — NĐ13/2023 blocks cloud escalation for VN** |

**Decision: Option B — Local only**
**Rationale:** (1) Duy nhất hợp pháp. (2) ISO auditable — giải quyết vấn đề inconsistent AI. (3) Offline — phòng khám VN không cần internet. (4) $0 vận hành — giá cạnh tranh.

---

## SECTION 9: LATEST TECHNOLOGY SCAN

### 9a. ASR — Vietnamese Medical

| Hiện tại (CA) | Mới nhất (2026) | Gap | Hành động |
|---|---|---|---|
| PhoWhisper-small (844h VN) | VietMed fine-tuned: WER 51.8%→29.6% (2024) | ✅ GAP | Fine-tune PhoWhisper trên 16h VietMed labeled |

### 9b. Code-switching (VI+EN)

| Hiện tại | Mới nhất | Gap | Hành động |
|---|---|---|---|
| Không xử lý | ViMedCSS dataset (2025) — VN medical VI+EN code-switching | ✅ GAP | Tích hợp ViMedCSS training data |

### 9c. NER Vietnamese

| Hiện tại | Mới nhất | Gap | Hành động |
|---|---|---|---|
| PhoBERT+CRF (val_f1=0.8163) | PhoBERT-base-v2 (2023) | Minor | Đánh giá v2 nếu F1 < 0.85 |

### 9d. Output Format

| CA | VN | Action |
|---|---|---|
| SOAP (tiếng Anh) | Bệnh án TT32/2023 (tiếng Việt) | **Rewrite L6 generator + plugins** |
| ICD-10-CA | ICD-10-VN (QĐ5837) | **Build ICD-10-VN database** |

### 9e. Translation

| CA | VN | Action |
|---|---|---|
| MarianMT VI→EN | Không cần | **DELETE L1b_translation** — major simplification |

### 9f. Clinical KB

| CA | VN | Action |
|---|---|---|
| FAISS (23 EN guidelines) | Hướng dẫn lâm sàng MOH VN (tiếng Việt) | Phase 2 |

### 9g. Competitor scan

| Product | Status | Risk |
|---|---|---|
| VEM.AI | ✅ Live tại BV E HN | 🔴 Direct competitor — nhưng cloud → vi phạm NĐ13 |
| Dr.AI SOAP QuickNote | Website VN chưa deploy | 🟡 12–18 tháng |
| Heidi Health | SEA hub Singapore | 🟡 12–18 tháng trước khi vào VN |

**Scan verdict:**
- [x] Upgrade: Fine-tune PhoWhisper trên VietMed (1 Kaggle session)
- [x] New data: ViMedCSS 2025 — critical cho clinical speech thực tế
- [x] Simplification lớn: Xóa MarianMT — major error source trong CA removed
- [x] ICD-10-VN: Build database từ QĐ5837/BYT

### 9h. Form templates — Core insight

**29 mẫu TT32/2023 = 70% common core + 30% specialty additions**

```
CORE (tất cả 29 mẫu): Hành chính + Lý do vào viện + Bệnh sử +
  Tiền sử + Khám LS + Cận LS + Chẩn đoán ICD-10-VN + Hướng điều trị

SPECIALTY PLUGINS Phase 1:
  plugin_cdha.py     — Báo cáo CĐHA (KHÔNG thuộc 29 mẫu — format riêng)
  plugin_ngoai_tru.py — Mẫu 15/BV1 (covers 45% use cases)
  plugin_nha_khoa.py  — Mẫu 16/BV1 (20,000+ phòng nha)
  → 3 plugins = 85% thị trường Phase 1
```

### 9i. VN healthcare workflow — Critical differences vs CA

**VN không có bác sĩ gia đình. Bệnh nhân tự đến chuyên khoa/BV.**

Key workflow differences requiring architecture change:
1. **Thư ký y khoa** — gõ theo lời BS đọc — Use Case #1 của MediVoice VN
2. **Multi-role** — nhiều người ghi 1 hồ sơ (ĐD, BS LS, BS CĐHA, KTV XN)
3. **Báo cáo CĐHA** — format riêng, không thuộc 29 mẫu bệnh án
4. **Patient ID linh hoạt** — không có CCCD/BHYT vẫn được khám
5. **ICD-10-VN bắt buộc** — không phải ICD-10-CA

---

## SECTION 10: APPROVAL GATE

| Checkpoint | Status |
|---|---|
| S1: Problem statement clear | ✅ Done |
| S2: Target market defined + competitor analysis | ✅ Done |
| S3: Legal scan — NĐ13/2023, TT32, TT13/2025, Luật AI 134 | ✅ Done — no blocking |
| S4: Data assessed (VietMed, ViMedCSS, ICD-10-VN) | ✅ Done |
| S5: Use cases classified (CĐHA, Lâm sàng, Nha khoa) | ✅ Done |
| S6: ISO_VN framework selected | ✅ Done |
| S7: 5M resources estimated | ✅ Done |
| S8: 3 options (A rejected, B selected, C rejected) | ✅ Done |
| S9: Tech scan (VietMed, ViMedCSS, competitors, forms) | ✅ Done |
| Owner reviewed all sections | ☐ **PENDING Andy review** |
| Legal blocker resolved | ✅ N/A — grace periods active |

**Decision:**
- [ ] **APPROVED** — proceed to: FID-VN-001 (plugin_cdha), FID-VN-002 (plugin_ngoai_tru)
- [ ] CONDITIONAL — resolve before: ___
- [ ] REJECTED — reason: ___

**Approved by:** _______________ | **Date:** _______________

---

## NEXT STEPS (sau S10 approval)

| # | Task | Thời gian |
|---|---|---|
| 1 | FID-VN-001: plugin_cdha.py — báo cáo siêu âm/X-quang | 1–2 ngày |
| 2 | FID-VN-002: plugin_ngoai_tru.py — Mẫu 15/BV1 | 1–2 ngày |
| 3 | Xóa L1b_translation (MarianMT) | 2 giờ |
| 4 | Thay PII patterns → CCCD/CMND/BHYT | 1 giờ |
| 5 | Build ICD-10-VN database (QĐ5837) | 1 ngày |
| 6 | Fine-tune PhoWhisper trên VietMed (Kaggle) | 1 session |
| 7 | ViMedCSS code-switching handling | 2–3 giờ |
| 8 | HL7 FHIR export basic (TT13/2025) | 1–2 ngày |
| 9 | Full test suite VN (target 100% PASS) | Per sprint |
| 10 | Pilot 1 phòng khám CĐHA tư | Andy arrange |

---

*DS-VN-CL08-PKF | PROJECT_KICKOFF MediVoice VN v1.0*
*Prepared by: Claude Sonnet 4.6 | Owner: Andy Phan — Maple Leaf Group*
*Date: 2026-06-03 | Research: ~15h ngày 2026-06-02*
