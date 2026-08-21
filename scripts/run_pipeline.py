import argparse
import sys
import os
import shutil
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Load .env file
load_dotenv(dotenv_path=root_dir / ".env")

from worker.pipeline.validation import validate_video
from worker.pipeline.audio import extract_audio
from worker.pipeline.transcription import run_transcription
from worker.pipeline.scenes import detect_scenes
from worker.pipeline.frames import extract_and_deduplicate_frames
from worker.pipeline.vision import analyze_frames
from worker.pipeline.evidence import build_timeline_evidence
from worker.pipeline.segmentation import segment_steps
from worker.pipeline.manual import compose_manual
from worker.pipeline.translation import translate_manual
from worker.pipeline.rendering import render_manual_documents, PdfRenderError

from worker.providers.transcription.mock_provider import MockTranscriptionProvider
from worker.providers.transcription.whisper_provider import FasterWhisperTranscriptionProvider
from worker.providers.vision.rule_provider import RuleBasedVisionProvider
from worker.providers.vision.llamacpp_provider import LlamaCppVisionProvider
from worker.providers.translation.mock_provider import MockTranslationProvider
from worker.providers.translation.ctranslate_provider import CTranslateTranslationProvider
from worker.schemas.glossary import GlossaryData

def run_video2doc_pipeline(
    input_video_path: str,
    output_dir: str,
    source_language: str = "ja",
    target_languages: list = None,
    use_mock: bool = True,
    glossary_path: str = None,
) -> dict:
    if target_languages is None:
        target_languages = ["vi", "id"]

    input_path = Path(input_video_path).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    # 1. Validation
    meta = validate_video(str(input_path))

    # 2. Audio Extraction
    audio_wav_path = str(out_dir / "audio.wav")
    transcript = None
    if meta["has_audio"]:
        extract_audio(str(input_path), audio_wav_path)

        # 3. Transcription
        if use_mock or os.getenv("WHISPER_PROVIDER") == "mock":
            trans_provider = MockTranscriptionProvider()
        else:
            try:
                trans_provider = FasterWhisperTranscriptionProvider()
            except Exception:
                trans_provider = MockTranscriptionProvider()

        transcript = run_transcription(
            audio_path=audio_wav_path,
            provider=trans_provider,
            language=source_language,
            output_json_path=str(out_dir / "transcript.json")
        )
    else:
        from worker.schemas.transcript import TranscriptData
        transcript = TranscriptData(language=source_language, segments=[])
        (out_dir / "transcript.json").write_text(transcript.model_dump_json(indent=2), encoding="utf-8")

    # 4. Scene Detection
    scenes = detect_scenes(
        video_path=str(input_path),
        duration=meta["duration"],
        output_json_path=str(out_dir / "scenes.json")
    )

    # 5. Frame Extraction & Deduplication
    frames = extract_and_deduplicate_frames(
        video_path=str(input_path),
        scenes=scenes,
        transcript=transcript,
        output_dir=str(frames_dir),
        output_json_path=str(out_dir / "frames.json")
    )

    # 6. Visual Analysis
    if use_mock or os.getenv("VISION_PROVIDER") == "rule" or not os.getenv("VISION_MODEL_PATH"):
        vision_provider = RuleBasedVisionProvider()
    else:
        vision_provider = LlamaCppVisionProvider()

    vision_data = analyze_frames(
        frames=frames,
        provider=vision_provider,
        output_json_path=str(out_dir / "vision.json")
    )

    # 7. Timeline Evidence Fusion
    evidence_data = build_timeline_evidence(
        duration=meta["duration"],
        scenes=scenes,
        transcript=transcript,
        frames=frames,
        vision=vision_data,
        output_json_path=str(out_dir / "evidence.json")
    )

    # 8. Step Segmentation & Manual Composition
    segmented_steps = segment_steps(evidence_data)
    manual_master = compose_manual(
        segmented_evidence=segmented_steps,
        title="作業手順マニュアル",
        source_language=source_language,
        output_json_path=str(out_dir / "manual_master.json")
    )

    # 9. Translation
    glossary = GlossaryData()
    if glossary_path and Path(glossary_path).exists():
        glossary_raw = json.loads(Path(glossary_path).read_text(encoding="utf-8"))
        glossary = GlossaryData(**glossary_raw)

    if use_mock or os.getenv("TRANSLATION_PROVIDER") == "mock" or not os.getenv("TRANSLATION_MODEL_PATH"):
        trans_provider = MockTranslationProvider()
    else:
        trans_provider = CTranslateTranslationProvider()

    translate_manual(
        manual_master=manual_master,
        target_languages=target_languages,
        provider=trans_provider,
        glossary=glossary,
        output_dir=str(out_dir)
    )

    # 10. Document Rendering
    doc_paths = render_manual_documents(
        manual_master=manual_master,
        frames=frames,
        output_dir=str(out_dir),
        template_dir=str(root_dir / "templates")
    )

    return {
        "manual_master": str(out_dir / "manual_master.json"),
        "evidence": str(out_dir / "evidence.json"),
        "documents": doc_paths,
    }


