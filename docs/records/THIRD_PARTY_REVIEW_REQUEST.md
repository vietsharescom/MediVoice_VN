# THIRD-PARTY REVIEW REQUEST
# MediVoice VN — Yêu Cầu Review Độc Lập
# Ngày: 2026-06-03 | Người yêu cầu: Andy Phan (Maple Leaf Group)
# Dành cho: AI reviewer (ChatGPT / Grok) hoặc chuyên gia độc lập

---

## MỤC ĐÍCH TÀI LIỆU NÀY

Chúng tôi đang xây dựng sản phẩm AI y tế tại Việt Nam và cần review độc lập,
trung thực từ bên thứ ba trước khi bắt đầu viết code. Tài liệu này trình bày
đầy đủ bối cảnh, những gì đã phân tích, quyết định đã đưa ra, và những điểm
còn không chắc cần xác nhận.

**Yêu cầu với reviewer:**
- Phản biện thẳng thắn — nói rõ nếu phân tích sai
- Bổ sung thông tin thực tế mà chúng tôi có thể bỏ sót
- Ưu tiên các điểm có rủi ro pháp lý, kỹ thuật, hoặc thị trường cao
- Không cần khen — cần chỉ ra lỗ hổng và blind spots

---

## PHẦN 1: DỰ ÁN LÀ GÌ?

### Tên & Mô Tả

**MediVoice VN** — Phần mềm AI chuyển giọng nói bác sĩ thành hồ sơ bệnh án
điện tử chuẩn Việt Nam, chạy 100% on-premise (không cần internet).

**Nguồn gốc:** Fork ý tưởng từ MediVoice AI (Canada) v2.61.3 — một sản phẩm
AI scribe cho bác sĩ gia đình Canada. Tuy nhiên hệ thống y tế VN khác hoàn toàn:
không có bác sĩ gia đình, không có gatekeeping, output phải theo mẫu TT32/2023
tiếng Việt thay vì SOAP tiếng Anh.

### Tech Stack Dự Kiến

| Component | Technology | Lý do chọn |
|---|---|---|
| ASR (Speech-to-Text) | PhoWhisper-small (fine-tuned) | Duy nhất hỗ trợ VN y tế |
| NLP/NER | PhoBERT + CRF | State-of-art cho VN |
| Backend | FastAPI (Python 3.10) | Nhẹ, phù hợp on-premise |
| Database | SQLite + Fernet encryption | Không cần server riêng |
| Storage | Local disk + tùy chọn VN Cloud | NĐ13/2023 compliance |
| Deployment | On-premise (Windows/Linux) | Data residency |

### Pipeline Xử Lý (L0–L10)

```
Audio → [L0] Normalize → [L1] PhoWhisper ASR → [L2] Validate
→ [L3] Route (detect: lâm sàng / CĐHA / nha khoa)
→ [L4] Human Gate (BS phải approve — bắt buộc theo Luật KCB)
→ [L5] PII Scan → [L6] Generate Form + Plugin
→ [L7] SQLite lưu trữ → [L8] Error handling
→ [L9] Export (PDF / HL7 FHIR / Zalo)
→ [L10] Immutable audit log
```

### Đội Ngũ & Giai Đoạn

- **Team:** Andy Phan (founder, Maple Leaf Group — đang ở Canada)
- **Trạng thái:** Documentation phase — code chưa bắt đầu
- **Vốn:** Bootstrapped, $0 cloud cost
- **Timeline mục tiêu:** Phase 0 MVP trong 2–3 tháng

---

## PHẦN 2: BỐI CẢNH THỊ TRƯỜNG ĐÃ PHÂN TÍCH

### Landscape HIS (Hospital Information System) Việt Nam

Thị trường HIS VN chia 5 tầng:

