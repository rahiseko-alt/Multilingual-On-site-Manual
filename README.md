# template-0811 (v3)

> **「既にあるものを探し、必要な差分だけ作り、過去の失敗に該当するときだけ照合し、重要な変更だけ独立した目で疑い、最後は実際に動いた事実で証明する。」**
> *(最小の工程で、十分な品質を得る)*

`template-0811 v3` は、AIペアプログラミングにおいて安全性と開発速度を両立するためのリポジトリ・ワークフローテンプレートです。

---

## 1. コア思想とアーキテクチャ

安全性や失敗防止のためのチェックを一律に適用すると開発摩擦が増大します。
本テンプレートは**「安全装置を維持しながら通常開発経路を軽量化する」**ことを目的とし、変更リスクに応じた動的Harnessを採用しています。

```text
                    GOAL
                      ↓
                [ EXPLORE ]
                 Search first
                 Reuse first
                Define the Gap
                      ↓
              Failure Match?
        ┌─────────────┼─────────────┐
        │ Level 2/3   │ Known Risk  │
        │             │ Area        │
        │ Repeated Failure          │
        └─────────────┬─────────────┘
                      ↓ YES
              [ FAILURE MATCHER ]
                Past failures only
                      ↓
                  [ BUILD ]
                Build only Gap
                      ↓
             [ MECHANICAL CHECK ]
            lint / test / build / CI
                      ↓
              Important Change?
                  ↙       ↘
                YES        NO
                 ↓          │
        [ INDEPENDENT CRITIC ]
          Wrong Goal
          Wrong Approach
          Real Bug
                 ↓
            Writer Fix
                 └──────┬───────┘
                        ↓
              [ REAL VERIFY ]
               Runtime Evidence
                        ↓
         [ INDEPENDENT VERIFIER ]
             (Level 3 / Release)
```

---

## 2. ルールの4層構造

すべてのルールは [`AGENTS.md`](./AGENTS.md) に集約・階層化されています。

```text
LEVEL A: NON-NEGOTIABLE RULES      (絶対ルール: 秘密・個人情報保護、テスト弱小化禁止など)
LEVEL B: DEVELOPMENT PRINCIPLES     (開発原則: Search First, Reuse First, Gap駆動)
LEVEL C: RISK-BASED WORKFLOW       (リスク別動的プロセス・Sub-Agent定義)
LEVEL D: REPOSITORY-SPECIFIC RULES  (プロジェクト固有ルール)
```

---

## 3. リスクレベル別の標準フロー

| Level | 種別 | 対象変更 | 適用フロー |
|---|---|---|---|
| **Level 0** | **TRIVIAL** | typo, コピー修正, CSS微調整, 単純rename, コメント修正, 1行バグ修正 | `BUILD` → `VERIFY` |
| **Level 1** | **NORMAL** | 単一API, 小機能, 局所バグ修正, 既存コンポーネント拡張 | `EXPLORE` → `BUILD` → `MECHANICAL CHECK` → `VERIFY` |
| **Level 2** | **IMPORTANT** | 新機能, 複数ファイル変更, State管理, DB設計/クエリ, 外部API連携, 既存仕様変更 | `EXPLORE` → `FAILURE MATCH` → `BUILD` → `MECHANICAL CHECK` → `INDEPENDENT CRITIC` → `WRITER FIX` → `VERIFY` |
| **Level 3** | **CRITICAL** | Auth/認可, 決済/課金, DBマイグレーション, セキュリティ基盤, 秘密情報 | `EXPLORE` → `FAILURE MATCH` → `BUILD` → `MECHANICAL CHECK` → `INDEPENDENT CRITIC` → `WRITER FIX` → `AUTOMATED TEST` → `RUNTIME VERIFY` → `INDEPENDENT VERIFIER` |

---

## 4. 三方向の品質保証 (Three Independent Eyes)

役割の異なる3つの独立サブエージェントを必要な場面でのみ動的に呼び出します。

```text
PAST    (過去)  -->  Failure Matcher     (docs/failures.md との照合のみ)
PRESENT (現在)  -->  Independent Critic   (WRONG GOAL / WRONG APPROACH / REAL BUG の指摘のみ)
REALITY (現実)  -->  Independent Verifier (完了報告の再実行とRuntime Evidenceの確認)
```

プロンプトおよび仕様詳細は [`prompts/`](./prompts/) に定義されています。

---

## 5. ドキュメント構造 (docs/)

| ファイル | 役割 | 運用ルール |
|---|---|---|
| [`docs/design.md`](./docs/design.md) | **恒久的な製品定義** | 対象ユーザー、解決課題、差別化、コア仕様、調査確定事実を記録。 |
| [`docs/failures.md`](./docs/failures.md) | **失敗記録** | Append-only (追記専用・過去記録改変禁止)。`failure-matcher` が必要時にのみ照合。 |
| [`docs/handoff.md`](./docs/handoff.md) | **セッション間引き継ぎ** | 揮発的な状態。「今回やったこと」「現在の状態」「次回やること」のみを記述。 |

---

## 6. セットアップの2段階運用 (FAST vs STRICT)

- **FAST (デフォルト)**: Prototype, PoC, UI検証, 実験, 内部ツール
  - 最小要件: 起動可能、Lint、最低限テスト、Git管理、README
- **STRICT**: Production, 公開サービス, Auth, 決済, 個人データ, DB migration
  - 追加要件: CI, Branch Protection, Smoke/E2E, 独立検証, セキュリティ監査

---

## 7. 評価指標 (Metrics)

本テンプレート自体の改善は、工程数やルール数の増加ではなく以下の指標によって評価します。

- 着手までの時間 / 作業時間
- Goal達成率 / 重大Bug率 / Regression率 / 同一失敗再発率
- ユーザーからの訂正回数 / 修正ループ回数 / Token消費量
