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

def _load_key(env_var: str, secrets_key: str) -> str:
    import os
    key = os.environ.get(env_var, "")
    if key:
        return key
    secrets = ROOT / ".streamlit" / "secrets.toml"
    if secrets.exists():
        for line in secrets.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(secrets_key) and "=" in line:
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _read_head(path: Path, n: int = 40) -> str:
    try:
        return "\n".join(path.read_text(encoding="utf-8").splitlines()[:n])
    except Exception as e:
        return f"[Cannot read {path.name}: {e}]"


def _banner(title: str) -> None:
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


def _openai_compatible_call(url: str, api_key: str, messages: list, model: str,
                             max_tokens: int, temperature: float) -> dict:
    """Shared caller for OpenAI-compatible chat completion APIs (Groq, OpenAI, xAI)."""
    if not api_key:
        return {"error": "API key not found — add to .streamlit/secrets.toml or set env var"}

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        resp = requests.post(
            url,
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


def _groq_call(messages: list, model: str = "llama-3.3-70b-versatile",
               max_tokens: int = 800, temperature: float = 0.3) -> dict:
    api_key = _load_key("GROQ_API_KEY", "groq_api_key")
    return _openai_compatible_call(
        "https://api.groq.com/openai/v1/chat/completions",
        api_key, messages, model, max_tokens, temperature,
    )


def _openai_call(messages: list, model: str = "gpt-4o-mini",
                 max_tokens: int = 800, temperature: float = 0.3) -> dict:
    api_key = _load_key("OPENAI_API_KEY", "openai_api_key")
    return _openai_compatible_call(
        "https://api.openai.com/v1/chat/completions",
        api_key, messages, model, max_tokens, temperature,
    )


def _xai_call(messages: list, model: str = "grok-3",
              max_tokens: int = 800, temperature: float = 0.3) -> dict:
    api_key = _load_key("XAI_API_KEY", "xai_api_key")
    return _openai_compatible_call(
        "https://api.x.ai/v1/chat/completions",
        api_key, messages, model, max_tokens, temperature,
    )


# Provider registry for multi-AI consultation
_PROVIDERS = {
    "Groq/LLaMA-3.3-70B": _groq_call,
    "OpenAI/GPT-4o-mini": _openai_call,
    "xAI/Grok-3": _xai_call,
}


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


def multi_ai_consult(topic: str, question: str, context: str = "") -> dict:
    """Send the same question to all configured providers in _PROVIDERS."""
    user_msg = f"Context:\n{context}\n\nQuestion:\n{question}" if context else question
    messages = [
        {"role": "system", "content": _SYSTEM + f"\nTopic hiện tại: {topic}"},
        {"role": "user", "content": user_msg},
    ]

    results = {}
    for name, fn in _PROVIDERS.items():
        print(f"  -> {name}...")
        results[name] = fn(messages)
    return results


def consult(topic: str, question: str, context: str = "") -> dict:
    """Consult all configured AI providers (Groq, OpenAI, xAI) and save evidence."""
    print(f"\n🔄 Multi-AI consult  |  topic: {topic}")
    results = multi_ai_consult(topic, question, context)

    out = {
        "type": "consultation",
        "topic": topic,
        "question": question,
        "responses": {},
        "timestamp": datetime.now().isoformat(),
    }

    _banner(f"CONSULTATION  |  {topic}")
    for name, result in results.items():
        print(f"\n--- {name} ---")
        if "error" in result:
            print(f"  [SKIPPED] {result['error']}")
            out["responses"][name] = {"error": result["error"]}
            continue
        print(result["content"])
        u = result.get("usage", {})
        if u:
            print(f"\n  [Tokens: {u.get('prompt_tokens', 0)} prompt + {u.get('completion_tokens', 0)} completion]")
        out["responses"][name] = {
            "model": result["model"],
            "response": result["content"],
            "usage": u,
        }
    print("=" * 60)

    _save_consult(out)
    return out


def _save_consult(r: dict) -> None:
    out_dir = ROOT / "docs" / "records" / "consultations"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    fname = f"ORCH-CONSULT-{ts}.json"
    (out_dir / fname).write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  💾 Saved → docs/records/consultations/{fname}")


# ── Consistency Check ─────────────────────────────────────────────────────────

def consistency_check(topic: str, question: str) -> None:
    """Send the same question to all providers, then ask Groq to analyse consistency."""
    print(f"\n🔄 Consistency check — querying {len(_PROVIDERS)} providers...")

    messages = [
        {"role": "system", "content": _SYSTEM + f"\nTopic: {topic}"},
        {"role": "user", "content": question},
    ]

    responses = {}
    for name, fn in _PROVIDERS.items():
        print(f"  -> {name}...")
        responses[name] = fn(messages)

    ok = {name: r for name, r in responses.items() if "error" not in r}
    skipped = {name: r for name, r in responses.items() if "error" in r}

    for name, r in skipped.items():
        print(f"  [SKIPPED] {name}: {r['error']}")

    if len(ok) < 2:
        print("  Not enough providers responded to compare — need at least 2.")
        return

    for name, r in ok.items():
        print(f"\n  📊 {name}:\n  {r['content'][:300]}...\n")

    comparison_text = "\n\n".join(
        f"Response from {name}:\n{r['content']}" for name, r in ok.items()
    )
    check = _groq_call(
        messages=[
            {"role": "system", "content": "You are a consistency analyser. Compare the AI responses below and output EXACTLY:\n1. AGREEMENTS:\n2. CONFLICTS:\n3. RECOMMENDATION:"},
            {"role": "user", "content": f"Topic: {topic}\n\n{comparison_text}"},
        ],
        model="llama-3.1-8b-instant",
        max_tokens=400,
        temperature=0.1,
    )

    _banner(f"CONSISTENCY CHECK  |  {topic}")
    print(check.get("content", check.get("error", "")))
    print("=" * 60)
    _save_consult({
        "type": "consistency_check", "topic": topic, "question": question,
        "responses": {name: r["content"] for name, r in ok.items()},
        "skipped": {name: r["error"] for name, r in skipped.items()},
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
