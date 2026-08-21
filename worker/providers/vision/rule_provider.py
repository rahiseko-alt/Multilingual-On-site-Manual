from worker.schemas.vision import VisionObservation, ActionItem

class RuleBasedVisionProvider:
    def __init__(self, default_observations: dict[str, dict] | None = None):
        self.default_observations = default_observations or {}

    def analyze_frame(self, frame_id: str, timestamp: float, image_path: str, context: str | None = None) -> VisionObservation:
        if frame_id in self.default_observations:
            obs = self.default_observations[frame_id]
            actions = [ActionItem(**a) for a in obs.get("actions", [])]
            return VisionObservation(
                frame_id=frame_id,
                timestamp=timestamp,
                objects=obs.get("objects", []),
                actions=actions,
                visible_text=obs.get("visible_text", []),
                uncertain=obs.get("uncertain", [])
            )
        
        # Default rule-based observation
        return VisionObservation(
            frame_id=frame_id,
            timestamp=timestamp,
            objects=["作業機器"],
            actions=[ActionItem(actor="作業者", action="操作する", target="作業機器")],
            visible_text=[],
            uncertain=[]
        )
