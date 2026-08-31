#!/usr/bin/env python3
"""
Prints a quick cost summary from ~/.claude/cost-tracker/cost-history.csv:
today's usage, the monthly budget, month-to-date cumulative usage, and what
percentage of the budget that is. Works with the CSV produced by either
ccusage-based/update-cost-history.py or statusline-based/statusline-cost-accumulator.py
— both write at least a `date,total_cost_usd` header.

Set up as a shell alias for a quick glance, e.g. in ~/.zshrc or ~/.bashrc:
    alias cost="python3 ~/.claude/cost-tracker/show-cost.py"
"""

import csv
from datetime import date
from pathlib import Path

# $20 is just the default this sample shipped with (it matched the Claude
# Pro plan on the machine it was written on). Change it to whatever your own
# plan's monthly budget actually is (e.g. 200 for Max 20x, 100 for Max 5x).
MONTHLY_LIMIT_USD = 20.0

HISTORY_FILE = Path.home() / ".claude" / "cost-tracker" / "cost-history.csv"


def load_history():
    rows = {}
    if HISTORY_FILE.exists():
        with HISTORY_FILE.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rows[row["date"]] = float(row["total_cost_usd"])
    return rows


def main():
    history = load_history()
    if not history:
        print(f"No data yet at {HISTORY_FILE}")
        return

    today = date.today()
    today_str = today.isoformat()
    month_prefix = today.strftime("%Y-%m")

    today_cost = history.get(today_str, 0.0)
    month_cost = sum(cost for d, cost in history.items() if d.startswith(month_prefix))
    percentage = (month_cost / MONTHLY_LIMIT_USD) * 100 if MONTHLY_LIMIT_USD else 0.0

    print(f"当日の使用量({today_str}): ${today_cost:,.2f}")
    print(f"月間制限: ${MONTHLY_LIMIT_USD:,.0f} 固定")
    print(f"累計使用量: ${month_cost:,.2f}")
    print(f"使用割合: {percentage:.1f}%")


if __name__ == "__main__":
    main()
