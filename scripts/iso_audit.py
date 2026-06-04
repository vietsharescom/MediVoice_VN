#!/usr/bin/env python3
"""
iso_audit.py — MediVoice VN ISO Health Check
DS-VN-COM-013 | v2.0 | 2026-06-06

STANDARDS:
  ISO 9001:2015 Cl.9.1.1  — Monitor, measure, analyze, evaluate
  ISO 9001:2015 Cl.9.2    — Internal audit at planned intervals
  ISO/IEC 42001:2023 Cl.9.1 — AI system performance evaluation
  ISO/IEC 25010:2023       — Software quality model
  ISO/IEC 42001:2023 Cl.8.5 — AI incident response

MODES:
  Default:              Document sync check (Tier 1) — run EVERY session (Step D)
  --quality:            Product quality audit (ISO/IEC 25010) — run after FID
  --weekly:             Full ISO audit (9001 + 42001) — triggered at session 7
  --all:                All modes combined
  --increment-session:  Increment session counter (run at SESSION CLOSE)
  --json:               Machine-readable output

USAGE:
  python scripts/iso_audit.py                  # session start check
  python scripts/iso_audit.py --quality        # post-FID quality audit
  python scripts/iso_audit.py --weekly         # full ISO 9001+42001 audit
  python scripts/iso_audit.py --all            # everything
  python scripts/iso_audit.py --increment-session  # session close counter
"""

import subprocess, re, sys, json
from pathlib import Path
from datetime import datetime, date

# Windows: force UTF-8 output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent
SCHEDULE_FILE = ROOT / "docs/records/audit_schedule.json"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def _load_schedule() -> dict:
    try:
        return json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {
            "last_full_audit_date": "unknown",
            "last_full_audit_session": "unknown",
            "sessions_since_full_audit": 0,
            "full_audit_trigger_sessions": 7,
        }


def _save_schedule(data: dict) -> None:
    SCHEDULE_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )


# ── Tier 1: Document Sync Checks (every session) ──────────────────────────────

def check_tests() -> dict:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no", "--no-header"],
            capture_output=True, text=True, cwd=ROOT, timeout=120,
        )
        m = re.search(r"(\d+) passed", result.stdout + result.stderr)
        if m:
            count = int(m.group(1))
            return {"ok": count >= 1, "count": count, "detail": f"{count} passed"}
        return {"ok": False, "count": 0, "detail": "Cannot parse pytest output"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "count": 0, "detail": "pytest timeout (>120s)"}
    except Exception as e:
        return {"ok": False, "count": 0, "detail": str(e)}


def check_rtm_gaps() -> dict:
    content = _read(ROOT / "docs/compliance/RTM.md")
    critical = [
        re.search(r"GAP-\d+", line).group(0)
        for line in content.splitlines()
        if "CRITICAL" in line and "OPEN" in line and re.search(r"GAP-\d+", line)
    ]
    return {
        "ok": len(critical) == 0,
        "gaps": critical,
        "detail": f"CRITICAL gaps open: {', '.join(critical)}" if critical else "No CRITICAL gaps",
    }


def check_backlog_critical() -> dict:
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
    content = _read(ROOT / "docs/records/LAST_SESSION.md")
    m = re.search(r"SES-(\d{8})", content)
    if not m:
        return {"ok": True, "detail": "No session date found"}
    session_date = datetime.strptime(m.group(1), "%Y%m%d").date()
    days_ago = (date.today() - session_date).days
    ok = abs(days_ago) <= 14
    return {
        "ok": ok,
        "days_ago": days_ago,
        "session_date": str(session_date),
        "detail": f"Last session: {session_date} ({days_ago} days ago)"
                  + (" ⚠️ >14 days" if not ok else ""),
    }


