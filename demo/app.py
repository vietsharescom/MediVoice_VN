"""
MediVoice VN — Demo App v2.0
Streamlit Cloud deployment for BS pilot testing
UI: Mẫu 15/BV-01 layout per DESIGN_REPORT §7
Fix: audio-hash guard prevents re-processing on widget reruns
"""
import hashlib
import io
import json
import os
import sys
import wave
from datetime import datetime
from pathlib import Path

import requests
import streamlit as st

# set_page_config MUST be the first Streamlit call — before @st.cache_data
st.set_page_config(
    page_title="MediVoice VN",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="expanded",
)

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from demo.rag_chain import extract_clinical_rag as _rag_extract
    _RAG_OK = True
except Exception:
    _RAG_OK = False

# ── Helpers ───────────────────────────────────────────────────────────────────

@st.cache_data
def load_test_suite():
    path = os.path.join(os.path.dirname(__file__), "test_scripts", "test_suite.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _secret(key: str, default: str = "") -> str:
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def get_audio_duration(audio_bytes: bytes) -> float:
    try:
        with wave.open(io.BytesIO(audio_bytes)) as w:
            return round(w.getnframes() / w.getframerate(), 1)
    except Exception:
        return round(max(0, (len(audio_bytes) - 44) / 32000), 1)


def get_browser_info() -> str:
    try:
        ua = st.context.headers.get("user-agent", "")
        for browser in ("Edg", "Chrome", "Firefox", "Safari"):
            if browser in ua:
                return browser
        return ua[:60] if ua else "unknown"
    except Exception:
        return "unknown"


def audio_hash(audio_bytes: bytes) -> str:
    return hashlib.md5(audio_bytes).hexdigest()[:12]


def transcribe_audio(audio_bytes: bytes) -> tuple[str, str]:
    try:
        api_key = _secret("groq_api_key")
        if not api_key:
            return "", "groq_api_key chưa cấu hình trong Secrets"
        resp = requests.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            files={
                "file": ("audio.wav", io.BytesIO(audio_bytes), "audio/wav"),
                "model": (None, "whisper-large-v3"),
                "language": (None, "vi"),
                "response_format": (None, "json"),
            },
            timeout=60,
        )
        if resp.status_code == 200:
            text = resp.json().get("text", "").strip()
            return (text, "") if text else ("", "Không nhận diện được giọng nói")
        return "", f"Groq {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return "", f"Lỗi kết nối: {e}"


def extract_clinical_data(transcript: str) -> tuple[dict, str]:
    try:
        api_key = _secret("groq_api_key")
        if not api_key or not transcript:
            return {}, "Thiếu transcript hoặc API key"
        prompt = f"""Bạn là AI phân tích bệnh án tiếng Việt. Trích xuất thông tin lâm sàng từ lời BS nói.

QUY TẮC:
1. BỎ QUA: chào hỏi, tiếng ừ/à/hmm
2. Thông tin BN: tên/tuổi/giới nếu BS đề cập
3. Sinh hiệu: để 0/"" nếu không đề cập
4. Tên thuốc: chuẩn hóa về INN quốc tế
5. ICD-10: chỉ điền khi chắc chắn (I10/J20.9/E11.9...)
6. "ngay" để "" nếu BS không nói số ngày
7. Chỉ trả về JSON

TRANSCRIPT: {transcript}

JSON:
{{
  "benh_nhan": {{"ten": "", "tuoi": 0, "gioi": "Nam/Nữ/Không rõ", "nam_sinh": ""}},
  "ly_do": "",
  "chan_doan": "",
  "icd": "",
  "sinh_hieu": {{"nhiet_do": 0, "huyet_ap": "", "mach": 0, "can_nang": 0}},
  "don_thuoc": [{{"ten": "", "ham_luong": "", "lieu": "", "ngay": ""}}],
  "tai_kham": ""
}}"""
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 1000,
            },
            timeout=30,
        )
        if resp.status_code != 200:
            return {}, f"Groq LLM lỗi {resp.status_code}"
        content = resp.json()["choices"][0]["message"]["content"].strip()
        import re
        m = re.search(r"\{.*\}", content, re.DOTALL)
        if not m:
            return {}, "LLM không trả về JSON"
        data = json.loads(m.group())
        sh = data.get("sinh_hieu", {})
        for k, cast, default in [("nhiet_do", float, 36.5), ("mach", int, 0), ("can_nang", float, 0.0)]:
            try:
                sh[k] = cast(sh.get(k, default))
            except (ValueError, TypeError):
                sh[k] = default
        data["sinh_hieu"] = sh
        return data, ""
    except Exception as e:
        return {}, f"NER exception: {e}"


