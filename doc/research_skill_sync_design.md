# 調査・設計記録: SKILLのPrivateリポジトリ（.profiles）同期設計

## 現状の課題
- `personas/` は `.profiles/personas/*` へのシンボリックリンクとして管理されており、セッション開始時に `git pull`、終了時に `git push` が自動実行される。
- 一方、`roles/` 配下のロール（`roles/programmer` など）およびその配下のスキル（`roles/programmer/skills/*`）は本体リポジトリ `agy_bootstrapper` 内に存在していた。
- さらに `roles/.gitignore` では `*/skills/*` が除外設定されているため、蓄積されたスキルは本体リポジトリにもコミットされず、Privateリポジトリ（`.profiles`）にも同期されない孤立状態にあった。

## 解決策の比較・選定
### 案A: `roles/programmer` を `.profiles/roles/programmer` に移行し、シンボリックリンク化する（採用）
- `install.sh` には既に `$PROFILES_DIR/roles/*` を検出し、`$INSTALL_DIR/roles/$name` へシンボリックリンクを張るロジックが実装されている。
- `roles/programmer` を `.profiles/roles/programmer` に配置することで、以下が実現される：
  1. `roles/programmer/skills` 配下に作成された新規スキルは物理的に `.profiles` 内に作成される。
  2. `run_partner.py` の `_collect_profile_git_roots` が `.profiles` を同期対象として追跡し、セッション終了時に自動で `git add -A && git commit && git push` される。
  3. 他のマシンで `install.sh --profiles-repo=...` を実行した際にも自動でシンボリックリンク化され、スキルが共有される。
- 本体リポジトリ（`agy_bootstrapper`）側で追跡されていたファイル（`roles/programmer/role.md`, `roles/programmer/skills/general/SKILL.md`）に関しては、`git update-index --skip-worktree` および `.git/info/exclude` を適用することで、本体リポジトリの `git status` をクリーンに維持する。

## 手順
1. `roles/programmer` の全内容を `.profiles/roles/programmer` に安全にコピー。
2. 本体側で追跡対象ファイルを `skip-worktree` に設定し、`.git/info/exclude` に `roles/programmer` を登録。
3. 本体の `roles/programmer` を削除し、`.profiles/roles/programmer` へのシンボリックリンクに置き換える。
4. `.profiles` リポジトリ側でコミット＆プッシュを実行。
5. `agy_bootstrapper` 本体の `git status` がクリーンであることを確認。
6. `run_partner.py` の同期検出が正しく動作することを検証。