| Tầng | Phân khúc | Nhà cung cấp chính | Tình trạng |
|---|---|---|---|
| T1 | BV công hạng I | FPT.eHospital, Viettel HIS | ~80–90% đã có HIS |
| T2 | BV tư lớn (Vinmec, Tâm Anh) | Oracle Health, in-house | ~95% có HIS tốt |
| T3 | BV hạng II–III tỉnh | FPT, CMC, BravoSoft | ~60–70% có HIS |
| **T4** | **Phòng khám tư + CĐHA** | **BravoSoft, Excel, giấy** | **30–40% dùng giấy** |
| **T5** | **Phòng mạch + BS tại nhà** | **Hầu như không có gì** | **~70% không có gì** |

**Kết luận từ phân tích:** T4 và T5 là target market của MediVoice VN.

### 4 Loại "Bác Sĩ Tư" Đã Khảo Sát

**Loại A — BS công bệnh viện khám tư tại nhà (moonlighting):**
- Phổ biến nhất, ít được phần mềm phục vụ nhất
- Quy trình: BN đến nhà → hỏi tên tuổi → khám → viết tay đơn thuốc giấy
- Thu tiền mặt → không lưu gì → lần sau hỏi lại từ đầu
- Hoa hồng từ chỉ định XN/chụp hình: ghi trong đầu hoặc tờ giấy riêng
- Ước tính: 20,000–30,000 BS trên cả nước

**Loại B — Phòng mạch tư cá nhân (có đăng ký BYT):**
- Có 1–2 nhân viên, có phòng riêng
- ~30% dùng BravoSoft hoặc phần mềm tương tự
- ~70% vẫn dùng sổ giấy hoặc Excel
- Ước tính: 15,000–20,000 cơ sở

**Loại C — Phòng khám đa khoa tư (5–20 BS):**
- Cơ cấu gần giống bệnh viện nhỏ
- ~60–70% có HIS (BravoSoft phổ biến nhất)
- Cần tích hợp, không cần thay thế
- Ước tính: 5,000–8,000 cơ sở

**Loại D — Trung tâm CĐHA tư (siêu âm, X-quang, CT):**
- Có RIS/PACS nhưng không có voice-to-report
- BS đọc to → thư ký gõ HOẶC BS tự gõ sau khi scan
- 30–50 ca/ngày × 5–10 phút gõ = 2.5–8 giờ/ngày lãng phí
- Ước tính: 1,000–2,000 trung tâm

### Xu Hướng Quy Định Đang Tới

Chúng tôi nhận định VN đang đi theo lộ trình Canada/Úc chậm hơn ~10–15 năm:

| Đã xảy ra | Đang xảy ra | Sắp tới (ước tính) |
|---|---|---|
| VNeID 2023 (CCCD = digital ID) | TT13/2025: EMR bắt buộc cho cơ sở y tế lớn | Mở rộng EMR cho phòng mạch tư? |
| BHYT qua VNeID đang hoạt động | Deadline 31/12/2026 cho chữ ký số + HL7 FHIR | VNeID health record integration? |
| BV công: quy trình đã vào khuôn | Phòng khám tư đang bị áp lực compliance | Patient data portability? |

**Chiến lược "xây trước sóng":** Khi BYT ban hành quy định cho tư nhân nhỏ,
MediVoice VN users đã compliant → zero switching cost → competitive moat.

---

## PHẦN 3: CÁC QUYẾT ĐỊNH ĐÃ ĐƯA RA

*(Để reviewer hiểu những gì đã lock — cần feedback nếu sai)*

