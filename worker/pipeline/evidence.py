from pathlib import Path
from worker.schemas.evidence import EvidenceData, EvidenceItem, AudioEvidence, VisionEvidence
from worker.schemas.frames import FrameData
from worker.schemas.scene import SceneData
from worker.schemas.transcript import TranscriptData
from worker.schemas.vision import VisionData

def build_timeline_evidence(
    duration: float,
    scenes: SceneData,
    transcript: TranscriptData | None,
    frames: FrameData,
    vision: VisionData,
    output_json_path: str | None = None
) -> EvidenceData:
    evidence_items = []
    
    # Map frame observations by frame_id and timestamp
    obs_map = {obs.frame_id: obs for obs in vision.observations}
    frame_map = {f.id: f for f in frames.frames}

    # Grouping timeline based on scenes or transcript segments
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
        
        # Collect audio
        audio_text = " ".join(s.text for s in segs) if segs else ""
        seg_ids = [s.id for s in segs]
        audio_ev = AudioEvidence(segment_ids=seg_ids, text=audio_text)

        # Collect vision within [start - 0.5, end + 0.5]
        matched_frame_ids = []
        matched_objects = set()
        matched_actions = []

        for f in frames.frames:
            if start - 0.5 <= f.timestamp <= end + 0.5:
                matched_frame_ids.append(f.id)
                if f.id in obs_map:
                    obs = obs_map[f.id]
                    matched_objects.update(obs.objects)
                    matched_actions.extend(obs.actions)

        vision_ev = VisionEvidence(
            frame_ids=matched_frame_ids,
            objects=list(matched_objects),
            actions=matched_actions
        )

        # Compute evidence_score
        score = 0.0
        if seg_ids and audio_text:
            score += 0.45
        if matched_frame_ids and (matched_objects or matched_actions):
            score += 0.45
        if seg_ids and matched_frame_ids:
            score += 0.10

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
