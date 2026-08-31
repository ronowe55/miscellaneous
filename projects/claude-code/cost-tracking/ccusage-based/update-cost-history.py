#!/usr/bin/env python3
"""
Snapshots ccusage's daily Claude Code cost report into a permanent CSV.

Claude Code prunes its local session logs after a retention window, so
`ccusage` alone only sees recent history. Running this script (manually, or
on whatever schedule you set up yourself) upserts each day's totals into
~/.claude/cost-tracker/cost-history.csv before that day's raw logs can be
pruned, giving a permanently accumulating record without any manual
/usage bookkeeping.
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

HISTORY_FILE = Path.home() / ".claude" / "cost-tracker" / "cost-history.csv"


def fetch_daily_report():
    # Run through an interactive login shell so nvm/nodenv/npx resolve the
    # same way they do in a normal terminal, even under a bare environment
    # (e.g. launchd, if you choose to schedule this yourself).
    result = subprocess.run(
        ["zsh", "-l", "-c", "npx --yes ccusage@latest daily --json"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        print(f"ccusage failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def load_existing():
    rows = {}
    if HISTORY_FILE.exists():
        with HISTORY_FILE.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rows[row["date"]] = row
    return rows


def main():
    report = fetch_daily_report()
    rows = load_existing()

    for day in report.get("daily", []):
        date = day["period"]
        rows[date] = {
            "date": date,
            "total_cost_usd": f"{day['totalCost']:.4f}",
            "total_tokens": str(day["totalTokens"]),
            "models_used": "|".join(day.get("modelsUsed", [])),
        }

    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = HISTORY_FILE.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "total_cost_usd", "total_tokens", "models_used"])
        writer.writeheader()
        for date in sorted(rows):
            writer.writerow(rows[date])
    tmp.replace(HISTORY_FILE)

    total = sum(float(r["total_cost_usd"]) for r in rows.values())
    print(f"Updated {HISTORY_FILE} ({len(rows)} days, cumulative total ${total:.2f})")


if __name__ == "__main__":
    main()
