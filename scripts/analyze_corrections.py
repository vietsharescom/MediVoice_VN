"""
analyze_corrections.py — L4 Correction Capture Analyzer
FID-VN-006 | TIER 2 Adaptive Learning

Reads data/corrections/{clinic_id}/corrections.jsonl
Outputs frequency table + alias suggestions for drug names.

Usage:
  python scripts/analyze_corrections.py
  python scripts/analyze_corrections.py --clinic DA_NANG_01
  python scripts/analyze_corrections.py --field don_thuoc --min-count 2
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


_CORRECTIONS_ROOT = Path(__file__).parent.parent / "data" / "corrections"


def load_entries(clinic_id: str | None = None) -> list[dict]:
    entries: list[dict] = []

    if clinic_id:
        dirs = [_CORRECTIONS_ROOT / clinic_id] if (_CORRECTIONS_ROOT / clinic_id).exists() else []
    else:
        dirs = [d for d in _CORRECTIONS_ROOT.iterdir() if d.is_dir()] if _CORRECTIONS_ROOT.exists() else []

    for d in dirs:
        log_file = d / "corrections.jsonl"
        if not log_file.exists():
            continue
        with log_file.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return entries


def analyze_field(entries: list[dict], field: str, min_count: int) -> None:
    corrections = [
        c for e in entries
        for c in e.get("corrections", [])
        if c["field"] == field
    ]

    if not corrections:
        print(f"  No corrections found for field '{field}'")
        return

    print(f"\n  [{field}] — {len(corrections)} corrections total")

    if field == "don_thuoc":
        _analyze_drug_corrections(corrections, min_count)
    else:
        _analyze_generic_corrections(corrections, min_count)


def _analyze_drug_corrections(corrections: list[dict], min_count: int) -> None:
    # Collect (ai_drugs, bs_drugs) pairs
    added_drugs: Counter = Counter()
    transcript_snippets: defaultdict[str, list[str]] = defaultdict(list)

    for c in corrections:
        ai_val = c.get("ai_value") or []
        bs_val = c.get("bs_value") or []
        transcript = c.get("transcript_snippet", "")

        ai_names = {d.get("name", "").lower() for d in (ai_val if isinstance(ai_val, list) else [])}
        bs_names = {d.get("name", "") for d in (bs_val if isinstance(bs_val, list) else [])}

        for drug in bs_names:
            if drug.lower() not in ai_names:
                added_drugs[drug] += 1
                if transcript:
                    transcript_snippets[drug].append(transcript[:200])

    print(f"  Drugs added by BS (AI missed):")
    for drug, count in added_drugs.most_common():
        if count >= min_count:
            print(f"    {drug}: {count}x missed")
            snippets = transcript_snippets[drug][:2]
            for s in snippets:
                print(f"      transcript: ...{s}...")
            print(f"    → SUGGESTION: add phonetic aliases for '{drug}' to drug_db.json")


def _analyze_generic_corrections(corrections: list[dict], min_count: int) -> None:
    pairs: Counter = Counter()
    for c in corrections:
        ai_val = str(c.get("ai_value", ""))[:80]
        bs_val = str(c.get("bs_value", ""))[:80]
        pairs[(ai_val, bs_val)] += 1

    print(f"  Top correction patterns (AI → BS):")
    for (ai_val, bs_val), count in pairs.most_common(10):
        if count >= min_count:
            print(f"    [{count}x] '{ai_val}' → '{bs_val}'")


def summary(entries: list[dict]) -> None:
    total = len(entries)
    with_corrections = sum(1 for e in entries if e.get("correction_count", 0) > 0)
    total_corr = sum(e.get("correction_count", 0) for e in entries)
    accuracy_rate = (total - with_corrections) / total * 100 if total else 0

    print(f"\n{'='*60}")
    print(f"  L4 Correction Analysis — MediVoice VN")
    print(f"{'='*60}")
    print(f"  Total sessions logged:  {total}")
    print(f"  Sessions with edits:    {with_corrections}")
    print(f"  AI accuracy rate:       {accuracy_rate:.1f}% (no BS edits needed)")
    print(f"  Total field corrections:{total_corr}")

    if total > 0:
        field_counts: Counter = Counter()
        for e in entries:
            for c in e.get("corrections", []):
                field_counts[c["field"]] += 1

        if field_counts:
            print(f"\n  Most corrected fields:")
            for field, count in field_counts.most_common(5):
                print(f"    {field}: {count}x")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze L4 BS corrections")
    parser.add_argument("--clinic", default=None, help="Clinic ID (default: all)")
    parser.add_argument("--field", default=None, help="Focus on specific field")
    parser.add_argument("--min-count", type=int, default=2,
                        help="Minimum occurrences to show (default: 2)")
    args = parser.parse_args()

    if not _CORRECTIONS_ROOT.exists():
        print("No corrections data found. Run the system and approve some records first.")
        return

    entries = load_entries(args.clinic)

    if not entries:
        print(f"No entries found{' for clinic ' + args.clinic if args.clinic else ''}.")
        return

    summary(entries)

    if args.field:
        analyze_field(entries, args.field, args.min_count)
    else:
        fields = sorted({
            c["field"]
            for e in entries
            for c in e.get("corrections", [])
        })
        for field in fields:
            analyze_field(entries, field, args.min_count)

    print(f"\n{'='*60}")
    print(f"  NOTE: Review suggestions above before updating drug_db.json")
    print(f"  Human review required (ISO 42001 Cl.8.6 — no auto-update)")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
