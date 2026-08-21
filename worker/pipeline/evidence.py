import re
from pathlib import Path
from worker.schemas.evidence import EvidenceData, EvidenceItem, AudioEvidence, VisionEvidence
from worker.schemas.frames import FrameData
from worker.schemas.scene import SceneData
from worker.schemas.transcript import TranscriptData
from worker.schemas.vision import VisionData

def calculate_semantic_alignment(audio_text: str, vision_objects: list[str], vision_actions: list) -> float:
    """Calculate semantic cross-modal consistency between audio text and visual observations."""
    if not audio_text or (not vision_objects and not vision_actions):
        return 0.0

    score = 0.0
    text_lower = audio_text.lower()

    # 1. Object matching
    object_matches = 0
    all_targets = set(vision_objects)
    for act in vision_actions:
        if hasattr(act, "target") and act.target:
            all_targets.add(act.target)

    for target in all_targets:
        if target and target.lower() in text_lower:
            object_matches += 1

    if object_matches > 0:
        score += min(0.40, object_matches * 0.25)

    # 2. Action / Verb matching
    action_matches = 0
    for act in vision_actions:
        action_name = act.action if hasattr(act, "action") else ""
        if action_name and (action_name.lower() in text_lower or (action_name == "押す" and "押" in text_lower) or (action_name == "回す" and "回" in text_lower) or (action_name == "投入する" and "投入" in text_lower)):
            action_matches += 1

    if action_matches > 0:
        score += min(0.30, action_matches * 0.20)

    return min(0.70, score)

def build_timeline_evidence(
    duration: float,
    scenes: SceneData,
    transcript: TranscriptData | None,
    frames: FrameData,
    vision: VisionData,
    output_json_path: str | None = None
) -> EvidenceData:
    evidence_items = []
    obs_map = {obs.frame_id: obs for obs in vision.observations}

    # Group timeline based on scenes or transcript segments
    time_slices = []
    if transcript and transcript.segments:
        for seg in transcript.segments:
            time_slices.append((seg.start, seg.end, [seg]))
    else:
        for s in scenes.scenes:
            time_slices.append((s.start, s.end, []))

    if not time_slices:
        time_slices.append((0.0, duration, []))

    for idx, (start, end, segs) in enumerate(time_slices, start=1):
        ev_id = f"ev_{idx:03d}"
        
        audio_text = " ".join(s.text for s in segs) if segs else ""
        seg_ids = [s.id for s in segs]
        audio_ev = AudioEvidence(segment_ids=seg_ids, text=audio_text)

        matched_frame_ids = []
        matched_objects = set()
        matched_actions = []
        has_failed_vision = False

        for f in frames.frames:
            if start - 0.5 <= f.timestamp <= end + 0.5:
                matched_frame_ids.append(f.id)
                if f.id in obs_map:
                    obs = obs_map[f.id]
                    if obs.provider_status == "failed" or "vision_analysis_failed" in obs.uncertain:
                        has_failed_vision = True
                    matched_objects.update(obs.objects)
                    matched_actions.extend(obs.actions)

        vision_ev = VisionEvidence(
            frame_ids=matched_frame_ids,
            objects=list(matched_objects),
            actions=matched_actions
        )

        # Rigorous cross-modal Evidence scoring
        score = 0.0
        # Temporal alignment signal (both modalities exist in window)
        if seg_ids and matched_frame_ids and not has_failed_vision:
            score += 0.30
        elif seg_ids or matched_frame_ids:
            score += 0.15

        # Semantic content alignment
        semantic_score = calculate_semantic_alignment(audio_text, list(matched_objects), matched_actions)
        score += semantic_score

        # If vision explicitly failed or no objects/actions found despite image presence
        if has_failed_vision:
            score = min(0.30, score)

        score = min(1.0, round(score, 2))

        evidence_items.append(
            EvidenceItem(
                id=ev_id,
                start=start,
                end=end,
                audio=audio_ev,
                vision=vision_ev,
                evidence_score=score
            )
        )

    data = EvidenceData(items=evidence_items)
    if output_json_path:
        out = Path(output_json_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(data.model_dump_json(indent=2), encoding="utf-8")

    return data