def main():
    parser = argparse.ArgumentParser(description="Video2Doc MultiLang CLI Pipeline")
    parser.add_argument("--input", required=True, help="Path to input video file (e.g. sample.mp4)")
    parser.add_argument("--source-language", default="ja", help="Source video language (default: ja)")
    parser.add_argument("--target-languages", default="vi,id", help="Comma-separated target languages (e.g. vi,id)")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--use-mock", action="store_true", help="Force mock providers for fast local testing")
    parser.add_argument("--skip-pdf", action="store_true", help="Skip PDF generation if WeasyPrint C-libs are missing")
    parser.add_argument("--max-frames", type=int, default=30, help="CPU budget frame extraction limit")
    parser.add_argument("--glossary", default=None, help="Path to optional glossary JSON file")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    print("==================================================")
    print("Video2Doc MultiLang v1.0 CLI Pipeline")
    print(f"Input Video : {input_path}")
    print(f"Output Dir  : {output_dir}")
    print(f"Languages   : {args.source_language} -> {args.target_languages}")
    print("==================================================")

    # 0. Preflight Check
    run_preflight_check()

    # 1. Validation
    max_size_mb = int(os.getenv("MAX_VIDEO_SIZE_MB", 500))
    max_duration_min = int(os.getenv("MAX_VIDEO_DURATION_MINUTES", 30))
    print("[1/10] Validating video format and metadata...")
    meta = validate_video(str(input_path), max_size_mb=max_size_mb, max_duration_minutes=max_duration_min)
    print(f"       Duration: {meta['duration']:.2f}s, Audio: {meta['has_audio']}, Size: {meta['size_mb']:.2f}MB")

    # 2. Audio Extraction
    audio_wav_path = str(output_dir / "audio.wav")
    transcript = None
    if meta["has_audio"]:
        print("[2/10] Extracting 16kHz mono audio...")
        extract_audio(str(input_path), audio_wav_path)

        # 3. Transcription
        print("[3/10] Transcribing audio with Whisper...")
        if args.use_mock or os.getenv("WHISPER_PROVIDER") == "mock":
            trans_provider = MockTranscriptionProvider()
        else:
            try:
                trans_provider = FasterWhisperTranscriptionProvider()
            except Exception as e:
                print(f"       Warning: FasterWhisper unavailable ({e}), using mock provider.")
                trans_provider = MockTranscriptionProvider()

        transcript = run_transcription(
            audio_path=audio_wav_path,
            provider=trans_provider,
            language=args.source_language,
            output_json_path=str(output_dir / "transcript.json")
        )
        print(f"       Transcribed {len(transcript.segments)} speech segments.")
    else:
        print("[2/10] Skipping audio extraction (Video has no audio stream).")
        from worker.schemas.transcript import TranscriptData
        transcript = TranscriptData(language=args.source_language, segments=[])
        (output_dir / "transcript.json").write_text(transcript.model_dump_json(indent=2), encoding="utf-8")

    # 4. Scene Detection
    print("[4/10] Detecting visual scenes...")
    scenes = detect_scenes(
        video_path=str(input_path),
        duration=meta["duration"],
        output_json_path=str(output_dir / "scenes.json")
    )
    print(f"       Detected {len(scenes.scenes)} scenes.")

    # 5. Frame Extraction & Scoped Deduplication
    print(f"[5/10] Extracting candidate frames (CPU budget max: {args.max_frames})...")
    frames = extract_and_deduplicate_frames(
        video_path=str(input_path),
        scenes=scenes,
        transcript=transcript,
        output_dir=str(frames_dir),
        max_frames=args.max_frames,
        output_json_path=str(output_dir / "frames.json")
    )
    print(f"       Extracted {len(frames.frames)} unique keyframes.")

    # 6. Visual Analysis
    print("[6/10] Performing visual analysis on keyframes...")
    if args.use_mock or os.getenv("VISION_PROVIDER") == "mock":
        vision_provider = RuleBasedVisionProvider()
    else:
        vision_provider = LlamaCppVisionProvider()

    vision_data = analyze_frames(
        frames=frames,
        provider=vision_provider,
        output_json_path=str(output_dir / "vision.json")
    )

    # 7. Semantic Timeline Evidence Fusion
    print("[7/10] Fusing audio and visual timeline with semantic consistency check...")
    evidence_data = build_timeline_evidence(
        duration=meta["duration"],
        scenes=scenes,
        transcript=transcript,
        frames=frames,
        vision=vision_data,
        output_json_path=str(output_dir / "evidence.json")
    )
    print(f"       Generated {len(evidence_data.items)} evidence items.")

    # 8. Step Segmentation & Manual Composition
    print("[8/10] Segmenting steps and composing canonical manual_master.json...")
    segmented_steps = segment_steps(evidence_data)
    manual_master = compose_manual(
        segmented_evidence=segmented_steps,
        title="作業手順マニュアル",
        source_language=args.source_language,
        output_json_path=str(output_dir / "manual_master.json")
    )
    print(f"       Composed {len(manual_master.manual.steps)} manual steps.")

    # 9. Translation with Full Metadata Preservation
    print("[9/10] Translating manual into target languages...")
    glossary = GlossaryData()
    if args.glossary and Path(args.glossary).exists():
        glossary_raw = json.loads(Path(args.glossary).read_text(encoding="utf-8"))
        glossary = GlossaryData(**glossary_raw)

    if args.use_mock or os.getenv("TRANSLATION_PROVIDER") == "mock" or not os.getenv("TRANSLATION_MODEL_PATH"):
        trans_provider = MockTranslationProvider()
    else:
        trans_provider = CTranslateTranslationProvider()

    target_langs = [l.strip() for l in args.target_languages.split(",") if l.strip()]
    translated_manuals = translate_manual(
        manual_master=manual_master,
        target_languages=target_langs,
        provider=trans_provider,
        glossary=glossary,
        output_dir=str(output_dir)
    )

    # 10. Document Rendering for All Languages
    print("[10/10] Rendering HTML, Markdown, and PDF documents for all languages...")
    try:
        doc_paths = render_manual_documents(
            manual_master=manual_master,
            frames=frames,
            output_dir=str(output_dir),
            translated_manuals=translated_manuals,
            template_dir=str(root_dir / "templates"),
            generate_pdf=not args.skip_pdf
        )
        for lang, files in doc_paths.items():
            print(f"       [{lang}] HTML: {files['html']}")
            print(f"       [{lang}] MD  : {files['markdown']}")
            if files['pdf']:
                print(f"       [{lang}] PDF : {files['pdf']}")
    except PdfRenderError as pe:
        if args.skip_pdf:
            print(f"       Warning: PDF rendering skipped ({pe})")
        else:
            raise

    print("==================================================")
    print("Pipeline Execution Completed Successfully!")
    print(f"All multilingual artifacts saved under: {output_dir}")
    print("==================================================")

if __name__ == "__main__":
    main()