| # | Quyết định | Lý do | Có thể sai không? |
|---|---|---|---|
| D01 | **100% on-premise, không cloud nước ngoài** | NĐ13/2023 data residency | Cần confirm exact wording |
| D02 | **VN Cloud (VNG/FPT/VNPT) là allowed** | NĐ13/2023 chỉ cấm foreign cloud | Cần confirm |
| D03 | **Output: TT32/2023 VN format** (không SOAP) | Pháp lý bắt buộc | Đúng |
| D04 | **ICD-10-VN** (QĐ5837) không phải ICD-10-CA | QĐ5837/BYT bắt buộc | Đúng |
| D05 | **Human gate L4 bắt buộc** — BS phải approve | Luật KCB 2023 Điều 62 | Cần confirm điều khoản chính xác |
| D06 | **Patient ID flexible** — không bắt buộc CCCD | Luật KCB 2023: BN không CCCD vẫn được khám | Cần confirm |
| D07 | **PhoWhisper-small** làm ASR core | Không có alternative VN tốt hơn | Cần benchmark thực tế |
| D08 | **Phase 0 trước:** BS tại nhà + phòng mạch nhỏ | Validate trước — revenue sớm hơn | Cần confirm vs CĐHA |
| D09 | **Form lâm sàng (Mẫu 15/BV1) ưu tiên Phase 0** | Phục vụ nhiều BS nhất | Cần confirm vs CĐHA flow |
| D10 | **Commission tracker** = "partner management" | Thực tế cần thiết, tránh gọi thẳng | Rủi ro pháp lý? |
| D11 | **Zalo API** cho notification BN | Zalo phổ biến ~70M users VN | Cần confirm API policy |
| D12 | **2-tier product:** Solo (BS tại nhà) + Clinic | Nhu cầu khác nhau rõ rệt | Cần confirm |

---

## PHẦN 4: NHỮNG ĐIỂM CÒN CONFUSE — CẦN XÁC NHẬN

### 4A. PHÁP LÝ VIỆT NAM ← QUAN TRỌNG NHẤT

---

**[PL-01] BS công khám tư tại nhà — hợp pháp không?**

Thực tế: Hàng chục nghìn BS bệnh viện công khám thêm tại nhà sau giờ làm.
Thu tiền mặt, không đăng ký cơ sở y tế riêng.

- Điều này có vi phạm Luật KCB 2023 không?
- Điều 14 Luật KCB 2023 có cho phép BS hành nghề tại cơ sở không đăng ký không?
- Nếu bất hợp pháp trên giấy tờ nhưng phổ biến thực tế — MediVoice VN có risk gì khi phục vụ nhóm này không?
- Khi họ dùng MediVoice VN và lưu hồ sơ bệnh nhân → có bị coi là "hoạt động cơ sở y tế" không?

---

**[PL-02] Hoa hồng chỉ định (Referral Commission) — trạng thái pháp lý?**

Thực tế: BS chỉ định BN đi chụp hình/XN ở cơ sở khác, nhận hoa hồng 10–30%.
Phổ biến đến mức gần như không ai giấu trong giới y tế.

- Thông tư 15/2019/TT-BYT cấm hoa hồng thuốc — có extend sang dịch vụ chẩn đoán không?
- Nghị định nào quy định về referral fee trong y tế VN?
- MediVoice VN tích hợp "partner referral management" (track commission) → có bị xem là facilitate illegal activity không?
- Mô hình nào an toàn về pháp lý: track commission, hay chỉ track "referral" không track tiền?

---

**[PL-03] NĐ13/2023 — Dữ liệu y tế lưu trữ, chính xác là gì?**

Chúng tôi hiểu: "dữ liệu cá nhân nhạy cảm (bao gồm thông tin sức khỏe) phải lưu tại VN".

Cần xác nhận:
- Điều khoản chính xác trong NĐ13/2023 về dữ liệu y tế là điều nào?
- "Lưu tại VN" có nghĩa là physical server ở VN hay legal jurisdiction VN?
- VNG Cloud / FPT Cloud / VNPT Cloud (data center tại VN) có đủ điều kiện không?
- Nếu BS dùng bản on-premise (local) nhưng backup lên cloud VN — có vi phạm không?
- Cross-border data transfer (ví dụ: Andy ở Canada remote access) có vi phạm không?

---

**[PL-04] Luật AI 134/2025 — Yêu cầu cụ thể cho AI y tế?**

Chúng tôi biết Luật AI 134/2025 tồn tại và có deadline conformity assessment 01/09/2027.

