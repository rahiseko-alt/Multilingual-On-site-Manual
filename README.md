# Video2Doc MultiLang v1.0

CPU対応・PWA型 多言語現場マニュアル自動生成SaaS & AI処理パイプライン。

現場で撮影した作業動画から音声認識・重要場面抽出・視覚解析を行い、動画内の客観的な根拠（Evidence）を紐付けた構造化データ（`manual_master.json`）を生成し、多言語翻訳（ベトナム語・インドネシア語等）および HTML / Markdown / PDF 出力を行います。

---

## 開発方針 & アーキテクチャ

1. **CPU完全対応**:
   GPUを前提とせず、CPU最適化（`faster-whisper` int8, `llama.cpp` GGUF Q4, `CTranslate2` M2M100）で動作。
2. **Evidence-First**:
   AIによる根拠のない補完を禁止。すべての手順は動画タイムライン、音声セグメント（`transcript_ids`）、キーフレーム（`frame_ids`）を厳格に保持。
3. **段階的構築 (CLI First)**:
   CLI Engine → API (FastAPI) → Worker (Celery/Redis) → Database (PostgreSQL) → PWA (React+Vite)。

---

## リポジトリ構成

```text
video2doc-multilang/
├ worker/
│  ├ pipeline/          # 各パイプライン処理 (validation, audio, transcription, scenes, frames, vision, evidence, segmentation, manual, translation, rendering)
│  ├ providers/         # 抽象化プロバイダー (transcription, vision, translation, storage)
│  └ schemas/           # Pydanticデータモデル (transcript, scene, frames, vision, evidence, manual, glossary)
├ templates/            # Jinja2 テンプレート (HTML, Markdown)
├ scripts/
│  ├ run_pipeline.py    # CLI E2E エントリーポイント
│  ├ setup_models.py    # モデルセットアップ補助
│  └ generate_sample_media.py # テスト用サンプル動画生成
├ fixtures/sample/      # サンプルメディア
└ tests/                # 単体・統合テスト
```

---

## クイックスタート (CLI Engine)

### 1. 依存ライブラリのインストール
```bash
pip install -r requirements.txt
```

### 2. テストの実行
```bash
pytest tests/
```

### 3. サンプル動画によるパイプライン実行 (CLI)
```bash
# サンプル動画の生成
python scripts/generate_sample_media.py

# パイプライン実行 (MP4 -> Evidence -> manual_master.json -> 翻訳 -> HTML/MD/PDF)
python scripts/run_pipeline.py \
  --input fixtures/sample/sample.mp4 \
  --source-language ja \
  --target-languages vi,id \
  --output ./output \
  --use-mock
```

出力先 `./output/` に以下の成果物が生成されます:
- `audio.wav` : 抽出された 16kHz mono 音声
- `frames/*.jpg` : 重複排除されたキーフレーム画像
- `transcript.json` : Whisper 音声認識結果
- `scenes.json` : シーン境界データ
- `frames.json` : キーフレームメタデータ
- `vision.json` : 各フレームの視覚解析結果
- `evidence.json` : 音声・映像を統合した根拠データ
- `manual_master.json` : **システムの正規マニュアルデータ**
- `manual_vi.json`, `manual_id.json` : 翻訳済みマニュアル
- `manual.html`, `manual.md`, `manual.pdf` : レンダリング済みドキュメント
