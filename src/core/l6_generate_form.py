# L6 — Generate Mẫu 15/BV-01
# Input: form_data dict + patient info | Output: BenhAnNgoaiTru object
# RULE: AI ghi lại lời BS nói — KHÔNG tự chẩn đoán
# TT32/2023 format
# FROZEN PIPELINE LAYER

from __future__ import annotations
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Import BenhAnNgoaiTru từ data model
_DATA_REF = Path(__file__).parent.parent.parent / "data" / "reference"
sys.path.insert(0, str(_DATA_REF.parent))

import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("mau15bv01", _DATA_REF / "MAU_15BV01_fields.py")
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

BenhAnNgoaiTru = _mod.BenhAnNgoaiTru
HanhChinh = _mod.HanhChinh
KhamBenh = _mod.KhamBenh
SinhHieu = _mod.SinhHieu
DonThuoc = _mod.DonThuoc
ThuocKe = _mod.ThuocKe
LyDoVaoVien = _mod.LyDoVaoVien
HoiBenh = _mod.HoiBenh


def generate_benh_an(
    form_data: dict,
    doctor_cchn: str,
    facility_id: str,
    patient_data: dict | None = None,
) -> BenhAnNgoaiTru:
    """
    Tạo BenhAnNgoaiTru từ form_data (output L2).
    AI chỉ điền những gì BS đã nói — không tự chẩn đoán thêm.
    """
    record = BenhAnNgoaiTru(
        record_id=str(uuid.uuid4()),
        facility_id=facility_id,
        doctor_cchn=doctor_cchn,
        created_at=datetime.now(),
    )

    # Hành chính — từ patient_data nếu có
    if patient_data:
        hc = record.hanh_chinh
        hc.ho_va_ten = patient_data.get("ho_va_ten", "")
        hc.nghe_nghiep = patient_data.get("nghe_nghiep", "")
        hc.dan_toc = patient_data.get("dan_toc", "")
        hc.bhyt_so_the = patient_data.get("bhyt_so_the", "")
        hc.dia_chi_so_nha = patient_data.get("dia_chi_so_nha", "")
        hc.dia_chi_tinh = patient_data.get("dia_chi_tinh", "")

    hc = record.hanh_chinh
    hc.gio_den_kham = datetime.now()

    # Lý do
    record.ly_do.ly_do = form_data.get("ly_do", "")

    # Hỏi bệnh
    record.hoi_benh.qua_trinh_benh_ly = form_data.get("ly_do", "")

    # Sinh hiệu
    sh_data = form_data.get("sinh_hieu", {})
    sh = record.kham_benh.sinh_hieu
    sh.nhiet_do = sh_data.get("nhiet_do")
    sh.huyet_ap_tam_thu = sh_data.get("huyet_ap_tam_thu")
    sh.huyet_ap_tam_truong = sh_data.get("huyet_ap_tam_truong")
    sh.mach = sh_data.get("mach")
    sh.nhip_tho = sh_data.get("nhip_tho")
    sh.can_nang = sh_data.get("can_nang")
    sh.spo2 = sh_data.get("spo2")

    # Khám bệnh
    record.kham_benh.toan_than = form_data.get("toan_than", "")
    record.kham_benh.cac_bo_phan = form_data.get("cac_bo_phan", "")
    record.kham_benh.chan_doan_ban_dau = form_data.get("chan_doan", "")
    record.kham_benh.chan_doan_ra_vien = form_data.get("chan_doan", "")
    record.kham_benh.ma_icd10 = form_data.get("icd_code", "")

    # Đơn thuốc
    for drug in form_data.get("don_thuoc", []):
        record.don_thuoc.danh_sach_thuoc.append(ThuocKe(
            ten_thuoc=drug.get("inn", ""),
            ham_luong=drug.get("ham_luong", ""),
            duong_dung=drug.get("duong_dung", "uống"),
            lieu_dung="",
            so_lan_ngay=drug.get("so_lan_ngay", ""),
            so_ngay=drug.get("so_ngay", 0),
        ))

    record.don_thuoc.tai_kham = form_data.get("tai_kham", "")

    return record
