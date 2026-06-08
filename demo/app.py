"""
MediVoice VN — Demo App
Streamlit Cloud deployment for BS pilot testing
Data collection: audio + corrections (no real PII)
"""
import streamlit as st
import json
import time
import io
import requests
from datetime import datetime


def transcribe_audio(audio_bytes: bytes) -> tuple[str, str]:
    """Transcribe using Google Cloud Speech-to-Text (Vietnamese).
    Tries WEBM_OPUS (Chrome/Edge) then OGG_OPUS (Firefox) automatically.
    Returns (transcript, error_msg).
    """
    try:
        from google.cloud import speech_v1 as speech
        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        client = speech.SpeechClient(credentials=creds)
        audio = speech.RecognitionAudio(content=audio_bytes)

        for encoding in [
            speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        ]:
            try:
                config = speech.RecognitionConfig(
                    encoding=encoding,
                    language_code="vi-VN",
                    enable_automatic_punctuation=True,
                    model="default",
                )
                response = client.recognize(config=config, audio=audio)
                texts = [
                    r.alternatives[0].transcript
                    for r in response.results
                    if r.alternatives
                ]
                text = " ".join(texts).strip()
                if text:
                    return text, ""
            except Exception:
                continue

        return "", "Không nhận diện được giọng nói — thử ghi âm lại rõ hơn"
    except Exception as e:
        return "", f"Speech API lỗi: {e}"


def upload_to_drive(audio_bytes: bytes, session_data: dict) -> tuple[bool, str]:
    """Returns (success, error_msg)."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload

        creds = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/drive"],
        )
        service = build("drive", "v3", credentials=creds, cache_discovery=False)
        folder_id = st.secrets["drive_folder_id"]
        ts = session_data["session_id"]

        audio_meta = {"name": f"medivoice_audio_{ts}.wav", "parents": [folder_id]}
        audio_media = MediaIoBaseUpload(io.BytesIO(audio_bytes), mimetype="audio/wav")
        service.files().create(
            body=audio_meta, media_body=audio_media, supportsAllDrives=True
        ).execute()

        json_bytes = json.dumps(session_data, ensure_ascii=False, indent=2).encode("utf-8")
        json_meta = {"name": f"medivoice_session_{ts}.json", "parents": [folder_id]}
        json_media = MediaIoBaseUpload(io.BytesIO(json_bytes), mimetype="application/json")
        service.files().create(
            body=json_meta, media_body=json_media, supportsAllDrives=True
        ).execute()

        return True, ""
    except Exception as e:
        return False, str(e)


st.set_page_config(
    page_title="MediVoice VN — Demo",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  .main { max-width: 640px; margin: 0 auto; }
  .disclaimer {
    background: #fff3e0; border-left: 4px solid #e65100;
    padding: 0.6rem 1rem; border-radius: 4px;
    font-size: 0.85rem; color: #e65100; font-weight: 600;
  }
  .result-box {
    background: #e8f0fe; border-radius: 8px; padding: 1rem;
    border: 1px solid #c5cae9; font-size: 0.9rem; white-space: pre-wrap;
  }
  .result-real {
    background: #e8f5e9; border-radius: 8px; padding: 1rem;
    border: 2px solid #2e7d32; font-size: 0.9rem; white-space: pre-wrap;
  }
  .conf-label { font-size: 0.8rem; color: #555; margin-bottom: 4px; }
  .drug-card {
    background: #f5f5f5; border-radius: 8px;
    padding: 0.5rem 0.75rem; margin-bottom: 0.4rem;
    font-size: 0.85rem;
  }
  .approved { color: #2e7d32; font-weight: 700; font-size: 1rem; }
  .badge-demo {
    background: #e3f2fd; color: #1565c0;
    padding: 2px 8px; border-radius: 12px;
    font-size: 0.72rem; font-weight: 600;
  }
</style>
""", unsafe_allow_html=True)

