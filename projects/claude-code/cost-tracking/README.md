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

## 0. リポジトリを取得

以下のセットアップ手順は、このリポジトリを取得した状態から進めます。

```bash
git clone https://github.com/ronowe55/miscellaneous.git
cd miscellaneous/projects/claude-code/cost-tracking
```

---

## `ccusage-based/` の使い方

1. `~/.claude/cost-tracker/` に配置し、実行権限を付与
   ```bash
   mkdir -p ~/.claude/cost-tracker
   cp ccusage-based/update-cost-history.py ~/.claude/cost-tracker/
   chmod +x ~/.claude/cost-tracker/update-cost-history.py
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

1. `~/.claude/cost-tracker/` に配置し、実行権限を付与
   ```bash
   mkdir -p ~/.claude/cost-tracker
   cp statusline-based/statusline-cost-accumulator.py ~/.claude/cost-tracker/
   chmod +x ~/.claude/cost-tracker/statusline-cost-accumulator.py
   ```
2. `~/.claude/settings.json` の `statusLine` に登録

   `~/.claude/settings.json` がまだ無い場合：
   ```bash
   mkdir -p ~/.claude
   printf '{\n  "statusLine": {\n    "type": "command",\n    "command": "%s/.claude/cost-tracker/statusline-cost-accumulator.py"\n  }\n}\n' "$HOME" > ~/.claude/settings.json
   ```
   （ヒアドキュメントではなく1行の`printf`にしているのは、この手順書のようにMarkdownの番号付きリスト内でコードブロックがインデントされていると、ヒアドキュメントの終端行`EOF`も字下げされてしまい、GitHub上のレンダリング経由のコピーボタンを使わず生のテキストをそのまま貼り付けた場合にシェルが閉じずにハングするためです）

   すでに `~/.claude/settings.json` があり他の設定も入っている場合は、上書きせず `statusLine` キーだけを手動で追記してください。
3. Claude Codeを使うだけで、ターン毎に自動的に呼ばれて `cost-history.csv` が更新されます。ターミナル下部には
   ```
   Opus | Session: $0.25 | All-time: $0.30
   ```
   のように、セッション内コストと全期間の累計コストが表示されます。

内部的には、`cost.total_cost_usd`が「セッション内の累計値」であることを利用し、`session-state.json`に前回値を保持して**差分だけ**を日次CSVに加算することで、同じセッションのターンを何度呼ばれても二重計上しないようにしています。あるセッションを初めて検知した時点では、それまでの累計はまるごと差分計上せず基準値としてだけ記録します（すでにしばらく走っていたセッションにこのスクリプトを後から取り付けた場合や、他の集計方法から乗り換えた場合に、それまでの分がまるごと二重計上されるのを防ぐためです）。

---

## `show-cost.py`: 現在の状況をひと目で見る

`ccusage-based/`・`statusline-based/`どちらの方法で作った`cost-history.csv`も、`date,total_cost_usd`という共通の列を持っているので、[`show-cost.py`](./show-cost.py)で共通してレポートできます。

1. `~/.claude/cost-tracker/` に配置
   ```bash
   cp show-cost.py ~/.claude/cost-tracker/
   ```
2. 実行
   ```bash
   python3 ~/.claude/cost-tracker/show-cost.py
   ```

出力例：
```
当日の使用量(2026-08-31): $1.28
月間制限: $20
累計使用量: $6.40
使用割合: 32.0%
```

- **当日の使用量** — `cost-history.csv`の今日の日付の行
- **月間制限** — スクリプト冒頭の `MONTHLY_LIMIT_USD` 定数（デフォルト$20固定）。この$20という値はこのサンプルを作成した環境の契約プラン（Claude Proプラン）の月額に合わせただけの初期値なので、実際に使う際は自分の契約プランの月額に書き換えてください（例: Max 20xなら200、Max 5xなら100）
- **累計使用量** — 今月（当月の年月に前方一致する行すべて）の合計。月が変われば自動的にリセットされます
- **使用割合** — 累計使用量 ÷ 月間制限

**注意:** `MONTHLY_LIMIT_USD`を`~/.claude/cost-tracker/show-cost.py`側で直接書き換えた場合、この`README`のセットアップ手順を再度なぞって`cp show-cost.py ~/.claude/cost-tracker/`を実行すると、リポジトリ側のデフォルト値で上書きされます。再実行する前に差分を確認するか、書き換えはリポジトリ側の`show-cost.py`に対して行ってから配置し直してください。

エイリアスに登録しておくと、`cost`と打つだけで確認できて便利です（すでに同じ行がある場合は追記しないようにしています）。

```bash
grep -qxF 'alias cost="python3 ~/.claude/cost-tracker/show-cost.py"' ~/.zshrc 2>/dev/null || echo 'alias cost="python3 ~/.claude/cost-tracker/show-cost.py"' >> ~/.zshrc
source ~/.zshrc
```

（bashの場合は `~/.zshrc` を `~/.bashrc` に置き換えてください）

---

## Claudeへの指示サンプルについて

各ディレクトリの `prompt.md`（[`ccusage-based/prompt.md`](./ccusage-based/prompt.md)、[`statusline-based/prompt.md`](./statusline-based/prompt.md)、[`show-cost.py`用](./prompt.md)）は、実際にこれらのスクリプトをClaude Codeに作らせた際の指示文そのものです。コピペやファイル転送ができない環境（社内PCなど）でも、この程度の短い指示文なら手入力で伝えられ、Claude側に実装の細部を任せられます。

---

## 免責事項

このソフトウェアは個人利用を目的として作成・公開しているものです。コスト計算はClaude Code本体または[ccusage](https://github.com/ryoppippi/ccusage)（サードパーティ製、非公式ツール）の実装に依存しており、正確性を保証するものではありません。実際の請求額とは差異が生じる可能性があります。本ソフトウェアの使用によって発生したいかなる損害についても、作者は一切の責任を負いません。正式なコスト管理には、各サービスの公式な利用状況・請求画面を必ず確認してください。
