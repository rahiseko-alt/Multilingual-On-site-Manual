import pytest
from worker.schemas.evidence import EvidenceData, EvidenceItem, AudioEvidence, VisionEvidence
from worker.schemas.vision import ActionItem
from worker.schemas.frames import FrameData, FrameItem
from worker.schemas.scene import SceneData, SceneItem
from worker.schemas.transcript import TranscriptData, TranscriptSegment
from worker.pipeline.evidence import build_timeline_evidence
from worker.pipeline.manual import compose_manual
from worker.pipeline.segmentation import segment_steps

def test_evidence_and_manual_composition():
    # Synthetic data
    scenes = SceneData(scenes=[SceneItem(id="scene_001", start=0.0, end=5.0)])
    transcript = TranscriptData(language="ja", segments=[
        TranscriptSegment(id="seg_001", start=0.5, end=4.5, text="赤色の電源ボタンを押します。")
    ])
    frames = FrameData(frames=[
        FrameItem(id="frame_001", timestamp=2.5, path="frames/frame_001.jpg")
    ])
    from worker.schemas.vision import VisionData, VisionObservation
    vision = VisionData(observations=[
        VisionObservation(
            frame_id="frame_001",
            timestamp=2.5,
            objects=["電源ボタン"],
            actions=[ActionItem(actor="作業者", action="押す", target="電源ボタン")]
        )
    ])

    ev_data = build_timeline_evidence(
        duration=5.0,
        scenes=scenes,
        transcript=transcript,
        frames=frames,
        vision=vision
    )

    assert len(ev_data.items) == 1
    ev_item = ev_data.items[0]
    assert ev_item.evidence_score >= 0.8 # High score since both audio and vision match
    assert ev_item.audio.segment_ids == ["seg_001"]
    assert "frame_001" in ev_item.vision.frame_ids

    # Step Segmentation & Manual Composition
    segmented = segment_steps(ev_data)
    manual_master = compose_manual(segmented, title="テストマニュアル")

    assert len(manual_master.manual.steps) == 1
    step = manual_master.manual.steps[0]
    assert step.step_id == "step_001"
    assert step.order == 1
    assert step.evidence.video_start == 0.5
    assert step.evidence.transcript_ids == ["seg_001"]
    assert step.evidence.frame_ids == ["frame_001"]
    assert step.media.primary_frame_id == "frame_001"
    assert step.status == "generated"
