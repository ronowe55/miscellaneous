# Claudeへの指示例

以下をそのままClaude Codeに伝えると、`statusline-cost-accumulator.py` と同等のスクリプトを生成できます。Node.js / npmが使えない環境（社内ポリシーでパッケージが申請制、など）向けです。

```
Claude Codeの累積コストをNode.js無しで管理したい。~/.claude/cost-tracker/statusline-cost-accumulator.py を
Python標準ライブラリのみで作って。仕様: statusLineフックとして毎ターンstdinのJSONを受け取り、
cost.total_cost_usd(セッション累計)とsession_idを取得。session_id→前回コストを
~/.claude/cost-tracker/session-state.jsonに保存し、差分だけを日付キーで
~/.claude/cost-tracker/cost-history.csvに加算(二重計上防止)。
~/.claude/settings.jsonのstatusLineにこのスクリプトを登録して。自動化(cron等)は不要。
```

ポイント: 「何を作るか」（ccusageというツール名やCSVのupsertという設計）だけを短く伝えれば、Node.jsの有無やOSの違いなどの実装細部はClaude側が判断してくれます。コピペやUSB転送ができない環境でも、この程度の長さなら手入力で伝えられます。