def upload_to_drive(audio_bytes: bytes, session_data: dict) -> tuple[bool, str]:
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
        service.files().create(
            body=audio_meta,
            media_body=MediaIoBaseUpload(io.BytesIO(audio_bytes), mimetype="audio/wav"),
            supportsAllDrives=True,
        ).execute()
        json_bytes = json.dumps(session_data, ensure_ascii=False, indent=2).encode()
        service.files().create(
            body={"name": f"medivoice_session_{ts}.json", "parents": [folder_id]},
            media_body=MediaIoBaseUpload(io.BytesIO(json_bytes), mimetype="application/json"),
            supportsAllDrives=True,
        ).execute()
        return True, ""
    except Exception as e:
        return False, str(e)


def auto_score(form_approved: dict, ground_truth: dict) -> dict:
    scores = {}
    gt_cd = ground_truth.get("chan_doan", "").lower().strip()
    ap_cd = form_approved.get("chan_doan", "").lower().strip()
    scores["chan_doan"] = "✅" if gt_cd and ap_cd and (gt_cd in ap_cd or ap_cd in gt_cd) else "❌"
    gt_icd = ground_truth.get("icd", "").strip()
    ap_icd = form_approved.get("icd", "").strip()
    scores["icd"] = "✅" if gt_icd and ap_icd and (gt_icd in ap_icd or ap_icd in gt_icd) else ("⚠️" if not ap_icd else "❌")
    gt_drugs = {d["ten"].lower() for d in ground_truth.get("don_thuoc", [])}
    ap_drugs = {d["ten"].lower() for d in form_approved.get("don_thuoc", [])}
    if gt_drugs:
        matched = sum(1 for g in gt_drugs if any(g in a or a in g for a in ap_drugs))
        scores["don_thuoc"] = f"✅ {matched}/{len(gt_drugs)}" if matched == len(gt_drugs) else f"⚠️ {matched}/{len(gt_drugs)}"
    else:
        scores["don_thuoc"] = "N/A"
    return scores



