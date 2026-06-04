# DECISIONS.md — MediVoice VN
# Architecture Decision Records (ADR)
# Format: Date | Decision | Why | Impact
# v0.2.0 — Updated after 3-party review (ChatGPT + Grok + Copilot)

---

## PRODUCT & ARCHITECTURE

| Date | Decision | Why | Impact |
|---|---|---|---|
| 2026-06-03 | **2-Layer architecture** (Patient Mgmt + AI Voice) | Phòng mạch cần quản lý BN + ghi chép — 2 nhu cầu khác nhau | Layer 1 optional, Layer 2 core |
| 2026-06-03 | **3 Gói dịch vụ** + 9 modules bật/tắt | Nhu cầu khác nhau: BS tại nhà vs phòng mạch vs phòng khám | Gói 1/2/3 bundle + module pricing |
| 2026-06-03 | **Mẫu 15/BV1 là form CORE** (Phase 0) | 95% BS lâm sàng tư dùng — phổ biến nhất | CĐHA và chuyên khoa là plugin, không phải core |
| 2026-06-03 | **CĐHA = Plugin/Option** (không phải Phase 0) | CĐHA dùng form chuyên ngành riêng, không dùng Mẫu 15 | FID-VN-001 lùi sang Phase 1 |
| 2026-06-03 | ~~Desktop: Tauri~~ → **PWA: FastAPI + HTML/JS** | Tauri cần Rust, phức tạp — FastAPI PWA đủ dùng Phase 0, BS dùng phone | Mobile-first ngay Phase 0, không cần install |
| 2026-06-04 | **Mobile-first Phase 0** (không phải desktop only) | BS dùng điện thoại trong phòng khám — PWA responsive là đủ | Không build native iOS/Android |
| 2026-06-03 | **Staff voice + Doctor voice** = 2 contexts riêng | Staff hỏi tiếp nhận, BS khám — 2 luồng khác nhau | Staff voice = Phase 1 feature |
| 2026-06-03 | **Module M3: Thu chi đơn giản** thêm vào | BS tư không biết thu bao nhiêu — voice log giải quyết | Voice: "Thu 200k BN Lan" → app ghi |
| 2026-06-03 | **Appointment booking** (M2) = Gói 2 feature | Giảm chờ đợi, tiết kiệm nhân viên phòng mạch | BN book online, QR check-in |

---

## LEGAL & COMPLIANCE

| Date | Decision | Why | Impact |
|---|---|---|---|
| 2026-06-03 | **Chỉ phục vụ cơ sở KCB có đăng ký BYT** | Luật KCB 2023 Điều 14: BS chỉ hành nghề tại cơ sở được cấp phép | Bắt buộc nhập GPHN/CCHN khi đăng ký |
| 2026-06-03 | **Self-attestation CCHN** khi đăng ký | Platform không chịu TN nếu user khai sai | Thu: số CCHN + tên + ảnh chụp CCHN |
| 2026-06-03 | **NOT SaMD** — không đăng ký thiết bị y tế | Chỉ transcription + điền mẫu, không chẩn đoán (TT46/2017) | Không cần quy trình BYT device registration |
| 2026-06-03 | **Positioning: "Documentation Assistant"** | Tránh SaMD classification, giảm liability | UI: "AI tạo nháp — BS chịu TN hoàn toàn" |
| 2026-06-03 | **Referral: KHÔNG ghi tiền/phần trăm** | Luật KCB 2023 Điều 80 + TT15/2019 cấm hoa hồng | Chỉ track: chỉ định ai, ngày nào |
| 2026-06-03 | **Storage: VN Cloud allowed** (VNG/FPT/VNPT) | NĐ13/2023: data tại VN — VN cloud compliant | Không dùng AWS/GCP/Azure region ngoài VN |
| 2026-06-03 | **Andy remote access OK** | Remote access ≠ cross-border data transfer | Cần VPN + access log |
| 2026-06-03 | **Conformity assessment budget** 80–200M VND | Luật AI 134/2025: bắt buộc trước 01/09/2027 | Phải có revenue trước mid-2027 |
| 2026-06-03 | **Zalo OA API: chỉ non-medical content** | Zalo cấm gửi thông tin y tế nhạy cảm qua OA API | Reminder: "Nhắc lịch tái khám" OK. Chẩn đoán/thuốc: KHÔNG |
| 2026-06-03 | **Lưu trữ 10 năm** tối thiểu | TT32/2023: bệnh án lưu 10–20 năm | Trách nhiệm thuộc cơ sở KCB, không phải platform |

