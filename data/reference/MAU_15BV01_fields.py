"""
Mẫu 15/BV-01 — Bệnh Án Ngoại Trú (TT32/2023)
Field specification extracted from official form MS: 15/BV-01
Source: PDF MS15BV-01_benh_an_ngoai_tru_chung.pdf

Phân loại nguồn điền:
  AUTO   = hệ thống tự điền (patient profile, timestamp)
  VOICE  = AI Voice điền từ lời BS nói
  MANUAL = nhân viên/BS nhập tay
  CALC   = tính toán tự động
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from enum import Enum


class GioiTinh(str, Enum):
    NAM = "Nam"
    NU  = "Nữ"


class DoiTuong(str, Enum):
    BHYT    = "BHYT"
    THU_PHI = "Thu phí"
    MIEN    = "Miễn"
    KHAC    = "Khác"


class NguonDen(str, Enum):
    Y_TE   = "Y tế"
    TU_DEN = "Tự đến"


class TinhTrangRaVien(str, Enum):
    KHOI        = "Khỏi"
    DO           = "Đỡ"
    KHONG_DO    = "Không đỡ"
    NANG_HON    = "Nặng hơn"
    TU_VONG     = "Tử vong"
    CHUYEN_VIEN = "Chuyển viện"


# ─────────────────────────────────────────────────────────────────
# PHẦN I — HÀNH CHÍNH
# ─────────────────────────────────────────────────────────────────
@dataclass
class HanhChinh:
    # Cơ sở y tế
    so_y_te: str = ""                    # AUTO from facility config
    benh_vien: str = ""                  # AUTO from facility config
    khoa: str = ""                       # AUTO/MANUAL
    so_ngoai_tru: str = ""               # AUTO generated
    so_luu_tru: str = ""                 # AUTO generated

    # Thông tin bệnh nhân
    ho_va_ten: str = ""                  # AUTO from patient profile / MANUAL
    sinh_ngay: Optional[date] = None     # AUTO from patient profile
    tuoi: Optional[int] = None           # CALC from sinh_ngay
    gioi_tinh: Optional[GioiTinh] = None # AUTO from patient profile
    nghe_nghiep: str = ""                # AUTO from patient profile / MANUAL
    dan_toc: str = ""                    # AUTO from patient profile / MANUAL
    ngoai_kieu: str = ""                 # AUTO from patient profile (optional)

    # Địa chỉ
    dia_chi_so_nha: str = ""             # AUTO from patient profile
    dia_chi_thon_pho: str = ""
    dia_chi_xa_phuong: str = ""
    dia_chi_huyen: str = ""
    dia_chi_tinh: str = ""

    # Thông tin bổ sung
    noi_lam_viec: str = ""               # AUTO from patient profile / MANUAL
    doi_tuong: Optional[DoiTuong] = None # MANUAL on arrival
    bhyt_han_ngay: Optional[date] = None # AUTO from VNeID/BHYT scan
    bhyt_so_the: str = ""                # AUTO from VNeID/BHYT scan

    # Liên hệ khẩn
    nguoi_nha_lien_he: str = ""          # MANUAL / AUTO from profile
    nguoi_nha_dien_thoai: str = ""       # MANUAL / AUTO from profile

    # Thời gian
    gio_den_kham: Optional[datetime] = None  # AUTO (system timestamp)
    chan_doan_noi_gioi_thieu: str = ""        # MANUAL
    nguon_den: Optional[NguonDen] = None      # MANUAL


# ─────────────────────────────────────────────────────────────────
# PHẦN II — LÝ DO VÀO VIỆN
# ─────────────────────────────────────────────────────────────────
@dataclass
class LyDoVaoVien:
    ly_do: str = ""                      # VOICE "Đau đầu, sốt 3 ngày"


# ─────────────────────────────────────────────────────────────────
# PHẦN III — HỎI BỆNH
# ─────────────────────────────────────────────────────────────────
@dataclass
class HoiBenh:
    qua_trinh_benh_ly: str = ""          # VOICE — triệu chứng, diễn biến theo thời gian
    tien_su_ban_than: str = ""           # VOICE — tiền sử cá nhân, dị ứng, bệnh mãn tính
    tien_su_gia_dinh: str = ""           # VOICE — tiền sử gia đình


# ─────────────────────────────────────────────────────────────────
# SINH HIỆU (sidebar Phần IV)
# ─────────────────────────────────────────────────────────────────
@dataclass
class SinhHieu:
    mach: Optional[float] = None         # VOICE "mạch 80 lần/phút" / MANUAL
    nhiet_do: Optional[float] = None     # VOICE "sốt 38.5" / MANUAL
    huyet_ap_tam_thu: Optional[int] = None   # VOICE "huyết áp 120/80" / MANUAL
    huyet_ap_tam_truong: Optional[int] = None
    nhip_tho: Optional[float] = None     # VOICE / MANUAL
    can_nang: Optional[float] = None     # VOICE "cân nặng 65kg" / MANUAL
    spo2: Optional[float] = None         # VOICE (optional, not on form but common)


# ─────────────────────────────────────────────────────────────────
# PHẦN IV — KHÁM BỆNH
# ─────────────────────────────────────────────────────────────────
@dataclass
class KhamBenh:
    sinh_hieu: SinhHieu = field(default_factory=SinhHieu)

    # IV.1 Toàn thân
    toan_than: str = ""                  # VOICE "Tỉnh táo, tiếp xúc tốt..."

    # IV.2 Các bộ phận
    cac_bo_phan: str = ""                # VOICE "Tim đều, phổi trong..."

    # IV.3 Tóm tắt cận lâm sàng
    tom_tat_can_lam_sang: str = ""       # VOICE / MANUAL (kết quả XN, CĐHA)

    # IV.4 Chẩn đoán ban đầu
    chan_doan_ban_dau: str = ""          # VOICE "Viêm họng cấp"

    # IV.5 Đã xử lý
    da_xu_ly: str = ""                   # VOICE "Kê Amoxicillin 500mg..."

    # IV.6 Chẩn đoán khi ra viện + Mã ICD-10-VN
    chan_doan_ra_vien: str = ""          # VOICE (final diagnosis)
    ma_icd10: str = ""                   # AUTO from ICD-10-VN lookup

    # IV.7 Thời gian điều trị
    ngay_bat_dau: Optional[date] = None  # AUTO (today)
    ngay_ket_thuc: Optional[date] = None # VOICE "tái khám sau 5 ngày" / MANUAL


# ─────────────────────────────────────────────────────────────────
# ĐƠN THUỐC (gắn với Mẫu 15/BV-01)
# ─────────────────────────────────────────────────────────────────
@dataclass
class ThuocKe:
    ten_thuoc: str = ""                  # VOICE "Amoxicillin" → drug DB lookup
    ham_luong: str = ""                  # VOICE "500mg"
    duong_dung: str = "uống"             # VOICE "uống / tiêm / nhỏ mắt..."
    lieu_dung: str = ""                  # VOICE "2 viên"
    so_lan_ngay: str = ""                # VOICE "3 lần/ngày"
    so_ngay: int = 0                     # VOICE "5 ngày"
    ghi_chu: str = ""                    # VOICE "sau ăn" / optional


@dataclass
class DonThuoc:
    danh_sach_thuoc: list[ThuocKe] = field(default_factory=list)
    tai_kham: str = ""                   # VOICE "tái khám sau 5 ngày / ngày 10/6"
    ghi_chu_them: str = ""               # VOICE


# ─────────────────────────────────────────────────────────────────
# TỔNG KẾT BỆNH ÁN (Trang 2 — dùng khi kết thúc đợt điều trị)
# ─────────────────────────────────────────────────────────────────
@dataclass
class TongKetBenhAn:
    qua_trinh_benh_ly_dien_bien: str = ""  # VOICE / MANUAL
    tom_tat_xet_nghiem: str = ""            # VOICE / MANUAL

    # Chẩn đoán ra viện
    benh_chinh: str = ""                    # VOICE
    ma_icd10_chinh: str = ""                # AUTO
    benh_kem_theo: str = ""                 # VOICE (optional)
    ma_icd10_kem: str = ""                  # AUTO

    phuong_phap_dieu_tri: str = ""          # VOICE
    tinh_trang_ra_vien: Optional[TinhTrangRaVien] = None  # VOICE / MANUAL
    huong_dieu_tri_tiep: str = ""           # VOICE "uống thuốc 5 ngày, tái khám..."

    # Hồ sơ đính kèm
    so_to_xquang: int = 0
    so_to_ct: int = 0
    so_to_sieu_am: int = 0
    so_to_xet_nghiem: int = 0
    so_to_khac: int = 0


# ─────────────────────────────────────────────────────────────────
# BỆNH ÁN NGOẠI TRÚ — COMPLETE RECORD
# ─────────────────────────────────────────────────────────────────
@dataclass
class BenhAnNgoaiTru:
    """
    Mẫu 15/BV-01 — Complete outpatient medical record.
    Fields marked VOICE are filled by MediVoice AI from doctor speech.
    Fields marked AUTO are filled by the system.
    Fields marked MANUAL require staff input.
    """
    # Metadata
    record_id: str = ""                  # AUTO UUID
    facility_id: str = ""               # AUTO from config
    doctor_cchn: str = ""               # AUTO from logged-in doctor
    created_at: Optional[datetime] = None  # AUTO
    approved_at: Optional[datetime] = None # AUTO when L4 approved
    approved_by: str = ""               # AUTO (doctor CCHN)

    # Form sections
    hanh_chinh: HanhChinh = field(default_factory=HanhChinh)
    ly_do: LyDoVaoVien = field(default_factory=LyDoVaoVien)
    hoi_benh: HoiBenh = field(default_factory=HoiBenh)
    kham_benh: KhamBenh = field(default_factory=KhamBenh)
    don_thuoc: DonThuoc = field(default_factory=DonThuoc)
    tong_ket: Optional[TongKetBenhAn] = None  # Filled at discharge

    # Audit (L10)
    audit_hash: str = ""                 # Fernet hash after approval
    byt_sync_status: str = "pending"     # pending / synced / not_required


# ─────────────────────────────────────────────────────────────────
# VOICE → FIELD MAPPING (cho L6 generator)
# ─────────────────────────────────────────────────────────────────

VOICE_FIELD_MAP = {
    # Triệu chứng / Lý do
    "ly_do": "ly_do.ly_do",
    "qua_trinh_benh_ly": "hoi_benh.qua_trinh_benh_ly",
    "tien_su": "hoi_benh.tien_su_ban_than",
    "tien_su_gia_dinh": "hoi_benh.tien_su_gia_dinh",

    # Sinh hiệu
    "mach": "kham_benh.sinh_hieu.mach",
    "nhiet_do": "kham_benh.sinh_hieu.nhiet_do",
    "huyet_ap": "kham_benh.sinh_hieu.huyet_ap_tam_thu",  # + tam_truong
    "nhip_tho": "kham_benh.sinh_hieu.nhip_tho",
    "can_nang": "kham_benh.sinh_hieu.can_nang",

    # Khám
    "toan_than": "kham_benh.toan_than",
    "cac_bo_phan": "kham_benh.cac_bo_phan",
    "can_lam_sang": "kham_benh.tom_tat_can_lam_sang",
    "chan_doan": "kham_benh.chan_doan_ban_dau",
    "chan_doan_ra_vien": "kham_benh.chan_doan_ra_vien",
    "ma_icd10": "kham_benh.ma_icd10",  # AUTO from ICD lookup

    # Đơn thuốc
    "thuoc": "don_thuoc.danh_sach_thuoc",  # List
    "tai_kham": "don_thuoc.tai_kham",
}

# Ví dụ mapping từ lời BS nói:
VOICE_EXAMPLES = {
    "Bệnh nhân đau đầu sốt 3 ngày":
        {"ly_do.ly_do": "Đau đầu, sốt 3 ngày"},

    "Huyết áp 120/80 nhiệt độ 37.5":
        {
            "kham_benh.sinh_hieu.huyet_ap_tam_thu": 120,
            "kham_benh.sinh_hieu.huyet_ap_tam_truong": 80,
            "kham_benh.sinh_hieu.nhiet_do": 37.5,
        },

    "Chẩn đoán viêm họng cấp":
        {
            "kham_benh.chan_doan_ban_dau": "Viêm họng cấp",
            "kham_benh.ma_icd10": "J02.9",  # auto-lookup
        },

    "Kê Amoxicillin 500mg 2 viên 3 lần ngày 5 ngày":
        {"don_thuoc.danh_sach_thuoc": [
            ThuocKe(
                ten_thuoc="Amoxicillin",
                ham_luong="500mg",
                lieu_dung="2 viên",
                so_lan_ngay="3 lần/ngày",
                so_ngay=5
            )
        ]},

    "Tái khám sau 5 ngày":
        {"don_thuoc.tai_kham": "Sau 5 ngày"},
}


if __name__ == "__main__":
    # Quick test
    record = BenhAnNgoaiTru(
        record_id="TEST-001",
        facility_id="PKT-DN-001",
        doctor_cchn="CCHN-012345",
        created_at=datetime.now()
    )
    record.hanh_chinh.ho_va_ten = "NGUYEN VAN A"
    record.ly_do.ly_do = "Đau đầu, sốt 3 ngày"
    record.kham_benh.sinh_hieu.nhiet_do = 38.5
    record.kham_benh.sinh_hieu.huyet_ap_tam_thu = 120
    record.kham_benh.sinh_hieu.huyet_ap_tam_truong = 80
    record.kham_benh.chan_doan_ban_dau = "Viêm họng cấp"
    record.kham_benh.ma_icd10 = "J02.9"
    record.don_thuoc.danh_sach_thuoc.append(
        ThuocKe("Amoxicillin", "500mg", "uống", "2 viên", "3 lần/ngày", 5)
    )
    record.don_thuoc.tai_kham = "Sau 5 ngày"

    import dataclasses
    print("Record created successfully:")
    print(f"  Patient: {record.hanh_chinh.ho_va_ten}")
    print(f"  Reason:  {record.ly_do.ly_do}")
    print(f"  Temp:    {record.kham_benh.sinh_hieu.nhiet_do}°C")
    print(f"  BP:      {record.kham_benh.sinh_hieu.huyet_ap_tam_thu}/{record.kham_benh.sinh_hieu.huyet_ap_tam_truong} mmHg")
    print(f"  Dx:      {record.kham_benh.chan_doan_ban_dau} [{record.kham_benh.ma_icd10}]")
    print(f"  Drugs:   {len(record.don_thuoc.danh_sach_thuoc)} item(s)")
    print(f"  Follow:  {record.don_thuoc.tai_kham}")
    print("\nMẫu 15/BV-01 field spec: OK")
