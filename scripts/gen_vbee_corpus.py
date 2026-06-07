#!/usr/bin/env python
# scripts/gen_vbee_corpus.py
# CONS-002-SPRINT6 — Vbee TTS API corpus generation
# Generates WAV 16kHz mono từ text scripts → fine-tune PhoWhisper
#
# Setup:
#   Đăng ký tại vbee.vn → lấy App-Id + Bearer token
#   Set env vars:
#     set VBEE_TOKEN=your_bearer_token
#     set VBEE_APP_ID=your_app_id
#
# Usage:
#   python -X utf8 scripts/gen_vbee_corpus.py --test        # 5 clips test
#   python -X utf8 scripts/gen_vbee_corpus.py --region HN   # chỉ HN
#   python -X utf8 scripts/gen_vbee_corpus.py --full        # tất cả 1100 clips
#
# API docs: https://api-docs.vbee.vn/

import argparse
import json
import os
import sys
import time
import unicodedata
from pathlib import Path

import requests
import soundfile as sf

sys.path.insert(0, str(Path(__file__).parent.parent))

# ─── CONFIG ──────────────────────────────────────────────────────────────────

VBEE_URL    = "https://api.vbee.vn/v1/tts"
VBEE_TOKEN  = os.getenv("VBEE_TOKEN", "")
VBEE_APP_ID = os.getenv("VBEE_APP_ID", "")

# Voices theo region — male (BS phần lớn nam) + female backup
VOICES = {
    "HN": {
        "male":   "hn_male_manhdung_news_48k-fhg",
        "female": "hn_female_ngochuyen_full_48k-fhg",
    },
    "SG": {
        "male":   "sg_male_minhhoang_full_48k-fhg",
        "female": "sg_female_thaotrinh_full_48k-fhg",
    },
    "DN": {  # Đà Nẵng → dùng Huế (Central accent gần nhất có sẵn)
        "male":   "hue_male_duyphuong_full_48k-fhg",
        "female": "hue_female_huonggiang_full_48k-fhg",
    },
    "CT": {  # Cần Thơ → dùng SG female (giọng chậm nhất)
        "male":   "sg_male_trungkien_vdts_48k-fhg",
        "female": "sg_female_thaotrinh_full_48k-fhg",
    },
}

OUT_DIR   = Path("data/synthetic_audio")
LOG_FILE  = OUT_DIR / "generation_log.jsonl"

# Sample rate 16kHz mono — khớp L0 pipeline PhoWhisper
SAMPLE_RATE = 16000
OUTPUT_FMT  = "wav"
MAX_SYNC    = 280  # chars — sync mode limit 300, buffer 20

# ─── CORPUS SCRIPTS (inline sample — expand từ CHATGPT_CORPUS_PROMPT.md) ────

