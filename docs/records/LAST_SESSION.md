# LAST_SESSION.md — MediVoice VN
# Ghi đè mỗi phiên — git history lưu lịch sử cũ tự động
# ISO/IEC 42001:2023 Cl.9.1 (Performance evaluation)

## Mã phiên: SES-20260608B
## Thời gian: 2026-06-08
## Version: v0.8.4 → v0.8.5

---

## Trạng thái đầu → cuối
v0.8.4 | 473 tests → v0.8.5 | 473 tests

## Đã hoàn thành

- [RAG-DEPLOY-001] LangChain RAG pipeline deploy lên Streamlit Cloud (commit `b1eb136`)
  - `demo/rag_chain.py`: L1b drug correction → LangChain NER (ChatGroq + JsonOutputParser + retry) → L1d ICD
  - `demo/requirements.txt`: thêm langchain-groq, langchain-core, rapidfuzz
  - `data/reference/drug_db_v200.json`: 11 drugs cập nhật ASR variants trong name_variants
  - Spinner: "🧠 MediVoice AI đang phân tích lâm sàng (RAG pipeline)..."

- [LOCAL-SETUP-001] Local dev setup hoàn chỉnh — chạy app tại localhost:8501
  - `demo/local_saves/` — local JSON fallback khi không có GCP
  - `.streamlit/secrets.toml` — template với groq_api_key (gitignored)
  - `.gitignore`: thêm `.streamlit/secrets.toml` + `demo/local_saves/`

- [SECRETS-FIX-001] Fix StreamlitSecretNotFoundError khi chạy local
  - `demo/app.py`: hàm `_secret(key, default="")` — wrap st.secrets.get() an toàn
  - `demo/app.py` line 756: `"gcp_service_account" not in st.secrets` → try/except `_has_gcp`
  - Thay tất cả 3 chỗ dùng `st.secrets.get(...)` bằng `_secret(...)`

- [L1B-FP-FIX-001] Fix L1b false positives — từ thường tiếng Việt không còn bị nhận nhầm là thuốc
  - Nguyên nhân: fuzzy cutoff 70% + token min_len=3 → "Vân","cám","mỗi","theo" match Valsartan/Amoxicillin/Meloxicam/Theophylline
  - Fix: minimum char length per n: `{1: 6, 2: 9, 3: 12}` trong Layer 2 fuzzy
  - Fix display: chỉ hiện drug_flags có confidence ≥ 0.85 hoặc DOSE_OUT_OF_RANGE
  - Kết quả: 0 false positives trên từ thường VN | Metformin/Glibenclamide vẫn Layer 1 exact ✅

## Kết quả đo được
- Tests: 473/473 PASS (không regression sau L1b fix)
- False positives giảm: 17 FP warnings → 0 khi test với đoạn văn thông thường tiếng Việt
- App chạy local: localhost:8501 với groq_api_key trong secrets.toml

## Blocker / Phụ thuộc bên ngoài
- [BENCH-002b] ⏳ Andy cần điền GT vào `data/eval/ref_voice_transcripts_review.txt` (Clip2+Clip3)
- [PA-007] Andy paste `docs/dev/CHATGPT_CORPUS_PROMPT.md` → ChatGPT → 41 corpus scripts
- [VBEE_TOKEN] Andy cần lấy VBEE_TOKEN + VBEE_APP_ID
- [VIETMED-FIX-001] HF_TOKEN cho `scripts/download_vietmed.py`

## Phiên tiếp theo — làm ngay theo thứ tự
1. [DEMO-TEST-001] Andy test lại app local — xác nhận 0 false positive drug warnings, Metformin+Glibenclamide nhận đúng
2. [BENCH-002b] Andy gửi GT fill xong → Claude chạy CEER thật (drug/vital/symptom per BS)
3. [PA-007] Andy paste ChatGPT corpus prompt → 41 clinical scripts → update CLINICAL_TEST_CORPUS_VN.md
4. [DRUG-DB-002] Mở rộng drug_db.json 118 → ~150 thuốc (Augmentin, Bisoprolol, Celecoxib...)
5. [L1B-TUNE-001] Cân nhắc tăng DRUG_FUZZY_CUTOFF_FLAG 70→78 sau khi có real pilot data
