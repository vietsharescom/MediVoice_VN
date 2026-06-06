#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
download_datasets.py — MediVoice VN
Tải datasets công khai từ HuggingFace + GitHub phục vụ fine-tune ASR/NER.

Usage:
    python -X utf8 scripts/download_datasets.py            # P1 only (mặc định)
    python -X utf8 scripts/download_datasets.py --p2       # P1 + P2 (lớn hơn)
    python -X utf8 scripts/download_datasets.py --list     # Liệt kê datasets, không tải
    python -X utf8 scripts/download_datasets.py --id VietMed-NER  # Tải 1 dataset cụ thể

Datasets được lưu tại: data/external/<dataset_id>/
"""

import sys
import os
import json
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# ── Cấu hình datasets ──────────────────────────────────────────────────────────

DATASETS = [
    # ── P1 — Download ngay, license OK cho commercial pilot ──
    {
        "id": "VietMed",
        "priority": "P1",
        "hf_id": "leduckhai/VietMed",
        "type": "huggingface",
        "license": "CC-BY-4.0",
        "size_gb": 2.5,         # labeled 16h portion trên HF
        "language": "VI",
        "use_case": ["asr"],
        "description": "16h audio y tế có label + 1,000h unlabeled. Đủ accent Bắc/Nam/Trung. "
                        "Bao phủ toàn bộ nhóm ICD-10. Tốt nhất để fine-tune PhoWhisper.",
        "pipeline_layer": "L1a (PhoWhisper)",
        "note": "Full 2,216h (incl. unlabeled) có trên Google Drive trong GitHub README.",
    },
    {
        "id": "VietMed-NER",
        "priority": "P1",
        "hf_id": "leduckhai/VietMed-NER",
        "type": "huggingface",
        "license": "CC-BY-4.0",
        "size_gb": 0.05,
        "language": "VI",
        "use_case": ["ner"],
        "description": "9,270 samples spoken medical NER (NAACL 2025). 18 entity types: DRUGCHEMICAL, "
                        "DISEASESYMPTOM(4,716), TREATMENT, DATETIME, UNITCALIBRATOR... "
                        "Map thẳng vào MEDICATION/SYMPTOM/VITAL của L1c.",
        "pipeline_layer": "L1c (PhoBERT+CRF NER)",
        "note": "Dataset quan trọng nhất cho NER. BIO tagging Parquet. Tải trước.",
    },
    {
        "id": "ViMedCSS",
        "priority": "P1",
        "hf_id": "tensorxt/ViMedCSS",
        "type": "huggingface",
        "license": "CC-BY-4.0",
        "size_gb": 4.0,         # ~34h audio
        "language": "VI+EN",
        "use_case": ["asr"],
        "description": "34h, 16,576 utterances. Code-switching VI+EN — BS nói 'Amoxicillin 500mg' "
                        "trong câu Việt. Benchmark PhoWhisper trực tiếp với English drug terms.",
        "pipeline_layer": "L1a + L1b (drug correction)",
        "note": "Quan trọng cho drug name ASR. Covers hardest failure mode của PhoWhisper.",
    },
    {
        "id": "VietMed-Sum",
        "priority": "P1",
        "hf_id": "leduckhai/VietMed-Sum",
        "type": "huggingface",
        "license": "MIT",
        "size_gb": 0.05,
        "language": "VI+EN",
        "use_case": ["ner", "summarization"],
        "description": "106K rows. Doctor-patient conversation → structured summary. "
                        "Tim mạch, hô hấp, da liễu, thần kinh, tiêu hóa. "
                        "Trực tiếp phản ánh task transcription-to-form của MediVoice.",
        "pipeline_layer": "L1c + L6 (NER → Mẫu 15)",
        "note": "Mine entity vocabulary từ summaries để mở rộng NER training data.",
    },
    {
        "id": "Vietnamese-Medical-QA",
        "priority": "P1",
        "hf_id": "hungnm/vietnamese-medical-qa",
        "type": "huggingface",
        "license": "Apache-2.0",
        "size_gb": 0.01,
        "language": "VI",
        "use_case": ["ner", "vocabulary"],
        "description": "9,335 QA pairs từ edoctor.vn + vinmec.com. Đa chuyên khoa: "
                        "nha, TMH, da liễu, tim mạch, thần kinh, tiêu hóa, nội tiết...",
        "pipeline_layer": "L1c (drug/disease vocabulary)",
        "note": "Mine clinical vocabulary. Apache 2.0 — commercial OK.",
    },

    # ── P2 — Download sau P1, verify license trước production ──
    {
        "id": "VLSP2020-VinAI",
        "priority": "P2",
        "hf_id": "doof-ferb/vlsp2020_vinai_100h",
        "type": "huggingface",
        "license": "CC-BY-4.0",
        "size_gb": 11.6,
        "language": "VI",
        "use_case": ["asr"],
        "description": "100h, 56K samples. 80h spontaneous speech — gần nhất với giọng "
                        "khám bệnh tự nhiên. CC-BY-4.0.",
        "pipeline_layer": "L1a (base ASR trước medical domain adapt)",
        "note": "Spontaneous speech component quan trọng cho conversation ASR.",
    },
    {
        "id": "BUD500",
        "priority": "P2",
        "hf_id": "linhtran92/viet_bud500",
        "type": "huggingface",
        "license": "Apache-2.0",
        "size_gb": 100.0,       # full download ~100GB
        "language": "VI",
        "use_case": ["asr"],
        "description": "500h podcast/general VI. Bắc/Nam/Trung accent. "
                        "Dùng streaming mode — KHÔNG full download.",
        "pipeline_layer": "L1a (Vietnamese acoustic base)",
        "note": "CẢNH BÁO: Full download ~100GB. Dùng --streaming. Verify NC clause trước production.",
        "streaming_only": True,
    },
    {
        "id": "ViMQ",
        "priority": "P2",
        "type": "github",
        "git_url": "https://github.com/tadeephuy/ViMQ.git",
        "license": "Check README",
        "size_gb": 0.02,
        "language": "VI",
        "use_case": ["ner"],
        "description": "9,000 patient questions từ Vinmec. MEDICINE entity type "
                        "— thêm vào NER training cho drug names.",
        "pipeline_layer": "L1c (MEDICATION entity)",
        "note": "Verify commercial use với tác giả trước production.",
    },
]

# ── Màu terminal ───────────────────────────────────────────────────────────────

class C:
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"


def cprint(color: str, msg: str):
    print(f"{color}{msg}{C.RESET}")


# ── Helpers ────────────────────────────────────────────────────────────────────

def check_dependencies() -> bool:
    """Kiểm tra datasets + git đã cài chưa."""
    ok = True
    try:
        import datasets  # noqa: F401
        cprint(C.GREEN, "  ✅ datasets (HuggingFace) — OK")
    except ImportError:
        cprint(C.RED, "  ❌ datasets chưa cài: pip install datasets")
        ok = False

    git = shutil.which("git")
    if git:
        cprint(C.GREEN, "  ✅ git — OK")
    else:
        cprint(C.RED, "  ❌ git không tìm thấy")
        ok = False
    return ok


def get_output_dir(base: Path, ds: dict) -> Path:
    return base / ds["id"]


def download_hf(ds: dict, out_dir: Path, streaming_only: bool = False) -> bool:
    """Tải dataset từ HuggingFace Datasets Hub."""
    from datasets import load_dataset  # type: ignore

    if ds.get("streaming_only") and not streaming_only:
        cprint(C.YELLOW, f"  ⚠️  {ds['id']} quá lớn ({ds['size_gb']:.0f} GB) — bỏ qua (dùng --p2 --streaming)")
        return False

    out_dir.mkdir(parents=True, exist_ok=True)
    cprint(C.BLUE, f"  → load_dataset(\"{ds['hf_id']}\")")

    try:
        if ds.get("streaming_only"):
            # Chỉ tải metadata
            dataset = load_dataset(ds["hf_id"], streaming=True)
            cprint(C.YELLOW, f"  ℹ️  Streaming mode — chỉ tải metadata, không lưu file.")
            meta = {"hf_id": ds["hf_id"], "streaming": True, "downloaded": str(datetime.now())}
            (out_dir / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
            return True
        else:
            dataset = load_dataset(ds["hf_id"])
            dataset.save_to_disk(str(out_dir))
            cprint(C.GREEN, f"  ✅ Lưu tại: {out_dir}")
            return True
    except Exception as e:
        cprint(C.RED, f"  ❌ Lỗi: {e}")
        return False


def download_github(ds: dict, out_dir: Path) -> bool:
    """Clone repo GitHub."""
    if out_dir.exists():
        cprint(C.YELLOW, f"  ⚠️  {out_dir} đã tồn tại — bỏ qua (dùng git pull để update).")
        return True

    cprint(C.BLUE, f"  → git clone {ds['git_url']}")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", ds["git_url"], str(out_dir)],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        cprint(C.GREEN, f"  ✅ Clone tại: {out_dir}")
        return True
    else:
        cprint(C.RED, f"  ❌ Lỗi: {result.stderr.strip()}")
        return False


def write_readme(out_dir: Path, ds: dict):
    """Ghi README.md cho từng dataset với thông tin license + usage."""
    lines = [
        f"# {ds['id']}",
        f"",
        f"**HuggingFace:** `{ds.get('hf_id', ds.get('git_url', ''))}`",
        f"**License:** {ds['license']}",
        f"**Size:** ~{ds['size_gb']} GB",
        f"**Language:** {ds['language']}",
        f"**Use case:** {', '.join(ds['use_case'])}",
        f"**Pipeline layer:** {ds['pipeline_layer']}",
        f"",
        f"## Mô tả",
        f"{ds['description']}",
        f"",
        f"## Lưu ý",
        f"{ds['note']}",
        f"",
        f"## Tải lại",
        f"```python",
        f"from datasets import load_dataset",
        f"ds = load_dataset(\"{ds.get('hf_id', '')}\")  # hoặc load_from_disk(\"{out_dir}\")",
        f"```",
        f"",
        f"*Downloaded: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
    ]
    (out_dir / "README_MEDIVOICE.md").write_text("\n".join(lines), encoding="utf-8")


def list_datasets(datasets_list: list[dict]):
    """In bảng tóm tắt tất cả datasets."""
    print()
    cprint(C.BOLD, "  DATASETS CHO MEDIVOICE VN")
    print(f"  {'ID':<25} {'Priority':<6} {'Size':>8} {'License':<16} {'Use case':<20} {'Layer'}")
    print("  " + "-" * 100)
    for ds in datasets_list:
        size = f"{ds['size_gb']:.1f} GB"
        use  = "+".join(ds["use_case"])
        note = " [STREAM]" if ds.get("streaming_only") else ""
        print(f"  {ds['id']:<25} {ds['priority']:<6} {size:>8}  {ds['license']:<16} {use:<20} {ds['pipeline_layer']}{note}")
    print()


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Download datasets cho MediVoice VN")
    parser.add_argument("--list",      action="store_true", help="Liệt kê datasets, không tải")
    parser.add_argument("--p2",        action="store_true", help="Tải thêm P2 datasets (lớn hơn)")
    parser.add_argument("--streaming", action="store_true", help="BUD500 dùng streaming (không lưu file)")
    parser.add_argument("--id",        type=str,            help="Chỉ tải dataset có ID này")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent.parent / "data" / "external"

    if args.list:
        list_datasets(DATASETS)
        total_p1 = sum(d["size_gb"] for d in DATASETS if d["priority"] == "P1")
        total_p2 = sum(d["size_gb"] for d in DATASETS if d["priority"] == "P2" and not d.get("streaming_only"))
        print(f"  Tổng P1: ~{total_p1:.1f} GB  |  P2 (không BUD500): ~{total_p2:.1f} GB  |  BUD500: ~100 GB (streaming)")
        return

    # Lọc danh sách sẽ tải
    to_download = [d for d in DATASETS if d["priority"] == "P1"]
    if args.p2:
        to_download += [d for d in DATASETS if d["priority"] == "P2"]
    if args.id:
        to_download = [d for d in DATASETS if d["id"] == args.id]
        if not to_download:
            cprint(C.RED, f"Không tìm thấy dataset: {args.id}")
            sys.exit(1)

    total_gb = sum(d["size_gb"] for d in to_download if not d.get("streaming_only"))
    print()
    cprint(C.BOLD, "  MediVoice VN — Dataset Downloader")
    print(f"  Sẽ tải: {len(to_download)} datasets  |  ~{total_gb:.1f} GB")
    print(f"  Lưu tại: {base_dir}")
    print()

    print("  Kiểm tra dependencies...")
    if not check_dependencies():
        cprint(C.RED, "\n  ❌ Cài đặt thiếu — chạy: pip install datasets gitpython")
        sys.exit(1)
    print()

    results = []

    for ds in to_download:
        cprint(C.CYAN, f"\n  [{ds['priority']}] {ds['id']} ({ds['license']}) — {ds['size_gb']} GB")
        print(f"  {ds['description'][:80]}...")

        out_dir = get_output_dir(base_dir, ds)

        if ds["type"] == "huggingface":
            ok = download_hf(ds, out_dir, streaming_only=args.streaming)
        elif ds["type"] == "github":
            ok = download_github(ds, out_dir)
        else:
            cprint(C.RED, f"  ❌ Loại không hỗ trợ: {ds['type']}")
            ok = False

        if ok and out_dir.exists():
            write_readme(out_dir, ds)

        results.append((ds["id"], ok))

    # Tóm tắt
    print()
    cprint(C.BOLD, "  ── KẾT QUẢ ──")
    ok_count = sum(1 for _, ok in results if ok)
    for name, ok in results:
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}")

    print()
    cprint(C.GREEN if ok_count == len(results) else C.YELLOW,
           f"  {ok_count}/{len(results)} datasets OK  |  {base_dir}")

    if ok_count == len(results):
        print()
        cprint(C.BOLD, "  BƯỚC TIẾP THEO:")
        print("  1. VietMed-NER → fine-tune PhoBERT+CRF:")
        print("     from datasets import load_from_disk")
        print(f"     ds = load_from_disk(\"data/external/VietMed-NER\")")
        print()
        print("  2. VietMed → fine-tune PhoWhisper:")
        print(f"     ds = load_from_disk(\"data/external/VietMed\")")
        print()
        print("  3. Benchmark sau khi fine-tune:")
        print("     python -X utf8 tools/bench_ceer.py --full --gt data/audio/corpus/semi_synthetic/groundtruth_all.json")


if __name__ == "__main__":
    main()
