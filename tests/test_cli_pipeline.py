import os
import shutil
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

def test_full_pipeline_e2e(tmp_path):
    # 1. Generate sample fixture mp4
    sample_mp4 = tmp_path / "sample.mp4"
    generate_sample_mp4(str(sample_mp4), duration=4)
    assert sample_mp4.exists()

    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = output_dir / "frames"

    # 2. Validation
    meta = validate_video(str(sample_mp4))
    assert meta["duration"] > 0
    assert meta["has_audio"] is True

    # 3. Audio Extraction
    audio_wav = output_dir / "audio.wav"
    extract_audio(str(sample_mp4), str(audio_wav))
    assert audio_wav.exists()

    # 4. Transcription
    trans_provider = MockTranscriptionProvider([
        {"id": "seg_001", "start": 0.0, "end": 2.0, "text": "STARTボタンを押して機械を起動します。"},
        {"id": "seg_002", "start": 2.2, "end": 3.8, "text": "投入レバーを回して材料を入れます。"}
    ])
    transcript = run_transcription(str(audio_wav), trans_provider, "ja", str(output_dir / "transcript.json"))
    assert len(transcript.segments) == 2
    assert (output_dir / "transcript.json").exists()

    # 5. Scene Detection
    scenes = detect_scenes(str(sample_mp4), meta["duration"], str(output_dir / "scenes.json"))
    assert len(scenes.scenes) >= 1
    assert (output_dir / "scenes.json").exists()

    # 6. Frames
    frames = extract_and_deduplicate_frames(str(sample_mp4), scenes, transcript, str(frames_dir), 6, str(output_dir / "frames.json"))
    assert len(frames.frames) >= 1
    assert (output_dir / "frames.json").exists()
    for f in frames.frames:
        assert Path(frames_dir / Path(f.path).name).exists()

    # 7. Vision Analysis
    vision_provider = RuleBasedVisionProvider({
        "frame_001": {
            "objects": ["STARTボタン", "操作パネル"],
            "actions": [{"actor": "作業者", "action": "押す", "target": "STARTボタン"}]
        }
    })
    vision_data = analyze_frames(frames, vision_provider, str(output_dir / "vision.json"))
    assert len(vision_data.observations) == len(frames.frames)
    assert (output_dir / "vision.json").exists()

    # 8. Evidence
    evidence_data = build_timeline_evidence(meta["duration"], scenes, transcript, frames, vision_data, str(output_dir / "evidence.json"))
    assert len(evidence_data.items) >= 1
    assert (output_dir / "evidence.json").exists()

    # 9. Step Segmentation & Manual Composition
    steps = segment_steps(evidence_data)
    manual_master = compose_manual(steps, title="機械操作マニュアル", output_json_path=str(output_dir / "manual_master.json"))
    assert len(manual_master.manual.steps) >= 1
    assert (output_dir / "manual_master.json").exists()

    # Verify Acceptance Criteria
    for st in manual_master.manual.steps:
        # AC-002: At least 1 evidence referenced
        assert st.evidence.video_start >= 0
        assert len(st.evidence.transcript_ids) > 0 or len(st.evidence.frame_ids) > 0
        # AC-003: Frame ID must exist if present
        for fid in st.evidence.frame_ids:
            assert any(f.id == fid for f in frames.frames)
        # AC-004: Transcript ID must exist if present
        for tid in st.evidence.transcript_ids:
            assert any(s.id == tid for s in transcript.segments)

    # 10. Translation with Glossary
    glossary = GlossaryData(terms=[
        GlossaryTerm(source="STARTボタン", translation={"vi": "nút START", "id": "tombol START"}, translate=True)
    ])
    trans_provider = MockTranslationProvider()
    translated_dict = translate_manual(manual_master, ["vi", "id"], trans_provider, glossary, str(output_dir))
    assert "vi" in translated_dict
    assert "id" in translated_dict
    assert (output_dir / "manual_vi.json").exists()
    assert (output_dir / "manual_id.json").exists()

    # 11. Render Documents
    doc_paths = render_manual_documents(manual_master, frames, str(output_dir), "templates")
    assert Path(doc_paths["html"]).exists()
    assert Path(doc_paths["markdown"]).exists()
    assert Path(doc_paths["pdf"]).exists()
