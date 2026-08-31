# Claudeへの指示例

以下をそのままClaude Codeに伝えると、`update-cost-history.py` と同等のスクリプトを生成できます。Node.js / npmが使える環境向けです。

```
Claude Codeの利用コストを累積管理したい。~/.claude/cost-tracker/update-cost-history.py を作成して。
内容: npx ccusage@latest daily --json を実行し、各daily行(period, totalCost, totalTokens, modelsUsed)を
~/.claude/cost-tracker/cost-history.csv に日付キーでupsert(同日付は上書き、他日付は保持)するスクリプト。
自動実行(launchd/cron)は不要、手動実行前提。作成後、使い方も教えて。
```
