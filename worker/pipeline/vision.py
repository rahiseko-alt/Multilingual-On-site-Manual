from pathlib import Path
from worker.providers.vision.base import VisionProvider
from worker.schemas.frames import FrameData
from worker.schemas.vision import VisionData

def analyze_frames(
    frames: FrameData,
    provider: VisionProvider,
    output_json_path: str | None = None
) -> VisionData:
    observations = []
    for f in frames.frames:
        obs = provider.analyze_frame(
            frame_id=f.id,
            timestamp=f.timestamp,
            image_path=f.path
        )
        observations.append(obs)

    data = VisionData(observations=observations)
    if output_json_path:
        out = Path(output_json_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(data.model_dump_json(indent=2), encoding="utf-8")

    return data