def check_doc_consistency() -> dict:
    issues = []
    claude = _read(ROOT / "CLAUDE.md")
    if "v0.4" not in claude:
        issues.append("CLAUDE.md: version not v0.4.x")
    decisions = _read(ROOT / "docs/records/DECISIONS.md")
    if "2026-06-06" not in decisions:
        issues.append("DECISIONS.md: missing 2026-06-06 ADRs")
    risk = _read(ROOT / "docs/compliance/RISK_REGISTER.md")
    if "R-D01" not in risk:
        issues.append("RISK_REGISTER.md: missing R-D01 (email data risk)")
    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "detail": "; ".join(issues) if issues else "All key docs consistent",
    }


def check_nonconforming() -> dict:
    content = _read(ROOT / "docs/compliance/NONCONFORMING.md")
    open_count = content.count("Status: OPEN")
    return {
        "ok": open_count == 0,
        "open": open_count,
        "detail": f"{open_count} open nonconformities" if open_count else "No open NCs",
    }


def check_design_report() -> dict:
    report = ROOT / "docs/records/DESIGN_REPORT_v1.1_20260606.md"
    exists = report.exists()
    claude = _read(ROOT / "CLAUDE.md")
    referenced = "DESIGN_REPORT" in claude
    issues = []
    if not exists:
        issues.append("DESIGN_REPORT file missing")
    if not referenced:
        issues.append("DESIGN_REPORT not referenced in CLAUDE.md")
    return {
        "ok": exists and referenced,
        "detail": "; ".join(issues) if issues else "DESIGN_REPORT present + referenced",
    }


def check_weekly_due() -> dict:
    sched = _load_schedule()
    sessions = sched.get("sessions_since_full_audit", 0)
    trigger = sched.get("full_audit_trigger_sessions", 7)
    due = sessions >= trigger
    return {
        "ok": not due,
        "sessions": sessions,
        "trigger": trigger,
        "last_audit": sched.get("last_full_audit_date", "unknown"),
        "detail": f"Sessions since last full audit: {sessions}/{trigger}"
                  + (" — ⚠️ WEEKLY AUDIT DUE" if due else ""),
    }


# ── ISO 9001:2015 + ISO 42001:2023 Specific Checks (--weekly) ────────────────

def check_iso9001_qms() -> dict:
    """ISO 9001:2015 Cl.9.1.1 — QMS monitoring."""
    issues = []
    warnings = []

    # Cl.9.1.1a: Monitor & measure QMS processes
    # → Test coverage as proxy for process effectiveness
    content = _read(ROOT / "docs/records/BACKLOG.md")
    done_count = content.count("[x]")
    todo_count = content.count("[ ]")
    total = done_count + todo_count
    if total > 0:
        completion = done_count / total * 100
        if completion < 50:
            warnings.append(f"Backlog completion {completion:.0f}% — low process effectiveness signal")

    # Cl.9.1.1b: Customer satisfaction (BS feedback)
    # → Check if /api/feedback endpoint exists
    api = _read(ROOT / "src/api/main.py")
    if "feedback" not in api:
        warnings.append("ISO9001 Cl.9.1.1b: /api/feedback not found — BS satisfaction data unavailable")

    # Cl.9.2: Internal audit planned
    sched = _load_schedule()
    if sched.get("last_full_audit_date") == "unknown":
        issues.append("ISO9001 Cl.9.2: No audit schedule found")

    # Cl.10.2: Nonconformity & corrective action
    nc = _read(ROOT / "docs/compliance/NONCONFORMING.md")
    open_nc = nc.count("Status: OPEN")
    if open_nc > 0:
        issues.append(f"ISO9001 Cl.10.2: {open_nc} open nonconformities require corrective action")

    ok = len(issues) == 0
    all_items = issues + ([f"⚠️ {w}" for w in warnings])
    return {
        "ok": ok,
        "issues": issues,
        "warnings": warnings,
        "detail": "; ".join(all_items) if all_items else "ISO 9001 QMS monitoring OK",
    }


