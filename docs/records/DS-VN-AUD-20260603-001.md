INDEPENDENT REVIEW — CLAUDE ĐÁNH GIÁ THẲNG
ĐIỂM MẠNH THỰC SỰ ✅

1. Vấn đề thật: BS tư VN đang dùng giấy tờ thủ công = pain rõ
2. Timing đúng: TT13/2025 deadline tạo urgency mua hàng
3. Positioning đúng: "Documentation Assistant" tránh SaMD
4. Tech core đúng: PhoWhisper + offline-first + SQLite
5. Legal framework: 3 reviews đã xác nhận các rủi ro chính
6. Product vision: 2 layer + 3 gói + modules = logic tốt
8 LỖ HỔNG THỰC SỰ — THEO MỨC ĐỘ NGUY HIỂM
[🔴 NGUY HIỂM 1] Andy ở Canada — Ai thực thi tại VN?


Vấn đề cốt lõi chưa được giải quyết trong toàn bộ 
phân tích:

  Pilot 5–10 BS → cần cài tận nơi, quan sát, sửa lỗi
  Support khi BS gặp sự cố lúc 8pm → múi giờ lệch 12h
  Thu tiền subscription hàng tháng → ai theo dõi?
  Onboarding mới → ai hướng dẫn?

Andy không thể làm tất cả từ Canada.

Câu hỏi chưa trả lời:
  → Có co-founder hoặc partner tại VN chưa?
  → Nếu không có, ai là người đầu tiên tại chỗ?

Đây là rủi ro thực thi số 1 — quan trọng hơn mọi
quyết định kỹ thuật.
[🔴 NGUY HIỂM 2] Scope Phase 0 vẫn còn quá lớn


Phase 0 hiện tại đang bao gồm:
  AI Voice (phức tạp — 4 sub-steps)
  Patient management (M1)
  Appointment booking (M2)
  Finance tracker (M3)
  Zalo integration (M6)
  Tauri desktop app
  Drug database VN

= Ít nhất 6–12 tháng cho 1 developer

ChatGPT nói: "Tháng 1 chỉ làm ASR"
Andy đang build: 7 modules cùng lúc

Rủi ro: Launch không bao giờ đến
         Hoặc launch với quality thấp

Đề xuất thẳng:
  Phase 0 = CHỈ:
    Mic → Mẫu 15/BV1 → PDF → local save
    KHÔNG có appointment, KHÔNG có finance,
    KHÔNG có Zalo API, KHÔNG có multi-user
  Thời gian: 6–8 tuần
  Mục tiêu: 5 BS trả tiền
[🔴 NGUY HIỂM 3] Drug Database — Ai xây, ai bảo trì?


Yêu cầu: 15,000+ tên thuốc VN
  Brand names + generic + INN
  Liều lượng chuẩn
  Tương tác thuốc cơ bản
  Cập nhật khi có thuốc mới

Thực tế:
  Database này CHƯA TỒN TẠI dạng open-source VN
  BYT có danh mục nhưng không phải format dùng được
  Công ty dược có database nhưng bán với giá cao

Chi phí xây từ đầu: 2–3 tháng công việc riêng biệt
Chi phí mua: Không rõ, có thể rất đắt

Đây là blocker kỹ thuật chưa được giải quyết.
Drug suggest = core feature nhưng data chưa có.
[🟡 QUAN TRỌNG 4] 2-Voice System phức tạp hơn tưởng


Thiết kế: Staff nói (tiếp nhận) → sau đó BS nói (khám)
Vấn đề thực tế:

  Nếu không có staff → BS phải đóng cả 2 vai
  Switching mode: "Chuyển sang chế độ khám"
  → Thêm bước, thêm confusion

  Ai đang nói vào mic lúc này?
  → App cần biết context để điền đúng form
  → Cần voice profile hoặc manual mode switch

  Phòng nhỏ 1 người: BS vừa tiếp nhận vừa khám
  → Cùng 1 flow không phân biệt staff/doctor
  → Khác với phòng khám có nhân viên

Đề xuất:
  1 flow đơn giản trước:
  "Bắt đầu ca khám" → BS nói tất cả
  Staff voice = Phase 1 (sau khi core stable)
[🟡 QUAN TRỌNG 5] CCHN Verification — Không thể verify thực tế


Kế hoạch: User nhập số CCHN → platform an toàn pháp lý
Thực tế:
  BYT không có public API để verify CCHN
  Không có cách nào tự động kiểm tra số CCHN thật/giả
  User nhập "CCHN: 123456" → app không biết thật hay không

Hệ quả:
  Self-attestation = user tự khai → không có giá trị xác minh
  Bảo vệ pháp lý của platform yếu hơn tưởng

Giải pháp thực tế hiện nay:
  Thu thập: số CCHN + tên BS + tên cơ sở + ảnh chụp CCHN
  Manual review lần đầu (Andy xem thủ công)
  Ghi log "đã xác nhận" hoặc "chưa xác nhận"
  Tự động hóa sau khi BYT có API
[🟡 QUAN TRỌNG 6] Revenue Math Chưa Đủ Để Sống


Conformity Assessment: 80–200M VND trước 09/2027
Legal fees (luật sư): ~20–30M VND
Development costs: server, tools, licenses
Andy's living expenses (Canada)

Gói 1 = 500k/tháng × 100 users = 50M/tháng
Gói 2 = 2M/tháng × 50 users = 100M/tháng