MOCK_CASES = {
    "Nội khoa tổng quát": {
        "transcript": "Bệnh nhân nam 45 tuổi, đau đầu vùng chẩm 3 ngày, không sốt, không nôn. Huyết áp đo được 155 trên 95. Nhịp tim 80 lần phút. Không tiền sử bệnh tim mạch. Chẩn đoán tăng huyết áp độ 1. Kê Amlodipine 5 milligram uống sáng, tái khám sau 4 tuần, theo dõi huyết áp tại nhà.",
        "ly_do": "Đau đầu vùng chẩm 3 ngày, huyết áp cao",
        "chan_doan": "Tăng huyết áp độ 1",
        "icd": "I10",
        "sinh_hieu": {"huyet_ap": "155/95", "mach": 80, "nhiet_do": 36.8},
        "don_thuoc": [
            {"ten": "Amlodipine", "ham_luong": "5mg", "lieu": "1 viên/sáng", "ngay": "30 ngày"},
        ],
        "tai_kham": "4 tuần",
        "confidence": 0.88,
    },
    "Hô hấp": {
        "transcript": "Bệnh nhân nữ 28 tuổi, ho có đờm vàng 5 ngày, sốt 38.2, nghe phổi ran ẩm hai đáy. Không khó thở. Chẩn đoán viêm phế quản cấp. Kê Amoxicillin-Clavulanate 625 milligram ngày 2 lần sau ăn, Bromhexine 8 milligram ngày 3 lần, Paracetamol 500 milligram khi sốt trên 38.5. Tái khám 7 ngày.",
        "ly_do": "Ho đờm vàng 5 ngày, sốt 38.2°C",
        "chan_doan": "Viêm phế quản cấp",
        "icd": "J20.9",
        "sinh_hieu": {"huyet_ap": "110/70", "mach": 90, "nhiet_do": 38.2},
        "don_thuoc": [
            {"ten": "Amoxicillin-Clavulanate", "ham_luong": "625mg", "lieu": "1 viên x 2/ngày", "ngay": "7 ngày"},
            {"ten": "Bromhexine", "ham_luong": "8mg", "lieu": "1 viên x 3/ngày", "ngay": "7 ngày"},
            {"ten": "Paracetamol", "ham_luong": "500mg", "lieu": "Khi sốt >38.5°C", "ngay": "7 ngày"},
        ],
        "tai_kham": "7 ngày",
        "confidence": 0.91,
    },
    "Tiêu hóa": {
        "transcript": "Bệnh nhân 50 tuổi, đau thượng vị sau ăn, ợ chua, buồn nôn 2 tuần. Không nôn ra máu, không đi ngoài phân đen. Chẩn đoán viêm dạ dày trào ngược. Kê Omeprazole 20 milligram sáng trước ăn 30 phút, Sucralfate 1 gram ngày 3 lần trước bữa ăn. Tái khám 4 tuần, nội soi nếu không cải thiện.",
        "ly_do": "Đau thượng vị, ợ chua, buồn nôn 2 tuần",
        "chan_doan": "Viêm dạ dày – trào ngược dạ dày thực quản",
        "icd": "K29.7",
        "sinh_hieu": {"huyet_ap": "120/80", "mach": 75, "nhiet_do": 36.6},
        "don_thuoc": [
            {"ten": "Omeprazole", "ham_luong": "20mg", "lieu": "1 viên/sáng trước ăn 30'", "ngay": "28 ngày"},
            {"ten": "Sucralfate", "ham_luong": "1g", "lieu": "1 gói x 3/ngày trước bữa ăn", "ngay": "28 ngày"},
        ],
        "tai_kham": "4 tuần",
        "confidence": 0.85,
    },
    "Nội tiết – Đái tháo đường": {
        "transcript": "Bệnh nhân nam 58 tuổi, đái tháo đường type 2 tái khám. Đường huyết lúc đói 8.5 mmol/L, cân nặng 78 kilogram. Bệnh nhân ăn nhiều tinh bột, ít vận động. Tiếp tục Metformin 500 milligram ngày 2 lần sau ăn. Thêm tư vấn chế độ ăn kiêng. Xét nghiệm HbA1c sau 3 tháng.",
        "ly_do": "Đái tháo đường type 2 – tái khám định kỳ",
        "chan_doan": "Đái tháo đường type 2 chưa kiểm soát tốt",
        "icd": "E11.9",
        "sinh_hieu": {"huyet_ap": "130/85", "mach": 76, "nhiet_do": 36.5, "can_nang": 78},
        "don_thuoc": [
            {"ten": "Metformin", "ham_luong": "500mg", "lieu": "1 viên x 2/ngày sau ăn", "ngay": "90 ngày"},
        ],
        "tai_kham": "3 tháng (kèm HbA1c)",
        "confidence": 0.93,
    },
    "Tai mũi họng": {
        "transcript": "Bệnh nhân 32 tuổi, đau họng nuốt đau 2 ngày, sốt 38 độ, không khó thở. Khám họng đỏ, amidan to độ 2, có mủ trắng. Chẩn đoán viêm amidan cấp mủ. Kê Amoxicillin 500 milligram ngày 3 lần sau ăn, Paracetamol 500 milligram khi sốt, súc họng nước muối ấm. Tái khám 5 ngày.",
        "ly_do": "Đau họng nuốt đau 2 ngày, sốt 38°C",
        "chan_doan": "Viêm amidan cấp có mủ",
        "icd": "J03.9",
        "sinh_hieu": {"huyet_ap": "115/75", "mach": 88, "nhiet_do": 38.0},
        "don_thuoc": [
            {"ten": "Amoxicillin", "ham_luong": "500mg", "lieu": "1 viên x 3/ngày sau ăn", "ngay": "7 ngày"},
            {"ten": "Paracetamol", "ham_luong": "500mg", "lieu": "Khi sốt >38°C", "ngay": "5 ngày"},
        ],
        "tai_kham": "5 ngày",
        "confidence": 0.90,
    },
    "Da liễu": {
        "transcript": "Bệnh nhân nữ 25 tuổi, nổi mẩn đỏ ngứa toàn thân 1 ngày sau ăn hải sản. Không phù mặt, không khó thở. Chẩn đoán mề đay cấp do dị ứng thức ăn. Kê Loratadine 10 milligram ngày 1 lần, Methylprednisolone 4 milligram ngày 2 lần sau ăn trong 3 ngày. Tránh hải sản. Tái khám nếu không đỡ hoặc khó thở.",
        "ly_do": "Mẩn đỏ ngứa toàn thân sau ăn hải sản",
        "chan_doan": "Mề đay cấp – dị ứng thức ăn",
        "icd": "L50.0",
        "sinh_hieu": {"huyet_ap": "112/72", "mach": 82, "nhiet_do": 36.7},
        "don_thuoc": [
            {"ten": "Loratadine", "ham_luong": "10mg", "lieu": "1 viên/ngày", "ngay": "7 ngày"},
            {"ten": "Methylprednisolone", "ham_luong": "4mg", "lieu": "1 viên x 2/ngày sau ăn", "ngay": "3 ngày"},
        ],
        "tai_kham": "Nếu không đỡ sau 3 ngày",
        "confidence": 0.87,
    },
}

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [("result", None), ("approved", False), ("drive_error", ""), ("drive_uploaded", False)]:
    if k not in st.session_state:
        st.session_state[k] = v
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🎙️ MediVoice VN")
st.markdown('<span class="badge-demo">DEMO — Phiên bản thử nghiệm</span>', unsafe_allow_html=True)
st.markdown("""
<div class="disclaimer">
⚠️ AI tạo nháp — Bác sĩ chịu trách nhiệm hoàn toàn về nội dung bệnh án<br>
🔒 DEMO: Vui lòng KHÔNG nhập tên/thông tin bệnh nhân thật
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Thông tin Bác sĩ ─────────────────────────────────────────────────────────
st.subheader("👤 Thông tin phiên khám")
col1, col2 = st.columns(2)
with col1:
    chuyen_khoa = st.selectbox("Chuyên khoa", list(MOCK_CASES.keys()), index=0)
with col2:
    cchn = st.text_input("Mã CCHN (demo)", placeholder="VD: CCHN-012345")

ten_bn_demo = st.text_input(
    "Tên bệnh nhân (dùng tên giả cho demo)",
    placeholder="VD: Bệnh nhân A, Nguyễn Văn Demo...",
    help="Không nhập tên thật trong bản demo này",
)

st.divider()

# ── Ghi âm ────────────────────────────────────────────────────────────────────
st.subheader("🎤 Ghi âm — Bác sĩ đọc ca lâm sàng tự nhiên")
st.caption("AI sẽ transcribe giọng BS bằng PhoWhisper. Form bên dưới là ví dụ minh họa NER — phiên bản production sẽ điền tự động từ transcript thật.")

audio_data = st.audio_input("Nhấn để ghi âm")

if audio_data is not None and not st.session_state.approved:
    audio_bytes = audio_data.getvalue()

    with st.spinner("🔄 Đang transcribe giọng nói (PhoWhisper-medium)..."):
        real_transcript, hf_error = transcribe_audio(audio_bytes)

    with st.spinner("🧠 Đang nhận diện thực thể y tế..."):
        time.sleep(0.8)

    result = MOCK_CASES[chuyen_khoa].copy()
    result["chuyen_khoa"] = chuyen_khoa
    result["ten_bn"] = ten_bn_demo or "Bệnh nhân Demo"
    result["cchn"] = cchn or "DEMO"
    result["audio"] = audio_bytes
    result["timestamp"] = datetime.now().isoformat()
    result["transcript_real"] = real_transcript
    result["hf_error"] = hf_error
    st.session_state.result = result
    st.session_state.approved = False
    st.session_state.drive_error = ""
    st.session_state.drive_uploaded = False

# ── Kết quả ───────────────────────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result
    st.divider()
    st.subheader("📋 Kết quả phân tích")

    real_t = r.get("transcript_real", "")
    hf_err = r.get("hf_error", "")

    if real_t:
        st.markdown("**🎙️ Transcript thật — PhoWhisper nghe giọng Bác sĩ**")
        st.markdown(f'<div class="result-real">{real_t}</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown("**📋 Form mô phỏng** *(NER production sẽ điền tự động từ transcript trên)*")
    else:
        if hf_err:
            st.warning(f"⚠️ Chưa transcribe được: **{hf_err}**")
        st.markdown("**Transcript mô phỏng** *(ví dụ minh họa — chuyên khoa đã chọn)*")

    st.markdown(f'<div class="result-box">{r["transcript"]}</div>', unsafe_allow_html=True)

    conf = r["confidence"]
    st.markdown(f'<div class="conf-label">Độ tin cậy mô phỏng: {int(conf*100)}%</div>', unsafe_allow_html=True)
    st.progress(conf)

    st.divider()

    st.subheader("📝 Nháp bệnh án (có thể chỉnh sửa)")
    col1, col2 = st.columns(2)
    sh = r.get("sinh_hieu", {})
    with col1:
        huyet_ap = st.text_input("Huyết áp (mmHg)", value=sh.get("huyet_ap", ""))
        mach = st.number_input("Mạch (lần/phút)", value=int(sh.get("mach", 0)), min_value=0, max_value=200)
    with col2:
        nhiet_do = st.number_input("Nhiệt độ (°C)", value=float(sh.get("nhiet_do", 36.5)), min_value=34.0, max_value=42.0, step=0.1)
        can_nang = st.number_input("Cân nặng (kg)", value=float(sh.get("can_nang", 0)), min_value=0.0, max_value=200.0, step=0.1)

    ly_do = st.text_area("Lý do khám", value=r.get("ly_do", ""), height=60)
    chan_doan = st.text_input("Chẩn đoán", value=r.get("chan_doan", ""))
    icd = st.text_input("Mã ICD-10-VN", value=r.get("icd", ""))
    tai_kham = st.text_input("Tái khám", value=r.get("tai_kham", ""))

    st.markdown("**Đơn thuốc**")
    for drug in r.get("don_thuoc", []):
        st.markdown(
            f'<div class="drug-card">💊 <b>{drug["ten"]}</b> {drug["ham_luong"]} — {drug["lieu"]} — {drug["ngay"]}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    st.subheader("💬 Phản hồi chất lượng")
    accuracy = st.radio(
        "Transcript AI có khớp với những gì Bác sĩ nói không?",
        ["✅ Đúng hoàn toàn", "🔶 Đúng một phần", "❌ Sai nhiều"],
        horizontal=True,
    )
    correction = st.text_area(
        "Bác sĩ ghi lại nội dung THỰC TẾ (nếu khác với transcript)",
        placeholder="Nếu AI nhận diện sai, ghi lại nội dung đúng ở đây để cải thiện hệ thống...",
        height=80,
    )

    st.divider()

    # Drive error hiện ở đây (persistent qua rerun)
    if st.session_state.drive_error:
        st.error(f"☁️ Drive upload lỗi: {st.session_state.drive_error}")

    col_approve, col_reject = st.columns(2)

    with col_approve:
        if st.button("✅ Xác nhận & Lưu", type="primary", use_container_width=True):
            if not st.session_state.approved:
                session_data = {
                    "session_id": st.session_state.session_id,
                    "timestamp": r["timestamp"],
                    "cchn": r["cchn"],
                    "ten_bn_demo": r["ten_bn"],
                    "chuyen_khoa": r["chuyen_khoa"],
                    "transcript_real": r.get("transcript_real", ""),
                    "transcript_mock": r["transcript"],
                    "accuracy_rating": accuracy,
                    "correction": correction,
                    "form_approved": {
                        "ly_do": ly_do,
                        "chan_doan": chan_doan,
                        "icd": icd,
                        "tai_kham": tai_kham,
                        "sinh_hieu": {
                            "huyet_ap": huyet_ap,
                            "mach": mach,
                            "nhiet_do": nhiet_do,
                            "can_nang": can_nang,
                        },
                        "don_thuoc": r["don_thuoc"],
                    },
                    "confidence": r["confidence"],
                }
                st.session_state.approved = True
                st.session_state.session_data = session_data

                if "gcp_service_account" in st.secrets:
                    with st.spinner("📤 Đang lưu lên Google Drive..."):
                        ok, err = upload_to_drive(r.get("audio", b""), session_data)
                    st.session_state.drive_uploaded = ok
                    st.session_state.drive_error = err
                st.rerun()

    with col_reject:
        if st.button("❌ Từ chối", use_container_width=True):
            st.warning("Đã từ chối — bệnh án không được lưu.")
            st.session_state.result = None
            st.session_state.approved = False
            st.rerun()

    if st.session_state.approved and hasattr(st.session_state, "session_data"):
        sd = st.session_state.session_data
        st.markdown('<p class="approved">✅ Bệnh án đã được xác nhận</p>', unsafe_allow_html=True)

        if st.session_state.drive_uploaded:
            st.success("☁️ Đã lưu tự động lên Google Drive của MediVoice")
        else:
            st.info("📩 Tải file bên dưới rồi gửi về **vietshares.com@gmail.com**")

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="⬇️ Tải dữ liệu phiên (JSON)",
                data=json.dumps(sd, ensure_ascii=False, indent=2),
                file_name=f"medivoice_session_{sd['session_id']}.json",
                mime="application/json",
                use_container_width=True,
            )
        with col_dl2:
            if "audio" in r:
                st.download_button(
                    label="⬇️ Tải file âm thanh",
                    data=r["audio"],
                    file_name=f"medivoice_audio_{sd['session_id']}.wav",
                    mime="audio/wav",
                    use_container_width=True,
                )

        st.info("📩 Gửi file JSON + âm thanh về: **vietshares.com@gmail.com** để đội ngũ cải thiện hệ thống. Cảm ơn Bác sĩ!")

        if st.button("🔄 Khám bệnh nhân tiếp theo"):
            st.session_state.result = None
            st.session_state.approved = False
            st.session_state.drive_error = ""
            st.session_state.drive_uploaded = False
            if hasattr(st.session_state, "session_data"):
                del st.session_state.session_data
            st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<center><small>MediVoice VN v0.8.4 · Demo · "
    "Liên hệ: vietshares.com@gmail.com · "
    "© 2026 Maple Leaf Group</small></center>",
    unsafe_allow_html=True,
)