def check_iso42001_ai_performance() -> dict:
    """ISO/IEC 42001:2023 Cl.9.1 — AI system performance evaluation."""
    issues = []
    warnings = []

    # Cl.9.1 + KPI-001: AI accuracy tracking
    # → Check if BENCH results exist
    backlog = _read(ROOT / "docs/records/BACKLOG.md")
    if "BENCH-001" in backlog and "✅" in backlog:
        pass  # BENCH-001 done
    else:
        warnings.append("42001 Cl.9.1: BENCH-001 not confirmed complete")

    if "BENCH-002" in backlog and "[ ]" in backlog[backlog.find("BENCH-002"):backlog.find("BENCH-002")+80]:
        warnings.append("42001 Cl.9.1: BENCH-002 (CEER pilot) pending — AI accuracy not validated with real audio")

    # Cl.9.1 + KPI-009: Human oversight — L4 bypass incidents
    l4 = _read(ROOT / "src/core/l4_human_gate.py")
    has_bypass_fn = bool(re.search(r"def\s+\w*bypass\w*\(", l4, re.IGNORECASE))
    if has_bypass_fn:
        issues.append("42001 Cl.9.1: L4 bypass function detected — human oversight violation")

    # Cl.8.5: AI incident response — nonconformities related to AI
    nc = _read(ROOT / "docs/compliance/NONCONFORMING.md")
    if "AI" in nc and "OPEN" in nc:
        warnings.append("42001 Cl.8.5: Open AI-related nonconformity — review required")

    # Cl.6.1: Risk register current
    risk = _read(ROOT / "docs/compliance/RISK_REGISTER.md")
    if "2026-06" not in risk:
        warnings.append("42001 Cl.6.1: RISK_REGISTER not updated in 2026-06 — may be stale")

    # Cl.5.2: AI Policy current
    policy = _read(ROOT / "docs/compliance/AI_POLICY.md")
    if "Documentation Assistant" not in policy:
        issues.append("42001 Cl.5.2: AI_POLICY missing 'Documentation Assistant' positioning")

    # Cl.7.2: AI transparency — disclaimer present in code
    pdf = _read(ROOT / "src/core/l9a_pdf_export.py")
    if "AI tạo nháp" not in pdf and "AI-assisted draft" not in pdf:
        issues.append("42001 Cl.6.3: Transparency disclaimer missing from PDF output")

    ok = len(issues) == 0
    all_items = issues + ([f"⚠️ {w}" for w in warnings])
    return {
        "ok": ok,
        "issues": issues,
        "warnings": warnings,
        "detail": "; ".join(all_items) if all_items else "ISO 42001 AI performance OK",
    }


def check_iso42001_human_oversight() -> dict:
    """ISO/IEC 42001:2023 Cl.6.1.2 — Human oversight control points."""
    issues = []

    # L4 Human Gate integrity
    l4 = _read(ROOT / "src/core/l4_human_gate.py")
    has_assert = "assert_approved" in l4 or "require_human_approval" in l4
    if not has_assert:
        issues.append("L4: assert_approved/require_human_approval not found")

    # L10 Audit log — no delete
    l10 = _read(ROOT / "src/core/l10_audit_log.py")
    has_delete_fn = bool(re.search(r"^\s*def\s+\w*delete\w*\s*\(", l10, re.IGNORECASE | re.MULTILINE))
    if has_delete_fn:
        issues.append("L10: delete function found — breaks immutability requirement")

    # Staff Confirm Gate — check api
    api = _read(ROOT / "src/api/main.py")
    has_approve = "approve" in api
    if not has_approve:
        issues.append("API: approve endpoint not found")

    ok = len(issues) == 0
    return {
        "ok": ok,
        "issues": issues,
        "detail": "; ".join(issues) if issues else "Human oversight controls intact",
    }


# ── Product Quality Checks (--quality) ────────────────────────────────────────

