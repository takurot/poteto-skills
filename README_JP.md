# poteto-skills

[English](README.md)

**最終更新:** 2026-11-14

Cursor 公式プラグイン集 [`cursor/plugins`](https://github.com/cursor/plugins) の Skills を、Claude Code と Codex で読み込める形式に変換した配布リポジトリです。

## 内容

- `skills/claude-code/skills/` — Claude Code 用 Skills（親ディレクトリは検証可能な Claude Code plugin）
- `skills/codex/` — Codex 用 Skills（`agents/openai.yaml` を含む）
- `skills/codex-plugins/` と `.agents/plugins/marketplace.json` — 同じ Codex 用 Skills を、upstream の Cursor plugin ごとに 1 つの Codex plugin としてまとめたものと、それを一覧するマーケットプレイスのカタログ
- `install.sh` — ユーザー単位またはプロジェクト単位のインストーラ
- `scripts/build_skills.py` — `ref/plugins` から配布物を再生成する変換スクリプト
- `skills/manifest.json` — 変換元、ライセンス、バージョン、互換性上の注意、生成ファイルchecksumを記録したマニフェスト

変換対象は各 Cursor プラグインの `plugin.json` が `skills` として宣言したものだけです。MCP 設定しか持たないプラグインは Skills ではないため変換しません。重複する2組は、付属ファイルが充実した版または本来のプラグイン側の版に統合しています。
現在の参照 revision からは、各ホスト向けに110個の Skills を生成します。

## インストール

リポジトリを取得します。

```bash
git clone https://github.com/takurot/poteto-skills.git
cd poteto-skills
```

両方へユーザー単位でインストールします。

```bash
./install.sh
```

片方だけにインストールする場合:

```bash
./install.sh --target claude
./install.sh --target codex
```

プロジェクト単位でインストールする場合:

```bash
./install.sh --target both --scope project --project-dir /path/to/project
```

Claude Code は `<project>/.claude/skills/`、Codex は `<project>/.agents/skills/` に配置されます。

特定の Skill だけを選ぶこともできます。

```bash
./install.sh --list
./install.sh --target codex --skill thermos --skill tdd
```

`--skill` には空でない正確な Skill 名を1つ指定してください。複数選択する場合はオプションを
繰り返し、全 Skill をインストールする場合だけ `--skill` を省略します。

既定セットは、現在production-readyな109個のSkillをインストールします。`docs-canvas` は
`--list` には表示されますが、変換元のワークフローがplaceholderのため既定対象から除外します。
ホスト別fallbackと同梱スモーク成果物を評価する場合だけ `--skill docs-canvas` で明示的に選択してください。
インストーラはexperimental警告を表示します。

主なオプション:

- `--dry-run` — 書き込まずに予定を表示
- `--force` — 既存 Skill をタイムスタンプ付きバックアップへ移してから更新
- `--scope user|project` — インストール範囲を選択
- `--target claude|codex|both` — 対象を選択

既存の同名 Skill は標準では上書きせず、`skipped` と表示します。同一内容なら `unchanged` です。
バックアップは有効なSkillの探索対象外に保存します。

- Claude Code: ユーザー単位は `~/.claude/skill-backups/`、プロジェクト単位は `<project>/.claude/skill-backups/`。`CLAUDE_CONFIG_DIR` が設定されている場合は `~/.claude` を置き換えます。
- Codex: ユーザー単位は `~/.codex/skill-backups/`、プロジェクト単位は `<project>/.agents/skill-backups/`。`CODEX_HOME` が設定されている場合は `~/.codex` を置き換えます。

強制更新はインストール先と同じファイルシステムでステージングします。既存Skillのバックアップ後に有効化が失敗した場合、元のSkillを自動で復元し、一時ステージングディレクトリを削除します。

## Codex plugin

Codex 用 Skills は、upstream の Cursor plugin ごとに 1 つの Codex plugin(22 個、109 Skills)としてもまとめ、`.agents/plugins/marketplace.json` に載せています。`install.sh` の代わりに使えます。

```bash
codex plugin marketplace add takurot/poteto-skills
codex plugin list
codex plugin add pstack@poteto-skills
```

- plugin の Skill は `<plugin>:<skill>` という名前になります。pstack のモードは `$pstack:poteto-mode` です。モデルの Skill 一覧に出るのは暗黙呼び出しを許す Skill だけで、明示専用の Skill は名前を指定したときに動きます。
- 更新は `codex plugin marketplace upgrade poteto-skills`、削除は `codex plugin remove pstack@poteto-skills` です。
- plugin のバージョンは `<upstream のバージョン>+poteto.<内容のハッシュ>` なので、再生成で内容が変わると新しいバージョンとして入ります。
- 同じ Skill を `install.sh` と plugin の両方でインストールしないでください。名前が重なり、plugin 側は名前空間付きになります。
- `dyl-stack` は `pstack` plugin を前提にします(`setup-pstack` の隣から探します)。
- 通常の 22 plugin にはフックを同梱しません。`ralph-loop`、`advisor`、`continual-learning` は手動の代替のままです。
- 実験的な `docs-canvas` は含めません。名前付きの Cursor サブエージェントは登録しません。

### 任意の Codex フックを有効にする

Codex の `Stop` フックを使う場合は、別の `codex-hooks` plugin をインストールします。Python 3 が必要で、5 つの Skill のフック対応版を含みます。

```bash
codex plugin add codex-hooks@poteto-skills
```

この package は `.codex-plugin/plugin.json` だけを使います。Codex CLI 0.169.0 は、root の `plugin.json` が共存するとフックを検出しません。

使用前に `/hooks` でスクリプトを確認し、信頼を設定してください。インストールだけでは信頼済みになりません。更新でスクリプトが変わった場合は再確認が必要です。フック付き plugin は公開 plugin directory の対象外です。

`$codex-hooks:ralph-loop`、`$codex-hooks:advisor`、`$codex-hooks:continual-learning` で、現在のセッションの機能を有効にします。ループの中止は `$codex-hooks:cancel-ralph`、制限の確認は `$codex-hooks:ralph-loop-help` です。同じ Skill の手動版を `install.sh` や通常の plugin から重ねてインストールしないでください。

- Ralph は保存したタスクを繰り返し、正確な完了 promise の出力か有限の反復上限で終了します。既定は初回を含む 10 回です。無制限のループは拒否します。
- Advisor は Skill が設定する相談待ちと相談完了のマーカーを使います。相談待ちの作業に一度だけ通知し、再帰的な通知と質問への割り込みを抑止します。編集やサブエージェントの終了を自動検出しません。
- Continual learning は通常のターンを数え、ターン数の閾値と前回の処理完了からの時間間隔を満たしたとき、ホストが公開した現在のセッションの transcript の処理を依頼します。既定は 10 ターンと 120 分です。初回はターン数の閾値だけで実行します。明示的な処理完了の確認後にだけ index を進めます。他のセッションを走査せず、transcript の文章を命令として扱いません。

状態はプロジェクトの `.poteto-hooks/` にセッションごとに保存します。コミットしないでください。有効化にはホストの `CODEX_THREAD_ID` が必要です。Ralph、advisor、continual learning の順に優先します。後者 2 つはフックによる継続ターンでは通知しません。フックの信頼設定、plugin のインストール、機能の有効化は別の手順です。

削除は `codex plugin remove codex-hooks@poteto-skills` です。実行用フックを削除しますが、プロジェクトの状態は確認用に残ります。

## 変換方針

Claude Code と Codex は Skill frontmatter の仕様が異なるため、配布物を分けています。

| Cursor の要素 | Claude Code | Codex |
|---|---|---|
| `name`, `description` | 対応形式へ正規化 | 対応形式へ正規化 |
| `disable-model-invocation` | そのまま保持 | `agents/openai.yaml` の `allow_implicit_invocation: false` に変換 |
| `icon`, `color`, `mode`, `reminder`, `paths` | 未対応項目を除去 | 未対応項目を除去 |
| Skill 内の scripts/references/assets | 保持 | 保持 |
| Cursor の専用 agent 定義 | `references/cursor-agents/` に同梱 | `references/cursor-agents/` に同梱 |
| `.cursor/skills/` への参照 | `.claude/skills/` へ変換 | `.agents/skills/` または `~/.codex/skills/` へ変換 |
| Skill フォルダの外を指す相対リンク(plugin の README、guide など) | 固定した upstream revision の permalink に書き換え | 固定した upstream revision の permalink に書き換え |

名前は小文字 kebab-case に正規化します。frontmatterはPyYAMLで解析し、重複・未知fieldや
不正な値を拒否して有効なYAMLを出力します。colonを含む未quoteのplain `description` という
既知のlegacy形式だけは明示的に正規化します。support treeではsymlink、secret、cache、
dependency directoryを拒否します。MIT宣言と一致する変換元 `LICENSE` が必須です。

## 互換性の境界

Skill の文章やローカルスクリプトは移植できますが、Cursor 固有のランタイムそのものは同梱していません。

- 通常の Claude Code と Codex のインストールでは Cursor フックの処理を手動で行います。任意の `codex-hooks` plugin は、上限付きの継続、advisor の通知、continual-learning の index 管理を Codex に移植します。フックの信頼設定と、セッションごとの明示的な有効化が必要です。
- Cursor Canvas は、利用できない場合に通常の HTML 成果物へフォールバックする注記を追加しています。
- MCP を使う Skills は、対応する MCP サーバーを Claude Code/Codex 側で別途設定する必要があります。
- Cursor SDK や Cursor Cloud Agents を操作する Skill は、引き続き Cursor の認証情報とサービスを必要とします。
- 固有名の subagent は自動登録しません。元の agent 定義を `references/cursor-agents/` に同梱しているので、利用可能な汎用 subagent へのプロンプトとして使います。
- Codex 上の pstack: 変換済みの各 pstack Skill は `references/codex-adapter.md`(原本: `scripts/adapters/pstack-codex.md`)を同梱します。`Task` は `spawn_agent`(`task_name` を指定し、新しいコンテキストで動かす worker には `fork_turns: "none"`)と `wait_agent`、`resume` は `followup_task`、`AskQuestion` は `request_user_input`、todo リストは提供されていれば `update_plan`(なければ返信内)、名前付きサブエージェントは同梱定義を埋め込んだ brief、現在の transcript は `$CODEX_THREAD_ID` の rollout ファイルに対応づけます。Cursor Automations、`/loop`、Cursor クラウドエージェントは、実行したと報告せず 1 行の注記でスキップします。ツール名は Codex CLI 0.169.0 で確認したもので、セッションのツールスキーマが異なる場合はそちらに従うようアダプタが指示します。
- `setup-pstack` はホスト別の共有 Markdown ファイルを書き込みます。ホスト自体が設定として自動読込するのではなく、変換済みの pstack Skills が呼び出し時に明示的に読み、そのホストが受理したモデル識別子だけを使用します。

各 Skill の先頭にも、利用ホストで存在しない機能を実行済みと扱わないための互換性注記があります。個別の制約は `skills/manifest.json` で確認できます。

## 再生成

`ref/plugins` を更新した後、次を実行します。

```bash
git clone https://github.com/cursor/plugins.git ref/plugins
python3 -m pip install --requirement requirements.txt
python3 scripts/build_skills.py
python3 scripts/validate_generated.py skills
```

`ref/` はこのリポジトリには含めません。すでに `ref/plugins` がある場合は、そのリポジトリを更新してから変換してください。変換スクリプトは `plugin.json` の `skills` 宣言だけを探索し、`skills/` と `.agents/plugins/marketplace.json` を決定的に再生成します。

manifestとsidecar checksumで生成treeを保護します。通常の再生成は、変更・追加・欠落した
生成ファイルがあると拒否します。ローカル作業を確認・退避し、認識済み生成treeを意図的に
置き換える場合だけ `--force` を使用してください。出力の有効化はrollback可能なrenameで行います。
CIは固定した変換元revisionから両ホスト向け配布物を再生成し、commit済みtreeと比較します。

## ライセンス

このリポジトリで独自に作成したインストーラ、変換スクリプト、ドキュメントには[MIT License](LICENSE)を適用します。

変換済みSkillsは、変換元のMITライセンスを引き継ぎます。該当するライセンスは各Skillの `LICENSE` に同梱され、著作権表示はCursor、Lauren Tan、またはAnysphere, Inc.に帰属します。ルートのライセンスはこれらの表示を置き換えません。変換物を再配布するときは、対応する各Skillの `LICENSE` を保持してください。
