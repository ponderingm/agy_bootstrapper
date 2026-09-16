# TODO: SKILLのPrivateリポジトリ自動同期化

## 目的
`roles/programmer/skills` 配下に蓄積されたスキル（および今後追加されるスキル）を、セッション終了時に `.profiles`（Privateリポジトリ）へ自動コミット＆プッシュ（同期）されるように構成する。

## タスク一覧
- [x] 1. 既存の `roles/programmer` と `.profiles/roles` の実態調査・影響調査
- [x] 2. 最適なシンボリックリンク・同期構成の設計
- [x] 3. 移行スクリプトの作成と実行
- [x] 4. 既存スキルの `.profiles` への移行確認
- [x] 5. `run_partner.py` の自動同期（pull/push）の動作検証
- [x] 6. 完了記録（`doc/done_skill_sync.md`）の作成
