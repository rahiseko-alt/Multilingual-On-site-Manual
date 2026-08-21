import re
from pathlib import Path
from worker.schemas.evidence import EvidenceItem
from worker.schemas.manual import ManualMaster, ManualMeta, ManualStep, StepEvidence, StepMedia

NEGATION_PATTERNS = [
    r"ないで", r"禁止", r"しない", r"触るな", r"押すな", r"回すな",
    r"ダメ", r"危険", r"注意", r"やめて", r"置かない", r"開けない"
]

def is_negation_or_warning(text: str) -> bool:
    if not text:
        return False
    return any(re.search(p, text) for p in NEGATION_PATTERNS)

def extract_safe_step_title(audio_text: str, vision_actions: list, order: int) -> tuple[str, str | None]:
    """
    Safely extract step title and explicit warning without flipping negative/prohibitive statements.
    Never turn '赤いボタンは押さないでください' into 'ボタンを押す'.
    """
    warning = None
    if is_negation_or_warning(audio_text):
        warning = audio_text.strip()
        return f"工程 {order}: 注意事項の確認", warning

    # If clean positive speech is available
    if audio_text:
        cleaned = audio_text.strip().rstrip("。！？")
        # Use first meaningful clause if speech is short
        if len(cleaned) <= 24:
            return cleaned, None
        
        # Split by punctuation or conjunctions
        parts = re.split(r"[、,]\s*|そして|次に|まず|最後に", cleaned)
        valid_parts = [p.strip() for p in parts if len(p.strip()) >= 3]
        if valid_parts:
            return valid_parts[0], None
        return f"工程 {order} の作業", None

    # If vision actions are clearly recognized
    if vision_actions:
        first_act = vision_actions[0]
        if hasattr(first_act, "target") and hasattr(first_act, "action"):
            return f"{first_act.target}の操作 ({first_act.action})", None

    return f"工程 {order} の手順", None

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
        audio_text = ev.audio.text.strip()
        
        step_title, detected_warning = extract_safe_step_title(audio_text, ev.vision.actions, order)

        # Instruction composition
        if audio_text:
            instruction = audio_text
        elif ev.vision.actions:
            first_act = ev.vision.actions[0]
            instruction = f"{first_act.target}を{first_act.action}します。"
        else:
            instruction = "映像および音声から手順を確認してください。"

        equipment = list(ev.vision.objects)
        for act in ev.vision.actions:
            if hasattr(act, "target") and act.target and act.target not in equipment:
                equipment.append(act.target)

        primary_frame_id = ev.vision.frame_ids[0] if ev.vision.frame_ids else None
        additional_frame_ids = ev.vision.frame_ids[1:] if len(ev.vision.frame_ids) > 1 else []

        # Strict status gating
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
                warning=detected_warning,
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
