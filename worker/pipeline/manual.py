from pathlib import Path
from worker.schemas.evidence import EvidenceItem
from worker.schemas.manual import ManualMaster, ManualMeta, ManualStep, StepEvidence, StepMedia

def compose_manual(
    segmented_evidence: list[EvidenceItem],
    title: str = "作業手順マニュアル",
    source_language: str = "ja",
    review_threshold: float = 0.5,
    output_json_path: str | None = None
) -> ManualMaster:
    steps = []

    for order, ev in enumerate(segmented_evidence, start=1):
        step_id = f"step_{order:03d}"
        
        # Audio based instruction candidate
        audio_text = ev.audio.text.strip()
        
        # Vision based candidate
        action_summary = ""
        equipment = list(ev.vision.objects)
        if ev.vision.actions:
            first_act = ev.vision.actions[0]
            action_summary = f"{first_act.target}を{first_act.action}"
            if first_act.target not in equipment:
                equipment.append(first_act.target)

        # Title & instruction composition
        if audio_text:
            # Prefer audio instruction if available
            instruction = audio_text
            # Derive concise title
            if "ボタン" in audio_text and "押" in audio_text:
                step_title = "ボタンを押す"
            elif "レバー" in audio_text or "投入" in audio_text:
                step_title = "材料を投入する"
            elif action_summary:
                step_title = action_summary
            else:
                step_title = f"工程 {order} の作業"
        elif action_summary:
            step_title = action_summary
            instruction = f"{action_summary}します。"
        else:
            step_title = f"作業手順 {order}"
            instruction = "映像および音声を確認の上、手順を記録してください。"

        # Media selection
        primary_frame_id = ev.vision.frame_ids[0] if ev.vision.frame_ids else None
        additional_frame_ids = ev.vision.frame_ids[1:] if len(ev.vision.frame_ids) > 1 else []

        status = "generated" if ev.evidence_score >= review_threshold else "needs_review"

        step_ev = StepEvidence(
            video_start=ev.start,
            video_end=ev.end,
            transcript_ids=ev.audio.segment_ids,
            frame_ids=ev.vision.frame_ids
        )

        steps.append(
            ManualStep(
                step_id=step_id,
                order=order,
                title=step_title,
                instruction=instruction,
                warning=None, # Never hallucinate warnings without explicit evidence
                equipment=equipment,
                media=StepMedia(
                    primary_frame_id=primary_frame_id,
                    additional_frame_ids=additional_frame_ids
                ),
                evidence=step_ev,
                evidence_score=ev.evidence_score,
                status=status
            )
        )

    meta = ManualMeta(
        title=title,
        source_language=source_language,
        steps=steps
    )
    manual_master = ManualMaster(
        schema_version="1.0",
        manual=meta
    )

    if output_json_path:
        out = Path(output_json_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(manual_master.model_dump_json(indent=2), encoding="utf-8")

    return manual_master
