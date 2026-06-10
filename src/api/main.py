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
from functools import lru_cache

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import logging

from ..core import l0_normalize, l1a_asr, l1b_drug_correct, l1c_ner
from ..core import l1d_icd_lookup, l2_validate, l3_route
from ..core import l4_human_gate, l4_correction_capture, l5_pii_scan, l6_generate_form
from ..core import l7_storage, l9a_pdf_export, l10_audit_log
from ..core.l7_storage import (
    init_db, _get_conn,
    save_doctor_profile, load_doctor_profile,
    get_pending_aliases, confirm_alias,
)
from ..core.dialect_norm import normalize_text as _dialect_normalize
from ..models.clinical_record import ClinicalRecord, RecordStatus
from ..models.doctor_profile import DoctorProfile, VALID_SPECIALTIES, VALID_REGIONS

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MediVoice VN",
    description="Documentation Assistant — AI tạo nháp, Bác sĩ chịu trách nhiệm",
    version="0.2.0",
)

# RAG model singletons — preloaded once at startup (FID-VN-011)
_embed_model = None
_drug_collection = None


@app.on_event("startup")
async def startup():
    global _embed_model, _drug_collection
    init_db()
    # Preload RAG embedding model + vectorstore if deps available
    try:
        from ..core.drug_rag import load_drug_vectorstore, _DEPS_AVAILABLE
        if _DEPS_AVAILABLE:
            from sentence_transformers import SentenceTransformer
            _embed_model = SentenceTransformer(
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            )
            _drug_collection = load_drug_vectorstore()
            logger.info("RAG model preloaded — embed_model ready, collection=%s", _drug_collection)
    except Exception as exc:
        logger.warning("RAG preload skipped: %s", exc)


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

        # DVP: load doctor profile for specialty + region injection (FID-VN-012)
        _dvp_profile = load_doctor_profile(doctor_cchn) if doctor_cchn else None
        _specialty = _dvp_profile.primary_specialty if _dvp_profile else "noi_khoa"
        _region = _dvp_profile.region if _dvp_profile else "auto"

        # L1a: ASR + A1 prompt injection with doctor specialty
        from ..core.l1b_drug_correct import _load_drug_db as _get_drug_db
        _drug_db = _get_drug_db()
        transcript_raw = l1a_asr.transcribe(audio_arr, drug_db=_drug_db, specialty=_specialty)

        # A3: Dialect normalization with doctor region (before L1b)
        transcript_normalized, _dialect_subs = _dialect_normalize(transcript_raw, _region)

        # L1b: Drug correction — v2 with optional RAG fallback (FID-VN-011)
        transcript_corrected, drug_matches = l1b_drug_correct.correct_drug_names_v2(
            transcript_normalized,
            rag_collection=_drug_collection,
            embed_model=_embed_model,
        )
        drug_candidates = [
            {"inn": dm.inn, "original_text": dm.original_text, "word_position": dm.word_position}
            for dm in drug_matches
        ]

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
            "dvp_specialty": _specialty,
            "dvp_region": _region,
            "dialect_subs": _dialect_subs,
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

    # Snapshot AI form trước khi áp dụng sửa đổi của BS
    ai_form_snapshot = dict(record.form_data)
    transcript_snapshot = record.transcript_corrected or ""

    # Áp dụng chỉnh sửa của BS nếu có
    if edited_form:
        try:
            edited_data = json.loads(edited_form)
            record = record.model_copy(update={"form_data": edited_data})
        except json.JSONDecodeError:
            pass

    # L4 Correction Capture — best-effort, không block approve flow (FID-VN-006)
    l4_correction_capture.capture(
        record_id=record_id,
        clinic_id=record.facility_id,
        transcript=transcript_snapshot,
        ai_form=ai_form_snapshot,
        bs_form=dict(record.form_data),
        doctor_cchn=doctor_cchn,
    )

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


# ── DVP — Doctor Profile endpoints (FID-VN-012) ───────────────────────────────

