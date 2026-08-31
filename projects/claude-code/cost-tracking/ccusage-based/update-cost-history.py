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
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HISTORY_FILE = Path.home() / ".claude" / "cost-tracker" / "cost-history.csv"


def fetch_daily_report():
    # Run through the user's own login shell (whatever $SHELL is, falling
    # back to sh) so nvm/nodenv/npx resolve the same way they do in a normal
    # terminal, even under a bare environment (e.g. launchd, if you choose
    # to schedule this yourself). Hardcoding zsh would fail on systems where
    # it isn't installed.
    shell = os.environ.get("SHELL", "/bin/sh")
    try:
        result = subprocess.run(
            [shell, "-l", "-c", "npx --yes ccusage@latest daily --json"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        print("ccusage timed out (first-time npx package download can be slow — try again)", file=sys.stderr)
        sys.exit(1)
    if result.returncode != 0:
        print(f"ccusage failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"ccusage did not return valid JSON:\n{result.stdout}", file=sys.stderr)
        sys.exit(1)


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

    try:
        for day in report.get("daily", []):
            date = day["period"]
            rows[date] = {
                "date": date,
                "total_cost_usd": f"{day['totalCost']:.4f}",
                "total_tokens": str(day["totalTokens"]),
                "models_used": "|".join(day.get("modelsUsed", [])),
            }
    except KeyError as e:
        print(f"ccusage output is missing an expected field ({e}) — its JSON shape may have changed", file=sys.stderr)
        sys.exit(1)

    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=str(HISTORY_FILE.parent))
    with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "total_cost_usd", "total_tokens", "models_used"])
        writer.writeheader()
        for date in sorted(rows):
            writer.writerow(rows[date])
    os.replace(tmp, HISTORY_FILE)

    total = sum(float(r["total_cost_usd"]) for r in rows.values())
    print(f"Updated {HISTORY_FILE} ({len(rows)} days, cumulative total ${total:.2f})")


if __name__ == "__main__":
    main()
