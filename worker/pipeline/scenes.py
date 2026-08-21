from pathlib import Path
from worker.schemas.scene import SceneData, SceneItem

def detect_scenes(video_path: str, duration: float, output_json_path: str | None = None) -> SceneData:
    v_path = Path(video_path).resolve()
    scenes = []
    
    try:
        from scenedetect import open_video, SceneManager
        from scenedetect.detectors import AdaptiveDetector

        video = open_video(str(v_path))
        scene_manager = SceneManager()
        scene_manager.add_detector(AdaptiveDetector())
        scene_manager.detect_scenes(video)
        scene_list = scene_manager.get_scene_list()

        if scene_list:
            for i, (start_time, end_time) in enumerate(scene_list, start=1):
                scenes.append(
                    SceneItem(
                        id=f"scene_{i:03d}",
                        start=round(start_time.get_seconds(), 2),
                        end=round(end_time.get_seconds(), 2)
                    )
                )
    except Exception:
        pass

    if not scenes:
        chunk_len = 5.0
        cur = 0.0
        idx = 1
        while cur < duration:
            nxt = min(cur + chunk_len, duration)
            scenes.append(
                SceneItem(
                    id=f"scene_{idx:03d}",
                    start=round(cur, 2),
                    end=round(nxt, 2)
                )
            )
            cur = nxt
            idx += 1

    data = SceneData(scenes=scenes)
    if output_json_path:
        out = Path(output_json_path).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(data.model_dump_json(indent=2), encoding="utf-8")

    return data
