#!/usr/bin/env python3
"""
Pure-stdlib Claude Code statusLine hook that accumulates cost permanently.

No Node.js / npm / ccusage / network access required. Claude Code already
computes session cost itself and passes it as cost.total_cost_usd on every
turn via stdin. This script tracks the per-session delta (since
total_cost_usd is cumulative *within* a session, not across sessions) and
adds it into a permanent, ever-growing daily CSV so the record survives
even after Claude Code prunes old session transcripts.

Files (all under ~/.claude/cost-tracker/):
  session-state.json  - {session_id: last_seen_total_cost_usd}, used only
                         to compute today's delta; safe to delete anytime
                         (worst case: today's partial total undercounts).
  cost-history.csv     - date,total_cost_usd — the permanent record.
"""

import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

DIR = Path.home() / ".claude" / "cost-tracker"
STATE_FILE = DIR / "session-state.json"
HISTORY_FILE = DIR / "cost-history.csv"


def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def load_history():
    rows = {}
    if HISTORY_FILE.exists():
        for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines()[1:]:
            if not line.strip():
                continue
            d, cost = line.split(",", 1)
            rows[d] = float(cost)
    return rows


def save_history(rows):
    lines = ["date,total_cost_usd"]
    for d in sorted(rows):
        lines.append(f"{d},{rows[d]:.4f}")
    atomic_write(HISTORY_FILE, "\n".join(lines) + "\n")


def main():
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            payload = {}
    except Exception:
        payload = {}

    session_id = payload.get("session_id") or "unknown-session"
    model = (payload.get("model") or {}).get("display_name") or "Claude Code"
    session_cost = (payload.get("cost") or {}).get("total_cost_usd")

    state = read_json(STATE_FILE, {})
    grand_total_line = ""

    if isinstance(session_cost, (int, float)):
        previous = state.get(session_id, 0.0)
        delta = session_cost - previous if session_cost > previous else 0.0
        state[session_id] = session_cost
        atomic_write(STATE_FILE, json.dumps(state))

        history = load_history()
        today = date.today().isoformat()
        history[today] = history.get(today, 0.0) + delta
        save_history(history)

        grand_total = sum(history.values())
        grand_total_line = f" | All-time: ${grand_total:,.2f}"

    session_part = f"${session_cost:,.2f}" if isinstance(session_cost, (int, float)) else "?"
    print(f"{model} | Session: {session_part}{grand_total_line}")


if __name__ == "__main__":
    main()