def check_quality_design_adherence() -> dict:
    content = _read(ROOT / "docs/records/BACKLOG.md")
    pending_red, pending_yellow = [], []
    in_immediate = False
    for line in content.splitlines():
        if "## IMMEDIATE" in line:
            in_immediate = True
        elif line.startswith("## ") and in_immediate:
            break
        if in_immediate and "[ ]" in line:
            m = re.search(r"\*\*([\w-]+)\*\*", line)
            if not m:
                continue
            if "🔴" in line:
                pending_red.append(m.group(1))
            elif "🟡" in line:
                pending_yellow.append(m.group(1))
    total = len(pending_red) + len(pending_yellow)
    return {
        "ok": len(pending_red) == 0,
        "red_pending": pending_red,
        "yellow_pending": pending_yellow,
        "detail": f"🔴: {pending_red} | 🟡: {pending_yellow}" if total else "All immediate tasks done",
    }


def check_quality_compliance() -> dict:
    issues = []
    pdf = _read(ROOT / "src/core/l9a_pdf_export.py")
    if "AI tạo nháp" not in pdf and "AI-assisted draft" not in pdf:
        issues.append("l9a_pdf_export.py: missing required disclaimer")
    l4 = _read(ROOT / "src/core/l4_human_gate.py")
    if "bypass" in l4.lower() and not re.search(r"no.bypass|BYPASS", l4):
        issues.append("l4_human_gate.py: verify no bypass logic")
    l10 = _read(ROOT / "src/core/l10_audit_log.py")
    if re.search(r"^\s*def\s+\w*delete\w*\s*\(", l10, re.IGNORECASE | re.MULTILINE):
        issues.append("l10_audit_log.py: delete function found — breaks immutability")
    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "detail": "; ".join(issues) if issues else "Compliance markers present",
    }


# ── Report runners ────────────────────────────────────────────────────────────

W = 62

def _line(icon: str, label: str, detail: str) -> None:
    print(f"  {icon} {label.ljust(24)} {detail}")


def run_doc_audit(as_json: bool = False) -> bool:
    """Tier 1: Document sync — every session."""
    checks = {
        "tests":             check_tests(),
        "rtm_gaps":          check_rtm_gaps(),
        "backlog_critical":  check_backlog_critical(),
        "last_session":      check_last_session(),
        "doc_consistency":   check_doc_consistency(),
        "nonconforming":     check_nonconforming(),
        "design_report":     check_design_report(),
        "weekly_due":        check_weekly_due(),
    }

    if as_json:
        print(json.dumps(checks, indent=2, ensure_ascii=False))
        return all(c["ok"] for c in checks.values())

    LABELS = {
        "tests": "Tests PASS",
        "rtm_gaps": "RTM CRITICAL gaps",
        "backlog_critical": "BACKLOG IMMEDIATE 🔴",
        "last_session": "Last session",
        "doc_consistency": "Doc consistency",
        "nonconforming": "Nonconformities",
        "design_report": "DESIGN_REPORT",
        "weekly_due": "Weekly audit",
    }

    print("=" * W)
    print("  ISO HEALTH CHECK (Doc Sync) — MediVoice VN")
    print(f"  {date.today()}  |  ISO 9001:2015 Cl.9.2 + 42001:2023 Cl.9.1")
    print("=" * W)

    issues, warnings = [], []
    weekly_due = False

    for key, result in checks.items():
        if key == "weekly_due":
            if not result["ok"]:
                weekly_due = True
            # Always show, don't count as error
            icon = "⚠️ " if not result["ok"] else "✅"
            _line(icon, LABELS[key], result["detail"])
            continue
        icon = "✅" if result["ok"] else ("⚠️ " if key == "last_session" else "🔴")
        _line(icon, LABELS[key], result["detail"])
        if not result["ok"]:
            if key == "last_session":
                warnings.append(result["detail"])
            else:
                issues.append(f"{LABELS[key]}: {result['detail']}")

    print("-" * W)

    if weekly_due:
        sched = _load_schedule()
        print()
        print("  ┌" + "─" * (W - 4) + "┐")
        print(f"  │  ⚠️  WEEKLY ISO AUDIT DUE — Session {sched['sessions_since_full_audit']}/{sched['full_audit_trigger_sessions']}  │")
        print(f"  │  Last audit: {sched['last_full_audit_date']}                          │")
        print("  │  Run at session CLOSE:                               │")
        print("  │    python scripts/iso_audit.py --weekly              │")
        print("  └" + "─" * (W - 4) + "┘")
        print()

    if not issues and not warnings:
        print("  ✅ DOC SYNC: ALL GOOD")
    else:
        if issues:
            print(f"  🔴 {len(issues)} ISSUE(S) — Address before proceeding:")
            for i in issues:
                print(f"     → {i}")
        if warnings:
            print(f"  ⚠️  {len(warnings)} WARNING(S):")
            for w in warnings:
                print(f"     → {w}")

    if issues:
        print()
        print("  ACTIONS:")
        for key, result in checks.items():
            if not result["ok"] and key not in ("last_session", "weekly_due"):
                if key == "rtm_gaps":
                    print(f"  → Write tests: {', '.join(result.get('gaps', []))}")
                elif key == "backlog_critical":
                    print(f"  → Work on: {', '.join(result.get('items', []))}")
                elif key == "doc_consistency":
                    for iss in result.get("issues", []):
                        print(f"  → Fix: {iss}")

    print("=" * W)
    return len(issues) == 0


