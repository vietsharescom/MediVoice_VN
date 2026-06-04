# L9a — PDF Export (Phase 0)
# Input: BenhAnNgoaiTru object + output_dir | Output: PDF file path
# Format: Mẫu 15/BV-01 (TT32/2023)
# FROZEN PIPELINE LAYER

from __future__ import annotations
import os
from datetime import datetime
from pathlib import Path

_EXPORTS_DIR = Path(os.getenv("MEDIVOICE_EXPORTS", "exports"))


def export_pdf(benh_an, output_dir: Path | None = None) -> str:
    """
    Xuất BenhAnNgoaiTru → PDF Mẫu 15/BV-01.
    Returns: đường dẫn file PDF.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    out_dir = output_dir or _EXPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    rid = benh_an.record_id[:8] if benh_an.record_id else "UNKNOWN"
    pdf_path = out_dir / f"BA_{rid}_{ts}.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    bold = ParagraphStyle("bold", parent=styles["Normal"], fontName="Helvetica-Bold")
    center = ParagraphStyle("center", parent=styles["Normal"], alignment=TA_CENTER)
    center_bold = ParagraphStyle("center_bold", parent=bold, alignment=TA_CENTER)
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8)

    story = []

    # ── Header ──────────────────────────────────────────────────
    story.append(Paragraph("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM", center_bold))
    story.append(Paragraph("Độc lập - Tự do - Hạnh phúc", center))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"<b>{benh_an.hanh_chinh.benh_vien or 'PHÒNG KHÁM'}</b>", center_bold))
    story.append(Paragraph(f"Khoa: {benh_an.hanh_chinh.khoa or '---'}", center))
    story.append(HRFlowable(width="100%", thickness=1))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("<b>BỆNH ÁN NGOẠI TRÚ</b>", center_bold))
    story.append(Paragraph("Mẫu 15/BV-01 (TT32/2023)", center))
    story.append(Spacer(1, 0.5*cm))

    # ── Phần I: Hành chính ──────────────────────────────────────
    story.append(Paragraph("<b>I. HÀNH CHÍNH</b>", bold))
    hc = benh_an.hanh_chinh
    admin_data = [
        ["Họ và tên:", hc.ho_va_ten or "---",
         "Tuổi:", str(hc.tuoi or "---")],
        ["Giới tính:", str(hc.gioi_tinh.value if hc.gioi_tinh else "---"),
         "Dân tộc:", hc.dan_toc or "---"],
        ["Địa chỉ:", f"{hc.dia_chi_so_nha} {hc.dia_chi_xa_phuong} {hc.dia_chi_tinh}".strip() or "---",
         "Nghề nghiệp:", hc.nghe_nghiep or "---"],
        ["Đối tượng:", str(hc.doi_tuong.value if hc.doi_tuong else "---"),
         "Số BHYT:", hc.bhyt_so_the or "---"],
        ["Giờ đến khám:", hc.gio_den_kham.strftime("%H:%M %d/%m/%Y") if hc.gio_den_kham else "---",
         "Mã ngoại trú:", hc.so_ngoai_tru or "---"],
    ]
    t = Table(admin_data, colWidths=[3.5*cm, 6*cm, 3*cm, 5*cm])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.3*cm))

    # ── Phần II: Lý do vào viện ─────────────────────────────────
    story.append(Paragraph("<b>II. LÝ DO VÀO VIỆN</b>", bold))
    story.append(Paragraph(benh_an.ly_do.ly_do or "---", styles["Normal"]))
    story.append(Spacer(1, 0.3*cm))

    # ── Phần III: Hỏi bệnh ─────────────────────────────────────
    story.append(Paragraph("<b>III. HỎI BỆNH</b>", bold))
    story.append(Paragraph(f"Quá trình bệnh lý: {benh_an.hoi_benh.qua_trinh_benh_ly or '---'}", styles["Normal"]))
    story.append(Paragraph(f"Tiền sử: {benh_an.hoi_benh.tien_su_ban_than or '---'}", styles["Normal"]))
    story.append(Spacer(1, 0.3*cm))

    # ── Phần IV: Khám bệnh ─────────────────────────────────────
    story.append(Paragraph("<b>IV. KHÁM BỆNH</b>", bold))
    sh = benh_an.kham_benh.sinh_hieu
    vitals_data = [
        ["Mạch:", f"{sh.mach or '---'} lần/ph",
         "Nhiệt độ:", f"{sh.nhiet_do or '---'} °C"],
        ["Huyết áp:", f"{sh.huyet_ap_tam_thu or '---'}/{sh.huyet_ap_tam_truong or '---'} mmHg",
         "Nhịp thở:", f"{sh.nhip_tho or '---'} lần/ph"],
        ["Cân nặng:", f"{sh.can_nang or '---'} kg",
         "SpO2:", f"{sh.spo2 or '---'} %"],
    ]
    vt = Table(vitals_data, colWidths=[3*cm, 4.5*cm, 3*cm, 4.5*cm])
    vt.setStyle(TableStyle([
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("TOPPADDING", (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
    ]))
    story.append(vt)
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(f"Toàn thân: {benh_an.kham_benh.toan_than or '---'}", styles["Normal"]))
    story.append(Paragraph(f"Các bộ phận: {benh_an.kham_benh.cac_bo_phan or '---'}", styles["Normal"]))
    story.append(Paragraph(
        f"<b>Chẩn đoán ban đầu:</b> {benh_an.kham_benh.chan_doan_ban_dau or '---'}", styles["Normal"]
    ))
    story.append(Paragraph(
        f"<b>Chẩn đoán ra viện:</b> {benh_an.kham_benh.chan_doan_ra_vien or '---'} "
        f"[ICD-10: {benh_an.kham_benh.ma_icd10 or '---'}]",
        styles["Normal"]
    ))
    story.append(Spacer(1, 0.3*cm))

    # ── Đơn thuốc ──────────────────────────────────────────────
    if benh_an.don_thuoc.danh_sach_thuoc:
        story.append(Paragraph("<b>ĐƠN THUỐC</b>", bold))
        drug_rows = [["STT", "Tên thuốc", "Hàm lượng", "Đường dùng", "Liều dùng", "Số ngày"]]
        for i, t in enumerate(benh_an.don_thuoc.danh_sach_thuoc, 1):
            drug_rows.append([
                str(i), t.ten_thuoc, t.ham_luong, t.duong_dung,
                t.so_lan_ngay, str(t.so_ngay) if t.so_ngay else "---"
            ])
        dt = Table(drug_rows, colWidths=[1*cm, 5*cm, 3*cm, 3*cm, 3*cm, 2.5*cm])
        dt.setStyle(TableStyle([
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("TOPPADDING", (0,0), (-1,-1), 2),
            ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ]))
        story.append(dt)
        if benh_an.don_thuoc.tai_kham:
            story.append(Paragraph(f"Tái khám: {benh_an.don_thuoc.tai_kham}", styles["Normal"]))
    story.append(Spacer(1, 0.5*cm))

    # ── Chữ ký ─────────────────────────────────────────────────
    sig_data = [
        ["", f"Ngày {datetime.now().strftime('%d tháng %m năm %Y')}"],
        ["BỆNH NHÂN / NGƯỜI NHÀ", "BÁC SĨ ĐIỀU TRỊ"],
        ["(Ký, ghi rõ họ tên)", "(Ký, ghi rõ họ tên + CCHN)"],
        ["", ""],
        ["", benh_an.doctor_cchn or ""],
    ]
    st = Table(sig_data, colWidths=[8.5*cm, 8.5*cm])
    st.setStyle(TableStyle([
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,1), (-1,1), "Helvetica-Bold"),
    ]))
    story.append(st)

    # ── Disclaimer bắt buộc ─────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5))
    story.append(Paragraph(
        "<i>AI tạo nháp — Bác sĩ chịu trách nhiệm hoàn toàn về nội dung bệnh án này.</i>",
        ParagraphStyle("disclaimer", parent=small, alignment=TA_CENTER)
    ))

    doc.build(story)
    return str(pdf_path)