@app.post("/api/doctors")
async def register_doctor(
    cchn: str = Form(...),
    name: str = Form(...),
    region: str = Form(...),
    primary_specialty: str = Form(...),
    secondary_specialty: str = Form(default=""),
    english_level: str = Form(default="Basic"),
    speaking_speed: str = Form(default="Vừa"),
):
    """
    Đăng ký DoctorProfile — region + primary_specialty bắt buộc.
    DVP Layer 1: metadata ảnh hưởng chất lượng ASR ngay session 1.
    """
    if region not in VALID_REGIONS:
        raise HTTPException(400, f"region phải là: {sorted(VALID_REGIONS)}")
    if primary_specialty not in VALID_SPECIALTIES:
        raise HTTPException(400, f"primary_specialty phải là: {sorted(VALID_SPECIALTIES)}")

    from datetime import datetime as _dt
    profile = DoctorProfile(
        cchn=cchn,
        name=name,
        region=region,
        primary_specialty=primary_specialty,
        secondary_specialty=secondary_specialty or None,
        english_level=english_level,
        speaking_speed=speaking_speed,
        created_at=_dt.now().isoformat(),
    )
    save_doctor_profile(profile)
    return {"cchn": cchn, "status": "registered", "specialty": primary_specialty, "region": region}


@app.get("/api/doctors/{cchn}")
async def get_doctor(cchn: str):
    """Lấy DoctorProfile theo cchn."""
    profile = load_doctor_profile(cchn)
    if not profile:
        raise HTTPException(404, f"Doctor {cchn} chưa đăng ký DVP")
    return {
        "cchn": profile.cchn,
        "name": profile.name,
        "region": profile.region,
        "primary_specialty": profile.primary_specialty,
        "secondary_specialty": profile.secondary_specialty,
        "english_level": profile.english_level,
        "speaking_speed": profile.speaking_speed,
    }


@app.get("/api/doctors/{cchn}/aliases/pending")
async def get_alias_pending(cchn: str):
    """
    Lấy danh sách aliases đủ điều kiện promote (≥3 lần / ≥2 phiên).
    BS xem xét và confirm YES/NO — Human Gate alias (Luật KCB 2023 Đ.62).
    """
    from ..core.dvp_alias import check_and_promote
    candidates = check_and_promote(cchn)
    return {"cchn": cchn, "pending": candidates, "count": len(candidates)}


@app.post("/api/doctors/{cchn}/aliases/{alias_id}/confirm")
async def confirm_doctor_alias(
    cchn: str,
    alias_id: int,
    doctor_cchn: str = Form(...),
    confirmed: str = Form(...),   # "yes" | "no"
):
    """
    BS confirm hoặc reject alias candidate.
    Human Gate — BS phải xác nhận trước khi alias active.
    """
    if doctor_cchn != cchn:
        raise HTTPException(403, "Chỉ BS đó mới confirm alias của mình")
    is_confirmed = confirmed.lower() in ("yes", "true", "1", "có")
    confirm_alias(alias_id, is_confirmed)
    return {
        "alias_id": alias_id,
        "status": "confirmed" if is_confirmed else "rejected",
        "message": "Trợ lý đã cập nhật." if is_confirmed else "Đã bỏ qua alias này.",
    }


# ── UI-SUGGEST-001: Drug candidates, Terms, Dialect check ─────────────────
# FID-VN-010 — Prerequisite: A3 + RAG-001 done

# ─── Specialty term reference (load-time constant) ────────────────────────

