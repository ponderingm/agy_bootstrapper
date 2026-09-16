# 実装完了記録: SKILLのPrivateリポジトリ自動同期化

## 実施日時
2026-09-16

## 実施概要
蓄積スキル（`roles/programmer/skills/*`）を非公開Privateリポジトリ（`.profiles`）に移行し、セッション終了時の自動コミット＆プッシュ（同期）の対象に組み込んだ。

## 実施手順と詳細
1. **ロール・スキル群の移行**:
   - `roles/programmer` の実体（`role.md` および既存の5スキル：`coolify_api_automation`, `gemini_api_routing`, `human_curated_lora_dataset`, `safe_asset_storage`, `vision_self_refining_loop`）を `.profiles/roles/programmer` にコピー。
   - `roles/programmer` を `.profiles/roles/programmer` へのシンボリックリンクに置換。
2. **本体リポジトリ（`agy_bootstrapper`）の保護**:
   - 元々本体リポジトリで追跡されていた `roles/programmer/role.md` と `general/SKILL.md` に対し `git update-index --skip-worktree` を適用。
   - `.git/info/exclude` に `roles/programmer` を追加し、シンボリックリンク化による作業ツリーのダーティ化を防止。
3. **Privateリポジトリ（`.profiles`）へのプッシュ**:
   - `.profiles` 側で新規追加されたロール・スキル群をコミット・プッシュ完了。
4. **`run_partner.py` の同期・クリーンアップ処理の改修**:
   - シンボリックリンク化されたロール配下のスキルが `~/.agents/skills` に登録される際、再起的なリンク解決により `roles_root` 判定から外れてクリーンアップ漏れ・`FileExistsError` が生じる問題を修正。
   - `.profiles/roles/` もクリーンアップ対象（`cleanup_roots`）に含め、安全なアトミックリンク置換処理を追加。
5. **動作検証**:
   - `run_partner.py --dry-run` による起動時 pull・スキル登録（5件）の成功を確認。
   - ダミースキル作成による `.profiles` での差分検知（`??`）と、セッション終了時自動プッシュの仕組みが機能することを確認。
