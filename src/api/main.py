"""
MediVoice VN — FastAPI PWA
Phase 0: BS nói → pipeline → Mẫu 15/BV-01 → PDF

Disclaimer bắt buộc: AI tạo nháp — Bác sĩ chịu trách nhiệm hoàn toàn.
"""
from __future__ import annotations
import os
import tempfile
import json
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..core import l0_normalize, l1a_asr, l1b_drug_correct, l1c_ner
from ..core import l1d_icd_lookup, l2_validate, l3_route
from ..core import l4_human_gate, l5_pii_scan, l6_generate_form
from ..core import l7_storage, l9a_pdf_export, l10_audit_log
from ..core.l7_storage import init_db, _get_conn
from ..models.clinical_record import ClinicalRecord, RecordStatus

app = FastAPI(
    title="MediVoice VN",
    description="Documentation Assistant — AI tạo nháp, Bác sĩ chịu trách nhiệm",
    version="0.2.0",
)

# Init DB khi startup
@app.on_event("startup")
async def startup():
    init_db()


# ── Static files (PWA) ─────────────────────────────────────────────────────

_STATIC = Path(__file__).parent / "static"
if _STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")


@app.get("/")
async def index():
    index_html = _STATIC / "index.html"
    if index_html.exists():
        return FileResponse(str(index_html))
    return {"message": "MediVoice VN v0.2.0 — API ready"}


# ── Pipeline endpoint ──────────────────────────────────────────────────────

@app.post("/api/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    facility_id: str = Form(default="FAC-DEFAULT"),
    doctor_cchn: str = Form(default=""),
    patient_name: str = Form(default=""),
):
    """
    Upload audio → chạy pipeline L0→L3 → trả về draft form data.
    BS xem xét + chỉnh sửa trước khi approve.
    """
    # Lưu audio tạm
    suffix = Path(audio.filename or "audio.wav").suffix or ".wav"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        content = await audio.read()
        tmp.write(content)
        tmp.close()

        # L0: Normalize
        audio_arr, wav_path = l0_normalize.normalize(tmp.name)

        # L1a: ASR
        transcript_raw = l1a_asr.transcribe(audio_arr)

        # L1b: Drug correction
        transcript_corrected = l1b_drug_correct.correct_drug_names(transcript_raw)
        drug_candidates = l1b_drug_correct.extract_drug_candidates(transcript_corrected)

        # L1c: NER
        entities = l1c_ner.extract_entities(transcript_corrected, drug_candidates)

        # L1d: ICD lookup
        icd_code, icd_display = l1d_icd_lookup.auto_lookup(entities.chan_doan)

        # L2: Validate + confidence
        form_data, conf_scores, overall_conf = l2_validate.validate(entities)
        form_data["icd_code"] = icd_code
        form_data["icd_display"] = icd_display

        # Thêm patient_name vào form_data nếu được cung cấp
        if patient_name:
            form_data["ho_va_ten"] = patient_name

        # L3: Route — pass transcript làm fallback khi NER không đủ
        route = l3_route.detect_route(form_data, transcript_corrected or transcript_raw or "")

        # L5: PII scan
        pii_detected = l5_pii_scan.scan_form_data(form_data)

        # Tạo ClinicalRecord draft
        record = ClinicalRecord(
            facility_id=facility_id,
            doctor_cchn=doctor_cchn,
            audio_path=tmp.name,
            transcript_raw=transcript_raw,
            transcript_corrected=transcript_corrected,
            ner_entities={
                "chan_doan": entities.chan_doan,
                "don_thuoc": entities.don_thuoc,
                "nhiet_do": entities.nhiet_do,
                "huyet_ap": [entities.huyet_ap_tam_thu, entities.huyet_ap_tam_truong],
                "mach": entities.mach,
                "tai_kham": entities.tai_kham,
            },
            icd_code=icd_code,
            icd_display=icd_display,
            form_data=form_data,
            confidence_scores=conf_scores,
            overall_confidence=overall_conf,
            route=route,
            pii_detected=pii_detected,
        )

        # L4: chuyển sang PENDING_REVIEW
        record = l4_human_gate.require_human_approval(record)

        # Lưu record ID tạm vào in-memory (production: dùng Redis/cache)
        _pending_records[record.record_id] = record

        return {
            "record_id": record.record_id,
            "transcript": transcript_corrected or transcript_raw,
            "form_data": form_data,
            "confidence": overall_conf,
            "route": route,
            "pii_detected": pii_detected,
            "status": record.status.value,
            "warning": "AI tạo nháp — Bác sĩ vui lòng kiểm tra trước khi lưu",
        }

    finally:
        # SRS-L0-003: xóa audio sau transcription — NĐ13/2023 data minimization
        l0_normalize.purge_audio(tmp.name)
        if 'wav_path' in locals():
            l0_normalize.purge_audio(wav_path)


# Pending records store (Phase 0: in-memory; Phase 1: Redis)
_pending_records: dict[str, ClinicalRecord] = {}


@app.get("/api/records/{record_id}")
async def get_record(record_id: str):
    """Lấy draft record để BS review."""
    record = _pending_records.get(record_id)
    if not record:
        # Thử load từ DB
        data = l7_storage.load_record(record_id)
        if not data:
            raise HTTPException(404, "Record không tìm thấy")
        return data

    return {
        "record_id": record.record_id,
        "status": record.status.value,
        "form_data": record.form_data,
        "transcript": record.transcript_corrected,
        "confidence": record.overall_confidence,
        "route": record.route,
    }


