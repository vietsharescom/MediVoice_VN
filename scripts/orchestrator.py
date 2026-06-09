#!/usr/bin/env python3
"""
MediVoice VN — Orchestrator v1.0
DS-VN-ORCH-001 | ISO/IEC 42001:2023 Cl.5.4
Automation Layer L1: Andy ↔ Orchestrator ↔ Multi-AI ↔ Pipeline

Usage:
  python scripts/orchestrator.py start
  python scripts/orchestrator.py consult "topic" "question"
  python scripts/orchestrator.py check  "topic" "question"
  python scripts/orchestrator.py close
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).parent.parent

# Windows UTF-8 output
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_groq_key() -> str:
    import os
    key = os.environ.get("GROQ_API_KEY", "")
    if key:
        return key
    secrets = ROOT / ".streamlit" / "secrets.toml"
    if secrets.exists():
        for line in secrets.read_text(encoding="utf-8").splitlines():
            if "groq_api_key" in line and "=" in line:
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _read_head(path: Path, n: int = 40) -> str:
    try:
        return "\n".join(path.read_text(encoding="utf-8").splitlines()[:n])
    except Exception as e:
        return f"[Cannot read {path.name}: {e}]"


def _banner(title: str) -> None:
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


def _groq_call(messages: list, model: str = "llama-3.3-70b-versatile",
               max_tokens: int = 800, temperature: float = 0.3) -> dict:
    api_key = _load_groq_key()
    if not api_key:
        return {"error": "GROQ_API_KEY not found — add to .streamlit/secrets.toml or set env var"}

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        if not resp.ok:
            return {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        data = resp.json()
        return {
            "content": data["choices"][0]["message"]["content"],
            "model": data.get("model", model),
            "usage": data.get("usage", {}),
        }
    except Exception as e:
        return {"error": str(e)}


# ── Session Start ──────────────────────────────────────────────────────────────

def start_session() -> None:
    _banner(f"MediVoice VN — ORCHESTRATOR v1.0  |  {datetime.now():%Y-%m-%d %H:%M}")

    # 1. ISO audit
    print("\n📋 [1/4] ISO Audit...")
    res = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "iso_audit.py")],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    for line in (res.stdout or "").splitlines():
        stripped = line.strip()
        if stripped and any(x in stripped for x in
                            ["PASS", "ISSUE", "Session", "✅", "⚠️", "🔴", "tests", "version"]):
            print(f"  {stripped}")

    # 2. Last session summary
    print("\n📋 [2/4] Last Session...")
    last = ROOT / "docs" / "records" / "LAST_SESSION.md"
    for line in _read_head(last, 20).splitlines():
        if line.strip():
            print(f"  {line}")

    # 3. BACKLOG — next pending tasks
    print("\n📋 [3/4] BACKLOG — next tasks...")
    backlog_text = (ROOT / "docs" / "records" / "BACKLOG.md").read_text(encoding="utf-8")
    in_imm, count = False, 0
    for line in backlog_text.splitlines():
        if "## IMMEDIATE" in line:
            in_imm = True
            continue
        if in_imm and line.startswith("## "):
            break
        if in_imm and "[ ]" in line and count < 4:
            print(f"  {line.strip()}")
            count += 1

    # 4. Pending requests
    print("\n📋 [4/4] Pending Requests...")
    pending = ROOT / "docs" / "records" / "PENDING_REQUESTS.md"
    found = 0
    if pending.exists():
        for line in pending.read_text(encoding="utf-8").splitlines():
            if any(t in line for t in ["PA-", "CT-", "TP-"]) and "[ ]" in line and found < 4:
                print(f"  {line.strip()}")
                found += 1
    if found == 0:
        print("  (Không có pending requests mở)")

    _banner("STATUS: Ready — Chờ lệnh Andy.")


# ── Consultation ───────────────────────────────────────────────────────────────

_SYSTEM = """Bạn là Technical Consultant cho MediVoice VN — phần mềm AI voice-to-form cho phòng mạch tư VN.
Stack: Python 3.10 · FastAPI · PhoWhisper-medium · PhoBERT+CRF · SQLite · Streamlit.
Pipeline frozen L0→L10. L4 Human Gate bắt buộc (Luật KCB 2023 Đ.62).
Compliance: NĐ13/2023 · TT32/2023 · ISO 42001 · Luật AI 134/2025.
Trả lời ngắn gọn, kỹ thuật, actionable. Nếu câu hỏi tiếng Việt thì trả lời tiếng Việt."""


def consult(topic: str, question: str, context: str = "") -> dict:
    """Call Groq LLaMA-3.3-70B as external AI consultant."""
    user_msg = f"Context:\n{context}\n\nQuestion:\n{question}" if context else question

    print(f"\n🔄 Consulting Groq/LLaMA-3.3-70B  |  topic: {topic}")
    result = _groq_call(
        messages=[
            {"role": "system", "content": _SYSTEM + f"\nTopic hiện tại: {topic}"},
            {"role": "user", "content": user_msg},
        ],
    )

    if "error" in result:
        return {"error": result["error"], "topic": topic}

    out = {
        "type": "consultation",
        "topic": topic,
        "question": question,
        "ai": "Groq/LLaMA-3.3-70B",
        "model": result["model"],
        "response": result["content"],
        "usage": result["usage"],
        "timestamp": datetime.now().isoformat(),
    }

    _print_consult(out)
    _save_consult(out)
    return out


def _print_consult(r: dict) -> None:
    _banner(f"CONSULTATION  |  {r.get('ai','AI')}  |  {r.get('topic','')}")
    print(r.get("response", r.get("error", "")))
    u = r.get("usage", {})
    if u:
        print(f"\n  [Tokens: {u.get('prompt_tokens',0)} prompt + {u.get('completion_tokens',0)} completion]")
    print("=" * 60)


def _save_consult(r: dict) -> None:
    out_dir = ROOT / "docs" / "records" / "consultations"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    fname = f"ORCH-CONSULT-{ts}.json"
    (out_dir / fname).write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  💾 Saved → docs/records/consultations/{fname}")


# ── Consistency Check ─────────────────────────────────────────────────────────

def consistency_check(topic: str, question: str) -> None:
    """
    Send same question twice (simulating 2 AI perspectives), then analyse consistency.
    Production version would call GPT-4 + Groq + Copilot in parallel.
    """
    print(f"\n🔄 Consistency check — calling 2x Groq with different temperatures...")

    r1 = _groq_call(
        messages=[
            {"role": "system", "content": _SYSTEM + f"\nTopic: {topic}\nPerspective: Conservative / risk-aware"},
            {"role": "user", "content": question},
        ],
        temperature=0.1,
    )
    r2 = _groq_call(
        messages=[
            {"role": "system", "content": _SYSTEM + f"\nTopic: {topic}\nPerspective: Innovative / performance-focused"},
            {"role": "user", "content": question},
        ],
        temperature=0.7,
    )

    if "error" in r1 or "error" in r2:
        print(f"  Error: {r1.get('error', r2.get('error', ''))}")
        return

    print(f"\n  📊 Response A (Conservative):\n  {r1['content'][:300]}...\n")
    print(f"  📊 Response B (Innovative):\n  {r2['content'][:300]}...\n")

    # Analyse consistency
    check = _groq_call(
        messages=[
            {"role": "system", "content": "You are a consistency analyser. Compare two AI responses and output EXACTLY:\n1. AGREEMENTS:\n2. CONFLICTS:\n3. RECOMMENDATION:"},
            {"role": "user", "content": f"Topic: {topic}\n\nResponse A:\n{r1['content']}\n\nResponse B:\n{r2['content']}"},
        ],
        model="llama-3.1-8b-instant",
        max_tokens=350,
        temperature=0.1,
    )

    _banner(f"CONSISTENCY CHECK  |  {topic}")
    print(check.get("content", check.get("error", "")))
    print("=" * 60)
    _save_consult({
        "type": "consistency_check", "topic": topic, "question": question,
        "response_a": r1["content"], "response_b": r2["content"],
        "consistency": check.get("content", ""), "timestamp": datetime.now().isoformat(),
    })


# ── Close Session ─────────────────────────────────────────────────────────────

def close_session() -> None:
    _banner("CLOSE SESSION — Checklist")
    steps = [
        "1. Update docs/records/BACKLOG.md       (DOING → DONE)",
        "2. Update docs/records/PROJECT_PROGRESS.md",
        "3. Update CHANGELOG.md",
        "4. Ghi đè docs/records/LAST_SESSION.md  (6-category template)",
        "5. python scripts/iso_audit.py --increment-session",
        "6. git add -A && git commit && git push",
    ]
    for s in steps:
        print(f"  □ {s}")
    print("\n  Capture Rules: docs/dev/SESSION_CAPTURE_RULES.md")
    print("=" * 60)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]
    cmd = args[0] if args else "start"

    if cmd == "start":
        start_session()

    elif cmd == "consult":
        if len(args) < 3:
            print("Usage: orchestrator.py consult <topic> <question> [context]")
            sys.exit(1)
        consult(args[1], args[2], args[3] if len(args) > 3 else "")

    elif cmd == "check":
        if len(args) < 3:
            print("Usage: orchestrator.py check <topic> <question>")
            sys.exit(1)
        consistency_check(args[1], args[2])

    elif cmd == "close":
        close_session()

    else:
        print("Commands: start | consult <topic> <question> | check <topic> <question> | close")


if __name__ == "__main__":
    main()