_SPECIALTY_TERMS: dict[str, list[dict]] = {
    "noi_khoa": [
        {"term": "Tăng huyết áp", "icd": "I10", "common": "cao huyết áp"},
        {"term": "Đái tháo đường type 2", "icd": "E11.9", "common": "tiểu đường type 2"},
        {"term": "Rối loạn lipid máu", "icd": "E78.5", "common": "mỡ máu cao"},
        {"term": "Suy tim", "icd": "I50.9", "common": "suy tim"},
        {"term": "Nhồi máu cơ tim cấp", "icd": "I21.9", "common": "đau tim cấp"},
        {"term": "Đau thắt ngực ổn định", "icd": "I20.8", "common": "đau ngực khi gắng sức"},
        {"term": "Trào ngược dạ dày thực quản", "icd": "K21.0", "common": "GERD / ợ chua"},
        {"term": "Viêm dạ dày mạn", "icd": "K29.5", "common": "đau dạ dày"},
        {"term": "Nhiễm khuẩn tiết niệu", "icd": "N39.0", "common": "nhiễm trùng đường tiểu"},
        {"term": "Thiếu máu", "icd": "D64.9", "common": "thiếu máu"},
        {"term": "Tăng acid uric máu", "icd": "E79.0", "common": "gout / tống phong"},
        {"term": "Viêm phổi cộng đồng", "icd": "J18.9", "common": "viêm phổi"},
        {"term": "Bệnh phổi tắc nghẽn mạn tính", "icd": "J44.9", "common": "COPD"},
        {"term": "Đau cột sống thắt lưng", "icd": "M54.5", "common": "đau lưng dưới"},
        {"term": "Suy giáp nguyên phát", "icd": "E03.9", "common": "suy tuyến giáp"},
        {"term": "Cường giáp (Basedow)", "icd": "E05.0", "common": "cường giáp / Basedow"},
        {"term": "Viêm khớp dạng thấp", "icd": "M05.9", "common": "thấp khớp RA"},
        {"term": "Hội chứng chuyển hóa", "icd": "E88.81", "common": "béo phì + ĐTĐ + THA"},
        {"term": "Đái tháo đường type 1", "icd": "E10.9", "common": "tiểu đường type 1"},
        {"term": "Tâm phế mạn", "icd": "I27.9", "common": "tim phổi mạn"},
    ],
    "ho_hap": [
        {"term": "Viêm phế quản cấp", "icd": "J20.9", "common": "viêm phế quản"},
        {"term": "Viêm phổi cộng đồng", "icd": "J18.9", "common": "viêm phổi"},
        {"term": "Hen phế quản", "icd": "J45.9", "common": "hen suyễn / asthma"},
        {"term": "Bệnh phổi tắc nghẽn mạn tính", "icd": "J44.9", "common": "COPD"},
        {"term": "Viêm mũi dị ứng", "icd": "J30.4", "common": "dị ứng mũi"},
        {"term": "Viêm xoang cấp", "icd": "J01.9", "common": "viêm xoang"},
        {"term": "Lao phổi AFB (+)", "icd": "A15.0", "common": "lao phổi"},
        {"term": "Tràn dịch màng phổi", "icd": "J90", "common": "tràn dịch màng phổi"},
        {"term": "Đợt cấp COPD", "icd": "J44.1", "common": "COPD đợt cấp"},
        {"term": "COVID-19", "icd": "U07.1", "common": "COVID / corona"},
        {"term": "Tràn khí màng phổi", "icd": "J93.9", "common": "tràn khí màng phổi"},
        {"term": "Suy hô hấp cấp", "icd": "J96.0", "common": "suy thở cấp"},
    ],
    "tieu_hoa": [
        {"term": "Viêm dạ dày cấp", "icd": "K29.1", "common": "đau dạ dày cấp"},
        {"term": "Loét dạ dày tá tràng", "icd": "K27.9", "common": "loét dạ dày"},
        {"term": "Trào ngược dạ dày thực quản", "icd": "K21.0", "common": "GERD / ợ chua"},
        {"term": "Hội chứng ruột kích thích", "icd": "K58.9", "common": "IBS / đại tràng kích thích"},
        {"term": "Viêm đại tràng mạn", "icd": "K52.9", "common": "viêm đại tràng"},
        {"term": "Tiêu chảy cấp", "icd": "A09", "common": "tiêu chảy cấp"},
        {"term": "Táo bón mạn", "icd": "K59.0", "common": "táo bón"},
        {"term": "Viêm gan B mạn", "icd": "B18.1", "common": "viêm gan B"},
        {"term": "Xơ gan", "icd": "K74.6", "common": "xơ gan"},
        {"term": "Sỏi mật", "icd": "K80.2", "common": "sỏi túi mật"},
        {"term": "Viêm ruột thừa cấp", "icd": "K35.9", "common": "đau ruột thừa"},
        {"term": "Tắc ruột", "icd": "K56.7", "common": "tắc ruột"},
    ],
    "noi_tiet": [
        {"term": "Đái tháo đường type 2", "icd": "E11.9", "common": "tiểu đường type 2"},
        {"term": "Đái tháo đường type 1", "icd": "E10.9", "common": "tiểu đường type 1"},
        {"term": "Suy giáp nguyên phát", "icd": "E03.9", "common": "suy giáp"},
        {"term": "Cường giáp (Basedow)", "icd": "E05.0", "common": "cường giáp"},
        {"term": "Đái tháo đường thai kỳ", "icd": "O24.4", "common": "tiểu đường thai kỳ"},
        {"term": "Béo phì", "icd": "E66.9", "common": "béo phì / thừa cân"},
        {"term": "Tăng acid uric máu", "icd": "E79.0", "common": "gout / hyperuricemia"},
        {"term": "Hạ đường huyết", "icd": "E16.0", "common": "tụt đường huyết"},
        {"term": "Rối loạn lipid máu", "icd": "E78.5", "common": "mỡ máu cao"},
        {"term": "Hội chứng buồng trứng đa nang", "icd": "E28.2", "common": "PCOS"},
        {"term": "Suy thượng thận", "icd": "E27.4", "common": "suy thượng thận"},
        {"term": "Cường aldosterone nguyên phát", "icd": "E26.0", "common": "Conn / cường aldosteron"},
    ],
    "tai_mui_hong": [
        {"term": "Viêm amidan cấp có mủ", "icd": "J03.9", "common": "viêm amidan mủ"},
        {"term": "Viêm họng cấp", "icd": "J02.9", "common": "đau họng / viêm họng"},
        {"term": "Viêm mũi dị ứng", "icd": "J30.4", "common": "dị ứng mũi / hắt hơi"},
        {"term": "Viêm xoang cấp", "icd": "J01.9", "common": "viêm xoang"},
        {"term": "Viêm tai giữa cấp", "icd": "H66.0", "common": "viêm tai giữa cấp"},
        {"term": "Viêm mũi xuất tiết cấp", "icd": "J06.9", "common": "sổ mũi / cảm lạnh"},
        {"term": "Polyp mũi", "icd": "J33.9", "common": "polyp mũi"},
        {"term": "Ù tai mạn", "icd": "H93.1", "common": "ù tai"},
        {"term": "Chóng mặt lành tính (BPPV)", "icd": "H81.1", "common": "chóng mặt tư thế"},
        {"term": "Viêm thanh quản cấp", "icd": "J04.0", "common": "viêm thanh quản / khàn tiếng"},
        {"term": "Dị vật đường thở", "icd": "T17.9", "common": "dị vật họng"},
    ],
    "da_lieu": [
        {"term": "Mề đay cấp", "icd": "L50.0", "common": "nổi mề đay / dị ứng nổi mẩn"},
        {"term": "Viêm da cơ địa", "icd": "L20.9", "common": "chàm / eczema"},
        {"term": "Viêm da tiếp xúc", "icd": "L25.9", "common": "dị ứng tiếp xúc"},
        {"term": "Nấm da", "icd": "B35.9", "common": "nấm da / hắc lào"},
        {"term": "Viêm nang lông", "icd": "L73.9", "common": "mụn nhọt / viêm nang lông"},
        {"term": "Vẩy nến", "icd": "L40.9", "common": "vẩy nến / psoriasis"},
        {"term": "Trứng cá (acne)", "icd": "L70.0", "common": "mụn trứng cá"},
        {"term": "Zona thần kinh", "icd": "B02.9", "common": "giời leo / zona"},
        {"term": "Bệnh ghẻ", "icd": "B86", "common": "ghẻ ngứa"},
        {"term": "Nấm móng", "icd": "B35.1", "common": "nấm móng tay / chân"},
        {"term": "Rụng tóc từng mảng", "icd": "L63.9", "common": "rụng tóc mảng"},
    ],
    "co_xuong_khop": [
        {"term": "Viêm khớp dạng thấp", "icd": "M05.9", "common": "thấp khớp RA"},
        {"term": "Thoái hóa khớp gối", "icd": "M17.9", "common": "thoái hóa gối"},
        {"term": "Gout cấp", "icd": "M10.0", "common": "gout / tống phong cấp"},
        {"term": "Thoát vị đĩa đệm cột sống thắt lưng", "icd": "M51.1", "common": "thoát vị đĩa đệm"},
        {"term": "Đau cột sống cổ", "icd": "M54.2", "common": "đau cổ / thoái hóa cổ"},
        {"term": "Loãng xương", "icd": "M81.0", "common": "loãng xương"},
        {"term": "Hội chứng ống cổ tay", "icd": "G56.0", "common": "đau tê bàn tay"},
        {"term": "Viêm bao gân", "icd": "M65.9", "common": "viêm gân"},
        {"term": "Lupus ban đỏ hệ thống", "icd": "M32.9", "common": "SLE / lupus"},
        {"term": "Fibromyalgia", "icd": "M79.7", "common": "đau cơ mạn tính"},
    ],
    "nhi_khoa": [
        {"term": "Viêm họng cấp", "icd": "J02.9", "common": "đau họng trẻ em"},
        {"term": "Sốt xuất huyết Dengue", "icd": "A97.9", "common": "sốt xuất huyết"},
        {"term": "Viêm phế quản cấp", "icd": "J20.9", "common": "viêm phế quản trẻ"},
        {"term": "Tiêu chảy cấp", "icd": "A09", "common": "tiêu chảy trẻ em"},
        {"term": "Viêm tai giữa cấp", "icd": "H66.0", "common": "viêm tai giữa trẻ"},
        {"term": "Tay chân miệng", "icd": "B08.4", "common": "tay chân miệng"},
        {"term": "Thủy đậu", "icd": "B01.9", "common": "trái rạ / thủy đậu"},
        {"term": "Hen phế quản", "icd": "J45.9", "common": "hen suyễn trẻ em"},
        {"term": "Sốt không rõ nguyên nhân", "icd": "R50.9", "common": "sốt NRN"},
        {"term": "Còi xương — thiếu vitamin D", "icd": "E55.0", "common": "còi xương"},
    ],
}


