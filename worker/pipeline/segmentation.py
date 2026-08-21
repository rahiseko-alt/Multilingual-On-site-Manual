from worker.schemas.evidence import EvidenceData, EvidenceItem

def segment_steps(evidence_data: EvidenceData) -> list[EvidenceItem]:
    # Ensure 1 Step = 1 primary operation unit
    # Filter empty or zero-signal evidence if appropriate, but preserve all operation slices
    steps = []
    for item in evidence_data.items:
        # Keep non-empty evidence items
        if item.audio.text or item.vision.frame_ids or item.vision.actions:
            steps.append(item)
    
    if not steps and evidence_data.items:
        steps = evidence_data.items
    return steps
