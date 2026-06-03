# CONTEXT_ANALYSIS.md | DS-VN-CL04-001
# ISO/IEC 42001:2023 Clause 4.1 | ISO_VN v1.0 | v1.0 | 2026-06-03

---

## BỐI CẢNH NỘI BỘ

| Yếu tố | Phân tích |
|---|---|
| Tổ chức | Maple Leaf Group — startup y tế công nghệ |
| Quy mô | 1 founder (Andy Phan), song tịch VN-CA |
| Hạ tầng VN | Văn phòng + phòng khám tại Đà Nẵng |
| Nguồn vốn | Bootstrapped — $0 cloud cost Phase 0 |
| Năng lực AI | Python/ML developer, kinh nghiệm từ MediVoice CA |
| Pilot | 2 phòng khám (Đà Nẵng + Sài Gòn) |
| Mục tiêu | Revenue từ phòng mạch tư VN trong 3 tháng |

---

## BỐI CẢNH BÊN NGOÀI

### Quy định pháp lý

| Luật | Áp dụng | Mức độ |
|---|---|---|
| NĐ13/2023 | Data y tế lưu tại VN | CRITICAL |
| TT32/2023 | Mẫu bệnh án chuẩn | CRITICAL |
| Luật KCB 2023 | BS ký, không hoa hồng | CRITICAL |
| TT13/2025 | EMR + FHIR deadline 31/12/2026 | HIGH |
| Luật AI 134/2025 | High-risk AI, conformity 09/2027 | HIGH |
| TT46/2017 | SaMD classification (NOT SaMD) | MEDIUM |

### Thị trường

| Yếu tố | Phân tích |
|---|---|
| Target | ~15,000 phòng mạch tư lâm sàng có đăng ký BYT |
| Pain point | Ghi chép thủ công 5-10 giờ/ngày |
| Urgency | TT13/2025 deadline tạo panic buying |
| Cạnh tranh | VEM.AI (hospital only), không ai làm phòng mạch tư nhỏ |
| Opportunity | 12-18 tháng window trước đối thủ pivot |

### Công nghệ

| Yếu tố | Phân tích |
|---|---|
| ASR VN | PhoWhisper-small (BSD-3-Clause) — duy nhất cho VN y tế |
| NLP VN | PhoBERT + CRF — tốt nhất hiện có |
| Mobile | 90%+ BS tư dùng Android |
| Internet | Không ổn định ở nhiều phòng mạch → offline-first bắt buộc |

---

*DS-VN-CL04-001 | CONTEXT_ANALYSIS v1.0 | 2026-06-03*