class DialectCheckRequest(BaseModel):
    text: str
    region: str = "auto"


@lru_cache(maxsize=1)
def _get_drug_inn_list() -> list[str]:
    from ..core.l1b_drug_correct import _load_drug_db
    db = _load_drug_db()
    return list(db.get("by_inn", {}).keys())


def _fuzzy_drug_candidates(q: str, n: int = 3) -> list[dict]:
    """Fallback drug search when RAG vectorstore not available."""
    from rapidfuzz import process as rf_process
    inn_list = _get_drug_inn_list()
    results = rf_process.extract(q, inn_list, limit=n, score_cutoff=25)
    return [
        {"inn": r[0], "drug_class": "", "score": round(r[1] / 100, 3), "doc_snippet": r[0]}
        for r in results
    ]


@app.get("/api/drug-candidates")
async def get_drug_candidates(
    q: str = Query(..., description="Distorted ASR token"),
    diagnosis: str = Query(default="", description="Diagnosis context"),
    n: int = Query(default=3, ge=1, le=10),
):
    """
    Query drug candidates cho distorted ASR token + diagnosis context.
    Dùng RAG vector store nếu đã build; fallback về fuzzy match nếu chưa.
    FID-VN-010 UI-SUGGEST-001.
    """
    if not q.strip():
        return {"candidates": [], "source": "empty_query"}

    from ..core.drug_rag import load_drug_vectorstore, hybrid_query_drug, _DEPS_AVAILABLE

    if not _DEPS_AVAILABLE:
        candidates = _fuzzy_drug_candidates(q, n)
        return {"candidates": candidates, "source": "fuzzy_fallback"}

    # Use preloaded singletons if available (FID-VN-011); fall back to lazy load
    collection = _drug_collection or load_drug_vectorstore()
    if collection is None:
        candidates = _fuzzy_drug_candidates(q, n)
        return {"candidates": candidates, "source": "fuzzy_fallback"}

    from ..core.l1b_drug_correct import _load_drug_db
    drug_db = _load_drug_db()
    model = _embed_model
    if model is None:
        from sentence_transformers import SentenceTransformer as _ST
        model = _ST("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    candidates = hybrid_query_drug(
        q, diagnosis, collection, drug_db, embed_model_instance=model, k=n
    )
    return {"candidates": candidates, "source": "hybrid"}


