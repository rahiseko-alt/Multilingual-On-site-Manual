import pytest
from worker.schemas.evidence import EvidenceData, EvidenceItem, AudioEvidence, VisionEvidence
from worker.schemas.vision import ActionItem, VisionObservation, VisionData
from worker.schemas.frames import FrameData, FrameItem
from worker.schemas.scene import SceneData, SceneItem
from worker.schemas.transcript import TranscriptData, TranscriptSegment
from worker.pipeline.evidence import build_timeline_evidence
from worker.pipeline.manual import compose_manual, is_negation_or_warning, extract_safe_step_title
from worker.pipeline.segmentation import segment_steps

def test_semantic_evidence_matching_and_scoring():
    scenes = SceneData(scenes=[SceneItem(id="scene_001", start=0.0, end=5.0)])
    transcript = TranscriptData(language="ja", segments=[
        TranscriptSegment(id="seg_001", start=0.5, end=4.5, text="赤色のボタンを押します。")
    ])
    frames = FrameData(frames=[
        FrameItem(id="frame_001", timestamp=2.5, path="frames/frame_001.jpg")
    ])

    # 1. Matching case: Audio and Vision agree
    matching_vision = VisionData(observations=[
        VisionObservation(
            frame_id="frame_001",
            timestamp=2.5,
            objects=["ボタン"],
            actions=[ActionItem(actor="作業者", action="押す", target="ボタン")],
            provider_status="success"
        )
    ])
    ev_matching = build_timeline_evidence(5.0, scenes, transcript, frames, matching_vision)
    assert len(ev_matching.items) == 1
    # Both temporal and semantic alignment pass
    assert ev_matching.items[0].evidence_score >= 0.70

    # 2. Mismatching case: Audio talks about button, but vision sees completely different object/action
    mismatching_vision = VisionData(observations=[
        VisionObservation(
            frame_id="frame_001",
            timestamp=2.5,
            objects=["青いレバー"],
            actions=[ActionItem(actor="作業者", action="引く", target="青いレバー")],
            provider_status="success"
        )
    ])
    ev_mismatch = build_timeline_evidence(5.0, scenes, transcript, frames, mismatching_vision)
    assert len(ev_mismatch.items) == 1
    # Score should be low due to semantic mismatch
    assert ev_mismatch.items[0].evidence_score < 0.50

    # 3. Fail-Closed case: Vision analysis failed
    failed_vision = VisionData(observations=[
        VisionObservation(
            frame_id="frame_001",
            timestamp=2.5,
            objects=[],
            actions=[],
            uncertain=["vision_analysis_failed"],
            provider_status="failed"
        )
    ])
    ev_failed = build_timeline_evidence(5.0, scenes, transcript, frames, failed_vision)
    assert len(ev_failed.items) == 1
    assert ev_failed.items[0].evidence_score <= 0.30

    # Manual composition on low score must trigger 'needs_review'
    steps = compose_manual(segment_steps(ev_failed)).manual.steps
    assert len(steps) == 1
    assert steps[0].status == "needs_review"

def test_negation_and_warning_safety():
    # Test P0-4: Negative/prohibitive phrases must never be flipped to positive imperatives
    neg_text_1 = "赤いボタンは押さないでください。"
    title_1, warn_1 = extract_safe_step_title(neg_text_1, [], 1)
    assert "ボタンを押す" not in title_1
    assert warn_1 is not None
    assert "押さないでください" in warn_1

    neg_text_2 = "ここには材料を投入しないでください。"
    title_2, warn_2 = extract_safe_step_title(neg_text_2, [], 2)
    assert "材料を投入する" not in title_2
    assert warn_2 is not None

    # Positive text extraction
    pos_text = "電源スイッチを入れます。"
    title_pos, warn_pos = extract_safe_step_title(pos_text, [], 3)
    assert warn_pos is None
    assert "電源スイッチを入れます" in title_pos
