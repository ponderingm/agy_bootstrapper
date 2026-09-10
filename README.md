# AI Partner Bootstrapper (agy_bootstrapper) 🎭

本プロジェクトは、CharaForge 等で生成されたキャラクターカード (SillyTavern Card V2 JSON) を読み込み、指定した役割（ロール）と動的にマージして各エンジンの指示ファイルに焼き、その人格の AI パートナーと対話しながら開発や創作を進められるようにする統合起動ランチャーです。

## 🤖 対応エンジン

| エンジン | CLI | 指示ファイル出力先 | エイリアス接頭辞 |
| :--- | :--- | :--- | :--- |
| `agy` | Antigravity CLI | `~/.gemini/GEMINI.md` | `agy` |
| `copilot` | [GitHub Copilot CLI](https://docs.github.com/copilot/how-tos/use-copilot-agents/use-copilot-cli) | `~/.copilot/copilot-instructions.md` | `cop` |
| `claude` | [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | `~/.claude/CLAUDE.md` | `cld` |

YOLOモード・セッション継続の各フラグはエンジンごとの差異（`--dangerously-skip-permissions` / `--yolo`、`-c` / `--continue` 等）をスクリプト内で吸収します。

---

## 📂 ディレクトリ構造
```text
agy_bootstrapper/
├── personas/                # キャラクターカード
│   ├── sample/
│   │   ├── profile.json     # 公開用サンプルカード (メイドロボ)
│   │   ├── memories.md      # セッション日記（起動時にリンクを注入）
│   │   └── status.json      # ステータス
│   └── .gitignore           # プライベートペルソナを保護
├── roles/                   # AIエージェントの役割定義
│   ├── programmer/
│   │   ├── role.md          # プログラミングパートナー
│   │   └── skills/          # 蓄積スキル (skills/{name}/SKILL.md)
│   └── .gitignore           # private_*/ のプライベートロールを保護
├── scripts/
│   ├── run_partner.py       # 統合起動合成スクリプト (--engine agy|copilot|claude)
│   └── compress_memory.py   # メモリ圧縮スクリプト
├── install.sh               # 統合インストーラー (--engine で対象選択)
└── README.md                # 本ファイル
```

---

## 🛠️ インストール方法

`install.sh` を実行するだけで、`~/.bashrc` へのショートカットコマンドの登録が完了します。

**① 対話式で設定を尋ねる場合**
```bash
./install.sh
# インストールするエンジン（agy,copilot,claude / all）と
# YOLOモード [y/N] を対話的に指定します。
```

**② 引数で一発インストールする場合**
```bash
# agy のみ、YOLOモード有効
./install.sh --engine=agy --yolo

# Copilot CLI と Claude Code、スタンダードモード
./install.sh --engine=copilot,claude --no-yolo

# 全エンジン
./install.sh --engine=all --yolo

# 非公開の profiles リポジトリも一緒にセットアップする場合
./install.sh --engine=claude,copilot --no-yolo --profiles-repo=<owner>/<repo>
```

インストール完了後、以下のコマンドで反映させます。
```bash
source ~/.bashrc
```

---

## 🚀 ショートカットコマンドの使い方

エンジンごとに接頭辞（`agy` / `cop` / `cld`）が異なるだけで、同じ体系のショートカットが登録されます。

| コマンド | モード | 説明 |
| :--- | :--- | :--- |
| `<prefix>sample` | 新規セッション | 「sample ペルソナ ＋ プログラマー」で新規対話を開始します。 |
| `<prefix>samplec` | セッション継続 | 前回の会話履歴を継続した状態で起動します。 |
| `<prefix>reset` | 初期化 | 指示ファイルを初期化し、通常の AI エージェント状態に戻します。 |
| `<prefix>p [P] [R] [options]` | 自由設定 | 任意のペルソナ[P]とロール[R]を指定して起動します。（引数省略時は sample / programmer） |

### 例
```bash
# agy: 凜子ペルソナを小説執筆（creative）ロール、セッション継続モードで起動
agyp rinko creative -c

# Copilot CLI: sample ペルソナ + プログラマーで新規起動
copsample

# Claude Code: 任意ペルソナ・ロールで起動
cldp rinko creative -c
```

### `run_partner.py` を直接使う場合
```bash
python3 scripts/run_partner.py --engine copilot --persona sample --role programmer --yolo
python3 scripts/run_partner.py --engine claude --reset
python3 scripts/run_partner.py --persona sample --role programmer --dry-run  # エンジン省略時は agy
```

---

## 🔒 セキュリティとプライベート保護

本プロジェクトは GitHub 公開を前提とした汎用設計となっていますが、プライベートで作成した「本命のキャラクターカード」やロールが誤って Git コミットに含まれて公開されないよう、`.gitignore` で完全に保護されています。

* `personas/` 配下はデフォルトですべて無視され、公開用の `sample/` のみ追跡されます。
* `roles/` 配下の `private_` 接頭辞のロールディレクトリ（例: `roles/private_xxx/`）は無視されます。

## 🔄 非公開プロファイル（複数マシン間の同期）

`personas/` / `roles/` は `.gitignore` で守られている分、本命データはどのマシンにも
自動では同期されません。これを解決するには、本命データだけを持つ**別の private
リポジトリ**（以下「profiles リポジトリ」）を用意し、このリポジトリに読み込ませます。

### profiles リポジトリの構造

agy_bootstrapper と同じディレクトリ構造をそのまま踏襲してください。

```
<profiles-repo>/
├── personas/
│   └── <persona-name>/
│       ├── profile.json
│       ├── memories.md
│       └── status.json
└── roles/
    └── private_<role-name>/
        └── role.md
```

### セットアップ

```bash
./install.sh --engine=claude,copilot --no-yolo --profiles-repo=<owner>/<repo>
```

`gh` (GitHub CLI) で認証済みであれば、`install.sh` が profiles リポジトリを
`.profiles/` に clone し、その中の `personas/<name>` と `roles/<name>` を
`personas/` / `roles/` へシンボリックリンクします（`.profiles/` は
`.gitignore` 済みなので本体には一切コミットされません）。

### 自動同期の仕組み

一度リンクしてしまえば、あとは追加の設定なしで `run_partner.py`（＝各種
`<prefix>p` エイリアス含む）が自動で面倒を見ます。

* セッション開始前: 対象の persona/role がリンクしているgitリポジトリを検出し、`git pull --rebase --autostash`
* セッション終了後: 変更があれば `git add -A && git commit && git push`

検出はシンボリックリンクの参照先が agy_bootstrapper 自身とは別のgitリポジトリかどうかで
自動判定するため、profiles リポジトリの名前などをどこかに設定し直す必要はありません。

`git pull --rebase` がコンフリクトした場合は自動解決しません。profiles リポジトリの
ディレクトリで手動解決してから再度セッションを起動してください（個人利用中心で
同時編集の頻度が低いことを前提にした、意図的な割り切りです）。