CORPUS: list[dict] = [
    # Format: {id, region, disease, icd10, style, text, ground_truth}

    # ── VIÊM HỌNG J02.9 ──────────────────────────────────────────────────────
    {"id": "j029_HN_normal_001", "region": "HN", "disease": "viem_hong_cap",
     "icd10": "J02.9", "style": "normal",
     "text": "Bệnh nhân nam bốn mươi hai tuổi, đau họng ba ngày nay, sốt nhẹ. "
             "Huyết áp một trăm hai mươi trên tám mươi, mạch tám mươi, nhiệt độ ba mươi bảy phẩy tám. "
             "Chẩn đoán viêm họng cấp. "
             "Kê Amoxicillin năm trăm miligam, uống ba lần một ngày trong năm ngày. "
             "Paracetamol năm trăm miligam khi sốt. Tái khám sau năm ngày.",
     "gt": {"chan_doan": "Viêm họng cấp", "icd10": "J02.9",
            "drugs": ["Amoxicillin 500mg 3l/ng 5ng", "Paracetamol 500mg khi sốt"],
            "tai_kham": "5 ngày"}},

    {"id": "j029_SG_concise_001", "region": "SG", "disease": "viem_hong_cap",
     "icd10": "J02.9", "style": "concise",
     "text": "Viêm họng cấp. Huyết áp một hai mươi tám mươi. Sốt ba bảy phẩy tám. "
             "Amoxi năm trăm ba lần năm ngày. Para năm trăm khi sốt. Tái khám năm ngày nha.",
     "gt": {"chan_doan": "Viêm họng cấp", "icd10": "J02.9",
            "drugs": ["Amoxicillin 500mg 3l/ng 5ng", "Paracetamol 500mg khi sốt"],
            "tai_kham": "5 ngày"}},

    {"id": "j029_DN_normal_001", "region": "DN", "disease": "viem_hong_cap",
     "icd10": "J02.9", "style": "normal",
     "text": "Bệnh nhân nữ ba mươi lăm tuổi, đau họng hai ngày nay, nuốt khó. "
             "Huyết áp một trăm mười trên bảy mươi, nhiệt độ ba mươi tám độ. "
             "Chẩn đoán viêm họng cấp. "
             "Kê Azithromycin hai trăm năm mươi miligam, uống một lần một ngày trong ba ngày. "
             "Tái khám sau ba ngày nếu không đỡ.",
     "gt": {"chan_doan": "Viêm họng cấp", "icd10": "J02.9",
            "drugs": ["Azithromycin 250mg 1l/ng 3ng"],
            "tai_kham": "3 ngày"}},

    # ── TĂNG HUYẾT ÁP I10 ────────────────────────────────────────────────────
    {"id": "i10_HN_normal_001", "region": "HN", "disease": "tang_huyet_ap",
     "icd10": "I10", "style": "normal",
     "text": "Bệnh nhân nam sáu mươi tuổi, tái khám tăng huyết áp. "
             "Huyết áp lần một một trăm bảy mươi trên một trăm, lần hai một trăm sáu mươi lăm trên chín mươi lăm. "
             "Đang dùng Amlodipine năm miligam một viên mỗi ngày. "
             "Điều chỉnh: tăng Amlodipine lên mười miligam mỗi ngày. "
             "Thêm Losartan năm mươi miligam uống sáng. Tái khám sau hai tuần.",
     "gt": {"chan_doan": "Tăng huyết áp", "icd10": "I10",
            "drugs": ["Amlodipine 10mg 1l/ng", "Losartan 50mg 1l/ng"],
            "tai_kham": "2 tuần"}},

    {"id": "i10_SG_fast_001", "region": "SG", "disease": "tang_huyet_ap",
     "icd10": "I10", "style": "fast_dictation",
     "text": "Tái khám huyết áp. Đo một bảy mươi một trăm, lần hai một sáu lăm chín lăm. "
             "Đang dùng Amlodipine năm. Chưa kiểm soát. "
             "Tăng lên mười. Thêm Losartan năm mươi uống sáng. Tái khám hai tuần nha.",
     "gt": {"chan_doan": "Tăng huyết áp", "icd10": "I10",
            "drugs": ["Amlodipine 10mg 1l/ng", "Losartan 50mg 1l/ng"],
            "tai_kham": "2 tuần"}},

    # ── ĐÁI THÁO ĐƯỜNG E11.9 ─────────────────────────────────────────────────
    {"id": "e119_HN_normal_001", "region": "HN", "disease": "dtd_type2",
     "icd10": "E11.9", "style": "normal",
     "text": "Bệnh nhân nữ năm mươi lăm tuổi, đái tháo đường type hai tám năm. "
             "Đường huyết đói chín phẩy ba, HbA1c tám phẩy hai phần trăm. "
             "Huyết áp một trăm ba mươi trên tám mươi lăm, cân nặng bảy mươi tám ki lô. "
             "Chẩn đoán đái tháo đường type hai chưa kiểm soát tốt. "
             "Giữ Metformin năm trăm miligam hai lần sau ăn. "
             "Thêm Glimepiride hai miligam một lần trước ăn sáng. "
             "Vitamin B1 B6 B12 một viên mỗi ngày. Tái khám sau một tháng.",
     "gt": {"chan_doan": "Đái tháo đường type 2", "icd10": "E11.9",
            "drugs": ["Metformin 500mg 2l/ng", "Glimepiride 2mg 1l/ng", "VitaminB 1l/ng"],
            "tai_kham": "1 tháng"}},

    # ── GOUT M10.9 ───────────────────────────────────────────────────────────
    {"id": "m109_SG_normal_001", "region": "SG", "disease": "gout_cap",
     "icd10": "M10.9", "style": "normal",
     "text": "Bệnh nhân nam bảy mươi tuổi, đau ngón chân cái phải đột ngột từ đêm qua, sưng đỏ nóng. "
             "Uống bia hôm qua khoảng mười lon. Axit uric tám phẩy ba. "
             "Chẩn đoán gout cấp ngón chân cái phải. "
             "Colchicine không phẩy năm miligam, uống hai viên ngay, sau đó một viên mỗi giờ tối đa sáu viên. "
             "Etoricoxib sáu mươi miligam một lần sau ăn trong năm ngày. "
             "Không uống bia rượu. Tái khám sau một tuần.",
     "gt": {"chan_doan": "Gout cấp", "icd10": "M10.9",
            "drugs": ["Colchicine 0.5mg", "Etoricoxib 60mg 1l/ng 5ng"],
            "tai_kham": "1 tuần"}},

    # ── LOÉT DẠ DÀY K25.9 ───────────────────────────────────────────────────
    {"id": "k259_CT_normal_001", "region": "CT", "disease": "loet_da_day",
     "icd10": "K25.9", "style": "normal",
     "text": "Bệnh nhân nữ ba mươi lăm tuổi, đau bụng trên hai tuần nay, đau khi đói, ăn vào thì đỡ. "
             "Có ợ chua, đầy bụng. Tiền sử uống Ibuprofen nhiều lần tháng trước. "
             "Huyết áp một trăm mười trên bảy mươi, mạch bảy mươi lăm. "
             "Chẩn đoán viêm loét dạ dày tá tràng. "
             "Omeprazole hai mươi miligam một lần trước ăn sáng ba mươi phút trong bốn tuần. "
             "Domperidone mười miligam ba lần trước ăn. Ngưng Ibuprofen hoàn toàn. "
             "Tái khám sau bốn tuần.",
     "gt": {"chan_doan": "Viêm loét dạ dày tá tràng", "icd10": "K25.9",
            "drugs": ["Omeprazole 20mg 1l/ng", "Domperidone 10mg 3l/ng"],
            "tai_kham": "4 tuần"}},
]