def run_quality_audit() -> bool:
    """ISO/IEC 25010: product quality checks — after FID."""
    print()
    print("=" * W)
    print("  PRODUCT QUALITY AUDIT — ISO/IEC 25010:2023")
    print(f"  {date.today()}  |  See: docs/dev/QUALITY_AUDIT_TEMPLATE.md")
    print("=" * W)

    checks = {
        "design_adherence": check_quality_design_adherence(),
        "compliance":       check_quality_compliance(),
        "rtm_gaps":         check_rtm_gaps(),
        "design_report":    check_design_report(),
    }

    LABELS = {
        "design_adherence": "Design adherence",
        "compliance": "Compliance markers",
        "rtm_gaps": "RTM CRITICAL gaps",
        "design_report": "DESIGN_REPORT",
    }

    issues = []
    for key, result in checks.items():
        icon = "✅" if result["ok"] else "🔴"
        _line(icon, LABELS[key], result["detail"])
        if not result["ok"]:
            issues.append(f"{LABELS[key]}: {result['detail']}")

    print()
    print("  ℹ️  For CEER, WER, BS approve rate → use QUALITY_AUDIT_TEMPLATE.md")
    print("     (requires pilot data from BS Đà Nẵng)")
    print("=" * W)

    if issues:
        print(f"  🔴 {len(issues)} QUALITY ISSUE(S):")
        for i in issues:
            print(f"     → {i}")
        print("=" * W)
    return len(issues) == 0