Cần xác nhận:
- AI y tế có thuộc "high-risk AI" category trong Luật 134 không?
- Nếu high-risk: yêu cầu cụ thể là gì? (audit, certification, human oversight?)
- "Human oversight bắt buộc" cụ thể là gì — BS phải approve từng record là đủ không?
- Conformity assessment: cơ quan nào thực hiện? Chi phí ước tính?
- Startup bootstrapped có được miễn/giảm không?

---

**[PL-05] Đăng ký phần mềm y tế với BYT — cần không?**

Khi MediVoice VN xuất ra "hồ sơ bệnh án" — đây có được coi là "trang thiết bị y tế phần mềm" (SaMD — Software as Medical Device) không?

- Thông tư 46/2017/TT-BYT về trang thiết bị y tế có cover phần mềm không?
- Nếu cần đăng ký: quy trình, thời gian, chi phí?
- Nếu MediVoice VN chỉ là "công cụ hỗ trợ" (không ra quyết định y tế) → có cần đăng ký không?
- Phân biệt: "AI ra chẩn đoán" (cần đăng ký) vs "AI transcribe giọng BS" (không cần?) — đúng không?

---

**[PL-06] Lưu trữ hồ sơ bệnh án — thời hạn và trách nhiệm?**

- TT32/2023 quy định lưu trữ bệnh án bao lâu? (Chúng tôi nghe nói 20 năm?)
- Trách nhiệm lưu trữ thuộc về BS hay cơ sở y tế?
- Nếu BS dùng MediVoice VN, dữ liệu trên laptop BS — khi laptop hỏng → ai chịu trách nhiệm?
- Cloud backup có được tính là "lưu trữ hợp lệ" không?

---

**[PL-07] TT13/2025 — Phạm vi áp dụng chính xác?**

TT13/2025 yêu cầu EMR + chữ ký số + HL7 FHIR, deadline 31/12/2026.

Cần xác nhận:
- TT13/2025 áp dụng cho tất cả cơ sở KCB hay chỉ từ quy mô nào trở lên?
- Phòng mạch cá nhân (1 BS, đăng ký BYT) có trong phạm vi không?
- BS công khám tư tại nhà (không đăng ký cơ sở) có trong phạm vi không?
- Nếu không comply đúng deadline: chế tài là gì?

---

### 4B. QUY ĐỊNH QUỐC TẾ & SO SÁNH

---

**[QT-01] HL7 FHIR R4 — Thực tế áp dụng tại VN hiện nay?**

- Các HIS VN (FPT.eHospital, Viettel) có thực sự implement FHIR R4 production-ready chưa?
- Hay chỉ là roadmap trên giấy để comply với TT13/2025?
- Thực tế integration: FHIR vs HL7 v2.5 — cái nào VN đang dùng nhiều hơn?
- Nếu MediVoice VN build FHIR R4 output ngay Phase 1 — có clinic nào consume được không?

---

**[QT-02] DICOM & PACS — Tích hợp CĐHA thực tế?**

Với plugin_cdha (báo cáo siêu âm/X-quang):
- Các trung tâm CĐHA tư tại VN đang dùng PACS gì phổ biến nhất?
- PACS tại VN có DICOM Structured Report (SR) support không?
- MediVoice VN output cần gắn Study UID để link với hình ảnh PACS — có phức tạp không?
- Có tiêu chuẩn báo cáo CĐHA VN cụ thể không (ngoài TT32)?

---

**[QT-03] So sánh với Canada (gốc của dự án)?**

MediVoice CA (Canada) dùng SOAP note format, tiếng Anh, FHIR Canada profile.
VN fork khác biệt như thế nào về technical và legal:

- Patient consent: Canada có opt-in/opt-out rõ ràng (PIPEDA). VN có tương đương không?
- Audit trail: Canada yêu cầu gì? VN yêu cầu gì? Khác nhau chỗ nào?
- AI liability: Nếu AI tạo bệnh án sai → BS ký → BN bị hại: ai chịu trách nhiệm tại VN? Tại Canada?
- GDPR/PIPEDA vs NĐ13/2023: Điểm mạnh/yếu so sánh?

