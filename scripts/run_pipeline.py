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

def run_preflight_check():
    """Verify system prerequisites before running heavy pipeline."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("Preflight Check Failed: 'ffmpeg' executable not found in PATH.")
    if not shutil.which("ffprobe"):
        raise RuntimeError("Preflight Check Failed: 'ffprobe' executable not found in PATH.")

def run_video2doc_pipeline(
    input_video_path: str,
    output_dir: str,
    source_language: str = "ja",
    target_languages: list = None,
    use_mock: bool = True,
    skip_pdf: bool = True,
    max_frames: int = 30,
    glossary_path: str = None,
) -> dict:
    if target_languages is None:
        target_languages = ["vi", "id"]

    input_path = Path(input_video_path).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    run_preflight_check()

    max_size_mb = int(os.getenv("MAX_VIDEO_SIZE_MB", 500))
    max_duration_min = int(os.getenv("MAX_VIDEO_DURATION_MINUTES", 30))
    meta = validate_video(str(input_path), max_size_mb=max_size_mb, max_duration_minutes=max_duration_min)

    audio_wav_path = str(out_dir / "audio.wav")
    transcript = None
    if meta["has_audio"]:
        extract_audio(str(input_path), audio_wav_path)
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

    scenes = detect_scenes(
        video_path=str(input_path),
        duration=meta["duration"],
        output_json_path=str(out_dir / "scenes.json")
    )

    frames = extract_and_deduplicate_frames(
        video_path=str(input_path),
        scenes=scenes,
        transcript=transcript,
        output_dir=str(frames_dir),
        max_frames=max_frames,
        output_json_path=str(out_dir / "frames.json")
    )

    if use_mock or os.getenv("VISION_PROVIDER") == "mock":
        vision_provider = RuleBasedVisionProvider()
    else:
        vision_provider = LlamaCppVisionProvider()

    vision_data = analyze_frames(
        frames=frames,
        provider=vision_provider,
        output_json_path=str(out_dir / "vision.json")
    )

    evidence_data = build_timeline_evidence(
        duration=meta["duration"],
        scenes=scenes,
        transcript=transcript,
        frames=frames,
        vision=vision_data,
        output_json_path=str(out_dir / "evidence.json")
    )

    segmented_steps = segment_steps(evidence_data)
    manual_master = compose_manual(
        segmented_evidence=segmented_steps,
        title="作業手順マニュアル",
        source_language=source_language,
        output_json_path=str(out_dir / "manual_master.json")
    )

    glossary = GlossaryData()
    if glossary_path and Path(glossary_path).exists():
        glossary_raw = json.loads(Path(glossary_path).read_text(encoding="utf-8"))
        glossary = GlossaryData(**glossary_raw)

    if use_mock or os.getenv("TRANSLATION_PROVIDER") == "mock" or not os.getenv("TRANSLATION_MODEL_PATH"):
        trans_provider = MockTranslationProvider()
    else:
        trans_provider = CTranslateTranslationProvider()

    translated_manuals = translate_manual(
        manual_master=manual_master,
        target_languages=target_languages,
        provider=trans_provider,
        glossary=glossary,
        output_dir=str(out_dir)
    )

    doc_paths = render_manual_documents(
        manual_master=manual_master,
        frames=frames,
        output_dir=str(out_dir),
        translated_manuals=translated_manuals,
        template_dir=str(root_dir / "templates"),
        generate_pdf=not skip_pdf
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

    target_langs = [l.strip() for l in args.target_languages.split(",") if l.strip()]

    print("==================================================")
    print("Video2Doc MultiLang v1.0 CLI Pipeline")
    print(f"Input Video : {args.input}")
    print(f"Output Dir  : {args.output}")
    print(f"Languages   : {args.source_language} -> {args.target_languages}")
    print("==================================================")

    res = run_video2doc_pipeline(
        input_video_path=args.input,
        output_dir=args.output,
        source_language=args.source_language,
        target_languages=target_langs,
        use_mock=args.use_mock,
        skip_pdf=args.skip_pdf,
        max_frames=args.max_frames,
        glossary_path=args.glossary
    )

    print("==================================================")
    print("Pipeline Execution Completed Successfully!")
    print(f"Master Manual: {res['manual_master']}")
    print(f"Evidence     : {res['evidence']}")
    for lang, docs in res["documents"].items():
        print(f"[{lang}] HTML: {docs['html']}")
        print(f"[{lang}] MD  : {docs['markdown']}")
        if docs.get("pdf"):
            print(f"[{lang}] PDF : {docs['pdf']}")
    print("==================================================")

if __name__ == "__main__":
    main()