def run_weekly_audit() -> bool:
    """Full ISO 9001:2015 + 42001:2023 audit — every 7 sessions."""
    print()
    print("=" * W)
    print("  WEEKLY ISO AUDIT — ISO 9001:2015 + ISO/IEC 42001:2023")
    print(f"  {date.today()}  |  Full system review")
    print("=" * W)

    print()
    print("  ── ISO 9001:2015 QMS MONITORING (Cl.9.1.1) ──")
    r9001 = check_iso9001_qms()
    icon = "✅" if r9001["ok"] else "🔴"
    for iss in r9001["issues"]:
        print(f"    🔴 {iss}")
    for w in r9001["warnings"]:
        print(f"    ⚠️  {w}")
    if not r9001["issues"] and not r9001["warnings"]:
        print("    ✅ ISO 9001 QMS monitoring OK")

    print()
    print("  ── ISO 42001:2023 AI PERFORMANCE (Cl.9.1) ──")
    r42_perf = check_iso42001_ai_performance()
    for iss in r42_perf["issues"]:
        print(f"    🔴 {iss}")
    for w in r42_perf["warnings"]:
        print(f"    ⚠️  {w}")
    if not r42_perf["issues"] and not r42_perf["warnings"]:
        print("    ✅ ISO 42001 AI performance OK")

    print()
    print("  ── ISO 42001:2023 HUMAN OVERSIGHT (Cl.6.1.2) ──")
    r42_ho = check_iso42001_human_oversight()
    for iss in r42_ho["issues"]:
        print(f"    🔴 {iss}")
    if not r42_ho["issues"]:
        print("    ✅ Human oversight controls intact")

    print()
    print("  ── DOCUMENT SYNC ──")
    doc_checks = {
        "tests": check_tests(),
        "rtm_gaps": check_rtm_gaps(),
        "nonconforming": check_nonconforming(),
        "doc_consistency": check_doc_consistency(),
    }
    doc_issues = []
    for key, result in doc_checks.items():
        icon = "✅" if result["ok"] else "🔴"
        print(f"    {icon} {key}: {result['detail']}")
        if not result["ok"]:
            doc_issues.append(result["detail"])

    all_issues = r9001["issues"] + r42_perf["issues"] + r42_ho["issues"] + doc_issues
    all_warnings = r9001["warnings"] + r42_perf["warnings"]

    print()
    print("=" * W)
    if not all_issues and not all_warnings:
        print("  ✅ WEEKLY AUDIT: PASS — All ISO controls verified")
    else:
        if all_issues:
            print(f"  🔴 {len(all_issues)} CRITICAL ISSUE(S):")
            for i in all_issues:
                print(f"     → {i}")
        if all_warnings:
            print(f"  ⚠️  {len(all_warnings)} WARNING(S):")
            for w in all_warnings:
                print(f"     → {w}")
    print("=" * W)

    # Reset counter after weekly audit
    if "--weekly" in sys.argv:
        sched = _load_schedule()
        sched["last_full_audit_date"] = str(date.today())
        sched["last_full_audit_session"] = f"SES-{date.today().strftime('%Y%m%d')}"
        sched["sessions_since_full_audit"] = 0
        _save_schedule(sched)
        print(f"\n  ✅ Audit schedule reset — next audit in {sched['full_audit_trigger_sessions']} sessions")

    return len(all_issues) == 0


def run_increment_session() -> None:
    """Increment session counter — run at SESSION CLOSE."""
    sched = _load_schedule()
    old = sched.get("sessions_since_full_audit", 0)
    sched["sessions_since_full_audit"] = old + 1
    _save_schedule(sched)
    trigger = sched.get("full_audit_trigger_sessions", 7)
    new = sched["sessions_since_full_audit"]
    print(f"  📊 Session counter: {new}/{trigger}")
    if new >= trigger:
        print(f"  ⚠️  WEEKLY AUDIT DUE at next session close!")
        print(f"     Run: python scripts/iso_audit.py --weekly")
    else:
        remaining = trigger - new
        print(f"  ℹ️  Next full audit in {remaining} session(s)")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    args = set(sys.argv[1:])
    as_json = "--json" in args

    if "--increment-session" in args:
        run_increment_session()
        sys.exit(0)

    run_quality = "--quality" in args or "--all" in args
    run_weekly  = "--weekly"  in args or "--all" in args
    run_doc     = "--quality" not in args or "--all" in args

    ok = True
    if run_doc:
        ok = run_doc_audit(as_json=as_json) and ok
    if run_quality:
        ok = run_quality_audit() and ok
    if run_weekly:
        ok = run_weekly_audit() and ok

    sys.exit(0 if ok else 1)