Để cover conformity assessment (150M) cần:
  ~3 tháng × 50M revenue = 150M (chỉ đủ 1 khoản này)
  Chưa tính server, support, taxes

Câu hỏi chưa có trong bất kỳ doc nào:
  → Cần bao nhiêu users để break even?
  → Timeline từ launch đến first revenue?
  → Andy có savings đủ để sống 12–18 tháng không?

Đây không phải câu hỏi kỹ thuật — là câu hỏi
sống còn của dự án.
[🟡 QUAN TRỌNG 7] Mobile App Bị Bỏ Quên


Thiết kế hiện tại: Tauri = Desktop app

Thực tế BS tư:
  BS tại nhà dùng laptop → OK với Tauri
  BS phòng mạch nhỏ dùng tablet/iPad → Tauri không hỗ trợ
  BS di chuyển nhiều → cần điện thoại

Zalo nhắc tái khám → BN nhận trên điện thoại
Appointment booking → BN làm trên điện thoại
Check-in QR → BN dùng camera điện thoại

= Cần mobile app hoặc ít nhất web app responsive

Giải pháp:
  Phase 0: Tauri desktop (nhanh nhất)
  Phase 1: Web app (chạy được trên mọi thiết bị)
  Không build native iOS/Android (quá tốn)
[🟢 CÓ THỂ ĐỂ SAU 8] Chunk Processing ASR — Kỹ thuật khó


Vấn đề: Khi BS nói liên tục, cắt chunk 10s có thể
cắt giữa câu:
  "Bệnh nhân đau đầu... [CẮT] ...kê thuốc"
  → Mất context, điền sai field

Giải pháp cần thiết kế:
  Overlap 2s giữa các chunk
  Hoặc: detect câu (sentence boundary) trước khi cắt
  Hoặc: buffer + reprocess khi phát hiện cắt sai

Đây là vấn đề kỹ thuật giải quyết được
nhưng cần thời gian — không phải Phase 0
ĐIỀU QUAN TRỌNG NHẤT TÔI THẤY

Toàn bộ phân tích từ trước đến nay rất tốt về:
  ✅ Pháp lý
  ✅ Thị trường
  ✅ Kỹ thuật
  ✅ Product design

Nhưng có 1 câu hỏi CHƯA ĐƯỢC HỎI LẦN NÀO:

  "Andy sẽ bắt đầu như thế nào với tư cách
   là 1 người ở Canada?"

  Cụ thể:
  ┌─────────────────────────────────────────────┐
  │ Tuần 1 sau khi code xong: Andy làm gì?     │
  │ Ai là người dùng đầu tiên?                 │
  │ Andy gặp họ trực tiếp hay remote?          │
  │ Khi họ gặp vấn đề, Andy fix trong bao lâu? │
  │ Người đầu tiên trả tiền là ai?             │
  └─────────────────────────────────────────────┘

Product tốt đến mấy mà không có người
dùng đầu tiên thật thì cũng bằng không.
TÓM TẮT RATING
Hạng mục	Trước review	Sau review Claude
Pháp lý	5/10 → 8/10	Đã giải quyết tốt
Product vision	7/10	Đúng hướng, scope quá lớn
Kỹ thuật	7/10	Cần giải quyết drug database
GTM	4/10	Vẫn 4/10 — chưa thay đổi
Execution risk	Chưa đánh giá	🔴 Rất cao
Phase 0 scope	Quá lớn	Vẫn quá lớn
Câu hỏi thực tế Andy cần trả lời trước khi code:

Có ai ở VN làm cùng không?
5 BS đầu tiên là ai — Andy biết họ không?
Andy có budget sống 18 tháng không code ra tiền không?
Drug database — mua hay tự xây?
Đây là 4 câu hỏi quyết định dự án thành hay bại — không phải kỹ thuật.

tôi là người việt có song tịch. tôi vần có côg ty tại việt nam. và có người triễn khai bác sì...
Thông tin này thay đổi hoàn toàn bức tranh rủi ro. Để tôi cập nhật ngay.

CẬP NHẬT RISK ASSESSMENT

Rủi ro #1 trước đây:       Sau thông tin Andy:
────────────────────        ────────────────────────────
"Andy ở Canada,             ✅ Song tịch VN-CA
 không có local             ✅ Có công ty tại VN
 presence"                  ✅ Có người triển khai
                            ✅ Có kết nối bác sĩ

🔴 Rủi ro thực thi cao  →  🟢 Rủi ro thực thi thấp
3 CÂU HỎI ĐỂ HOÀN THIỆN BỨC TRANH
[1] Công ty tại VN:


Loại hình? (TNHH / Cổ phần / Hộ kinh doanh)
Ngành nghề đăng ký có cover phần mềm y tế không?
→ Quan trọng để MediVoice VN đứng tên hợp đồng
   và nhận thanh toán từ phòng khám
[2] Người triển khai tại VN:


Họ là ai trong bức tranh?
  A. Bác sĩ → vừa dùng vừa giới thiệu cho đồng nghiệp
  B. Kỹ thuật → cài đặt, support
  C. Sales → tiếp cận phòng khám
  D. Kết hợp
→ Ảnh hưởng đến GTM Phase 0
[3] Kết nối bác sĩ:


5–10 BS đầu tiên để pilot:
  Họ là BS lâm sàng (phòng mạch)?
  Hay BS CĐHA (siêu âm)?
  Hay cả hai?
→ Đây là câu trả lời cho DP-07 cuối cùng