---

### 4C. THỰC TẾ THỊ TRƯỜNG — CẦN XÁC NHẬN SỐ LIỆU

---

**[TT-01] Số lượng thực tế BS tư VN?**

Ước tính của chúng tôi (cần verify):
- ~70,000 BS có CCHN (chứng chỉ hành nghề) tại VN
- ~30–40% có hình thức khám tư (phòng mạch + tại nhà)
- = ~21,000–28,000 potential users

Câu hỏi:
- Số liệu BYT về BS đăng ký hành nghề tư nhân chính xác là bao nhiêu?
- Tỷ lệ BS có 2 jobs (công + tư) ước tính thực tế?

---

**[TT-02] BravoSoft và thị trường phần mềm phòng khám?**

- BravoSoft có thực sự ~500+ clinic không? Hay con số lớn hơn/nhỏ hơn?
- Giá BravoSoft thực tế 2026? (Chúng tôi nghe 3–5 triệu/năm)
- Tính năng BravoSoft hiện tại: có voice, có AI, có FHIR chưa?
- Đối thủ nào đang thực sự grow nhanh trong phân khúc clinic nhỏ VN?

---

**[TT-03] VEM.AI — Tình trạng thực tế?**

VEM.AI được biết là đang pilot tại BV E Hà Nội (AI scribe VN).
- Họ đang ở giai đoạn nào? Revenue chưa?
- Họ target segment nào?
- Họ có offline capability không?
- Pricing của họ (nếu biết)?

---

**[TT-04] Khả năng thanh toán thực tế?**

Pricing ước tính của chúng tôi cho MediVoice VN:
- BS tại nhà: 300–800k VNĐ/tháng
- Phòng mạch nhỏ: 1–3M VNĐ/tháng
- Phòng khám lớn: 3–8M VNĐ/tháng

- Các benchmark này có hợp lý so với thực tế WTP (willingness to pay) của BS VN không?
- BravoSoft đang charge bao nhiêu/tháng?
- BS tư có thói quen trả subscription monthly không hay prefer trả 1 lần?

---

### 4D. KỸ THUẬT & AI

---

**[KT-01] PhoWhisper-small — Đủ dùng cho y tế không?**

- WER 29.6% trên VietMed dataset — dataset này có representative cho medical speech thực tế không?
- Fine-tune trên 16h labeled data (VietMed Kaggle) — đủ không? Canada dùng bao nhiêu giờ?
- Code-switching VI+EN (bác sĩ trộn tiếng Anh khi nói tên thuốc, kỹ thuật): ViMedCSS dataset coverage đủ không?
- Alternative: whisper-large-v3 fine-tuned on VN medical — có ai đã làm chưa?
- Latency thực tế của PhoWhisper-small trên CPU thường (không có GPU)? Có đạt < 5 giây không?

---

**[KT-02] PhoBERT cho NER y tế — Baseline tốt không?**

- PhoBERT + CRF cho Named Entity Recognition y tế VN: có pre-trained checkpoint không?
- Hay phải fine-tune từ PhoBERT base?
- Tên thuốc VN (~15,000+ brand names): có dataset nào để fine-tune không?
- ICD-10-VN mapping tự động từ text: có research/model nào đã làm chưa?

---

**[KT-03] ICD-10-VN Database — Nguồn chính thức?**

- QĐ5837/BYT: file ICD-10-VN có download được ở đâu chính thức?
- Format: text, XML, hay database?
- Cập nhật lần cuối là năm nào?
- Có Python library parse ICD-10-VN không?

---

**[KT-04] SQLite cho medical data — Đủ không?**

Chúng tôi chọn SQLite vì đơn giản, on-premise, không cần server.
- SQLite có đủ scalability cho 1 BS với 5,000–50,000 bệnh nhân không?
- Fernet encryption at rest trên SQLite — có security issue gì không?
- Backup strategy: SQLite file copy đủ không hay cần WAL mode?

