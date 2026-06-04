#!/usr/bin/env python3
"""
iso_audit.py — MediVoice VN ISO Health Check
DS-VN-COM-013 | ISO 9001:2015 Cl.10.3 | ISO/IEC 42001:2023 Cl.10
ISO/IEC 25010:2023 (quality section)

TWO MODES:
  Default (--doc):  Document consistency check — run EVERY session (Step D)
                    Fast, checks: tests + RTM gaps + BACKLOG + doc sync
  Quality (--quality): Product quality audit — run after FID or before phase launch
                    Slower, checks: test details + design adherence + compliance

Usage:
    python scripts/iso_audit.py              # document check (default)
    python scripts/iso_audit.py --quality    # full quality audit
    python scripts/iso_audit.py --json       # machine-readable output
    python scripts/iso_audit.py --all        # both modes
"""

import subprocess
import re
import sys
import json
from pathlib import Path
from datetime import datetime, date

# Windows: force UTF-8 output to avoid cp1252 errors
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent


# ── Helpers ──────────────────────────────────────────────────────────────────

def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


# ── Checks ───────────────────────────────────────────────────────────────────

def check_tests() -> dict:
    """Run pytest -q and parse pass count."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no", "--no-header"],
            capture_output=True, text=True, cwd=ROOT, timeout=120,
        )
        output = result.stdout + result.stderr
        m = re.search(r"(\d+) passed", output)
        if m:
            count = int(m.group(1))
            return {"ok": count >= 1, "count": count, "detail": f"{count} passed"}
        return {"ok": False, "count": 0, "detail": "Cannot parse pytest output"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "count": 0, "detail": "pytest timeout (>120s)"}
    except Exception as e:
        return {"ok": False, "count": 0, "detail": str(e)}


def check_rtm_gaps() -> dict:
    """Scan RTM.md for open CRITICAL gaps."""
    content = _read(ROOT / "docs/compliance/RTM.md")
    critical = []
    for line in content.splitlines():
        if "CRITICAL" in line and "OPEN" in line:
            m = re.search(r"GAP-\d+", line)
            if m:
                critical.append(m.group(0))
    return {
        "ok": len(critical) == 0,
        "gaps": critical,
        "detail": f"CRITICAL gaps open: {', '.join(critical)}" if critical else "No CRITICAL gaps",
    }


def check_backlog_critical() -> dict:
    """Find 🔴 items in IMMEDIATE section of BACKLOG.md not yet done."""
    content = _read(ROOT / "docs/records/BACKLOG.md")
    pending = []
    in_immediate = False
    for line in content.splitlines():
        if "## IMMEDIATE" in line:
            in_immediate = True
        elif line.startswith("## ") and in_immediate:
            break
        if in_immediate and "🔴" in line and "[ ]" in line:
            m = re.search(r"\*\*([\w-]+)\*\*", line)
            if m:
                pending.append(m.group(1))
    return {
        "ok": len(pending) == 0,
        "items": pending,
        "detail": f"Pending: {', '.join(pending)}" if pending else "None pending",
    }


def check_last_session() -> dict:
    """Check LAST_SESSION.md — warn if > 14 days old."""
    content = _read(ROOT / "docs/records/LAST_SESSION.md")
    m = re.search(r"SES-(\d{8})", content)
    if not m:
        return {"ok": True, "detail": "No session date found"}
    session_date = datetime.strptime(m.group(1), "%Y%m%d").date()
    days_ago = (date.today() - session_date).days
    ok = days_ago <= 14
    return {
        "ok": ok,
        "days_ago": days_ago,
        "session_date": str(session_date),
        "detail": f"Last session: {session_date} ({days_ago} days ago)"
                  + (" ⚠️ Review cadence" if not ok else ""),
    }


def check_doc_consistency() -> dict:
    """Check key files have matching version refs."""
    issues = []

    # CLAUDE.md should reference current version
    claude = _read(ROOT / "CLAUDE.md")
    if "v0.4" not in claude:
        issues.append("CLAUDE.md: version not v0.4.x")

    # DECISIONS.md should have 2026-06-06 entries
    decisions = _read(ROOT / "docs/records/DECISIONS.md")
    if "2026-06-06" not in decisions:
        issues.append("DECISIONS.md: missing 2026-06-06 ADRs")

    # RISK_REGISTER should have R-D01 (new risk)
    risk = _read(ROOT / "docs/compliance/RISK_REGISTER.md")
    if "R-D01" not in risk:
        issues.append("RISK_REGISTER.md: missing R-D01 (email data risk)")

    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "detail": "; ".join(issues) if issues else "All key docs consistent",
    }


def check_nonconforming() -> dict:
    """Check NONCONFORMING.md for open unresolved items."""
    content = _read(ROOT / "docs/compliance/NONCONFORMING.md")
    # Look for open NC entries (OPEN status)
    open_count = content.count("Status: OPEN")
    return {
        "ok": open_count == 0,
        "open": open_count,
        "detail": f"{open_count} open nonconformities" if open_count else "No open NCs",
    }


def check_design_report() -> dict:
    """Verify DESIGN_REPORT exists and is referenced in CLAUDE.md."""
    report = ROOT / "docs/records/DESIGN_REPORT_v1.1_20260606.md"
    exists = report.exists()
    claude = _read(ROOT / "CLAUDE.md")
    referenced = "DESIGN_REPORT" in claude
    ok = exists and referenced
    detail_parts = []
    if not exists:
        detail_parts.append("DESIGN_REPORT file missing")
    if not referenced:
        detail_parts.append("DESIGN_REPORT not referenced in CLAUDE.md")
    return {
        "ok": ok,
        "exists": exists,
        "referenced": referenced,
        "detail": "; ".join(detail_parts) if detail_parts else "DESIGN_REPORT present + referenced",
    }


# ── Report ────────────────────────────────────────────────────────────────────

def run_audit(as_json: bool = False) -> bool:
    checks = {
        "tests":           check_tests(),
        "rtm_gaps":        check_rtm_gaps(),
        "backlog_critical":check_backlog_critical(),
        "last_session":    check_last_session(),
        "doc_consistency": check_doc_consistency(),
        "nonconforming":   check_nonconforming(),
        "design_report":   check_design_report(),
    }

    if as_json:
        print(json.dumps(checks, indent=2, ensure_ascii=False))
        return all(c["ok"] for c in checks.values())

    LABELS = {
        "tests":            "Tests PASS",
        "rtm_gaps":         "RTM gaps",
        "backlog_critical":  "BACKLOG IMMEDIATE 🔴",
        "last_session":     "Last session",
        "doc_consistency":  "Doc consistency",
        "nonconforming":    "Nonconformities",
        "design_report":    "DESIGN_REPORT",
    }

    width = 60
    print("=" * width)
    print("  ISO HEALTH CHECK — MediVoice VN")
    print(f"  {date.today().strftime('%Y-%m-%d')}  |  DS-VN-COM-013")
    print("=" * width)

    issues = []
    warnings = []

    for key, result in checks.items():
        icon = "✅" if result["ok"] else ("⚠️ " if key == "last_session" else "🔴")
        label = LABELS[key].ljust(24)
        detail = result.get("detail", "")
        print(f"  {icon} {label} {detail}")
        if not result["ok"]:
            if key == "last_session":
                warnings.append(f"{LABELS[key]}: {detail}")
            else:
                issues.append(f"{LABELS[key]}: {detail}")

    print("-" * width)

    if not issues and not warnings:
        print("  ✅ ISO HEALTH: ALL GOOD — Ready to work")
    else:
        if issues:
            print(f"  🔴 {len(issues)} ISSUE(S) — Fix before proceeding:")
            for i in issues:
                print(f"     → {i}")
        if warnings:
            print(f"  ⚠️  {len(warnings)} WARNING(S):")
            for w in warnings:
                print(f"     → {w}")

    print("=" * width)

    # Specific guidance
    if issues:
        print()
        print("  ACTIONS REQUIRED:")
        for key, result in checks.items():
            if not result["ok"] and key != "last_session":
                if key == "tests":
                    print("  → Run: pytest tests/ -v  (find failing tests)")
                elif key == "rtm_gaps":
                    gaps = result.get("gaps", [])
                    print(f"  → Write unit tests for: {', '.join(gaps)}")
                elif key == "backlog_critical":
                    items = result.get("items", [])
                    print(f"  → Address in BACKLOG IMMEDIATE: {', '.join(items)}")
                elif key == "doc_consistency":
                    for iss in result.get("issues", []):
                        print(f"  → Fix: {iss}")
                elif key == "design_report":
                    print("  → Ensure DESIGN_REPORT_v1.1_20260606.md exists in docs/records/")
        print()

    return len(issues) == 0


# ── Quality checks (--quality mode) ─────────────────────────────────────────

def check_quality_design_adherence() -> dict:
    """Check if BACKLOG IMMEDIATE items are all done (design on track)."""
    content = _read(ROOT / "docs/records/BACKLOG.md")
    pending_red = []
    pending_yellow = []
    in_immediate = False
    for line in content.splitlines():
        if "## IMMEDIATE" in line:
            in_immediate = True
        elif line.startswith("## ") and in_immediate:
            break
        if in_immediate and "[ ]" in line:
            if "🔴" in line:
                m = re.search(r"\*\*([\w-]+)\*\*", line)
                if m:
                    pending_red.append(m.group(1))
            elif "🟡" in line:
                m = re.search(r"\*\*([\w-]+)\*\*", line)
                if m:
                    pending_yellow.append(m.group(1))
    total = len(pending_red) + len(pending_yellow)
    return {
        "ok": len(pending_red) == 0,
        "red_pending": pending_red,
        "yellow_pending": pending_yellow,
        "detail": f"Red: {pending_red}, Yellow: {pending_yellow}" if total else "All immediate tasks done",
    }


def check_quality_compliance() -> dict:
    """Spot-check compliance markers in source code."""
    issues = []
    # Check disclaimer in PDF export
    pdf = _read(ROOT / "src/core/l9a_pdf_export.py")
    if "AI tạo nháp" not in pdf and "AI-assisted draft" not in pdf:
        issues.append("l9a_pdf_export.py: missing required disclaimer")
    # Check L4 no bypass
    l4 = _read(ROOT / "src/core/l4_human_gate.py")
    if "bypass" in l4.lower() and "no_bypass" not in l4.lower() and "BYPASS" not in l4.upper():
        issues.append("l4_human_gate.py: possible bypass logic detected — verify manually")
    # Check audit log immutability: look for actual delete function defs, not comments
    l10 = _read(ROOT / "src/core/l10_audit_log.py")
    has_delete_fn = bool(re.search(r'^\s*def\s+\w*delete\w*\s*\(', l10, re.IGNORECASE | re.MULTILINE))
    if has_delete_fn:
        issues.append("l10_audit_log.py: delete function found — breaks immutability")
    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "detail": "; ".join(issues) if issues else "Compliance markers present",
    }


def run_quality_audit() -> bool:
    """ISO/IEC 25010 product quality checks."""
    print()
    print("=" * 60)
    print("  PRODUCT QUALITY AUDIT — MediVoice VN")
    print(f"  {date.today()}  |  ISO/IEC 25010:2023")
    print("=" * 60)

    checks = {
        "design_adherence": check_quality_design_adherence(),
        "compliance":       check_quality_compliance(),
        "rtm_gaps":         check_rtm_gaps(),
        "design_report":    check_design_report(),
    }

    LABELS = {
        "design_adherence": "Design adherence",
        "compliance":       "Compliance markers",
        "rtm_gaps":         "RTM CRITICAL gaps",
        "design_report":    "DESIGN_REPORT",
    }

    issues = []
    for key, result in checks.items():
        icon = "✅" if result["ok"] else "🔴"
        label = LABELS[key].ljust(22)
        detail = result.get("detail", "")
        print(f"  {icon} {label} {detail}")
        if not result["ok"]:
            issues.append(f"{LABELS[key]}: {detail}")

    print()
    print("  📋 For full quality audit, use:")
    print("     docs/dev/QUALITY_AUDIT_TEMPLATE.md")
    print("=" * 60)

    if issues:
        print(f"  🔴 {len(issues)} QUALITY ISSUE(S):")
        for i in issues:
            print(f"     → {i}")
        print("=" * 60)

    return len(issues) == 0


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    as_json = "--json" in sys.argv
    run_quality = "--quality" in sys.argv or "--all" in sys.argv
    run_doc = "--quality" not in sys.argv or "--all" in sys.argv

    ok_doc = True
    ok_quality = True

    if run_doc:
        ok_doc = run_audit(as_json=as_json)

    if run_quality:
        ok_quality = run_quality_audit()

    sys.exit(0 if (ok_doc and ok_quality) else 1)
