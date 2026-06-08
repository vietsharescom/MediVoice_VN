# Recording Guide — MediVoice VN Data Collection
# Hướng dẫn thu âm dữ liệu huấn luyện

## Cấu trúc thư mục

```
data/
├── scripts/                    ← Script đọc (input — Andy đọc từ đây)
│   ├── by_disease/             ← Theo bệnh lý
│   │   ├── tang_huyet_ap/      ← Tăng huyết áp (tim mạch)
│   │   ├── dai_thao_duong/     ← Đái tháo đường (nội tiết)
│   │   ├── thoat_vi_dia_dem/   ← Thoát vị đĩa đệm (cơ xương khớp) — từ khó
│   │   ├── viem_phoi_viem_phe_quan/  ← Hô hấp
│   │   └── tram_cam_lo_au/     ← Tâm thần / SSRI
│   ├── by_drug_hard/           ← Luyện tên thuốc khó (tiếng Anh)
│   └── by_accent/              ← Theo giọng vùng miền
│       ├── mien_nam/
│       ├── mien_trung/
│       └── mien_bac/
│
└── recordings/                 ← File audio ghi âm (Andy lưu vào đây)
    ├── by_disease/
    ├── by_drug_hard/
    └── by_accent/
```

## Quy tắc đặt tên file audio

```
{SCRIPT_ID}_{SPEAKER}_{DATE}_{TAKE}.wav

Ví dụ:
  HA-001_andy_20260608_T1.wav      ← Take 1
  HA-001_andy_20260608_T2.wav      ← Take 2 (nếu cần)
  DM-001_bs_nguyen_20260610_T1.wav ← BS pilot khác
```

## Workflow thu âm

1. Mở script trong thư mục tương ứng
2. Đọc **Ghi chú BS** trước — hiểu ngữ cảnh
3. Ghi âm — nói tự nhiên theo kịch bản
4. **Tên thuốc tiếng Anh / từ khó** → nói 2-3 lần chậm rãi
5. Lưu audio vào `recordings/` cùng sub-folder với script
6. Upload lên app demo → AI transcribe → review → đánh giá → Lưu
7. Drive tự lưu JSON với transcript + ground truth để so sánh

## Ground truth và Auto-score

Mỗi script có `ground_truth` — kết quả lâm sàng chuẩn.
Sau khi upload audio vào app demo → chọn Script tương ứng trong sidebar → Lưu:
- App tự so sánh NER output vs ground_truth
- Auto-score hiển thị ngay: chan_doan ✅/❌, don_thuoc ✅ 3/3, icd ✅/❌
- JSON đầy đủ lưu trên Drive: `form_ner` + `form_approved` + `ground_truth` + `auto_score`

**Andy KHÔNG cần copy-paste** — tất cả tự động khi bấm "Xác nhận & Lưu".