---

## TECHNICAL

| Date | Decision | Why | Impact |
|---|---|---|---|
| 2026-06-04 | **"Documentation Assistant" = transcription + form mapping** (KHÔNG = no reasoning) | AI đọc lời BS → phân loại đúng vào field đúng (S/O/A/P hay Mẫu 15/BV1 section) — đây là mapping, không phải autonomous diagnosis. Không được tự ra chẩn đoán nếu BS chưa nói. | AI phải hiểu thuật ngữ chuyên khoa để map đúng. FAISS KB Phase 1 là mapping tool, không phải diagnosis engine. |
| 2026-06-05 | **Canada pipeline = core pipeline VN** (giữ nguyên, không sửa) | Pipeline Canada đã đạt hiệu suất tiếng Việt cao (20/22 PASS, 91%). Không rewrite — chỉ thêm VN routing layer trên top. | src/pipeline/ = Canada handlers. VN thêm l9_vn_router.py để branch lam_sang→Mẫu 15/BV-01, cdha→SOAP. |
| 2026-06-05 | **MarianMT KÍCH HOẠT NGAY** (sửa quyết định 2026-06-04) | MarianMT dùng nội bộ cho NER (không phải output) — giải quyết CEER=0% mà không vi phạm pháp lý VN (output vẫn VI). T-005 xác nhận hoạt động tốt. | l1b_translation.py active. Output Mẫu 15/BV-01 vẫn VI. CEER cải thiện đáng kể. |
| 2026-06-05 | **SOAP = output chuẩn cho CĐHA branch** | SOAP (S/O/A/P) phù hợp với báo cáo CĐHA: S=chỉ định, O=kết quả hình ảnh, A=kết luận, P=đề nghị. Canada pipeline đã implement sẵn. | L3 route=cdha → giữ SOAP output. L3 route=lam_sang → VN routing convert → Mẫu 15/BV-01. |
| 2026-06-05 | **FAISS Clinical KB kích hoạt** (copy từ Canada) | KB giúp DDx reasoning — cải thiện SOAP A section. chunks.json + faiss_index.bin từ Canada tương thích ngay. | data/kb/ active. Sentence-transformers installed. Qwen fallback về template DDx (chấp nhận được Phase 0). |
| 2026-06-04 | ~~**MarianMT VI→EN = Option Phase 1**~~ → **ĐÃ SỬA 2026-06-05** | Quyết định cũ sai — MarianMT cần thiết ngay cho NER chất lượng cao. | Xem quyết định 2026-06-05 bên trên. |
| 2026-06-04 | **CĐHA forms = specialized per modality** (Phase 1) | Siêu âm ≠ X-quang ≠ ECG ≠ Tim mạch — mỗi loại có template riêng. Không dùng Mẫu 15/BV1. Persona #2 BS CĐHA: 30-50 ca/ngày, WTP cao. | FID-VN-001 CĐHA: cần template builder per specialty (echo, US, X-ray, CT, MRI...). |
| 2026-06-04 | **Bilingual EN/VI output = option** cho foreign doctors | VN có BS nước ngoài (FDI hospitals, international clinics). Code-switching VN+EN phổ biến trong môi trường y tế. | L3 routing: detect ngôn ngữ → chọn output template phù hợp. Default: VI. |
| 2026-06-03 | **PhoWhisper-small** là ASR chính | BSD-3-Clause (commercial OK), only offline VN medical ASR | Cần fine-tune + 4 sub-steps L1a-L1d |
| 2026-06-03 | **VietMed dataset** cho fine-tuning | MIT license (commercial OK), 16h medical VN audio | WER thực tế ~30-40% không fine-tune |
| 2026-06-03 | **Streaming chunk 10s** (không phải record toàn bộ) | Latency: 10s audio → 3-6s processing → perceived <5s | Cần overlap giữa chunks để tránh cắt giữa câu |
| 2026-06-03 | **CEER quan trọng hơn WER** | Paracetamol↔Piracetam, 5mg↔50mg = hậu quả nguy hiểm | Test set riêng: thuốc + liều + chẩn đoán |
| 2026-06-03 | **L1 = 4 sub-steps** (không phải 1 bước) | ASR raw output không đủ dùng cho y tế | L1a chunk, L1b drug correct, L1c NER, L1d ICD lookup |
| 2026-06-03 | **SQLite + WAL + Fernet** | Đơn giản, offline, encrypted at rest | Đủ cho phòng mạch 5,000–50,000 BN |
| 2026-06-03 | **Export Phase 0: PDF only** | FHIR chưa production tại VN — PDF đủ dùng | Phase 1: HL7 v2; Phase 2: FHIR R4 |
| 2026-06-03 | **HL7 v2 trước FHIR** (Phase 1) | HL7 v2 vẫn là chuẩn thực tế VN (BravoSoft etc.) | FHIR R4 chỉ khi TT13/2025 thực sự enforce |
| 2026-06-03 | **Drug database = Blocker** chưa giải quyết | 15k+ tên thuốc VN, không có open-source database | Cần mua hoặc xây trước khi code L1b |
| 2026-06-03 | **PACS không cần Phase 0** | CĐHA Phase 0: text report + Study UID nhập tay | PACS API = Phase 2 sau khi có đủ partner |

