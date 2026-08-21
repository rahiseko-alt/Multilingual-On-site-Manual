---
name: session-checkout
description: >-
  Use this skill at the end of a working session or when completing a task.
  Performs the Out-check protocol: updates docs/handoff.md, records failures to docs/failures.md
  if any occurred, and commits/pushes changes.
---

# Session Check-out Skill (セッション終了プロトコル)

作業完了時またはセッション終了時 (`Out`) に実行する標準チェックアウト手順。

## 手順 (Workflow)

1. **機械検査・ランタイム検証の完了確認**:
   - 変更内容に応じたテスト・Lint・実環境確認 (Runtime Evidence) が完了していることを確認する。

2. **Handoff の更新 (Update Handoff)**:
   - [`docs/handoff.md`](../../docs/handoff.md) を更新する。
     - **今回やったこと**: 完了したタスク・変更点
     - **現在の状態**: 動作状態、未解決事項
     - **次回やること**: 次セッションでのタスク

3. **失敗事例の記録 (Append Failures if applicable)**:
   - 作業中にエラー、コマンド失敗、バグ、誤ったアプローチなどの失敗が発生し解決した場合は、[`docs/failures.md`](../../docs/failures.md) の末尾に追記する (Append-Only)。

4. **安全なGitステージング & コミット (Safe Stage & Commit)**:
   - 不要ファイルやシークレットが混入していないか `git status --short` および `git diff --name-only` で確認する。
   - `git add -A` は**禁止**。今回の作業スコープに合致する対象ファイルのみ `git add -- <path>` でステージングする。
   - コミットメッセージを作成しコミット: `git commit -m "..."`

5. **プッシュ判定 (Push Gate)**:
   - default branch (main/master) への自動 push は行わない。
   - 作業ブランチ、upstream、未同期の他者変更がないか確認する。
   - ユーザーからの明示的な指示またはCI連携要件がある場合のみ `git push` を実行する。
   - *(注意: PR作成やマージはユーザーからの明示的な指示がある場合のみ行う)*
