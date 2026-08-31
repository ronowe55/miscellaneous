#!/usr/bin/env python3
"""
Pure-stdlib Claude Code statusLine hook that accumulates cost permanently.

No Node.js / npm / ccusage / network access required. Claude Code already
computes session cost itself and passes it as cost.total_cost_usd on every
turn via stdin. This script tracks the per-session delta (since
total_cost_usd is cumulative *within* a session, not across sessions) and
adds it into a permanent, ever-growing daily CSV so the record survives
even after Claude Code prunes old session transcripts.

The first time a given session_id is observed, its cost-so-far is only used
to seed the baseline — it does NOT get credited as a delta. Otherwise a
session that had already been running for a while before this hook started
tracking it (right after installing this script, after session-state.json
was deleted/reset, or when switching over from a different cost-tracking
method that already counted this session's cost, e.g.
ccusage-based/update-cost-history.py) would have its entire accumulated
cost double-counted on top of whatever was already recorded for it
elsewhere. The tradeoff: a brand new session's very first turn is not
counted either, which undercounts by a negligible amount (usually a
fraction of a cent).

Files (all under ~/.claude/cost-tracker/):
  session-state.json  - {session_id: last_seen_total_cost_usd}, used only
                         to compute each turn's delta; safe to delete
                         anytime (worst case: today's partial total
                         undercounts, since every currently-open session
                         looks "new" again on its next turn).
  cost-history.csv     - date,total_cost_usd,... — the permanent record.
                         Reading tolerates extra trailing columns, so this
                         file can be shared with ccusage-based/update-cost-history.py
                         (which also writes total_tokens/models_used columns).

This script assumes a single Claude Code session writes to these files at a
time. Two sessions finishing a turn at the same instant can race on the
unlocked read-modify-write and one update can be lost; not handled here.
"""

import csv
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
        with HISTORY_FILE.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    rows[row["date"]] = float(row["total_cost_usd"])
                except (KeyError, ValueError, TypeError):
                    continue
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
        if session_id in state:
            previous = state[session_id]
            delta = session_cost - previous if session_cost > previous else 0.0
        else:
            # First sight of this session: seed the baseline only, don't
            # credit its cost-so-far as new (see module docstring).
            delta = 0.0

        # Write the history (the durable ledger) before the state file (just
        # a cursor). If the process dies in between, the next run recomputes
        # the same delta from the same `previous` baseline and re-adds it —
        # a rare, narrow double-count window — instead of the state file
        # already having moved on and silently dropping this delta forever.
        history = load_history()
        today = date.today().isoformat()
        history[today] = history.get(today, 0.0) + delta
        save_history(history)

        state[session_id] = session_cost
        atomic_write(STATE_FILE, json.dumps(state))

        grand_total = sum(history.values())
        grand_total_line = f" | All-time: ${grand_total:,.2f}"

    session_part = f"${session_cost:,.2f}" if isinstance(session_cost, (int, float)) else "?"
    print(f"{model} | Session: {session_part}{grand_total_line}")


if __name__ == "__main__":
    main()