st.markdown("""
<style>
  section.main > div { max-width: 680px; margin: 0 auto; }
  .disclaimer {
    background:#fff3e0; border-left:4px solid #e65100;
    padding:0.5rem 0.9rem; border-radius:4px;
    font-size:0.82rem; color:#e65100; font-weight:600; margin-bottom:0.5rem;
  }
  .mau15-box {
    background:#f8fafb; border:1.5px solid #b0bec5; border-radius:10px;
    padding:1.2rem 1.4rem; margin-top:0.5rem;
  }
  .mau15-header {
    font-size:0.78rem; color:#546e7a; font-weight:700;
    text-transform:uppercase; letter-spacing:0.06em; margin-bottom:0.7rem;
  }
  .transcript-box {
    background:#e8f5e9; border:2px solid #2e7d32; border-radius:8px;
    padding:0.9rem 1rem; font-size:0.88rem; white-space:pre-wrap;
    line-height:1.5; color:#1b5e20;
  }
  .confidence-bar {
    height:6px; border-radius:3px; background:#e0e0e0; margin:4px 0 8px;
  }
  .confidence-fill {
    height:6px; border-radius:3px;
    background: linear-gradient(90deg, #ef5350 0%, #ffa726 40%, #66bb6a 80%);
  }
  .drug-card {
    background:#fff; border:1px solid #e0e0e0; border-radius:8px;
    padding:0.55rem 0.8rem; margin-bottom:0.35rem;
    display:flex; align-items:center; gap:0.5rem;
  }
  .drug-flagged { border-color:#ffa726; background:#fff8e1; }
  .approved-stamp {
    color:#2e7d32; font-weight:800; font-size:1.05rem;
    text-align:center; padding:0.3rem;
  }
  .badge-demo {
    background:#e3f2fd; color:#1565c0;
    padding:2px 10px; border-radius:12px;
    font-size:0.72rem; font-weight:700;
  }
  .section-label {
    font-size:0.78rem; font-weight:700; color:#455a64;
    text-transform:uppercase; letter-spacing:0.05em;
    margin: 0.8rem 0 0.3rem;
  }
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
_DEFAULTS = {
    "result": None, "approved": False,
    "drive_error": "", "drive_uploaded": False,
    "_audio_hash": None,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

# ── Test Mode Sidebar ─────────────────────────────────────────────────────────
test_suite = load_test_suite()
active_script = None
if test_suite:
    with st.sidebar:
        st.markdown("## 🧪 Test Mode")
        script_options = {f"{s['id']} · {s['title']}": s for s in test_suite["scripts"]}
        selected = st.selectbox("Script", ["— Demo thường —"] + list(script_options.keys()))
        if selected != "— Demo thường —":
            active_script = script_options[selected]
            s = active_script
            st.caption(f"**Weakness:** `{s['target_weakness']}` · {'⭐'*s['difficulty']}")
            st.info(s["clinical_content"])
            st.warning(s["natural_wrapper"])

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🎙️ MediVoice VN")
st.markdown('<span class="badge-demo">DEMO — Thử nghiệm · v2.0</span>', unsafe_allow_html=True)
st.markdown("""
<div class="disclaimer">
⚠️ AI tạo nháp — Bác sĩ chịu trách nhiệm hoàn toàn về nội dung bệnh án<br>
🔒 DEMO: Vui lòng KHÔNG nhập tên/thông tin bệnh nhân thật
</div>
""", unsafe_allow_html=True)

# ── Thông tin Bác sĩ ─────────────────────────────────────────────────────────
st.subheader("👨‍⚕️ Thông tin phiên khám")
c1, c2 = st.columns(2)
with c1:
    ten_bs = st.text_input("Tên Bác sĩ ★", placeholder="BS Nguyễn Văn An", key="ten_bs")
with c2:
    co_so = st.text_input("Cơ sở y tế ★", placeholder="Phòng khám ABC", key="co_so")

c3, c4, c5 = st.columns(3)
with c3:
    cchn = st.text_input("Mã CCHN ★", placeholder="CCHN-012345", key="cchn")
with c4:
    SPECIALTIES = [
        "Nội khoa tổng quát", "Tim mạch", "Hô hấp", "Tiêu hóa",
        "Nội tiết – Đái tháo đường", "Tai mũi họng", "Da liễu",
        "Cơ xương khớp", "Nhi", "Sản phụ khoa", "Ngoại",
        "Chẩn đoán hình ảnh",
    ]
    chuyen_khoa = st.selectbox("Chuyên khoa", SPECIALTIES, key="chuyen_khoa")
with c5:
    ngay_kham_str = datetime.now().strftime("%d/%m/%Y")
    st.text_input("Ngày khám", value=ngay_kham_str, disabled=True)

_pf1, _pf2, _pf3 = st.columns([3, 1, 1])
with _pf1:
    ten_bn_demo = st.text_input(
        "Tên bệnh nhân *(dùng tên giả cho demo)*",
        placeholder="Bệnh nhân A / Nguyễn Văn Demo...",
        help="Không nhập tên thật trong bản demo",
        key="ten_bn_demo",
    )
with _pf2:
    tuoi_bn_demo = st.number_input("Tuổi BN", min_value=0, max_value=120, value=0, key="tuoi_bn_demo")
with _pf3:
    _gioi_pre_opts = ["Không rõ", "Nam", "Nữ"]
    gioi_bn_demo = st.selectbox("Giới tính", _gioi_pre_opts, key="gioi_bn_demo")

st.divider()

# ── Ghi âm ────────────────────────────────────────────────────────────────────
st.subheader("🎤 Ghi âm")

recording_type = st.radio(
    "Loại ghi âm",
    ["🗒️ Script chuẩn", "💬 Tự nhiên"],
    horizontal=True,
    help="Script: đo baseline accuracy · Tự nhiên: dữ liệu training thực",
)
if "Tự nhiên" in recording_type:
    st.info("💬 Nói tự nhiên như đang khám thật. AI tự lọc thông tin lâm sàng.")
else:
    st.info("🗒️ Đọc theo script, nói rõ ràng, đủ thông tin lâm sàng.")

with st.expander("💡 Tips ghi âm — tên thuốc & sinh hiệu", expanded=False):
    st.markdown("""
**Tên thuốc khó → nói chậm 2 lần:** *"Atorvastatin... Atorvastatin... 20 milligram"*

**Sinh hiệu → đọc rõ từng chỉ số:** *"Huyết áp 130 trên 85 — mạch 72 — cân 68 kilo"*

**Liều lượng:** nói "5 milligram" thay vì "5mg" — **Tái khám:** nói cuối cùng sau đơn thuốc
    """)

audio_data = st.audio_input("Nhấn để ghi âm")

# ── Audio processing — HASH GUARD (fix: prevent re-processing on reruns) ─────
if audio_data is not None and not st.session_state.approved:
    audio_bytes = audio_data.getvalue()
    current_hash = audio_hash(audio_bytes)

    if st.session_state._audio_hash != current_hash:
        # NEW audio — process it
        st.session_state._audio_hash = current_hash

        with st.spinner("🔄 MediVoice AI đang nhận dạng giọng nói..."):
            real_transcript, asr_error = transcribe_audio(audio_bytes)

        clinical_data: dict = {}
        ner_error = ""
        drug_flags: list = []

        if real_transcript:
            api_key = _secret("groq_api_key")
            try:
                if _RAG_OK and api_key:
                    with st.spinner("🧠 Đang phân tích lâm sàng (RAG pipeline)..."):
                        clinical_data, ner_error, drug_flags = _rag_extract(real_transcript, api_key)
                else:
                    with st.spinner("🧠 Đang phân tích lâm sàng..."):
                        clinical_data, ner_error = extract_clinical_data(real_transcript)
            except Exception as e:
                ner_error = f"NER lỗi: {e}"
                clinical_data = {}

        result = {
            "transcript_real": real_transcript,
            "asr_error": asr_error,
            "ner_ok": bool(clinical_data),
            "ner_error": ner_error,
            "audio": audio_bytes,
            "timestamp": datetime.now().isoformat(),
            "chuyen_khoa": chuyen_khoa,
            "ten_bn": ten_bn_demo or "Bệnh nhân Demo",
            "cchn": cchn or "DEMO",
            "confidence": 0.88 if clinical_data else 0.0,
            "benh_nhan_ner": clinical_data.get("benh_nhan", {}) if clinical_data else {},
            "ly_do": clinical_data.get("ly_do", "") if clinical_data else "",
            "chan_doan": clinical_data.get("chan_doan", "") if clinical_data else "",
            "icd": clinical_data.get("icd", "") if clinical_data else "",
            "sinh_hieu": clinical_data.get("sinh_hieu", {"nhiet_do": 36.5, "huyet_ap": "", "mach": 0, "can_nang": 0.0}) if clinical_data else {"nhiet_do": 36.5, "huyet_ap": "", "mach": 0, "can_nang": 0.0},
            "don_thuoc": clinical_data.get("don_thuoc", []) if clinical_data else [],
            "tai_kham": clinical_data.get("tai_kham", "") if clinical_data else "",
            "drug_flags": [
                {"inn": m.inn, "original": m.original_text, "reason": m.flag_reason, "confidence": round(m.confidence, 2)}
                for m in drug_flags
                if m.flagged_for_review and (m.confidence >= 0.85 or m.flag_reason == "DOSE_OUT_OF_RANGE")
            ] if drug_flags else [],
            "form_ner": {
                "ly_do": clinical_data.get("ly_do", "") if clinical_data else "",
                "chan_doan": clinical_data.get("chan_doan", "") if clinical_data else "",
                "icd": clinical_data.get("icd", "") if clinical_data else "",
                "sinh_hieu": clinical_data.get("sinh_hieu", {}) if clinical_data else {},
                "don_thuoc": clinical_data.get("don_thuoc", []) if clinical_data else [],
                "tai_kham": clinical_data.get("tai_kham", "") if clinical_data else "",
            },
        }
        st.session_state.result = result
        st.session_state.approved = False
        st.session_state.drive_error = ""
        st.session_state.drive_uploaded = False
        # Clean drug confirm keys
        for _k in [k for k in st.session_state.keys() if k.startswith("drug_confirm_")]:
            del st.session_state[_k]
        st.rerun()  # force re-render from new state — form will show on next pass

# ── Kết quả — MẪU 15/BV-01 layout ────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result
    st.divider()

    # ── Transcript box + confidence ───────────────────────────────────────────
    real_t = r.get("transcript_real", "")
    asr_err = r.get("asr_error", "")
    ner_ok = r.get("ner_ok", False)
    ner_err = r.get("ner_error", "")
    conf = r.get("confidence", 0.0)
    _flags = r.get("drug_flags", [])

    if real_t:
        st.markdown("#### 🎙️ AI nghe giọng Bác sĩ")
        st.markdown(f'<div class="transcript-box">{real_t}</div>', unsafe_allow_html=True)
        conf_pct = int(conf * 100) if conf else 0
        col_conf, col_status = st.columns([3, 2])
        with col_conf:
            st.markdown(
                f'<div style="font-size:0.8rem;color:#555;margin-top:4px;">'
                f'Độ tin cậy AI: <b>{conf_pct}%</b></div>'
                f'<div class="confidence-bar"><div class="confidence-fill" style="width:{conf_pct}%"></div></div>',
                unsafe_allow_html=True,
            )
        with col_status:
            if ner_ok:
                st.success("✅ Form tự động điền")
            elif ner_err:
                st.warning(f"⚠️ NER: {ner_err[:80]}")
            else:
                st.info("ℹ️ Form dùng ví dụ")
        for f in _flags:
            st.warning(f"⚠️ Thuốc cần xác nhận: **{f['inn']}** (nghe: *{f['original']}* · {f['reason']} · {f['confidence']:.0%})")
    else:
        if asr_err:
            st.warning(f"⚠️ Chưa transcribe được: **{asr_err}**")
        else:
            st.info("ℹ️ Chưa có transcript — dùng ví dụ minh họa theo chuyên khoa")

    # ── Đánh giá transcript ───────────────────────────────────────────────────
    def _s(v): return {1:"1 ❌", 2:"2 🔴", 3:"3 🟡", 4:"4 🟢", 5:"5 ✅"}[v]
    score_transcript = st.select_slider(
        "Transcript nghe đúng chưa?", options=[1,2,3,4,5], value=5,
        format_func=_s, key="score_transcript",
        help="1=Sai hoàn toàn · 5=Đúng hoàn toàn",
    )

    st.divider()

    # ── MẪU 15/BV-01 ─────────────────────────────────────────────────────────
    st.subheader("📋 Mẫu 15/BV-01 — Nháp AI")
    st.markdown("""
    <div class="disclaimer" style="font-size:0.78rem;">
    ⚠️ AI tạo nháp — Bác sĩ xem lại, chỉnh sửa và chịu trách nhiệm hoàn toàn
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        # ── I. Thông tin hành chính ───────────────────────────────────────────
        st.markdown('<div class="section-label">I. Thông tin bệnh nhân</div>', unsafe_allow_html=True)
        _bn = r.get("benh_nhan_ner", {})
        # Fallback: use pre-filled values from top-of-page inputs when NER didn't extract them
        _ten_fallback  = _bn.get("ten","") or st.session_state.get("ten_bn_demo","")
        _tuoi_fallback = int(_bn.get("tuoi",0) or 0) or int(st.session_state.get("tuoi_bn_demo",0) or 0)
        _gioi_fallback = _bn.get("gioi","") or st.session_state.get("gioi_bn_demo","Không rõ")

        c1, c2, c3 = st.columns(3)
        with c1:
            bn_ten = st.text_input("Họ tên BN", value=_ten_fallback, placeholder="(Demo)")
        with c2:
            bn_tuoi = st.number_input("Tuổi", value=_tuoi_fallback, min_value=0, max_value=120)
        with c3:
            _gioi_opts = ["Không rõ","Nam","Nữ"]
            bn_gioi = st.selectbox("Giới tính", _gioi_opts,
                index=_gioi_opts.index(_gioi_fallback) if _gioi_fallback in _gioi_opts else 0)

        c4, c5, c6 = st.columns(3)
        with c4:
            bn_nam_sinh = st.text_input("Năm sinh", value=_bn.get("nam_sinh","") or "")
        with c5:
            bn_sdt = st.text_input("SĐT", placeholder="(Demo)")
        with c6:
            bn_cccd = st.text_input("CCCD/CMND", placeholder="(Demo)")

        ca1, ca2, ca3 = st.columns(3)
        with ca1:
            score_ten = st.select_slider("Tên BN", [1,2,3,4,5], 5, _s, key="score_ten")
        with ca2:
            score_tuoi = st.select_slider("Tuổi", [1,2,3,4,5], 5, _s, key="score_tuoi")
        with ca3:
            score_ngay = st.select_slider("Ngày khám", [1,2,3,4,5], 5, _s, key="score_ngay")

        st.divider()

        # ── II. Lý do vào viện ────────────────────────────────────────────────
        st.markdown('<div class="section-label">II. Lý do khám / Triệu chứng chính</div>', unsafe_allow_html=True)
        ly_do = st.text_area("", value=r.get("ly_do",""), height=60, placeholder="VD: Đau đầu vùng chẩm 3 ngày, huyết áp cao", label_visibility="collapsed")
        score_ly_do = st.select_slider("Lý do khám đúng chưa?", [1,2,3,4,5], 5, _s, key="score_ly_do")

        st.divider()

        # ── III. Sinh hiệu ────────────────────────────────────────────────────
        st.markdown('<div class="section-label">III. Sinh hiệu</div>', unsafe_allow_html=True)
        sh = r.get("sinh_hieu", {})
        cs1, cs2, cs3, cs4 = st.columns(4)
        with cs1:
            huyet_ap = st.text_input("Huyết áp (mmHg)", value=sh.get("huyet_ap",""), placeholder="120/80")
        with cs2:
            mach = st.number_input("Mạch (lần/ph)", value=int(sh.get("mach",0)), min_value=0, max_value=200)
        with cs3:
            _nd = float(sh.get("nhiet_do",0) or 0)
            nhiet_do = st.number_input("Nhiệt độ (°C)", value=_nd if 34.0<=_nd<=42.0 else 36.5,
                                        min_value=34.0, max_value=42.0, step=0.1)
        with cs4:
            can_nang = st.number_input("Cân nặng (kg)", value=float(sh.get("can_nang",0)), min_value=0.0, max_value=200.0, step=0.1)
        score_sh = st.select_slider("Sinh hiệu đúng chưa?", [1,2,3,4,5], 5, _s, key="score_sh")

        st.divider()

        # ── IV. Chẩn đoán + ICD ───────────────────────────────────────────────
        st.markdown('<div class="section-label">IV. Chẩn đoán lâm sàng ★</div>', unsafe_allow_html=True)
        chan_doan = st.text_input(
            "Chẩn đoán chính ★",
            value=r.get("chan_doan",""),
            placeholder="VD: Tăng huyết áp độ 1 / Viêm phế quản cấp / Đái tháo đường type 2",
            help="Bắt buộc theo TT32/2023. BS chịu trách nhiệm hoàn toàn.",
            label_visibility="collapsed",
        )
        ci1, ci2 = st.columns(2)
        with ci1:
            icd = st.text_input("Mã ICD-10-VN ★", value=r.get("icd",""), placeholder="VD: J20.9 / I10 / E11.9")
        with ci2:
            tai_kham = st.text_input("Tái khám", value=r.get("tai_kham",""), placeholder="VD: 7 ngày / 1 tháng")
        cd1, cd2 = st.columns(2)
        with cd1:
            score_cd = st.select_slider("Chẩn đoán đúng chưa?", [1,2,3,4,5], 5, _s, key="score_cd")
        with cd2:
            score_tk = st.select_slider("Tái khám đúng chưa?", [1,2,3,4,5], 5, _s, key="score_tk")

        st.divider()

        # ── V. Đơn thuốc — L4 Human Gate ────────────────────────────────────
        st.markdown('<div class="section-label">V. Đơn thuốc — Bác sĩ xác nhận từng thuốc ★</div>', unsafe_allow_html=True)
        _don_thuoc = r.get("don_thuoc", [])
        _flags_map = {f["inn"].lower(): f for f in _flags}

        def _flag_for(drug_name: str):
            dn = drug_name.lower()
            for k, v in _flags_map.items():
                if k in dn or dn in k:
                    return v
            return None

        _drug_confirmed = []
        for _i, _drug in enumerate(_don_thuoc):
            _name = _drug.get("ten", "")
            _hl = _drug.get("ham_luong","")
            _lieu = _drug.get("lieu","")
            _ngay = _drug.get("ngay","")
            _flag = _flag_for(_name)
            _label_parts = [f"**{_name}** {_hl}".strip()]
            if _lieu: _label_parts.append(_lieu)
            if _ngay: _label_parts.append(_ngay)
            _label = " · ".join(p for p in _label_parts if p.strip())

            dc1, dc2 = st.columns([5,1])
            with dc1:
                if _flag:
                    st.warning(f"⚠️ {_label}  |  AI nghe: *{_flag['original']}*  |  {_flag['confidence']:.0%}")
                else:
                    st.markdown(f'<div class="drug-card">💊 {_label}</div>', unsafe_allow_html=True)
            with dc2:
                _confirmed = st.checkbox("✓", key=f"drug_confirm_{_i}",
                                          help=f"Xác nhận {_name}: tên, liều, số ngày đúng")
                _drug_confirmed.append(_confirmed)

        if not _don_thuoc:
            st.caption("*(Chưa phát hiện đơn thuốc trong giọng nói)*")

        _all_confirmed = all(_drug_confirmed) if _drug_confirmed else True
        if _drug_confirmed:
            n_ok = sum(_drug_confirmed)
            if _all_confirmed:
                st.success(f"✅ {len(_drug_confirmed)}/{len(_drug_confirmed)} thuốc đã xác nhận")
            else:
                st.info(f"💊 {n_ok}/{len(_drug_confirmed)} thuốc — tick ✓ từng thuốc trước khi lưu")

        score_dt = st.select_slider("Đơn thuốc đúng chưa?", [1,2,3,4,5], 5, _s, key="score_dt")

    st.divider()

    # ── Ghi chú môi trường ────────────────────────────────────────────────────
    st.markdown("**🎙️ Ghi chú cho dữ liệu training**")
    nc1, nc2 = st.columns(2)
    with nc1:
        note_giong = st.multiselect("Giọng vùng miền",
            ["Bắc","Trung","Nam","Huế","Tây Nguyên","Khác"], key="note_giong")
        note_noise = st.multiselect("Môi trường",
            ["Yên tĩnh","Ồn quạt","Ồn nhiều người","Phòng vang","Tiếng xe ngoài"], key="note_noise")
    with nc2:
        note_bs = st.multiselect("Đặc điểm BS",
            ["Rõ ràng","Nói nhanh","Giọng nhẹ","Tiếng địa phương","Thuật ngữ đặc biệt"], key="note_bs")
        correction = st.text_input("Ghi chú sửa lỗi AI",
            placeholder="VD: 'L'Occitane'→Losartan · ồn quạt · giọng Nam",
            key="correction_text")

    _scores = [score_transcript, score_ten, score_tuoi, score_ngay, score_sh, score_cd, score_dt, score_tk, score_ly_do]
    avg_score = round(sum(_scores)/len(_scores), 1)

    st.divider()

    # ── Drive error display ───────────────────────────────────────────────────
    if st.session_state.drive_error:
        if "local_saves" in st.session_state.drive_error:
            st.info(f"💾 {st.session_state.drive_error}")
        else:
            st.error(f"☁️ Drive: {st.session_state.drive_error}")

    # ── Action buttons ────────────────────────────────────────────────────────
    ba1, ba2 = st.columns(2)
    with ba1:
        if not _all_confirmed and _drug_confirmed:
            st.warning("⚠️ Tick ✓ xác nhận từng thuốc")
        if st.button("✅ Phê duyệt & Lưu", type="primary",
                      use_container_width=True, disabled=not _all_confirmed):
            if not st.session_state.approved:
                session_data = {
                    "session_id": st.session_state.session_id,
                    "timestamp": r["timestamp"],
                    "ngay_kham": ngay_kham_str,
                    "ten_bs": ten_bs,
                    "co_so": co_so,
                    "cchn": r["cchn"],
                    "ten_bn_demo": r["ten_bn"],
                    "chuyen_khoa": chuyen_khoa,
                    "audio_duration_sec": get_audio_duration(r.get("audio", b"")),
                    "device_browser": get_browser_info(),
                    "recording_type": "script" if "Script" in recording_type else "natural",
                    "transcript_real": r.get("transcript_real",""),
                    "accuracy_rating": f"{avg_score}/5",
                    "avg_score": avg_score,
                    "benh_nhan": {
                        "ten": bn_ten, "tuoi": bn_tuoi, "gioi": bn_gioi,
                        "nam_sinh": bn_nam_sinh, "sdt": bn_sdt, "cccd": bn_cccd,
                    },
                    "field_eval": {
                        "transcript": score_transcript, "ten_bn": score_ten,
                        "tuoi": score_tuoi, "ngay_kham": score_ngay,
                        "ly_do": score_ly_do, "sinh_hieu": score_sh,
                        "chan_doan": score_cd, "don_thuoc": score_dt, "tai_kham": score_tk,
                    },
                    "notes": {"giong_vung_mien": note_giong, "moi_truong": note_noise, "dac_diem_bs": note_bs},
                    "correction": correction,
                    "form_ner": r.get("form_ner", {}),
                    "form_approved": {
                        "ly_do": ly_do,
                        "chan_doan": chan_doan,
                        "icd": icd,
                        "tai_kham": tai_kham,
                        "sinh_hieu": {"huyet_ap": huyet_ap, "mach": mach, "nhiet_do": nhiet_do, "can_nang": can_nang},
                        "don_thuoc": r["don_thuoc"],
                    },
                    "test_script_id": active_script["id"] if active_script else None,
                    "ground_truth": active_script["ground_truth"] if active_script else None,
                }
                if active_script:
                    session_data["auto_score"] = auto_score(
                        {"chan_doan": chan_doan, "icd": icd,
                         "sinh_hieu": {"huyet_ap": huyet_ap, "mach": mach},
                         "don_thuoc": r["don_thuoc"]},
                        active_script["ground_truth"],
                    )
                st.session_state.approved = True
                st.session_state.session_data = session_data

                # Upload
                try:
                    _has_gcp = "gcp_service_account" in st.secrets
                except Exception:
                    _has_gcp = False

                if _has_gcp:
                    with st.spinner("📤 Đang lưu lên Google Drive..."):
                        ok, err = upload_to_drive(r.get("audio", b""), session_data)
                    st.session_state.drive_uploaded = ok
                    st.session_state.drive_error = err
                else:
                    _save_dir = Path(__file__).parent / "local_saves"
                    _save_dir.mkdir(exist_ok=True)
                    _path = _save_dir / f"session_{session_data['session_id']}.json"
                    try:
                        _path.write_text(json.dumps(session_data, ensure_ascii=False, indent=2), encoding="utf-8")
                        st.session_state.drive_error = f"Local mode — đã lưu: demo/local_saves/{_path.name}"
                    except Exception as _e:
                        st.session_state.drive_error = f"Local save lỗi: {_e}"

                st.rerun()

    with ba2:
        if st.button("❌ Từ chối", use_container_width=True):
            st.session_state.result = None
            st.session_state.approved = False
            st.session_state._audio_hash = None
            st.rerun()

    # ── Approved state ────────────────────────────────────────────────────────
    if st.session_state.approved and hasattr(st.session_state, "session_data"):
        sd = st.session_state.session_data
        st.markdown('<p class="approved-stamp">✅ Bệnh án đã được Bác sĩ phê duyệt & lưu</p>', unsafe_allow_html=True)

        if st.session_state.get("drive_uploaded"):
            st.success("☁️ Đã lưu lên Google Drive — cảm ơn Bác sĩ!")
        elif st.session_state.get("drive_error"):
            if "local_saves" not in st.session_state.drive_error:
                st.warning("📩 Drive lỗi — tải file bên dưới gửi về **vietshares.com@gmail.com**")

        if sd.get("auto_score"):
            sc = sd["auto_score"]
            st.markdown(f"### 🎯 Auto-score — Script `{sd.get('test_script_id')}`")
            sc_cols = st.columns(len(sc))
            for i, (field, score) in enumerate(sc.items()):
                sc_cols[i].metric(field, score)
            st.divider()

        with st.expander("🔍 Xem dữ liệu đã lưu", expanded=False):
            fe = sd.get("field_eval", {})
            st.markdown(f"**Điểm TB:** {sd.get('avg_score','—')}/5 · **Browser:** {sd.get('device_browser','—')}")
            st.markdown(f"**CĐ:** {sd.get('form_approved',{}).get('chan_doan','—')} · **ICD:** {sd.get('form_approved',{}).get('icd','—')}")
            drugs = sd.get("form_approved",{}).get("don_thuoc",[])
            st.markdown(f"**Thuốc:** {', '.join(d.get('ten','') for d in drugs) or '—'} · **Duration:** {sd.get('audio_duration_sec','—')}s")

        c_dl1, c_dl2 = st.columns(2)
        with c_dl1:
            st.download_button(
                "⬇️ Tải dữ liệu phiên (JSON)",
                data=json.dumps(sd, ensure_ascii=False, indent=2),
                file_name=f"medivoice_session_{sd['session_id']}.json",
                mime="application/json",
                use_container_width=True,
            )
        with c_dl2:
            if "audio" in r:
                st.download_button(
                    "⬇️ Tải file âm thanh",
                    data=r["audio"],
                    file_name=f"medivoice_audio_{sd['session_id']}.wav",
                    mime="audio/wav",
                    use_container_width=True,
                )

        st.info("📩 Gửi JSON + âm thanh về: **vietshares.com@gmail.com** để cải thiện hệ thống")

        if st.button("🔄 Khám bệnh nhân tiếp theo"):
            for k, v in _DEFAULTS.items():
                st.session_state[k] = v
            if hasattr(st.session_state, "session_data"):
                del st.session_state.session_data
            st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.rerun()

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<center><small>MediVoice VN v2.0 · Demo · "
    "© 2026 Maple Leaf Group · vietshares.com@gmail.com</small></center>",
    unsafe_allow_html=True,
)
