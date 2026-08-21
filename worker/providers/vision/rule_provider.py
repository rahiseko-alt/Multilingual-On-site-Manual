from worker.schemas.vision import VisionObservation, ActionItem

class RuleBasedVisionProvider:
    def __init__(self, explicit_observations: dict[str, dict] | None = None):
        self.explicit_observations = explicit_observations or {}

    def analyze_frame(self, frame_id: str, timestamp: float, image_path: str, context: str | None = None) -> VisionObservation:
        if frame_id in self.explicit_observations:
            obs = self.explicit_observations[frame_id]
            actions = [ActionItem(**a) for a in obs.get("actions", [])]
            return VisionObservation(
                frame_id=frame_id,
                timestamp=timestamp,
                objects=obs.get("objects", []),
                actions=actions,
                visible_text=obs.get("visible_text", []),
                uncertain=obs.get("uncertain", []),
                provider_status="success"
            )
        
        # Fail-closed: Never generate fake objects or actions without explicit evidence
        return VisionObservation(
            frame_id=frame_id,
            timestamp=timestamp,
            objects=[],
            actions=[],
            visible_text=[],
            uncertain=["no_visual_evidence_detected"],
            provider_status="unprocessed"
        )