---

## MARKET & GTM

| Date | Decision | Why | Impact |
|---|---|---|---|
| 2026-06-03 | **Target: Phòng mạch tư có đăng ký BYT** | WTP 1-3M/tháng, TT13 deadline urgency, hợp pháp | Không target BS tại nhà không đăng ký |
| 2026-06-03 | **Pilot: Đà Nẵng + Sài Gòn** | Andy có phòng khám Đà Nẵng + BS partner Sài Gòn | Không cần tìm pilot từ đầu |
| 2026-06-03 | **GTM: 10 BS thủ công** (không ads) | Healthcare = trust business, không phải click business | Andy cài tận nơi, quan sát, sửa ngay |
| 2026-06-03 | **Pricing: hỗ trợ trả năm** | 70% BS VN thích trả 1 lần/năm (WTP research) | Annual prepay = cash flow positive |
| 2026-06-03 | **Không cạnh tranh FPT/Viettel** | Họ có 600+ BV — tích hợp là win-win (M9) | Plugin/add-on approach với HIS lớn |
| 2026-06-03 | **Giá VNĐ** (không USD) | $149/tháng Dr.AI quá cao cho VN | 500k–8M VNĐ/tháng tùy gói |

---

## PROCESS

| Date | Decision | Why | Impact |
|---|---|---|---|
| 2026-06-03 | **FID threshold: 100 LOC** | Lean > paperwork | Tầng 2 (20–100 LOC) không cần FID |
| 2026-06-03 | **4 files tracking** | Over-documented = chậm development | CLAUDE.md + BACKLOG + DECISIONS + CHANGELOG |
| 2026-06-03 | **External review: 3 AI đã review** | ChatGPT + Grok + Copilot — 2026-06-03 | Xem THIRD_PARTY_REVIEW_REQUEST.md |
| 2026-06-03 | **Luật sư VN** trước khi launch | PL-01/02/04/05 cần verify chuyên nghiệp | Budget: 10–20M VND |

---

## Template thêm decision mới

```
| YYYY-MM-DD | **Tên decision** | Lý do ngắn | Tác động |
```

*DECISIONS.md | MediVoice VN | v0.2.0 | Updated: 2026-06-03*
