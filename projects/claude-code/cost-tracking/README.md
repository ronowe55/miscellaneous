# Claude Code Cost Tracking

Claude Codeの利用コストを、毎日`/usage`を手動で確認・記録する代わりに**自動で永続的に累積管理**するためのサンプルスクリプト集です。

どちらのアプローチも、日付ごとの累積コストを `~/.claude/cost-tracker/cost-history.csv` というシンプルなCSVに書き出します。自動実行(launchd/cronなど)は前提にしていません。スケジューリングしたい場合は各自の環境に合わせて設定してください。

---

## 2つのアプローチ

環境によって使えるものが変わるため、2通り用意しています。

| | [`ccusage-based/`](./ccusage-based) | [`statusline-based/`](./statusline-based) |
|---|---|---|
| 依存関係 | Node.js / npm (`npx`) | なし（Python標準ライブラリのみ） |
| データ取得元 | ローカルのセッショントランスクリプト(`~/.claude/projects/**/*.jsonl`)を[ccusage](https://github.com/ryoppippi/ccusage)が解析 | Claude Code本体が計算してstatusLine hookに渡す`cost.total_cost_usd` |
| 過去分の遡り | 可能（ただしClaude Code側のログ保持期間内のみ） | 不可（スクリプトを設置した時点から先の分のみ記録される） |
| 実行タイミング | 手動 or 好きなタイミングで実行 | Claude Codeの各ターンで自動的に呼ばれる（statusLine hook） |
| 向いている環境 | Node.jsが自由に使える環境 | パッケージ導入が申請制など、外部パッケージを入れられない環境 |

**ネットワークアクセスは両方とも発生しません。** どちらもローカルにすでにある情報を読むだけです。

---

## `ccusage-based/` の使い方

1. `update-cost-history.py` を `~/.claude/cost-tracker/update-cost-history.py` に配置し、実行権限を付与
   ```bash
   chmod +x update-cost-history.py
   ```
2. 記録したいタイミングで手動実行
   ```bash
   python3 ~/.claude/cost-tracker/update-cost-history.py
   ```
   実行するたびに、その時点でccusageが検出できる全期間の日次コストが `cost-history.csv` にupsertされます（同じ日付の行は上書き、それ以外の日付の行は保持）。
3. 累計を見たいとき
   ```bash
   cat ~/.claude/cost-tracker/cost-history.csv
   ```
   実行時に表示される `cumulative total $X.XX` を見るだけでも確認できます。

**注意:** Claude Codeはセッションログを一定期間で自動削除するため、その期間内に最低1回はこのスクリプトを実行しておく必要があります。実行を忘れて保持期間を過ぎると、その期間の分だけ集計から漏れます。

---

## `statusline-based/` の使い方

1. `statusline-cost-accumulator.py` を `~/.claude/cost-tracker/statusline-cost-accumulator.py` に配置し、実行権限を付与
2. `~/.claude/settings.json` の `statusLine` に登録
   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "/Users/YOU/.claude/cost-tracker/statusline-cost-accumulator.py"
     }
   }
   ```
   （`/Users/YOU` の部分は実際のホームディレクトリに置き換えてください）
3. Claude Codeを使うだけで、ターン毎に自動的に呼ばれて `cost-history.csv` が更新されます。ターミナル下部には
   ```
   Opus | Session: $0.25 | All-time: $0.30
   ```
   のように、セッション内コストと全期間の累計コストが表示されます。

内部的には、`cost.total_cost_usd`が「セッション内の累計値」であることを利用し、`session-state.json`に前回値を保持して**差分だけ**を日次CSVに加算することで、同じセッションのターンを何度呼ばれても二重計上しないようにしています。

---

## `show-cost.py`: 現在の状況をひと目で見る

`ccusage-based/`・`statusline-based/`どちらの方法で作った`cost-history.csv`も、`date,total_cost_usd`という共通の列を持っているので、[`show-cost.py`](./show-cost.py)で共通してレポートできます。

```bash
python3 show-cost.py
```

出力例：
```
当日の使用量(2026-08-31): $4.96
月間制限: $200 固定
累計使用量: $27.50
使用割合: 13.8%
```

- **当日の使用量** — `cost-history.csv`の今日の日付の行
- **月間制限** — スクリプト冒頭の `MONTHLY_LIMIT_USD` 定数（デフォルト$200固定）。契約プランに合わせて書き換えてください
- **累計使用量** — 今月（当月の年月に前方一致する行すべて）の合計。月が変われば自動的にリセットされます
- **使用割合** — 累計使用量 ÷ 月間制限

エイリアスに登録しておくと、`cost`と打つだけで確認できて便利です。

```bash
# ~/.zshrc や ~/.bashrc に追記
alias cost="python3 ~/.claude/cost-tracker/show-cost.py"
```

---

## Claudeへの指示サンプルについて

各ディレクトリの `prompt.md`（[`ccusage-based/prompt.md`](./ccusage-based/prompt.md)、[`statusline-based/prompt.md`](./statusline-based/prompt.md)、[`show-cost.py`用](./prompt.md)）は、実際にこれらのスクリプトをClaude Codeに作らせた際の指示文そのものです。コピペやファイル転送ができない環境（社内PCなど）でも、この程度の短い指示文なら手入力で伝えられ、Claude側に実装の細部を任せられます。

---

## 免責事項

このソフトウェアは個人利用を目的として作成・公開しているものです。コスト計算はClaude Code本体または[ccusage](https://github.com/ryoppippi/ccusage)（サードパーティ製、非公式ツール）の実装に依存しており、正確性を保証するものではありません。実際の請求額とは差異が生じる可能性があります。本ソフトウェアの使用によって発生したいかなる損害についても、作者は一切の責任を負いません。正式なコスト管理には、各サービスの公式な利用状況・請求画面を必ず確認してください。
