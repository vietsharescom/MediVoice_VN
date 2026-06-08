# Accent Training Scripts

## Mục đích
Thu âm cùng một kịch bản HA-001 (tăng huyết áp) nhưng với giọng từng vùng miền.
Dữ liệu này giúp model nhận dạng tốt hơn với BS từ nhiều tỉnh thành.

## Script sử dụng
→ Dùng cùng script: `../by_disease/tang_huyet_ap/HA-001_co_ban.txt`
→ Nhưng nói theo giọng vùng miền tự nhiên của mình
→ KHÔNG cần giả giọng — nếu không phải giọng vùng đó thì nhờ BS pilot tương ứng

## Ghi chú theo vùng

### Miền Nam (mien_nam/)
- Giọng đặc trưng: "huyết áp" nghe gần "huết ép"
- "tái khám" nghe gần "tái khém"
- Thuốc: "Amlodipine" đôi khi nghe "Am lo đi pin"
- BS Sài Gòn hay nói nhanh, nuốt âm

### Miền Trung / Huế (mien_trung/)
- Giọng Huế: nặng, âm "a" nghe như "ơ"
- "Losartan" nghe rất khác so với giọng Bắc
- Dấu hỏi/ngã đặc trưng

### Miền Bắc (mien_bac/)
- Giọng chuẩn phổ biến nhất trong dataset hiện tại
- Vẫn cần thu thêm để đa dạng
- Chú ý: một số BS Hà Nội nói rất nhanh

## Đặt tên file
```
HA-001_{giong}_{nguoi}_{date}_T{take}.wav
Ví dụ:
  HA-001_mien_nam_andy_20260608_T1.wav
  HA-001_mien_trung_bs_hue_20260615_T1.wav
```
