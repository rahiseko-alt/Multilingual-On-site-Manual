from typing import Protocol
from worker.schemas.vision import VisionObservation

class VisionProvider(Protocol):
    def analyze_frame(self, frame_id: str, timestamp: float, image_path: str, context: str | None = None) -> VisionObservation:
        ...