---

**[KT-05] Offline-first Architecture?**

Requirement: hoạt động 100% khi không có internet, sync khi có mạng.
- Framework nào phù hợp nhất: local SQLite + background sync lên VN cloud?
- Conflict resolution khi sync (BS dùng cả phone lẫn laptop)?
- Electron cho desktop app hay pure web app (PWA offline)?

---

### 4E. CHIẾN LƯỢC SẢN PHẨM

---

**[SP-01] Phase 0 đúng không? BS tại nhà vs CĐHA?**

Chúng tôi đã thay đổi ưu tiên từ CĐHA (ban đầu) sang BS tại nhà (phân tích gần đây).

Lý do chuyển:
- BS tại nhà: 20,000+ users, dễ onboard, không cần compliance phức tạp
- CĐHA: 1,000–2,000 users nhưng WTP cao hơn, pain point rõ hơn

**Câu hỏi cho reviewer:**
- Với bootstrapped startup 1 founder — nên focus BS tại nhà (nhiều users, ít tiền) hay CĐHA (ít users, nhiều tiền)?
- "Đơn thuốc điện tử + lịch sử BN" cho BS tại nhà có đủ differentiator không hay quá generic?
- Có player nào đang serve BS tại nhà VN tốt rồi (mà chúng tôi chưa biết)?

---

**[SP-02] 2-Tier Product hay 1 Product?**

Đề xuất hiện tại:
- Tier 1 "MediVoice Solo": BS tại nhà, mobile-first, 300–800k/tháng
- Tier 2 "MediVoice Clinic": Phòng khám, desktop+mobile, 2–8M/tháng

**Câu hỏi:**
- 2 tier = 2 codebase = phức tạp hơn → hay 1 codebase nhiều feature flags?
- Có nên bắt đầu với 1 tier và pivot sau không?
- Lesson learned từ các healthcare startup khác khi chọn segment?

---

**[SP-03] Commission Tracker — Làm hay không làm?**

Thực tế: Referral commission rất phổ biến ở VN nhưng pháp lý mơ hồ.
Nếu làm: gọi là "partner management", không gọi là "hoa hồng".
Nếu không làm: mất feature quan trọng, BS sẽ tự dùng Excel.

**Câu hỏi:**
- Rủi ro pháp lý cho MediVoice VN nếu tích hợp tính năng này?
- Có precedent nào (VN hoặc quốc tế) về healthcare referral tracking software?
- Cách framing an toàn nhất là gì?

---

**[SP-04] Go-to-Market: Trực tiếp hay qua Partner?**

Options:
- A. Direct to BS: marketing digital (Facebook/Zalo), freemium trial
- B. Qua hiệp hội BS (Hội Y học TP.HCM, v.v.)
- C. Qua nhà thuốc (BS thường quen nhà thuốc — channel tự nhiên)
- D. Qua FPT/Viettel (white-label cho clinic nhỏ)

**Câu hỏi:**
- Channel nào thực tế nhất cho bootstrapped founder ở nước ngoài (Andy ở Canada)?
- Freemium có work cho BS VN không hay họ ngại data privacy?
- Cộng đồng BS VN online ở đâu (Facebook group, Zalo group)?

---

## PHẦN 5: BLIND SPOTS — NHỮNG GÌ CHÚNG TÔI CÓ THỂ ĐANG BỎ QUA?

*Đây là phần QUAN TRỌNG NHẤT — mong reviewer thêm vào*

Những câu hỏi chúng tôi chưa nghĩ đến:

**5A. Cạnh tranh chưa rõ:**
- Có startup AI y tế VN nào đang stealth mode chúng tôi chưa biết?
- FPT có đang build AI scribe nội bộ không?
- Google/Microsoft có đang enter VN healthcare market?

