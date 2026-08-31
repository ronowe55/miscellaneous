# Claudeへの指示例（show-cost.py）

`ccusage-based/`または`statusline-based/`のいずれかで`cost-history.csv`ができている前提で、以下をそのままClaude Codeに伝えると `show-cost.py` と同等のスクリプトを生成できます。

```
~/.claude/cost-tracker/cost-history.csv (date,total_cost_usd の列を持つCSV) を読んで、
当日の使用量、月間制限:$200固定、累計使用量(当月分の合計)、使用割合:% を表示する
show-cost.py を作って。エイリアスcostとして使いたいので使い方も教えて。
```
