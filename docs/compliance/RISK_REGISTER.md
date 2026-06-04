# RISK_REGISTER.md | DS-VN-CL06-001
# ISO/IEC 42001:2023 Clause 6 | ISO_VN v1.0 | v1.1
# MediVoice VN — Risk Register
# Updated: 2026-06-06 (Design Review — DESIGN_REPORT_v1.1)

Format: R-[PREFIX][NN] | Severity | Probability | Control

---

## PHÁP LÝ (R-P)

| ID | Rủi ro | Mức độ | Khả năng | Kiểm soát hiện tại |
|---|---|---|---|---|
| R-P01 | BS khám tại nhà không đăng ký dùng app | HIGH | HIGH | Self-attestation CCHN; disclaimer rõ; platform không chịu TN |
| R-P02 | Referral commission tracker vi phạm Luật KCB Đ.80 | HIGH | MEDIUM | M5 chỉ track volume + deal% trong config partner (không ghi tiền trong giao dịch). Thanh toán thực ngoài app. |
| R-P03 | Data vi phạm NĐ13/2023 (lưu ngoài VN) | CRITICAL | LOW | SQLite local; VN Cloud only; no AWS/GCP |
| R-P04 | Không có conformity assessment trước 01/09/2027 | HIGH | MEDIUM | Budget 80-200M VND; track trong BACKLOG |
| R-P05 | Bị xếp SaMD → cần đăng ký BYT | MEDIUM | LOW | Positioning "Documentation Assistant"; không tự chẩn đoán |
| R-P06 | Vi phạm TT13/2025 deadline 31/12/2026 | HIGH | MEDIUM | Phase 2 roadmap; HL7 FHIR + chữ ký số |
| R-P07 | BS dùng app mà không có CCHN | MEDIUM | MEDIUM | Self-attestation; toggle optional nhưng có disclaimer |

---

## KỸ THUẬT / AI (R-A)

| ID | Rủi ro | Mức độ | Khả năng | Kiểm soát hiện tại |
|---|---|---|---|---|
| R-A01 | ASR nhầm tên thuốc (Paracetamol ↔ Piracetam) | CRITICAL | MEDIUM | L1b drug correction; L4 human review; CEER metric |
| R-A02 | ASR nhầm liều lượng (5mg → 50mg) | CRITICAL | MEDIUM | L1b validation; drug DB dosage ranges; L4 review |
| R-A03 | PhoWhisper WER > 30% trong điều kiện thực tế | HIGH | HIGH | Fine-tune trên pilot audio; benchmark CEER |
| R-A04 | L4 Human Gate bị bypass | CRITICAL | LOW | tests/test_pipeline_integrity.py; frozen layer |
| R-A05 | L10 Audit Log bị modify/delete | HIGH | LOW | Immutable ledger + hash chain; test verify |
| R-A06 | Drug database thiếu thuốc hay dùng | MEDIUM | MEDIUM | Expand từ pilot data; BS feedback loop |
| R-A07 | ICD-10-VN lookup không chính xác | MEDIUM | MEDIUM | L4 human review cuối cùng; DB từ HL7 Vietnam |
| R-A08 | Latency > 5 giây trên máy yếu | MEDIUM | HIGH | Streaming chunk 10s; benchmark trước launch |

---

## DỰ ÁN / VẬN HÀNH (R-O)

| ID | Rủi ro | Mức độ | Khả năng | Kiểm soát hiện tại |
|---|---|---|---|---|
| R-O01 | Pilot BS không adopt sau 2 tuần | HIGH | MEDIUM | In-person onboarding; Andy Đà Nẵng trực tiếp |
| R-O02 | Đối thủ pivot vào VN trước (VEM.AI, Heidi) | HIGH | MEDIUM | 12-18 tháng window; phase 0 trong 8 tuần |
| R-O03 | Drug DB outdated khi thuốc mới ra | MEDIUM | HIGH | Link CSDL Dược Quốc Gia API Phase 1 |
| R-O04 | Zalo API thay đổi chính sách | MEDIUM | MEDIUM | Phase 0: manual share (không dùng API) |
| R-O05 | VN Cloud downtime ảnh hưởng sync | LOW | MEDIUM | Offline-first; cloud chỉ là backup |

---

---

## DATA & TÍCH HỢP (R-D) — Thêm từ Design Review 2026-06-06

| ID | Rủi ro | Mức độ | Khả năng | Kiểm soát hiện tại |
|---|---|---|---|---|
| R-D01 | BN gửi file y tế không được yêu cầu qua email → vi phạm NĐ13/2023 nếu auto-process | HIGH | MEDIUM | Email auto-processor có 3 điều kiện bắt buộc: ① BN đã đăng ký M1 ② Có referral ACTIVE ③ BN đã ký consent. Thiếu 1 → QUARANTINE. Staff xem xét thủ công. |
| R-D02 | Zalo OA gửi file y tế → vi phạm Zalo policy → account bị khoá | HIGH | LOW | Design: Zalo OA = text non-medical ONLY. File y tế (kết quả XN, bệnh án) → Email only. Enforced qua M6 adapter tách kênh. |
| R-D03 | Thông tin commission bí mật bị lộ qua Zalo OA | MEDIUM | LOW | Partner comm = Email PRIMARY (chính thức, bảo mật). Zalo chỉ optional cho text không nhạy cảm. Commission info KHÔNG qua Zalo. |
| R-O06 | BN no-show không báo → BS mất giờ chờ (30–60 phút/ca) | MEDIUM | HIGH | Reminder H-2 + H-0:15. Waitlist fill slot cancel ngay. Buffer 15ph sau mỗi 4 ca hấp thụ trễ. Staff alert khi BN không confirm đến H-1. |

---

*DS-VN-CL06-001 | RISK_REGISTER v1.1 | ISO/IEC 42001:2023 Clause 6 | 2026-06-06*
