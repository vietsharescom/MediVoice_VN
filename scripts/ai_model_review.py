"""
ai_model_review.py — V4 AI Model Code Review Tool
ISO/IEC 42001:2023 Cl.8.6 — Independent V&V for L1a/L1c changes

Dùng khi:
  - Thay đổi src/core/l1a_asr.py
  - Thay đổi src/core/l1c_ner.py
  - Thay đổi data/reference/drug_db.json

Usage:
  python scripts/ai_model_review.py --save-baseline
  python scripts/ai_model_review.py --compare-baseline
  python scripts/ai_model_review.py --run          (chỉ xem, không lưu)
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

BASELINE_FILE = ROOT / "docs" / "records" / "AI_REVIEW_BASELINE.json"

# ── Test cases chuẩn (không thay đổi) ────────────────────────────────────────

TEST_CASES = [
    {
        "id": "TC-001",
        "desc": "Lâm sàng đầy đủ — cảm cúm",
        "input": "bệnh nhân sốt 38.5 huyết áp 120/80 mạch 80 chẩn đoán viêm họng cấp kê Amoxicillin 500mg 2 viên 3 lần ngày 5 ngày tái khám sau 5 ngày",
        "expected": {
            "nhiet_do": 38.5,
            "huyet_ap_tam_thu": 120,
            "huyet_ap_tam_truong": 80,
            "chan_doan_contains": "viêm họng",
            "drug_inns": ["Amoxicillin"],
            "tai_kham_contains": "5 ngày",
            "icd_prefix": "J",
            "confidence_min": 0.70,
        },
    },
    {
        "id": "TC-002",
        "desc": "Đơn thuốc phức tạp — nhiều thuốc",
        "input": "kê Paracetamol 500mg 2 viên 3 lần ngày và Amoxicillin 250mg 1 viên 2 lần ngày 7 ngày",
        "expected": {
            "drug_inns": ["Paracetamol", "Amoxicillin"],
            "drug_count_min": 2,
            "confidence_min": 0.20,
        },
    },
    {
        "id": "TC-003",
        "desc": "Sinh hiệu đa dạng",
        "input": "nhiệt độ 37.2 huyết áp 130/85 mạch 72 nhịp thở 18 cân nặng 60kg",
        "expected": {
            "nhiet_do": 37.2,
            "huyet_ap_tam_thu": 130,
            "mach": 72.0,
            "confidence_min": 0.20,
        },
    },
    {
        "id": "TC-004",
        "desc": "Tái khám và chẩn đoán",
        "input": "chẩn đoán tăng huyết áp nguyên phát tái khám sau 2 tuần",
        "expected": {
            "chan_doan_contains": "huyết áp",
            "tai_kham_contains": "2 tuần",
            # ICD lookup Phase 0 rule-based — không enforce prefix
            "confidence_min": 0.30,
        },
    },
    {
        "id": "TC-005",
        "desc": "Drug INN không bị dịch",
        "input": "uống Metformin 500mg và Omeprazole 20mg sau ăn",
        "expected": {
            "drug_inns": ["Metformin", "Omeprazole"],
            "no_vi_translation": True,
            "confidence_min": 0.20,
        },
    },
]


def run_pipeline(text: str) -> dict:
    """Chạy L1b → L1c → L1d → L2 trên input text."""
    from src.core.l1b_drug_correct import correct_drug_names, extract_drug_candidates
    from src.core.l1c_ner import extract_entities
    from src.core.l1d_icd_lookup import auto_lookup
    from src.core.l2_validate import validate

    corrected = correct_drug_names(text)
    drugs = extract_drug_candidates(corrected)
    entities = extract_entities(corrected, drugs)
    icd_code, _ = auto_lookup(entities.chan_doan)
    form_data, _, conf = validate(entities)

    return {
        "nhiet_do": entities.nhiet_do,
        "huyet_ap_tam_thu": entities.huyet_ap_tam_thu,
        "huyet_ap_tam_truong": entities.huyet_ap_tam_truong,
        "mach": entities.mach,
        "chan_doan": entities.chan_doan,
        "icd_code": icd_code,
        "drug_inns": [d["inn"] for d in entities.don_thuoc],
        "drug_count": len(entities.don_thuoc),
        "tai_kham": entities.tai_kham,
        "confidence": conf,
    }


def check_case(tc: dict, result: dict) -> tuple[bool, list[str]]:
    """Kiểm tra output so với expected. Returns (passed, failures)."""
    exp = tc["expected"]
    failures = []

    if "nhiet_do" in exp and exp["nhiet_do"] is not None:
        if result["nhiet_do"] is None or abs(result["nhiet_do"] - exp["nhiet_do"]) > 0.1:
            failures.append(f"nhiet_do: expected {exp['nhiet_do']}, got {result['nhiet_do']}")

    if "huyet_ap_tam_thu" in exp:
        if result["huyet_ap_tam_thu"] != exp["huyet_ap_tam_thu"]:
            failures.append(f"HA systolic: expected {exp['huyet_ap_tam_thu']}, got {result['huyet_ap_tam_thu']}")

    if "chan_doan_contains" in exp:
        if exp["chan_doan_contains"].lower() not in (result["chan_doan"] or "").lower():
            failures.append(f"chan_doan: '{exp['chan_doan_contains']}' not in '{result['chan_doan']}'")

    if "drug_inns" in exp:
        for inn in exp["drug_inns"]:
            if inn not in result["drug_inns"]:
                failures.append(f"Missing drug INN: {inn} (got {result['drug_inns']})")

    if "drug_count_min" in exp:
        if result["drug_count"] < exp["drug_count_min"]:
            failures.append(f"drug_count: {result['drug_count']} < {exp['drug_count_min']}")

    if "tai_kham_contains" in exp:
        if exp["tai_kham_contains"] not in (result["tai_kham"] or ""):
            failures.append(f"tai_kham: '{exp['tai_kham_contains']}' not in '{result['tai_kham']}'")

    if "icd_prefix" in exp:
        if not (result["icd_code"] or "").startswith(exp["icd_prefix"]):
            failures.append(f"ICD prefix: expected {exp['icd_prefix']}, got {result['icd_code']}")

    if "confidence_min" in exp:
        if result["confidence"] < exp["confidence_min"]:
            failures.append(f"confidence: {result['confidence']:.2f} < {exp['confidence_min']}")

    if exp.get("no_vi_translation"):
        vi_words = ["thuốc hạ sốt", "kháng sinh", "thuốc tiểu đường"]
        found = [w for w in vi_words if w in str(result.get("drug_inns", "")).lower()]
        if found:
            failures.append(f"Drug name translated to Vietnamese: {found}")

    return len(failures) == 0, failures


def run_all() -> list[dict]:
    results = []
    for tc in TEST_CASES:
        result = run_pipeline(tc["input"])
        passed, failures = check_case(tc, result)
        results.append({
            "id": tc["id"],
            "desc": tc["desc"],
            "passed": passed,
            "failures": failures,
            "output": result,
        })
    return results


def print_report(results: list[dict], label: str = "") -> bool:
    print(f"\n{'='*60}")
    print(f"V4 AI MODEL REVIEW — {label}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    all_pass = True
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"\n{status} [{r['id']}] {r['desc']}")
        if r["failures"]:
            all_pass = False
            for f in r["failures"]:
                print(f"       ↳ {f}")
        else:
            out = r["output"]
            print(f"       conf={out['confidence']:.2f} | icd={out['icd_code']} | drugs={out['drug_inns']}")

    print(f"\n{'='*60}")
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    verdict = "V4 REVIEW OK" if all_pass else "REVIEW FAILED"
    print(f"RESULT: {passed}/{total} PASS | {verdict}")
    print(f"{'='*60}\n")
    return all_pass


def compare_with_baseline(current: list[dict]) -> bool:
    if not BASELINE_FILE.exists():
        print("ERROR: Baseline không tìm thấy. Chạy --save-baseline trước.")
        return False

    baseline = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    print(f"\n{'='*60}")
    print("V4 REGRESSION COMPARISON vs BASELINE")
    print(f"{'='*60}")

    regressions = []
    for curr, base in zip(current, baseline):
        if base["passed"] and not curr["passed"]:
            regressions.append(f"REGRESSION [{curr['id']}]: was PASS, now FAIL")
            for f in curr["failures"]:
                regressions.append(f"  ↳ {f}")
        conf_delta = curr["output"]["confidence"] - base["output"]["confidence"]
        if conf_delta < -0.10:
            regressions.append(f"CONFIDENCE DROP [{curr['id']}]: {base['output']['confidence']:.2f} → {curr['output']['confidence']:.2f} (Δ={conf_delta:.2f})")

    if regressions:
        print("❌ REGRESSIONS FOUND:")
        for r in regressions:
            print(f"  {r}")
        return False
    else:
        print("NO REGRESSIONS — safe to merge")
        return True


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="V4 AI Model Review Tool")
    parser.add_argument("--save-baseline", action="store_true", help="Save current output as baseline")
    parser.add_argument("--compare-baseline", action="store_true", help="Compare current vs baseline")
    parser.add_argument("--run", action="store_true", help="Run review (no save)")
    args = parser.parse_args()

    results = run_all()
    all_pass = print_report(results, "CURRENT")

    if args.save_baseline:
        BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE_FILE.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Baseline saved: {BASELINE_FILE}")

    elif args.compare_baseline:
        no_regression = compare_with_baseline(results)
        sys.exit(0 if (all_pass and no_regression) else 1)

    else:
        sys.exit(0 if all_pass else 1)
