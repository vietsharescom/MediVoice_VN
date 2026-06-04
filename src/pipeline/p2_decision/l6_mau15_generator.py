# src/pipeline/p2_decision/l6_mau15_generator.py
# Stage:    L6_AGENT sub-module (called when vn_route == "lam_sang")
# Role:     Convert Canada NER entities → BenhAnNgoaiTru (Mẫu 15/BV-01)
# FID:      FID-VN-004 | 2026-06-06 (approved Andy Phan)
# Spec:     DESIGN_REPORT_v1.1_20260606.md §15
# Standard: ISO/IEC 42001:2023 Cl.8.5 | TT32/2023
# Version:  v1.0

"""
NER entities → form_data dict → generate_benh_an() → BenhAnNgoaiTru

Tái sử dụng src/core/l6_generate_form.generate_benh_an() để:
  - Không duplicate logic tạo BenhAnNgoaiTru
  - Đảm bảo nhất quán với VN pipeline

Mapping:
  NEREntity(type=VITAL, value="120/80")   → sinh_hieu.huyet_ap_*
  NEREntity(type=SYMPTOM, ...)            → ly_do + qua_trinh_benh_ly
  NEREntity(type=MEDICATION, ...)         → don_thuoc.danh_sach_thuoc
  NEREntity(type=HISTORY, ...)            → hoi_benh.tien_su_ban_than
  ICD code (from L1d via payload)         → kham_benh.ma_icd10
  diagnosis text (from SOAP Assessment)   → kham_benh.chan_doan_ban_dau
  follow-up text                          → don_thuoc.tai_kham
"""

from __future__ import annotations
import re
from typing import Any, Dict, List