@app.post("/api/records/{record_id}/approve")
async def approve_record(
    record_id: str,
    doctor_cchn: str = Form(...),
    edited_form: str = Form(default=""),
):
    """
    BS approve record sau khi review.
    Luật KCB 2023 Điều 62: BS phải ký trước khi lưu.
    """
    record = _pending_records.get(record_id)
    if not record:
        raise HTTPException(404, "Record không tìm thấy hoặc đã xử lý")

    # Áp dụng chỉnh sửa của BS nếu có
    if edited_form:
        try:
            edited_data = json.loads(edited_form)
            record = record.model_copy(update={"form_data": edited_data})
        except json.JSONDecodeError:
            pass

    # L4: Approve
    try:
        record = l4_human_gate.approve(record, doctor_cchn)
    except l4_human_gate.HumanGateError as e:
        raise HTTPException(400, str(e))

    # L7 + L10: dùng cùng connection để đảm bảo atomicity
    conn = _get_conn()
    try:
        l7_storage.store_record(record, conn=conn)
        l10_audit_log.log_event(conn, record_id, doctor_cchn, "APPROVED", "BS approved")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, f"Lưu thất bại: {e}")
    finally:
        conn.close()

    # Xóa khỏi pending
    _pending_records.pop(record_id, None)

    return {
        "record_id": record_id,
        "status": "approved",
        "message": "Bệnh án đã được lưu. Dùng /api/records/{id}/pdf để xuất PDF.",
    }


@app.post("/api/records/{record_id}/reject")
async def reject_record(
    record_id: str,
    doctor_cchn: str = Form(...),
    reason: str = Form(default=""),
):
    """BS reject — không lưu vào DB."""
    record = _pending_records.get(record_id)
    if not record:
        raise HTTPException(404, "Record không tìm thấy")

    try:
        record = l4_human_gate.reject(record, doctor_cchn, reason)
    except l4_human_gate.HumanGateError as e:
        raise HTTPException(400, str(e))

    # L10: Audit log (reject cũng cần log)
    conn = _get_conn()
    try:
        l10_audit_log.log_event(conn, record_id, doctor_cchn, "REJECTED", reason)
    finally:
        conn.close()

    _pending_records.pop(record_id, None)

    return {"record_id": record_id, "status": "rejected"}


@app.get("/api/records/{record_id}/pdf")
async def export_pdf(record_id: str):
    """Xuất PDF Mẫu 15/BV-01 cho record đã approved."""
    data = l7_storage.load_record(record_id)
    if not data:
        raise HTTPException(404, "Record không tìm thấy")

    # Tạo BenhAnNgoaiTru từ form_data
    # patient_data: lấy từ form_data nếu có (Phase 0 không có M1 riêng)
    stored_form = data.get("form_data", {})
    _patient_data = None
    if stored_form.get("ho_va_ten"):
        _patient_data = {"ho_va_ten": stored_form.get("ho_va_ten", "")}
    benh_an = l6_generate_form.generate_benh_an(
        form_data=stored_form,
        doctor_cchn=data.get("doctor_cchn", ""),
        facility_id=data.get("facility_id", ""),
        patient_data=_patient_data,
    )
    benh_an.record_id = record_id
    benh_an.approved_by = data.get("approved_by", "")

    pdf_path = l9a_pdf_export.export_pdf(benh_an)

    # Cập nhật DB
    l7_storage.update_pdf_path(record_id, pdf_path)

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=Path(pdf_path).name,
    )


@app.post("/api/feedback")
async def submit_feedback(
    record_id: str = Form(...),
    doctor_cchn: str = Form(...),
    feedback_type: str = Form(...),   # drug_error|ner_error|icd_error|latency|other
    field_affected: str = Form(default=""),
    correct_value: str = Form(default=""),
    severity: str = Form(default="medium"),  # critical|high|medium|low
    comment: str = Form(default=""),
):
    """
    BS báo lỗi AI sau khi review bản nháp.
    ISO/IEC 42001:2023 Annex A.6.2 — Feedback mechanism bắt buộc.
    """
    conn = _get_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id TEXT, doctor_cchn TEXT,
                feedback_type TEXT, field_affected TEXT,
                correct_value TEXT, severity TEXT,
                comment TEXT, created_at TEXT,
                resolved INTEGER DEFAULT 0
            )
        """)
        from datetime import datetime
        conn.execute("""
            INSERT INTO feedback
            (record_id, doctor_cchn, feedback_type, field_affected,
             correct_value, severity, comment, created_at)
            VALUES (?,?,?,?,?,?,?,?)
        """, (record_id, doctor_cchn, feedback_type, field_affected,
              correct_value, severity, comment, datetime.now().isoformat()))
        conn.commit()

        l10_audit_log.log_event(
            conn, record_id, doctor_cchn, "FEEDBACK",
            f"{feedback_type}/{severity}: {field_affected}"
        )
    finally:
        conn.close()

    return {"status": "received", "severity": severity,
            "message": "Cảm ơn phản hồi — chúng tôi sẽ cải thiện AI."}


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.3.0"}