# ─── VBEE API ─────────────────────────────────────────────────────────────────

def vbee_tts(text: str, voice_code: str, out_path: Path,
             speed: float = 1.0, retries: int = 3) -> bool:
    if not VBEE_TOKEN or not VBEE_APP_ID:
        print("  [ERROR] VBEE_TOKEN hoặc VBEE_APP_ID chưa set.")
        print("  → set VBEE_TOKEN=... && set VBEE_APP_ID=...")
        return False

    headers = {
        "Authorization": f"Bearer {VBEE_TOKEN}",
        "App-Id": VBEE_APP_ID,
        "Content-Type": "application/json",
    }

    # Sync mode cho text ngắn (≤280 chars), async cho dài hơn
    mode = "sync" if len(text) <= MAX_SYNC else "async"
    payload = {
        "text": text,
        "voiceCode": voice_code,
        "mode": mode,
        "outputFormat": OUTPUT_FMT,
        "sampleRate": SAMPLE_RATE,
        "speed": speed,
    }

    for attempt in range(retries):
        try:
            resp = requests.post(VBEE_URL, json=payload, headers=headers, timeout=30)
            if resp.status_code == 200:
                if mode == "sync":
                    out_path.write_bytes(resp.content)
                    return True
                else:
                    # Async: poll for result
                    data = resp.json()
                    req_id = data.get("requestId")
                    return _poll_async(req_id, out_path, headers)
            else:
                print(f"  [HTTP {resp.status_code}] {resp.text[:200]}")
        except requests.RequestException as e:
            print(f"  [Attempt {attempt+1}] Error: {e}")
        time.sleep(2 ** attempt)

    return False