@app.get("/api/terms")
async def get_terms(
    specialty: str = Query(default="noi_khoa", description="Specialty key"),
    n: int = Query(default=20, ge=1, le=50),
):
    """
    Lấy danh sách thuật ngữ y khoa theo chuyên khoa.
    Dùng để hiện sidebar gợi ý thuật ngữ trong UI.
    FID-VN-010 UI-SUGGEST-001.
    """
    terms = _SPECIALTY_TERMS.get(specialty, [])[:n]
    return {
        "specialty": specialty,
        "terms": terms,
        "count": len(terms),
        "available_specialties": list(_SPECIALTY_TERMS.keys()),
    }


@app.post("/api/dialect-check")
async def dialect_check(req: DialectCheckRequest):
    """
    Normalize dialect text + trả về substitutions đã thực hiện.
    Dùng để hiện dialect badge trong UI (FID-VN-010 UI-SUGGEST-001).
    Region: central | southern | northern | auto (auto-detect default).
    """
    from ..core.dialect_norm import normalize_text

    if not req.text.strip():
        return {"normalized": "", "substitutions": [], "region": req.region}

    normalized, subs = normalize_text(req.text, req.region)

    # detect_region để trả về region thật khi auto
    from ..core.dialect_norm import detect_region
    resolved_region = detect_region(req.text) if req.region == "auto" else req.region

    return {
        "normalized": normalized,
        "substitutions": subs,
        "region": resolved_region,
        "changed": len(subs) > 0,
    }
