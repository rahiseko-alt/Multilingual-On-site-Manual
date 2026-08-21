import pytest
from pathlib import Path
from scripts.generate_sample_media import generate_sample_mp4
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
from worker.pipeline.rendering import render_manual_documents

from worker.providers.transcription.mock_provider import MockTranscriptionProvider
from worker.providers.vision.rule_provider import RuleBasedVisionProvider
from worker.providers.translation.mock_provider import MockTranslationProvider
from worker.schemas.glossary import GlossaryData, GlossaryTerm

def test_full_pipeline_multilingual_e2e(tmp_path):
    sample_mp4 = tmp_path / "sample.mp4"
    generate_sample_mp4(str(sample_mp4), duration=4)
    assert sample_mp4.exists()

    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = output_dir / "frames"

    meta = validate_video(str(sample_mp4))
    assert meta["duration"] > 0

    audio_wav = output_dir / "audio.wav"
    extract_audio(str(sample_mp4), str(audio_wav))

    trans_provider = MockTranscriptionProvider([
        {"id": "seg_001", "start": 0.0, "end": 2.0, "text": "STARTボタンを押して機械を起動します。"},
        {"id": "seg_002", "start": 2.2, "end": 3.8, "text": "投入レバーを回して材料を入れます。"}
    ])
    transcript = run_transcription(str(audio_wav), trans_provider, "ja", str(output_dir / "transcript.json"))
    scenes = detect_scenes(str(sample_mp4), meta["duration"], str(output_dir / "scenes.json"))
    frames = extract_and_deduplicate_frames(str(sample_mp4), scenes, transcript, str(frames_dir), 6, 10, str(output_dir / "frames.json"))

    vision_provider = RuleBasedVisionProvider({
        "frame_001": {
            "objects": ["STARTボタン"],
            "actions": [{"actor": "作業者", "action": "押す", "target": "STARTボタン"}]
        },
        "frame_002": {
            "objects": ["投入レバー"],
            "actions": [{"actor": "作業者", "action": "回す", "target": "投入レバー"}]
        }
    })
    vision_data = analyze_frames(frames, vision_provider, str(output_dir / "vision.json"))
    evidence_data = build_timeline_evidence(meta["duration"], scenes, transcript, frames, vision_data, str(output_dir / "evidence.json"))
    steps = segment_steps(evidence_data)
    manual_master = compose_manual(steps, title="機械操作マニュアル", output_json_path=str(output_dir / "manual_master.json"))

    glossary = GlossaryData(terms=[
        GlossaryTerm(source="STARTボタン", translation={"vi": "nút START", "id": "tombol START"}, translate=True)
    ])
    trans_provider = MockTranslationProvider()
    translated_dict = translate_manual(manual_master, ["vi", "id"], trans_provider, glossary, str(output_dir))

    # Test multilingual rendering across all languages (P0-5)
    doc_paths = render_manual_documents(
        manual_master=manual_master,
        frames=frames,
        output_dir=str(output_dir),
        translated_manuals=translated_dict,
        template_dir="templates",
        generate_pdf=False # Testing HTML & MD rendering directly
    )

    # Check JA documents
    assert "ja" in doc_paths
    assert Path(doc_paths["ja"]["html"]).exists()
    assert Path(doc_paths["ja"]["markdown"]).exists()

    # Check VI documents
    assert "vi" in doc_paths
    assert Path(doc_paths["vi"]["html"]).exists()
    assert Path(doc_paths["vi"]["markdown"]).exists()

    # Check ID documents
    assert "id" in doc_paths
    assert Path(doc_paths["id"]["html"]).exists()
    assert Path(doc_paths["id"]["markdown"]).exists()
