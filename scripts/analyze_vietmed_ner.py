#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_vietmed_ner.py — MediVoice VN
Phân tích VietMed-NER dataset → map entity types → MediVoice L1c schema.
Xuất DRUGCHEMICAL entities để mở rộng drug_db.json.

Usage:
    python -X utf8 scripts/analyze_vietmed_ner.py               # Full analysis
    python -X utf8 scripts/analyze_vietmed_ner.py --drugs-only  # Chỉ xuất drug entities
    python -X utf8 scripts/analyze_vietmed_ner.py --apply       # Áp dụng vào drug_db.json
"""

import sys
import json
import argparse
import re
from pathlib import Path
from collections import Counter, defaultdict

# ── MediVoice entity mapping ────────────────────────────────────────────────
# VietMed-NER (18 types) → MediVoice L1c (5 types)
ENTITY_MAP = {
    # ⭐ Critical — map trực tiếp
    # NOTE: dataset dùng "DISEASESYMTOM" (typo — thiếu P) — đã verify thực tế
    "DISEASESYMTOM":    "SYMPTOM_DIAGNOSIS",   # 5,179 instances — lớn nhất
    "DRUGCHEMICAL":     "MEDICATION",           # 2,114 instances — media/lecture domain
    "TREATMENT":        "MEDICATION_FOLLOWUP",  # 1,150 instances
    "DATETIME":         "FOLLOWUP",             # 1,528 instances — tái khám ngày, thời gian
    # QUAN TRỌNG: UNITCALIBRATOR trong dataset = adjectives ("cao", "thấp", "nhiều")
    # KHÔNG phải vital sign measurements. Cần tự build vitals regex cho MediVoice.
    "UNITCALIBRATOR":   "VITAL_CONTEXT",       # 1,299 instances — adjectives, not numbers

    # ✅ Useful — bổ sung context
    "ORGAN":            "SYMPTOM_CONTEXT",      # 3,712 instances — họng, tim, não
    "DIAGNOSTICS":      "DIAGNOSIS",            # 763 instances — xét nghiệm, siêu âm
    "SURGERY":          "HISTORY",              # 532 instances — tiền sử phẫu thuật
    "PERSONALCARE":     "MEDICATION",           # 567 instances — OTC, tự mua
    "PREVENTIVEMED":    "FOLLOWUP",             # 441 instances — tiêm ngừa, phòng bệnh
    "FOODDRINK":        "FOLLOWUP_ADVICE",      # 574 instances — ăn kiêng, uống nhiều nước

    # 🟡 Low priority — ít dùng trong L1c
    "MEDDEVICETECHNIQUE": "EQUIPMENT",          # 1,029 instances — thiết bị y tế
    "AGE":              "PATIENT_INTAKE",       # 1,186 instances
    "GENDER":           "PATIENT_INTAKE",       # 819 instances
    "OCCUPATION":       "PATIENT_CONTEXT",      # 1,244 instances

    # — Không cần thiết cho MediVoice
    "LOCATION":         "SKIP",                 # 697 instances
    "ORGANIZATION":     "SKIP",                 # 82 instances
    "TRANSPORTATION":   "SKIP",                 # 35 instances — bỏ hoàn toàn khi train
}

PRIORITY = {
    "DISEASESYMTOM":    "P1 ⭐⭐",
    "DRUGCHEMICAL":     "P1 ⭐⭐",
    "TREATMENT":        "P1 ⭐⭐",
    "DATETIME":         "P1 ⭐⭐",
    "UNITCALIBRATOR":   "P1 ⭐⭐",
    "ORGAN":            "P2 ✅",
    "DIAGNOSTICS":      "P2 ✅",
    "SURGERY":          "P2 ✅",
    "PERSONALCARE":     "P2 ✅",
    "PREVENTIVEMED":    "P2 ✅",
    "FOODDRINK":        "P2 ✅",
    "MEDDEVICETECHNIQUE": "P3 🟡",
    "AGE":              "P3 🟡",
    "GENDER":           "P3 🟡",
    "OCCUPATION":       "P3 🟡",
    "LOCATION":         "SKIP",
    "ORGANIZATION":     "SKIP",
    "TRANSPORTATION":   "SKIP",
}


class C:
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    RED    = "\033[91m"
    RESET  = "\033[0m"


def cprint(color: str, msg: str):
    print(f"{color}{msg}{C.RESET}")


def load_dataset_safe(path: Path):
    """Load VietMed-NER từ disk hoặc HuggingFace Hub.
    Schema thực tế: words (List[str]), labels (List[str] BIO), tags (List[int]), audio, duration.
    Audio column yêu cầu torchcodec → remove trước khi iterate.
    """
    local_path = path / "VietMed-NER"

    if local_path.exists():
        cprint(C.CYAN, f"  Đọc từ disk: {local_path}")
        from datasets import load_from_disk  # type: ignore
        ds = load_from_disk(str(local_path))
    else:
        cprint(C.CYAN, "  Tải từ HuggingFace Hub (cần internet)...")
        from datasets import load_dataset  # type: ignore
        ds = load_dataset("leduckhai/VietMed-NER")
        ds.save_to_disk(str(local_path))
        cprint(C.GREEN, f"  Đã lưu: {local_path}")

    # Remove audio column để tránh cần torchcodec
    first_split = list(ds.keys())[0]
    if "audio" in ds[first_split].column_names:
        ds = ds.remove_columns("audio")
        cprint(C.YELLOW, "  Audio column removed (torchcodec not required)")
    return ds


def extract_entities_from_bio(tokens: list[str], labels: list[str]) -> dict[str, list[str]]:
    """Parse BIO tags → dict[entity_type → list of entity strings]."""
    entities: dict[str, list[str]] = defaultdict(list)
    current_type = None
    current_tokens: list[str] = []

    for token, label in zip(tokens, labels):
        if label.startswith("B-"):
            if current_type and current_tokens:
                entities[current_type].append(" ".join(current_tokens))
            current_type = label[2:]
            current_tokens = [token]
        elif label.startswith("I-") and current_type:
            current_tokens.append(token)
        else:  # O tag
            if current_type and current_tokens:
                entities[current_type].append(" ".join(current_tokens))
            current_type = None
            current_tokens = []

    if current_type and current_tokens:
        entities[current_type].append(" ".join(current_tokens))

    return entities


def analyze_full(ds, output_dir: Path):
    """Full entity distribution analysis + mapping report."""

    print()
    print(f"{C.BOLD}  VietMed-NER — Entity Analysis{C.RESET}")
    print(f"  Dataset: {sum(len(ds[split]) for split in ds)} samples "
          f"({', '.join(f'{s}: {len(ds[s])}' for s in ds)})")
    print()

    # Count entities across all splits
    entity_counts: Counter = Counter()
    entity_examples: dict[str, list[str]] = defaultdict(list)
    all_drugs: list[str] = []

    for split in ["train", "validation", "test"]:
        if split not in ds:
            continue
        for row in ds[split]:
            tokens = row.get("tokens", row.get("words", []))
            labels = row.get("ner_tags", row.get("labels", []))

            # Handle integer labels → string labels
            if labels and isinstance(labels[0], int):
                label_names = ds[split].features["ner_tags"].feature.names
                labels = [label_names[l] for l in labels]

            extracted = extract_entities_from_bio(tokens, labels)
            for etype, elist in extracted.items():
                entity_counts[etype] += len(elist)
                # Keep first 5 examples per type
                if len(entity_examples[etype]) < 5:
                    entity_examples[etype].extend(elist[:3])
                if etype == "DRUGCHEMICAL":
                    all_drugs.extend(elist)

    # Print mapping table
    print(f"  {'Entity Type':<22} {'Count':>6}  {'→ MediVoice':<22} {'Priority'}")
    print("  " + "─" * 80)
    total = sum(entity_counts.values())
    for etype in sorted(entity_counts, key=lambda x: -entity_counts[x]):
        count = entity_counts[etype]
        pct = count / total * 100
        medivoice = ENTITY_MAP.get(etype, "UNKNOWN")
        pri = PRIORITY.get(etype, "—")
        skip = " (skip)" if medivoice == "SKIP" else ""
        bar = "█" * min(20, int(pct))
        print(f"  {etype:<22} {count:>6}  → {medivoice:<22} {pri}{skip}")

    print(f"\n  Tổng entities: {total:,} | Types: {len(entity_counts)}")

    # Examples
    print(f"\n{C.CYAN}  VÍ DỤ ENTITIES (5 per type):{C.RESET}")
    for etype in ["DISEASESYMPTOM", "DRUGCHEMICAL", "TREATMENT", "DATETIME", "UNITCALIBRATOR"]:
        examples = list(set(entity_examples.get(etype, [])))[:5]
        if examples:
            print(f"  {etype}: {' | '.join(examples)}")

    # Drug analysis
    print(f"\n{C.BOLD}  DRUGCHEMICAL SUMMARY:{C.RESET}")
    drug_counter = Counter(d.lower().strip() for d in all_drugs if d.strip())
    print(f"  Tổng mentions: {len(all_drugs)} | Unique drugs: {len(drug_counter)}")
    print(f"  Top 20 drugs:")
    for drug, cnt in drug_counter.most_common(20):
        print(f"    {cnt:>4}×  {drug}")

    # Save outputs
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Entity mapping JSON
    mapping = {
        "generated": "2026-06-09",
        "source": "VietMed-NER (NAACL 2025, CC-BY-4.0)",
        "total_entities": total,
        "entity_counts": dict(entity_counts.most_common()),
        "medivoice_mapping": ENTITY_MAP,
        "priority": PRIORITY,
    }
    mapping_path = output_dir / "vietmed_ner_mapping.json"
    mapping_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  Saved mapping: {mapping_path}")

    # 2. Drug list for drug_db expansion
    drugs_path = output_dir / "vietmed_drugs_raw.json"
    drugs_path.write_text(
        json.dumps({"source": "VietMed-NER DRUGCHEMICAL entities",
                    "total_unique": len(drug_counter),
                    "drugs": dict(drug_counter.most_common())},
                   ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"  Saved drugs: {drugs_path}")

    return drug_counter


def normalize_drug_name(raw: str) -> str:
    """Chuẩn hóa tên thuốc từ corpus."""
    name = raw.strip()
    name = re.sub(r"\s+", " ", name)
    name = name.title()  # Capitalize each word
    # Remove stray punctuation
    name = re.sub(r"[^\w\s\-]", "", name)
    return name.strip()


def expand_drug_db(drug_counter: Counter, drug_db_path: Path, dry_run: bool = True):
    """Thêm drugs từ VietMed-NER vào drug_db.json."""

    db = json.loads(drug_db_path.read_text(encoding="utf-8"))
    # drug_db.json schema: {"_meta": ..., "by_inn": {INN: entry}, "keyword_index": {...}}
    by_inn = db.get("by_inn", {})
    existing_names = {k.lower() for k in by_inn}
    existing_aliases = {
        alias.lower()
        for entry in by_inn.values()
        for alias in entry.get("brands", []) + entry.get("aliases", [])
    }

    # Tìm drugs chưa có trong db (xuất hiện >= 3 lần — đủ confident)
    new_drugs = []
    for raw_drug, count in drug_counter.most_common():
        if count < 3:
            continue
        normalized = normalize_drug_name(raw_drug)
        if not normalized or len(normalized) < 3:
            continue
        key = normalized.lower()
        if key in existing_names or key in existing_aliases:
            continue

        new_drugs.append({
            "name": normalized,
            "aliases": [raw_drug] if raw_drug.lower() != key else [],
            "brands": [],
            "route": "uống",        # default — cần review thủ công
            "unit": "mg",           # default — cần review thủ công
            "source": "VietMed-NER",
            "count": count,
            "_needs_review": True,  # Flag để BS/Claude review trước dùng
        })

    print(f"\n{C.BOLD}  DRUG DB EXPANSION:{C.RESET}")
    print(f"  drug_db.json hiện tại: {len(by_inn)} entries")
    print(f"  VietMed-NER drugs (≥3 mentions): {sum(1 for _, c in drug_counter.items() if c >= 3)}")
    print(f"  Mới, chưa có trong db: {len(new_drugs)} drugs")

    if new_drugs:
        print(f"\n  Top 20 drugs cần thêm:")
        for d in new_drugs[:20]:
            print(f"    {d['count']:>4}×  {d['name']}")

    if dry_run:
        # Lưu vào file staging riêng, không modify drug_db.json
        staging_path = drug_db_path.parent / "drug_db_vietmed_additions.json"
        staging_data = {
            "source": "VietMed-NER DRUGCHEMICAL (auto-extracted)",
            "date": "2026-06-09",
            "warning": "Cần review thủ công trước khi merge vào drug_db.json",
            "merge_command": "python -X utf8 scripts/analyze_vietmed_ner.py --apply",
            "entries": new_drugs,
        }
        staging_path.write_text(json.dumps(staging_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n{C.YELLOW}  DRY RUN: Không thay đổi drug_db.json{C.RESET}")
        print(f"  Xem staging: {staging_path}")
        print(f"  Để áp dụng: python -X utf8 scripts/analyze_vietmed_ner.py --apply")
    else:
        # Merge vào drug_db.json (chỉ entries đã review / không có flag)
        confirmed = [d for d in new_drugs if not d.get("_needs_review")]
        if confirmed:
            db.extend(confirmed)
            drug_db_path.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"\n{C.GREEN}  Đã thêm {len(confirmed)} drugs vào drug_db.json{C.RESET}")
        else:
            print(f"\n{C.YELLOW}  Không có entries nào đã review sẵn sàng để merge.{C.RESET}")
            print(f"  Xem và sửa drug__db_vietmed_additions.json, xoá '_needs_review' trước khi --apply")


def main():
    parser = argparse.ArgumentParser(description="Phân tích VietMed-NER → MediVoice mapping")
    parser.add_argument("--drugs-only", action="store_true", help="Chỉ xuất drug entities")
    parser.add_argument("--apply",      action="store_true", help="Merge vào drug_db.json (sau review)")
    args = parser.parse_args()

    base = Path(__file__).resolve().parent.parent
    external_dir = base / "data" / "external"
    output_dir   = base / "data" / "reference" / "vietmed_analysis"
    drug_db_path = base / "data" / "reference" / "drug_db.json"

    try:
        import datasets as _  # noqa: F401
    except ImportError:
        print("❌ datasets chưa cài: pip install datasets")
        sys.exit(1)

    print(f"\n{C.BOLD}  analyze_vietmed_ner.py — MediVoice VN{C.RESET}")

    ds = load_dataset_safe(external_dir)

    if args.drugs_only:
        drug_counter = Counter()
        for split in ds:
            for row in ds[split]:
                tokens = row.get("tokens", row.get("words", []))
                labels = row.get("ner_tags", row.get("labels", []))
                if labels and isinstance(labels[0], int):
                    label_names = ds[split].features["ner_tags"].feature.names
                    labels = [label_names[l] for l in labels]
                extracted = extract_entities_from_bio(tokens, labels)
                drug_counter.update(d.lower().strip() for d in extracted.get("DRUGCHEMICAL", []))
        expand_drug_db(drug_counter, drug_db_path, dry_run=not args.apply)
    else:
        drug_counter = analyze_full(ds, output_dir)
        expand_drug_db(drug_counter, drug_db_path, dry_run=not args.apply)

    print()


if __name__ == "__main__":
    main()