def _poll_async(req_id: str, out_path: Path, headers: dict,
                max_wait: int = 120) -> bool:
    url = f"https://api.vbee.vn/v1/tts/requests/{req_id}"
    for _ in range(max_wait // 3):
        time.sleep(3)
        try:
            r = requests.get(url, headers=headers, timeout=10)
            data = r.json()
            status = data.get("status")
            if status == "done":
                audio_url = data.get("audioUrl")
                if audio_url:
                    audio_resp = requests.get(audio_url, timeout=30)
                    out_path.write_bytes(audio_resp.content)
                    return True
            elif status == "error":
                print(f"  [ASYNC ERROR] {data}")
                return False
        except Exception as e:
            print(f"  [POLL] {e}")
    print(f"  [TIMEOUT] requestId={req_id}")
    return False


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Vbee TTS corpus generator")
    parser.add_argument("--test",   action="store_true", help="5 clips test mode")
    parser.add_argument("--region", choices=["HN","SG","DN","CT"], help="Chỉ 1 region")
    parser.add_argument("--full",   action="store_true", help="Full 1,100 clips")
    parser.add_argument("--gender", choices=["male","female"], default="male")
    parser.add_argument("--speed",  type=float, default=1.0)
    args = parser.parse_args()

    if not VBEE_TOKEN:
        print("[ERROR] Chưa set VBEE_TOKEN và VBEE_APP_ID")
        print("  1. Đăng ký tại vbee.vn → Dashboard → API Keys")
        print("  2. set VBEE_TOKEN=your_token")
        print("  3. set VBEE_APP_ID=your_app_id")
        sys.exit(1)

    corpus = CORPUS
    if args.region:
        corpus = [c for c in corpus if c["region"] == args.region]
    if args.test:
        corpus = corpus[:5]

    print("=" * 60)
    print("  Vbee TTS Corpus Generator | MediVoice VN")
    print(f"  Clips: {len(corpus)} | Gender: {args.gender} | Speed: {args.speed}")
    print(f"  Output: {OUT_DIR}")
    print("=" * 60)

    ok = fail = 0
    total_chars = 0
    log_entries = []

    for item in corpus:
        region  = item["region"]
        voice   = VOICES.get(region, VOICES["HN"])[args.gender]
        split   = "train"  # TODO: stratify train/val/test
        out_dir = OUT_DIR / split
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{item['id']}.wav"

        if out_path.exists():
            print(f"  [SKIP] {out_path.name} (đã có)")
            continue

        text = item["text"]
        total_chars += len(text)
        print(f"  [{region}] {item['id']} ({len(text)} chars, voice={voice})")

        t0 = time.time()
        success = vbee_tts(text, voice, out_path, speed=args.speed)
        elapsed = time.time() - t0

        if success and out_path.exists():
            info = sf.info(str(out_path))
            dur  = info.frames / info.samplerate
            print(f"    → {dur:.1f}s audio | {elapsed:.1f}s elapsed | {info.samplerate}Hz {info.channels}ch")
            ok += 1
            log_entries.append({**item, "duration": dur, "voice": voice,
                                 "elapsed": elapsed, "ok": True})
        else:
            print(f"    → FAILED")
            fail += 1
            log_entries.append({**item, "ok": False})

    # Log
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        for e in log_entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    # Summary
    print("=" * 60)
    print(f"  Generated: {ok}/{ok+fail} ✅  Failed: {fail}")
    print(f"  Total chars: {total_chars:,}")
    cost_est = total_chars / 1_000_000 * 750_000  # ~750k VND/triệu ký tự
    print(f"  Cost est: ~{cost_est:,.0f} VND ({total_chars/1_000_000:.3f}M ký tự × 750k VND)")
    print(f"  Log: {LOG_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