**5B. Rủi ro chưa xét:**
- Nếu một BS dùng MediVoice VN, AI tạo bệnh án có lỗi, BS không đọc kỹ trước khi ký, BN bị hại → liability của MediVoice VN là gì?
- Data breach: nếu laptop BS bị hack, hồ sơ hàng nghìn BN lộ → trách nhiệm pháp lý?
- BYT có thể ban hành quy định CHỐNG lại AI scribe không (vì lo ngại chất lượng)?

**5C. Giả định sai có thể:**
- Chúng tôi giả định BS tại nhà MUỐN lưu hồ sơ → thực ra có BS nào không muốn lưu (vì sợ bị phát hiện khám không đăng ký)?
- Chúng tôi giả định Zalo API dễ tích hợp → thực ra Zalo có hạn chế gì?
- Chúng tôi giả định VN Cloud đủ ổn định → thực tế uptime VNG/FPT Cloud là bao nhiêu?

**5D. Kỹ thuật tiềm ẩn:**
- PhoWhisper có license cho commercial use không?
- VietMed dataset (Kaggle) có license cho commercial training không?
- PhoBERT license cho commercial use?

---

## PHẦN 6: YÊU CẦU CỤ THỂ TỪ REVIEWER

### Ưu tiên cao (cần trả lời):

1. **[PL-01]** BS công khám tư tại nhà — pháp lý thực tế và rủi ro cho MediVoice VN
2. **[PL-02]** Commission tracker — có thể build an toàn không, framing như thế nào
3. **[PL-04]** Luật AI 134/2025 — yêu cầu thực tế cho medical AI startup nhỏ
4. **[PL-05]** Có cần đăng ký phần mềm với BYT không?
5. **[SP-01]** BS tại nhà vs CĐHA — phase 0 nên là cái nào?
6. **[KT-01]** PhoWhisper commercial license + WER thực tế trên medical VN

### Ưu tiên trung bình:

7. **[PL-03]** NĐ13/2023 exact wording về cloud storage
8. **[QT-01]** HL7 FHIR thực tế tại VN hiện nay
9. **[TT-02]** BravoSoft giá và tính năng thực tế
10. **[SP-03]** Go-to-market channel khả thi nhất

### Nếu có thêm thời gian:

11. Bất kỳ blind spot nào reviewer thấy chúng tôi đang bỏ qua
12. So sánh với healthcare AI startup ở Đông Nam Á khác đã thành/thất bại
13. Kỹ thuật: có giải pháp ASR VN nào tốt hơn PhoWhisper không?

---

## PHẦN 7: TÀI LIỆU THAM KHẢO CỦA DỰ ÁN

*(Để reviewer đọc thêm nếu cần)*

Các văn bản pháp lý VN liên quan:
- Nghị định 13/2023/NĐ-CP: Bảo vệ dữ liệu cá nhân
- Thông tư 32/2023/TT-BYT: Mẫu hồ sơ bệnh án điện tử
- Thông tư 13/2025/TT-BYT: Ứng dụng CNTT trong KCB (EMR/FHIR)
- Luật Khám chữa bệnh 2023 (số 15/2023/QH15)
- Luật AI 134/2025 (nếu đã có văn bản chính thức)
- Quyết định 5837/QĐ-BYT: Ban hành ICD-10-VN

---

## KẾT LUẬN YÊU CẦU

Chúng tôi cần một đánh giá **trung thực, không né tránh** về:

1. **Có làm được không?** — Kỹ thuật và pháp lý có barrier nào không vượt được?
2. **Làm đúng hướng chưa?** — Segment, phase, positioning có logic không?
3. **Đang sai ở đâu?** — Blind spots, wrong assumptions chúng tôi chưa nhìn thấy
4. **Nên làm gì trước?** — Nếu chỉ có 1 founder, 3 tháng, $0 budget — làm gì?

**Tone mong muốn:** Thẳng thắn như một co-founder, không phải như một consultant muốn làm hài lòng.

---

*MediVoice VN | Third-Party Review Request v1.0 | 2026-06-03*
*Contact: Andy Phan | vietshares.com@gmail.com*
*GitHub: https://github.com/vietsharescom/MediVoice_VN*
