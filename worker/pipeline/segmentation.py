from worker.schemas.evidence import EvidenceData, EvidenceItem, AudioEvidence, VisionEvidence

def segment_steps(evidence_data: EvidenceData, max_step_gap: float = 1.5) -> list[EvidenceItem]:
    """
    Cluster and segment raw timeline evidence slices into distinct operational steps.
    Consolidates continuous speech / local actions within the same operational unit.
    """
    if not evidence_data.items:
        return []

    clustered_steps: list[EvidenceItem] = []
    current_cluster: list[EvidenceItem] = []

    for item in evidence_data.items:
        if not current_cluster:
            current_cluster.append(item)
            continue

        prev = current_cluster[-1]
        gap = item.start - prev.end

        # If evidence items are close in time (< max_step_gap) and share continuous context
        is_continuous = gap <= max_step_gap

        if is_continuous and len(current_cluster) < 3:
            current_cluster.append(item)
        else:
            # Merge current cluster into a single consolidated step
            merged = _merge_evidence_cluster(current_cluster, f"step_ev_{len(clustered_steps) + 1:03d}")
            clustered_steps.append(merged)
            current_cluster = [item]

    if current_cluster:
        merged = _merge_evidence_cluster(current_cluster, f"step_ev_{len(clustered_steps) + 1:03d}")
        clustered_steps.append(merged)

    return clustered_steps

def _merge_evidence_cluster(cluster: list[EvidenceItem], cluster_id: str) -> EvidenceItem:
    if len(cluster) == 1:
        return cluster[0]

    start = cluster[0].start
    end = cluster[-1].end
    
    # Merge audio
    all_seg_ids = []
    texts = []
    for c in cluster:
        all_seg_ids.extend(c.audio.segment_ids)
        if c.audio.text:
            texts.append(c.audio.text)
    
    # Merge vision
    all_frame_ids = []
    all_objects = set()
    all_actions = []
    for c in cluster:
        all_frame_ids.extend(c.vision.frame_ids)
        all_objects.update(c.vision.objects)
        all_actions.extend(c.vision.actions)

    # Average score
    avg_score = round(sum(c.evidence_score for c in cluster) / len(cluster), 2)

    return EvidenceItem(
        id=cluster_id,
        start=start,
        end=end,
        audio=AudioEvidence(segment_ids=list(dict.fromkeys(all_seg_ids)), text=" ".join(texts)),
        vision=VisionEvidence(
            frame_ids=list(dict.fromkeys(all_frame_ids)),
            objects=list(all_objects),
            actions=all_actions
        ),
        evidence_score=avg_score
    )
