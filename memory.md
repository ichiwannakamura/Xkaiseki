# 🧠 AI自己進化メモリ (MEMORY & SKILLS)

---

## 💡 獲得したスキルと失敗録 (Learned Skills & Post-mortems)

### 📝 記録日: 2026-03-19

- **💡 知見: anthropic SDK 0.83.0 での例外モック方法**
  - **問題:** `anthropic.AuthenticationError(message="...", response=MagicMock(status_code=401), body={})` が `TypeError` になる（httpx.Response が必須）
  - **根本原因:** SDK 0.83.0 では例外コンストラクタが httpx.Response インスタンスを必須とする仕様に変更された
  - **解決策:** テストでは `exc = anthropic.AuthenticationError.__new__(anthropic.AuthenticationError)` を使って `__new__()` 経由でインスタンス化してから `side_effect` に設定する

### 📝 記録日: 2026-03-19

- **💡 知見: Windows環境でのgit check-ignoreの注意点**
  - **問題:** `git check-ignore .worktrees` がディレクトリ未存在時に "not ignored" を返す
  - **根本原因:** `.gitignore` に `.worktrees/`（末尾スラッシュ）で記載されている場合、ディレクトリが実在しないと `git check-ignore` が反応しない
  - **解決策:** `mkdir -p .worktrees` で先にディレクトリを作成してから `git check-ignore` で確認する

### 📝 記録日: 2026-03-19

- **💡 知見: KB検索の設計パターン**
  - **問題:** ベクトル検索はStreamlit Cloudのメモリ制限（1GB）に引っかかるリスクがある
  - **解決策:** lowercase部分一致 OR 検索（最大3件）でシンプルに実装。5トピック程度の小さなKBならこれで十分。
  - **適用場面:** 軽量なRAGが必要でリソース制限がある場合

---
（新しい学びを得たら上に追記すること）
