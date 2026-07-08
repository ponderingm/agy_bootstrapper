# Antigravity CLI Partner Bootstrapper (agy_bootstrapper) 🎭

本プロジェクトは、CharaForge 等で生成されたキャラクターカード (SillyTavern Card V2 JSON) を読み込み、指定した役割（ロール）と動的にマージして `GEMINI.md` に焼き、その人格の AI パートナーと対話しながら開発や創作を進められるようにする `agy` 起動ランチャーです。

---

## 📂 ディレクトリ構造
```text
agy_bootstrapper/
├── personas/            # キャラクターカード JSON
│   ├── sample.json      # 公開用サンプルカード (メイドロボ)
│   └── .gitignore       # yukikaze.json 等のプライベートデータを保護
├── roles/               # AIエージェントの役割定義 Markdown
│   └── programmer.md    # プログラミングパートナー
├── scripts/
│   ├── run_partner.py          # 起動合成スクリプト (Antigravity CLI / agy 用, 引数でYOLOモード制御可能)
│   └── run_partner_copilot.py  # 起動合成スクリプト (GitHub Copilot CLI 用)
├── install.sh            # 自動環境設定スクリプト (Antigravity CLI / agy 用)
├── install_copilot.sh    # 自動環境設定スクリプト (GitHub Copilot CLI 用)
└── README.md              # 本ファイル
```

---

## 🛠️ インストール方法

提供されている `install.sh` を実行するだけで、必要な環境設定や `~/.bashrc` へのショートカットコマンドの登録が完了します。

### 1. YOLOモード（権限ダイアログ自動承認）を対話的または引数で指定して実行

**① 対話式で設定を尋ねる場合**
```bash
./install.sh
# 実行時に [y/N] の入力プロンプトが表示され、YOLOモードをデフォルトにするかを決定します。
```

**② YOLOモードを明示的に有効（または無効）にして一発でインストールする場合**
```bash
# YOLOモード（権限ダイアログ自動承認）を有効にする
./install.sh --yolo

# スタンダードモード（通常権限ダイアログを表示）にする
./install.sh --no-yolo
```

### 2. 反射
インストール完了後、以下のコマンドで環境変数を反映させます。
```bash
source ~/.bashrc
```

---

## 🚀 ショートカットコマンドの使い方

インストールが完了すると、どのディレクトリからでも以下のショートカットが使用できます。

| コマンド | モード | 説明 |
| :--- | :--- | :--- |
| `agykaze` | 新規セッション | 「ゆきかぜ人格 ＋ プログラマー」で新規対話を開始します。 |
| `agykazec` | セッション継続 | 前回の会話履歴を継続した状態で「ゆきかぜ ＋ プログラマー」を起動します。 |
| `agyreset` | 初期化 | `GEMINI.md` を初期化し、通常の AI エージェント状態に戻します。 |
| `agyp [P] [R] [options]` | 自由設定 | 任意のペルソナ[P]とロール[R]を指定して起動します。（引数省略時は yukikaze / programmer） |

### `agyp` コマンドの例
```bash
# 凜子ペルソナを小説執筆（creative）ロール、かつセッション継続モードで起動
agyp rinko creative -c
```

---

## 🔒 セキュリティとプライベート保護

本プロジェクトは GitHub 公開を前提とした汎用設計となっていますが、プライベートで作成した「本命のキャラクターカード」が誤って Git コミットに含まれて公開されないよう、`personas/.gitignore` で完全に保護されています。

* デフォルトで `personas/` 直下のすべての JSON は無視されます。
* 例外的に公開用の `sample.json` のみ追跡されるようになっています。

---

## 🤖 GitHub Copilot CLI 版

Antigravity CLI (`agy`) の代わりに [GitHub Copilot CLI](https://docs.github.com/copilot/how-tos/use-copilot-agents/use-copilot-cli) (`copilot`) を起動ランチャーとして使いたい場合は、Copilot 用のインストーラーとスクリプトを使用してください。

```text
agy_bootstrapper/
├── install_copilot.sh              # Copilot CLI 用の自動環境設定スクリプト
└── scripts/
    └── run_partner_copilot.py      # Copilot CLI 用の起動合成スクリプト
```

Copilot CLI は `--yolo` と `--continue` を標準でサポートしているため、`agy` 版のような専用ラッパーオプションは不要です。また、生成した人格プロンプトは `.gemini/GEMINI.md` の代わりに Copilot CLI がグローバルに参照する `$HOME/.copilot/copilot-instructions.md` に書き出されます（Copilot は `.github/copilot-instructions.md` などリポジトリ側の指示ファイルも自動で併せて読み込みます）。

### インストール方法

```bash
./install_copilot.sh
# または
./install_copilot.sh --yolo      # YOLOモード（権限確認を自動許可）を既定にする
./install_copilot.sh --no-yolo   # スタンダードモード（毎回権限確認を表示）にする
```

インストール後は `source ~/.bashrc` を実行して反映してください。

### ショートカットコマンド

| コマンド | モード | 説明 |
| :--- | :--- | :--- |
| `copkaze` | 新規セッション | 「ゆきかぜ人格 ＋ プログラマー」で Copilot CLI の新規対話を開始します。 |
| `copkazec` | セッション継続 | 前回の会話履歴を継続した状態で Copilot CLI を起動します（`copilot --continue`）。 |
| `copreset` | 初期化 | Copilot CLI 用の指示ファイルを初期化し、通常のエージェント状態に戻します。 |
| `copp [P] [R] [options]` | 自由設定 | 任意のペルソナ[P]とロール[R]を指定して Copilot CLI を起動します。（引数省略時は yukikaze / programmer） |

```bash
# 凜子ペルソナを小説執筆（creative）ロール、かつセッション継続モードで起動
copp rinko creative -c
```

`agy` 版と `copilot` 版はエイリアス名（`agy*` / `cop*`）や指示ファイルの出力先が異なるため、両方を同じ環境に共存してインストールできます。