def generate_mau15(entities, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Canada NER entities + payload → form_data dict for generate_benh_an().

    Returns serializable dict (not BenhAnNgoaiTru object) so it can be
    stored in L7 SQLite and returned via L9_RESPONSE JSON.

    Caller (l6_agent.py) stores result as payload["benh_an"].
    """
    form_data = _entities_to_form_data(entities, payload)

    # Call VN pipeline's generate_benh_an to create structured object
    try:
        from src.core.l6_generate_form import generate_benh_an
        doctor_cchn = payload.get("doctor_id", "") or payload.get("doctor_cchn", "")
        facility_id = payload.get("facility_id", "FAC-DEFAULT")

        patient_data = None
        if payload.get("ho_va_ten"):
            patient_data = {"ho_va_ten": payload["ho_va_ten"]}

        benh_an = generate_benh_an(
            form_data=form_data,
            doctor_cchn=doctor_cchn,
            facility_id=facility_id,
            patient_data=patient_data,
        )
        return _benh_an_to_dict(benh_an, form_data)

    except ImportError:
        # Fallback: return raw form_data if VN core not available
        return {"form_data": form_data, "source": "form_data_fallback"}


# ── NER entities → form_data ─────────────────────────────────────────────────

def _entities_to_form_data(entities, payload: Dict) -> Dict[str, Any]:
    """Map Canada NER entities to VN form_data dict format."""

    # ── Sinh hiệu from VITAL entities ────────────────────────────────────────
    sinh_hieu: Dict[str, Any] = {}
    symptoms: List[str] = []
    medications: List[Dict] = []
    history: List[str] = []
    diagnosis = ""
    followup = ""

    for e in entities:
        etype = getattr(e, "type", "")
        evalue = getattr(e, "value", "") or ""

        if etype == "VITAL":
            _parse_vital(evalue, sinh_hieu)

        elif etype == "SYMPTOM":
            symptoms.append(evalue)

        elif etype == "MEDICATION":
            med = {
                "inn": evalue,
                "ham_luong": getattr(e, "dose", "") or "",
                "so_lan_ngay": getattr(e, "frequency", "") or "",
                "so_ngay": _parse_days(getattr(e, "frequency", "") or ""),
                "duong_dung": "uống",
            }
            medications.append(med)

        elif etype == "HISTORY":
            history.append(evalue)

    # ── Vitals from entities objects (direct fields) ──────────────────────────
    if hasattr(entities, "__iter__"):
        pass  # already processed above

    # Also try direct entity attributes if SOAPGenerator-style NEREntity
    for e in entities:
        if getattr(e, "type", "") == "VITAL":
            v = getattr(e, "value", "") or ""
            _parse_vital(v, sinh_hieu)
        if getattr(e, "type", "") == "FOLLOWUP":
            followup = getattr(e, "value", "") or ""

    # ── Get diagnosis from payload (SOAP Assessment or ICD lookup) ────────────
    soap_note = payload.get("soap_note", {})
    if isinstance(soap_note, dict):
        # Extract first DDx from Assessment section
        a_section = soap_note.get("A", "") or ""
        diagnosis = _extract_primary_diagnosis(a_section)
        # Extract follow-up from Plan section
        if not followup:
            p_section = soap_note.get("P", "") or ""
            followup = _extract_followup(p_section)

    # ICD code from L1d (passed through payload)
    icd_code = payload.get("icd_code", "") or ""
    icd_display = payload.get("icd_display", "") or ""

    # ── Build form_data ───────────────────────────────────────────────────────
    ly_do = ", ".join(symptoms[:3]) if symptoms else ""  # first 3 symptoms as chief complaint
    if not ly_do and diagnosis:
        ly_do = diagnosis

    form_data: Dict[str, Any] = {
        "ly_do": ly_do,
        "trieu_chung": symptoms,
        "sinh_hieu": sinh_hieu,
        "toan_than": "",       # BS điền thủ công tại L4 review
        "cac_bo_phan": "",     # BS điền thủ công tại L4 review
        "chan_doan": diagnosis or icd_display,
        "icd_code": icd_code,
        "icd_display": icd_display,
        "don_thuoc": medications,
        "tai_kham": followup,
        "chi_dinh": [],
        "tien_su": "; ".join(history) if history else "",
    }

    # Patient name if available
    ho_va_ten = payload.get("ho_va_ten", "") or payload.get("patient_name", "")
    if ho_va_ten:
        form_data["ho_va_ten"] = ho_va_ten

    return form_data


def _parse_vital(value: str, sink: Dict) -> None:
    """Parse vital sign string into structured dict."""
    v = value.lower()

    # Blood pressure: "120/80" or "120/80 mmhg"
    m = re.search(r"(\d{2,3})\s*/\s*(\d{2,3})", v)
    if m:
        sink["huyet_ap_tam_thu"] = int(m.group(1))
        sink["huyet_ap_tam_truong"] = int(m.group(2))
        return

    # Temperature: "38.5" after "fever/temp"
    m = re.search(r"(\d{2}(?:\.\d)?)", v)
    if m and ("fever" in v or "temp" in v or "38" in v or "37" in v or "39" in v):
        try:
            val = float(m.group(1))
            if 35.0 <= val <= 42.0:
                sink["nhiet_do"] = val
        except ValueError:
            pass
        return

    # Heart rate: "80 bpm"
    m = re.search(r"(\d{2,3})\s*(?:bpm|/min)?", v)
    if m and ("heart" in v or "hr" in v or "pulse" in v or "rate" in v):
        sink["mach"] = float(m.group(1))
        return

    # SpO2: "98%"
    m = re.search(r"(\d{2,3})\s*%", v)
    if m and "spo2" in v:
        sink["spo2"] = float(m.group(1))
        return

    # Weight: "65 kg"
    m = re.search(r"(\d{2,3}(?:\.\d)?)\s*kg", v)
    if m:
        sink["can_nang"] = float(m.group(1))
        return

    # Respiratory rate
    m = re.search(r"(\d{1,2})\s*(?:/min|breaths)?", v)
    if m and ("resp" in v or "rr" in v or "breath" in v):
        sink["nhip_tho"] = float(m.group(1))


def _parse_days(frequency_text: str) -> int:
    """Extract number of days from frequency string."""
    m = re.search(r"(\d+)\s*(?:day|ngày)", frequency_text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return 0


def _extract_primary_diagnosis(assessment: str) -> str:
    """Extract first diagnosis from SOAP Assessment DDx text."""
    if not assessment:
        return ""
    # First line or first DDx item
    lines = [ln.strip() for ln in assessment.split("\n") if ln.strip()]
    for line in lines:
        # Skip "DDx:", "Assessment:", header lines
        clean = re.sub(r"^(ddx:|assessment:|a:|\d+\.|\-|\*)\s*", "", line, flags=re.IGNORECASE).strip()
        if clean and len(clean) > 3:
            return clean
    return lines[0] if lines else ""


def _extract_followup(plan: str) -> str:
    """Extract follow-up instructions from SOAP Plan text."""
    if not plan:
        return ""
    m = re.search(
        r"(?:follow.?up|review|tái\s*khám)\s*(?:in|after|sau)?\s*([^.\n,]{3,40})",
        plan, re.IGNORECASE
    )
    if m:
        return m.group(0).strip()
    return ""


# ── BenhAnNgoaiTru → serializable dict ───────────────────────────────────────

def _benh_an_to_dict(benh_an, form_data: Dict) -> Dict[str, Any]:
    """Convert BenhAnNgoaiTru object to JSON-serializable dict for L7 storage."""
    hc = benh_an.hanh_chinh
    kb = benh_an.kham_benh
    sh = kb.sinh_hieu
    dt = benh_an.don_thuoc

    return {
        "record_id": benh_an.record_id,
        "vn_route": "lam_sang",
        "mau_form": "15/BV-01",
        "hanh_chinh": {
            "ho_va_ten": hc.ho_va_ten or "",
            "gio_den_kham": str(hc.gio_den_kham) if hc.gio_den_kham else "",
        },
        "ly_do": benh_an.ly_do.ly_do,
        "hoi_benh": {
            "qua_trinh_benh_ly": benh_an.hoi_benh.qua_trinh_benh_ly,
            "tien_su_ban_than": benh_an.hoi_benh.tien_su_ban_than,
        },
        "sinh_hieu": {
            "nhiet_do": sh.nhiet_do,
            "huyet_ap_tam_thu": sh.huyet_ap_tam_thu,
            "huyet_ap_tam_truong": sh.huyet_ap_tam_truong,
            "mach": sh.mach,
            "nhip_tho": sh.nhip_tho,
            "can_nang": sh.can_nang,
            "spo2": sh.spo2,
        },
        "chan_doan_ban_dau": kb.chan_doan_ban_dau,
        "chan_doan_ra_vien": kb.chan_doan_ra_vien,
        "ma_icd10": kb.ma_icd10,
        "don_thuoc": [
            {
                "ten_thuoc": t.ten_thuoc,
                "ham_luong": t.ham_luong,
                "duong_dung": t.duong_dung,
                "so_lan_ngay": t.so_lan_ngay,
                "so_ngay": t.so_ngay,
            }
            for t in dt.danh_sach_thuoc
        ],
        "tai_kham": dt.tai_kham,
        "disclaimer": "AI tạo nháp — Bác sĩ chịu trách nhiệm hoàn toàn.",
        # Raw form_data preserved for L7 storage + audit
        "form_data": form_data,
    }
