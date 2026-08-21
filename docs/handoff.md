# Session Handoff (docs/handoff.md)

> **運用ルール**
> - セッション間の揮発的な作業状態の引き継ぎファイルです。
> - セッション開始時 (`In`) に読み込み、セッション終了時 (`Out`) に更新します。
> - 恒久的な設計情報はここではなく `docs/design.md` に記載してください。

---

## 1. 今回やったこと (Completed in this session)
- 仕様書「Video2Doc MultiLang v1.0 実装仕様書」に基づき、リポジトリ構成を初期化（Phase 0）。
- Pydantic スキーマ群（`worker/schemas/`）を定義:
  - `transcript.py`, `scene.py`, `frames.py`, `vision.py`, `evidence.py`, `manual.py`, `glossary.py`
- Provider 抽象化（`worker/providers/`）を実装:
  - `StorageProvider` (Local), `TranscriptionProvider` (FasterWhisper CPU/int8, Mock)
  - `VisionProvider` (LlamaCpp Qwen3-VL-2B GGUF, Rule-based), `TranslationProvider` (CTranslate2 M2M100, Mock)
- コアパイプライン（`worker/pipeline/`）を実装（Phase 1 〜 Phase 6）:
  - `validation.py`, `audio.py`, `transcription.py`, `scenes.py`, `frames.py` (dHash 重複排除), `vision.py`, `evidence.py`, `segmentation.py`, `manual.py`, `translation.py`, `rendering.py`
- Jinja2 テンプレート（`templates/manual.html.j2`, `templates/manual.md.j2`）を作成。
- CLI E2E スクリプト `scripts/run_pipeline.py` を実装し、テスト用サンプル動画によるパイプライン実行・全生成物（JSON/HTML/MD/PDF）の生成を実証（Phase 7）。
- 単体テスト・E2Eテスト（`pytest tests/`）を実装し、全テストパスを確認。

## 2. 現在の状態 (Current State)
- **CLI Engine & AI Pipeline (Phase 0 〜 Phase 7)** が完全に稼働可能。
- `pytest tests/` (3 tests) All Passed。
- `output/` に `manual_master.json`, `evidence.json`, `manual_vi.json`, `manual_id.json`, `manual.html`, `manual.md`, `manual.pdf`, `frames/*.jpg`, `audio.wav` が出力実証済み。

## 3. 次回やること (Next Steps)
- Phase 8: FastAPI バックエンドの構築（CLI Pipeline を Service として統合）
- Phase 9: Celery & Redis による非同期 Worker 処理
- Phase 10: PostgreSQL & SQLAlchemy によるマルチテナントデータモデル・Alembic マイグレーション
- Phase 11: React + Vite による PWA フロントエンド実装
- Phase 12: マルチテナント・SaaS ハードニング
